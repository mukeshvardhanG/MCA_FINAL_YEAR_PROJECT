"""
Research Results API — Serves pre-computed experimental data to the frontend.
Reads CSV/JSON artifacts from research/results/ and returns structured JSON.

Endpoints:
  GET /api/research/summary          — master bundle (existing)
  GET /api/research/residuals        — residual scatter + histogram
  GET /api/research/correlation      — 21×21 feature correlation matrix
  GET /api/research/statistics       — bootstrap CI + Welch's t-test
  GET /api/research/ensemble-analysis — variance & stability comparison
  GET /api/research/error-analysis   — top-10 best/worst predictions
  GET /api/research/llm-evaluation   — Groq/LLM quality scores
"""
import os
import csv
import json
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_roles

router = APIRouter(prefix="/api/research", tags=["Research Results"])

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "research", "results")


# ── Shared helpers ────────────────────────────────────────────

def _read_csv(filename: str) -> list:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def _read_json(filename: str) -> dict | list:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _file_exists(filename: str) -> bool:
    return os.path.exists(os.path.join(RESULTS_DIR, filename))


# ── /summary ─────────────────────────────────────────────────

@router.get("/summary", dependencies=[Depends(require_roles(["admin"]))])
async def get_research_summary():
    """Master summary endpoint — returns everything the dashboard needs in one call."""

    # Model comparison
    model_comparison = _read_csv("model_comparison_table.csv")
    for row in model_comparison:
        for key in ["R²", "RMSE", "MAE", "MedAE", "MAPE%", "Max_Error", "Explained_Var"]:
            if key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass

    # Ablation study
    ablation = _read_csv("ablation_ensemble_summary.csv")
    for row in ablation:
        try:
            row["Num_Features"] = int(row["Num_Features"])
        except (ValueError, KeyError):
            pass
        for key in ["R²", "RMSE", "MAE"]:
            if key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass

    # PFI validation (top 10)
    pfi_raw = _read_csv("pfi_validation.csv")
    pfi = []
    for row in pfi_raw[:10]:
        try:
            pfi.append({
                "rank":       int(row.get("Final_Rank", 0)),
                "feature":    row.get("Display_Name", row.get("Feature", "")),
                "importance": float(row.get("Mean_Importance", 0)),
                "std":        float(row.get("Std_Importance", 0)),
                "cv_pct":     float(row.get("CV%", 0)),
                "mean_rank":  float(row.get("Mean_Rank", 0)),
                "rank_range": int(row.get("Rank_Range", 0)),
            })
        except (ValueError, TypeError):
            pass

    # Scalability
    scalability = _read_csv("scalability_analysis.csv")
    for row in scalability:
        try:
            row["N_Records"] = int(row["N_Records"])
        except (ValueError, KeyError):
            pass
        for key in ["Total_Mean_s", "Throughput_records_per_s", "Per_Record_ms"]:
            if key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass

    # Generalization gap
    generalization = _read_csv("generalization_gap.csv")
    for row in generalization:
        for key in ["Syn_R²", "Real_R²", "R²_Gap", "Syn_MAE", "Real_MAE", "MAE_Increase"]:
            if key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass

    # JSON artifacts
    pfi_stability  = _read_json("pfi_stability.json")
    error_analysis = _read_json("error_analysis_summary.json")
    groq_eval      = _read_json("groq_evaluation_summary.json")
    dataset_info   = _read_json("dataset_description.json")
    timings        = _read_json("experiment_timings.json")

    return {
        "model_comparison": model_comparison,
        "ablation":         ablation,
        "pfi":              pfi,
        "pfi_stability":    pfi_stability,
        "scalability":      scalability,
        "generalization":   generalization,
        "error_analysis":   error_analysis,
        "groq_evaluation":  groq_eval,
        "dataset_info":     dataset_info,
        "timings":          timings,
    }


# ── /residuals ────────────────────────────────────────────────

@router.get("/residuals", dependencies=[Depends(require_roles(["admin"]))])
async def get_residuals():
    """
    Returns residual analysis data for the Ensemble model.
    Includes scatter plot data (actual vs predicted) and residual histogram.
    """
    if not _file_exists("residuals.json"):
        raise HTTPException(
            status_code=404,
            detail="Residuals not computed yet. Run: python -m research.residuals"
        )
    data = _read_json("residuals.json")
    return data


# ── /correlation ──────────────────────────────────────────────

@router.get("/correlation", dependencies=[Depends(require_roles(["admin"]))])
async def get_correlation():
    """
    Returns 21×21 Pearson correlation matrix computed on the synthetic training dataset.
    """
    if not _file_exists("correlation_matrix.json"):
        raise HTTPException(
            status_code=404,
            detail="Correlation matrix not computed yet. Run: python -m research.correlation"
        )
    data = _read_json("correlation_matrix.json")
    return data


# ── /statistics ───────────────────────────────────────────────

@router.get("/statistics", dependencies=[Depends(require_roles(["admin"]))])
async def get_statistics():
    """
    Returns bootstrap confidence intervals for R² + Welch's t-test comparisons.
    """
    if not _file_exists("statistical_validation.json"):
        raise HTTPException(
            status_code=404,
            detail="Statistical validation not computed yet. Run: python -m research.statistics"
        )
    data = _read_json("statistical_validation.json")
    return data


# ── /ensemble-analysis ────────────────────────────────────────

@router.get("/ensemble-analysis", dependencies=[Depends(require_roles(["admin"]))])
async def get_ensemble_analysis():
    """
    Returns ensemble variance & stability analysis.
    Proves the ensemble is more stable than individual models across datasets,
    justifying its deployment even where XGBoost has higher R².
    """
    stability_csv = _read_csv("ensemble_stability.csv")
    variance_json = _read_json("ensemble_variance.json")

    if not stability_csv and not variance_json:
        raise HTTPException(
            status_code=404,
            detail="Ensemble analysis not computed yet. Run: python -m research.ensemble_analysis"
        )

    # Cast numeric columns
    for row in stability_csv:
        for key in ["Syn_Consistency", "Real_Consistency", "Syn_Var_Error",
                    "Real_Var_Error", "Syn_Std_Error", "Real_Std_Error", "Consistency_Drop"]:
            if key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass

    return {
        "stability_table": stability_csv,
        "justification":   variance_json,
    }


# ── /error-analysis ───────────────────────────────────────────

@router.get("/error-analysis", dependencies=[Depends(require_roles(["admin"]))])
async def get_error_analysis():
    """
    Returns top-10 best and worst ensemble predictions.
    Exposes feature deviation analysis for worst-case inputs.
    """
    summary      = _read_json("error_analysis_summary.json")
    best_preds   = _read_csv("best_predictions.csv")
    worst_preds  = _read_csv("worst_predictions.csv")
    feature_inf  = _read_csv("feature_influence_errors.csv")
    error_range  = _read_csv("error_by_score_range.csv")

    # Cast numerics
    for table in [best_preds, worst_preds]:
        for row in table:
            for k in ["y_true", "y_pred", "error", "abs_error", "model_disagreement"]:
                if k in row:
                    try:
                        row[k] = float(row[k])
                    except (ValueError, TypeError):
                        pass

    for row in feature_inf:
        for k in ["Test_Mean", "Worst_Mean", "Best_Mean", "Z_Worst", "Z_Best"]:
            if k in row:
                try:
                    row[k] = float(row[k])
                except (ValueError, TypeError):
                    pass

    return {
        "summary":           summary,
        "best_predictions":  best_preds,
        "worst_predictions": worst_preds,
        "feature_influence": feature_inf,
        "error_by_range":    error_range,
    }


# ── /llm-evaluation ──────────────────────────────────────────

@router.get("/llm-evaluation", dependencies=[Depends(require_roles(["admin"]))])
async def get_llm_evaluation():
    """
    Returns automated quality scoring of Groq/LLM-generated student insights.
    Scores: relevance, correctness, usefulness (0–10 each).
    """
    summary = _read_json("groq_evaluation_summary.json")
    cases   = _read_csv("groq_evaluation.csv")

    for row in cases:
        for k in ["Score", "Relevance", "Correctness", "Usefulness", "Average",
                  "N_Strengths", "N_Weaknesses", "N_Actions", "Summary_Len"]:
            if k in row:
                try:
                    row[k] = float(row[k])
                except (ValueError, TypeError):
                    pass

    if not summary and not cases:
        raise HTTPException(
            status_code=404,
            detail="LLM evaluation not computed yet. Run: python -m research.groq_evaluation"
        )

    return {
        "summary": summary,
        "cases":   cases,
    }
