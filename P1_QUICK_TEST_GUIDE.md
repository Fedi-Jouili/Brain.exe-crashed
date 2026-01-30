# P1 QUICK TEST GUIDE

## 🎯 Quick Testing Commands

### Start Backend
```bash
cd backend
python main.py
# Wait for: "📡 API running at: http://localhost:8000"
```

---

## ✅ Test Suite Execution

### Run All Tests
```bash
pytest backend/tests/ -v
# Expected: 15+ tests pass in ~10s
```

### Run Individual Test Files
```bash
# E2E test (user journey + RL learning)
pytest backend/tests/test_e2e.py -v -s

# Thompson Sampling unit tests
pytest backend/tests/test_thompson_sampling.py -v

# Cache unit tests
pytest backend/tests/test_cache.py -v
```

---

## 🧪 Manual Cache Testing

### Test 1: Verify Cache Miss → Cache Hit
```bash
# First request (MISS)
curl -X POST "http://localhost:8000/api/search" \
  -F "query=laptop under $1000" \
  -F "max_results=5"

# Check response: "cache_hit": false, "execution_time_ms": ~1500

# Second request (HIT)
curl -X POST "http://localhost:8000/api/search" \
  -F "query=laptop under $1000" \
  -F "max_results=5"

# Check response: "cache_hit": true, "execution_time_ms": <100
```

**Expected Result**: 2nd request is **10-20x faster**

---

### Test 2: Check Cache Stats
```bash
curl http://localhost:8000/api/cache/stats | jq
```

**Expected Output**:
```json
{
  "cache_enabled": true,
  "total_keys": 234,
  "memory_usage_mb": 12.34,
  "search_cache_keys": 45,
  "cache_hits": 120,
  "cache_misses": 30,
  "hit_rate_percent": 80.0
}
```

---

### Test 3: Clear Cache
```bash
curl -X DELETE "http://localhost:8000/api/cache/clear?pattern=search:*&confirm=true" | jq
```

**Expected Output**:
```json
{
  "cleared": 45,
  "pattern": "search:*",
  "message": "Successfully cleared 45 cache entries"
}
```

---

## 🤖 Thompson Sampling Testing

### Test Learning Cycle
```bash
# 1. Search for products
curl -X POST "http://localhost:8000/api/search" \
  -F "query=laptop" \
  -F "max_results=10" | jq '.recommendations[0]'

# Note the product_id from first result

# 2. Send purchase signal
curl -X POST "http://localhost:8000/api/interact" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "TEST_USER",
    "product_id": "PROD_123",  # Use actual product_id
    "action": "purchase"
  }' | jq

# Expected: {"alpha": 2.0, "beta": 1.0, "conversion_rate": 0.667}

# 3. Search again
curl -X POST "http://localhost:8000/api/search" \
  -F "query=laptop" \
  -F "max_results=10" | jq '.recommendations[0]'

# Product PROD_123 should rank higher now
```

---

## 📊 Success Criteria Verification

### Cache Performance
- ✅ First request: cache_hit=false, time ~1500ms
- ✅ Second request: cache_hit=true, time <100ms
- ✅ Hit rate after 10 queries: >40%

### Thompson Sampling
- ✅ Alpha increases after positive signals
- ✅ Beta increases after negative signals
- ✅ Product ranking improves after purchase

### Test Coverage
- ✅ E2E test passes (user journey)
- ✅ Thompson tests pass (8 tests)
- ✅ Cache tests pass (6 tests)

---

## 🐛 Common Issues

### Issue: "Connection refused" in tests
**Fix**: Start backend first
```bash
cd backend
python main.py
# In another terminal:
pytest backend/tests/ -v
```

---

### Issue: Redis connection failed
**Fix**: Start Redis
```bash
redis-server
# Or if using Docker:
docker start redis
```

---

### Issue: Tests timeout
**Fix**: Increase timeout in pytest.ini
```ini
[pytest]
timeout = 60
```

---

## 🎯 Quick Validation Checklist

Before deployment, verify:
- [ ] Backend starts without errors
- [ ] Redis connection works (`redis-cli ping`)
- [ ] Cache stats endpoint returns data
- [ ] First search is cache miss
- [ ] Second identical search is cache hit
- [ ] Thompson Sampling updates parameters
- [ ] All pytest tests pass

---

## 📚 API Documentation

Full API docs: http://localhost:8000/api/docs

**New Endpoints**:
- `GET /api/cache/stats` - Cache statistics
- `DELETE /api/cache/clear` - Clear cache
- `GET /api/cache/inspect/{key}` - Inspect entry
- `POST /api/interact` - Thompson Sampling feedback

---

## 🚀 Production Deployment

1. **Pre-flight checks**:
   ```bash
   pytest backend/tests/ -v
   # All tests must pass
   ```

2. **Deploy**:
   - Upload `backend/main.py`
   - Restart backend service
   - Verify Redis is running

3. **Monitor**:
   - Cache hit rate (target: >35%)
   - Average latency (target: <1000ms)
   - Error rate (should be 0%)

---

**Status**: 🟢 PRODUCTION READY

All P1 features implemented and tested ✅
