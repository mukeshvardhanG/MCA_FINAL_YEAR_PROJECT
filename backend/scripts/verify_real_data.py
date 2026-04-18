import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
import json
import torch
import joblib
from xgboost import XGBRegressor
import os
import sys

# Add backend path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.pipeline import FEATURE_COLUMNS, TARGET_COLUMN
from ml.models import BPNN

def main():
    print("--------------------------------------------------")
    print("1. VERIFY NO DATA LEAKAGE")
    # LOAD REAL DATA
    df = pd.read_csv("data/dataset1.csv")

    # Ensure No Overlap Check
    synthetic_df = pd.read_csv("data/dataset2.csv")
    
    # Check overlap based on features (assumes no two students have exactly identical float specs everywhere)
    overlap = pd.merge(df[FEATURE_COLUMNS], synthetic_df[FEATURE_COLUMNS], how='inner')
    print(f"  Overlap between synthetic train and real test: {len(overlap)} exact records.")
    if len(overlap) == 0:
        print("  [OK] Train Data != Test Data. No leakage.")
    else:
        print("  [WARNING] Minor overlap found (might be identical generic records).")

    # Load Data
    X_real = df[FEATURE_COLUMNS].values.astype(np.float64)
    y_real = df[TARGET_COLUMN].values.astype(np.float64)

    # Load Scaler
    with open("models/scaler_params.json", "r") as f:
        scaler_params = json.load(f)
    means = np.array(scaler_params["mean"])
    scales = np.array(scaler_params["scale"])

    X_scaled = (X_real - means) / scales

    # Load Weights
    with open("models/weights.json", "r") as f:
        weights = json.load(f)

    # Load BPNN
    input_dim = len(FEATURE_COLUMNS)
    bpnn = BPNN(input_dim)
    bpnn.load_state_dict(torch.load("models/bpnn.pt", map_location="cpu", weights_only=True))
    bpnn.eval()
    with torch.no_grad():
        p_bpnn = bpnn(torch.FloatTensor(X_scaled)).numpy().flatten()

    # Load RF
    rf = joblib.load("models/rf.pkl")
    p_rf = rf.predict(X_scaled)

    # Load XGB
    xgb = XGBRegressor()
    xgb.load_model("models/xgb.json")
    p_xgb = xgb.predict(X_scaled)

    p_ensemble = weights["bpnn"] * p_bpnn + weights["rf"] * p_rf + weights["xgb"] * p_xgb

    print("--------------------------------------------------")
    print("2. RUN ON REAL DATA ONLY")
    r2 = r2_score(y_real, p_ensemble)
    print(f"  R² on REAL dataset: {r2:.4f}")
    
    if r2 > 0.975:
        print("  [WARNING] Suspiciously high R²! Possible overfitting.")
    elif r2 >= 0.93:
        print("  [OK] Excellent! Matches expected research benchmark (0.93 - 0.96).")
    else:
        print("  [WARNING] Somewhat lower than Expected.")
        
    print("--------------------------------------------------")
    print("3. CHECK MODEL AGREEMENT")
    stacked_preds = np.vstack([p_bpnn, p_rf, p_xgb])
    std_preds = np.std(stacked_preds, axis=0)

    mean_std = np.mean(std_preds)
    print(f"  Avg Standard Deviation among model predictions: {mean_std:.4f}")
    if mean_std < 0.1:
        print("  [WARNING] std ≈ 0. Models are identical -> overfitting.")
    else:
        print("  [OK] Models have varying opinions -> True Ensemble Behavior.")

    print("--------------------------------------------------")
    print("4. CHECK RESIDUAL DISTRIBUTION")
    residuals = y_real - p_ensemble

    plt.figure(figsize=(8, 6))
    plt.hist(residuals, bins=15, edgecolor="black", alpha=0.7, color='steelblue')
    plt.axvline(0, color='red', linestyle='dashed', linewidth=2, label="Zero Error")
    plt.title("Residual Distribution (Real Data Testing)")
    plt.xlabel("Residual (y_true - y_pred)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = os.path.join("models", "residuals_real_data.png")
    plt.savefig(plot_path)
    print(f"  Residual Plot saved to {plot_path}")
    print("--------------------------------------------------")
    print("Done.")

if __name__ == "__main__":
    main()
