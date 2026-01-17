"""
Recommendation Engine
Analyzes replay results and provides intelligent model recommendations
"""

import logging
from typing import List, Dict
from schemas import QualityMetrics, Recommendation, ParetoPoint
from quality_scorer import quality_scorer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates smart recommendations for model selection"""
    
    def find_pareto_frontier(self, metrics_dict: Dict[str, QualityMetrics]) -> List[ParetoPoint]:
        """
        Find Pareto frontier (optimal cost-quality trade-offs)
        
        A point is on the frontier if no other point is better in both dimensions
        """
        points = []
        
        for model, metrics in metrics_dict.items():
            quality = quality_scorer.calculate_quality_score(metrics)
            cost = metrics.avg_cost_per_call
            
            points.append(ParetoPoint(
                model=model,
                cost=cost,
                quality=quality,
                is_optimal=False
            ))
        
        # Find non-dominated points
        for i, point in enumerate(points):
            is_dominated = False
            
            for j, other in enumerate(points):
                if i == j:
                    continue
                
                # Other point dominates if it's cheaper AND better quality
                if other.cost <= point.cost and other.quality >= point.quality:
                    if other.cost < point.cost or other.quality > point.quality:
                        is_dominated = True
                        break
            
            if not is_dominated:
                points[i].is_optimal = True
        
        return sorted(points, key=lambda p: p.cost)
    
    def recommend(
        self,
        metrics_dict: Dict[str, QualityMetrics],
        max_quality_loss: float = 0.05,  # 5% acceptable quality degradation
        min_cost_savings: float = 0.20    # 20% minimum savings to recommend switch
    ) -> Recommendation:
        """
        Generate smart recommendation
        
        Strategy:
        1. Find the most expensive model (baseline)
        2. Find cheapest model that maintains >95% quality
        3. Calculate savings and confidence
        """
        if not metrics_dict:
            raise ValueError("No metrics to analyze")
        
        # Find baseline (most expensive model)
        baseline_model = max(metrics_dict.items(), key=lambda x: x[1].avg_cost_per_call)
        baseline_name = baseline_model[0]
        baseline_metrics = baseline_model[1]
        baseline_quality = quality_scorer.calculate_quality_score(baseline_metrics)
        baseline_cost = baseline_metrics.avg_cost_per_call
        
        # Find candidates (cheaper models with acceptable quality)
        min_acceptable_quality = baseline_quality * (1 - max_quality_loss)
        
        candidates = []
        for model, metrics in metrics_dict.items():
            if model == baseline_name:
                continue
            
            quality = quality_scorer.calculate_quality_score(metrics)
            cost = metrics.avg_cost_per_call
            
            if quality >= min_acceptable_quality and cost < baseline_cost:
                savings_pct = ((baseline_cost - cost) / baseline_cost) * 100
                quality_retention_pct = (quality / baseline_quality) * 100
                
                candidates.append({
                    "model": model,
                    "cost": cost,
                    "quality": quality,
                    "savings_pct": savings_pct,
                    "quality_retention_pct": quality_retention_pct,
                    "metrics": metrics
                })
        
        # Sort by savings (highest first)
        candidates.sort(key=lambda x: x["savings_pct"], reverse=True)
        
        if not candidates:
            # No better alternative found
            return Recommendation(
                recommended_model=baseline_name,
                confidence="HIGH",
                baseline_model=baseline_name,
                cost_savings_pct=0.0,
                cost_savings_usd_per_1k=0.0,
                quality_retention_pct=100.0,
                reasoning=f"{baseline_name} is already the optimal choice. No cheaper alternatives maintain acceptable quality.",
                tested_on_calls=baseline_metrics.total_calls,
                risks=[]
            )
        
        # Recommend best candidate
        best = candidates[0]
        
        # Determine confidence
        confidence = self._determine_confidence(best["metrics"], best["savings_pct"])
        
        # Calculate savings per 1000 calls
        savings_per_1k = (baseline_cost - best["cost"]) * 1000
        
        # Identify risks
        risks = self._identify_risks(best["metrics"], baseline_metrics)
        
        reasoning = (
            f"{best['model']} offers {best['savings_pct']:.1f}% cost savings "
            f"while maintaining {best['quality_retention_pct']:.1f}% quality retention. "
            f"Validated on {best['metrics'].total_calls} test calls "
            f"with {(1 - best['metrics'].refusal_rate) * 100:.1f}% success rate."
        )
        
        return Recommendation(
            recommended_model=best["model"],
            confidence=confidence,
            baseline_model=baseline_name,
            cost_savings_pct=best["savings_pct"],
            cost_savings_usd_per_1k=savings_per_1k,
            quality_retention_pct=best["quality_retention_pct"],
            reasoning=reasoning,
            tested_on_calls=best["metrics"].total_calls,
            risks=risks
        )
    
    def _determine_confidence(self, metrics: QualityMetrics, savings_pct: float) -> str:
        """Determine confidence level of recommendation"""
        
        # High confidence criteria:
        # - Tested on >50 calls
        # - <5% refusal rate
        # - >90% success rate
        # - Significant savings (>30%)
        
        success_rate = metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0.0
        
        if (
            metrics.total_calls >= 50 and
            metrics.refusal_rate < 0.05 and
            success_rate > 0.9 and
            savings_pct > 30
        ):
            return "HIGH"
        elif (
            metrics.total_calls >= 20 and
            metrics.refusal_rate < 0.10 and
            success_rate > 0.8
        ):
            return "MEDIUM"
        else:
            return "LOW"
    
    def _identify_risks(
        self,
        candidate_metrics: QualityMetrics,
        baseline_metrics: QualityMetrics
    ) -> List[str]:
        """Identify potential risks in switching models"""
        
        risks = []
        
        # Latency risk
        if candidate_metrics.avg_latency_ms > baseline_metrics.avg_latency_ms * 1.5:
            risks.append(
                f"Latency increase: {candidate_metrics.avg_latency_ms:.0f}ms vs "
                f"{baseline_metrics.avg_latency_ms:.0f}ms baseline"
            )
        
        # Refusal rate risk
        if candidate_metrics.refusal_rate > baseline_metrics.refusal_rate * 2:
            risks.append(
                f"Higher refusal rate: {candidate_metrics.refusal_rate * 100:.1f}% vs "
                f"{baseline_metrics.refusal_rate * 100:.1f}% baseline"
            )
        
        # Consistency risk
        if candidate_metrics.consistency_score < baseline_metrics.consistency_score * 0.9:
            risks.append(
                f"Lower output consistency: {candidate_metrics.consistency_score:.2f} vs "
                f"{baseline_metrics.consistency_score:.2f} baseline"
            )
        
        # Sample size warning
        if candidate_metrics.total_calls < 30:
            risks.append(
                f"Limited test sample: Only {candidate_metrics.total_calls} calls analyzed"
            )
        
        return risks


# Singleton instance
recommendation_engine = RecommendationEngine()
