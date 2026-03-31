"""
Shared utilities for Jesse MCP tool modules.

Eliminates repeated boilerplate for:
- REST client access
- Module availability guards
- Error handling
- Async-to-sync bridging
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("jesse-mcp.tools")

_jesse: Optional[Any] = None
_optimizer: Optional[Any] = None
_risk_analyzer: Optional[Any] = None
_pairs_analyzer: Optional[Any] = None


def initialize(
    jesse_instance, optimizer_instance, risk_analyzer_instance, pairs_analyzer_instance
):
    """Inject module references from server.py initialization."""
    global _jesse, _optimizer, _risk_analyzer, _pairs_analyzer
    _jesse = jesse_instance
    _optimizer = optimizer_instance
    _risk_analyzer = risk_analyzer_instance
    _pairs_analyzer = pairs_analyzer_instance


def get_client():
    """Get Jesse REST client instance."""
    from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

    return get_jesse_rest_client()


def require_jesse():
    """Guard: raise if Jesse framework not initialized."""
    if _jesse is None:
        raise RuntimeError("Jesse framework not initialized")
    return _jesse


def require_optimizer():
    if _optimizer is None:
        raise RuntimeError("Optimizer module not initialized")
    return _optimizer


def require_risk_analyzer():
    if _risk_analyzer is None:
        raise RuntimeError("Risk analyzer module not initialized")
    return _risk_analyzer


def require_pairs_analyzer():
    if _pairs_analyzer is None:
        raise RuntimeError("Pairs analyzer module not initialized")
    return _pairs_analyzer


def get_strategies_path():
    """Get strategies path from jesse, raising if unavailable."""
    j = require_jesse()
    path = getattr(j, "strategies_path", None)
    if not path:
        raise RuntimeError("Strategies path not available")
    return path


def tool_error_handler(func: Callable) -> Callable:
    """Decorator that wraps MCP tools with standardized error handling.

    Catches exceptions, logs them, and returns
    {"error": str(e), "error_type": type(e).__name__}.
    Works with both sync and async functions.
    """
    tool_name = func.__name__

    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{tool_name} failed: {e}")
                return {"error": str(e), "error_type": type(e).__name__}

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{tool_name} failed: {e}")
                return {"error": str(e), "error_type": type(e).__name__}

        return sync_wrapper


async def async_call(func: Callable, *args, **kwargs):
    """Run a sync function in a thread pool from async context."""
    return await asyncio.to_thread(func, *args, **kwargs)
