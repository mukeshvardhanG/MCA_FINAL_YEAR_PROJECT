"""
Groq Output Evaluation — Compare LLM-generated vs rule-based insights.
Scores both approaches on relevance, correctness, and usefulness.

Usage:
    python -m research.groq_evaluation
"""
import numpy as np
import pandas as pd
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integrations.groq_client import generate_template_fallback


def _create_test_cases() -> list:
    """Create diverse test cases spanning all grade levels."""
    cases = [
        {
            "label": "High Performer (Grade A)",
            "prediction": {"final_score": 92.5, "performance_grade": "A",
                           "bpnn_score": 91.0, "rf_score": 93.5, "xgb_score": 93.0},
            "pfi_top5": [
                {"feature_name": "strength_score", "importance_score": 0.15},
                {"feature_name": "motivation_score", "importance_score": 0.12},
                {"feature_name": "coordination_score", "importance_score": 0.10},
                {"feature_name": "teamwork_score", "importance_score": 0.09},
                {"feature_name": "running_speed_100m", "importance_score": 0.08},
            ],
            "assessment": {
                "running_speed_100m": 11.5, "endurance_1500m": 5.5,
                "strength_score": 88, "bmi": 21.0, "reaction_time_ms": 210,
                "motivation_score": 9.0, "self_confidence_score": 8.5,
                "stress_management_score": 7.5, "goal_orientation_score": 8.8,
                "mental_resilience_score": 8.0,
                "teamwork_score": 8.5, "participation_score": 9.0,
                "communication_score": 7.8, "leadership_score": 7.5,
                "peer_collaboration_score": 8.2, "quiz_tier_reached": 2,
            },
        },
        {
            "label": "Average Performer (Grade C)",
            "prediction": {"final_score": 62.0, "performance_grade": "C",
                           "bpnn_score": 60.0, "rf_score": 63.0, "xgb_score": 63.0},
            "pfi_top5": [
                {"feature_name": "endurance_1500m", "importance_score": 0.14},
                {"feature_name": "stress_management_score", "importance_score": 0.11},
                {"feature_name": "strength_score", "importance_score": 0.10},
                {"feature_name": "leadership_score", "importance_score": 0.09},
                {"feature_name": "self_confidence_score", "importance_score": 0.08},
            ],
            "assessment": {
                "running_speed_100m": 15.5, "endurance_1500m": 9.0,
                "strength_score": 45, "bmi": 24.5, "reaction_time_ms": 320,
                "motivation_score": 5.5, "self_confidence_score": 4.8,
                "stress_management_score": 4.0, "goal_orientation_score": 5.5,
                "mental_resilience_score": 4.5,
                "teamwork_score": 5.0, "participation_score": 5.5,
                "communication_score": 4.5, "leadership_score": 3.8,
                "peer_collaboration_score": 5.0, "quiz_tier_reached": 1,
            },
        },
        {
            "label": "Low Performer (Grade D)",
            "prediction": {"final_score": 38.5, "performance_grade": "D",
                           "bpnn_score": 40.0, "rf_score": 37.0, "xgb_score": 38.5},
            "pfi_top5": [
                {"feature_name": "motivation_score", "importance_score": 0.16},
                {"feature_name": "running_speed_100m", "importance_score": 0.13},
                {"feature_name": "stress_management_score", "importance_score": 0.11},
                {"feature_name": "peer_collaboration_score", "importance_score": 0.09},
                {"feature_name": "endurance_1500m", "importance_score": 0.08},
            ],
            "assessment": {
                "running_speed_100m": 19.0, "endurance_1500m": 11.5,
                "strength_score": 22, "bmi": 28.0, "reaction_time_ms": 380,
                "motivation_score": 2.5, "self_confidence_score": 3.0,
                "stress_management_score": 2.0, "goal_orientation_score": 3.0,
                "mental_resilience_score": 2.5,
                "teamwork_score": 3.0, "participation_score": 3.5,
                "communication_score": 2.8, "leadership_score": 2.0,
                "peer_collaboration_score": 3.0, "quiz_tier_reached": 1,
            },
        },
        {
            "label": "Good Performer (Grade B)",
            "prediction": {"final_score": 76.0, "performance_grade": "B",
                           "bpnn_score": 75.0, "rf_score": 77.0, "xgb_score": 76.0},
            "pfi_top5": [
                {"feature_name": "coordination_score", "importance_score": 0.13},
                {"feature_name": "goal_orientation_score", "importance_score": 0.11},
                {"feature_name": "strength_score", "importance_score": 0.10},
                {"feature_name": "communication_score", "importance_score": 0.09},
                {"feature_name": "mental_resilience_score", "importance_score": 0.08},
            ],
            "assessment": {
                "running_speed_100m": 13.0, "endurance_1500m": 7.0,
                "strength_score": 65, "bmi": 22.0, "reaction_time_ms": 260,
                "motivation_score": 7.0, "self_confidence_score": 6.5,
                "stress_management_score": 6.0, "goal_orientation_score": 7.2,
                "mental_resilience_score": 6.0,
                "teamwork_score": 6.8, "participation_score": 7.0,
                "communication_score": 5.5, "leadership_score": 5.8,
                "peer_collaboration_score": 6.5, "quiz_tier_reached": 2,
            },
        },
    ]
    return cases


def _evaluate_insight(insight: dict, case: dict) -> dict:
    """Score an insight on relevance, correctness, and usefulness (0-10 each)."""
    scores = {"relevance": 0, "correctness": 0, "usefulness": 0}
    details = []

    # ── Relevance (0-10): Does it reference the actual data? ──
    rel_score = 0
    summary = insight.get("summary", "")

    # Check if score/grade is mentioned
    if str(case["prediction"]["final_score"]) in summary or case["prediction"]["performance_grade"] in summary:
        rel_score += 3
        details.append("References actual score/grade")
    else:
        rel_score += 1
        details.append("Does not reference specific score")

    # Check if weaknesses reference actual low scores
    weaknesses = insight.get("weaknesses", [])
    if weaknesses and any(w for w in weaknesses if len(w) > 10):
        rel_score += 3
        details.append("Provides specific weakness descriptions")
    else:
        rel_score += 1

    # Check if strengths exist
    strengths = insight.get("strengths", [])
    if strengths and len(strengths) >= 2:
        rel_score += 2
        details.append(f"Lists {len(strengths)} strengths")
    else:
        rel_score += 1

    # Action steps present
    action_steps = insight.get("action_steps", [])
    if action_steps and len(action_steps) >= 2:
        rel_score += 2
        details.append(f"Lists {len(action_steps)} action steps")

    scores["relevance"] = min(10, rel_score)

    # ── Correctness (0-10): Is the assessment accurate? ──
    corr_score = 0
    grade = case["prediction"]["performance_grade"]

    # Summary tone should match grade
    positive_words = ["outstanding", "excellent", "exceptional", "strong", "great", "good"]
    negative_words = ["below", "poor", "needs", "struggling", "weak", "low"]
    neutral_words = ["average", "moderate", "solid", "foundation"]

    summary_lower = summary.lower()
    if grade == "A" and any(w in summary_lower for w in positive_words):
        corr_score += 4
        details.append("Tone correctly matches high performance")
    elif grade == "D" and any(w in summary_lower for w in negative_words):
        corr_score += 4
        details.append("Tone correctly matches low performance")
    elif grade in ["B", "C"] and any(w in summary_lower for w in neutral_words + positive_words):
        corr_score += 3
        details.append("Tone approximately matches mid performance")
    else:
        corr_score += 1

    # Weaknesses should point to lowest actual scores
    assessment = case["assessment"]
    psych_scores = {k: v for k, v in assessment.items() if k.endswith("_score") and isinstance(v, (int, float)) and v <= 10}
    if psych_scores:
        lowest_area = min(psych_scores, key=psych_scores.get)
        if weaknesses and any(lowest_area.replace("_score", "").replace("_", " ") in w.lower() for w in weaknesses):
            corr_score += 3
            details.append(f"Correctly identifies {lowest_area} as weak")
        else:
            corr_score += 1

    # Psych guidance exists
    psych_g = insight.get("psych_guidance", "")
    if psych_g and len(psych_g) > 50:
        corr_score += 3
        details.append("Substantial psychological guidance provided")
    else:
        corr_score += 1

    scores["correctness"] = min(10, corr_score)

    # ── Usefulness (0-10): Are recommendations actionable? ──
    use_score = 0

    # Action steps should be specific (contain numbers, frequencies, etc.)
    specific_indicators = ["per week", "times", "minutes", "sets", "reps", "daily", "weekly", "target", "/10"]
    if action_steps:
        specific_count = sum(1 for step in action_steps
                           if any(ind in step.lower() for ind in specific_indicators))
        use_score += min(4, specific_count + 1)
        if specific_count > 0:
            details.append(f"{specific_count}/{len(action_steps)} action steps are specific")
    else:
        use_score += 1

    # Motivation message exists
    motivation = insight.get("motivation", "")
    if motivation and len(motivation) > 20:
        use_score += 2
        details.append("Motivational message provided")
    else:
        use_score += 1

    # Overall length indicates depth
    total_content_len = sum(len(str(v)) for v in insight.values())
    if total_content_len > 500:
        use_score += 2
        details.append(f"Comprehensive response ({total_content_len} chars)")
    elif total_content_len > 200:
        use_score += 1

    # Has psych or social guidance
    if psych_g and len(psych_g) > 30:
        use_score += 2

    scores["usefulness"] = min(10, use_score)

    return {
        "scores": scores,
        "total": round(sum(scores.values()) / 3, 2),
        "details": details,
    }


def run_groq_evaluation(results_dir: str = "research/results") -> dict:
    """Compare template-based (rule-based) insight generation across test cases."""
    os.makedirs(results_dir, exist_ok=True)

    cases = _create_test_cases()
    rows = []

    print("\n" + "=" * 80)
    print("  GROQ OUTPUT EVALUATION — Rule-Based Insights")
    print("=" * 80)

    for case in cases:
        print(f"\n  Case: {case['label']}")

        # Generate rule-based insight
        rule_insight = generate_template_fallback(
            case["prediction"], case["pfi_top5"], case["assessment"]
        )

        # Evaluate
        evaluation = _evaluate_insight(rule_insight, case)

        row = {
            "Case": case["label"],
            "Grade": case["prediction"]["performance_grade"],
            "Score": case["prediction"]["final_score"],
            "Relevance": evaluation["scores"]["relevance"],
            "Correctness": evaluation["scores"]["correctness"],
            "Usefulness": evaluation["scores"]["usefulness"],
            "Average": evaluation["total"],
            "N_Strengths": len(rule_insight.get("strengths", [])),
            "N_Weaknesses": len(rule_insight.get("weaknesses", [])),
            "N_Actions": len(rule_insight.get("action_steps", [])),
            "Summary_Len": len(rule_insight.get("summary", "")),
            "Has_Psych_Guidance": "Yes" if len(rule_insight.get("psych_guidance", "")) > 30 else "No",
        }
        rows.append(row)

        print(f"    Relevance: {evaluation['scores']['relevance']}/10")
        print(f"    Correctness: {evaluation['scores']['correctness']}/10")
        print(f"    Usefulness: {evaluation['scores']['usefulness']}/10")
        print(f"    Average: {evaluation['total']}/10")
        for d in evaluation["details"]:
            print(f"      • {d}")

    results_df = pd.DataFrame(rows)
    results_df.to_csv(os.path.join(results_dir, "groq_evaluation.csv"), index=False)

    # Summary
    summary = {
        "n_cases": len(cases),
        "mean_relevance": round(results_df["Relevance"].mean(), 2),
        "mean_correctness": round(results_df["Correctness"].mean(), 2),
        "mean_usefulness": round(results_df["Usefulness"].mean(), 2),
        "mean_overall": round(results_df["Average"].mean(), 2),
        "best_case": results_df.loc[results_df["Average"].idxmax(), "Case"],
        "worst_case": results_df.loc[results_df["Average"].idxmin(), "Case"],
        "methodology": "Automated scoring of rule-based template fallback insights. "
                       "Scores assess data reference accuracy, tone-grade alignment, "
                       "weakness identification precision, and action step specificity.",
    }

    with open(os.path.join(results_dir, "groq_evaluation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Overall Mean: {summary['mean_overall']}/10")
    print(f"  Best: {summary['best_case']}, Worst: {summary['worst_case']}")

    return summary


if __name__ == "__main__":
    run_groq_evaluation()
