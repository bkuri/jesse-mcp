"""Test to verify increased backtest polling timeout works correctly."""

import inspect
import pytest
from jesse_mcp.core.jesse_rest_client import JesseRESTClient


class TestBacktestPollingTimeout:
    """Tests for backtest polling with increased timeout."""

    def test_backtest_polling_timeout_increased_to_300s(self):
        """Verify max_poll_time default is 300 seconds, not 60."""
        # This ensures we don't regress back to the short timeout
        sig = inspect.signature(JesseRESTClient._rate_limited_backtest)
        max_poll_time_param = sig.parameters["max_poll_time"]

        assert max_poll_time_param.default == 300.0, (
            f"Expected max_poll_time default to be 300s, got {max_poll_time_param.default}s"
        )

    def test_backtest_polling_method_signature(self):
        """Test that polling method has proper parameters."""
        # Verify the method has poll_interval and max_poll_time parameters
        sig = inspect.signature(JesseRESTClient._poll_backtest_result)

        assert "poll_interval" in sig.parameters
        assert "max_poll_time" in sig.parameters

        # Verify defaults
        assert sig.parameters["poll_interval"].default == 1.0
        assert sig.parameters["max_poll_time"].default == 300.0

    def test_rate_limited_backtest_has_correct_defaults(self):
        """Test that _rate_limited_backtest method has correct parameter defaults."""
        sig = inspect.signature(JesseRESTClient._rate_limited_backtest)

        # Verify timeout default (300 seconds)
        assert sig.parameters["timeout"].default == 300
        # Verify poll_interval default
        assert sig.parameters["poll_interval"].default == 1.0
        # Verify max_poll_time default (300 seconds, not 60)
        assert sig.parameters["max_poll_time"].default == 300.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
