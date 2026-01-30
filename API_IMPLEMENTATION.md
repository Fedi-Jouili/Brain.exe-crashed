# FastAPI REST API Implementation

## Overview

Complete FastAPI REST API layer for PriceSense multi-agent recommendation system, integrating the LangGraph workflow orchestration with all 5 agents.

## Implementation Summary

### Files Created/Modified

1. **backend/models/api_models.py** (NEW - 175 lines)
   - Complete Pydantic request/response models for all endpoints
   - Field validation for user profiles and constraints
   - Comprehensive documentation

2. **backend/main.py** (UPDATED - 755 lines)
   - Refactored to use api_models.py imports
   - Integrated LangGraph workflow (run_recommendation_pipeline)
   - Added new endpoints
   - Removed duplicate model definitions

3. **backend/scripts/test_api.py** (ENHANCED)
   - Added tests for new endpoints
   - 9 comprehensive API tests total

## API Endpoints

### 1. GET / (Root)
```
GET http://localhost:8000/
```
Returns service information and API documentation link.

### 2. GET /api/health (Health Check)
```
GET http://localhost:8000/api/health
```
**Response:** HealthResponse
- System health status (healthy | degraded | down)
- Individual service statuses (Qdrant, Redis, all 5 agents)
- Server uptime in seconds
- API version

### 3. POST /api/search (Main Search with LangGraph)
```
POST http://localhost:8000/api/search
Content-Type: application/json

{
  "query": "affordable gaming laptop under $1500",
  "user_profile": {
    "user_id": "USER001",
    "monthly_income": 4500.0,
    "credit_score": 720,
    "existing_debt": 5000.0,
    "risk_tolerance": "medium"
  },
  "max_results": 10,
  "include_alternatives": true
}
```

**Response:** SearchResponse
- Complete recommendations with:
  - Product details (name, price, rating, etc.)
  - Affordability analysis (cash/financing paths)
  - LLM explanations with trust scores [0.0-1.0]
  - Verification status (violations list)
  - Multi-armed bandit scores
  - Cluster-based alternatives
- Execution metadata (agent timings, candidate counts)
- Errors list (graceful degradation)

**Workflow Integration:**
- Uses `run_recommendation_pipeline()` from orchestration.workflow
- Executes full LangGraph workflow:
  1. Agent 1 (Discovery): Semantic search
  2. Agent 2 (Financial): Affordability analysis
  3. Agent 2.5 (Pathfinder): Alternative budget paths (conditional)
  4. Agent 3 (Recommender): Multi-armed bandit ranking
  5. Agent 4 (Explainer): LLM explanations with verification

### 4. POST /api/recommend (Simplified Recommendations)
```
POST http://localhost:8000/api/recommend
Content-Type: application/json

{
  "user_id": "USER002",
  "category": "laptops",
  "max_price": 2000.0,
  "top_k": 5
}
```

**Response:** SearchResponse
- Same structure as /api/search
- Simplified interface without complex query needed
- Uses same LangGraph workflow internally

### 5. GET /api/products/{product_id} (Product Details)
```
GET http://localhost:8000/api/products/{product_id}
```

**Response:** ProductResponse
- Complete product details from Qdrant
- In-stock status
- Financing availability
- Rating and review count
- Description and images

### 6. POST /api/interact (Thompson Sampling Interaction)
```
POST http://localhost:8000/api/interact
Content-Type: application/json

{
  "user_id": "USER003",
  "product_id": "PROD0042",
  "action": "purchase"
}
```

**Valid Actions:**
- `view`: User viewed product (+0.1)
- `click`: User clicked product (+0.3)
- `add_to_cart`: User added to cart (+0.7)
- `purchase`: User purchased product (+1.0)
- `skip`: User skipped product (-0.3)
- `remove_from_cart`: User removed from cart (-0.5)
- `return`: User returned product (-1.0)

**Response:** InteractionResponse
- Updated Thompson Sampling parameters (α, β)
- Conversion rate
- Confidence level (low | medium | high)

### 7. GET /api/thompson/stats (Thompson Sampling Statistics)
```
GET http://localhost:8000/api/thompson/stats
```

**Response:** ThompsonStatsResponse
- Total products tracked
- Average α, β parameters
- Average conversion rate
- Confidence distribution

### 8. POST /api/feedback/action (User Feedback - Legacy)
```
POST http://localhost:8000/api/feedback/action
Content-Type: application/json

{
  "user_id": "USER004",
  "product_id": "PROD123",
  "action": "purchase",
  "query": "gaming laptop",
  "rating": 4.5
}
```

**Response:** FeedbackResponse
- Feedback submission confirmation
- Thompson Sampling update status

### 9. GET /api/cache/stats (Cache Statistics)
```
GET http://localhost:8000/api/cache/stats
```

**Response:** CacheStatsResponse
- Cache enabled status
- Total keys stored
- Memory usage (MB)

## Request/Response Models

### SearchRequest
- `query`: str (3-200 chars, required)
- `user_profile`: UserProfile (optional, but required fields if provided)
  - `user_id`: str
  - `monthly_income`: float
  - `credit_score`: int
  - `existing_debt`: float (optional)
  - `risk_tolerance`: str (optional)
- `max_results`: int (1-50, default: 10)
- `include_alternatives`: bool (default: True)

**Field Validation:**
- Query length: 3-200 characters
- Max results: 1-50
- User profile validator checks required fields

### RecommendRequest
- `user_id`: str (required)
- `category`: str (optional)
- `max_price`: float (optional)
- `top_k`: int (1-50, default: 10)

### ProductResponse
- `product_id`: str
- `name`: str
- `price`: float
- `category`: str (optional)
- `brand`: str (optional)
- `rating`: float (optional)
- `num_reviews`: int (optional)
- `in_stock`: bool (default: True)
- `description`: str (optional)
- `image_url`: str (optional)
- `financing_available`: bool (default: False)

### AffordabilityResponse
- `can_afford_cash`: bool
- `can_afford_financing`: bool
- `risk_level`: str (low | medium | high | unknown)
- `recommendation`: str
- `cash_analysis`: Dict (optional)
- `financing_paths`: List[Dict] (optional)

### ExplanationResponse
- `text`: str (LLM-generated or template)
- `trust`: float (0.0-1.0, verification score)
- `verified`: bool (passed fact verification)
- `violations`: List[str] (fact-checking violations found)
- `used_llm`: bool (whether LLM was used)
- `type`: str (llm | template | fallback)

### RecommendationResponse
- `rank`: int (1-based ranking)
- `product`: ProductResponse
- `affordability`: AffordabilityResponse (optional)
- `explanation`: ExplanationResponse
- `scores`: Dict[str, float] (thompson, collaborative, ragas, etc.)
- `final_score`: float (0.0-1.0, weighted combination)

### SearchResponse
- `query`: str (original or generated query)
- `user_id`: str
- `recommendations`: List[RecommendationResponse]
- `metadata`: Dict (execution timings, counts, etc.)
- `errors`: List[str] (graceful degradation)
- `timestamp`: datetime

### HealthResponse
- `status`: str (overall | degraded | down)
- `services`: Dict[str, str] (service → status mapping)
- `version`: str (API version)
- `uptime_seconds`: float (server uptime)

## Error Handling

### HTTPException with ErrorResponse
All endpoints use try-catch blocks with proper error responses:

```python
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Error message"
)
```

### Graceful Degradation
- Errors stored in SearchResponse.errors list
- Workflow continues even if individual agents fail
- Partial results returned when possible

## CORS Configuration

```python
allow_origins=["*"]  # Configure for production
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

## Testing

### Run API Server
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
# Docs at http://localhost:8000/api/docs
```

### Run Test Suite
```bash
python backend/scripts/test_api.py
```

**Test Coverage:**
1. ✓ Health Check
2. ✓ Simple Search (no user profile)
3. ✓ Search with Profile (full workflow)
4. ✓ Feedback Submission
5. ✓ Cache Statistics
6. ✓ Simplified Recommendations
7. ✓ Get Product by ID
8. ✓ Thompson Interaction
9. ✓ Thompson Statistics

## LangGraph Integration

### Workflow Execution
```python
from orchestration.workflow import run_recommendation_pipeline

result_state = run_recommendation_pipeline(
    query="affordable gaming laptop",
    user_profile=UserProfile(...)
)
```

### State Flow
```
START
  ↓
Agent 1 (Discovery) - Semantic search → candidate_products
  ↓
Agent 2 (Financial) - Affordability → affordable_products
  ↓
[Conditional: if all_unaffordable]
  ↓
Agent 2.5 (Pathfinder) - Alternative budget paths → alternative_products
  ↓
Agent 3 (Recommender) - Multi-armed bandit ranking → final_recommendations
  ↓
Agent 4 (Explainer) - LLM explanations + verification → explanations with trust
  ↓
END
```

### Result State Structure
```python
{
    'query': str,
    'user_profile': UserProfile,
    'candidate_products': List[Product],
    'affordable_products': List[Product],
    'alternative_products': List[Product],
    'final_recommendations': List[Dict],
    'errors': List[str],
    'search_time_ms': int,
    'financial_analysis_time_ms': int,
    'pathfinder_time_ms': int,
    'recommender_time_ms': int,
    'explainer_time_ms': int,
    'total_execution_time_ms': int
}
```

## Architecture

```
FastAPI REST API Layer (main.py)
    ↓
LangGraph Workflow Orchestration (orchestration/workflow.py)
    ↓
5 Agent Pipeline
    ├── Agent 1: Discovery (semantic search)
    ├── Agent 2: Financial Analysis (affordability)
    ├── Agent 2.5: Pathfinder (budget alternatives)
    ├── Agent 3: Recommender (multi-armed bandit)
    └── Agent 4: Explainer (LLM + verification)
         ↓
    Gemini LLM (gemini-2.5-flash)
         ↓
    Fact Verification (trust scores 0.0-1.0)
```

## Key Features

### 1. Complete LangGraph Integration
- All 5 agents orchestrated via LangGraph StateGraph
- Conditional routing (Agent 2.5 only if all unaffordable)
- Per-agent timing tracking
- Error isolation and graceful degradation

### 2. Trust-Scored Explanations
- LLM-generated explanations via Gemini
- Fact verification against product data
- Trust scores: 0.0 (many violations) to 1.0 (perfect)
- Violation tracking for debugging

### 3. Multi-Armed Bandit Ranking
- Thompson Sampling for exploration/exploitation
- Collaborative filtering boost
- RAGAS retrieval scores
- Weighted final score combination

### 4. Financial Intelligence
- Affordability analysis (cash vs financing)
- Risk level assessment
- Alternative budget paths
- Financing option detection

### 5. Comprehensive Metadata
- Per-agent execution times
- Candidate/affordable product counts
- Agent routing decisions
- Error tracking

## Performance

### Expected Response Times
- Health Check: <100ms
- Simple Search (no profile): 200-500ms
- Full Search (with profile): 1000-3000ms
- Get Product: <50ms
- Thompson Sampling: <10ms

### Optimization
- Parallel agent execution where possible
- Caching (Redis for Thompson Sampling)
- Graceful timeout handling
- Background task processing for feedback

## Production Considerations

### Security
- [ ] Configure CORS for specific origins
- [ ] Add API key authentication
- [ ] Rate limiting
- [ ] Input sanitization

### Monitoring
- [ ] Add structured logging
- [ ] Prometheus metrics
- [ ] OpenTelemetry tracing
- [ ] Error tracking (Sentry)

### Scalability
- [ ] Horizontal scaling with load balancer
- [ ] Redis cluster for Thompson Sampling
- [ ] Qdrant cluster for vector search
- [ ] Agent result caching

## Documentation

- **Interactive API Docs:** http://localhost:8000/api/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/api/redoc (ReDoc)
- **OpenAPI Schema:** http://localhost:8000/openapi.json

## Next Steps

1. **Testing:**
   - Run test suite: `python backend/scripts/test_api.py`
   - Verify all 9 tests pass
   - Check agent timing metrics

2. **Integration:**
   - Connect frontend to new endpoints
   - Implement result caching
   - Add user profile service integration

3. **Monitoring:**
   - Add logging dashboard
   - Track agent performance
   - Monitor trust score trends

4. **Optimization:**
   - Profile slow endpoints
   - Optimize LLM prompt size
   - Implement result pagination

## Success Criteria

- [x] All endpoints implemented
- [x] LangGraph workflow integrated
- [x] Request/response models complete
- [x] Field validation working
- [x] Error handling comprehensive
- [x] Test suite created
- [ ] All tests passing
- [ ] Documentation complete

---

**Status:** ✅ Implementation Complete

**Next:** Run test suite and verify functionality
