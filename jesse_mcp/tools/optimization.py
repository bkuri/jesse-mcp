"""
Phase 3: Optimization Tools

Provides optimization and analysis functionality for the Jesse MCP server:
- Strategy hyperparameter optimization via Bayesian search
- Walk-forward analysis for overfitting detection
- Batch backtesting for multi-symbol comparison
- Deep result analysis and trade metrics
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np

from jesse_mcp.tools._utils import (
    async_call,
    get_client,
    require_optimizer,
    tool_error_handler,
)

logger = logging.getLogger("jesse-mcp.optimization")


def register_optimization_tools(mcp):
    """Register optimization tools with the MCP server."""

    @mcp.tool
    @tool_error_handler
    async def optimize(
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        param_space: Dict[str, Any],
        metric: str = "total_return",
        n_trials: int = 100,
        n_jobs: int = 1,
        exchange: str = "Binance Spot",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "spot",
    ) -> Dict[str, Any]:
        """
        Auto-optimize strategy hyperparameters using Bayesian optimization.

        Automatically tests many parameter combinations to find best metrics.

        Example: Improve Sharpe ratio by optimizing EMA periods
        - param_space: {"ema_fast": [5, 30], "ema_slow": [20, 100]}
        - metric: "sharpe_ratio"

        Returns best parameters found and their performance metrics.
        """
        client = get_client()
        result = client.optimization(
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
        return result

    @mcp.tool
    @tool_error_handler
    async def optimization_cancel(
        optimization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel a running optimization.

        Use this to stop a long-running or stuck optimization session.

        Args:
            optimization_id: Optional specific optimization session ID to cancel
        """
        client = get_client()
        result = await async_call(client.cancel_optimization, optimization_id)
        return result

    @mcp.tool
    @tool_error_handler
    async def monte_carlo_cancel(
        monte_carlo_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel a running Monte Carlo simulation.

        Use this to stop a long-running or stuck Monte Carlo session.

        Args:
            monte_carlo_id: Optional specific Monte Carlo session ID to cancel
        """
        client = get_client()
        result = await async_call(client.cancel_monte_carlo, monte_carlo_id)
        return result

    @mcp.tool
    @tool_error_handler
    async def walk_forward(
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        in_sample_period: int = 365,
        out_sample_period: int = 30,
        step_forward: int = 7,
        param_space: Optional[Dict[str, Any]] = None,
        metric: str = "total_return",
    ) -> Dict[str, Any]:
        """Perform walk-forward analysis to detect overfitting"""
        optimizer = require_optimizer()
        result = await optimizer.walk_forward(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            in_sample_period=in_sample_period,
            out_sample_period=out_sample_period,
            step_forward=step_forward,
            param_space=param_space or {},
            metric=metric,
        )
        return result

    @mcp.tool
    @tool_error_handler
    async def backtest_batch(
        strategy: str,
        symbols: List[str],
        timeframes: List[str],
        start_date: str,
        end_date: str,
        exchange: str = "Binance Spot",
        starting_balance: float = 10000,
        hyperparameters: Optional[List[Dict[str, Any]]] = None,
        concurrent_limit: int = 4,
    ) -> Dict[str, Any]:
        """Run multiple backtests concurrently for strategy comparison"""
        client = get_client()

        start_time = time.time()

        if hyperparameters is None:
            hyperparameters = [{}]

        task_info: List[Dict[str, Any]] = []
        for symbol in symbols:
            for timeframe in timeframes:
                for i, params in enumerate(hyperparameters):
                    task_info.append(
                        {
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "params_index": i,
                            "params": params,
                        }
                    )

        semaphore = asyncio.Semaphore(concurrent_limit)

        async def run_single_backtest(info: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    routes = [
                        {
                            "strategy": strategy,
                            "symbol": info["symbol"],
                            "timeframe": info["timeframe"],
                        }
                    ]
                    result = await async_call(
                        client.backtest,
                        routes=routes,
                        start_date=start_date,
                        end_date=end_date,
                        exchange=exchange,
                        starting_balance=starting_balance,
                        hyperparameters=info["params"],
                        auto_import_candles=True,
                        fast_mode=True,
                    )
                    return {
                        "info": info,
                        "result": result,
                        "success": not result.get("error"),
                        "error": result.get("error"),
                    }
                except Exception as e:
                    logger.error(
                        f"Batch backtest failed for {info['symbol']} {info['timeframe']}: {e}"
                    )
                    return {
                        "info": info,
                        "result": None,
                        "success": False,
                        "error": str(e),
                    }

        results = await asyncio.gather(
            *[run_single_backtest(info) for info in task_info]
        )

        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        comparison_matrix: Dict[str, List[Dict[str, Any]]] = {}
        for result in successful_results:
            key = f"{result['info']['symbol']}_{result['info']['timeframe']}"
            if key not in comparison_matrix:
                comparison_matrix[key] = []
            comparison_matrix[key].append(
                {
                    "params_index": result["info"]["params_index"],
                    "params": result["info"]["params"],
                    "result": result["result"],
                }
            )

        top_performers: List[Any] = []
        if successful_results:
            all_returns: List[float] = []
            all_sharpes: List[float] = []
            for r in successful_results:
                res = r.get("result") or {}
                tr = res.get("total_return")
                sr = res.get("sharpe_ratio")
                if tr is not None:
                    all_returns.append(float(tr))
                if sr is not None:
                    all_sharpes.append(float(sr))

            overall_stats: Dict[str, Any] = {
                "total_backtests": len(task_info),
                "successful_backtests": len(successful_results),
                "failed_backtests": len(failed_results),
                "success_rate": (
                    round(len(successful_results) / len(task_info), 4)
                    if task_info
                    else 0
                ),
            }
            if all_returns:
                overall_stats["best_return"] = round(max(all_returns), 4)
                overall_stats["worst_return"] = round(min(all_returns), 4)
                overall_stats["average_return"] = round(float(np.mean(all_returns)), 4)
            if all_sharpes:
                overall_stats["best_sharpe"] = round(max(all_sharpes), 4)
                overall_stats["average_sharpe"] = round(float(np.mean(all_sharpes)), 4)

            top_performers = sorted(
                successful_results,
                key=lambda x: (x.get("result") or {}).get(
                    "total_return", float("-inf")
                ),
                reverse=True,
            )[:5]
        else:
            overall_stats = {
                "total_backtests": len(task_info),
                "successful_backtests": 0,
                "failed_backtests": len(failed_results),
                "success_rate": 0,
            }

        execution_time = time.time() - start_time

        return {
            "strategy": strategy,
            "symbols": symbols,
            "timeframes": timeframes,
            "start_date": start_date,
            "end_date": end_date,
            "concurrent_limit": concurrent_limit,
            "comparison_matrix": comparison_matrix,
            "successful_results": successful_results,
            "failed_results": failed_results,
            "overall_statistics": overall_stats,
            "top_performers": top_performers,
            "execution_time": round(execution_time, 2),
        }

    @mcp.tool
    @tool_error_handler
    async def analyze_results(
        backtest_result: Dict[str, Any],
        analysis_type: str = "basic",
        include_trade_analysis: bool = True,
        include_correlation: bool = False,
        include_monte_carlo: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract deep insights from backtest results.

        Takes backtest result dict and returns detailed analysis including:
        - Trade metrics (win rate, avg return, etc.)
        - Performance breakdown
        - Risk metrics summary

        Use this after backtest() to understand strategy performance better.
        Common workflow:
        1. backtest() -> get result
        2. analyze_results(result) -> understand what happened
        3. monte_carlo() -> validate with simulation
        4. risk_report() -> comprehensive assessment
        """
        optimizer = require_optimizer()
        result = optimizer.analyze_results(
            backtest_result=backtest_result,
            analysis_type=analysis_type,
            include_trade_analysis=include_trade_analysis,
            include_correlation=include_correlation,
            include_monte_carlo=include_monte_carlo,
        )
        return result
