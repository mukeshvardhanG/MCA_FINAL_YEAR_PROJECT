"""
Generalization Test — Train on synthetic, validate on real (unseen) data.
Evaluates cross-domain transfer performance of the ensemble model.

Usage:
    python -m research.generalization_test
"""
import numpy as np
import pandas as pd
import torch
import os
import sys
import json
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.experimental_results import load_models, predict_all, compute_metrics
from research.real_dataset import load_or_generate_real_dataset
from pipeline.pipeline import FEATURE_COLUMNS, TARGET_COLUMN


def run_generalization_test(results_dir: str = "research/results") -> dict:
    """Evaluate models trained on synthetic data against real dataset."""
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load synthetic dataset (for scaler fitting reference)
    syn_df = pd.read_csv("data/dataset2.csv")
    for col in FEATURE_COLUMNS:
        if col in syn_df.columns and syn_df[col].isnull().sum() > 0:
            syn_df[col] = syn_df[col].fillna(syn_df[col].mean())

    # 2. Load real dataset
    real_df = load_or_generate_real_dataset()
    for col in FEATURE_COLUMNS:
        if col in real_df.columns and real_df[col].isnull().sum() > 0:
            real_df[col] = real_df[col].fillna(real_df[col].mean())

    # 3. Load the SAVED scaler (fitted during training) — must match training pipeline exactly
    scaler_path = os.path.join("models", "scaler_params.json")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError("models/scaler_params.json not found — run train_models.py first")

    with open(scaler_path) as f:
        scaler_params = json.load(f)
    means  = np.array(scaler_params["mean"])
    scales = np.array(scaler_params["scale"])

    X_syn  = syn_df[FEATURE_COLUMNS].values.astype(np.float64)
    X_real = real_df[FEATURE_COLUMNS].values.astype(np.float64)
    y_real = real_df[TARGET_COLUMN].values.astype(np.float64)

    # Transform both sets with the SAME scaler that was used during training
    X_real_scaled = (X_real - means) / scales

    # Synthetic test set (same 15% held-out as pipeline.py)
    np.random.seed(42)
    indices  = np.random.permutation(len(X_syn))
    test_idx = indices[int(0.85 * len(indices)):]
    X_syn_test  = (X_syn[test_idx] - means) / scales
    y_syn_test  = syn_df[TARGET_COLUMN].values[test_idx]

    # 4. Load pre-trained models
    bpnn, rf, xgb, weights, feature_names = load_models()

    # 5. Predict on both domains
    pred_real = predict_all(bpnn, rf, xgb, weights, X_real_scaled)
    pred_syn = predict_all(bpnn, rf, xgb, weights, X_syn_test)

    # 6. Compute metrics for both domains
    results_rows = []

    for model_name in ["BPNN", "Random Forest", "XGBoost", "Ensemble"]:
        # Synthetic test performance
        syn_metrics = compute_metrics(y_syn_test, pred_syn[model_name])
        syn_metrics["Model"] = model_name
        syn_metrics["Domain"] = "Synthetic (In-Domain)"
        syn_metrics["N"] = len(y_syn_test)
        results_rows.append(syn_metrics)

        # Real data performance
        real_metrics = compute_metrics(y_real, pred_real[model_name])
        real_metrics["Model"] = model_name
        real_metrics["Domain"] = "Real (Cross-Domain)"
        real_metrics["N"] = len(y_real)
        results_rows.append(real_metrics)

    results_df = pd.DataFrame(results_rows)
    col_order = ["Model", "Domain", "N", "R²", "RMSE", "MAE", "MedAE", "MAPE%", "Max_Error"]
    results_df = results_df[col_order]
    results_df.to_csv(os.path.join(results_dir, "generalization_test.csv"), index=False)

    # 7. Compute generalization gap
    gap_rows = []
    for model_name in ["BPNN", "Random Forest", "XGBoost", "Ensemble"]:
        syn_r2 = results_df[(results_df["Model"] == model_name) & (results_df["Domain"].str.contains("Synthetic"))]["R²"].values[0]
        real_r2 = results_df[(results_df["Model"] == model_name) & (results_df["Domain"].str.contains("Real"))]["R²"].values[0]
        syn_mae = results_df[(results_df["Model"] == model_name) & (results_df["Domain"].str.contains("Synthetic"))]["MAE"].values[0]
        real_mae = results_df[(results_df["Model"] == model_name) & (results_df["Domain"].str.contains("Real"))]["MAE"].values[0]

        gap_rows.append({
            "Model": model_name,
            "Syn_R²": syn_r2,
            "Real_R²": real_r2,
            "R²_Gap": round(syn_r2 - real_r2, 4),
            "Syn_MAE": syn_mae,
            "Real_MAE": real_mae,
            "MAE_Increase": round(real_mae - syn_mae, 4),
            "Generalization": "Good" if (syn_r2 - real_r2) < 0.1 else (
                "Moderate" if (syn_r2 - real_r2) < 0.25 else "Poor"
            ),
        })

    gap_df = pd.DataFrame(gap_rows)
    gap_df.to_csv(os.path.join(results_dir, "generalization_gap.csv"), index=False)

    # 8. Grade-level analysis on real data
    real_preds = pred_real["Ensemble"]
    real_grades_true = pd.cut(y_real, bins=[0, 55, 70, 85, 100], labels=["D", "C", "B", "A"])
    real_grades_pred = pd.cut(np.clip(real_preds, 0, 100), bins=[0, 55, 70, 85, 100], labels=["D", "C", "B", "A"])
    grade_accuracy = (real_grades_true == real_grades_pred).mean()

    summary = {
        "synthetic_test_n": int(len(y_syn_test)),
        "real_test_n": int(len(y_real)),
        "ensemble_syn_r2": float(gap_df[gap_df["Model"] == "Ensemble"]["Syn_R²"].values[0]),
        "ensemble_real_r2": float(gap_df[gap_df["Model"] == "Ensemble"]["Real_R²"].values[0]),
        "ensemble_r2_gap": float(gap_df[gap_df["Model"] == "Ensemble"]["R²_Gap"].values[0]),
        "ensemble_generalization": gap_df[gap_df["Model"] == "Ensemble"]["Generalization"].values[0],
        "grade_accuracy_on_real": round(float(grade_accuracy) * 100, 1),
    }

    with open(os.path.join(results_dir, "generalization_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Print results
    print("\n" + "=" * 80)
    print("  TABLE: Generalization Test Results")
    print("=" * 80)
    print(results_df.to_string(index=False))
    print("\n  Generalization Gap:")
    print(gap_df.to_string(index=False))
    print(f"\n  Grade classification accuracy on real data: {summary['grade_accuracy_on_real']}%")

    return summary


if __name__ == "__main__":
    run_generalization_test()
