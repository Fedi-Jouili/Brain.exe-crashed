"""
Test script to verify all components are working
Run this after setup to ensure everything is operational
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_imports() -> Tuple[bool, List[str]]:
    """Test that all modules can be imported"""
    logger.info("🧪 Testing imports...")

    errors = []

    try:
        from core.config import settings
        logger.info("   ✅ core.config")
    except Exception as e:
        errors.append(f"core.config: {e}")

    try:
        from core.embeddings import MultimodalEmbedder
        logger.info("   ✅ core.embeddings (CLIP)")
    except Exception as e:
        errors.append(f"core.embeddings: {e}")

    try:
        from core.qdrant_client import qdrant_manager
        logger.info("   ✅ core.qdrant_client")
    except Exception as e:
        errors.append(f"core.qdrant_client: {e}")

    try:
        from core.redis_client import redis_manager
        logger.info("   ✅ core.redis_client")
    except Exception as e:
        errors.append(f"core.redis_client: {e}")

    try:
        from models.schemas import UserProfile, Product
        logger.info("   ✅ models.schemas")
    except Exception as e:
        errors.append(f"models.schemas: {e}")

    try:
        from utils.financial import FinancialCalculator
        logger.info("   ✅ utils.financial")
    except Exception as e:
        errors.append(f"utils.financial: {e}")

    try:
        from agents.agent1_discovery import product_discovery_agent
        logger.info("   ✅ agents.agent1_discovery")
    except Exception as e:
        errors.append(f"agents.agent1_discovery: {e}")

    return len(errors) == 0, errors


def test_databases() -> Tuple[bool, List[str]]:
    """Test database connections"""
    logger.info("\n🧪 Testing database connections...")

    errors = []

    try:
        from core.qdrant_client import qdrant_manager
        if qdrant_manager.health_check():
            logger.info("   ✅ Qdrant connection")
        else:
            errors.append("Qdrant health check failed")
    except Exception as e:
        errors.append(f"Qdrant error: {e}")

    try:
        from core.redis_client import redis_manager
        if redis_manager.health_check():
            logger.info("   ✅ Redis connection")
        else:
            errors.append("Redis health check failed")
    except Exception as e:
        errors.append(f"Redis error: {e}")

    return len(errors) == 0, errors


def test_collections() -> Tuple[bool, List[str]]:
    """Test Qdrant collections"""
    logger.info("\n🧪 Testing Qdrant collections...")

    errors = []

    try:
        from core.qdrant_client import qdrant_manager
        from core.config import settings

        collections = [
            settings.qdrant_collection_products,
            settings.qdrant_collection_users,
            settings.qdrant_collection_financial_kb,
            settings.qdrant_collection_transactions,
        ]

        for collection_name in collections:
            try:
                count = qdrant_manager.count_points(collection_name)
                logger.info(f"   ✅ {collection_name}: {count} points")
            except Exception as e:
                errors.append(f"{collection_name}: {e}")

    except Exception as e:
        errors.append(f"Collection error: {e}")

    return len(errors) == 0, errors


def test_clip_embeddings() -> Tuple[bool, List[str]]:
    """Test CLIP embeddings"""
    logger.info("\n🧪 Testing CLIP embeddings...")

    errors = []

    try:
        from core.embeddings import MultimodalEmbedder

        embedder = MultimodalEmbedder()

        # Test text embedding
        embedding = embedder.embed_text("gaming laptop under $1000")
        if len(embedding) == 512:
            logger.info(f"   ✅ Text embedding: 512 dimensions")
        else:
            errors.append(f"Unexpected embedding dimension: {len(embedding)}")

        # Test batch encoding
        texts = ["laptop", "tablet", "phone"]
        embeddings = embedder.embed_batch_text(texts)
        if embeddings.shape == (3, 512):
            logger.info(f"   ✅ Batch encoding: {embeddings.shape}")
        else:
            errors.append(f"Unexpected batch shape: {embeddings.shape}")

    except Exception as e:
        errors.append(f"CLIP error: {e}")

    return len(errors) == 0, errors


def test_financial_calculator() -> Tuple[bool, List[str]]:
    """Test financial calculations"""
    logger.info("\n🧪 Testing financial calculator...")

    errors = []

    try:
        from models.schemas import UserProfile
        from utils.financial import FinancialCalculator

        # Create test profile
        profile = UserProfile(
            user_id="TEST001",
            monthly_income=5000,
            monthly_expenses=3500,
            savings=15000,
            current_debt=5000,
            credit_score=720
        )

        # Test calculations
        disposable = FinancialCalculator.calculate_disposable_income(profile)
        if disposable == 1500:
            logger.info(f"   ✅ Disposable income: ${disposable:.2f}")
        else:
            errors.append(f"Disposable income wrong: expected 1500, got {disposable}")

        safe_limit = FinancialCalculator.calculate_safe_cash_limit(profile)
        if safe_limit == 450:
            logger.info(f"   ✅ Safe cash limit: ${safe_limit:.2f}")
        else:
            errors.append(f"Safe limit wrong: expected 450, got {safe_limit}")

        dti = FinancialCalculator.calculate_dti_ratio(profile)
        if 0 <= dti <= 1:
            logger.info(f"   ✅ DTI ratio: {dti*100:.1f}%")
        else:
            errors.append(f"DTI ratio invalid: {dti}")

        can_afford, metrics = FinancialCalculator.check_cash_affordability(profile, 899.99)
        logger.info(f"   ✅ Affordability check: {'Yes' if can_afford else 'No'}")

    except Exception as e:
        errors.append(f"Financial calculator error: {e}")

    return len(errors) == 0, errors


def test_product_search() -> Tuple[bool, List[str]]:
    """Test product search"""
    logger.info("\n🧪 Testing product search...")

    errors = []

    try:
        from core.qdrant_client import qdrant_manager
        from core.embeddings import MultimodalEmbedder

        embedder = MultimodalEmbedder()

        # Search for laptops
        query_embedding = embedder.embed_text("laptop for programming")
        results = qdrant_manager.search_products(query_embedding.tolist(), top_k=5)

        if len(results) > 0:
            logger.info(f"   ✅ Found {len(results)} products")
            for i, result in enumerate(results[:3], 1):
                logger.info(f"      {i}. {result.payload['name']} (${result.payload['price']}) - Score: {result.score:.3f}")
        else:
            errors.append("No products found (did you run seed_data.py?)")

    except Exception as e:
        errors.append(f"Search error: {e}")

    return len(errors) == 0, errors


def test_redis_cache() -> Tuple[bool, List[str]]:
    """Test Redis caching"""
    logger.info("\n🧪 Testing Redis cache...")

    errors = []

    try:
        from core.redis_client import redis_manager

        # Test cache set/get
        test_data = {"test": "data", "timestamp": "2025-01-24"}
        redis_manager.cache_search_results("test_query", "TEST_USER", test_data)

        cached = redis_manager.get_cached_search("test_query", "TEST_USER")
        if cached and cached.get("test") == "data":
            logger.info("   ✅ Cache set/get working")
        else:
            errors.append("Cache retrieval failed")

        # Test Thompson parameters
        params = redis_manager.get_thompson_params("PROD0042")
        if 'alpha' in params and 'beta' in params:
            logger.info(f"   ✅ Thompson params: α={params['alpha']}, β={params['beta']}")
        else:
            errors.append("Thompson params retrieval failed")

    except Exception as e:
        errors.append(f"Redis cache error: {e}")

    return len(errors) == 0, errors


def test_agent1() -> Tuple[bool, List[str]]:
    """Test Agent 1 (Product Discovery)"""
    logger.info("\n🧪 Testing Agent 1 (Product Discovery)...")

    errors = []

    try:
        from agents.agent1_discovery import product_discovery_agent
        from models.schemas import UserProfile

        # Create test state
        state = {
            'query': 'laptop under $1000 with financing',
            'user_profile': UserProfile(
                user_id="TEST001",
                monthly_income=5000,
                monthly_expenses=3500,
                savings=15000,
                current_debt=5000,
                credit_score=720
            ),
            'image_embedding': None,
            'filters': {},
            'errors': [],
            'warnings': []
        }

        # Run agent
        result = product_discovery_agent.execute(state)

        if 'candidate_products' in result:
            num_products = len(result['candidate_products'])
            exec_time = result.get('search_time_ms', 0)
            logger.info(f"   ✅ Found {num_products} products in {exec_time}ms")

            if num_products > 0:
                for i, product in enumerate(result['candidate_products'][:3], 1):
                    logger.info(f"      {i}. {product.name} (${product.price})")
        else:
            errors.append("No candidate_products in result")

    except Exception as e:
        errors.append(f"Agent 1 error: {e}")

    return len(errors) == 0, errors


def main():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("🚀 PRICESENSE - COMPONENT TESTS")
    logger.info("=" * 70)
    logger.info("")

    all_tests = [
        ("Imports", test_imports),
        ("Database Connections", test_databases),
        ("Qdrant Collections", test_collections),
        ("CLIP Embeddings", test_clip_embeddings),
        ("Financial Calculator", test_financial_calculator),
        ("Product Search", test_product_search),
        ("Redis Cache", test_redis_cache),
        ("Agent 1", test_agent1),
    ]

    results = {}
    total_errors = []

    for test_name, test_func in all_tests:
        success, errors = test_func()
        results[test_name] = success
        if errors:
            total_errors.extend([f"{test_name}: {err}" for err in errors])

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}  {test_name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")

    if total_errors:
        logger.info("")
        logger.info("❌ ERRORS:")
        for error in total_errors:
            logger.info(f"   - {error}")
    else:
        logger.info("")
        logger.info("🎉 All tests passed! System is ready.")

    logger.info("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
