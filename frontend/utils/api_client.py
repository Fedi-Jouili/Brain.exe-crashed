"""
API Client - Handles all backend communication
"""

import requests
import streamlit as st
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """
    Client for FinCommerce Engine backend API.

    Handles:
    - Product search
    - User interactions
    - System health
    - Metrics retrieval
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client"""
        self.base_url = base_url
        self.session = requests.Session()

    def get_health(self) -> Optional[Dict[str, Any]]:
        """Get system health status"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return None

    def search(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search products (text only).

        Args:
            request: Search request dict

        Returns:
            Search response or None
        """
        try:
            # Prepare form data
            data = {
                "query": request["query"],
                "max_results": request.get("max_results", 10)
            }

            # Add user profile if provided
            if request.get("user_profile"):
                import json
                data["user_profile"] = json.dumps(request["user_profile"])

            response = self.session.post(
                f"{self.base_url}/api/search",
                data=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            st.error("⏱️ Search timed out. Please try again.")
            return None
        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")
            logger.error(f"Search error: {e}")
            return None

    def search_with_image(
        self,
        query: str,
        image,
        max_results: int = 10,
        user_profile: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search products with image (multimodal).

        Args:
            query: Search query
            image: Uploaded image file
            max_results: Number of results
            user_profile: Optional user profile

        Returns:
            Search response or None
        """
        try:
            # Prepare multipart form data
            files = {"image": (image.name, image.getvalue(), image.type)}

            data = {
                "query": query,
                "max_results": max_results
            }

            if user_profile:
                import json
                data["user_profile"] = json.dumps(user_profile)

            response = self.session.post(
                f"{self.base_url}/api/search",
                data=data,
                files=files,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            st.error(f"❌ Multimodal search failed: {str(e)}")
            logger.error(f"Multimodal search error: {e}")
            return None

    def track_interaction(
        self,
        user_id: str,
        product_id: str,
        action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Track user interaction (Thompson Sampling).

        Args:
            user_id: User identifier
            product_id: Product identifier
            action: Action type (view, click, add_to_cart, purchase, etc.)

        Returns:
            Interaction response or None
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/interact",
                json={
                    "user_id": user_id,
                    "product_id": product_id,
                    "action": action
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Interaction tracking failed: {e}")
            return None

    def get_thompson_stats(self) -> Optional[Dict[str, Any]]:
        """Get Thompson Sampling statistics"""
        try:
            response = self.session.get(f"{self.base_url}/api/thompson/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Thompson stats retrieval failed: {e}")
            return None

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics"""
        try:
            response = self.session.get(f"{self.base_url}/api/cache/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Cache stats retrieval failed: {e}")
            return None
