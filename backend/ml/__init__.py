"""Machine Learning modules for PriceSense FinCommerce."""

# Lazy imports to avoid heavy dependencies on module load
__all__ = ["ThompsonSamplingEngine", "ComplexityEstimator", "complexity_estimator"]

def __getattr__(name):
    """Lazy import of ML modules"""
    if name == "ThompsonSamplingEngine":
        from .thompson_sampling import ThompsonSamplingEngine
        return ThompsonSamplingEngine
    elif name == "ComplexityEstimator":
        from .complexity_estimator import ComplexityEstimator
        return ComplexityEstimator
    elif name == "complexity_estimator":
        from .complexity_estimator import complexity_estimator
        return complexity_estimator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
