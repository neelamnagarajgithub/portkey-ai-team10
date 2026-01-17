"""
Test Supabase PostgreSQL Connection
"""

from db.historical_db import SupabaseDB

def test_supabase_connection():
    """Test basic Supabase operations"""
    
    print("\n" + "="*70)
    print(" TESTING SUPABASE CONNECTION")
    print("="*70)
    
    try:
        # Initialize database
        print("\n1. Connecting to Supabase...")
        db = SupabaseDB()
        print("   ✅ Connected successfully!")
        
        # Store a test validation
        print("\n2. Storing test validation...")
        db.store_validation(
            prompt_text="What is machine learning?",
            model="gpt-4o",
            provider="openai",
            scenario="factual_qa",
            output="Machine learning is a subset of AI...",
            score=92.5,
            method="llm_judge",
            confidence="HIGH",
            procedure="test_validation"
        )
        print("   ✅ Stored validation successfully!")
        
        # Retrieve similar prompts
        print("\n3. Finding similar prompts...")
        result = db.find_similar(
            prompt_text="What is machine learning?",
            model="gpt-4o",
            scenario="factual_qa"
        )
        
        if result:
            print(f"   ✅ Found similar prompts!")
            print(f"      Average Score: {result.avg_score:.1f}/100")
            print(f"      Confidence: {result.confidence}")
            print(f"      Count: {result.similar_count}")
        else:
            print("   ⚠️  No similar prompts found")
        
        # Get stats
        print("\n4. Getting database stats...")
        stats = db.get_stats()
        print(f"   Total Validations: {stats.get('total_validations', 0)}")
        print(f"   Unique Models: {stats.get('unique_models', 0)}")
        print(f"   Unique Scenarios: {stats.get('unique_scenarios', 0)}")
        print(f"   Average Score: {stats.get('avg_score', 0):.1f}/100")
        
        print("\n" + "="*70)
        print(" ✅ ALL TESTS PASSED")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_supabase_connection()
    exit(0 if success else 1)
