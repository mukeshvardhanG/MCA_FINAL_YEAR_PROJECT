"""
Force-generate predictions for seeded users so their dashboard populates immediately.
Also seeds Teacher + Admin accounts and multi-semester history for each demo student.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import random
from datetime import date
from sqlalchemy import select, text
from app.core.database import async_session, init_db
from app.core.security import hash_password
from app.models import Student, Assessment, Prediction, Class
from app.services.prediction_service import run_prediction_pipeline
import uuid

# ── Semester definitions for multi-semester trend ─────────────
SEMESTERS = [
    ("2024-S1", date(2024, 3, 15)),
    ("2024-S2", date(2024, 9, 15)),
    ("2025-S1", date(2025, 3, 15)),
    ("2025-S2", date(2025, 9, 15)),
]

def _random_assessment_data(semester_index=0):
    """Generate plausible physical/psych/social scores.
       Later semesters show slight improvement (simulating real progress)."""
    improvement = semester_index * 0.3  # slight upward trend
    def clamp(val, lo, hi):
        return round(max(lo, min(hi, val)), 2)
    return {
        "running_speed_100m": clamp(random.uniform(12.0, 16.0) - improvement * 0.2, 9.0, 25.0),
        "endurance_1500m": clamp(random.uniform(6.0, 10.0) - improvement * 0.1, 4.0, 15.0),
        "flexibility_score": clamp(random.uniform(25, 65) + improvement * 2, 0, 100),
        "strength_score": clamp(random.uniform(30, 70) + improvement * 2, 0, 100),
        "bmi": clamp(random.uniform(18.0, 26.0), 10.0, 40.0),
        "coordination_score": clamp(random.uniform(40, 80) + improvement * 2, 0, 100),
        "reaction_time_ms": clamp(random.uniform(180, 350) - improvement * 5, 100, 500),
        "physical_progress_index": clamp(improvement * 2 + random.uniform(-2, 3), -20, 25),
        "skill_acquisition_speed": clamp(random.uniform(4, 8) + improvement * 0.2, 1, 10),
        # Psychological (0-10)
        "motivation_score": clamp(random.uniform(5.0, 8.5) + improvement * 0.2, 0, 10),
        "self_confidence_score": clamp(random.uniform(4.5, 8.0) + improvement * 0.2, 0, 10),
        "stress_management_score": clamp(random.uniform(4.0, 7.5) + improvement * 0.1, 0, 10),
        "goal_orientation_score": clamp(random.uniform(5.0, 8.0) + improvement * 0.2, 0, 10),
        "mental_resilience_score": clamp(random.uniform(4.5, 7.5) + improvement * 0.1, 0, 10),
        "quiz_tier_reached": 2,
        # Social (0-10)
        "teamwork_score": clamp(random.uniform(5.0, 8.5) + improvement * 0.2, 0, 10),
        "participation_score": clamp(random.uniform(5.5, 9.0) + improvement * 0.2, 0, 10),
        "communication_score": clamp(random.uniform(5.0, 8.0) + improvement * 0.1, 0, 10),
        "leadership_score": clamp(random.uniform(4.0, 7.5) + improvement * 0.2, 0, 10),
        "peer_collaboration_score": clamp(random.uniform(5.0, 8.0) + improvement * 0.1, 0, 10),
        "social_tier_reached": 2,
        "is_complete": True,
    }


async def main():
    random.seed(42)  # reproducible demo data

    await init_db()  # Ensure database tables are created

    async with async_session() as db:
        # ── 0. Add 'role' column if missing (SQLite ALTER TABLE) ──
        try:
            await db.execute(text("ALTER TABLE students ADD COLUMN role VARCHAR(20) DEFAULT 'student'"))
            await db.commit()
            print("✅ Added 'role' column to students table.")
        except Exception:
            await db.rollback()

        try:
            await db.execute(text("ALTER TABLE students ADD COLUMN class_id VARCHAR(36)"))
            await db.commit()
            print("✅ Added 'class_id' column to students table.")
        except Exception:
            await db.rollback()

        # ── 1. Seed Teacher & Admin accounts ─────────────────────
        teacher_id = None
        for email, name, role, password in [
            ("teacher@pe-assessment.com", "Ms. Sarah Thompson (Teacher)", "teacher", "teacher123"),
            ("admin@pe-assessment.com", "System Admin", "admin", "admin123"),
        ]:
            existing = await db.execute(select(Student).where(Student.email == email))
            existing_account = existing.scalar_one_or_none()
            if existing_account:
                print(f"⏭️  {email} already exists, skipping.")
                # Ensure role is set
                await db.execute(
                    text("UPDATE students SET role = :role WHERE email = :email"),
                    {"role": role, "email": email}
                )
                await db.commit()
                if role == "teacher":
                    teacher_id = existing_account.student_id
                continue

            account = Student(
                name=name,
                email=email,
                password_hash=hash_password(password),
                age=30,
                gender="F" if "Teacher" in name else "Other",
                grade_level=12,
                role=role,
            )
            db.add(account)
            await db.commit()
            print(f"✅ Created {role} account: {email} / {password}")
            if role == "teacher":
                teacher_id = account.student_id

        # Ensure teacher has a class
        class_id = None
        if teacher_id:
            existing_class = await db.execute(select(Class).where(Class.teacher_id == teacher_id))
            teacher_class = existing_class.scalar_one_or_none()
            if teacher_class:
                class_id = teacher_class.id
                print("⏭️  Teacher class already exists, skipping.")
            else:
                new_class = Class(
                    name="Web Apps 101",
                    teacher_id=teacher_id,
                    semester="2025-S1"
                )
                db.add(new_class)
                await db.commit()
                class_id = new_class.id
                print("✅ Created demo class for teacher.")

        # ── 2. Get demo student accounts ─────────────────────────
        users = await db.execute(
            select(Student).where(Student.email.like("demo%@pe-assessment.com"))
        )
        students = users.scalars().all()
        print(f"\nFound {len(students)} demo student(s).")

        for student in students:
            # Ensure role is set to student and assigned to teacher's class
            await db.execute(
                text("UPDATE students SET role = 'student', class_id = :cid WHERE student_id = :sid"),
                {"sid": student.student_id, "cid": class_id}
            )
            await db.commit()

            # ── 3. Create multi-semester assessments ──────────────
            for sem_idx, (semester_id, assess_date) in enumerate(SEMESTERS):
                # Check if assessment already exists for this semester
                existing_assess = await db.execute(
                    select(Assessment).where(
                        Assessment.student_id == student.student_id,
                        Assessment.semester_id == semester_id
                    )
                )
                if existing_assess.scalars().first():
                    print(f"  ⏭️  {student.email} already has {semester_id}, skipping.")
                    continue

                data = _random_assessment_data(sem_idx)
                assessment = Assessment(
                    student_id=student.student_id,
                    assessment_date=assess_date,
                    semester_id=semester_id,
                    **data
                )
                db.add(assessment)
                await db.commit()
                await db.refresh(assessment)

                # Create prediction and run pipeline
                pred_id = str(uuid.uuid4())
                prediction = Prediction(
                    prediction_id=pred_id,
                    assessment_id=assessment.assessment_id,
                    student_id=student.student_id,
                    final_score=0.0,
                    status="processing",
                )
                db.add(prediction)
                await db.commit()

                print(f"  🔄 {student.email} → {semester_id}: generating prediction...")
                await run_prediction_pipeline(
                    assessment.assessment_id, student.student_id, pred_id, db
                )

        print("\n✅ All demo users updated with multi-semester data, PFI, and AI Insights!")
        print("✅ Teacher and Admin accounts seeded.")
        print("\n📋 Login credentials:")
        print("   Student:  demo1@pe-assessment.com / demo123 (or existing password)")
        print("   Teacher:  teacher@pe-assessment.com / teacher123")
        print("   Admin:    admin@pe-assessment.com / admin123")

if __name__ == "__main__":
    asyncio.run(main())
