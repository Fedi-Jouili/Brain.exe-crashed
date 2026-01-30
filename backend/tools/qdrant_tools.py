"""
Qdrant Tools - Vector Database Operations

This module provides 4 tools for interacting with the Qdrant vector database:

1. qdrant_search_products - Semantic product search using CLIP embeddings
2. qdrant_retrieve_financial_rules - RAG retrieval from financial knowledge base
3. qdrant_find_similar_users - Collaborative filtering via user similarity
4. cluster_alternatives - Find alternatives using K-Means clustering

Architecture:
- Each tool wraps a specific Qdrant operation
- Tools use lazy imports to avoid circular dependencies
- Input validation via Pydantic schemas
- Consistent error handling and logging

Usage Example:
    from tools.qdrant_tools import qdrant_search_products

    result = qdrant_search_products.invoke({
        "query_vector": embedding.tolist(),
        "top_k": 50,
        "filters": {"category": "Electronics", "in_stock": True},
        "score_threshold": 0.7
    })

    if result["success"]:
        products = result["data"]["products"]
        for product in products:
            print(f"{product['name']}: {product['similarity_score']}")
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from .base import BaseTool, ToolInput, ToolOutput
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: Product Search
# ============================================================================

class ProductSearchInput(ToolInput):
    """
    Input schema for semantic product search.

    Attributes:
        query_vector: 512-dimensional CLIP embedding
        top_k: Number of results to return (1-100)
        filters: Optional filters (category, price, in_stock, etc.)
        score_threshold: Minimum similarity score (0.0-1.0)
    """
    query_vector: List[float] = Field(
        ...,
        description="512-dimensional CLIP embedding vector",
        min_items=512,
        max_items=512
    )
    top_k: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of products to return"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Search filters (category, price, in_stock, rating, etc.)"
    )
    score_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )

    @validator('query_vector')
    def validate_vector_dimension(cls, v):
        """Ensure vector is 512-dimensional"""
        if len(v) != 512:
            raise ValueError(f"query_vector must be 512-dimensional, got {len(v)}")
        return v


class QdrantSearchProductsTool(BaseTool):
    """
    Semantic product search using CLIP-based multimodal embeddings.

    This tool searches the Qdrant products collection using vector similarity.
    It supports filtering by category, price, stock status, rating, etc.

    Used by:
        - Agent 1 (Product Discovery) - Initial candidate retrieval

    Algorithm:
        1. Receive query vector (512-dim CLIP embedding)
        2. Search Qdrant products collection
        3. Apply filters (category, price, stock, etc.)
        4. Apply score threshold
        5. Return top_k products sorted by similarity

    Example:
        tool = QdrantSearchProductsTool()
        result = tool.invoke({
            "query_vector": [0.1, 0.2, ...],  # 512-dim
            "top_k": 50,
            "filters": {
                "category": "Electronics",
                "max_price": 1000,
                "in_stock": True,
                "min_rating": 4.0
            },
            "score_threshold": 0.7
        })

        if result["success"]:
            products = result["data"]["products"]
            count = result["data"]["count"]
            print(f"Found {count} products")
    """

    name = "qdrant_search_products"
    description = "Search products using CLIP-based multimodal embeddings with optional filters"
    input_schema = ProductSearchInput

    def _execute(self, input_data: ProductSearchInput) -> ToolOutput:
        """
        Execute semantic product search in Qdrant.

        Args:
            input_data: Validated search parameters

        Returns:
            ToolOutput with:
                - products: List of product dicts with similarity_score
                - count: Number of products found
        """
        try:
            # Lazy import to avoid circular dependencies
            from core.qdrant_client import qdrant_manager

            logger.info(
                f"Searching products: top_k={input_data.top_k}, "
                f"threshold={input_data.score_threshold}, "
                f"filters={input_data.filters}"
            )

            # Execute Qdrant search
            search_results = qdrant_manager.search_products(
                query_vector=input_data.query_vector,
                top_k=input_data.top_k,
                filters=input_data.filters or {},
                score_threshold=input_data.score_threshold
            )

            # Convert Qdrant points to product dicts
            products = []
            for point in search_results:
                product = dict(point.payload)  # Copy payload
                product['similarity_score'] = float(point.score)  # Add score
                products.append(product)

            logger.info(f"Found {len(products)} products matching criteria")

            return ToolOutput(
                success=True,
                data={
                    "products": products,
                    "count": len(products)
                }
            )

        except Exception as e:
            logger.error(f"Product search failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Product search failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 2: Financial Rules Retrieval
# ============================================================================

class FinancialRulesInput(ToolInput):
    """
    Input schema for financial rules RAG retrieval.

    Attributes:
        context: Query context for semantic retrieval
        limit: Number of rules to retrieve (1-20)
        score_threshold: Minimum relevance score (0.0-1.0)
    """
    context: str = Field(
        ...,
        description="Query context for RAG retrieval (e.g., 'User earns $5000, wants $1000 laptop')",
        min_length=10
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of financial rules to retrieve"
    )
    score_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score threshold"
    )


class QdrantRetrieveFinancialRulesTool(BaseTool):
    """
    RAG retrieval of financial rules from knowledge base.

    This tool retrieves relevant financial rules for affordability analysis
    using semantic search over the financial_kb collection.

    Used by:
        - Agent 2 (Financial Analyzer) - Affordability assessment
        - Agent 4 (Explainer) - Financial reasoning explanations

    Knowledge Base:
        - Collection: financial_kb
        - Rules include: DTI limits, PTI ratios, emergency fund guidelines,
          credit score requirements, down payment rules, etc.
        - Each rule has: rule_id, rule_text, category, threshold, examples

    Algorithm:
        1. Embed context string using MultimodalEmbedder
        2. Search financial_kb collection
        3. Apply score threshold
        4. Return top limit rules sorted by relevance

    Example:
        tool = QdrantRetrieveFinancialRulesTool()
        result = tool.invoke({
            "context": "User earns $5000/month, wants $1000 laptop, has $2000 savings",
            "limit": 5,
            "score_threshold": 0.6
        })

        if result["success"]:
            rules = result["data"]["rules"]
            for rule in rules:
                print(f"{rule['category']}: {rule['rule_text']} (score: {rule['relevance_score']})")
    """

    name = "qdrant_retrieve_financial_rules"
    description = "Retrieve relevant financial rules for affordability analysis using RAG"
    input_schema = FinancialRulesInput

    def _execute(self, input_data: FinancialRulesInput) -> ToolOutput:
        """
        Execute financial rules retrieval.

        Args:
            input_data: Validated retrieval parameters

        Returns:
            ToolOutput with:
                - rules: List of rule dicts with relevance scores
                - count: Number of rules retrieved
        """
        try:
            # Lazy imports
            from core.qdrant_client import qdrant_manager
            from core.embeddings import MultimodalEmbedder

            logger.info(
                f"Retrieving financial rules: context='{input_data.context[:50]}...', "
                f"limit={input_data.limit}, threshold={input_data.score_threshold}"
            )

            # Generate context embedding
            embedder = MultimodalEmbedder()
            context_embedding = embedder.embed_text(input_data.context)

            # Search financial_kb collection
            search_results = qdrant_manager.client.search(
                collection_name="financial_kb",
                query_vector=context_embedding.tolist(),
                limit=input_data.limit,
                score_threshold=input_data.score_threshold
            )

            # Extract rule information
            rules = []
            for point in search_results:
                rule = {
                    "rule_id": point.payload.get("rule_id"),
                    "rule_text": point.payload.get("rule_text"),
                    "category": point.payload.get("category"),
                    "threshold": point.payload.get("threshold"),
                    "examples": point.payload.get("examples", []),
                    "relevance_score": float(point.score)
                }
                rules.append(rule)

            logger.info(f"Retrieved {len(rules)} financial rules")

            return ToolOutput(
                success=True,
                data={
                    "rules": rules,
                    "count": len(rules)
                }
            )

        except Exception as e:
            logger.error(f"Financial rules retrieval failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Financial rules retrieval failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 3: Similar Users (Collaborative Filtering)
# ============================================================================

class SimilarUsersInput(ToolInput):
    """
    Input schema for similar users search.

    Attributes:
        user_vector: 512-dimensional user preference embedding
        limit: Number of similar users to find (1-50)
        score_threshold: Minimum similarity score (0.0-1.0)
    """
    user_vector: List[float] = Field(
        ...,
        description="512-dimensional user preference vector",
        min_items=512,
        max_items=512
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of similar users to return"
    )
    score_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )

    @validator('user_vector')
    def validate_vector_dimension(cls, v):
        """Ensure vector is 512-dimensional"""
        if len(v) != 512:
            raise ValueError(f"user_vector must be 512-dimensional, got {len(v)}")
        return v


class QdrantFindSimilarUsersTool(BaseTool):
    """
    Find similar users for collaborative filtering.

    This tool finds users with similar preferences to enable
    collaborative filtering recommendations (users-who-liked-X-also-liked-Y).

    Used by:
        - Agent 3 (Smart Recommender) - Collaborative filtering signals

    Algorithm:
        1. Receive user preference vector (512-dim)
        2. Search users collection for similar vectors
        3. Apply score threshold
        4. Return similar users with their preferences

    User Representation:
        - Each user has a 512-dim preference vector
        - Vector encodes category preferences, price sensitivity, brand affinity
        - Updated incrementally based on interactions

    Example:
        tool = QdrantFindSimilarUsersTool()
        result = tool.invoke({
            "user_vector": current_user_embedding.tolist(),
            "limit": 10,
            "score_threshold": 0.6
        })

        if result["success"]:
            similar_users = result["data"]["similar_users"]
            for user in similar_users:
                print(f"User {user['user_id']}: similarity={user['similarity_score']}")
                print(f"  Liked products: {user['purchase_history_ids']}")
    """

    name = "qdrant_find_similar_users"
    description = "Find users with similar preferences for collaborative filtering"
    input_schema = SimilarUsersInput

    def _execute(self, input_data: SimilarUsersInput) -> ToolOutput:
        """
        Execute similar users search.

        Args:
            input_data: Validated search parameters

        Returns:
            ToolOutput with:
                - similar_users: List of user dicts with similarity scores
                - count: Number of similar users found
        """
        try:
            # Lazy import
            from core.qdrant_client import qdrant_manager

            logger.info(
                f"Finding similar users: limit={input_data.limit}, "
                f"threshold={input_data.score_threshold}"
            )

            # Search users collection
            search_results = qdrant_manager.client.search(
                collection_name="users",
                query_vector=input_data.user_vector,
                limit=input_data.limit,
                score_threshold=input_data.score_threshold
            )

            # Extract user data
            similar_users = []
            for point in search_results:
                user = {
                    "user_id": point.payload.get("user_id"),
                    "similarity_score": float(point.score),
                    "preferred_categories": point.payload.get("preferred_categories", []),
                    "purchase_history_ids": point.payload.get("purchase_history_ids", []),
                    "avg_purchase_price": point.payload.get("avg_purchase_price"),
                    "interaction_count": point.payload.get("interaction_count", 0)
                }
                similar_users.append(user)

            logger.info(f"Found {len(similar_users)} similar users")

            return ToolOutput(
                success=True,
                data={
                    "similar_users": similar_users,
                    "count": len(similar_users)
                }
            )

        except Exception as e:
            logger.error(f"Similar users search failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Similar users search failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 4: Cluster Alternatives
# ============================================================================

class ClusterAlternativesInput(ToolInput):
    """
    Input schema for cluster-based alternatives search.

    Attributes:
        product_id: Reference product ID (to exclude from results)
        cluster_id: K-Means cluster ID (0-9)
        budget: Maximum price constraint
        limit: Number of alternatives to return (1-10)
    """
    product_id: str = Field(
        ...,
        description="Reference product ID to find alternatives for"
    )
    cluster_id: int = Field(
        ...,
        ge=0,
        le=9,
        description="K-Means cluster ID (0-9)"
    )
    budget: float = Field(
        ...,
        gt=0,
        description="Maximum price constraint"
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of alternative products to return"
    )


class ClusterAlternativesTool(BaseTool):
    """
    Find alternative products using K-Means clustering.

    This tool finds similar products within the same K-Means cluster,
    filtered by budget and stock availability.

    Used by:
        - Agent 2.5 (PathFinder) - Budget-friendly alternatives
        - Agent 3 (Smart Recommender) - Similar product recommendations

    K-Means Clustering:
        - 10 clusters (0-9) based on product features
        - Clusters group similar products by category, features, price range
        - Each product has a cluster_id in its metadata

    Algorithm:
        1. Filter by cluster_id (same cluster as reference product)
        2. Filter by budget (price <= budget)
        3. Filter by in_stock = True
        4. Exclude reference product_id
        5. Return top limit alternatives

    Example:
        tool = ClusterAlternativesTool()
        result = tool.invoke({
            "product_id": "PROD0042",
            "cluster_id": 3,
            "budget": 1000.0,
            "limit": 3
        })

        if result["success"]:
            alternatives = result["data"]["alternatives"]
            for alt in alternatives:
                print(f"{alt['name']}: ${alt['price']} - {alt['reason']}")
    """

    name = "cluster_alternatives"
    description = "Find similar products using K-Means clustering with budget constraints"
    input_schema = ClusterAlternativesInput

    def _execute(self, input_data: ClusterAlternativesInput) -> ToolOutput:
        """
        Execute cluster alternatives search.

        Args:
            input_data: Validated search parameters

        Returns:
            ToolOutput with:
                - alternatives: List of alternative product dicts
                - count: Number of alternatives found
        """
        try:
            # Lazy imports
            from core.qdrant_client import qdrant_manager
            from qdrant_client.models import Filter, FieldCondition, Range, MatchValue

            logger.info(
                f"Finding cluster alternatives: product_id={input_data.product_id}, "
                f"cluster={input_data.cluster_id}, budget=${input_data.budget:.2f}, "
                f"limit={input_data.limit}"
            )

            # Build Qdrant filter
            filter_conditions = Filter(
                must=[
                    # Same cluster
                    FieldCondition(
                        key="cluster_id",
                        match=MatchValue(value=input_data.cluster_id)
                    ),
                    # In stock
                    FieldCondition(
                        key="in_stock",
                        match=MatchValue(value=True)
                    ),
                    # Within budget
                    FieldCondition(
                        key="price",
                        range=Range(lte=input_data.budget)
                    )
                ],
                must_not=[
                    # Exclude reference product
                    FieldCondition(
                        key="product_id",
                        match=MatchValue(value=input_data.product_id)
                    )
                ]
            )

            # Search with scroll (no vector search needed, just filtering)
            search_results = qdrant_manager.client.scroll(
                collection_name="products",
                scroll_filter=filter_conditions,
                limit=input_data.limit + 5,  # Get extra to ensure enough results
                with_vectors=False  # Don't need vectors
            )

            # Extract alternatives
            alternatives = []
            for point in search_results[0][:input_data.limit]:
                alt = {
                    "product_id": point.payload.get("product_id"),
                    "name": point.payload.get("name"),
                    "price": float(point.payload.get("price", 0)),
                    "rating": float(point.payload.get("rating", 0)),
                    "category": point.payload.get("category"),
                    "in_stock": point.payload.get("in_stock"),
                    "reason": "Similar product in same category cluster"
                }
                alternatives.append(alt)

            logger.info(f"Found {len(alternatives)} cluster alternatives")

            return ToolOutput(
                success=True,
                data={
                    "alternatives": alternatives,
                    "count": len(alternatives)
                }
            )

        except Exception as e:
            logger.error(f"Cluster alternatives search failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Cluster alternatives search failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL INSTANCES
# ============================================================================

# Create singleton instances for easy import
qdrant_search_products = QdrantSearchProductsTool()
qdrant_retrieve_financial_rules = QdrantRetrieveFinancialRulesTool()
qdrant_find_similar_users = QdrantFindSimilarUsersTool()
cluster_alternatives = ClusterAlternativesTool()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Tool classes
    "QdrantSearchProductsTool",
    "QdrantRetrieveFinancialRulesTool",
    "QdrantFindSimilarUsersTool",
    "ClusterAlternativesTool",
    # Tool instances
    "qdrant_search_products",
    "qdrant_retrieve_financial_rules",
    "qdrant_find_similar_users",
    "cluster_alternatives",
]
