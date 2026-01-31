"""
Search Routes
Product discovery with multi-agent processing
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.middleware import require_auth, rate_limit
from app.core.config import settings
from app.schemas.auth import AuthenticatedUser
from app.schemas.search import (
    SearchRequest, SearchResponse,
    InteractionRequest, InteractionResponse, InteractionType
)
from app.schemas.errors import ErrorCode, ErrorResponse
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/search", tags=["Search"])

# Mock profile store (in production, use database)
_profiles_db: dict = {}


def get_profile_for_user(user_id: str):
    """Get user profile from store"""
    return _profiles_db.get(user_id)


@router.post(
    "",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid search query"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        429: {"model": ErrorResponse, "description": "Rate limited"},
        500: {"model": ErrorResponse, "description": "Search failed"}
    }
)
async def search_products(
    request: Request,
    search_request: SearchRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)],
    _: Annotated[None, Depends(rate_limit(settings.RATE_LIMIT_SEARCH, 60))]
):
    """
    Search for products with AI-powered financial analysis.
    
    The search is processed through a multi-agent pipeline:
    1. Discovery Agent - Semantic product search
    2. Financial Analyzer - Affordability assessment
    3. PathFinder - Alternative suggestions
    4. Ranking Agent - Thompson Sampling optimization
    5. Explainer Agent - Human-readable insights
    
    Returns products with financial analysis and a trace_id for debugging.
    """
    try:
        # Get user profile for financial analysis
        profile = get_profile_for_user(current_user.user_id)
        
        # Execute agent pipeline
        response, trace = await orchestrator.search(
            request=search_request,
            user_id=current_user.user_id,
            profile=profile,
            request_id=request.state.request_id
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code=ErrorCode.SEARCH_FAILED,
                message="Search processing failed",
                details={"error": str(e)}
            ).model_dump()
        )


@router.post(
    "/interaction",
    response_model=InteractionResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        400: {"model": ErrorResponse, "description": "Invalid interaction"}
    }
)
async def record_interaction(
    interaction: InteractionRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)]
):
    """
    Record user interaction for ranking optimization.
    
    Interactions feed into the Thompson Sampling algorithm to improve
    future product rankings based on user behavior.
    """
    import uuid
    
    # Calculate reward signal based on interaction type
    reward_map = {
        InteractionType.VIEW: 0.1,
        InteractionType.CLICK: 0.3,
        InteractionType.ADD_TO_CART: 0.6,
        InteractionType.PURCHASE: 1.0,
        InteractionType.DISMISS: -0.2
    }
    
    reward = reward_map.get(interaction.interaction_type, 0)
    
    # In production: Update Redis with Thompson Sampling alpha/beta
    # For now, just acknowledge
    
    return InteractionResponse(
        success=True,
        interaction_id=str(uuid.uuid4()),
        reward_signal=reward
    )


# Export profiles_db for profile router
def set_profile(user_id: str, profile):
    _profiles_db[user_id] = profile


def get_profiles_db():
    return _profiles_db
