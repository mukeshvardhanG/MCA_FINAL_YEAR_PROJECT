"""
PFI Validation — Multi-run Permutation Feature Importance consistency analysis.
Runs PFI N times with different random seeds and measures ranking stability.

Usage:
    python -m research.pfi_validation
"""
import numpy as np
import pandas as pd
import os
import sys
import json
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.experimental_results import load_models
from pipeline.pipeline import preprocess_bulk_dataset, FEATURE_COLUMNS

DISPLAY_NAMES = {
    "running_speed_100m": "Sprint 100m",
    "endurance_1500m": "Endurance 1500m",
    "flexibility_score": "Flexibility",
    "strength_score": "Strength",
    "bmi": "BMI",
    "coordination_score": "Coordination",
    "reaction_time_ms": "Reaction Time",
    "physical_progress_index": "Progress Index",
    "skill_acquisition_speed": "Skill Acquisition",
    "motivation_score": "Motivation",
    "self_confidence_score": "Self-Confidence",
    "stress_management_score": "Stress Mgmt",
    "goal_orientation_score": "Goal Orientation",
    "mental_resilience_score": "Resilience",
    "teamwork_score": "Teamwork",
    "participation_score": "Participation",
    "communication_score": "Communication",
    "leadership_score": "Leadership",
    "peer_collaboration_score": "Peer Collab",
    "age": "Age",
    "grade_level": "Grade Level",
}


def run_pfi_multi(n_runs: int = 5, n_repeats: int = 10,
                  results_dir: str = "research/results") -> pd.DataFrame:
    """Run PFI multiple times and analyze consistency."""
    os.makedirs(results_dir, exist_ok=True)

    # Load data and models
    data = preprocess_bulk_dataset("data/dataset2.csv")
    X_test, y_test = data["X_test"], data["y_test"]
    bpnn, rf, xgb, weights, feature_names = load_models()

    # Run PFI n_runs times with different seeds
    all_importances = {feat: [] for feat in feature_names}
    all_rankings = {feat: [] for feat in feature_names}

    for run_idx in range(n_runs):
        seed = 42 + run_idx * 7
        print(f"  PFI run {run_idx + 1}/{n_runs} (seed={seed})...")

        run_importances = {}

        # RF PFI
        pfi_rf = permutation_importance(
            rf, X_test, y_test,
            n_repeats=n_repeats, random_state=seed,
            scoring="neg_mean_absolute_error",
        )
        for i, feat in enumerate(feature_names):
            run_importances[feat] = run_importances.get(feat, 0) + pfi_rf.importances_mean[i]

        # XGB PFI
        pfi_xgb = permutation_importance(
            xgb, X_test, y_test,
            n_repeats=n_repeats, random_state=seed,
            scoring="neg_mean_absolute_error",
        )
        for i, feat in enumerate(feature_names):
            run_importances[feat] += pfi_xgb.importances_mean[i]

        # Average across models
        for feat in feature_names:
            run_importances[feat] /= 2
            all_importances[feat].append(run_importances[feat])

        # Compute rankings for this run
        ranked = sorted(run_importances.items(), key=lambda x: x[1], reverse=True)
        for rank, (feat, _) in enumerate(ranked):
            all_rankings[feat].append(rank + 1)

    # Aggregate results
    rows = []
    for feat in feature_names:
        imps = all_importances[feat]
        ranks = all_rankings[feat]
        rows.append({
            "Feature": feat,
            "Display_Name": DISPLAY_NAMES.get(feat, feat),
            "Mean_Importance": round(float(np.mean(imps)), 6),
            "Std_Importance": round(float(np.std(imps)), 6),
            "CV%": round(float(np.std(imps) / max(abs(np.mean(imps)), 1e-10) * 100), 2),
            "Mean_Rank": round(float(np.mean(ranks)), 1),
            "Rank_Std": round(float(np.std(ranks)), 2),
            "Min_Rank": int(np.min(ranks)),
            "Max_Rank": int(np.max(ranks)),
            "Rank_Range": int(np.max(ranks) - np.min(ranks)),
        })

    results_df = pd.DataFrame(rows).sort_values("Mean_Importance", ascending=False).reset_index(drop=True)
    results_df.index = results_df.index + 1
    results_df.index.name = "Final_Rank"
    results_df.to_csv(os.path.join(results_dir, "pfi_validation.csv"))

    # Stability metrics
    top5_features = results_df.head(5)["Feature"].tolist()
    mean_rank_std = results_df["Rank_Std"].mean()
    max_rank_range = results_df["Rank_Range"].max()
    stable_features = int((results_df["Rank_Range"] <= 2).sum())

    stability = {
        "n_runs": n_runs,
        "n_repeats_per_run": n_repeats,
        "top5_features": top5_features,
        "mean_rank_std": float(round(mean_rank_std, 2)),
        "max_rank_range": int(max_rank_range),
        "stable_features_pct": float(round(stable_features / len(feature_names) * 100, 1)),
        "interpretation": (
            "High stability" if mean_rank_std < 1.5
            else "Moderate stability" if mean_rank_std < 3.0
            else "Low stability"
        ),
    }
    with open(os.path.join(results_dir, "pfi_stability.json"), "w") as f:
        json.dump(stability, f, indent=2)

    # Print results
    print("\n" + "=" * 80)
    print(f"  TABLE: PFI Consistency Analysis ({n_runs} runs)")
    print("=" * 80)
    display_cols = ["Display_Name", "Mean_Importance", "Std_Importance", "CV%", "Mean_Rank", "Rank_Range"]
    print(results_df[display_cols].head(10).to_string())
    print(f"\n  Stability: {stability['interpretation']} (mean rank σ = {mean_rank_std:.2f})")
    print(f"  Top 5 consistent features: {', '.join(top5_features)}")

    return results_df


if __name__ == "__main__":
    run_pfi_multi()
