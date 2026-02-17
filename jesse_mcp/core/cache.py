"""
TTL Cache Layer for Jesse MCP API Calls

Provides configurable caching with:
- Cache hit/miss statistics
- Per-cache TTL support
- Manual cache clearing
- Environment variable configuration

Environment variables:
- JESSE_CACHE_ENABLED: Enable caching (default: true)
- JESSE_CACHE_TTL: Default TTL in seconds (default: 300)
- JESSE_CACHE_STRATEGY_TTL: Strategy list TTL (default: 300)
- JESSE_CACHE_BACKTEST_TTL: Backtest result TTL (default: 3600)
"""

import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger("jesse-mcp.cache")

JESSE_CACHE_ENABLED = os.getenv("JESSE_CACHE_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
JESSE_CACHE_TTL = int(os.getenv("JESSE_CACHE_TTL", "300"))
JESSE_CACHE_STRATEGY_TTL = int(os.getenv("JESSE_CACHE_STRATEGY_TTL", "300"))
JESSE_CACHE_BACKTEST_TTL = int(os.getenv("JESSE_CACHE_BACKTEST_TTL", "3600"))
JESSE_CACHE_MAX_SIZE = int(os.getenv("JESSE_CACHE_MAX_SIZE", "1000"))

_cache_instances: Dict[str, "TTLCache"] = {}
_stats: Dict[str, Dict[str, int]] = {}


class TTLCache:
    """Simple TTL cache with statistics tracking"""

    def __init__(
        self,
        name: str,
        ttl: int = JESSE_CACHE_TTL,
        max_size: int = JESSE_CACHE_MAX_SIZE,
    ):
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, tuple] = {}
        self._stats = {"hits": 0, "misses": 0}

    def _hash_key(self, *args, **kwargs) -> str:
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def get(self, key: str) -> Optional[Any]:
        import time

        entry = self._cache.get(key)
        if entry is None:
            self._stats["misses"] += 1
            return None

        value, expiry = entry
        if time.time() > expiry:
            del self._cache[key]
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        return value

    def set(self, key: str, value: Any) -> None:
        import time

        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        expiry = time.time() + self.ttl
        self._cache[key] = (value, expiry)

    def clear(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> Dict[str, int]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "size": self.size(),
            "max_size": self.max_size,
        }

    def wrap(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not JESSE_CACHE_ENABLED:
                return func(*args, **kwargs)

            key = self._hash_key(*args, **kwargs)
            cached = self.get(key)
            if cached is not None:
                logger.debug(f"Cache HIT for {self.name}: {func.__name__}")
                return cached

            logger.debug(f"Cache MISS for {self.name}: {func.__name__}")
            result = func(*args, **kwargs)
            self.set(key, result)
            return result

        return wrapper


def get_cache(name: str, ttl: Optional[int] = None) -> TTLCache:
    """Get or create a named cache instance"""
    if name not in _cache_instances:
        cache_ttl = ttl if ttl is not None else JESSE_CACHE_TTL
        _cache_instances[name] = TTLCache(name, ttl=cache_ttl)
        _stats[name] = {"hits": 0, "misses": 0}
    return _cache_instances[name]


def get_strategy_cache() -> TTLCache:
    """Get cache for strategy list (5 minute TTL)"""
    return get_cache("strategy_list", ttl=JESSE_CACHE_STRATEGY_TTL)


def get_backtest_cache() -> TTLCache:
    """Get cache for backtest results (1 hour TTL)"""
    return get_cache("backtest", ttl=JESSE_CACHE_BACKTEST_TTL)


def clear_all_caches() -> Dict[str, int]:
    """Clear all cache instances and return counts"""
    results = {}
    for name, cache in _cache_instances.items():
        results[name] = cache.clear()
    return results


def clear_cache(name: str) -> int:
    """Clear a specific cache"""
    if name in _cache_instances:
        return _cache_instances[name].clear()
    return 0


def get_all_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        "enabled": JESSE_CACHE_ENABLED,
        "default_ttl": JESSE_CACHE_TTL,
        "caches": {name: cache.stats() for name, cache in _cache_instances.items()},
        "totals": {
            "total_hits": sum(c._stats["hits"] for c in _cache_instances.values()),
            "total_misses": sum(c._stats["misses"] for c in _cache_instances.values()),
        },
    }


def cache_stats_summary() -> str:
    """Return a human-readable cache stats summary"""
    stats = get_all_stats()
    if not stats["caches"]:
        return "No caches active"

    lines = [f"Cache Status: {'ENABLED' if stats['enabled'] else 'DISABLED'}"]
    for name, cache_stats in stats["caches"].items():
        lines.append(
            f"  {name}: {cache_stats['size']}/{cache_stats['max_size']} entries, "
            f"{cache_stats['hit_rate']}% hit rate"
        )
    return "\n".join(lines)
