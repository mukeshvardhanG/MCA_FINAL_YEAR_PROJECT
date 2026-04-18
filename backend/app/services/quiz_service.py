"""
Quiz Service — Adaptive Two-Tier Quiz Engine
Handles Tier 1 evaluation, escalation detection, Tier 2 scoring, and cross-validation.
"""
import json
import os
from typing import List, Dict, Optional
import asyncio
from integrations.groq_client import evaluate_open_text

ESCALATION_THRESHOLD = 0.80
INCONSISTENCY_THRESHOLD = 2.5

QUESTION_BANK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "question_bank.json")

_question_bank = None

def _load_question_bank():
    global _question_bank
    if _question_bank is None:
        with open(QUESTION_BANK_PATH, "r", encoding="utf-8-sig") as f:
            _question_bank = json.load(f)
    return _question_bank

def get_questions(quiz_type: str, tier: int) -> list:
    bank = _load_question_bank()
    key = f"tier{tier}_{quiz_type}"
    questions = bank.get(key, [])
    # Strip answer keys for client
    return [
        {
            "question_id": q["question_id"],
            "text": q["text"],
            "question_type": q["question_type"],
            "options": q.get("options"),
            "maps_to_indicator": q.get("maps_to_indicator"),
        }
        for q in questions
    ]

def _get_question(question_id: str) -> dict:
    bank = _load_question_bank()
    for key in bank:
        for q in bank[key]:
            if q["question_id"] == question_id:
                return q
    raise ValueError(f"Question {question_id} not found")

async def _score_response(question: dict, answer) -> tuple:
    """Returns (score 0-10, is_positive bool)"""
    qtype = question["question_type"]

    if qtype == "likert":
        val = int(answer)
        score = (val / 5) * 10
        is_positive = val >= 4
        return score, is_positive

    elif qtype == "mcq":
        chosen_idx = int(answer)
        positive_ids = question.get("positive_option_ids", [])
        is_positive = chosen_idx in positive_ids
        score = 10.0 if is_positive else 4.0
        return score, is_positive

    elif qtype == "short_answer":
        score = await evaluate_open_text(question.get("text", ""), str(answer))
        is_positive = score >= 6.0
        return score, is_positive

    return 5.0, False

async def evaluate_tier1(responses: List[Dict]) -> dict:
    """Evaluate Tier 1 responses, return score and whether Tier 2 is needed."""
    positive_count = 0
    total = len(responses)
    scores = []

    coros = [_score_response(_get_question(r["question_id"]), r["answer"]) for r in responses]
    results = await asyncio.gather(*coros)

    for score, is_positive in results:
        scores.append(score)
        if is_positive:
            positive_count += 1

    positivity_ratio = positive_count / total if total > 0 else 0
    tier1_score = sum(scores) / len(scores) if scores else 0

    return {
        "tier1_score": round(tier1_score, 2),
        "positivity_ratio": round(positivity_ratio, 2),
        "requires_tier2": True,  # Always escalate to Tier 2 interactive tests
    }

async def evaluate_tier2(tier1_score: float, tier2_responses: List[Dict]) -> dict:
    """Evaluate Tier 2 responses and cross-validate with Tier 1."""
    scores = []
    coros = [_score_response(_get_question(r["question_id"]), r["answer"]) for r in tier2_responses]
    results = await asyncio.gather(*coros)
    
    for score, _ in results:
        scores.append(score)

    tier2_score = sum(scores) / len(scores) if scores else 0
    inconsistency = abs(tier1_score - tier2_score)

    if inconsistency > INCONSISTENCY_THRESHOLD:
        final_score = 0.35 * tier1_score + 0.65 * tier2_score
    else:
        final_score = 0.50 * tier1_score + 0.50 * tier2_score

    return {
        "tier2_score": round(tier2_score, 2),
        "final_score": round(final_score, 2),
        "tier_reached": 2,
        "inconsistency_detected": inconsistency > INCONSISTENCY_THRESHOLD,
    }

async def compute_indicator_scores(responses: List[Dict]) -> Dict[str, float]:
    """Group question scores by their mapped indicator and average them."""
    indicator_scores = {}
    indicator_counts = {}

    coros = []
    questions = []
    for r in responses:
        q = _get_question(r["question_id"])
        questions.append(q)
        coros.append(_score_response(q, r["answer"]))
        
    results = await asyncio.gather(*coros)

    for i, (score, _) in enumerate(results):
        q = questions[i]
        indicator = q.get("maps_to_indicator", "unknown")
        indicator_scores[indicator] = indicator_scores.get(indicator, 0) + score
        indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1

    return {
        k: round(indicator_scores[k] / indicator_counts[k], 2)
        for k in indicator_scores
    }
