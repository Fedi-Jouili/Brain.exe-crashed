"""
Initialize Thompson Sampling Parameters in Redis
Loads all products from Qdrant and initializes their alpha/beta parameters in Redis

Features:
- Initializes ALL products with uniform prior (alpha=1.0, beta=1.0)
- No bias, no hints, no historical data - pure reinforcement learning
- Idempotent: skips products already initialized
- Progress tracking with detailed logging

Run: python backend/scripts/initialize_thompson.py
"""
import sys
from pathlib import Path
import logging
import time

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from core.qdrant_client import qdrant_manager
from core.redis_client import redis_manager
from core.embeddings import MultimodalEmbedder
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_prerequisites() -> bool:
    """
    Check that Qdrant and Redis are accessible and have required data

    Returns:
        True if all prerequisites met, False otherwise
    """
    logger.info("\n📋 Checking prerequisites...")

    # Check Qdrant connection
    try:
        if not qdrant_manager.health_check():
            logger.error("❌ Qdrant is not healthy")
            return False
        logger.info("✓ Qdrant connection: OK")
    except Exception as e:
        logger.error(f"❌ Cannot connect to Qdrant: {e}")
        return False

    # Check Redis connection
    try:
        if not redis_manager.health_check():
            logger.error("❌ Redis is not healthy")
            return False
        logger.info("✓ Redis connection: OK")
    except Exception as e:
        logger.error(f"❌ Cannot connect to Redis: {e}")
        return False

    # Check products collection exists and has data
    try:
        info = qdrant_manager.get_collection_info(settings.qdrant_collection_products)
        product_count = info.points_count

        if product_count == 0:
            logger.error("❌ No products in Qdrant")
            logger.error("   Run 'python scripts/load_products_data.py' first")
            return False

        logger.info(f"✓ Products in Qdrant: {product_count}")

    except Exception as e:
        logger.error(f"❌ Cannot access products collection: {e}")
        return False

    logger.info("\n✅ All prerequisites met")
    return True


def retrieve_all_products() -> list:
    """
    Retrieve all products from Qdrant

    Uses search with very high limit and score_threshold=0 to get all products

    Returns:
        List of product dictionaries with metadata
    """
    logger.info("\n📦 Retrieving products from Qdrant...")

    try:
        # Get total count first
        info = qdrant_manager.get_collection_info(settings.qdrant_collection_products)
        total_count = info.points_count

        logger.info(f"Total products in Qdrant: {total_count}")

        # Use a dummy query vector to search all products
        # (Qdrant search with score_threshold=0 returns all)
        embedder = MultimodalEmbedder()
        dummy_query = embedder.embed_text("product")

        # Search with high limit to get all products
        results = qdrant_manager.search_products(
            query_vector=dummy_query,
            top_k=min(1000, total_count + 100),  # Add buffer, max 1000
            score_threshold=0.0  # Get all products regardless of similarity
        )

        logger.info(f"Retrieved {len(results)} products from Qdrant")

        # Convert to list of dicts with product_id only (minimal extraction)
        products = []
        for result in results:
            product = {
                'product_id': result.payload['product_id'],
                'name': result.payload.get('name', 'Unknown'),  # For logging only
            }
            products.append(product)

        if len(products) < total_count:
            logger.warning(
                f"⚠️  Retrieved {len(products)}/{total_count} products. "
                f"Some may be missing (Qdrant search limit)."
            )

        return products

    except Exception as e:
        logger.error(f"Failed to retrieve products: {e}")
        raise


def initialize_thompson_params(products: list) -> dict:
    """
    Initialize Thompson Sampling parameters for all products

    Args:
        products: List of product dictionaries

    Returns:
        Statistics dict with counts
    """
    logger.info("\n🎲 Initializing Thompson Sampling parameters...")
    logger.info(f"Processing {len(products)} products...\n")

    stats = {
        'total': len(products),
        'initialized': 0,
        'skipped': 0,
        'errors': 0
    }

    start_time = time.time()

    for i, product in enumerate(products, 1):
        product_id = product['product_id']

        try:
            # Check if already initialized
            existing_params = redis_manager.get_thompson_params(product_id)

            if existing_params is not None:
                # Already initialized, skip
                stats['skipped'] += 1
                logger.debug(f"[{i}/{len(products)}] Skipped {product_id} (already exists)")
                continue

            # Use uniform prior (1.0, 1.0) for ALL products
            # This ensures unbiased Thompson Sampling that learns only from user interactions
            alpha = settings.thompson_alpha_init  # 1.0
            beta = settings.thompson_beta_init    # 1.0

            # Initialize in Redis
            redis_manager.initialize_thompson_params(
                product_id=product_id,
                alpha=alpha,
                beta=beta
            )

            stats['initialized'] += 1

            # Log progress every 20 products
            if i % 20 == 0 or i == len(products):
                logger.info(
                    f"[{i}/{len(products)}] Initialized: {stats['initialized']}, "
                    f"Skipped: {stats['skipped']}"
                )

            # Detailed log for first few products
            if i <= 5:
                logger.info(
                    f"   ✓ {product_id}: α={alpha:.2f}, β={beta:.2f} "
                    f"(uniform prior) - {product['name'][:40]}"
                )

        except Exception as e:
            logger.error(f"Error initializing {product_id}: {e}")
            stats['errors'] += 1
            continue

    elapsed_time = time.time() - start_time

    logger.info(f"\n⏱️  Initialization completed in {elapsed_time:.1f} seconds")

    return stats


def verify_initialization(stats: dict) -> bool:
    """
    Verify that Thompson parameters were initialized correctly

    Args:
        stats: Statistics from initialization

    Returns:
        True if verification passed
    """
    logger.info("\n🔍 Verifying initialization...")

    try:
        # Get overall Thompson stats from Redis
        thompson_stats = redis_manager.get_thompson_stats()

        logger.info(f"\nRedis Thompson Statistics:")
        logger.info(f"   Products tracked: {thompson_stats['products_tracked']}")
        logger.info(f"   Average α: {thompson_stats['avg_alpha']:.3f}")
        logger.info(f"   Average β: {thompson_stats['avg_beta']:.3f}")
        logger.info(f"   Average conversion: {thompson_stats['avg_conversion']:.3f}")

        # Verify count matches
        expected_total = stats['initialized'] + stats['skipped']
        actual_total = thompson_stats['products_tracked']

        if actual_total >= stats['initialized']:
            logger.info(f"\n✅ Verification passed")
            logger.info(f"   Expected at least: {stats['initialized']}")
            logger.info(f"   Found in Redis: {actual_total}")
            return True
        else:
            logger.warning(f"\n⚠️  Count mismatch")
            logger.warning(f"   Initialized: {stats['initialized']}")
            logger.warning(f"   Found in Redis: {actual_total}")
            return False

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


def sample_products_verification(sample_size: int = 5):
    """
    Sample a few products and show their Thompson parameters

    Args:
        sample_size: Number of random products to sample
    """
    logger.info(f"\n📊 Sampling {sample_size} random products...")

    try:
        # Get a few products to verify
        embedder = MultimodalEmbedder()
        dummy_query = embedder.embed_text("product")
        results = qdrant_manager.search_products(
            query_vector=dummy_query,
            top_k=sample_size,
            score_threshold=0.0
        )

        logger.info("\nSample Product Parameters:")
        logger.info("-" * 80)

        for i, result in enumerate(results, 1):
            product_id = result.payload['product_id']
            name = result.payload['name']

            # Get Thompson params from Redis
            params = redis_manager.get_thompson_params(product_id)

            if params:
                logger.info(
                    f"{i}. {product_id}: {name[:40]}\n"
                    f"   α={params['alpha']:.2f}, β={params['beta']:.2f}, "
                    f"conversion={params['conversion_rate']:.3f}"
                )
            else:
                logger.warning(f"{i}. {product_id}: NOT FOUND IN REDIS")

        logger.info("-" * 80)

    except Exception as e:
        logger.error(f"Sample verification failed: {e}")


def main():
    """Main initialization workflow"""

    logger.info("=" * 80)
    logger.info("THOMPSON SAMPLING - REDIS INITIALIZATION")
    logger.info("=" * 80)

    try:
        # Step 1: Check prerequisites
        if not check_prerequisites():
            sys.exit(1)

        # Step 2: Retrieve all products from Qdrant
        products = retrieve_all_products()

        if not products:
            logger.error("No products found in Qdrant!")
            sys.exit(1)

        # Step 3: Initialize Thompson params in Redis
        stats = initialize_thompson_params(products)

        # Step 4: Verify initialization
        verify_initialization(stats)

        # Step 5: Show sample products (optional)
        sample_products_verification(sample_size=5)

        # Success!
        logger.info("\n" + "=" * 80)
        logger.info("✅ INITIALIZATION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Products processed: {stats['total']}")
        logger.info(f"Newly initialized: {stats['initialized']}")
        logger.info(f"Already existed: {stats['skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"All products initialized with uniform prior (α=1.0, β=1.0)")
        logger.info("\n🎯 Thompson Sampling ready for Agent 3!")

        return 0

    except KeyboardInterrupt:
        logger.warning("\nInitialization interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Initialization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
