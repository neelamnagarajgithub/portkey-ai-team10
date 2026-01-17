"""
Example Usage: Multi-Method Validation System
Demonstrates how to use the hybrid validator with LLM judge, heuristics, and historical DB
"""

import json
from schemas import HistoricalPrompt, ReplayRequest
from replay_engine import replay_engine
from quality_scorer import quality_scorer
from recommender import recommendation_engine
from validator.hybrid_validator import hybrid_validator

# Example 1: Simple model comparison with validation
def example_basic_validation():
    """Test multiple models on sample prompts with automatic validation"""
    
    print("="*70)
    print(" Example 1: Basic Model Comparison with Validation")
    print("="*70)
    
    # Sample prompts
    prompts = [
        HistoricalPrompt(
            messages=[
                {"role": "user", "content": "Explain quantum entanglement in simple terms"}
            ]
        ),
        HistoricalPrompt(
            messages=[
                {"role": "user", "content": "Write a Python function to calculate Fibonacci numbers"}
            ]
        ),
        HistoricalPrompt(
            messages=[
                {"role": "user", "content": "Summarize the benefits of cloud computing"}
            ]
        )
    ]
    
    # Models to test
    models = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20250122"]
    
    # Replay with validation enabled
    print(f"\nTesting {len(models)} models on {len(prompts)} prompts...")
    results = replay_engine.replay_batch(
        prompts=prompts,
        models=models,
        use_validation=True,  # Enable hybrid validation
        validation_phase="discovery"  # Use LLM judge frequently
    )
    
    # Analyze results
    print("\n" + "="*70)
    print(" Results Summary")
    print("="*70)
    
    metrics = quality_scorer.aggregate_metrics(results)
    
    for model, metric in metrics.items():
        print(f"\n{model}:")
        print(f"  Success rate: {(metric.successful_calls / metric.total_calls) * 100:.1f}%")
        print(f"  Avg cost: ${metric.avg_cost_per_call:.6f}")
        print(f"  Avg latency: {metric.avg_latency_ms:.0f}ms")
        print(f"  Validation score: {metric.avg_validation_score:.1f}/100")  # NEW!
        print(f"  Overall quality: {quality_scorer.calculate_quality_score(metric):.2f}")
    
    # Get recommendation
    print("\n" + "="*70)
    print(" Recommendation")
    print("="*70)
    
    recommendation = recommendation_engine.recommend(metrics)
    print(f"\nRecommended model: {recommendation.recommended_model}")
    print(f"Confidence: {recommendation.confidence}")
    print(f"Cost savings: {recommendation.cost_savings_pct:.1f}%")
    print(f"Quality retention: {recommendation.quality_retention_pct:.1f}%")
    print(f"\nReasoning: {recommendation.reasoning}")
    
    if recommendation.risks:
        print(f"\nRisks:")
        for risk in recommendation.risks:
            print(f"  ⚠️  {risk}")
    
    # Validation stats
    print("\n" + "="*70)
    print(" Validation Statistics")
    print("="*70)
    
    stats = hybrid_validator.get_stats()
    print(f"\nLLM Judge calls: {stats['llm_judge_calls']}")
    print(f"Heuristic checks: {stats['heuristic_calls']}")
    print(f"DB cache hits: {stats['db_hits']}")
    print(f"DB cache misses: {stats['db_misses']}")
    print(f"Budget spent: ${stats['spent_budget']:.2f}")


# Example 2: Production mode (minimal LLM judge usage)
def example_production_mode():
    """Production usage with cost-optimized validation"""
    
    print("\n\n" + "="*70)
    print(" Example 2: Production Mode (Cost-Optimized)")
    print("="*70)
    
    # Many prompts in production
    prompts = [
        HistoricalPrompt(
            messages=[{"role": "user", "content": f"Explain concept {i}"}]
        )
        for i in range(20)  # 20 prompts
    ]
    
    # Test single model in production
    models = ["gpt-4o-mini"]
    
    print(f"\nReplaying {len(prompts)} prompts in production mode...")
    results = replay_engine.replay_batch(
        prompts=prompts,
        models=models,
        use_validation=True,
        validation_phase="production"  # Uses heuristics + DB, 10% LLM judge
    )
    
    # Show cache effectiveness
    stats = hybrid_validator.get_stats()
    total_validations = stats['llm_judge_calls'] + stats['heuristic_calls']
    cache_hit_rate = stats['db_hits'] / (stats['db_hits'] + stats['db_misses']) * 100 if (stats['db_hits'] + stats['db_misses']) > 0 else 0
    
    print(f"\nValidation efficiency:")
    print(f"  Total validations: {total_validations}")
    print(f"  LLM judge used: {stats['llm_judge_calls']} ({stats['llm_judge_calls']/total_validations*100:.1f}%)")
    print(f"  Heuristics used: {stats['heuristic_calls']}")
    print(f"  Cache hit rate: {cache_hit_rate:.1f}%")
    print(f"  Budget spent: ${stats['spent_budget']:.2f}")


# Example 3: Direct validation testing
def example_direct_validation():
    """Test validation methods directly"""
    
    print("\n\n" + "="*70)
    print(" Example 3: Direct Validation Testing")
    print("="*70)
    
    prompt = HistoricalPrompt(
        messages=[{"role": "user", "content": "What is machine learning?"}]
    )
    
    outputs = {
        "good": "Machine learning is a subset of AI that enables systems to learn from data...",
        "refusal": "I cannot provide information about machine learning.",
        "short": "ML is AI.",
        "error": "Error: Failed to process request"
    }
    
    for label, output in outputs.items():
        print(f"\n\nTesting: {label}")
        print(f"Output: {output[:60]}...")
        
        validation = hybrid_validator.validate(
            prompt=prompt,
            output=output,
            model="test-model",
            phase="discovery"
        )
        
        print(f"\nScore: {validation.score:.1f}/100")
        print(f"Method: {validation.method}")
        print(f"Confidence: {validation.confidence}")
        print(f"Reasoning: {validation.reasoning}")
        print(f"Methods used: {', '.join(validation.methods_used)}")


if __name__ == "__main__":
    # Run examples
    example_basic_validation()
    example_production_mode()
    example_direct_validation()
    
    print("\n\n" + "="*70)
    print(" All Examples Complete!")
    print("="*70)
