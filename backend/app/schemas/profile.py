"""
Financial Profile Schemas
User financial data for affordability analysis
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
from datetime import datetime


class RiskTolerance(str, Enum):
    """User's risk tolerance level"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class CreditScoreRange(str, Enum):
    """Credit score ranges"""
    POOR = "poor"          # 300-579
    FAIR = "fair"          # 580-669
    GOOD = "good"          # 670-739
    VERY_GOOD = "very_good"  # 740-799
    EXCELLENT = "excellent"  # 800-850


class ProfileCreateRequest(BaseModel):
    """Create/update financial profile"""
    monthly_income: float = Field(..., gt=0, description="Monthly income in USD")
    monthly_expenses: float = Field(..., ge=0, description="Fixed monthly expenses")
    current_debt: float = Field(default=0, ge=0, description="Total current debt")
    savings: float = Field(default=0, ge=0, description="Total savings")
    credit_score_range: CreditScoreRange
    risk_tolerance: RiskTolerance
    
    @field_validator("monthly_expenses")
    @classmethod
    def validate_expenses(cls, v: float, info) -> float:
        # Will be validated against income in the service layer
        return v


class ProfileResponse(BaseModel):
    """Financial profile response"""
    id: str
    user_id: str
    monthly_income: float
    monthly_expenses: float
    current_debt: float
    savings: float
    credit_score_range: CreditScoreRange
    risk_tolerance: RiskTolerance
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FinancialHealthResponse(BaseModel):
    """Computed financial health metrics (from backend only)"""
    user_id: str
    
    # Key ratios
    debt_to_income_ratio: float = Field(..., description="DTI ratio (0-1)")
    disposable_income: float = Field(..., description="Monthly disposable income")
    safe_purchase_limit: float = Field(..., description="Max safe single purchase")
    emergency_fund_months: float = Field(..., description="Months of expenses covered by savings")
    
    # Health indicators
    dti_status: str  # "healthy", "warning", "critical"
    emergency_fund_status: str  # "healthy", "warning", "critical"
    overall_health: str  # "excellent", "good", "fair", "poor"
    
    # Recommendations
    recommendations: list[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "debt_to_income_ratio": 0.28,
                "disposable_income": 1500.0,
                "safe_purchase_limit": 750.0,
                "emergency_fund_months": 4.2,
                "dti_status": "healthy",
                "emergency_fund_status": "warning",
                "overall_health": "good",
                "recommendations": [
                    "Consider building emergency fund to 6 months",
                    "Your DTI is healthy - you have room for planned purchases"
                ]
            }
        }
