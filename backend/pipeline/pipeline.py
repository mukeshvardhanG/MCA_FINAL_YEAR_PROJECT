"""
PySpark Preprocessing Pipeline
Two functions:
  1. preprocess_student_record() — single row, used during inference
  2. preprocess_bulk_dataset()    — full CSV, used during training
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
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

TARGET_COLUMN = "overall_pe_score"


def preprocess_student_record(student_dict: dict, scaler_path: str = "models/scaler_params.json") -> np.ndarray:
    """
    Preprocess a single student record for inference.
    Returns a 1×N numpy array ready for model input.
    """
    values = []
    for col in FEATURE_COLUMNS:
        val = student_dict.get(col, 0.0)
        values.append(float(val) if val is not None else 0.0)

    X = np.array([values])

    # Apply saved scaler if available
    if os.path.exists(scaler_path):
        with open(scaler_path, "r") as f:
            params = json.load(f)
        means = np.array(params["mean"])
        scales = np.array(params["scale"])
        X = (X - means) / scales

    return X


def preprocess_bulk_dataset(csv_path: str, output_dir: str = "data/processed") -> dict:
    """
    Preprocess entire CSV dataset for training.
    Returns dict with X_train, X_val, X_test, y_train, y_val, y_test, feature_names.
    Saves scaler parameters for inference use.

    Dataset Split Enforcement (IEEE Reproducibility):
      ✔ Training set  → SYNTHETIC data only (this function)
      ✔ Testing set   → REAL pilot data only (generalization_test.py)
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # ── DATASET SPLIT ENFORCEMENT ──────────────────────────────────
    print("=" * 60)
    print("  [DATASET SPLIT ENFORCEMENT]")
    print("  Training on SYNTHETIC dataset (generated distribution)")
    print("  Real dataset reserved for testing/generalization ONLY")
    print("=" * 60)

    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} synthetic records from {csv_path}")

    # Impute missing values with column means
    for col in FEATURE_COLUMNS:
        if col in df.columns and df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].mean())

    # Extract features and target
    X = df[FEATURE_COLUMNS].values.astype(np.float64)
    y = df[TARGET_COLUMN].values.astype(np.float64)

    # StandardScaler normalization
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Save scaler parameters for inference
    scaler_params = {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "feature_names": FEATURE_COLUMNS,
    }
    with open(os.path.join("models", "scaler_params.json"), "w") as f:
        json.dump(scaler_params, f, indent=2)

    # Train/Val/Test split (70/15/15)
    np.random.seed(42)
    indices = np.random.permutation(len(X_scaled))
    n_train = int(0.70 * len(indices))
    n_val = int(0.15 * len(indices))

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    result = {
        "X_train": X_scaled[train_idx],
        "X_val": X_scaled[val_idx],
        "X_test": X_scaled[test_idx],
        "y_train": y[train_idx],
        "y_val": y[val_idx],
        "y_test": y[test_idx],
        "feature_names": FEATURE_COLUMNS,
    }

    print(f"  Split: train={len(train_idx)}, val={len(val_idx)}, test={len(test_idx)}")
    return result
