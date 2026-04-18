"""
Master Runner — Executes all research experiments sequentially.
Produces the complete results/ directory with all CSVs, JSONs, and the final report.

Usage:
    cd backend
    python -m research.run_all_experiments
"""
import os
import sys
import time
import json

# Ensure backend root is on path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

RESULTS_DIR = os.path.join("research", "results")


def banner(title: str):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def timed(func, *args, **kwargs):
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"  [done] Completed in {elapsed:.1f}s")
    return result, elapsed


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timings = {}

    banner("PE ASSESSMENT RESEARCH — FULL EXPERIMENT SUITE")
    print(f"  Working directory: {os.getcwd()}")
    print(f"  Results output:    {os.path.abspath(RESULTS_DIR)}")

    # ─── 1. Real Dataset Generation ───────────────────────────
    banner("1/10  Real Dataset Generation")
    from research.real_dataset import load_or_generate_real_dataset
    _, t = timed(load_or_generate_real_dataset)
    timings["dataset1"] = t

    # ─── 2. Dataset Validation ────────────────────────────────
    banner("2/10  Dataset Validation (Distributions + Correlations)")
    from research.dataset_validation import run_dataset_validation
    dataset_results, t = timed(run_dataset_validation, RESULTS_DIR)
    timings["dataset_validation"] = t

    # ─── 3. Experimental Results ──────────────────────────────
    banner("3/10  Experimental Results (RMSE / MAE / R²)")
    from research.experimental_results import run_experimental_results
    exp_results, t = timed(run_experimental_results, RESULTS_DIR)
    timings["experimental_results"] = t

    # ─── 4. Ablation Study ────────────────────────────────────
    banner("4/10  Ablation Study (Feature Subset Analysis)")
    from research.ablation_study import run_ablation_study
    ablation_results, t = timed(run_ablation_study, RESULTS_DIR)
    timings["ablation_study"] = t

    # ─── 5. PFI Validation ────────────────────────────────────
    banner("5/10  PFI Validation (Multi-Run Consistency)")
    from research.pfi_validation import run_pfi_multi
    pfi_results, t = timed(run_pfi_multi, 5, 10, RESULTS_DIR)
    timings["pfi_validation"] = t

    # ─── 6. Error Analysis ────────────────────────────────────
    banner("6/10  Error Analysis (Best / Worst Predictions)")
    from research.error_analysis import run_error_analysis
    error_results, t = timed(run_error_analysis, 10, RESULTS_DIR)
    timings["error_analysis"] = t

    # ─── 7. Scalability Analysis ──────────────────────────────
    banner("7/10  Scalability Analysis (100 / 1000 / 10000)")
    from research.scalability_analysis import run_scalability_analysis
    scale_results, t = timed(run_scalability_analysis, [100, 1000, 10000], 3, RESULTS_DIR)
    timings["scalability_analysis"] = t

    # ─── 8. Generalization Test ───────────────────────────────
    banner("8/10  Generalization Test (Synthetic → Real)")
    from research.generalization_test import run_generalization_test
    gen_results, t = timed(run_generalization_test, RESULTS_DIR)
    timings["generalization_test"] = t

    # ─── 9. Groq Evaluation ───────────────────────────────────
    banner("9/10  Groq Output Evaluation")
    from research.groq_evaluation import run_groq_evaluation
    groq_results, t = timed(run_groq_evaluation, RESULTS_DIR)
    timings["groq_evaluation"] = t

    # ─── 10. Generate Final Report ────────────────────────────
    banner("10/10  Generating Research Report")
    from research.generate_report import generate_research_report
    report_data = {
        "dataset": dataset_results,
        "experimental": exp_results,
        "ablation": ablation_results,
        "pfi": pfi_results,
        "error": error_results,
        "scalability": scale_results,
        "generalization": gen_results,
        "groq": groq_results,
    }
    _, t = timed(generate_research_report, report_data, RESULTS_DIR)
    timings["report_generation"] = t

    # ─── Summary ──────────────────────────────────────────────
    total_time = sum(timings.values())
    timings["total"] = total_time

    with open(os.path.join(RESULTS_DIR, "experiment_timings.json"), "w") as f:
        json.dump({k: round(v, 2) for k, v in timings.items()}, f, indent=2)

    banner("ALL EXPERIMENTS COMPLETE")
    print(f"\n  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Results directory: {os.path.abspath(RESULTS_DIR)}")
    print(f"\n  Generated files:")
    for f_name in sorted(os.listdir(RESULTS_DIR)):
        size = os.path.getsize(os.path.join(RESULTS_DIR, f_name))
        print(f"    {f_name:45s} {size:>8,} bytes")


if __name__ == "__main__":
    main()
