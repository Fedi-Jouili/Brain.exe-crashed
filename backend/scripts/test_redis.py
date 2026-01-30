"""
Test Redis Functionality
Tests caching, Thompson state, sessions, metrics

Run: python backend/scripts/test_redis.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.redis_client import redis_manager
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_health():
    """Test 1: Health check"""
    print("\n" + "=" * 80)
    print("TEST 1: HEALTH CHECK")
    print("=" * 80)
    
    healthy = redis_manager.health_check()
    
    if healthy:
        print("✅ Redis is healthy")
        return True
    else:
        print("❌ Redis health check failed")
        return False


def test_cache():
    """Test 2: Caching"""
    print("\n" + "=" * 80)
    print("TEST 2: CACHING")
    print("=" * 80)
    
    try:
        # Cache search results
        test_query = "test laptop"
        test_results = [
            {'product_id': 'PROD001', 'name': 'Test Laptop', 'price': 999.99}
        ]
        
        print(f"Caching search results for '{test_query}'...")
        redis_manager.cache_search_results(test_query, results=test_results, ttl=60)
        
        # Retrieve from cache
        print(f"Retrieving cached results...")
        cached = redis_manager.get_cached_search_results(test_query)
        
        if cached:
            print(f"✅ Cache HIT: {len(cached)} results")
        else:
            print("❌ Cache MISS (should have been a hit)")
            return False
        
        # Test cache miss
        print(f"Testing cache miss...")
        missed = redis_manager.get_cached_search_results("nonexistent query")
        
        if missed is None:
            print("✅ Cache MISS (as expected)")
        else:
            print("❌ Got results for nonexistent query")
            return False
        
        # Test product caching
        print("\nTesting product caching...")
        test_product = {'product_id': 'PROD001', 'name': 'Test Laptop', 'price': 999.99}
        redis_manager.cache_product('PROD001', test_product, ttl_seconds=60)
        
        cached_product = redis_manager.get_cached_product('PROD001')
        
        if cached_product:
            print(f"✅ Product cached and retrieved: {cached_product['name']}")
        else:
            print("❌ Failed to cache/retrieve product")
            return False
        
        # Test cache stats
        print("\nCache statistics:")
        stats = redis_manager.get_cache_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_thompson():
    """Test 3: Thompson parameters"""
    print("\n" + "=" * 80)
    print("TEST 3: THOMPSON PARAMETERS")
    print("=" * 80)
    
    try:
        test_product_id = "TEST_PRODUCT_001"
        
        # Initialize
        print(f"Initializing Thompson params for {test_product_id}...")
        redis_manager.initialize_thompson_params(test_product_id, alpha=1.0, beta=1.0)
        
        # Get params
        params = redis_manager.get_thompson_params(test_product_id)
        
        if params:
            print(f"✅ Got params: α={params['alpha']}, β={params['beta']}")
        else:
            print("❌ Failed to get params")
            return False
        
        # Update params (simulate purchase)
        print("Simulating purchase (α += 1.0)...")
        redis_manager.set_thompson_params(test_product_id, alpha=2.0, beta=1.0)
        
        # Verify update
        updated_params = redis_manager.get_thompson_params(test_product_id)
        
        if updated_params and updated_params['alpha'] == 2.0:
            print(f"✅ Params updated: α={updated_params['alpha']}, β={updated_params['beta']}")
        else:
            print("❌ Params not updated correctly")
            return False
        
        # Test update_thompson_params method
        print("Testing update_thompson_params (simulate click)...")
        redis_manager.update_thompson_params(test_product_id, signal_weight=0.5)
        
        updated_params2 = redis_manager.get_thompson_params(test_product_id)
        
        if updated_params2 and updated_params2['alpha'] == 2.5:
            print(f"✅ Update method works: α={updated_params2['alpha']}")
        else:
            print("❌ Update method failed")
            return False
        
        # Get stats
        print("\nThompson statistics:")
        stats = redis_manager.get_thompson_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sessions():
    """Test 4: Session management"""
    print("\n" + "=" * 80)
    print("TEST 4: SESSION MANAGEMENT")
    print("=" * 80)
    
    try:
        session_id = "test_session_123"
        session_data = {
            'user_id': 'user_test',
            'query': 'laptop',
            'timestamp': time.time()
        }
        
        # Create session
        print(f"Creating session {session_id}...")
        redis_manager.create_session(session_id, session_data, ttl_seconds=60)
        
        # Retrieve session
        retrieved = redis_manager.get_session(session_id)
        
        if retrieved:
            print(f"✅ Retrieved session: user_id={retrieved['user_id']}")
        else:
            print("❌ Failed to retrieve session")
            return False
        
        # Update session
        session_data['updated'] = True
        print("Updating session...")
        redis_manager.update_session(session_id, session_data)
        
        # Verify update
        updated = redis_manager.get_session(session_id)
        
        if updated and updated.get('updated'):
            print("✅ Session updated successfully")
        else:
            print("❌ Session not updated")
            return False
        
        # Delete session
        print("Deleting session...")
        redis_manager.delete_session(session_id)
        
        # Verify deletion
        deleted_check = redis_manager.get_session(session_id)
        
        if deleted_check is None:
            print("✅ Session deleted successfully")
        else:
            print("❌ Session still exists")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics():
    """Test 5: Metrics and counters"""
    print("\n" + "=" * 80)
    print("TEST 5: METRICS & COUNTERS")
    print("=" * 80)
    
    try:
        counter_name = "test:counter"
        
        # Reset counter
        print(f"Resetting counter '{counter_name}'...")
        redis_manager.reset_counter(counter_name)
        
        # Increment counter
        print("Incrementing counter 5 times...")
        for i in range(5):
            redis_manager.increment_counter(counter_name)
        
        # Get counter value
        value = redis_manager.get_counter(counter_name)
        
        if value == 5:
            print(f"✅ Counter value: {value}")
        else:
            print(f"❌ Expected 5, got {value}")
            return False
        
        # Record timing
        print("\nRecording operation timings...")
        for duration in [100, 150, 200, 120, 180]:
            redis_manager.record_timing("test_operation", duration)
        
        # Get timing stats
        timing_stats = redis_manager.get_timing_stats("test_operation")
        
        if timing_stats:
            print("✅ Timing statistics:")
            for key, value in timing_stats.items():
                print(f"  {key}: {value:.2f}ms" if isinstance(value, float) else f"  {key}: {value}")
        else:
            print("❌ No timing stats")
            return False
        
        # Get all metrics
        print("\nAll metrics:")
        all_metrics = redis_manager.get_all_metrics()
        for key, value in all_metrics.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory():
    """Test 6: Memory info"""
    print("\n" + "=" * 80)
    print("TEST 6: MEMORY INFO")
    print("=" * 80)
    
    try:
        memory_info = redis_manager.get_memory_info()
        
        if memory_info:
            print("✅ Memory information:")
            for key, value in memory_info.items():
                print(f"  {key}: {value}")
            return True
        else:
            print("❌ Failed to get memory info")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🔍 REDIS FUNCTIONALITY TESTS")
    print("=" * 80)
    
    tests = [
        ("Health Check", test_health),
        ("Caching", test_cache),
        ("Thompson Parameters", test_thompson),
        ("Session Management", test_sessions),
        ("Metrics & Counters", test_metrics),
        ("Memory Info", test_memory),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(p for _, p in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Redis is fully operational!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check logs above for details")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
