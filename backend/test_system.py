"""
Test script to verify the backend is working
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from schemas import HistoricalPrompt, ReplayRequest
from replay_engine import replay_engine
from quality_scorer import quality_scorer
from recommender import recommendation_engine


def test_basic_replay():
    """Test basic replay functionality"""
    
    print("🧪 Testing Cost-Quality Optimization System\n")
    
    # Load demo prompts
    with open("../data/demo_prompts.json", "r") as f:
        prompts_data = json.load(f)
    
    # Take first 2 prompts for quick test
    prompts = [HistoricalPrompt(**p) for p in prompts_data[:2]]
    
    # Test with 2 models
    models = ["gpt-4o-mini", "gpt-3.5-turbo"]
    
    print(f"📝 Replaying {len(prompts)} prompts across {len(models)} models...")
    print(f"Models: {', '.join(models)}\n")
    
    # Run replay
    results = replay_engine.replay_batch(
        prompts=prompts,
        models=models,
        temperature=0.0,
        max_tokens=200
    )
    
    print(f"✅ Replay complete! {len(results)} results\n")
    
    # Show results
    for result in results:
        status = "✅ Success" if result.success else "❌ Failed"
        print(f"{status} | {result.model}")
        print(f"  Cost: ${result.cost_usd:.6f}")
        print(f"  Latency: {result.latency_ms:.0f}ms")
        print(f"  Tokens: {result.total_tokens}")
        if result.output:
            preview = result.output[:100] + "..." if len(result.output) > 100 else result.output
            print(f"  Output: {preview}")
        print()
    
    # Calculate metrics
    print("📊 Calculating quality metrics...\n")
    metrics_dict = quality_scorer.aggregate_metrics(results)
    
    for model, metrics in metrics_dict.items():
        quality = quality_scorer.calculate_quality_score(metrics)
        print(f"Model: {model}")
        print(f"  Quality Score: {quality:.2f}")
        print(f"  Avg Cost: ${metrics.avg_cost_per_call:.6f}")
        print(f"  Avg Latency: {metrics.avg_latency_ms:.0f}ms")
        print(f"  Success Rate: {metrics.successful_calls}/{metrics.total_calls}")
        print()
    
    # Generate recommendation
    print("🎯 Generating recommendation...\n")
    recommendation = recommendation_engine.recommend(metrics_dict)
    
    print(f"💡 RECOMMENDED: {recommendation.recommended_model}")
    print(f"Confidence: {recommendation.confidence}")
    print(f"Savings: {recommendation.cost_savings_pct:.1f}%")
    print(f"Quality Retention: {recommendation.quality_retention_pct:.1f}%")
    print(f"\nReasoning: {recommendation.reasoning}")
    
    if recommendation.risks:
        print(f"\n⚠️  Risks:")
        for risk in recommendation.risks:
            print(f"  - {risk}")
    
    print("\n✨ Test complete!")


if __name__ == "__main__":
    try:
        test_basic_replay()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
