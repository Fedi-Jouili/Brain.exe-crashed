# Quick Start Guide

## Start the Complete System

### 1. Start Backend API
```powershell
cd c:\Users\mezen\fincommerce-engine\backend
C:/Users/mezen/AppData/Local/Python/pythoncore-3.14-64/python.exe -m uvicorn main:app --reload
```

### 2. Start Frontend UI (in a new terminal)
```powershell
cd c:\Users\mezen\fincommerce-engine\frontend
C:/Users/mezen/AppData/Local/Python/pythoncore-3.14-64/python.exe -m streamlit run app.py
```

### 3. Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│                  Streamlit App (Port 8501)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│                FastAPI (Port 8000)                          │
│  Endpoints: /api/search, /api/health, /api/feedback        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ LangGraph
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orchestration Layer                         │
│         LangGraph (FAST/SMART/DEEP Workflows)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Agent Execution
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Multi-Agent System                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Agent 1  │ Agent 2  │Agent 2.5 │ Agent 3  │ Agent 4  │  │
│  │Discovery │Financial │Pathfinder│Recommend │Explainer │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Data Access
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌────────────────────┐    ┌────────────────────┐          │
│  │ Qdrant (Port 6333) │    │ Redis (Port 6379)  │          │
│  │ - Products         │    │ - Thompson Params  │          │
│  │ - Users            │    │ - Cache            │          │
│  │ - Financial KB     │    └────────────────────┘          │
│  │ - Transactions     │                                     │
│  └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

## Testing the System

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

### 2. Simple Search (via API)
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "gaming laptop", "use_cache": false}'
```

### 3. Search with Financial Profile (via UI)
1. Go to http://localhost:8501
2. Enable "Include financial analysis" in sidebar
3. Enter financial details
4. Search for a product
5. View personalized recommendations

## Example Workflows

### Scenario 1: Quick Search (SMART Path)
- Query: "wireless headphones"
- No user profile
- Expected: 3-5 second response with 5-8 recommendations

### Scenario 2: Financial Analysis (DEEP Path)
- Query: "professional laptop"
- User profile: $5000/month income, $3500 expenses
- Expected: 5-8 second response with affordability analysis

### Scenario 3: Cached Results (FAST Path)
- Repeat the same query within 1 hour
- Expected: <1 second response from cache

## Troubleshooting

### Backend not starting
```powershell
# Check if Qdrant is running
curl http://localhost:6333/collections

# Check if Redis is running
redis-cli ping
```

### Frontend not connecting to API
1. Verify backend is running: http://localhost:8000/api/health
2. Check CORS settings in backend/main.py
3. Verify API_BASE_URL in frontend/app.py

### No recommendations returned
1. Check Qdrant has products: `curl http://localhost:6333/collections/products`
2. Verify product embeddings exist
3. Check backend logs for errors

## Production Deployment

For production deployment, update:
- `API_BASE_URL` in frontend/app.py
- CORS origins in backend/main.py
- Use environment variables for configuration
- Enable authentication
- Use production-grade ASGI server (Gunicorn + Uvicorn workers)
- Deploy behind reverse proxy (Nginx)
