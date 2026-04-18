from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import Student, Assessment, Class, Prediction, QuizSession
from app.schemas import AssessmentCreate, StudentReportResponse
from app.routers.dashboard import get_student_report

router = APIRouter(prefix="/api/teacher", tags=["Teacher Portal"])


async def get_teacher_class_id(user: dict, db: AsyncSession):
    # Retrieve the class ID where this user is the teacher
    result = await db.execute(select(Class).where(Class.teacher_id == user["student_id"]))
    teacher_class = result.scalar_one_or_none()
    if not teacher_class:
        raise HTTPException(status_code=404, detail="No class assigned to this teacher")
    return teacher_class.id


async def verify_student_in_class(student_id: str, class_id: str, db: AsyncSession):
    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.class_id != class_id:
        raise HTTPException(status_code=403, detail="Student not in your class")
    return student


@router.get("/class", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def get_class_overview(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    class_id = await get_teacher_class_id(user, db)
    
    # Get all students in this class
    students_res = await db.execute(
        select(Student).where(Student.class_id == class_id)
    )
    students = students_res.scalars().all()
    
    student_list = []
    
    for s in students:
        # Get their latest assessment and prediction
        assess_res = await db.execute(
            select(Assessment)
            .where(Assessment.student_id == s.student_id)
            .order_by(Assessment.created_at.desc())
            .limit(1)
        )
        assessment = assess_res.scalar_one_or_none()
        
        pred_res = await db.execute(
            select(Prediction)
            .where(Prediction.student_id == s.student_id, Prediction.status == "complete")
            .order_by(Prediction.predicted_at.desc())
            .limit(1)
        )
        prediction = pred_res.scalar_one_or_none()
        
        student_list.append({
            "id": s.student_id,
            "name": s.name,
            "age": s.age,
            "gender": s.gender,
            "grade": str(s.grade_level) if s.grade_level else None,
            "overall_score": prediction.final_score if prediction else None,
            "performance_grade": prediction.performance_grade if prediction else None,
            "last_assessment": str(assessment.assessment_date) if assessment else None,
            "status": "Complete" if (assessment and assessment.is_complete) else ("Pending" if assessment else "Not Started"),
        })

    scored = [s["overall_score"] for s in student_list if s["overall_score"] is not None]

    return {
        "class_id": class_id,
        "total_students": len(students),
        "students": student_list,
        "avg_score": round(sum(scored) / max(1, len(scored)), 2) if scored else 0,
        "completion_rate": round(len([s for s in student_list if s["status"] == "Complete"]) / max(1, len(students)) * 100, 1)
    }


@router.get("/student/{student_id}", response_model=StudentReportResponse, dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def get_teacher_student_view(
    student_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    class_id = await get_teacher_class_id(user, db)
    await verify_student_in_class(student_id, class_id, db)
    
    # Reuse dashboard route logic since the UI is identical read-only
    return await get_student_report(student_id, user, db)


@router.put("/student/{student_id}/metrics", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def update_student_metrics(
    student_id: str,
    data: AssessmentCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    class_id = await get_teacher_class_id(user, db)
    await verify_student_in_class(student_id, class_id, db)
    
    # Find active assessment to update
    assess_res = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == student_id, Assessment.semester_id == data.semester_id)
        .order_by(Assessment.created_at.desc())
    )
    assessment = assess_res.scalars().first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found for this semester to update")
        
    assessment.running_speed_100m = data.running_speed_100m
    assessment.endurance_1500m = data.endurance_1500m
    assessment.flexibility_score = data.flexibility_score
    assessment.strength_score = data.strength_score
    assessment.bmi = data.bmi
    assessment.coordination_score = data.coordination_score
    assessment.reaction_time_ms = data.reaction_time_ms
    assessment.physical_progress_index = data.physical_progress_index
    assessment.skill_acquisition_speed = data.skill_acquisition_speed
    assessment.plank_hold_seconds = data.plank_hold_seconds
    assessment.breath_hold_seconds = data.breath_hold_seconds
    
    await db.commit()
    return {"status": "ok", "message": "Metrics updated successfully"}

