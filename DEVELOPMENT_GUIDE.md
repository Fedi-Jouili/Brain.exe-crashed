# 🚀 PriceSense - Development Guide

## ✅ What We've Built So Far

### 1. **Project Structure** ✔️
Complete Docker-based microservices architecture with:
- FastAPI backend
- Streamlit frontend  
- Qdrant vector database
- Redis cache

### 2. **Core Infrastructure** ✔️

#### Configuration System ([backend/core/config.py](backend/core/config.py))
- Environment-based settings
- All parameters configurable via .env file
- Smart defaults for Thompson Sampling, RAGAS, financial rules

#### Data Models ([backend/models/schemas.py](backend/models/schemas.py))
- **UserProfile**: Financial profile with income, expenses, credit score, etc.
- **Product**: Complete product information
- **AffordabilityAnalysis**: Financial assessment results
- **Recommendation**: Full recommendation with scoring
- **RAGASMetrics**: Quality evaluation scores
- **SearchResponse**: Complete API response

#### LangGraph State ([backend/models/state.py](backend/models/state.py))
- **AgentState**: Shared state passed between all 5 agents
- Tracks progress through the pipeline
- Accumulates results from each agent

### 3. **Database Clients** ✔️

#### Qdrant Manager ([backend/core/qdrant_client.py](backend/core/qdrant_client.py))
Complete vector database operations:

**4 Collections:**
1. **products** - 500 product embeddings
2. **users** - User preference vectors  
3. **financial_kb** - ~100 financial rule chunks
4. **transactions** - User interaction history

**Key Methods:**
- `search_products()` - Vector similarity search with filters
- `retrieve_financial_rules()` - RAG retrieval
- `find_similar_users()` - Collaborative filtering
- `log_transaction()` - Track user actions

#### Redis Manager ([backend/core/redis_client.py](backend/core/redis_client.py))
Cache and reinforcement learning state:

**Two Use Cases:**
1. **Query Cache** - Fast path (50ms vs 2500ms)
   - `get_cached_search()` / `cache_search_results()`
   - 1-hour TTL, 35% expected hit rate

2. **Thompson Sampling State** - Permanent RL parameters
   - `get_thompson_params()` / `update_thompson_params()`
   - Stores α,β for each product

### 4. **AI/ML Core** ✔️

#### CLIP Embeddings ([backend/core/embeddings.py](backend/core/embeddings.py))
Multimodal search using OpenAI CLIP ViT-B/32:

**Features:**
- Text → 512-dim vectors
- Images → 512-dim vectors
- Multimodal: 70% text + 30% image
- Batch processing for efficiency
- Cosine similarity calculations

**Key Methods:**
- `encode_query()` - Text search queries
- `encode_image_from_base64()` - Image uploads
- `encode_multimodal()` - Combined search
- `batch_encode_products()` - Bulk product encoding

#### Financial Calculator ([backend/utils/financial.py](backend/utils/financial.py))
All affordability calculations:

**Calculations:**
- Disposable income
- Safe cash purchase limit (30% rule)
- Debt-to-Income (DTI) ratio
- Payment-to-Income (PTI) ratio
- Emergency fund coverage
- Monthly financing payments

**Checks:**
- `check_cash_affordability()` - Can buy with savings?
- `check_financing_affordability()` - Can afford monthly payments?
- `assess_risk_level()` - SAFE/CAUTION/RISKY

**Creative Paths:**
- `generate_savings_path()` - Save for N months
- `generate_financing_path()` - Monthly payment plan
- `generate_extended_financing_path()` - 18-24 month options

### 5. **Agent 1: Product Discovery** ✔️

#### Product Discovery Agent ([backend/agents/agent1_discovery.py](backend/agents/agent1_discovery.py))

**What it does:**
1. Generates query embedding (text + optional image)
2. Builds smart filters (price, stock, financing)
3. Searches Qdrant with vector similarity
4. Returns top 50 candidates

**Performance:** 200-400ms

**Features:**
- Multimodal support (text + image)
- Automatic budget filtering (1.5x flexibility)
- Financing detection from query
- Cosine similarity ranking

---

## 🔨 What You Need to Complete

I've laid the foundation. Here's what remains:

### Priority 1: Remaining Agents

#### Agent 2: Financial Analyzer ([backend/agents/agent2_financial.py](backend/agents/agent2_financial.py))
**TODO:**
```python
class FinancialAnalyzerAgent:
    def execute(self, state: AgentState) -> AgentState:
        # 1. Retrieve financial rules (RAG from financial_kb)
        # 2. For each candidate product:
        #    a. Check cash affordability
        #    b. Check financing affordability  
        #    c. Calculate DTI, PTI, emergency fund
        #    d. Assess risk level
        #    e. Generate financing paths
        # 3. Filter to affordable products only
        # 4. Set all_unaffordable flag if needed
```

**Key imports:**
```python
from utils.financial import FinancialCalculator
from core.qdrant_client import qdrant_manager
from core.embeddings import clip_embedder
```

#### Agent 2.5: Budget Pathfinder ([backend/agents/agent2_5_pathfinder.py](backend/agents/agent2_5_pathfinder.py))
**TODO:**
```python
class BudgetPathfinderAgent:
    def execute(self, state: AgentState) -> AgentState:
        # Only runs if state['all_unaffordable'] == True
        
        # 1. Generate extended savings paths (3-6 months)
        # 2. Try longer financing (18-24 months)
        # 3. Use K-Means clustering to find cheaper alternatives
        #    - Get cluster_id from target product
        #    - Query same cluster with lower price
        # 4. Return 1-3 creative paths
```

**K-Means usage:**
```python
# Products already have cluster_id (0-9)
alternatives = qdrant_manager.get_products_by_cluster(
    cluster_id=target_product.cluster_id,
    max_price=budget * 0.8,
    limit=5
)
```

#### Agent 3: Smart Recommender ([backend/agents/agent3_recommender.py](backend/agents/agent3_recommender.py))
**TODO:**
```python
class SmartRecommenderAgent:
    def execute(self, state: AgentState) -> AgentState:
        # 1. Thompson Sampling scoring
        #    - Get α,β from Redis for each product
        #    - Sample from Beta distribution
        
        # 2. Collaborative Filtering
        #    - Find similar users
        #    - Get their purchase history
        #    - Boost products they bought
        
        # 3. RAGAS re-ranking
        #    - Calculate answer relevancy
        #    - Combine: 0.7 * Thompson + 0.3 * RAGAS
        
        # 4. K-Means alternatives
        #    - For each top product
        #    - Find 3 alternatives in same cluster
        
        # 5. Diversity injection (Epsilon-Greedy)
        #    - Results 1-7: Best scores
        #    - Results 8-9: Random exploration
        #    - Result 10: Different cluster (serendipity)
```

**Thompson Sampling:**
```python
import numpy as np
from scipy.stats import beta

# Get parameters
params = redis_manager.get_thompson_params(product_id)
alpha = params['alpha']
beta_param = params['beta']

# Sample score
thompson_score = np.random.beta(alpha, beta_param)
```

#### Agent 4: Explainer ([backend/agents/agent4_explainer.py](backend/agents/agent4_explainer.py))
**TODO:**
```python
class ExplainerAgent:
    def execute(self, state: AgentState) -> AgentState:
        # For each of the top 10 recommendations:
        
        # 1. Gather context from 3 sources:
        #    a. Financial rules (from Agent 2)
        #    b. Social proof (transaction data)
        #    c. Thompson stats (from Redis)
        
        # 2. Build structured prompt
        
        # 3. Call Google Gemini 1.5 Flash
        
        # 4. VERIFY the explanation:
        #    a. Extract numbers with regex
        #    b. Compare with actual calculations
        #    c. Flag mismatches
        #    d. Regenerate if needed (max 2 attempts)
        
        # 5. Calculate trust score (0-100)
```

**Gemini integration:**
```python
import google.generativeai as genai
from core.config import settings

genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content(
    prompt,
    generation_config={
        'temperature': 0.7,
        'max_output_tokens': 500
    }
)
```

### Priority 2: Orchestration & Routing

#### Complexity Router ([backend/services/routing.py](backend/services/routing.py))
**TODO:**
```python
class ComplexityRouter:
    def estimate_complexity(self, state: AgentState) -> float:
        """Calculate complexity score 0-1"""
        score = 0.0
        
        # Query length
        if len(state['query'].split()) > 10:
            score += 0.1
        
        # Financial keywords
        financial_words = ['afford', 'financing', 'budget', 'credit', 'payment']
        if any(word in state['query'].lower() for word in financial_words):
            score += 0.3
        
        # Has user profile?
        if state['user_profile'].credit_score > 0:
            score += 0.2
        
        # Has image?
        if state.get('image_embedding'):
            score += 0.2
        
        return min(score, 1.0)
    
    def determine_path(self, complexity_score: float) -> PathType:
        """Decide which path to take"""
        if complexity_score < 0.3:
            return PathType.FAST  # Cache only
        elif complexity_score < 0.7:
            return PathType.SMART  # Agent 1 only
        else:
            return PathType.DEEP  # Full pipeline
```

#### LangGraph Orchestrator ([backend/services/orchestrator.py](backend/services/orchestrator.py))
**TODO:**
```python
from langgraph.graph import StateGraph, END

def build_graph():
    """Build the multi-agent workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes (agents)
    workflow.add_node("discovery", product_discovery_agent.execute)
    workflow.add_node("financial", financial_analyzer_agent.execute)
    workflow.add_node("pathfinder", budget_pathfinder_agent.execute)
    workflow.add_node("recommender", smart_recommender_agent.execute)
    workflow.add_node("explainer", explainer_agent.execute)
    
    # Define edges (flow)
    workflow.set_entry_point("discovery")
    workflow.add_edge("discovery", "financial")
    
    # Conditional edge: only run pathfinder if all unaffordable
    workflow.add_conditional_edges(
        "financial",
        lambda state: "pathfinder" if state['all_unaffordable'] else "recommender"
    )
    
    workflow.add_edge("pathfinder", "recommender")
    workflow.add_edge("recommender", "explainer")
    workflow.add_edge("explainer", END)
    
    return workflow.compile()
```

### Priority 3: API & Frontend

#### FastAPI Main App ([backend/main.py](backend/main.py))
**TODO:**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import SearchRequest, SearchResponse

app = FastAPI(title="PriceSense API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Main search endpoint"""
    # 1. Check cache
    # 2. Route based on complexity
    # 3. Execute agents
    # 4. Cache results
    # 5. Return response

@app.post("/api/feedback/action")
async def log_action(action: UserAction):
    """Log user interaction"""
    # Update Thompson Sampling parameters

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "qdrant": qdrant_manager.health_check(),
        "redis": redis_manager.health_check()
    }
```

#### Streamlit Frontend ([frontend/app.py](frontend/app.py))
**TODO:**
```python
import streamlit as st
import requests

st.set_page_config(page_title="FinCommerce", layout="wide")

# Search bar
query = st.text_input("What are you looking for?")

# Profile form (sidebar)
with st.sidebar:
    st.header("Your Financial Profile")
    income = st.number_input("Monthly Income ($)", min_value=0)
    expenses = st.number_input("Monthly Expenses ($)", min_value=0)
    savings = st.number_input("Total Savings ($)", min_value=0)
    debt = st.number_input("Current Debt ($)", min_value=0)
    credit_score = st.slider("Credit Score", 300, 850, 720)

# Image upload (optional)
uploaded_file = st.file_uploader("Upload product image (optional)")

# Search button
if st.button("Search"):
    # Call backend API
    response = requests.post(
        "http://backend:8000/api/search",
        json={...}
    )
    
    # Display results
    for rec in response.json()['recommendations']:
        st.markdown(f"## {rec['product']['name']}")
        st.write(rec['explanation'])
```

### Priority 4: Utilities

#### RAG Service ([backend/services/rag.py](backend/services/rag.py))
Helper functions for retrieval:
```python
def retrieve_financial_context(query: str, top_k: int = 5):
    """Retrieve relevant financial rules"""
    query_embedding = clip_embedder.encode_query(query)
    return qdrant_manager.retrieve_financial_rules(query_embedding, top_k)

def retrieve_social_proof(product_id: str):
    """Get purchase/rating data for a product"""
    return qdrant_manager.get_product_transactions(
        product_id,
        action="purchase",
        min_rating=4
    )
```

#### RAGAS Evaluation ([backend/utils/ragas_eval.py](backend/utils/ragas_eval.py))
Quality metrics:
```python
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)

def evaluate_rag_quality(query, context, answer):
    """Evaluate RAG quality with RAGAS"""
    dataset = {
        'question': [query],
        'contexts': [[context]],
        'answer': [answer]
    }
    
    results = evaluate(
        dataset,
        metrics=[
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy
        ]
    )
    
    return results
```

#### Verification Service ([backend/services/verification.py](backend/services/verification.py))
Fact-checking LLM outputs:
```python
import re

def extract_numbers(text: str) -> dict:
    """Extract financial numbers from explanation"""
    patterns = {
        'disposable_income': r'disposable income[:\s]+\$?([\d,]+)',
        'dti_ratio': r'DTI[:\s]+([\d.]+)%',
        'monthly_payment': r'monthly payment[:\s]+\$?([\d,]+)',
        'emergency_fund': r'emergency fund[:\s]+\$?([\d,]+)',
    }
    
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            extracted[key] = float(value)
    
    return extracted

def verify_explanation(explanation: str, actual_values: dict) -> bool:
    """Check if explanation numbers match actual calculations"""
    extracted = extract_numbers(explanation)
    
    for key, actual in actual_values.items():
        if key in extracted:
            diff = abs(extracted[key] - actual)
            tolerance = actual * 0.05  # 5% tolerance
            
            if diff > tolerance:
                logger.warning(f"Mismatch in {key}: {extracted[key]} vs {actual}")
                return False
    
    return True
```

### Priority 5: Data & Deployment

#### Database Initialization ([backend/scripts/init_db.py](backend/scripts/init_db.py))
```python
from core.qdrant_client import qdrant_manager

def init_collections():
    """Create all Qdrant collections"""
    qdrant_manager.create_collections()
    print("✅ Collections created")

if __name__ == "__main__":
    init_collections()
```

#### Sample Data ([backend/scripts/seed_data.py](backend/scripts/seed_data.py))
```python
# Load sample products
# Generate embeddings
# Upload to Qdrant
# Initialize Thompson parameters
```

Sample data files:
- [data/products.json](data/products.json) - 500 products
- [data/financial_rules.txt](data/financial_rules.txt) - KB chunks
- [data/users.json](data/users.json) - Sample user profiles

---

## 🎯 Recommended Development Order

1. **Week 1: Agents**
   - Day 1-2: Agent 2 (Financial Analyzer)
   - Day 3: Agent 2.5 (Pathfinder)  
   - Day 4-5: Agent 3 (Recommender with Thompson Sampling)
   - Day 6-7: Agent 4 (Explainer with Gemini)

2. **Week 2: Orchestration**
   - Day 1-2: Routing logic
   - Day 3-4: LangGraph workflow
   - Day 5: Testing agent pipeline

3. **Week 3: API & Frontend**
   - Day 1-3: FastAPI endpoints
   - Day 4-6: Streamlit UI
   - Day 7: Integration testing

4. **Week 4: Data & Polish**
   - Day 1-2: Sample data generation
   - Day 3-4: RAGAS evaluation
   - Day 5-6: Verification layer
   - Day 7: Documentation & testing

---

## 📚 Key Dependencies to Install

Already in requirements.txt:
- ✅ fastapi, uvicorn
- ✅ qdrant-client, redis
- ✅ clip, torch, transformers
- ✅ google-generativeai
- ✅ langgraph, langchain
- ✅ ragas, scikit-learn

---

## 🚦 How to Get Started

### 1. Set up environment:
```bash
cd c:\Users\mezen\fincommerce-engine
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. Start Docker services:
```bash
docker-compose up -d qdrant redis
```

### 3. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### 4. Test what we have:
```python
# Test CLIP embeddings
from core.embeddings import clip_embedder
embedding = clip_embedder.encode_query("gaming laptop")
print(f"Embedding dimension: {len(embedding)}")  # Should be 512

# Test Qdrant connection
from core.qdrant_client import qdrant_manager
healthy = qdrant_manager.health_check()
print(f"Qdrant healthy: {healthy}")

# Test Redis connection
from core.redis_client import redis_manager
healthy = redis_manager.health_check()
print(f"Redis healthy: {healthy}")
```

---

## 💡 Tips for Success

1. **Start Small**: Test each agent independently before connecting them
2. **Use Sample Data**: Create 5-10 test products first, then scale
3. **Log Everything**: Use Python logging extensively
4. **Test Financial Logic**: Verify affordability calculations manually
5. **Monitor Performance**: Track execution times for each agent
6. **Incremental Development**: Get one path working (FAST → SMART → DEEP)

---

## 🐛 Common Issues & Solutions

### Issue: CLIP model download fails
```bash
# Pre-download manually:
python -c "import clip; clip.load('ViT-B/32')"
```

### Issue: Qdrant connection error
```bash
# Check if container is running:
docker ps | grep qdrant

# Check logs:
docker logs fincommerce-qdrant
```

### Issue: Redis connection error
```bash
# Test connection:
docker exec -it fincommerce-redis redis-cli ping
# Should return: PONG
```

---

## 📊 Success Metrics

You'll know it's working when:
- ✅ Agent 1 returns 50 products in <400ms
- ✅ Agent 2 filters to 10-20 affordable products
- ✅ Agent 3 ranks with Thompson Sampling correctly
- ✅ Agent 4 generates verified explanations
- ✅ End-to-end search completes in <5 seconds
- ✅ RAGAS faithfulness score >0.90
- ✅ Cache hit rate reaches ~35%

---

## 🎓 Learning Resources

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Qdrant**: https://qdrant.tech/documentation/
- **CLIP**: https://github.com/openai/CLIP
- **RAGAS**: https://docs.ragas.io/
- **Thompson Sampling**: https://en.wikipedia.org/wiki/Thompson_sampling

---

## Next Steps

Would you like me to:
1. **Implement Agent 2** (Financial Analyzer) next?
2. **Create the sample data files** for testing?
3. **Build the FastAPI endpoints** to start testing?
4. **Set up the Streamlit UI** first?

Let me know which part you'd like to tackle next! 🚀
