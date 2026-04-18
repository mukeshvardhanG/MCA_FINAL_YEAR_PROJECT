import json
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.quiz_service import evaluate_tier1, get_questions, _score_response, _get_question

async def test():
    qs = get_questions("social", 1)
    responses = []
    
    print("--- Tier 1 Social Scoring ---")
    for q in qs:
        full_q = _get_question(q["question_id"])
        
        if full_q["question_type"] == "likert":
            ans = "5"
        else:
            positive_ids = full_q.get("positive_option_ids", [])
            # In social tier 1 MCQ options:
            # S1T1Q03: [1, 3] -> options are indices 0, 1, 2, 3 so 1 is "I listen to everyone"
            ans = str(positive_ids[0]) if len(positive_ids) > 0 else "0"
            
        responses.append({"question_id": q["question_id"], "answer": ans})
        score, is_pos = await _score_response(full_q, ans)
        print(f"{q['question_id']}: type={full_q['question_type']} | '{ans}' -> score: {score}, positive: {is_pos}")
        
    res = await evaluate_tier1(responses)
    print("\nFinal Result:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
