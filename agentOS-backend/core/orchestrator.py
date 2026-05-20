"""
TaskOrchestrator — runs the LangGraph pipeline for a given task,
persisting DB state throughout the run.

Supports both the original graph and the new enhanced graph with all 7 USPs.
Set USE_ENHANCED_GRAPH=True to enable the enhanced pipeline.
"""
import traceback
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

# Import both graphs
from core.graph import compiled_graph as original_graph, AgentState
from core.enhanced_graph import compiled_graph as enhanced_graph, EnhancedOrchestrator

from db.database import AsyncSessionLocal
from db.models import Task, AgentLog
from agents.memory_agent import MemoryAgent

# Agent names for original graph
_AGENT_NAMES = ["Planner", "Research", "Executor", "Critic", "Memory"]

# Enhanced graph agent names
_ENHANCED_AGENT_NAMES = [
    "DAGPlanner", "CognitiveRouter", "Router", "Research",
    "Writer", "Editor", "Coder", "Debugger", "Tester",
    "AdversarialCritic", "Uncertainty", "TrieMemory", "Metacognition"
]

# Feature flag - set to True to use enhanced graph
USE_ENHANCED_GRAPH = os.environ.get("USE_ENHANCED_GRAPH", "true").lower() == "true"

# Cache for enhanced orchestrator
_enhanced_orchestrator: Optional[EnhancedOrchestrator] = None


class TaskOrchestrator:
    """
    Main orchestrator for AgentOS task execution.
    
    Supports two modes:
    - Original: Simple linear pipeline (Planner → Executor → Critic → Memory)
    - Enhanced: Full 7-USP pipeline with DAG planning, cognitive routing, 
                adversarial critics, uncertainty quantification, 3-tier memory, etc.
    """
    
    def __init__(self, enhanced: bool = USE_ENHANCED_GRAPH):
        """
        Initialize orchestrator.
        
        Args:
            enhanced: If True, uses the enhanced graph with all USPs.
                     Default is controlled by USE_ENHANCED_GRAPH env var.
        """
        self._enhanced = enhanced
        self._enhanced_orch = None
        
        if self._enhanced:
            # Initialize enhanced orchestrator
            global _enhanced_orchestrator
            if _enhanced_orchestrator is None:
                _enhanced_orchestrator = EnhancedOrchestrator()
            self._enhanced_orch = _enhanced_orchestrator
            
            print(f"[Orchestrator] Using ENHANCED graph (7 USPs enabled)")
        else:
            print(f"[Orchestrator] Using ORIGINAL graph (legacy mode)")
    
    async def run(
        self,
        task_id: str,
        task_description: str,
        human_review: bool,
    ) -> None:
        """Execute the task through the appropriate graph pipeline."""
        
        if self._enhanced:
            await self._run_enhanced(task_id, task_description, human_review)
        else:
            await self._run_original(task_id, task_description, human_review)
    
    async def _run_enhanced(
        self,
        task_id: str,
        task_description: str,
        human_review: bool,
    ) -> None:
        """
        Run enhanced graph with all 7 USPs.
        """
        started_at = datetime.now(timezone.utc)
        
        # Initialize agent logs for enhanced graph
        for name in _ENHANCED_AGENT_NAMES:
            await _update_agent_log(task_id, name, "pending")
        
        # Mark task as running
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = "running"
                task.updated_at = datetime.now(timezone.utc)
                await session.commit()
        
        # Run enhanced pipeline
        try:
            result = await self._enhanced_orch.run(
                task_id=task_id,
                task_description=task_description,
                human_review=human_review,
            )
            
            duration = (datetime.now(timezone.utc) - started_at).total_seconds()
            
            async with AsyncSessionLocal() as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = result.get("status", "done")
                    task.final_output = result.get("output", "")
                    task.duration_seconds = duration
                    task.updated_at = datetime.now(timezone.utc)
                    await session.commit()
            
            # Mark all agent logs done
            for name in _ENHANCED_AGENT_NAMES:
                await _update_agent_log(task_id, name, "done")
                
            print(f"[Orchestrator] Enhanced task completed: {result.get('status')}, "
                  f"{result.get('nodes_processed', 0)} nodes processed")
            
        except Exception as exc:
            print(f"[Orchestrator] Enhanced pipeline failed for task {task_id}:")
            traceback.print_exc()
            async with AsyncSessionLocal() as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    task.final_output = f"Pipeline error: {exc}"
                    task.updated_at = datetime.now(timezone.utc)
                    await session.commit()
    
    async def _run_original(
        self,
        task_id: str,
        task_description: str,
        human_review: bool,
    ) -> None:
        """
        Run the original (legacy) graph - kept for backward compatibility.
        """
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
            final_state: AgentState = await original_graph.ainvoke(initial_state)

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


# Convenience function to check which mode is active
def get_mode() -> str:
    """Return the current orchestrator mode."""
    return "enhanced" if USE_ENHANCED_GRAPH else "original"
