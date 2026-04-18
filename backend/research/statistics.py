"""
Statistical Validation — Bootstrap Confidence Intervals + Welch's T-Test.

Provides rigorous statistical proof that model differences are significant.
Uses bootstrap resampling (N=1000) to compute CI for R² per model.
Uses Welch's t-test to compare XGBoost vs Ensemble error distributions.

Usage:
    cd backend
    python -m research.statistics
"""
import numpy as np
import pandas as pd
import scipy.stats as stats
import os
import sys
import json

np.random.seed(42)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.experimental_results import load_models, predict_all
from pipeline.pipeline import preprocess_bulk_dataset
from sklearn.metrics import r2_score, mean_absolute_error


def _bootstrap_r2(y_true: np.ndarray, y_pred: np.ndarray,
                   n_boot: int = 1000, ci: float = 0.95) -> dict:
    """Bootstrap confidence interval for R² score."""
    boot_r2 = []
    n = len(y_true)
    rng = np.random.RandomState(42)

    for _ in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        try:
            r2 = r2_score(y_true[idx], y_pred[idx])
            boot_r2.append(r2)
        except Exception:
            pass

    boot_r2 = np.array(boot_r2)
    alpha = (1.0 - ci) / 2.0

    return {
        "mean":      round(float(np.mean(boot_r2)),         4),
        "std":       round(float(np.std(boot_r2)),          4),
        "ci_lower":  round(float(np.percentile(boot_r2, alpha * 100)),       4),
        "ci_upper":  round(float(np.percentile(boot_r2, (1 - alpha) * 100)), 4),
        "ci_pct":    int(ci * 100),
        "n_boot":    n_boot,
    }


def _welch_ttest(errors_a: np.ndarray, errors_b: np.ndarray,
                 label_a: str, label_b: str) -> dict:
    """Welch's t-test comparing absolute error distributions of two models."""
    abs_a = np.abs(errors_a)
    abs_b = np.abs(errors_b)
    t_stat, p_val = stats.ttest_ind(abs_a, abs_b, equal_var=False)
    return {
        "model_a":        label_a,
        "model_b":        label_b,
        "mean_error_a":   round(float(np.mean(abs_a)), 4),
        "mean_error_b":   round(float(np.mean(abs_b)), 4),
        "t_statistic":    round(float(t_stat), 4),
        "p_value":        round(float(p_val), 6),
        "significant":    bool(p_val < 0.05),
        "interpretation": (
            f"Statistically significant difference (p={p_val:.4f}<0.05): "
            f"{label_a} and {label_b} have different error distributions."
        ) if p_val < 0.05 else (
            f"No statistically significant difference (p={p_val:.4f}≥0.05): "
            f"{label_a} and {label_b} have similar error distributions."
        ),
    }


def run_statistical_validation(n_boot: int = 1000,
                                results_dir: str = "research/results") -> dict:
    """
    Run bootstrap CI analysis and Welch's t-test.
    Training data: SYNTHETIC only.
    Test set:      held-out split of synthetic (strict separation).
    """
    os.makedirs(results_dir, exist_ok=True)

    print("[Statistics] Training on SYNTHETIC dataset only — running bootstrap validation...")

    # Load data and models
    data = preprocess_bulk_dataset("data/dataset2.csv")
    X_test, y_test = data["X_test"], data["y_test"]

    bpnn, rf, xgb, weights, feature_names = load_models()
    predictions = predict_all(bpnn, rf, xgb, weights, X_test)

    # ── Bootstrap CI per model ────────────────────────────
    print(f"  Running bootstrap (n={n_boot}) confidence intervals...")
    model_stats = {}
    rows = []

    for model_name, preds in predictions.items():
        ci_data = _bootstrap_r2(y_test, preds, n_boot=n_boot)
        mae_val = round(float(mean_absolute_error(y_test, preds)), 4)
        r2_val  = round(float(r2_score(y_test, preds)), 4)

        model_stats[model_name] = {
            "r2":          r2_val,
            "mae":         mae_val,
            "bootstrap":   ci_data,
        }
        rows.append({
            "Model":      model_name,
            "R²":         r2_val,
            "MAE":        mae_val,
            "Boot_Mean":  ci_data["mean"],
            "Boot_Std":   ci_data["std"],
            "CI_Lower":   ci_data["ci_lower"],
            "CI_Upper":   ci_data["ci_upper"],
            "CI_Pct":     f"{ci_data['ci_pct']}%",
        })

    stats_df = pd.DataFrame(rows)
    stats_df.to_csv(os.path.join(results_dir, "statistical_validation.csv"), index=False)

    # ── Welch's T-Test: XGBoost vs Ensemble ──────────────
    print("  Running Welch's t-test: XGBoost vs Ensemble...")
    errors_xgb      = predictions["XGBoost"]   - y_test
    errors_ensemble = predictions["Ensemble"]  - y_test
    errors_rf       = predictions["Random Forest"] - y_test

    ttest_xgb_ensemble = _welch_ttest(errors_xgb, errors_ensemble,
                                       "XGBoost", "Ensemble")
    ttest_rf_ensemble  = _welch_ttest(errors_rf,  errors_ensemble,
                                       "Random Forest", "Ensemble")

    # ── Final output ──────────────────────────────────────
    output = {
        "dataset_type":   "synthetic",
        "n_test_samples": int(len(y_test)),
        "n_bootstrap":    n_boot,
        "model_statistics": model_stats,
        "t_tests": {
            "xgb_vs_ensemble":  ttest_xgb_ensemble,
            "rf_vs_ensemble":   ttest_rf_ensemble,
        },
    }

    with open(os.path.join(results_dir, "statistical_validation.json"), "w") as f:
        json.dump(output, f, indent=2)

    # ── Print summary ─────────────────────────────────────
    print("\n" + "=" * 80)
    print("  STATISTICAL VALIDATION RESULTS")
    print("=" * 80)
    print(stats_df.to_string(index=False))
    print(f"\n  T-Test (XGBoost vs Ensemble): {ttest_xgb_ensemble['interpretation']}")
    print(f"  T-Test (RF vs Ensemble):      {ttest_rf_ensemble['interpretation']}")

    return output


if __name__ == "__main__":
    run_statistical_validation()
