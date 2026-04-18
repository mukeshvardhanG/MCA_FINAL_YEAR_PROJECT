"""
Scalability Analysis — Measure preprocessing and prediction time at varying scales.
Tests 100, 1000, and 10000 records to demonstrate system scalability.

Usage:
    python -m research.scalability_analysis
"""
import numpy as np
import pandas as pd
import time
import os
import sys
import json
from sklearn.preprocessing import MinMaxScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.experimental_results import load_models, predict_all
from scripts.generate_dataset import generate_synthetic_dataset
from pipeline.pipeline import FEATURE_COLUMNS, TARGET_COLUMN


def run_scalability_analysis(scales=None, n_trials: int = 3,
                              results_dir: str = "research/results") -> pd.DataFrame:
    """Benchmark preprocessing and prediction time at different scales."""
    if scales is None:
        scales = [100, 1000, 10000]

    os.makedirs(results_dir, exist_ok=True)

    # Load models once
    bpnn, rf, xgb, weights, feature_names = load_models()

    rows = []

    for n in scales:
        print(f"\n  Benchmarking scale: {n} records...")
        trial_times = {"preprocess": [], "predict": [], "total": []}

        for trial in range(n_trials):
            # Generate fresh dataset
            df = generate_synthetic_dataset(n, seed=42 + trial)

            # Impute
            for col in FEATURE_COLUMNS:
                if col in df.columns and df[col].isnull().sum() > 0:
                    df[col] = df[col].fillna(df[col].mean())

            # ── Preprocessing time ──
            t0 = time.perf_counter()
            X = df[FEATURE_COLUMNS].values.astype(np.float64)
            scaler = MinMaxScaler()
            X_scaled = scaler.fit_transform(X)
            t_preprocess = time.perf_counter() - t0
            trial_times["preprocess"].append(t_preprocess)

            # ── Prediction time (all models) ──
            t0 = time.perf_counter()
            _ = predict_all(bpnn, rf, xgb, weights, X_scaled)
            t_predict = time.perf_counter() - t0
            trial_times["predict"].append(t_predict)

            trial_times["total"].append(t_preprocess + t_predict)

        rows.append({
            "N_Records": n,
            "Preprocess_Mean_s": round(np.mean(trial_times["preprocess"]), 4),
            "Preprocess_Std_s": round(np.std(trial_times["preprocess"]), 4),
            "Predict_Mean_s": round(np.mean(trial_times["predict"]), 4),
            "Predict_Std_s": round(np.std(trial_times["predict"]), 4),
            "Total_Mean_s": round(np.mean(trial_times["total"]), 4),
            "Total_Std_s": round(np.std(trial_times["total"]), 4),
            "Throughput_records_per_s": round(n / np.mean(trial_times["total"]), 0),
            "Per_Record_ms": round(np.mean(trial_times["total"]) / n * 1000, 3),
        })

    results_df = pd.DataFrame(rows)
    results_df.to_csv(os.path.join(results_dir, "scalability_analysis.csv"), index=False)

    # Compute scaling factor
    if len(scales) >= 2:
        base = results_df.iloc[0]["Total_Mean_s"]
        results_df["Scaling_Factor"] = (results_df["Total_Mean_s"] / base).round(2)

    results_df.to_csv(os.path.join(results_dir, "scalability_analysis.csv"), index=False)

    # Summary
    summary = {
        "scales_tested": scales,
        "n_trials_per_scale": n_trials,
        "results": rows,
        "is_approximately_linear": bool(
            len(scales) >= 2 and
            rows[-1]["Total_Mean_s"] / max(rows[0]["Total_Mean_s"], 0.001)
            < (scales[-1] / scales[0]) * 2
        ),
    }
    with open(os.path.join(results_dir, "scalability_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Print results
    print("\n" + "=" * 80)
    print("  TABLE: Scalability Analysis")
    print("=" * 80)
    display_cols = ["N_Records", "Preprocess_Mean_s", "Predict_Mean_s", "Total_Mean_s", "Throughput_records_per_s", "Per_Record_ms"]
    print(results_df[display_cols].to_string(index=False))
    print(f"\n  Scaling is approximately linear: {summary['is_approximately_linear']}")

    return results_df


if __name__ == "__main__":
    run_scalability_analysis()
