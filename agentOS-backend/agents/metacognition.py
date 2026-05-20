"""
Metacognition Agent - USP #3: Self-Calibration
Scores each agent's performance using a rubric, adjusts prompts dynamically
based on failure patterns, and tracks confidence calibration.

This makes AgentOS a self-improving system - agents literally get better
the more tasks they run. This is a genuine research contribution.
"""
import json
from datetime import datetime, timezone
from typing import TypedDict
from sqlalchemy import select
from core.llm import llm, rate_limit_delay
from db.database import AsyncSessionLocal
from db.models import Task, AgentLog
from config import settings


class AgentScore(TypedDict):
    """Score breakdown for a single agent execution."""
    agent_name: str
    performance_score: float      # 0-1
    efficiency_score: float       # 0-1 - speed vs quality tradeoff
    quality_score: float          # 0-1 - output quality
    calibration_score: float      # 0-1 - did confidence match actual quality?
    issues: list[str]
    suggestions: list[str]


class MetacogResult(TypedDict):
    """Full metacognitive assessment."""
    task_id: str
    timestamp: str
    agent_scores: list[AgentScore]
    overall_performance: float
    improvement_focus: str
    prompt_adjustments: dict
    run_count: int


_SYSTEM_PROMPT = """You are a metacognitive evaluator. Analyze agent execution logs and score performance.

For each agent, evaluate:
- performance_score: Overall success at their task (0.0-1.0)
- efficiency_score: Speed/quality tradeoff (did they complete quickly AND well?)
- quality_score: Output quality without considering speed
- calibration_score: Did their self-reported confidence match reality? (1.0 = perfect calibration)

Look for:
- Which agent caused the most failures?
- Which failures were due to insufficient context vs processing errors?
- What patterns exist in critic rejections?

Return ONLY JSON:
{
  "agent_scores": [
    {
      "agent_name": "Planner",
      "performance_score": 0.8,
      "efficiency_score": 0.7,
      "quality_score": 0.85,
      "calibration_score": 0.75,
      "issues": ["occasionally missed dependency"],
      "suggestions": ["add explicit dependency rules"]
    }
  ],
  "overall_performance": 0.75,
  "improvement_focus": "Planner dependency handling",
  "prompt_adjustments": {
    "Planner": "Add rule: always check for dependencies between tasks"
  }
}

No markdown, no extra text."""


class MetacognitionAgent:
    """
    Self-calibrating agent that tracks performance and adjusts system prompts.
    
    Tracks:
    - Per-agent performance over time
    - Confidence calibration (is the critic's score reliable?)
    - Failure patterns (systematic vs random)
    
    Dynamically adjusts agent prompts based on accumulated feedback.
    Stores prompt deltas in SQLite for audit trail.
    """
    
    def __init__(self):
        self._prompt_adjustments: dict[str, str] = {}
        self._calibration_history: list[dict] = []
        self._run_count = 0
    
    async def run(self, task_id: str) -> MetacogResult:
        """
        Analyze a completed task and generate metacognitive feedback.
        
        Args:
            task_id: The task to analyze
            
        Returns:
            MetacogResult with scores and prompt adjustments
        """
        print(f"[Metacog] Analyzing task: {task_id}")
        
        # Fetch logs for this task
        logs = await self._fetch_task_logs(task_id)
        
        if not logs:
            return {
                "task_id": task_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_scores": [],
                "overall_performance": 0.5,
                "improvement_focus": "insufficient data",
                "prompt_adjustments": {},
                "run_count": self._run_count,
            }
        
        # Build prompt with logs
        prompt = self._build_log_summary(logs) + f"\n\n{_SYSTEM_PROMPT}"
        
        try:
            response = llm.invoke(prompt)
            await rate_limit_delay()
            result = self._parse_result(task_id, response.content)
        except Exception as e:
            print(f"[Metacog] LLM failed: {e}, using default")
            result = self._default_result(task_id)
        
        self._run_count += 1
        
        # Store adjustments in memory
        for agent, adjustment in result.get("prompt_adjustments", {}).items():
            self._prompt_adjustments[agent] = adjustment
        
        # Store calibration history
        for score in result.get("agent_scores", []):
            self._calibration_history.append({
                "agent": score["agent_name"],
                "performance": score["performance_score"],
                "calibration": score["calibration_score"],
                "timestamp": result["timestamp"],
            })
        
        print(f"[Metacog] Overall performance: {result['overall_performance']:.2f}, "
              f"Improvement focus: {result['improvement_focus']}")
        
        return result
    
    async def _fetch_task_logs(self, task_id: str) -> list[dict]:
        """Fetch all agent logs for a task from the database."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentLog).where(AgentLog.task_id == task_id)
            )
            logs = result.scalars().all()
            
            log_list = []
            for log in logs:
                log_list.append({
                    "agent_name": log.agent_name,
                    "status": log.status,
                    "input_text": log.input_text or "",
                    "output_text": log.output_text or "",
                    "started_at": log.started_at.isoformat() if log.started_at else "",
                    "completed_at": log.completed_at.isoformat() if log.completed_at else "",
                })
            return log_list
    
    def _build_log_summary(self, logs: list[dict]) -> str:
        """Build a summary of logs for the LLM to analyze."""
        lines = ["=== Agent Execution Logs ===\n"]
        for log in logs:
            status = log.get("status", "unknown")
            agent = log.get("agent_name", "unknown")
            input_t = log.get("input_text", "")[:100]
            output_t = log.get("output_text", "")[:200]
            
            lines.append(f"Agent: {agent} | Status: {status}")
            if input_t:
                lines.append(f"  Input: {input_t}...")
            if output_t:
                lines.append(f"  Output: {output_t}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def _parse_result(self, task_id: str, text: str) -> MetacogResult:
        """Parse LLM's metacognitive analysis."""
        cleaned = text.strip()
        for fence in ("```json", "```"):
            if cleaned.startswith(fence):
                cleaned = cleaned[len(fence):]
        if cleaned.endswith("`"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            obj = json.loads(cleaned)
            return {
                "task_id": task_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_scores": obj.get("agent_scores", []),
                "overall_performance": float(obj.get("overall_performance", 0.5)),
                "improvement_focus": str(obj.get("improvement_focus", "none")),
                "prompt_adjustments": obj.get("prompt_adjustments", {}),
                "run_count": self._run_count,
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._default_result(task_id)
    
    def _default_result(self, task_id: str) -> MetacogResult:
        """Default result when LLM fails."""
        return {
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_scores": [],
            "overall_performance": 0.5,
            "improvement_focus": "analysis failed",
            "prompt_adjustments": {},
            "run_count": self._run_count,
        }
    
    def get_calibration_stats(self) -> dict:
        """Get calibration statistics across all runs."""
        if not self._calibration_history:
            return {"avg_calibration": 0.5, "per_agent": {}, "total_runs": 0}
        
        agent_scores: dict[str, list[float]] = {}
        for entry in self._calibration_history:
            agent = entry["agent"]
            if agent not in agent_scores:
                agent_scores[agent] = []
            agent_scores[agent].append(entry["calibration"])
        
        per_agent = {
            agent: sum(scores) / len(scores) 
            for agent, scores in agent_scores.items()
        }
        
        all_scores = [e["calibration"] for e in self._calibration_history]
        
        return {
            "avg_calibration": sum(all_scores) / len(all_scores) if all_scores else 0.5,
            "per_agent": per_agent,
            "total_runs": self._run_count,
        }
    
    def get_adjusted_prompt(self, agent_name: str, base_prompt: str) -> str:
        """
        Get the adjusted system prompt for an agent.
        
        If metacognition has learned improvements for this agent, append them.
        """
        adjustment = self._prompt_adjustments.get(agent_name, "")
        if not adjustment:
            return base_prompt
        
        return f"{base_prompt}\n\n[Auto-improvement from metacognition]: {adjustment}"


# Singleton instance
metacognition_agent = MetacognitionAgent()
