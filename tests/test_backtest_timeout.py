"""Test to verify increased backtest polling timeout works correctly."""

import inspect
import pytest
from unittest.mock import MagicMock, patch
from jesse_mcp.core.jesse_rest_client import JesseRESTClient


class TestBacktestPollingTimeout:
    """Tests for backtest polling with increased timeout."""

    def test_backtest_polling_timeout_is_dynamic(self):
        """Verify max_poll_time defaults to None for dynamic calculation."""
        # None means it will be calculated based on date range
        sig = inspect.signature(JesseRESTClient._rate_limited_backtest)
        max_poll_time_param = sig.parameters["max_poll_time"]

        assert max_poll_time_param.default is None, (
            f"Expected max_poll_time default to be None (dynamic), got {max_poll_time_param.default}"
        )

    def test_backtest_polling_method_signature(self):
        """Test that polling method has proper parameters."""
        # Verify the method has poll_interval and max_poll_time parameters
        sig = inspect.signature(JesseRESTClient._poll_backtest_result)

        assert "poll_interval" in sig.parameters
        assert "max_poll_time" in sig.parameters

        # Verify defaults for _poll_backtest_result (called directly)
        assert sig.parameters["poll_interval"].default == 1.0
        assert sig.parameters["max_poll_time"].default == 300.0

    def test_rate_limited_backtest_has_correct_defaults(self):
        """Test that _rate_limited_backtest method has correct parameter defaults."""
        sig = inspect.signature(JesseRESTClient._rate_limited_backtest)

        # Verify timeout default (300 seconds)
        assert sig.parameters["timeout"].default == 300
        # Verify poll_interval default
        assert sig.parameters["poll_interval"].default == 1.0
        # Verify max_poll_time default is None (dynamic calculation)
        assert sig.parameters["max_poll_time"].default is None

    def test_estimate_max_backtest_time(self):
        """Test that timeout estimation returns reasonable values."""
        # Mock the client to avoid connection
        with patch.object(JesseRESTClient, "_verify_connection"):
            client = JesseRESTClient(base_url="http://localhost:9100", api_token="test")

        # Test 1 month, 1h timeframe
        timeout = client._estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-02-01", timeframe="1h"
        )
        # 31 days * 24h = 744 candles + 240 warmup = 984 candles
        # 984 / 500 * 3 = ~6s, but bounded by MIN_TIMEOUT (30s)
        assert timeout >= 30, f"Expected at least 30s, got {timeout}s"
        assert timeout <= 600, f"Expected at most 600s, got {timeout}s"

        # Test 1 year, 1h timeframe
        timeout_year = client._estimate_max_backtest_time(
            start_date="2023-01-01", end_date="2024-01-01", timeframe="1h"
        )
        # Should be capped at MAX_TIMEOUT (600s)
        assert timeout_year <= 600, f"Expected capped at 600s, got {timeout_year}s"

    def test_estimate_respects_timeframe(self):
        """Test that faster timeframes get longer timeouts (more candles)."""
        with patch.object(JesseRESTClient, "_verify_connection"):
            client = JesseRESTClient(base_url="http://localhost:9100", api_token="test")

        timeout_1h = client._estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-02-01", timeframe="1h"
        )

        timeout_1m = client._estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-02-01", timeframe="1m"
        )

        # 1m timeframe has 60x more candles than 1h
        # So timeout should be longer (though capped)
        assert timeout_1m >= timeout_1h, (
            f"Expected 1m timeout >= 1h timeout, got {timeout_1m}s vs {timeout_1h}s"
        )

    def test_estimate_applies_bounds(self):
        """Test that timeout estimation applies min/max bounds."""
        with patch.object(JesseRESTClient, "_verify_connection"):
            client = JesseRESTClient(base_url="http://localhost:9100", api_token="test")

        # Very short range (1 day) should hit MIN_TIMEOUT
        timeout_short = client._estimate_max_backtest_time(
            start_date="2024-01-01", end_date="2024-01-02", timeframe="1h"
        )
        assert timeout_short >= 30, f"Expected min 30s, got {timeout_short}s"

        # Very long range (10 years) should hit MAX_TIMEOUT
        timeout_long = client._estimate_max_backtest_time(
            start_date="2014-01-01", end_date="2024-01-01", timeframe="1h"
        )
        assert timeout_long <= 600, f"Expected max 600s, got {timeout_long}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
