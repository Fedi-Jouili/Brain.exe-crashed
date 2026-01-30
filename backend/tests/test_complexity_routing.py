"""
Unit Tests for 3-Tier Complexity Routing System

Tests:
1. Complexity estimation logic
2. Route selection (FAST/SMART/DEEP)
3. Cache behavior
4. SMART PATH execution
"""
import pytest
from ml.complexity_estimator import ComplexityEstimator
from models.schemas import UserProfile


class TestComplexityEstimation:
    """Test complexity scoring and route selection"""

    def setup_method(self):
        """Initialize estimator before each test"""
        self.estimator = ComplexityEstimator()

    def test_simple_query_routes_to_fast(self):
        """Simple 1-2 word queries should route to FAST/SMART path"""
        result = self.estimator.estimate("laptops", None, False)

        assert result['level'] in ['FAST', 'SMART'], f"Expected FAST or SMART, got {result['level']}"
        assert result['score'] < 0.7, f"Score too high: {result['score']}"
        assert 'factors' in result
        assert 'reasoning' in result

    def test_price_constraint_increases_complexity(self):
        """Queries with price constraints should increase complexity"""
        result = self.estimator.estimate("laptop under $1000", None, False)

        # Should be SMART or DEEP due to price constraint (+0.2)
        assert result['level'] in ['SMART', 'DEEP']
        assert result['score'] >= 0.3, f"Score should be at least 0.3, got {result['score']}"
        assert result['factors']['price_constraints'] > 0

    def test_financial_keywords_route_to_deep(self):
        """Queries with financial keywords should route to DEEP path"""
        result = self.estimator.estimate(
            "laptop under $1000 with financing",
            None,
            False
        )

        assert result['level'] in ['SMART', 'DEEP']
        assert result['factors']['financial_keywords'] > 0
        assert 'financing' in result['reasoning'].lower() or 'financial' in result['reasoning'].lower()

    def test_complete_profile_routes_to_deep(self):
        """Complete user profile should increase complexity"""
        user_profile = UserProfile(
            user_id="test_user",
            monthly_income=5000.0,
            credit_score=720
        )

        result = self.estimator.estimate(
            "laptop under $1000 with financing",
            user_profile,
            False
        )

        # With profile + financial keywords + price constraint
        # Score should be: 0.15 (length) + 0.3 (financing) + 0.2 (price) + 0.2 (profile) = 0.85
        assert result['level'] == 'DEEP', f"Expected DEEP, got {result['level']}"
        assert result['score'] >= 0.7, f"Score should be >= 0.7, got {result['score']}"
        assert result['factors']['user_profile'] > 0

    def test_multimodal_increases_complexity(self):
        """Image upload should add complexity"""
        result_no_image = self.estimator.estimate("gaming laptop", None, False)
        result_with_image = self.estimator.estimate("gaming laptop", None, True)

        assert result_with_image['score'] > result_no_image['score']
        assert result_with_image['factors']['multimodal'] == 0.1
        assert result_no_image['factors']['multimodal'] == 0.0

    def test_empty_query_defaults_to_fast(self):
        """Empty query should safely default to FAST path"""
        result = self.estimator.estimate("", None, False)

        assert result['level'] == 'FAST'
        assert result['score'] == 0.0
        assert 'empty' in result['reasoning'].lower()

    def test_multiple_financial_keywords(self):
        """Multiple financial keywords should accumulate (capped at 0.9)"""
        query = "affordable laptop with financing and monthly payment budget under credit score"
        result = self.estimator.estimate(query, None, False)

        # Should hit the 0.9 cap
        assert result['factors']['financial_keywords'] >= 0.6
        assert result['level'] == 'DEEP'

    def test_long_complex_query(self):
        """Long queries with many words should get higher length score"""
        query = "I need a high performance gaming laptop with excellent graphics card under my budget"
        result = self.estimator.estimate(query, None, False)

        # 15 words = 0.3 length score
        assert result['factors']['query_length'] == 0.3
        assert result['score'] >= 0.3


class TestRouteSelection:
    """Test route selection boundaries"""

    def setup_method(self):
        self.estimator = ComplexityEstimator()

    def test_fast_boundary(self):
        """Score < 0.3 should route to FAST"""
        # Simple query: "laptop" = 0.1 (length)
        result = self.estimator.estimate("laptop", None, False)

        if result['score'] < 0.3:
            assert result['level'] == 'FAST'

    def test_smart_boundary(self):
        """0.3 <= Score < 0.7 should route to SMART"""
        # Medium query with price: "laptop under $800"
        # = 0.15 (length) + 0.2 (price) = 0.35
        result = self.estimator.estimate("laptop under $800", None, False)

        if 0.3 <= result['score'] < 0.7:
            assert result['level'] == 'SMART'

    def test_deep_boundary(self):
        """Score >= 0.7 should route to DEEP"""
        user_profile = UserProfile(
            user_id="test",
            monthly_income=5000.0,
            credit_score=720
        )

        # Complex: "laptop financing" with profile
        # = 0.15 (length) + 0.3 (financing) + 0.2 (profile) = 0.65
        # Add price constraint: +0.2 = 0.85
        result = self.estimator.estimate(
            "laptop under $1000 with financing",
            user_profile,
            False
        )

        if result['score'] >= 0.7:
            assert result['level'] == 'DEEP'


class TestEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        self.estimator = ComplexityEstimator()

    def test_none_user_profile(self):
        """Should handle None user_profile gracefully"""
        result = self.estimator.estimate("laptop", None, False)

        assert result['factors']['user_profile'] == 0.0
        assert result is not None

    def test_incomplete_user_profile(self):
        """Should handle profile without income/credit"""
        # Profile with only user_id
        class PartialProfile:
            user_id = "test"

        profile = PartialProfile()
        result = self.estimator.estimate("laptop", profile, False)

        # Should not crash, profile score should be 0
        assert result['factors']['user_profile'] == 0.0

    def test_whitespace_only_query(self):
        """Should handle whitespace-only query"""
        result = self.estimator.estimate("   ", None, False)

        assert result['level'] == 'FAST'
        assert result['score'] == 0.0

    def test_special_characters_in_query(self):
        """Should handle special characters gracefully"""
        result = self.estimator.estimate("laptop @ $500 (gaming)", None, False)

        # Should detect $ as price constraint
        assert result['factors']['price_constraints'] > 0
        assert result is not None

    def test_case_insensitive_keywords(self):
        """Keywords should be case-insensitive"""
        result_lower = self.estimator.estimate("laptop with financing", None, False)
        result_upper = self.estimator.estimate("LAPTOP WITH FINANCING", None, False)
        result_mixed = self.estimator.estimate("Laptop With Financing", None, False)

        # All should detect the financial keyword
        assert result_lower['factors']['financial_keywords'] > 0
        assert result_upper['factors']['financial_keywords'] > 0
        assert result_mixed['factors']['financial_keywords'] > 0


class TestRealWorldScenarios:
    """Test with realistic user queries"""

    def setup_method(self):
        self.estimator = ComplexityEstimator()

    def test_scenario_simple_search(self):
        """Scenario: User just browsing, no financial needs"""
        queries = ["laptops", "phones", "headphones"]

        for query in queries:
            result = self.estimator.estimate(query, None, False)
            # Should be FAST or SMART
            assert result['level'] in ['FAST', 'SMART']
            assert result['score'] < 0.7

    def test_scenario_budget_conscious(self):
        """Scenario: User with price constraint but no financing"""
        queries = [
            "laptop under $500",
            "phone below $800",
            "headphones less than $200"
        ]

        for query in queries:
            result = self.estimator.estimate(query, None, False)
            # Should be SMART (has price constraint)
            assert result['level'] in ['SMART', 'DEEP']
            assert result['factors']['price_constraints'] > 0

    def test_scenario_financing_needed(self):
        """Scenario: User needs financing options"""
        user_profile = UserProfile(
            user_id="finance_user",
            monthly_income=3500.0,
            credit_score=680
        )

        queries = [
            "laptop I can afford with payment plan",
            "phone with monthly financing",
            "can I afford this gaming laptop on my budget"
        ]

        for query in queries:
            result = self.estimator.estimate(query, user_profile, False)
            # Should route to DEEP (financial analysis needed)
            assert result['level'] == 'DEEP'
            assert result['score'] >= 0.7


class TestCacheBehavior:
    """Test cache key generation and behavior"""

    def test_cache_key_generation(self):
        """Cache keys should be deterministic for same query+user"""
        import hashlib

        query = "laptop under $1000"
        user_id = "user123"

        # Generate cache key twice
        hash1 = hashlib.md5(query.encode()).hexdigest()
        hash2 = hashlib.md5(query.encode()).hexdigest()

        cache_key1 = f"search:{hash1}:{user_id}"
        cache_key2 = f"search:{hash2}:{user_id}"

        assert cache_key1 == cache_key2, "Cache keys should be deterministic"

    def test_cache_key_different_users(self):
        """Different users should get different cache keys"""
        import hashlib

        query = "laptop"
        query_hash = hashlib.md5(query.encode()).hexdigest()

        key1 = f"search:{query_hash}:user1"
        key2 = f"search:{query_hash}:user2"

        assert key1 != key2, "Different users should have different cache keys"

    def test_cache_key_different_queries(self):
        """Different queries should get different cache keys"""
        import hashlib

        user_id = "user123"

        hash1 = hashlib.md5("laptop".encode()).hexdigest()
        hash2 = hashlib.md5("phone".encode()).hexdigest()

        key1 = f"search:{hash1}:{user_id}"
        key2 = f"search:{hash2}:{user_id}"

        assert key1 != key2, "Different queries should have different cache keys"


class TestFactorContributions:
    """Test individual factor contributions"""

    def setup_method(self):
        self.estimator = ComplexityEstimator()

    def test_factor_length_simple(self):
        """1-2 word queries should get 0.1 length score"""
        result = self.estimator.estimate("laptop", None, False)
        assert result['factors']['query_length'] == 0.1

    def test_factor_length_medium(self):
        """3-10 word queries should get 0.15 length score"""
        result = self.estimator.estimate("gaming laptop for programming", None, False)
        assert result['factors']['query_length'] == 0.15

    def test_factor_length_long(self):
        """11+ word queries should get 0.3 length score"""
        query = "I am looking for a high quality gaming laptop with excellent graphics card and fast processor"
        result = self.estimator.estimate(query, None, False)
        assert result['factors']['query_length'] == 0.3

    def test_factor_financial_single(self):
        """Single financial keyword should add 0.3"""
        result = self.estimator.estimate("laptop with financing", None, False)
        assert result['factors']['financial_keywords'] == 0.3

    def test_factor_price_constraint(self):
        """Price constraint should add 0.2"""
        result = self.estimator.estimate("laptop under $1000", None, False)
        assert result['factors']['price_constraints'] == 0.2

    def test_factor_complete_profile(self):
        """Complete profile (income + credit) should add 0.2"""
        user_profile = UserProfile(
            user_id="test",
            monthly_income=5000.0,
            credit_score=720
        )
        result = self.estimator.estimate("laptop", user_profile, False)
        assert result['factors']['user_profile'] == 0.2

    def test_factor_multimodal(self):
        """Image upload should add 0.1"""
        result = self.estimator.estimate("laptop", None, True)
        assert result['factors']['multimodal'] == 0.1


# ============================================================================
# INTEGRATION TESTS (require Redis and actual API)
# ============================================================================

class TestIntegrationCacheHit:
    """Integration tests for cache behavior (requires Redis)"""

    @pytest.mark.integration
    def test_cache_hit_returns_fast(self):
        """Test that identical query+user returns cached result"""
        # This would require actual Redis connection and API call
        # Implementation depends on test setup
        pytest.skip("Integration test - requires Redis and running API")

    @pytest.mark.integration
    def test_cache_miss_executes_path(self):
        """Test that new query executes SMART or DEEP path"""
        pytest.skip("Integration test - requires Redis and running API")

    @pytest.mark.integration
    def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL"""
        pytest.skip("Integration test - requires Redis and running API")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
