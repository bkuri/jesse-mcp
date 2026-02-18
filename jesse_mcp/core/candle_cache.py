"""
Candle Cache Module - RAM-based caching for Jesse candle data

Provides multiple cache layers:
1. In-memory LRU cache (fastest, process-local)
2. Redis cache (shared across processes/servers)
3. Fallback to Jesse API (persistent PostgreSQL)

Architecture:
    Request → Memory Cache → Redis Cache → Jesse API → PostgreSQL
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
import json

logger = logging.getLogger("jesse-mcp.candle-cache")

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis not available - using memory-only cache")


class CandleCache:
    """
    Multi-layer RAM cache for Jesse candle data

    Layers (fastest to slowest):
    1. In-memory LRU cache (~0.1ms lookup)
    2. Redis cache (~1ms lookup, shared across processes)
    3. Jesse API / PostgreSQL (~50-200ms)
    """

    DEFAULT_TTL = 3600  # 1 hour cache
    MAX_MEMORY_ITEMS = 1000  # Max items in LRU cache

    def __init__(
        self,
        redis_host: str = "127.0.0.1",
        redis_port: int = 6379,
        redis_db: int = 1,  # Use separate DB for candles
        redis_password: str = "",
        ttl: int = DEFAULT_TTL,
    ):
        self.ttl = ttl
        self._redis_client = None
        self._redis_config = {
            "host": redis_host,
            "port": redis_port,
            "db": redis_db,
            "password": redis_password if redis_password else None,
            "decode_responses": True,
        }

        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._access_order: List[str] = []  # For LRU eviction

        self._stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "api_calls": 0,
            "evictions": 0,
        }

        if REDIS_AVAILABLE:
            self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self._redis_client = redis.Redis(**self._redis_config)
            self._redis_client.ping()
            logger.info(f"✅ Candle cache connected to Redis (db={self._redis_config['db']})")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e} - using memory-only cache")
            self._redis_client = None

    @staticmethod
    def _make_key(exchange: str, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> str:
        """Create cache key"""
        return f"candle:{exchange}:{symbol}:{timeframe}:{start_ts}:{end_ts}"

    def _evict_lru(self):
        """Evict least recently used items if cache is full"""
        while len(self._memory_cache) >= self.MAX_MEMORY_ITEMS:
            if not self._access_order:
                break
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._memory_cache:
                del self._memory_cache[oldest_key]
                self._stats["evictions"] += 1

    def get(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start_ts: int,
        end_ts: int,
    ) -> Optional[List[Dict]]:
        """
        Get candles from cache layers

        Returns cached candles or None if not found
        """
        key = self._make_key(exchange, symbol, timeframe, start_ts, end_ts)

        # Layer 1: Memory cache
        if key in self._memory_cache:
            data, expiry = self._memory_cache[key]
            if time.time() < expiry:
                self._stats["memory_hits"] += 1
                # Update access order
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                return data
            else:
                del self._memory_cache[key]

        # Layer 2: Redis cache
        if self._redis_client:
            try:
                cached = self._redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    self._stats["redis_hits"] += 1
                    # Promote to memory cache
                    self._set_memory(key, data)
                    return data
            except Exception as e:
                logger.debug(f"Redis get error: {e}")

        return None

    def _set_memory(self, key: str, data: Any):
        """Set in memory cache with LRU eviction"""
        self._evict_lru()
        self._memory_cache[key] = (data, time.time() + self.ttl)
        self._access_order.append(key)

    def set(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start_ts: int,
        end_ts: int,
        candles: List[Dict],
    ):
        """Store candles in all cache layers"""
        key = self._make_key(exchange, symbol, timeframe, start_ts, end_ts)

        # Layer 1: Memory cache
        self._set_memory(key, candles)

        # Layer 2: Redis cache
        if self._redis_client:
            try:
                self._redis_client.setex(key, self.ttl, json.dumps(candles))
            except Exception as e:
                logger.debug(f"Redis set error: {e}")

    def preload(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        candles: List[Dict],
    ):
        """
        Pre-load candles into cache (e.g., on startup)
        Candles should be full historical data
        """
        if not candles:
            return

        # Group candles by day/hour for granular caching
        # This allows partial cache hits
        start_ts = candles[0].get("timestamp", 0)
        end_ts = candles[-1].get("timestamp", 0)

        key = self._make_key(exchange, symbol, timeframe, start_ts, end_ts)
        self._set_memory(key, candles)

        if self._redis_client:
            try:
                self._redis_client.setex(key, self.ttl * 24, json.dumps(candles))
                logger.info(f"✅ Pre-loaded {len(candles)} candles for {symbol}")
            except Exception as e:
                logger.debug(f"Redis preload error: {e}")

    def invalidate(
        self,
        exchange: str = None,
        symbol: str = None,
    ):
        """Invalidate cache entries"""
        # Clear memory cache
        if exchange and symbol:
            prefix = f"candle:{exchange}:{symbol}:"
        elif exchange:
            prefix = f"candle:{exchange}:"
        else:
            prefix = "candle:"

        # Memory cache
        keys_to_remove = [k for k in self._memory_cache if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._memory_cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

        # Redis cache
        if self._redis_client:
            try:
                for key in self._redis_client.scan_iter(f"{prefix}*"):
                    self._redis_client.delete(key)
            except Exception as e:
                logger.debug(f"Redis invalidate error: {e}")

    def clear(self):
        """Clear all caches"""
        self._memory_cache.clear()
        self._access_order.clear()

        if self._redis_client:
            try:
                for key in self._redis_client.scan_iter("candle:*"):
                    self._redis_client.delete(key)
            except Exception as e:
                logger.debug(f"Redis clear error: {e}")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_hits = self._stats["memory_hits"] + self._stats["redis_hits"]
        total_requests = total_hits + self._stats["api_calls"]
        hit_rate = total_hits / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "memory_items": len(self._memory_cache),
            "hit_rate": f"{hit_rate:.1%}",
            "redis_enabled": self._redis_client is not None,
        }


# Global candle cache instance
_candle_cache: Optional[CandleCache] = None


def get_candle_cache() -> CandleCache:
    """Get or create global candle cache"""
    global _candle_cache
    if _candle_cache is None:
        import os

        _candle_cache = CandleCache(
            redis_host=os.getenv("REDIS_HOST", "127.0.0.1"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
        )
    return _candle_cache


def warm_cache_from_jesse(exchange: str, symbol: str, timeframe: str = "1h"):
    """
    Warm up cache by loading candles from Jesse
    Call this on startup or before intensive backtesting
    """
    from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

    client = get_jesse_rest_client()
    cache = get_candle_cache()

    # Get candles from Jesse
    result = client.get_candles(exchange, symbol, timeframe)

    if "data" in result and result["data"]:
        cache.preload(exchange, symbol, timeframe, result["data"])
        return len(result["data"])

    return 0
