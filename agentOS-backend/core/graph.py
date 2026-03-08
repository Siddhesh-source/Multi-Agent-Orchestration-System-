from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from datetime import datetime, timezone
from sqlalchemy import select

from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from agents.memory_agent import MemoryAgent
from db.database import AsyncSessionLocal
from db.models import AgentLog


# ─── State schema ─────────────────────────────────────────────────────

class AgentState(TypedDict):
    task_id: str
    task_description: str
    human_review: bool
    subtasks: List[str]
    current_subtask_index: int
    research_context: str
    current_output: str
    final_output: str
    critic_approved: bool
    critic_feedback: str
    retry_count: int
    human_review_required: bool
    human_approved: Optional[bool]
    human_feedback: str
    error: Optional[str]


# ─── Helper function ──────────────────────────────────────────────────

async def _update_agent_log(
    task_id: str,
    agent_name: str,
    status: str,
    input_text: str | None = None,
    output_text: str | None = None,
) -> None:
    """Update agent log in database for real-time frontend updates."""
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


# ─── Node functions ───────────────────────────────────────────────────

async def plan_node(state: AgentState) -> dict:
    await _update_agent_log(state["task_id"], "Planner", "running")
    subtasks = await PlannerAgent().run(state["task_description"])
    await _update_agent_log(
        state["task_id"], 
        "Planner", 
        "done",
        input_text=state["task_description"],
        output_text="\n".join(f"{i+1}. {s}" for i, s in enumerate(subtasks))
    )
    return {
        "subtasks": subtasks,
        "current_subtask_index": 0,
        "retry_count": 0,
    }


async def research_node(state: AgentState) -> dict:
    subtask = state["subtasks"][state["current_subtask_index"]]
    print(f"[Research] Starting research for: '{subtask}'")
    await _update_agent_log(state["task_id"], "Research", "running", input_text=subtask)
    context = await ResearchAgent().run(subtask)
    await _update_agent_log(state["task_id"], "Research", "done", output_text=context[:500])
    print(f"[Research] Completed research")
    return {"research_context": context}


async def execute_node(state: AgentState) -> dict:
    subtask = state["subtasks"][state["current_subtask_index"]]
    print(f"[Executor] Executing subtask {state['current_subtask_index'] + 1}/{len(state['subtasks'])}: '{subtask}'")
    await _update_agent_log(state["task_id"], "Executor", "running", input_text=subtask)
    output = await ExecutorAgent().run(subtask, state["research_context"])
    await _update_agent_log(state["task_id"], "Executor", "done", output_text=output[:500])
    print(f"[Executor] Completed execution")
    return {"current_output": output}


async def critic_node(state: AgentState) -> dict:
    subtask = state["subtasks"][state["current_subtask_index"]]
    print(f"[Critic] Reviewing output for subtask {state['current_subtask_index'] + 1}")
    print(f"[Critic] Current retry_count: {state['retry_count']}, human_review: {state['human_review']}")
    await _update_agent_log(state["task_id"], "Critic", "running", input_text=state["current_output"][:500])
    result = await CriticAgent().run(
        subtask,  # Pass the current subtask, not the full task description
        state["current_output"]
    )
    approved = result["approved"]
    feedback = result["feedback"]
    retry_count = state["retry_count"]
    
    print(f"[Critic] LLM decision - approved: {approved}, confidence: {result.get('confidence', 'N/A')}")
    if feedback:
        print(f"[Critic] Feedback: {feedback}")

    if not approved and retry_count < 2:
        print(f"[Critic] Not approved. Retry {retry_count + 1}/2")
        await _update_agent_log(state["task_id"], "Critic", "done", output_text=f"Retry {retry_count + 1}: {feedback}")
        return {
            "critic_approved": False,
            "critic_feedback": feedback,
            "retry_count": retry_count + 1,
        }
    if not approved and state["human_review"]:
        print(f"[Critic] Not approved. Requesting human review")
        await _update_agent_log(state["task_id"], "Critic", "done", output_text=f"Human review required: {feedback}")
        return {
            "critic_approved": False,
            "human_review_required": True,
            "critic_feedback": feedback,
        }
    print(f"[Critic] Approved (auto-approved after retries or LLM approved)")
    await _update_agent_log(state["task_id"], "Critic", "done", output_text="Approved")
    return {
        "critic_approved": True,
        "critic_feedback": "",
        "human_review_required": False,
    }


async def memory_node(state: AgentState) -> dict:
    print(f"[Memory] Storing subtask {state['current_subtask_index'] + 1}/{len(state['subtasks'])}")
    await _update_agent_log(state["task_id"], "Memory", "running")
    await MemoryAgent().store(
        state["task_id"],
        state["task_description"],
        state["current_output"],
    )
    new_index = state["current_subtask_index"] + 1
    if new_index < len(state["subtasks"]):
        print(f"[Memory] Moving to next subtask: {state['subtasks'][new_index]}")
        await _update_agent_log(state["task_id"], "Memory", "done", output_text=f"Stored subtask {state['current_subtask_index'] + 1}")
        return {
            "current_subtask_index": new_index,
            "research_context": "",
            "current_output": "",
            "critic_approved": False,
            "retry_count": 0,
            "human_review_required": False,
        }
    print(f"[Memory] All subtasks completed. Ending workflow.")
    await _update_agent_log(state["task_id"], "Memory", "done", output_text="All subtasks completed")
    return {
        "current_subtask_index": new_index,
        "final_output": state["current_output"],
    }


async def human_wait_node(state: AgentState) -> dict:
    """Poll the DB every 3 s for a human decision. Timeout → auto-approve."""
    from db.database import AsyncSessionLocal
    from db.models import Task
    from sqlalchemy import select
    import asyncio

    timeout = 300  # 5 minutes
    elapsed = 0
    while elapsed < timeout:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Task).where(Task.id == state["task_id"])
            )
            task = result.scalar_one_or_none()
            if task and task.human_approved is not None:
                if task.human_approved:
                    return {
                        "human_review_required": False,
                        "critic_approved": True,
                        "human_approved": True,
                    }
                else:
                    return {
                        "human_review_required": False,
                        "critic_approved": False,
                        "retry_count": 0,
                        "human_feedback": task.human_feedback or "",
                        "human_approved": False,
                    }
        await asyncio.sleep(3)
        elapsed += 3

    # Timeout: auto-approve
    return {
        "human_review_required": False,
        "critic_approved": True,
    }


# ─── Conditional edge routers ─────────────────────────────────────────

_RESEARCH_TRIGGERS = [
    "find", "search", "research", "look up",
    "what is", "latest", "current", "recent",
    "discover", "investigate",
]


def route_after_plan(state: AgentState) -> str:
    subtask = state["subtasks"][state["current_subtask_index"]]
    if any(k in subtask.lower() for k in _RESEARCH_TRIGGERS):
        return "research"
    return "execute"


def route_after_critic(state: AgentState) -> str:
    if state["human_review_required"]:
        return "human_wait"
    if not state["critic_approved"]:
        return "execute"
    return "memory"


def route_after_memory(state: AgentState) -> str:
    print(f"[Router] After memory - current_subtask_index: {state['current_subtask_index']}, total subtasks: {len(state['subtasks'])}")
    if state["current_subtask_index"] < len(state["subtasks"]):
        subtask = state["subtasks"][state["current_subtask_index"]]
        print(f"[Router] Next subtask: '{subtask}'")
        research_triggers = ["find", "search", "research",
                           "look up", "what is", "latest",
                           "current", "recent", "discover",
                           "investigate"]
        if any(k in subtask.lower() for k in research_triggers):
            print(f"[Router] Routing to: research")
            return "research"
        print(f"[Router] Routing to: execute")
        return "execute"
    print(f"[Router] Routing to: __end__")
    return "__end__"


# ─── Build and compile the graph ──────────────────────────────────────

def _build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("plan",       plan_node)
    graph.add_node("research",   research_node)
    graph.add_node("execute",    execute_node)
    graph.add_node("critic",     critic_node)
    graph.add_node("memory",     memory_node)
    graph.add_node("human_wait", human_wait_node)

    graph.set_entry_point("plan")

    graph.add_conditional_edges("plan", route_after_plan, {
        "research": "research",
        "execute":  "execute",
    })
    graph.add_edge("research", "execute")
    graph.add_edge("execute",  "critic")
    graph.add_conditional_edges("critic", route_after_critic, {
        "human_wait": "human_wait",
        "execute":    "execute",
        "memory":     "memory",
    })
    graph.add_edge("human_wait", "critic")
    graph.add_conditional_edges("memory", route_after_memory, {
        "research": "research",
        "execute":  "execute",
        "__end__":  END,
    })

    return graph.compile()


compiled_graph = _build_graph()
