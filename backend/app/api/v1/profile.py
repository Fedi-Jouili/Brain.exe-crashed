"""
Profile Routes
Financial profile management
"""
from typing import Annotated
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.middleware import require_auth
from app.schemas.auth import AuthenticatedUser
from app.schemas.profile import (
    ProfileCreateRequest, ProfileResponse, FinancialHealthResponse
)
from app.schemas.errors import ErrorCode, ErrorResponse
from app.api.v1.auth import get_users_db
from app.api.v1.search import set_profile, get_profiles_db

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid profile data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def create_or_update_profile(
    profile_data: ProfileCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)]
):
    """
    Create or update user's financial profile.
    
    This profile is used by the Financial Analyzer agent to assess
    product affordability and provide personalized recommendations.
    """
    now = datetime.now(timezone.utc)
    
    # Check if profile exists
    existing = get_profiles_db().get(current_user.user_id)
    
    profile = ProfileResponse(
        id=existing.id if existing else str(uuid.uuid4()),
        user_id=current_user.user_id,
        monthly_income=profile_data.monthly_income,
        monthly_expenses=profile_data.monthly_expenses,
        current_debt=profile_data.current_debt,
        savings=profile_data.savings,
        credit_score_range=profile_data.credit_score_range,
        risk_tolerance=profile_data.risk_tolerance,
        created_at=existing.created_at if existing else now,
        updated_at=now
    )
    
    # Store profile
    set_profile(current_user.user_id, profile)
    
    # Update user's has_profile flag
    users_db = get_users_db()
    for email, user in users_db.items():
        if user["id"] == current_user.user_id:
            user["has_profile"] = True
            break
    
    return profile


@router.get(
    "",
    response_model=ProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Profile not found"}
    }
)
async def get_profile(
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)]
):
    """
    Get current user's financial profile.
    """
    profile = get_profiles_db().get(current_user.user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code=ErrorCode.PROFILE_NOT_FOUND,
                message="Financial profile not found. Please create one first."
            ).model_dump()
        )
    
    return profile


@router.get(
    "/health",
    response_model=FinancialHealthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Profile not found"}
    }
)
async def get_financial_health(
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)]
):
    """
    Get computed financial health metrics.
    
    All calculations are performed server-side. The frontend
    should never compute these values.
    """
    profile = get_profiles_db().get(current_user.user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code=ErrorCode.PROFILE_NOT_FOUND,
                message="Financial profile not found"
            ).model_dump()
        )
    
    # Calculate metrics (backend-only logic)
    monthly_income = profile.monthly_income
    monthly_expenses = profile.monthly_expenses
    current_debt = profile.current_debt
    savings = profile.savings
    
    # DTI calculation (annual)
    annual_income = monthly_income * 12
    dti_ratio = current_debt / annual_income if annual_income > 0 else 0
    
    # Disposable income
    disposable = monthly_income - monthly_expenses
    
    # Safe purchase limit (50% of monthly disposable)
    safe_limit = disposable * 0.5 if disposable > 0 else 0
    
    # Emergency fund months
    emergency_months = savings / monthly_expenses if monthly_expenses > 0 else 0
    
    # Status determinations
    dti_status = "healthy" if dti_ratio < 0.36 else "warning" if dti_ratio < 0.43 else "critical"
    ef_status = "healthy" if emergency_months >= 6 else "warning" if emergency_months >= 3 else "critical"
    
    # Overall health
    if dti_status == "healthy" and ef_status == "healthy":
        overall = "excellent"
    elif dti_status == "critical" or ef_status == "critical":
        overall = "poor"
    elif dti_status == "warning" or ef_status == "warning":
        overall = "fair"
    else:
        overall = "good"
    
    # Recommendations
    recommendations = []
    if emergency_months < 6:
        recommendations.append(f"Build emergency fund to 6 months (currently {emergency_months:.1f})")
    if dti_ratio > 0.36:
        recommendations.append(f"Consider debt reduction - DTI at {dti_ratio:.1%}")
    if disposable < monthly_income * 0.2:
        recommendations.append("Look for ways to increase disposable income")
    if not recommendations:
        recommendations.append("Your financial health is strong - maintain current habits")
    
    return FinancialHealthResponse(
        user_id=current_user.user_id,
        debt_to_income_ratio=round(dti_ratio, 3),
        disposable_income=round(disposable, 2),
        safe_purchase_limit=round(safe_limit, 2),
        emergency_fund_months=round(emergency_months, 1),
        dti_status=dti_status,
        emergency_fund_status=ef_status,
        overall_health=overall,
        recommendations=recommendations
    )
