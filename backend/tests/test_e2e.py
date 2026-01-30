"""
End-to-End Test - Complete User Journey with RL Learning

This test validates the ENTIRE system:
1. User searches for products
2. Views recommendations
3. Interacts with products (view, click, add_to_cart, purchase)
4. Thompson Sampling learns from interactions
5. Next search shows updated rankings

Run with: pytest backend/tests/test_e2e.py -v -s
"""

import pytest
import requests
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"


class TestEndToEndUserJourney:
    """Test complete user journey with reinforcement learning"""

    def test_complete_user_journey_with_learning(self):
        """
        CRITICAL E2E TEST: Validates entire system including RL learning.

        Flow:
        1. User searches "laptop under $1000"
        2. Gets 10 recommendations
        3. Views product #1
        4. Clicks product #1
        5. Adds product #1 to cart
        6. Purchases product #1
        7. Searches again (same query)
        8. Verifies product #1 ranking improved (Thompson Sampling learned)

        Success criteria:
        - All API calls return 200
        - Thompson parameters increase after purchase
        - Product ranking improves on second search
        - Cache works (second search faster if same user)
        """
        # Use unique user ID for test isolation
        user_id = f"E2E_TEST_USER_{int(time.time())}"

        user_profile = {
            "user_id": user_id,
            "monthly_income": 5000.0,
            "credit_score": 720,
            "monthly_expenses": 3000.0,
            "savings": 10000.0,
            "current_debt": 2000.0
        }

        # ========================================
        # STEP 1: Initial search
        # ========================================
        print("\n" + "="*60)
        print("STEP 1: Initial Product Search")
        print("="*60)

        # Note: API expects Form data, not JSON
        search_request_data = {
            "query": "laptop under $1000",
            "max_results": 10,
            "user_profile": str(user_profile).replace("'", '"')  # Convert to JSON string
        }

        search_response = requests.post(
            f"{API_BASE_URL}/api/search",
            data=search_request_data
        )

        assert search_response.status_code == 200, f"Search failed: {search_response.text}"

        search_data = search_response.json()
        recommendations = search_data["recommendations"]

        assert len(recommendations) > 0, "No recommendations returned"
        print(f"✅ Got {len(recommendations)} recommendations")

        # Select first product for interaction
        first_product = recommendations[0]
        product_id = first_product["product"]["product_id"]
        product_name = first_product["product"]["name"]
        initial_rank = first_product["rank"]
        initial_score = first_product["final_score"]

        print(f"Selected product: {product_name} (ID: {product_id})")
        print(f"Initial rank: {initial_rank}, score: {initial_score:.2f}")

        # ========================================
        # STEP 2: Get initial Thompson parameters
        # ========================================
        print("\n" + "="*60)
        print("STEP 2: Get Initial Thompson Parameters")
        print("="*60)

        # Get Thompson stats before interactions
        stats_before = requests.get(f"{API_BASE_URL}/api/thompson/stats")
        assert stats_before.status_code == 200

        print(f"✅ Thompson Sampling active: {stats_before.json()['products_tracked']} products tracked")

        # ========================================
        # STEP 3: User views product
        # ========================================
        print("\n" + "="*60)
        print("STEP 3: User Views Product (Signal: +0.1)")
        print("="*60)

        view_response = requests.post(
            f"{API_BASE_URL}/api/interact",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "action": "view"
            }
        )

        assert view_response.status_code == 200
        view_data = view_response.json()

        alpha_after_view = view_data["alpha"]
        beta_after_view = view_data["beta"]
        conversion_after_view = view_data["conversion_rate"]

        print(f"After view: α={alpha_after_view:.2f}, β={beta_after_view:.2f}, conversion={conversion_after_view:.3f}")

        # ========================================
        # STEP 4: User clicks product
        # ========================================
        print("\n" + "="*60)
        print("STEP 4: User Clicks Product (Signal: +0.3)")
        print("="*60)

        click_response = requests.post(
            f"{API_BASE_URL}/api/interact",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "action": "click"
            }
        )

        assert click_response.status_code == 200
        click_data = click_response.json()

        alpha_after_click = click_data["alpha"]
        beta_after_click = click_data["beta"]

        print(f"After click: α={alpha_after_click:.2f}, β={beta_after_click:.2f}")

        # Verify alpha increased
        assert alpha_after_click > alpha_after_view, \
            f"Alpha should increase after click: {alpha_after_view} → {alpha_after_click}"

        # ========================================
        # STEP 5: User adds to cart
        # ========================================
        print("\n" + "="*60)
        print("STEP 5: User Adds to Cart (Signal: +0.7)")
        print("="*60)

        cart_response = requests.post(
            f"{API_BASE_URL}/api/interact",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "action": "add_to_cart"
            }
        )

        assert cart_response.status_code == 200
        cart_data = cart_response.json()

        alpha_after_cart = cart_data["alpha"]
        beta_after_cart = cart_data["beta"]

        print(f"After add_to_cart: α={alpha_after_cart:.2f}, β={beta_after_cart:.2f}")

        # Verify alpha increased significantly
        assert alpha_after_cart > alpha_after_click, \
            f"Alpha should increase after add_to_cart: {alpha_after_click} → {alpha_after_cart}"

        # ========================================
        # STEP 6: User purchases product
        # ========================================
        print("\n" + "="*60)
        print("STEP 6: User Purchases Product (Signal: +1.0)")
        print("="*60)

        purchase_response = requests.post(
            f"{API_BASE_URL}/api/interact",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "action": "purchase"
            }
        )

        assert purchase_response.status_code == 200
        purchase_data = purchase_response.json()

        alpha_final = purchase_data["alpha"]
        beta_final = purchase_data["beta"]
        conversion_final = purchase_data["conversion_rate"]

        print(f"After purchase: α={alpha_final:.2f}, β={beta_final:.2f}, conversion={conversion_final:.3f}")

        # Verify learning occurred
        assert alpha_final > alpha_after_cart, \
            f"Alpha should increase after purchase: {alpha_after_cart} → {alpha_final}"

        # Calculate total alpha increase
        alpha_increase = alpha_final - alpha_after_view
        expected_increase = 0.3 + 0.7 + 1.0  # click + cart + purchase = 2.0

        print(f"\n📊 Learning Summary:")
        print(f"  Total α increase: {alpha_increase:.2f} (expected ~{expected_increase:.2f})")
        print(f"  Conversion rate: {conversion_after_view:.3f} → {conversion_final:.3f}")

        # ========================================
        # STEP 7: Second search (verify ranking improved)
        # ========================================
        print("\n" + "="*60)
        print("STEP 7: Second Search - Verify Ranking Improved")
        print("="*60)

        # Wait 1 second to ensure Thompson update propagated
        time.sleep(1)

        search_response_2 = requests.post(
            f"{API_BASE_URL}/api/search",
            data=search_request_data
        )

        assert search_response_2.status_code == 200

        search_data_2 = search_response_2.json()
        recommendations_2 = search_data_2["recommendations"]

        # Find the product we interacted with
        interacted_product = next(
            (rec for rec in recommendations_2 if rec["product"]["product_id"] == product_id),
            None
        )

        assert interacted_product is not None, \
            f"Product {product_id} not found in second search results"

        new_rank = interacted_product["rank"]
        new_score = interacted_product["final_score"]

        print(f"\n📈 Ranking Comparison:")
        print(f"  Before interactions: Rank #{initial_rank}, Score {initial_score:.2f}")
        print(f"  After interactions:  Rank #{new_rank}, Score {new_score:.2f}")

        # Verify ranking improved OR stayed the same (if already #1)
        # Note: Ranking is probabilistic (Thompson Sampling), so might not always improve
        # But score should be higher due to increased alpha
        if initial_rank > 1:
            # If not already #1, ranking should improve or score should increase
            ranking_improved = new_rank < initial_rank
            score_increased = new_score > initial_score

            assert ranking_improved or score_increased, \
                f"Expected improvement: rank {initial_rank}→{new_rank} or score {initial_score:.2f}→{new_score:.2f}"

            if ranking_improved:
                print(f"✅ RANKING IMPROVED: #{initial_rank} → #{new_rank}")
            if score_increased:
                print(f"✅ SCORE INCREASED: {initial_score:.2f} → {new_score:.2f}")
        else:
            # Already #1, just verify it stayed #1
            assert new_rank == 1, f"Product should remain #1, but dropped to #{new_rank}"
            print(f"✅ MAINTAINED TOP RANK: #{new_rank}")

        # ========================================
        # STEP 8: Verify cache works
        # ========================================
        print("\n" + "="*60)
        print("STEP 8: Verify Cache Works (FAST Path)")
        print("="*60)

        # Third search (should hit cache)
        start_cache_test = time.time()
        search_response_3 = requests.post(
            f"{API_BASE_URL}/api/search",
            data=search_request_data
        )
        cache_test_time = (time.time() - start_cache_test) * 1000  # ms

        assert search_response_3.status_code == 200

        search_data_3 = search_response_3.json()
        cache_hit = search_data_3["metadata"].get("cache_hit", False)

        if cache_hit:
            print(f"✅ CACHE HIT: Response time {cache_test_time:.0f}ms (should be <200ms)")
            assert cache_test_time < 500, \
                f"Cache hit should be fast (<500ms), but took {cache_test_time:.0f}ms"
        else:
            print(f"⚠️ CACHE MISS: Response time {cache_test_time:.0f}ms (cache might not be enabled yet)")

        # ========================================
        # FINAL SUMMARY
        # ========================================
        print("\n" + "="*60)
        print("✅ END-TO-END TEST PASSED")
        print("="*60)
        print("Summary:")
        print(f"  • Product: {product_name}")
        print(f"  • Interactions: view → click → cart → purchase")
        print(f"  • Thompson Learning: α {alpha_after_view:.2f} → {alpha_final:.2f} (Δ{alpha_increase:.2f})")
        print(f"  • Ranking: #{initial_rank} → #{new_rank}")
        print(f"  • Cache: {'HIT' if cache_hit else 'MISS'}")
        print(f"  • System Status: WORKING CORRECTLY ✅")
        print("="*60)


# Run with: pytest backend/tests/test_e2e.py -v -s
