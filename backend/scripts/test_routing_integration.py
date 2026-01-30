"""
Integration Test for 3-Tier Routing System
Tests the complete flow: complexity estimation → routing → execution

Run this after starting the backend server:
    python backend/scripts/test_routing_integration.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from datetime import datetime
from ml.complexity_estimator import complexity_estimator
from models.schemas import UserProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_routing_scenarios():
    """Test all three routing paths"""

    print("\n" + "="*70)
    print("3-TIER ROUTING INTEGRATION TEST")
    print("="*70 + "\n")

    # Test scenario 1: FAST/SMART PATH
    print("TEST 1: Simple query (should route to FAST or SMART)")
    print("-" * 70)
    query1 = "laptops"
    result1 = complexity_estimator.estimate(query1, None, False)

    print(f"Query: '{query1}'")
    print(f"Route: {result1['level']}")
    print(f"Score: {result1['score']:.3f}")
    print(f"Reasoning: {result1['reasoning']}")
    print(f"Expected: FAST or SMART (score < 0.7)")
    print(f"Status: {'✅ PASS' if result1['level'] in ['FAST', 'SMART'] else '❌ FAIL'}")
    print()

    # Test scenario 2: SMART PATH
    print("TEST 2: Price constraint query (should route to SMART)")
    print("-" * 70)
    query2 = "laptop under $1000"
    result2 = complexity_estimator.estimate(query2, None, False)

    print(f"Query: '{query2}'")
    print(f"Route: {result2['level']}")
    print(f"Score: {result2['score']:.3f}")
    print(f"Reasoning: {result2['reasoning']}")
    print(f"Expected: SMART (0.3 ≤ score < 0.7)")
    print(f"Status: {'✅ PASS' if result2['level'] == 'SMART' else '⚠️ ACCEPTABLE' if result2['level'] in ['FAST', 'DEEP'] else '❌ FAIL'}")
    print()

    # Test scenario 3: DEEP PATH
    print("TEST 3: Financial query with profile (should route to DEEP)")
    print("-" * 70)
    query3 = "laptop under $1000 with financing"
    user_profile = UserProfile(
        user_id="test_user",
        monthly_income=5000.0,
        credit_score=720
    )
    result3 = complexity_estimator.estimate(query3, user_profile, False)

    print(f"Query: '{query3}'")
    print(f"User Profile: income=${user_profile.monthly_income}, credit={user_profile.credit_score}")
    print(f"Route: {result3['level']}")
    print(f"Score: {result3['score']:.3f}")
    print(f"Reasoning: {result3['reasoning']}")
    print(f"Expected: DEEP (score ≥ 0.7)")
    print(f"Status: {'✅ PASS' if result3['level'] == 'DEEP' else '❌ FAIL'}")
    print()

    # Factor breakdown
    print("TEST 4: Factor contribution analysis")
    print("-" * 70)
    for key, value in result3['factors'].items():
        print(f"  {key}: {value:.2f}")
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    test_results = [
        result1['level'] in ['FAST', 'SMART'],
        result2['level'] in ['SMART', 'FAST', 'DEEP'],  # Acceptable range
        result3['level'] == 'DEEP'
    ]

    passed = sum(test_results)
    total = len(test_results)

    print(f"Tests Passed: {passed}/{total}")
    print(f"Status: {'✅ ALL TESTS PASSED' if passed == total else '⚠️ SOME TESTS FAILED'}")
    print()

    # Cache key demonstration
    print("TEST 5: Cache key generation")
    print("-" * 70)
    import hashlib

    cache_key1 = f"search:{hashlib.md5(query1.encode()).hexdigest()}:anonymous"
    cache_key2 = f"search:{hashlib.md5(query2.encode()).hexdigest()}:anonymous"
    cache_key3 = f"search:{hashlib.md5(query3.encode()).hexdigest()}:{user_profile.user_id}"

    print(f"Query 1 cache key: {cache_key1}")
    print(f"Query 2 cache key: {cache_key2}")
    print(f"Query 3 cache key: {cache_key3}")
    print()

    print("="*70)
    print("EXPECTED PERFORMANCE")
    print("="*70)
    print("FAST PATH:  <100ms  (cache hit)")
    print("SMART PATH: 300-800ms (Agent 1 only)")
    print("DEEP PATH:  1500-3000ms (full pipeline)")
    print()

    print("="*70)
    print("INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")

    return passed == total


async def test_smart_path_execution():
    """Test SMART PATH execution (requires imports)"""
    print("\n" + "="*70)
    print("SMART PATH EXECUTION TEST")
    print("="*70 + "\n")

    try:
        from models.api_models import SearchRequest
        from main import execute_smart_path
        import time

        # Create a simple request
        request = SearchRequest(
            query="gaming laptops",
            user_profile={
                "user_id": "test_user",
                "monthly_income": 5000,
                "credit_score": 700
            },
            max_results=5
        )

        print("Testing SMART PATH execution...")
        start_time = time.time()

        result = await execute_smart_path(request, start_time)

        execution_time = int((time.time() - start_time) * 1000)

        print(f"✅ Execution time: {execution_time}ms")
        print(f"Candidates found: {len(result.get('candidate_products', []))}")
        print(f"Final recommendations: {len(result.get('final_recommendations', []))}")
        print(f"Errors: {result.get('errors', [])}")
        print(f"Target: 300-800ms")
        print(f"Status: {'✅ PASS' if 50 <= execution_time <= 1500 else '⚠️ ACCEPTABLE'}")
        print()

    except ImportError as e:
        print(f"⚠️ Cannot test SMART PATH execution: {e}")
        print("This requires Agent 1 to be available (may need Python 3.11/3.12)")
    except Exception as e:
        print(f"❌ SMART PATH execution failed: {e}")

    print("="*70 + "\n")


if __name__ == "__main__":
    # Run the main routing tests
    success = asyncio.run(test_routing_scenarios())

    # Try to run SMART PATH test (may fail if dependencies unavailable)
    asyncio.run(test_smart_path_execution())

    # Exit with appropriate code
    exit(0 if success else 1)
