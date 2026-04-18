from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Assessment
from app.schemas import AssessmentCreate, AssessmentResponse

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post("/", response_model=dict)
async def create_assessment(
    req: AssessmentCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    assessment = Assessment(
        student_id=user["student_id"],
        semester_id=req.semester_id,
        running_speed_100m=req.running_speed_100m,
        endurance_1500m=req.endurance_1500m,
        strength_score=req.strength_score,
        bmi=req.bmi,
        reaction_time_ms=req.reaction_time_ms,
        push_ups=req.push_ups,
        squats=req.squats,
        sit_ups=req.sit_ups,
        height_cm=req.height_cm,
        weight_kg=req.weight_kg,
        flexibility_score=req.flexibility_score,
        coordination_score=req.coordination_score,
        physical_progress_index=req.physical_progress_index,
        skill_acquisition_speed=req.skill_acquisition_speed,
        plank_hold_seconds=req.plank_hold_seconds,
        breath_hold_seconds=req.breath_hold_seconds,
        locked=False,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return {"assessment_id": str(assessment.assessment_id)}


@router.get("/", response_model=list)
async def get_assessments(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == user["student_id"])
        .order_by(Assessment.assessment_date.desc())
    )
    assessments = result.scalars().all()
    return [
        {
            "assessment_id": str(a.assessment_id),
            "student_id": str(a.student_id),
            "assessment_date": str(a.assessment_date),
            "semester_id": a.semester_id,
            "is_complete": a.is_complete,
            "running_speed_100m": a.running_speed_100m,
            "endurance_1500m": a.endurance_1500m,
            "flexibility_score": a.flexibility_score,
            "strength_score": a.strength_score,
            "bmi": a.bmi,
            "coordination_score": a.coordination_score,
            "reaction_time_ms": a.reaction_time_ms,
            "push_ups": a.push_ups,
            "squats": a.squats,
            "sit_ups": a.sit_ups,
            "height_cm": a.height_cm,
            "weight_kg": a.weight_kg,
            "plank_hold_seconds": a.plank_hold_seconds,
            "breath_hold_seconds": a.breath_hold_seconds,
            "quiz_tier_reached": a.quiz_tier_reached,
            "social_tier_reached": a.social_tier_reached,
        }
        for a in assessments
    ]
