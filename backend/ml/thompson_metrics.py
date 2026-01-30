"""
Thompson Sampling Observability Module

Provides metrics, monitoring, and debugging capabilities for Thompson Sampling.
"""
from typing import Dict, Any, List
import logging
from ml.thompson_sampling import ThompsonSamplingEngine

logger = logging.getLogger(__name__)


class ThompsonMetrics:
    """
    Observability layer for Thompson Sampling.

    Provides:
    - Aggregate statistics across all products
    - Confidence distribution
    - Learning rate tracking
    """

    def __init__(self, engine: ThompsonSamplingEngine):
        """
        Initialize metrics tracker.

        Args:
            engine: Thompson Sampling engine instance
        """
        self.engine = engine
        self.interaction_count = 0
        self.last_metric_time = self._get_timestamp()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive Thompson Sampling statistics.

        Returns:
            Dictionary containing:
            - products_tracked: Total products with parameters
            - avg_alpha: Mean α across all products
            - avg_beta: Mean β across all products
            - avg_conversion: Mean α/(α+β)
            - confidence: Distribution of confidence levels
        """
        try:
            # Get all product IDs from in-memory store
            all_product_ids = list(self.engine.params_store.keys())

            if not all_product_ids:
                return {
                    "products_tracked": 0,
                    "avg_alpha": 1.0,
                    "avg_beta": 1.0,
                    "avg_conversion": 0.5,
                    "confidence": {
                        "low": 0,
                        "medium": 0,
                        "high": 0
                    }
                }

            # Collect parameters for all products
            alphas = []
            betas = []
            conversions = []
            confidence_counts = {"low": 0, "medium": 0, "high": 0}

            for product_id in all_product_ids:
                params = self.engine.get_params(product_id)
                alpha = params["alpha"]
                beta = params["beta"]

                alphas.append(alpha)
                betas.append(beta)
                conversions.append(alpha / (alpha + beta))

                # Get confidence level
                confidence = params["confidence"]
                confidence_counts[confidence] += 1

            # Calculate averages
            avg_alpha = sum(alphas) / len(alphas)
            avg_beta = sum(betas) / len(betas)
            avg_conversion = sum(conversions) / len(conversions)

            stats = {
                "products_tracked": len(all_product_ids),
                "avg_alpha": round(avg_alpha, 2),
                "avg_beta": round(avg_beta, 2),
                "avg_conversion": round(avg_conversion, 3),
                "confidence": confidence_counts
            }

            logger.info(f"Thompson stats: {len(all_product_ids)} products, "
                       f"avg_conversion={avg_conversion:.3f}")

            return stats

        except Exception as e:
            logger.error(f"Error calculating Thompson stats: {e}")
            return {
                "products_tracked": 0,
                "avg_alpha": 1.0,
                "avg_beta": 1.0,
                "avg_conversion": 0.5,
                "confidence": {"low": 0, "medium": 0, "high": 0},
                "error": str(e)
            }

    def track_interaction(self, product_id: str, action: str):
        """
        Track a user interaction for rate monitoring.

        Args:
            product_id: Product being interacted with
            action: Type of interaction
        """
        self.interaction_count += 1

        # Log meaningful events only
        if self.interaction_count % 100 == 0:
            logger.info(f"Thompson interactions: {self.interaction_count} total")

    def get_product_stats(self, product_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a single product.

        Args:
            product_id: Product to get stats for

        Returns:
            Product-specific Thompson parameters
        """
        try:
            params = self.engine.get_params(product_id)

            return {
                "product_id": product_id,
                "alpha": params["alpha"],
                "beta": params["beta"],
                "conversion_rate": round(params["alpha"] / (params["alpha"] + params["beta"]), 3),
                "confidence": params["confidence"],
                "total_interactions": params["total_interactions"]
            }

        except Exception as e:
            logger.error(f"Error getting product stats for {product_id}: {e}")
            return {
                "product_id": product_id,
                "error": str(e)
            }

    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        import time
        return int(time.time() * 1000)


# Singleton instance (will be initialized in main.py)
_metrics_instance = None


def get_metrics(engine: ThompsonSamplingEngine = None) -> ThompsonMetrics:
    """
    Get or create the global metrics instance.

    Args:
        engine: Thompson Sampling engine (required on first call)

    Returns:
        ThompsonMetrics instance
    """
    global _metrics_instance

    if _metrics_instance is None:
        if engine is None:
            raise ValueError("Engine required for first metrics initialization")
        _metrics_instance = ThompsonMetrics(engine)

    return _metrics_instance
