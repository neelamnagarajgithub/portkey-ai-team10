"""
Debug script to test database storage
Run this to see exactly what's happening with storage
"""

import logging
import sys
import os

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.historical_db import SupabaseDB, historical_db
from schemas import HistoricalPrompt
from backend.validator.hybrid_validator import hybrid_validator

def test_direct_storage():
    """Test direct database storage"""
    print("\n" + "="*70)
    print(" TEST 1: Direct Database Storage")
    print("="*70)
    
    db = SupabaseDB()
    
    test_data = {
        "prompt_text": "Test direct storage: What is 2+2?",
        "model": "gpt-4o",
        "provider": "openai",
        "scenario": "math_qa",
        "output": "2+2 equals 4.",
        "score": 95.0,
        "method": "direct_test",
        "confidence": "HIGH"
    }
    
    print(f"\nAttempting to store: {test_data}")
    result = db.store_validation(**test_data)
    
    if result:
        print("✅ Direct storage SUCCESS")
    else:
        print("❌ Direct storage FAILED - check logs above")
    
    return result

def test_validator_storage():
    """Test storage through validator"""
    print("\n" + "="*70)
    print(" TEST 2: Storage Through Validator")
    print("="*70)
    
    prompt = HistoricalPrompt(
        messages=[
            {"role": "user", "content": "What is machine learning?"}
        ]
    )
    
    output = "Machine learning is a subset of artificial intelligence."
    
    print(f"\nValidating prompt: {prompt.messages[0]['content']}")
    print(f"Output: {output}")
    
    try:
        validation = hybrid_validator.validate(
            prompt=prompt,
            output=output,
            model="gpt-4o",
            phase="discovery"
        )
        
        print(f"\n✅ Validation complete:")
        print(f"   Score: {validation.score:.1f}/100")
        print(f"   Method: {validation.method}")
        print(f"   Confidence: {validation.confidence}")
        print(f"\n💾 Check logs above to see if storage was attempted")
        
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_db_connection():
    """Test database connection"""
    print("\n" + "="*70)
    print(" TEST 3: Database Connection")
    print("="*70)
    
    db = SupabaseDB()
    
    # Try to get stats
    print("\nAttempting to get database stats...")
    stats = db.get_stats()
    
    if stats:
        print(f"✅ Connection successful!")
        print(f"   Total validations: {stats.get('total_validations', 0)}")
        print(f"   Unique models: {stats.get('unique_models', 0)}")
        print(f"   Unique scenarios: {stats.get('unique_scenarios', 0)}")
        return True
    else:
        print("❌ Failed to get stats - connection may be failing")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" 🔍 DATABASE STORAGE DEBUG SCRIPT")
    print("="*70)
    
    # Test 1: Direct storage
    test1 = test_direct_storage()
    
    # Test 2: Validator storage
    test2 = test_validator_storage()
    
    # Test 3: Connection
    test3 = test_db_connection()
    
    # Summary
    print("\n" + "="*70)
    print(" 📊 SUMMARY")
    print("="*70)
    print(f"Direct Storage: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Validator Storage: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"DB Connection: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if not (test1 and test2 and test3):
        print("\n⚠️ Some tests failed. Check the logs above for details.")
        print("Common issues:")
        print("  1. Supabase credentials not set (SUPABASE_URL, SUPABASE_KEY)")
        print("  2. Network connectivity issues")
        print("  3. Table doesn't exist in Supabase")
        print("  4. Row Level Security (RLS) policies blocking inserts")
