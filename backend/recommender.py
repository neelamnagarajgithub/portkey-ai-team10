"""
Recommendation Engine - Improved
Smarter model recommendations with better cost-quality analysis
"""

import logging
from typing import List, Dict
from backend.schemas import QualityMetrics, Recommendation, ParetoPoint
from backend.quality_scorer import quality_scorer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates smart recommendations for model selection"""
    
    def find_pareto_frontier(self, metrics_dict: Dict[str, QualityMetrics]) -> List[ParetoPoint]:
        """Find Pareto frontier (optimal cost-quality trade-offs)"""
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
        max_quality_loss: float = 0.05,
        min_cost_savings: float = 0.10
    ) -> Recommendation:
        """Generate smart recommendation"""
        
        if not metrics_dict:
            raise ValueError("No metrics to analyze")
        
        # Filter out completely failed models
        valid_metrics = {
            model: metrics 
            for model, metrics in metrics_dict.items() 
            if metrics.successful_calls > 0  # Must have at least 1 success
        }
        
        if not valid_metrics:
            raise ValueError("No models succeeded - all calls failed")
        
        # Calculate quality scores for valid models only
        model_scores = {
            model: quality_scorer.calculate_quality_score(metrics)
            for model, metrics in valid_metrics.items()
        }
        
        # Find baseline: HIGHEST QUALITY model
        baseline_name = max(model_scores, key=model_scores.get)
        baseline_metrics = valid_metrics[baseline_name]
        baseline_quality = model_scores[baseline_name]
        baseline_cost = baseline_metrics.avg_cost_per_call
        
        logger.info(f"📌 Baseline: {baseline_name} (quality={baseline_quality:.3f}, cost=${baseline_cost:.6f})")
        
        # Find candidates (cheaper models with acceptable quality)
        min_acceptable_quality = baseline_quality * (1 - max_quality_loss)
        
        candidates = []
        for model, metrics in metrics_dict.items():
            if model == baseline_name:
                continue
            
            quality = model_scores[model]
            cost = metrics.avg_cost_per_call
            
            # Must be cheaper AND have acceptable quality
            if quality >= min_acceptable_quality and cost < baseline_cost:
                savings_pct = ((baseline_cost - cost) / baseline_cost) * 100
                quality_retention_pct = (quality / baseline_quality) * 100
                
                # Calculate value score (quality * savings)
                value_score = quality * savings_pct
                
                candidates.append({
                    "model": model,
                    "cost": cost,
                    "quality": quality,
                    "savings_pct": savings_pct,
                    "quality_retention_pct": quality_retention_pct,
                    "value_score": value_score,
                    "metrics": metrics
                })
                
                logger.info(
                    f"  Candidate: {model} "
                    f"(quality={quality:.3f}, cost=${cost:.6f}, "
                    f"savings={savings_pct:.1f}%, value={value_score:.2f})"
                )
        
        # Sort by value score (quality * savings)
        candidates.sort(key=lambda x: x["value_score"], reverse=True)
        
        if not candidates:
            # No better alternative found
            return Recommendation(
                recommended_model=baseline_name,
                confidence="HIGH",
                baseline_model=baseline_name,
                cost_savings_pct=0.0,
                cost_savings_usd_per_1k=0.0,
                quality_retention_pct=100.0,
                reasoning=f"{baseline_name} is already optimal. No cheaper alternatives maintain ≥{min_acceptable_quality:.2f} quality.",
                tested_on_calls=baseline_metrics.total_calls,
                risks=[]
            )
        
        # Recommend best candidate (highest value score)
        best = candidates[0]
        
        # Determine confidence
        confidence = self._determine_confidence(best["metrics"], best["savings_pct"], best["quality_retention_pct"])
        
        # Calculate savings per 1000 calls
        savings_per_1k = (baseline_cost - best["cost"]) * 1000
        
        # Identify risks
        risks = self._identify_risks(best["metrics"], baseline_metrics)
        
        reasoning = (
            f"✨ {best['model']} offers **{best['savings_pct']:.1f}% cost savings** "
            f"while maintaining **{best['quality_retention_pct']:.1f}% quality retention**. "
            f"Validated on {best['metrics'].total_calls} test calls "
            f"with {(best['metrics'].successful_calls / best['metrics'].total_calls * 100):.1f}% success rate. "
            f"Value score: {best['value_score']:.2f} (quality × savings)."
        )
        
        logger.info(f"💡 Recommendation: {best['model']} (confidence={confidence})")
        
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
    
    def _determine_confidence(self, metrics: QualityMetrics, savings_pct: float, quality_retention_pct: float) -> str:
        """Determine confidence level of recommendation"""
        success_rate = metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0.0
        
        # HIGH confidence: lots of data, good quality retention, significant savings
        if (
            metrics.total_calls >= 10 and
            metrics.refusal_rate < 0.05 and
            success_rate > 0.9 and
            quality_retention_pct >= 95 and
            savings_pct > 20
        ):
            return "HIGH"
        
        # MEDIUM confidence: decent data, acceptable quality
        elif (
            metrics.total_calls >= 5 and
            metrics.refusal_rate < 0.10 and
            success_rate > 0.8 and
            quality_retention_pct >= 90
        ):
            return "MEDIUM"
        
        # LOW confidence: limited data or concerns
        else:
            return "LOW"
    
    def _identify_risks(
        self,
        candidate_metrics: QualityMetrics,
        baseline_metrics: QualityMetrics
    ) -> List[str]:
        """Identify potential risks in switching models"""
        risks = []
        
        # Latency risk (>50% slower)
        if candidate_metrics.avg_latency_ms > baseline_metrics.avg_latency_ms * 1.5:
            risks.append(
                f"⚠️ **Latency increase**: {candidate_metrics.avg_latency_ms:.0f}ms vs "
                f"{baseline_metrics.avg_latency_ms:.0f}ms baseline (+{((candidate_metrics.avg_latency_ms / baseline_metrics.avg_latency_ms - 1) * 100):.0f}%)"
            )
        
        # Refusal rate risk (doubled)
        if candidate_metrics.refusal_rate > baseline_metrics.refusal_rate * 2 and candidate_metrics.refusal_rate > 0.01:
            risks.append(
                f"⚠️ **Higher refusal rate**: {candidate_metrics.refusal_rate * 100:.1f}% vs "
                f"{baseline_metrics.refusal_rate * 100:.1f}% baseline"
            )
        
        # Consistency risk (>10% drop)
        if candidate_metrics.consistency_score < baseline_metrics.consistency_score * 0.9:
            risks.append(
                f"⚠️ **Lower output consistency**: {candidate_metrics.consistency_score:.2f} vs "
                f"{baseline_metrics.consistency_score:.2f} baseline (-{((1 - candidate_metrics.consistency_score / baseline_metrics.consistency_score) * 100):.0f}%)"
            )
        
        # Sample size warning
        if candidate_metrics.total_calls < 10:
            risks.append(
                f"⚠️ **Limited test sample**: Only {candidate_metrics.total_calls} calls analyzed. "
                f"Test on more data before production deployment."
            )
        
        return risks


# Singleton instance
recommendation_engine = RecommendationEngine()
