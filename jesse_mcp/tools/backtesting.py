"""
Phase 1: Backtesting Tools

Core backtesting functionality:
- Strategy execution and testing
- Exchange validation
- Strategy management (list, read, validate)
- Candle data import
- Performance benchmarking
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from jesse_mcp.tools._utils import (
    async_call,
    get_client,
    require_jesse,
    tool_error_handler,
)

logger = logging.getLogger("jesse-mcp.backtesting")


def register_backtesting_tools(mcp):
    """Register backtesting tools with the MCP server"""

    @mcp.tool
    @tool_error_handler
    def jesse_status() -> Dict[str, Any]:
        """
        Check Jesse REST API health and connection status.

        Returns connection status, Jesse version, and available strategies count.
        Use this to verify Jesse is reachable before running backtests or optimizations.
        """
        return get_client().health_check()

    @mcp.tool
    @tool_error_handler
    def get_exchanges() -> Dict[str, Any]:
        """
        Get list of supported exchanges in Jesse.

        Returns a list of exchange names that Jesse supports for trading and backtesting.
        Use this to validate exchange names before creating trading workflows or backtests.

        Returns:
            Dict with 'exchanges' list of supported exchange names and 'exchange_configs' with details
        """
        from jesse_mcp.core.rest.config import EXCHANGE_CONFIG, list_supported_exchanges

        exchanges = list_supported_exchanges()

        exchange_details = []
        for exchange in exchanges:
            config = EXCHANGE_CONFIG.get(exchange, {})
            exchange_details.append(
                {
                    "name": exchange,
                    "supports_spot": config.get("supports_spot", False),
                    "supports_futures": config.get("supports_futures", False),
                    "symbol_format": config.get("symbol_format", "UNKNOWN"),
                    "timeframes": config.get("timeframes", []),
                }
            )

        return {
            "exchanges": sorted(exchanges),
            "exchange_details": exchange_details,
            "count": len(exchanges),
        }

    @mcp.tool
    @tool_error_handler
    async def backtest(
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
        fast_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a single backtest on a strategy with specified parameters.

        Returns metrics: total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, etc.

        Use this to:
        - Test a single strategy version
        - Get baseline metrics for comparison
        - As first step before analyze_results, monte_carlo, or risk_report
        - For A/B testing: run backtest twice with different parameters/strategies

        Args:
            fast_mode: Enable fast mode for orders-of-magnitude speedup (default: True)
        """
        client = get_client()
        if client is None:
            raise RuntimeError("Jesse REST client not available")

        routes = [{"strategy": strategy, "symbol": symbol, "timeframe": timeframe}]
        result = await async_call(
            client.backtest,
            routes=routes,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            hyperparameters=hyperparameters,
            include_trades=include_trades,
            include_equity_curve=include_equity_curve,
            include_logs=include_logs,
            auto_import_candles=True,
            fast_mode=fast_mode,
        )

        if result.get("error") or not result.get("success", True):
            logger.error(f"Backtest failed: {result.get('error', 'Unknown error')}")
            return {
                "error": result.get("error", "Backtest failed"),
                "error_type": result.get("error_type", "BacktestError"),
                "success": False,
            }

        return result

    @mcp.tool
    @tool_error_handler
    async def backtest_cancel(
        backtest_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel a running backtest.

        Use this to stop a runaway or stuck backtest. If no backtest_id is provided,
        cancels the currently running backtest.

        Args:
            backtest_id: Optional specific backtest session ID to cancel
        """
        return await async_call(get_client().cancel_backtest, backtest_id)

    @mcp.tool
    @tool_error_handler
    async def active_workers() -> Dict[str, Any]:
        """
        Get list of active workers (running backtests, optimizations, Monte Carlo simulations).

        Use this to check what's currently running before starting new jobs,
        or to find session IDs for cancellation.
        """
        return await async_call(get_client().get_active_workers)

    @mcp.tool
    @tool_error_handler
    def strategy_list(include_test_strategies: bool = False) -> Dict[str, Any]:
        """
        List all available trading strategies.

        Use this as the FIRST step to see what strategies are available to test.
        Returns list of strategy names that can be passed to backtest(), analyze_results(), etc.
        """
        return require_jesse().list_strategies(include_test_strategies)

    @mcp.tool
    @tool_error_handler
    def strategy_read(name: str) -> Dict[str, Any]:
        """Read strategy source code"""
        return require_jesse().read_strategy(name)

    @mcp.tool
    @tool_error_handler
    def strategy_validate(code: str) -> Dict[str, Any]:
        """Validate strategy code without saving"""
        return require_jesse().validate_strategy(code)

    @mcp.tool
    @tool_error_handler
    async def candles_import(
        exchange: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download candle data from exchange via Jesse REST API"""
        return await async_call(
            get_client().import_candles,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )

    @mcp.tool
    @tool_error_handler
    async def backtest_benchmark(
        symbol: str = "BTC-USDT",
        timeframe: str = "1h",
        days: int = 30,
        exchange: str = "Binance Spot",
    ) -> Dict[str, Any]:
        """
        Run a benchmark backtest to measure performance metrics.

        Measures backtest execution time and calculates candles/second performance.
        Useful for understanding how long different backtests will take.

        Args:
            symbol: Trading symbol (default: BTC-USDT)
            timeframe: Candle timeframe (default: 1h)
            days: Number of days to backtest (default: 30)
            exchange: Exchange name (default: Binance Spot)

        Returns:
            Dict with benchmark results including execution time and candles/second
        """
        import time
        from datetime import datetime

        client = get_client()
        if client is None:
            raise RuntimeError("Jesse REST client not available")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        timeframe_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }
        minutes = timeframe_minutes.get(timeframe, 60)
        warmup_candles = 240
        trading_candles = (days * 24 * 60) // minutes
        total_candles = trading_candles + warmup_candles

        start_time = time.time()
        routes = [
            {"strategy": "SMACrossover", "symbol": symbol, "timeframe": timeframe}
        ]
        result = await async_call(
            client.backtest,
            routes=routes,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            exchange=exchange,
            exchange_type="spot" if "Spot" in exchange else "futures",
        )
        end_time = time.time()

        execution_time = end_time - start_time

        if execution_time > 0:
            candles_per_second = total_candles / execution_time
            candles_per_minute = candles_per_second * 60
        else:
            candles_per_second = 0
            candles_per_minute = 0

        status = result.get("status", "unknown")
        is_mock = result.get("_mock_data", True)

        return {
            "benchmark_config": {
                "symbol": symbol,
                "timeframe": timeframe,
                "days": days,
                "exchange": exchange,
            },
            "performance": {
                "execution_time_seconds": round(execution_time, 3),
                "total_candles": total_candles,
                "trading_candles": trading_candles,
                "warmup_candles": warmup_candles,
                "candles_per_second": round(candles_per_second, 1),
                "candles_per_minute": round(candles_per_minute, 1),
            },
            "backtest_status": status,
            "mock_data_used": is_mock,
            "estimates": {
                "1_month_1h": f"~{round(960 / candles_per_second, 2)}s",
                "3_months_1h": f"~{round(2400 / candles_per_second, 2)}s",
                "1_year_1h": f"~{round(8880 / candles_per_second, 2)}s",
                "1_month_5m": f"~{round(8880 / candles_per_second, 2)}s",
                "1_month_1m": f"~{round(43440 / candles_per_second, 2)}s",
            },
        }
