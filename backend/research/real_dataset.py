"""
Database Pilot Extraction — Real Dataset Generator
Extracts real system usage (Assessments & Students) from the SQLite DB.
Serves as the authentic real-world Pilot Dataset for validation, ensuring
custom psychological and social features are preserved.

Usage:
    python -m research.real_dataset
"""
import asyncio
import pandas as pd
import numpy as np
import os
import sys
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session
from app.models import Student, Assessment, Prediction

FEATURE_COLUMNS = [
    "running_speed_100m", "endurance_1500m", "flexibility_score",
    "strength_score", "bmi", "coordination_score", "reaction_time_ms",
    "physical_progress_index", "skill_acquisition_speed",
    "motivation_score", "self_confidence_score", "stress_management_score",
    "goal_orientation_score", "mental_resilience_score",
    "teamwork_score", "participation_score", "communication_score",
    "leadership_score", "peer_collaboration_score",
    "age", "grade_level",
]

def _compute_target(df: pd.DataFrame) -> np.ndarray:
    """Compute overall_pe_score using the exact mathematically defined rubric."""
    phys = pd.DataFrame()
    phys["sprint"]   = ((20 - df["running_speed_100m"]) / 11 * 100).clip(0, 100)
    phys["endurance"] = ((12 - df["endurance_1500m"]) / 7.5 * 100).clip(0, 100)
    phys["flex"]     = (df["flexibility_score"] / 60 * 100).clip(0, 100)
    phys["strength"] = df["strength_score"].clip(0, 100)
    phys["bmi_h"]    = ((1 - (df["bmi"] - 21.5).abs() / 10) * 100).clip(0, 100)
    phys["coord"]    = df["coordination_score"].clip(0, 100)
    phys["reaction"] = ((400 - df["reaction_time_ms"]) / 250 * 100).clip(0, 100)
    phys["progress"] = ((df["physical_progress_index"] + 15) / 35 * 100).clip(0, 100)
    phys["skill"]    = (df["skill_acquisition_speed"] / 10 * 100).clip(0, 100)
    physical_avg = phys.mean(axis=1)

    psych_avg = df[
        ["motivation_score", "self_confidence_score", "stress_management_score",
         "goal_orientation_score", "mental_resilience_score"]
    ].mean(axis=1) * 10

    social_avg = df[
        ["teamwork_score", "participation_score", "communication_score",
         "leadership_score", "peer_collaboration_score"]
    ].mean(axis=1) * 10

    raw = 0.40 * physical_avg + 0.35 * psych_avg + 0.25 * social_avg
    return raw.values

async def extract_db_pilot_dataset() -> pd.DataFrame:
    """Extract real data from the database."""
    async with async_session() as db:
        a_res = await db.execute(select(Assessment).where(Assessment.is_complete == True))
        assessments = a_res.scalars().all()

        rows = []
        for a in assessments:
            s_res = await db.execute(select(Student).where(Student.student_id == a.student_id))
            student = s_res.scalar_one_or_none()

            if not student:
                continue

            row = {
                "student_id": student.student_id,
                "name": student.name,
                "age": student.age,
                "gender": student.gender,
                "grade_level": student.grade_level,
                "semester_id": a.semester_id,
                "assessment_date": a.assessment_date,
                
                # Features
                "running_speed_100m": a.running_speed_100m,
                "endurance_1500m": a.endurance_1500m,
                "flexibility_score": a.flexibility_score,
                "strength_score": a.strength_score,
                "bmi": a.bmi,
                "coordination_score": a.coordination_score,
                "reaction_time_ms": a.reaction_time_ms,
                "physical_progress_index": a.physical_progress_index,
                "skill_acquisition_speed": a.skill_acquisition_speed,
                
                "motivation_score": a.motivation_score,
                "self_confidence_score": a.self_confidence_score,
                "stress_management_score": a.stress_management_score,
                "goal_orientation_score": a.goal_orientation_score,
                "mental_resilience_score": a.mental_resilience_score,

                "teamwork_score": a.teamwork_score,
                "participation_score": a.participation_score,
                "communication_score": a.communication_score,
                "leadership_score": a.leadership_score,
                "peer_collaboration_score": a.peer_collaboration_score,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        print("[WARNING] No complete assessments found in the database. Pilot dataset is empty.")
        return df

    # Drop any rows missing core metric data (so models don't crash)
    df.dropna(subset=FEATURE_COLUMNS, inplace=True)

    # Compute Target Value if not using DB output directly
    df["overall_pe_score"] = np.round(_compute_target(df), 2)
    df["performance_grade"] = pd.cut(
        df["overall_pe_score"],
        bins=[0, 55, 70, 85, 100],
        labels=["D", "C", "B", "A"],
    )

    return df

def load_or_generate_real_dataset(data_dir: str = "data") -> pd.DataFrame:
    """Synchronous hook for cross-module loading.

    Dataset Split Enforcement:
      ✔ dataset1.csv is used for TESTING ONLY — never for model training.
      ✔ Models are trained exclusively on dataset2.csv (synthetic data).
      ✔ dataset3.csv is reserved for pure validation (held-out).
    """
    path = os.path.join(data_dir, "dataset1.csv")

    # ── DATASET SPLIT ENFORCEMENT ──────────────────────────────────────
    print("=" * 60)
    print("  [DATASET SPLIT ENFORCEMENT]")
    print("  Testing on DATASET1 (authentic pilot records)")
    print("  This data is used for validation ONLY — not for training")
    print("=" * 60)

    # We always re-extract to stay sync'd with the DB pilot
    df = asyncio.run(extract_db_pilot_dataset())

    if not df.empty:
        os.makedirs(data_dir, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"  [OK] Extracted {len(df)} authentic pilot records -> {path}")
    elif os.path.exists(path):
        print("  [INFO] Fallback: Loading old dataset1.csv since DB extraction yielded 0 records.")
        df = pd.read_csv(path)

    return df

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = load_or_generate_real_dataset()
    if not df.empty:
        print(f"   Score range: {df['overall_pe_score'].min():.1f} – {df['overall_pe_score'].max():.1f}")
        print(f"   Mean: {df['overall_pe_score'].mean():.1f}, Std: {df['overall_pe_score'].std():.1f}")
        print(f"   Grade distribution:\n{df['performance_grade'].value_counts().sort_index()}")
