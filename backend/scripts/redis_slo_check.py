"""
Redis SLO (Service Level Objective) Enforcement
Validates Redis performance against production thresholds

Run: python backend/scripts/redis_slo_check.py
Exit Code: 0 if all SLOs met, 1 if violations detected
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.redis_client import redis_manager
import logging

logging.basicConfig(level=logging.WARNING)


# SLO THRESHOLDS (PRODUCTION)
SLO_THRESHOLDS = {
    'cache_hit_rate_min': 80.0,      # ≥ 80%
    'p95_latency_max_ms': 50.0,      # ≤ 50ms
    'mem_fragmentation_max': 10.0,   # ≤ 10
    'memory_usage_max_pct': 80.0,    # ≤ 80% of maxmemory
}


def check_cache_hit_rate() -> tuple[bool, str, float]:
    """
    Check cache hit rate SLO
    
    Returns:
        (passed, message, actual_value)
    """
    try:
        stats = redis_manager.get_cache_stats()
        hit_rate = stats.get('hit_rate', 0.0)
        
        threshold = SLO_THRESHOLDS['cache_hit_rate_min']
        passed = hit_rate >= threshold
        
        message = f"Cache Hit Rate: {hit_rate:.2f}% (threshold: ≥{threshold}%)"
        
        return passed, message, hit_rate
        
    except Exception as e:
        return False, f"Cache hit rate check failed: {e}", 0.0


def check_memory_fragmentation() -> tuple[bool, str, float]:
    """
    Check memory fragmentation SLO
    
    Returns:
        (passed, message, actual_value)
    """
    try:
        memory_info = redis_manager.get_memory_info()
        fragmentation = memory_info.get('mem_fragmentation_ratio', 0.0)
        
        threshold = SLO_THRESHOLDS['mem_fragmentation_max']
        passed = fragmentation <= threshold
        
        message = f"Memory Fragmentation: {fragmentation:.2f} (threshold: ≤{threshold})"
        
        return passed, message, fragmentation
        
    except Exception as e:
        return False, f"Memory fragmentation check failed: {e}", 0.0


def check_memory_usage() -> tuple[bool, str, float]:
    """
    Check memory usage SLO
    
    Returns:
        (passed, message, actual_value)
    """
    try:
        memory_info = redis_manager.get_memory_info()
        used_mb = memory_info.get('used_memory_mb', 0.0)
        max_mb = memory_info.get('maxmemory_mb', 0.0)
        
        if max_mb == 0:
            # No maxmemory set - cannot enforce SLO
            return True, "Memory Usage: No maxmemory limit set (SLO skipped)", 0.0
        
        usage_pct = (used_mb / max_mb) * 100
        threshold = SLO_THRESHOLDS['memory_usage_max_pct']
        passed = usage_pct <= threshold
        
        message = f"Memory Usage: {usage_pct:.2f}% ({used_mb:.2f}MB / {max_mb:.2f}MB) (threshold: ≤{threshold}%)"
        
        return passed, message, usage_pct
        
    except Exception as e:
        return False, f"Memory usage check failed: {e}", 0.0


def check_latency() -> tuple[bool, str, float]:
    """
    Check Redis latency SLO (p95)
    
    Note: This requires timing data to be recorded
    
    Returns:
        (passed, message, actual_value)
    """
    try:
        # Check if we have timing data for Redis operations
        timing_stats = redis_manager.get_timing_stats('redis_operation')
        
        if not timing_stats or timing_stats.get('count', 0) == 0:
            # No timing data - cannot enforce SLO
            return True, "Latency: No timing data available (SLO skipped)", 0.0
        
        p95 = timing_stats.get('p95', 0.0)
        threshold = SLO_THRESHOLDS['p95_latency_max_ms']
        passed = p95 <= threshold
        
        message = f"P95 Latency: {p95:.2f}ms (threshold: ≤{threshold}ms)"
        
        return passed, message, p95
        
    except Exception as e:
        return False, f"Latency check failed: {e}", 0.0


def main():
    """
    Run all SLO checks
    
    Returns:
        0 if all SLOs met
        1 if any SLO violated
    """
    print("=" * 80)
    print("📊 REDIS SLO ENFORCEMENT CHECK")
    print("=" * 80)
    print()
    
    # Run all checks
    checks = [
        ("Cache Hit Rate", check_cache_hit_rate),
        ("Memory Fragmentation", check_memory_fragmentation),
        ("Memory Usage", check_memory_usage),
        ("P95 Latency", check_latency),
    ]
    
    results = []
    violations = []
    
    for check_name, check_func in checks:
        passed, message, value = check_func()
        results.append((check_name, passed, message, value))
        
        if passed:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            violations.append((check_name, message, value))
    
    print()
    print("=" * 80)
    
    if violations:
        print("❌ SLO VIOLATIONS DETECTED")
        print("=" * 80)
        print()
        print("The following SLOs are violated:")
        for check_name, message, value in violations:
            print(f"  • {check_name}: {message}")
        print()
        print("🚨 ACTION REQUIRED:")
        print("  1. Investigate Redis performance degradation")
        print("  2. Check for memory leaks or excessive fragmentation")
        print("  3. Review cache invalidation strategy")
        print("  4. Consider scaling Redis resources")
        print("=" * 80)
        return 1
    else:
        print("✅ ALL SLOs MET")
        print("Redis is operating within acceptable performance thresholds")
        print("=" * 80)
        return 0


if __name__ == "__main__":
    sys.exit(main())
