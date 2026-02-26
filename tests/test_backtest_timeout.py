"""Test to verify increased backtest polling timeout works correctly."""

import inspect
import pytest
from jesse_mcp.core.rest import backtest
from jesse_mcp.core.rest import JesseRESTClient


class TestBacktestPollingTimeout:
    """Tests for backtest polling with increased timeout."""

    def test_backtest_polling_timeout_is_dynamic(self):
        """Verify max_poll_time defaults to None for dynamic calculation."""
        sig = inspect.signature(backtest.execute_backtest)
        max_poll_time_param = sig.parameters["max_poll_time"]

        assert max_poll_time_param.default is None, (
            f"Expected max_poll_time default to be None (dynamic), got {max_poll_time_param.default}"
        )

    def test_backtest_polling_method_signature(self):
        """Test that polling method has proper parameters."""
        sig = inspect.signature(backtest.poll_backtest_result)

        assert "poll_interval" in sig.parameters
        assert "max_poll_time" in sig.parameters

        assert sig.parameters["poll_interval"].default == 1.0
        assert sig.parameters["max_poll_time"].default == 300.0

    def test_rate_limited_backtest_has_correct_defaults(self):
        """Test that execute_backtest method has correct parameter defaults."""
        sig = inspect.signature(backtest.execute_backtest)

        assert sig.parameters["timeout"].default == 300
        assert sig.parameters["poll_interval"].default == 1.0
        assert sig.parameters["max_poll_time"].default is None

    def test_estimate_max_backtest_time(self):
        """Test that timeout estimation returns reasonable values."""
        timeout = backtest.estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-02-01", timeframe="1h"
        )
        assert timeout >= 30, f"Expected at least 30s, got {timeout}s"
        assert timeout <= 600, f"Expected at most 600s, got {timeout}s"

        timeout_year = backtest.estimate_max_backtest_time(
            start_date="2023-01-01", end_date="2024-01-01", timeframe="1h"
        )
        assert timeout_year <= 600, f"Expected capped at 600s, got {timeout_year}s"

    def test_estimate_respects_timeframe(self):
        """Test that faster timeframes get longer timeouts (more candles)."""
        timeout_1h = backtest.estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-02-01", timeframe="1h"
        )

        timeout_1m = backtest.estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-02-01", timeframe="1m"
        )

        assert timeout_1m >= timeout_1h, (
            f"Expected 1m timeout >= 1h timeout, got {timeout_1m}s vs {timeout_1h}s"
        )

    def test_estimate_applies_bounds(self):
        """Test that timeout estimation applies min/max bounds."""
        timeout_short = backtest.estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-01-02", timeframe="1h"
        )
        assert timeout_short >= 30, f"Expected min 30s, got {timeout_short}s"

        timeout_long = backtest.estimate_max_backtest_time(
            start_date="2014-01-01", end_date="2024-01-01", timeframe="1h"
        )
        assert timeout_long <= 600, f"Expected max 600s, got {timeout_long}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
