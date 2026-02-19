#!/usr/bin/env python3
"""
Jesse MCP Server - FastMCP Implementation

Provides 18 tools for quantitative trading analysis:
- Phase 1: Backtesting (5 tools)
- Phase 3: Optimization (4 tools) [formerly phase3]
- Phase 4: Risk Analysis (4 tools) [formerly phase4]
- Phase 5: Pairs Trading (5 tools) [formerly phase5]
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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

        if JESSE_AVAILABLE:
            jesse = get_jesse_wrapper()
            logger.info("✅ Jesse framework initialized")
        else:
            logger.warning("⚠️ Jesse framework not available - running in mock mode")
    except Exception as e:
        logger.warning(f"⚠️ Jesse initialization failed: {e} - running in mock mode")

    try:
        from jesse_mcp.optimizer import get_optimizer

        optimizer = get_optimizer()
        logger.info("✅ Optimizer module loaded")
    except Exception as e:
        logger.warning(f"⚠️ Optimizer initialization failed: {e}")

    try:
        from jesse_mcp.risk_analyzer import get_risk_analyzer

        risk_analyzer = get_risk_analyzer()
        logger.info("✅ Risk analyzer module loaded")
    except Exception as e:
        logger.warning(f"⚠️ Risk analyzer initialization failed: {e}")

    try:
        from jesse_mcp.pairs_analyzer import get_pairs_analyzer

        pairs_analyzer = get_pairs_analyzer()
        logger.info("✅ Pairs analyzer module loaded")
    except Exception as e:
        logger.warning(f"⚠️ Pairs analyzer initialization failed: {e}")

    _initialized = True


# ==================== FASTMCP INITIALIZATION ====================

mcp = FastMCP("jesse-mcp", version="1.0.0")


@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """
    HTTP health endpoint for monitoring Jesse MCP server status.

    Returns MCP server status, Jesse connection status, and timestamp.
    """
    from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

    jesse_status = {"connected": False, "error": None}
    try:
        client = get_jesse_rest_client()
        jesse_status = client.health_check()
    except Exception as e:
        jesse_status["error"] = str(e)

    return JSONResponse(
        {
            "status": "healthy",
            "mcp_server": "jesse-mcp",
            "version": "1.0.0",
            "jesse": jesse_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ==================== PHASE 1: BACKTESTING TOOLS ====================


@mcp.tool
def jesse_status() -> dict:
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
        result = client.backtest(
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
    """
    List all available trading strategies.

    Use this as the FIRST step to see what strategies are available to test.
    Returns list of strategy names that can be passed to backtest(), analyze_results(), etc.
    """
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


@mcp.tool
def rate_limit_status() -> dict:
    """
    Get current rate limiter status for Jesse API calls.

    Returns:
        Dict with rate limit configuration and statistics:
        - enabled: Whether rate limiting is active
        - rate_per_second: Configured requests per second
        - available_tokens: Current tokens available
        - wait_mode: Whether to wait or reject when limited
        - stats: Total requests, waits, rejections, wait time
    """
    try:
        from jesse_mcp.core.rate_limiter import get_rate_limiter

        limiter = get_rate_limiter()
        return limiter.get_status()
    except Exception as e:
        logger.error(f"Rate limit status failed: {e}")
        return {"error": str(e)}


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
    """
    Auto-optimize strategy hyperparameters using Bayesian optimization.

    Automatically tests many parameter combinations to find best metrics.

    Example: Improve Sharpe ratio by optimizing EMA periods
    - param_space: {"ema_fast": [5, 30], "ema_slow": [20, 100]}
    - metric: "sharpe_ratio"

    Returns best parameters found and their performance metrics.
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
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


# ==================== CACHE MANAGEMENT TOOLS ====================


@mcp.tool
def cache_stats() -> dict:
    """
    Get cache statistics including hit/miss ratio and cache sizes.

    Returns:
        Dict with cache status, hit rates, and sizes for all caches
    """
    try:
        from jesse_mcp.core.cache import get_all_stats

        return get_all_stats()
    except Exception as e:
        logger.error(f"Cache stats failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def cache_clear(cache_name: Optional[str] = None) -> dict:
    """
    Clear cache(s) to free memory or force fresh data.

    Args:
        cache_name: Specific cache to clear (strategy_list, backtest).
                   If None, clears all caches.

    Returns:
        Dict with number of entries cleared per cache
    """
    try:
        from jesse_mcp.core.cache import clear_all_caches, clear_cache

        if cache_name:
            count = clear_cache(cache_name)
            return {"cleared": {cache_name: count}}
        else:
            return {"cleared": clear_all_caches()}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


# ==================== LIVE TRADING TOOLS (Phase 6) ====================


@mcp.tool
def live_check_plugin() -> dict:
    """
    Check if jesse-live plugin is installed and available.

    Returns:
        Dict with 'available' boolean and optional 'error' message
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.check_live_plugin_available()
    except Exception as e:
        logger.error(f"Live plugin check failed: {e}")
        return {"available": False, "error": str(e)}


@mcp.tool
def live_start_paper_trading(
    strategy: str,
    symbol: str,
    timeframe: str,
    exchange: str,
    exchange_api_key_id: str,
    notification_api_key_id: str = "",
    debug_mode: bool = False,
) -> dict:
    """
    Start a PAPER trading session (simulated, no real money).

    Paper trading simulates trades without using real funds.
    Use this to test strategies before going live.

    Args:
        strategy: Strategy name (must exist in strategies directory)
        symbol: Trading symbol (e.g., "BTC-USDT")
        timeframe: Candle timeframe (e.g., "1h", "4h", "1d")
        exchange: Exchange name (e.g., "Binance", "Bybit")
        exchange_api_key_id: ID of stored exchange API key in Jesse
        notification_api_key_id: ID of stored notification config (optional)
        debug_mode: Enable debug logging

    Returns:
        Dict with session_id and status, or error details
    """
    try:
        from jesse_mcp.core.live_config import PAPER_TRADING_INFO
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        logger.info(PAPER_TRADING_INFO)

        client = get_jesse_rest_client()
        result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=True,
            debug_mode=debug_mode,
        )
        result["mode"] = "paper"
        return result
    except Exception as e:
        logger.error(f"Paper trading start failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def live_start_live_trading(
    strategy: str,
    symbol: str,
    timeframe: str,
    exchange: str,
    exchange_api_key_id: str,
    confirmation: str,
    notification_api_key_id: str = "",
    debug_mode: bool = False,
    permission: str = "confirm_required",
) -> dict:
    """
    Start LIVE trading with REAL MONEY.

    ⚠️  WARNING: This will execute real trades with real funds. ⚠️

    RISKS:
    - Your funds are at risk of total loss
    - Automated trading can result in significant losses
    - No guarantee of profit

    REQUIREMENTS:
    1. Thoroughly backtested strategy
    2. Successful paper trading first
    3. Understanding of strategy's risk profile
    4. Capital you can afford to lose

    Args:
        strategy: Strategy name (must exist in strategies directory)
        symbol: Trading symbol (e.g., "BTC-USDT")
        timeframe: Candle timeframe (e.g., "1h", "4h", "1d")
        exchange: Exchange name (e.g., "Binance", "Bybit")
        exchange_api_key_id: ID of stored exchange API key in Jesse
        confirmation: REQUIRED: Must be exactly "I UNDERSTAND THE RISKS"
        notification_api_key_id: ID of stored notification config (optional)
        debug_mode: Enable debug logging
        permission: Agent permission level ("paper_only", "confirm_required", "full_autonomous")

    Returns:
        Dict with session_id and status, or error details
    """
    try:
        from jesse_mcp.core.live_config import (
            LiveTradingConfig,
            AgentPermission,
            LIVE_TRADING_WARNING,
            LiveSessionRequest,
        )
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        config = LiveTradingConfig.from_env()

        if confirmation != config.confirmation_phrase:
            return {
                "error": f"Invalid confirmation. Required: '{config.confirmation_phrase}'",
                "warning": LIVE_TRADING_WARNING,
            }

        try:
            perm = AgentPermission(permission)
        except ValueError:
            perm = AgentPermission.CONFIRM_REQUIRED

        request = LiveSessionRequest(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=False,
            debug_mode=debug_mode,
            permission=perm,
            confirmation=confirmation,
        )

        validation = request.validate_for_live_mode(config)
        if not validation.get("valid"):
            return {"error": validation.get("error"), "warning": LIVE_TRADING_WARNING}

        logger.warning(LIVE_TRADING_WARNING)

        client = get_jesse_rest_client()
        result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=False,
            debug_mode=debug_mode,
        )
        result["mode"] = "live"
        result["warning"] = "REAL MONEY TRADING - Monitor closely!"
        return result
    except Exception as e:
        logger.error(f"Live trading start failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def live_cancel_session(session_id: str, paper_mode: bool = True) -> dict:
    """
    Cancel a running live/paper trading session.

    Args:
        session_id: Session ID to cancel
        paper_mode: True if paper trading session, False if live

    Returns:
        Dict with cancellation status
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.cancel_live_session(session_id, paper_mode)
    except Exception as e:
        logger.error(f"Session cancel failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def live_get_sessions(limit: int = 50, offset: int = 0) -> dict:
    """
    Get list of live trading sessions.

    Args:
        limit: Maximum number of sessions to return (default: 50)
        offset: Offset for pagination (default: 0)

    Returns:
        Dict with sessions list
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_sessions(limit, offset)
    except Exception as e:
        logger.error(f"Get sessions failed: {e}")
        return {"error": str(e), "sessions": []}


@mcp.tool
def live_get_status(session_id: str) -> dict:
    """
    Get status of a specific live trading session.

    Args:
        session_id: Session ID to check

    Returns:
        Dict with session details and current status
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_session(session_id)
    except Exception as e:
        logger.error(f"Get session status failed: {e}")
        return {"error": str(e), "session": None}


@mcp.tool
def live_get_orders(session_id: str) -> dict:
    """
    Get orders from a live trading session.

    Args:
        session_id: Session ID

    Returns:
        Dict with orders list
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_orders(session_id)
    except Exception as e:
        logger.error(f"Get orders failed: {e}")
        return {"error": str(e), "orders": []}


@mcp.tool
def live_get_equity_curve(
    session_id: str,
    from_ms: Optional[int] = None,
    to_ms: Optional[int] = None,
) -> dict:
    """
    Get real-time equity curve (P&L) for a session.

    Args:
        session_id: Session ID
        from_ms: Start time in milliseconds (optional)
        to_ms: End time in milliseconds (optional)

    Returns:
        Dict with equity curve data points
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_equity_curve(session_id, from_ms, to_ms)
    except Exception as e:
        logger.error(f"Get equity curve failed: {e}")
        return {"error": str(e), "data": []}


@mcp.tool
def live_get_logs(session_id: str, log_type: str = "all") -> dict:
    """
    Get logs from a live trading session.

    Args:
        session_id: Session ID
        log_type: Log type filter ("all", "info", "error", "warning")

    Returns:
        Dict with log entries
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_logs(session_id, log_type)
    except Exception as e:
        logger.error(f"Get logs failed: {e}")
        return {"error": str(e), "data": []}


# ==================== PAPER TRADING TOOLS (PRD-PAPER.md) ====================


@mcp.tool
def paper_start(
    strategy: str,
    symbol: str,
    timeframe: str = "1h",
    exchange: str = "Binance",
    exchange_api_key_id: str = "",
    starting_balance: float = 10000,
    leverage: float = 1,
    fee: float = 0.001,
    session_id: Optional[str] = None,
) -> dict:
    """
    Start a paper trading session.

    Paper trading simulates trades without using real funds.
    Use this to test strategies before going live.

    Args:
        strategy: Strategy name (e.g., 'SMACrossover', 'DayTrader')
        symbol: Trading pair (e.g., 'BTC-USDT')
        timeframe: Candle timeframe (default: '1h')
        exchange: Exchange name (default: 'Binance')
        exchange_api_key_id: ID of stored exchange API key in Jesse
        starting_balance: Initial capital (default: 10000)
        leverage: Futures leverage (default: 1)
        fee: Trading fee rate (default: 0.001)
        session_id: Optional custom session ID (auto-generated if not provided)

    Returns:
        Dict with session_id, status, and configuration
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()

        config = {
            "starting_balance": starting_balance,
            "fee": fee,
            "futures_leverage": leverage,
        }

        result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            paper_mode=True,
            config=config,
        )

        if "error" not in result:
            result["mode"] = "paper"
            result["starting_balance"] = starting_balance
            result["leverage"] = leverage
            result["fee"] = fee

        return result
    except Exception as e:
        logger.error(f"Paper trading start failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def paper_stop(session_id: str) -> dict:
    """
    Stop a paper trading session and return final metrics.

    Args:
        session_id: Session ID to stop

    Returns:
        Dict with stopped_at, duration, and final_metrics
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client
        from datetime import datetime

        client = get_jesse_rest_client()

        result = client.cancel_live_session(session_id, paper_mode=True)

        if "error" not in result:
            session = client.get_live_session(session_id)
            result["stopped_at"] = datetime.utcnow().isoformat()
            result["final_metrics"] = session.get("session", {}).get("metrics", {})

        return result
    except Exception as e:
        logger.error(f"Paper trading stop failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def paper_status(session_id: str) -> dict:
    """
    Get current status of a paper trading session.

    Args:
        session_id: Session ID to check

    Returns:
        Dict with session status, equity, positions, and metrics
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_session(session_id)
    except Exception as e:
        logger.error(f"Paper status failed: {e}")
        return {"error": str(e), "session": None}


@mcp.tool
def paper_get_trades(session_id: str, limit: int = 100, offset: int = 0) -> dict:
    """
    Get trades executed in a paper trading session.

    Args:
        session_id: Session ID
        limit: Maximum number of trades to return (default: 100)
        offset: Offset for pagination (default: 0)

    Returns:
        Dict with total_trades and trades list
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        result = client.get_closed_trades(session_id, limit)

        trades = result.get("data", [])
        if offset > 0:
            trades = trades[offset:]

        return {
            "session_id": session_id,
            "total_trades": len(result.get("data", [])),
            "trades": trades,
        }
    except Exception as e:
        logger.error(f"Paper get trades failed: {e}")
        return {"error": str(e), "trades": []}


@mcp.tool
def paper_get_equity(session_id: str, resolution: str = "1h") -> dict:
    """
    Get equity curve data for a paper trading session.

    Args:
        session_id: Session ID
        resolution: Resolution of equity curve data (default: '1h')

    Returns:
        Dict with equity_curve containing timestamp, equity, drawdown data
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()

        timeframe_map = {
            "1m": 60000,
            "5m": 300000,
            "15m": 900000,
            "1h": 3600000,
            "4h": 14400000,
            "1d": 86400000,
        }
        max_points = 1000

        result = client.get_live_equity_curve(
            session_id,
            timeframe=resolution,
            max_points=max_points,
        )

        return {
            "session_id": session_id,
            "resolution": resolution,
            "equity_curve": result.get("data", []),
        }
    except Exception as e:
        logger.error(f"Paper get equity failed: {e}")
        return {"error": str(e), "equity_curve": []}


@mcp.tool
def paper_get_metrics(session_id: str) -> dict:
    """
    Get calculated performance metrics for a paper trading session.

    Args:
        session_id: Session ID

    Returns:
        Dict with metrics: total_return, sharpe_ratio, max_drawdown, win_rate, etc.
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        session = client.get_live_session(session_id)

        session_data = session.get("session", {})
        metrics = session_data.get("metrics", {})

        return {
            "session_id": session_id,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"Paper get metrics failed: {e}")
        return {"error": str(e), "metrics": {}}


@mcp.tool
def paper_list_sessions() -> dict:
    """
    List all paper trading sessions.

    Returns:
        Dict with sessions list and total count
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()
        return client.get_live_sessions()
    except Exception as e:
        logger.error(f"Paper list sessions failed: {e}")
        return {"error": str(e), "sessions": []}


@mcp.tool
def paper_update_session(session_id: str, notes: Optional[str] = None) -> dict:
    """
    Update session parameters (limited to safe modifications).

    Args:
        session_id: Session ID to update
        notes: Notes text to associate with session

    Returns:
        Dict with update status
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

        client = get_jesse_rest_client()

        if notes is not None:
            return client.update_live_session_notes(session_id, notes)

        return {"session_id": session_id, "status": "no_updates"}
    except Exception as e:
        logger.error(f"Paper update session failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


# ==================== MAIN ENTRY POINT ====================


def main():
    """Main entry point with transport options"""
    import argparse

    # Initialize dependencies when server starts
    _initialize_dependencies()

    # Register agent tools
    try:
        from jesse_mcp.agent_tools import register_agent_tools

        register_agent_tools(mcp)
        logger.info("✅ Agent tools registered")
    except Exception as e:
        logger.warning(f"⚠️  Agent tools registration failed: {e}")

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
