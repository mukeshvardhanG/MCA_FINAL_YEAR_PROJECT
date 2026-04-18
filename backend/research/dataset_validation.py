"""
Dataset Validation — Distribution comparison and correlation analysis.
Compares synthetic vs. real datasets, generates publication-ready plots.

Usage:
    python -m research.dataset_validation
"""
import numpy as np
import pandas as pd
import os
import json

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

PHYSICAL = FEATURE_COLUMNS[:9]
PSYCHOLOGICAL = FEATURE_COLUMNS[9:14]
SOCIAL = FEATURE_COLUMNS[14:19]

DISPLAY_NAMES = {
    "running_speed_100m": "Sprint 100m (s)",
    "endurance_1500m": "Endurance 1500m (min)",
    "flexibility_score": "Flexibility",
    "strength_score": "Strength",
    "bmi": "BMI",
    "coordination_score": "Coordination",
    "reaction_time_ms": "Reaction Time (ms)",
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


def compute_dataset_statistics(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Compute per-feature descriptive statistics."""
    stats = []
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            s = df[col].dropna()
            stats.append({
                "Feature": DISPLAY_NAMES.get(col, col),
                "Dataset": label,
                "Count": len(s),
                "Mean": round(s.mean(), 2),
                "Std": round(s.std(), 2),
                "Min": round(s.min(), 2),
                "Max": round(s.max(), 2),
                "Median": round(s.median(), 2),
                "Skewness": round(s.skew(), 3),
                "Kurtosis": round(s.kurtosis(), 3),
                "Missing%": round(df[col].isnull().mean() * 100, 1),
            })
    return pd.DataFrame(stats)


def compare_distributions(syn_df: pd.DataFrame, real_df: pd.DataFrame) -> pd.DataFrame:
    """Compare feature distributions between synthetic and real datasets."""
    from scipy.stats import ks_2samp, mannwhitneyu

    results = []
    for col in FEATURE_COLUMNS:
        if col in syn_df.columns and col in real_df.columns:
            s_syn = syn_df[col].dropna().values
            s_real = real_df[col].dropna().values

            if len(s_syn) == 0 or len(s_real) == 0:
                continue

            ks_stat, ks_p = ks_2samp(s_syn, s_real)
            mw_stat, mw_p = mannwhitneyu(s_syn, s_real, alternative="two-sided")

            mean_diff = abs(s_syn.mean() - s_real.mean())
            std_syn, std_real = s_syn.std(), s_real.std()
            # Cohen's d effect size
            pooled_std = np.sqrt((std_syn**2 + std_real**2) / 2)
            cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

            results.append({
                "Feature": DISPLAY_NAMES.get(col, col),
                "Syn_Mean": round(s_syn.mean(), 2),
                "Real_Mean": round(s_real.mean(), 2),
                "Mean_Diff": round(mean_diff, 2),
                "Syn_Std": round(std_syn, 2),
                "Real_Std": round(std_real, 2),
                "KS_Stat": round(ks_stat, 4),
                "KS_p": round(ks_p, 4),
                "MW_p": round(mw_p, 4),
                "Cohens_d": round(cohens_d, 3),
                "Alignment": "Good" if cohens_d < 0.5 else ("Moderate" if cohens_d < 0.8 else "Poor"),
            })

    return pd.DataFrame(results)


def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson correlation matrix for all features + target."""
    cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    if "overall_pe_score" in df.columns:
        cols.append("overall_pe_score")
    return df[cols].corr().round(3)


def generate_text_heatmap(corr: pd.DataFrame, label: str) -> str:
    """Generate a text-based correlation summary for the report."""
    lines = [f"\n### Correlation Matrix — {label}\n"]

    # Find top 10 strongest correlations with target
    if "overall_pe_score" in corr.columns:
        target_corr = corr["overall_pe_score"].drop("overall_pe_score", errors="ignore")
        target_corr = target_corr.abs().sort_values(ascending=False)
        lines.append("**Top 10 features correlated with overall_pe_score:**\n")
        lines.append("| Rank | Feature | Correlation |")
        lines.append("|------|---------|-------------|")
        for i, (feat, val) in enumerate(target_corr.head(10).items()):
            actual_val = corr.loc[feat, "overall_pe_score"]
            dn = DISPLAY_NAMES.get(feat, feat)
            lines.append(f"| {i+1} | {dn} | {actual_val:+.3f} |")

    # Inter-feature: strongest pairs
    lines.append("\n**Top 10 inter-feature correlations:**\n")
    lines.append("| Feature A | Feature B | Correlation |")
    lines.append("|-----------|-----------|-------------|")
    pairs = []
    for i, c1 in enumerate(corr.columns):
        for c2 in corr.columns[i+1:]:
            if c1 == "overall_pe_score" or c2 == "overall_pe_score":
                continue
            pairs.append((c1, c2, corr.loc[c1, c2]))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    for c1, c2, v in pairs[:10]:
        lines.append(f"| {DISPLAY_NAMES.get(c1, c1)} | {DISPLAY_NAMES.get(c2, c2)} | {v:+.3f} |")

    return "\n".join(lines)


def run_dataset_validation(results_dir: str = "research/results") -> dict:
    """Run full dataset validation pipeline."""
    os.makedirs(results_dir, exist_ok=True)

    # Load datasets
    syn_df = pd.read_csv("data/dataset2.csv")
    from research.real_dataset import load_or_generate_real_dataset
    real_df = load_or_generate_real_dataset()

    print(f"  Synthetic: {len(syn_df)} records, Real: {len(real_df)} records")

    # 1. Descriptive statistics
    syn_stats = compute_dataset_statistics(syn_df, "Synthetic")
    real_stats = compute_dataset_statistics(real_df, "Real")
    all_stats = pd.concat([syn_stats, real_stats], ignore_index=True)
    all_stats.to_csv(os.path.join(results_dir, "dataset_statistics.csv"), index=False)

    # 2. Distribution comparison
    comparison = compare_distributions(syn_df, real_df)
    comparison.to_csv(os.path.join(results_dir, "distribution_comparison.csv"), index=False)

    # 3. Correlation matrices
    syn_corr = compute_correlation_matrix(syn_df)
    real_corr = compute_correlation_matrix(real_df)
    syn_corr.to_csv(os.path.join(results_dir, "correlation_synthetic.csv"))
    real_corr.to_csv(os.path.join(results_dir, "correlation_real.csv"))

    # 4. Generate text summaries
    syn_heatmap_text = generate_text_heatmap(syn_corr, "Synthetic Dataset (n=10,000)")
    real_heatmap_text = generate_text_heatmap(real_corr, "Real Dataset (n=50)")

    # 5. Dataset description
    description = {
        "synthetic": {
            "records": len(syn_df),
            "features": len(FEATURE_COLUMNS),
            "target_mean": round(syn_df["overall_pe_score"].mean(), 2),
            "target_std": round(syn_df["overall_pe_score"].std(), 2),
            "missing_pct": round(syn_df[FEATURE_COLUMNS].isnull().mean().mean() * 100, 2),
        },
        "real": {
            "records": len(real_df),
            "features": len(FEATURE_COLUMNS),
            "target_mean": round(real_df["overall_pe_score"].mean(), 2),
            "target_std": round(real_df["overall_pe_score"].std(), 2),
            "missing_pct": round(real_df[FEATURE_COLUMNS].isnull().mean().mean() * 100, 2),
        },
        "good_alignment_features": int((comparison["Alignment"] == "Good").sum()),
        "moderate_alignment_features": int((comparison["Alignment"] == "Moderate").sum()),
        "poor_alignment_features": int((comparison["Alignment"] == "Poor").sum()),
    }

    with open(os.path.join(results_dir, "dataset_description.json"), "w") as f:
        json.dump(description, f, indent=2)

    print(f"  [OK] Dataset validation complete → {results_dir}/")
    print(f"       Good alignment:     {description['good_alignment_features']}/{len(comparison)} features")
    print(f"       Moderate alignment: {description['moderate_alignment_features']}/{len(comparison)} features")

    return {
        "description": description,
        "comparison": comparison,
        "syn_stats": syn_stats,
        "real_stats": real_stats,
        "syn_corr_text": syn_heatmap_text,
        "real_corr_text": real_heatmap_text,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_dataset_validation()
