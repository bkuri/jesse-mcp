#!/usr/bin/env python3
"""
Unit tests for JesseRESTClient

Tests the REST API client for Jesse trading framework.
Uses mocking to avoid actual HTTP requests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests


class TestJesseRESTClientInit:
    """Tests for JesseRESTClient initialization"""

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    @patch("jesse_mcp.core.jesse_rest_client.requests.post")
    def test_init_with_password_auth(self, mock_post, mock_session_class):
        """Test initialization with password authentication"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"auth_token": "test-session-token"},
            raise_for_status=Mock(),
        )

        mock_session = Mock()
        mock_session.get.return_value = Mock(status_code=200)
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            from jesse_mcp.core.jesse_rest_client import JesseRESTClient

            client = JesseRESTClient(
                base_url="http://test:8000",
                password="test-password",
                api_token="",
            )

            assert client.auth_token == "test-session-token"
            assert "authorization" in client.session.headers

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    def test_init_with_token_auth(self, mock_session_class):
        """Test initialization with pre-generated API token"""
        mock_session = Mock()
        mock_session.get.return_value = Mock(status_code=200)
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            from jesse_mcp.core.jesse_rest_client import JesseRESTClient

            client = JesseRESTClient(
                base_url="http://test:8000",
                password="",
                api_token="pre-generated-token",
            )

            assert client.auth_token == "pre-generated-token"
            assert client.session.headers["authorization"] == "pre-generated-token"

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    def test_init_no_credentials(self, mock_session_class):
        """Test initialization without credentials logs warning"""
        mock_session = Mock()
        mock_session.get.return_value = Mock(status_code=200)
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            from jesse_mcp.core.jesse_rest_client import JesseRESTClient

            with patch("jesse_mcp.core.jesse_rest_client.logger") as mock_logger:
                client = JesseRESTClient(
                    base_url="http://test:8000",
                    password="",
                    api_token="",
                )

                mock_logger.warning.assert_called()


class TestAuthenticateWithPassword:
    """Tests for _authenticate_with_password method"""

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    @patch("jesse_mcp.core.jesse_rest_client.requests.post")
    def test_authenticate_success(self, mock_post, mock_session_class):
        """Test successful password authentication"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"auth_token": "session-abc-123"},
            raise_for_status=Mock(),
        )

        mock_session = Mock()
        mock_session.get.return_value = Mock(status_code=200)
        mock_session_class.return_value = mock_session

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            from jesse_mcp.core.jesse_rest_client import JesseRESTClient

            client = JesseRESTClient.__new__(JesseRESTClient)
            client.base_url = "http://test:8000"
            client.session = Mock()
            client.session.headers = {}
            client.auth_token = None

            client._authenticate_with_password("secret-password")

            assert client.auth_token == "session-abc-123"
            assert client.session.headers["authorization"] == "session-abc-123"

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    @patch("jesse_mcp.core.jesse_rest_client.requests.post")
    def test_authenticate_no_token_in_response(self, mock_post, mock_session_class):
        """Test authentication when response has no auth_token"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"error": "invalid password"},
            raise_for_status=Mock(),
        )

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.headers = {}
        client.auth_token = None

        with patch("jesse_mcp.core.jesse_rest_client.logger") as mock_logger:
            client._authenticate_with_password("wrong-password")

            assert client.auth_token is None
            mock_logger.error.assert_called()

    @patch("jesse_mcp.core.jesse_rest_client.requests.Session")
    @patch("jesse_mcp.core.jesse_rest_client.requests.post")
    def test_authenticate_connection_error(self, mock_post, mock_session_class):
        """Test authentication when connection fails"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.headers = {}
        client.auth_token = None

        with patch("jesse_mcp.core.jesse_rest_client.logger") as mock_logger:
            client._authenticate_with_password("password")

            assert client.auth_token is None
            mock_logger.error.assert_called()


class TestAuthenticateWithToken:
    """Tests for _authenticate_with_token method"""

    def test_authenticate_with_token_success(self):
        """Test setting pre-generated token"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.session = Mock()
        client.session.headers = {}
        client.auth_token = None

        client._authenticate_with_token("my-api-token-123")

        assert client.auth_token == "my-api-token-123"
        assert client.session.headers["authorization"] == "my-api-token-123"


class TestVerifyConnection:
    """Tests for _verify_connection method"""

    def test_verify_connection_success(self):
        """Test successful connection verification"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.return_value = Mock(status_code=200)

        with patch("jesse_mcp.core.jesse_rest_client.logger"):
            client._verify_connection()

        client.session.get.assert_called_once_with("http://test:8000/")

    def test_verify_connection_unauthorized(self):
        """Test connection verification with 401 response"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.return_value = Mock(status_code=401)

        with pytest.raises(ConnectionError, match="Unauthorized"):
            client._verify_connection()

    def test_verify_connection_server_error(self):
        """Test connection verification with 500 response"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.return_value = Mock(status_code=500)

        with pytest.raises(ConnectionError, match="500"):
            client._verify_connection()


class TestHealthCheck:
    """Tests for health_check method"""

    def test_health_check_connected(self):
        """Test health check when connected"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()

        client.session.get.side_effect = [
            Mock(
                status_code=200,
                json=lambda: {"version": "1.13.0"},
            ),
            Mock(
                status_code=200,
                json=lambda: ["Strategy1", "Strategy2"],
            ),
        ]

        result = client.health_check()

        assert result["connected"] is True
        assert result["jesse_version"] == "1.13.0"
        assert result["strategies_count"] == 2

    def test_health_check_unauthorized(self):
        """Test health check with unauthorized response"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.return_value = Mock(status_code=401)

        result = client.health_check()

        assert result["connected"] is False
        assert "Unauthorized" in result["error"]

    def test_health_check_timeout(self):
        """Test health check with connection timeout"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.side_effect = requests.exceptions.Timeout()

        result = client.health_check()

        assert result["connected"] is False
        assert "timeout" in result["error"].lower()

    def test_health_check_connection_refused(self):
        """Test health check with connection refused"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.side_effect = requests.exceptions.ConnectionError()

        result = client.health_check()

        assert result["connected"] is False
        assert "refused" in result["error"].lower()

    def test_health_check_strategies_dict_format(self):
        """Test health check with strategies in dict format"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()

        client.session.get.side_effect = [
            Mock(
                status_code=200,
                json=lambda: {"version": "1.13.0"},
            ),
            Mock(
                status_code=200,
                json=lambda: {"strategies": ["S1", "S2", "S3"]},
            ),
        ]

        result = client.health_check()

        assert result["strategies_count"] == 3


class TestBacktest:
    """Tests for backtest method"""

    def test_backtest_success(self):
        """Test successful backtest execution"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "total_return": 0.25,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.10,
            },
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            result = client.backtest(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
            )

            assert "total_return" in result
            assert result["total_return"] == 0.25

    def test_backtest_with_custom_parameters(self):
        """Test backtest with custom parameters"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True},
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            result = client.backtest(
                strategy="TestStrategy",
                symbol="ETH-USDT",
                timeframe="4h",
                start_date="2023-01-01",
                end_date="2023-12-31",
                exchange="Bybit",
                starting_balance=50000,
                fee=0.0005,
                leverage=2,
                exchange_type="futures",
            )

            call_args = client.session.post.call_args
            payload = call_args[1]["json"]

            assert payload["exchange"] == "Bybit"
            assert payload["config"]["starting_balance"] == 50000
            assert payload["routes"][0]["symbol"] == "ETH-USDT"

    def test_backtest_rate_limited(self):
        """Test backtest when rate limit is exceeded"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=False))

            result = client.backtest(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
            )

            assert "error" in result
            assert "Rate limit" in result["error"]

    def test_backtest_api_error(self):
        """Test backtest when API returns error"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.side_effect = requests.exceptions.HTTPError("500 Error")

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            result = client.backtest(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
            )

            assert "error" in result
            assert result["success"] is False


class TestOptimization:
    """Tests for optimization method"""

    def test_optimization_success(self):
        """Test successful optimization execution"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "best_params": {"rsi_period": 14},
                "best_value": 0.3,
            },
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            result = client.optimization(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
                param_space={
                    "rsi_period": {"type": "int", "min": 5, "max": 25},
                    "tp_rate": {"type": "float", "min": 0.01, "max": 0.1},
                },
            )

            assert "best_params" in result
            call_args = client.session.post.call_args
            payload = call_args[1]["json"]
            assert "hyperparameters" in payload

    def test_optimization_param_space_conversion(self):
        """Test optimization parameter space conversion"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {},
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            client.optimization(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
                param_space={
                    "int_param": {"type": "int", "min": 1, "max": 100},
                    "float_param": {"type": "float", "min": 0.0, "max": 1.0},
                },
            )

            call_args = client.session.post.call_args
            payload = call_args[1]["json"]
            hyperparams = payload["hyperparameters"]

            int_param = next(h for h in hyperparams if h["name"] == "int_param")
            float_param = next(h for h in hyperparams if h["name"] == "float_param")

            assert int_param["type"] == "int"
            assert int_param["min"] == 1
            assert int_param["max"] == 100
            assert float_param["type"] == "float"
            assert float_param["min"] == 0.0

    def test_optimization_rate_limited(self):
        """Test optimization when rate limit is exceeded"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=False))

            result = client.optimization(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
                param_space={},
            )

            assert "error" in result
            assert "Rate limit" in result["error"]


class TestMonteCarlo:
    """Tests for monte_carlo method"""

    def test_monte_carlo_success(self):
        """Test successful Monte Carlo simulation"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "var_95": -0.15,
                "var_99": -0.25,
                "max_drawdown": -0.30,
            },
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            result = client.monte_carlo(
                backtest_result={"trades": [], "metrics": {}},
                simulations=1000,
            )

            assert "var_95" in result
            call_args = client.session.post.call_args
            payload = call_args[1]["json"]
            assert payload["simulations"] == 1000

    def test_monte_carlo_with_custom_params(self):
        """Test Monte Carlo with custom parameters"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {},
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

            client.monte_carlo(
                backtest_result={},
                simulations=5000,
                block_size=30,
                confidence_levels=[0.90, 0.95, 0.99],
            )

            call_args = client.session.post.call_args
            payload = call_args[1]["json"]

            assert payload["simulations"] == 5000
            assert payload["block_size"] == 30
            assert payload["confidence_levels"] == [0.90, 0.95, 0.99]


class TestImportCandles:
    """Tests for import_candles method"""

    def test_import_candles_success(self):
        """Test import_candles successful call"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "Import started"},
            raise_for_status=Mock(),
        )

        result = client.import_candles(
            exchange="Binance",
            symbol="BTC-USDT",
            start_date="2023-01-01",
        )

        assert result["success"] is True
        client.session.post.assert_called_once()
        call_args = client.session.post.call_args
        assert "/candles/import" in call_args[0][0]

    def test_import_candles_with_end_date(self):
        """Test import_candles with optional end_date"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "Import started"},
            raise_for_status=Mock(),
        )

        result = client.import_candles(
            exchange="Binance",
            symbol="BTC-USDT",
            start_date="2023-01-01",
            end_date="2023-12-31",
        )

        assert result["success"] is True
        call_args = client.session.post.call_args
        payload = call_args[1]["json"]
        assert payload["end_date"] == "2023-12-31"

    def test_import_candles_async_mode(self):
        """Test import_candles with async_mode"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"status": "started", "job_id": "123"},
            raise_for_status=Mock(),
        )

        result = client.import_candles(
            exchange="Binance",
            symbol="BTC-USDT",
            start_date="2023-01-01",
            async_mode=True,
        )

        assert result["status"] == "started"
        call_args = client.session.post.call_args
        payload = call_args[1]["json"]
        assert payload["async_mode"] is True


class TestGetBacktestSessions:
    """Tests for get_backtest_sessions method"""

    def test_get_backtest_sessions_success(self):
        """Test fetching backtest sessions"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"sessions": [{"id": "123", "status": "completed"}]},
            raise_for_status=Mock(),
        )

        result = client.get_backtest_sessions()

        assert "sessions" in result
        assert len(result["sessions"]) == 1

    def test_get_backtest_sessions_error(self):
        """Test backtest sessions with API error"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.side_effect = Exception("Network error")

        with patch("jesse_mcp.core.jesse_rest_client.logger"):
            result = client.get_backtest_sessions()

            assert "error" in result
            assert result["sessions"] == []


class TestGetOptimizationSessions:
    """Tests for get_optimization_sessions method"""

    def test_get_optimization_sessions_success(self):
        """Test fetching optimization sessions"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"sessions": [{"id": "456", "status": "running"}]},
            raise_for_status=Mock(),
        )

        result = client.get_optimization_sessions()

        assert "sessions" in result


class TestCachedBacktest:
    """Tests for cached_backtest method"""

    def test_cached_backtest_cache_disabled(self):
        """Test cached_backtest when cache is disabled"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.post.return_value = Mock(
            status_code=200,
            json=lambda: {"total_return": 0.1},
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.JESSE_CACHE_ENABLED", False):
            with patch("jesse_mcp.core.jesse_rest_client.get_rate_limiter") as mock_limiter:
                mock_limiter.return_value = Mock(acquire=Mock(return_value=True))

                result = client.cached_backtest(
                    strategy="TestStrategy",
                    symbol="BTC-USDT",
                    timeframe="1h",
                    start_date="2023-01-01",
                    end_date="2023-12-31",
                )

                assert "total_return" in result

    def test_cached_backtest_cache_hit(self):
        """Test cached_backtest returns cached result"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()

        mock_cache = Mock()
        mock_cache.get.return_value = {"total_return": 0.2, "cached": True}

        with patch("jesse_mcp.core.jesse_rest_client.JESSE_CACHE_ENABLED", True):
            with patch(
                "jesse_mcp.core.jesse_rest_client.get_backtest_cache",
                return_value=mock_cache,
            ):
                result = client.cached_backtest(
                    strategy="TestStrategy",
                    symbol="BTC-USDT",
                    timeframe="1h",
                    start_date="2023-01-01",
                    end_date="2023-12-31",
                )

                assert result.get("cached") is True
                mock_cache.get.assert_called_once()


class TestGetStrategiesCached:
    """Tests for get_strategies_cached method"""

    def test_get_strategies_cached_cache_disabled(self):
        """Test get_strategies_cached when cache is disabled"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.return_value = Mock(
            status_code=200,
            json=lambda: ["Strategy1", "Strategy2"],
            raise_for_status=Mock(),
        )

        with patch("jesse_mcp.core.jesse_rest_client.JESSE_CACHE_ENABLED", False):
            result = client.get_strategies_cached()

            assert isinstance(result, list)

    def test_get_strategies_cached_error(self):
        """Test get_strategies_cached with API error"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"
        client.session = Mock()
        client.session.get.side_effect = Exception("API Error")

        with patch("jesse_mcp.core.jesse_rest_client.logger"):
            result = client._fetch_strategies()

            assert "error" in result
            assert result["strategies"] == []


class TestValidateBacktestResult:
    """Tests for _validate_backtest_result helper method"""

    def test_validate_success_all_fields(self):
        """Test validation passes with all fields"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {
            "total_return": 0.25,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.1,
            "win_rate": 0.55,
        }

        is_valid, message = client._validate_backtest_result(result)
        assert is_valid
        assert message == "Result validation passed"

    def test_validate_success_partial_fields(self):
        """Test validation passes with at least one metric field"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {"total_return": 0.25}

        is_valid, message = client._validate_backtest_result(result)
        assert is_valid
        assert "passed" in message.lower()

    def test_validate_failure_no_metrics(self):
        """Test validation fails when no metric fields present"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {"strategy": "TestStrategy", "symbol": "BTC-USDT"}

        is_valid, message = client._validate_backtest_result(result)
        assert not is_valid
        assert "metric" in message.lower()

    def test_validate_failure_error_in_result(self):
        """Test validation fails when error key present"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {"error": "Backtest failed"}

        is_valid, message = client._validate_backtest_result(result)
        assert not is_valid
        assert "error" in message.lower()

    def test_validate_failure_processing_status(self):
        """Test validation fails when status is processing"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {"status": "processing", "total_return": 0.25}

        is_valid, message = client._validate_backtest_result(result)
        assert not is_valid
        assert "processing" in message.lower()

    def test_validate_failure_nan_value(self):
        """Test validation fails when field contains NaN"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient
        import math

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {"total_return": math.nan, "sharpe_ratio": 1.5}

        is_valid, message = client._validate_backtest_result(result)
        assert not is_valid
        assert "nan" in message.lower()

    def test_validate_failure_non_numeric(self):
        """Test validation fails when numeric field is not numeric"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        result = {"total_return": "not a number", "sharpe_ratio": 1.5}

        is_valid, message = client._validate_backtest_result(result)
        assert not is_valid
        assert "numeric" in message.lower()


class TestBacktestWithRetry:
    """Tests for backtest_with_retry method"""

    def test_backtest_with_retry_success_first_attempt(self):
        """Test backtest succeeds on first attempt"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)
        client.base_url = "http://test:8000"

        # Mock successful backtest
        successful_result = {
            "total_return": 0.25,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.1,
            "win_rate": 0.55,
        }

        with patch.object(client, "backtest", return_value=successful_result):
            result = client.backtest_with_retry(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
            )

            assert result == successful_result

    def test_backtest_with_retry_success_after_retries(self):
        """Test backtest succeeds after retries"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        successful_result = {
            "total_return": 0.25,
            "sharpe_ratio": 1.5,
        }

        # Fail first, then succeed
        with patch.object(
            client,
            "backtest",
            side_effect=[
                {"error": "Rate limit exceeded"},
                successful_result,
            ],
        ):
            result = client.backtest_with_retry(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
                max_retries=3,
                initial_delay=0.01,
            )

            assert result == successful_result

    def test_backtest_with_retry_failure_all_attempts(self):
        """Test backtest fails after all retry attempts"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        # Always fail
        with patch.object(
            client,
            "backtest",
            return_value={"error": "Service unavailable"},
        ):
            result = client.backtest_with_retry(
                strategy="TestStrategy",
                symbol="BTC-USDT",
                timeframe="1h",
                start_date="2023-01-01",
                end_date="2023-12-31",
                max_retries=2,
                initial_delay=0.01,
            )

            assert "error" in result
            assert "failed after" in result["error"].lower()

    def test_is_retryable_error_timeout(self):
        """Test _is_retryable_error identifies timeout"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        assert client._is_retryable_error("Request timeout after 300s")
        assert client._is_retryable_error("timeout")

    def test_is_retryable_error_rate_limit(self):
        """Test _is_retryable_error identifies rate limit"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        assert client._is_retryable_error("Rate limit exceeded")
        assert client._is_retryable_error("rate limit")

    def test_is_retryable_error_not_retryable(self):
        """Test _is_retryable_error identifies non-retryable errors"""
        from jesse_mcp.core.jesse_rest_client import JesseRESTClient

        client = JesseRESTClient.__new__(JesseRESTClient)

        assert not client._is_retryable_error("Invalid strategy")
        assert not client._is_retryable_error("Authentication failed")


class TestGetJesseRestClient:
    """Tests for get_jesse_rest_client singleton function"""

    @patch("jesse_mcp.core.jesse_rest_client.JesseRESTClient")
    def test_get_client_creates_singleton(self, mock_client_class):
        """Test that get_jesse_rest_client creates and returns singleton"""
        import jesse_mcp.core.jesse_rest_client as module

        module._client = None

        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        client1 = module.get_jesse_rest_client()
        client2 = module.get_jesse_rest_client()

        assert client1 is client2
        mock_client_class.assert_called_once()

        module._client = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
