"""
Rate Limiter using Token Bucket Algorithm

Provides thread-safe rate limiting for Jesse API calls with configurable
behavior when limits are reached (wait or reject).

Configuration (environment variables):
- JESSE_RATE_LIMIT: Requests per second (default: 10, 0=disabled)
- JESSE_RATE_LIMIT_WAIT: 'true' to wait, 'false' to reject (default: true)
"""

import os
import time
import threading
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("jesse-mcp.rate-limiter")

JESSE_RATE_LIMIT = float(os.getenv("JESSE_RATE_LIMIT", "10"))
JESSE_RATE_LIMIT_WAIT = os.getenv("JESSE_RATE_LIMIT_WAIT", "true").lower() in (
    "true",
    "1",
    "yes",
)


@dataclass
class RateLimitStats:
    total_requests: int = 0
    total_waited: int = 0
    total_rejected: int = 0
    total_wait_time_ms: float = 0.0


class TokenBucket:
    """Thread-safe token bucket rate limiter"""

    def __init__(
        self,
        rate: float = JESSE_RATE_LIMIT,
        wait_when_limited: bool = JESSE_RATE_LIMIT_WAIT,
    ):
        self.rate = rate
        self.wait_when_limited = wait_when_limited
        self.tokens = rate
        self.max_tokens = rate
        self.last_update = time.monotonic()
        self.lock = threading.Lock()
        self.stats = RateLimitStats()
        self.enabled = rate > 0

        if self.enabled:
            mode = "WAIT" if wait_when_limited else "REJECT"
            logger.info(f"✅ Rate limiter initialized: {rate} req/s, mode={mode}")
        else:
            logger.info("⚠️  Rate limiter DISABLED (JESSE_RATE_LIMIT=0)")

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
        self.last_update = now

    def acquire(self) -> bool:
        if not self.enabled:
            return True

        with self.lock:
            self._refill()
            self.stats.total_requests += 1

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            if not self.wait_when_limited:
                self.stats.total_rejected += 1
                logger.warning("⚠️  Rate limit exceeded - request rejected")
                return False

            wait_time = (1 - self.tokens) / self.rate
            self.stats.total_waited += 1
            self.stats.total_wait_time_ms += wait_time * 1000

            logger.info(f"⏳ Rate limit - waiting {wait_time:.3f}s")

        time.sleep(wait_time)

        with self.lock:
            self.tokens = 0
            return True

    def get_status(self) -> dict:
        with self.lock:
            self._refill()
            return {
                "enabled": self.enabled,
                "rate_per_second": self.rate,
                "max_tokens": self.max_tokens,
                "available_tokens": round(self.tokens, 2),
                "wait_mode": self.wait_when_limited,
                "stats": {
                    "total_requests": self.stats.total_requests,
                    "total_waited": self.stats.total_waited,
                    "total_rejected": self.stats.total_rejected,
                    "total_wait_time_ms": round(self.stats.total_wait_time_ms, 2),
                },
            }


_rate_limiter: Optional[TokenBucket] = None


def get_rate_limiter() -> TokenBucket:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = TokenBucket()
    return _rate_limiter


def rate_limited(func):
    def wrapper(*args, **kwargs):
        limiter = get_rate_limiter()
        if not limiter.acquire():
            return {
                "error": "Rate limit exceeded",
                "error_type": "RateLimitError",
                "success": False,
            }
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
