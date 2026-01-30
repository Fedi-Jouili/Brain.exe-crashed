"""
Initialize Thompson Sampling Parameters in Redis
Sets initial alpha=1.0, beta=1.0 for all products in Qdrant

Run: python backend/scripts/initialize_thompson_redis.py

Prerequisites:
- Qdrant populated with products
- Redis running
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Force UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from core.redis_client import redis_manager
from core.qdrant_client import qdrant_manager
from core.embeddings import clip_embedder
from core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_product_ids():
    """Retrieve all product IDs from Qdrant"""
    logger.info("Retrieving all products from Qdrant...")
    
    # Use dummy query to get all products
    dummy_embedding = clip_embedder.embed_text("product")
    
    results = qdrant_manager.search_products(
        query_vector=dummy_embedding,
        top_k=1000,  # Get all products
        score_threshold=0.0  # No threshold
    )
    
    product_ids = [r['product_id'] for r in results]
    
    logger.info(f"✅ Retrieved {len(product_ids)} product IDs")
    return product_ids


def initialize_thompson_params(product_ids):
    """Initialize Thompson parameters for all products"""
    logger.info(f"Initializing Thompson parameters for {len(product_ids)} products...")
    
    initialized = 0
    skipped = 0
    
    for i, product_id in enumerate(product_ids):
        # Check if params already exist
        existing_params = redis_manager.get_thompson_params(product_id)
        
        if existing_params:
            logger.debug(f"  {product_id}: already initialized (skipping)")
            skipped += 1
        else:
            # Initialize with uniform prior (alpha=1.0, beta=1.0)
            redis_manager.initialize_thompson_params(
                product_id=product_id,
                alpha=1.0,
                beta=1.0
            )
            initialized += 1
        
        # Progress logging
        if (i + 1) % 20 == 0:
            logger.info(f"  Processed {i + 1}/{len(product_ids)} products")
    
    logger.info(f"✅ Initialized {initialized} products, skipped {skipped} (already initialized)")
    
    return initialized, skipped


def verify_initialization(product_ids):
    """Verify all products have Thompson parameters"""
    logger.info("Verifying initialization...")
    
    missing = []
    
    for product_id in product_ids:
        params = redis_manager.get_thompson_params(product_id)
        
        if not params:
            missing.append(product_id)
    
    if missing:
        logger.error(f"❌ {len(missing)} products missing Thompson params:")
        for pid in missing[:5]:
            logger.error(f"  - {pid}")
        if len(missing) > 5:
            logger.error(f"  ... and {len(missing) - 5} more")
        return False
    
    logger.info("✅ All products have Thompson parameters")
    return True


def show_sample_params(product_ids):
    """Show sample Thompson parameters"""
    logger.info("\nSample Thompson parameters:")
    
    for product_id in product_ids[:5]:
        params = redis_manager.get_thompson_params(product_id)
        
        if params:
            logger.info(
                f"  {product_id}: "
                f"α={params['alpha']:.2f}, "
                f"β={params['beta']:.2f}, "
                f"conversion_rate={params['conversion_rate']:.3f}"
            )


def main():
    """Main execution flow"""
    logger.info("=" * 80)
    logger.info("🚀 INITIALIZING THOMPSON SAMPLING PARAMETERS IN REDIS")
    logger.info("=" * 80)
    logger.info("")
    
    # Step 1: Check Redis health
    logger.info("1️⃣ Checking Redis connection...")
    if not redis_manager.health_check():
        logger.error("❌ Redis is not healthy")
        logger.error("   Make sure Redis is running: docker-compose up redis")
        return 1
    
    logger.info("✅ Redis is healthy")
    logger.info("")
    
    # Step 2: Check Qdrant health
    logger.info("2️⃣ Checking Qdrant connection...")
    if not qdrant_manager.health_check():
        logger.error("❌ Qdrant is not healthy")
        return 1
    
    logger.info("✅ Qdrant is healthy")
    logger.info("")
    
    # Step 3: Get all product IDs
    logger.info("3️⃣ Retrieving products from Qdrant...")
    product_ids = get_all_product_ids()
    
    if not product_ids:
        logger.error("❌ No products found in Qdrant")
        logger.error("   Run populate_qdrant.py first")
        return 1
    
    logger.info("")
    
    # Step 4: Initialize Thompson parameters
    logger.info("4️⃣ Initializing Thompson parameters...")
    initialized, skipped = initialize_thompson_params(product_ids)
    logger.info("")
    
    # Step 5: Verify initialization
    logger.info("5️⃣ Verifying initialization...")
    verification_passed = verify_initialization(product_ids)
    logger.info("")
    
    # Step 6: Show sample params
    logger.info("6️⃣ Sample parameters:")
    show_sample_params(product_ids)
    logger.info("")
    
    # Step 7: Get Thompson stats
    logger.info("7️⃣ Thompson Sampling statistics:")
    stats = redis_manager.get_thompson_stats()
    
    if stats:
        logger.info(f"  Products tracked: {stats.get('products_tracked', 0)}")
        logger.info(f"  Average α: {stats.get('avg_alpha', 0):.2f}")
        logger.info(f"  Average β: {stats.get('avg_beta', 0):.2f}")
        logger.info(f"  Average conversion: {stats.get('avg_conversion_rate', 0):.3f}")
    
    logger.info("")
    logger.info("=" * 80)
    if verification_passed:
        logger.info("✅ THOMPSON INITIALIZATION COMPLETE!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📊 Summary:")
        logger.info(f"   - Products initialized: {initialized}")
        logger.info(f"   - Products skipped: {skipped}")
        logger.info(f"   - Total products: {len(product_ids)}")
        logger.info("")
        logger.info("🎯 Thompson Sampling is ready!")
        logger.info("   Agents can now use reinforcement learning!")
    else:
        logger.error("❌ INITIALIZATION INCOMPLETE")
        logger.error("   Some products are missing Thompson parameters")
    
    logger.info("=" * 80)
    
    return 0 if verification_passed else 1


if __name__ == "__main__":
    sys.exit(main())
