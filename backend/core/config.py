"""
Configuration settings for PriceSense
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    google_api_key: Optional[str] = None  # Only required for Agent 4 (Explainer)
    openai_api_key: Optional[str] = None

    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_collection_products: str = "products"
    qdrant_collection_users: str = "users"
    qdrant_collection_financial_kb: str = "financial_kb"
    qdrant_collection_transactions: str = "transactions"

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_cache_ttl: int = 3600  # 1 hour

    # Embedding Configuration
    embedding_model: str = "openai/clip-vit-base-patch32"
    embedding_dimension: int = 512
    chunk_size: int = 512

    # LLM Configuration
    # DO NOT use gemini-1.5-* models — not supported for this API key
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 500

    # Routing Configuration
    complexity_threshold_fast: float = 0.3
    complexity_threshold_smart: float = 0.7

    # Thompson Sampling
    thompson_alpha_init: float = 1.0
    thompson_beta_init: float = 1.0

    # Signal Weights
    signal_weight_view: float = 0.1
    signal_weight_click: float = 0.3
    signal_weight_add_to_cart: float = 0.7
    signal_weight_purchase: float = 1.0
    signal_weight_skip: float = -0.3
    signal_weight_remove_from_cart: float = -0.5
    signal_weight_return: float = -1.0

    # K-Means Configuration
    kmeans_n_clusters: int = 10

    # Search Configuration
    search_top_k: int = 50
    final_recommendations: int = 10
    alternatives_per_product: int = 3

    # Financial Rules
    dti_threshold: float = 0.43  # 43%
    pti_threshold: float = 0.15  # 15%
    disposable_income_ratio: float = 0.30  # 30%
    emergency_fund_months_min: int = 3
    emergency_fund_months_max: int = 6
    credit_score_threshold: int = 650

    # RAGAS Targets
    ragas_context_precision_target: float = 0.85
    ragas_context_recall_target: float = 0.80
    ragas_faithfulness_target: float = 0.90
    ragas_answer_relevancy_target: float = 0.85

    # Performance
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_url: Optional[str] = None
    streamlit_port: Optional[int] = None

    @property
    def signal_weights(self) -> dict:
        """
        Get all signal weights as a dictionary.

        Returns:
            Dictionary mapping action name to weight value
        """
        return {
            "view": self.signal_weight_view,
            "click": self.signal_weight_click,
            "add_to_cart": self.signal_weight_add_to_cart,
            "purchase": self.signal_weight_purchase,
            "skip": self.signal_weight_skip,
            "remove_from_cart": self.signal_weight_remove_from_cart,
            "return": self.signal_weight_return,
        }

    class Config:
        # Try multiple .env locations to support different run contexts
        env_file = None  # Will be set dynamically
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


# Global settings instance
# Try to find .env file in multiple locations
import os
from pathlib import Path

def _find_env_file():
    """Find .env file in project root"""
    # Try current directory
    if Path(".env").exists():
        return ".env"

    # Try parent directory (when running from backend/)
    if Path("../.env").exists():
        return "../.env"

    # Try project root (when running from backend/scripts/)
    backend_dir = Path(__file__).parent.parent
    root_env = backend_dir.parent / ".env"
    if root_env.exists():
        return str(root_env)

    return None

_env_file = _find_env_file()
if _env_file:
    Settings.model_config['env_file'] = _env_file

settings = Settings()
