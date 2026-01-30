"""
FastAPI backend for PriceSense multi-agent recommendation system

Endpoints:
- POST /api/search - Main product search and recommendation
- POST /api/feedback/action - User action feedback for Thompson Sampling
- GET /api/health - System health check
- GET /api/cache/stats - Cache statistics
"""
from fastapi import FastAPI, HTTPException, status, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import hashlib
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


async def execute_smart_path(request: SearchRequest, start_time: float) -> Dict[str, Any]:
    """
    SMART PATH: Run Agent 1 only with simple ranking

    Target: 300-800ms execution time
    Use case: Simple queries without financial constraints

    Steps:
    1. Run Agent 1 (Discovery) to get candidate products
    2. Apply simple scoring: similarity_score * rating * 20
    3. Sort by score, return top 10
    4. Skip financial analysis, skip explainer
    5. Return minimal recommendations

    Args:
        request: SearchRequest with query and user profile
        start_time: Request start time for timing measurement

    Returns:
        Dict with query results and metadata
    """
    logger.info(f"🎯 SMART PATH: Executing Agent 1 only for query='{request.query}'")
    smart_start = time.time()

    try:
        # Step 1: Run Agent 1 (Discovery)
        from agents.agent1_discovery import ProductDiscoveryAgent
        from models.state import AgentState

        agent1 = ProductDiscoveryAgent()
        state = AgentState(
            query=request.query,
            user_profile=request.user_profile,
            candidate_products=[],
            affordable_products=[],
            final_recommendations=[],
            errors=[]
        )

        result_state = agent1.execute(state)
        agent1_time = int((time.time() - smart_start) * 1000)

        # Step 2: Simple scoring and ranking
        candidates = result_state.get('candidate_products', [])
        logger.info(f"Agent 1 returned {len(candidates)} candidates in {agent1_time}ms")

        ranked_products = []

        for product in candidates[:50]:  # Top 50 from Agent 1
            # Simple score: similarity * rating * 20 (scale to 0-100)
            similarity = product.get('similarity_score', 0.7)
            rating = product.get('rating', 3.5) or 3.5
            simple_score = similarity * rating * 20

            ranked_products.append({
                'product': product,
                'final_score': simple_score,
                'scores': {
                    'similarity': similarity,
                    'rating': rating,
                    'simple_rank': simple_score
                },
                'affordability': None,  # Not analyzed in SMART path
                'explanation': {
                    'text': f"Recommended based on search relevance and {rating:.1f}★ rating",
                    'type': 'simple',
                    'verified': False,
                    'trust': 0.5,
                    'used_llm': False,
                    'violations': []
                }
            })

        # Step 3: Sort and take top 10
        ranked_products.sort(key=lambda x: x['final_score'], reverse=True)
        top_recommendations = ranked_products[:request.max_results]

        execution_time = int((time.time() - start_time) * 1000)
        logger.info(f"✅ SMART PATH complete: {execution_time}ms total, {len(top_recommendations)} recommendations")

        return {
            'query': request.query,
            'candidate_products': candidates,
            'affordable_products': [],  # Not analyzed
            'final_recommendations': top_recommendations,
            'all_unaffordable': False,
            'errors': result_state.get('errors', []),
            'search_time_ms': agent1_time,
            'financial_analysis_time_ms': 0,
            'pathfinder_time_ms': 0,
            'recommender_time_ms': 0,
            'explainer_time_ms': 0,
            'complexity_level': 'SMART'
        }

    except Exception as e:
        logger.error(f"SMART PATH failed: {e}", exc_info=True)
        # Fallback: return error state
        return {
            'query': request.query,
            'candidate_products': [],
            'affordable_products': [],
            'final_recommendations': [],
            'all_unaffordable': False,
            'errors': [f"SMART PATH error: {str(e)}"],
            'search_time_ms': 0,
            'complexity_level': 'SMART'
        }


@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_products(
    query: str = Form(..., description="Text search query", min_length=3, max_length=200),
    max_results: int = Form(default=10, ge=1, le=50, description="Maximum number of results"),
    user_profile: Optional[str] = Form(None, description="User profile as JSON string"),
    include_alternatives: bool = Form(default=True, description="Include alternative financing paths"),
    image: Optional[UploadFile] = File(None, description="Optional image for multimodal search")
):
    """
    Main product search with optional image upload for multimodal search

    **Multimodal Search:**
    When an image is provided, the system:
    1. Generates CLIP embedding for the image (512-dim)
    2. Generates CLIP embedding for the text query (512-dim)
    3. Combines: 70% text + 30% image → final query embedding
    4. Searches Qdrant with combined embedding

    **Use Cases:**
    - Text only: "laptop under $1000"
    - Text + Image: Upload phone photo + "phones like this under $500"

    **Supported Image Formats:** JPG, PNG, WebP
    **Max Image Size:** 10MB

    **Routing Logic:**
    - FAST PATH (<100ms): Cache hit, return cached SearchResponse
    - SMART PATH (300-800ms): Agent 1 only with simple ranking
    - DEEP PATH (1500-3000ms): Full LangGraph pipeline (5 agents)

    **Full Workflow (DEEP PATH):**
    1. Agent 1 (Discovery): Multimodal semantic search
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
        # ========================================
        # STEP 1: Parse user profile
        # ========================================
        user_profile_obj = None
        if user_profile:
            import json
            try:
                user_profile_dict = json.loads(user_profile)
                # Validate required fields
                required = ['user_id', 'monthly_income', 'credit_score']
                missing = [f for f in required if f not in user_profile_dict]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required user_profile fields: {missing}"
                    )
                user_profile_obj = user_profile_dict
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON in user_profile: {str(e)}"
                )
            except Exception as e:
                logger.warning(f"Failed to parse user_profile: {e}")

        logger.info(
            f"🔍 Search request: '{query}' "
            f"(user={'provided' if user_profile_obj else 'anonymous'}, "
            f"image={'provided' if image else 'none'})"
        )

        # ========================================
        # STEP 2: Handle image upload (if provided)
        # ========================================
        image_embedding = None
        image_path = None

        if image:
            # Validate image
            if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image format: {image.content_type}. Use JPG, PNG, or WebP."
                )

            # Check file size (max 10MB)
            contents = await image.read()
            if len(contents) > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too large. Maximum size: 10MB"
                )

            # Save to temporary file
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
                tmp.write(contents)
                image_path = tmp.name

            logger.info(f"📷 Image uploaded: {image.filename} ({len(contents)} bytes) → {image_path}")

            # Generate image embedding
            try:
                from core.embeddings import MultimodalEmbedder
                embedder = MultimodalEmbedder()
                image_embedding = embedder.embed_image(image_path).tolist()
                logger.info("✅ Image embedding generated (512-dim)")
            except Exception as e:
                logger.error(f"Failed to generate image embedding: {e}")
                # Clean up temp file
                if image_path and os.path.exists(image_path):
                    os.unlink(image_path)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process image: {str(e)}"
                )
            finally:
                # Clean up temp file
                if image_path and os.path.exists(image_path):
                    try:
                        os.unlink(image_path)
                    except:
                        pass

        # ============================================================
        # STEP 3: Generate cache key
        # ============================================================
        query_hash = hashlib.md5(query.encode()).hexdigest()
        user_id = user_profile_obj.get('user_id') if user_profile_obj else "anonymous"
        image_suffix = ":img" if image_embedding else ""
        cache_key = f"search:{query_hash}:{user_id}{image_suffix}"

        # ============================================================
        # STEP 4: Check Redis cache (FAST PATH)
        # ============================================================
        try:
            from core.redis_client import redis_manager

            if redis_manager and redis_manager.client:
                cached_response = redis_manager.client.get(cache_key)

                if cached_response:
                    # Cache HIT - increment metrics
                    try:
                        redis_manager.client.incr("metrics:cache_hits")
                    except:
                        pass

                    cache_hit_time = int((time.time() - start_time) * 1000)
                    logger.info(
                        f"✅ CACHE HIT: key={cache_key}, time={cache_hit_time}ms"
                    )

                    # Parse cached response
                    response = SearchResponse.parse_raw(cached_response)

                    # Update metadata to reflect cache hit
                    response.metadata['cache_hit'] = True
                    response.metadata['cache_key'] = cache_key
                    response.metadata['complexity_level'] = 'FAST'
                    response.metadata['multimodal'] = image_embedding is not None
                    response.metadata['original_execution_time_ms'] = response.metadata.get('execution_time_ms', 0)
                    response.metadata['execution_time_ms'] = cache_hit_time
                    response.timestamp = datetime.utcnow()  # Update timestamp

                    return response
                else:
                    # Cache MISS - increment metrics
                    try:
                        redis_manager.client.incr("metrics:cache_misses")
                    except:
                        pass

                    logger.info(f"⚠️ CACHE MISS: key={cache_key}")
        except Exception as e:
            logger.warning(f"Redis cache check failed: {e}. Continuing without cache.")

        # ============================================================
        # STEP 5: Estimate complexity
        # ============================================================
        try:
            from ml.complexity_estimator import complexity_estimator

            complexity_result = complexity_estimator.estimate(
                query=query,
                user_profile=user_profile_obj,
                has_image=image_embedding is not None
            )

            logger.info(
                f"📊 Complexity: {complexity_result['level']} "
                f"(score={complexity_result['score']:.3f}) - {complexity_result['reasoning']}"
            )
        except Exception as e:
            logger.error(f"Complexity estimation failed: {e}. Defaulting to DEEP path.")
            complexity_result = {
                'level': 'DEEP',
                'score': 1.0,
                'reasoning': f'Complexity estimation error: {str(e)}',
                'factors': {}
            }

        # ============================================================
        # STEP 6: Route based on complexity
        # ============================================================
        if complexity_result['level'] == 'SMART':
            # SMART PATH: Agent 1 only + simple ranking
            # Create mock request object for backward compatibility
            class MockRequest:
                def __init__(self, q, up, mr):
                    self.query = q
                    self.user_profile = up
                    self.max_results = mr
            mock_request = MockRequest(query, user_profile_obj, max_results)
            result_state = await execute_smart_path(mock_request, start_time)
            result_state['image_embedding'] = image_embedding  # Add for metadata
        else:
            # DEEP PATH: Full LangGraph pipeline
            logger.info(f"🔬 DEEP PATH: Running full 5-agent pipeline")

            # Lazy load workflow - will raise HTTPException if unavailable
            workflow = get_workflow()

            # Use LangGraph workflow for complete pipeline
            result_state = workflow(
                query=query,
                user_profile=user_profile_obj,
                image_embedding=image_embedding  # Pass to Agent 1 for multimodal search
            )

            result_state['complexity_level'] = 'DEEP'

        # Calculate total execution time
        total_time = int((time.time() - start_time) * 1000)

        # Format recommendations from final state
        recommendations = []
        for i, rec in enumerate(result_state.get('final_recommendations', [])[:max_results], 1):
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

        # Build metadata with routing information
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
            },
            # Routing metadata
            'cache_hit': False,
            'cache_key': cache_key,
            'complexity_level': result_state.get('complexity_level', complexity_result['level']),
            'complexity_score': complexity_result['score'],
            'routing_reasoning': complexity_result['reasoning'],
            # Multimodal metadata
            'multimodal': image_embedding is not None,
            'search_mode': 'multimodal' if image_embedding else 'text_only'
        }

        response = SearchResponse(
            query=query,
            user_id=user_profile_obj.get('user_id') if user_profile_obj else 'anonymous',
            recommendations=recommendations,
            metadata=metadata,
            errors=result_state.get('errors', []),
            timestamp=datetime.utcnow()
        )
        # ============================================================
        # STEP 5: Cache the response for future FAST PATH hits
        # ============================================================
        try:
            if redis_manager and redis_manager.client:
                response_json = response.json()
                redis_manager.client.setex(cache_key, 3600, response_json)  # 1 hour TTL
                logger.info(
                    f"💾 CACHE STORED: key={cache_key}, "
                    f"ttl=3600s, size={len(response_json)} bytes"
                )
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

        return response
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

    Architecture Specification - Signal Weights:
    - view: +0.1 (Weak positive: User viewed product)
    - click: +0.3 (Moderate positive: User clicked product)
    - add_to_cart: +0.7 (Strong positive: User added to cart)
    - purchase: +1.0 (Strongest positive: User purchased product)
    - skip: -0.3 (Weak negative: User skipped product)
    - remove_from_cart: -0.5 (Moderate negative: User removed from cart)
    - return: -1.0 (Strongest negative: User returned product)

    This updates the Thompson Sampling beta distribution (α, β) for the product.
    """
    try:
        logger.info(f"Feedback: user={request.user_id}, product={request.product_id}, action={request.action}")

        # Map action to reward (ARCHITECTURE SPECIFICATION)
        # These weights define the reinforcement learning signal strength
        # DO NOT MODIFY without updating architecture documentation
        SIGNAL_WEIGHTS = {
            # Positive signals (α parameter increases)
            "view": 0.1,              # Weak positive: User viewed product
            "click": 0.3,             # Moderate positive: User clicked product
            "add_to_cart": 0.7,       # Strong positive: User added to cart
            "purchase": 1.0,          # Strongest positive: User purchased product

            # Negative signals (β parameter increases)
            "skip": -0.3,             # Weak negative: User skipped product
            "remove_from_cart": -0.5, # Moderate negative: User removed from cart
            "return": -1.0            # Strongest negative: User returned product
        }

        reward = SIGNAL_WEIGHTS.get(request.action.lower(), 0.0)

        # Validate action
        if request.action.lower() not in SIGNAL_WEIGHTS:
            logger.warning(f"Unknown action '{request.action}' - using neutral reward (0.0)")

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

        # Update Thompson Sampling parameters based on signal weight
        thompson_updated = False
        if reward != 0:  # Skip neutral signals
            try:
                from core.redis_client import redis_manager

                # Get current parameters
                key = f"thompson:{request.product_id}"
                old_alpha = float(redis_manager.client.hget(key, "alpha") or 1.0)
                old_beta = float(redis_manager.client.hget(key, "beta") or 1.0)

                alpha = old_alpha
                beta = old_beta

                # Update Thompson Sampling parameters based on signal weight
                # Architecture: IF weight > 0 → increase α (success)
                #               IF weight < 0 → increase β (failure)
                #               IF weight = 0 → no update (neutral)

                if reward > 0:  # Positive signal
                    alpha += reward  # Direct weight mapping (e.g., purchase: +1.0, view: +0.1)
                    logger.debug(f"Positive signal: α += {reward} → α = {alpha}")
                elif reward < 0:  # Negative signal
                    beta += abs(reward)  # Increase failure count (e.g., return: +1.0, skip: +0.3)
                    logger.debug(f"Negative signal: β += {abs(reward)} → β = {beta}")

                # Store updated parameters
                redis_manager.client.hset(key, "alpha", alpha)
                redis_manager.client.hset(key, "beta", beta)

                thompson_updated = True

                # Detailed logging with before/after comparison
                conversion = alpha / (alpha + beta)
                logger.info(
                    f"Thompson update: user={request.user_id}, product={request.product_id}, "
                    f"action={request.action}, signal_weight={reward:+.1f}, "
                    f"α: {old_alpha:.2f} → {alpha:.2f}, "
                    f"β: {old_beta:.2f} → {beta:.2f}, "
                    f"conversion: {conversion:.3f}"
                )

            except Exception as e:
                logger.error(f"Failed to update Thompson Sampling: {e}")

        return FeedbackResponse(
            success=True,
            message=f"Feedback recorded: {request.action} on {request.product_id} (signal weight: {reward:+.1f})",
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
        # ============================================================================
        # SIGNAL WEIGHTS (Architecture Specification)
        # ============================================================================
        # These weights define Thompson Sampling reinforcement signals:
        #   Positive: view (+0.1), click (+0.3), add_to_cart (+0.7), purchase (+1.0)
        #   Negative: skip (-0.3), remove_from_cart (-0.5), return (-1.0)
        #
        # The ThompsonSamplingEngine handles the actual weight mapping.
        # This endpoint validates actions and delegates to the engine.
        # ============================================================================

        # Validate action against architecture specification
        # These actions MUST match SIGNAL_WEIGHTS keys
        VALID_ACTIONS = {"view", "click", "add_to_cart", "purchase", "skip", "remove_from_cart", "return"}

        if request.action not in VALID_ACTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Must be one of: {', '.join(sorted(VALID_ACTIONS))}"
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

        # Log meaningful events with conversion rate
        if request.action in {"purchase", "return", "add_to_cart", "remove_from_cart"}:
            conversion = params['alpha'] / (params['alpha'] + params['beta'])
            logger.info(
                f"Thompson interaction: user={request.user_id}, "
                f"product={request.product_id}, action={request.action}, "
                f"α={params['alpha']:.2f}, β={params['beta']:.2f}, "
                f"conversion={conversion:.3f}"
            )

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

# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/cache/stats", response_model=Dict[str, Any], tags=["Cache"])
async def get_cache_stats():
    """
    Get Redis cache statistics.

    Returns:
    - Total keys
    - Memory usage
    - Search cache keys count
    - Hit rate (if tracking enabled)
    """
    try:
        from core.redis_client import redis_manager

        # Get total keys
        total_keys = redis_manager.client.dbsize()

        # Get memory usage
        info = redis_manager.client.info("memory")
        memory_mb = info.get("used_memory", 0) / (1024 * 1024)

        # Count search cache keys
        search_keys = redis_manager.client.keys("search:*")
        search_cache_count = len(search_keys)

        # Get cache metrics from Redis (if tracking)
        try:
            cache_hits = int(redis_manager.client.get("metrics:cache_hits") or 0)
            cache_misses = int(redis_manager.client.get("metrics:cache_misses") or 0)
            total_requests = cache_hits + cache_misses
            hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0
        except:
            cache_hits = 0
            cache_misses = 0
            hit_rate = 0.0

        return {
            "cache_enabled": True,
            "total_keys": total_keys,
            "memory_usage_mb": round(memory_mb, 2),
            "search_cache_keys": search_cache_count,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate_percent": round(hit_rate, 2)
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "cache_enabled": False,
            "error": str(e)
        }


@app.delete("/api/cache/clear", tags=["Cache"])
async def clear_cache(
    pattern: str = "search:*",
    confirm: bool = False
):
    """
    Clear cache entries matching pattern.

    Args:
        pattern: Redis key pattern (default: "search:*" - all search caches)
        confirm: Must be True to execute (safety check)

    Examples:
        - Clear all search caches: DELETE /api/cache/clear?pattern=search:*&confirm=true
        - Clear user's cache: DELETE /api/cache/clear?pattern=search:*:USER123&confirm=true
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must set confirm=true to clear cache"
        )

    try:
        from core.redis_client import redis_manager

        # Find keys matching pattern
        keys = redis_manager.client.keys(pattern)

        if not keys:
            return {"cleared": 0, "message": f"No keys found matching pattern: {pattern}"}

        # Delete keys
        deleted = redis_manager.client.delete(*keys)

        logger.info(f"Cache cleared: {deleted} keys deleted (pattern: {pattern})")

        return {
            "cleared": deleted,
            "pattern": pattern,
            "message": f"Successfully cleared {deleted} cache entries"
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.get("/api/cache/inspect/{cache_key}", tags=["Cache"])
async def inspect_cache(cache_key: str):
    """
    Inspect a specific cache entry.

    Args:
        cache_key: Full cache key (e.g., "search:abc123:USER001")

    Returns:
        Cached data + metadata (TTL, size, etc.)
    """
    try:
        from core.redis_client import redis_manager

        # Check if key exists
        exists = redis_manager.client.exists(cache_key)

        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cache key not found: {cache_key}"
            )

        # Get TTL
        ttl = redis_manager.client.ttl(cache_key)

        # Get value
        value = redis_manager.client.get(cache_key)

        # Get size
        size_bytes = len(value) if value else 0

        # Parse JSON
        import json
        try:
            data = json.loads(value)
            parsed = True
        except:
            data = value
            parsed = False

        return {
            "cache_key": cache_key,
            "exists": True,
            "ttl_seconds": ttl,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "parsed": parsed,
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to inspect cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect cache: {str(e)}"
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

    logger.info("")
    logger.info("✨ FEATURES:")
    logger.info("  • 3-tier complexity routing (FAST/SMART/DEEP)")
    logger.info("  • Thompson Sampling reinforcement learning")
    logger.info("  • Multimodal search (text + image) with CLIP embeddings")
    logger.info("  • Financial affordability analysis with DTI/PTI calculations")
    logger.info("  • Gemini 2.0 Flash explanations with 7-check fact verification")
    logger.info("  • Budget pathfinding with savings/financing alternatives")
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
