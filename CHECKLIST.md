# ✅ PriceSense - Setup Checklist

## 🎯 Initial Setup (15 minutes)

- [ ] **1. Get Google Gemini API Key**
  - Visit: https://makersuite.google.com/app/apikey
  - Create account (free)
  - Generate API key
  - Copy key to clipboard

- [ ] **2. Configure Environment**
  ```powershell
  cd c:\Users\mezen\fincommerce-engine
  Copy-Item .env.example .env
  notepad .env
  # Paste your GOOGLE_API_KEY
  ```

- [ ] **3. Start Docker Services**
  ```powershell
  docker-compose up -d qdrant redis
  docker ps  # Verify both running
  ```

- [ ] **4. Install Python Dependencies**
  ```powershell
  cd backend
  pip install -r requirements.txt
  # Wait 5-10 minutes for CLIP model download
  ```

- [ ] **5. Initialize Databases**
  ```powershell
  python scripts/init_db.py
  # Should see: ✅ Collections created
  ```

- [ ] **6. Load Sample Data**
  ```powershell
  python scripts/seed_data.py
  # Should see: 8 products, 5 rules, 3 users
  ```

- [ ] **7. Run Tests**
  ```powershell
  python scripts/test_system.py
  # All tests should pass
  ```

---

## ✅ OR: Automated Setup (5 minutes)

- [ ] **Run setup script**
  ```powershell
  cd c:\Users\mezen\fincommerce-engine
  .\setup.ps1
  # Follow prompts
  ```

---

## 🧪 Verification Tests

### Test 1: Docker Services
- [ ] Qdrant running on port 6333
  ```powershell
  # Visit: http://localhost:6333/dashboard
  # Should see Qdrant UI
  ```

- [ ] Redis running on port 6379
  ```powershell
  docker exec -it fincommerce-redis redis-cli ping
  # Should return: PONG
  ```

### Test 2: Python Imports
- [ ] All modules load without errors
  ```powershell
  python -c "from core.embeddings import clip_embedder; print('✅')"
  python -c "from core.qdrant_client import qdrant_manager; print('✅')"
  python -c "from core.redis_client import redis_manager; print('✅')"
  python -c "from utils.financial import FinancialCalculator; print('✅')"
  python -c "from agents.agent1_discovery import product_discovery_agent; print('✅')"
  ```

### Test 3: CLIP Embeddings
- [ ] Text embeddings work
  ```powershell
  python -c "from core.embeddings import clip_embedder; emb = clip_embedder.encode_query('test'); print(f'✅ {len(emb)} dimensions')"
  # Should print: ✅ 512 dimensions
  ```

### Test 4: Database Operations
- [ ] Qdrant search works
  ```powershell
  python -c "from core.qdrant_client import qdrant_manager; from core.embeddings import clip_embedder; emb = clip_embedder.encode_query('laptop'); results = qdrant_manager.search_products(emb, top_k=3); print(f'✅ Found {len(results)} products')"
  ```

- [ ] Redis cache works
  ```powershell
  python -c "from core.redis_client import redis_manager; redis_manager.cache_search_results('test', 'U1', {}); print('✅ Cache works')"
  ```

### Test 5: Financial Calculator
- [ ] Calculations accurate
  ```powershell
  python -c "from models.schemas import UserProfile; from utils.financial import FinancialCalculator; p = UserProfile(user_id='T', monthly_income=5000, monthly_expenses=3500, savings=15000, current_debt=5000, credit_score=720); print(f'✅ Safe limit: ${FinancialCalculator.calculate_safe_cash_limit(p):.2f}')"
  # Should print: ✅ Safe limit: $450.00
  ```

### Test 6: Agent 1
- [ ] Product discovery works
  ```powershell
  python -c "from agents.agent1_discovery import product_discovery_agent; from models.schemas import UserProfile; s = {'query': 'laptop', 'user_profile': UserProfile(user_id='T', monthly_income=5000, monthly_expenses=3500, savings=15000, current_debt=5000, credit_score=720), 'image_embedding': None, 'filters': {}, 'errors': [], 'warnings': []}; r = product_discovery_agent.execute(s); print(f'✅ {len(r[\"candidate_products\"])} products in {r[\"search_time_ms\"]}ms')"
  ```

---

## 📚 Next Steps Checklist

### Phase 1: Build Agents (Week 1)
- [ ] **Agent 2: Financial Analyzer** (6 hours)
  - [ ] Read DEVELOPMENT_GUIDE.md section on Agent 2
  - [ ] Create backend/services/rag.py
  - [ ] Create backend/agents/agent2_financial.py
  - [ ] Test with sample products
  - [ ] Verify affordability calculations

- [ ] **Agent 2.5: Budget Pathfinder** (4 hours)
  - [ ] Create backend/agents/agent2_5_pathfinder.py
  - [ ] Implement K-Means alternatives
  - [ ] Test creative financing paths

- [ ] **Agent 3: Smart Recommender** (8 hours)
  - [ ] Create backend/services/thompson.py
  - [ ] Create backend/agents/agent3_recommender.py
  - [ ] Implement Thompson Sampling
  - [ ] Add collaborative filtering
  - [ ] Test ranking logic

- [ ] **Agent 4: Explainer** (10 hours)
  - [ ] Create backend/utils/llm.py (Gemini wrapper)
  - [ ] Create backend/services/verification.py
  - [ ] Create backend/agents/agent4_explainer.py
  - [ ] Test explanation generation
  - [ ] Verify fact-checking works

### Phase 2: Orchestration (Week 2)
- [ ] **Complexity Router** (3 hours)
  - [ ] Create backend/services/routing.py
  - [ ] Test path decisions
  - [ ] Verify threshold logic

- [ ] **LangGraph Workflow** (5 hours)
  - [ ] Create backend/services/orchestrator.py
  - [ ] Connect all 5 agents
  - [ ] Add conditional routing
  - [ ] Test end-to-end flow

### Phase 3: API & Frontend (Week 3)
- [ ] **FastAPI Backend** (8 hours)
  - [ ] Create backend/main.py
  - [ ] Create backend/routers/search.py
  - [ ] Create backend/routers/feedback.py
  - [ ] Create backend/routers/monitoring.py
  - [ ] Test all endpoints

- [ ] **Streamlit Frontend** (8 hours)
  - [ ] Create frontend/app.py
  - [ ] Create frontend/components/search_bar.py
  - [ ] Create frontend/components/profile_form.py
  - [ ] Create frontend/components/results_display.py
  - [ ] Test UI interactions

### Phase 4: Quality & Polish (Week 4)
- [ ] **RAGAS Integration** (4 hours)
  - [ ] Create backend/utils/ragas_eval.py
  - [ ] Add quality metrics
  - [ ] Test evaluation

- [ ] **Monitoring** (3 hours)
  - [ ] Create backend/services/monitoring.py
  - [ ] Add latency tracking
  - [ ] Add error monitoring

- [ ] **Documentation** (2 hours)
  - [ ] Update README with final screenshots
  - [ ] Create API documentation
  - [ ] Write deployment guide

---

## 🎯 Success Criteria

### What Works Now ✅
- [x] Docker infrastructure running
- [x] Vector search (CLIP + Qdrant)
- [x] Financial calculations
- [x] Agent 1 (Product Discovery)
- [x] Sample data loaded
- [x] Cache layer operational

### What Should Work When Complete ❌
- [ ] End-to-end search (<5 seconds)
- [ ] Financial analysis for all products
- [ ] Thompson Sampling learning from actions
- [ ] LLM explanations (verified, no hallucinations)
- [ ] REST API serving requests
- [ ] Web UI for user interaction
- [ ] RAGAS faithfulness >90%
- [ ] Cache hit rate ~35%

---

## 🐛 Troubleshooting Checklist

### Issue: Docker containers won't start
- [ ] Check Docker Desktop is running
- [ ] Check ports 6333, 6379 not in use
- [ ] Run: `docker-compose logs qdrant`
- [ ] Run: `docker-compose logs redis`

### Issue: CLIP model download fails
- [ ] Check internet connection
- [ ] Check disk space (need ~500MB)
- [ ] Try manual download:
  ```python
  import clip
  clip.load("ViT-B/32", device="cpu")
  ```

### Issue: "Module not found" errors
- [ ] Verify in backend directory: `cd backend`
- [ ] Check PYTHONPATH includes backend
- [ ] Reinstall: `pip install -r requirements.txt`

### Issue: Qdrant connection refused
- [ ] Verify container running: `docker ps`
- [ ] Check logs: `docker logs fincommerce-qdrant`
- [ ] Restart: `docker-compose restart qdrant`

### Issue: Redis connection timeout
- [ ] Verify container running: `docker ps`
- [ ] Test ping: `docker exec -it fincommerce-redis redis-cli ping`
- [ ] Restart: `docker-compose restart redis`

### Issue: Financial calculations incorrect
- [ ] Manually verify with calculator
- [ ] Check UserProfile values are correct
- [ ] Review utils/financial.py logic
- [ ] Add debug logging

---

## 📊 Progress Tracking

### Current Status: 40% Complete
- ✅ Infrastructure: 100%
- ✅ Data Models: 100%
- ✅ Database Clients: 100%
- ✅ AI/ML Core: 100%
- ✅ Financial Engine: 100%
- ✅ Agent 1: 100%
- ⬜ Agent 2: 0%
- ⬜ Agent 3: 0%
- ⬜ Agent 4: 0%
- ⬜ Orchestration: 0%
- ⬜ API: 0%
- ⬜ Frontend: 0%

### Estimated Remaining: 43-59 hours
- Week 1: Agents (20-28 hours)
- Week 2: Orchestration (6-8 hours)
- Week 3: API + Frontend (12-16 hours)
- Week 4: Quality + Polish (5-7 hours)

---

## 🎉 Completion Celebration

When you finish:
- [ ] Run full end-to-end search
- [ ] Verify all RAGAS metrics >target
- [ ] Test with real user scenarios
- [ ] Deploy to production
- [ ] Share your achievement!

---

**Last Updated:** January 25, 2026  
**Status:** Foundation Complete (40%)  
**Next:** Build Agent 2 (Financial Analyzer)

Good luck! You've got this! 💪🚀
