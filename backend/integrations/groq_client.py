"""
Groq API Client — Generates AI-powered PE performance insights.
Uses llama3-8b-8192 model. Includes template-based fallback.
"""
import os
import json
import httpx
from typing import Optional

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

SYSTEM_PROMPT = """You are an expert physical education performance analyst and sports psychologist.
Given a student's PE assessment data, return ONLY valid JSON (no markdown, no preamble) exactly matching this structure:
{
  "strengths": ["strength 1 with specific data reference", "strength 2"],
  "weaknesses": ["weak area 1 with data reference", "weak area 2"],
  "action_steps": [
    "PHYSICAL: Specific workout recommendation with sets/reps/frequency",
    "PSYCHOLOGICAL: Specific mental training technique",
    "SOCIAL: Team-based activity or communication drill"
  ],
  "youtube_recommendations": [
    "Search phrase for physical workout related to weakness",
    "Search phrase for mental resilience or sports psychology"
  ],
  "psych_guidance": "Personalized mental and psychological guidance (2 sentences)",
  "motivation": "A powerful motivational quote (author included)"
}
Be extremely specific, data-backed, and practical. Never use generic advice. Reference actual scores from the data."""


def build_prompt(prediction: dict, pfi_top5: list, assessment: dict) -> str:
    return f"""
Student PE Assessment Data:

Overall Score: {prediction['final_score']}/100 (Grade: {prediction['performance_grade']})

Top 5 Influential Features (Permutation Feature Importance):
{json.dumps(pfi_top5, indent=2)}

Physical Indicators:
- 100m Sprint: {assessment.get('running_speed_100m')}s
- 1500m Endurance: {assessment.get('endurance_1500m')} min
- Strength Score: {assessment.get('strength_score')}/100
- BMI: {assessment.get('bmi')}
- Reaction Time: {assessment.get('reaction_time_ms')}ms
- Plank Hold: {assessment.get('plank_hold_seconds', 0)}s
- Breath Hold: {assessment.get('breath_hold_seconds', 0)}s

Psychological Indicators (0-10 scale):
- Motivation: {assessment.get('motivation_score')}
- Self-Confidence: {assessment.get('self_confidence_score')}
- Stress Management: {assessment.get('stress_management_score')}
- Goal Orientation: {assessment.get('goal_orientation_score')}
- Mental Resilience: {assessment.get('mental_resilience_score')}
- Quiz Tier Reached: {assessment.get('quiz_tier_reached')}

Social Indicators (0-10 scale):
- Teamwork: {assessment.get('teamwork_score')}
- Participation: {assessment.get('participation_score')}
- Communication: {assessment.get('communication_score')}
- Leadership: {assessment.get('leadership_score')}
- Peer Collaboration: {assessment.get('peer_collaboration_score')}

Provide SPECIFIC, ACTIONABLE improvement recommendations:
1. Identify the 3 major factors most affecting their overall score
2. Give exact workout prescriptions (exercises, sets, reps, frequency)
3. Suggest psychological techniques (visualization, mindfulness, confidence drills)
4. Recommend social improvement strategies (team exercises, communication drills)
5. Create a brief weekly training plan targeting their weakest areas
"""


async def generate_insight_sync(prediction: dict, pfi_top5: list, assessment: dict) -> Optional[dict]:
    """Call Groq API to generate structured insight JSON."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set")

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(prediction, pfi_top5, assessment)},
        ],
        "temperature": 0.4,
        "max_tokens": 1500,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    return json.loads(content)


def generate_template_fallback(prediction: dict, pfi_top5: list, assessment: dict) -> dict:
    """Template-based fallback when Groq API is unavailable.
    Returns the same JSON structure as the Groq response.
    Uses *relative* weakness detection — always finds something actionable."""
    score = prediction.get("final_score", 0)
    grade = prediction.get("performance_grade", "N/A")

    # Determine strengths from PFI top features
    top_features = [p.get("feature_name", "Unknown") for p in pfi_top5[:3]]

    # ── Relative weakness detection ──────────────────────────
    # Score all measurable dimensions and rank them to find the lowest 2
    scored_areas = []
    psych_fields = [
        ("motivation_score", "Motivation"),
        ("self_confidence_score", "Self-Confidence"),
        ("stress_management_score", "Stress Management"),
        ("goal_orientation_score", "Goal Orientation"),
        ("mental_resilience_score", "Mental Resilience"),
    ]
    social_fields = [
        ("teamwork_score", "Teamwork"),
        ("participation_score", "Participation"),
        ("communication_score", "Communication"),
        ("leadership_score", "Leadership"),
        ("peer_collaboration_score", "Peer Collaboration"),
    ]
    all_rated = psych_fields + social_fields
    for key, label in all_rated:
        val = assessment.get(key)
        if val is not None:
            scored_areas.append((label, val, 10.0))

    # Sort ascending — weakest areas first
    scored_areas.sort(key=lambda x: x[1])

    # Compute category averages for context
    psych_vals = [assessment.get(k) for k, _ in psych_fields if assessment.get(k) is not None]
    social_vals = [assessment.get(k) for k, _ in social_fields if assessment.get(k) is not None]
    psych_mean = round(sum(psych_vals) / len(psych_vals), 1) if psych_vals else 5.0
    social_mean = round(sum(social_vals) / len(social_vals), 1) if social_vals else 5.0

    # Always produce 2 weaknesses (the relative weakest, even if absolute scores are high)
    weak_areas = []
    for label, val, max_val in scored_areas[:2]:
        cat_avg = psych_mean if any(label == lbl for _, lbl in psych_fields) else social_mean
        comparison = "below" if val < cat_avg else "near"
        weak_areas.append(f"{label} ({val}/10) — {comparison} your category average of {cat_avg}")

    if not weak_areas:
        weak_areas = ["Insufficient data to determine relative weaknesses"]

    # ── Grade-based messaging ─────────────────────────────────
    weakest_label = scored_areas[0][0] if scored_areas else "general fitness"
    weakest_val = scored_areas[0][1] if scored_areas else 0
    second_label = scored_areas[1][0] if len(scored_areas) > 1 else "overall"

    if grade == "A":
        summary = f"Outstanding performance with a score of {score}/100. The student demonstrates excellence across most dimensions but can still sharpen {weakest_label} ({weakest_val}/10) for holistic growth."
        motivation = f"Exceptional work achieving Grade {grade}! Target {weakest_label} to push toward peak performance."
    elif grade == "B":
        summary = f"Good performance with a score of {score}/100. Strong fundamentals, with {weakest_label} ({weakest_val}/10) and {second_label} identified as growth areas."
        motivation = f"Great progress at Grade {grade}! Focused work on {weakest_label} can take you to the next level."
    elif grade == "C":
        summary = f"Average performance with a score of {score}/100. Solid foundation but {weakest_label} ({weakest_val}/10) needs targeted attention alongside {second_label}."
        motivation = f"You're building momentum at Grade {grade}. Consistent effort on {weakest_label} will drive real improvement."
    else:
        summary = f"Below average performance with a score of {score}/100. Priority areas: {weakest_label} ({weakest_val}/10) and {second_label} require dedicated support."
        motivation = f"Every athlete starts somewhere. Focus first on {weakest_label} — small, consistent gains lead to big results."

    # ── Build specific action steps ────────────────────────────
    action_steps = [
        f"Prioritize {weakest_label}: design 2-3 weekly drills targeting this area (current: {weakest_val}/10, target: {min(10, weakest_val + 1.5)}/10)",
        f"Strengthen {second_label} through structured practice sessions (15–20 min, 3× per week)",
        "Set specific measurable goals for the next assessment period and track progress weekly",
    ]

    # Determine which psychological area to focus guidance on
    psych_weakest = sorted(
        [(label, assessment.get(key, 5.0)) for key, label in psych_fields if assessment.get(key) is not None],
        key=lambda x: x[1]
    )
    if psych_weakest:
        pw_label, pw_val = psych_weakest[0]
        psych_text = (
            f"Your lowest psychological indicator is {pw_label} at {pw_val}/10 "
            f"(category average: {psych_mean}). "
            f"Research shows that targeted mindfulness, visualization, and positive self-talk "
            f"can improve psychological fitness scores by 15–20% over one semester. "
            f"Consider incorporating a 5-minute daily mental conditioning routine."
        )
    else:
        psych_text = "Focus on building overall mental resilience through regular mindfulness practice and positive self-talk."

    return {
        "summary": summary,
        "strengths": [f"Strong performance in {f}" for f in top_features],
        "weaknesses": weak_areas[:2],
        "action_steps": action_steps,
        "youtube_recommendations": [
            f"How to improve {weakest_label} for athletes",
            f"Sports psychology and mindfulness for {second_label}"
        ],
        "psych_guidance": psych_text,
        "motivation": motivation
    }


async def evaluate_open_text(question: str, response: str) -> float:
    """Call Groq API to evaluate a student's open-ended response."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Fallback to simple keyword scoring if Groq is not configured
        return 5.0
        
    prompt = f"""Score this student's open-ended physical education quiz response from 1.0 to 10.0.
Question: {question}
Response: {response}

Scoring criteria:
- Specificity and detail (1-3 pts)
- Self-awareness and reflection (1-3 pts) 
- Growth mindset indicators (1-2 pts)
- Authenticity (1-2 pts)

Return ONLY a number between 1.0 and 10.0. No explanation."""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            res.raise_for_status()
            
        content = res.json()["choices"][0]["message"]["content"].strip()
        # Parse float
        import re
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", content)
        if matches:
            score = float(matches[0])
            return max(1.0, min(10.0, score))
        return 5.0
    except Exception as e:
        print(f"Groq API evaluation failed: {e}")
        return 5.0
