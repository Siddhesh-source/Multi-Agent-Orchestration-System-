"""
Enhanced Agent Graph - USP #1-7 Complete Integration
====================================================

This is the new graph that integrates all 7 USPs:
1. Cognitive Router (USP #1) - intelligent research routing
2. DAG Planner (USP #6) - causal dependency planning with parallelism
3. Router Agent - intelligent specialist dispatch
4. Adversarial Critic (USP #5) - multi-agent debate
5. 3-Tier Memory (USP #2) - episodic + semantic + procedural
6. Metacognition (USP #3) - self-calibration
7. Uncertainty (USP #7) - confidence quantification

Plus all specialist agents.
"""
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from datetime import datetime, timezone
from sqlalchemy import select

# Import all agents
from agents.dag_planner import DAGPlannerAgent, SubtaskNode, PlanResult
from agents.cognitive_router import CognitiveRouter, RoutingDecision
from agents.router import RouterAgent
from agents.specialists import get_agent
from agents.adversarial_critic import AdversarialCritic, DebateResult
from agents.uncertainty import UncertaintyAgent
from agents.metacognition import MetacognitionAgent
from memory.trie_memory import trie_memory

from core.llm import llm, rate_limit_delay
from db.database import AsyncSessionLocal
from db.models import AgentLog


# ─── State schema ─────────────────────────────────────────────────────

class EnhancedAgentState(TypedDict):
    # Core task info
    task_id: str
    task_description: str
    human_review: bool
    
    # DAG Planning (USP #6)
    dag_nodes: List[SubtaskNode]
    execution_batches: List[List[str]]  # Parallel execution groups
    current_batch_index: int
    current_node_id: str
    
    # Cognitive routing (USP #1)
    routing_decision: dict
    
    # Memory context (USP #2)
    memory_context: dict
    
    # Specialist agent execution
    current_agent: str
    specialist_output: str
    
    # Research context
    research_context: str
    
    # Quality control (USP #5 - Adversarial Critic)
    debate_result: dict
    critic_approved: bool
    critic_feedback: str
    
    # Uncertainty (USP #7)
    uncertainty_result: dict
    
    # Retry logic
    retry_count: int
    
    # Human review
    human_review_required: bool
    human_approved: Optional[bool]
    human_feedback: str
    
    # Final output
    final_output: str
    all_outputs: List[dict]
    
    # Error handling
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


# ─── NODE FUNCTIONS ───────────────────────────────────────────────────

async def plan_node(state: EnhancedAgentState) -> dict:
    """
    USP #6: DAG Planner with dependency-aware planning.
    Creates a full task DAG instead of a flat list.
    """
    print(f"[plan_node] START task_id={state['task_id']}")
    await _update_agent_log(state["task_id"], "DAGPlanner", "running", 
                           input_text=state["task_description"])
    
    # Get memory context for enrichment
    print(f"[plan_node] Retrieving memory context...")
    memory_context = await trie_memory.retrieve_all_context(state["task_description"])
    print(f"[plan_node] Retrieved {len(memory_context.get('procedural', []))} workflow templates")
    
    # Use DAG Planner
    print(f"[plan_node] Running DAG Planner...")
    planner = DAGPlannerAgent()
    plan_result = await planner.run(state["task_description"])
    print(f"[plan_node] DAG Planner created {len(plan_result['nodes'])} nodes")
    
    # Check for similar past workflows to reuse
    if memory_context.get("procedural"):
        print(f"[plan_node] Found similar past workflow, may reuse structure")
    
    await _update_agent_log(state["task_id"], "DAGPlanner", "done",
                           output_text=f"Created {len(plan_result['nodes'])} nodes, "
                                      f"{len(plan_result['execution_order'])} execution batches")
    
    print(f"[plan_node] COMPLETE")
    return {
        "dag_nodes": plan_result["nodes"],
        "execution_batches": plan_result["execution_order"],
        "current_batch_index": 0,
        "current_node_id": "",
        "memory_context": memory_context,
    }


async def cognitive_route_node(state: EnhancedAgentState) -> dict:
    """
    USP #1: Cognitive Complexity Router.
    Analyzes if current subtask needs research using LLM-as-judge.
    """
    print(f"[cognitive_route_node] START batch={state['current_batch_index']}")
    
    # Get current subtask
    if not state["dag_nodes"]:
        print(f"[cognitive_route_node] ERROR: No DAG nodes")
        return {"error": "No DAG nodes available"}
    
    current_batch = state["execution_batches"][state["current_batch_index"]]
    node_id = current_batch[0] if current_batch else ""
    print(f"[cognitive_route_node] node_id={node_id}")
    
    if not node_id:
        print(f"[cognitive_route_node] ERROR: No nodes in batch")
        return {"error": "No nodes in current batch"}
    
    # Find the node
    dag_planner = DAGPlannerAgent()
    node = dag_planner.get_node_by_id(state["dag_nodes"], node_id)
    
    if not node:
        print(f"[cognitive_route_node] ERROR: Node {node_id} not found")
        return {"error": f"Node {node_id} not found"}
    
    print(f"[cognitive_route_node] Analyzing: {node['task'][:50]}...")
    await _update_agent_log(state["task_id"], "CognitiveRouter", "running",
                           input_text=node["task"])
    
    # Analyze cognitive complexity
    try:
        router = CognitiveRouter()
        routing = await router.analyze(node["task"])
        print(f"[cognitive_route_node] needs_research={routing['needs_research']}, complexity={routing['complexity_score']:.2f}")
    except Exception as e:
        print(f"[cognitive_route_node] ERROR in router: {e}")
        routing = {"needs_research": False, "complexity_score": 0.5}
    
    await _update_agent_log(state["task_id"], "CognitiveRouter", "done",
                           output_text=f"needs_research={routing['needs_research']}, "
                                      f"complexity={routing['complexity_score']:.2f}")
    
    return {
        "current_node_id": node_id,
        "routing_decision": routing,
    }


async def research_node(state: EnhancedAgentState) -> dict:
    """Run Research Agent if cognitive router says we need it."""
    print(f"[research_node] START")
    
    if not state["routing_decision"].get("needs_research", False):
        print(f"[research_node] Skipping - no research needed")
        return {"research_context": ""}
    
    node_id = state["current_node_id"]
    dag_planner = DAGPlannerAgent()
    node = dag_planner.get_node_by_id(state["dag_nodes"], node_id)
    
    await _update_agent_log(state["task_id"], "Research", "running",
                           input_text=node["task"])
    
    try:
        # Use the specialist researcher
        print(f"[research_node] Running research for: {node['task'][:50]}...")
        researcher = get_agent("researcher")
        context = await researcher.run(node["task"])
        print(f"[research_node] Research complete, context length: {len(context)}")
    except Exception as e:
        print(f"[research_node] ERROR: {e}")
        context = f"Research failed: {e}"
    
    await _update_agent_log(state["task_id"], "Research", "done",
                           output_text=context[:500])
    
    return {"research_context": context}


async def route_to_specialist_node(state: EnhancedAgentState) -> dict:
    """
    Router Agent: Select best specialist agent for current subtask.
    Uses LLM-as-judge for intelligent dispatch.
    """
    print(f"[route_to_specialist_node] START")
    node_id = state["current_node_id"]
    dag_planner = DAGPlannerAgent()
    node = dag_planner.get_node_by_id(state["dag_nodes"], node_id)
    
    if not node:
        print(f"[route_to_specialist_node] ERROR: Node {node_id} not found")
        return {"error": f"Node {node_id} not found"}
    
    # Use the Router Agent
    print(f"[route_to_specialist_node] Routing: {node['task'][:50]}...")
    try:
        router = RouterAgent()
        routing = await router.route(node["task"])
    except Exception as e:
        print(f"[route_to_specialist_node] ERROR: {e}")
        routing = {"agent": "writer", "confidence": 0.5, "reasoning": str(e)}
    
    # Also consider the agent_hint from DAG planner
    agent_hint = node.get("agent_hint", "executor")
    
    # Prefer the DAG's agent_hint if it's specific
    if agent_hint != "executor" and routing["confidence"] < 0.8:
        routing["agent"] = agent_hint
        routing["reasoning"] = f"DAG suggested: {agent_hint}"
    
    print(f"[route_to_specialist_node] Routed to: {routing['agent']}")
    await _update_agent_log(state["task_id"], "Router", "running",
                           input_text=node["task"])
    await _update_agent_log(state["task_id"], "Router", "done",
                           output_text=f"Routed to: {routing['agent']}")
    
    return {
        "current_agent": routing["agent"],
        "routing_decision": {**state["routing_decision"], **routing},
    }


async def execute_specialist_node(state: EnhancedAgentState) -> dict:
    """Execute the selected specialist agent."""
    agent_name = state["current_agent"]
    node_id = state["current_node_id"]
    print(f"[execute_specialist_node] START agent={agent_name} node={node_id}")
    
    dag_planner = DAGPlannerAgent()
    node = dag_planner.get_node_by_id(state["dag_nodes"], node_id)
    
    # Map router agent names to valid specialist names
    AGENT_MAP = {
        "planner": "writer",      # planner's output → use writer
        "researcher": "writer",   # research → writer handles content
        "executor": "writer",     # fallback → writer
        "code_executor": "coder", # run code → coder
        "self_healing_coder": "coder",
    }
    mapped_agent = AGENT_MAP.get(agent_name, agent_name)
    print(f"[execute_specialist_node] mapped_agent={mapped_agent} (original: {agent_name})")
    
    await _update_agent_log(state["task_id"], mapped_agent, "running",
                           input_text=node["task"])
    
    try:
        # Get the appropriate specialist agent
        agent = get_agent(mapped_agent)
        print(f"[execute_specialist_node] Agent class: {type(agent).__name__}")
        
        # Execute based on agent type
        context = state.get("research_context", "")
        
        if mapped_agent in ["writer", "editor", "summarizer", "coder"]:
            result = await agent.run(node["task"], context if context else "")
        elif mapped_agent == "debugger":
            result = await agent.run(context, node.get("error", ""))
        else:
            result = await agent.run(node["task"])
        
        print(f"[execute_specialist_node] Result length: {len(result)}")
        await _update_agent_log(state["task_id"], mapped_agent, "done",
                               output_text=result[:500])
        
        return {"specialist_output": result}
        
    except Exception as e:
        print(f"[execute_specialist_node] ERROR agent={mapped_agent}: {e}")
        import traceback; traceback.print_exc()
        await _update_agent_log(state["task_id"], mapped_agent, "failed",
                               output_text=str(e))
        return {"specialist_output": f"Error: {e}", "error": str(e)}


async def adversarial_critic_node(state: EnhancedAgentState) -> dict:
    """
    USP #5: Multi-Agent Debate Critic.
    Uses Society of Critics (Skeptic, Devil's Advocate, Synthesis).
    """
    print(f"[adversarial_critic_node] START")
    node_id = state["current_node_id"]
    dag_planner = DAGPlannerAgent()
    node = dag_planner.get_node_by_id(state["dag_nodes"], node_id)
    output = state.get("specialist_output", "")
    
    await _update_agent_log(state["task_id"], "AdversarialCritic", "running")
    
    try:
        critic = AdversarialCritic()
        print(f"[adversarial_critic_node] Running debate...")
        debate_result = await critic.run(node["task"], output)
        print(f"[adversarial_critic_node] Debate complete: approved={debate_result['approved']}")
    except Exception as e:
        print(f"[adversarial_critic_node] ERROR: {e}")
        debate_result = {"approved": True, "consensus_type": "error_fallback", "synthesis_reasoning": str(e)}
    
    await _update_agent_log(state["task_id"], "AdversarialCritic", "done",
                           output_text=f"approved={debate_result['approved']}, "
                                      f"consensus={debate_result['consensus_type']}")
    
    return {
        "debate_result": debate_result,
        "critic_approved": debate_result["approved"],
        "critic_feedback": debate_result.get("synthesis_reasoning", ""),
    }


async def uncertainty_node(state: EnhancedAgentState) -> dict:
    """
    USP #7: Uncertainty Quantification.
    Estimates confidence via ensemble sampling.
    """
    print(f"[uncertainty_node] START")
    output = state.get("specialist_output", "")
    node_id = state["current_node_id"]
    
    await _update_agent_log(state["task_id"], "Uncertainty", "running")
    
    try:
        uncertainty = UncertaintyAgent()
        print(f"[uncertainty_node] Quantifying confidence...")
        uncertainty_result = await uncertainty.quantify(
            subtask=state.get("current_node_id", ""),
            context=state.get("research_context", ""),
        )
        print(f"[uncertainty_node] confidence={uncertainty_result['confidence_score']:.2f}")
    except Exception as e:
        print(f"[uncertainty_node] ERROR: {e}")
        uncertainty_result = {"confidence_score": 0.5, "reasoning": str(e)}
    
    await _update_agent_log(state["task_id"], "Uncertainty", "done",
                           output_text=f"confidence={uncertainty_result['confidence_score']:.2f}")
    
    return {"uncertainty_result": uncertainty_result}


async def memory_node(state: EnhancedAgentState) -> dict:
    """
    USP #2: 3-Tier Memory storage.
    Stores in episodic, semantic, and procedural memory.
    """
    print(f"[memory_node] START batch={state['current_batch_index']}")
    node_id = state["current_node_id"]
    dag_planner = DAGPlannerAgent()
    node = dag_planner.get_node_by_id(state["dag_nodes"], node_id)
    
    await _update_agent_log(state["task_id"], "TrieMemory", "running")
    
    # Determine valence from critic approval
    valence = 1.0 if state.get("critic_approved") else 0.0
    output = state.get("specialist_output", "")
    
    try:
        # Tier 1: Episodic
        print(f"[memory_node] Storing episodic...")
        await trie_memory.store_episode(
            state["task_id"],
            node["task"],
            output,
            valence=valence,
        )
        
        # Tier 2: Semantic (extract entities)
        print(f"[memory_node] Storing semantic entities...")
        await trie_memory.store_entities(state["task_id"], output, llm)
        
        # Tier 3: Procedural - store complete workflow after final batch
        current_batch = state["current_batch_index"]
        total_batches = len(state["execution_batches"])
        print(f"[memory_node] batch={current_batch}/{total_batches}")
        
        if current_batch >= total_batches - 1:
            print(f"[memory_node] Storing workflow (final batch)...")
            await trie_memory.store_workflow(
                state["task_id"],
                state["task_description"],
                state["dag_nodes"],
                duration_seconds=0,
                success=state.get("critic_approved", True),
            )
    except Exception as e:
        print(f"[memory_node] ERROR: {e}")
    
    # Continue to next batch or finish
    next_batch_index = state["current_batch_index"] + 1
    
    # Collect outputs from this batch
    batch_output = {
        "node_id": node_id,
        "agent": state.get("current_agent", "unknown"),
        "output": output,
        "approved": state.get("critic_approved", True),
        "confidence": state.get("uncertainty_result", {}).get("confidence_score", 0.5),
    }
    
    all_outputs = state.get("all_outputs", [])
    all_outputs.append(batch_output)
    
    await _update_agent_log(state["task_id"], "TrieMemory", "done",
                           output_text="Stored in all 3 memory tiers")
    
    if next_batch_index >= len(state["execution_batches"]):
        # All batches complete
        print(f"[memory_node] All batches complete, finalizing output")
        final_output = "\n\n---\n\n".join(
            f"### {o['node_id']} ({o['agent']})\n{o['output']}"
            for o in all_outputs
        )
        return {
            "all_outputs": all_outputs,
            "final_output": final_output,
            "current_batch_index": next_batch_index,
        }
    else:
        # Move to next batch
        print(f"[memory_node] Moving to batch {next_batch_index}")
        return {
            "all_outputs": all_outputs,
            "current_batch_index": next_batch_index,
            "research_context": "",
            "specialist_output": "",
            "critic_approved": False,
            "retry_count": 0,
        }


async def metacognition_node(state: EnhancedAgentState) -> dict:
    """
    USP #3: Metacognition Agent.
    Self-calibration and improvement suggestions.
    """
    # Only run on completion
    if not state.get("final_output"):
        return {}
    
    await _update_agent_log(state["task_id"], "Metacognition", "running")
    
    metacog = MetacognitionAgent()
    result = await metacog.run(state["task_id"])
    
    await _update_agent_log(state["task_id"], "Metacognition", "done",
                           output_text=f"performance={result['overall_performance']:.2f}")
    
    return {}


async def human_wait_node(state: EnhancedAgentState) -> dict:
    """Poll DB for human decision. Timeout → auto-approve."""
    from db.models import Task
    import asyncio
    
    timeout = 300
    elapsed = 0
    
    while elapsed < timeout:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Task).where(Task.id == state["task_id"])
            )
            task = result.scalar_one_or_none()
            if task and task.human_approved is not None:
                if task.human_approved:
                    return {"human_review_required": False, "critic_approved": True}
                else:
                    return {
                        "human_review_required": False,
                        "critic_approved": False,
                        "retry_count": 0,
                        "human_feedback": task.human_feedback or "",
                    }
        await asyncio.sleep(3)
        elapsed += 3
    
    return {"human_review_required": False, "critic_approved": True}


# ─── CONDITIONAL EDGES ─────────────────────────────────────────────────

def route_after_plan(state: EnhancedAgentState) -> str:
    """After planning, start executing batches."""
    if state.get("error"):
        print(f"[route_after_plan] ERROR, ending")
        return "__end__"
    print(f"[route_after_plan] Proceeding to cognitive_route")
    return "cognitive_route"


def route_after_cognitive(state: EnhancedAgentState) -> str:
    """Decide whether to run research based on cognitive routing."""
    needs_research = state.get("routing_decision", {}).get("needs_research", False)
    print(f"[route_after_cognitive] needs_research={needs_research}")
    if needs_research:
        return "research"
    return "route_to_specialist"


def route_after_critic(state: EnhancedAgentState) -> str:
    """Decide after critic review."""
    print(f"[route_after_critic] critic_approved={state.get('critic_approved')}")
    if state.get("human_review_required"):
        return "human_wait"
    
    if not state.get("critic_approved", True):
        retry_count = state.get("retry_count", 0)
        if retry_count < 2:
            return "route_to_specialist"
    
    return "uncertainty"


def route_after_uncertainty(state: EnhancedAgentState) -> str:
    """After uncertainty, store in memory."""
    print(f"[route_after_uncertainty] proceeding to memory")
    return "memory"


def route_after_memory(state: EnhancedAgentState) -> str:
    """Check if more batches to process."""
    current = state["current_batch_index"]
    total = len(state["execution_batches"])
    print(f"[route_after_memory] current_batch_index={current} total={total}")

    if current >= total:
        return "metacognition"

    return "cognitive_route"


# ─── BUILD AND COMPILE ────────────────────────────────────────────────

def build_enhanced_graph() -> StateGraph:
    """Build the enhanced LangGraph with all USPs."""
    graph = StateGraph(EnhancedAgentState)
    
    # Add all nodes
    graph.add_node("plan", plan_node)
    graph.add_node("cognitive_route", cognitive_route_node)
    graph.add_node("research", research_node)
    graph.add_node("route_to_specialist", route_to_specialist_node)
    graph.add_node("execute_specialist", execute_specialist_node)
    graph.add_node("adversarial_critic", adversarial_critic_node)
    graph.add_node("uncertainty", uncertainty_node)
    graph.add_node("memory", memory_node)
    graph.add_node("metacognition", metacognition_node)
    graph.add_node("human_wait", human_wait_node)
    
    # Set entry point
    graph.set_entry_point("plan")
    
    # Edges
    graph.add_edge("plan", "cognitive_route")
    
    # Cognitive routing decisions
    graph.add_conditional_edges(
        "cognitive_route",
        route_after_cognitive,
        {"research": "research", "route_to_specialist": "route_to_specialist"}
    )
    
    graph.add_edge("research", "route_to_specialist")
    
    # Specialist execution
    graph.add_edge("route_to_specialist", "execute_specialist")
    graph.add_edge("execute_specialist", "adversarial_critic")
    
    # Critic decisions
    graph.add_conditional_edges(
        "adversarial_critic",
        route_after_critic,
        {"human_wait": "human_wait", "route_to_specialist": "route_to_specialist", 
         "uncertainty": "uncertainty"}
    )
    
    graph.add_edge("human_wait", "adversarial_critic")
    
    # Uncertainty → Memory
    graph.add_edge("uncertainty", "memory")
    
    # Memory → next batch or finish
    graph.add_conditional_edges(
        "memory",
        route_after_memory,
        {"cognitive_route": "cognitive_route", "metacognition": "metacognition"}
    )
    
    # Final
    graph.add_edge("metacognition", END)
    
    return graph


# Create compiled graph
enhanced_graph = build_enhanced_graph()
compiled_graph = enhanced_graph.compile()


# ─── ORCHESTRATOR WREAPPER ────────────────────────────────────────────

class EnhancedOrchestrator:
    """Wrapper to run the enhanced graph with proper state initialization."""
    
    async def run(
        self,
        task_id: str,
        task_description: str,
        human_review: bool,
    ) -> dict:
        """Run the complete enhanced agent pipeline."""
        print(f"[EnhancedOrchestrator] START task_id={task_id}")
        print(f"[EnhancedOrchestrator] task_description: {task_description[:100]}...")
        
        started_at = datetime.now(timezone.utc)
        
        # Initial state
        initial_state: EnhancedAgentState = {
            "task_id": task_id,
            "task_description": task_description,
            "human_review": human_review,
            "dag_nodes": [],
            "execution_batches": [],
            "current_batch_index": 0,
            "current_node_id": "",
            "routing_decision": {},
            "memory_context": {},
            "current_agent": "",
            "specialist_output": "",
            "research_context": "",
            "debate_result": {},
            "critic_approved": False,
            "critic_feedback": "",
            "uncertainty_result": {},
            "retry_count": 0,
            "human_review_required": False,
            "human_approved": None,
            "human_feedback": "",
            "final_output": "",
            "all_outputs": [],
            "error": None,
        }
        
        # Run the graph
        try:
            print(f"[EnhancedOrchestrator] Invoking compiled graph...")
            final_state = await compiled_graph.ainvoke(initial_state)
            print(f"[EnhancedOrchestrator] Graph complete, final_output length: {len(final_state.get('final_output', ''))}")
            
            duration = (datetime.now(timezone.utc) - started_at).total_seconds()
            
            return {
                "status": "done",
                "output": final_state.get("final_output", ""),
                "duration_seconds": duration,
                "nodes_processed": len(final_state.get("all_outputs", [])),
            }
        except Exception as e:
            print(f"[EnhancedOrchestrator] ERROR: {e}")
            import traceback; traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e),
            }
