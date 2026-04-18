"""
Correlation Analysis — Pearson correlation matrix for all 21 features.

Computes correlation between all input features and the target variable.
Uses SYNTHETIC dataset ONLY for training-domain analysis (strict separation).

Outputs:
  - correlation_matrix.json (for API/frontend heatmap)
  - correlation_features.csv (for paper)

Usage:
    cd backend
    python -m research.correlation
"""
import numpy as np
import pandas as pd
import os
import sys
import json

np.random.seed(42)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.pipeline import FEATURE_COLUMNS, TARGET_COLUMN


def run_correlation_analysis(results_dir: str = "research/results") -> dict:
    """
    Compute Pearson correlation matrix across all features + target.
    Strictly uses the SYNTHETIC training dataset only.
    """
    os.makedirs(results_dir, exist_ok=True)

    print("[Correlation] Training on SYNTHETIC dataset only — computing correlation matrix...")

    # Load synthetic dataset (training domain only)
    df = pd.read_csv("data/dataset2.csv")

    # Impute missing values
    all_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    for col in all_cols:
        if col in df.columns and df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mean())

    # Use only feature columns + target for correlation
    analysis_df = df[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()

    # Compute Pearson correlation matrix
    corr_matrix = analysis_df.corr(method="pearson")

    # ── Short display names ────────────────────────────────
    display_names = {
        "running_speed_100m":    "Sprint",
        "endurance_1500m":       "Endurance",
        "flexibility_score":     "Flexibility",
        "strength_score":        "Strength",
        "bmi":                   "BMI",
        "coordination_score":    "Coordination",
        "reaction_time_ms":      "Reaction",
        "physical_progress_index": "Progress Idx",
        "skill_acquisition_speed": "Skill Acq.",
        "motivation_score":      "Motivation",
        "self_confidence_score": "Confidence",
        "stress_management_score": "Stress Mgmt",
        "goal_orientation_score": "Goal Orient.",
        "mental_resilience_score": "Resilience",
        "teamwork_score":        "Teamwork",
        "participation_score":   "Participation",
        "communication_score":   "Communication",
        "leadership_score":      "Leadership",
        "peer_collaboration_score": "Peer Collab",
        "age":                   "Age",
        "grade_level":           "Grade Level",
        TARGET_COLUMN:           "Score (Target)",
    }

    feature_labels = [display_names.get(c, c) for c in analysis_df.columns]

    # ── Build JSON matrix ──────────────────────────────────
    # Format: list of {feature, correlations: [{with, value}]}
    matrix_json = []
    for i, row_col in enumerate(analysis_df.columns):
        row_label = feature_labels[i]
        correlations = []
        for j, col_col in enumerate(analysis_df.columns):
            col_label = feature_labels[j]
            val = corr_matrix.iloc[i, j]
            correlations.append({
                "feature": col_label,
                "value":   round(float(val), 4),
            })
        matrix_json.append({
            "feature":      row_label,
            "correlations": correlations,
        })

    # ── Top correlations with target ────────────────────────
    target_corr = corr_matrix[TARGET_COLUMN].drop(TARGET_COLUMN)
    top_positive = target_corr.nlargest(5)
    top_negative = target_corr.nsmallest(5)

    top_correlations = {
        "with_target_positive": [
            {"feature": display_names.get(k, k), "correlation": round(float(v), 4)}
            for k, v in top_positive.items()
        ],
        "with_target_negative": [
            {"feature": display_names.get(k, k), "correlation": round(float(v), 4)}
            for k, v in top_negative.items()
        ],
    }

    # ── CSV Export (for paper) ────────────────────────────
    renamed = corr_matrix.copy()
    renamed.index   = feature_labels
    renamed.columns = feature_labels
    renamed.to_csv(os.path.join(results_dir, "correlation_matrix.csv"))

    # ── Build output ──────────────────────────────────────
    output = {
        "dataset":           "Synthetic (Training Domain)",
        "dataset_type":      "synthetic",
        "n_samples":         int(len(df)),
        "n_features":        len(FEATURE_COLUMNS),
        "feature_labels":    feature_labels,
        "matrix":            matrix_json,
        "top_correlations":  top_correlations,
    }

    with open(os.path.join(results_dir, "correlation_matrix.json"), "w") as f:
        json.dump(output, f, indent=2)

    print(f"  ✔ Correlation matrix: {len(analysis_df.columns)}×{len(analysis_df.columns)}")
    print(f"  Top positive correlations with target:")
    for item in top_correlations["with_target_positive"]:
        print(f"    {item['feature']}: {item['correlation']}")
    print(f"  CSV saved to: {results_dir}/correlation_matrix.csv")

    return output


if __name__ == "__main__":
    run_correlation_analysis()
