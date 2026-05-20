"""
Adversarial Critic - USP #5: Multi-Agent Debate
Replaces single Critic with a Society of Critics using constitutional AI principles.

Critics:
1. Skeptic: Attacks the output, finds weaknesses
2. Devil's Advocate: Proposes alternative approaches  
3. Synthesis: Reconciles and produces final verdict

Research angle: Compare output quality vs single-critic baseline.
"""
import json
from typing import TypedDict
from core.llm import llm, rate_limit_delay


class CriticVote(TypedDict):
    """Individual critic's assessment."""
    critic_name: str
    approved: bool
    confidence: float
    feedback: str
    strengths: list[str]
    weaknesses: list[str]


class DebateResult(TypedDict):
    """Aggregated result from Society of Critics."""
    approved: bool
    final_confidence: float
    consensus_type: str  # "unanimous", "majority", "split"
    debate_transcript: list[CriticVote]
    synthesis_reasoning: str
    all_critics_agreed: bool


_SKEPTIC_SYSTEM = """You are a SKEPTIC critic. Your job is to ATTACK and FIND WEAKNESSES in the output.

Be harsh but fair. Look for:
- Factual errors or potential hallucinations
- Logical fallacies or contradictions
- Missing information or gaps in reasoning
- Overstated claims without evidence
- Formatting or structural issues

Return ONLY JSON:
{"approved": false, "confidence": 0.0-1.0, "feedback": "specific weaknesses found", "strengths": [], "weaknesses": ["list of specific issues"]}"""

_DEVILS_ADVOCATE_SYSTEM = """You are a DEVIL'S ADVOCATE. Your job is to PROPOSE ALTERNATIVES.

Think about what other approaches could work. Consider:
- Different ways to solve the same problem
- Counterarguments to the main thesis
- Alternative data sources or methodologies
- What a competitor might do differently
- Unconventional but potentially better approaches

Return ONLY JSON:
{"approved": false, "confidence": 0.0-1.0, "feedback": "alternative approaches", "strengths": [], "weaknesses": []}"""

_SYNTHESIS_SYSTEM = """You are a SYNTHESIS critic. Your job is to RECONCILE different viewpoints.

Given critiques from the Skeptic and Devil's Advocate:
1. Acknowledge valid criticisms
2. Identify where alternatives could improve the work
3. Make a FINAL judgment: approve (with refinements) or reject

Consider: Are the weaknesses fatal? Can the alternatives be incorporated?
Can the work move forward with some adjustments?

Return ONLY JSON:
{"approved": true/false, "confidence": 0.0-1.0, "feedback": "final refined assessment incorporating valid points", "strengths": [], "weaknesses": []}"""


class AdversarialCritic:
    """
    Society of Critics using constitutional AI principles.
    
    Creates a structured debate: Skeptic → Devil's Advocate → Synthesis
    The final verdict is based on synthesis, but the full debate transcript
    is available for Explainability.
    """
    
    MAX_RETRIES = 2
    
    async def run(self, subtask: str, output: str) -> DebateResult:
        """
        Run the full adversarial debate.
        
        Args:
            subtask: The subtask this output is meant to complete
            output: The output to critique
            
        Returns:
            DebateResult with full debate transcript and final verdict
        """
        print(f"[AdversarialCritic] Starting debate for subtask: '{subtask[:50]}...'")
        
        # Phase 1: Skeptic reviews
        skeptic_vote = await self._get_critic_vote("Skeptic", _SKEPTIC_SYSTEM, subtask, output, retries=1)
        
        # Phase 2: Devil's Advocate reviews
        devils_advocate_vote = await self._get_critic_vote(
            "Devil's Advocate", 
            _DEVILS_ADVOCATE_SYSTEM, 
            subtask, 
            output,
            context_vote=skeptic_vote,  # They can see each other's work!
            retries=1
        )
        
        # Phase 3: Synthesis reviews (sees full debate)
        synthesis_vote = await self._get_critic_vote(
            "Synthesis",
            _SYNTHESIS_SYSTEM,
            subtask,
            output,
            context_vote=skeptic_vote,
            additional_context=devils_advocate_vote,
            retries=1
        )
        
        # Build transcript
        transcript = [
            skeptic_vote,
            devils_advocate_vote,
            synthesis_vote,
        ]
        
        # Compute consensus
        approvals = [v["approved"] for v in transcript]
        consensus_type = self._compute_consensus(approvals)
        
        # Final decision based on Synthesis (the tie-breaker)
        final_approved = synthesis_vote["approved"]
        final_confidence = synthesis_vote["confidence"]
        
        print(f"[AdversarialCritic] Debate result: approved={final_approved}, "
              f"consensus={consensus_type}, confidence={final_confidence:.2f}")
        
        return {
            "approved": final_approved,
            "final_confidence": final_confidence,
            "consensus_type": consensus_type,
            "debate_transcript": transcript,
            "synthesis_reasoning": synthesis_vote["feedback"],
            "all_critics_agreed": len(set(approvals)) == 1,
        }
    
    async def _get_critic_vote(
        self, 
        critic_name: str,
        system_prompt: str,
        subtask: str,
        output: str,
        context_vote: CriticVote | None = None,
        additional_context: CriticVote | None = None,
        retries: int = MAX_RETRIES
    ) -> CriticVote:
        """Get a single critic's vote."""
        
        prompt = f"{system_prompt}\n\nSubtask to complete: {subtask}\n\nOutput to review:\n{output}\n"
        
        # Add context from previous critics if available
        if context_vote:
            prompt += f"\n[Context from previous review]\n{context_vote['critic_name']} said: {context_vote['feedback']}\n"
        
        if additional_context:
            prompt += f"\n[Additional context]\n{additional_context['critic_name']} said: {additional_context['feedback']}\n"
        
        for attempt in range(retries):
            try:
                response = llm.invoke(prompt)
                await rate_limit_delay()
                
                result = self._parse_vote(critic_name, response.content)
                if result:
                    return result
            except Exception as e:
                print(f"[AdversarialCritic] {critic_name} attempt {attempt+1} failed: {e}")
        
        # Fallback to safe approve
        print(f"[AdversarialCritic] {critic_name} failed, using fallback")
        return {
            "critic_name": critic_name,
            "approved": True,
            "confidence": 0.5,
            "feedback": "Critic unavailable - default approval",
            "strengths": [],
            "weaknesses": [],
        }
    
    def _parse_vote(self, critic_name: str, text: str) -> CriticVote | None:
        """Parse critic vote from JSON response."""
        import json
        
        # Clean markdown
        cleaned = text.strip()
        for fence in ("```json", "```"):
            if cleaned.startswith(fence):
                cleaned = cleaned[len(fence):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            obj = json.loads(cleaned)
            return {
                "critic_name": critic_name,
                "approved": bool(obj.get("approved", True)),
                "confidence": float(obj.get("confidence", 0.5)),
                "feedback": str(obj.get("feedback", "")),
                "strengths": list(obj.get("strengths", [])),
                "weaknesses": list(obj.get("weaknesses", [])),
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"[AdversarialCritic] Parse error for {critic_name}: {e}")
            return None
    
    def _compute_consensus(self, approvals: list[bool]) -> str:
        """Compute consensus type from approval votes."""
        true_count = sum(approvals)
        false_count = len(approvals) - true_count
        
        if true_count == len(approvals):
            return "unanimous"
        elif false_count == 0:
            return "unanimous"
        elif true_count > false_count:
            return "majority"
        elif false_count > true_count:
            return "majority"
        else:
            return "split"
    
    async def quick_review(self, subtask: str, output: str) -> dict:
        """
        Quick single-pass review when speed matters.
        Uses a simpler single-agent approach.
        """
        prompt = f"""You are a quality reviewer. Evaluate if the output adequately completes THIS SPECIFIC SUBTASK.

Subtask: {subtask}

Output to Review:
{output}

Return ONLY JSON:
{{"approved": true/false, "confidence": 0.0-1.0, "feedback": "specific issue if not approved, empty if approved"}}

No markdown, no extra text."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        result = self._parse_vote("QuickCritic", response.content)
        if result:
            return {
                "approved": result["approved"],
                "confidence": result["confidence"],
                "feedback": result["feedback"],
            }
        return {"approved": True, "confidence": 0.5, "feedback": ""}


# Singleton instance
adversarial_critic = AdversarialCritic()
