"""
Populate Qdrant with clustered products

REQUIREMENTS:
- products_clustered.json MUST exist
- Embeddings MUST be 512-dimensional
- cluster_id MUST be present
- Qdrant MUST be running

FAIL FAST on validation errors.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from typing import List, Dict, Any

from core.qdrant_client import qdrant_manager
from core.config import settings
from validators.cluster_validator import validate_clustered_products

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_clustered_products() -> List[Dict[str, Any]]:
    """
    Load products_clustered.json with strict validation

    Returns:
        List of validated products with embeddings and cluster_id

    Raises:
        FileNotFoundError: If products_clustered.json doesn't exist
        ValueError: If validation fails
    """
    products_file = Path(__file__).parent.parent / "data" / "products_clustered.json"

    if not products_file.exists():
        logger.error(f"❌ products_clustered.json not found at {products_file}")
        logger.error("Run clustering script first: python backend/scripts/cluster_products.py")
        raise FileNotFoundError(f"Missing {products_file}")

    logger.info(f"Loading products from {products_file}")

    with open(products_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"✅ Loaded {len(products)} products")

    # STRICT VALIDATION - fail fast
    logger.info("Validating embeddings and cluster_id...")
    try:
        validate_clustered_products(products, expected_n_clusters=10)
        logger.info("✅ Validation passed")
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        raise ValueError(f"Invalid clustering data: {e}")

    return products


def populate_products():
    """
    Main population function

    Steps:
    1. Check Qdrant health
    2. Load and validate products_clustered.json
    3. Create collections if needed
    4. Batch upload products
    5. Verify count
    6. Test semantic search
    7. Print sample with cluster_id
    """
    logger.info("=" * 80)
    logger.info("POPULATE QDRANT - Products Collection")
    logger.info("=" * 80)

    # Step 1: Health check
    logger.info("\n[1/7] Checking Qdrant health...")
    if not qdrant_manager.health_check():
        logger.error("❌ Qdrant is not healthy. Is it running?")
        logger.error("Start with: docker-compose up -d")
        sys.exit(1)
    logger.info("✅ Qdrant is healthy")

    # Step 2: Load and validate products
    logger.info("\n[2/7] Loading products_clustered.json...")
    try:
        products = load_clustered_products()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"❌ Failed to load products: {e}")
        sys.exit(1)

    # Step 3: Create collections
    logger.info("\n[3/7] Creating collections...")
    try:
        qdrant_manager.create_collections()
        logger.info("✅ Collections ready")
    except Exception as e:
        logger.error(f"❌ Failed to create collections: {e}")
        sys.exit(1)

    # Step 4: Upload products
    logger.info(f"\n[4/7] Uploading {len(products)} products to Qdrant...")
    try:
        qdrant_manager.batch_upsert_products(products, batch_size=50)
        logger.info("✅ Products uploaded")
    except Exception as e:
        logger.error(f"❌ Failed to upload products: {e}")
        sys.exit(1)

    # Step 5: Verify count
    logger.info("\n[5/7] Verifying product count...")
    try:
        count = qdrant_manager.count_points(settings.qdrant_collection_products)
        logger.info(f"✅ Products in Qdrant: {count}")

        if count != len(products):
            logger.warning(f"⚠️ Count mismatch: expected {len(products)}, got {count}")
    except Exception as e:
        logger.error(f"❌ Failed to verify count: {e}")
        sys.exit(1)

    # Step 6: Test semantic search
    logger.info("\n[6/7] Testing semantic search...")
    try:
        # Use first product's embedding as test query
        test_product = products[0]
        test_embedding = test_product['embedding']

        search_results = qdrant_manager.search_products(
            query_vector=test_embedding,
            top_k=5,
            score_threshold=0.5
        )

        logger.info(f"✅ Semantic search works - found {len(search_results)} similar products")

        # Print top result
        if search_results:
            top = search_results[0]
            logger.info(f"   Top match: {top['name']} (score: {top['score']:.3f}, cluster_id: {top.get('cluster_id', 'N/A')})")

    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}")
        sys.exit(1)

    # Step 7: Print sample with cluster_id
    logger.info("\n[7/7] Sample products with cluster_id:")
    logger.info("-" * 80)

    # Get products from different clusters
    clusters_shown = set()
    for product in products[:20]:  # Check first 20
        cluster_id = product.get('cluster_id')
        if cluster_id not in clusters_shown:
            logger.info(f"  📦 {product['name']}")
            logger.info(f"     Price: ${product['price']:.2f} | Rating: {product.get('rating', 'N/A')}/5")
            logger.info(f"     Category: {product['category']} | Cluster: {cluster_id}")
            logger.info("")
            clusters_shown.add(cluster_id)

            if len(clusters_shown) >= 5:  # Show 5 different clusters
                break

    logger.info("=" * 80)
    logger.info("✅ POPULATE COMPLETE")
    logger.info(f"   Total products: {count}")
    logger.info(f"   Clusters represented: {len(set(p.get('cluster_id') for p in products))}")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        populate_products()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)
