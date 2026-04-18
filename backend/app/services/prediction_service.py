"""
Prediction Service — Orchestrates: Spark → ML → PFI → Groq
Runs as an async background task; updates prediction status for polling.
"""
import numpy as np
import pandas as pd
import json
import os
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Assessment, Prediction, PFIResult, Insight

# Feature columns used in ML (must match training)
FEATURE_COLUMNS = [
    "running_speed_100m", "endurance_1500m", "flexibility_score",
    "strength_score", "bmi", "coordination_score", "reaction_time_ms",
    "physical_progress_index", "skill_acquisition_speed",
    "motivation_score", "self_confidence_score", "stress_management_score",
    "goal_orientation_score", "mental_resilience_score",
    "teamwork_score", "participation_score", "communication_score",
    "leadership_score", "peer_collaboration_score",
    "age", "grade_level"
]

FEATURE_DISPLAY_NAMES = {
    "motivation_score": "Motivation Level",
    "self_confidence_score": "Self-Confidence",
    "stress_management_score": "Stress Management",
    "goal_orientation_score": "Goal Orientation",
    "mental_resilience_score": "Mental Resilience",
    "teamwork_score": "Teamwork",
    "participation_score": "Class Participation",
    "communication_score": "Communication",
    "leadership_score": "Leadership",
    "peer_collaboration_score": "Peer Collaboration",
    "running_speed_100m": "Sprint Speed (100m)",
    "endurance_1500m": "Endurance (1500m)",
    "flexibility_score": "Flexibility",
    "strength_score": "Physical Strength",
    "bmi": "Body Mass Index",
    "coordination_score": "Coordination",
    "reaction_time_ms": "Reaction Time",
    "physical_progress_index": "Physical Progress",
    "skill_acquisition_speed": "Skill Learning Speed",
    "age": "Age",
    "grade_level": "Grade Level",
}


async def run_prediction_pipeline(
    assessment_id: str, student_id: str, prediction_id: str, db: AsyncSession
):
    """Full prediction pipeline — designed to run as a background task."""
    try:
        # 1. Load assessment data
        result = await db.execute(
            select(Assessment).where(Assessment.assessment_id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if not assessment:
            await _update_status(db, prediction_id, "failed")
            return

        # Also load student info for age/grade
        from app.models import Student
        student_result = await db.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = student_result.scalar_one_or_none()

        # 2. Build feature vector
        feature_dict = {}
        for col in FEATURE_COLUMNS:
            if col == "age":
                feature_dict[col] = float(student.age or 18)
            elif col == "grade_level":
                feature_dict[col] = float(student.grade_level or 10)
            else:
                val = getattr(assessment, col, None)
                feature_dict[col] = float(val) if val is not None else 0.0

        # 3. Load ML models and predict
        model_dir = settings.MODEL_DIR
        feature_names_path = os.path.join(model_dir, "feature_names.json")

        if os.path.exists(feature_names_path):
            with open(feature_names_path, "r") as f:
                trained_feature_names = json.load(f)
        else:
            trained_feature_names = FEATURE_COLUMNS

        # Build feature array in training order
        X = np.array([[feature_dict.get(f, 0.0) for f in trained_feature_names]])
        
        scaler_path = os.path.join(model_dir, "scaler_params.json")
        if os.path.exists(scaler_path):
            with open(scaler_path, "r") as f:
                params = json.load(f)
            means = np.array(params["mean"])
            scales = np.array(params["scale"])
            X = (X - means) / scales

        # Load models
        import torch
        import joblib
        from xgboost import XGBRegressor

        # Load weights
        weights_path = os.path.join(model_dir, "weights.json")
        if os.path.exists(weights_path):
            with open(weights_path, "r") as f:
                weights = json.load(f)
        else:
            weights = {"bpnn": 0.40, "rf": 0.30, "xgb": 0.30}

        # BPNN
        from ml.models import BPNN
        input_dim = len(trained_feature_names)
        bpnn = BPNN(input_dim)
        bpnn_path = os.path.join(model_dir, "bpnn.pt")
        if os.path.exists(bpnn_path):
            bpnn.load_state_dict(torch.load(bpnn_path, map_location="cpu", weights_only=True))
        bpnn.eval()
        with torch.no_grad():
            s_bpnn_raw = float(bpnn(torch.FloatTensor(X)).numpy()[0])
        s_bpnn = max(0.0, min(100.0, s_bpnn_raw))  # Clamp to [0, 100]

        # Random Forest
        rf_path = os.path.join(model_dir, "rf.pkl")
        rf = joblib.load(rf_path) if os.path.exists(rf_path) else None
        s_rf = max(0.0, min(100.0, float(rf.predict(X)[0]))) if rf else s_bpnn

        # XGBoost
        xgb_path = os.path.join(model_dir, "xgb.json")
        xgb = XGBRegressor()
        if os.path.exists(xgb_path):
            xgb.load_model(xgb_path)
            s_xgb = max(0.0, min(100.0, float(xgb.predict(X)[0])))
        else:
            s_xgb = s_bpnn

        # Ensemble
        final_score = round(max(0.0, min(100.0,
            weights["bpnn"] * s_bpnn + weights["rf"] * s_rf + weights["xgb"] * s_xgb
        )), 2)
        grade = "A" if final_score >= 85 else "B" if final_score >= 70 else "C" if final_score >= 55 else "D"
        
        agreement = np.std([s_bpnn, s_rf, s_xgb])
        confidence_score = round(max(0.0, min(100.0, 100.0 - float(agreement) * 2)), 2)

        # 4. Update prediction record
        pred_result = await db.execute(
            select(Prediction).where(Prediction.prediction_id == prediction_id)
        )
        prediction = pred_result.scalar_one()
        prediction.bpnn_score = round(s_bpnn, 2)
        prediction.rf_score = round(s_rf, 2)
        prediction.xgb_score = round(s_xgb, 2)
        prediction.final_score = final_score
        prediction.performance_grade = grade
        prediction.status = "complete"

        # 5. Compute PFI (average across RF + XGBoost)
        pfi_results = _compute_pfi_simple(rf, xgb, X, trained_feature_names)
        for i, item in enumerate(pfi_results[:10]):
            display_name = FEATURE_DISPLAY_NAMES.get(item["feature_name"], item["feature_name"])
            pfi = PFIResult(
                prediction_id=prediction_id,
                feature_name=display_name,
                importance_score=item["importance_score"],
                rank=i + 1,
            )
            db.add(pfi)

        # 6. Generate AI insight
        pfi_top5 = pfi_results[:5]
        assessment_dict = feature_dict.copy()
        assessment_dict["quiz_tier_reached"] = assessment.quiz_tier_reached
        pred_dict = {
            "final_score": final_score,
            "performance_grade": grade,
            "bpnn_score": s_bpnn,
            "rf_score": s_rf,
            "xgb_score": s_xgb,
            "confidence": confidence_score,
            "agreement": agreement,
        }

        try:
            from integrations.groq_client import generate_insight_sync, generate_template_fallback
            insight_data = await generate_insight_sync(pred_dict, pfi_top5, assessment_dict)
        except Exception:
            from integrations.groq_client import generate_template_fallback
            insight_data = generate_template_fallback(pred_dict, pfi_top5, assessment_dict)

        raw_actions = insight_data.get("action_steps", [])
        yt_recs = ["YOUTUBE:: " + y for y in insight_data.get("youtube_recommendations", [])]
        combined_actions = raw_actions + yt_recs

        insight = Insight(
            prediction_id=prediction_id,
            student_id=student_id,
            summary=insight_data.get("summary", ""),
            strengths=insight_data.get("strengths", []),
            weaknesses=insight_data.get("weaknesses", []),
            action_steps=combined_actions,
            psych_guidance=insight_data.get("psych_guidance", ""),
            motivation=insight_data.get("motivation", ""),
        )
        db.add(insight)
        await db.commit()

    except Exception as e:
        traceback.print_exc()
        await _update_status(db, prediction_id, "failed")


async def _update_status(db: AsyncSession, prediction_id: str, status: str):
    result = await db.execute(
        select(Prediction).where(Prediction.prediction_id == prediction_id)
    )
    pred = result.scalar_one_or_none()
    if pred:
        pred.status = status
        await db.commit()


def _compute_pfi_simple(rf, xgb_model, X, feature_names):
    """Simple PFI using model feature importances (fast approximation)."""
    results = {}

    # RF feature importances
    if rf is not None and hasattr(rf, "feature_importances_"):
        for i, feat in enumerate(feature_names):
            results[feat] = results.get(feat, 0) + rf.feature_importances_[i]

    # XGBoost feature importances
    if xgb_model is not None and hasattr(xgb_model, "feature_importances_"):
        for i, feat in enumerate(feature_names):
            results[feat] = results.get(feat, 0) + xgb_model.feature_importances_[i]

    # Average and rank
    n_models = sum([
        1 for m in [rf, xgb_model]
        if m is not None and hasattr(m, "feature_importances_")
    ])
    if n_models == 0:
        n_models = 1

    ranked = sorted(
        [{"feature_name": k, "importance_score": round(v / n_models, 4)}
         for k, v in results.items()],
        key=lambda x: x["importance_score"], reverse=True
    )
    for i, item in enumerate(ranked):
        item["rank"] = i + 1
    return ranked
