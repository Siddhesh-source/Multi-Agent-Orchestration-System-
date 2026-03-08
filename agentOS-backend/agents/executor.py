from core.llm import llm, rate_limit_delay

_CODE_KEYWORDS = [
    "write code", "python script", "function",
    "class", "script", "implement", "code for",
]

_CODE_SYSTEM = (
    "You are a coding assistant. Complete the given subtask by writing clean, "
    "working Python code. Return only the code inside a ```python block. "
    "No explanation outside the code block."
)

_TASK_SYSTEM = (
    "You are a task execution assistant. Complete the given subtask thoroughly "
    "and accurately. Return only the completed output. "
    "No preamble, no meta-commentary."
)


class ExecutorAgent:
    async def run(self, subtask: str, context: str = "") -> str:
        is_code_task = any(k in subtask.lower() for k in _CODE_KEYWORDS)
        system_prompt = _CODE_SYSTEM if is_code_task else _TASK_SYSTEM

        if context:
            message = (
                system_prompt
                + "\n\nContext:\n" + context
                + "\n\nSubtask: " + subtask
            )
        else:
            message = system_prompt + "\n\nSubtask: " + subtask

        response = llm.invoke(message)
        await rate_limit_delay()
        return response.content.strip()
