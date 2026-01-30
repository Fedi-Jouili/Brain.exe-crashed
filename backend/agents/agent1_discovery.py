"""
Agent 1: Product Discovery Agent
Finds products using CLIP-based multimodal semantic search

ARCHITECTURE:
Uses MCP tools abstraction for loose coupling:
- qdrant_search_products tool (instead of direct qdrant_manager calls)
- Clean separation of concerns
- Testable with mocked tools
"""
import time
import logging
from typing import Dict, Any
from models.state import AgentState
from models.schemas import Product
from core.embeddings import MultimodalEmbedder
from core.config import settings

# MCP Tools (Model Context Protocol abstraction)
from tools.mcp_tools import qdrant_search_products

logger = logging.getLogger(__name__)


class ProductDiscoveryAgent:
    """
    Agent 1: Finds products matching user query using vector similarity

    Features:
    - Multimodal search (text + image)
    - CLIP ViT-B/32 embeddings (512-dimensional)
    - Qdrant vector database
    - Filters: price, category, in_stock, financing
    """

    def __init__(self):
        self.top_k = settings.search_top_k
        self.embedder = MultimodalEmbedder()

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute product discovery

        Args:
            state: Current agent state

        Returns:
            Updated state with candidate_products
        """
        start_time = time.time()

        try:
            logger.info("Agent 1: Starting product discovery")

            # Step 1: Generate query embedding
            query_embedding = self._generate_query_embedding(
                state['query'],
                state.get('image_embedding')
            )

            # Step 2: Build search filters
            filters = self._build_filters(state)

            # Step 3: Search using MCP tool (loose coupling)
            tool_result = qdrant_search_products.invoke({
                "query_vector": query_embedding,
                "top_k": self.top_k,
                "filters": filters,
                "score_threshold": 0.7
            })

            # Handle tool result
            if not tool_result["success"]:
                logger.error(f"Product search tool failed: {tool_result['error']}")
                state['candidate_products'] = []
                state['search_time_ms'] = int((time.time() - start_time) * 1000)
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(f"Product search failed: {tool_result['error']}")
                return state

            # Extract products from tool result
            products_data = tool_result["data"]["products"]

            # Step 4: Convert to Product objects
            candidate_products = self._convert_to_products_from_dicts(products_data)

            # Step 5: Update state
            state['candidate_products'] = candidate_products
            state['search_time_ms'] = int((time.time() - start_time) * 1000)

            logger.info(
                f"Agent 1: Found {len(candidate_products)} products in "
                f"{state['search_time_ms']}ms"
            )

            return state

        except Exception as e:
            logger.error(f"Agent 1 error: {e}", exc_info=True)
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append(f"Product Discovery: {str(e)}")
            state['candidate_products'] = []
            state['search_time_ms'] = int((time.time() - start_time) * 1000)
            return state

    def _generate_query_embedding(
        self,
        query: str,
        image_embedding: list = None
    ) -> list:
        """
        Generate query embedding (text + optional image)

        Args:
            query: Text query
            image_embedding: Optional pre-computed image embedding

        Returns:
            512-dimensional embedding
        """
        if image_embedding:
            # Multimodal: 70% text + 30% image
            logger.info("Generating multimodal embedding (text + image)")

            # Get text embedding
            text_embedding = self.embedder.embed_text(query)

            # Weighted combination
            import numpy as np
            image_array = np.array(image_embedding)

            combined = 0.7 * text_embedding + 0.3 * image_array
            combined = combined / np.linalg.norm(combined)

            return combined.tolist()
        else:
            # Text only
            logger.info("Generating text embedding")
            return self.embedder.embed_text(query).tolist()

    def _build_filters(self, state: AgentState) -> Dict[str, Any]:
        """
        Build search filters from state

        Args:
            state: Current agent state

        Returns:
            Filter dictionary for Qdrant
        """
        filters = {
            'in_stock': True  # Always filter for in-stock items
        }

        # User-provided filters
        user_filters = state.get('filters', {})

        # Budget filter (allow 1.5x flexibility)
        user_profile = state.get('user_profile')
        if user_profile and hasattr(user_profile, 'monthly_income') and user_profile.monthly_income > 0:
            # Estimate max affordable price
            max_price = user_filters.get('max_price')
            if not max_price:
                # Use safe cash limit × 1.5 as upper bound
                from utils.financial import FinancialCalculator
                safe_limit = FinancialCalculator.calculate_safe_cash_limit(user_profile)
                max_price = safe_limit * 1.5

            filters['max_price'] = max_price

        # Category filter
        if 'category' in user_filters:
            filters['category'] = user_filters['category']

        # Financing filter (check if mentioned in query)
        query_lower = state['query'].lower()
        if any(word in query_lower for word in ['financing', 'payment plan', 'installment']):
            filters['financing_required'] = True

        logger.debug(f"Search filters: {filters}")
        return filters

    def _convert_to_products_from_dicts(self, products_data: list) -> list:
        """
        Convert product dictionaries to Product objects

        NOTE: Tool already returns dictionaries (no Qdrant ScoredPoint objects),
        so this is simpler than the old _convert_to_products method.

        Args:
            products_data: List of product dicts from tool

        Returns:
            List of Product objects
        """
        products = []

        for product_dict in products_data:
            try:
                product = Product(
                    product_id=product_dict['product_id'],
                    name=product_dict['name'],
                    description=product_dict['description'],
                    price=product_dict['price'],
                    category=product_dict['category'],
                    rating=product_dict['rating'],
                    num_reviews=product_dict['num_reviews'],
                    image_url=product_dict.get('image_url'),
                    in_stock=product_dict.get('in_stock', True),
                    financing_available=product_dict.get('financing_available', False),
                    financing_terms=product_dict.get('financing_terms'),
                    cluster_id=product_dict.get('cluster_id'),
                    embedding=None  # Don't include embedding in response (large)
                )
                products.append(product)

            except Exception as e:
                logger.warning(f"Failed to convert product {product_dict.get('product_id', 'UNKNOWN')}: {e}")
                continue

        return products


# Global instance
product_discovery_agent = ProductDiscoveryAgent()

# Alias for export compliance
discovery_agent = product_discovery_agent
