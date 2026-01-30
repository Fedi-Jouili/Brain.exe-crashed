"""
Unit tests for CollaborativeFilter

Run with: pytest test_collaborative_filtering.py -v

Tests cover:
- Initialization
- Finding similar users
- Product recommendations
- Single product scoring
- Feature vector construction
- Edge cases (empty data, exclusions)
"""

import pytest
import numpy as np
from collaborative_filtering import CollaborativeFilter


class TestCollaborativeFilter:
    """Test suite for collaborative filtering module"""

    def test_initialization(self):
        """Test filter initializes with correct defaults"""
        cf = CollaborativeFilter(default_top_k=5, default_threshold=0.7)

        assert cf.default_top_k == 5, "Should set custom top_k"
        assert cf.default_threshold == 0.7, "Should set custom threshold"

        # Test default initialization
        cf_default = CollaborativeFilter()
        assert cf_default.default_top_k == 10, "Should have default top_k=10"
        assert cf_default.default_threshold == 0.6, "Should have default threshold=0.6"

    def test_find_similar_users(self):
        """Test finding similar users with cosine similarity"""
        cf = CollaborativeFilter()

        # Create test vectors: one very similar, one medium, one orthogonal
        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER_SIMILAR": [0.9, 0.1, 0.0],      # High similarity (~0.99)
            "USER_MEDIUM": [0.7, 0.7, 0.0],       # Medium similarity (~0.70)
            "USER_ORTHOGONAL": [0.0, 1.0, 0.0]   # Low similarity (~0.0)
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=3,
            score_threshold=0.5
        )

        # Should return 2 users (orthogonal filtered out)
        assert len(similar_users) == 2, "Should filter out low similarity users"

        # Should be sorted by similarity descending
        assert similar_users[0][0] == "USER_SIMILAR", "Most similar user should be first"
        assert similar_users[0][1] > similar_users[1][1], "Should be sorted descending"

        # Similarity scores should be in 0-1 range
        for user_id, similarity in similar_users:
            assert 0.0 <= similarity <= 1.0, f"Similarity {similarity} out of range"

    def test_find_similar_users_with_threshold(self):
        """Test threshold filtering"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER1": [0.95, 0.05, 0.0],  # ~0.99 similarity
            "USER2": [0.5, 0.5, 0.0]     # ~0.70 similarity
        }

        # High threshold should filter out USER2
        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=10,
            score_threshold=0.9
        )

        assert len(similar_users) == 1, "High threshold should filter users"
        assert similar_users[0][0] == "USER1", "Only highly similar user should pass"

    def test_recommend_from_similar_users(self):
        """Test product recommendations from similar users"""
        cf = CollaborativeFilter()

        # Two similar users with overlapping purchases
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

        # Should have 3 products
        assert len(recommendations) == 3, "Should recommend all unique products"

        # PROD001 should rank highest (purchased by both users)
        assert recommendations[0][0] == "PROD001", "Most popular product should rank first"

        # Scores should be in 0-100 range
        for product_id, score in recommendations:
            assert 0.0 <= score <= 100.0, f"Score {score} out of 0-100 range"

        # Top score should be 100 (normalized)
        assert recommendations[0][1] == 100.0, "Top recommendation should have score 100"

    def test_recommend_with_exclusions(self):
        """Test excluding already purchased products"""
        cf = CollaborativeFilter()

        similar_users = [("USER001", 0.85)]
        purchase_history = {"USER001": ["PROD001", "PROD002", "PROD003"]}

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5,
            exclude_products=["PROD001", "PROD002"]
        )

        # Should only recommend PROD003
        assert len(recommendations) == 1, "Should exclude specified products"
        assert recommendations[0][0] == "PROD003", "Only non-excluded product"

        # Verify excluded products not in results
        product_ids = [prod_id for prod_id, _ in recommendations]
        assert "PROD001" not in product_ids, "PROD001 should be excluded"
        assert "PROD002" not in product_ids, "PROD002 should be excluded"

    def test_calculate_product_score_for_user(self):
        """Test single product scoring"""
        cf = CollaborativeFilter()

        # Create similar user vector
        np.random.seed(42)
        user_vector = np.random.randn(512).tolist()
        similar_user_vector = (np.array(user_vector) + np.random.randn(512) * 0.05).tolist()

        all_user_vectors = {
            "USER001": similar_user_vector
        }

        purchase_history = {
            "USER001": ["PROD005", "PROD010"]
        }

        # Score for product purchased by similar user
        score_purchased = cf.calculate_product_score_for_user(
            product_id="PROD005",
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            purchase_history=purchase_history
        )

        assert 0.0 <= score_purchased <= 100.0, "Score should be in 0-100 range"
        assert score_purchased > 0.0, "Should be non-zero for purchased product"

        # Score for product NOT purchased
        score_not_purchased = cf.calculate_product_score_for_user(
            product_id="PROD999",
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            purchase_history=purchase_history
        )

        assert score_not_purchased == 0.0, "Should be 0.0 for non-purchased product"

        print(f"\n✅ Purchased product score: {score_purchased:.2f}/100")
        print(f"✅ Non-purchased product score: {score_not_purchased:.2f}/100")

    def test_build_user_feature_vector(self):
        """Test feature vector construction from user profile"""
        cf = CollaborativeFilter()

        user_profile = {
            "monthly_income": 5000.0,
            "credit_score": 720,
            "savings": 10000.0,
            "current_debt": 2000.0,
            "preferred_categories": ["Laptops", "Phones"],
            "risk_tolerance": "medium"
        }

        vector = cf.build_user_feature_vector(user_profile)

        # Check dimension
        assert len(vector) == 512, "Should be 512-dimensional"
        assert vector.shape == (512,), "Should be numpy array with shape (512,)"

        # Check normalization (unit vector)
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01, f"Should be unit vector, got norm={norm:.4f}"

        # Check some features are non-zero
        non_zero_count = np.count_nonzero(vector)
        assert non_zero_count > 0, "Should have non-zero features"

        print(f"\n✅ Feature vector: dim={vector.shape}, norm={norm:.4f}, "
              f"non-zero={non_zero_count}")

    def test_empty_purchase_history(self):
        """Test with no purchase history"""
        cf = CollaborativeFilter()

        similar_users = [("USER001", 0.85), ("USER002", 0.70)]
        purchase_history = {}  # Empty

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5
        )

        assert len(recommendations) == 0, "Should return empty list with no history"
        print("\n✅ Empty purchase history handled gracefully")

    def test_no_similar_users(self):
        """Test when no similar users found"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER001": [0.0, 1.0, 0.0]  # Orthogonal (similarity ~0)
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=10,
            score_threshold=0.8  # High threshold
        )

        assert len(similar_users) == 0, "Should find no similar users"

        # Test product scoring with no similar users
        score = cf.calculate_product_score_for_user(
            product_id="PROD005",
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            purchase_history={"USER001": ["PROD005"]},
            score_threshold=0.8
        )

        assert score == 0.0, "Should return 0.0 with no similar users"
        print("\n✅ No similar users scenario handled gracefully")

    def test_dimension_mismatch(self):
        """Test handling of dimension mismatch"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]  # 3-dim
        all_user_vectors = {
            "USER001": [0.9, 0.1, 0.0],      # 3-dim (matches)
            "USER002": [0.5, 0.5, 0.0, 0.0]  # 4-dim (mismatch)
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=10
        )

        # Should only return USER001 (matching dimension)
        assert len(similar_users) == 1, "Should skip mismatched dimensions"
        assert similar_users[0][0] == "USER001", "Should only include matching dimension"

        print("\n✅ Dimension mismatch handled gracefully")

    def test_feature_vector_with_missing_fields(self):
        """Test feature vector construction with missing profile fields"""
        cf = CollaborativeFilter()

        # Minimal profile (missing some fields)
        minimal_profile = {
            "monthly_income": 5000.0,
            "credit_score": 700
            # Missing: savings, debt, categories, risk_tolerance
        }

        vector = cf.build_user_feature_vector(minimal_profile)

        # Should still return valid vector
        assert len(vector) == 512, "Should handle missing fields"
        assert abs(np.linalg.norm(vector) - 1.0) < 0.01, "Should still be normalized"

        print("\n✅ Missing profile fields handled gracefully")

    def test_score_normalization(self):
        """Test that scores are properly normalized to 0-100"""
        cf = CollaborativeFilter()

        # Three similar users with different similarities
        similar_users = [
            ("USER001", 0.90),
            ("USER002", 0.70),
            ("USER003", 0.50)
        ]

        purchase_history = {
            "USER001": ["PROD001"],
            "USER002": ["PROD002"],
            "USER003": ["PROD003"]
        }

        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=5
        )

        # Top score should be 100
        assert recommendations[0][1] == 100.0, "Top score should be 100"

        # Scores should be proportional to similarity
        # PROD001 (0.90 sim) > PROD002 (0.70 sim) > PROD003 (0.50 sim)
        assert recommendations[0][1] > recommendations[1][1] > recommendations[2][1], \
            "Scores should decrease proportionally"

        print("\n✅ Score normalization:")
        for product_id, score in recommendations:
            print(f"   {product_id}: {score:.1f}/100")


class TestCollaborativeFilterEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_user_vector(self):
        """Test with empty user vector"""
        cf = CollaborativeFilter()

        similar_users = cf.find_similar_users(
            user_vector=[],
            all_user_vectors={"USER001": [1.0, 0.0]},
            top_k=5
        )

        assert similar_users == [], "Should return empty list for empty vector"

    def test_zero_vectors(self):
        """Test with zero vectors"""
        cf = CollaborativeFilter()

        user_vector = [0.0, 0.0, 0.0]
        all_user_vectors = {
            "USER001": [0.0, 0.0, 0.0],
            "USER002": [1.0, 0.0, 0.0]
        }

        # Should handle zero vectors gracefully
        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=5
        )

        # Zero vectors should be skipped
        assert len(similar_users) == 0, "Should skip zero vectors"

    def test_single_user_scenario(self):
        """Test with only one user"""
        cf = CollaborativeFilter()

        user_vector = [1.0, 0.0, 0.0]
        all_user_vectors = {
            "USER001": [0.9, 0.1, 0.0]
        }

        similar_users = cf.find_similar_users(
            user_vector=user_vector,
            all_user_vectors=all_user_vectors,
            top_k=10
        )

        assert len(similar_users) == 1, "Should work with single user"
        assert similar_users[0][0] == "USER001"


class TestCollaborativeFilterIntegration:
    """Integration tests simulating real-world usage"""

    def test_full_workflow(self):
        """Test complete collaborative filtering workflow"""
        cf = CollaborativeFilter(default_top_k=5, default_threshold=0.6)

        # Create realistic scenario: 5 users, some purchases
        np.random.seed(42)
        target_user = np.random.randn(512).tolist()

        all_user_vectors = {
            f"USER{i:03d}": (
                np.array(target_user) + np.random.randn(512) * (0.1 * i)
            ).tolist()
            for i in range(1, 6)
        }

        purchase_history = {
            "USER001": ["PROD001", "PROD002", "PROD005"],
            "USER002": ["PROD001", "PROD003", "PROD005"],
            "USER003": ["PROD004"],
            "USER004": ["PROD002", "PROD006"],
            "USER005": ["PROD007"]
        }

        # Step 1: Find similar users
        similar_users = cf.find_similar_users(
            user_vector=target_user,
            all_user_vectors=all_user_vectors,
            top_k=3
        )

        assert len(similar_users) > 0, "Should find similar users"

        # Step 2: Get recommendations
        recommendations = cf.recommend_from_similar_users(
            similar_users=similar_users,
            purchase_history=purchase_history,
            top_k=10,
            exclude_products=["PROD001"]  # Already purchased
        )

        assert len(recommendations) > 0, "Should generate recommendations"
        assert "PROD001" not in [p for p, _ in recommendations], \
            "Should exclude specified products"

        # Step 3: Score specific product
        score = cf.calculate_product_score_for_user(
            product_id="PROD005",
            user_vector=target_user,
            all_user_vectors=all_user_vectors,
            purchase_history=purchase_history
        )

        assert 0.0 <= score <= 100.0, "Score should be in valid range"

        print("\n✅ Full workflow completed successfully")
        print(f"   Similar users found: {len(similar_users)}")
        print(f"   Recommendations: {len(recommendations)}")
        print(f"   Sample score: {score:.2f}/100")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
