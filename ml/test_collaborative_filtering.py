"""
Unit tests for CollaborativeFilter

Run with: pytest ml/test_collaborative_filtering.py -v
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path so we can import from ml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.collaborative_filtering import CollaborativeFilter


class TestCollaborativeFilter:
    """Test collaborative filtering module"""

    def test_initialization(self):
        """Test filter initializes correctly"""
        cf = CollaborativeFilter(default_top_k=5, default_threshold=0.7)
        assert cf.default_top_k == 5
        assert cf.default_threshold == 0.7

        # Test default initialization
        cf_default = CollaborativeFilter()
        assert cf_default.default_top_k == 10
        assert cf_default.default_threshold == 0.6

    def test_find_similar_users(self):
        """Test finding similar users"""
        cf = CollaborativeFilter()

        # Create test vectors (orthogonal and parallel)
        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER_SIMILAR": [0.9, 0.1, 0.0],    # High similarity
            "USER_MEDIUM": [0.5, 0.5, 0.0],     # Medium similarity
            "USER_DIFFERENT": [0.0, 1.0, 0.0]   # Low similarity
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=2,
            score_threshold=0.5
        )

        # Should return 2 users, sorted by similarity
        assert len(similar_users) == 2
        assert similar_users[0][0] == "USER_SIMILAR"  # Highest similarity first
        assert similar_users[0][1] > similar_users[1][1]  # Descending order
        assert 0.0 <= similar_users[0][1] <= 1.0  # Valid similarity range

    def test_find_similar_users_with_threshold(self):
        """Test threshold filtering in find_similar_users"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER_HIGH": [0.95, 0.05, 0.0],      # ~0.95 similarity
            "USER_LOW": [0.1, 0.9, 0.0]          # Low similarity
        }

        # High threshold should filter out USER_LOW
        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=10,
            score_threshold=0.8
        )

        assert len(similar_users) == 1
        assert similar_users[0][0] == "USER_HIGH"

    def test_recommend_from_similar_users(self):
        """Test product recommendations from similar users"""
        cf = CollaborativeFilter()

        similar_users = [
            ("USER001", 0.85),
            ("USER002", 0.70)
        ]

        purchase_history = {
            "USER001": ["PROD001", "PROD002"],
            "USER002": ["PROD001", "PROD003"]
        }

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5
        )

        # PROD001 should rank highest (purchased by both users)
        assert len(recommendations) > 0
        assert recommendations[0][0] == "PROD001"

        # Scores should be in 0-100 range
        for product_id, score in recommendations:
            assert 0.0 <= score <= 100.0

        # Verify descending order
        scores = [score for _, score in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_calculate_product_score_for_user(self):
        """Test single product scoring"""
        cf = CollaborativeFilter()

        # Create similar vectors for high similarity
        user_vector = np.random.randn(512)
        similar_vector = user_vector + np.random.randn(512) * 0.1  # Very similar

        all_user_vectors = {
            "USER001": similar_vector.tolist()
        }
        purchase_history = {
            "USER001": ["PROD005"]
        }

        # Score for product purchased by similar user
        score = cf.calculate_product_score_for_user(
            product_id="PROD005",
            user_vector=user_vector.tolist(),
            all_user_vectors=all_user_vectors,
            purchase_history=purchase_history
        )

        assert 0.0 <= score <= 100.0
        assert score > 0.0  # Should be non-zero

        # Score for product NOT purchased
        score_not_purchased = cf.calculate_product_score_for_user(
            product_id="PROD999",
            user_vector=user_vector.tolist(),
            all_user_vectors=all_user_vectors,
            purchase_history=purchase_history
        )

        assert score_not_purchased == 0.0

    def test_build_user_feature_vector(self):
        """Test feature vector construction"""
        cf = CollaborativeFilter()

        user_profile = {
            "monthly_income": 5000.0,
            "credit_score": 720,
            "savings": 10000.0,
            "current_debt": 2000.0,
            "preferred_categories": ["Laptops"],
            "risk_tolerance": "medium"
        }

        vector = cf.build_user_feature_vector(user_profile)

        # Check dimension
        assert len(vector) == 512

        # Check normalization (should be unit vector)
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01  # Should be close to 1.0

        # Check that it's not all zeros
        assert np.any(vector != 0)

    def test_empty_purchase_history(self):
        """Test with no purchase history"""
        cf = CollaborativeFilter()

        similar_users = [("USER001", 0.85)]
        purchase_history = {}  # Empty

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5
        )

        assert len(recommendations) == 0

    def test_product_exclusion(self):
        """Test excluding already purchased products"""
        cf = CollaborativeFilter()

        similar_users = [("USER001", 0.85)]
        purchase_history = {"USER001": ["PROD001", "PROD002"]}

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5,
            exclude_products=["PROD001"]
        )

        # PROD001 should not appear
        product_ids = [prod_id for prod_id, _ in recommendations]
        assert "PROD001" not in product_ids
        assert "PROD002" in product_ids

    def test_empty_user_vectors(self):
        """Test edge case with empty user vectors"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {}  # Empty

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=5
        )

        assert len(similar_users) == 0

    def test_dimension_mismatch(self):
        """Test handling of dimension mismatch"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]  # 3D
        all_user_vectors = {
            "USER001": [1.0, 0.0, 0.0],      # 3D - OK
            "USER002": [1.0, 0.0, 0.0, 0.0]  # 4D - mismatch
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=5
        )

        # Should only return USER001 (matching dimension)
        assert len(similar_users) == 1
        assert similar_users[0][0] == "USER001"

    def test_score_aggregation_weights(self):
        """Test that scores are properly weighted by similarity"""
        cf = CollaborativeFilter()

        similar_users = [
            ("USER001", 0.9),   # High similarity
            ("USER002", 0.3)    # Low similarity
        ]

        purchase_history = {
            "USER001": ["PROD001"],
            "USER002": ["PROD002"]
        }

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5
        )

        # PROD001 should score higher (purchased by more similar user)
        prod001_score = next(score for pid, score in recommendations if pid == "PROD001")
        prod002_score = next(score for pid, score in recommendations if pid == "PROD002")

        assert prod001_score > prod002_score

    def test_single_user_scenario(self):
        """Test with only one user in the system"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER001": [0.9, 0.1, 0.0]
        }
        purchase_history = {
            "USER001": ["PROD001", "PROD002"]
        }

        score = cf.calculate_product_score_for_user(
            product_id="PROD001",
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            purchase_history=purchase_history
        )

        # Should work with single user
        assert 0.0 <= score <= 100.0
        assert score > 0.0

    def test_top_k_limiting(self):
        """Test that top_k correctly limits results"""
        cf = CollaborativeFilter()

        similar_users = [
            ("USER001", 0.9),
            ("USER002", 0.8),
            ("USER003", 0.7)
        ]

        purchase_history = {
            "USER001": ["PROD001"],
            "USER002": ["PROD002"],
            "USER003": ["PROD003"]
        }

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=2  # Limit to 2
        )

        assert len(recommendations) == 2

    def test_feature_vector_missing_fields(self):
        """Test feature vector with missing profile fields"""
        cf = CollaborativeFilter()

        # Minimal profile with missing fields
        user_profile = {
            "monthly_income": 3000.0
        }

        vector = cf.build_user_feature_vector(user_profile)

        # Should still work with defaults
        assert len(vector) == 512
        assert np.linalg.norm(vector) > 0

    def test_zero_vector_handling(self):
        """Test handling of zero vectors"""
        cf = CollaborativeFilter()

        user_vector = [0.0, 0.0, 0.0]  # Zero vector
        all_user_vectors = {
            "USER001": [1.0, 0.0, 0.0]
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=5
        )

        # Should handle gracefully (may return empty or skip zero vectors)
        assert isinstance(similar_users, list)


# Run with: pytest test_collaborative_filtering.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
