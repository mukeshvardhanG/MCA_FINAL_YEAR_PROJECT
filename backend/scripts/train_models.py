"""
Model Training Script
Trains BPNN + Random Forest + XGBoost on Dataset2 (synthetic training data).
Saves model artifacts + weights + feature_names.json to models/ dir.
Asserts test accuracy (R² ≥ 0.93), stops with error if below threshold.

Dataset Split:
  - dataset2.csv → Training (80%) + Test (20%)
  - dataset1.csv → Real-world pilot testing (validation/testing only)
  - dataset3.csv → Held-out validation (never seen during training)

Usage: python scripts/train_models.py
"""
import sys
import os
import numpy as np

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.pipeline import preprocess_bulk_dataset
from ml.models import MLEngine
from sklearn.metrics import r2_score, mean_absolute_error


def main():
    csv_path = os.path.join("data", "dataset2.csv")
    model_dir = "models"

    if not os.path.exists(csv_path):
        print(f"[X] Dataset not found at {csv_path}. Run generate_dataset.py first.")
        sys.exit(1)

    print("=" * 60)
    print("  PE Assessment — Model Training Pipeline")
    print("=" * 60)

    # 1. Preprocess
    print("\n[1/4] Preprocessing dataset...")
    data = preprocess_bulk_dataset(csv_path)

    # 2. Train all models
    print("\n[2/4] Training models...")
    engine = MLEngine(model_dir=model_dir)
    engine.train(
        X_train=data["X_train"],
        y_train=data["y_train"],
        X_val=data["X_val"],
        y_val=data["y_val"],
        feature_names=data["feature_names"],
    )

    # 3. Evaluate on test set
    print("\n[3/4] Evaluating on test set...")
    engine.load()  # Reload from saved files
    result = engine.predict(data["X_test"][:1])
    print(f"  Sample prediction: {result}")

    # Full test set evaluation
    import torch
    engine.bpnn.eval()
    with torch.no_grad():
        p_bpnn = engine.bpnn(torch.FloatTensor(data["X_test"])).numpy()
    p_rf = engine.rf.predict(data["X_test"])
    p_xgb = engine.xgb.predict(data["X_test"])

    p_ensemble = (
        engine.weights["bpnn"] * p_bpnn
        + engine.weights["rf"] * p_rf
        + engine.weights["xgb"] * p_xgb
    )

    r2 = r2_score(data["y_test"], p_ensemble)
    mae = mean_absolute_error(data["y_test"], p_ensemble)

    print(f"\n  ======================================")
    print(f"  |   Test Set Results                 |")
    print(f"  |------------------------------------|")
    print(f"  |   R² Score:    {r2:.4f}             |")
    print(f"  |   MAE:         {mae:.4f}             |")
    print(f"  |   Accuracy:    {r2 * 100:.2f}%            |")
    print(f"  ======================================")

    # Assert accuracy threshold
    ACCURACY_THRESHOLD = 0.93
    if r2 < ACCURACY_THRESHOLD:
        print(f"\n[X] FAILED: R² = {r2:.4f} is below threshold {ACCURACY_THRESHOLD}")
        print("   Model accuracy does not meet the 93% requirement.")
        sys.exit(1)

    print("\n[4/5] Logging Errors & Saving Metrics...")
    errors = np.abs(data["y_test"] - p_ensemble)
    residuals = data["y_test"] - p_ensemble
    threshold = np.percentile(errors, 90)
    std_y = np.std(data["y_test"])

    error_log = []
    confidence_array = []
    for i in range(len(errors)):
        err = float(errors[i])
        if err > threshold:
            label = "high_error"
        elif err > threshold / 2:
            label = "medium_error"
        else:
            label = "low_error"
            
        error_log.append({
            "y_true": float(data["y_test"][i]),
            "y_pred": float(p_ensemble[i]),
            "error": err,
            "label": label
        })
        
        conf = 1 - (err / std_y)
        conf = max(0.0, min(1.0, conf)) * 100
        confidence_array.append(conf)

    import json
    with open(os.path.join(model_dir, "error_log.json"), "w") as f:
        json.dump(error_log, f, indent=2)
        
    experiment_results = {
        "predictions": p_ensemble.tolist(),
        "residuals": residuals.tolist(),
        "confidence": confidence_array
    }
    with open(os.path.join(model_dir, "experiment_results.json"), "w") as f:
        json.dump(experiment_results, f)

    # 5. Verify saved artifacts
    print("\n[5/5] Verifying saved artifacts...")
    required_files = ["bpnn.pt", "rf.pkl", "xgb.json", "weights.json", "feature_names.json", "experiment_results.json"]
    for f in required_files:
        path = os.path.join(model_dir, f)
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[X]"
        print(f"  {status} {f}")

    # Verify feature_names.json has correct count
    with open(os.path.join(model_dir, "feature_names.json"), "r") as f:
        feature_names = json.load(f)
    assert len(feature_names) == 21, f"Expected 21 features, got {len(feature_names)}"
    print(f"  [OK] feature_names.json has {len(feature_names)} features")

    # Compute and display PFI
    print("\n  Top 10 Feature Importances:")
    pfi = engine.compute_pfi(data["X_test"], data["y_test"])
    for item in pfi[:10]:
        print(f"    {item['rank']:2d}. {item['feature_name']:<30s} {item['importance_score']:.4f}")

    with open(os.path.join(model_dir, "pfi_results.json"), "w") as f:
        json.dump(pfi, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  [OK] Training complete! R² = {r2:.4f} ({r2*100:.1f}%)")
    print(f"  Models saved to: {os.path.abspath(model_dir)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
