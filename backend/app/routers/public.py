from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Student, Assessment, Prediction, PFIResult, Insight
from app.schemas import PublicProfileResponse, RadarData, PFIItem

router = APIRouter(prefix="/api/public", tags=["Public Profile"])


@router.get("/profile/{student_id}", response_model=PublicProfileResponse)
async def get_public_profile(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Public profile — no auth required. Only works if student.is_public = True."""
    sid = student_id

    student_result = await db.execute(select(Student).where(Student.student_id == sid))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    if not student.is_public:
        raise HTTPException(403, "This profile is not public")

    # Latest prediction
    pred_result = await db.execute(
        select(Prediction)
        .where(Prediction.student_id == sid, Prediction.status == "complete")
        .order_by(Prediction.predicted_at.desc())
    )
    latest_pred = pred_result.scalars().first()

    grade = None
    score = None
    radar = None
    pfi_top5 = []
    ai_summary = None

    if latest_pred:
        grade = latest_pred.performance_grade
        score = latest_pred.final_score

        # Radar — 6 axes (same logic as dashboard)
        assess_result = await db.execute(
            select(Assessment).where(Assessment.assessment_id == latest_pred.assessment_id)
        )
        assessment = assess_result.scalar_one_or_none()
        if assessment:
            from app.routers.dashboard import _norm_sprint, _norm_reaction, _norm_generic, _safe_mean

            sprint_norm = _norm_sprint(assessment.running_speed_100m)
            endurance_norm = _norm_generic(assessment.endurance_1500m, 4.0, 15.0)
            endurance_norm = round(10.0 - endurance_norm, 2)
            flex_norm = _norm_generic(assessment.flexibility_score, 0, 100)
            strength_norm = _norm_generic(assessment.strength_score, 0, 100)
            bmi_norm = _norm_generic(assessment.bmi, 10.0, 40.0)
            if assessment.bmi is not None:
                bmi_norm = round(max(0, 10.0 - abs(assessment.bmi - 22.0) * 0.7), 2)
            coord_norm = _norm_generic(assessment.coordination_score, 0, 100)
            reaction_norm = _norm_reaction(assessment.reaction_time_ms)
            progress_norm = _norm_generic(assessment.physical_progress_index, -20, 25)
            skill_norm = _norm_generic(assessment.skill_acquisition_speed, 1, 10)

            phys_avg = _safe_mean([sprint_norm, endurance_norm, flex_norm, strength_norm, bmi_norm, coord_norm])
            psych_avg = _safe_mean([
                assessment.motivation_score, assessment.self_confidence_score,
                assessment.stress_management_score, assessment.goal_orientation_score,
                assessment.mental_resilience_score,
            ])
            social_avg = _safe_mean([
                assessment.teamwork_score, assessment.participation_score,
                assessment.communication_score, assessment.leadership_score,
                assessment.peer_collaboration_score,
            ])
            cognitive_avg = _safe_mean([reaction_norm, skill_norm])
            technical_avg = _safe_mean([coord_norm, sprint_norm, progress_norm])
            behavioral_avg = _safe_mean([
                assessment.motivation_score, assessment.goal_orientation_score,
                assessment.participation_score,
            ])

            radar = RadarData(
                physical_avg=phys_avg,
                psychological_avg=psych_avg,
                social_avg=social_avg,
                cognitive_avg=cognitive_avg,
                technical_avg=technical_avg,
                behavioral_avg=behavioral_avg,
            )

        # PFI top 5
        pfi_result = await db.execute(
            select(PFIResult)
            .where(PFIResult.prediction_id == latest_pred.prediction_id)
            .order_by(PFIResult.rank)
            .limit(5)
        )
        pfi_top5 = [
            PFIItem(feature_name=p.feature_name, importance_score=p.importance_score, rank=p.rank)
            for p in pfi_result.scalars().all()
        ]

        # AI summary
        insight_result = await db.execute(
            select(Insight).where(Insight.prediction_id == latest_pred.prediction_id)
        )
        insight = insight_result.scalar_one_or_none()
        if insight:
            ai_summary = insight.summary

    return PublicProfileResponse(
        name=student.name,
        performance_grade=grade,
        final_score=score,
        radar=radar,
        pfi_top5=pfi_top5,
        ai_summary=ai_summary,
    )


@router.patch("/toggle-visibility")
async def toggle_visibility(
    is_public: bool,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle public profile visibility (requires auth for own profile)."""
    sid = user["student_id"]
    student_result = await db.execute(select(Student).where(Student.student_id == sid))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")
    student.is_public = is_public
    await db.commit()
    return {"is_public": is_public}
