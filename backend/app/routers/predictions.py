from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.core.database import get_db, async_session
from app.core.security import get_current_user
from app.models import Prediction, Assessment, PFIResult, Insight
from app.schemas import PredictionResponse, PredictionStatusResponse

router = APIRouter(prefix="/api/predict", tags=["Predictions"])


@router.post("/{assessment_id}", response_model=PredictionStatusResponse)
async def trigger_prediction(
    assessment_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify assessment exists and is complete
    result = await db.execute(
        select(Assessment).where(Assessment.assessment_id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Create pending prediction record
    prediction = Prediction(
        assessment_id=assessment_id,
        student_id=user["student_id"],
        final_score=0.0,
        status="processing",
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)

    pred_id = str(prediction.prediction_id)

    # Run prediction in background
    background_tasks.add_task(
        _run_prediction_background,
        assessment_id, user["student_id"], pred_id
    )

    return PredictionStatusResponse(
        prediction_id=pred_id,
        status="processing",
    )


async def _run_prediction_background(assessment_id: str, student_id: str, prediction_id: str):
    """Background wrapper that creates its own DB session."""
    from app.services.prediction_service import run_prediction_pipeline
    async with async_session() as db:
        await run_prediction_pipeline(assessment_id, student_id, prediction_id, db)


@router.get("/{assessment_id}/status", response_model=PredictionStatusResponse)
async def get_prediction_status(
    assessment_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.assessment_id == assessment_id,
            Prediction.student_id == user["student_id"],
        )
        .order_by(Prediction.predicted_at.desc())
    )
    prediction = result.scalars().first()
    if not prediction:
        raise HTTPException(404, "No prediction found for this assessment")

    return PredictionStatusResponse(
        prediction_id=str(prediction.prediction_id),
        status=prediction.status,
        final_score=prediction.final_score if prediction.status == "complete" else None,
        performance_grade=prediction.performance_grade if prediction.status == "complete" else None,
    )


@router.get("/history/{student_id}")
async def get_prediction_history(
    student_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Prediction)
        .where(Prediction.student_id == student_id)
        .order_by(Prediction.predicted_at.desc())
    )
    predictions = result.scalars().all()
    return [
        {
            "prediction_id": str(p.prediction_id),
            "assessment_id": str(p.assessment_id),
            "final_score": p.final_score,
            "performance_grade": p.performance_grade,
            "bpnn_score": p.bpnn_score,
            "rf_score": p.rf_score,
            "xgb_score": p.xgb_score,
            "status": p.status,
            "predicted_at": str(p.predicted_at),
        }
        for p in predictions
    ]

@router.get("/{assessment_id}/result")
async def get_prediction_result(
    assessment_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Prediction).where(Prediction.assessment_id == assessment_id))
    prediction = result.scalars().first()
    if not prediction or prediction.status != "complete":
        return {"status": "pending"}

    agreement = np.std([prediction.bpnn_score or 0, prediction.rf_score or 0, prediction.xgb_score or 0])
    confidence = round(max(0.0, min(100.0, 100.0 - float(agreement) * 2)), 2)

    pfis = await db.execute(select(PFIResult)
                            .where(PFIResult.prediction_id == str(prediction.prediction_id))
                            .order_by(PFIResult.rank))
    top_features = [p.feature_name for p in pfis.scalars().all()[:3]]

    ins = await db.execute(select(Insight).where(Insight.prediction_id == str(prediction.prediction_id)))
    insight = ins.scalar_one_or_none()

    insight_dict = {}
    if insight:
        actions = insight.action_steps or []
        real_actions = [a for a in actions if not a.startswith("YOUTUBE:: ")]
        youtube_recs = [a.replace("YOUTUBE:: ", "") for a in actions if a.startswith("YOUTUBE:: ")]
        
        insight_dict = {
            "strengths": insight.strengths or [],
            "weaknesses": insight.weaknesses or [],
            "action_steps": real_actions,
            "youtube_recommendations": youtube_recs,
            "psych_guidance": insight.psych_guidance or "",
            "motivation": insight.motivation or "",
        }

    return {
        "final_score": prediction.final_score,
        "grade": prediction.performance_grade,
        "confidence": confidence,
        "top_features": top_features,
        "insights": insight_dict
    }
