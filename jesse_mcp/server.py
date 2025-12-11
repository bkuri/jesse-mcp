#!/usr/bin/env python3
"""
Jesse MCP Server - FastMCP Implementation

Provides 17 tools for quantitative trading analysis:
- Phase 1: Backtesting (4 tools)
- Phase 3: Optimization (4 tools) [formerly phase3]
- Phase 4: Risk Analysis (4 tools) [formerly phase4]
- Phase 5: Pairs Trading (5 tools) [formerly phase5]
"""

import asyncio
import logging
from typing import Optional

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jesse-mcp")

# ==================== LAZY INITIALIZATION ====================
# These will be initialized when main() is called, not at import time
# This allows the server module to be imported for testing without Jesse

jesse = None
optimizer = None
risk_analyzer = None
pairs_analyzer = None
_initialized = False


def _initialize_dependencies():
    """Initialize Jesse and analyzer modules - called from main()"""
    global jesse, optimizer, risk_analyzer, pairs_analyzer, _initialized

    if _initialized:
        return

    try:
        from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE

        if not JESSE_AVAILABLE:
            raise ImportError("Jesse framework not available")
        jesse = get_jesse_wrapper()
        logger.info("✅ Jesse framework initialized")
    except Exception as e:
        logger.critical(f"❌ Jesse initialization failed: {e}")
        raise SystemExit(1)

    try:
        from jesse_mcp.optimizer import get_optimizer

        optimizer = get_optimizer()
        logger.info("✅ Optimizer module loaded")
    except Exception as e:
        logger.critical(f"❌ Optimizer initialization failed: {e}")
        raise SystemExit(1)

    try:
        from jesse_mcp.risk_analyzer import get_risk_analyzer

        risk_analyzer = get_risk_analyzer()
        logger.info("✅ Risk analyzer module loaded")
    except Exception as e:
        logger.critical(f"❌ Risk analyzer initialization failed: {e}")
        raise SystemExit(1)

    try:
        from jesse_mcp.pairs_analyzer import get_pairs_analyzer

        pairs_analyzer = get_pairs_analyzer()
        logger.info("✅ Pairs analyzer module loaded")
    except Exception as e:
        logger.critical(f"❌ Pairs analyzer initialization failed: {e}")
        raise SystemExit(1)

    _initialized = True


# ==================== FASTMCP INITIALIZATION ====================

mcp = FastMCP("jesse-mcp", version="1.0.0")

# ==================== PHASE 1: BACKTESTING TOOLS ====================


@mcp.tool
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
    hyperparameters: Optional[dict] = None,
    include_trades: bool = False,
    include_equity_curve: bool = False,
    include_logs: bool = False,
) -> dict:
    """Run a single backtest with specified parameters"""
    try:
        result = jesse.backtest(
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
            include_trades=include_trades,
            include_equity_curve=include_equity_curve,
            include_logs=include_logs,
        )
        return result
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def strategy_list(include_test_strategies: bool = False) -> dict:
    """List available strategies"""
    try:
        return jesse.list_strategies(include_test_strategies)
    except Exception as e:
        logger.error(f"Strategy list failed: {e}")
        return {"error": str(e), "strategies": []}


@mcp.tool
def strategy_read(name: str) -> dict:
    """Read strategy source code"""
    try:
        return jesse.read_strategy(name)
    except Exception as e:
        logger.error(f"Strategy read failed: {e}")
        return {"error": str(e), "name": name}


@mcp.tool
def strategy_validate(code: str) -> dict:
    """Validate strategy code without saving"""
    try:
        return jesse.validate_strategy(code)
    except Exception as e:
        logger.error(f"Strategy validation failed: {e}")
        return {"error": str(e), "valid": False}


@mcp.tool
def candles_import(
    exchange: str,
    symbol: str,
    start_date: str,
    end_date: Optional[str] = None,
) -> dict:
    """Download candle data from exchange"""
    try:
        return jesse.import_candles(
            exchange=exchange,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        logger.error(f"Candles import failed: {e}")
        return {"error": str(e), "success": False}


# ==================== PHASE 3: OPTIMIZATION TOOLS ====================


@mcp.tool
async def optimize(
    strategy: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    param_space: dict,
    metric: str = "total_return",
    n_trials: int = 100,
    n_jobs: int = 1,
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
) -> dict:
    """Optimize strategy hyperparameters using Optuna"""
    try:
        result = await optimizer.optimize(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            param_space=param_space,
            metric=metric,
            n_trials=n_trials,
            n_jobs=n_jobs,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
        )
        return result
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def walk_forward(
    strategy: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    in_sample_period: int = 365,
    out_sample_period: int = 30,
    step_forward: int = 7,
    param_space: Optional[dict] = None,
    metric: str = "total_return",
) -> dict:
    """Perform walk-forward analysis to detect overfitting"""
    try:
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
    except Exception as e:
        logger.error(f"Walk-forward analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def backtest_batch(
    strategy: str,
    symbols: list,
    timeframes: list,
    start_date: str,
    end_date: str,
    hyperparameters: Optional[list] = None,
    concurrent_limit: int = 4,
) -> dict:
    """Run multiple backtests concurrently for strategy comparison"""
    try:
        result = await optimizer.backtest_batch(
            strategy=strategy,
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            hyperparameters=hyperparameters or [],
            concurrent_limit=concurrent_limit,
        )
        return result
    except Exception as e:
        logger.error(f"Batch backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def analyze_results(
    backtest_result: dict,
    analysis_type: str = "basic",
    include_trade_analysis: bool = True,
    include_correlation: bool = False,
    include_monte_carlo: bool = False,
) -> dict:
    """Extract deep insights from backtest results"""
    try:
        result = optimizer.analyze_results(
            backtest_result=backtest_result,
            analysis_type=analysis_type,
            include_trade_analysis=include_trade_analysis,
            include_correlation=include_correlation,
            include_monte_carlo=include_monte_carlo,
        )
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


# ==================== PHASE 4: RISK ANALYSIS TOOLS ====================


@mcp.tool
async def monte_carlo(
    backtest_result: dict,
    simulations: int = 10000,
    confidence_levels: Optional[list] = None,
    resample_method: str = "bootstrap",
    block_size: int = 20,
    include_drawdowns: bool = True,
    include_returns: bool = True,
) -> dict:
    """Generate Monte Carlo simulations for comprehensive risk analysis"""
    try:
        result = await risk_analyzer.monte_carlo(
            backtest_result=backtest_result,
            simulations=simulations,
            confidence_levels=confidence_levels or [],
            resample_method=resample_method,
            block_size=block_size,
            include_drawdowns=include_drawdowns,
            include_returns=include_returns,
        )
        return result
    except Exception as e:
        logger.error(f"Monte Carlo analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def var_calculation(
    backtest_result: dict,
    confidence_levels: Optional[list] = None,
    time_horizons: Optional[list] = None,
    method: str = "all",
    monte_carlo_sims: int = 10000,
) -> dict:
    """Calculate Value at Risk using multiple methods"""
    try:
        result = await risk_analyzer.var_calculation(
            backtest_result=backtest_result,
            confidence_levels=confidence_levels or [],
            time_horizons=time_horizons or [],
            method=method,
            monte_carlo_sims=monte_carlo_sims,
        )
        return result
    except Exception as e:
        logger.error(f"VaR calculation failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def stress_test(
    backtest_result: dict,
    scenarios: Optional[list] = None,
    include_custom_scenarios: bool = False,
) -> dict:
    """Test strategy performance under extreme market scenarios"""
    try:
        result = await risk_analyzer.stress_test(
            backtest_result=backtest_result,
            scenarios=scenarios,
            custom_scenarios=include_custom_scenarios,
        )
        return result
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def risk_report(
    backtest_result: dict,
    include_monte_carlo: bool = True,
    include_var_analysis: bool = True,
    include_stress_test: bool = True,
    monte_carlo_sims: int = 5000,
    report_format: str = "summary",
) -> dict:
    """Generate comprehensive risk assessment and recommendations"""
    try:
        result = await risk_analyzer.risk_report(
            backtest_result=backtest_result,
            include_monte_carlo=include_monte_carlo,
            include_var_analysis=include_var_analysis,
            include_stress_test=include_stress_test,
            monte_carlo_sims=monte_carlo_sims,
            report_format=report_format,
        )
        return result
    except Exception as e:
        logger.error(f"Risk report failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


# ==================== PHASE 5: PAIRS TRADING TOOLS ====================


@mcp.tool
async def correlation_matrix(
    backtest_results: list,
    lookback_period: int = 60,
    correlation_threshold: float = 0.7,
    include_rolling: bool = True,
    rolling_window: int = 20,
    include_heatmap: bool = False,
) -> dict:
    """Analyze cross-asset correlations and identify pairs trading opportunities"""
    try:
        result = await pairs_analyzer.correlation_matrix(
            backtest_results=backtest_results,
            lookback_period=lookback_period,
            correlation_threshold=correlation_threshold,
            include_rolling=include_rolling,
            rolling_window=rolling_window,
            include_heatmap=include_heatmap,
        )
        return result
    except Exception as e:
        logger.error(f"Correlation matrix failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def pairs_backtest(
    pair: dict,
    backtest_result_1: dict,
    backtest_result_2: dict,
    strategy: str = "mean_reversion",
    lookback_period: int = 60,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    position_size: float = 0.02,
    max_holding_days: int = 20,
) -> dict:
    """Backtest pairs trading strategies"""
    try:
        result = await pairs_analyzer.pairs_backtest(
            pair=pair,
            strategy=strategy,
            backtest_result_1=backtest_result_1,
            backtest_result_2=backtest_result_2,
            lookback_period=lookback_period,
            entry_threshold=entry_threshold,
            exit_threshold=exit_threshold,
            position_size=position_size,
            max_holding_days=max_holding_days,
        )
        return result
    except Exception as e:
        logger.error(f"Pairs backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def factor_analysis(
    backtest_result: dict,
    factors: Optional[list] = None,
    factor_returns: Optional[dict] = None,
    include_residuals: bool = True,
    analysis_period: int = 252,
    confidence_level: float = 0.95,
) -> dict:
    """Decompose returns into systematic factors"""
    try:
        result = await pairs_analyzer.factor_analysis(
            backtest_result=backtest_result,
            factors=factors,
            factor_returns=factor_returns,
            include_residuals=include_residuals,
            analysis_period=analysis_period,
            confidence_level=confidence_level,
        )
        return result
    except Exception as e:
        logger.error(f"Factor analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
async def regime_detector(
    backtest_results: list,
    lookback_period: int = 60,
    detection_method: str = "hmm",
    n_regimes: int = 3,
    include_transitions: bool = True,
    include_forecast: bool = True,
) -> dict:
    """Identify market regimes and transitions"""
    try:
        result = await pairs_analyzer.regime_detector(
            backtest_results=backtest_results,
            lookback_period=lookback_period,
            detection_method=detection_method,
            n_regimes=n_regimes,
            include_transitions=include_transitions,
            include_forecast=include_forecast,
        )
        return result
    except Exception as e:
        logger.error(f"Regime detector failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


# ==================== MAIN ENTRY POINT ====================


def main():
    """Main entry point with transport options"""
    import argparse

    # Initialize dependencies when server starts
    _initialize_dependencies()

    parser = argparse.ArgumentParser(description="Jesse MCP Server - Quantitative Trading Analysis")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)",
    )

    args = parser.parse_args()

    if args.transport == "http":
        logger.info(f"Starting Jesse MCP Server on http://0.0.0.0:{args.port}")
        mcp.run(transport="http", host="0.0.0.0", port=args.port)
    else:
        logger.info("Starting Jesse MCP Server (stdio transport)")
        mcp.run()


if __name__ == "__main__":
    main()
