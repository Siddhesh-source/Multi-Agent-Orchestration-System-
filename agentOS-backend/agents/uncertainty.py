"""
Uncertainty Quantification Agent - USP #7
Estimates output confidence via ensemble sampling (multiple runs with temperature variation)
and measures semantic variance to flag potential hallucinations.

This directly addresses the hallucination problem in a measurable way.
No existing open-source agent OS does uncertainty quantification at the output level.
"""
import json
import asyncio
from typing import TypedDict
from datetime import datetime, timezone
from core.llm import llm, rate_limit_delay


class ConfidenceResult(TypedDict):
    """Uncertainty quantification result."""
    confidence_score: float      # 0-1 overall confidence
    is_reliable: bool            # True if confidence is trustworthy
    ensemble_variance: float     # Semantic variance across samples
    token_level_uncertainty: list[dict]  # Per-token uncertainty regions
    knowledge_gap_regions: list[dict]     # Areas that may be hallucinated
    recommendations: list[str]
    sample_count: int
    temperature_range: tuple[float, float]


class Sampler:
    """Wrapper around LLM to run with different temperatures."""
    
    async def sample(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Sample the LLM with specific temperature."""
        from langchain.schema import HumanMessage
        
        # Create a temperature-adjusted LLM
        temp_llm = llm.bind(temperature=temperature)
        response = temp_llm.invoke([HumanMessage(content=prompt)])
        await rate_limit_delay()
        
        return response.content


class UncertaintyAgent:
    """
    Estimates uncertainty/confidence for agent outputs using ensemble sampling.
    
    Method:
    1. Run the executor multiple times with different temperatures
    2. Compute semantic similarity between outputs
    3. Higher variance = lower confidence
    4. Identify knowledge gap regions (text betweenstable segments)
    
    Research: Compare calibration curves vs single-sample baselines.
    """
    
    DEFAULT_SAMPLES = 3
    TEMPERATURE_RANGE = (0.3, 0.9)  # Low to high creativity
    
    def __init__(self):
        self._sampler = Sampler()
    
    async def quantify(
        self, 
        subtask: str,
        context: str = "",
        n_samples: int = DEFAULT_SAMPLES,
    ) -> ConfidenceResult:
        """
        Quantify uncertainty in an output.
        
        Args:
            subtask: The task that was executed
            context: Any context provided to the executor
            n_samples: Number of ensemble samples to generate
            
        Returns:
            ConfidenceResult with uncertainty metrics
        """
        print(f"[Uncertainty] Quantifying confidence for: '{subtask[:50]}...'")
        
        # Build prompt
        prompt = f"Context: {context}\n\n" if context else ""
        prompt += f"Task: {subtask}"
        
        # Run ensemble samples concurrently
        samples = await self._run_ensemble(prompt, n_samples)
        
        if len(samples) < 2:
            return self._default_result()
        
        # Compute variance
        variance = self._compute_semantic_variance(samples)
        
        # Convert variance to confidence (inverse relationship)
        # Low variance = high confidence
        confidence = max(0.0, 1.0 - variance)
        
        # Identify knowledge gap regions
        knowledge_gaps = self._find_knowledge_gaps(samples)
        
        # Determine if result is reliable
        is_reliable = (
            len(samples) >= 2 and
            variance < 0.5 and
            confidence > 0.3
        )
        
        # Build recommendations
        recommendations = []
        if confidence < 0.5:
            recommendations.append("HIGH UNCERTAINTY: Consider requesting human review")
        if confidence < 0.7:
            recommendations.append("MEDIUM UNCERTAINTY: Output may contain factual errors")
        if variance < 0.2:
            recommendations.append("LOW VARIANCE: Results are consistent across runs")
        if knowledge_gaps:
            recommendations.append(f"FLAG: {len(knowledge_gaps)} potential knowledge gap regions detected")
        if not is_reliable:
            recommendations.append("WARNING: Confidence score may be unreliable - insufficient sample diversity")
        
        print(f"[Uncertainty] Confidence: {confidence:.2f}, Variance: {variance:.2f}, "
              f"Reliable: {is_reliable}")
        
        return {
            "confidence_score": confidence,
            "is_reliable": is_reliable,
            "ensemble_variance": variance,
            "token_level_uncertainty": [],  # Simplification - could add n-gram analysis
            "knowledge_gap_regions": knowledge_gaps,
            "recommendations": recommendations,
            "sample_count": len(samples),
            "temperature_range": self.TEMPERATURE_RANGE,
        }
    
    async def _run_ensemble(self, prompt: str, n_samples: int) -> list[str]:
        """Run multiple samples with varying temperatures."""
        temps = [
            self.TEMPERATURE_RANGE[0],
            (self.TEMPERATURE_RANGE[0] + self.TEMPERATURE_RANGE[1]) / 2,
            self.TEMPERATURE_RANGE[1],
        ]
        
        # Run in parallel
        tasks = [self._sampler.sample(prompt, temp) for temp in temps[:n_samples]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        samples = [r for r in results if isinstance(r, str) and r.strip()]
        
        return samples
    
    def _compute_semantic_variance(self, samples: list[str]) -> float:
        """
        Compute semantic variance between samples.
        
        Uses a simple word overlap method as a proxy for semantic similarity.
        More sophisticated: would use embedding similarity.
        """
        if len(samples) < 2:
            return 1.0
        
        # Tokenize each sample
        tokenized = [
            set(s.lower().split()) for s in samples
        ]
        
        # Compute Jaccard similarity for each pair
        similarities = []
        for i in range(len(tokenized)):
            for j in range(i + 1, len(tokenized)):
                intersection = len(tokenized[i] & tokenized[j])
                union = len(tokenized[i] | tokenized[j])
                jaccard = intersection / union if union > 0 else 0
                similarities.append(jaccard)
        
        # Average similarity
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Variance = 1 - similarity (high similarity = low variance)
        return 1.0 - avg_similarity
    
    def _find_knowledge_gaps(self, samples: list[str]) -> list[dict]:
        """
        Identify potential knowledge gaps - regions where samples differ.
        
        Heuristic: Find sentences/phrases that appear in only some samples.
        These are likely creative additions or hallucinations.
        """
        if len(samples) < 2:
            return []
        
        gaps = []
        
        # Split each sample into sentences
        all_sentences = []
        sample_sentences = []
        
        for sample in samples:
            # Simple sentence split
            sentences = [s.strip() for s in sample.split(". ") if s.strip()]
            sample_sentences.append(sentences)
            all_sentences.extend(sentences)
        
        # Find sentences unique to few samples
        sentence_counts = {}
        for sentence in all_sentences:
            # Normalize for comparison
            norm = sentence.lower()
            sentence_counts[norm] = sentence_counts.get(norm, 0) + 1
        
        # Sentences appearing in < 50% of samples are potential gaps
        threshold = len(samples) / 2
        for sentence, count in sentence_counts.items():
            if 0 < count <= threshold:
                gaps.append({
                    "text": sentence,
                    "frequency": count,
                    "total_samples": len(samples),
                    "risk": "high" if count == 1 else "medium",
                })
        
        # Limit to top 5
        return gaps[:5]
    
    def _default_result(self) -> ConfidenceResult:
        """Default result when ensemble fails."""
        return {
            "confidence_score": 0.5,
            "is_reliable": False,
            "ensemble_variance": 1.0,
            "token_level_uncertainty": [],
            "knowledge_gap_regions": [],
            "recommendations": ["Unable to calculate confidence - using default"],
            "sample_count": 0,
            "temperature_range": (0.0, 0.0),
        }
    
    async def quick_confidence(self, output: str) -> float:
        """
        Quick confidence check for an existing output.
        
        Uses simpler heuristic when full ensemble isn't available.
        """
        # Simple heuristics
        confidence = 0.5
        
        # Penalize for hedge words (danger: may encode uncertainty poorly)
        hedge_words = ["might", "could", "possibly", "perhaps", "probably", "likely"]
        hedge_count = sum(1 for w in hedge_words if w in output.lower())
        confidence -= hedge_count * 0.05
        
        # Boost for factual indicators
        factual_indicators = ["according to", "research shows", "data indicates", "study found"]
        factual_count = sum(1 for w in factual_indicators if w in output.lower())
        confidence += factual_count * 0.1
        
        # Penalize for very long outputs (increases hallucination risk)
        if len(output) > 2000:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))


# Singleton instance
uncertainty_agent = UncertaintyAgent()
