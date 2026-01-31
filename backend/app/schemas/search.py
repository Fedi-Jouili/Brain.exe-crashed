"""
Search and Product Schemas
Product discovery and affordability analysis
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime


class AffordabilityStatus(str, Enum):
    """Product affordability status"""
    AFFORDABLE = "affordable"
    CAUTION = "caution"
    UNAFFORDABLE = "unaffordable"


class SearchType(str, Enum):
    """Type of search query"""
    TEXT = "text"
    IMAGE = "image"
    HYBRID = "hybrid"


class SortOption(str, Enum):
    """Sort options for results"""
    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    AFFORDABILITY = "affordability"
    RATING = "rating"


class SearchFilters(BaseModel):
    """Search filter options"""
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    categories: Optional[list[str]] = None
    brands: Optional[list[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    in_stock_only: bool = True


class SearchRequest(BaseModel):
    """Product search request"""
    query: str = Field(..., min_length=1, max_length=500)
    search_type: SearchType = SearchType.TEXT
    image_url: Optional[str] = None  # For image search
    filters: Optional[SearchFilters] = None
    sort_by: SortOption = SortOption.RELEVANCE
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "wireless headphones",
                "search_type": "text",
                "filters": {
                    "min_price": 50,
                    "max_price": 300,
                    "min_rating": 4.0
                },
                "sort_by": "affordability",
                "page": 1,
                "page_size": 20
            }
        }


class FinancialAnalysis(BaseModel):
    """Backend-computed financial analysis for a product"""
    affordability_status: AffordabilityStatus
    affordability_score: float = Field(..., ge=0, le=100)
    
    # Impact metrics
    price_to_income_ratio: float
    impact_on_dti: float
    impact_on_savings: float
    months_to_save: float
    
    # Financing options
    recommended_financing: Optional[str] = None
    monthly_payment_estimate: Optional[float] = None
    
    # Risk assessment
    risk_factors: list[str]
    approval_likelihood: Optional[str] = None  # "high", "medium", "low"


class ProductResult(BaseModel):
    """Product search result with financial analysis"""
    id: str
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    currency: str = "USD"
    image_url: str
    product_url: str
    brand: Optional[str] = None
    category: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    in_stock: bool = True
    
    # Backend-computed financial analysis
    financial_analysis: FinancialAnalysis
    
    # AI explanation
    ai_summary: str
    why_recommended: Optional[str] = None


class AlternativeProduct(BaseModel):
    """Alternative product suggestion from PathFinder agent"""
    product: ProductResult
    reason: str  # Why this alternative
    savings_vs_original: float
    trade_offs: list[str]


class SearchResponse(BaseModel):
    """Search response with trace"""
    trace_id: str
    request_id: str
    
    # Results
    products: list[ProductResult]
    alternatives: list[AlternativeProduct]  # From PathFinder
    
    # Pagination
    total_results: int
    page: int
    page_size: int
    total_pages: int
    
    # Search metadata
    query_understood: str  # AI interpretation of query
    filters_applied: dict
    search_time_ms: int


class InteractionType(str, Enum):
    """User interaction types for Thompson Sampling"""
    VIEW = "view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    DISMISS = "dismiss"


class InteractionRequest(BaseModel):
    """Record user interaction for ranking optimization"""
    product_id: str
    interaction_type: InteractionType
    trace_id: str
    metadata: Optional[dict] = None


class InteractionResponse(BaseModel):
    """Interaction recorded confirmation"""
    success: bool
    interaction_id: str
    reward_signal: float  # For Thompson Sampling
