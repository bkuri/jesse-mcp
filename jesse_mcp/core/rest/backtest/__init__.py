"""
Backtest module for Jesse REST API client.

Submodules:
- api: Low-level API functions (submit, poll, get_result)
- helpers: Utility functions (build_payload, validate, estimate_time)
- wrappers: Client method variants (backtest, cached, retry)
"""

from jesse_mcp.core.rest.backtest.api import (
    execute_backtest,
    get_backtest_session_result,
    poll_backtest_result,
    submit_backtest,
)
from jesse_mcp.core.rest.backtest.helpers import (
    build_backtest_payload,
    estimate_max_backtest_time,
    is_retryable_error,
    validate_backtest_result,
)
from jesse_mcp.core.rest.backtest.wrappers import (
    backtest,
    backtest_with_retry,
    cached_backtest,
)

__all__ = [
    "execute_backtest",
    "get_backtest_session_result",
    "poll_backtest_result",
    "submit_backtest",
    "build_backtest_payload",
    "estimate_max_backtest_time",
    "is_retryable_error",
    "validate_backtest_result",
    "backtest",
    "backtest_with_retry",
    "cached_backtest",
]
