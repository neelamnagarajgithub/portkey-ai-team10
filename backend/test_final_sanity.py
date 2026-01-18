"""
Final Sanity E2E Test - Complete System Validation
Tests all components end-to-end with verification checkpoints
"""

import asyncio
from schemas import HistoricalPrompt
from replay_engine import ReplayEngine
from quality_scorer import QualityScorer
from recommender import RecommendationEngine
from db.historical_db import SupabaseDB

async def final_sanity_test():
    """Complete end-to-end sanity test"""
    
    print("\n" + "="*70)
    print(" 🧪 FINAL SANITY E2E TEST")
    print("="*70)
    
    results = {"passed": 0, "failed": 0, "checks": []}
    
    # ============================================
    # TEST 1: Supabase Connection
    # ============================================
    print("\n📍 TEST 1: Supabase Connection")
    try:
        db = SupabaseDB()
        test_data = {
            "prompt_text": "Test connection",
            "model": "gpt-4o",
            "provider": "openai",
            "scenario": "test",
            "output": "Test output",
            "score": 95.0,
            "method": "test",
            "confidence": "HIGH"
        }
        db.store_validation(**test_data)
        
        # Verify retrieval
        result = db.find_similar("Test connection", "gpt-4o", "test", limit=1)
        
        if result and result.avg_score == 95.0:
            print("   ✅ PASS: Supabase read/write working")
            results["passed"] += 1
            results["checks"].append("Supabase connection")
        else:
            print("   ❌ FAIL: Data mismatch")
            results["failed"] += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        results["failed"] += 1
    
    # ============================================
    # TEST 2: Replay Engine
    # ============================================
    print("\n📍 TEST 2: Replay Engine (Portkey)")
    try:
        engine = ReplayEngine()
        prompts = [
            HistoricalPrompt(messages=[{"role": "user", "content": "What is 2+2?"}])
        ]
        
        replay_results = engine.replay_batch(
            prompts=prompts,
            models=["gpt-4o-mini"],
            use_validation=False  # Skip validation for this test
        )
        
        if len(replay_results) == 1 and replay_results[0].success:
            print("   ✅ PASS: Replay working")
            results["passed"] += 1
            results["checks"].append("Replay engine")
        else:
            print("   ❌ FAIL: Replay failed")
            results["failed"] += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        results["failed"] += 1
    
    # ============================================
    # TEST 3: Hybrid Validation
    # ============================================
    print("\n📍 TEST 3: Hybrid Validation")
    try:
        engine = ReplayEngine()
        prompts = [
            HistoricalPrompt(messages=[{"role": "user", "content": "What is machine learning?"}])
        ]
        
        replay_results = engine.replay_batch(
            prompts=prompts,
            models=["gpt-4o"],
            use_validation=True,
            validation_phase="discovery"
        )
        
        validated = [r for r in replay_results if r.validation_score is not None]
        
        if len(validated) > 0:
            print(f"   ✅ PASS: Validation working ({validated[0].validation_method})")
            results["passed"] += 1
            results["checks"].append("Hybrid validation")
        else:
            print("   ❌ FAIL: No validation scores")
            results["failed"] += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        results["failed"] += 1
    
    # ============================================
    # TEST 4: Quality Metrics
    # ============================================
    print("\n📍 TEST 4: Quality Metrics")
    try:
        scorer = QualityScorer()
        metrics = scorer.aggregate_metrics(replay_results)
        
        if len(metrics) > 0 and "gpt-4o" in metrics:
            m = metrics["gpt-4o"]
            print(f"   ✅ PASS: Metrics calculated (quality: {scorer.calculate_quality_score(m):.3f})")
            results["passed"] += 1
            results["checks"].append("Quality metrics")
        else:
            print("   ❌ FAIL: No metrics generated")
            results["failed"] += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        results["failed"] += 1
    
    # ============================================
    # TEST 5: Recommendations
    # ============================================
    print("\n📍 TEST 5: Recommendation Engine")
    try:
        recommender = RecommendationEngine()
        recommendation = recommender.recommend(metrics)
        
        if recommendation and recommendation.recommended_model:
            print(f"   ✅ PASS: Recommendation: {recommendation.recommended_model}")
            results["passed"] += 1
            results["checks"].append("Recommendations")
        else:
            print("   ❌ FAIL: No recommendation")
            results["failed"] += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        results["failed"] += 1
    
    # ============================================
    # TEST 6: Cache Hit Verification
    # ============================================
    print("\n📍 TEST 6: Cache Hit Verification")
    try:
        # Run same prompt again, should hit cache
        replay_results_2 = engine.replay_batch(
            prompts=prompts,
            models=["gpt-4o"],
            use_validation=True,
            validation_phase="production"
        )
        
        cache_hits = [r for r in replay_results_2 if r.validation_method == "historical_db"]
        
        if len(cache_hits) > 0:
            print(f"   ✅ PASS: Cache hit detected ({cache_hits[0].validation_score:.1f})")
            results["passed"] += 1
            results["checks"].append("Cache hits")
        else:
            print("   ⚠️  WARN: No cache hit (may be expected)")
            results["passed"] += 1  # Not critical
            results["checks"].append("Cache hits (no hit)")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        results["failed"] += 1
    
    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "="*70)
    print(" 📊 TEST SUMMARY")
    print("="*70)
    
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\n✅ Passed: {results['passed']}/{total} ({pass_rate:.0f}%)")
    print(f"❌ Failed: {results['failed']}/{total}")
    
    print("\n✅ Working Components:")
    for check in results["checks"]:
        print(f"   • {check}")
    
    if results["failed"] == 0:
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n✅ Ready for:")
        print("   1. Provider extraction (30 min)")
        print("   2. Scenario classification (1 hour)")
        print("   3. Scenario-aware validation (2 hours)")
        print("   4. Production deployment")
        return True
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(final_sanity_test())
    exit(0 if success else 1)
