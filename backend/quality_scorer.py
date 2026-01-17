"""
Quality Scorer
Evaluates output quality across models using consistency and other metrics
"""

import logging
from typing import List, Dict
from collections import defaultdict
import statistics
from schemas import ReplayResult, QualityMetrics
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class QualityScorer:
    """Evaluates quality of model outputs"""
    
    def calculate_consistency_score(self, outputs: List[str]) -> float:
        """
        Calculate consistency across multiple model outputs
        Uses pairwise similarity and averages
        
        Returns: Score from 0.0 (completely different) to 1.0 (identical)
        """
        if len(outputs) < 2:
            return 1.0
        
        # Remove None/empty outputs
        valid_outputs = [o for o in outputs if o]
        
        if len(valid_outputs) < 2:
            return 0.0
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(valid_outputs)):
            for j in range(i + 1, len(valid_outputs)):
                sim = self._string_similarity(valid_outputs[i], valid_outputs[j])
                similarities.append(sim)
        
        # Average similarity
        return statistics.mean(similarities) if similarities else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using SequenceMatcher"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def aggregate_metrics(self, results: List[ReplayResult]) -> Dict[str, QualityMetrics]:
        """
        Aggregate replay results into quality metrics per model
        
        Returns: Dict mapping model name to QualityMetrics
        """
        # Group results by model
        by_model = defaultdict(list)
        for result in results:
            by_model[result.model].append(result)
        
        # Calculate metrics for each model
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
            
            # Quality scores
            outputs = [r.output for r in successful if r.output]
            consistency_score = self.calculate_consistency_score(outputs)
            
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
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """
        Calculate overall quality score (0.0 to 1.0)
        
        Weighted combination of:
        - Consistency: 40%
        - Schema compliance: 30%
        - Success rate: 20%
        - Low refusal rate: 10%
        """
        success_rate = metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0.0
        refusal_score = 1.0 - metrics.refusal_rate
        
        quality = (
            (metrics.consistency_score * 0.4) +
            (metrics.schema_compliance_rate * 0.3) +
            (success_rate * 0.2) +
            (refusal_score * 0.1)
        )
        
        return min(1.0, max(0.0, quality))


# Singleton instance
quality_scorer = QualityScorer()
