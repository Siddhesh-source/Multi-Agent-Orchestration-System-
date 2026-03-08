import json
from core.llm import llm, rate_limit_delay

_SYSTEM_PROMPT = (
    "You are a quality reviewer for a subtask in a larger workflow. "
    "Evaluate if the output adequately completes THIS SPECIFIC SUBTASK. "
    "Be reasonable - the output doesn't need to be perfect, just good enough to move forward. "
    "Return ONLY a valid JSON object with exactly these three fields:\n"
    "{\n"
    '  "approved": true or false,\n'
    '  "confidence": a float between 0.0 and 1.0,\n'
    '  "feedback": "specific issue if not approved, empty string if approved"\n'
    "}\n"
    "No markdown. No extra text. Only the JSON object."
)

_FALLBACK = {"approved": True, "confidence": 0.5, "feedback": ""}


class CriticAgent:
    async def run(self, subtask: str, output: str) -> dict:
        message = (
            _SYSTEM_PROMPT
            + "\n\nSubtask: " + subtask
            + "\n\nOutput to Review:\n" + output
        )

        response = llm.invoke(message)
        await rate_limit_delay()

        result = _parse_critic_json(response.content)
        if result is None:
            print(f"[Critic] JSON parse failed, using safe fallback. Raw: {response.content[:200]}")
            return _FALLBACK.copy()
        return result


def _parse_critic_json(text: str) -> dict | None:
    cleaned = text.strip()
    for fence in ("```json", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        obj = json.loads(cleaned)
        if all(k in obj for k in ("approved", "confidence", "feedback")):
            return {
                "approved":   bool(obj["approved"]),
                "confidence": float(obj["confidence"]),
                "feedback":   str(obj["feedback"]),
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return None
