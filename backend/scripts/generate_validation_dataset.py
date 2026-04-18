"""
Validation Dataset Generator — dataset3.csv
Generates a held-out validation set using a different seed than dataset2 (synthetic training set).
This dataset is SEPARATE from:
  - dataset1.csv (real-world pilot records — for testing)
  - dataset2.csv (synthetic training data — for training/testing split)
  - dataset3.csv (this file — pure VALIDATION use only)

Usage: python scripts/generate_validation_dataset.py [--records 2000]
"""
import numpy as np
import pandas as pd
from scipy.stats import truncnorm
import os
import sys
import argparse

# Add parent dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def bounded_normal(mean, std, low, high, n):
    a, b = (low - mean) / std, (high - mean) / std
    return truncnorm.rvs(a, b, loc=mean, scale=std, size=n)


def generate_validation_dataset(n: int = 2000, seed: int = 999) -> pd.DataFrame:
    """
    Generate a validation dataset with a completely different seed
    to ensure no overlap with training data (dataset2, seed=42).
    """
    np.random.seed(seed)

    df = pd.DataFrame()

    # Identifiers — use VAL- prefix to distinguish from synthetic STU- prefix
    df["student_id"] = [f"VAL-{i+5001:04d}" for i in range(n)]
    df["name"] = [f"Val_Student_{i+1}" for i in range(n)]

    # Demographics — slightly different distribution for realistic drift
    df["age"] = np.random.randint(14, 23, n)
    df["gender"] = np.random.choice(["M", "F", "Other"], n, p=[0.47, 0.47, 0.06])
    df["grade_level"] = np.random.randint(8, 13, n)

    # Latent talent factor — slightly wider variance for more coverage
    talent = bounded_normal(0.5, 0.25, 0.0, 1.0, n)

    # ── Physical indicators ──
    df["running_speed_100m"] = np.round(20 - talent * 10 + np.random.normal(0, 1.2, n), 2).clip(9, 20)
    df["endurance_1500m"] = np.round(12 - talent * 6 + np.random.normal(0, 0.9, n), 2).clip(4.5, 12)
    df["flexibility_score"] = np.round(15 + talent * 40 + np.random.normal(0, 5.5, n), 2).clip(10, 60)
    df["strength_score"] = np.round(15 + talent * 70 + np.random.normal(0, 9, n), 2).clip(10, 100)
    df["bmi"] = np.round(bounded_normal(22.0, 3.8, 14, 35, n), 2)
    df["coordination_score"] = np.round(25 + talent * 65 + np.random.normal(0, 7, n), 2).clip(20, 100)
    df["reaction_time_ms"] = np.round(380 - talent * 200 + np.random.normal(0, 22, n), 2).clip(150, 400)
    df["physical_progress_index"] = np.round(-10 + talent * 25 + np.random.normal(0, 3.5, n), 2).clip(-15, 20)
    df["skill_acquisition_speed"] = np.round(2 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(1, 10)

    # ── Psychological indicators ──
    df["motivation_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["self_confidence_score"] = np.round(1.5 + talent * 7.5 + np.random.normal(0, 1.0, n), 2).clip(0, 10)
    df["stress_management_score"] = np.round(1 + talent * 7 + np.random.normal(0, 1.1, n), 2).clip(0, 10)
    df["goal_orientation_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["mental_resilience_score"] = np.round(1.5 + talent * 7 + np.random.normal(0, 1.0, n), 2).clip(0, 10)
    df["quiz_tier_reached"] = np.where(talent > 0.7, 2, np.random.choice([1, 2], n, p=[0.50, 0.50]))

    # ── Social indicators ──
    df["teamwork_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["participation_score"] = np.round(2.5 + talent * 6.5 + np.random.normal(0, 0.8, n), 2).clip(0, 10)
    df["communication_score"] = np.round(1.5 + talent * 7 + np.random.normal(0, 1.0, n), 2).clip(0, 10)
    df["leadership_score"] = np.round(1 + talent * 7.5 + np.random.normal(0, 1.1, n), 2).clip(0, 10)
    df["peer_collaboration_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["social_tier_reached"] = df["quiz_tier_reached"]

    # ── Composite target ──
    phys_sub = pd.DataFrame()
    phys_sub["sprint"] = ((20 - df["running_speed_100m"]) / 11 * 100).clip(0, 100)
    phys_sub["endurance"] = ((12 - df["endurance_1500m"]) / 7.5 * 100).clip(0, 100)
    phys_sub["flex"] = (df["flexibility_score"] / 60 * 100).clip(0, 100)
    phys_sub["strength"] = df["strength_score"].clip(0, 100)
    phys_sub["bmi_health"] = ((1 - (df["bmi"] - 21.5).abs() / 10) * 100).clip(0, 100)
    phys_sub["coord"] = df["coordination_score"].clip(0, 100)
    phys_sub["reaction"] = ((400 - df["reaction_time_ms"]) / 250 * 100).clip(0, 100)
    phys_sub["progress"] = ((df["physical_progress_index"] + 15) / 35 * 100).clip(0, 100)
    phys_sub["skill"] = (df["skill_acquisition_speed"] / 10 * 100).clip(0, 100)
    physical_avg = phys_sub.mean(axis=1)

    psych_avg = df[
        ["motivation_score", "self_confidence_score", "stress_management_score",
         "goal_orientation_score", "mental_resilience_score"]
    ].mean(axis=1) * 10

    social_avg = df[
        ["teamwork_score", "participation_score", "communication_score",
         "leadership_score", "peer_collaboration_score"]
    ].mean(axis=1) * 10

    raw_score = 0.40 * physical_avg + 0.35 * psych_avg + 0.25 * social_avg
    noise = np.clip(np.random.normal(0, 1.8, n), -3.5, 3.5)
    df["overall_pe_score"] = (raw_score + noise).clip(0, 100).round(2)

    df["performance_grade"] = pd.cut(
        df["overall_pe_score"],
        bins=[0, 55, 70, 85, 100],
        labels=["D", "C", "B", "A"],
    )

    # Metadata
    semesters = ["2024-S1", "2024-S2", "2025-S1", "2025-S2", "2026-S1"]
    df["semester_id"] = np.random.choice(semesters, n)
    df["assessment_date"] = "2026-04-01"

    # Introduce ~2.5% missing values
    np.random.seed(seed + 77)
    numeric_cols = [
        "running_speed_100m", "endurance_1500m", "flexibility_score",
        "strength_score", "coordination_score", "reaction_time_ms",
    ]
    for col in numeric_cols:
        mask = np.random.random(n) < 0.025
        df.loc[mask, col] = np.nan

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate validation PE assessment dataset (dataset3)")
    parser.add_argument("--records", type=int, default=2000, help="Number of records")
    args = parser.parse_args()

    os.makedirs("data", exist_ok=True)
    df = generate_validation_dataset(args.records)

    output_path = os.path.join("data", "dataset3.csv")
    df.to_csv(output_path, index=False)

    print(f"[OK] Generated {len(df)} VALIDATION records → {output_path}")
    print(f"     Seed: 999 (distinct from training seed=42)")
    print(f"     Split purpose: VALIDATION ONLY (never used for training)")
    print(f"     Columns: {len(df.columns)}")
    print(f"     Grade distribution:\n{df['performance_grade'].value_counts().sort_index()}")
    print(f"     Score range: {df['overall_pe_score'].min():.1f} – {df['overall_pe_score'].max():.1f}")
    print(f"     Mean score: {df['overall_pe_score'].mean():.1f}")
