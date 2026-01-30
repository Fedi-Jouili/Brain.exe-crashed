"""
FastAPI backend for PriceSense multi-agent recommendation system

Endpoints:
- POST /api/search - Main product search and recommendation
- POST /api/feedback/action - User action feedback for Thompson Sampling
- GET /api/health - System health check
- GET /api/cache/stats - Cache statistics
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
from datetime import datetime

from models.schemas import UserProfile
from models.state import AgentState
from models.api_models import (
    SearchRequest, SearchResponse, RecommendRequest,
    ProductResponse, RecommendationResponse,
    HealthResponse, ErrorResponse,
    AffordabilityResponse, ExplanationResponse
)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lazy import flags - will import when actually needed to avoid startup crashes
WORKFLOW_AVAILABLE = False
run_recommendation_pipeline = None
QDRANT_AVAILABLE = False
qdrant_manager = None
settings = None

# Try importing basic config
try:
    from core.config import settings
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    settings = None

# Initialize FastAPI app
app = FastAPI(
    title="PriceSense API",
    description="Multi-agent AI recommendation system for e-commerce",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Track server start time for uptime
_server_start_time = time.time()

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS - Imported from models.api_models
# ============================================================================
# Additional models for feedback and cache operations

class FeedbackRequest(BaseModel):
    """Request model for user action feedback"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product identifier")
    action: str = Field(..., description="Action type: view, click, purchase, like, dislike")
    query: Optional[str] = Field(None, description="Original search query")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="User rating if applicable")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "product_id": "prod_456",
                "action": "purchase",
                "query": "gaming laptop",
                "rating": 4.5
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    success: bool
    message: str
    thompson_updated: bool = False


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    cache_enabled: bool
    total_keys: int
    memory_usage_mb: Optional[float] = None


class InteractionRequest(BaseModel):
    """Request model for user interaction tracking"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product identifier")
    action: str = Field(..., description="Action type: view, click, add_to_cart, purchase, skip, remove_from_cart, return")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "USER123",
                "product_id": "PROD0042",
                "action": "purchase"
            }
        }


class InteractionResponse(BaseModel):
    """Response model for interaction tracking"""
    product_id: str
    alpha: float
    beta: float
    conversion_rate: float
    confidence: str


class ThompsonStatsResponse(BaseModel):
    """Response model for Thompson Sampling statistics"""
    products_tracked: int
    avg_alpha: float
    avg_beta: float
    avg_conversion: float
    confidence: Dict[str, int]


# ============================================================================
# LAZY IMPORT HELPERS
# ============================================================================

def get_workflow():
    """Lazy import of workflow - only loads when actually needed"""
    global WORKFLOW_AVAILABLE, run_recommendation_pipeline
    if not WORKFLOW_AVAILABLE and run_recommendation_pipeline is None:
        try:
            from orchestration.workflow import run_recommendation_pipeline as pipeline
            run_recommendation_pipeline = pipeline
            WORKFLOW_AVAILABLE = True
            logger.info("LangGraph workflow loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LangGraph workflow: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LangGraph workflow not available. Python 3.14 compatibility issues with dependencies (qdrant-client, torchvision). Recommend Python 3.11 or 3.12. Error: {str(e)}"
            )
    return run_recommendation_pipeline

def get_qdrant():
    """Lazy import of Qdrant client - only loads when actually needed"""
    global QDRANT_AVAILABLE, qdrant_manager
    if not QDRANT_AVAILABLE and qdrant_manager is None:
        try:
            from core.qdrant_client import qdrant_manager as qm
            qdrant_manager = qm
            QDRANT_AVAILABLE = True
            logger.info("Qdrant client loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Qdrant client: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Qdrant database not available. Python 3.14 compatibility issues with sqlite3. Recommend Python 3.11 or 3.12. Error: {str(e)}"
            )
    return qdrant_manager


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "PriceSense API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    System health check

    Returns status of all critical services:
    - Qdrant (vector database)
    - Redis (Thompson Sampling state)
    - LangGraph workflow
    - Agents (all 5 agents)
    """
    services = {}

    # Check Qdrant (lazy load)
    try:
        qm = get_qdrant()
        collections = qm.client.get_collections()
        services["qdrant"] = "healthy"
    except HTTPException as e:
        services["qdrant"] = f"unavailable: Python 3.14 compatibility issue"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        services["qdrant"] = f"unhealthy: {str(e)}"

    # Check Redis (Thompson Sampling)
    try:
        from core.redis_client import redis_manager
        redis_manager.client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = f"unhealthy: {str(e)}"

    # Check LangGraph workflow (lazy load test)
    try:
        workflow = get_workflow()
        services["langgraph_workflow"] = "healthy"
        services["agent1_discovery"] = "healthy"
        services["agent2_financial"] = "healthy"
        services["agent2_5_pathfinder"] = "healthy"
        services["agent3_recommender"] = "healthy"
        services["agent4_explainer"] = "healthy"
    except HTTPException as e:
        services["langgraph_workflow"] = "unavailable: Python 3.14 compatibility issue"
        services["agents"] = "unavailable (workflow dependency failed)"
    except Exception as e:
        services["langgraph_workflow"] = f"unhealthy: {str(e)}"
        services["agents"] = "unavailable"

    # Overall status
    all_healthy = all("healthy" in status for status in services.values())
    overall_status = "healthy" if all_healthy else "degraded"

    # Calculate uptime
    uptime = time.time() - _server_start_time

    return HealthResponse(
        status=overall_status,
        services=services,
        version="1.0.0",
        uptime_seconds=uptime
    )


@app.post("/api/recommend", response_model=SearchResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendRequest):
    """
    Simplified recommendation endpoint (no complex query needed)

    Use this when you have a user profile and want recommendations based on:
    - User's budget and financial profile
    - Optional category filter
    - Optional max price constraint

    This endpoint uses the same LangGraph workflow as /api/search but with
    a simpler interface focused on user-based recommendations.
    """
    start_time = time.time()

    try:
        # Build a query from the request
        query_parts = []
        if request.category:
            query_parts.append(request.category)
        if request.max_price:
            query_parts.append(f"under ${request.max_price}")

        query = " ".join(query_parts) if query_parts else "recommended products"

        logger.info(f"Recommendation request for user={request.user_id}, query='{query}'")

        # Use LangGraph workflow
        result_state = run_recommendation_pipeline(
            query=query,
            user_profile=UserProfile(
                user_id=request.user_id,
                monthly_income=0.0,  # Will be loaded from user profile service
                credit_score=0  # Will be loaded from user profile service
            )
        )

        total_time = int((time.time() - start_time) * 1000)

        # Format recommendations
        recommendations = []
        for i, rec in enumerate(result_state.get('final_recommendations', [])[:request.top_k], 1):
            product = rec['product']

            product_response = ProductResponse(
                product_id=product.get('product_id') or product.get('id'),
                name=product.get('name', 'Unknown Product'),
                price=float(product.get('price', 0.0)),
                category=product.get('category'),
                brand=product.get('brand'),
                rating=product.get('rating'),
                in_stock=product.get('in_stock', True),
                description=product.get('description'),
                image_url=product.get('image_url'),
                financing_available=product.get('financing_available', False)
            )

            affordability_data = rec.get('affordability')
            affordability = None
            if affordability_data:
                affordability = AffordabilityResponse(
                    can_afford_cash=affordability_data.get('can_afford_cash', False),
                    can_afford_financing=affordability_data.get('can_afford_financing', False),
                    risk_level=affordability_data.get('risk_level', 'unknown'),
                    recommendation=affordability_data.get('recommendation', ''),
                    cash_analysis=affordability_data.get('cash_analysis'),
                    financing_paths=affordability_data.get('financing_paths', [])
                )

            explanation_data = rec.get('explanation', {})
            if isinstance(explanation_data, str):
                explanation_data = {'text': explanation_data}

            explanation = ExplanationResponse(
                text=explanation_data.get('text', ''),
                trust=explanation_data.get('trust', 0.0),
                verified=explanation_data.get('verified', False),
                violations=explanation_data.get('violations', []),
                used_llm=explanation_data.get('used_llm', False),
                type=explanation_data.get('type', 'template')
            )

            recommendations.append(RecommendationResponse(
                rank=i,
                product=product_response,
                affordability=affordability,
                explanation=explanation,
                scores=rec.get('scores', {}),
                final_score=rec.get('final_score', 0.0)
            ))

        metadata = {
            'total_candidates': len(result_state.get('candidate_products', [])),
            'affordable_count': len(result_state.get('affordable_products', [])),
            'execution_time_ms': total_time
        }

        return SearchResponse(
            query=query,
            user_id=request.user_id,
            recommendations=recommendations,
            metadata=metadata,
            errors=result_state.get('errors', []),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Recommendation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )


@app.get("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: str):
    """
    Get detailed information about a specific product

    Returns:
    - Complete product details from Qdrant vector database
    - In-stock status
    - Financing availability
    - Rating and reviews count
    """
    try:
        # Lazy load Qdrant client
        qm = get_qdrant()

        # Search for product by ID in Qdrant
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        search_result = qm.client.scroll(
            collection_name="products",
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="product_id",
                        match=MatchValue(value=product_id)
                    )
                ]
            ),
            limit=1
        )

        if not search_result[0]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )

        product_point = search_result[0][0]
        product = product_point.payload

        return ProductResponse(
            product_id=product.get('product_id') or product.get('id'),
            name=product.get('name', 'Unknown Product'),
            price=float(product.get('price', 0.0)),
            category=product.get('category'),
            brand=product.get('brand'),
            rating=product.get('rating'),
            num_reviews=product.get('num_reviews'),
            in_stock=product.get('in_stock', True),
            description=product.get('description'),
            image_url=product.get('image_url'),
            financing_available=product.get('financing_available', False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product: {str(e)}"
        )


@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_products(request: SearchRequest):
    """
    Main product search and recommendation endpoint using LangGraph workflow

    Workflow:
    1. Agent 1 (Discovery): Semantic search for candidate products
    2. Agent 2 (Financial): Affordability analysis
    3. Agent 2.5 (Pathfinder): Alternative budget paths (if all unaffordable)
    4. Agent 3 (Recommender): Multi-armed bandit ranking with collaborative filtering
    5. Agent 4 (Explainer): LLM-generated explanations with fact verification

    Returns ranked recommendations with:
    - Product details
    - Affordability analysis
    - Verified explanations with trust scores
    - Cluster-based alternatives
    """
    start_time = time.time()

    try:
        logger.info(f"Search request: '{request.query}' (user_profile: {request.user_profile is not None})")

        # Lazy load workflow - will raise HTTPException if unavailable
        workflow = get_workflow()

        # Use LangGraph workflow for complete pipeline
        result_state = workflow(
            query=request.query,
            user_profile=request.user_profile
        )

        # Calculate total execution time
        total_time = int((time.time() - start_time) * 1000)

        # Format recommendations from final state
        recommendations = []
        for i, rec in enumerate(result_state.get('final_recommendations', [])[:request.max_results], 1):
            product = rec['product']

            # Build product response
            product_response = ProductResponse(
                product_id=product.get('product_id') or product.get('id'),
                name=product.get('name', 'Unknown Product'),
                price=float(product.get('price', 0.0)),
                category=product.get('category'),
                brand=product.get('brand'),
                rating=product.get('rating'),
                in_stock=product.get('in_stock', True),
                description=product.get('description'),
                image_url=product.get('image_url'),
                financing_available=product.get('financing_available', False)
            )

            # Build affordability response
            affordability_data = rec.get('affordability')
            affordability = None
            if affordability_data:
                affordability = AffordabilityResponse(
                    can_afford_cash=affordability_data.get('can_afford_cash', False),
                    can_afford_financing=affordability_data.get('can_afford_financing', False),
                    risk_level=affordability_data.get('risk_level', 'unknown'),
                    recommendation=affordability_data.get('recommendation', ''),
                    cash_analysis=affordability_data.get('cash_analysis'),
                    financing_paths=affordability_data.get('financing_paths', [])
                )

            # Build explanation response
            explanation_data = rec.get('explanation', {})
            if isinstance(explanation_data, str):
                explanation_data = {'text': explanation_data}

            explanation = ExplanationResponse(
                text=explanation_data.get('text', ''),
                trust=explanation_data.get('trust', 0.0),
                verified=explanation_data.get('verified', False),
                violations=explanation_data.get('violations', []),
                used_llm=explanation_data.get('used_llm', False),
                type=explanation_data.get('type', 'template')
            )

            # Build recommendation response
            recommendations.append(RecommendationResponse(
                rank=i,
                product=product_response,
                affordability=affordability,
                explanation=explanation,
                scores=rec.get('scores', {}),
                final_score=rec.get('final_score', 0.0)
            ))

        # Build metadata
        metadata = {
            'total_candidates': len(result_state.get('candidate_products', [])),
            'affordable_count': len(result_state.get('affordable_products', [])),
            'used_pathfinder': not result_state.get('all_unaffordable', True),
            'execution_time_ms': total_time,
            'agent_timings': {
                'discovery': result_state.get('search_time_ms', 0),
                'financial': result_state.get('financial_analysis_time_ms', 0),
                'pathfinder': result_state.get('pathfinder_time_ms', 0),
                'recommender': result_state.get('recommender_time_ms', 0),
                'explainer': result_state.get('explainer_time_ms', 0)
            }
        }

        return SearchResponse(
            query=request.query,
            user_id=request.user_profile.user_id if request.user_profile else 'anonymous',
            recommendations=recommendations,
            metadata=metadata,
            errors=result_state.get('errors', []),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/api/feedback/action", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user action feedback for Thompson Sampling

    Actions affect future recommendations:
    - purchase: Strong positive signal (+1.0 reward)
    - like: Positive signal (+0.5 reward)
    - click: Weak positive signal (+0.1 reward)
    - view: Neutral signal (exploration)
    - dislike: Negative signal (-0.5 reward)

    This updates the Thompson Sampling beta distribution for the product.
    """
    try:
        logger.info(f"Feedback: user={request.user_id}, product={request.product_id}, action={request.action}")

        # Map action to reward
        reward_map = {
            "purchase": 1.0,
            "like": 0.5,
            "click": 0.1,
            "view": 0.0,
            "dislike": -0.5
        }

        reward = reward_map.get(request.action.lower(), 0.0)

        # Store transaction in Qdrant
        try:
            transaction_data = {
                "user_id": request.user_id,
                "product_id": request.product_id,
                "action": request.action,
                "query": request.query,
                "rating": request.rating,
                "reward": reward,
                "timestamp": datetime.utcnow().isoformat()
            }

            qdrant_manager.store_transaction(**transaction_data)
            logger.info(f"Stored transaction: {transaction_data}")

        except Exception as e:
            logger.error(f"Failed to store transaction: {e}")

        # Update Thompson Sampling (if positive action)
        thompson_updated = False
        if reward > 0:
            try:
                from core.redis_client import redis_manager

                # Get current parameters
                key = f"thompson:{request.product_id}"
                alpha = float(redis_manager.client.hget(key, "alpha") or 1.0)
                beta = float(redis_manager.client.hget(key, "beta") or 1.0)

                # Update based on reward
                if reward >= 0.5:  # Strong positive
                    alpha += 1.0
                else:  # Weak positive
                    alpha += 0.5
                    beta += 0.5

                # Store updated parameters
                redis_manager.client.hset(key, "alpha", alpha)
                redis_manager.client.hset(key, "beta", beta)

                thompson_updated = True
                logger.info(f"Thompson updated: {request.product_id} -> alpha={alpha}, beta={beta}")

            except Exception as e:
                logger.error(f"Failed to update Thompson Sampling: {e}")

        return FeedbackResponse(
            success=True,
            message=f"Feedback recorded for {request.action} on {request.product_id}",
            thompson_updated=thompson_updated
        )

    except Exception as e:
        logger.error(f"Feedback submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )


@app.get("/api/cache/stats", response_model=CacheStatsResponse, tags=["Cache"])
async def get_cache_stats():
    """
    Get cache statistics

    Returns information about the Redis cache used for:
    - Thompson Sampling parameters
    - Cached search results (future)
    """
    try:
        from core.redis_client import redis_manager

        # Get number of keys
        total_keys = redis_manager.client.dbsize()

        # Get memory usage (if available)
        try:
            info = redis_manager.client.info("memory")
            memory_mb = info.get("used_memory", 0) / (1024 * 1024)
        except:
            memory_mb = None

        return CacheStatsResponse(
            cache_enabled=True,
            total_keys=total_keys,
            memory_usage_mb=memory_mb
        )

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return CacheStatsResponse(
            cache_enabled=False,
            total_keys=0,
            memory_usage_mb=None
        )


@app.post("/api/interact", response_model=InteractionResponse, tags=["Thompson Sampling"])
async def track_interaction(request: InteractionRequest):
    """
    Track user interaction for Thompson Sampling learning

    Valid actions:
    - view: User viewed product (+0.1)
    - click: User clicked product (+0.3)
    - add_to_cart: User added to cart (+0.7)
    - purchase: User purchased product (+1.0)
    - skip: User skipped product (-0.3)
    - remove_from_cart: User removed from cart (-0.5)
    - return: User returned product (-1.0)

    This endpoint:
    1. Validates input
    2. Updates Thompson Sampling parameters
    3. Persists to Redis
    4. Returns updated statistics

    Thread-safe and idempotent.
    """
    try:
        # Validate action
        valid_actions = {"view", "click", "add_to_cart", "purchase", "skip", "remove_from_cart", "return"}
        if request.action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )

        # Initialize Thompson Sampling engine
        from ml.thompson_sampling import ThompsonSamplingEngine
        from ml.thompson_metrics import get_metrics

        engine = ThompsonSamplingEngine()

        # Update parameters based on action
        engine.update_params(request.product_id, request.action)

        # Track interaction for metrics
        metrics = get_metrics(engine)
        metrics.track_interaction(request.product_id, request.action)

        # Get updated parameters
        params = engine.get_params(request.product_id)

        # Log meaningful event
        if request.action in {"purchase", "return"}:
            logger.info(f"Thompson interaction: user={request.user_id}, "
                       f"product={request.product_id}, action={request.action}, "
                       f"α={params['alpha']:.2f}, β={params['beta']:.2f}")

        # Return updated stats
        return InteractionResponse(
            product_id=request.product_id,
            alpha=params["alpha"],
            beta=params["beta"],
            conversion_rate=round(params["alpha"] / (params["alpha"] + params["beta"]), 3),
            confidence=params["confidence"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track interaction: {str(e)}"
        )


@app.get("/api/thompson/stats", response_model=ThompsonStatsResponse, tags=["Thompson Sampling"])
async def get_thompson_stats():
    """
    Get Thompson Sampling statistics across all products

    Returns:
    - products_tracked: Total number of products being tracked
    - avg_alpha: Average α parameter
    - avg_beta: Average β parameter
    - avg_conversion: Average conversion rate (α/(α+β))
    - confidence: Distribution of confidence levels (low/medium/high)

    Use this endpoint to:
    - Monitor learning progress
    - Debug Thompson Sampling behavior
    - Audit system state
    """
    try:
        from ml.thompson_sampling import ThompsonSamplingEngine
        from ml.thompson_metrics import get_metrics

        engine = ThompsonSamplingEngine()
        metrics = get_metrics(engine)

        stats = metrics.get_stats()

        return ThompsonStatsResponse(
            products_tracked=stats["products_tracked"],
            avg_alpha=stats["avg_alpha"],
            avg_beta=stats["avg_beta"],
            avg_conversion=stats["avg_conversion"],
            confidence=stats["confidence"]
        )

    except Exception as e:
        logger.error(f"Failed to get Thompson stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Thompson stats: {str(e)}"
        )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 80)
    logger.info("🚀 PriceSense API Starting Up")
    logger.info("=" * 80)

    # Check Qdrant connection (lazy load)
    try:
        qm = get_qdrant()
        collections = qm.client.get_collections()
        logger.info(f"✅ Qdrant connected: {len(collections.collections)} collections")
    except HTTPException:
        logger.warning("⚠️ Qdrant unavailable: Python 3.14 compatibility issue (will use lazy loading)")
    except Exception as e:
        logger.error(f"❌ Qdrant connection failed: {e}")

    # Check Redis connection
    try:
        from core.redis_client import redis_client
        redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

    # Check LangGraph workflow (lazy load)
    try:
        workflow = get_workflow()
        logger.info("✅ LangGraph workflow loaded")
    except HTTPException:
        logger.warning("⚠️ LangGraph workflow unavailable: Python 3.14 compatibility issue")
    except Exception as e:
        logger.error(f"❌ LangGraph workflow failed: {e}")

    # Initialize Thompson Sampling metrics
    try:
        from ml.thompson_sampling import ThompsonSamplingEngine
        from ml.thompson_metrics import get_metrics

        engine = ThompsonSamplingEngine()
        metrics = get_metrics(engine)
        stats = metrics.get_stats()

        logger.info(f"✅ Thompson Sampling initialized: {stats['products_tracked']} products tracked")
    except Exception as e:
        logger.error(f"❌ Thompson Sampling initialization failed: {e}")

    logger.info("=" * 80)
    logger.info(f"📡 API running at: http://localhost:8000")
    logger.info(f"📚 Docs available at: http://localhost:8000/api/docs")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 PriceSense API Shutting Down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
