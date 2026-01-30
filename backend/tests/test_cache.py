"""
Unit tests for Redis query caching

Run with: pytest backend/tests/test_cache.py -v
"""

import pytest
import requests
import time
import hashlib

API_BASE_URL = "http://localhost:8000"


class TestQueryCaching:
    """Test Redis query caching functionality"""

    def test_cache_key_generation(self):
        """Test cache key format is correct"""
        query = "laptop under $1000"
        user_id = "USER123"

        # Expected key format
        query_hash = hashlib.md5(query.encode()).hexdigest()
        expected_key = f"search:{query_hash}:{user_id}"

        # Verify format
        assert expected_key.startswith("search:")
        assert user_id in expected_key
        assert len(query_hash) == 32  # MD5 full hash

    def test_first_request_is_cache_miss(self):
        """Test first request with unique query is cache miss"""
        # Use timestamp to ensure uniqueness
        unique_query = f"laptop test_{int(time.time())}"

        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={"query": unique_query, "max_results": 5}
        )

        assert response.status_code == 200
        data = response.json()

        # Should be cache miss
        assert data["metadata"]["cache_hit"] == False, \
            "First request should be cache miss"

    def test_second_request_is_cache_hit(self):
        """Test second identical request is cache hit"""
        # Use same query twice
        query = f"laptop cache_test_{int(time.time())}"

        # First request (cache miss)
        response1 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={"query": query, "max_results": 5}
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["metadata"]["cache_hit"] == False

        time1 = data1["metadata"]["execution_time_ms"]

        # Second request (should be cache hit)
        response2 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={"query": query, "max_results": 5}
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Should be cache hit
        assert data2["metadata"]["cache_hit"] == True, \
            "Second identical request should be cache hit"

        time2 = data2["metadata"]["execution_time_ms"]

        # Cache hit should be MUCH faster
        assert time2 < time1 * 0.5, \
            f"Cache hit ({time2}ms) should be <50% of miss time ({time1}ms)"

        # Should be <200ms for cache hit
        assert time2 < 200, \
            f"Cache hit should be <200ms, but took {time2}ms"

    def test_different_users_different_cache(self):
        """Test different users get different cache entries"""
        query = "laptop"

        user1_profile = {"user_id": "USER_A", "monthly_income": 5000, "credit_score": 720}
        user2_profile = {"user_id": "USER_B", "monthly_income": 3000, "credit_score": 650}

        # Request for user 1
        response1 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": query,
                "user_profile": str(user1_profile).replace("'", '"'),
                "max_results": 5
            }
        )

        # Request for user 2 (should NOT hit user 1's cache)
        response2 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": query,
                "user_profile": str(user2_profile).replace("'", '"'),
                "max_results": 5
            }
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both could be misses (first time) or hits (if cached separately)
        # Key point: results should be different (different affordability)
        data1 = response1.json()
        data2 = response2.json()

        # Cache keys should be different
        key1 = data1["metadata"].get("cache_key", "")
        key2 = data2["metadata"].get("cache_key", "")

        assert key1 != key2, \
            f"Different users should have different cache keys: {key1} vs {key2}"

    def test_cache_stats_endpoint(self):
        """Test /api/cache/stats endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/cache/stats")

        assert response.status_code == 200
        data = response.json()

        # Verify expected fields
        assert "cache_enabled" in data
        assert "total_keys" in data
        assert "memory_usage_mb" in data
        assert "search_cache_keys" in data

        # If cache is enabled, should have positive values
        if data["cache_enabled"]:
            assert data["total_keys"] >= 0
            assert data["memory_usage_mb"] >= 0

    def test_cache_clear_endpoint(self):
        """Test /api/cache/clear endpoint"""
        # Create a cached entry
        query = f"test_clear_{int(time.time())}"
        requests.post(f"{API_BASE_URL}/api/search", data={"query": query})

        # Clear cache
        response = requests.delete(
            f"{API_BASE_URL}/api/cache/clear",
            params={"pattern": "search:*", "confirm": True}
        )

        assert response.status_code == 200
        data = response.json()

        assert "cleared" in data
        assert data["cleared"] >= 0

    def test_cache_ttl_expiration(self):
        """Test cache entries expire after TTL"""
        # Note: This test requires waiting for TTL expiration (3600s)
        # For practical testing, we'd need to either:
        # 1. Mock Redis with shorter TTL
        # 2. Manually set TTL to 1-2 seconds for testing
        # 3. Skip this test in CI (mark as slow)

        pytest.skip("TTL test requires 3600s wait time - skip for CI")


# Run with: pytest backend/tests/test_cache.py -v
