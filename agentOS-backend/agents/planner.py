import json
from typing import List
from core.llm import llm, rate_limit_delay

_SYSTEM_PROMPT = (
    "You are a task planning assistant. Given a complex task, "
    "break it into 3 to 5 clear sequential subtasks. Each subtask "
    "must be specific and actionable. Return ONLY a valid JSON array "
    "of strings. No explanation, no markdown, no extra text.\n"
    'Example output: ["Search for X", "Summarize findings", "Write report", "Verify facts"]'
)

_RETRY_SUFFIX = (
    "\n\nYou must return ONLY a JSON array. Nothing else. "
    "No text before or after the array."
)


class PlannerAgent:
    async def run(self, task_description: str) -> List[str]:
        message = _SYSTEM_PROMPT + "\n\nTask: " + task_description

        # First attempt
        response = llm.invoke(message)
        await rate_limit_delay()
        subtasks = _parse_json_list(response.content)

        if subtasks is None:
            # Retry once with stricter instruction
            response = llm.invoke(message + _RETRY_SUFFIX)
            await rate_limit_delay()
            subtasks = _parse_json_list(response.content)

        if subtasks is None:
            print(f"[Planner] JSON parse failed twice. Using fallback.")
            subtasks = [task_description]

        print(f"[Planner] Subtasks: {subtasks}")
        return subtasks


def _parse_json_list(text: str) -> List[str] | None:
    """Strip markdown fences and attempt JSON parse."""
    cleaned = text.strip()
    for fence in ("```json", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return [str(item) for item in result]
    except json.JSONDecodeError:
        return None
    return None
