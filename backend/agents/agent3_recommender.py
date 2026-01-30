"""
Agent 3: Smart Recommender
Applies Thompson Sampling, collaborative filtering, and diversity injection
to rank and recommend products
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import numpy as np

# Optional imports for type hints (fallback to Any if not available)
try:
    from models.state import AgentState
    from models.schemas import UserProfile, Product, Recommendation
except ImportError:
    AgentState = Dict[str, Any]
    UserProfile = Any
    Product = Any
    Recommendation = Any

from ml.thompson_sampling import ThompsonSamplingEngine

try:
    from core.qdrant_client import qdrant_manager
    from core.embeddings import MultimodalEmbedder
    from qdrant_client.models import Filter, FieldCondition, Range
    QDRANT_AVAILABLE = True
except ImportError:
    qdrant_manager = None
    MultimodalEmbedder = None
    Filter = None
    FieldCondition = None
    Range = None
    QDRANT_AVAILABLE = False

try:
    from core.redis_client import redis_manager
    REDIS_AVAILABLE = True
except ImportError:
    redis_manager = None
    REDIS_AVAILABLE = False

from core.config import settings

logger = logging.getLogger(__name__)


class SmartRecommenderAgent:
    """
    Agent 3: Intelligent Product Ranking

    Responsibilities:
    1. Thompson Sampling scoring from Redis α,β parameters
    2. Financial scoring from Agent 2 (0.0-1.0)
    3. RAGAS re-ranking for answer quality
    4. K-Means cluster alternatives for serendipity
    5. Epsilon-Greedy diversity injection
    6. Return top 10 ranked recommendations

    🔒 SCORE CONTRACT (LOCKED):
    - Thompson Sampling (0.4 weight): Bandit-based exploration
    - Financial Score (0.3 weight): From Agent 2 (0.0-1.0)
    - RAGAS Relevancy (0.2 weight): Query-product match quality
    - Diversity Bonus (0.1 weight): Cluster variety

    All scores normalized to 0.0-1.0 before weighting.
    """

    def __init__(self):
        self.epsilon = 0.15  # 15% exploration rate

        # 🔒 SCORE CONTRACT: These weights are LOCKED
        self.thompson_weight = 0.4
        self.financial_weight = 0.3  # Uses Agent 2's financial_score
        self.ragas_weight = 0.2
        self.diversity_weight = 0.1

        # Initialize Thompson Sampling engine (production-safe batch API)
        self.thompson_engine = ThompsonSamplingEngine()

        logger.info("Smart Recommender Agent initialized with Thompson Sampling engine")

    def execute(self, state: Union[Dict[str, Any], AgentState]) -> Union[Dict[str, Any], AgentState]:
        """
        Rank affordable products using multi-factor intelligence

        Args:
            state: Current agent state with affordable_products

        Returns:
            Updated state with top 10 recommendations
        """
        start_time = self._get_timestamp()
        logger.info("Agent 3: Starting smart recommendation")

        try:
            affordable_products = state.get('affordable_products', [])

            if not affordable_products:
                logger.warning("Agent 3: No affordable products to recommend")
                state['final_recommendations'] = []
                return state

            logger.info(f"Ranking {len(affordable_products)} affordable products")

            # Step 1: Collect all product IDs for batch Thompson ranking
            product_ids = [
                item['product'].product_id if hasattr(item['product'], 'product_id')
                else item['product']['product_id']
                for item in affordable_products
            ]

            # Get Thompson scores in one batch call (production-safe)
            thompson_scores = self._get_thompson_scores(product_ids)
            logger.info(f"Thompson Sampling: Ranked {len(thompson_scores)} products")

            # Step 2: Calculate all scores for each product
            scored_products = []
            user_profile = state.get('user_profile')

            for item in affordable_products:
                product = item['product']
                product_id = product.product_id if hasattr(product, 'product_id') else product['product_id']

                # Get financial score from Agent 2 (already 0.0-1.0)
                financial_score = item.get('financial_score', 0.5)

                # 🔒 CONTRACT: All scores MUST be normalized to 0.0-1.0 before weighting
                scores = {
                    'thompson': thompson_scores.get(product_id, 50.0) / 100.0,  # Normalize 0-100 → 0.0-1.0
                    'financial': financial_score,  # Already 0.0-1.0 from Agent 2
                    'ragas': self._calculate_ragas_score(
                        product=product,
                        query=state['query']
                    ) / 100.0,  # Normalize 0-100 → 0.0-1.0
                    'diversity': 0.0  # Applied later
                }

                # Calculate composite score (all components 0.0-1.0)
                # 🔒 CONTRACT: Weights are LOCKED (0.4 + 0.3 + 0.2 + 0.1 = 1.0)
                composite_score = (
                    scores['thompson'] * self.thompson_weight +
                    scores['financial'] * self.financial_weight +
                    scores['ragas'] * self.ragas_weight
                )

                scored_products.append({
                    'product': product,
                    'affordability': item['affordability'],
                    'financial_score': financial_score,
                    'thompson_score': scores['thompson'] * 100.0,  # Store as 0-100 for display
                    'ragas_score': scores['ragas'] * 100.0,  # Store as 0-100 for display
                    'composite_score': composite_score,  # Normalized 0.0-1.0
                    'diversity_bonus': 0.0,
                    'final_score': composite_score  # Normalized 0.0-1.0
                })

            # Step 3: Apply diversity injection (epsilon-greedy) if user profile available
            if user_profile:
                scored_products = self._apply_diversity_injection(scored_products, user_profile)

            # Step 4: Sort by final score
            ranked_products = sorted(scored_products, key=lambda x: x['final_score'], reverse=True)

            # Step 5: Take top 10
            top_10 = ranked_products[:10]

            # Log top 3 for debugging
            logger.info("Top 3 recommendations:")
            for i, item in enumerate(top_10[:3], 1):
                prod = item['product']
                prod_name = prod.name if hasattr(prod, 'name') else prod['name']
                logger.info(f"  {i}. {prod_name} (Thompson: {item['thompson_score']:.1f}, Final: {item['final_score']:.1f})")

            # Step 6: Find cluster alternatives for each top product
            enriched_recommendations = []
            for rank, item in enumerate(top_10, 1):
                product = item['product']
                alternatives = self._find_cluster_alternatives(product, limit=2)

                recommendation = {
                    'rank': rank,
                    'product': product,
                    'scores': {
                        'thompson': item['thompson_score'],  # Display as 0-100
                        'ragas': item['ragas_score'],  # Display as 0-100
                        'diversity_bonus': item['diversity_bonus'],
                        'composite': item['composite_score'] * 100.0,  # Display as 0-100
                        'financial': item['financial_score']  # Display as 0.0-1.0 (contract)
                    },
                    'final_score': item['final_score'] * 100.0,  # Display as 0-100
                    'affordability': item['affordability'],
                    'cluster_alternatives': alternatives,
                    'explanation': self._generate_explanation(item, rank)
                }

                enriched_recommendations.append(recommendation)

            # Update state
            state['final_recommendations'] = enriched_recommendations
            state['recommender_time_ms'] = int(self._get_timestamp() - start_time)

            logger.info(f"Agent 3 complete: Generated {len(enriched_recommendations)} recommendations in {state['recommender_time_ms']}ms")
            logger.info(f"Agent 3 DEBUG: State now has {len(state.get('final_recommendations', []))} recommendations")

            return state

        except Exception as e:
            logger.error(f"Agent 3 error: {e}", exc_info=True)
            state['errors'] = state.get('errors', []) + [f"Recommendation failed: {str(e)}"]
            state['final_recommendations'] = []
            return state

    def _get_thompson_scores(self, product_ids: List[str]) -> Dict[str, float]:
        """
        Get Thompson Sampling scores for a batch of products.

        Uses production-safe rank_product_ids() for batch ranking.
        Returns a mapping {product_id: score}.

        This is the ONLY method that should interact with Thompson Sampling.
        Agent 3 must NOT call sample_score() per product.

        Args:
            product_ids: List of product identifiers

        Returns:
            Dictionary mapping product_id to Thompson score (0-100 scale)
        """
        try:
            if not product_ids:
                return {}

            # Call production-safe batch ranking API
            # Returns List[Tuple[product_id, thompson_score]] sorted by score
            ranked_tuples = self.thompson_engine.rank_product_ids(product_ids)

            # Convert to dict and scale to 0-100
            # Thompson scores are in [0, 1], scale to [0, 100] for consistency
            thompson_scores = {
                product_id: score * 100
                for product_id, score in ranked_tuples
            }

            logger.debug(f"Thompson batch ranking: {len(thompson_scores)} products scored")
            return thompson_scores

        except Exception as e:
            logger.warning(f"Error in Thompson batch ranking: {e}")
            # Return uniform scores (50.0) on error - never crash Agent 3
            return {product_id: 50.0 for product_id in product_ids}

    def _calculate_collaborative_score(
        self,
        product: Any,
        user_profile: UserProfile
    ) -> float:
        """
        Collaborative filtering score based on similar users.

        TODO: Implement collaborative filtering logic.
        For MVP, return neutral score.

        Args:
            product: Product to score
            user_profile: Current user profile

        Returns:
            Collaborative score 0-100 (currently 0.0 - placeholder)
        """
        # Placeholder for future implementation
        # Will use user similarity and purchase history
        return 0.0

    def _calculate_ragas_score(
        self,
        product: Any,
        query: str
    ) -> float:
        """
        RAGAS relevancy score - how well product matches query.

        TODO: Implement RAGAS-based relevancy scoring.
        For MVP, return neutral score.

        Args:
            product: Product to score
            query: User search query

        Returns:
            RAGAS relevancy score 0-100 (currently 50.0 - placeholder)
        """
        # Placeholder for future RAGAS implementation
        # Will use query-product relevancy metrics
        return 50.0

    def _apply_diversity_injection(
        self,
        scored_products: List[Dict[str, Any]],
        user_profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """
        Apply epsilon-greedy exploration for diversity

        Strategy:
        - Positions 1-7: Keep best scores (exploitation)
        - Positions 8-9: Moderate randomization
        - Position 10: Force different cluster (serendipity)

        Args:
            scored_products: All scored products
            user_profile: User profile for cluster preference

        Returns:
            Products with diversity bonus applied
        """
        if len(scored_products) < 3:
            return scored_products  # Can't apply diversity with < 3 products

        # Sort by composite score first
        ranked = sorted(scored_products, key=lambda x: x['composite_score'], reverse=True)

        # Top 7: Keep as is (exploitation)
        top_7 = ranked[:7]
        remaining = ranked[7:]

        # Positions 8-9: Add randomization
        if len(remaining) >= 2:
            # Add noise to scores
            for item in remaining[:2]:
                noise = np.random.normal(0, 0.05)  # ±5% noise
                item['diversity_bonus'] = noise * 10
                item['final_score'] = item['composite_score'] + item['diversity_bonus']

        # Position 10: Force different cluster
        if len(remaining) >= 3:
            # Find a product from different cluster than top pick
            top_cluster = top_7[0]['product'].cluster_id if hasattr(top_7[0]['product'], 'cluster_id') else top_7[0]['product'].get('cluster_id')

            different_cluster_idx = None
            for i, item in enumerate(remaining):
                cluster = item['product'].cluster_id if hasattr(item['product'], 'cluster_id') else item['product'].get('cluster_id')
                if cluster != top_cluster:
                    different_cluster_idx = i
                    break

            if different_cluster_idx is not None:
                # Boost score for serendipity
                remaining[different_cluster_idx]['diversity_bonus'] = 15
                remaining[different_cluster_idx]['final_score'] = remaining[different_cluster_idx]['composite_score'] + 15

        return top_7 + remaining

    def _find_cluster_alternatives(
        self,
        product: Any,
        limit: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find 2-3 similar products in same cluster

        Args:
            product: Reference product
            limit: Number of alternatives to return

        Returns:
            List of alternative products
        """
        try:
            cluster_id = product.cluster_id if hasattr(product, 'cluster_id') else product.get('cluster_id')
            product_id = product.product_id if hasattr(product, 'product_id') else product['product_id']

            if cluster_id is None:
                return []

            # Query for products in same cluster
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="cluster_id",
                        match={'value': cluster_id}
                    ),
                    FieldCondition(
                        key="in_stock",
                        match={'value': True}
                    )
                ]
            )

            results = qdrant_manager.client.scroll(
                collection_name=settings.qdrant_collection_products,
                scroll_filter=filter_condition,
                limit=limit + 2,  # Get extra to filter out the main product
                with_vectors=False
            )

            alternatives = []
            if results:
                for point in results[0]:
                    payload = point.payload
                    if payload['product_id'] != product_id:  # Skip the main product
                        alternatives.append({
                            'product_id': payload['product_id'],
                            'name': payload['name'],
                            'price': payload['price'],
                            'rating': payload.get('rating', 0),
                            'num_reviews': payload.get('num_reviews', 0)
                        })

                        if len(alternatives) >= limit:
                            break

            return alternatives

        except Exception as e:
            logger.warning(f"Error finding cluster alternatives: {e}")
            return []

    def _generate_explanation(
        self,
        item: Dict[str, Any],
        rank: int
    ) -> str:
        """
        Generate human-readable explanation for recommendation

        Args:
            item: Scored product item
            rank: Ranking position

        Returns:
            Explanation string
        """
        product = item['product']
        product_name = product.name if hasattr(product, 'name') else product['name']
        product_rating = product.rating if hasattr(product, 'rating') else product.get('rating', 0)
        scores = item

        # Build explanation based on top factors
        reasons = []

        # Thompson Sampling
        if scores['thompson_score'] > 70:
            reasons.append("✅ Popular choice (high engagement)")

        # Collaborative filtering
        if scores['collaborative_score'] > 60:
            reasons.append("✅ Similar users love this")

        # RAGAS relevancy
        if scores['ragas_score'] > 70:
            reasons.append("✅ Perfect match for your search")

        # Rating
        if product_rating > 4.5:
            reasons.append(f"⭐ Highly rated ({product_rating}/5)")

        # Financial
        affordability = item['affordability']
        if affordability.get('can_afford_cash'):
            reasons.append("💰 Affordable with cash")
        elif affordability.get('can_afford_financing'):
            reasons.append("💳 Available with financing")

        if not reasons:
            reasons.append("🎯 Strong overall match")

        reason_text = " • ".join(reasons)

        return f"#{rank} {product_name} - {reason_text}"

    def _get_timestamp(self) -> float:
        """Get current timestamp in milliseconds"""
        import time
        return time.time() * 1000


# Global agent instance
smart_recommender_agent = SmartRecommenderAgent()
