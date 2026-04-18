"""
Export Router — PDF and Excel report generation
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io
import json

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import Student, Assessment, Prediction, PFIResult, Insight, Attendance
from sqlalchemy import func

router = APIRouter(prefix="/api/export", tags=["Export"])


async def _build_student_report_data(student_id: str, db: AsyncSession) -> dict:
    """Gather all data needed for a student report."""
    s_res = await db.execute(select(Student).where(Student.student_id == student_id))
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    # Latest assessment
    a_res = await db.execute(
        select(Assessment).where(Assessment.student_id == student_id)
        .order_by(Assessment.created_at.desc()).limit(1)
    )
    assessment = a_res.scalar_one_or_none()

    # Latest prediction
    p_res = await db.execute(
        select(Prediction).where(
            Prediction.student_id == student_id, Prediction.status == "complete"
        ).order_by(Prediction.predicted_at.desc()).limit(1)
    )
    prediction = p_res.scalar_one_or_none()

    # Insight
    insight = None
    if prediction:
        i_res = await db.execute(
            select(Insight).where(Insight.prediction_id == prediction.prediction_id)
        )
        insight = i_res.scalar_one_or_none()

    return {
        "student": student,
        "assessment": assessment,
        "prediction": prediction,
        "insight": insight,
    }


@router.get("/report/{student_id}")
async def export_report(
    student_id: str,
    format: str = Query(default="json", pattern="^(json|excel|csv)$"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export a single student's report in JSON, Excel/CSV format."""
    data = await _build_student_report_data(student_id, db)
    s = data["student"]
    a = data["assessment"]
    p = data["prediction"]
    ins = data["insight"]

    report = {
        "Student Name": s.name,
        "Age": s.age,
        "Gender": s.gender,
        "Grade Level": s.grade_level,
        "Assessment Date": str(a.assessment_date) if a else "N/A",
        "100m Sprint (s)": a.running_speed_100m if a else None,
        "1500m Endurance (min)": a.endurance_1500m if a else None,
        "Strength Score": a.strength_score if a else None,
        "BMI": a.bmi if a else None,
        "Reaction Time (ms)": a.reaction_time_ms if a else None,
        "Plank Hold (s)": a.plank_hold_seconds if a else None,
        "Breath Hold (s)": a.breath_hold_seconds if a else None,
        "Motivation": a.motivation_score if a else None,
        "Self-Confidence": a.self_confidence_score if a else None,
        "Stress Management": a.stress_management_score if a else None,
        "Goal Orientation": a.goal_orientation_score if a else None,
        "Mental Resilience": a.mental_resilience_score if a else None,
        "Teamwork": a.teamwork_score if a else None,
        "Participation": a.participation_score if a else None,
        "Communication": a.communication_score if a else None,
        "Leadership": a.leadership_score if a else None,
        "Peer Collaboration": a.peer_collaboration_score if a else None,
        "Overall Score": p.final_score if p else None,
        "Grade": p.performance_grade if p else None,
        "BPNN Score": p.bpnn_score if p else None,
        "RF Score": p.rf_score if p else None,
        "XGBoost Score": p.xgb_score if p else None,
        "AI Summary": ins.summary if ins else None,
        "Strengths": json.dumps(ins.strengths) if ins and ins.strengths else None,
        "Weaknesses": json.dumps(ins.weaknesses) if ins and ins.weaknesses else None,
        "Action Steps": json.dumps(ins.action_steps) if ins and ins.action_steps else None,
    }

    if format == "json":
        return report

    elif format in ("excel", "csv"):
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(report.keys())
        writer.writerow(report.values())
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={s.name.replace(' ', '_')}_report.csv"}
        )


@router.get("/class/{class_id}", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def export_class(
    class_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export entire class data as CSV."""
    import csv

    students_res = await db.execute(
        select(Student).where(Student.class_id == class_id)
    )
    students = students_res.scalars().all()

    headers = [
        "Name", "Age", "Gender", "Grade Level", "Overall Score", "Grade",
        "Sprint 100m", "Endurance 1500m", "Strength", "BMI", "Reaction Time",
        "Plank Hold", "Breath Hold",
        "Motivation", "Self-Confidence", "Stress Mgmt", "Goal Orientation", "Mental Resilience",
        "Teamwork", "Participation", "Communication", "Leadership", "Peer Collaboration",
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for s in students:
        a_res = await db.execute(
            select(Assessment).where(Assessment.student_id == s.student_id)
            .order_by(Assessment.created_at.desc()).limit(1)
        )
        a = a_res.scalar_one_or_none()
        p_res = await db.execute(
            select(Prediction).where(
                Prediction.student_id == s.student_id, Prediction.status == "complete"
            ).order_by(Prediction.predicted_at.desc()).limit(1)
        )
        p = p_res.scalar_one_or_none()

        writer.writerow([
            s.name, s.age, s.gender, s.grade_level,
            p.final_score if p else "", p.performance_grade if p else "",
            a.running_speed_100m if a else "", a.endurance_1500m if a else "",
            a.strength_score if a else "", a.bmi if a else "",
            a.reaction_time_ms if a else "",
            a.plank_hold_seconds if a else "", a.breath_hold_seconds if a else "",
            a.motivation_score if a else "", a.self_confidence_score if a else "",
            a.stress_management_score if a else "", a.goal_orientation_score if a else "",
            a.mental_resilience_score if a else "",
            a.teamwork_score if a else "", a.participation_score if a else "",
            a.communication_score if a else "", a.leadership_score if a else "",
            a.peer_collaboration_score if a else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=class_{class_id}_report.csv"}
    )
