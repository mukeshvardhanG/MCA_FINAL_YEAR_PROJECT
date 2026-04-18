"""
Ablation Study — Evaluate model performance with different feature subsets.
Tests three configurations to isolate the contribution of each dimension:
  1. Physical features only (9 features)
  2. Physical + Psychological (14 features)
  3. Full feature set (21 features)

Usage:
    python -m research.ablation_study
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import os
import sys
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.models import BPNN
from pipeline.pipeline import FEATURE_COLUMNS, TARGET_COLUMN

# ── Feature subsets ────────────────────────────────────────────
PHYSICAL_FEATURES = [
    "running_speed_100m", "endurance_1500m", "flexibility_score",
    "strength_score", "bmi", "coordination_score", "reaction_time_ms",
    "physical_progress_index", "skill_acquisition_speed",
]

PSYCHOLOGICAL_FEATURES = [
    "motivation_score", "self_confidence_score", "stress_management_score",
    "goal_orientation_score", "mental_resilience_score",
]

SOCIAL_FEATURES = [
    "teamwork_score", "participation_score", "communication_score",
    "leadership_score", "peer_collaboration_score",
]

DEMOGRAPHIC_FEATURES = ["age", "grade_level"]

ABLATION_CONFIGS = {
    "Physical Only": PHYSICAL_FEATURES + DEMOGRAPHIC_FEATURES,
    "Physical + Psychological": PHYSICAL_FEATURES + PSYCHOLOGICAL_FEATURES + DEMOGRAPHIC_FEATURES,
    "Full Feature Set": FEATURE_COLUMNS,  # all 21
}


def _train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test, input_dim):
    """Train all three models from scratch and evaluate."""
    # ── BPNN (fixed: mini-batch, LR scheduler, patience=30) ──────
    bpnn = BPNN(input_dim)
    optimizer = torch.optim.Adam(bpnn.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=10
    )
    criterion = nn.MSELoss()
    X_t = torch.FloatTensor(X_train)
    y_t = torch.FloatTensor(y_train)
    X_v = torch.FloatTensor(X_val)
    y_v = torch.FloatTensor(y_val)

    batch_size = 256
    n_samples  = X_t.shape[0]
    best_val_loss = float("inf")
    best_state    = None
    patience, wait = 30, 0          # FIX: 10 → 30

    for epoch in range(500):        # FIX: 200 → 500
        bpnn.train()
        perm = torch.randperm(n_samples)
        for start in range(0, n_samples, batch_size):
            idx = perm[start: start + batch_size]
            optimizer.zero_grad()
            loss = criterion(bpnn(X_t[idx]), y_t[idx])
            loss.backward()
            optimizer.step()
        bpnn.eval()
        with torch.no_grad():
            vl = criterion(bpnn(X_v), y_v).item()
        scheduler.step(vl)
        if vl < best_val_loss:
            best_val_loss = vl
            best_state = {k: v.clone() for k, v in bpnn.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break
    if best_state:
        bpnn.load_state_dict(best_state)
    bpnn.eval()

    # RF
    rf = RandomForestRegressor(n_estimators=200, min_samples_split=4, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    # XGB
    xgb = XGBRegressor(n_estimators=300, learning_rate=0.03, max_depth=7,
                        subsample=0.8, reg_lambda=1.0, random_state=42)
    xgb.fit(X_train, y_train)

    # Predictions
    with torch.no_grad():
        p_bpnn = bpnn(torch.FloatTensor(X_test)).numpy()
    p_rf = rf.predict(X_test)
    p_xgb = xgb.predict(X_test)

    # Compute weights from val MAE
    with torch.no_grad():
        v_bpnn = bpnn(X_v).numpy()
    v_rf = rf.predict(X_val)
    v_xgb = xgb.predict(X_val)
    errs = [
        max(mean_absolute_error(y_val, v_bpnn), 0.01),
        max(mean_absolute_error(y_val, v_rf), 0.01),
        max(mean_absolute_error(y_val, v_xgb), 0.01),
    ]
    inv = [1/e for e in errs]
    total = sum(inv)
    w = [i/total for i in inv]

    p_ensemble = w[0] * p_bpnn + w[1] * p_rf + w[2] * p_xgb

    results = {}
    for name, preds in [("BPNN", p_bpnn), ("RF", p_rf), ("XGBoost", p_xgb), ("Ensemble", p_ensemble)]:
        results[name] = {
            "R²": round(float(r2_score(y_test, preds)), 4),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_test, preds))), 4),
            "MAE": round(float(mean_absolute_error(y_test, preds)), 4),
        }

    return results


def run_ablation_study(results_dir: str = "research/results") -> pd.DataFrame:
    """Run ablation study across feature subsets."""
    os.makedirs(results_dir, exist_ok=True)

    # Load full dataset
    df = pd.read_csv("data/dataset2.csv")

    # Impute
    for col in FEATURE_COLUMNS:
        if col in df.columns and df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].mean())

    y = df[TARGET_COLUMN].values.astype(np.float64)

    # Fixed split
    np.random.seed(42)
    indices = np.random.permutation(len(df))
    n_train = int(0.70 * len(indices))
    n_val = int(0.15 * len(indices))
    train_idx = indices[:n_train]
    val_idx = indices[n_train:n_train + n_val]
    test_idx = indices[n_train + n_val:]

    all_rows = []

    for config_name, feature_list in ABLATION_CONFIGS.items():
        print(f"\n  Running ablation: {config_name} ({len(feature_list)} features)...")
        X = df[feature_list].values.astype(np.float64)

        # Scale — use StandardScaler to match the main training pipeline
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train = X_scaled[train_idx]
        X_val   = X_scaled[val_idx]
        X_test  = X_scaled[test_idx]
        y_train = y[train_idx]
        y_val   = y[val_idx]
        y_test  = y[test_idx]

        results = _train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test, len(feature_list))

        for model_name, metrics in results.items():
            row = {"Config": config_name, "Num_Features": len(feature_list), "Model": model_name}
            row.update(metrics)
            all_rows.append(row)

    results_df = pd.DataFrame(all_rows)
    results_df.to_csv(os.path.join(results_dir, "ablation_study.csv"), index=False)

    # Paper table: ensemble only
    ensemble_only = results_df[results_df["Model"] == "Ensemble"][
        ["Config", "Num_Features", "R²", "RMSE", "MAE"]
    ].reset_index(drop=True)
    ensemble_only.to_csv(os.path.join(results_dir, "ablation_ensemble_summary.csv"), index=False)

    # Print results
    print("\n" + "=" * 80)
    print("  TABLE: Ablation Study — Ensemble Results")
    print("=" * 80)
    print(ensemble_only.to_string(index=False))

    print("\n  Full ablation table:")
    pivot = results_df.pivot_table(index="Config", columns="Model", values="R²")
    print(pivot.to_string())

    return results_df


if __name__ == "__main__":
    run_ablation_study()
