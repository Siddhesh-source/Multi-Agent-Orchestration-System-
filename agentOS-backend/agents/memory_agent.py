from datetime import datetime, timezone
from typing import List
from memory.chroma_store import chroma_store as _chroma


class MemoryAgent:
    def __init__(self):
        self._store = _chroma

    async def store(self, task_id: str, task_description: str, output: str):
        document = f"Task: {task_description}\nOutput: {output}"
        metadata = {
            "task_id": task_id,
            "task_description": task_description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._store.add(task_id, document, metadata)

    async def retrieve(self, query: str, n_results: int = 3) -> list:
        return await self._store.query(query, n_results)
