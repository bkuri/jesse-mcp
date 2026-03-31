"""
Phase 7: Strategy Creation & Management Tools

Iterative strategy refinement (Ralph Wiggum Loop) with async job support,
strategy metadata, cache management, and rate limiting.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from jesse_mcp.core.strategy_validation.metadata import (
    CERTIFICATION_MIN_TESTS,
    CERTIFICATION_PASS_RATE,
    get_or_create_metadata,
    load_metadata,
    save_metadata,
)
from jesse_mcp.tools._utils import (
    get_strategies_path,
    require_jesse,
    tool_error_handler,
)

logger = logging.getLogger("jesse-mcp.strategy")


def _strategy_create_impl(
    name: str,
    description: str,
    indicators: Optional[List[str]] = None,
    strategy_type: str = "trend_following",
    risk_per_trade: float = 0.02,
    timeframe: str = "1h",
    max_iterations: int = 5,
    overwrite: bool = False,
    skip_backtest: bool = False,
    progress_callback: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Internal implementation for strategy creation with iterative refinement.
    """
    from jesse_mcp.core.job_manager import JobStatus, get_job_manager
    from jesse_mcp.core.strategy_builder import StrategySpec, get_strategy_builder
    from jesse_mcp.core.strategy_validator import get_validator
    import os

    try:
        strategies_path = get_strategies_path()

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
                {
                    "iteration": h["iteration"],
                    "passed": h["result"].get("passed", False),
                }
                for h in history
            ],
            "path": strategy_file if success else None,
            "code": final_code,
            "ready_for_backtest": success,
        }

    except Exception as e:
        logger.error(f"Strategy creation failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__, "status": "failed"}


def register_strategy_tools(mcp):
    """Register strategy creation and management tools with the MCP server."""

    @mcp.tool(name="strategy_create")
    @tool_error_handler
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
        skip_backtest: bool = False,
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
            skip_backtest: Skip dry-run backtest validation (default: False)

        Returns:
            Dict with status, name, iterations, validation_history, path, code, ready_for_backtest
        """
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

        import threading

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

    @mcp.tool(name="strategy_create_status")
    @tool_error_handler
    def strategy_create_status(job_id: str) -> Dict[str, Any]:
        """
        Poll async job progress for strategy creation.

        Args:
            job_id: Job identifier from strategy_create

        Returns:
            Dict with job_id, status, progress_percent, current_step,
            iterations_completed, iterations_total, elapsed_seconds, result (when complete)
        """
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

    @mcp.tool(name="strategy_create_cancel")
    @tool_error_handler
    def strategy_create_cancel(job_id: str) -> Dict[str, Any]:
        """
        Cancel async strategy creation job.

        Args:
            job_id: Job identifier to cancel

        Returns:
            Dict with status, job_id
        """
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

    @mcp.tool(name="strategy_refine")
    @tool_error_handler
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
        import os

        from jesse_mcp.core.strategy_builder import get_strategy_builder
        from jesse_mcp.core.strategy_validator import get_validator

        strategies_path = get_strategies_path()

        strategy_dir = os.path.join(strategies_path, name)
        strategy_file = os.path.join(strategy_dir, "__init__.py")

        if not os.path.exists(strategy_file):
            return {
                "error": f"Strategy '{name}' not found",
                "status": "failed",
                "name": name,
            }

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

            current_code = builder.refine_from_validation(
                current_code, validation_result
            )

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

    @mcp.tool(name="strategy_delete")
    @tool_error_handler
    def strategy_delete(name: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Delete a strategy.

        Args:
            name: Strategy name to delete
            confirm: Must be True to actually delete (default: False)

        Returns:
            Dict with status, name
        """
        import os
        import shutil

        if not confirm:
            return {
                "status": "confirmation_required",
                "name": name,
                "message": "Set confirm=True to delete the strategy",
            }

        strategies_path = get_strategies_path()

        strategy_dir = os.path.join(strategies_path, name)

        if not os.path.exists(strategy_dir):
            return {
                "error": f"Strategy '{name}' not found",
                "status": "not_found",
                "name": name,
            }

        shutil.rmtree(strategy_dir)
        logger.info(f"✅ Strategy deleted: {strategy_dir}")

        return {"status": "deleted", "name": name}

    @mcp.tool(name="jobs_list")
    @tool_error_handler
    def jobs_list(job_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        List recent jobs.

        Args:
            job_type: Filter by job type (optional)
            limit: Maximum number of jobs to return (default: 50)

        Returns:
            Dict with list of jobs containing id, type, status, progress, current_step, started_at
        """
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
                    "started_at": (
                        job.started_at.isoformat() if job.started_at else None
                    ),
                }
                for job in jobs
            ],
            "count": len(jobs),
        }

    @mcp.tool(name="strategy_metadata")
    @tool_error_handler
    def strategy_metadata(name: str) -> Dict[str, Any]:
        """
        Get metadata and version info for a strategy.

        Args:
            name: Strategy name

        Returns:
            Dict with strategy metadata including version, test_count, test_pass_count,
            certified status, and certification thresholds
        """
        import os

        strategies_path = get_strategies_path()

        strategy_dir = os.path.join(strategies_path, name)
        if not os.path.exists(strategy_dir):
            return {
                "error": f"Strategy '{name}' not found",
                "status": "not_found",
                "name": name,
            }

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
                metadata.test_pass_count / metadata.test_count
                if metadata.test_count > 0
                else 0
            ),
        }
        result["status"] = "found"
        return result

    @mcp.tool(name="rate_limit_status")
    @tool_error_handler
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
        from jesse_mcp.core.rate_limiter import get_rate_limiter

        limiter = get_rate_limiter()
        return limiter.get_status()

    @mcp.tool(name="cache_stats")
    @tool_error_handler
    def cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics including hit/miss ratio and cache sizes.

        Returns:
            Dict with cache status, hit rates, and sizes for all caches
        """
        from jesse_mcp.core.cache import get_all_stats

        return get_all_stats()

    @mcp.tool(name="cache_clear")
    @tool_error_handler
    def cache_clear(cache_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cache(s) to free memory or force fresh data.

        Args:
            cache_name: Specific cache to clear (strategy_list, backtest).
                       If None, clears all caches.

        Returns:
            Dict with number of entries cleared per cache
        """
        from jesse_mcp.core.cache import clear_all_caches, clear_cache

        if cache_name:
            count = clear_cache(cache_name)
            return {"cleared": {cache_name: count}}
        else:
            return {"cleared": clear_all_caches()}
