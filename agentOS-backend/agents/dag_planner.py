"""
DAG Planner Agent - USP #6: Causal Task Graph
Replaces linear sequential planning with a Directed Acyclic Graph (DAG)
where independent subtasks can execute in parallel.

Novel contribution: First open-source LangGraph system with automatic
subtask parallelism via DAG-aware planning.
"""
import json
from typing import List, TypedDict
from core.llm import llm, rate_limit_delay


class SubtaskNode(TypedDict):
    """A node in the task DAG."""
    id: str              # unique id, e.g. "t1", "t2", ...
    task: str            # human-readable subtask description
    depends_on: List[str]  # list of task ids this depends on
    agent_hint: str      # suggested agent type for this task
    estimated_complexity: str  # "low", "medium", "high"


class PlanResult(TypedDict):
    """Full planning result including DAG structure."""
    nodes: List[SubtaskNode]
    execution_order: List[List[str]]  # batches that can run in parallel
    estimated_total_tasks: int


_SYSTEM_PROMPT = """You are an advanced task planning agent that builds Directed Acyclic Graphs (DAGs) for task execution.

Given a complex task, decompose it into 3-8 specific subtasks and establish their DEPENDENCIES.

CRITICAL RULES:
1. Independent tasks (no common dependency) MUST have empty depends_on lists
2. Tasks that need results from other tasks MUST list those task ids in depends_on
3. Parallel execution: tasks with the same set of dependencies can run simultaneously
4. agent_hint must be one of: researcher, writer, editor, coder, debugger, tester, analyzer, visualizer, summarizer, doc_generator, fact_checker, executor

Return ONLY a valid JSON object. No markdown. No explanation outside JSON.

Example for "Write a research paper on quantum computing":
{
  "nodes": [
    {"id": "t1", "task": "Search for recent quantum computing papers (2022-2026)", "depends_on": [], "agent_hint": "researcher", "estimated_complexity": "medium"},
    {"id": "t2", "task": "Research quantum computing fundamentals and key applications", "depends_on": [], "agent_hint": "researcher", "estimated_complexity": "low"},
    {"id": "t3", "task": "Create paper outline and structure", "depends_on": ["t1", "t2"], "agent_hint": "writer", "estimated_complexity": "low"},
    {"id": "t4", "task": "Write introduction and background sections", "depends_on": ["t3"], "agent_hint": "writer", "estimated_complexity": "medium"},
    {"id": "t5", "task": "Write results and discussion sections", "depends_on": ["t3"], "agent_hint": "writer", "estimated_complexity": "high"},
    {"id": "t6", "task": "Generate citations and bibliography", "depends_on": ["t4", "t5"], "agent_hint": "fact_checker", "estimated_complexity": "low"},
    {"id": "t7", "task": "Final editing, formatting and export", "depends_on": ["t6"], "agent_hint": "editor", "estimated_complexity": "low"}
  ]
}

Notice t1 and t2 have no dependencies so they run IN PARALLEL. t4 and t5 also have the same dependencies (just t3) so they run IN PARALLEL.
"""


class DAGPlannerAgent:
    """
    Advanced planner that generates a DAG of subtasks instead of a flat list.
    Enables parallel execution of independent subtasks for 2-5x speedup.
    """
    
    async def run(self, task_description: str) -> PlanResult:
        """
        Plan a task and return a full DAG with dependency information.
        
        Args:
            task_description: The high-level task to decompose
            
        Returns:
            PlanResult with nodes (DAG) and computed execution order
        """
        prompt = f"{_SYSTEM_PROMPT}\n\nTask to decompose: {task_description}\n\nReturn the JSON:"
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        nodes = self._parse_nodes(response.content)
        
        if nodes is None:
            # Retry with stricter prompt
            retry_prompt = prompt + "\n\nIMPORTANT: Return ONLY a JSON object. No text before or after."
            response = llm.invoke(retry_prompt)
            await rate_limit_delay()
            nodes = self._parse_nodes(response.content)
        
        if nodes is None:
            # Fallback: linear sequential plan (no parallelism)
            print("[DAGPlanner] JSON parse failed twice. Using linear fallback.")
            nodes = self._build_linear_fallback(task_description)
        
        # Compute execution batches (parallel groups)
        execution_order = self._compute_execution_order(nodes)
        
        print(f"[DAGPlanner] Planned {len(nodes)} subtasks")
        print(f"[DAGPlanner] Execution batches: {execution_order}")
        
        # Log parallel opportunities
        parallel_count = sum(1 for batch in execution_order if len(batch) > 1)
        if parallel_count:
            print(f"[DAGPlanner] {parallel_count} parallel execution opportunities found")
        
        return {
            "nodes": nodes,
            "execution_order": execution_order,
            "estimated_total_tasks": len(nodes),
        }
    
    def _parse_nodes(self, text: str) -> List[SubtaskNode] | None:
        """Parse DAG nodes from LLM response."""
        cleaned = text.strip()
        for fence in ("```json", "```"):
            if cleaned.startswith(fence):
                cleaned = cleaned[len(fence):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            obj = json.loads(cleaned)
            nodes = obj.get("nodes", [])
            
            validated = []
            for node in nodes:
                if "id" in node and "task" in node:
                    validated.append({
                        "id": str(node["id"]),
                        "task": str(node["task"]),
                        "depends_on": [str(d) for d in node.get("depends_on", [])],
                        "agent_hint": str(node.get("agent_hint", "executor")),
                        "estimated_complexity": str(node.get("estimated_complexity", "medium")),
                    })
            
            return validated if validated else None
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
            print(f"[DAGPlanner] Parse error: {e}, raw: {text[:300]}")
            return None
    
    def _build_linear_fallback(self, task_description: str) -> List[SubtaskNode]:
        """Build a simple 3-step sequential plan as fallback."""
        return [
            {
                "id": "t1",
                "task": f"Research and gather information for: {task_description}",
                "depends_on": [],
                "agent_hint": "researcher",
                "estimated_complexity": "medium",
            },
            {
                "id": "t2",
                "task": f"Execute the main task: {task_description}",
                "depends_on": ["t1"],
                "agent_hint": "executor",
                "estimated_complexity": "high",
            },
            {
                "id": "t3",
                "task": "Review and finalize the output",
                "depends_on": ["t2"],
                "agent_hint": "editor",
                "estimated_complexity": "low",
            },
        ]
    
    def _compute_execution_order(self, nodes: List[SubtaskNode]) -> List[List[str]]:
        """
        Topological sort to find parallel execution batches.
        
        Returns a list of batches where each batch is a list of task ids
        that can run in parallel (all their dependencies are satisfied by
        previous batches).
        
        This is Kahn's algorithm for topological sort with parallel grouping.
        """
        # Build adjacency and in-degree maps
        node_ids = {n["id"] for n in nodes}
        in_degree = {n["id"]: 0 for n in nodes}
        dependents = {n["id"]: [] for n in nodes}  # who depends on me?
        
        for node in nodes:
            for dep in node["depends_on"]:
                if dep in node_ids:
                    in_degree[node["id"]] += 1
                    dependents[dep].append(node["id"])
        
        # Nodes with no dependencies can start first
        ready = [nid for nid, degree in in_degree.items() if degree == 0]
        batches = []
        
        while ready:
            # All ready tasks form a parallel batch
            batches.append(list(sorted(ready)))
            next_ready = []
            
            for nid in ready:
                for dependent in dependents[nid]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_ready.append(dependent)
            
            ready = next_ready
        
        # If there are remaining nodes, there's a cycle - append them as final batch
        remaining = [nid for nid, degree in in_degree.items() if degree > 0]
        if remaining:
            print(f"[DAGPlanner] WARNING: Cycle detected in DAG! Remaining: {remaining}")
            batches.append(remaining)
        
        return batches
    
    def get_node_by_id(self, nodes: List[SubtaskNode], task_id: str) -> SubtaskNode | None:
        """Find a node by its id."""
        for node in nodes:
            if node["id"] == task_id:
                return node
        return None
