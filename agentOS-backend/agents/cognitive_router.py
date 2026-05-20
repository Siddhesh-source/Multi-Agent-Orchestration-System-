"""
Cognitive Router Agent - USP #1
Replaces brittle keyword matching with LLM-as-judge for intelligent routing.

Estimates the epistemic gap between what the LLM already knows vs what it needs
to complete the subtask. Routes to Research only when complexity score > threshold.
"""
import json
from typing import TypedDict
from core.llm import llm, rate_limit_delay


class RoutingDecision(TypedDict):
    """Result of cognitive load analysis."""
    needs_research: bool
    confidence: float
    reasoning: str
    temporal_sensitivity: float  # 0-1: how time-sensitive is this?
    domain_specificity: float     # 0-1: how domain-specific is this?
    factual_verifiability: float  # 0-1: how fact-checkable is this?
    complexity_score: float       # 0-1: overall cognitive load


_SYSTEM_PROMPT = """You are a cognitive complexity analyzer for agent task routing.
Your job is to estimate the "epistemic gap" - the gap between what an LLM already knows
and what it needs to know to complete a subtask.

Analyze the subtask and return scores (0.0 to 1.0) for:
- temporal_sensitivity: Does this require CURRENT/LATEST information? (1.0 = must be today)
- domain_specificity: Is this highly specialized knowledge? (1.0 = very niche)
- factual_verifiability: Can this be fact-checked against sources? (1.0 = highly factual)

Then decide:
- needs_research: TRUE if temporal_sensitivity > 0.5 OR domain_specificity > 0.7 OR factual_verifiability > 0.6
- confidence: How confident are you in this analysis? (0.0-1.0)
- reasoning: Brief explanation of your decision

Return ONLY valid JSON, no markdown, no explanation outside JSON.
"""


class CognitiveRouter:
    """
    Intelligent router using LLM-as-judge for adaptive routing decisions.
    Replaces the brittle keyword list in graph.py:route_after_plan
    """
    
    COMPLEXITY_THRESHOLD = 0.5  # Route to research if complexity > threshold
    
    async def analyze(self, subtask: str) -> RoutingDecision:
        """
        Analyze a subtask and determine if it needs research.
        
        Args:
            subtask: The subtask description to analyze
            
        Returns:
            RoutingDecision with analysis results
        """
        prompt = f"""{_SYSTEM_PROMPT}

Subtask to analyze: {subtask}

Return JSON:
{{
  "needs_research": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "1-2 sentence explanation",
  "temporal_sensitivity": 0.0-1.0,
  "domain_specificity": 0.0-1.0,
  "factual_verifiability": 0.0-1.0,
  "complexity_score": 0.0-1.0
}}"""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        result = self._parse_response(response.content)
        
        # Fallback logic if LLM fails
        if result is None:
            result = self._keyword_fallback(subtask)
        
        print(f"[CognitiveRouter] Analyzed: '{subtask}'")
        print(f"[CognitiveRouter] Needs research: {result['needs_research']}, "
              f"Complexity: {result['complexity_score']:.2f}, Reasoning: {result['reasoning']}")
        
        return result
    
    def _parse_response(self, text: str) -> RoutingDecision | None:
        """Parse JSON from LLM response."""
        import json
        
        # Clean markdown fences
        cleaned = text.strip()
        for fence in ("```json", "```"):
            if cleaned.startswith(fence):
                cleaned = cleaned[len(fence):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            obj = json.loads(cleaned)
            
            # Validate required fields
            required = ["needs_research", "confidence", "reasoning", 
                       "temporal_sensitivity", "domain_specificity", 
                       "factual_verifiability", "complexity_score"]
            
            if all(k in obj for k in required):
                return {
                    "needs_research": bool(obj["needs_research"]),
                    "confidence": float(obj["confidence"]),
                    "reasoning": str(obj["reasoning"]),
                    "temporal_sensitivity": float(obj["temporal_sensitivity"]),
                    "domain_specificity": float(obj["domain_specificity"]),
                    "factual_verifiability": float(obj["factual_verifiability"]),
                    "complexity_score": float(obj["complexity_score"]),
                }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"[CognitiveRouter] Parse failed: {e}, raw: {text[:200]}")
        
        return None
    
    def _keyword_fallback(self, subtask: str) -> RoutingDecision:
        """
        Fallback when LLM fails - uses keyword matching as safety net.
        This ensures the system still works even if the LLM call fails.
        """
        lower = subtask.lower()
        
        # Temporal sensitivity keywords
        temporal_keywords = ["latest", "current", "recent", "today", "yesterday", 
                           "this week", "this month", "2024", "2025", "2026", "now"]
        
        # Domain specificity keywords  
        domain_keywords = ["medical", "legal", "financial", "scientific", "academic",
                         "research paper", "patent", "regulation", "compliance"]
        
        # Factual verifiability keywords
        factual_keywords = ["find", "search", "research", "look up", "discover",
                          "verify", "check", "confirm", "cite", "source", "reference"]
        
        # Calculate scores
        temporal = min(1.0, sum(1 for k in temporal_keywords if k in lower) * 0.5)
        domain = min(1.0, sum(1 for k in domain_keywords if k in lower) * 0.4)
        factual = min(1.0, sum(1 for k in factual_keywords if k in lower) * 0.35)
        
        # Overall complexity
        complexity = (temporal * 0.3) + (domain * 0.35) + (factual * 0.35)
        
        return {
            "needs_research": complexity > self.COMPLEXITY_THRESHOLD,
            "confidence": 0.5,
            "reasoning": f"Keyword fallback: temporal={temporal:.2f}, domain={domain:.2f}, factual={factual:.2f}",
            "temporal_sensitivity": temporal,
            "domain_specificity": domain,
            "factual_verifiability": factual,
            "complexity_score": complexity,
        }
    
    async def batch_analyze(self, subtasks: list[str]) -> list[RoutingDecision]:
        """
        Analyze multiple subtasks in parallel for efficiency.
        Uses asyncio.gather for concurrent LLM calls.
        """
        import asyncio
        
        tasks = [self.analyze(s) for s in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[CognitiveRouter] Error on task {i}: {result}")
                processed.append(self._keyword_fallback(subtasks[i]))
            else:
                processed.append(result)
        
        return processed


# Singleton instance
cognitive_router = CognitiveRouter()
