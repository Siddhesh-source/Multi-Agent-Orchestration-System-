"""
TaskOrchestrator — runs the LangGraph pipeline for a given task,
persisting DB state throughout the run.
"""
import traceback
from datetime import datetime, timezone

from sqlalchemy import select

from core.graph import compiled_graph, AgentState
from db.database import AsyncSessionLocal
from db.models import Task, AgentLog
from agents.memory_agent import MemoryAgent

_AGENT_NAMES = ["Planner", "Research", "Executor", "Critic", "Memory"]


class TaskOrchestrator:
    async def run(
        self,
        task_id: str,
        task_description: str,
        human_review: bool,
    ) -> None:
        started_at = datetime.now(timezone.utc)

        # ── 1. Mark task as running ───────────────────────────────────
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = "running"
                task.updated_at = datetime.now(timezone.utc)
                await session.commit()

        # ── 2. Retrieve relevant past context from memory ─────────────
        try:
            memory = MemoryAgent()
            past = await memory.retrieve(task_description, n_results=2)
            if past:
                chunks = "\n".join(r["chunk"] for r in past)
                enriched_description = (
                    f"Relevant context from past tasks:\n{chunks}"
                    f"\n\nCurrent Task: {task_description}"
                )
            else:
                enriched_description = task_description
        except Exception:
            enriched_description = task_description

        # ── 3. Build initial state ────────────────────────────────────
        initial_state: AgentState = {
            "task_id":               task_id,
            "task_description":      enriched_description,
            "human_review":          human_review,
            "subtasks":              [],
            "current_subtask_index": 0,
            "research_context":      "",
            "current_output":        "",
            "final_output":          "",
            "critic_approved":       False,
            "critic_feedback":       "",
            "retry_count":           0,
            "human_review_required": False,
            "human_approved":        None,
            "human_feedback":        "",
            "error":                 None,
        }

        # ── 4. Reset all AgentLogs to pending ─────────────────────────
        for name in _AGENT_NAMES:
            await _update_agent_log(task_id, name, "pending")

        # ── 5. Run the LangGraph pipeline ─────────────────────────────
        try:
            final_state: AgentState = await compiled_graph.ainvoke(initial_state)

            final_output = final_state.get("final_output") or final_state.get("current_output", "")
            duration = (datetime.now(timezone.utc) - started_at).total_seconds()

            async with AsyncSessionLocal() as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = "done"
                    task.final_output = final_output
                    task.duration_seconds = duration
                    task.updated_at = datetime.now(timezone.utc)
                    await session.commit()

            # Mark all agent logs done
            for name in _AGENT_NAMES:
                await _update_agent_log(task_id, name, "done")

        except Exception as exc:
            print(f"[Orchestrator] Pipeline failed for task {task_id}:")
            traceback.print_exc()
            async with AsyncSessionLocal() as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    task.final_output = f"Pipeline error: {exc}"
                    task.updated_at = datetime.now(timezone.utc)
                    await session.commit()


# ─── Helper ───────────────────────────────────────────────────────────

async def _update_agent_log(
    task_id: str,
    agent_name: str,
    status: str,
    input_text: str | None = None,
    output_text: str | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentLog).where(
                AgentLog.task_id == task_id,
                AgentLog.agent_name == agent_name,
            )
        )
        log = result.scalar_one_or_none()
        if log:
            log.status = status
            if input_text is not None:
                log.input_text = input_text
            if output_text is not None:
                log.output_text = output_text
            if status == "running":
                log.started_at = datetime.now(timezone.utc)
            if status in ("done", "failed"):
                log.completed_at = datetime.now(timezone.utc)
            await session.commit()
