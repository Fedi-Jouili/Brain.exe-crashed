"""
Redis client for caching and Thompson Sampling state
"""
import redis
import json
import hashlib
import logging
import time
import statistics
from typing import Optional, Dict, Any, List
from datetime import timedelta
from core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis operations for caching and RL state"""
    
    def __init__(self):
        """Initialize Redis client"""
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        self.cache_ttl = settings.redis_cache_ttl
    
    # ========================================================================
    # CACHE OPERATIONS (Query Results & Products)
    # ========================================================================
    
    def generate_cache_key(self, query: str, user_id: str) -> str:
        """
        Generate cache key from query and user ID
        
        Format: search:{query_hash}:{user_id}
        """
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:12]
        return f"search:{query_hash}:{user_id}"
    
    def get_cached_search(self, query: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached search results
        
        Returns:
            Cached response dict or None if not found
        """
        cache_key = self.generate_cache_key(query, user_id)
        
        try:
            cached_data = self.client.get(cache_key)
            if cached_data:
                logger.info(f"Cache HIT for key: {cache_key}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for key: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving cache: {e}")
            return None
    
    def cache_search_results(
        self,
        query: str,
        user_id: str = "default",
        results: Optional[List[Dict]] = None,
        response: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results with TTL
        
        Args:
            query: Original search query
            user_id: User identifier (default: "default")
            results: List of search results (product dicts) - for simple caching
            response: Complete search response to cache - for full response caching
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully
            
        Example:
            >>> redis_manager.cache_search_results("gaming laptop", results=results, ttl_seconds=3600)
        """
        ttl = ttl or self.cache_ttl
        
        try:
            # Support both simple results list and full response dict
            if results is not None:
                # Simple cache key for query-only caching
                cache_key = f"search:{query.lower().strip()}"
                results_json = json.dumps(results, default=str)
                self.client.setex(cache_key, ttl, results_json)
                logger.debug(f"Cached search results for '{query}' (TTL: {ttl}s)")
            elif response is not None:
                # User-specific cache key
                cache_key = self.generate_cache_key(query, user_id)
                self.client.setex(
                    cache_key,
                    ttl,
                    json.dumps(response, default=str)
                )
                logger.info(f"Cached response for key: {cache_key} (TTL: {ttl}s)")
            else:
                logger.warning("cache_search_results called without results or response")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error caching results: {e}")
            return False
    
    def get_cached_search_results(self, query: str) -> Optional[List[Dict]]:
        """
        Retrieve cached search results (simple query-based caching)
        
        Args:
            query: Search query string
            
        Returns:
            List of cached results or None if cache miss
            
        Example:
            >>> results = redis_manager.get_cached_search_results("gaming laptop")
            >>> if results:
            ...     print(f"Cache hit! {len(results)} results")
        """
        try:
            cache_key = f"search:{query.lower().strip()}"
            
            # Get from cache
            cached_data = self.client.get(cache_key)
            
            if cached_data:
                results = json.loads(cached_data)
                logger.debug(f"Cache HIT for '{query}' ({len(results)} results)")
                return results
            
            logger.debug(f"Cache MISS for '{query}'")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached results: {e}")
            return None
    
    def cache_product(
        self,
        product_id: str,
        product_data: Dict,
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Cache product details
        
        Args:
            product_id: Product identifier
            product_data: Product details dict
            ttl_seconds: Time to live (default 1 hour)
            
        Returns:
            True if cached successfully
        """
        try:
            cache_key = f"product:{product_id}"
            
            product_json = json.dumps(product_data, default=str)
            
            self.client.setex(cache_key, ttl_seconds, product_json)
            
            logger.debug(f"Cached product {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching product {product_id}: {e}")
            return False
    
    def get_cached_product(self, product_id: str) -> Optional[Dict]:
        """
        Retrieve cached product details
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product dict or None if cache miss
        """
        try:
            cache_key = f"product:{product_id}"
            
            cached_data = self.client.get(cache_key)
            
            if cached_data:
                product = json.loads(cached_data)
                logger.debug(f"Cache HIT for product {product_id}")
                return product
            
            logger.debug(f"Cache MISS for product {product_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached product: {e}")
            return None
    
    def invalidate_cache(self, pattern: str = "*") -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Redis key pattern (default: all)
            
        Returns:
            Number of keys deleted
            
        Example:
            >>> redis_manager.invalidate_cache("search:*")  # Clear all search caches
            >>> redis_manager.invalidate_cache("product:LAPTOP_*")  # Clear laptop caches
        """
        try:
            # Find matching keys
            keys = list(self.client.scan_iter(match=pattern))
            
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries (pattern: {pattern})")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0
    
    def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a user"""
        pattern = f"search:*:{user_id}"
        return self.invalidate_cache(pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats (hits, misses, size, etc.)
        """
        try:
            info = self.client.info('stats')
            
            # Get counts by prefix
            search_cache_count = len(list(self.client.scan_iter(match="search:*")))
            product_cache_count = len(list(self.client.scan_iter(match="product:*")))
            thompson_count = len(list(self.client.scan_iter(match="thompson:*")))
            
            return {
                'total_keys': self.client.dbsize(),
                'search_cache_entries': search_cache_count,
                'product_cache_entries': product_cache_count,
                'thompson_params_count': thompson_count,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
    
    # ========================================================================
    # THOMPSON SAMPLING STATE
    # ========================================================================
    
    def get_thompson_params(self, product_id: str) -> Optional[Dict[str, float]]:
        """
        Get Thompson Sampling parameters (α, β) for a product
        
        Returns:
            {'alpha': float, 'beta': float, 'conversion_rate': float} or None
        """
        key = f"thompson:{product_id}"
        
        try:
            data = self.client.get(key)
            if data:
                params = json.loads(data)
                # Calculate conversion rate if not present
                if 'conversion_rate' not in params:
                    alpha = params['alpha']
                    beta = params['beta']
                    params['conversion_rate'] = alpha / (alpha + beta)
                return params
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting Thompson params for {product_id}: {e}")
            return None
    
    def set_thompson_params(
        self,
        product_id: str,
        alpha: float,
        beta: float
    ) -> bool:
        """
        Set Thompson Sampling parameters directly
        
        Args:
            product_id: Product identifier
            alpha: Alpha parameter (successes)
            beta: Beta parameter (failures)
            
        Returns:
            True if set successfully
            
        Example:
            >>> redis_manager.set_thompson_params("PROD001", alpha=5.0, beta=2.0)
        """
        key = f"thompson:{product_id}"
        
        try:
            # Calculate conversion rate
            conversion_rate = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
            
            params = {
                'alpha': alpha,
                'beta': beta,
                'conversion_rate': conversion_rate,
                'last_updated': time.time()
            }
            
            self.client.set(key, json.dumps(params))
            
            logger.debug(
                f"Set Thompson params for {product_id}: "
                f"α={alpha:.2f}, β={beta:.2f}, CR={conversion_rate:.3f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting Thompson params: {e}")
            return False
    
    def initialize_thompson_params(
        self,
        product_id: str,
        alpha: float = 1.0,
        beta: float = 1.0
    ) -> bool:
        """
        Initialize Thompson Sampling parameters for a product
        
        Args:
            product_id: Product identifier
            alpha: Initial alpha (default 1.0 - uniform prior)
            beta: Initial beta (default 1.0 - uniform prior)
            
        Returns:
            True if initialized successfully
            
        Example:
            >>> redis_manager.initialize_thompson_params("PROD001", alpha=1.0, beta=1.0)
        """
        # Check if already exists
        existing = self.get_thompson_params(product_id)
        
        if existing:
            logger.debug(f"Thompson params already exist for {product_id}, skipping initialization")
            return False
        
        # Initialize with provided values
        return self.set_thompson_params(product_id, alpha, beta)
    
    def update_thompson_params(
        self,
        product_id: str,
        signal_weight: float
    ) -> bool:
        """
        Update Thompson Sampling parameters based on user action
        
        Args:
            product_id: Product identifier
            signal_weight: Signal weight (+1.0 to -1.0)
                          +1.0 = strong positive (purchase)
                          +0.5 = weak positive (click)
                          -0.5 = weak negative (skip)
                          -1.0 = strong negative (reject)
            
        Returns:
            True if updated successfully
        """
        key = f"thompson:{product_id}"
        
        try:
            # Get current parameters
            params = self.get_thompson_params(product_id)
            
            if not params:
                # Initialize if doesn't exist
                alpha = settings.thompson_alpha_init
                beta = settings.thompson_beta_init
            else:
                alpha = params['alpha']
                beta = params['beta']
            
            # Update based on signal
            if signal_weight > 0:
                alpha += signal_weight
            else:
                beta += abs(signal_weight)
            
            # Save updated parameters
            return self.set_thompson_params(product_id, alpha, beta)
            
        except Exception as e:
            logger.error(f"Error updating Thompson params: {e}")
            return False
    
    def get_all_thompson_params(self) -> Dict[str, Dict[str, float]]:
        """Get Thompson parameters for all products"""
        pattern = "thompson:*"
        keys = list(self.client.scan_iter(match=pattern))
        
        results = {}
        for key in keys:
            product_id = key.split(':')[1] if ':' in key else key
            data = self.client.get(key)
            if data:
                results[product_id] = json.loads(data)
        
        return results
    
    def get_thompson_stats(self) -> Dict[str, Any]:
        """Get overall Thompson Sampling statistics"""
        all_params = self.get_all_thompson_params()
        
        if not all_params:
            return {
                'products_tracked': 0,
                'total_products': 0,
                'avg_alpha': 0,
                'avg_beta': 0,
                'avg_conversion_rate': 0
            }
        
        alphas = [p['alpha'] for p in all_params.values()]
        betas = [p['beta'] for p in all_params.values()]
        conversions = [
            a / (a + b) for a, b in zip(alphas, betas)
        ]
        
        return {
            'products_tracked': len(all_params),
            'total_products': len(all_params),
            'avg_alpha': sum(alphas) / len(alphas),
            'avg_beta': sum(betas) / len(betas),
            'avg_conversion_rate': sum(conversions) / len(conversions)
        }
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def create_session(
        self,
        session_id: str,
        session_data: Dict,
        ttl_seconds: int = 86400
    ) -> bool:
        """
        Create user session
        
        Args:
            session_id: Unique session identifier
            session_data: Session data dict
            ttl_seconds: Session lifetime (default 24 hours)
            
        Returns:
            True if created successfully
            
        Example:
            >>> session_data = {
            ...     'user_id': 'user123',
            ...     'query': 'laptop',
            ...     'timestamp': time.time()
            ... }
            >>> redis_manager.create_session('session_abc', session_data)
        """
        try:
            session_key = f"session:{session_id}"
            
            session_json = json.dumps(session_data, default=str)
            
            self.client.setex(session_key, ttl_seconds, session_json)
            
            logger.debug(f"Created session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dict or None if expired/not found
        """
        try:
            session_key = f"session:{session_id}"
            
            session_data = self.client.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            return None
    
    def update_session(
        self,
        session_id: str,
        session_data: Dict,
        extend_ttl: bool = True
    ) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            session_data: Updated session data
            extend_ttl: Whether to reset TTL (default True)
            
        Returns:
            True if updated successfully
        """
        try:
            session_key = f"session:{session_id}"
            
            session_json = json.dumps(session_data, default=str)
            
            if extend_ttl:
                # Reset TTL to 24 hours
                self.client.setex(session_key, 86400, session_json)
            else:
                # Keep existing TTL
                self.client.set(session_key, session_json, keepttl=True)
            
            logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            session_key = f"session:{session_id}"
            deleted = self.client.delete(session_key)
            
            logger.debug(f"Deleted session {session_id}")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    # ========================================================================
    # METRICS & COUNTERS
    # ========================================================================
    
    def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        """
        Increment a counter
        
        Args:
            counter_name: Counter identifier
            amount: Increment amount (default 1)
            
        Returns:
            New counter value
            
        Example:
            >>> redis_manager.increment_counter("api:search:calls")
            >>> redis_manager.increment_counter("thompson:updates:purchase", 1)
        """
        try:
            counter_key = f"counter:{counter_name}"
            new_value = self.client.incr(counter_key, amount)
            
            logger.debug(f"Counter '{counter_name}' incremented to {new_value}")
            return new_value
            
        except Exception as e:
            logger.error(f"Error incrementing counter: {e}")
            return 0
    
    def get_counter(self, counter_name: str) -> int:
        """
        Get counter value
        
        Args:
            counter_name: Counter identifier
            
        Returns:
            Counter value (0 if not exists)
        """
        try:
            counter_key = f"counter:{counter_name}"
            value = self.client.get(counter_key)
            
            return int(value) if value else 0
            
        except Exception as e:
            logger.error(f"Error getting counter: {e}")
            return 0
    
    def reset_counter(self, counter_name: str) -> bool:
        """Reset counter to 0"""
        try:
            counter_key = f"counter:{counter_name}"
            self.client.set(counter_key, 0)
            
            logger.debug(f"Counter '{counter_name}' reset to 0")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting counter: {e}")
            return False
    
    def get_all_metrics(self) -> Dict[str, int]:
        """
        Get all counter metrics
        
        Returns:
            Dict of counter names to values
        """
        try:
            counter_keys = list(self.client.scan_iter(match="counter:*"))
            
            metrics = {}
            for key in counter_keys:
                counter_name = key.replace('counter:', '') if isinstance(key, str) else key.decode('utf-8').replace('counter:', '')
                value = self.client.get(key)
                metrics[counter_name] = int(value) if value else 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    def record_timing(
        self,
        operation: str,
        duration_ms: float
    ) -> bool:
        """
        Record operation timing (for performance monitoring)
        
        Args:
            operation: Operation name (e.g., 'agent1_execution')
            duration_ms: Duration in milliseconds
            
        Returns:
            True if recorded successfully
            
        Example:
            >>> redis_manager.record_timing("agent1_execution", 245.3)
        """
        try:
            # Store in a sorted set with timestamp as score
            timing_key = f"timing:{operation}"
            
            timestamp = time.time()
            
            # Add to sorted set (keep last 100 measurements)
            self.client.zadd(timing_key, {str(duration_ms): timestamp})
            
            # Trim to keep only last 100
            self.client.zremrangebyrank(timing_key, 0, -101)
            
            logger.debug(f"Recorded timing for '{operation}': {duration_ms:.2f}ms")
            return True
            
        except Exception as e:
            logger.error(f"Error recording timing: {e}")
            return False
    
    def get_timing_stats(self, operation: str) -> Dict[str, float]:
        """
        Get timing statistics for an operation
        
        Args:
            operation: Operation name
            
        Returns:
            Dict with avg, min, max, p50, p95, p99 timings
        """
        try:
            timing_key = f"timing:{operation}"
            
            # Get all timings
            timings_raw = self.client.zrange(timing_key, 0, -1)
            
            if not timings_raw:
                return {}
            
            timings = [float(t) if isinstance(t, str) else float(t.decode('utf-8')) for t in timings_raw]
            timings.sort()
            
            return {
                'count': len(timings),
                'avg': statistics.mean(timings),
                'min': min(timings),
                'max': max(timings),
                'p50': statistics.median(timings),
                'p95': timings[int(len(timings) * 0.95)] if len(timings) > 1 else timings[0],
                'p99': timings[int(len(timings) * 0.99)] if len(timings) > 1 else timings[0],
            }
            
        except Exception as e:
            logger.error(f"Error getting timing stats: {e}")
            return {}
    
    def set_metric(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a metric value"""
        if ttl:
            self.client.setex(key, timedelta(seconds=ttl), json.dumps(value))
        else:
            self.client.set(key, json.dumps(value))
    
    def get_metric(self, key: str) -> Optional[Any]:
        """Get metric value"""
        value = self.client.get(key)
        return json.loads(value) if value else None
    
    # ========================================================================
    # HEALTH & DIAGNOSTICS
    # ========================================================================
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get Redis memory usage information
        
        Returns:
            Dict with memory stats
        """
        try:
            info = self.client.info('memory')
            
            return {
                'used_memory_mb': info.get('used_memory', 0) / 1024 / 1024,
                'used_memory_peak_mb': info.get('used_memory_peak', 0) / 1024 / 1024,
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'maxmemory_mb': info.get('maxmemory', 0) / 1024 / 1024 if info.get('maxmemory', 0) > 0 else 'unlimited',
                'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {}
    
    def health_check(self) -> bool:
        """
        Check Redis connection health
        
        Returns:
            True if Redis is accessible and responsive
            
        Example:
            >>> if redis_manager.health_check():
            ...     print("Redis is healthy!")
        """
        try:
            response = self.client.ping()
            
            if response:
                logger.debug("Redis health check: PASS")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Redis health check FAILED: {e}")
            return False
    
    def flush_all(self, confirm: bool = False) -> bool:
        """
        Flush all Redis data (USE WITH CAUTION!)
        
        Args:
            confirm: Must be True to execute
            
        Returns:
            True if flushed successfully
            
        Warning:
            This deletes ALL data including Thompson parameters!
            Only use in development/testing.
        """
        if not confirm:
            logger.warning("flush_all() called without confirmation")
            return False
        
        try:
            self.client.flushall()
            logger.warning("⚠️  ALL REDIS DATA FLUSHED")
            return True
            
        except Exception as e:
            logger.error(f"Error flushing Redis: {e}")
            return False


# Global instance
redis_manager = RedisManager()
