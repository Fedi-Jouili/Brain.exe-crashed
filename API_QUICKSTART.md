# FastAPI Quick Start Guide

## Prerequisites

- Python 3.8+
- Qdrant running (default: localhost:6333)
- Redis running (default: localhost:6379)
- All dependencies installed

## Installation

```bash
# Install dependencies
cd backend
pip install -r requirements.txt
```

## Starting the API Server

### Option 1: Direct Python
```bash
cd backend
python main.py
```

### Option 2: Using Uvicorn
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on **http://localhost:8000**

## Verify Installation

### Check Health
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "qdrant": "healthy",
    "redis": "healthy",
    "agent1_discovery": "healthy",
    "agent2_financial": "healthy",
    "agent2_5_pathfinder": "healthy",
    "agent3_recommender": "healthy",
    "agent4_explainer": "healthy"
  },
  "version": "1.0.0",
  "uptime_seconds": 123.45
}
```

## Testing the API

### Run Test Suite
```bash
python backend/scripts/test_api.py
```

Expected output:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧪 PRICESENSE API TESTS                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
🧪 TEST 1: HEALTH CHECK
================================================================================
...
✅ Health Check
✅ Simple Search
✅ Search with Profile
✅ Feedback Submission
✅ Cache Statistics
✅ Simplified Recommendations
✅ Get Product by ID
✅ Thompson Interaction
✅ Thompson Statistics

✅ PASSED: 9/9 tests
```

## Example API Calls

### 1. Simple Search
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "affordable gaming laptop",
    "max_results": 5
  }'
```

### 2. Search with User Profile (Full Workflow)
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### 3. Simplified Recommendations
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER002",
    "category": "laptops",
    "max_price": 2000.0,
    "top_k": 5
  }'
```

### 4. Get Product Details
```bash
curl http://localhost:8000/api/products/PROD0042
```

### 5. Track User Interaction
```bash
curl -X POST http://localhost:8000/api/interact \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER003",
    "product_id": "PROD0042",
    "action": "purchase"
  }'
```

### 6. Get Thompson Sampling Statistics
```bash
curl http://localhost:8000/api/thompson/stats
```

## Interactive Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

These provide:
- Interactive request/response testing
- Schema documentation
- Example payloads
- Try-it-out functionality

## Using Python Requests

```python
import requests

# Simple search
response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "affordable gaming laptop",
        "max_results": 5
    }
)

data = response.json()
print(f"Found {len(data['recommendations'])} recommendations")

for rec in data['recommendations']:
    product = rec['product']
    print(f"{rec['rank']}. {product['name']} - ${product['price']:.2f}")

    # Check explanation trust score
    if rec.get('explanation'):
        exp = rec['explanation']
        print(f"   Explanation: {exp['text'][:100]}...")
        print(f"   Trust: {exp['trust']:.2f}")
```

## Troubleshooting

### Issue: "Cannot connect to Qdrant"
**Solution:**
```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Issue: "Cannot connect to Redis"
**Solution:**
```bash
# Start Redis
docker run -p 6379:6379 redis
```

### Issue: "Module 'langgraph' not found"
**Solution:**
```bash
pip install langgraph
```

### Issue: "No products found"
**Solution:**
```bash
# Load sample data
cd backend
python scripts/load_products_data.py
```

### Issue: "LLM explanations failing"
**Solution:**
Check `.env` file has valid Gemini API key:
```bash
GOOGLE_API_KEY=your_api_key_here
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Gemini LLM
GOOGLE_API_KEY=your_gemini_api_key

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Performance Tips

### 1. Reduce max_results
```json
{
  "query": "laptop",
  "max_results": 3  // Faster than 10
}
```

### 2. Skip alternatives
```json
{
  "query": "laptop",
  "include_alternatives": false  // Faster without cluster alternatives
}
```

### 3. Use simple search without profile
```json
{
  "query": "laptop"
  // No user_profile = skips financial analysis
}
```

## Monitoring

### Check Server Logs
```bash
# Server logs show agent execution
INFO - Search request: 'gaming laptop' (user_profile: True)
INFO - Agent 1 (Discovery): Found 15 candidates in 234ms
INFO - Agent 2 (Financial): Analyzed affordability in 89ms
INFO - Agent 3 (Recommender): Ranked products in 123ms
INFO - Agent 4 (Explainer): Generated explanations in 456ms
```

### Monitor Agent Performance
```python
import requests

response = requests.post("http://localhost:8000/api/search", json={"query": "laptop"})
data = response.json()

# Check agent timings
timings = data['metadata']['agent_timings']
print(f"Discovery: {timings['discovery']}ms")
print(f"Financial: {timings['financial']}ms")
print(f"Recommender: {timings['recommender']}ms")
print(f"Explainer: {timings['explainer']}ms")
```

## Next Steps

1. **Test all endpoints:** Run `python scripts/test_api.py`
2. **Load sample data:** Ensure Qdrant has products loaded
3. **Configure LLM:** Set up Gemini API key for explanations
4. **Monitor performance:** Check agent timing metrics
5. **Integrate frontend:** Connect UI to REST API endpoints

## Support

- API Documentation: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health
- OpenAPI Schema: http://localhost:8000/openapi.json

---

**Status:** ✅ Ready to use

**Port:** 8000
**Docs:** /api/docs
