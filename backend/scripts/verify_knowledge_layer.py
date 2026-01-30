"""
Comprehensive Knowledge & Memory Layer Verification
Tests both Qdrant and Redis together

Run: python backend/scripts/verify_knowledge_layer.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Force UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from core.qdrant_client import qdrant_manager
from core.redis_client import redis_manager
from core.embeddings import clip_embedder
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def verify_infrastructure():
    """Verify Qdrant and Redis are healthy"""
    print("\n" + "=" * 80)
    print("INFRASTRUCTURE HEALTH")
    print("=" * 80)
    
    qdrant_ok = qdrant_manager.health_check()
    redis_ok = redis_manager.health_check()
    
    print(f"{'✅' if qdrant_ok else '❌'} Qdrant: {'HEALTHY' if qdrant_ok else 'UNHEALTHY'}")
    print(f"{'✅' if redis_ok else '❌'} Redis: {'HEALTHY' if redis_ok else 'UNHEALTHY'}")
    
    return qdrant_ok and redis_ok


def verify_data_population():
    """Verify data is populated in both systems"""
    print("\n" + "=" * 80)
    print("DATA POPULATION")
    print("=" * 80)
    
    try:
        # Qdrant
        products_info = qdrant_manager.get_collection_info(settings.qdrant_collection_products)
        financial_info = qdrant_manager.get_collection_info(settings.qdrant_collection_financial_kb)
        
        print(f"Qdrant Products: {products_info.points_count}")
        print(f"Qdrant Financial Rules: {financial_info.points_count}")
        
        # Redis
        thompson_stats = redis_manager.get_thompson_stats()
        cache_stats = redis_manager.get_cache_stats()
        
        print(f"Redis Thompson Params: {thompson_stats.get('products_tracked', 0)}")
        print(f"Redis Cache Entries: {cache_stats.get('total_keys', 0)}")
        
        return (
            products_info.points_count > 0 and
            financial_info.points_count > 0 and
            thompson_stats.get('products_tracked', 0) > 0
        )
    except Exception as e:
        print(f"❌ Error checking data population: {e}")
        return False


def verify_integration():
    """Test Qdrant + Redis integration"""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST")
    print("=" * 80)
    
    try:
        # Search product in Qdrant
        query = "gaming laptop"
        print(f"Searching Qdrant for '{query}'...")
        
        embedding = clip_embedder.embed_text(query)
        results = qdrant_manager.search_products(embedding, top_k=5, score_threshold=0.0)
        
        if not results:
            print("❌ No search results")
            return False
        
        print(f"✅ Found {len(results)} products")
        
        # Get Thompson params from Redis
        first_product = results[0]
        product_id = first_product['product_id']
        
        print(f"\nChecking Thompson params for {product_id}...")
        thompson_params = redis_manager.get_thompson_params(product_id)
        
        if thompson_params:
            print(f"✅ Thompson params: α={thompson_params['alpha']}, β={thompson_params['beta']}")
        else:
            print(f"⚠️ No Thompson params found for {product_id}, initializing now...")
            redis_manager.initialize_thompson_params(product_id)
            thompson_params = redis_manager.get_thompson_params(product_id)
            if thompson_params:
                print(f"✅ Initialized and retrieved params: α={thompson_params['alpha']}")
            else:
                 print(f"❌ Failed to initialize/retrieve params")
                 return False
        
        # Cache product in Redis
        print(f"\nCaching product in Redis...")
        redis_manager.cache_product(product_id, first_product, ttl_seconds=60)
        
        # Retrieve from cache
        cached_product = redis_manager.get_cached_product(product_id)
        
        if cached_product:
            print(f"✅ Product cached and retrieved: {cached_product['name']}")
        else:
            print("❌ Failed to cache/retrieve product")
            return False
        
        # Cache search results
        print(f"\nCaching search results...")
        redis_manager.cache_search_results(query, results=results, ttl=60)
        
        # Retrieve cached search
        cached_search = redis_manager.get_cached_search_results(query)
        
        if cached_search:
            print(f"✅ Search results cached and retrieved: {len(cached_search)} results")
        else:
            print("❌ Failed to cache/retrieve search results")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_thompson_sampling():
    """Verify Thompson Sampling functionality"""
    print("\n" + "=" * 80)
    print("THOMPSON SAMPLING VERIFICATION")
    print("=" * 80)
    
    try:
        # Get Thompson stats
        stats = redis_manager.get_thompson_stats()
        
        print(f"Products tracked: {stats.get('products_tracked', 0)}")
        print(f"Average α: {stats.get('avg_alpha', 0):.2f}")
        print(f"Average β: {stats.get('avg_beta', 0):.2f}")
        print(f"Average conversion rate: {stats.get('avg_conversion_rate', 0):.3f}")
        
        if stats.get('products_tracked', 0) > 0:
            print("✅ Thompson Sampling is operational")
            return True
        else:
            print("❌ No Thompson parameters found")
            print("   Run: python backend/scripts/initialize_thompson_redis.py")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Thompson Sampling: {e}")
        return False


def verify_cache_performance():
    """Verify cache performance"""
    print("\n" + "=" * 80)
    print("CACHE PERFORMANCE")
    print("=" * 80)
    
    try:
        stats = redis_manager.get_cache_stats()
        
        print(f"Total keys: {stats.get('total_keys', 0)}")
        print(f"Search cache entries: {stats.get('search_cache_entries', 0)}")
        print(f"Product cache entries: {stats.get('product_cache_entries', 0)}")
        print(f"Thompson params: {stats.get('thompson_params_count', 0)}")
        print(f"Keyspace hits: {stats.get('keyspace_hits', 0)}")
        print(f"Keyspace misses: {stats.get('keyspace_misses', 0)}")
        print(f"Hit rate: {stats.get('hit_rate', 0):.2f}%")
        
        print("✅ Cache statistics retrieved")
        return True
        
    except Exception as e:
        print(f"❌ Error checking cache performance: {e}")
        return False


def verify_memory_usage():
    """Verify Redis memory usage"""
    print("\n" + "=" * 80)
    print("MEMORY USAGE")
    print("=" * 80)
    
    try:
        memory_info = redis_manager.get_memory_info()
        
        print(f"Used memory: {memory_info.get('used_memory_human', 'N/A')}")
        print(f"Peak memory: {memory_info.get('used_memory_peak_mb', 0):.2f} MB")
        print(f"Max memory: {memory_info.get('maxmemory_mb', 'unlimited')}")
        print(f"Fragmentation ratio: {memory_info.get('mem_fragmentation_ratio', 0):.2f}")
        
        print("✅ Memory info retrieved")
        return True
        
    except Exception as e:
        print(f"❌ Error checking memory usage: {e}")
        return False


def main():
    """Run verification"""
    print("\n" + "=" * 80)
    print("🔍 KNOWLEDGE & MEMORY LAYER VERIFICATION")
    print("=" * 80)
    
    tests = [
        ("Infrastructure Health", verify_infrastructure),
        ("Data Population", verify_data_population),
        ("Qdrant-Redis Integration", verify_integration),
        ("Thompson Sampling", verify_thompson_sampling),
        ("Cache Performance", verify_cache_performance),
        ("Memory Usage", verify_memory_usage),
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
        print("✅ KNOWLEDGE & MEMORY LAYER COMPLETE!")
        print("Both Qdrant and Redis are operational!")
        print("")
        print("🎯 Next Steps:")
        print("   1. Test agent integration with Thompson Sampling")
        print("   2. Monitor cache hit rates")
        print("   3. Track Thompson parameter evolution")
    else:
        print("❌ SOME CHECKS FAILED")
        print("")
        print("🔧 Troubleshooting:")
        print("   - Ensure Docker containers are running")
        print("   - Check if Qdrant is populated: python backend/scripts/populate_qdrant.py")
        print("   - Initialize Thompson params: python backend/scripts/initialize_thompson_redis.py")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
