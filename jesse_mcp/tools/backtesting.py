"""
Phase 1: Backtesting Tools

Provides core backtesting functionality for the Jesse MCP server:
- Strategy execution and testing
- Exchange validation
- Strategy management (list, read, validate)
- Candle data import
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("jesse-mcp.backtesting")

# Global references (injected from server.py)
jesse: Optional[Any] = None


def register_backtesting_tools(mcp, jesse_instance):
    """Register backtesting tools with the MCP server"""
    global jesse
    jesse = jesse_instance

    @mcp.tool(name="backtesting:status")
    def jesse_status() -> Dict[str, Any]:
        """
        Check Jesse REST API health and connection status.

        Returns connection status, Jesse version, and available strategies count.
        Use this to verify Jesse is reachable before running backtests or optimizations.
        """
        try:
            from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

            client = get_jesse_rest_client()
            return client.health_check()
        except Exception as e:
            logger.error(f"Jesse status check failed: {e}")
            return {
                "connected": False,
                "jesse_url": None,
                "jesse_version": None,
                "strategies_count": None,
                "error": str(e),
            }

    @mcp.tool(name="backtesting:exchanges")
    def get_exchanges() -> Dict[str, Any]:
        """
        Get list of supported exchanges in Jesse.

        Returns a list of exchange names that Jesse supports for trading and backtesting.
        Use this to validate exchange names before creating trading workflows or backtests.

        Returns:
            Dict with 'exchanges' list of supported exchange names and 'exchange_configs' with details
        """
        try:
            from jesse_mcp.core.rest.config import list_supported_exchanges, EXCHANGE_CONFIG

            exchanges = list_supported_exchanges()

            # Build detailed exchange info including spot/futures support
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
        except Exception as e:
            logger.error(f"Failed to get exchanges: {e}")
            return {"error": str(e), "exchanges": []}

    @mcp.tool(name="backtesting:run")
    def backtest(
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
        Run a single backtest on a strategy with specified parameters.

        Returns metrics: total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, etc.

        Use this to:
        - Test a single strategy version
        - Get baseline metrics for comparison
        - As first step before analyze_results, monte_carlo, or risk_report
        - For A/B testing: run backtest twice with different parameters/strategies

        Example flow for A/B testing:
        1. backtest(strategy="EMA_original", ...)
        2. backtest(strategy="EMA_with_filter", ...)
        3. analyze_results() on both to compare
        """
        try:
            from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

            client = get_jesse_rest_client()
            if client is None:
                raise RuntimeError("Jesse REST client not available")

            routes = [{"strategy": strategy, "symbol": symbol, "timeframe": timeframe}]
            result = client.backtest(
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
            )

            # Check if result contains an error (validation or execution failure)
            if result.get("error") or not result.get("success", True):
                logger.warning(
                    f"Backtest failed, attempting fallback to mock: {result.get('error', 'Unknown error')}"
                )
                # Try mock fallback
                from jesse_mcp.core.mock import get_mock_jesse_wrapper

                mock_wrapper = get_mock_jesse_wrapper()
                mock_result = mock_wrapper.backtest(
                    strategy_name=strategy,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    starting_balance=starting_balance,
                )
                mock_result["_mock_data"] = True
                mock_result["_fallback_reason"] = result.get("error", "Unknown error")
                logger.info(f"✅ Using mock backtest data for {strategy}")
                return mock_result

            return result
        except Exception as e:
            logger.warning(f"Backtest failed with exception: {e}, attempting fallback to mock")
            try:
                # Fallback to mock implementation
                from jesse_mcp.core.mock import get_mock_jesse_wrapper

                mock_wrapper = get_mock_jesse_wrapper()
                mock_result = mock_wrapper.backtest(
                    strategy_name=strategy,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    starting_balance=starting_balance,
                )
                mock_result["_mock_data"] = True
                mock_result["_fallback_reason"] = str(e)
                logger.info(f"✅ Using mock backtest data for {strategy} (fallback)")
                return mock_result
            except Exception as mock_error:
                logger.error(f"Both real and mock backtest failed: {mock_error}")
                return {
                    "error": f"Backtest failed: {str(e)}, Mock fallback also failed: {str(mock_error)}",
                    "error_type": type(e).__name__,
                }

    @mcp.tool(name="backtesting:list-strategies")
    def strategy_list(include_test_strategies: bool = False) -> Dict[str, Any]:
        """
        List all available trading strategies.

        Use this as the FIRST step to see what strategies are available to test.
        Returns list of strategy names that can be passed to backtest(), analyze_results(), etc.
        """
        try:
            if jesse is None:
                raise RuntimeError("Jesse framework not initialized")
            return jesse.list_strategies(include_test_strategies)
        except Exception as e:
            logger.error(f"Strategy list failed: {e}")
            return {"error": str(e), "strategies": []}

    @mcp.tool(name="backtesting:read-strategy")
    def strategy_read(name: str) -> Dict[str, Any]:
        """Read strategy source code"""
        try:
            if jesse is None:
                raise RuntimeError("Jesse framework not initialized")
            return jesse.read_strategy(name)
        except Exception as e:
            logger.error(f"Strategy read failed: {e}")
            return {"error": str(e), "name": name}

    @mcp.tool(name="backtesting:validate-strategy")
    def strategy_validate(code: str) -> Dict[str, Any]:
        """Validate strategy code without saving"""
        try:
            if jesse is None:
                raise RuntimeError("Jesse framework not initialized")
            return jesse.validate_strategy(code)
        except Exception as e:
            logger.error(f"Strategy validation failed: {e}")
            return {"error": str(e), "valid": False}

    @mcp.tool(name="backtesting:import-candles")
    def candles_import(
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download candle data from exchange via Jesse REST API"""
        try:
            from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

            client = get_jesse_rest_client()
            return client.import_candles(
                exchange=exchange,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            logger.error(f"Candles import failed: {e}")
            return {"error": str(e), "success": False}
