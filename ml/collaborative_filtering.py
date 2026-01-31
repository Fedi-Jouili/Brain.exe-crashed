"""
Collaborative Filtering Module - Standalone Implementation
Finds similar users and recommends products they purchased

Author: FinCommerce ML Team
Created: January 31, 2026
Requirements: numpy, scipy
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from scipy.spatial.distance import cosine
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class CollaborativeFilter:
    """
    User-user collaborative filtering using vector similarity.

    Workflow:
    1. Find K similar users using cosine similarity
    2. Aggregate products from similar users
    3. Weight products by user similarity
    4. Return ranked product recommendations

    Can work with:
    - Pre-computed user embeddings (512-dim from Qdrant)
    - OR on-the-fly feature vectors (constructed from user profile)

    Usage:
        cf = CollaborativeFilter()

        # Find similar users
        similar_users = cf.find_similar_users(
            user_vector=[0.1, 0.5, ...],  # 512-dim
            all_user_vectors={
                "USER001": [0.2, 0.4, ...],
                "USER002": [0.1, 0.6, ...],
            },
            top_k=10,
            score_threshold=0.6
        )
        # Returns: [("USER001", 0.85), ("USER002", 0.70), ...]

        # Get product recommendations
        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history={
                "USER001": ["PROD001", "PROD002"],
                "USER002": ["PROD001", "PROD003"]
            },
            top_k=10,
            exclude_products=["PROD001"]  # Already purchased
        )
        # Returns: [("PROD002", 85.0), ("PROD003", 70.0), ...]

        # Calculate score for single product (Agent 3 use case)
        score = cf.calculate_product_score_for_user(
            product_id="PROD005",
            user_vector=[0.1, 0.5, ...],
            all_user_vectors={...},
            purchase_history={...}
        )
        # Returns: 0.0-100.0
    """

    def __init__(self, default_top_k: int = 10, default_threshold: float = 0.6):
        """
        Initialize collaborative filter.

        Args:
            default_top_k: Default number of similar users to find
            default_threshold: Default minimum similarity score (0.0-1.0)
        """
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold
        logger.info(f"CollaborativeFilter initialized (top_k={default_top_k}, threshold={default_threshold})")

    def find_similar_users(
        self,
        user_vector: List[float],
        all_user_vectors: Dict[str, List[float]],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """
        Find K most similar users using cosine similarity.

        Args:
            user_vector: Target user's 512-dim embedding
            all_user_vectors: Dict of {user_id: 512-dim embedding}
            top_k: Number of similar users to return (default: self.default_top_k)
            score_threshold: Minimum similarity score 0.0-1.0 (default: self.default_threshold)

        Returns:
            List of (user_id, similarity_score) tuples, sorted by score descending

        Example:
            similar = cf.find_similar_users(
                user_vector=[0.1, 0.2, ...],
                all_user_vectors={"USER001": [...], "USER002": [...]},
                top_k=5
            )
            # Returns: [("USER001", 0.92), ("USER002", 0.85), ...]
        """
        top_k = top_k or self.default_top_k
        score_threshold = score_threshold or self.default_threshold

        try:
            # Convert to numpy array
            user_vec = np.array(user_vector)

            # Validate input
            if len(user_vec) == 0:
                logger.warning("Empty user vector provided")
                return []

            if not all_user_vectors:
                logger.warning("No user vectors provided for comparison")
                return []

            # Calculate similarities
            similarities = []
            for other_user_id, other_vector in all_user_vectors.items():
                try:
                    other_vec = np.array(other_vector)

                    # Validate dimensions
                    if len(user_vec) != len(other_vec):
                        logger.warning(
                            f"Dimension mismatch: user={len(user_vec)}, "
                            f"{other_user_id}={len(other_vec)} - skipping"
                        )
                        continue

                    # Check for zero vectors
                    if np.linalg.norm(user_vec) == 0 or np.linalg.norm(other_vec) == 0:
                        logger.debug(f"Zero vector detected for {other_user_id} - skipping")
                        continue

                    # Calculate cosine similarity
                    similarity = 1 - cosine(user_vec, other_vec)

                    # Filter by threshold
                    if similarity >= score_threshold:
                        similarities.append((other_user_id, float(similarity)))

                except Exception as e:
                    logger.debug(f"Error calculating similarity for {other_user_id}: {e}")
                    continue

            # Sort by similarity descending
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Take top K
            top_similar = similarities[:top_k]

            logger.info(
                f"Found {len(top_similar)} similar users "
                f"(from {len(all_user_vectors)} candidates, threshold={score_threshold:.2f})"
            )

            return top_similar

        except Exception as e:
            logger.error(f"find_similar_users failed: {e}", exc_info=True)
            return []

    def recommend_from_similar_users(
        self,
        similar_users: List[Tuple[str, float]],
        purchase_history: Dict[str, List[str]],
        top_k: Optional[int] = None,
        exclude_products: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Recommend products based on similar users' purchase history.

        Aggregation Strategy:
        - Each product gets a weighted score = sum of similarities of users who purchased it
        - Products are ranked by aggregated score
        - Scores are normalized to 0-100 scale

        Args:
            similar_users: List of (user_id, similarity_score) from find_similar_users()
            purchase_history: Dict of {user_id: [product_ids]}
            top_k: Number of recommendations (default: self.default_top_k)
            exclude_products: Products to exclude (e.g., already purchased)

        Returns:
            List of (product_id, collaborative_score) tuples, sorted by score descending
            Scores are normalized to 0-100 scale

        Example:
            recommendations = cf.recommend_from_similar_users(
                similar_users=[("USER001", 0.85), ("USER002", 0.70)],
                purchase_history={
                    "USER001": ["PROD001", "PROD002"],
                    "USER002": ["PROD001", "PROD003"]
                },
                top_k=5,
                exclude_products=["PROD001"]
            )
            # Returns: [("PROD002", 85.0), ("PROD003", 70.0)]
        """
        top_k = top_k or self.default_top_k
        exclude_products = set(exclude_products or [])

        try:
            # Validate input
            if not similar_users:
                logger.info("No similar users provided")
                return []

            if not purchase_history:
                logger.info("No purchase history provided")
                return []

            # Aggregate product scores
            product_scores = defaultdict(float)

            for user_id, similarity in similar_users:
                # Get user's purchase history
                purchased_products = purchase_history.get(user_id, [])

                # Add similarity score to each product they purchased
                for product_id in purchased_products:
                    if product_id not in exclude_products:
                        product_scores[product_id] += similarity

            if not product_scores:
                logger.info("No collaborative recommendations found")
                return []

            # Normalize scores to 0-100 scale
            max_score = max(product_scores.values())
            normalized_scores = [
                (product_id, (score / max_score) * 100.0)
                for product_id, score in product_scores.items()
            ]

            # Sort by score descending
            normalized_scores.sort(key=lambda x: x[1], reverse=True)

            # Take top K
            top_recommendations = normalized_scores[:top_k]

            logger.info(
                f"Generated {len(top_recommendations)} collaborative recommendations "
                f"from {len(similar_users)} similar users"
            )

            # Log top 3 for debugging
            for i, (product_id, score) in enumerate(top_recommendations[:3], 1):
                logger.debug(f"  {i}. {product_id}: {score:.1f}")

            return top_recommendations

        except Exception as e:
            logger.error(f"recommend_from_similar_users failed: {e}", exc_info=True)
            return []

    def calculate_product_score_for_user(
        self,
        product_id: str,
        user_vector: List[float],
        all_user_vectors: Dict[str, List[float]],
        purchase_history: Dict[str, List[str]],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> float:
        """
        Calculate collaborative filtering score for a SINGLE product.

        This is the method used by Agent 3 for ranking.

        Workflow:
        1. Find K similar users
        2. Check which of them purchased this product
        3. Sum their similarity scores
        4. Normalize to 0-100 scale

        Args:
            product_id: Product to score
            user_vector: Target user's 512-dim embedding
            all_user_vectors: Dict of {user_id: embedding}
            purchase_history: Dict of {user_id: [product_ids]}
            top_k: Number of similar users to consider
            score_threshold: Minimum similarity score

        Returns:
            Collaborative score 0.0-100.0 (0.0 if no similar users purchased it)

        Example:
            score = cf.calculate_product_score_for_user(
                product_id="PROD005",
                user_vector=[0.1, 0.2, ...],
                all_user_vectors={...},
                purchase_history={...}
            )
            # Returns: 72.5
        """
        try:
            # Validate input
            if not product_id:
                logger.warning("Empty product_id provided")
                return 0.0

            if not user_vector:
                logger.warning("Empty user_vector provided")
                return 0.0

            # Find similar users
            similar_users = self.find_similar_users(
                user_vector=user_vector,
                all_user_vectors=all_user_vectors,
                top_k=top_k,
                score_threshold=score_threshold
            )

            if not similar_users:
                logger.debug(f"No similar users found for product {product_id}")
                return 0.0

            # Calculate aggregated score from users who purchased this product
            aggregated_score = 0.0
            purchaser_count = 0

            for user_id, similarity in similar_users:
                purchased_products = purchase_history.get(user_id, [])
                if product_id in purchased_products:
                    aggregated_score += similarity
                    purchaser_count += 1

            if purchaser_count == 0:
                logger.debug(f"No similar users purchased {product_id}")
                return 0.0

            # Normalize to 0-100 scale
            # Max possible score = sum of all similarity scores
            max_possible = sum(sim for _, sim in similar_users)
            normalized_score = (aggregated_score / max_possible) * 100.0

            logger.debug(
                f"Collaborative score for {product_id}: {normalized_score:.1f} "
                f"({purchaser_count}/{len(similar_users)} similar users purchased it)"
            )

            return round(normalized_score, 2)

        except Exception as e:
            logger.error(f"calculate_product_score_for_user failed: {e}", exc_info=True)
            return 0.0

    def build_user_feature_vector(
        self,
        user_profile: Dict[str, Any],
        embedding_dim: int = 512
    ) -> np.ndarray:
        """
        Construct user feature vector from profile (fallback if no embedding).

        This is a simplified feature engineering approach when embeddings
        are not available. NOT as accurate as learned embeddings, but better than nothing.

        Features:
        - Income (normalized)
        - Credit score (normalized)
        - Savings (normalized)
        - Debt (normalized)
        - Preferred categories (one-hot encoded)
        - Risk tolerance (one-hot encoded)

        Args:
            user_profile: Dict with keys: monthly_income, credit_score, savings,
                          current_debt, preferred_categories, risk_tolerance
            embedding_dim: Target embedding dimension (default: 512)

        Returns:
            512-dimensional numpy array

        Example:
            user_profile = {
                "monthly_income": 5000.0,
                "credit_score": 720,
                "savings": 10000.0,
                "current_debt": 2000.0,
                "preferred_categories": ["Laptops", "Phones"],
                "risk_tolerance": "medium"
            }

            vector = cf.build_user_feature_vector(user_profile)
            # Returns: np.array([0.5, 0.72, ...]) of length 512
        """
        try:
            features = []

            # Numerical features (normalized to 0-1)
            income = user_profile.get("monthly_income", 5000.0)
            features.append(min(income / 20000.0, 1.0))  # Normalize to 0-1 (max $20k)

            credit_score = user_profile.get("credit_score", 650)
            features.append((credit_score - 300) / 550.0)  # 300-850 → 0-1

            savings = user_profile.get("savings", 5000.0)
            features.append(min(savings / 100000.0, 1.0))  # Normalize to 0-1 (max $100k)

            debt = user_profile.get("current_debt", 0.0)
            features.append(min(debt / 50000.0, 1.0))  # Normalize to 0-1 (max $50k)

            # Categorical features (one-hot encoded)
            all_categories = ["Laptops", "Phones", "Tablets", "Headphones", "Monitors"]
            preferred = user_profile.get("preferred_categories", [])
            for category in all_categories:
                features.append(1.0 if category in preferred else 0.0)

            # Risk tolerance (one-hot)
            risk = user_profile.get("risk_tolerance", "medium")
            features.append(1.0 if risk == "low" else 0.0)
            features.append(1.0 if risk == "medium" else 0.0)
            features.append(1.0 if risk == "high" else 0.0)

            # Pad with zeros to reach embedding_dim
            feature_vector = np.array(features)
            if len(feature_vector) < embedding_dim:
                padding = np.zeros(embedding_dim - len(feature_vector))
                feature_vector = np.concatenate([feature_vector, padding])
            elif len(feature_vector) > embedding_dim:
                feature_vector = feature_vector[:embedding_dim]

            # Normalize vector
            norm = np.linalg.norm(feature_vector)
            if norm > 0:
                feature_vector = feature_vector / norm

            logger.debug(f"Built user feature vector: dim={len(feature_vector)}")

            return feature_vector

        except Exception as e:
            logger.error(f"build_user_feature_vector failed: {e}", exc_info=True)
            # Return zero vector on failure
            return np.zeros(embedding_dim)


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

def example_basic_usage():
    """Example: Basic collaborative filtering workflow"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Collaborative Filtering Workflow")
    print("=" * 60)

    cf = CollaborativeFilter()

    # Mock data
    target_user_vector = np.random.randn(512).tolist()

    all_user_vectors = {
        "USER001": np.random.randn(512).tolist(),
        "USER002": np.random.randn(512).tolist(),
        "USER003": np.random.randn(512).tolist(),
    }

    purchase_history = {
        "USER001": ["PROD001", "PROD002", "PROD005"],
        "USER002": ["PROD001", "PROD003"],
        "USER003": ["PROD004", "PROD005"]
    }

    # Step 1: Find similar users
    similar_users = cf.find_similar_users(
        user_vector=target_user_vector,
        all_user_vectors=all_user_vectors,
        top_k=5
    )

    print(f"\nSimilar users: {similar_users}")

    # Step 2: Get recommendations
    recommendations = cf.recommend_from_similar_users(
        similar_users=similar_users,
        purchase_history=purchase_history,
        top_k=5,
        exclude_products=["PROD001"]  # Already purchased
    )

    print(f"Recommendations: {recommendations}")


def example_agent3_usage():
    """Example: How Agent 3 would use this for product ranking"""
    print("\n" + "=" * 60)
    print("Example 2: Agent 3 Product Ranking Use Case")
    print("=" * 60)

    cf = CollaborativeFilter()

    # Mock data
    target_user_vector = np.random.randn(512).tolist()
    all_user_vectors = {"USER001": np.random.randn(512).tolist()}
    purchase_history = {"USER001": ["PROD005"]}

    # Calculate score for a specific product
    product_id = "PROD005"
    score = cf.calculate_product_score_for_user(
        product_id=product_id,
        user_vector=target_user_vector,
        all_user_vectors=all_user_vectors,
        purchase_history=purchase_history
    )

    print(f"\nCollaborative score for {product_id}: {score:.2f}/100")

    # Agent 3 will use this score in composite ranking:
    collaborative_weight = 0.2  # 20% of final score
    final_score_contribution = score * collaborative_weight
    print(f"Contribution to final score: {final_score_contribution:.2f} (weight=0.2)")


def example_feature_vector_fallback():
    """Example: Building feature vector when embedding not available"""
    print("\n" + "=" * 60)
    print("Example 3: Feature Vector Fallback (No Embedding)")
    print("=" * 60)

    cf = CollaborativeFilter()

    user_profile = {
        "monthly_income": 5000.0,
        "credit_score": 720,
        "savings": 10000.0,
        "current_debt": 2000.0,
        "preferred_categories": ["Laptops", "Phones"],
        "risk_tolerance": "medium"
    }

    feature_vector = cf.build_user_feature_vector(user_profile)

    print(f"\nFeature vector shape: {feature_vector.shape}")
    print(f"Feature vector norm: {np.linalg.norm(feature_vector):.4f}")
    print(f"First 10 features: {feature_vector[:10]}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    # Run examples
    print("\n" + "=" * 60)
    print("Collaborative Filtering Module - Standalone Tests")
    print("=" * 60)

    example_basic_usage()
    example_agent3_usage()
    example_feature_vector_fallback()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
