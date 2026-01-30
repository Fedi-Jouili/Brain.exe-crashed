"""
Cluster & Embedding Validator for PriceSense

Validates clustering artifacts to ensure data integrity.
Used in CI tests and Qdrant population scripts.
"""
from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class ClusterValidationError(Exception):
    """Raised when clustering artifacts fail validation"""
    pass


def validate_clustered_products(
    products: List[Dict[str, Any]],
    expected_n_clusters: int = 10
) -> None:
    """
    Validate clustering artifacts for data integrity

    Args:
        products: List of product dicts with embeddings and cluster_id
        expected_n_clusters: Expected number of clusters (default 10)

    Raises:
        ClusterValidationError: If validation fails
    """
    if not products:
        raise ClusterValidationError("Product list is empty")

    errors = []
    warnings = []
    product_ids_seen: Set[str] = set()
    cluster_counts: Dict[int, int] = {}

    for idx, product in enumerate(products):
        product_id = product.get('product_id', f'<missing at index {idx}>')

        # ================================================================
        # 1. PRODUCT_ID VALIDATION
        # ================================================================
        if 'product_id' not in product:
            errors.append(f"Product at index {idx} missing 'product_id'")
            continue

        if not isinstance(product['product_id'], str):
            errors.append(f"Product {product_id}: product_id must be string, got {type(product['product_id']).__name__}")

        # Check uniqueness
        if product_id in product_ids_seen:
            errors.append(f"Duplicate product_id: {product_id}")
        product_ids_seen.add(product_id)

        # ================================================================
        # 2. EMBEDDING VALIDATION (CRITICAL)
        # ================================================================
        if 'embedding' not in product:
            errors.append(f"Product {product_id}: missing 'embedding' field")
            continue

        embedding = product['embedding']

        # Type check
        if not isinstance(embedding, list):
            errors.append(f"Product {product_id}: embedding must be list, got {type(embedding).__name__}")
            continue

        # Dimension check (CRITICAL)
        if len(embedding) != 512:
            errors.append(f"Product {product_id}: embedding dimension must be 512, got {len(embedding)}")
            continue

        # Value type check
        if not all(isinstance(x, (int, float)) for x in embedding):
            errors.append(f"Product {product_id}: embedding must contain only numbers")
            continue

        # Check for NaN/Inf
        if any(x != x for x in embedding):  # NaN check
            errors.append(f"Product {product_id}: embedding contains NaN values")

        if any(abs(x) == float('inf') for x in embedding):
            errors.append(f"Product {product_id}: embedding contains Infinity values")

        # ================================================================
        # 3. CLUSTER_ID VALIDATION (CRITICAL)
        # ================================================================
        if 'cluster_id' not in product:
            errors.append(f"Product {product_id}: missing 'cluster_id' field")
            continue

        cluster_id = product['cluster_id']

        # Type check
        if not isinstance(cluster_id, int):
            errors.append(f"Product {product_id}: cluster_id must be int, got {type(cluster_id).__name__}")
            continue

        # Range check
        if cluster_id < 0 or cluster_id >= expected_n_clusters:
            errors.append(
                f"Product {product_id}: cluster_id {cluster_id} out of range [0, {expected_n_clusters-1}]"
            )
            continue

        # Track cluster distribution
        cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1

    # ================================================================
    # 4. CLUSTER DISTRIBUTION VALIDATION (SOFT)
    # ================================================================

    # Check if all clusters are represented
    missing_clusters = set(range(expected_n_clusters)) - set(cluster_counts.keys())
    if missing_clusters:
        warnings.append(f"Missing clusters: {sorted(missing_clusters)}")

    # Check for clusters with too few products (soft constraint)
    for cluster_id, count in cluster_counts.items():
        if count < 2:
            warnings.append(f"Cluster {cluster_id} has only {count} product(s) - may cause poor alternatives")

    # ================================================================
    # 5. REPORT RESULTS
    # ================================================================

    # Log warnings
    if warnings:
        logger.warning(f"Validation warnings ({len(warnings)}):")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    # Fail if errors
    if errors:
        error_message = f"Clustering validation failed with {len(errors)} error(s):\n"
        for error in errors[:10]:  # Show max 10 errors
            error_message += f"  - {error}\n"
        if len(errors) > 10:
            error_message += f"  ... and {len(errors) - 10} more errors\n"
        raise ClusterValidationError(error_message)

    # Success
    logger.info(f"✅ Clustering validation passed: {len(products)} products, {len(cluster_counts)} clusters")
    logger.info(f"   Cluster distribution: {dict(sorted(cluster_counts.items()))}")


def validate_single_product(product: Dict[str, Any]) -> bool:
    """
    Quick validation for a single product

    Args:
        product: Product dict

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields
        if 'product_id' not in product:
            return False
        if 'embedding' not in product:
            return False
        if 'cluster_id' not in product:
            return False

        # Check embedding
        embedding = product['embedding']
        if not isinstance(embedding, list):
            return False
        if len(embedding) != 512:
            return False

        # Check cluster_id
        cluster_id = product['cluster_id']
        if not isinstance(cluster_id, int):
            return False
        if cluster_id < 0:
            return False

        return True
    except Exception:
        return False


def get_validation_summary(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get validation summary without raising exceptions

    Args:
        products: List of product dicts

    Returns:
        Dict with validation statistics
    """
    summary = {
        'total_products': len(products),
        'valid_products': 0,
        'invalid_products': 0,
        'missing_embeddings': 0,
        'invalid_embeddings': 0,
        'missing_cluster_id': 0,
        'invalid_cluster_id': 0,
        'cluster_distribution': {}
    }

    for product in products:
        is_valid = True

        # Check embedding
        if 'embedding' not in product:
            summary['missing_embeddings'] += 1
            is_valid = False
        elif not isinstance(product.get('embedding'), list) or len(product.get('embedding', [])) != 512:
            summary['invalid_embeddings'] += 1
            is_valid = False

        # Check cluster_id
        if 'cluster_id' not in product:
            summary['missing_cluster_id'] += 1
            is_valid = False
        elif not isinstance(product.get('cluster_id'), int):
            summary['invalid_cluster_id'] += 1
            is_valid = False
        else:
            cluster_id = product['cluster_id']
            summary['cluster_distribution'][cluster_id] = summary['cluster_distribution'].get(cluster_id, 0) + 1

        if is_valid:
            summary['valid_products'] += 1
        else:
            summary['invalid_products'] += 1

    return summary
