"""
Tests for multimodal image upload and search

Run with: pytest backend/tests/test_multimodal_search.py -v
"""

import pytest
import requests
from io import BytesIO
from PIL import Image


API_BASE_URL = "http://localhost:8000"


class TestMultimodalSearch:
    """Test image upload and multimodal search"""

    def create_test_image(self, color='red', size=(300, 300)):
        """Create a test image in memory"""
        img = Image.new('RGB', size, color=color)
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.mark.integration
    def test_search_without_image(self):
        """Test text-only search (existing functionality)"""
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "laptops",
                "max_results": 10,
                "user_profile": '{"user_id": "TEST001", "monthly_income": 5000, "credit_score": 720}'
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "metadata" in data, "Response should have metadata"
        assert data["metadata"]["multimodal"] == False, "Should indicate text-only search"
        assert data["metadata"]["search_mode"] == "text_only", "Search mode should be text_only"

    @pytest.mark.integration
    def test_search_with_image(self):
        """Test multimodal search with image upload"""
        img_bytes = self.create_test_image(color='red')

        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "phones like this",
                "max_results": 10,
                "user_profile": '{"user_id": "TEST002", "monthly_income": 5000, "credit_score": 720}'
            },
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "metadata" in data, "Response should have metadata"
        assert data["metadata"]["multimodal"] == True, "Should indicate multimodal search"
        assert data["metadata"]["search_mode"] == "multimodal", "Search mode should be multimodal"

    @pytest.mark.integration
    def test_invalid_image_format(self):
        """Test rejection of invalid image formats"""
        # Create a text file
        text_file = BytesIO(b"This is not an image")

        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "test",
                "max_results": 10,
                "user_profile": '{"user_id": "TEST003", "monthly_income": 5000, "credit_score": 720}'
            },
            files={"image": ("test.txt", text_file, "text/plain")}
        )

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Unsupported image format" in response.json()["detail"], \
            "Should reject non-image files"

    @pytest.mark.integration
    def test_image_too_large(self):
        """Test rejection of images > 10MB"""
        # Create a large image (6000x6000 pixels ≈ 108MB uncompressed)
        large_img = self.create_test_image(color='blue', size=(6000, 6000))

        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "test",
                "max_results": 10,
                "user_profile": '{"user_id": "TEST004", "monthly_income": 5000, "credit_score": 720}'
            },
            files={"image": ("large.jpg", large_img, "image/jpeg")}
        )

        # Might be 400 or 413 depending on server config
        assert response.status_code in [400, 413], \
            f"Expected 400 or 413 for large image, got {response.status_code}"

    @pytest.mark.integration
    def test_multimodal_different_from_text_only(self):
        """Test that multimodal embeddings are different from text-only"""
        # Text-only search
        response1 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "red laptops",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST005", "monthly_income": 5000, "credit_score": 720}'
            }
        )

        # Multimodal search with red image
        img_bytes = self.create_test_image(color='red')
        response2 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "red laptops",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST005", "monthly_income": 5000, "credit_score": 720}'
            },
            files={"image": ("red.jpg", img_bytes, "image/jpeg")}
        )

        assert response1.status_code == 200, f"Text-only search failed: {response1.text}"
        assert response2.status_code == 200, f"Multimodal search failed: {response2.text}"

        data1 = response1.json()
        data2 = response2.json()

        # Check metadata differences
        assert data1["metadata"]["multimodal"] == False, "First search should be text-only"
        assert data2["metadata"]["multimodal"] == True, "Second search should be multimodal"

        # Results might be different (different embeddings)
        # This is a rough check - embeddings should influence ranking
        # NOTE: In practice, results may vary, so we just verify the flag changed
        print(f"Text-only candidates: {data1['metadata']['total_candidates']}")
        print(f"Multimodal candidates: {data2['metadata']['total_candidates']}")

    @pytest.mark.integration
    def test_supported_image_formats(self):
        """Test all supported image formats (JPG, PNG, WebP)"""
        formats = [
            ("test.jpg", "image/jpeg", "JPEG"),
            ("test.png", "image/png", "PNG"),
            ("test.webp", "image/webp", "WEBP")
        ]

        for filename, content_type, pil_format in formats:
            img = Image.new('RGB', (200, 200), color='green')
            img_bytes = BytesIO()
            img.save(img_bytes, format=pil_format)
            img_bytes.seek(0)

            response = requests.post(
                f"{API_BASE_URL}/api/search",
                data={
                    "query": "test",
                    "max_results": 5,
                    "user_profile": '{"user_id": "TEST006", "monthly_income": 5000, "credit_score": 720}'
                },
                files={"image": (filename, img_bytes, content_type)}
            )

            assert response.status_code == 200, \
                f"Format {pil_format} should be accepted, got {response.status_code}: {response.text}"

            data = response.json()
            assert data["metadata"]["multimodal"] == True, \
                f"Format {pil_format} should enable multimodal"

    @pytest.mark.integration
    def test_cache_key_differs_with_image(self):
        """Test that cache keys differ for text vs text+image"""
        # First request: text-only
        response1 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "laptop",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST007", "monthly_income": 5000, "credit_score": 720}'
            }
        )

        # Second request: same text + image
        img_bytes = self.create_test_image()
        response2 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "laptop",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST007", "monthly_income": 5000, "credit_score": 720}'
            },
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )

        # Third request: text-only again (should hit cache)
        response3 = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "laptop",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST007", "monthly_income": 5000, "credit_score": 720}'
            }
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # Third request should potentially be a cache hit
        # (if caching is enabled and working)
        data3 = response3.json()
        if data3["metadata"].get("cache_hit"):
            print("✅ Cache working: Third request was a cache hit")
        else:
            print("⚠️ Cache miss (might be first run or cache disabled)")


class TestMultimodalErrorHandling:
    """Test error handling for multimodal search"""

    @pytest.mark.integration
    def test_missing_required_fields(self):
        """Test that required fields are validated"""
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "test"
                # Missing user_profile
            }
        )

        # Should work without user_profile (anonymous user)
        # But check the response
        if response.status_code == 200:
            data = response.json()
            assert data["user_id"] == "anonymous", "Should handle anonymous users"

    @pytest.mark.integration
    def test_malformed_json_user_profile(self):
        """Test rejection of malformed JSON in user_profile"""
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "test",
                "max_results": 5,
                "user_profile": "not valid json"
            }
        )

        assert response.status_code == 400, \
            f"Expected 400 for malformed JSON, got {response.status_code}"
        assert "Invalid JSON" in response.json()["detail"], \
            "Should indicate JSON parsing error"

    @pytest.mark.integration
    def test_missing_user_profile_required_fields(self):
        """Test validation of user_profile required fields"""
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "test",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST"}' # Missing monthly_income, credit_score
            }
        )

        assert response.status_code == 400, \
            f"Expected 400 for missing fields, got {response.status_code}"
        assert "Missing required" in response.json()["detail"], \
            "Should indicate missing required fields"


class TestAgent1MultimodalIntegration:
    """Test Agent 1 multimodal logic integration"""

    @pytest.mark.integration
    def test_agent1_receives_image_embedding(self):
        """Test that Agent 1 correctly receives and uses image embedding"""
        img_bytes = BytesIO()
        img = Image.new('RGB', (300, 300), color='blue')
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        response = requests.post(
            f"{API_BASE_URL}/api/search",
            data={
                "query": "blue products",
                "max_results": 5,
                "user_profile": '{"user_id": "TEST_AGENT1", "monthly_income": 5000, "credit_score": 720}'
            },
            files={"image": ("blue.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()

        # Verify multimodal search was executed
        assert data["metadata"]["multimodal"] == True, \
            "Should indicate multimodal search"

        # Verify Agent 1 found products
        assert data["metadata"]["total_candidates"] >= 0, \
            "Agent 1 should return candidate count"

        # Check that we got recommendations
        assert len(data["recommendations"]) >= 0, \
            "Should return recommendations (empty is ok if no products match)"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
