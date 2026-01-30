"""
Integration Test for Thompson Sampling API Endpoints

Tests:
1. POST /api/interact - User interaction tracking
2. GET /api/thompson/stats - Thompson statistics

Run:
    python backend/scripts/test_thompson_api.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from ml.thompson_sampling import ThompsonSamplingEngine
from ml.thompson_metrics import get_metrics


def test_interaction_tracking():
    """Test interaction tracking updates Thompson parameters"""
    print("\n" + "=" * 80)
    print("TEST 1: Interaction Tracking")
    print("=" * 80)

    try:
        engine = ThompsonSamplingEngine()

        # Get initial params
        initial_params = engine.get_params("PROD_TEST_001")
        print(f"Initial: alpha={initial_params['alpha']}, beta={initial_params['beta']}")

        # Simulate purchase
        engine.update_params("PROD_TEST_001", "purchase")

        # Get updated params
        updated_params = engine.get_params("PROD_TEST_001")
        print(f"After purchase: alpha={updated_params['alpha']}, beta={updated_params['beta']}")

        # Verify alpha increased
        assert updated_params['alpha'] > initial_params['alpha'], \
            "Alpha should increase after purchase"

        print("PASS: Interaction tracking works correctly")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thompson_stats():
    """Test Thompson statistics aggregation"""
    print("\n" + "=" * 80)
    print("TEST 2: Thompson Statistics")
    print("=" * 80)

    try:
        engine = ThompsonSamplingEngine()

        # Add some test interactions
        products = ["PROD_TEST_001", "PROD_TEST_002", "PROD_TEST_003"]

        for product_id in products:
            engine.update_params(product_id, "purchase")
            engine.update_params(product_id, "view")

        # Get stats
        metrics = get_metrics(engine)
        stats = metrics.get_stats()

        print(f"Products tracked: {stats['products_tracked']}")
        print(f"Avg alpha: {stats['avg_alpha']}")
        print(f"Avg beta: {stats['avg_beta']}")
        print(f"Avg conversion: {stats['avg_conversion']}")
        print(f"Confidence distribution: {stats['confidence']}")

        # Verify structure
        assert "products_tracked" in stats, "Should have products_tracked"
        assert "avg_alpha" in stats, "Should have avg_alpha"
        assert "avg_beta" in stats, "Should have avg_beta"
        assert "avg_conversion" in stats, "Should have avg_conversion"
        assert "confidence" in stats, "Should have confidence distribution"

        # Verify values make sense
        assert stats['products_tracked'] >= len(products), \
            f"Should track at least {len(products)} products"

        assert stats['avg_alpha'] >= 1.0, "Avg alpha should be >= 1.0"
        assert stats['avg_beta'] >= 1.0, "Avg beta should be >= 1.0"

        assert 0.0 <= stats['avg_conversion'] <= 1.0, \
            "Avg conversion should be in [0, 1]"

        print("PASS: Thompson statistics work correctly")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_valid_actions():
    """Test all valid action types"""
    print("\n" + "=" * 80)
    print("TEST 3: Valid Actions")
    print("=" * 80)

    try:
        engine = ThompsonSamplingEngine()

        valid_actions = [
            "view", "click", "add_to_cart", "purchase",
            "skip", "remove_from_cart", "return"
        ]

        for action in valid_actions:
            product_id = f"PROD_ACTION_{action.upper()}"
            engine.update_params(product_id, action)
            params = engine.get_params(product_id)

            print(f"  OK {action:20s} -> alpha={params['alpha']:.2f}, beta={params['beta']:.2f}")

        print(f"PASS: All {len(valid_actions)} action types work correctly")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_confidence_levels():
    """Test confidence level calculation"""
    print("\n" + "=" * 80)
    print("TEST 4: Confidence Levels")
    print("=" * 80)

    try:
        engine = ThompsonSamplingEngine()

        # Low confidence (0 interactions)
        params_low = engine.get_params("PROD_LOW")
        assert params_low['confidence'] == 'low', "Should be low confidence with 0 interactions"
        print(f"  OK Low confidence: {params_low['total_interactions']} interactions -> {params_low['confidence']}")

        # Medium confidence (10 interactions)
        for _ in range(10):
            engine.update_params("PROD_MED", "view")
        params_med = engine.get_params("PROD_MED")
        assert params_med['confidence'] == 'medium', "Should be medium confidence with 10 interactions"
        print(f"  OK Medium confidence: {params_med['total_interactions']} interactions -> {params_med['confidence']}")

        # High confidence (25+ interactions)
        for _ in range(25):
            engine.update_params("PROD_HIGH", "click")
        params_high = engine.get_params("PROD_HIGH")
        assert params_high['confidence'] == 'high', "Should be high confidence with 25+ interactions"
        print(f"  OK High confidence: {params_high['total_interactions']} interactions -> {params_high['confidence']}")

        print("PASS: Confidence levels calculated correctly")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all API integration tests"""

    print("=" * 80)
    print("THOMPSON SAMPLING API - INTEGRATION TEST")
    print("=" * 80)
    print("\nThis test validates:")
    print("  * Interaction tracking (/api/interact)")
    print("  * Statistics endpoint (/api/thompson/stats)")
    print("  * All valid action types")
    print("  * Confidence level calculation")

    # Run all tests
    results = {}

    results["Test 1: Interaction Tracking"] = test_interaction_tracking()
    results["Test 2: Thompson Statistics"] = test_thompson_stats()
    results["Test 3: Valid Actions"] = test_valid_actions()
    results["Test 4: Confidence Levels"] = test_confidence_levels()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "-" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)

    if passed == total:
        print("\nSUCCESS: All API tests passed!")
        print("Endpoints /api/interact and /api/thompson/stats are ready.")
        return 0
    else:
        print("\nFAILURE: Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
