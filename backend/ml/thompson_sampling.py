from typing import Dict, List, Tuple
import threading
import logging
from scipy.stats import beta
import numpy as np

# Use absolute imports from backend root
try:
    from backend.core.config import settings
except ImportError:
    # Fallback for different import contexts
    from core.config import settings

# Setup logging
log = logging.getLogger(__name__)


class ThompsonSamplingEngine:


    def __init__(self):

        self.params_store: Dict[str, Dict[str, float]] = {}
        self.lock = threading.Lock()
        log.info("Thompson Sampling Engine initialized with in-memory storage")

    def get_params(self, product_id: str) -> Dict[str, float]:

        with self.lock:
            if product_id not in self.params_store:
                # Initialize new product with uniform prior (unbiased)
                self.params_store[product_id] = {
                    "alpha": settings.thompson_alpha_init,
                    "beta": settings.thompson_beta_init,
                    "total_interactions": 0
                }
                log.debug(
                    f"Initialized new product {product_id} with "
                    f"α={settings.thompson_alpha_init}, "
                    f"β={settings.thompson_beta_init}"
                )

            params = self.params_store[product_id].copy()

            # Add confidence level
            total = params["total_interactions"]
            if total < 5:
                params["confidence"] = "low"
            elif total < 20:
                params["confidence"] = "medium"
            else:
                params["confidence"] = "high"

        return params

    def sample_score(self, product_id: str) -> float:

        params = self.get_params(product_id)
        alpha = params["alpha"]
        beta_val = params["beta"]

        # Sample from Beta distribution
        score = beta.rvs(alpha, beta_val)

        log.debug(
            f"Sampled score {score:.3f} for {product_id} "
            f"(α={alpha:.2f}, β={beta_val:.2f})"
        )

        return float(score)

    def sample(self, product_id: str) -> float:
        """
        Sample a score for a product using Thompson Sampling (Alias for sample_score).
        
        Args:
            product_id: Product identifier
            
        Returns:
            Sampled probability score [0, 1]
        """
        return self.sample_score(product_id)

    def rank_product_ids(self, product_ids: List[str]) -> List[Tuple[str, float]]:
        """
        Rank product IDs using Thompson Sampling without mutating data.

        This is the PRODUCTION-SAFE method for Agent 3.

        Args:
            product_ids: List of product identifiers to rank

        Returns:
            List of (product_id, thompson_score) tuples,
            sorted by score descending.

        Note:
            - Does NOT mutate any product objects
            - Does NOT attach metadata to products
            - Thread-safe and side-effect free
            - Each call produces different rankings (stochastic sampling)

        Example:
            >>> engine = ThompsonSamplingEngine()
            >>> ranked = engine.rank_product_ids(["LAPTOP-001", "PHONE-002"])
            >>> [("LAPTOP-001", 0.872), ("PHONE-002", 0.543)]
        """
        if not product_ids:
            return []

        # Sample scores for each product ID
        scored_products = []
        for product_id in product_ids:
            # Basic validation
            assert isinstance(product_id, str), f"Product ID must be string, got {type(product_id)}"

            thompson_score = self.sample_score(product_id)
            scored_products.append((product_id, thompson_score))

        # Sort by thompson_score descending
        ranked_tuples = sorted(scored_products, key=lambda x: x[1], reverse=True)

        log.info(f"Ranked {len(product_ids)} products using Thompson Sampling")

        return ranked_tuples

    def rank_products(self, products: List[Dict]) -> List[Dict]:
        """
        Rank products using Thompson Sampling and add RL metadata to product dicts.

        ⚠️  WARNING: TEST / ANALYTICS ONLY ⚠️

        This method MUTATES input product objects by injecting Thompson Sampling
        metadata. It is intended ONLY for:
        - Testing (unit tests, integration tests)
        - Debugging and development
        - Analytics dashboards and reports

        ❌ PRODUCTION AGENTS MUST NOT USE THIS METHOD ❌

        For production use by Agent 3 (Recommender), use rank_product_ids() instead,
        which is pure, non-mutating, and safe for multi-agent orchestration.

        Args:
            products: List of product dictionaries (must have 'product_id' key)

        Returns:
            Ranked list of products with added Thompson Sampling fields:
            - thompson_score: Sampled probability [0, 1]
            - thompson_alpha: Current alpha parameter
            - thompson_beta: Current beta parameter
            - thompson_confidence: Confidence level (low/medium/high)
            - conversion_rate: Estimated conversion probability

        Side Effects:
            ⚠️  MUTATES each product dictionary by adding Thompson Sampling fields
        """
        # WARNING:
        # This method mutates product objects and is intended ONLY for
        # testing, debugging, or analytics.
        # Production agents MUST NOT use this method.
        # Validate all products have product_id
        for product in products:
            if "product_id" not in product:
                log.error(f"Product missing 'product_id' key: {product}")
                raise KeyError("All products must have 'product_id' key")

        # Sample scores and add metadata to each product
        for product in products:
            product_id = product["product_id"]

            # Get current parameters
            params = self.get_params(product_id)

            # Sample Thompson score
            product["thompson_score"] = self.sample_score(product_id)

            # Add RL metadata for analytics
            product["thompson_alpha"] = params["alpha"]
            product["thompson_beta"] = params["beta"]
            product["thompson_confidence"] = self.get_confidence_level(product_id)
            product["conversion_rate"] = params["alpha"] / (params["alpha"] + params["beta"])

        # Sort by thompson_score descending
        ranked_products = sorted(
            products,
            key=lambda p: p["thompson_score"],
            reverse=True
        )

        log.info(f"Ranked {len(products)} products using Thompson Sampling")

        return ranked_products

    def update_params(self, product_id: str, action: str) -> None:

        # Validate action exists in signal weights
        if action not in settings.signal_weights:
            valid_actions = list(settings.signal_weights.keys())
            log.error(
                f"Invalid action '{action}' for {product_id}. "
                f"Valid actions: {valid_actions}"
            )
            raise ValueError(
                f"Action '{action}' not found in signal_weights. "
                f"Valid actions: {valid_actions}"
            )

        # Get signal weight from centralized config
        weight = settings.signal_weights[action]

        # Get current params (initializes if new product)
        params = self.get_params(product_id)

        with self.lock:
            # Update alpha or beta based on signal polarity
            if weight > 0:
                # Positive signal: increase alpha (success count)
                self.params_store[product_id]["alpha"] += weight
            elif weight < 0:
                # Negative signal: increase beta (failure count)
                self.params_store[product_id]["beta"] += abs(weight)

            # Increment total interactions
            self.params_store[product_id]["total_interactions"] += 1

            # Get updated values for logging
            alpha = self.params_store[product_id]["alpha"]
            beta_val = self.params_store[product_id]["beta"]
            total = self.params_store[product_id]["total_interactions"]

        log.info(
            f"Updated {product_id}: action={action}, weight={weight:+.1f}, "
            f"α={alpha:.2f}, β={beta_val:.2f}, interactions={total}"
        )

    def get_confidence_level(self, product_id: str) -> str:

        params = self.get_params(product_id)
        total = params["total_interactions"]

        if total < 5:
            return "low"
        elif total < 20:
            return "medium"
        else:
            return "high"

    def get_all_stats(self) -> Dict[str, Dict]:

        with self.lock:
            return self.params_store.copy()

    def reset_product(self, product_id: str) -> None:

        with self.lock:
            self.params_store[product_id] = {
                "alpha": settings.thompson_alpha_init,
                "beta": settings.thompson_beta_init,
                "total_interactions": 0
            }

        log.info(f"Reset {product_id} to initial parameters")

    def export_state(self) -> Dict:

        with self.lock:
            state = self.params_store.copy()

        log.info(f"Exported state for {len(state)} products")

        return state

    def import_state(self, state: Dict) -> None:

        with self.lock:
            self.params_store = state.copy()

        log.info(f"Imported state for {len(state)} products")
