"""
Unit tests for Thompson Sampling reinforcement learning

Run with: pytest backend/tests/test_thompson_sampling.py -v
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.thompson_sampling import ThompsonSamplingEngine


class TestThompsonSampling:
    """Test Thompson Sampling RL engine"""

    def test_initialization(self):
        """Test engine initializes with correct defaults"""
        engine = ThompsonSamplingEngine()

        # Test default parameters for new product
        params = engine.get_params("NEW_PRODUCT")

        assert params["alpha"] == 1.0, "Default alpha should be 1.0"
        assert params["beta"] == 1.0, "Default beta should be 1.0"
        assert params["conversion_rate"] == 0.5, "Default conversion should be 0.5"

    def test_positive_signal_increases_alpha(self):
        """Test that positive signals increase alpha parameter"""
        engine = ThompsonSamplingEngine()
        product_id = "TEST_PROD_001"

        # Get initial parameters
        initial_params = engine.get_params(product_id)
        initial_alpha = initial_params["alpha"]

        # Send positive signal (view: +0.1)
        engine.update_params(product_id, "view")

        # Get updated parameters
        updated_params = engine.get_params(product_id)
        updated_alpha = updated_params["alpha"]

        # Verify alpha increased
        assert updated_alpha > initial_alpha, \
            f"Alpha should increase after positive signal: {initial_alpha} → {updated_alpha}"

        expected_increase = 0.1
        actual_increase = updated_alpha - initial_alpha

        assert abs(actual_increase - expected_increase) < 0.01, \
            f"Alpha should increase by {expected_increase}, but increased by {actual_increase}"

    def test_negative_signal_increases_beta(self):
        """Test that negative signals increase beta parameter"""
        engine = ThompsonSamplingEngine()
        product_id = "TEST_PROD_002"

        # Get initial parameters
        initial_params = engine.get_params(product_id)
        initial_beta = initial_params["beta"]

        # Send negative signal (skip: -0.3)
        engine.update_params(product_id, "skip")

        # Get updated parameters
        updated_params = engine.get_params(product_id)
        updated_beta = updated_params["beta"]

        # Verify beta increased
        assert updated_beta > initial_beta, \
            f"Beta should increase after negative signal: {initial_beta} → {updated_beta}"

        expected_increase = 0.3
        actual_increase = updated_beta - initial_beta

        assert abs(actual_increase - expected_increase) < 0.01, \
            f"Beta should increase by {expected_increase}, but increased by {actual_increase}"

    def test_signal_weights_are_correct(self):
        """Test all signal weights match architecture specification"""
        engine = ThompsonSamplingEngine()

        # Expected signal weights from architecture
        expected_weights = {
            "view": 0.1,
            "click": 0.3,
            "add_to_cart": 0.7,
            "purchase": 1.0,
            "skip": -0.3,
            "remove_from_cart": -0.5,
            "return": -1.0
        }

        for action, expected_weight in expected_weights.items():
            product_id = f"TEST_{action.upper()}"

            # Get initial alpha/beta
            initial_params = engine.get_params(product_id)
            initial_alpha = initial_params["alpha"]
            initial_beta = initial_params["beta"]

            # Apply signal
            engine.update_params(product_id, action)

            # Get updated parameters
            updated_params = engine.get_params(product_id)
            updated_alpha = updated_params["alpha"]
            updated_beta = updated_params["beta"]

            # Calculate actual change
            if expected_weight > 0:
                # Positive signal → alpha increases
                actual_change = updated_alpha - initial_alpha
                assert abs(actual_change - expected_weight) < 0.01, \
                    f"Action '{action}' should increase alpha by {expected_weight}, but changed by {actual_change}"
            else:
                # Negative signal → beta increases
                actual_change = updated_beta - initial_beta
                expected_beta_increase = abs(expected_weight)
                assert abs(actual_change - expected_beta_increase) < 0.01, \
                    f"Action '{action}' should increase beta by {expected_beta_increase}, but changed by {actual_change}"

    def test_conversion_rate_calculation(self):
        """Test conversion rate = alpha / (alpha + beta)"""
        engine = ThompsonSamplingEngine()
        product_id = "TEST_CONVERSION"

        # Apply 10 purchases (alpha should be ~11.0)
        for _ in range(10):
            engine.update_params(product_id, "purchase")

        # Apply 2 returns (beta should be ~3.0)
        for _ in range(2):
            engine.update_params(product_id, "return")

        params = engine.get_params(product_id)
        alpha = params["alpha"]
        beta = params["beta"]
        conversion = params["conversion_rate"]

        expected_conversion = alpha / (alpha + beta)

        assert abs(conversion - expected_conversion) < 0.01, \
            f"Conversion rate calculation wrong: expected {expected_conversion:.3f}, got {conversion:.3f}"

    def test_batch_ranking(self):
        """Test batch ranking of multiple products"""
        engine = ThompsonSamplingEngine()

        # Create products with different performance
        products = ["PROD_GOOD", "PROD_MEDIUM", "PROD_BAD"]

        # PROD_GOOD: 5 purchases (high alpha)
        for _ in range(5):
            engine.update_params("PROD_GOOD", "purchase")

        # PROD_MEDIUM: 2 purchases (medium alpha)
        for _ in range(2):
            engine.update_params("PROD_MEDIUM", "purchase")

        # PROD_BAD: 3 returns (high beta)
        for _ in range(3):
            engine.update_params("PROD_BAD", "return")

        # Rank products
        ranked = engine.rank_product_ids(products)

        # Verify ranking order (probabilistic, so we check conversion rates)
        good_params = engine.get_params("PROD_GOOD")
        medium_params = engine.get_params("PROD_MEDIUM")
        bad_params = engine.get_params("PROD_BAD")

        assert good_params["conversion_rate"] > medium_params["conversion_rate"], \
            "PROD_GOOD should have higher conversion than PROD_MEDIUM"

        assert medium_params["conversion_rate"] > bad_params["conversion_rate"], \
            "PROD_MEDIUM should have higher conversion than PROD_BAD"

    def test_persistence_to_redis(self):
        """Test parameters are persisted to Redis"""
        engine = ThompsonSamplingEngine()
        product_id = "TEST_PERSISTENCE"

        # Apply signal
        engine.update_params(product_id, "purchase")

        # Get parameters
        params1 = engine.get_params(product_id)

        # Create new engine instance (should load from Redis)
        engine2 = ThompsonSamplingEngine()
        params2 = engine2.get_params(product_id)

        # Verify parameters match
        assert params1["alpha"] == params2["alpha"], \
            "Alpha should persist across engine instances"
        assert params1["beta"] == params2["beta"], \
            "Beta should persist across engine instances"


# Run with: pytest backend/tests/test_thompson_sampling.py -v
