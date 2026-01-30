"""
Similarity Service for PriceSense

Provides cluster-based product similarity logic.
Powers "similar products" recommendations without runtime embedding computation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for clustered products
_PRODUCTS_CACHE: Optional[List[Dict[str, Any]]] = None
_CLUSTER_INDEX: Optional[Dict[int, List[Dict[str, Any]]]] = None


def _load_clustered_products() -> List[Dict[str, Any]]:
    """
    Load clustered products from JSON file (with caching)

    Returns:
        List of products with embeddings and cluster_id
    """
    global _PRODUCTS_CACHE

    if _PRODUCTS_CACHE is not None:
        return _PRODUCTS_CACHE

    products_file = Path(__file__).parent.parent / "data" / "products_clustered.json"

    if not products_file.exists():
        logger.error(f"Clustering artifacts not found at {products_file}")
        raise FileNotFoundError(
            f"Clustering artifacts not found. Run clustering script first: "
            f"python backend/scripts/cluster_products.py"
        )

    logger.info(f"Loading clustered products from {products_file}")
    with open(products_file, 'r', encoding='utf-8') as f:
        _PRODUCTS_CACHE = json.load(f)

    logger.info(f"✅ Loaded {len(_PRODUCTS_CACHE)} clustered products")
    return _PRODUCTS_CACHE


def _build_cluster_index() -> Dict[int, List[Dict[str, Any]]]:
    """
    Build index mapping cluster_id to products (with caching)

    Returns:
        Dict mapping cluster_id to list of products
    """
    global _CLUSTER_INDEX

    if _CLUSTER_INDEX is not None:
        return _CLUSTER_INDEX

    products = _load_clustered_products()
    _CLUSTER_INDEX = {}

    for product in products:
        cluster_id = product.get('cluster_id')
        if cluster_id is not None:
            if cluster_id not in _CLUSTER_INDEX:
                _CLUSTER_INDEX[cluster_id] = []
            _CLUSTER_INDEX[cluster_id].append(product)

    logger.info(f"✅ Built cluster index: {len(_CLUSTER_INDEX)} clusters")
    return _CLUSTER_INDEX


def get_similar_products(
    product_id: str,
    limit: int = 5,
    exclude_self: bool = True,
    in_stock_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get similar products based on cluster membership

    Args:
        product_id: ID of the target product
        limit: Maximum number of similar products to return (default 5)
        exclude_self: Whether to exclude the original product (default True)
        in_stock_only: Whether to return only in-stock products (default False)

    Returns:
        List of similar products sorted by:
        1. Closest price to target
        2. Highest rating

    Example:
        >>> similar = get_similar_products("LAPTOP_MID_001", limit=3)
        >>> for product in similar:
        ...     print(f"{product['name']}: ${product['price']}")
    """
    products = _load_clustered_products()
    cluster_index = _build_cluster_index()

    # Find target product
    target_product = None
    for product in products:
        if product['product_id'] == product_id:
            target_product = product
            break

    if target_product is None:
        logger.warning(f"Product {product_id} not found in clustered products")
        return []

    target_cluster_id = target_product.get('cluster_id')
    if target_cluster_id is None:
        logger.warning(f"Product {product_id} has no cluster_id")
        return []

    target_price = target_product.get('price', 0)

    # Get products in same cluster
    cluster_products = cluster_index.get(target_cluster_id, [])

    # Filter
    candidates = []
    for product in cluster_products:
        # Exclude self
        if exclude_self and product['product_id'] == product_id:
            continue

        # Filter by stock
        if in_stock_only and not product.get('in_stock', True):
            continue

        candidates.append(product)

    # Sort by:
    # 1. Price difference (closest to target)
    # 2. Rating (highest first)
    candidates.sort(key=lambda p: (
        abs(p.get('price', 0) - target_price),  # Closest price
        -p.get('rating', 0)                      # Highest rating
    ))

    return candidates[:limit]


def get_cheaper_alternatives(
    product_id: str,
    max_price: Optional[float] = None,
    limit: int = 3,
    in_stock_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Get cheaper alternatives to a product within the same cluster

    Used by Agent 2.5 (PathFinder) for budget alternatives.

    Args:
        product_id: ID of the target product
        max_price: Maximum price threshold (default: use target product price)
        limit: Maximum number of alternatives (default 3)
        in_stock_only: Only return in-stock products (default True)

    Returns:
        List of cheaper alternatives sorted by price (ascending)

    Example:
        >>> alternatives = get_cheaper_alternatives("LAPTOP_PREMIUM_001", limit=3)
        >>> for alt in alternatives:
        ...     print(f"{alt['name']}: ${alt['price']}")
    """
    products = _load_clustered_products()
    cluster_index = _build_cluster_index()

    # Find target product
    target_product = None
    for product in products:
        if product['product_id'] == product_id:
            target_product = product
            break

    if target_product is None:
        logger.warning(f"Product {product_id} not found")
        return []

    target_cluster_id = target_product.get('cluster_id')
    if target_cluster_id is None:
        logger.warning(f"Product {product_id} has no cluster_id")
        return []

    # Use target price if max_price not specified
    if max_price is None:
        max_price = target_product.get('price', float('inf'))

    # Get products in same cluster
    cluster_products = cluster_index.get(target_cluster_id, [])

    # Filter cheaper alternatives
    alternatives = []
    for product in cluster_products:
        # Exclude self
        if product['product_id'] == product_id:
            continue

        # Must be cheaper
        product_price = product.get('price', float('inf'))
        if product_price >= max_price:
            continue

        # Filter by stock
        if in_stock_only and not product.get('in_stock', True):
            continue

        alternatives.append(product)

    # Sort by price (cheapest first), then rating (highest first)
    alternatives.sort(key=lambda p: (
        p.get('price', float('inf')),
        -p.get('rating', 0)
    ))

    return alternatives[:limit]


def get_cluster_products(
    cluster_id: int,
    limit: Optional[int] = None,
    in_stock_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get all products in a specific cluster

    Args:
        cluster_id: Cluster ID (0-9)
        limit: Maximum number of products to return (default: all)
        in_stock_only: Only return in-stock products (default False)

    Returns:
        List of products in the cluster, sorted by rating descending
    """
    cluster_index = _build_cluster_index()

    products = cluster_index.get(cluster_id, [])

    # Filter by stock
    if in_stock_only:
        products = [p for p in products if p.get('in_stock', True)]

    # Sort by rating
    products.sort(key=lambda p: -p.get('rating', 0))

    if limit is not None:
        products = products[:limit]

    return products


def get_cluster_summary() -> Dict[int, Dict[str, Any]]:
    """
    Get summary statistics for all clusters

    Returns:
        Dict mapping cluster_id to statistics:
        {
            0: {
                'count': 12,
                'avg_price': 1456.78,
                'price_range': (299.99, 2399.99),
                'top_category': 'Electronics',
                'top_subcategory': 'Gaming Laptops'
            },
            ...
        }
    """
    cluster_index = _build_cluster_index()
    summary = {}

    for cluster_id, products in cluster_index.items():
        prices = [p.get('price', 0) for p in products]
        categories = {}
        subcategories = {}

        for product in products:
            cat = product.get('category', 'Unknown')
            subcat = product.get('subcategory', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
            subcategories[subcat] = subcategories.get(subcat, 0) + 1

        top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else None
        top_subcategory = max(subcategories.items(), key=lambda x: x[1])[0] if subcategories else None

        summary[cluster_id] = {
            'count': len(products),
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'price_range': (min(prices), max(prices)) if prices else (0, 0),
            'top_category': top_category,
            'top_subcategory': top_subcategory
        }

    return summary


def find_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a product by ID

    Args:
        product_id: Product ID to search for

    Returns:
        Product dict if found, None otherwise
    """
    products = _load_clustered_products()

    for product in products:
        if product['product_id'] == product_id:
            return product

    return None


def clear_cache():
    """Clear the products cache (useful for testing or reloading data)"""
    global _PRODUCTS_CACHE, _CLUSTER_INDEX
    _PRODUCTS_CACHE = None
    _CLUSTER_INDEX = None
    logger.info("Cache cleared")
