# Redis Client Quick Reference Guide

## Import

```python
from core.redis_client import redis_manager
```

---

## 🔍 CACHE OPERATIONS

### Cache Search Results

```python
# Simple caching (query-based)
results = [{'product_id': 'PROD001', 'name': 'Laptop', 'price': 999}]
redis_manager.cache_search_results("gaming laptop", results=results, ttl=3600)

# User-specific caching
response = {'products': results, 'count': 1}
redis_manager.cache_search_results(
    query="gaming laptop",
    user_id="user123",
    response=response,
    ttl=3600
)
```

### Retrieve Cached Search

```python
# Simple retrieval
cached = redis_manager.get_cached_search_results("gaming laptop")
if cached:
    print(f"Cache hit! {len(cached)} results")

# User-specific retrieval
cached = redis_manager.get_cached_search("gaming laptop", "user123")
```

### Cache Products

```python
# Cache product details
product = {'product_id': 'PROD001', 'name': 'Laptop', 'price': 999}
redis_manager.cache_product('PROD001', product, ttl_seconds=3600)

# Retrieve cached product
cached_product = redis_manager.get_cached_product('PROD001')
```

### Cache Management

```python
# Invalidate specific pattern
redis_manager.invalidate_cache("search:*")  # Clear all search caches
redis_manager.invalidate_cache("product:LAPTOP_*")  # Clear laptop caches

# Invalidate user cache
redis_manager.invalidate_user_cache("user123")

# Get cache statistics
stats = redis_manager.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2f}%")
print(f"Total keys: {stats['total_keys']}")
```

---

## 🎯 THOMPSON SAMPLING

### Initialize Thompson Parameters

```python
# Initialize for new product (α=1.0, β=1.0)
redis_manager.initialize_thompson_params("PROD001", alpha=1.0, beta=1.0)
```

### Get Thompson Parameters

```python
params = redis_manager.get_thompson_params("PROD001")
if params:
    print(f"α={params['alpha']}, β={params['beta']}")
    print(f"Conversion rate: {params['conversion_rate']:.3f}")
```

### Set Thompson Parameters

```python
# Set parameters directly
redis_manager.set_thompson_params("PROD001", alpha=5.0, beta=2.0)
```

### Update Thompson Parameters

```python
# Update based on user signals
redis_manager.update_thompson_params("PROD001", signal_weight=1.0)   # Purchase
redis_manager.update_thompson_params("PROD001", signal_weight=0.5)   # Click
redis_manager.update_thompson_params("PROD001", signal_weight=-0.5)  # Skip
redis_manager.update_thompson_params("PROD001", signal_weight=-1.0)  # Reject
```

### Thompson Statistics

```python
stats = redis_manager.get_thompson_stats()
print(f"Products tracked: {stats['products_tracked']}")
print(f"Average α: {stats['avg_alpha']:.2f}")
print(f"Average β: {stats['avg_beta']:.2f}")
print(f"Average conversion: {stats['avg_conversion_rate']:.3f}")
```

---

## 👤 SESSION MANAGEMENT

### Create Session

```python
import time

session_data = {
    'user_id': 'user123',
    'query': 'laptop',
    'timestamp': time.time(),
    'preferences': {'budget': 1000}
}

redis_manager.create_session('session_abc', session_data, ttl_seconds=86400)
```

### Get Session

```python
session = redis_manager.get_session('session_abc')
if session:
    print(f"User: {session['user_id']}")
```

### Update Session

```python
session_data['last_action'] = 'search'

# Update and extend TTL
redis_manager.update_session('session_abc', session_data, extend_ttl=True)

# Update without extending TTL
redis_manager.update_session('session_abc', session_data, extend_ttl=False)
```

### Delete Session

```python
redis_manager.delete_session('session_abc')
```

---

## 📊 METRICS & COUNTERS

### Increment Counter

```python
# Increment by 1
redis_manager.increment_counter("api:search:calls")

# Increment by custom amount
redis_manager.increment_counter("api:errors", amount=5)
```

### Get Counter

```python
count = redis_manager.get_counter("api:search:calls")
print(f"API calls: {count}")
```

### Reset Counter

```python
redis_manager.reset_counter("api:search:calls")
```

### Get All Metrics

```python
metrics = redis_manager.get_all_metrics()
for name, value in metrics.items():
    print(f"{name}: {value}")
```

---

## ⏱️ PERFORMANCE MONITORING

### Record Timing

```python
import time

start = time.time()
# ... perform operation ...
duration_ms = (time.time() - start) * 1000

redis_manager.record_timing("agent1_execution", duration_ms)
```

### Get Timing Statistics

```python
stats = redis_manager.get_timing_stats("agent1_execution")
if stats:
    print(f"Average: {stats['avg']:.2f}ms")
    print(f"Min: {stats['min']:.2f}ms")
    print(f"Max: {stats['max']:.2f}ms")
    print(f"P50: {stats['p50']:.2f}ms")
    print(f"P95: {stats['p95']:.2f}ms")
    print(f"P99: {stats['p99']:.2f}ms")
```

---

## 🏥 HEALTH & DIAGNOSTICS

### Health Check

```python
if redis_manager.health_check():
    print("Redis is healthy!")
else:
    print("Redis is down!")
```

### Memory Info

```python
memory = redis_manager.get_memory_info()
print(f"Used memory: {memory['used_memory_human']}")
print(f"Peak memory: {memory['used_memory_peak_mb']:.2f} MB")
print(f"Max memory: {memory['maxmemory_mb']}")
print(f"Fragmentation ratio: {memory['mem_fragmentation_ratio']:.2f}")
```

### Flush All (CAUTION!)

```python
# This deletes ALL data including Thompson parameters!
# Only use in development/testing
redis_manager.flush_all(confirm=True)
```

---

## 🔑 KEY PATTERNS

```python
# Search cache (simple)
"search:{query}"

# Search cache (user-specific)
"search:{query_hash}:{user_id}"

# Product cache
"product:{product_id}"

# Thompson parameters
"thompson:{product_id}"

# Sessions
"session:{session_id}"

# Counters
"counter:{counter_name}"

# Timings
"timing:{operation}"
```

---

## 💡 USAGE EXAMPLES

### Example 1: Search with Caching

```python
from core.redis_client import redis_manager
from core.qdrant_client import qdrant_manager
from core.embeddings import clip_embedder

def search_products(query: str, user_id: str = "default"):
    # Try cache first
    cached = redis_manager.get_cached_search_results(query)
    
    if cached:
        print("Cache hit!")
        return cached
    
    # Cache miss - search Qdrant
    print("Cache miss - searching Qdrant...")
    embedding = clip_embedder.encode_query(query)
    results = qdrant_manager.search_products(embedding, top_k=10)
    
    # Cache results
    products = [r.payload for r in results]
    redis_manager.cache_search_results(query, results=products, ttl=3600)
    
    return products
```

### Example 2: Thompson Sampling Integration

```python
def track_user_action(product_id: str, action: str):
    """Track user action and update Thompson parameters"""
    
    # Map actions to signal weights
    signal_weights = {
        'purchase': 1.0,
        'click': 0.5,
        'skip': -0.5,
        'reject': -1.0
    }
    
    signal = signal_weights.get(action, 0)
    
    if signal != 0:
        redis_manager.update_thompson_params(product_id, signal)
        redis_manager.increment_counter(f"thompson:updates:{action}")
        
        print(f"Updated Thompson params for {product_id} (action: {action})")
```

### Example 3: Session-Based Personalization

```python
def get_user_context(session_id: str):
    """Get user context from session"""
    
    session = redis_manager.get_session(session_id)
    
    if not session:
        # Create new session
        session = {
            'user_id': 'anonymous',
            'created_at': time.time(),
            'searches': []
        }
        redis_manager.create_session(session_id, session)
    
    return session

def update_user_search(session_id: str, query: str):
    """Update user session with new search"""
    
    session = get_user_context(session_id)
    session['searches'].append({
        'query': query,
        'timestamp': time.time()
    })
    
    redis_manager.update_session(session_id, session, extend_ttl=True)
```

### Example 4: Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                redis_manager.record_timing(operation_name, duration_ms)
        return wrapper
    return decorator

@monitor_performance("agent1_execution")
def execute_agent1(query: str):
    # Agent logic here
    pass
```

---

## 🚀 Best Practices

1. **Always check cache first** before expensive operations
2. **Set appropriate TTLs** (1 hour for search results, 24 hours for sessions)
3. **Use pattern-based invalidation** for bulk cache clearing
4. **Track Thompson signals** for all user interactions
5. **Monitor timing stats** for performance optimization
6. **Use health checks** before critical operations
7. **Increment counters** for important events
8. **Never use flush_all()** in production

---

## ⚠️ Important Notes

- All methods include error handling and logging
- Cache keys are automatically generated with hashing
- Thompson parameters persist indefinitely (no TTL)
- Sessions default to 24-hour TTL
- Timing stats keep last 100 measurements
- scan_iter is used for better performance than keys()
- JSON serialization handles datetime objects automatically

---

**For more details, see:** `backend/core/redis_client.py`
