"""
Complete End-to-End Test
Tests the full flow: Replay → Validation → Quality Scoring → Recommendation
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path so we can import without 'backend.' prefix
sys.path.insert(0, str(Path(__file__).parent))

from schemas import HistoricalPrompt
from replay_engine import ReplayEngine
from quality_scorer import QualityScorer
from recommender import RecommendationEngine

async def test_complete_flow():
    """Test the complete validation flow"""
    
    print("\n" + "="*70)
    print(" COMPLETE VALIDATION FLOW TEST")
    print("="*70)
    
    # Step 1: Create test prompts
    prompts = [
        HistoricalPrompt(
            messages=[{"role": "user", "content": "What is machine learning?"}]
        ),
        HistoricalPrompt(
            messages=[{"role": "user", "content": "What is the capital of France?"}]
        )
    ]
    
    # Step 2: Select models to test (OpenAI only - no Anthropic auth needed)
    models = [
        "gpt-4o",
        "gpt-4o-mini"
    ]
    
    print(f"\n📋 Test Setup:")
    print(f"  Prompts: {len(prompts)}")
    print(f"  Models: {models}")
    print(f"  Total calls: {len(prompts) * len(models)}")
    
    # Step 3: Run replay with validation
    print(f"\n🔄 Starting replay with hybrid validation...")
    
    engine = ReplayEngine()
    results = engine.replay_batch(
        prompts=prompts,
        models=models,
        use_validation=True,
        validation_phase="discovery"
    )
    
    print(f"\n✅ Replay complete: {len(results)} results")
    
    # Step 4: Check validation scores
    print(f"\n📊 Validation Results:")
    print("-" * 70)
    
    validated_count = 0
    for result in results:
        if result.validation_score is not None:
            validated_count += 1
            print(f"\n{result.model}:")
            print(f"  Output: {result.output[:100]}..." if result.output and len(result.output) > 100 else f"  Output: {result.output}")
            print(f"  Validation: {result.validation_score:.1f}/100")
            print(f"  Method: {result.validation_method}")
            print(f"  Confidence: {result.validation_confidence}")
            print(f"  Cost: ${result.cost_usd:.6f}")
    
    validation_rate = (validated_count / len(results)) * 100 if len(results) > 0 else 0
    print(f"\n📈 Validation Rate: {validation_rate:.0f}% ({validated_count}/{len(results)})")
    
    if validation_rate < 100:
        print(f"⚠️  Warning: Not all results were validated!")
    
    # Step 5: Calculate quality metrics
    print(f"\n📊 Calculating quality metrics...")
    
    scorer = QualityScorer()
    metrics_dict = scorer.aggregate_metrics(results)
    
    print(f"\n📈 Quality Metrics Per Model:")
    print("-" * 70)
    
    for model, metrics in metrics_dict.items():
        quality_score = scorer.calculate_quality_score(metrics)
        
        print(f"\n{model}:")
        print(f"  Quality Score: {quality_score:.3f}")
        print(f"  Avg Validation: {metrics.avg_validation_score:.1f}/100")
        print(f"  Consistency: {metrics.consistency_score:.3f}")
        print(f"  Schema Compliance: {metrics.schema_compliance_rate:.3f}")
        print(f"  Cost: ${metrics.avg_cost_per_call:.6f}")
        print(f"  Success Rate: {metrics.successful_calls}/{metrics.total_calls}")
    
    # Step 6: Get recommendation
    print(f"\n🎯 Getting recommendation...")
    
    recommender = RecommendationEngine()
    recommendation = recommender.recommend(
        metrics_dict=metrics_dict
    )
    
    print(f"\n💡 Recommendation:")
    print("-" * 70)
    print(f"  Recommended: {recommendation.recommended_model}")
    print(f"  Confidence: {recommendation.confidence}")
    print(f"  Baseline: {recommendation.baseline_model}")
    print(f"  Cost Savings: {recommendation.cost_savings_pct:.1f}%")
    print(f"  Quality Retention: {recommendation.quality_retention_pct:.1f}%")
    print(f"\n{recommendation.reasoning}")
    
    if recommendation.risks:
        print(f"\n⚠️  Risks:")
        for risk in recommendation.risks:
            print(f"  {risk}")
    
    # Step 7: Check fallback usage
    print(f"\n🔍 Validation Method Breakdown:")
    print("-" * 70)
    
    methods = {}
    for result in results:
        if result.validation_method:
            methods[result.validation_method] = methods.get(result.validation_method, 0) + 1
    
    for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / validated_count) * 100 if validated_count > 0 else 0
        print(f"  {method:20s}: {count:2d} ({percentage:5.1f}%)")
    
    # Step 8: Verify integration
    print(f"\n✅ Integration Check:")
    print("-" * 70)
    
    checks = {
        "Validation scores present": validated_count > 0,
        "Supabase working": any(r.validation_method == "historical_db" for r in results if r.validation_method),
        "Quality includes validation": any(m.avg_validation_score > 0 for m in metrics_dict.values()),
        "Recommendation generated": recommendation is not None
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    all_passed = all(checks.values())
    
    # Summary
    print(f"\n\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    if all_passed:
        print("✅ All systems working correctly!")
        print("\n📊 System is ready for:")
        print("  1. Scenario classification")
        print("  2. Per-scenario validation strategies")
        print("  3. Production deployment")
    else:
        print("⚠️  Some checks failed. Review the output above.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_complete_flow())
    exit(0 if success else 1)
