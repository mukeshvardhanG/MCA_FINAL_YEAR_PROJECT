"""
Teacher Tools Router — Attendance, Notes, Comparison, Analytics, Notifications
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import (
    Student, Assessment, Prediction, Attendance, TeacherNote,
    Notification, Class
)
from app.schemas import (
    AttendanceCreate, AttendanceBulkCreate, AttendanceResponse,
    TeacherNoteCreate, TeacherNoteResponse,
    NotificationCreate, NotificationResponse,
)

router = APIRouter(prefix="/api/teacher", tags=["Teacher Tools"])


# ─── Helper ─────────────────────────────────────────────────
async def _get_teacher_class_id(user: dict, db: AsyncSession) -> str:
    result = await db.execute(select(Class).where(Class.teacher_id == user["student_id"]))
    teacher_class = result.scalar_one_or_none()
    if not teacher_class:
        raise HTTPException(404, "No class assigned to this teacher")
    return teacher_class.id


# ═══════════════════════════════════════════════════════════
# ATTENDANCE
# ═══════════════════════════════════════════════════════════

@router.post("/attendance", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def record_attendance(
    data: AttendanceBulkCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    class_id = await _get_teacher_class_id(user, db)
    created = 0
    for rec in data.records:
        attendance = Attendance(
            student_id=rec.student_id,
            class_id=class_id,
            date=rec.date,
            status=rec.status,
        )
        db.add(attendance)
        created += 1
    await db.commit()
    return {"status": "ok", "created": created}


@router.get("/attendance", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def get_attendance(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    student_id: str = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    class_id = await _get_teacher_class_id(user, db)
    query = select(Attendance, Student.name).join(
        Student, Attendance.student_id == Student.student_id
    ).where(Attendance.class_id == class_id)

    if date_from:
        query = query.where(Attendance.date >= date_from)
    if date_to:
        query = query.where(Attendance.date <= date_to)
    if student_id:
        query = query.where(Attendance.student_id == student_id)

    query = query.order_by(Attendance.date.desc())
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": str(r.Attendance.id),
            "student_id": str(r.Attendance.student_id),
            "student_name": r.name,
            "date": str(r.Attendance.date),
            "status": r.Attendance.status,
        }
        for r in rows
    ]


@router.get("/attendance/summary", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def get_attendance_summary(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Attendance rates per student with performance correlation."""
    class_id = await _get_teacher_class_id(user, db)

    # Get all students in class
    students_res = await db.execute(select(Student).where(Student.class_id == class_id))
    students = students_res.scalars().all()

    summary = []
    for s in students:
        # Count attendance
        total_res = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == s.student_id,
                Attendance.class_id == class_id
            )
        )
        total = total_res.scalar() or 0

        present_res = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == s.student_id,
                Attendance.class_id == class_id,
                Attendance.status == "present"
            )
        )
        present = present_res.scalar() or 0
        rate = round(present / total * 100, 1) if total > 0 else 0

        # Get latest score
        pred_res = await db.execute(
            select(Prediction.final_score).where(
                Prediction.student_id == s.student_id,
                Prediction.status == "complete"
            ).order_by(Prediction.predicted_at.desc()).limit(1)
        )
        score = pred_res.scalar()

        summary.append({
            "student_id": str(s.student_id),
            "name": s.name,
            "total_days": total,
            "present_days": present,
            "attendance_rate": rate,
            "latest_score": score,
        })

    return summary


# ═══════════════════════════════════════════════════════════
# TEACHER NOTES / FEEDBACK
# ═══════════════════════════════════════════════════════════

@router.post("/notes/{student_id}", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def add_note(
    student_id: str,
    data: TeacherNoteCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    class_id = await _get_teacher_class_id(user, db)
    # Verify student in class
    student_res = await db.execute(select(Student).where(Student.student_id == student_id))
    student = student_res.scalar_one_or_none()
    if not student or student.class_id != class_id:
        raise HTTPException(403, "Student not in your class")

    note = TeacherNote(
        student_id=student_id,
        teacher_id=user["student_id"],
        content=data.content,
        category=data.category,
    )
    db.add(note)

    # Also create notification for the student
    notif = Notification(
        user_id=student_id,
        title="New feedback from your teacher",
        message=data.content[:100] + ("..." if len(data.content) > 100 else ""),
        type="info",
    )
    db.add(notif)

    await db.commit()
    return {"status": "ok", "note_id": str(note.id)}


@router.get("/notes/{student_id}", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def get_notes(
    student_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TeacherNote, Student.name).join(
            Student, TeacherNote.teacher_id == Student.student_id
        ).where(
            TeacherNote.student_id == student_id
        ).order_by(TeacherNote.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(r.TeacherNote.id),
            "content": r.TeacherNote.content,
            "category": r.TeacherNote.category,
            "teacher_name": r.name,
            "created_at": str(r.TeacherNote.created_at),
        }
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════
# STUDENT COMPARISON
# ═══════════════════════════════════════════════════════════

@router.get("/compare", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def compare_students(
    student_a: str = Query(...),
    student_b: str = Query(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Side-by-side comparison of two students."""
    class_id = await _get_teacher_class_id(user, db)

    async def _get_student_data(sid):
        s_res = await db.execute(select(Student).where(Student.student_id == sid))
        s = s_res.scalar_one_or_none()
        if not s or s.class_id != class_id:
            raise HTTPException(403, f"Student {sid} not in your class")

        assess_res = await db.execute(
            select(Assessment).where(Assessment.student_id == sid)
            .order_by(Assessment.created_at.desc()).limit(1)
        )
        a = assess_res.scalar_one_or_none()

        pred_res = await db.execute(
            select(Prediction).where(
                Prediction.student_id == sid, Prediction.status == "complete"
            ).order_by(Prediction.predicted_at.desc()).limit(1)
        )
        p = pred_res.scalar_one_or_none()

        # Attendance rate
        total_att = await db.execute(
            select(func.count(Attendance.id)).where(Attendance.student_id == sid)
        )
        present_att = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == sid, Attendance.status == "present"
            )
        )
        total = total_att.scalar() or 0
        present = present_att.scalar() or 0

        return {
            "student_id": str(s.student_id),
            "name": s.name,
            "age": s.age,
            "gender": s.gender,
            "grade_level": s.grade_level,
            "overall_score": p.final_score if p else None,
            "grade": p.performance_grade if p else None,
            "physical": {
                "sprint_100m": a.running_speed_100m if a else None,
                "endurance_1500m": a.endurance_1500m if a else None,
                "strength": a.strength_score if a else None,
                "bmi": a.bmi if a else None,
                "reaction_time": a.reaction_time_ms if a else None,
                "plank_hold": a.plank_hold_seconds if a else None,
                "breath_hold": a.breath_hold_seconds if a else None,
            },
            "psychological": {
                "motivation": a.motivation_score if a else None,
                "self_confidence": a.self_confidence_score if a else None,
                "stress_management": a.stress_management_score if a else None,
                "goal_orientation": a.goal_orientation_score if a else None,
                "mental_resilience": a.mental_resilience_score if a else None,
            },
            "social": {
                "teamwork": a.teamwork_score if a else None,
                "participation": a.participation_score if a else None,
                "communication": a.communication_score if a else None,
                "leadership": a.leadership_score if a else None,
                "peer_collaboration": a.peer_collaboration_score if a else None,
            },
            "attendance_rate": round(present / total * 100, 1) if total > 0 else None,
        }

    data_a = await _get_student_data(student_a)
    data_b = await _get_student_data(student_b)
    return {"student_a": data_a, "student_b": data_b}


# ═══════════════════════════════════════════════════════════
# CLASS ANALYTICS (REAL DATA)
# ═══════════════════════════════════════════════════════════

@router.get("/analytics/detailed", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def get_detailed_analytics(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Full class analytics with distribution, trends, and top/bottom performers."""
    class_id = await _get_teacher_class_id(user, db)

    students_res = await db.execute(select(Student).where(Student.class_id == class_id))
    students = students_res.scalars().all()
    student_ids = [s.student_id for s in students]

    if not student_ids:
        return {"message": "No students in class", "data": {}}

    # Get all completed predictions for class students
    preds_res = await db.execute(
        select(Prediction, Student.name).join(
            Student, Prediction.student_id == Student.student_id
        ).where(
            Prediction.student_id.in_(student_ids),
            Prediction.status == "complete"
        ).order_by(Prediction.predicted_at.desc())
    )
    all_preds = preds_res.all()

    # Latest scores per student
    latest_scores = {}
    for row in all_preds:
        sid = row.Prediction.student_id
        if sid not in latest_scores:
            latest_scores[sid] = {
                "name": row.name,
                "score": row.Prediction.final_score,
                "grade": row.Prediction.performance_grade,
            }

    scores = [v["score"] for v in latest_scores.values() if v["score"] is not None]

    # Score distribution buckets
    distribution = {"A (85+)": 0, "B (70-84)": 0, "C (55-69)": 0, "D (<55)": 0}
    for s in scores:
        if s >= 85: distribution["A (85+)"] += 1
        elif s >= 70: distribution["B (70-84)"] += 1
        elif s >= 55: distribution["C (55-69)"] += 1
        else: distribution["D (<55)"] += 1

    # Top/bottom performers
    sorted_students = sorted(latest_scores.items(), key=lambda x: x[1]["score"] or 0, reverse=True)
    top_5 = [{"name": v["name"], "score": v["score"], "grade": v["grade"]}
             for _, v in sorted_students[:5]]
    bottom_5 = [{"name": v["name"], "score": v["score"], "grade": v["grade"]}
                for _, v in sorted_students[-5:]]

    # Attendance-performance correlation
    attendance_perf = []
    for sid, data in latest_scores.items():
        total_att = await db.execute(
            select(func.count(Attendance.id)).where(Attendance.student_id == sid)
        )
        present_att = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == sid, Attendance.status == "present"
            )
        )
        total = total_att.scalar() or 0
        present = present_att.scalar() or 0
        rate = round(present / total * 100, 1) if total > 0 else None
        if rate is not None and data["score"] is not None:
            attendance_perf.append({
                "name": data["name"],
                "attendance_rate": rate,
                "score": data["score"],
            })

    # Performance by grade level
    grade_perf = {}
    for s in students:
        gl = s.grade_level or 0
        if s.student_id in latest_scores:
            score = latest_scores[s.student_id]["score"]
            if score is not None:
                grade_perf.setdefault(gl, []).append(score)
    grade_averages = {
        str(k): round(sum(v) / len(v), 1)
        for k, v in sorted(grade_perf.items())
    }

    return {
        "total_students": len(students),
        "assessed_students": len(latest_scores),
        "class_average": round(sum(scores) / len(scores), 1) if scores else 0,
        "distribution": distribution,
        "top_performers": top_5,
        "bottom_performers": bottom_5,
        "attendance_performance": attendance_perf,
        "grade_level_averages": grade_averages,
    }


# ═══════════════════════════════════════════════════════════
# NOTIFICATIONS / REMINDERS
# ═══════════════════════════════════════════════════════════

@router.post("/notify", dependencies=[Depends(require_roles(["teacher", "admin"]))])
async def send_notification(
    data: NotificationCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send notification to a specific student or all class students."""
    if data.user_id == "all":
        class_id = await _get_teacher_class_id(user, db)
        students_res = await db.execute(select(Student).where(Student.class_id == class_id))
        students = students_res.scalars().all()
        for s in students:
            notif = Notification(
                user_id=s.student_id,
                title=data.title,
                message=data.message,
                type=data.type,
            )
            db.add(notif)
        await db.commit()
        return {"status": "ok", "sent_to": len(students)}
    else:
        notif = Notification(
            user_id=data.user_id,
            title=data.title,
            message=data.message,
            type=data.type,
        )
        db.add(notif)
        await db.commit()
        return {"status": "ok", "sent_to": 1}
