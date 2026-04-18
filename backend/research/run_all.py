"""
Central Research Runner — Executes all research experiments sequentially.
Produces the complete research/results/ directory with all outputs.

Usage:
    cd backend
    python -m research.run_all
"""
import os
import sys
import time
import json
import uuid

np_seed = 42

# Ensure backend root is on path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# Set global random seed for full reproducibility
import numpy as np
np.random.seed(np_seed)
print(f"[Seed] Global numpy seed set to {np_seed} for reproducibility.")

RESULTS_DIR = os.path.join("research", "results")
RUN_ID = str(uuid.uuid4())


def banner(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def timed(func, label: str, *args, **kwargs):
    """Run a function, print timing, return (result, elapsed_seconds)."""
    print(f"\n  ▶  {label} ...")
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"  ✔  {label} completed in {elapsed:.2f}s")
    return result, elapsed


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timings = {}
    all_outputs = {"run_id": RUN_ID}

    banner("PE ASSESSMENT — FULL RESEARCH EXPERIMENT SUITE")
    print(f"  Run ID:          {RUN_ID}")
    print(f"  Working dir:     {os.getcwd()}")
    print(f"  Results output:  {os.path.abspath(RESULTS_DIR)}")
    print(f"  Numpy seed:      {np_seed}")

    # ─── 1. Real Dataset Generation ────────────────────────────
    banner("1/12  Real Dataset Generation")
    print("  Running Real Dataset Extraction...")
    from research.real_dataset import load_or_generate_real_dataset
    real_df, t = timed(load_or_generate_real_dataset, "Real Dataset Extraction")
    timings["dataset1"] = round(t, 2)
    all_outputs["real_records"] = int(len(real_df)) if real_df is not None and not real_df.empty else 0

    # ─── 2. Dataset Validation ─────────────────────────────────
    banner("2/12  Dataset Validation (Distributions + Correlations)")
    print("  Running Dataset Validation...")
    from research.dataset_validation import run_dataset_validation
    dataset_results, t = timed(run_dataset_validation, "Dataset Validation", RESULTS_DIR)
    timings["dataset_validation"] = round(t, 2)
    all_outputs["dataset"] = dataset_results

    # ─── 3. Experimental Results ───────────────────────────────
    banner("3/12  Experimental Results (RMSE / MAE / R²)")
    print("  Running Model Evaluation Pipeline...")
    from research.experimental_results import run_experimental_results
    exp_results, t = timed(run_experimental_results, "Experimental Results", RESULTS_DIR)
    timings["experimental_results"] = round(t, 2)
    all_outputs["experimental"] = exp_results.get("summary", {}) if isinstance(exp_results, dict) else {}

    # ─── 4. Ablation Study ─────────────────────────────────────
    banner("4/12  Ablation Study (Feature Subset Analysis)")
    print("  Running Ablation Study...")
    from research.ablation_study import run_ablation_study
    ablation_results, t = timed(run_ablation_study, "Ablation Study", RESULTS_DIR)
    timings["ablation_study"] = round(t, 2)

    # ─── 5. PFI Validation ─────────────────────────────────────
    banner("5/12  PFI Validation (Multi-Run Consistency)")
    print("  Running Permutation Feature Importance Validation...")
    from research.pfi_validation import run_pfi_multi
    pfi_results, t = timed(run_pfi_multi, "PFI Validation", 5, 10, RESULTS_DIR)
    timings["pfi_validation"] = round(t, 2)

    # ─── 6. Error Analysis ─────────────────────────────────────
    banner("6/12  Error Analysis (Best / Worst Predictions)")
    print("  Running Error Analysis...")
    from research.error_analysis import run_error_analysis
    error_results, t = timed(run_error_analysis, "Error Analysis", 10, RESULTS_DIR)
    timings["error_analysis"] = round(t, 2)
    all_outputs["error"] = error_results

    # ─── 7. Residual Analysis ──────────────────────────────────
    banner("7/12  Residual Analysis (y_true - y_pred)")
    print("  Running Residual Analysis...")
    from research.residuals import run_residual_analysis
    residual_results, t = timed(run_residual_analysis, "Residual Analysis", RESULTS_DIR)
    timings["residual_analysis"] = round(t, 2)
    all_outputs["residuals"] = {
        "n_samples":      residual_results.get("n_samples"),
        "ensemble_mean":  residual_results.get("ensemble_summary", {}).get("mean_residual"),
        "ensemble_std":   residual_results.get("ensemble_summary", {}).get("std_residual"),
    }

    # ─── 8. Correlation Analysis ───────────────────────────────
    banner("8/12  Correlation Analysis (Feature Heatmap)")
    print("  Running Correlation Analysis...")
    from research.correlation import run_correlation_analysis
    corr_results, t = timed(run_correlation_analysis, "Correlation Analysis", RESULTS_DIR)
    timings["correlation"] = round(t, 2)
    all_outputs["correlation"] = {
        "n_features":  corr_results.get("n_features"),
        "dataset_type": corr_results.get("dataset_type"),
    }

    # ─── 9. Statistical Validation ─────────────────────────────
    banner("9/12  Statistical Validation (Bootstrap CI + T-Test)")
    print("  Running Statistical Validation...")
    from research.statistics import run_statistical_validation
    stats_results, t = timed(run_statistical_validation, "Statistical Validation", 1000, RESULTS_DIR)
    timings["statistical_validation"] = round(t, 2)
    all_outputs["statistics"] = {
        "n_bootstrap":  stats_results.get("n_bootstrap"),
        "dataset_type": stats_results.get("dataset_type"),
    }

    # ─── 10. Ensemble Analysis ─────────────────────────────────
    banner("10/12  Ensemble Analysis (Variance & Stability)")
    print("  Running Ensemble Analysis...")
    from research.ensemble_analysis import run_ensemble_analysis
    ensemble_results, t = timed(run_ensemble_analysis, "Ensemble Analysis", RESULTS_DIR)
    timings["ensemble_analysis"] = round(t, 2)
    all_outputs["ensemble"] = ensemble_results.get("justification", {}) if isinstance(ensemble_results, dict) else {}

    # ─── 11. Scalability Analysis ──────────────────────────────
    banner("11/12  Scalability Analysis (100 / 1,000 / 10,000)")
    print("  Running Scalability Analysis...")
    from research.scalability_analysis import run_scalability_analysis
    scale_results, t = timed(run_scalability_analysis, "Scalability Analysis", [100, 1000, 10000], 3, RESULTS_DIR)
    timings["scalability_analysis"] = round(t, 2)

    # ─── 12. Groq Evaluation ───────────────────────────────────
    banner("12/12  Groq / LLM Output Evaluation")
    print("  Running LLM Evaluation...")
    from research.groq_evaluation import run_groq_evaluation
    groq_results, t = timed(run_groq_evaluation, "Groq LLM Evaluation", RESULTS_DIR)
    timings["groq_evaluation"] = round(t, 2)
    all_outputs["groq"] = groq_results

    # ─── Generalization Test ────────────────────────────────────
    banner("  Bonus: Generalization Test (Synthetic → Real)")
    print("  Running Generalization Test (testing on REAL dataset only)...")
    from research.generalization_test import run_generalization_test
    gen_results, t = timed(run_generalization_test, "Generalization Test", RESULTS_DIR)
    timings["generalization_test"] = round(t, 2)
    all_outputs["generalization"] = gen_results

    # ─── Save Timings ───────────────────────────────────────────
    total_time = sum(timings.values())
    timings["total"] = round(total_time, 2)
    with open(os.path.join(RESULTS_DIR, "experiment_timings.json"), "w") as f:
        json.dump(timings, f, indent=2)

    # ─── Save Final Summary ─────────────────────────────────────
    all_outputs["timings"] = timings
    with open(os.path.join(RESULTS_DIR, "all_experiments_output.json"), "w") as f:
        json.dump(all_outputs, f, indent=2, default=str)

    # ─── Print Summary ──────────────────────────────────────────
    banner("ALL EXPERIMENTS COMPLETE")
    print(f"\n  Run ID:     {RUN_ID}")
    print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Results:    {os.path.abspath(RESULTS_DIR)}")

    print(f"\n  Per-module timings:")
    for name, secs in timings.items():
        if name != "total":
            print(f"    {name:<30s} {secs:>6.2f}s")
    print(f"    {'TOTAL':<30s} {total_time:>6.2f}s")

    print(f"\n  Generated files:")
    for f_name in sorted(os.listdir(RESULTS_DIR)):
        full_path = os.path.join(RESULTS_DIR, f_name)
        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            print(f"    {f_name:<50s} {size:>8,} bytes")


if __name__ == "__main__":
    main()
