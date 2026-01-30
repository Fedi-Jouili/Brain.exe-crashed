# 🚀 Quick Start Guide - PriceSense

## What You Have Right Now

✅ **Complete Infrastructure**
- Docker Compose configuration
- Qdrant vector database client
- Redis cache client  
- CLIP embeddings (multimodal AI)
- Pydantic data models
- Financial calculator
- Agent 1: Product Discovery
- Database initialization scripts
- Sample data generator

## 🎯 Get It Running in 5 Steps

### Step 1: Set Up Environment

```powershell
cd c:\Users\mezen\fincommerce-engine

# Copy environment template
Copy-Item .env.example .env

# Edit .env and add your Google Gemini API key
# Get one free at: https://makersuite.google.com/app/apikey
notepad .env
```

In `.env`, set:
```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

### Step 2: Start Docker Services

```powershell
# Start Qdrant and Redis
docker-compose up -d qdrant redis

# Verify they're running
docker ps
```

You should see:
```
fincommerce-qdrant   Up
fincommerce-redis    Up
```

### Step 3: Install Python Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

This will install:
- FastAPI, Uvicorn
- Qdrant, Redis clients
- PyTorch, CLIP (AI models)
- Google Gemini SDK
- LangGraph, LangChain
- scikit-learn, numpy

**Note**: CLIP model download (~350MB) happens on first run.

### Step 4: Initialize Databases

```powershell
# Create Qdrant collections
python scripts/init_db.py
```

Expected output:
```
🚀 FinCommerce Engine - Database Initialization
✅ Collection 'products': 0 points
✅ Collection 'users': 0 points
✅ Collection 'financial_kb': 0 points
✅ Collection 'transactions': 0 points
✅ Redis initialization complete!
```

### Step 5: Load Sample Data

```powershell
# Seed with sample products and financial rules
python scripts/seed_data.py
```

Expected output:
```
🌱 FinCommerce Engine - Seeding Sample Data
✅ Seeded 8 products with Thompson parameters
✅ Seeded 5 financial rule chunks
✅ Seeded 3 user profiles
📊 Database Summary:
   - Products: 8
   - Financial KB: 5
   - Users: 3
```

## ✅ Verify Everything Works

### Test 1: CLIP Embeddings

```powershell
python
```

```python
from core.embeddings import clip_embedder

# Generate embedding
embedding = clip_embedder.encode_query("gaming laptop under $1000")
print(f"✅ Embedding dimension: {len(embedding)}")  # Should be 512
```

### Test 2: Qdrant Search

```python
from core.qdrant_client import qdrant_manager
from core.embeddings import clip_embedder

# Search for products
query_embedding = clip_embedder.encode_query("laptop for programming")
results = qdrant_manager.search_products(query_embedding, top_k=5)

print(f"✅ Found {len(results)} products")
for result in results:
    print(f"  - {result.payload['name']} (${result.payload['price']}) - Score: {result.score:.3f}")
```

### Test 3: Redis Cache

```python
from core.redis_client import redis_manager

# Test cache
redis_manager.cache_search_results(
    query="test",
    user_id="USER0001",
    response={"test": "data"}
)

cached = redis_manager.get_cached_search("test", "USER0001")
print(f"✅ Cache working: {cached is not None}")
```

### Test 4: Thompson Sampling

```python
from core.redis_client import redis_manager

# Get Thompson params
params = redis_manager.get_thompson_params("PROD0042")
print(f"✅ Thompson params: α={params['alpha']}, β={params['beta']}")

# Update after a purchase
redis_manager.update_thompson_params("PROD0042", signal_weight=1.0)
updated = redis_manager.get_thompson_params("PROD0042")
print(f"✅ Updated: α={updated['alpha']}, β={updated['beta']}")
```

### Test 5: Financial Calculations

```python
from models.schemas import UserProfile
from utils.financial import FinancialCalculator

# Create test profile
profile = UserProfile(
    user_id="TEST001",
    monthly_income=5000,
    monthly_expenses=3500,
    savings=15000,
    current_debt=5000,
    credit_score=720
)

# Check affordability
product_price = 899.99
can_afford, metrics = FinancialCalculator.check_cash_affordability(profile, product_price)

print(f"✅ Can afford ${product_price}? {can_afford}")
print(f"   Safe cash limit: ${metrics['safe_cash_limit']:.2f}")
print(f"   Emergency fund after: ${metrics['emergency_fund_after']:.2f}")
```

### Test 6: Agent 1 (Product Discovery)

```python
from agents.agent1_discovery import product_discovery_agent
from models.schemas import UserProfile
from models.state import AgentState

# Create state
state = {
    'query': 'laptop under $1000 with financing',
    'user_profile': UserProfile(
        user_id="TEST001",
        monthly_income=5000,
        monthly_expenses=3500,
        savings=15000,
        current_debt=5000,
        credit_score=720
    ),
    'image_embedding': None,
    'filters': {},
    'errors': [],
    'warnings': []
}

# Run Agent 1
result = product_discovery_agent.execute(state)

print(f"✅ Agent 1 found {len(result['candidate_products'])} products")
print(f"   Execution time: {result['search_time_ms']}ms")
for product in result['candidate_products'][:3]:
    print(f"   - {product.name} (${product.price})")
```

## 🎨 Sample Data Overview

You now have:

**8 Sample Products:**
- 2 budget laptops ($350-450)
- 2 mid-range laptops ($850-900)  
- 2 gaming laptops ($1000-1500)
- 1 workstation ($2300)
- 1 tablet alternative ($650)

**5 Financial Rules:**
- Debt-to-Income (DTI) ratio guidelines
- Payment-to-Income (PTI) thresholds
- Emergency fund requirements
- Safe purchase limits
- Credit score financing requirements

**3 Sample Users:**
- USER0001: Mid-income, good credit (720)
- USER0002: Lower income, fair credit (680)
- USER0003: High income, excellent credit (780)

## 🔍 Explore the Database

### Qdrant UI
Open your browser: http://localhost:6333/dashboard

You can:
- Browse collections
- View vector points
- Test searches

### Redis CLI

```powershell
docker exec -it fincommerce-redis redis-cli

# List all Thompson parameters
> KEYS thompson:*

# Get a specific product's Thompson params
> GET thompson:PROD0042

# Check cache
> KEYS search:*
```

## 📊 Current System Capabilities

✅ **Working Now:**
- Product search by text
- Vector similarity matching (CLIP)
- Financial calculations (all formulas)
- Thompson Sampling state management
- Cache layer (Redis)
- Database operations (Qdrant)

⏳ **Still To Build:**
- Agent 2: Financial Analyzer (filters affordable products)
- Agent 2.5: Budget Pathfinder (creative financing)
- Agent 3: Smart Recommender (Thompson + collaborative filtering)
- Agent 4: Explainer (Gemini LLM + verification)
- LangGraph orchestration (connects all agents)
- FastAPI endpoints (REST API)
- Streamlit UI (web interface)
- RAGAS evaluation (quality metrics)

## 🎯 Next Steps

### Option A: Build Next Agent (Recommended)
Follow the [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) to implement:
1. Agent 2: Financial Analyzer
2. Agent 3: Smart Recommender  
3. Agent 4: Explainer
4. Orchestration layer

### Option B: Test Current Features
Experiment with what you have:
- Try different search queries
- Test financial calculations with various profiles
- Explore Thompson Sampling updates
- Load more sample data

### Option C: Build API First
Create FastAPI endpoints to expose current functionality:
- `POST /api/search` - Basic search (Agent 1 only)
- `GET /api/products/{id}` - Get product details
- `POST /api/calculate-affordability` - Financial checks

## 💡 Tips

### If CLIP download is slow:
```python
# Pre-download in a separate script
import clip
model, preprocess = clip.load("ViT-B/32", device="cpu")
print("✅ CLIP model cached")
```

### If you want more products:
Edit [backend/scripts/seed_data.py](backend/scripts/seed_data.py) and add more to `generate_sample_products()`

### To reset everything:
```powershell
# Stop containers
docker-compose down

# Delete data
Remove-Item -Recurse -Force data/qdrant_storage, data/redis_data

# Restart
docker-compose up -d qdrant redis
python scripts/init_db.py
python scripts/seed_data.py
```

## 🐛 Troubleshooting

### "Module not found" errors
```powershell
# Make sure you're in the backend directory
cd c:\Users\mezen\fincommerce-engine\backend

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Qdrant connection error
```powershell
# Check if container is running
docker ps | Select-String qdrant

# View logs
docker logs fincommerce-qdrant

# Restart if needed
docker-compose restart qdrant
```

### Redis connection error
```powershell
# Check if running
docker ps | Select-String redis

# Test ping
docker exec -it fincommerce-redis redis-cli ping
# Should return: PONG
```

### CLIP/PyTorch issues on Windows
```powershell
# Install CPU version explicitly
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## 📚 Documentation

- [README.md](README.md) - Project overview
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Complete implementation guide
- [docker-compose.yml](docker-compose.yml) - Service configuration
- [.env.example](.env.example) - Environment variables

## 🎓 Learning Path

1. **Understand the architecture** - Read the full architecture doc you provided
2. **Test each component** - Run the verification tests above
3. **Build one agent at a time** - Follow development guide
4. **Connect with LangGraph** - Orchestrate the workflow
5. **Add API layer** - Expose via FastAPI
6. **Create UI** - Build Streamlit interface
7. **Add monitoring** - RAGAS metrics and logging

## 🚀 You're Ready!

You have a solid foundation. The core infrastructure is working:
- ✅ Vector database
- ✅ Cache layer
- ✅ AI embeddings
- ✅ Financial logic
- ✅ First agent
- ✅ Sample data

Time to build the remaining agents and see it all come together! 💪
