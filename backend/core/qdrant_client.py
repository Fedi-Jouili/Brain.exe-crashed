"""
Qdrant vector database client for managing embeddings
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, Range,
    SearchRequest, ScoredPoint
)
from typing import List, Dict, Any, Optional
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages Qdrant vector database operations"""

    def __init__(self):
        """Initialize Qdrant client"""
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            grpc_port=settings.qdrant_grpc_port,
            prefer_grpc=False,  # Use HTTP to avoid gRPC version issues
            timeout=30,
            check_compatibility=False  # Suppress version warning
        )
        self.embedding_dim = settings.embedding_dimension

    # ========================================================================
    # COLLECTION MANAGEMENT
    # ========================================================================

    def create_collections(self):
        """Create all required collections if they don't exist"""
        collections = [
            settings.qdrant_collection_products,
            settings.qdrant_collection_users,
            settings.qdrant_collection_financial_kb,
            settings.qdrant_collection_transactions,
        ]

        # Get existing collections
        try:
            existing_collections = {col.name for col in self.client.get_collections().collections}
        except Exception as e:
            logger.warning(f"Could not fetch collections: {e}, assuming none exist")
            existing_collections = set()

        for collection_name in collections:
            if collection_name not in existing_collections:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")

    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)
            logger.info(f"Collection deleted: {collection_name}")

    # ========================================================================
    # PRODUCTS COLLECTION
    # ========================================================================

    def upsert_products(self, products: List[Dict[str, Any]]):
        """
        Insert or update products in the vector database

        Args:
            products: List of product dictionaries with 'embedding' and metadata
        """
        points = [
            PointStruct(
                id=hash(product['product_id']) & 0x7FFFFFFF,  # Convert string to positive int
                vector=product['embedding'],
                payload={
                    'product_id': product['product_id'],
                    'name': product['name'],
                    'description': product['description'],
                    'price': product['price'],
                    'category': product['category'],
                    'rating': product['rating'],
                    'num_reviews': product['num_reviews'],
                    'in_stock': product.get('in_stock', True),
                    'financing_available': product.get('financing_available', False),
                    'financing_terms': product.get('financing_terms'),
                    'cluster_id': product.get('cluster_id'),
                    'image_url': product.get('image_url'),
                    'subcategory': product.get('subcategory'),
                    'brand': product.get('brand'),
                }
            )
            for product in products
        ]

        self.client.upsert(
            collection_name=settings.qdrant_collection_products,
            points=points
        )
        logger.info(f"Upserted {len(points)} products")

    def batch_upsert_products(self, products: List[Dict[str, Any]], batch_size: int = 100):
        """
        Insert or update products in batches (for large datasets)

        Args:
            products: List of product dictionaries with 'embedding' and metadata
            batch_size: Number of products per batch (default 100)
        """
        total = len(products)
        logger.info(f"Starting batch upsert of {total} products (batch_size={batch_size})")

        for i in range(0, total, batch_size):
            batch = products[i:i + batch_size]
            self.upsert_products(batch)
            logger.info(f"Progress: {min(i + batch_size, total)}/{total} products upserted")

        logger.info(f"✅ Batch upsert complete: {total} products")

    def search_products(
        self,
        query_vector: List[float],
        top_k: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar products using vector similarity with cosine distance

        Args:
            query_vector: 512-dimensional query embedding
            top_k: Number of results to return
            filters: Optional filters:
                - in_stock: bool
                - max_price: float
                - min_price: float
                - category: str
                - subcategory: str
                - min_rating: float
                - cluster_id: int
                - financing_required: bool
            score_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of dicts with product payload + 'score' field (NO vectors)
        """
        if query_vector is None or len(query_vector) != self.embedding_dim:
            raise ValueError(f"query_vector must be {self.embedding_dim}-dimensional")

        # Build filter conditions
        filter_conditions = []

        if filters:
            # In stock filter
            if filters.get('in_stock'):
                filter_conditions.append(
                    FieldCondition(key="in_stock", match=MatchValue(value=True))
                )

            # Price range filters
            if 'max_price' in filters:
                filter_conditions.append(
                    FieldCondition(
                        key="price",
                        range=Range(lte=filters['max_price'])
                    )
                )

            if 'min_price' in filters:
                filter_conditions.append(
                    FieldCondition(
                        key="price",
                        range=Range(gte=filters['min_price'])
                    )
                )

            # Category filters
            if 'category' in filters:
                filter_conditions.append(
                    FieldCondition(key="category", match=MatchValue(value=filters['category']))
                )

            if 'subcategory' in filters:
                filter_conditions.append(
                    FieldCondition(key="subcategory", match=MatchValue(value=filters['subcategory']))
                )

            # Rating filter
            if 'min_rating' in filters:
                filter_conditions.append(
                    FieldCondition(
                        key="rating",
                        range=Range(gte=filters['min_rating'])
                    )
                )

            # Cluster ID filter
            if 'cluster_id' in filters:
                filter_conditions.append(
                    FieldCondition(key="cluster_id", match=MatchValue(value=filters['cluster_id']))
                )

            # Financing filter
            if filters.get('financing_required'):
                filter_conditions.append(
                    FieldCondition(key="financing_available", match=MatchValue(value=True))
                )

        # Build filter object
        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        try:
            # Use scroll for compatibility with different Qdrant versions
            # Scroll gets all matching points, then we filter by embedding similarity
            results = self.client.scroll(
                collection_name=settings.qdrant_collection_products,
                scroll_filter=search_filter,
                limit=top_k,
                with_vectors=True  # Need vectors for similarity calculation
            )

            points = results[0]

            # Calculate cosine similarity scores
            import numpy as np
            query_np = np.array(query_vector)
            query_norm = np.linalg.norm(query_np)

            scored_products = []
            for point in points:
                product_vector = np.array(point.vector)
                product_norm = np.linalg.norm(product_vector)

                if query_norm > 0 and product_norm > 0:
                    score = np.dot(query_np, product_vector) / (query_norm * product_norm)
                else:
                    score = 0.0

                if score >= score_threshold:
                    scored_products.append({
                        **point.payload,
                        'score': float(score)
                    })

            # Sort by score descending
            scored_products.sort(key=lambda x: x['score'], reverse=True)

            # Return top_k results
            products = scored_products[:top_k]

            logger.info(f"Found {len(products)} products matching query")
            return products

        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single product by product_id (uses scroll for exact match)

        Args:
            product_id: Product ID to search for

        Returns:
            Product payload dict (NO embedding) or None if not found
        """
        try:
            filter_condition = Filter(
                must=[FieldCondition(key="product_id", match=MatchValue(value=product_id))]
            )

            results = self.client.scroll(
                collection_name=settings.qdrant_collection_products,
                scroll_filter=filter_condition,
                limit=1,
                with_vectors=False
            )

            points = results[0]
            if points:
                return points[0].payload
            return None

        except Exception as e:
            logger.error(f"Error retrieving product {product_id}: {e}")
            return None

    def get_products_by_cluster(
        self,
        cluster_id: int,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        exclude_product_ids: Optional[List[str]] = None,
        in_stock_only: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get products from the same cluster (CRITICAL for Agent 2.5)

        Args:
            cluster_id: Cluster ID to filter by (0-9 for 10 clusters)
            max_price: Optional maximum price filter
            min_rating: Optional minimum rating filter
            exclude_product_ids: Optional list of product IDs to exclude
            in_stock_only: Only return in-stock products (default True)
            limit: Maximum number of products to return

        Returns:
            List of product dicts sorted by price ASCENDING (NO vectors)
        """
        try:
            # Build filter conditions
            filter_conditions = [
                FieldCondition(key="cluster_id", match=MatchValue(value=cluster_id))
            ]

            if max_price is not None:
                filter_conditions.append(
                    FieldCondition(key="price", range=Range(lte=max_price))
                )

            if min_rating is not None:
                filter_conditions.append(
                    FieldCondition(key="rating", range=Range(gte=min_rating))
                )

            if in_stock_only:
                filter_conditions.append(
                    FieldCondition(key="in_stock", match=MatchValue(value=True))
                )

            # Execute scroll query
            results = self.client.scroll(
                collection_name=settings.qdrant_collection_products,
                scroll_filter=Filter(must=filter_conditions),
                limit=limit * 2,  # Get extra for exclusion filtering
                with_vectors=False
            )

            points = results[0]

            # Convert to payload dicts
            products = [point.payload for point in points]

            # Apply exclusion filter
            if exclude_product_ids:
                exclude_set = set(exclude_product_ids)
                products = [p for p in products if p['product_id'] not in exclude_set]

            # Sort by price ASCENDING (cheapest first)
            products.sort(key=lambda p: p.get('price', float('inf')))

            # Apply final limit
            products = products[:limit]

            logger.info(f"Found {len(products)} products in cluster {cluster_id}")
            return products

        except Exception as e:
            logger.error(f"Error getting products from cluster {cluster_id}: {e}")
            return []

    # ========================================================================
    # USERS COLLECTION
    # ========================================================================

    def upsert_user(self, user_data: Dict[str, Any]):
        """Insert or update user profile"""
        point = PointStruct(
            id=hash(user_data['user_id']) & 0x7FFFFFFF,  # Convert string to positive int
            vector=user_data['preference_vector'],
            payload={
                'user_id': user_data['user_id'],
                'monthly_income': user_data['monthly_income'],
                'credit_score': user_data['credit_score'],
                'risk_tolerance': user_data.get('risk_tolerance', 'medium'),
                'preferred_categories': user_data.get('preferred_categories', []),
                'purchase_history': user_data.get('purchase_history', [])
            }
        )

        self.client.upsert(
            collection_name=settings.qdrant_collection_users,
            points=[point]
        )

    def find_similar_users(
        self,
        user_vector: List[float],
        top_k: int = 10,
        similarity_threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Find users with similar preferences (for collaborative filtering)"""
        # Use scroll for compatibility
        results = self.client.scroll(
            collection_name=settings.qdrant_collection_users,
            limit=top_k * 2,
            with_vectors=True
        )

        points = results[0]

        # Calculate similarity scores
        import numpy as np
        query_np = np.array(user_vector)
        query_norm = np.linalg.norm(query_np)

        scored_users = []
        for point in points:
            user_vec = np.array(point.vector)
            user_norm = np.linalg.norm(user_vec)

            if query_norm > 0 and user_norm > 0:
                score = np.dot(query_np, user_vec) / (query_norm * user_norm)
            else:
                score = 0.0

            if score >= similarity_threshold:
                class ScoredUser:
                    def __init__(self, payload, score):
                        self.payload = payload
                        self.score = score

                scored_users.append(ScoredUser(point.payload, float(score)))

        # Sort by score descending
        scored_users.sort(key=lambda x: x.score, reverse=True)

        return scored_users[:top_k]

    # ========================================================================
    # FINANCIAL KB COLLECTION
    # ========================================================================

    def upsert_financial_rules(self, rules: List[Dict[str, Any]]):
        """Insert financial knowledge base chunks"""
        points = [
            PointStruct(
                id=hash(rule['chunk_id']) & 0x7FFFFFFF,  # Convert string to positive int
                vector=rule['embedding'],
                payload={
                    'chunk_id': rule['chunk_id'],
                    'text': rule['text'],
                    'category': rule.get('category', 'general'),
                    'source': rule.get('source', 'system')
                }
            )
            for rule in rules
        ]

        self.client.upsert(
            collection_name=settings.qdrant_collection_financial_kb,
            points=points
        )
        logger.info(f"Upserted {len(points)} financial rule chunks")

    def retrieve_financial_rules(
        self,
        query_vector: List[float],
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant financial rules (RAG retrieval)"""
        filter_condition = None
        if category:
            filter_condition = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value=category))]
            )

        # Use scroll for compatibility
        results = self.client.scroll(
            collection_name=settings.qdrant_collection_financial_kb,
            scroll_filter=filter_condition,
            limit=top_k * 2,  # Get more for scoring
            with_vectors=True
        )

        points = results[0]

        # Calculate similarity scores
        import numpy as np
        query_np = np.array(query_vector)
        query_norm = np.linalg.norm(query_np)

        scored_rules = []
        for point in points:
            rule_vector = np.array(point.vector)
            rule_norm = np.linalg.norm(rule_vector)

            if query_norm > 0 and rule_norm > 0:
                score = np.dot(query_np, rule_vector) / (query_norm * rule_norm)
            else:
                score = 0.0

            # Create scored point-like object
            class ScoredRule:
                def __init__(self, payload, score):
                    self.payload = payload
                    self.score = score

            scored_rules.append(ScoredRule(point.payload, float(score)))

        # Sort by score descending
        scored_rules.sort(key=lambda x: x.score, reverse=True)

        return scored_rules[:top_k]

    # ========================================================================
    # TRANSACTIONS COLLECTION
    # ========================================================================

    def log_transaction(self, transaction: Dict[str, Any]):
        """Log user interaction/purchase"""
        point = PointStruct(
            id=hash(transaction['transaction_id']) & 0x7FFFFFFF,  # Convert string to positive int
            vector=transaction['embedding'],
            payload={
                'transaction_id': transaction['transaction_id'],
                'user_id': transaction['user_id'],
                'product_id': transaction['product_id'],
                'action': transaction['action'],
                'timestamp': transaction['timestamp'],
                'rating': transaction.get('rating'),
                'additional_data': transaction.get('additional_data', {})
            }
        )

        self.client.upsert(
            collection_name=settings.qdrant_collection_transactions,
            points=[point]
        )

    def get_user_transactions(
        self,
        user_id: str,
        action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transaction history for a user"""
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]

        if action:
            filter_conditions.append(
                FieldCondition(key="action", match=MatchValue(value=action))
            )

        results = self.client.scroll(
            collection_name=settings.qdrant_collection_transactions,
            scroll_filter=Filter(must=filter_conditions),
            limit=100,
            with_vectors=False
        )

        return [point.payload for point in results[0]]

    def get_product_transactions(
        self,
        product_id: str,
        action: Optional[str] = None,
        min_rating: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for a specific product (for social proof)"""
        filter_conditions = [
            FieldCondition(key="product_id", match=MatchValue(value=product_id))
        ]

        if action:
            filter_conditions.append(
                FieldCondition(key="action", match=MatchValue(value=action))
            )

        if min_rating:
            filter_conditions.append(
                FieldCondition(key="rating", range=Range(gte=min_rating))
            )

        results = self.client.scroll(
            collection_name=settings.qdrant_collection_transactions,
            scroll_filter=Filter(must=filter_conditions),
            limit=1000,
            with_vectors=False
        )

        return [point.payload for point in results[0]]

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        return self.client.get_collection(collection_name)

    def count_points(self, collection_name: str) -> int:
        """Count number of points in a collection"""
        info = self.get_collection_info(collection_name)
        return info.points_count

    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global instance
qdrant_manager = QdrantManager()
