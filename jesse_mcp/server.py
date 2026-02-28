#!/usr/bin/env python3
"""
Jesse MCP Server - FastMCP Implementation

Provides 46 tools for quantitative trading analysis:
- Phase 1: Backtesting (5 tools)
- Phase 3: Optimization (4 tools)
- Phase 4: Risk Analysis (4 tools)
- Phase 5: Pairs Trading (5 tools)
- Phase 6: Live Trading (12 tools)
- Strategy Creation (6 tools) - Ralph Wiggum Loop with progress tracking
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from jesse_mcp.core.strategy_validation.metadata import (
    get_or_create_metadata,
    save_metadata,
    load_metadata,
    CERTIFICATION_MIN_TESTS,
    CERTIFICATION_PASS_RATE,
)
from starlette.requests import Request
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jesse-mcp")

# ==================== LAZY INITIALIZATION ====================
# These will be initialized when main() is called, not at import time
# This allows the server module to be imported for testing without Jesse

jesse: Optional[Any] = None
optimizer: Optional[Any] = None
risk_analyzer: Optional[Any] = None
pairs_analyzer: Optional[Any] = None
_initialized: bool = False


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


@mcp.tool
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


@mcp.tool
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


@mcp.tool
def strategy_read(name: str) -> Dict[str, Any]:
    """Read strategy source code"""
    try:
        if jesse is None:
            raise RuntimeError("Jesse framework not initialized")
        return jesse.read_strategy(name)
    except Exception as e:
        logger.error(f"Strategy read failed: {e}")
        return {"error": str(e), "name": name}


@mcp.tool
def strategy_validate(code: str) -> Dict[str, Any]:
    """Validate strategy code without saving"""
    try:
        if jesse is None:
            raise RuntimeError("Jesse framework not initialized")
        return jesse.validate_strategy(code)
    except Exception as e:
        logger.error(f"Strategy validation failed: {e}")
        return {"error": str(e), "valid": False}


# ==================== STRATEGY CREATION TOOLS (Ralph Wiggum Loop) ====================


def _strategy_create_impl(
    name: str,
    description: str,
    indicators: Optional[List[str]] = None,
    strategy_type: str = "trend_following",
    risk_per_trade: float = 0.02,
    timeframe: str = "1h",
    max_iterations: int = 5,
    overwrite: bool = False,
    skip_backtest: bool = True,
    progress_callback: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Internal implementation for strategy creation with iterative refinement.
    """
    from jesse_mcp.core.job_manager import get_job_manager, JobStatus
    from jesse_mcp.core.strategy_validator import get_validator
    from jesse_mcp.core.strategy_builder import get_strategy_builder, StrategySpec
    import os

    try:
        if jesse is None:
            raise RuntimeError("Jesse framework not initialized")

        strategies_path = getattr(jesse, "strategies_path", None)
        if not strategies_path:
            return {"error": "Strategies path not available", "status": "failed"}

        strategy_dir = os.path.join(strategies_path, name)
        strategy_file = os.path.join(strategy_dir, "__init__.py")

        if os.path.exists(strategy_dir) and not overwrite:
            return {
                "error": f"Strategy '{name}' already exists. Use overwrite=True to replace.",
                "status": "failed",
                "name": name,
            }

        validator = get_validator()
        builder = get_strategy_builder(validator)

        metadata = get_or_create_metadata(name, strategies_path)

        spec = StrategySpec(
            name=name,
            description=description,
            strategy_type=strategy_type,
            indicators=indicators or [],
            risk_per_trade=risk_per_trade,
            timeframe=timeframe,
        )

        if progress_callback:
            progress_callback(0.1, "Generating initial strategy code", 0)

        code = builder.generate_initial(spec)

        def internal_progress(pct: float, step: str, iteration: int):
            if progress_callback:
                progress_callback(0.1 + (pct * 0.8), step, iteration)

        os.makedirs(strategy_dir, exist_ok=True)
        with open(strategy_file, "w") as f:
            f.write(code)
        logger.info(f"✅ Strategy saved: {strategy_file}")

        final_code, history, success = builder.refinement_loop(
            code,
            spec,
            max_iter=max_iterations,
            skip_backtest=skip_backtest,
            progress_callback=internal_progress,
        )

        for h in history:
            dry_run = h.get("dry_run", {})
            if dry_run and not dry_run.get("skipped"):
                passed = dry_run.get("passed", False)
                metadata.record_test(passed)
                save_metadata(metadata, strategies_path)

        if metadata.should_certify():
            metadata.certify()
            save_metadata(metadata, strategies_path)

        if progress_callback:
            progress_callback(0.95, "Updating strategy", max_iterations)

        if final_code != code:
            with open(strategy_file, "w") as f:
                f.write(final_code)
            logger.info(f"✅ Strategy updated: {strategy_file}")

        return {
            "status": "created" if success else "validation_failed",
            "name": name,
            "version": metadata.version,
            "test_count": metadata.test_count,
            "test_pass_count": metadata.test_pass_count,
            "certified": metadata.certified_at is not None,
            "iterations": len(history),
            "validation_history": [
                {"iteration": h["iteration"], "passed": h["result"].get("passed", False)}
                for h in history
            ],
            "path": strategy_file if success else None,
            "code": final_code,
            "ready_for_backtest": success,
        }

    except Exception as e:
        logger.error(f"Strategy creation failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__, "status": "failed"}


@mcp.tool
def strategy_create(
    name: str,
    description: str,
    indicators: Optional[List[str]] = None,
    strategy_type: str = "trend_following",
    risk_per_trade: float = 0.02,
    timeframe: str = "1h",
    max_iterations: int = 5,
    overwrite: bool = False,
    async_mode: bool = False,
    skip_backtest: bool = True,
) -> Dict[str, Any]:
    """
    Create strategy with iterative refinement (Ralph Wiggum loop).

    If async_mode=True, creates a Job and returns job_id immediately.
    Otherwise runs synchronously with progress logging.

    Args:
        name: Strategy name (used as class name)
        description: Human-readable description of the strategy
        indicators: List of technical indicators to use (optional)
        strategy_type: Type classification (default: trend_following)
        risk_per_trade: Risk percentage per trade (default: 0.02 = 2%)
        timeframe: Primary trading timeframe (default: 1h)
        max_iterations: Maximum refinement iterations (default: 5)
        overwrite: Overwrite existing strategy (default: False)
        async_mode: Run asynchronously (default: False)
        skip_backtest: Skip dry-run backtest validation (default: True)

    Returns:
        Dict with status, name, iterations, validation_history, path, code, ready_for_backtest
    """
    try:
        if not async_mode:
            return _strategy_create_impl(
                name=name,
                description=description,
                indicators=indicators,
                strategy_type=strategy_type,
                risk_per_trade=risk_per_trade,
                timeframe=timeframe,
                max_iterations=max_iterations,
                overwrite=overwrite,
                skip_backtest=skip_backtest,
            )

        from jesse_mcp.core.job_manager import get_job_manager

        job_manager = get_job_manager()
        job = job_manager.create_job(
            "strategy_create",
            {
                "name": name,
                "description": description,
                "indicators": indicators,
                "strategy_type": strategy_type,
                "risk_per_trade": risk_per_trade,
                "timeframe": timeframe,
                "max_iterations": max_iterations,
                "overwrite": overwrite,
                "skip_backtest": skip_backtest,
            },
        )
        job_id = job.id

        def run_async():
            def progress_callback(pct: float, step: str, iteration: int):
                job_manager.update_progress(
                    job_id,
                    progress_percent=pct * 100,
                    current_step=step,
                    iterations_completed=iteration,
                    iterations_total=max_iterations,
                )

            try:
                result = _strategy_create_impl(
                    name=name,
                    description=description,
                    indicators=indicators,
                    strategy_type=strategy_type,
                    risk_per_trade=risk_per_trade,
                    timeframe=timeframe,
                    max_iterations=max_iterations,
                    overwrite=overwrite,
                    skip_backtest=skip_backtest,
                    progress_callback=progress_callback,
                )
                if "error" in result and result.get("status") == "failed":
                    job_manager.fail_job(job_id, result["error"])
                else:
                    job_manager.complete_job(job_id, result)
            except Exception as e:
                job_manager.fail_job(job_id, str(e))

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

        return {"job_id": job_id, "status": "started", "async_mode": True}

    except Exception as e:
        logger.error(f"Strategy create failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def strategy_create_status(job_id: str) -> Dict[str, Any]:
    """
    Poll async job progress for strategy creation.

    Args:
        job_id: Job identifier from strategy_create

    Returns:
        Dict with job_id, status, progress_percent, current_step,
        iterations_completed, iterations_total, elapsed_seconds, result (when complete)
    """
    try:
        from jesse_mcp.core.job_manager import get_job_manager

        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            return {"error": f"Job not found: {job_id}", "job_id": job_id}

        elapsed = None
        if job.started_at:
            elapsed = (datetime.now(timezone.utc) - job.started_at).total_seconds()

        result = {
            "job_id": job_id,
            "status": job.status.value,
            "progress_percent": job.progress_percent,
            "current_step": job.current_step,
            "iterations_completed": job.iterations_completed,
            "iterations_total": job.iterations_total,
            "elapsed_seconds": elapsed,
        }

        if job.status.value in ("complete", "failed", "cancelled"):
            result["result"] = job.result
            if job.error:
                result["error"] = job.error

        return result

    except Exception as e:
        logger.error(f"Strategy create status failed: {e}")
        return {"error": str(e), "job_id": job_id}


@mcp.tool
def strategy_create_cancel(job_id: str) -> Dict[str, Any]:
    """
    Cancel async strategy creation job.

    Args:
        job_id: Job identifier to cancel

    Returns:
        Dict with status, job_id
    """
    try:
        from jesse_mcp.core.job_manager import get_job_manager

        job_manager = get_job_manager()
        cancelled = job_manager.cancel_job(job_id)

        if cancelled:
            return {"status": "cancelled", "job_id": job_id}
        else:
            return {
                "status": "not_cancelled",
                "job_id": job_id,
                "reason": "Job not found or already complete",
            }

    except Exception as e:
        logger.error(f"Strategy create cancel failed: {e}")
        return {"error": str(e), "job_id": job_id}


@mcp.tool
def strategy_refine(
    name: str,
    feedback: str,
    focus_area: str = "general",
    max_iterations: int = 3,
) -> Dict[str, Any]:
    """
    Refine existing strategy based on feedback.

    Reads strategy, refines based on feedback, re-validates.

    Args:
        name: Strategy name to refine
        feedback: Feedback/issues to address
        focus_area: Area to focus refinement (default: general)
        max_iterations: Maximum refinement iterations (default: 3)

    Returns:
        Dict with status, name, iterations, changes
    """
    try:
        from jesse_mcp.core.strategy_validator import get_validator
        from jesse_mcp.core.strategy_builder import get_strategy_builder
        import os

        if jesse is None:
            raise RuntimeError("Jesse framework not initialized")

        strategies_path = getattr(jesse, "strategies_path", None)
        if not strategies_path:
            return {"error": "Strategies path not available", "status": "failed"}

        strategy_dir = os.path.join(strategies_path, name)
        strategy_file = os.path.join(strategy_dir, "__init__.py")

        if not os.path.exists(strategy_file):
            return {"error": f"Strategy '{name}' not found", "status": "failed", "name": name}

        with open(strategy_file, "r") as f:
            current_code = f.read()

        validator = get_validator()
        builder = get_strategy_builder(validator)

        spec = {
            "name": name,
            "description": f"Refined: {feedback}",
            "strategy_type": focus_area,
        }

        changes = []
        for iteration in range(max_iterations):
            logger.info(f"Refinement iteration {iteration + 1}/{max_iterations}")

            validation_result = validator.full_validation(current_code, spec)
            changes.append(
                {
                    "iteration": iteration + 1,
                    "validation_passed": validation_result.get("passed", False),
                    "errors": validation_result.get("errors", [])[:3],
                }
            )

            if validation_result.get("passed", False):
                break

            current_code = builder.refine_from_validation(current_code, validation_result)

        with open(strategy_file, "w") as f:
            f.write(current_code)

        logger.info(f"✅ Strategy refined: {strategy_file}")

        return {
            "status": "refined",
            "name": name,
            "iterations": len(changes),
            "changes": changes,
            "path": strategy_file,
        }

    except Exception as e:
        logger.error(f"Strategy refine failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def strategy_delete(name: str, confirm: bool = False) -> Dict[str, Any]:
    """
    Delete a strategy.

    Args:
        name: Strategy name to delete
        confirm: Must be True to actually delete (default: False)

    Returns:
        Dict with status, name
    """
    try:
        import os
        import shutil

        if not confirm:
            return {
                "status": "confirmation_required",
                "name": name,
                "message": "Set confirm=True to delete the strategy",
            }

        if jesse is None:
            raise RuntimeError("Jesse framework not initialized")

        strategies_path = getattr(jesse, "strategies_path", None)
        if not strategies_path:
            return {"error": "Strategies path not available", "status": "failed"}

        strategy_dir = os.path.join(strategies_path, name)

        if not os.path.exists(strategy_dir):
            return {"error": f"Strategy '{name}' not found", "status": "not_found", "name": name}

        shutil.rmtree(strategy_dir)
        logger.info(f"✅ Strategy deleted: {strategy_dir}")

        return {"status": "deleted", "name": name}

    except Exception as e:
        logger.error(f"Strategy delete failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
def jobs_list(job_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    List recent jobs.

    Args:
        job_type: Filter by job type (optional)
        limit: Maximum number of jobs to return (default: 50)

    Returns:
        Dict with list of jobs containing id, type, status, progress, current_step, started_at
    """
    try:
        from jesse_mcp.core.job_manager import get_job_manager

        job_manager = get_job_manager()
        jobs = job_manager.list_jobs(job_type=job_type, limit=limit)

        return {
            "jobs": [
                {
                    "id": job.id,
                    "type": job.type,
                    "status": job.status.value,
                    "progress": job.progress_percent,
                    "current_step": job.current_step,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                }
                for job in jobs
            ],
            "count": len(jobs),
        }

    except Exception as e:
        logger.error(f"Jobs list failed: {e}")
        return {"error": str(e), "jobs": []}


@mcp.tool
def strategy_metadata(name: str) -> Dict[str, Any]:
    """
    Get metadata and version info for a strategy.

    Args:
        name: Strategy name

    Returns:
        Dict with strategy metadata including version, test_count, test_pass_count,
        certified status, and certification thresholds
    """
    try:
        import os

        if jesse is None:
            raise RuntimeError("Jesse framework not initialized")

        strategies_path = getattr(jesse, "strategies_path", None)
        if not strategies_path:
            return {"error": "Strategies path not available", "status": "failed"}

        strategy_dir = os.path.join(strategies_path, name)
        if not os.path.exists(strategy_dir):
            return {"error": f"Strategy '{name}' not found", "status": "not_found", "name": name}

        metadata = load_metadata(name, strategies_path)
        if metadata is None:
            return {
                "error": f"Metadata not found for strategy '{name}'",
                "status": "not_found",
                "name": name,
            }

        result = metadata.to_dict()
        result["certification_requirements"] = {
            "min_tests": CERTIFICATION_MIN_TESTS,
            "pass_rate": CERTIFICATION_PASS_RATE,
            "current_pass_rate": (
                metadata.test_pass_count / metadata.test_count if metadata.test_count > 0 else 0
            ),
        }
        result["status"] = "found"
        return result

    except Exception as e:
        logger.error(f"Strategy metadata failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool
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


@mcp.tool
def rate_limit_status() -> Dict[str, Any]:
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
    param_space: Dict[str, Any],
    metric: str = "total_return",
    n_trials: int = 100,
    n_jobs: int = 1,
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
) -> Dict[str, Any]:
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
    param_space: Optional[Dict[str, Any]] = None,
    metric: str = "total_return",
) -> Dict[str, Any]:
    """Perform walk-forward analysis to detect overfitting"""
    try:
        if optimizer is None:
            raise RuntimeError("Optimizer module not initialized")
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
    symbols: List[str],
    timeframes: List[str],
    start_date: str,
    end_date: str,
    hyperparameters: Optional[List[Dict[str, Any]]] = None,
    concurrent_limit: int = 4,
) -> Dict[str, Any]:
    """Run multiple backtests concurrently for strategy comparison"""
    try:
        if optimizer is None:
            raise RuntimeError("Optimizer module not initialized")
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
    try:
        if optimizer is None:
            raise RuntimeError("Optimizer module not initialized")
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
    backtest_result: Dict[str, Any],
    simulations: int = 10000,
    confidence_levels: Optional[List[float]] = None,
    resample_method: str = "bootstrap",
    block_size: int = 20,
    include_drawdowns: bool = True,
    include_returns: bool = True,
) -> Dict[str, Any]:
    """Generate Monte Carlo simulations for comprehensive risk analysis"""
    try:
        if risk_analyzer is None:
            raise RuntimeError("Risk analyzer module not initialized")
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
    backtest_result: Dict[str, Any],
    confidence_levels: Optional[List[float]] = None,
    time_horizons: Optional[List[int]] = None,
    method: str = "all",
    monte_carlo_sims: int = 10000,
) -> Dict[str, Any]:
    """Calculate Value at Risk using multiple methods"""
    try:
        if risk_analyzer is None:
            raise RuntimeError("Risk analyzer module not initialized")
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
    backtest_result: Dict[str, Any],
    scenarios: Optional[List[str]] = None,
    include_custom_scenarios: bool = False,
) -> Dict[str, Any]:
    """Test strategy performance under extreme market scenarios"""
    try:
        if risk_analyzer is None:
            raise RuntimeError("Risk analyzer module not initialized")
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
    backtest_result: Dict[str, Any],
    include_monte_carlo: bool = True,
    include_var_analysis: bool = True,
    include_stress_test: bool = True,
    monte_carlo_sims: int = 5000,
    report_format: str = "summary",
) -> Dict[str, Any]:
    """Generate comprehensive risk assessment and recommendations"""
    try:
        if risk_analyzer is None:
            raise RuntimeError("Risk analyzer module not initialized")
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
    backtest_results: List[Dict[str, Any]],
    lookback_period: int = 60,
    correlation_threshold: float = 0.7,
    include_rolling: bool = True,
    rolling_window: int = 20,
    include_heatmap: bool = False,
) -> Dict[str, Any]:
    """Analyze cross-asset correlations and identify pairs trading opportunities"""
    try:
        if pairs_analyzer is None:
            raise RuntimeError("Pairs analyzer module not initialized")
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
    pair: Dict[str, Any],
    backtest_result_1: Dict[str, Any],
    backtest_result_2: Dict[str, Any],
    strategy: str = "mean_reversion",
    lookback_period: int = 60,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    position_size: float = 0.02,
    max_holding_days: int = 20,
) -> Dict[str, Any]:
    """Backtest pairs trading strategies"""
    try:
        if pairs_analyzer is None:
            raise RuntimeError("Pairs analyzer module not initialized")
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
    backtest_result: Dict[str, Any],
    factors: Optional[List[str]] = None,
    factor_returns: Optional[Dict[str, List[float]]] = None,
    include_residuals: bool = True,
    analysis_period: int = 252,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """Decompose returns into systematic factors"""
    try:
        if pairs_analyzer is None:
            raise RuntimeError("Pairs analyzer module not initialized")
        result = await pairs_analyzer.factor_analysis(
            backtest_result=backtest_result,
            factors=factors or [],
            factor_returns=factor_returns or {},
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
    backtest_results: List[Dict[str, Any]],
    lookback_period: int = 60,
    detection_method: str = "hmm",
    n_regimes: int = 3,
    include_transitions: bool = True,
    include_forecast: bool = True,
) -> Dict[str, Any]:
    """Identify market regimes and transitions"""
    try:
        if pairs_analyzer is None:
            raise RuntimeError("Pairs analyzer module not initialized")
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
def cache_stats() -> Dict[str, Any]:
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
def cache_clear(cache_name: Optional[str] = None) -> Dict[str, Any]:
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


@mcp.tool
def backtest_benchmark(
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
    from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

    try:
        client = get_jesse_rest_client()
        if client is None:
            return {"error": "Jesse REST client not available"}

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Calculate expected candles
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

        # Run backtest with timing
        start_time = time.time()
        routes = [{"strategy": "SMACrossover", "symbol": symbol, "timeframe": timeframe}]
        result = client.backtest(
            routes=routes,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            exchange=exchange,
            exchange_type="spot" if "Spot" in exchange else "futures",
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # Calculate performance metrics
        if execution_time > 0:
            candles_per_second = total_candles / execution_time
            candles_per_minute = candles_per_second * 60
        else:
            candles_per_second = 0
            candles_per_minute = 0

        # Extract backtest status
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

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


# ==================== LIVE TRADING TOOLS (Phase 6) ====================


@mcp.tool
def live_check_plugin() -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
        from jesse_mcp.core.strategy_validation.certification import (
            get_strategy_certification,
            CERTIFICATION_MIN_TESTS,
            CERTIFICATION_PASS_RATE,
        )

        logger.info(PAPER_TRADING_INFO)

        _initialize_dependencies()
        import os

        if jesse is None:
            return {"error": "Jesse framework not initialized"}

        strategies_path = getattr(jesse, "strategies_path", None)
        if not strategies_path:
            return {"error": "Strategies path not available"}

        cert_status = get_strategy_certification(strategy, strategies_path)

        if not cert_status.is_certified:
            if cert_status.test_count > 0:
                logger.warning(
                    f"⚠️  Paper trading with uncertified strategy '{strategy}': "
                    f"{cert_status.test_pass_count}/{cert_status.test_count} tests passed ({cert_status.pass_rate:.0%})"
                )
            else:
                logger.warning(
                    f"⚠️  Paper trading with untested strategy '{strategy}'. "
                    f"Recommend testing with backtests first."
                )

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
        if not cert_status.is_certified:
            if cert_status.test_count > 0:
                result["warning"] = (
                    f"Strategy '{strategy}' not certified: "
                    f"{cert_status.test_pass_count}/{cert_status.test_count} tests ({cert_status.pass_rate:.0%}). "
                    f"Need {CERTIFICATION_MIN_TESTS - cert_status.test_count} more tests at {CERTIFICATION_PASS_RATE:.0%}+ pass rate."
                )
            else:
                result["warning"] = (
                    f"Strategy '{strategy}' has no recorded backtests. "
                    f"Backtest recommended before paper trading."
                )
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
) -> Dict[str, Any]:
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

        _initialize_dependencies()
        import os

        if jesse is None:
            return {"error": "Jesse framework not initialized", "status": "failed"}

        strategies_path = getattr(jesse, "strategies_path", None)
        if not strategies_path:
            return {"error": "Strategies path not available", "status": "failed"}

        from jesse_mcp.core.strategy_validation.certification import (
            check_live_trading_allowed,
            CERTIFICATION_MIN_TESTS,
            CERTIFICATION_PASS_RATE,
        )

        check_result = check_live_trading_allowed(strategy, strategies_path)

        if not check_result["allowed"]:
            status = check_result["status"]
            return {
                "error": f"Cannot start live trading: Strategy '{strategy}' is not certified",
                "status": "blocked",
                "reason": check_result["reason"],
                "certification": {
                    "is_certified": status.is_certified,
                    "test_count": status.test_count,
                    "test_pass_count": status.test_pass_count,
                    "pass_rate": status.pass_rate,
                    "min_tests_required": CERTIFICATION_MIN_TESTS,
                    "min_pass_rate_required": CERTIFICATION_PASS_RATE,
                },
                "recommendation": check_result["recommendation"],
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
def live_cancel_session(session_id: str, paper_mode: bool = True) -> Dict[str, Any]:
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
def live_get_sessions(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
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
def live_get_status(session_id: str) -> Dict[str, Any]:
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
def live_get_orders(session_id: str) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
def live_get_logs(session_id: str, log_type: str = "all") -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
def paper_stop(session_id: str) -> Dict[str, Any]:
    """
    Stop a paper trading session and return final metrics.

    Args:
        session_id: Session ID to stop

    Returns:
        Dict with stopped_at, duration, and final_metrics
    """
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

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
def paper_status(session_id: str) -> Dict[str, Any]:
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
def paper_get_trades(session_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
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
def paper_get_equity(session_id: str, resolution: str = "1h") -> Dict[str, Any]:
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
def paper_get_metrics(session_id: str) -> Dict[str, Any]:
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
def paper_list_sessions() -> Dict[str, Any]:
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
def paper_update_session(session_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
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
