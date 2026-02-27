"""
Jesse Integration Layer

Provides a clean abstraction over Jesse's research module and related functionality.
Handles all interactions with Jesse to enable autonomous trading strategy operations.
"""

import sys
import os
import re
import shutil
import logging
from typing import Dict, Any, Optional
import traceback

logger = logging.getLogger("jesse-mcp.integration")

# Jesse paths - try multiple locations
JESSE_PATHS = [
    "/home/bk/source/jesse-bot",
    "/srv/containers/jesse",
    "/mnt/nfs/server1/containers/jesse",
]

# Find Jesse installation
JESSE_PATH = None
for path in JESSE_PATHS:
    if os.path.exists(path):
        JESSE_PATH = path
        logger.info(f"Found Jesse at: {JESSE_PATH}")
        break

if JESSE_PATH:
    sys.path.insert(0, JESSE_PATH)


def _check_jesse_ntfy_available() -> bool:
    """Check if jesse-ntfy API is available as fallback"""
    try:
        import requests

        response = requests.get("http://localhost:5033/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# Check if Jesse API is accessible
# This allows jesse-mcp to work without importing Jesse dependencies
JESSE_AVAILABLE = False
JESSE_ERROR = None
JESSE_API_URL = os.getenv("JESSE_URL", "http://server2:9100")
JESSE_RESEARCH_AVAILABLE = False  # Track if we can import Jesse's research module

try:
    import requests

    response = requests.get(f"{JESSE_API_URL}/", timeout=2)
    if response.status_code == 200:
        JESSE_AVAILABLE = True
        logger.info(f"✅ Jesse API found at {JESSE_API_URL}")
except Exception as e:
    JESSE_ERROR = str(e)
    logger.warning(f"⚠️ Jesse API not accessible at {JESSE_API_URL}: {e}")

# Try to import Jesse's research module (only available with local installation)
if JESSE_PATH:
    try:
        # This will fail if Jesse dependencies are not installed
        import jesse.helpers as jh
        from jesse import research

        JESSE_RESEARCH_AVAILABLE = True
        logger.info("✅ Jesse research module available for local operations")
    except ImportError as e:
        JESSE_RESEARCH_AVAILABLE = False
        logger.warning(f"⚠️ Jesse research module not available: {e}")


class JesseIntegrationError(Exception):
    """Raised when Jesse integration fails"""

    pass


class JesseWrapper:
    """
    Wrapper around Jesse for MCP operations

    Provides clean abstractions for:
    - Running backtests
    - Managing strategies
    - Downloading candle data
    - Analyzing results
    """

    def __init__(self):
        if not JESSE_AVAILABLE:
            raise JesseIntegrationError("Jesse framework not available")

        self.jesse_path = JESSE_PATH
        # Only set strategies_path if jesse_path is available (local installation)
        # When using REST API, this path may not be needed
        if JESSE_PATH:
            self.strategies_path = os.path.join(JESSE_PATH, "strategies")
        else:
            self.strategies_path = None
        logger.info(
            f"Initialized JesseWrapper (path: {self.jesse_path}, REST API: {JESSE_AVAILABLE})"
        )

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
        Run a backtest using Jesse's research module

        Args:
            strategy: Strategy name (must exist in strategies directory)
            symbol: Trading symbol (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h", "1D")
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"
            exchange: Exchange name (default: Binance)
            starting_balance: Initial capital (default: 10000)
            fee: Trading fee as decimal (default: 0.001 = 0.1%)
            leverage: Leverage for futures (default: 1)
            exchange_type: 'spot' or 'futures' (default: futures)
            hyperparameters: Dict of strategy hyperparameter overrides
            include_trades: Include individual trades in response
            include_equity_curve: Include equity curve data
            include_logs: Include strategy logs

        Returns:
            Dict with backtest results and metrics
        """
        try:
            logger.info(f"Starting backtest: {strategy} on {symbol} ({timeframe})")

            # Check if we have access to Jesse's research module (requires local installation)
            if not JESSE_RESEARCH_AVAILABLE:
                return {
                    "error": "Backtest requires local Jesse research module",
                    "detail": "This tool requires Jesse.research module which needs full Jesse installation. Use the Jesse REST API /backtest endpoint instead.",
                    "success": False,
                }

            # Format config for Jesse
            config = {
                "starting_balance": starting_balance,
                "fee": fee,
                "type": exchange_type,
                "futures_leverage": leverage,
                "futures_leverage_mode": "cross",
                "exchange": exchange,
                "warm_up_candles": 240,
            }

            # Format routes
            routes = [
                {
                    "exchange": exchange,
                    "strategy": strategy,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

            # Get candles from database
            logger.info(f"Fetching candles: {symbol} from {start_date} to {end_date}")
            start_ts = jh.arrow_to_timestamp(start_date)
            end_ts = jh.arrow_to_timestamp(end_date)

            candles, warmup = research.get_candles(
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                start_date_timestamp=start_ts,
                finish_date_timestamp=end_ts,
                warmup_candles_num=240,
            )

            if candles is None or len(candles) == 0:
                raise JesseIntegrationError(f"No candle data available for {symbol}")

            logger.info(f"Got {len(candles)} candles (warmup: {len(warmup)})")

            # Run backtest
            result = research.backtest(
                config=config,
                routes=routes,
                data_routes=[],
                candles={
                    "Binance-" + symbol: {
                        "exchange": exchange,
                        "symbol": symbol,
                        "candles": candles,
                    }
                },
                generate_equity_curve=include_equity_curve,
                generate_trades=include_trades,
                generate_logs=include_logs,
                hyperparameters=hyperparameters,
                fast_mode=True,
            )

            logger.info(
                f"✅ Backtest complete: {result.get('metrics', {}).get('total_trades', 0)} trades"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e), "error_type": type(e).__name__, "success": False}

    def list_strategies(self, include_test_strategies: bool = False) -> Dict[str, Any]:
        """
        List all available strategies

        Args:
            include_test_strategies: Whether to include test strategies (unused, for compatibility)

        Returns:
            Dict with list of strategies and their metadata
        """
        try:
            logger.info("Listing available strategies")
            strategies = []

            if not self.strategies_path or not os.path.exists(self.strategies_path):
                logger.warning(f"Strategies path not available (using REST API)")
                return {"strategies": [], "count": 0}

            for item in os.listdir(self.strategies_path):
                item_path = os.path.join(self.strategies_path, item)
                if os.path.isdir(item_path) and not item.startswith("_"):
                    init_file = os.path.join(item_path, "__init__.py")
                    if os.path.exists(init_file):
                        strategies.append({"name": item, "path": item_path, "init_file": init_file})

            logger.info(f"Found {len(strategies)} strategies")
            return {
                "strategies": sorted(strategies, key=lambda x: x["name"]),
                "count": len(strategies),
            }

        except Exception as e:
            logger.error(f"❌ Failed to list strategies: {e}")
            return {"error": str(e), "strategies": []}

    def read_strategy(self, name: str) -> Dict[str, Any]:
        """
        Read strategy source code

        Args:
            name: Strategy name

        Returns:
            Dict with strategy code and metadata
        """
        try:
            logger.info(f"Reading strategy: {name}")

            if not self.strategies_path:
                raise JesseIntegrationError(f"Strategy path not available (using REST API)")

            strategy_path = os.path.join(self.strategies_path, name, "__init__.py")

            if not os.path.exists(strategy_path):
                raise JesseIntegrationError(f"Strategy not found: {name}")

            with open(strategy_path, "r") as f:
                code = f.read()

            logger.info(f"✅ Read strategy {name} ({len(code)} bytes)")

            return {
                "name": name,
                "code": code,
                "path": strategy_path,
                "size_bytes": len(code),
            }

        except Exception as e:
            logger.error(f"❌ Failed to read strategy {name}: {e}")
            return {"error": str(e), "name": name}

    def validate_strategy(self, code: str) -> Dict[str, Any]:
        """
        Validate strategy code without saving

        Args:
            code: Python code to validate

        Returns:
            Dict with validation results
        """
        try:
            logger.info("Validating strategy code")

            # Try to compile the code
            try:
                compile(code, "<string>", "exec")
                syntax_valid = True
                syntax_error = None
            except SyntaxError as e:
                syntax_valid = False
                syntax_error = str(e)

            # Check for required methods
            required_methods = ["should_long", "go_long", "should_short", "go_short"]
            missing_methods = [m for m in required_methods if f"def {m}(" not in code]

            # Check imports
            imports_valid = "from jesse.strategies import Strategy" in code

            result = {
                "valid": syntax_valid and imports_valid and len(missing_methods) == 0,
                "syntax_valid": syntax_valid,
                "syntax_error": syntax_error,
                "imports_valid": imports_valid,
                "has_required_methods": len(missing_methods) == 0,
                "missing_methods": missing_methods,
                "has_hyperparameters": "def hyperparameters(" in code,
            }

            logger.info(f"Strategy validation: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
            return result

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return {"error": str(e), "valid": False}

    def _sanitize_strategy_name(self, name: str) -> tuple[bool, str]:
        if not name:
            return False, "Strategy name cannot be empty"
        if len(name) > 50:
            return False, "Strategy name must be 50 characters or less"
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
            return (
                False,
                "Strategy name must start with a letter and contain only alphanumeric characters and underscores",
            )
        return True, name

    def save_strategy(self, name: str, code: str, overwrite: bool = False) -> Dict[str, Any]:
        try:
            logger.info(f"Saving strategy: {name}")

            if not self.strategies_path:
                return {"success": False, "error": "Strategy path not available (using REST API)"}

            valid, sanitized = self._sanitize_strategy_name(name)
            if not valid:
                return {"success": False, "error": sanitized}

            strategy_dir = os.path.join(self.strategies_path, sanitized)
            strategy_file = os.path.join(strategy_dir, "__init__.py")

            real_strategies_path = os.path.realpath(self.strategies_path)
            real_strategy_dir = os.path.realpath(strategy_dir)
            if (
                not real_strategy_dir.startswith(real_strategies_path + os.sep)
                and real_strategy_dir != real_strategies_path
            ):
                return {"success": False, "error": "Invalid strategy path: path traversal detected"}

            if os.path.exists(strategy_file) and not overwrite:
                return {
                    "success": False,
                    "error": f"Strategy '{sanitized}' already exists. Use overwrite=True to replace.",
                }

            os.makedirs(strategy_dir, exist_ok=True)

            with open(strategy_file, "w") as f:
                f.write(code)

            logger.info(f"✅ Saved strategy {sanitized} ({len(code)} bytes)")
            return {
                "success": True,
                "name": sanitized,
                "path": strategy_file,
                "size_bytes": len(code),
            }

        except Exception as e:
            logger.error(f"❌ Failed to save strategy {name}: {e}")
            return {"success": False, "error": str(e)}

    def delete_strategy(self, name: str) -> Dict[str, Any]:
        try:
            logger.info(f"Deleting strategy: {name}")

            if not self.strategies_path:
                return {"success": False, "error": "Strategy path not available (using REST API)"}

            valid, sanitized = self._sanitize_strategy_name(name)
            if not valid:
                return {"success": False, "error": sanitized}

            strategy_dir = os.path.join(self.strategies_path, sanitized)

            real_strategies_path = os.path.realpath(self.strategies_path)
            real_strategy_dir = os.path.realpath(strategy_dir)
            if (
                not real_strategy_dir.startswith(real_strategies_path + os.sep)
                and real_strategy_dir != real_strategies_path
            ):
                return {"success": False, "error": "Invalid strategy path: path traversal detected"}

            if not os.path.exists(strategy_dir):
                return {"success": False, "error": f"Strategy '{sanitized}' does not exist"}

            shutil.rmtree(strategy_dir)

            logger.info(f"✅ Deleted strategy {sanitized}")
            return {"success": True, "name": sanitized}

        except Exception as e:
            logger.error(f"❌ Failed to delete strategy {name}: {e}")
            return {"success": False, "error": str(e)}

    def strategy_exists(self, name: str) -> bool:
        try:
            if not self.strategies_path:
                return False

            valid, sanitized = self._sanitize_strategy_name(name)
            if not valid:
                return False

            strategy_file = os.path.join(self.strategies_path, sanitized, "__init__.py")

            real_strategies_path = os.path.realpath(self.strategies_path)
            real_strategy_file = os.path.realpath(strategy_file)
            if not real_strategy_file.startswith(real_strategies_path + os.sep):
                return False

            return os.path.exists(strategy_file)

        except Exception:
            return False

    def import_candles(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Import candle data from exchange

        Args:
            exchange: Exchange name (e.g., "Binance")
            symbol: Trading symbol (e.g., "BTC-USDT")
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD" (default: today)

        Returns:
            Dict with import results
        """
        try:
            logger.info(f"Importing candles: {exchange} {symbol} from {start_date}")

            # Check if we have access to Jesse's research module (requires local installation)
            if not JESSE_RESEARCH_AVAILABLE:
                return {
                    "error": "Import candles requires local Jesse research module",
                    "detail": "This tool requires Jesse.research module which needs full Jesse installation. Use the Jesse REST API /exchange/import-candles endpoint instead.",
                    "success": False,
                }

            result = research.import_candles(
                exchange=exchange,
                symbol=symbol,
                start_date=start_date,
                show_progressbar=False,
            )

            logger.info(f"✅ Import complete: {result}")
            return {
                "success": True,
                "exchange": exchange,
                "symbol": symbol,
                "start_date": start_date,
                "result_message": str(result),
            }

        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "exchange": exchange,
                "symbol": symbol,
            }

    def get_candles_available(
        self, exchange: Optional[str] = None, symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get information about available candle data

        Args:
            exchange: Filter by exchange (optional)
            symbol: Filter by symbol (optional)

        Returns:
            Dict with available date ranges
        """
        try:
            logger.info(f"Getting available candles (exchange={exchange}, symbol={symbol})")

            # This would query the database for available data
            # For now, return a placeholder that indicates this needs database access
            return {
                "status": "requires_database_query",
                "note": "Need to implement database queries for available candle ranges",
            }

        except Exception as e:
            logger.error(f"❌ Failed to get available candles: {e}")
            return {"error": str(e)}


def get_jesse_wrapper() -> JesseWrapper:
    """
    Factory function to get JesseWrapper instance

    Returns:
        JesseWrapper instance

    Raises:
        JesseIntegrationError if Jesse is not available
    """
    if not JESSE_AVAILABLE:
        raise JesseIntegrationError("Jesse framework not available")

    return JesseWrapper()
