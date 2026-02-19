"""
Tests for Live Trading functionality (Phase 6)

Tests cover:
- LiveTradingConfig validation
- TradingAgent permissions
- Live trading MCP tools
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestLiveTradingConfig:
    """Tests for LiveTradingConfig pydantic model."""

    def test_default_config(self):
        """Test default configuration values."""
        from jesse_mcp.core.live_config import LiveTradingConfig, AgentPermission

        config = LiveTradingConfig()

        assert config.default_permission == AgentPermission.PAPER_ONLY
        assert config.max_position_size_pct == 0.1
        assert config.max_daily_loss_pct == 0.05
        assert config.max_drawdown_pct == 0.15
        assert config.require_confirmation_phrase is True
        assert config.confirmation_phrase == "I UNDERSTAND THE RISKS"
        assert config.auto_stop_on_max_loss is True

    def test_permission_enum(self):
        """Test AgentPermission enum values."""
        from jesse_mcp.core.live_config import AgentPermission

        assert AgentPermission.PAPER_ONLY.value == "paper_only"
        assert AgentPermission.CONFIRM_REQUIRED.value == "confirm_required"
        assert AgentPermission.FULL_AUTONOMOUS.value == "full_autonomous"

    def test_config_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        from jesse_mcp.core.live_config import LiveTradingConfig, AgentPermission

        monkeypatch.setenv("JESSE_DEFAULT_PERMISSION", "confirm_required")
        monkeypatch.setenv("JESSE_MAX_POSITION_SIZE", "0.2")
        monkeypatch.setenv("JESSE_MAX_DAILY_LOSS", "0.03")

        config = LiveTradingConfig.from_env()

        assert config.default_permission == AgentPermission.CONFIRM_REQUIRED
        assert config.max_position_size_pct == 0.2
        assert config.max_daily_loss_pct == 0.03

    def test_position_size_validation(self):
        """Test position size percentage validation."""
        from jesse_mcp.core.live_config import LiveTradingConfig
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LiveTradingConfig(max_position_size_pct=0.005)

        with pytest.raises(ValidationError):
            LiveTradingConfig(max_position_size_pct=1.5)


class TestLiveSessionRequest:
    """Tests for LiveSessionRequest validation."""

    def test_paper_mode_validation(self):
        """Test validation passes for paper mode."""
        from jesse_mcp.core.live_config import (
            LiveSessionRequest,
            LiveTradingConfig,
            AgentPermission,
        )

        request = LiveSessionRequest(
            strategy="TestStrategy",
            symbol="BTC-USDT",
            timeframe="1h",
            exchange="Binance",
            exchange_api_key_id="test-key-id",
            paper_mode=True,
        )

        config = LiveTradingConfig()
        result = request.validate_for_live_mode(config)

        assert result["valid"] is True

    def test_live_mode_paper_only_permission(self):
        """Test validation fails for paper_only permission with live mode."""
        from jesse_mcp.core.live_config import (
            LiveSessionRequest,
            LiveTradingConfig,
            AgentPermission,
        )

        request = LiveSessionRequest(
            strategy="TestStrategy",
            symbol="BTC-USDT",
            timeframe="1h",
            exchange="Binance",
            exchange_api_key_id="test-key-id",
            paper_mode=False,
            permission=AgentPermission.PAPER_ONLY,
        )

        config = LiveTradingConfig()
        result = request.validate_for_live_mode(config)

        assert result["valid"] is False
        assert "PAPER_ONLY" in result["error"]

    def test_live_mode_confirmation_required(self):
        """Test validation requires confirmation phrase."""
        from jesse_mcp.core.live_config import (
            LiveSessionRequest,
            LiveTradingConfig,
            AgentPermission,
        )

        request = LiveSessionRequest(
            strategy="TestStrategy",
            symbol="BTC-USDT",
            timeframe="1h",
            exchange="Binance",
            exchange_api_key_id="test-key-id",
            paper_mode=False,
            permission=AgentPermission.CONFIRM_REQUIRED,
            confirmation="wrong phrase",
        )

        config = LiveTradingConfig(require_confirmation_phrase=True)
        result = request.validate_for_live_mode(config)

        assert result["valid"] is False
        assert "confirmation" in result["error"].lower()

    def test_live_mode_with_correct_confirmation(self):
        """Test validation passes with correct confirmation."""
        from jesse_mcp.core.live_config import (
            LiveSessionRequest,
            LiveTradingConfig,
            AgentPermission,
        )

        request = LiveSessionRequest(
            strategy="TestStrategy",
            symbol="BTC-USDT",
            timeframe="1h",
            exchange="Binance",
            exchange_api_key_id="test-key-id",
            paper_mode=False,
            permission=AgentPermission.CONFIRM_REQUIRED,
            confirmation="I UNDERSTAND THE RISKS",
        )

        config = LiveTradingConfig(require_confirmation_phrase=True)
        result = request.validate_for_live_mode(config)

        assert result["valid"] is True


class TestTradingAgent:
    """Tests for TradingAgent class."""

    def test_paper_only_permission(self):
        """Test agent with paper_only permission."""
        from jesse_mcp.agents.live_trader import TradingAgent, get_trading_agent
        from jesse_mcp.core.live_config import AgentPermission

        agent = get_trading_agent("paper_only")

        assert agent.permission == AgentPermission.PAPER_ONLY
        assert agent.can_trade_live is False
        assert agent.requires_confirmation is False

    def test_confirm_required_permission(self):
        """Test agent with confirm_required permission."""
        from jesse_mcp.agents.live_trader import get_trading_agent
        from jesse_mcp.core.live_config import AgentPermission

        agent = get_trading_agent("confirm_required")

        assert agent.permission == AgentPermission.CONFIRM_REQUIRED
        assert agent.can_trade_live is True
        assert agent.requires_confirmation is True

    def test_full_autonomous_permission(self):
        """Test agent with full_autonomous permission."""
        from jesse_mcp.agents.live_trader import get_trading_agent
        from jesse_mcp.core.live_config import AgentPermission

        agent = get_trading_agent("full_autonomous")

        assert agent.permission == AgentPermission.FULL_AUTONOMOUS
        assert agent.can_trade_live is True
        assert agent.requires_confirmation is False

    def test_invalid_permission_defaults_to_paper(self):
        """Test invalid permission defaults to paper_only."""
        from jesse_mcp.agents.live_trader import get_trading_agent
        from jesse_mcp.core.live_config import AgentPermission

        agent = get_trading_agent("invalid_permission")

        assert agent.permission == AgentPermission.PAPER_ONLY

    def test_check_permission(self):
        """Test permission checking."""
        from jesse_mcp.agents.live_trader import get_trading_agent

        paper_agent = get_trading_agent("paper_only")
        result = paper_agent.check_permission(require_live=True)
        assert result["allowed"] is False

        full_agent = get_trading_agent("full_autonomous")
        result = full_agent.check_permission(require_live=True)
        assert result["allowed"] is True


class TestLiveRESTClientMethods:
    """Tests for live trading REST client methods."""

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    def test_check_live_plugin_available(self, mock_session):
        """Test plugin availability check."""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        with patch.object(JesseRESTClient, "_verify_connection"):
            with patch.object(JesseRESTClient, "_authenticate_with_token"):
                client = JesseRESTClient(api_token="test-token")

        result = client.check_live_plugin_available()

        assert result["available"] is True

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    def test_start_live_session_payload(self, mock_session):
        """Test start_live_session creates correct payload."""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {"message": "Started paper trading..."}
        mock_session.return_value.post.return_value = mock_response

        with patch.object(JesseRESTClient, "_verify_connection"):
            with patch.object(JesseRESTClient, "_authenticate_with_token"):
                client = JesseRESTClient(api_token="test-token")

        result = client.start_live_session(
            strategy="TestStrategy",
            symbol="BTC-USDT",
            timeframe="1h",
            exchange="Binance",
            exchange_api_key_id="test-key-id",
            paper_mode=True,
        )

        assert "session_id" in result
        assert result.get("paper_mode") is True

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    def test_get_live_sessions(self, mock_session):
        """Test get_live_sessions method."""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sessions": []}
        mock_session.return_value.post.return_value = mock_response

        with patch.object(JesseRESTClient, "_verify_connection"):
            with patch.object(JesseRESTClient, "_authenticate_with_token"):
                client = JesseRESTClient(api_token="test-token")

        result = client.get_live_sessions(limit=10, offset=0)

        assert "sessions" in result
