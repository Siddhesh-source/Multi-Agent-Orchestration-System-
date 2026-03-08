import asyncio
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from agents.memory_agent import MemoryAgent


async def run_test():
    task = "Research the top 3 open source LLMs available in 2025 and write a brief comparison"

    print("\n========== PLANNER ==========")
    subtasks = await PlannerAgent().run(task)
    print(f"Subtasks: {subtasks}")
    assert isinstance(subtasks, list), "Planner must return a list"
    assert len(subtasks) >= 2, "Planner must return at least 2 subtasks"

    print("\n========== RESEARCHER ==========")
    research = await ResearchAgent().run(subtasks[0])
    print(f"Research (first 300 chars): {research[:300]}")
    assert len(research) > 50, "Research output too short"

    print("\n========== EXECUTOR ==========")
    output = await ExecutorAgent().run(subtasks[1], research)
    print(f"Output (first 300 chars): {output[:300]}")
    assert len(output) > 50, "Executor output too short"

    print("\n========== CRITIC ==========")
    review = await CriticAgent().run(task, output)
    print(f"Review: {review}")
    assert "approved" in review, "Critic must return approved field"
    assert "confidence" in review, "Critic must return confidence field"

    print("\n========== MEMORY STORE ==========")
    await MemoryAgent().store("test-pipeline-001", task, output)
    print("Stored successfully.")

    print("\n========== MEMORY RETRIEVE ==========")
    results = await MemoryAgent().retrieve("open source LLMs", n_results=1)
    print(f"Retrieved: {results}")
    assert len(results) > 0, "Memory retrieve returned nothing"

    print("\n========== ALL TESTS PASSED ==========")


asyncio.run(run_test())
