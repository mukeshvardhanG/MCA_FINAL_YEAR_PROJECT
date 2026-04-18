"""
Experimental Results Module — Compute RMSE, MAE, R² for each model + ensemble.
Generates paper-ready comparison tables and data for charts.

Usage:
    python -m research.experimental_results
"""
import numpy as np
import pandas as pd
import torch
import joblib
import json
import os
import sys
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, \
    explained_variance_score, median_absolute_error
from xgboost import XGBRegressor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.models import BPNN
from pipeline.pipeline import preprocess_bulk_dataset, FEATURE_COLUMNS


def load_models(model_dir: str = "models"):
    """Load all three trained models and ensemble weights."""
    with open(os.path.join(model_dir, "feature_names.json")) as f:
        feature_names = json.load(f)
    with open(os.path.join(model_dir, "weights.json")) as f:
        weights = json.load(f)

    input_dim = len(feature_names)
    bpnn = BPNN(input_dim)
    bpnn.load_state_dict(
        torch.load(os.path.join(model_dir, "bpnn.pt"), map_location="cpu", weights_only=True)
    )
    bpnn.eval()

    rf = joblib.load(os.path.join(model_dir, "rf.pkl"))

    xgb = XGBRegressor()
    xgb.load_model(os.path.join(model_dir, "xgb.json"))

    return bpnn, rf, xgb, weights, feature_names


def predict_all(bpnn, rf, xgb, weights, X: np.ndarray) -> dict:
    """Run all models and ensemble on feature matrix X."""
    bpnn.eval()
    with torch.no_grad():
        p_bpnn = bpnn(torch.FloatTensor(X)).numpy()
    p_rf = rf.predict(X)
    p_xgb = xgb.predict(X)

    p_ensemble = (
        weights["bpnn"] * p_bpnn
        + weights["rf"] * p_rf
        + weights["xgb"] * p_xgb
    )

    return {
        "BPNN": p_bpnn,
        "Random Forest": p_rf,
        "XGBoost": p_xgb,
        "Ensemble": p_ensemble,
    }


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute comprehensive regression metrics."""
    return {
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "R²": round(float(r2_score(y_true, y_pred)), 4),
        "MedAE": round(float(median_absolute_error(y_true, y_pred)), 4),
        "Explained_Var": round(float(explained_variance_score(y_true, y_pred)), 4),
        "Max_Error": round(float(np.max(np.abs(y_true - y_pred))), 4),
        "MAPE%": round(float(np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None))) * 100), 2),
    }


def run_experimental_results(results_dir: str = "research/results") -> dict:
    """Run full experimental evaluation pipeline."""
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load data
    print("\n[1/4] Loading and preprocessing dataset...")
    data = preprocess_bulk_dataset("data/dataset2.csv")
    X_test, y_test = data["X_test"], data["y_test"]
    X_train, y_train = data["X_train"], data["y_train"]
    X_val, y_val = data["X_val"], data["y_val"]

    # 2. Load models
    print("[2/4] Loading trained models...")
    bpnn, rf, xgb, weights, feature_names = load_models()

    # 3. Predict on all splits
    print("[3/4] Computing predictions...")
    splits = {
        "Train": (X_train, y_train),
        "Validation": (X_val, y_val),
        "Test": (X_test, y_test),
    }

    all_results = []
    for split_name, (X, y) in splits.items():
        predictions = predict_all(bpnn, rf, xgb, weights, X)
        for model_name, preds in predictions.items():
            metrics = compute_metrics(y, preds)
            metrics["Model"] = model_name
            metrics["Split"] = split_name
            metrics["N"] = len(y)
            all_results.append(metrics)

    results_df = pd.DataFrame(all_results)

    # Reorder columns for readability
    col_order = ["Model", "Split", "N", "R²", "RMSE", "MAE", "MedAE", "MAPE%", "Max_Error", "Explained_Var"]
    results_df = results_df[col_order]

    # 4. Save results
    print("[4/4] Saving results...")
    results_df.to_csv(os.path.join(results_dir, "experimental_results.csv"), index=False)

    # Paper-ready test-set table
    test_only = results_df[results_df["Split"] == "Test"].copy()
    test_only = test_only.drop(columns=["Split", "N"])
    test_only.to_csv(os.path.join(results_dir, "model_comparison_table.csv"), index=False)

    # Model ranking (by test R²)
    ranking = test_only.sort_values("R²", ascending=False).reset_index(drop=True)
    ranking.index = ranking.index + 1
    ranking.index.name = "Rank"

    # Print paper table
    print("\n" + "=" * 80)
    print("  TABLE: Model Performance Comparison (Test Set)")
    print("=" * 80)
    print(ranking.to_string())
    print("\n  Ensemble weights:", weights)

    # Baseline comparison: how much ensemble improves over best individual
    best_individual_r2 = test_only[test_only["Model"] != "Ensemble"]["R²"].max()
    ensemble_r2 = test_only[test_only["Model"] == "Ensemble"]["R²"].values[0]
    improvement = ensemble_r2 - best_individual_r2

    summary = {
        "ensemble_r2": ensemble_r2,
        "best_individual_r2": best_individual_r2,
        "ensemble_improvement": round(improvement, 4),
        "weights": weights,
        "test_samples": int(len(y_test)),
        "train_samples": int(len(y_train)),
    }

    with open(os.path.join(results_dir, "baseline_comparison.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Ensemble R²: {ensemble_r2:.4f}")
    print(f"  Best Individual R²: {best_individual_r2:.4f}")
    print(f"  Improvement: +{improvement:.4f}")

    return {
        "results_df": results_df,
        "test_table": test_only,
        "summary": summary,
    }


if __name__ == "__main__":
    run_experimental_results()
