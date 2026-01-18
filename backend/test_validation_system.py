"""
Complete System Validation Test
Tests all validation methods: LLM Judge, Heuristics, Semantic Search
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from schemas import HistoricalPrompt
from llm_judge import LLMJudge, PortkeyLLMClient, JudgeModelSelector, CostTracker
from validator.heuristic_validator import HeuristicValidator
from db.historical_db import HistoricalDB
from validator.hybrid_validator import HybridValidator


async def test_llm_judge():
    """Test LLM-as-a-Judge evaluation"""
    print("\n" + "="*70)
    print("TEST 1: LLM Judge Evaluation")
    print("="*70)
    
    try:
        # Check API key
        api_key = os.getenv("PORTKEY_API_KEY")
        if not api_key:
            print("❌ PORTKEY_API_KEY not set. Skipping LLM judge test.")
            return False
        
        # Create judge with DI
        llm_client = PortkeyLLMClient(api_key)
        model_selector = JudgeModelSelector(default_tier="tier_3")  # Use cheap model for testing
        cost_tracker = CostTracker()
        
        judge = LLMJudge(
            llm_client=llm_client,
            model_selector=model_selector,
            cost_tracker=cost_tracker
        )
        
        # Test prompt
        prompt = HistoricalPrompt(
            messages=[
                {"role": "user", "content": "Explain quantum entanglement in simple terms"}
            ]
        )
        
        # Good output
        output = """Quantum entanglement is a phenomenon where two particles become connected 
        in such a way that the state of one instantly affects the state of the other, 
        regardless of the distance between them. It's like having two coins that always 
        land on opposite sides when flipped, no matter how far apart they are."""
        
        print("\n📝 Evaluating output...")
        score = await judge.evaluate_single(
            prompt=prompt,
            output=output,
            model_name="test-model"
        )
        
        print(f"\n✅ LLM Judge Results:")
        print(f"  Overall Score: {score.score}/100")
        print(f"  Correctness: {score.correctness}/100")
        print(f"  Helpfulness: {score.helpfulness}/100")
        print(f"  Instruction Following: {score.instruction_following}/100")
        print(f"  Reasoning: {score.reasoning}")
        
        # Get stats
        stats = judge.get_stats()
        print(f"\n💰 Cost Stats:")
        print(f"  Total calls: {stats['total_calls']}")
        print(f"  Total cost: ${stats['total_cost']:.6f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ LLM Judge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_heuristic_validator():
    """Test heuristic validation (fast, rule-based)"""
    print("\n" + "="*70)
    print("TEST 2: Heuristic Validator")
    print("="*70)
    
    try:
        validator = HeuristicValidator()
        
        test_cases = [
            {
                "name": "Good Output",
                "output": "Machine learning is a type of artificial intelligence that enables systems to learn from data without being explicitly programmed. It uses algorithms to identify patterns and make predictions.",
                "expected_range": (70, 100)
            },
            {
                "name": "Refusal",
                "output": "I cannot provide information about that topic.",
                "expected_range": (0, 30)
            },
            {
                "name": "Error",
                "output": "Error: Request failed with status code 500",
                "expected_range": (0, 30)
            },
            {
                "name": "Too Short",
                "output": "AI is ML.",
                "expected_range": (30, 70)
            }
        ]
        
        all_passed = True
        
        for test in test_cases:
            result = validator.validate(test["output"])
            passed = test["expected_range"][0] <= result.score <= test["expected_range"][1]
            
            status = "✅" if passed else "❌"
            print(f"\n{status} {test['name']}:")
            print(f"  Output: {test['output'][:60]}...")
            print(f"  Score: {result.score}/100")
            print(f"  Confidence: {result.confidence}")
            print(f"  Method: {result.method}")
            print(f"  Expected: {test['expected_range'][0]}-{test['expected_range'][1]}")
            
            if not passed:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Heuristic validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_historical_db():
    """Test semantic search with historical database"""
    print("\n" + "="*70)
    print("TEST 3: Historical DB with Semantic Search")
    print("="*70)
    
    try:
        db = HistoricalDB(cache_file="/tmp/test_validation_cache.pkl")
        
        # Add some test data
        print("\n📝 Adding test data to cache...")
        
        test_data = [
            {
                "prompt": "What is machine learning?",
                "model": "gpt-4o",
                "score": 92.0,
                "method": "llm_judge"
            },
            {
                "prompt": "Explain neural networks",
                "model": "gpt-4o",
                "score": 88.0,
                "method": "llm_judge"
            },
            {
                "prompt": "How does deep learning work?",
                "model": "gpt-4o",
                "score": 90.0,
                "method": "llm_judge"
            }
        ]
        
        for data in test_data:
            db.store_validation(
                prompt_text=data["prompt"],
                model=data["model"],
                output="Test output",
                score=data["score"],
                method=data["method"],
                confidence="HIGH"
            )
        
        # Test semantic search
        print("\n🔍 Testing semantic search...")
        
        similar_prompt = "What are machine learning algorithms?"
        result = db.find_similar(similar_prompt, "gpt-4o")
        
        if result:
            print(f"\n✅ Found similar prompts:")
            print(f"  Query: {similar_prompt}")
            print(f"  Average score: {result.avg_score:.1f}/100")
            print(f"  Confidence: {result.confidence}")
            print(f"  Sample count: {result.sample_count}")
            print(f"  Method: {result.method}")
            return True
        else:
            print(f"\n❌ No similar prompts found (might need more data)")
            return False
            
    except Exception as e:
        print(f"\n❌ Historical DB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_validator():
    """Test the complete hybrid validation system"""
    print("\n" + "="*70)
    print("TEST 4: Hybrid Validator (Complete System)")
    print("="*70)
    
    try:
        # Import hybrid validator
        from validator.hybrid_validator import hybrid_validator
        
        # Test prompt
        prompt = HistoricalPrompt(
            messages=[
                {"role": "user", "content": "Explain the difference between supervised and unsupervised learning"}
            ]
        )
        
        outputs = [
            {
                "model": "gpt-4o",
                "output": "Supervised learning uses labeled data where the algorithm learns from examples with known answers. Unsupervised learning works with unlabeled data to find patterns and structures on its own.",
                "expected": "MEDIUM"
            },
            {
                "model": "gpt-4o-mini",
                "output": "Error: timeout",
                "expected": "HIGH"
            },
            {
                "model": "claude",
                "output": "I cannot answer that question.",
                "expected": "HIGH"
            }
        ]
        
        print("\n📝 Testing hybrid validation...")
        
        for test in outputs:
            print(f"\n\nTesting {test['model']}:")
            print(f"Output: {test['output'][:80]}...")
            
            result = hybrid_validator.validate(
                prompt=prompt,
                output=test["output"],
                model=test['model'],
                phase="discovery"
            )
            
            print(f"\n  Score: {result.score}/100")
            print(f"  Method: {result.method}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Reasoning: {result.reasoning}")
            print(f"  Methods used: {', '.join(result.methods_used)}")
        
        # Get stats
        stats = hybrid_validator.get_stats()
        print(f"\n\n📊 Hybrid Validator Stats:")
        print(f"  LLM Judge calls: {stats['llm_judge_calls']}")
        print(f"  Heuristic checks: {stats['heuristic_calls']}")
        print(f"  DB hits: {stats['db_hits']}")
        print(f"  DB misses: {stats['db_misses']}")
        print(f"  Budget spent: ${stats['spent_budget']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Hybrid validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests"""
    print("\n" + "="*70)
    print(" VALIDATION SYSTEM COMPREHENSIVE TEST")
    print("="*70)
    
    results = {}
    
    # Test each component
    results["heuristics"] = test_heuristic_validator()
    results["historical_db"] = test_historical_db()
    results["llm_judge"] = await test_llm_judge()
    results["hybrid_system"] = await test_hybrid_validator()
    
    # Summary
    print("\n\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All tests passed! System is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
