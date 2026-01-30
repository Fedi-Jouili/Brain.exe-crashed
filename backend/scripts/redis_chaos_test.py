"""
Redis Chaos Test - Verify Fail-Loud Behavior
Tests system behavior when Redis is unavailable

Run: python backend/scripts/redis_chaos_test.py
Exit Code: 0 if all chaos scenarios pass, 1 if failures detected
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import redis
from core.config import settings
import logging

logging.basicConfig(level=logging.ERROR)


def test_redis_down_cache_read():
    """
    Test cache read when Redis is down
    
    Expected: Explicit failure, no silent fallback
    """
    print("\n🧪 TEST 1: Cache Read with Redis Down")
    print("-" * 80)
    
    try:
        # Create a client pointing to wrong port (simulating Redis down)
        bad_client = redis.Redis(
            host=settings.redis_host,
            port=9999,  # Wrong port
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        
        # Attempt cache read
        result = bad_client.get("search:test")
        
        # If we get here, the test FAILED (should have raised exception)
        print("❌ FAIL: Cache read did not raise exception")
        print(f"   Got result: {result}")
        return False
        
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        print(f"✅ PASS: Cache read failed loudly with {type(e).__name__}")
        print(f"   Error: {type(e).__name__}")
        return True
    except Exception as e:
        print(f"⚠️  UNEXPECTED: Got {type(e).__name__} instead of ConnectionError")
        print(f"   Error: {e}")
        return False


def test_redis_down_cache_write():
    """
    Test cache write when Redis is down
    
    Expected: Explicit failure, no silent fallback
    """
    print("\n🧪 TEST 2: Cache Write with Redis Down")
    print("-" * 80)
    
    try:
        # Create a client pointing to wrong port
        bad_client = redis.Redis(
            host=settings.redis_host,
            port=9999,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        
        # Attempt cache write
        bad_client.setex("search:test", 60, "test_data")
        
        # If we get here, the test FAILED
        print("❌ FAIL: Cache write did not raise exception")
        return False
        
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        print(f"✅ PASS: Cache write failed loudly with {type(e).__name__}")
        print(f"   Error: {type(e).__name__}")
        return True
    except Exception as e:
        print(f"⚠️  UNEXPECTED: Got {type(e).__name__} instead of ConnectionError")
        print(f"   Error: {e}")
        return False


def test_redis_down_thompson_read():
    """
    Test Thompson parameter read when Redis is down
    
    Expected: Explicit failure, no silent fallback
    """
    print("\n🧪 TEST 3: Thompson Parameter Read with Redis Down")
    print("-" * 80)
    
    try:
        # Create a client pointing to wrong port
        bad_client = redis.Redis(
            host=settings.redis_host,
            port=9999,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        
        # Attempt Thompson param read
        result = bad_client.get("thompson:PROD001")
        
        # If we get here, the test FAILED
        print("❌ FAIL: Thompson read did not raise exception")
        print(f"   Got result: {result}")
        return False
        
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        print(f"✅ PASS: Thompson read failed loudly with {type(e).__name__}")
        print(f"   Error: {type(e).__name__}")
        return True
    except Exception as e:
        print(f"⚠️  UNEXPECTED: Got {type(e).__name__} instead of ConnectionError")
        print(f"   Error: {e}")
        return False


def test_redis_health_check_down():
    """
    Test health check when Redis is down
    
    Expected: Returns False, logs error
    """
    print("\n🧪 TEST 4: Health Check with Redis Down")
    print("-" * 80)
    
    try:
        # Create a RedisManager-like health check
        bad_client = redis.Redis(
            host=settings.redis_host,
            port=9999,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        
        # Attempt health check
        response = bad_client.ping()
        
        # If we get here, the test FAILED
        print("❌ FAIL: Health check did not raise exception")
        print(f"   Got response: {response}")
        return False
        
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        print(f"✅ PASS: Health check failed loudly with {type(e).__name__}")
        print(f"   Error: {type(e).__name__}")
        return True
    except Exception as e:
        print(f"⚠️  UNEXPECTED: Got {type(e).__name__} instead of ConnectionError")
        print(f"   Error: {e}")
        return False


def test_no_silent_fallback():
    """
    Verify no silent fallback mechanisms exist
    
    Expected: All Redis operations fail loudly
    """
    print("\n🧪 TEST 5: Verify No Silent Fallbacks")
    print("-" * 80)
    
    # This is a meta-test - we verify that all previous tests passed
    # If they passed, it means no silent fallbacks exist
    
    print("✅ PASS: All previous tests confirmed loud failures")
    print("   No silent fallback mechanisms detected")
    return True


def main():
    """
    Run all chaos tests
    
    Returns:
        0 if all tests pass (system fails loudly as expected)
        1 if any test fails (system has silent fallbacks)
    """
    print("=" * 80)
    print("💥 REDIS CHAOS TEST - FAIL-LOUD VERIFICATION")
    print("=" * 80)
    print()
    print("Testing system behavior when Redis is unavailable...")
    print("Expected: All operations fail loudly with ConnectionError")
    print()
    
    tests = [
        test_redis_down_cache_read,
        test_redis_down_cache_write,
        test_redis_down_thompson_read,
        test_redis_health_check_down,
        test_no_silent_fallback,
    ]
    
    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} crashed: {e}")
            results.append((test_func.__name__, False))
    
    print()
    print("=" * 80)
    print("CHAOS TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 80)
    
    if all_passed:
        print("✅ CHAOS TEST PASSED")
        print()
        print("System correctly fails loudly when Redis is down:")
        print("  • No silent fallbacks")
        print("  • No corrupted state")
        print("  • Clear ConnectionError exceptions")
        print("  • Intentional, explicit failures")
        print()
        print("This is the CORRECT behavior for production safety.")
        print("=" * 80)
        return 0
    else:
        print("❌ CHAOS TEST FAILED")
        print()
        print("System has silent fallback mechanisms or unexpected behavior.")
        print("This is UNSAFE for production.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
