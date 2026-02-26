"""
Backtest methods for Jesse REST API client.

This module has been refactored into jesse_mcp.core.rest.backtest package.
Please use the new import paths:

    from jesse_mcp.core.rest.backtest import (
        execute_backtest,
        build_backtest_payload,
        validate_backtest_result,
        backtest,
    )

Or import from specific submodules:
    from jesse_mcp.core.rest.backtest.api import submit_backtest, poll_backtest_result
    from jesse_mcp.core.rest.backtest.helpers import build_backtest_payload
    from jesse_mcp.core.rest.backtest.wrappers import cached_backtest
"""

from jesse_mcp.core.rest.backtest import (
    backtest,
    backtest_with_retry,
    build_backtest_payload,
    cached_backtest,
    estimate_max_backtest_time,
    execute_backtest,
    get_backtest_session_result,
    is_retryable_error,
    poll_backtest_result,
    submit_backtest,
    validate_backtest_result,
)

__all__ = [
    "backtest",
    "backtest_with_retry",
    "build_backtest_payload",
    "cached_backtest",
    "estimate_max_backtest_time",
    "execute_backtest",
    "get_backtest_session_result",
    "is_retryable_error",
    "poll_backtest_result",
    "submit_backtest",
    "validate_backtest_result",
]
