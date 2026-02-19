"""
Jesse REST API Client

Provides a clean abstraction over Jesse's REST API running on server2
allowing full interactivity with Jesse without requiring local module imports.

Configuration (via MetaMCP MCP Servers panel):
- JESSE_URL: URL to Jesse API (default: http://server2:8000)
- JESSE_PASSWORD: Jesse UI login password (for /auth/login endpoint)
- JESSE_API_TOKEN: Pre-generated API token from Jesse UI (alternative to password)
  Choose one of JESSE_PASSWORD or JESSE_API_TOKEN
"""

import os
import re
import requests
import logging
from typing import Dict, Any, Optional, List

from jesse_mcp.core.rate_limiter import get_rate_limiter
from jesse_mcp.core.cache import (
    get_backtest_cache,
    get_strategy_cache,
    JESSE_CACHE_ENABLED,
)

logger = logging.getLogger("jesse-mcp.rest-client")

# Get Jesse API configuration from environment
JESSE_URL = os.getenv("JESSE_URL", "http://localhost:9000")
JESSE_PASSWORD = os.getenv("JESSE_PASSWORD", "")
JESSE_API_TOKEN = os.getenv("JESSE_API_TOKEN", "")
JESSE_API_BASE = JESSE_URL

EXCHANGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "Binance": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,5}$",
        "symbol_format": "BTC-USDT",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Bybit": {
        "symbol_pattern": r"^[A-Z]{3,10}[A-Z]{3,5}$",
        "symbol_format": "BTCUSDT",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "OKX": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,5}(-[A-Z]{3,10})?$",
        "symbol_format": "BTC-USDT-SWAP",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Coinbase": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,4}$",
        "symbol_format": "BTC-USD",
        "timeframes": ["1m", "5m", "15m", "1h", "6h", "1d"],
        "supports_futures": False,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Gate": {
        "symbol_pattern": r"^[A-Z]{2,10}_[A-Z]{3,5}$",
        "symbol_format": "BTC_USDT",
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "8h", "1d", "1w", "1M"],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Hyperliquid": {
        "symbol_pattern": r"^[A-Z]{2,10}$",
        "symbol_format": "BTC",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
        ],
        "supports_futures": True,
        "supports_spot": False,
        "api_prefix": None,
    },
    "Apex": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,5}$",
        "symbol_format": "BTC-USDT",
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        "supports_futures": True,
        "supports_spot": False,
        "api_prefix": None,
    },
    "Bitfinex": {
        "symbol_pattern": r"^[tT][A-Z]{3,6}[A-Z]{3,6}$|^[A-Z]{2,6}/[A-Z]{3,6}$",
        "symbol_format": "tBTCUST",
        "timeframes": [
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "3h",
            "6h",
            "12h",
            "1d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
}


class JesseRESTClient:
    """Client for interacting with Jesse via REST API

    Supports two authentication methods:
    1. JESSE_PASSWORD: Login via /auth/login endpoint
    2. JESSE_API_TOKEN: Use pre-generated token directly
    """

    def __init__(
        self,
        base_url: str = JESSE_API_BASE,
        password: str = JESSE_PASSWORD,
        api_token: str = JESSE_API_TOKEN,
    ):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None

        # Try authentication with provided credentials
        if api_token:
            # Use pre-generated API token directly
            self._authenticate_with_token(api_token)
        elif password:
            # Login with password to get a session token
            self._authenticate_with_password(password)
        else:
            logger.warning("⚠️ No JESSE_PASSWORD or JESSE_API_TOKEN provided - requests will fail")

        self._verify_connection()

    def _authenticate_with_token(self, token: str):
        """Use a pre-generated API token directly"""
        try:
            self.auth_token = token
            # Use lowercase 'authorization' header with raw token (no Bearer prefix)
            self.session.headers.update({"authorization": self.auth_token})
            logger.info("✅ Authenticated with Jesse API (using pre-generated token)")
        except Exception as e:
            logger.error(f"❌ Token configuration failed: {e}")

    def _authenticate_with_password(self, password: str):
        """Authenticate with Jesse API password to obtain a session token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"password": password},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            self.auth_token = data.get("auth_token")
            if self.auth_token:
                # Use lowercase 'authorization' header with raw token (no Bearer prefix)
                self.session.headers.update({"authorization": self.auth_token})
                logger.info("✅ Authenticated with Jesse API (via login)")
            else:
                logger.error("❌ No auth_token in login response")
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")

    def _verify_connection(self):
        """Verify connection to Jesse API"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 401:
                raise ConnectionError("Unauthorized - check JESSE_API_TOKEN")
            if response.status_code != 200:
                raise ConnectionError(f"Jesse API returned {response.status_code}")
            logger.info(f"✅ Connected to Jesse API at {self.base_url}")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Jesse API: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Check Jesse API health and return status info.

        Returns:
            Dict with connection status, Jesse version, and strategies count
        """
        result = {
            "connected": False,
            "jesse_url": self.base_url,
            "jesse_version": None,
            "strategies_count": None,
            "error": None,
        }

        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                result["connected"] = True
                data = response.json()
                result["jesse_version"] = data.get("version", "unknown")
            elif response.status_code == 401:
                result["error"] = "Unauthorized - check JESSE_API_TOKEN"
            else:
                result["error"] = f"Jesse API returned {response.status_code}"
        except requests.exceptions.Timeout:
            result["error"] = "Connection timeout"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection refused"
        except Exception as e:
            result["error"] = str(e)

        if result["connected"]:
            try:
                strategies_response = self.session.get(f"{self.base_url}/strategies", timeout=5)
                if strategies_response.status_code == 200:
                    strategies_data = strategies_response.json()
                    if isinstance(strategies_data, list):
                        result["strategies_count"] = len(strategies_data)
                    elif isinstance(strategies_data, dict):
                        strategies = strategies_data.get("strategies", [])
                        result["strategies_count"] = len(strategies)
            except Exception:
                pass

        return result

    def backtest(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        hyperparameters: Optional[Dict[str, Any]] = None,
        include_trades: bool = False,
        include_equity_curve: bool = False,
        include_logs: bool = False,
    ) -> Dict[str, Any]:
        """
        Run a backtest via Jesse REST API

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            timeframe: Candle timeframe
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            exchange: Exchange name
            starting_balance: Initial capital
            fee: Trading fee
            leverage: Leverage for futures
            exchange_type: 'spot' or 'futures'
            hyperparameters: Strategy parameter overrides
            include_trades: Include individual trades
            include_equity_curve: Include equity curve data
            include_logs: Include strategy logs

        Returns:
            Backtest results dict
        """
        try:
            logger.info(f"Starting backtest via REST API: {strategy} on {symbol}")

            import uuid

            # Format routes and data_routes as Jesse expects
            routes = [
                {
                    "exchange": exchange,
                    "strategy": strategy,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

            data_routes = [
                {
                    "exchange": exchange,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

            # Format config as Jesse 1.13.x expects
            config = {
                "starting_balance": starting_balance,
                "fee": fee,
                "futures_leverage": leverage,
                "type": exchange_type,
                "warm_up_candles": 240,
                "logging": {
                    "balance": True,
                    "trades": include_trades,
                    "signals": False,
                },
                "exchanges": {
                    exchange: {
                        "name": exchange,
                        "fee": fee,
                        "type": exchange_type,
                        "balance": starting_balance,
                        "futures_leverage": int(leverage),
                        "futures_leverage_mode": "cross",
                    }
                },
            }

            # Jesse 1.13.x payload format
            payload = {
                "id": str(uuid.uuid4()),
                "exchange": exchange,
                "routes": routes,
                "data_routes": data_routes,
                "config": config,
                "start_date": start_date,
                "finish_date": end_date,
                "debug_mode": include_logs,
                "export_csv": False,
                "export_json": include_trades,
                "export_chart": False,
                "export_tradingview": False,
                "fast_mode": True,
                "benchmark": False,
            }

            result = self._rate_limited_backtest(payload)

            logger.info(f"✅ Backtest completed for {strategy}")
            return result

        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return {"error": str(e), "success": False}

    def cached_backtest(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a backtest with caching support (1 hour TTL by default).

        Cache key is based on all parameters - identical requests will return
        cached results if within TTL.

        Args:
            Same as backtest()

        Returns:
            Backtest results dict (cached or fresh)
        """
        if not JESSE_CACHE_ENABLED:
            return self.backtest(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                starting_balance=starting_balance,
                fee=fee,
                leverage=leverage,
                exchange_type=exchange_type,
                hyperparameters=hyperparameters,
            )

        cache = get_backtest_cache()
        cache_key = cache._hash_key(
            strategy,
            symbol,
            timeframe,
            start_date,
            end_date,
            exchange,
            starting_balance,
            fee,
            leverage,
            exchange_type,
            tuple(sorted((hyperparameters or {}).items())),
        )

        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"✅ Cache hit for backtest: {strategy} on {symbol}")
            return cached

        result = self.backtest(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            hyperparameters=hyperparameters,
        )

        if "error" not in result:
            cache.set(cache_key, result)
            logger.debug(f"Cached backtest result for: {strategy} on {symbol}")

        return result

    def get_strategies_cached(self) -> Dict[str, Any]:
        """
        Get list of strategies with caching (5 minute TTL by default).

        Returns:
            Dict with strategies list
        """
        if not JESSE_CACHE_ENABLED:
            return self._fetch_strategies()

        cache = get_strategy_cache()
        cache_key = "strategy_list"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info("✅ Cache hit for strategy list")
            return cached

        result = self._fetch_strategies()
        if "error" not in result:
            cache.set(cache_key, result)
            logger.debug("Cached strategy list")

        return result

    def _fetch_strategies(self) -> Dict[str, Any]:
        """Fetch strategies from API without caching."""
        try:
            response = self.session.get(f"{self.base_url}/strategies", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get strategies: {e}")
            return {"error": str(e), "strategies": []}

    def _rate_limited_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[requests.Response]:
        limiter = get_rate_limiter()
        if not limiter.acquire():
            return None
        return getattr(self.session, method)(f"{self.base_url}{endpoint}", **kwargs)

    def _rate_limited_backtest(self, payload: dict) -> Dict[str, Any]:
        limiter = get_rate_limiter()
        if not limiter.acquire():
            return {"error": "Rate limit exceeded", "success": False}
        response = self.session.post(f"{self.base_url}/backtest", json=payload)
        response.raise_for_status()
        return response.json()

    def _rate_limited_optimization(self, payload: dict) -> Dict[str, Any]:
        limiter = get_rate_limiter()
        if not limiter.acquire():
            return {"error": "Rate limit exceeded", "success": False}
        response = self.session.post(f"{self.base_url}/optimization", json=payload)
        response.raise_for_status()
        return response.json()

    def _rate_limited_monte_carlo(self, payload: dict) -> Dict[str, Any]:
        limiter = get_rate_limiter()
        if not limiter.acquire():
            return {"error": "Rate limit exceeded", "success": False}
        response = self.session.post(f"{self.base_url}/monte-carlo", json=payload)
        response.raise_for_status()
        return response.json()

    def optimization(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        param_space: Dict[str, Any],
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
    ) -> Dict[str, Any]:
        """
        Run optimization via Jesse REST API

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            timeframe: Candle timeframe
            start_date: Start date
            end_date: End date
            param_space: Parameter space for optimization
            exchange: Exchange name
            starting_balance: Initial capital
            fee: Trading fee
            leverage: Leverage
            exchange_type: 'spot' or 'futures'

        Returns:
            Optimization results dict
        """
        try:
            logger.info(f"Starting optimization via REST API: {strategy}")

            import uuid

            # Format routes for Jesse 1.13.x
            routes = [
                {
                    "exchange": exchange,
                    "strategy": strategy,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

            data_routes = [
                {
                    "exchange": exchange,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

            config = {
                "starting_balance": starting_balance,
                "fee": fee,
                "futures_leverage": leverage,
                "type": exchange_type,
                "warm_up_candles": 240,
                "logging": {
                    "balance": True,
                    "trades": False,
                    "signals": False,
                },
                "exchanges": {
                    exchange: {
                        "name": exchange,
                        "fee": fee,
                        "type": exchange_type,
                        "balance": starting_balance,
                        "futures_leverage": int(leverage),
                        "futures_leverage_mode": "cross",
                    }
                },
            }

            # Convert param_space to Jesse's hyperparameters format
            hyperparameters = []
            for name, spec in param_space.items():
                hp = {"name": name}
                if spec.get("type") == "int":
                    hp["type"] = "int"
                    hp["min"] = spec.get("min", 1)
                    hp["max"] = spec.get("max", 100)
                    hp["default"] = spec.get("default", (hp["min"] + hp["max"]) // 2)
                elif spec.get("type") == "float":
                    hp["type"] = "float"
                    hp["min"] = spec.get("min", 0.0)
                    hp["max"] = spec.get("max", 1.0)
                    hp["default"] = spec.get("default", (hp["min"] + hp["max"]) / 2)
                else:
                    hp["type"] = str(spec.get("type", "str"))
                    hp["default"] = spec.get("default", "")
                hyperparameters.append(hp)

            # Jesse 1.13.x optimization payload
            payload = {
                "id": str(uuid.uuid4()),
                "exchange": exchange,
                "routes": routes,
                "data_routes": data_routes,
                "config": config,
                "start_date": start_date,
                "finish_date": end_date,
                "hyperparameters": hyperparameters,
                "n_trials": param_space.get("n_trials", 50),
                "max_cpus": 1,
            }

            result = self._rate_limited_optimization(payload)

            logger.info(f"✅ Optimization started for {strategy}")
            return result

        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            return {"error": str(e), "success": False}

    def monte_carlo(
        self,
        backtest_result: Dict[str, Any],
        simulations: int = 10000,
        block_size: int = 20,
        confidence_levels: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation via REST API

        Args:
            backtest_result: Backtest result to analyze
            simulations: Number of simulations
            block_size: Block size for resampling
            confidence_levels: Confidence levels to compute

        Returns:
            Monte Carlo results dict
        """
        try:
            logger.info("Starting Monte Carlo simulation via REST API")

            payload = {
                "backtest_result": backtest_result,
                "simulations": simulations,
                "block_size": block_size,
            }

            if confidence_levels:
                payload["confidence_levels"] = confidence_levels

            result = self._rate_limited_monte_carlo(payload)

            logger.info("✅ Monte Carlo simulation completed")
            return result

        except Exception as e:
            logger.error(f"❌ Monte Carlo failed: {e}")
            return {"error": str(e), "success": False}

    def import_candles(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
        async_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Import candle data from exchange via Jesse REST API.

        This is a long-running operation. Jesse returns progress info
        that can be polled to track import status.

        Args:
            exchange: Exchange name (e.g., "Binance")
            symbol: Trading symbol (e.g., "BTC-USDT")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to now)
            async_mode: If True, return immediately without waiting for completion

        Returns:
            Dict with import status, progress info, or error details
        """
        try:
            logger.info(f"📥 Importing candles: {exchange} {symbol} from {start_date}")

            payload: Dict[str, Any] = {
                "exchange": exchange,
                "symbol": symbol,
                "start_date": start_date,
            }

            if end_date:
                payload["end_date"] = end_date

            if async_mode:
                payload["async_mode"] = True

            response = self.session.post(
                f"{self.base_url}/candles/import",
                json=payload,
                timeout=300 if not async_mode else 30,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success", False) or result.get("status") == "started":
                logger.info(f"✅ Candle import started for {exchange} {symbol}")
            else:
                logger.warning(f"⚠️ Candle import response: {result.get('message', 'unknown')}")

            return result

        except requests.exceptions.Timeout:
            logger.error(f"❌ Candle import timeout for {exchange} {symbol}")
            return {
                "error": "Import request timed out - try async_mode=True",
                "success": False,
            }
        except Exception as e:
            logger.error(f"❌ Candle import failed: {e}")
            return {"error": str(e), "success": False}

    def cancel_import(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel a running candle import via Jesse REST API.

        Args:
            exchange: Exchange name
            symbol: Trading symbol

        Returns:
            Dict with cancellation status
        """
        try:
            logger.info(f"🚫 Cancelling import: {exchange} {symbol}")

            payload = {
                "exchange": exchange,
                "symbol": symbol,
            }

            response = self.session.post(
                f"{self.base_url}/candles/cancel-import",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success", False) or result.get("cancelled", False):
                logger.info(f"✅ Import cancelled for {exchange} {symbol}")
            else:
                logger.warning(f"⚠️ Cancel response: {result.get('message', 'unknown')}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to cancel import: {e}")
            return {"error": str(e), "success": False}

    def get_existing_candles(
        self,
        exchange: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get list of existing candles with date ranges via Jesse REST API.

        Args:
            exchange: Filter by exchange name (optional)
            symbol: Filter by trading symbol (optional)

        Returns:
            Dict with list of available candle data and their date ranges
        """
        try:
            logger.info("📊 Fetching existing candles info")

            payload = {}
            if exchange:
                payload["exchange"] = exchange
            if symbol:
                payload["symbol"] = symbol

            response = self.session.post(
                f"{self.base_url}/candles/existing",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            candles = result.get("candles", result.get("data", []))
            count = len(candles) if isinstance(candles, list) else 0
            logger.info(f"✅ Found {count} existing candle datasets")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to get existing candles: {e}")
            return {"error": str(e), "candles": []}

    def get_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get candle data for a specific exchange/symbol/timeframe.

        Args:
            exchange: Exchange name
            symbol: Trading symbol
            timeframe: Candle timeframe (e.g., "1h", "4h", "1d")
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            Dict with candle data
        """
        try:
            logger.info(f"📊 Fetching candles: {exchange} {symbol} {timeframe}")

            payload = {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
            }

            if start_date:
                payload["start_date"] = start_date
            if end_date:
                payload["end_date"] = end_date

            response = self.session.post(
                f"{self.base_url}/candles/get",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            candles = result.get("candles", result.get("data", []))
            count = len(candles) if isinstance(candles, list) else 0
            logger.info(f"✅ Retrieved {count} candles")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to get candles: {e}")
            return {"error": str(e), "candles": []}

    def delete_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delete candle data for a specific exchange/symbol.

        Args:
            exchange: Exchange name
            symbol: Trading symbol
            timeframe: Specific timeframe to delete (optional, deletes all if omitted)

        Returns:
            Dict with deletion status
        """
        try:
            logger.info(f"🗑️ Deleting candles: {exchange} {symbol}")

            payload = {
                "exchange": exchange,
                "symbol": symbol,
            }

            if timeframe:
                payload["timeframe"] = timeframe

            response = self.session.post(
                f"{self.base_url}/candles/delete",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success", False):
                logger.info(f"✅ Candles deleted for {exchange} {symbol}")
            else:
                logger.warning(f"⚠️ Delete response: {result.get('message', 'unknown')}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to delete candles: {e}")
            return {"error": str(e), "success": False}

    def clear_candles_cache(self) -> Dict[str, Any]:
        """
        Clear the candles database cache via Jesse REST API.

        Returns:
            Dict with cache clear status
        """
        try:
            logger.info("🧹 Clearing candles cache")

            response = self.session.post(
                f"{self.base_url}/candles/clear-cache",
                json={},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success", False):
                logger.info("✅ Candles cache cleared")
            else:
                logger.warning(f"⚠️ Cache clear response: {result.get('message', 'unknown')}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to clear candles cache: {e}")
            return {"error": str(e), "success": False}

    def get_supported_symbols(self, exchange: str) -> Dict[str, Any]:
        """
        Get list of supported symbols for an exchange.

        Args:
            exchange: Exchange name

        Returns:
            Dict with list of supported symbols
        """
        try:
            logger.info(f"📋 Fetching supported symbols for {exchange}")

            payload = {"exchange": exchange}

            response = self.session.post(
                f"{self.base_url}/exchange/supported-symbols",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            symbols = result.get("symbols", result.get("data", []))
            count = len(symbols) if isinstance(symbols, list) else 0
            logger.info(f"✅ Found {count} symbols for {exchange}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to get supported symbols: {e}")
            return {"error": str(e), "symbols": []}

    @staticmethod
    def list_supported_exchanges() -> List[str]:
        """
        Get list of supported exchanges.

        Returns:
            List of exchange names
        """
        return list(EXCHANGE_CONFIG.keys())

    @staticmethod
    def get_exchange_config(exchange: str) -> Dict[str, Any]:
        """
        Get configuration for a specific exchange.

        Args:
            exchange: Exchange name

        Returns:
            Dict with exchange config or error if not found
        """
        config = EXCHANGE_CONFIG.get(exchange)
        if config is None:
            return {
                "error": f"Unknown exchange: {exchange}",
                "valid_exchanges": list(EXCHANGE_CONFIG.keys()),
            }
        return {"exchange": exchange, **config}

    @staticmethod
    def validate_symbol(exchange: str, symbol: str) -> Dict[str, Any]:
        """
        Validate a trading symbol format for a specific exchange.

        Args:
            exchange: Exchange name
            symbol: Trading symbol to validate

        Returns:
            Dict with validation result and details
        """
        config = EXCHANGE_CONFIG.get(exchange)
        if config is None:
            return {
                "valid": False,
                "error": f"Unknown exchange: {exchange}",
                "valid_exchanges": list(EXCHANGE_CONFIG.keys()),
            }

        pattern = config.get("symbol_pattern", "")
        if not pattern:
            return {
                "valid": True,
                "warning": "No validation pattern defined for this exchange",
                "symbol": symbol,
                "expected_format": config.get("symbol_format"),
            }

        if re.match(pattern, symbol):
            logger.info(f"✅ Symbol validated: {symbol} for {exchange}")
            return {
                "valid": True,
                "symbol": symbol,
                "exchange": exchange,
                "expected_format": config.get("symbol_format"),
            }
        else:
            logger.warning(f"⚠️ Invalid symbol format: {symbol} for {exchange}")
            return {
                "valid": False,
                "error": f"Symbol '{symbol}' does not match expected format for {exchange}",
                "symbol": symbol,
                "exchange": exchange,
                "expected_format": config.get("symbol_format"),
                "pattern": pattern,
            }

    @staticmethod
    def validate_timeframe(exchange: str, timeframe: str) -> Dict[str, Any]:
        """
        Validate a timeframe for a specific exchange.

        Args:
            exchange: Exchange name
            timeframe: Timeframe to validate (e.g., "1h", "4h", "1d")

        Returns:
            Dict with validation result
        """
        config = EXCHANGE_CONFIG.get(exchange)
        if config is None:
            return {
                "valid": False,
                "error": f"Unknown exchange: {exchange}",
                "valid_exchanges": list(EXCHANGE_CONFIG.keys()),
            }

        supported = config.get("timeframes", [])
        if timeframe in supported:
            return {"valid": True, "timeframe": timeframe, "exchange": exchange}
        else:
            return {
                "valid": False,
                "error": f"Timeframe '{timeframe}' not supported by {exchange}",
                "timeframe": timeframe,
                "exchange": exchange,
                "supported_timeframes": supported,
            }

    def get_backtest_sessions(self) -> Dict[str, Any]:
        """Get list of backtest sessions"""
        try:
            payload = {"limit": 50, "offset": 0}
            response = self.session.post(f"{self.base_url}/backtest/sessions", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get backtest sessions: {e}")
            return {"error": str(e), "sessions": []}

    def get_optimization_sessions(self) -> Dict[str, Any]:
        """Get list of optimization sessions"""
        try:
            payload = {"limit": 50, "offset": 0}
            response = self.session.post(f"{self.base_url}/optimization/sessions", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get optimization sessions: {e}")
            return {"error": str(e), "sessions": []}

    def check_live_plugin_available(self) -> Dict[str, Any]:
        """
        Check if jesse-live plugin is installed and available.

        Returns:
            Dict with 'available' boolean and optional 'error' message
        """
        try:
            response = self.session.get(f"{self.base_url}/live/sessions", timeout=10)
            if response.status_code == 200:
                logger.info("✅ jesse-live plugin is available")
                return {"available": True}
            elif response.status_code == 404:
                logger.warning("⚠️ jesse-live plugin not installed")
                return {"available": False, "error": "jesse-live plugin not installed"}
            else:
                return {"available": False, "error": f"Unexpected status: {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Failed to check live plugin: {e}")
            return {"available": False, "error": str(e)}

    def start_live_session(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        exchange: str,
        exchange_api_key_id: str,
        notification_api_key_id: str = "",
        paper_mode: bool = True,
        debug_mode: bool = False,
        config: Optional[Dict[str, Any]] = None,
        routes: Optional[List[Dict[str, str]]] = None,
        data_routes: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Start a live or paper trading session via Jesse REST API.

        Args:
            strategy: Strategy name
            symbol: Trading symbol (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h")
            exchange: Exchange name (e.g., "Binance")
            exchange_api_key_id: ID of stored exchange API key
            notification_api_key_id: ID of stored notification config (optional)
            paper_mode: True for paper trading (simulated), False for live (real money)
            debug_mode: Enable debug logging
            config: Additional configuration dict
            routes: Custom routes (default: single route for strategy)
            data_routes: Custom data routes (default: single route for data)

        Returns:
            Dict with session info or error
        """
        try:
            import uuid

            mode = "paper" if paper_mode else "LIVE"
            logger.info(f"🚀 Starting {mode} trading session: {strategy} on {symbol}")

            if routes is None:
                routes = [
                    {
                        "exchange": exchange,
                        "strategy": strategy,
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                ]

            if data_routes is None:
                data_routes = [
                    {
                        "exchange": exchange,
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                ]

            default_config = {
                "warm_up_candles": 240,
                "logging": {"output_type": "json"},
            }
            if config:
                default_config.update(config)

            payload = {
                "id": str(uuid.uuid4()),
                "exchange": exchange,
                "exchange_api_key_id": exchange_api_key_id,
                "notification_api_key_id": notification_api_key_id,
                "routes": routes,
                "data_routes": data_routes,
                "config": default_config,
                "debug_mode": debug_mode,
                "paper_mode": paper_mode,
            }

            response = self.session.post(
                f"{self.base_url}/live",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            result["session_id"] = payload["id"]
            result["paper_mode"] = paper_mode

            logger.info(f"✅ {mode.upper()} trading session started: {payload['id']}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to start live session: {e}")
            return {"error": str(e), "success": False}

    def cancel_live_session(self, session_id: str, paper_mode: bool = True) -> Dict[str, Any]:
        """
        Cancel a running live trading session.

        Args:
            session_id: Session ID to cancel
            paper_mode: True if paper trading, False if live trading

        Returns:
            Dict with cancellation status
        """
        try:
            mode = "paper" if paper_mode else "LIVE"
            logger.info(f"🛑 Cancelling {mode} session: {session_id}")

            payload = {
                "id": session_id,
                "paper_mode": paper_mode,
            }

            response = self.session.post(
                f"{self.base_url}/live/cancel",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ Session cancelled: {session_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to cancel session: {e}")
            return {"error": str(e), "success": False}

    def get_live_sessions(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get list of live trading sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Offset for pagination

        Returns:
            Dict with sessions list
        """
        try:
            logger.info("📋 Fetching live sessions")

            payload = {"limit": limit, "offset": offset}

            response = self.session.post(
                f"{self.base_url}/live/sessions",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            sessions = result.get("sessions", result.get("data", []))
            count = len(sessions) if isinstance(sessions, list) else 0
            logger.info(f"✅ Found {count} live sessions")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to get live sessions: {e}")
            return {"error": str(e), "sessions": []}

    def get_live_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get a specific live session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Dict with session details
        """
        try:
            logger.info(f"📊 Fetching live session: {session_id}")

            payload = {"id": session_id}

            response = self.session.post(
                f"{self.base_url}/live/sessions/{session_id}",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ Retrieved session: {session_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to get live session: {e}")
            return {"error": str(e), "session": None}

    def get_live_logs(
        self,
        session_id: str,
        log_type: str = "all",
        start_time: int = 0,
    ) -> Dict[str, Any]:
        """
        Get logs for a live trading session.

        Args:
            session_id: Session ID
            log_type: Log type filter ("all", "info", "error", "warning")
            start_time: Unix timestamp to filter logs from

        Returns:
            Dict with logs data
        """
        try:
            logger.info(f"📜 Fetching logs for session: {session_id}")

            payload = {
                "id": session_id,
                "type": log_type,
                "start_time": start_time,
            }

            response = self.session.post(
                f"{self.base_url}/live/logs",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            logs = result.get("data", [])
            count = len(logs) if isinstance(logs, list) else 0
            logger.info(f"✅ Retrieved {count} log entries")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to get live logs: {e}")
            return {"error": str(e), "data": []}

    def get_live_orders(self, session_id: str) -> Dict[str, Any]:
        """
        Get orders for a live trading session.

        Args:
            session_id: Session ID

        Returns:
            Dict with orders data
        """
        try:
            logger.info(f"📦 Fetching orders for session: {session_id}")

            payload = {"id": session_id}

            response = self.session.post(
                f"{self.base_url}/live/orders",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            orders = result.get("orders", result.get("data", []))
            count = len(orders) if isinstance(orders, list) else 0
            logger.info(f"✅ Retrieved {count} orders")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to get live orders: {e}")
            return {"error": str(e), "orders": []}

    def get_live_equity_curve(
        self,
        session_id: str,
        from_ms: Optional[int] = None,
        to_ms: Optional[int] = None,
        timeframe: str = "auto",
        max_points: int = 1000,
    ) -> Dict[str, Any]:
        """
        Get equity curve for a live trading session.

        Args:
            session_id: Session ID
            from_ms: Start time in milliseconds (optional)
            to_ms: End time in milliseconds (optional)
            timeframe: Timeframe for downsampling ("auto" or specific)
            max_points: Maximum number of data points

        Returns:
            Dict with equity curve data
        """
        try:
            logger.info(f"📈 Fetching equity curve for session: {session_id}")

            params = {
                "session_id": session_id,
                "timeframe": timeframe,
                "max_points": max_points,
            }
            if from_ms is not None:
                params["from_ms"] = from_ms
            if to_ms is not None:
                params["to_ms"] = to_ms

            response = self.session.get(
                f"{self.base_url}/live/equity-curve",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ Retrieved equity curve")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to get equity curve: {e}")
            return {"error": str(e), "data": []}

    def update_live_session_notes(self, session_id: str, notes: str) -> Dict[str, Any]:
        """
        Update notes for a live trading session.

        Args:
            session_id: Session ID
            notes: Notes text

        Returns:
            Dict with update status
        """
        try:
            logger.info(f"📝 Updating notes for session: {session_id}")

            payload = {"id": session_id, "notes": notes}

            response = self.session.post(
                f"{self.base_url}/live/sessions/{session_id}/notes",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ Updated session notes")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to update session notes: {e}")
            return {"error": str(e), "success": False}

    def purge_live_sessions(self, days_old: Optional[int] = None) -> Dict[str, Any]:
        """
        Purge old live trading sessions from database.

        Args:
            days_old: Delete sessions older than this many days (optional)

        Returns:
            Dict with deletion count
        """
        try:
            logger.info(f"🧹 Purging old live sessions")

            payload = {}
            if days_old is not None:
                payload["days_old"] = days_old

            response = self.session.post(
                f"{self.base_url}/live/purge-sessions",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            deleted = result.get("deleted_count", 0)
            logger.info(f"✅ Purged {deleted} sessions")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to purge sessions: {e}")
            return {"error": str(e), "deleted_count": 0}


# Global instance
_client = None


def get_jesse_rest_client() -> JesseRESTClient:
    """Get or create the global Jesse REST client"""
    global _client
    if _client is None:
        _client = JesseRESTClient()
    return _client
