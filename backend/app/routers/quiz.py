from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Assessment, QuizSession
from app.schemas import QuizSubmitRequest, QuizTierResult
from app.services.quiz_service import (
    get_questions, evaluate_tier1, evaluate_tier2, compute_indicator_scores
)

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

# Mapping from indicator to assessment column
PSYCH_INDICATORS = [
    "motivation_score", "self_confidence_score", "stress_management_score",
    "goal_orientation_score", "mental_resilience_score"
]
SOCIAL_INDICATORS = [
    "teamwork_score", "participation_score", "communication_score",
    "leadership_score", "peer_collaboration_score"
]


# ─── Tier 1 physical metric → weak-area mapping ────────────────
PHYSICAL_METRIC_INDICATORS = {
    "strength": ["motivation_score", "mental_resilience_score"],
    "endurance": ["stress_management_score", "motivation_score"],
    "sprint": ["self_confidence_score", "goal_orientation_score"],
    "bmi": ["stress_management_score", "motivation_score"],
    "reaction": ["mental_resilience_score", "self_confidence_score"],
}

def _identify_weak_areas(assessment: Assessment) -> list:
    """Return a list of indicator names to focus on based on weak Tier 1 metrics."""
    metrics = {
        "strength": assessment.strength_score or 50,
        "endurance": 100 - ((assessment.endurance_1500m or 7.0) / 15.0 * 100),  # lower time = better
        "sprint": 100 - ((assessment.running_speed_100m or 13.0) / 25.0 * 100),
        "bmi": max(0, 100 - abs((assessment.bmi or 22) - 22) * 5),  # deviation from 22 is worse
        "reaction": max(0, 100 - ((assessment.reaction_time_ms or 300) - 100) / 4),
    }
    sorted_metrics = sorted(metrics.items(), key=lambda x: x[1])
    weakest = sorted_metrics[:2]  # take the two weakest
    focus_indicators = []
    for metric_name, _ in weakest:
        focus_indicators.extend(PHYSICAL_METRIC_INDICATORS.get(metric_name, []))
    return list(set(focus_indicators))


@router.get("/questions")
async def get_quiz_questions(
    type: str, tier: int = 1,
    assessment_id: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import random

    if type not in ("psychological", "social"):
        raise HTTPException(400, "type must be 'psychological' or 'social'")
    if tier not in (1, 2):
        raise HTTPException(400, "tier must be 1 or 2")

    questions = get_questions(type, tier)

    # For Tier 2, filter questions to focus on weak Tier 1 areas
    if tier == 2 and assessment_id:
        result = await db.execute(
            select(Assessment).where(Assessment.assessment_id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment:
            focus_indicators = _identify_weak_areas(assessment)
            if focus_indicators:
                # Prioritize questions mapped to weak indicators
                focused = [q for q in questions if q.get("maps_to_indicator") in focus_indicators]
                other = [q for q in questions if q.get("maps_to_indicator") not in focus_indicators]
                # Return focused questions first, then fill with others up to 10
                questions = (focused + other)[:10]

    # For Tier 1, randomly select 5 questions from the bank
    if tier == 1:
        if len(questions) > 5:
            questions = random.sample(questions, 5)
        else:
            random.shuffle(questions)

    return questions


@router.post("/submit", response_model=QuizTierResult)
async def submit_quiz(
    req: QuizSubmitRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    assessment_id = req.assessment_id
    result_a = await db.execute(
        select(Assessment).where(Assessment.assessment_id == assessment_id)
    )
    assessment = result_a.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    responses_dicts = [{"question_id": r.question_id, "answer": r.answer} for r in req.responses]

    if req.tier == 1:
        # Delete any existing session for this assessment+type so student can retake freely
        existing_res = await db.execute(
            select(QuizSession).where(
                QuizSession.assessment_id == assessment_id, 
                QuizSession.quiz_type == req.quiz_type,
            )
        )
        old_session = existing_res.scalars().first()
        if old_session:
            await db.delete(old_session)
            await db.flush()

        # Evaluate Tier 1
        eval_result = await evaluate_tier1(responses_dicts)

        # Save quiz session
        session = QuizSession(
            assessment_id=assessment_id,
            quiz_type=req.quiz_type,
            tier1_responses=responses_dicts,
            tier1_score=eval_result["tier1_score"],
            tier_reached=1,
        )
        db.add(session)

        if not eval_result["requires_tier2"]:
            # Finalize with Tier 1 scores only
            indicator_scores = await compute_indicator_scores(responses_dicts)
            _apply_scores(assessment, req.quiz_type, indicator_scores, tier_reached=1)
            session.final_score = eval_result["tier1_score"]
            session.tier_reached = 1
            session.completed_at = datetime.utcnow()
            session.locked = True

        await db.commit()
        return QuizTierResult(
            tier1_score=eval_result["tier1_score"],
            positivity_ratio=eval_result["positivity_ratio"],
            requires_tier2=eval_result["requires_tier2"],
            tier_reached=1,
        )

    elif req.tier == 2:
        # Find existing Tier 1 session for this assessment + type
        result_s = await db.execute(
            select(QuizSession).where(
                QuizSession.assessment_id == assessment_id,
                QuizSession.quiz_type == req.quiz_type,
            )
        )
        session = result_s.scalar_one_or_none()
        if not session:
            raise HTTPException(409, "Tier 1 not completed yet")

        tier1_score = session.tier1_score
        eval_result = await evaluate_tier2(tier1_score, responses_dicts)

        session.tier2_responses = responses_dicts
        session.tier2_score = eval_result["tier2_score"]
        session.final_score = eval_result["final_score"]
        session.tier_reached = 2
        session.completed_at = datetime.utcnow()
        session.locked = True

        # Compute per-indicator scores using combined T1+T2 responses
        all_responses = (session.tier1_responses or []) + responses_dicts
        indicator_scores = await compute_indicator_scores(all_responses)

        # Apply cross-validated scaling to indicator scores
        scale_factor = eval_result["final_score"] / tier1_score if tier1_score > 0 else 1.0
        for k in indicator_scores:
            indicator_scores[k] = round(min(10.0, indicator_scores[k] * scale_factor), 2)

        _apply_scores(assessment, req.quiz_type, indicator_scores, tier_reached=2)
        await db.commit()

        return QuizTierResult(
            tier1_score=tier1_score,
            tier2_score=eval_result["tier2_score"],
            final_score=eval_result["final_score"],
            requires_tier2=False,
            tier_reached=2,
            inconsistency_detected=eval_result["inconsistency_detected"],
        )


def _apply_scores(assessment: Assessment, quiz_type: str, scores: dict, tier_reached: int):
    """Write validated quiz scores to the assessment record."""
    if quiz_type == "psychological":
        for indicator in PSYCH_INDICATORS:
            if indicator in scores:
                setattr(assessment, indicator, scores[indicator])
        assessment.quiz_tier_reached = tier_reached
    elif quiz_type == "social":
        for indicator in SOCIAL_INDICATORS:
            if indicator in scores:
                setattr(assessment, indicator, scores[indicator])
        assessment.social_tier_reached = tier_reached

    # Check if both quizzes done → mark complete
    psych_done = assessment.motivation_score is not None
    social_done = assessment.teamwork_score is not None
    if psych_done and social_done:
        assessment.is_complete = True


from pydantic import BaseModel

class InteractiveTestSubmit(BaseModel):
    assessment_id: str
    quiz_type: str  # "psychological" or "social"
    # Psychological metrics
    memory_score: Optional[float] = None      # 0-100
    pattern_score: Optional[float] = None     # 0-100
    # Social metrics
    emotion_score: Optional[float] = None     # 0-100
    trust_score: Optional[float] = None       # 0-100


def _interactive_to_indicator_scores(quiz_type: str, test_scores: dict, tier1_score: float) -> dict:
    """Convert interactive test raw scores to 0-10 indicator values."""
    if quiz_type == "psychological":
        memory_norm = max(0, min(10, (test_scores.get("memory_score", 50) / 10)))
        pattern_norm = max(0, min(10, (test_scores.get("pattern_score", 50) / 10)))
        interactive_avg = (memory_norm + pattern_norm) / 2

        return {
            "motivation_score": round(min(10, (tier1_score * 0.5) + (interactive_avg * 0.5)), 2),
            "self_confidence_score": round(min(10, (tier1_score * 0.4) + (pattern_norm * 0.6)), 2),
            "stress_management_score": round(min(10, (tier1_score * 0.4) + (interactive_avg * 0.6)), 2),
            "goal_orientation_score": round(min(10, (tier1_score * 0.5) + (memory_norm * 0.5)), 2),
            "mental_resilience_score": round(min(10, (tier1_score * 0.3) + (interactive_avg * 0.7)), 2),
        }
    else:  # social
        emotion_norm = max(0, min(10, (test_scores.get("emotion_score", 50) / 10)))
        trust_norm = max(0, min(10, (test_scores.get("trust_score", 50) / 10)))
        interactive_avg = (emotion_norm + trust_norm) / 2

        return {
            "teamwork_score": round(min(10, (tier1_score * 0.5) + (trust_norm * 0.5)), 2),
            "participation_score": round(min(10, (tier1_score * 0.4) + (interactive_avg * 0.6)), 2),
            "communication_score": round(min(10, (tier1_score * 0.4) + (emotion_norm * 0.6)), 2),
            "leadership_score": round(min(10, (tier1_score * 0.5) + (interactive_avg * 0.5)), 2),
            "peer_collaboration_score": round(min(10, (tier1_score * 0.3) + (trust_norm * 0.7)), 2),
        }


@router.post("/submit-interactive")
async def submit_interactive_tier2(
    req: InteractiveTestSubmit,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit Tier 2 interactive (Human Benchmark) test results."""
    # Verify assessment belongs to user
    assess_res = await db.execute(
        select(Assessment).where(Assessment.assessment_id == req.assessment_id)
    )
    assessment = assess_res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if assessment.student_id != user["student_id"]:
        raise HTTPException(403, "Not your assessment")

    # Find existing Tier 1 quiz session
    session_res = await db.execute(
        select(QuizSession).where(
            QuizSession.assessment_id == req.assessment_id,
            QuizSession.quiz_type == req.quiz_type,
        )
    )
    session = session_res.scalar_one_or_none()
    if not session:
        raise HTTPException(409, "Tier 1 quiz not completed yet")

    tier1_score = session.tier1_score or 5.0

    # Extract specific scores based on quiz type
    test_scores = {}
    if req.quiz_type == "psychological":
        test_scores["memory_score"] = getattr(req, "memory_score", 50.0) or 50.0
        test_scores["pattern_score"] = getattr(req, "pattern_score", 50.0) or 50.0
    else:
        test_scores["emotion_score"] = getattr(req, "emotion_score", 50.0) or 50.0
        test_scores["trust_score"] = getattr(req, "trust_score", 50.0) or 50.0

    # Convert interactive scores to indicator scores
    indicator_scores = _interactive_to_indicator_scores(
        req.quiz_type, test_scores, tier1_score
    )

    # Compute tier2 and final scores
    tier2_avg = sum(indicator_scores.values()) / len(indicator_scores)
    inconsistency = abs(tier1_score - tier2_avg)
    if inconsistency > 2.5:
        final_score = 0.35 * tier1_score + 0.65 * tier2_avg
    else:
        final_score = 0.50 * tier1_score + 0.50 * tier2_avg

    # Update session
    session.tier2_score = round(tier2_avg, 2)
    session.final_score = round(final_score, 2)
    session.tier_reached = 2
    session.completed_at = datetime.utcnow()
    session.locked = True
    session.tier2_responses = [{
        "type": "interactive",
        **test_scores
    }]

    # Apply scores to assessment
    _apply_scores(assessment, req.quiz_type, indicator_scores, tier_reached=2)
    await db.commit()

    return QuizTierResult(
        tier1_score=tier1_score,
        tier2_score=round(tier2_avg, 2),
        final_score=round(final_score, 2),
        requires_tier2=False,
        tier_reached=2,
        inconsistency_detected=inconsistency > 2.5,
    )

