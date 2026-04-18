"""
Seed Database Script — loads synthetic CSV data into the database
for testing the dashboard with pre-existing students and predictions.
Usage: python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from app.core.database import async_session, engine, Base
from app.models import Student, Assessment
from app.core.security import hash_password


async def main():
    # Create tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    csv_path = os.path.join("data", "dataset2.csv")
    if not os.path.exists(csv_path):
        print(f"❌ Dataset not found at {csv_path}. Run generate_dataset.py first.")
        return

    df = pd.read_csv(csv_path)
    print(f"Seeding {len(df)} records into database...")

    async with async_session() as db:
        # Create 10 demo students with full assessment data
        count = 0
        skipped = 0
        for _, row in df.head(10).iterrows():
            email = f"demo{count+1}@pe-assessment.com"

            # Skip if already exists
            from sqlalchemy import select
            existing = await db.execute(select(Student).where(Student.email == email))
            if existing.scalar_one_or_none():
                skipped += 1
                count += 1
                continue

            student = Student(
                name=row.get("name", f"Demo Student {count+1}"),
                email=email,
                password_hash=hash_password("demo123"),
                age=int(row.get("age", 18)),
                gender=row.get("gender", "M"),
                grade_level=int(row.get("grade_level", 10)),
                is_public=True,
            )
            db.add(student)
            await db.flush()

            assessment = Assessment(
                student_id=student.student_id,
                semester_id=row.get("semester_id", "2025-S1"),
                running_speed_100m=row.get("running_speed_100m"),
                endurance_1500m=row.get("endurance_1500m"),
                flexibility_score=row.get("flexibility_score"),
                strength_score=row.get("strength_score"),
                bmi=row.get("bmi"),
                coordination_score=row.get("coordination_score"),
                reaction_time_ms=row.get("reaction_time_ms"),
                physical_progress_index=row.get("physical_progress_index", 0),
                skill_acquisition_speed=row.get("skill_acquisition_speed", 5),
                motivation_score=row.get("motivation_score"),
                self_confidence_score=row.get("self_confidence_score"),
                stress_management_score=row.get("stress_management_score"),
                goal_orientation_score=row.get("goal_orientation_score"),
                mental_resilience_score=row.get("mental_resilience_score"),
                teamwork_score=row.get("teamwork_score"),
                participation_score=row.get("participation_score"),
                communication_score=row.get("communication_score"),
                leadership_score=row.get("leadership_score"),
                peer_collaboration_score=row.get("peer_collaboration_score"),
                quiz_tier_reached=int(row.get("quiz_tier_reached", 1)),
                social_tier_reached=int(row.get("quiz_tier_reached", 1)),
                is_complete=True,
            )
            db.add(assessment)
            count += 1

        await db.commit()

    print(f"✅ Seeded {count - skipped} new students ({skipped} already existed).")
    print(f"   Login with: demo1@pe-assessment.com / demo123")
    print(f"   ... through demo10@pe-assessment.com / demo123")


if __name__ == "__main__":
    asyncio.run(main())
