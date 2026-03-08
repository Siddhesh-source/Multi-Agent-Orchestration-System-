"""Quick smoke test for the local memory system."""
from memory.chroma_store import chroma_store
import asyncio


async def test():
    await chroma_store.add(
        "test-001",
        "Task: Benefits of solar energy\nOutput: Solar is renewable and cheap.",
        {
            "task_description": "Benefits of solar energy",
            "timestamp": "2026-01-01T00:00:00",
        },
    )
    results = await chroma_store.query("renewable energy", n_results=1)
    print("Results:", results)
    score = results[0]["score"]
    assert score > 0.3, f"Score too low: {score}"
    print("Memory test PASSED.")


asyncio.run(test())
