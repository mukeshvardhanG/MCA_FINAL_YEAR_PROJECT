"""
Student Tools Router — Goals, Badges, Notifications
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import StudentGoal, Badge, Notification, Assessment, Prediction
from app.schemas import (
    StudentGoalCreate, StudentGoalUpdate, StudentGoalResponse,
    NotificationResponse,
)

router = APIRouter(prefix="/api/student", tags=["Student Tools"])


# ═══════════════════════════════════════════════════════════
# GOALS
# ═══════════════════════════════════════════════════════════

@router.post("/goals")
async def create_goal(
    data: StudentGoalCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    goal = StudentGoal(
        student_id=user["student_id"],
        title=data.title,
        target_value=data.target_value,
        current_value=data.current_value,
        metric_type=data.metric_type,
        deadline=data.deadline,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return {"status": "ok", "goal_id": str(goal.id)}


@router.get("/goals")
async def list_goals(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StudentGoal).where(
            StudentGoal.student_id == user["student_id"]
        ).order_by(StudentGoal.created_at.desc())
    )
    goals = result.scalars().all()
    return [
        {
            "id": str(g.id),
            "title": g.title,
            "target_value": g.target_value,
            "current_value": g.current_value,
            "metric_type": g.metric_type,
            "deadline": str(g.deadline) if g.deadline else None,
            "status": g.status,
            "progress_pct": round(g.current_value / g.target_value * 100, 1)
                if g.target_value and g.target_value > 0 else None,
            "created_at": str(g.created_at),
        }
        for g in goals
    ]


@router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    data: StudentGoalUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StudentGoal).where(
            StudentGoal.id == goal_id,
            StudentGoal.student_id == user["student_id"]
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(404, "Goal not found")

    if data.current_value is not None:
        goal.current_value = data.current_value
        # Auto-complete if target reached
        if goal.target_value and goal.current_value >= goal.target_value:
            goal.status = "completed"
            # Award badge for completing a goal
            badge = Badge(
                student_id=user["student_id"],
                badge_type="goal_achieved",
                badge_name="🎯 Goal Crusher",
                description=f"Completed goal: {goal.title}",
            )
            db.add(badge)

    if data.status is not None:
        goal.status = data.status

    await db.commit()
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════
# BADGES
# ═══════════════════════════════════════════════════════════

@router.get("/badges")
async def list_badges(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Badge).where(Badge.student_id == user["student_id"])
        .order_by(Badge.earned_at.desc())
    )
    badges = result.scalars().all()
    return [
        {
            "id": str(b.id),
            "badge_type": b.badge_type,
            "badge_name": b.badge_name,
            "description": b.description,
            "earned_at": str(b.earned_at),
        }
        for b in badges
    ]


# ═══════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════

@router.get("/notifications")
async def list_notifications(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user["student_id"]
        ).order_by(Notification.created_at.desc()).limit(50)
    )
    notifs = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": str(n.created_at),
        }
        for n in notifs
    ]


@router.put("/notifications/{notif_id}/read")
async def mark_read(
    notif_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.user_id == user["student_id"]
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.get("/notifications/unread-count")
async def unread_count(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user["student_id"],
            Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    return {"unread": count}
