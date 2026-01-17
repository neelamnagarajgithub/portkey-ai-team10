"""
Quality Scorer - Optimized for Speed
Uses fast string similarity instead of slow Pinecone embeddings
"""

import logging
from typing import List, Dict
from collections import defaultdict
import statistics
import re
from difflib import SequenceMatcher
from backend.schemas import ReplayResult, QualityMetrics

logger = logging.getLogger(__name__)


class QualityScorer:
    """Evaluates quality using fast similarity metrics"""
    
    def __init__(self):
        logger.info("✓ Quality Scorer initialized (fast mode)")
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Fast multi-metric string similarity"""
        # Sequence similarity (0-1)
        seq_sim = SequenceMatcher(None, str1, str2).ratio()
        
        # Jaccard similarity on words
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        jaccard = len(words1 & words2) / len(words1 | words2) if (words1 or words2) else 0.0
        
        # Length similarity
        len1, len2 = len(str1), len(str2)
        len_sim = min(len1, len2) / max(len1, len2) if (len1 > 0 and len2 > 0) else 0.0
        
        # Weighted combination
        return (seq_sim * 0.5) + (jaccard * 0.3) + (len_sim * 0.2)
    
    def calculate_consistency_score(self, outputs: List[str]) -> float:
        """Calculate consistency using fast string similarity"""
        if len(outputs) < 2:
            return 1.0
        
        valid_outputs = [o for o in outputs if o and len(o.strip()) > 0]
        
        if len(valid_outputs) < 2:
            return 0.0
        
        # Calculate all pairwise similarities
        similarities = []
        for i in range(len(valid_outputs)):
            for j in range(i + 1, len(valid_outputs)):
                sim = self._string_similarity(valid_outputs[i], valid_outputs[j])
                similarities.append(sim)
        
        return statistics.mean(similarities) if similarities else 0.0
    
    def _assess_completeness(self, output: str) -> float:
        """Assess if output is complete"""
        score = 1.0
        
        # Ends properly
        if not output.rstrip().endswith(('.', '!', '?', '"', "'", ')', ']', '}')):
            score -= 0.3
        
        # Has sufficient content
        word_count = len(output.split())
        if word_count < 5:
            score -= 0.3
        elif word_count < 10:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_coherence(self, output: str) -> float:
        """Assess coherence of output"""
        score = 1.0
        
        sentences = [s.strip() for s in re.split(r'[.!?]+', output) if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Check average sentence length
        avg_len = statistics.mean([len(s.split()) for s in sentences])
        if avg_len < 3 or avg_len > 50:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_informativeness(self, output: str) -> float:
        """Assess information density"""
        words = output.split()
        if not words:
            return 0.0
        
        filler = {'uh', 'um', 'like', 'actually', 'basically', 'just', 'really'}
        density = sum(1 for w in words if w.lower() not in filler) / len(words)
        
        return density
    
    def _assess_formatting(self, output: str) -> float:
        """Assess formatting quality"""
        score = 1.0
        
        # No excessive whitespace
        if '  ' in output:
            score -= 0.1
        
        # Balanced code blocks
        if '```' in output and output.count('```') % 2 != 0:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def aggregate_metrics(self, results: List[ReplayResult]) -> Dict[str, QualityMetrics]:
        """Aggregate metrics across all results"""
        by_model = defaultdict(list)
        by_prompt = defaultdict(list)
        
        for result in results:
            by_model[result.model].append(result)
            if result.success and result.output:  # Only include successful results with output
                by_prompt[result.prompt_id].append(result)
        
        metrics = {}
        
        for model, model_results in by_model.items():
            total_calls = len(model_results)
            successful = [r for r in model_results if r.success]
            failed = [r for r in model_results if not r.success]
            refusals = [r for r in model_results if r.is_refusal]
            
            successful_count = len(successful)
            failed_count = len(failed)
            refusal_rate = len(refusals) / total_calls if total_calls > 0 else 0.0
            
            # Cost metrics
            costs = [r.cost_usd for r in successful if r.cost_usd > 0]
            avg_cost = statistics.mean(costs) if costs else 0.0
            total_cost = sum(costs)
            
            # Latency metrics
            latencies = [r.latency_ms for r in successful if r.latency_ms > 0]
            avg_latency = statistics.mean(latencies) if latencies else 0.0
            p50_latency = statistics.median(latencies) if latencies else 0.0
            p95_latency = self._percentile(latencies, 0.95) if latencies else 0.0
            
            # Consistency: Only if we have successful outputs
            consistency_score = 0.0  # Default for failed models
            
            if successful_count > 0:  # Only calculate if model succeeded at least once
                consistency_scores = []
                for prompt_id in by_prompt:
                    prompt_results = by_prompt[prompt_id]
                    
                    # Get this model's output
                    model_output = next((r.output for r in prompt_results if r.model == model and r.output), None)
                    
                    if model_output:
                        # Compare to other models' outputs
                        other_outputs = [r.output for r in prompt_results if r.model != model and r.output]
                        if other_outputs:  # Only if there are other outputs to compare
                            for other in other_outputs:
                                sim = self._string_similarity(model_output, other)
                                consistency_scores.append(sim)
                
                consistency_score = statistics.mean(consistency_scores) if consistency_scores else 0.5  # Default to 0.5 if no comparisons
            
            # Schema compliance
            schema_compliant = [r for r in successful if r.schema_valid]
            schema_compliance_rate = len(schema_compliant) / successful_count if successful_count > 0 else 0.0
            
            metrics[model] = QualityMetrics(
                model=model,
                total_calls=total_calls,
                successful_calls=successful_count,
                failed_calls=failed_count,
                refusal_rate=refusal_rate,
                avg_cost_per_call=avg_cost,
                total_cost=total_cost,
                avg_latency_ms=avg_latency,
                p50_latency_ms=p50_latency,
                p95_latency_ms=p95_latency,
                consistency_score=consistency_score,
                schema_compliance_rate=schema_compliance_rate
            )
            
            if successful_count > 0:
                logger.info(
                    f"📊 {model}: "
                    f"quality={consistency_score:.3f}, "
                    f"cost=${avg_cost:.6f}, "
                    f"latency={avg_latency:.0f}ms, "
                    f"success={successful_count}/{total_calls}"
                )
            else:
                logger.warning(
                    f"⚠️  {model}: "
                    f"ALL CALLS FAILED ({failed_count}/{total_calls} failed)"
                )
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """
        Calculate overall quality score (0-1)
        
        Weighted combination:
        - Consistency: 40% (how similar to other models)
        - Schema compliance: 25% (valid outputs)
        - Success rate: 25% (didn't fail)
        - Refusal rate: 10% (didn't refuse)
        """
        success_rate = metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0.0
        refusal_score = 1.0 - metrics.refusal_rate
        
        quality = (
            (metrics.consistency_score * 0.40) +
            (metrics.schema_compliance_rate * 0.25) +
            (success_rate * 0.25) +
            (refusal_score * 0.10)
        )
        
        return min(1.0, max(0.0, quality))


# Singleton instance
quality_scorer = QualityScorer()