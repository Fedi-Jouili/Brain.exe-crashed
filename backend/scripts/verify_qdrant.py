"""
Verify Qdrant Setup - Comprehensive Test Suite

Tests all Qdrant functionality required for PriceSense.
MUST pass all tests before production deployment.

Exit codes:
- 0: All tests passed
- 1: At least one test failed
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import List, Dict, Any

from core.qdrant_client import qdrant_manager
from core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestResult:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []

    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        logger.info(f"✅ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        logger.error(f"❌ FAIL: {test_name}")
        logger.error(f"   Error: {error}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {len(self.passed)} ✅")
        logger.info(f"Failed: {len(self.failed)} ❌")

        if self.failed:
            logger.info("\nFailed tests:")
            for test_name, error in self.failed:
                logger.info(f"  - {test_name}: {error}")

        logger.info("=" * 80)

        return len(self.failed) == 0


def test_qdrant_health(results: TestResult):
    """Test 1: Qdrant health check"""
    logger.info("\n[Test 1] Qdrant Health Check")
    logger.info("-" * 80)

    try:
        healthy = qdrant_manager.health_check()
        if healthy:
            results.add_pass("Qdrant health check")
        else:
            results.add_fail("Qdrant health check", "health_check() returned False")
    except Exception as e:
        results.add_fail("Qdrant health check", str(e))


def test_collections_exist(results: TestResult):
    """Test 2: All required collections exist"""
    logger.info("\n[Test 2] Collection Existence")
    logger.info("-" * 80)

    required_collections = [
        settings.qdrant_collection_products,
        settings.qdrant_collection_financial_kb,
        settings.qdrant_collection_users,
        settings.qdrant_collection_transactions
    ]

    try:
        existing = {col.name for col in qdrant_manager.client.get_collections().collections}

        for collection in required_collections:
            if collection in existing:
                results.add_pass(f"Collection exists: {collection}")
                logger.info(f"   Found: {collection}")
            else:
                results.add_fail(f"Collection exists: {collection}", "Collection not found")

    except Exception as e:
        results.add_fail("Collections check", str(e))


def test_products_collection(results: TestResult):
    """Test 3: Products collection has data and works correctly"""
    logger.info("\n[Test 3] Products Collection")
    logger.info("-" * 80)

    # Test 3.1: Count > 0
    try:
        count = qdrant_manager.count_points(settings.qdrant_collection_products)
        logger.info(f"   Products count: {count}")

        if count > 0:
            results.add_pass("Products collection has data")
        else:
            results.add_fail("Products collection has data", f"Count is {count}")
    except Exception as e:
        results.add_fail("Products collection count", str(e))
        return  # Can't continue if collection is empty

    # Test 3.2: Get product by ID
    try:
        # Scroll to get first product's ID
        scroll_result = qdrant_manager.client.scroll(
            collection_name=settings.qdrant_collection_products,
            limit=1,
            with_vectors=False
        )

        if scroll_result[0]:
            test_product_id = scroll_result[0][0].payload['product_id']
            logger.info(f"   Testing with product_id: {test_product_id}")

            product = qdrant_manager.get_product_by_id(test_product_id)

            if product:
                results.add_pass("get_product_by_id() works")
                logger.info(f"   Retrieved: {product['name']}")
                logger.info(f"   Price: ${product['price']:.2f}")
                logger.info(f"   Cluster ID: {product.get('cluster_id', 'N/A')}")

                # Verify no embedding in response
                if 'embedding' not in product:
                    results.add_pass("get_product_by_id() excludes embeddings")
                else:
                    results.add_fail("get_product_by_id() excludes embeddings", "Embedding found in response")
            else:
                results.add_fail("get_product_by_id() works", "Returned None for valid ID")
        else:
            results.add_fail("get_product_by_id() setup", "No products to test with")

    except Exception as e:
        results.add_fail("get_product_by_id()", str(e))

    # Test 3.3: Semantic search
    try:
        # Get a product's embedding for test query
        scroll_result = qdrant_manager.client.scroll(
            collection_name=settings.qdrant_collection_products,
            limit=1,
            with_vectors=True
        )

        if scroll_result[0]:
            test_vector = scroll_result[0][0].vector

            search_results = qdrant_manager.search_products(
                query_vector=test_vector,
                top_k=5,
                score_threshold=0.5
            )

            if search_results:
                results.add_pass("search_products() works")
                logger.info(f"   Found {len(search_results)} similar products")
                logger.info(f"   Top match: {search_results[0]['name']} (score: {search_results[0]['score']:.3f})")

                # Verify no embeddings in results
                if 'embedding' not in search_results[0]:
                    results.add_pass("search_products() excludes embeddings")
                else:
                    results.add_fail("search_products() excludes embeddings", "Embedding found in results")
            else:
                results.add_fail("search_products() works", "No results returned")
        else:
            results.add_fail("search_products() setup", "No products to test with")

    except Exception as e:
        results.add_fail("search_products()", str(e))

    # Test 3.4: Cluster-based retrieval (CRITICAL for Agent 2.5)
    try:
        # Get a product with cluster_id
        scroll_result = qdrant_manager.client.scroll(
            collection_name=settings.qdrant_collection_products,
            limit=10,
            with_vectors=False
        )

        test_cluster_id = None
        test_max_price = None

        for point in scroll_result[0]:
            if 'cluster_id' in point.payload:
                test_cluster_id = point.payload['cluster_id']
                test_max_price = point.payload['price'] * 1.5  # 50% higher than test product
                break

        if test_cluster_id is not None:
            logger.info(f"   Testing cluster retrieval with cluster_id={test_cluster_id}")

            cluster_products = qdrant_manager.get_products_by_cluster(
                cluster_id=test_cluster_id,
                max_price=test_max_price,
                limit=5
            )

            if cluster_products:
                results.add_pass("get_products_by_cluster() works")
                logger.info(f"   Found {len(cluster_products)} products in cluster {test_cluster_id}")

                # Verify all have same cluster_id
                all_same_cluster = all(p.get('cluster_id') == test_cluster_id for p in cluster_products)
                if all_same_cluster:
                    results.add_pass("get_products_by_cluster() filters by cluster_id")
                else:
                    results.add_fail("get_products_by_cluster() filters by cluster_id", "Mixed cluster IDs returned")

                # Verify sorted by price ascending
                prices = [p['price'] for p in cluster_products]
                if prices == sorted(prices):
                    results.add_pass("get_products_by_cluster() sorts by price ascending")
                    logger.info(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                else:
                    results.add_fail("get_products_by_cluster() sorts by price ascending", "Prices not sorted")

            else:
                results.add_fail("get_products_by_cluster() works", "No products returned")
        else:
            results.add_fail("get_products_by_cluster() setup", "No products with cluster_id found")

    except Exception as e:
        results.add_fail("get_products_by_cluster()", str(e))

    # Test 3.5: Search with filters
    try:
        search_results = qdrant_manager.search_products(
            query_vector=test_vector,
            top_k=10,
            filters={'in_stock': True, 'max_price': 1000.0},
            score_threshold=0.3
        )

        if search_results:
            results.add_pass("search_products() with filters works")

            # Verify all in stock
            all_in_stock = all(p.get('in_stock', False) for p in search_results)
            if all_in_stock:
                results.add_pass("search_products() in_stock filter works")
            else:
                results.add_fail("search_products() in_stock filter", "Out-of-stock products returned")

            # Verify all under max price
            all_under_price = all(p['price'] <= 1000.0 for p in search_results)
            if all_under_price:
                results.add_pass("search_products() max_price filter works")
            else:
                results.add_fail("search_products() max_price filter", "Products over max_price returned")
        else:
            logger.warning("   No products match filtered search (may be OK)")

    except Exception as e:
        results.add_fail("search_products() with filters", str(e))


def test_financial_kb_collection(results: TestResult):
    """Test 4: Financial KB collection has data and retrieval works"""
    logger.info("\n[Test 4] Financial Knowledge Base Collection")
    logger.info("-" * 80)

    # Test 4.1: Count > 0
    try:
        count = qdrant_manager.count_points(settings.qdrant_collection_financial_kb)
        logger.info(f"   Financial rules count: {count}")

        if count > 0:
            results.add_pass("Financial KB has data")
        else:
            results.add_fail("Financial KB has data", f"Count is {count}")
            return  # Can't continue
    except Exception as e:
        results.add_fail("Financial KB count", str(e))
        return

    # Test 4.2: RAG retrieval works
    try:
        # Get a rule's embedding for test
        scroll_result = qdrant_manager.client.scroll(
            collection_name=settings.qdrant_collection_financial_kb,
            limit=1,
            with_vectors=True
        )

        if scroll_result[0]:
            test_vector = scroll_result[0][0].vector

            retrieved_rules = qdrant_manager.retrieve_financial_rules(
                query_vector=test_vector,
                top_k=3
            )

            if retrieved_rules:
                results.add_pass("retrieve_financial_rules() works")
                logger.info(f"   Retrieved {len(retrieved_rules)} rules")

                top_rule = retrieved_rules[0]
                logger.info(f"   Top rule category: {top_rule.payload['category']}")
                logger.info(f"   Score: {top_rule.score:.3f}")
                logger.info(f"   Text preview: {top_rule.payload['text'][:100]}...")
            else:
                results.add_fail("retrieve_financial_rules() works", "No rules retrieved")
        else:
            results.add_fail("retrieve_financial_rules() setup", "No rules to test with")

    except Exception as e:
        results.add_fail("retrieve_financial_rules()", str(e))

    # Test 4.3: Category filtering
    try:
        # Try to find a financing category rule
        scroll_result = qdrant_manager.client.scroll(
            collection_name=settings.qdrant_collection_financial_kb,
            limit=10,
            with_vectors=True
        )

        financing_vector = None
        for point in scroll_result[0]:
            if point.payload.get('category') == 'financing':
                financing_vector = point.vector
                break

        if financing_vector:
            category_results = qdrant_manager.retrieve_financial_rules(
                query_vector=financing_vector,
                top_k=5,
                category='financing'
            )

            if category_results:
                results.add_pass("retrieve_financial_rules() category filter works")
                logger.info(f"   Found {len(category_results)} financing rules")
            else:
                results.add_fail("retrieve_financial_rules() category filter", "No results with category filter")
        else:
            logger.warning("   No 'financing' category rules found for testing")

    except Exception as e:
        results.add_fail("retrieve_financial_rules() category filter", str(e))


def verify_qdrant():
    """
    Main verification function

    Runs all test suites and reports results
    """
    logger.info("=" * 80)
    logger.info("QDRANT VERIFICATION - Comprehensive Test Suite")
    logger.info("=" * 80)

    results = TestResult()

    # Run all test suites
    test_qdrant_health(results)
    test_collections_exist(results)
    test_products_collection(results)
    test_financial_kb_collection(results)

    # Print summary
    all_passed = results.summary()

    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED - Qdrant is ready for production")
        return 0
    else:
        logger.error("\n⚠️ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    try:
        exit_code = verify_qdrant()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)
