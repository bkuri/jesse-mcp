"""
Jesse REST API Client

Provides a clean abstraction over Jesse's REST API (http://localhost:8000)
allowing full interactivity with Jesse without requiring local module imports.
"""

import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("jesse-mcp.rest-client")

# Get Jesse API configuration from environment
JESSE_URL = os.getenv("JESSE_URL", "http://localhost:8000")
JESSE_API_TOKEN = os.getenv("JESSE_API_TOKEN", "")
JESSE_API_BASE = JESSE_URL


class JesseRESTClient:
    """Client for interacting with Jesse via REST API"""

    def __init__(
        self, base_url: str = JESSE_API_BASE, api_token: str = JESSE_API_TOKEN
    ):
        self.base_url = base_url
        self.api_token = api_token
        self.session = requests.Session()

        # Set authorization header if token is provided
        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
            logger.info("✅ Authorization token configured")
        else:
            logger.warning("⚠️ No JESSE_API_TOKEN provided - requests may fail")

        self._verify_connection()

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

            # Format config as Jesse expects
            config = {
                "starting_balance": starting_balance,
                "fee": fee,
                "futures_leverage": leverage,
                "type": exchange_type,
                "warm_up_candles": 240,
            }

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

            response = self.session.post(f"{self.base_url}/backtest", json=payload)
            response.raise_for_status()

            logger.info(f"✅ Backtest completed for {strategy}")
            return response.json()

        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return {"error": str(e), "success": False}

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

            payload = {
                "strategy": strategy,
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "param_space": param_space,
                "exchange": exchange,
                "starting_balance": starting_balance,
                "fee": fee,
                "futures_leverage": leverage,
                "type": exchange_type,
            }

            response = self.session.post(f"{self.base_url}/optimization", json=payload)
            response.raise_for_status()

            logger.info(f"✅ Optimization started for {strategy}")
            return response.json()

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

            response = self.session.post(f"{self.base_url}/monte-carlo", json=payload)
            response.raise_for_status()

            logger.info("✅ Monte Carlo simulation completed")
            return response.json()

        except Exception as e:
            logger.error(f"❌ Monte Carlo failed: {e}")
            return {"error": str(e), "success": False}

    def import_candles(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Import candle data via REST API

        Args:
            exchange: Exchange name
            symbol: Trading symbol
            start_date: Start date
            end_date: End date (optional)

        Returns:
            Import results dict
        """
        try:
            logger.info(f"Importing candles via REST API: {exchange} {symbol}")

            payload = {
                "exchange": exchange,
                "symbol": symbol,
                "start_date": start_date,
            }

            if end_date:
                payload["end_date"] = end_date

            # This would be a candles import endpoint if Jesse API has one
            # For now, return a message directing to Jesse API
            return {
                "message": "Use Jesse REST API /exchange endpoint for candle imports",
                "endpoint": f"{self.base_url}/exchange",
                "success": False,
            }

        except Exception as e:
            logger.error(f"❌ Candles import failed: {e}")
            return {"error": str(e), "success": False}

    def get_backtest_sessions(self) -> Dict[str, Any]:
        """Get list of backtest sessions"""
        try:
            payload = {"limit": 50, "offset": 0}
            response = self.session.post(
                f"{self.base_url}/backtest/sessions", json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get backtest sessions: {e}")
            return {"error": str(e), "sessions": []}

    def get_optimization_sessions(self) -> Dict[str, Any]:
        """Get list of optimization sessions"""
        try:
            payload = {"limit": 50, "offset": 0}
            response = self.session.post(
                f"{self.base_url}/optimization/sessions", json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get optimization sessions: {e}")
            return {"error": str(e), "sessions": []}


# Global instance
_client = None


def get_jesse_rest_client() -> JesseRESTClient:
    """Get or create the global Jesse REST client"""
    global _client
    if _client is None:
        _client = JesseRESTClient()
    return _client
