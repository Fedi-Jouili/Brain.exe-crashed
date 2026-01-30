"""
Comprehensive Test Suite for Thompson Sampling Engine
Tests all functionality: sampling, ranking, learning, weighted signals

Run: python backend/scripts/test_thompson.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from ml.thompson_sampling import ThompsonSamplingEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_1_initialization(engine: ThompsonSamplingEngine) -> bool:
    """Test engine initializes with correct defaults"""
    print("\n" + "─" * 80)
    print("TEST 1: Engine Initialization")
    print("─" * 80)

    try:
        # Import settings to check signal weights
        from core.config import settings

        # Test signal weights are loaded
        signal_weights = settings.signal_weights
        assert len(signal_weights) == 7, f"Should have 7 signal types, got {len(signal_weights)}"
        assert signal_weights['purchase'] == 1.0, f"Purchase weight should be 1.0, got {signal_weights['purchase']}"
        assert signal_weights['return'] == -1.0, f"Return weight should be -1.0, got {signal_weights['return']}"

        # Test initial params for new product
        params = engine.get_params("TEST_PRODUCT")
        assert params['alpha'] == 1.0, f"Initial alpha should be 1.0, got {params['alpha']}"
        assert params['beta'] == 1.0, f"Initial beta should be 1.0, got {params['beta']}"
        assert params['total_interactions'] == 0, f"Initial interactions should be 0, got {params['total_interactions']}"

        print("✅ Initialization test passed")
        print(f"   - Signal weights: {len(signal_weights)} types loaded")
        print(f"   - Default prior: α={params['alpha']}, β={params['beta']}")
        return True

    except AssertionError as e:
        print(f"❌ Initialization test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization test error: {e}")
        return False


def test_2_uniform_prior_ranking(engine: ThompsonSamplingEngine) -> bool:
    """Test that new products rank randomly with uniform prior"""
    print("\n" + "─" * 80)
    print("TEST 2: Uniform Prior Ranking (New Products)")
    print("─" * 80)

    try:
        # Create 10 new products
        products = [
            {"product_id": f"PROD{i:04d}", "name": f"Product {i}"}
            for i in range(1, 11)
        ]

        # Rank products
        ranked = engine.rank_products(products.copy())

        # Verify all have Thompson scores
        for product in ranked:
            assert 'thompson_score' in product, "Product should have thompson_score"
            assert 0 <= product['thompson_score'] <= 1, f"Score should be in [0,1], got {product['thompson_score']}"
            assert product['thompson_alpha'] == 1.0, f"Alpha should be 1.0 (prior), got {product['thompson_alpha']}"
            assert product['thompson_beta'] == 1.0, f"Beta should be 1.0 (prior), got {product['thompson_beta']}"
            assert product['thompson_confidence'] == 'low', f"Confidence should be low, got {product['thompson_confidence']}"

        print("✅ Uniform prior ranking test passed")
        print(f"   Ranked {len(ranked)} products")
        print(f"   Top 5 rankings (should be somewhat random):")
        for i, p in enumerate(ranked[:5], 1):
            print(f"      {i}. {p['product_id']} - Score: {p['thompson_score']:.3f}")

        return True

    except AssertionError as e:
        print(f"❌ Uniform prior test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Uniform prior test error: {e}")
        return False


def test_3_positive_signals(engine: ThompsonSamplingEngine) -> bool:
    """Test that positive signals increase product ranking"""
    print("\n" + "─" * 80)
    print("TEST 3: Positive Signals (Purchases)")
    print("─" * 80)

    try:
        # Simulate 10 purchases on PROD0001
        print("   Simulating 10 purchases on PROD0001...")

        for i in range(10):
            engine.update_params("PROD0001", "purchase")

        # Check final params
        params = engine.get_params("PROD0001")

        print(f"   Final parameters:")
        print(f"      α = {params['alpha']:.2f} (was 1.0)")
        print(f"      β = {params['beta']:.2f} (should still be 1.0)")
        conversion_rate = params['alpha'] / (params['alpha'] + params['beta'])
        print(f"      Conversion = {conversion_rate:.3f}")
        print(f"      Total interactions = {params['total_interactions']:.0f}")

        # Verify
        assert params['alpha'] == 11.0, f"Alpha should be 11.0 (1 + 10*1.0), got {params['alpha']}"
        assert params['beta'] == 1.0, f"Beta should still be 1.0, got {params['beta']}"
        assert params['total_interactions'] == 10, f"Should have 10 interactions, got {params['total_interactions']}"
        assert conversion_rate > 0.90, f"Conversion should be >90%, got {conversion_rate}"

        # Test ranking - PROD0001 should rank higher now
        products = [
            {"product_id": f"PROD{i:04d}", "name": f"Product {i}"}
            for i in range(1, 11)
        ]

        ranked = engine.rank_products(products.copy())

        # Find PROD0001 rank
        prod0001_rank = next(i for i, p in enumerate(ranked, 1) if p['product_id'] == "PROD0001")

        print(f"\n   Ranking after purchases:")
        for i, p in enumerate(ranked[:5], 1):
            symbol = "🔥" if p['product_id'] == "PROD0001" else "  "
            print(f"      {i}. {symbol} {p['product_id']} - Score: {p['thompson_score']:.3f}")

        # PROD0001 should rank in top 5 (probabilistic, so not always #1)
        # Using ≤5 because Beta sampling is stochastic and heavily-purchased products
        # will usually rank very high but not guaranteed top 3
        assert prod0001_rank <= 5, f"PROD0001 should rank ≤5, got rank {prod0001_rank}"

        print(f"\n✅ Positive signals test passed")
        print(f"   PROD0001 ranked #{prod0001_rank} after 10 purchases")

        return True

    except AssertionError as e:
        print(f"❌ Positive signals test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Positive signals test error: {e}")
        return False


def test_4_negative_signals(engine: ThompsonSamplingEngine) -> bool:
    """Test that negative signals decrease product ranking"""
    print("\n" + "─" * 80)
    print("TEST 4: Negative Signals (Skips)")
    print("─" * 80)

    try:
        # Simulate 10 skips on PROD0002
        print("   Simulating 10 skips on PROD0002...")

        for i in range(10):
            engine.update_params("PROD0002", "skip")

        # Check final params
        params = engine.get_params("PROD0002")

        print(f"   Final parameters:")
        print(f"      α = {params['alpha']:.2f} (should still be 1.0)")
        print(f"      β = {params['beta']:.2f} (was 1.0)")
        conversion_rate = params['alpha'] / (params['alpha'] + params['beta'])
        print(f"      Conversion = {conversion_rate:.3f}")
        print(f"      Total interactions = {params['total_interactions']:.0f}")

        # Verify (skip has weight -0.3, so beta increases by 0.3 each time)
        expected_beta = 1.0 + (10 * 0.3)  # 4.0
        assert params['alpha'] == 1.0, f"Alpha should still be 1.0, got {params['alpha']}"
        # Use approximate comparison for floating point
        assert abs(params['beta'] - expected_beta) < 0.001, \
            f"Beta should be ~{expected_beta}, got {params['beta']}"
        assert params['total_interactions'] == 10, f"Should have 10 interactions, got {params['total_interactions']}"
        assert conversion_rate < 0.30, f"Conversion should be <30%, got {conversion_rate}"

        # Test ranking - PROD0002 should rank lower
        products = [
            {"product_id": f"PROD{i:04d}", "name": f"Product {i}"}
            for i in range(1, 11)
        ]

        ranked = engine.rank_products(products.copy())

        # Find PROD0002 rank
        prod0002_rank = next(i for i, p in enumerate(ranked, 1) if p['product_id'] == "PROD0002")

        print(f"\n   Ranking after skips:")
        for i, p in enumerate(ranked, 1):
            symbol = "❄️ " if p['product_id'] == "PROD0002" else "  "
            print(f"      {i:2d}. {symbol} {p['product_id']} - Score: {p['thompson_score']:.3f}")

        # PROD0002 should rank in bottom half (≥6)
        assert prod0002_rank >= 6, f"PROD0002 should rank ≥6, got rank {prod0002_rank}"

        print(f"\n✅ Negative signals test passed")
        print(f"   PROD0002 ranked #{prod0002_rank} after 10 skips")

        return True

    except AssertionError as e:
        print(f"❌ Negative signals test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Negative signals test error: {e}")
        return False


def test_5_learning_verification(engine: ThompsonSamplingEngine) -> bool:
    """Verify the engine learns: purchased products rank higher than skipped"""
    print("\n" + "─" * 80)
    print("TEST 5: Learning Verification (Purchases vs Skips)")
    print("─" * 80)

    try:
        # Get final ranking
        products = [
            {"product_id": f"PROD{i:04d}", "name": f"Product {i}"}
            for i in range(1, 11)
        ]

        ranked = engine.rank_products(products.copy())

        # Find ranks
        prod0001_rank = next(i for i, p in enumerate(ranked, 1) if p['product_id'] == "PROD0001")
        prod0002_rank = next(i for i, p in enumerate(ranked, 1) if p['product_id'] == "PROD0002")

        print(f"   PROD0001 (10 purchases): Rank #{prod0001_rank}")
        print(f"   PROD0002 (10 skips):     Rank #{prod0002_rank}")

        # Verify learning: purchased product ranks higher than skipped
        assert prod0001_rank < prod0002_rank, \
            f"Purchased product should rank higher: {prod0001_rank} vs {prod0002_rank}"

        # Verify significant difference (at least 3 positions apart)
        rank_diff = prod0002_rank - prod0001_rank
        assert rank_diff >= 3, f"Rank difference should be ≥3, got {rank_diff}"

        print(f"\n✅ Learning verification passed")
        print(f"   The engine learned from user actions!")
        print(f"   Rank difference: {rank_diff} positions")

        return True

    except AssertionError as e:
        print(f"❌ Learning verification failed: {e}")
        print("   Note: This test is probabilistic. Try running again.")
        return False
    except Exception as e:
        print(f"❌ Learning verification error: {e}")
        return False


def test_6_confidence_levels(engine: ThompsonSamplingEngine) -> bool:
    """Test confidence levels based on interaction count"""
    print("\n" + "─" * 80)
    print("TEST 6: Confidence Levels")
    print("─" * 80)

    try:
        # Test low confidence (0-4 interactions)
        params_low = engine.get_params("PROD0009")  # No interactions
        confidence_low = engine.get_confidence_level("PROD0009")
        assert confidence_low == "low", f"Should be low confidence, got {confidence_low}"
        print(f"   ✓ Low confidence: {params_low['total_interactions']:.0f} interactions → {confidence_low}")

        # Test medium confidence (5-19 interactions)
        # Add interactions to PROD0003
        for _ in range(10):
            engine.update_params("PROD0003", "click")  # weight 0.3

        params_med = engine.get_params("PROD0003")
        confidence_med = engine.get_confidence_level("PROD0003")
        assert confidence_med == "medium", f"Should be medium confidence, got {confidence_med}"
        print(f"   ✓ Medium confidence: {params_med['total_interactions']:.0f} interactions → {confidence_med}")

        # Test high confidence (20+ interactions)
        # Add more interactions to PROD0003
        for _ in range(15):
            engine.update_params("PROD0003", "view")  # weight 0.1

        params_high = engine.get_params("PROD0003")
        confidence_high = engine.get_confidence_level("PROD0003")
        assert confidence_high == "high", f"Should be high confidence, got {confidence_high}"
        print(f"   ✓ High confidence: {params_high['total_interactions']:.0f} interactions → {confidence_high}")

        print("\n✅ Confidence levels test passed")

        return True

    except AssertionError as e:
        print(f"❌ Confidence levels test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Confidence levels test error: {e}")
        return False


def test_7_all_signal_types(engine: ThompsonSamplingEngine) -> bool:
    """Test all 7 signal types work correctly"""
    print("\n" + "─" * 80)
    print("TEST 7: All Signal Types")
    print("─" * 80)

    try:
        signal_tests = [
            ("view", 0.1, "PROD_VIEW"),
            ("click", 0.3, "PROD_CLICK"),
            ("add_to_cart", 0.7, "PROD_CART"),
            ("purchase", 1.0, "PROD_PURCHASE"),
            ("skip", -0.3, "PROD_SKIP"),
            ("remove_from_cart", -0.5, "PROD_REMOVE"),
            ("return", -1.0, "PROD_RETURN"),
        ]

        for action, weight, product_id in signal_tests:
            # Apply signal
            engine.update_params(product_id, action)
            params = engine.get_params(product_id)

            # Verify
            if weight > 0:
                expected_alpha = 1.0 + weight
                assert params['alpha'] == expected_alpha, \
                    f"{action}: alpha should be {expected_alpha}, got {params['alpha']}"
                assert params['beta'] == 1.0, f"{action}: beta should still be 1.0, got {params['beta']}"
            else:
                expected_beta = 1.0 + abs(weight)
                assert params['alpha'] == 1.0, f"{action}: alpha should still be 1.0, got {params['alpha']}"
                assert params['beta'] == expected_beta, \
                    f"{action}: beta should be {expected_beta}, got {params['beta']}"

            print(f"   ✓ {action:20s} (weight={weight:+.1f}) → α={params['alpha']:.2f}, β={params['beta']:.2f}")

        print("\n✅ All signal types test passed")

        return True

    except AssertionError as e:
        print(f"❌ Signal types test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Signal types test error: {e}")
        return False


def main():
    """Run all Thompson Sampling tests"""

    print("=" * 80)
    print("THOMPSON SAMPLING ENGINE - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Create engine (in-memory only for isolated testing)
    engine = ThompsonSamplingEngine()

    # Run test suite
    all_tests_passed = True

    all_tests_passed &= test_1_initialization(engine)
    all_tests_passed &= test_2_uniform_prior_ranking(engine)
    all_tests_passed &= test_3_positive_signals(engine)
    all_tests_passed &= test_4_negative_signals(engine)
    all_tests_passed &= test_5_learning_verification(engine)
    all_tests_passed &= test_6_confidence_levels(engine)
    all_tests_passed &= test_7_all_signal_types(engine)

    # Final summary
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED!")
        print("Thompson Sampling Engine is working correctly.")
        print("Ready for Redis integration and Agent 3 integration.")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("Review the output above to identify issues.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
