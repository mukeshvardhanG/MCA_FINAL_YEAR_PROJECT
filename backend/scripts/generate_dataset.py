"""
Dataset2 Generator (Synthetic Training Dataset) — student PE assessment records.
Produces all 30 required columns with realistic distributions.
Dataset Split Role: TRAINING + TEST split (80/20)
Usage: python scripts/generate_dataset.py [--records 10000]
"""
import numpy as np
import pandas as pd
from scipy.stats import truncnorm
import os
import sys
import argparse


def bounded_normal(mean, std, low, high, n):
    a, b = (low - mean) / std, (high - mean) / std
    return truncnorm.rvs(a, b, loc=mean, scale=std, size=n)


def generate_synthetic_dataset(n: int = 10000, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)

    df = pd.DataFrame()

    # Identifiers
    df["student_id"] = [f"STU-{i+1001:04d}" for i in range(n)]
    df["name"] = [f"Student_{i+1}" for i in range(n)]

    # Demographics
    df["age"] = np.random.randint(15, 22, n)
    df["gender"] = np.random.choice(["M", "F", "Other"], n, p=[0.48, 0.48, 0.04])
    df["grade_level"] = np.random.randint(9, 13, n)

    # Latent talent factor — drives correlated features across all dimensions
    talent = bounded_normal(0.5, 0.22, 0.0, 1.0, n)

    # ── Physical indicators (talent-correlated) ──
    df["running_speed_100m"] = np.round(20 - talent * 10 + np.random.normal(0, 1.0, n), 2).clip(9, 20)
    df["endurance_1500m"] = np.round(12 - talent * 6 + np.random.normal(0, 0.8, n), 2).clip(4.5, 12)
    df["flexibility_score"] = np.round(15 + talent * 40 + np.random.normal(0, 5, n), 2).clip(10, 60)
    df["strength_score"] = np.round(15 + talent * 70 + np.random.normal(0, 8, n), 2).clip(10, 100)
    df["bmi"] = np.round(bounded_normal(21.5, 3.5, 14, 35, n), 2)
    df["coordination_score"] = np.round(25 + talent * 65 + np.random.normal(0, 6, n), 2).clip(20, 100)
    df["reaction_time_ms"] = np.round(380 - talent * 200 + np.random.normal(0, 20, n), 2).clip(150, 400)
    df["physical_progress_index"] = np.round(-10 + talent * 25 + np.random.normal(0, 3, n), 2).clip(-15, 20)
    df["skill_acquisition_speed"] = np.round(2 + talent * 7 + np.random.normal(0, 0.8, n), 2).clip(1, 10)

    # ── Psychological indicators (0–10, talent-correlated) ──
    df["motivation_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.8, n), 2).clip(0, 10)
    df["self_confidence_score"] = np.round(1.5 + talent * 7.5 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["stress_management_score"] = np.round(1 + talent * 7 + np.random.normal(0, 1.0, n), 2).clip(0, 10)
    df["goal_orientation_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.8, n), 2).clip(0, 10)
    df["mental_resilience_score"] = np.round(1.5 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["quiz_tier_reached"] = np.where(talent > 0.7, 2, np.random.choice([1, 2], n, p=[0.50, 0.50]))

    # ── Social indicators (0–10, talent-correlated) ──
    df["teamwork_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.8, n), 2).clip(0, 10)
    df["participation_score"] = np.round(2.5 + talent * 6.5 + np.random.normal(0, 0.7, n), 2).clip(0, 10)
    df["communication_score"] = np.round(1.5 + talent * 7 + np.random.normal(0, 0.9, n), 2).clip(0, 10)
    df["leadership_score"] = np.round(1 + talent * 7.5 + np.random.normal(0, 1.0, n), 2).clip(0, 10)
    df["peer_collaboration_score"] = np.round(2 + talent * 7 + np.random.normal(0, 0.8, n), 2).clip(0, 10)
    df["social_tier_reached"] = df["quiz_tier_reached"]

    # ── Composite target: overall_pe_score ──
    # Physical sub-score: normalize each to 0-100, then average
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

    # Psych + Social already 0-10, scale to 0-100
    psych_avg = df[
        ["motivation_score", "self_confidence_score", "stress_management_score",
         "goal_orientation_score", "mental_resilience_score"]
    ].mean(axis=1) * 10

    social_avg = df[
        ["teamwork_score", "participation_score", "communication_score",
         "leadership_score", "peer_collaboration_score"]
    ].mean(axis=1) * 10

    # Weighted composite (with realistic human variance/noise)
    raw_score = 0.40 * physical_avg + 0.35 * psych_avg + 0.25 * social_avg
    noise = np.clip(np.random.normal(0, 1.5, n), -3, 3)
    df["overall_pe_score"] = (raw_score + noise).clip(0, 100).round(2)

    df["performance_grade"] = pd.cut(
        df["overall_pe_score"],
        bins=[0, 55, 70, 85, 100],
        labels=["D", "C", "B", "A"],
    )

    # Metadata
    semesters = ["2024-S1", "2024-S2", "2025-S1", "2025-S2"]
    df["semester_id"] = np.random.choice(semesters, n)
    df["assessment_date"] = "2026-03-14"

    # Introduce ~3% missing values for realism
    np.random.seed(seed + 1)
    numeric_cols = [
        "running_speed_100m", "endurance_1500m", "flexibility_score",
        "strength_score", "coordination_score", "reaction_time_ms",
    ]
    for col in numeric_cols:
        mask = np.random.random(n) < 0.03
        df.loc[mask, col] = np.nan

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic PE assessment dataset")
    parser.add_argument("--records", type=int, default=10000, help="Number of records")
    args = parser.parse_args()

    os.makedirs("data", exist_ok=True)
    df = generate_synthetic_dataset(args.records)

    output_path = os.path.join("data", "dataset2.csv")
    df.to_csv(output_path, index=False)

    print(f"[OK] Generated {len(df)} records → {output_path}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Grade distribution:\n{df['performance_grade'].value_counts().sort_index()}")
    print(f"   Score range: {df['overall_pe_score'].min():.1f} – {df['overall_pe_score'].max():.1f}")
    print(f"   Mean score: {df['overall_pe_score'].mean():.1f}")
