"""
Residual Analysis — Compute residuals, scatter data, and distribution stats.

residual = y_true - y_pred

Generates:
  - JSON payload for frontend scatter/histogram charts
  - residuals.csv for paper graph production

Usage:
    cd backend
    python -m research.residuals
"""
import numpy as np
import pandas as pd
import os
import sys
import json

np.random.seed(42)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.experimental_results import load_models, predict_all
from pipeline.pipeline import preprocess_bulk_dataset


def run_residual_analysis(results_dir: str = "research/results") -> dict:
    """Compute residuals for the ensemble model on the test set."""
    os.makedirs(results_dir, exist_ok=True)

    print("[Residuals] Training on SYNTHETIC dataset only — computing residuals on held-out test split...")

    # Load data (synthetic test set — strict held-out, not used in training)
    data = preprocess_bulk_dataset("data/dataset2.csv")
    X_test, y_test = data["X_test"], data["y_test"]

    # Load models
    bpnn, rf, xgb, weights, feature_names = load_models()
    predictions = predict_all(bpnn, rf, xgb, weights, X_test)

    # ── Per-model residuals ───────────────────────────────
    model_residuals = {}
    for model_name, preds in predictions.items():
        residuals = y_test - preds  # signed: positive = underpredicted
        model_residuals[model_name] = {
            "residuals":        [round(float(r), 4) for r in residuals],
            "mean":             round(float(np.mean(residuals)), 4),
            "std":              round(float(np.std(residuals)), 4),
            "skewness":         round(float(pd.Series(residuals).skew()), 4),
            "kurtosis":         round(float(pd.Series(residuals).kurtosis()), 4),
            "pct_positive":     round(float((residuals > 0).mean() * 100), 1),
            "pct_negative":     round(float((residuals < 0).mean() * 100), 1),
        }

    # ── Ensemble-specific scatter data (for frontend chart) ──
    ensemble_preds = predictions["Ensemble"]
    ensemble_residuals = y_test - ensemble_preds

    scatter_data = [
        {
            "actual":    round(float(y_test[i]), 2),
            "predicted": round(float(ensemble_preds[i]), 2),
            "residual":  round(float(ensemble_residuals[i]), 4),
        }
        for i in range(len(y_test))
    ]

    # ── Residual histogram buckets (for distribution chart) ──
    bins = np.arange(-25, 26, 5)
    hist, bin_edges = np.histogram(ensemble_residuals, bins=bins)
    histogram = [
        {
            "bucket": f"{int(bin_edges[i])} to {int(bin_edges[i+1])}",
            "count":  int(hist[i]),
            "center": round(float((bin_edges[i] + bin_edges[i+1]) / 2), 1),
        }
        for i in range(len(hist))
    ]

    # ── CSV Export (for paper) ────────────────────────────
    csv_df = pd.DataFrame({
        "y_true":            y_test,
        "ensemble_pred":     ensemble_preds,
        "residual":          ensemble_residuals,
        "bpnn_pred":         predictions["BPNN"],
        "rf_pred":           predictions["Random Forest"],
        "xgb_pred":          predictions["XGBoost"],
    })
    csv_df.to_csv(os.path.join(results_dir, "residuals.csv"), index=False)

    # ── Build final payload ───────────────────────────────
    output = {
        "n_samples":           int(len(y_test)),
        "scatter":             scatter_data,
        "histogram":           histogram,
        "model_residual_stats": {
            k: {kk: vv for kk, vv in v.items() if kk != "residuals"}
            for k, v in model_residuals.items()
        },
        "ensemble_summary": {
            "mean_residual":    round(float(np.mean(ensemble_residuals)), 4),
            "std_residual":     round(float(np.std(ensemble_residuals)), 4),
            "zero_mean_check":  abs(float(np.mean(ensemble_residuals))) < 1.0,
            "normality_note":   "Residuals should be ~N(0, σ) for unbiased model.",
        },
    }

    with open(os.path.join(results_dir, "residuals.json"), "w") as f:
        json.dump(output, f, indent=2)

    print(f"  ✔ Residuals computed: {len(y_test)} samples")
    print(f"  Mean residual (Ensemble): {output['ensemble_summary']['mean_residual']}")
    print(f"  Std  residual (Ensemble): {output['ensemble_summary']['std_residual']}")
    print(f"  CSV  saved to: {results_dir}/residuals.csv")

    return output


if __name__ == "__main__":
    run_residual_analysis()
