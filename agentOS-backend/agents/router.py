"""
Router Agent - Intelligent Agent Dispatcher
Routes subtasks to the appropriate specialist agent based on task intent.

Part of the pluggable agent architecture for end-to-end workflows.
"""
import json
from typing import TypedDict
from core.llm import llm, rate_limit_delay


class RoutingDecision(TypedDict):
    """Result of routing decision."""
    agent: str              # selected agent name
    confidence: float       # 0-1 confidence in route
    reasoning: str          # why this agent was selected
    requires_context: bool  # does this need memory or research context?


# Agent registry with capability signatures
AGENT_REGISTRY = {
    "planner": {
        "capabilities": ["plan", "break down", "decompose", "outline", "structure"],
        "triggers": ["create a plan", "break down", "decompose", "outline structure"],
        "description": "Task planning and decomposition",
    },
    "researcher": {
        "capabilities": ["research", "search", "find", "investigate", "discover", "look up"],
        "triggers": ["search for", "find information", "research", "investigate", "latest", "current"],
        "requires_context": True,
        "description": "Web search and information gathering",
    },
    "writer": {
        "capabilities": ["write", "draft", "create", "compose", "generate content", "produce"],
        "triggers": ["write", "draft", "compose", "create article", "create paper", "blog post", "essay"],
        "description": "Content creation and drafting",
    },
    "editor": {
        "capabilities": ["edit", "revise", "proofread", "improve", "refine", "polish"],
        "triggers": ["edit", "revise", "proofread", "improve style", "polish", "fix grammar"],
        "description": "Editing and style improvement",
    },
    "summarizer": {
        "capabilities": ["summarize", "summarise", "tldr", "shorten", "extract", "condense"],
        "triggers": ["summary", "summarize", "key points", "takeaways", "tldr", "condense"],
        "description": "Summarization and key point extraction",
    },
    "coder": {
        "capabilities": ["code", "program", "implement", "build", "write code", "create function"],
        "triggers": ["python", "javascript", "code", "function", "class", "script", "app", "api", "implement"],
        "description": "Code generation",
    },
    "debugger": {
        "capabilities": ["debug", "fix", "error", "exception", "traceback", "troubleshoot"],
        "triggers": ["debug", "fix error", "exception", "troubleshoot", "bug", "broken"],
        "description": "Debugging and error fixing",
    },
    "tester": {
        "capabilities": ["test", "spec", "verify", "assert", "coverage"],
        "triggers": ["test", "unit test", "write tests", "coverage", "verify", "assert"],
        "description": "Test generation",
    },
    "code_reviewer": {
        "capabilities": ["review", "analyze code", "check", "audit", "security"],
        "triggers": ["review code", "analyze", "audit", "security check", "static analysis"],
        "description": "Code review and security analysis",
    },
    "literature_agent": {
        "capabilities": ["academic", "paper", "scholar", "arxiv", "citation"],
        "triggers": ["paper", "academic", "research paper", "arxiv", "scholar", "google scholar"],
        "requires_context": True,
        "description": "Academic literature search",
    },
    "citation_agent": {
        "capabilities": ["citation", "bibliography", "reference", "cite", "apa", "mla"],
        "triggers": ["citation", "bibliography", "references", "cite", "apa format", "mla"],
        "description": "Citation formatting and bibliography",
    },
    "fact_checker": {
        "capabilities": ["verify", "fact check", "confirm", "validate", "cross reference"],
        "triggers": ["verify", "fact check", "confirm", "validate", "is this true"],
        "requires_context": True,
        "description": "Fact verification",
    },
    "analyzer": {
        "capabilities": ["analyze", "statistics", "statistical", "trend", "insight"],
        "triggers": ["analyze", "statistics", "trend", "insight", "statistical analysis", "data"],
        "description": "Data analysis",
    },
    "visualizer": {
        "capabilities": ["visualize", "chart", "graph", "plot", "dashboard"],
        "triggers": ["chart", "graph", "visualize", "plot", "dashboard", "visualization"],
        "description": "Data visualization generation",
    },
    "cleaner": {
        "capabilities": ["clean", "deduplicate", "normalize", "preprocess"],
        "triggers": ["clean", "deduplicate", "normalize", "preprocess", "fix data"],
        "description": "Data cleaning",
    },
    "doc_generator": {
        "capabilities": ["generate pdf", "export pdf", "document", "format"],
        "triggers": ["pdf", "export", "document", "generate pdf", "convert to pdf"],
        "description": "Document generation (PDF, etc)",
    },
    "slide_generator": {
        "capabilities": ["slides", "presentation", "deck", "powerpoint"],
        "triggers": ["slides", "presentation", "powerpoint", "deck", "presentation"],
        "description": "Presentation generation",
    },
    "executor": {
        "capabilities": ["execute", "run", "perform", "do"],
        "triggers": ["execute", "run", "perform", "do the thing"],
        "description": "General task execution (fallback)",
    },
    "code_executor": {
        "capabilities": ["run code", "execute code", "test code", "run python"],
        "triggers": ["run code", "execute", "run and test", "run this"],
        "description": "Actually executes code and returns real output",
    },
    "self_healing_coder": {
        "capabilities": ["write and run", "build and test", "working code"],
        "triggers": ["working app", "create and run", "make it work", "self-healing"],
        "description": "Write code + run it + fix it until it works",
    },
    "real_doc_generator": {
        "capabilities": ["generate pdf file", "export pdf", "create pdf", "save pdf"],
        "triggers": ["generate pdf", "export to pdf", "save as pdf", "create pdf", "pdf file"],
        "description": "Generate actual PDF file for download",
    },
    "real_slide_generator": {
        "capabilities": ["generate pptx", "create powerpoint", "make slides", "pptx file"],
        "triggers": ["generate pptx", "powerpoint file", "create slides", "pptx", "slide deck"],
        "description": "Generate actual PowerPoint file for download",
    },
    "github_deployer": {
        "capabilities": ["deploy to github", "create repo", "push to github"],
        "triggers": ["github repo", "deploy", "create repository", "push code", "github"],
        "description": "Create GitHub repository with code",
    },
}


class RouterAgent:
    """
    Intelligent router that selects the best specialist agent for a subtask.
    
    Uses LLM-as-judge for intelligent selection when available,
    falls back to keyword matching when needed.
    """
    
    def __init__(self):
        self._registry = AGENT_REGISTRY
    
    async def route(self, subtask: str) -> RoutingDecision:
        """
        Determine which agent should handle this subtask.
        
        Args:
            subtask: The subtask description to route
            
        Returns:
            RoutingDecision with selected agent and reasoning
        """
        print(f"[Router] Routing subtask: '{subtask[:50]}...'")
        
        # Try LLM-based routing first
        try:
            result = await self._llm_route(subtask)
            if result:
                print(f"[Router] LLM chose: {result['agent']} (confidence: {result['confidence']:.2f})")
                return result
        except Exception as e:
            print(f"[Router] LLM routing failed: {e}")
        
        # Fallback to keyword matching
        result = self._keyword_route(subtask)
        print(f"[Router] Keyword fallback chose: {result['agent']}")
        
        return result
    
    async def _llm_route(self, subtask: str) -> RoutingDecision | None:
        """Use LLM to intelligently select the best agent."""
        registry_text = self._format_registry()
        
        prompt = f"""You are an intelligent task router. Given this subtask, 
select the best specialized agent to handle it.

Available agents and their capabilities:
{registry_text}

Subtask: {subtask}

Return ONLY a JSON object:
{{"agent": "agent_name", "confidence": 0.0-1.0, "reasoning": "1-sentence why this agent", "requires_context": true/false}}
No markdown, no extra text."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        return self._parse_route_response(response.content)
    
    def _format_registry(self) -> str:
        """Format agent registry for LLM prompt."""
        lines = []
        for name, info in self._registry.items():
            lines.append(f"- {name}: {info['description']}")
            lines.append(f"  Capabilities: {', '.join(info['capabilities'])}")
        return "\n".join(lines)
    
    def _parse_route_response(self, text: str) -> RoutingDecision | None:
        """Parse routing decision from LLM response."""
        cleaned = text.strip()
        for fence in ("```json", "```"):
            if cleaned.startswith(fence):
                cleaned = cleaned[len(fence):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            obj = json.loads(cleaned)
            agent = obj.get("agent", "executor")
            confidence = float(obj.get("confidence", 0.5))
            reasoning = str(obj.get("reasoning", ""))
            requires_context = bool(obj.get("requires_context", False))
            
            # Validate agent exists
            if agent not in self._registry:
                return None
            
            return {
                "agent": agent,
                "confidence": confidence,
                "reasoning": reasoning,
                "requires_context": requires_context,
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"[Router] Parse error: {e}")
            return None
    
    def _keyword_route(self, subtask: str) -> RoutingDecision:
        """Fallback keyword-based routing."""
        lower = subtask.lower()
        
        for name, info in self._registry.items():
            triggers = info.get("triggers", [])
            if any(t in lower for t in triggers):
                return {
                    "agent": name,
                    "confidence": 0.7,
                    "reasoning": f"keyword match: {triggers[0]}",
                    "requires_context": info.get("requires_context", False),
                }
        
        # Default fallback
        return {
            "agent": "executor",
            "confidence": 0.5,
            "reasoning": "default fallback",
            "requires_context": False,
        }
    
    def get_agent_description(self, agent_name: str) -> str:
        """Get the description for an agent."""
        return self._registry.get(agent_name, {}).get("description", "Unknown agent")
    
    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._registry.keys())


# Singleton instance
router_agent = RouterAgent()
