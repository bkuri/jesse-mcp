"""
Jesse REST API Client

Provides a clean abstraction over Jesse's REST API running on server2
allowing full interactivity with Jesse without requiring local module imports.

Configuration (via MetaMCP MCP Servers panel or environment variables):
- JESSE_URL: URL to Jesse API (default: http://server2:9100)
- JESSE_PASSWORD: Jesse UI login password (recommended - will auto-login)
- JESSE_API_TOKEN: Session token from /auth/login (alternative to password)
  IMPORTANT: This is NOT the LICENSE_API_TOKEN from .env - it must be a session token!
  To get a session token, call POST /auth/login with your password, or use JESSE_PASSWORD instead.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

from jesse_mcp.core.cache import (
    get_backtest_cache,
    get_strategy_cache,
    JESSE_CACHE_ENABLED,
)
from jesse_mcp.core.rate_limiter import get_rate_limiter

from . import auth, backtest, candles, config, live, optimization

logger = logging.getLogger("jesse-mcp.rest-client")

JESSE_URL = os.getenv("JESSE_URL", "http://server2:9100")
JESSE_PASSWORD = os.getenv("JESSE_PASSWORD", "")
JESSE_API_TOKEN = os.getenv("JESSE_API_TOKEN", "")
JESSE_API_BASE = JESSE_URL


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

        if api_token:
            self.auth_token = auth.authenticate_with_token(self.session, self.base_url, api_token)
        elif password:
            self.auth_token = auth.authenticate_with_password(self.session, self.base_url, password)
        else:
            logger.warning("⚠️ No JESSE_PASSWORD or JESSE_API_TOKEN provided - requests will fail")

        auth.verify_connection(self.session, self.base_url)

    def health_check(self) -> Dict[str, Any]:
        """Check Jesse API health and return status info."""
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
        routes: List[Dict[str, str]],
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        data_routes: Optional[List[Dict[str, str]]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        include_trades: bool = False,
        include_equity_curve: bool = False,
        include_logs: bool = False,
        auto_import_candles: bool = False,
        auto_import_max_candles: int = 50000,
        fast_mode: bool = True,
    ) -> Dict[str, Any]:
        """Run a backtest via Jesse REST API."""
        try:
            logger.info(f"Starting backtest via REST API with {len(routes)} routes")

            validation_error = candles.validate_candle_data(
                self.session,
                self.base_url,
                routes,
                exchange,
                exchange_type,
                start_date,
                end_date,
                auto_import_candles=auto_import_candles,
                auto_import_max_candles=auto_import_max_candles,
            )
            if validation_error:
                return validation_error

            payload = backtest.build_backtest_payload(
                routes=routes,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                starting_balance=starting_balance,
                exchange_type=exchange_type,
                data_routes=data_routes,
                include_logs=include_logs,
                include_trades=include_trades,
                fast_mode=fast_mode,
            )

            result = backtest.execute_backtest(self.session, self.base_url, payload)

            is_valid, message = backtest.validate_backtest_result(result)
            if not is_valid:
                logger.warning(f"⚠️  Backtest result validation failed: {message}")
                return {
                    "error": f"Invalid backtest result: {message}",
                    "success": False,
                    "raw_result": result,
                }

            logger.info(f"✅ Backtest completed for {len(routes)} routes")
            return result

        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return {"error": str(e), "success": False}

    def cached_backtest(
        self,
        routes: List[Dict[str, str]],
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        data_routes: Optional[List[Dict[str, str]]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        include_trades: bool = False,
        include_equity_curve: bool = False,
        include_logs: bool = False,
        auto_import_candles: bool = False,
        auto_import_max_candles: int = 50000,
        fast_mode: bool = True,
    ) -> Dict[str, Any]:
        """Run a backtest with caching support (1 hour TTL by default)."""
        if not JESSE_CACHE_ENABLED:
            return self.backtest(
                routes=routes,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                starting_balance=starting_balance,
                fee=fee,
                leverage=leverage,
                exchange_type=exchange_type,
                data_routes=data_routes,
                hyperparameters=hyperparameters,
                include_trades=include_trades,
                include_equity_curve=include_equity_curve,
                include_logs=include_logs,
            )

        cache = get_backtest_cache()
        route_key = json.dumps(routes, sort_keys=True)
        cache_key = cache._hash_key(
            route_key,
            start_date,
            end_date,
            exchange,
            starting_balance,
            fee,
            leverage,
            exchange_type,
            json.dumps(data_routes or [], sort_keys=True) if data_routes else "",
            json.dumps(hyperparameters or {}, sort_keys=True) if hyperparameters else "",
        )

        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"✅ Cache hit for backtest with {len(routes)} routes")
            return cached

        result = self.backtest(
            routes=routes,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            data_routes=data_routes,
            hyperparameters=hyperparameters,
            include_trades=include_trades,
            include_equity_curve=include_equity_curve,
            include_logs=include_logs,
            auto_import_candles=auto_import_candles,
            auto_import_max_candles=auto_import_max_candles,
            fast_mode=fast_mode,
        )

        if "error" not in result:
            cache.set(cache_key, result)
            logger.debug(f"Cached backtest result for {len(routes)} routes")

        return result

    def backtest_with_retry(
        self,
        routes: List[Dict[str, str]],
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        data_routes: Optional[List[Dict[str, str]]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        auto_import_candles: bool = False,
        auto_import_max_candles: int = 50000,
        fast_mode: bool = True,
    ) -> Dict[str, Any]:
        """Run a backtest with retry logic for transient errors."""
        import time

        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Backtest attempt {attempt + 1}/{max_retries}: {len(routes)} routes")

                result = self.backtest(
                    routes=routes,
                    start_date=start_date,
                    end_date=end_date,
                    exchange=exchange,
                    starting_balance=starting_balance,
                    fee=fee,
                    leverage=leverage,
                    exchange_type=exchange_type,
                    data_routes=data_routes,
                    hyperparameters=hyperparameters,
                    auto_import_candles=auto_import_candles,
                    auto_import_max_candles=auto_import_max_candles,
                    fast_mode=fast_mode,
                )

                if "error" not in result and result.get("success", True):
                    logger.info(f"✅ Backtest succeeded on attempt {attempt + 1}/{max_retries}")
                    return result

                error_msg = result.get("error", "Unknown error")
                if backtest.is_retryable_error(error_msg):
                    last_error = error_msg
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2**attempt)
                        logger.warning(f"⚠️  Retryable error: {error_msg}. Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                else:
                    logger.error(f"❌ Non-retryable error: {error_msg}")
                    return result

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning(f"⚠️  Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2**attempt)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
                logger.warning(f"⚠️  Connection error on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2**attempt)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2**attempt)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue

        logger.error(f"❌ All {max_retries} retry attempts failed. Last error: {last_error}")
        return {
            "error": f"Backtest failed after {max_retries} retries: {last_error}",
            "success": False,
        }

    def get_strategies_cached(self) -> Dict[str, Any]:
        """Get list of strategies with caching (5 minute TTL by default)."""
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
        """Fetch strategies from local strategies directory."""
        try:
            return {
                "strategies": [],
                "message": "Local strategies loaded from filesystem. Use Jesse UI to manage strategies.",
            }
        except Exception as e:
            logger.error(f"❌ Failed to get strategies: {e}")
            return {"error": str(e), "strategies": []}

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
        """Run optimization via Jesse REST API."""
        try:
            logger.info(f"Starting optimization via REST API: {strategy}")

            payload = optimization.build_optimization_payload(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                param_space=param_space,
                exchange=exchange,
                starting_balance=starting_balance,
                fee=fee,
                leverage=leverage,
                exchange_type=exchange_type,
            )

            result = optimization.rate_limited_optimization(self.session, self.base_url, payload)

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
        """Run Monte Carlo simulation via REST API."""
        try:
            logger.info("Starting Monte Carlo simulation via REST API")

            payload = optimization.build_monte_carlo_payload(
                backtest_result=backtest_result,
                simulations=simulations,
                block_size=block_size,
                confidence_levels=confidence_levels,
            )

            result = optimization.rate_limited_monte_carlo(self.session, self.base_url, payload)

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
        """Import candle data from exchange via Jesse REST API."""
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
        """Cancel a running candle import."""
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
        """Get list of existing candles with date ranges."""
        return candles.get_existing_candles(self.session, self.base_url, exchange, symbol)

    def get_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get candle data for a specific exchange/symbol/timeframe."""
        return candles.get_candles(
            self.session,
            self.base_url,
            exchange,
            symbol,
            timeframe,
            start_date,
            end_date,
        )

    def delete_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete candle data for a specific exchange/symbol."""
        return candles.delete_candles(self.session, self.base_url, exchange, symbol, timeframe)

    def clear_candles_cache(self) -> Dict[str, Any]:
        """Clear the candles database cache."""
        return candles.clear_candles_cache(self.session, self.base_url)

    def get_supported_symbols(self, exchange: str) -> Dict[str, Any]:
        """Get list of supported symbols for an exchange."""
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
        """Get list of supported exchanges."""
        return config.list_supported_exchanges()

    @staticmethod
    def get_exchange_config(exchange: str) -> Dict[str, Any]:
        """Get configuration for a specific exchange."""
        return config.get_exchange_config(exchange)

    @staticmethod
    def validate_symbol(exchange: str, symbol: str) -> Dict[str, Any]:
        """Validate a trading symbol format for a specific exchange."""
        return config.validate_symbol(exchange, symbol)

    @staticmethod
    def validate_timeframe(exchange: str, timeframe: str) -> Dict[str, Any]:
        """Validate a timeframe for a specific exchange."""
        return config.validate_timeframe(exchange, timeframe)

    def get_backtest_sessions(self) -> Dict[str, Any]:
        """Get list of backtest sessions."""
        try:
            payload = {"limit": 50, "offset": 0}
            response = self.session.post(f"{self.base_url}/backtest/sessions", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get backtest sessions: {e}")
            return {"error": str(e), "sessions": []}

    def get_optimization_sessions(self) -> Dict[str, Any]:
        """Get list of optimization sessions."""
        try:
            payload = {"limit": 50, "offset": 0}
            response = self.session.post(f"{self.base_url}/optimization/sessions", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get optimization sessions: {e}")
            return {"error": str(e), "sessions": []}

    def check_live_plugin_available(self) -> Dict[str, Any]:
        """Check if jesse-live plugin is installed and available."""
        return live.check_live_plugin_available(self.session, self.base_url)

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
        """Start a live or paper trading session."""
        return live.start_live_session(
            self.session,
            self.base_url,
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=paper_mode,
            debug_mode=debug_mode,
            config=config,
            routes=routes,
            data_routes=data_routes,
        )

    def cancel_live_session(self, session_id: str, paper_mode: bool = True) -> Dict[str, Any]:
        """Cancel a running live trading session."""
        return live.cancel_live_session(self.session, self.base_url, session_id, paper_mode)

    def get_live_sessions(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get list of live trading sessions."""
        return live.get_live_sessions(self.session, self.base_url, limit, offset)

    def get_live_session(self, session_id: str) -> Dict[str, Any]:
        """Get a specific live session by ID."""
        return live.get_live_session(self.session, self.base_url, session_id)

    def get_live_logs(
        self,
        session_id: str,
        log_type: str = "all",
        start_time: int = 0,
    ) -> Dict[str, Any]:
        """Get logs for a live trading session."""
        return live.get_live_logs(self.session, self.base_url, session_id, log_type, start_time)

    def get_live_orders(self, session_id: str) -> Dict[str, Any]:
        """Get orders for a live trading session."""
        return live.get_live_orders(self.session, self.base_url, session_id)

    def get_closed_trades(
        self,
        session_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get closed/completed trades for a live trading session."""
        return live.get_closed_trades(self.session, self.base_url, session_id, limit)

    def get_live_equity_curve(
        self,
        session_id: str,
        from_ms: Optional[int] = None,
        to_ms: Optional[int] = None,
        timeframe: str = "auto",
        max_points: int = 1000,
    ) -> Dict[str, Any]:
        """Get equity curve for a live trading session."""
        return live.get_live_equity_curve(
            self.session,
            self.base_url,
            session_id,
            from_ms,
            to_ms,
            timeframe,
            max_points,
        )

    def update_live_session_notes(self, session_id: str, notes: str) -> Dict[str, Any]:
        """Update notes for a live trading session."""
        return live.update_live_session_notes(self.session, self.base_url, session_id, notes)

    def purge_live_sessions(self, days_old: Optional[int] = None) -> Dict[str, Any]:
        """Purge old live trading sessions from database."""
        return live.purge_live_sessions(self.session, self.base_url, days_old)


_client = None


def get_jesse_rest_client() -> JesseRESTClient:
    """Get or create the global Jesse REST client"""
    global _client
    if _client is None:
        _client = JesseRESTClient()
    return _client
