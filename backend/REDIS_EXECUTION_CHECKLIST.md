# 🚀 Redis Layer Execution Checklist

## Prerequisites

Before running the scripts, ensure:

- [ ] **Docker is running**
  ```bash
  docker --version
  ```

- [ ] **Redis container is running**
  ```bash
  docker ps | grep redis
  ```
  If not running:
  ```bash
  docker-compose up -d redis
  ```

- [ ] **Qdrant container is running**
  ```bash
  docker ps | grep qdrant
  ```
  If not running:
  ```bash
  docker-compose up -d qdrant
  ```

- [ ] **Qdrant is populated with products**
  ```bash
  python backend/scripts/populate_qdrant.py
  ```

---

## Execution Steps

### Step 1: Initialize Thompson Parameters ⚡

**Script:** `backend/scripts/initialize_thompson_redis.py`

**What it does:**
- Retrieves all product IDs from Qdrant
- Initializes Thompson Sampling parameters (α=1.0, β=1.0) in Redis
- Skips already-initialized products
- Verifies all products have parameters
- Shows sample parameters and statistics

**Run:**
```bash
python backend/scripts/initialize_thompson_redis.py
```

**Expected Output:**
```
================================================================================
🚀 INITIALIZING THOMPSON SAMPLING PARAMETERS IN REDIS
================================================================================

1️⃣ Checking Redis connection...
✅ Redis is healthy

2️⃣ Checking Qdrant connection...
✅ Qdrant is healthy

3️⃣ Retrieving products from Qdrant...
✅ Retrieved 50 product IDs

4️⃣ Initializing Thompson parameters...
✅ Initialized 50 products, skipped 0 (already initialized)

5️⃣ Verifying initialization...
✅ All products have Thompson parameters

6️⃣ Sample parameters:
  PROD001: α=1.00, β=1.00, conversion_rate=0.500
  PROD002: α=1.00, β=1.00, conversion_rate=0.500
  ...

7️⃣ Thompson Sampling statistics:
  Products tracked: 50
  Average α: 1.00
  Average β: 1.00
  Average conversion: 0.500

================================================================================
✅ THOMPSON INITIALIZATION COMPLETE!
================================================================================
```

**Success Criteria:**
- ✅ All products initialized
- ✅ Verification passed
- ✅ Statistics show correct averages

---

### Step 2: Test Redis Functionality 🧪

**Script:** `backend/scripts/test_redis.py`

**What it does:**
- Tests health check
- Tests caching (search results, products)
- Tests Thompson parameters (initialize, get, set, update)
- Tests session management (create, get, update, delete)
- Tests metrics and counters
- Tests memory info

**Run:**
```bash
python backend/scripts/test_redis.py
```

**Expected Output:**
```
================================================================================
🔍 REDIS FUNCTIONALITY TESTS
================================================================================

================================================================================
TEST 1: HEALTH CHECK
================================================================================
✅ Redis is healthy

================================================================================
TEST 2: CACHING
================================================================================
Caching search results for 'test laptop'...
Retrieving cached results...
✅ Cache HIT: 1 results
Testing cache miss...
✅ Cache MISS (as expected)
Testing product caching...
✅ Product cached and retrieved: Test Laptop

Cache statistics:
  total_keys: 5
  search_cache_entries: 1
  product_cache_entries: 1
  thompson_params_count: 51
  keyspace_hits: 2
  keyspace_misses: 1
  hit_rate: 66.67

================================================================================
TEST 3: THOMPSON PARAMETERS
================================================================================
Initializing Thompson params for TEST_PRODUCT_001...
✅ Got params: α=1.0, β=1.0
Simulating purchase (α += 1.0)...
✅ Params updated: α=2.0, β=1.0
Testing update_thompson_params (simulate click)...
✅ Update method works: α=2.5

Thompson statistics:
  products_tracked: 52
  avg_alpha: 1.03
  avg_beta: 1.00
  avg_conversion_rate: 0.503

================================================================================
TEST 4: SESSION MANAGEMENT
================================================================================
Creating session test_session_123...
✅ Retrieved session: user_id=user_test
Updating session...
✅ Session updated successfully
Deleting session...
✅ Session deleted successfully

================================================================================
TEST 5: METRICS & COUNTERS
================================================================================
Resetting counter 'test:counter'...
Incrementing counter 5 times...
✅ Counter value: 5

Recording operation timings...
✅ Timing statistics:
  count: 5
  avg: 150.00ms
  min: 100.00ms
  max: 200.00ms
  p50: 150.00ms
  p95: 200.00ms
  p99: 200.00ms

All metrics:
  test:counter: 5

================================================================================
TEST 6: MEMORY INFO
================================================================================
✅ Memory information:
  used_memory_mb: 2.45
  used_memory_peak_mb: 2.50
  used_memory_human: 2.45M
  maxmemory_mb: unlimited
  mem_fragmentation_ratio: 1.05

================================================================================
SUMMARY
================================================================================
✅ PASS: Health Check
✅ PASS: Caching
✅ PASS: Thompson Parameters
✅ PASS: Session Management
✅ PASS: Metrics & Counters
✅ PASS: Memory Info

================================================================================
✅ ALL TESTS PASSED
Redis is fully operational!
================================================================================
```

**Success Criteria:**
- ✅ All 6 tests pass
- ✅ No errors in output
- ✅ Cache hit/miss working correctly
- ✅ Thompson parameters updating correctly

---

### Step 3: Verify Knowledge & Memory Layer 🔍

**Script:** `backend/scripts/verify_knowledge_layer.py`

**What it does:**
- Verifies Qdrant and Redis infrastructure health
- Checks data population in both systems
- Tests Qdrant-Redis integration
- Verifies Thompson Sampling functionality
- Checks cache performance
- Monitors memory usage

**Run:**
```bash
python backend/scripts/verify_knowledge_layer.py
```

**Expected Output:**
```
================================================================================
🔍 KNOWLEDGE & MEMORY LAYER VERIFICATION
================================================================================

================================================================================
INFRASTRUCTURE HEALTH
================================================================================
✅ Qdrant: HEALTHY
✅ Redis: HEALTHY

================================================================================
DATA POPULATION
================================================================================
Qdrant Products: 50
Qdrant Financial Rules: 25
Redis Thompson Params: 50
Redis Cache Entries: 5

================================================================================
INTEGRATION TEST
================================================================================
Searching Qdrant for 'gaming laptop'...
✅ Found 5 products

Checking Thompson params for PROD001...
✅ Thompson params: α=1.0, β=1.0

Caching product in Redis...
✅ Product cached and retrieved: Gaming Laptop XYZ

Caching search results...
✅ Search results cached and retrieved: 5 results

================================================================================
THOMPSON SAMPLING VERIFICATION
================================================================================
Products tracked: 50
Average α: 1.00
Average β: 1.00
Average conversion rate: 0.500
✅ Thompson Sampling is operational

================================================================================
CACHE PERFORMANCE
================================================================================
Total keys: 8
Search cache entries: 2
Product cache entries: 2
Thompson params: 50
Keyspace hits: 5
Keyspace misses: 2
Hit rate: 71.43%
✅ Cache statistics retrieved

================================================================================
MEMORY USAGE
================================================================================
Used memory: 2.50M
Peak memory: 2.55 MB
Max memory: unlimited
Fragmentation ratio: 1.05
✅ Memory info retrieved

================================================================================
SUMMARY
================================================================================
✅ PASS: Infrastructure Health
✅ PASS: Data Population
✅ PASS: Qdrant-Redis Integration
✅ PASS: Thompson Sampling
✅ PASS: Cache Performance
✅ PASS: Memory Usage

================================================================================
✅ KNOWLEDGE & MEMORY LAYER COMPLETE!
Both Qdrant and Redis are operational!

🎯 Next Steps:
   1. Test agent integration with Thompson Sampling
   2. Monitor cache hit rates
   3. Track Thompson parameter evolution
================================================================================
```

**Success Criteria:**
- ✅ All 6 verification tests pass
- ✅ Qdrant and Redis both healthy
- ✅ Data populated in both systems
- ✅ Integration working correctly

---

## Troubleshooting

### Issue: Redis is not healthy

**Solution:**
```bash
# Check if Redis is running
docker ps | grep redis

# If not running, start it
docker-compose up -d redis

# Check logs
docker logs <redis_container_id>
```

### Issue: Qdrant is not healthy

**Solution:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker-compose up -d qdrant

# Check logs
docker logs <qdrant_container_id>
```

### Issue: No products found in Qdrant

**Solution:**
```bash
# Populate Qdrant with products
python backend/scripts/populate_qdrant.py
```

### Issue: Thompson initialization fails

**Possible causes:**
1. Redis not running
2. Qdrant not populated
3. Connection issues

**Solution:**
```bash
# Check Redis
python -c "from core.redis_client import redis_manager; print(redis_manager.health_check())"

# Check Qdrant
python -c "from core.qdrant_client import qdrant_manager; print(qdrant_manager.health_check())"

# Verify products exist
python backend/scripts/verify_qdrant.py
```

### Issue: Tests fail

**Solution:**
1. Check error messages in output
2. Verify Docker containers are running
3. Check Redis logs: `docker logs <redis_container_id>`
4. Ensure Qdrant is populated
5. Try flushing Redis (CAUTION - development only):
   ```python
   from core.redis_client import redis_manager
   redis_manager.flush_all(confirm=True)
   ```

---

## Post-Execution Verification

After running all scripts, verify:

- [ ] **Thompson parameters initialized**
  ```bash
  python -c "from core.redis_client import redis_manager; print(redis_manager.get_thompson_stats())"
  ```

- [ ] **Cache working**
  ```bash
  python -c "from core.redis_client import redis_manager; print(redis_manager.get_cache_stats())"
  ```

- [ ] **All tests passed**
  - initialize_thompson_redis.py: ✅
  - test_redis.py: ✅
  - verify_knowledge_layer.py: ✅

---

## Next Steps After Completion

1. **Integrate with Agents**
   - Update agents to use Thompson Sampling
   - Implement cache-first search strategy
   - Track user signals for RL

2. **Monitor Performance**
   - Track cache hit rates
   - Monitor Thompson parameter evolution
   - Analyze timing statistics

3. **Optimize**
   - Adjust TTLs based on usage patterns
   - Fine-tune Thompson Sampling signals
   - Monitor memory usage

---

## Quick Commands Reference

```bash
# Initialize Thompson parameters
python backend/scripts/initialize_thompson_redis.py

# Test Redis functionality
python backend/scripts/test_redis.py

# Verify complete layer
python backend/scripts/verify_knowledge_layer.py

# Check Redis health
python -c "from core.redis_client import redis_manager; print('Healthy' if redis_manager.health_check() else 'Down')"

# Get Thompson stats
python -c "from core.redis_client import redis_manager; import json; print(json.dumps(redis_manager.get_thompson_stats(), indent=2))"

# Get cache stats
python -c "from core.redis_client import redis_manager; import json; print(json.dumps(redis_manager.get_cache_stats(), indent=2))"
```

---

**Status:** Ready for execution! 🚀
