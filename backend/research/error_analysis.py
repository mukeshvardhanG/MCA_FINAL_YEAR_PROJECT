"""
Error Analysis — Identify best/worst predictions and analyze feature influence.
Diagnoses systematic error patterns in the ensemble model.

Usage:
    python -m research.error_analysis
"""
import numpy as np
import pandas as pd
import torch
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.experimental_results import load_models, predict_all
from pipeline.pipeline import preprocess_bulk_dataset, FEATURE_COLUMNS

DISPLAY_NAMES = {
    "running_speed_100m": "Sprint 100m",
    "endurance_1500m": "Endurance 1500m",
    "flexibility_score": "Flexibility",
    "strength_score": "Strength",
    "bmi": "BMI",
    "coordination_score": "Coordination",
    "reaction_time_ms": "Reaction Time",
    "physical_progress_index": "Progress Index",
    "skill_acquisition_speed": "Skill Acquisition",
    "motivation_score": "Motivation",
    "self_confidence_score": "Self-Confidence",
    "stress_management_score": "Stress Mgmt",
    "goal_orientation_score": "Goal Orientation",
    "mental_resilience_score": "Resilience",
    "teamwork_score": "Teamwork",
    "participation_score": "Participation",
    "communication_score": "Communication",
    "leadership_score": "Leadership",
    "peer_collaboration_score": "Peer Collab",
    "age": "Age",
    "grade_level": "Grade Level",
}


def run_error_analysis(top_k: int = 10, results_dir: str = "research/results") -> dict:
    """Analyze best and worst predictions to identify error patterns."""
    os.makedirs(results_dir, exist_ok=True)

    # Load data
    data = preprocess_bulk_dataset("data/dataset2.csv")
    X_test, y_test = data["X_test"], data["y_test"]
    bpnn, rf, xgb, weights, feature_names = load_models()

    predictions = predict_all(bpnn, rf, xgb, weights, X_test)

    # Ensemble errors
    p_ensemble = predictions["Ensemble"]
    errors = p_ensemble - y_test
    abs_errors = np.abs(errors)

    # Build analysis dataframe
    analysis_df = pd.DataFrame(X_test, columns=feature_names)
    analysis_df["y_true"] = y_test
    analysis_df["y_pred"] = p_ensemble
    analysis_df["error"] = errors
    analysis_df["abs_error"] = abs_errors
    analysis_df["bpnn_pred"] = predictions["BPNN"]
    analysis_df["rf_pred"] = predictions["Random Forest"]
    analysis_df["xgb_pred"] = predictions["XGBoost"]
    analysis_df["model_disagreement"] = np.std(
        np.column_stack([predictions["BPNN"], predictions["Random Forest"], predictions["XGBoost"]]),
        axis=1,
    )

    # ── Best and worst predictions ──
    best_idx = np.argsort(abs_errors)[:top_k]
    worst_idx = np.argsort(abs_errors)[-top_k:][::-1]

    best_df = analysis_df.iloc[best_idx][
        ["y_true", "y_pred", "error", "abs_error", "model_disagreement"]
    ].reset_index(drop=True)
    worst_df = analysis_df.iloc[worst_idx][
        ["y_true", "y_pred", "error", "abs_error", "model_disagreement"]
    ].reset_index(drop=True)

    best_df.to_csv(os.path.join(results_dir, "best_predictions.csv"), index=False)
    worst_df.to_csv(os.path.join(results_dir, "worst_predictions.csv"), index=False)

    # ── Error distribution by score range ──
    bins = [0, 30, 50, 70, 85, 100]
    labels = ["0-30", "30-50", "50-70", "70-85", "85-100"]
    analysis_df["score_range"] = pd.cut(analysis_df["y_true"], bins=bins, labels=labels)
    error_by_range = analysis_df.groupby("score_range", observed=True).agg(
        Count=("abs_error", "count"),
        Mean_AbsError=("abs_error", "mean"),
        Median_AbsError=("abs_error", "median"),
        Max_AbsError=("abs_error", "max"),
        Mean_Disagreement=("model_disagreement", "mean"),
    ).round(3)
    error_by_range.to_csv(os.path.join(results_dir, "error_by_score_range.csv"))

    # ── Feature influence in worst predictions ──
    # Compare feature means of worst predictions vs full test set
    influence_rows = []
    for feat in feature_names:
        full_mean = analysis_df[feat].mean()
        full_std = analysis_df[feat].std()
        worst_mean = analysis_df.iloc[worst_idx][feat].mean()
        best_mean = analysis_df.iloc[best_idx][feat].mean()

        z_worst = (worst_mean - full_mean) / full_std if full_std > 0 else 0
        z_best = (best_mean - full_mean) / full_std if full_std > 0 else 0

        influence_rows.append({
            "Feature": DISPLAY_NAMES.get(feat, feat),
            "Test_Mean": round(full_mean, 3),
            "Worst_Mean": round(worst_mean, 3),
            "Best_Mean": round(best_mean, 3),
            "Z_Worst": round(z_worst, 3),
            "Z_Best": round(z_best, 3),
            "Deviation_Dir": "High" if z_worst > 0.5 else ("Low" if z_worst < -0.5 else "Normal"),
        })

    influence_df = pd.DataFrame(influence_rows)
    influence_df = influence_df.sort_values("Z_Worst", key=abs, ascending=False)
    influence_df.to_csv(os.path.join(results_dir, "feature_influence_errors.csv"), index=False)

    # ── Summary statistics ──
    summary = {
        "total_test_samples": int(len(y_test)),
        "mean_absolute_error": round(float(abs_errors.mean()), 4),
        "median_absolute_error": round(float(np.median(abs_errors)), 4),
        "std_error": round(float(errors.std()), 4),
        "error_skewness": round(float(pd.Series(errors).skew()), 4),
        "pct_within_5pts": round(float((abs_errors < 5).mean() * 100), 1),
        "pct_within_10pts": round(float((abs_errors < 10).mean() * 100), 1),
        "worst_error": round(float(abs_errors.max()), 2),
        "best_error": round(float(abs_errors.min()), 4),
        "mean_model_disagreement": round(float(analysis_df["model_disagreement"].mean()), 3),
        "worst_top_deviating_features": influence_df.head(3)["Feature"].tolist(),
    }

    with open(os.path.join(results_dir, "error_analysis_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Print results
    print("\n" + "=" * 80)
    print("  ERROR ANALYSIS RESULTS")
    print("=" * 80)
    print(f"\n  Mean Abs Error: {summary['mean_absolute_error']}")
    print(f"  Within ±5 pts:  {summary['pct_within_5pts']}%")
    print(f"  Within ±10 pts: {summary['pct_within_10pts']}%")
    print(f"  Worst error:    {summary['worst_error']}")
    print(f"\n  Error by score range:")
    print(error_by_range.to_string())
    print(f"\n  Top features deviating in worst predictions: {summary['worst_top_deviating_features']}")

    return summary


if __name__ == "__main__":
    run_error_analysis()
