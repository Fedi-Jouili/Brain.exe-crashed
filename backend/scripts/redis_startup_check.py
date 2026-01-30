"""
Redis Startup Health Check - Fail-Fast Guard
Ensures Redis is healthy before application starts

Run: python backend/scripts/redis_startup_check.py
Exit Code: 0 if healthy, 1 if unhealthy
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.redis_client import redis_manager
import logging

logging.basicConfig(level=logging.ERROR)


def main():
    """
    Fail-fast startup check for Redis health
    
    Returns:
        0 if Redis is healthy
        1 if Redis is unhealthy
    """
    print("=" * 80)
    print("🔍 REDIS STARTUP HEALTH CHECK")
    print("=" * 80)
    
    try:
        healthy = redis_manager.health_check()
        
        if healthy:
            print("✅ Redis is HEALTHY - Application can start")
            print("=" * 80)
            return 0
        else:
            print("❌ FATAL: Redis health check FAILED")
            print("=" * 80)
            print("\n🚨 APPLICATION CANNOT START")
            print("Redis is required for:")
            print("  - Thompson Sampling state")
            print("  - Search result caching")
            print("  - Session management")
            print("  - Metrics tracking")
            print("\nAction Required:")
            print("  1. Ensure Redis is running")
            print("  2. Check Redis connection settings")
            print("  3. Verify network connectivity")
            print("=" * 80)
            return 1
            
    except Exception as e:
        print(f"❌ FATAL: Redis connection error: {e}")
        print("=" * 80)
        print("\n🚨 APPLICATION CANNOT START")
        print("Redis is unreachable or misconfigured")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
