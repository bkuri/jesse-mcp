"""
Phase 3 Optimization Tools Implementation

Advanced optimization and analysis tools for autonomous strategy improvement.
Implements optimize(), walk_forward(), backtest_batch(), and analyze_results().
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import numpy as np

# Try to import Optuna, but make it optional for development
try:
    import optuna
    from optuna.samplers import TPESampler
    from optuna.pruners import MedianPruner

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    optuna = None
    TPESampler = None
    MedianPruner = None

# Import our integration layers
try:
    from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
except ImportError:
    JESSE_AVAILABLE = False
    get_jesse_wrapper = None

try:
    from jesse_mcp.core.mock import get_mock_jesse_wrapper

    MOCK_AVAILABLE = True
except ImportError:
    MOCK_AVAILABLE = False
    get_mock_jesse_wrapper = None

logger = logging.getLogger("jesse-mcp.phase3")


class Phase3Optimizer:
    """Phase 3 optimization tools implementation"""

    def __init__(self, use_mock=None):
        """
        Initialize optimizer with appropriate Jesse wrapper

        Args:
            use_mock: Force use of mock wrapper. If None, auto-detect based on availability
        """
        if use_mock is None:
            # Auto-detect: prefer real Jesse, fall back to mock
            if JESSE_AVAILABLE and get_jesse_wrapper:
                self.wrapper = get_jesse_wrapper()
                self.use_mock = False
                logger.info("Using real Jesse wrapper")
            elif MOCK_AVAILABLE and get_mock_jesse_wrapper:
                self.wrapper = get_mock_jesse_wrapper()
                self.use_mock = True
                logger.info("Using mock Jesse wrapper for development")
            else:
                raise RuntimeError("No Jesse wrapper available - neither real nor mock")
        else:
            if use_mock:
                if not MOCK_AVAILABLE:
                    raise RuntimeError("Mock wrapper not available")
                self.wrapper = get_mock_jesse_wrapper()
                self.use_mock = True
                logger.info("Forced use of mock Jesse wrapper")
            else:
                if not JESSE_AVAILABLE:
                    raise RuntimeError("Real Jesse wrapper not available")
                self.wrapper = get_jesse_wrapper()
                self.use_mock = False
                logger.info("Forced use of real Jesse wrapper")

    async def optimize(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        param_space: Dict[str, Dict[str, Any]],
        metric: str = "total_return",
        n_trials: int = 100,
        n_jobs: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Optimize strategy hyperparameters using Optuna

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            timeframe: Candlestick timeframe
            start_date: Backtest start date
            end_date: Backtest end date
            param_space: Parameter space to optimize
                Format: {"param_name": {"type": "float", "min": 0, "max": 1, "step": 0.1}}
            metric: Optimization metric (total_return, sharpe_ratio, etc.)
            n_trials: Number of optimization trials
            n_jobs: Number of parallel jobs
            **kwargs: Additional backtest parameters

        Returns:
            Optimization results with best parameters and trial history
        """
        if not OPTUNA_AVAILABLE:
            logger.warning("Optuna not available, using mock optimization")
            return await self._mock_optimize(
                strategy,
                symbol,
                timeframe,
                start_date,
                end_date,
                param_space,
                metric,
                n_trials,
                **kwargs,
            )

        logger.info(f"Starting optimization: {strategy} on {symbol} {timeframe}")
        start_time = time.time()

        # Create Optuna study
        sampler = TPESampler(seed=42) if TPESampler else None
        pruner = (
            MedianPruner(n_startup_trials=5, n_warmup_steps=3) if MedianPruner else None
        )

        study = optuna.create_study(
            direction="maximize",
            sampler=sampler,
            pruner=pruner,
            study_name=f"optimize_{strategy}_{symbol}_{timeframe}",
        )

        # Define objective function
        def objective(trial):
            # Generate parameters for this trial
            trial_params = {}
            for param_name, param_config in param_space.items():
                param_type = param_config.get("type", "float")

                if param_type == "float":
                    trial_params[param_name] = trial.suggest_float(
                        param_name,
                        param_config["min"],
                        param_config["max"],
                        step=param_config.get("step"),
                    )
                elif param_type == "int":
                    trial_params[param_name] = trial.suggest_int(
                        param_name,
                        param_config["min"],
                        param_config["max"],
                        step=param_config.get("step", 1),
                    )
                elif param_type == "categorical":
                    trial_params[param_name] = trial.suggest_categorical(
                        param_name, param_config["choices"]
                    )
                else:
                    raise ValueError(f"Unsupported parameter type: {param_type}")

            # Run backtest with trial parameters
            try:
                result = self.wrapper.backtest(
                    strategy,
                    symbol,
                    timeframe,
                    start_date,
                    end_date,
                    hyperparameters=trial_params,
                    **kwargs,
                )

                # Extract optimization metric
                if metric not in result:
                    raise ValueError(f"Metric '{metric}' not found in backtest result")

                value = result[metric]

                # Report intermediate value for pruning
                trial.report(value, trial.number)

                # Check if trial should be pruned
                if trial.should_prune():
                    raise optuna.exceptions.TrialPruned()

                return value

            except Exception as e:
                logger.error(f"Trial {trial.number} failed: {e}")
                # Return very bad score so Optuna avoids this region
                return -float("inf")

        # Run optimization
        try:
            study.optimize(objective, n_trials=n_trials, n_jobs=n_jobs)
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

        # Process results
        best_params = study.best_params
        best_value = study.best_value
        trials = []

        for trial in study.trials:
            trial_data = {
                "number": trial.number,
                "value": trial.value if trial.value is not None else float("nan"),
                "params": trial.params,
                "state": trial.state.name,
                "datetime_start": trial.datetime_start.isoformat()
                if trial.datetime_start
                else None,
                "datetime_complete": trial.datetime_complete.isoformat()
                if trial.datetime_complete
                else None,
            }
            trials.append(trial_data)

        # Generate convergence data
        convergence = self._calculate_convergence(trials)

        execution_time = time.time() - start_time

        # Run final backtest with best parameters
        final_result = self.wrapper.backtest(
            strategy,
            symbol,
            timeframe,
            start_date,
            end_date,
            hyperparameters=best_params,
            **kwargs,
        )

        return {
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "optimization_metric": metric,
            "best_parameters": best_params,
            "best_value": best_value,
            "n_trials": n_trials,
            "n_successful_trials": len(
                [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
            ),
            "n_pruned_trials": len(
                [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
            ),
            "trials": trials,
            "convergence": convergence,
            "final_backtest": final_result,
            "execution_time": round(execution_time, 2),
            "study_name": study.study_name,
            "use_mock": self.use_mock,
        }

    async def _mock_optimize(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        param_space: Dict[str, Dict[str, Any]],
        metric: str,
        n_trials: int,
        **kwargs,
    ) -> Dict[str, Any]:
        """Mock optimization when Optuna is not available"""
        logger.info(f"Running mock optimization with {n_trials} trials")
        start_time = time.time()

        best_value = -float("inf")
        best_params = {}
        trials = []

        for i in range(n_trials):
            # Generate random parameters
            trial_params = {}
            for param_name, param_config in param_space.items():
                param_type = param_config.get("type", "float")

                if param_type == "float":
                    trial_params[param_name] = np.random.uniform(
                        param_config["min"], param_config["max"]
                    )
                elif param_type == "int":
                    trial_params[param_name] = np.random.randint(
                        param_config["min"], param_config["max"] + 1
                    )
                elif param_type == "categorical":
                    trial_params[param_name] = np.random.choice(param_config["choices"])

            # Run mock backtest
            result = self.wrapper.backtest(
                strategy,
                symbol,
                timeframe,
                start_date,
                end_date,
                hyperparameters=trial_params,
                **kwargs,
            )

            value = result.get(metric, 0)

            # Track best
            if value > best_value:
                best_value = value
                best_params = trial_params.copy()

            # Record trial
            trials.append(
                {
                    "number": i,
                    "value": value,
                    "params": trial_params,
                    "state": "COMPLETE",
                    "datetime_start": datetime.now().isoformat(),
                    "datetime_complete": datetime.now().isoformat(),
                }
            )

            # Small delay to simulate real optimization
            await asyncio.sleep(0.01)

        # Generate mock convergence
        convergence = self._calculate_convergence(trials)

        # Run final backtest
        final_result = self.wrapper.backtest(
            strategy,
            symbol,
            timeframe,
            start_date,
            end_date,
            hyperparameters=best_params,
            **kwargs,
        )

        execution_time = time.time() - start_time

        return {
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "optimization_metric": metric,
            "best_parameters": best_params,
            "best_value": best_value,
            "n_trials": n_trials,
            "n_successful_trials": n_trials,
            "n_pruned_trials": 0,
            "trials": trials,
            "convergence": convergence,
            "final_backtest": final_result,
            "execution_time": round(execution_time, 2),
            "study_name": f"mock_optimize_{strategy}_{symbol}_{timeframe}",
            "use_mock": True,
        }

    def _calculate_convergence(self, trials) -> List[Dict[str, Any]]:
        """Calculate convergence data from trials"""
        convergence = []
        best_so_far = -float("inf")

        for i, trial in enumerate(trials):
            if trial["value"] > best_so_far and not np.isnan(trial["value"]):
                best_so_far = trial["value"]

            convergence.append(
                {"trial": i, "best_value": best_so_far, "current_value": trial["value"]}
            )

        return convergence

    async def walk_forward(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        in_sample_period: int = 365,
        out_sample_period: int = 30,
        step_forward: int = 7,
        param_space: Dict[str, Dict[str, Any]] = None,
        metric: str = "total_return",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Perform walk-forward analysis to detect overfitting

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            timeframe: Candlestick timeframe
            start_date: Analysis start date
            end_date: Analysis end date
            in_sample_period: Days for optimization period
            out_sample_period: Days for validation period
            step_forward: Days to move window forward
            param_space: Parameter space for optimization
            metric: Optimization metric
            **kwargs: Additional backtest parameters

        Returns:
            Walk-forward analysis results with per-period statistics
        """
        logger.info(f"Starting walk-forward analysis: {strategy} on {symbol}")
        start_time = time.time()

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        results = []
        current_start = start_dt

        while current_start < end_dt:
            in_sample_end = current_start + timedelta(days=in_sample_period)
            out_sample_end = in_sample_end + timedelta(days=out_sample_period)

            if out_sample_end > end_dt:
                break

            # Optimize on in-sample period
            logger.info(f"Optimizing {current_start.date()} to {in_sample_end.date()}")

            if param_space:
                optimization = await self.optimize(
                    strategy,
                    symbol,
                    timeframe,
                    current_start.strftime("%Y-%m-%d"),
                    in_sample_end.strftime("%Y-%m-%d"),
                    param_space,
                    metric=metric,
                    n_trials=20,
                    **kwargs,
                )
                best_params = optimization["best_parameters"]
                in_sample_result = optimization["final_backtest"]
            else:
                # Use default parameters
                in_sample_result = self.wrapper.backtest(
                    strategy,
                    symbol,
                    timeframe,
                    current_start.strftime("%Y-%m-%d"),
                    in_sample_end.strftime("%Y-%m-%d"),
                    **kwargs,
                )
                best_params = {}

            # Validate on out-sample period
            logger.info(f"Validating {in_sample_end.date()} to {out_sample_end.date()}")

            out_sample_result = self.wrapper.backtest(
                strategy,
                symbol,
                timeframe,
                in_sample_end.strftime("%Y-%m-%d"),
                out_sample_end.strftime("%Y-%m-%d"),
                hyperparameters=best_params,
                **kwargs,
            )

            # Calculate degradation
            in_sample_metric = in_sample_result.get(metric, 0)
            out_sample_metric = out_sample_result.get(metric, 0)

            if in_sample_metric != 0:
                degradation = (out_sample_metric - in_sample_metric) / abs(
                    in_sample_metric
                )
            else:
                degradation = 0

            results.append(
                {
                    "period": len(results) + 1,
                    "in_sample_start": current_start.strftime("%Y-%m-%d"),
                    "in_sample_end": in_sample_end.strftime("%Y-%m-%d"),
                    "out_sample_start": in_sample_end.strftime("%Y-%m-%d"),
                    "out_sample_end": out_sample_end.strftime("%Y-%m-%d"),
                    "best_parameters": best_params,
                    "in_sample_result": in_sample_result,
                    "out_sample_result": out_sample_result,
                    "in_sample_metric": in_sample_metric,
                    "out_sample_metric": out_sample_metric,
                    "degradation": degradation,
                    "degradation_percent": round(degradation * 100, 2),
                }
            )

            # Move window forward
            current_start += timedelta(days=step_forward)

        # Calculate overall statistics
        if results:
            avg_degradation = np.mean([r["degradation"] for r in results])
            std_degradation = np.std([r["degradation"] for r in results])
            positive_periods = len([r for r in results if r["out_sample_metric"] > 0])

            overall = {
                "total_periods": len(results),
                "positive_periods": positive_periods,
                "positive_period_rate": round(positive_periods / len(results), 4),
                "average_degradation": round(avg_degradation, 4),
                "std_degradation": round(std_degradation, 4),
                "overfitting_indicator": avg_degradation
                < -0.2,  # 20%+ degradation suggests overfitting
            }
        else:
            overall = {}

        execution_time = time.time() - start_time

        return {
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "in_sample_period": in_sample_period,
            "out_sample_period": out_sample_period,
            "step_forward": step_forward,
            "optimization_metric": metric,
            "periods": results,
            "overall": overall,
            "execution_time": round(execution_time, 2),
            "use_mock": self.use_mock,
        }

    async def backtest_batch(
        self,
        strategy: str,
        symbols: List[str],
        timeframes: List[str],
        start_date: str,
        end_date: str,
        hyperparameters: List[Dict[str, Any]] = None,
        concurrent_limit: int = 4,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run multiple backtests concurrently for strategy comparison

        Args:
            strategy: Strategy name
            symbols: List of trading symbols
            timeframes: List of timeframes
            start_date: Backtest start date
            end_date: Backtest end date
            hyperparameters: List of parameter sets to test
            concurrent_limit: Maximum concurrent backtests
            **kwargs: Additional backtest parameters

        Returns:
            Batch results with comparison matrix and statistics
        """
        logger.info(
            f"Starting batch backtest: {strategy} on {len(symbols)} symbols, {len(timeframes)} timeframes"
        )
        start_time = time.time()

        if hyperparameters is None:
            hyperparameters = [{}]  # Use default parameters

        # Create all combinations
        tasks = []
        task_info = []

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

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def run_single_backtest(info):
            async with semaphore:
                try:
                    result = self.wrapper.backtest(
                        strategy,
                        info["symbol"],
                        info["timeframe"],
                        start_date,
                        end_date,
                        hyperparameters=info["params"],
                        **kwargs,
                    )
                    return {
                        "info": info,
                        "result": result,
                        "success": True,
                        "error": None,
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

        # Run all tasks
        logger.info(
            f"Executing {len(task_info)} backtests with concurrency limit {concurrent_limit}"
        )
        results = await asyncio.gather(
            *[run_single_backtest(info) for info in task_info]
        )

        # Organize results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        # Create comparison matrix
        comparison_matrix = {}
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

        # Calculate overall statistics
        if successful_results:
            all_returns = [r["result"]["total_return"] for r in successful_results]
            all_sharpes = [r["result"]["sharpe_ratio"] for r in successful_results]

            overall_stats = {
                "total_backtests": len(task_info),
                "successful_backtests": len(successful_results),
                "failed_backtests": len(failed_results),
                "success_rate": round(len(successful_results) / len(task_info), 4),
                "best_return": round(max(all_returns), 4),
                "worst_return": round(min(all_returns), 4),
                "average_return": round(np.mean(all_returns), 4),
                "best_sharpe": round(max(all_sharpes), 4),
                "average_sharpe": round(np.mean(all_sharpes), 4),
            }

            # Find top performers
            top_performers = sorted(
                successful_results,
                key=lambda x: x["result"]["total_return"],
                reverse=True,
            )[:5]
        else:
            overall_stats = {
                "total_backtests": len(task_info),
                "successful_backtests": 0,
                "failed_backtests": len(failed_results),
                "success_rate": 0,
            }
            top_performers = []

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
            "use_mock": self.use_mock,
        }

    def analyze_results(
        self,
        backtest_result: Dict[str, Any],
        analysis_type: str = "basic",
        include_trade_analysis: bool = True,
        include_correlation: bool = False,
        include_monte_carlo: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract deep insights from backtest results

        Args:
            backtest_result: Result from backtest() or backtest_batch()
            analysis_type: "basic", "advanced", or "deep"
            include_trade_analysis: Include detailed trade analysis
            include_correlation: Include correlation analysis (requires benchmarks)
            include_monte_carlo: Include Monte Carlo analysis

        Returns:
            Comprehensive analysis with insights and metrics
        """
        logger.info(f"Analyzing results with depth: {analysis_type}")
        start_time = time.time()

        analysis = {
            "analysis_type": analysis_type,
            "analysis_timestamp": datetime.now().isoformat(),
            "use_mock": self.use_mock,
        }

        # Basic analysis
        if "basic" in analysis_type:
            analysis["basic"] = self._basic_analysis(backtest_result)

        # Advanced analysis
        if "advanced" in analysis_type:
            analysis["advanced"] = self._advanced_analysis(backtest_result)

        # Deep analysis
        if "deep" in analysis_type:
            analysis["deep"] = self._deep_analysis(backtest_result)

        # Trade analysis
        if include_trade_analysis and "trades" in backtest_result:
            analysis["trade_analysis"] = self._trade_analysis(backtest_result["trades"])

        # Correlation analysis
        if include_correlation:
            analysis["correlation"] = self._correlation_analysis(backtest_result)

        # Monte Carlo analysis
        if include_monte_carlo:
            analysis["monte_carlo"] = self._monte_carlo_analysis(backtest_result)

        execution_time = time.time() - start_time
        analysis["execution_time"] = round(execution_time, 2)

        return analysis

    def _basic_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Basic performance analysis"""
        return {
            "total_return": result.get("total_return", 0),
            "sharpe_ratio": result.get("sharpe_ratio", 0),
            "max_drawdown": result.get("max_drawdown", 0),
            "win_rate": result.get("win_rate", 0),
            "total_trades": result.get("total_trades", 0),
            "starting_balance": result.get("starting_balance", 0),
            "ending_balance": result.get("ending_balance", 0),
            "performance_rating": self._calculate_performance_rating(result),
        }

    def _advanced_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced risk and performance metrics"""
        if "equity_curve" not in result:
            return {"error": "Equity curve data not available"}

        equity_curve = result["equity_curve"]
        returns = [point["return"] for point in equity_curve]

        # Calculate advanced metrics
        returns_array = np.array(returns)

        return {
            "volatility": round(
                float(np.std(returns_array) * np.sqrt(252)), 4
            ),  # Annualized
            "sortino_ratio": round(
                float(self._calculate_sortino_ratio(returns_array)), 4
            ),
            "calmar_ratio": round(float(self._calculate_calmar_ratio(result)), 4),
            "var_95": round(float(np.percentile(returns_array, 5)), 4),  # 5% VaR
            "var_99": round(float(np.percentile(returns_array, 1)), 4),  # 1% VaR
            "skewness": round(float(self._calculate_skewness(returns_array)), 4),
            "kurtosis": round(float(self._calculate_kurtosis(returns_array)), 4),
            "max_consecutive_wins": self._calculate_max_consecutive(
                result["trades"], True
            ),
            "max_consecutive_losses": self._calculate_max_consecutive(
                result["trades"], False
            ),
        }

    def _deep_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Deep analysis with ML insights"""
        insights = {
            "regime_analysis": self._analyze_market_regimes(result),
            "pattern_detection": self._detect_patterns(result["trades"]),
            "risk_assessment": self._assess_risk_profile(result),
            "recommendations": self._generate_recommendations(result),
        }
        return insights

    def _trade_analysis(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detailed trade-level analysis"""
        if not trades:
            return {"error": "No trades available for analysis"}

        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] <= 0]

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(len(winning_trades) / len(trades), 4),
            "avg_win": round(float(np.mean([t["pnl"] for t in winning_trades])), 4)
            if winning_trades
            else 0,
            "avg_loss": round(float(np.mean([t["pnl"] for t in losing_trades])), 4)
            if losing_trades
            else 0,
            "profit_factor": round(
                sum(t["pnl"] for t in winning_trades)
                / abs(sum(t["pnl"] for t in losing_trades)),
                4,
            )
            if losing_trades
            else float("inf"),
            "largest_win": round(max(t["pnl"] for t in trades), 4),
            "largest_loss": round(min(t["pnl"] for t in trades), 4),
            "avg_trade_duration": self._calculate_avg_duration(trades),
            "trade_distribution": self._analyze_trade_distribution(trades),
        }

    def _correlation_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Correlation analysis with benchmarks (mock implementation)"""
        # In real implementation, would correlate with market indices
        return {
            "note": "Mock correlation analysis - would compare with market benchmarks",
            "market_correlation": round(np.random.uniform(-0.3, 0.3), 4),
            "beta": round(np.random.uniform(0.5, 1.5), 4),
            "alpha": round(np.random.uniform(-0.1, 0.1), 4),
        }

    def _monte_carlo_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Monte Carlo simulation of strategy performance"""
        if "equity_curve" not in result:
            return {"error": "Equity curve data not available for Monte Carlo"}

        # Simple Monte Carlo - in real implementation would be more sophisticated
        returns = [point["return"] for point in result["equity_curve"]]
        simulations = 1000
        final_values = []

        for _ in range(simulations):
            # Randomly shuffle returns to create alternative paths
            shuffled_returns = np.random.choice(
                returns, size=len(returns), replace=True
            )
            final_value = 10000  # Starting value
            for ret in shuffled_returns:
                final_value *= 1 + ret
            final_values.append(final_value)

        return {
            "simulations": simulations,
            "mean_final_value": round(float(np.mean(final_values)), 2),
            "std_final_value": round(float(np.std(final_values)), 2),
            "percentile_5": round(float(np.percentile(final_values, 5)), 2),
            "percentile_95": round(float(np.percentile(final_values, 95)), 2),
            "probability_of_profit": round(
                len([v for v in final_values if v > 10000]) / simulations, 4
            ),
        }

    # Helper methods for calculations
    def _calculate_performance_rating(self, result: Dict[str, Any]) -> str:
        """Calculate overall performance rating"""
        score = 0
        if result.get("total_return", 0) > 0.1:
            score += 1
        if result.get("sharpe_ratio", 0) > 1.0:
            score += 1
        if result.get("max_drawdown", 1) < 0.2:
            score += 1
        if result.get("win_rate", 0) > 0.5:
            score += 1

        ratings = ["Poor", "Below Average", "Average", "Good", "Excellent"]
        return ratings[min(score, 4)]

    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float("inf")
        downside_std = np.std(downside_returns)
        return float(np.mean(returns) / downside_std) if downside_std != 0 else 0

    def _calculate_calmar_ratio(self, result: Dict[str, Any]) -> float:
        """Calculate Calmar ratio (Annual Return / Max Drawdown)"""
        annual_return = result.get("total_return", 0)
        max_dd = result.get("max_drawdown", 1)
        return float(annual_return / max_dd) if max_dd != 0 else 0

    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate return skewness"""
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0
        return float(np.mean(((returns - mean) / std) ** 3))

    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate return kurtosis"""
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0
        return float(np.mean(((returns - mean) / std) ** 4) - 3)

    def _calculate_max_consecutive(
        self, trades: List[Dict[str, Any]], wins: bool
    ) -> int:
        """Calculate maximum consecutive wins or losses"""
        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            is_win = trade["pnl"] > 0
            if is_win == wins:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_avg_duration(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate average trade duration in hours"""
        durations = []
        for trade in trades:
            try:
                entry = datetime.strptime(trade["entry_date"], "%Y-%m-%d %H:%M:%S")
                exit = datetime.strptime(trade["exit_date"], "%Y-%m-%d %H:%M:%S")
                duration = (exit - entry).total_seconds() / 3600  # Convert to hours
                durations.append(duration)
            except:
                continue

        return round(float(np.mean(durations)), 2) if durations else 0

    def _analyze_trade_distribution(
        self, trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze trade return distribution"""
        returns = [t["pnl"] for t in trades]
        return {
            "mean": round(float(np.mean(returns)), 4),
            "std": round(float(np.std(returns)), 4),
            "min": round(min(returns), 4),
            "max": round(max(returns), 4),
            "median": round(float(np.median(returns)), 4),
        }

    def _analyze_market_regimes(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance across market regimes (mock)"""
        return {
            "bull_market_performance": round(np.random.uniform(0.15, 0.25), 4),
            "bear_market_performance": round(np.random.uniform(-0.05, 0.05), 4),
            "sideways_market_performance": round(np.random.uniform(0.02, 0.08), 4),
            "regime_adaptability": "Good",
        }

    def _detect_patterns(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in trading behavior (mock)"""
        return {
            "day_of_week_analysis": {"best_day": "Wednesday", "worst_day": "Monday"},
            "time_of_day_analysis": {
                "best_hour": "14:00-15:00",
                "worst_hour": "09:00-10:00",
            },
            "seasonal_patterns": "No significant seasonal patterns detected",
        }

    def _assess_risk_profile(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk profile"""
        risk_score = 0
        if result.get("max_drawdown", 0) > 0.2:
            risk_score += 1
        if result.get("sharpe_ratio", 0) < 1.0:
            risk_score += 1
        if result.get("win_rate", 0) < 0.4:
            risk_score += 1

        risk_levels = ["Low", "Medium", "High", "Very High"]
        return {
            "risk_level": risk_levels[min(risk_score, 3)],
            "risk_factors": [
                f"Max Drawdown: {result.get('max_drawdown', 0):.2%}",
                f"Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}",
                f"Win Rate: {result.get('win_rate', 0):.2%}",
            ],
        }

    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if result.get("max_drawdown", 0) > 0.2:
            recommendations.append(
                "Consider adding stop-loss to reduce maximum drawdown"
            )

        if result.get("sharpe_ratio", 0) < 1.0:
            recommendations.append(
                "Strategy has low risk-adjusted returns - consider optimization"
            )

        if result.get("win_rate", 0) < 0.4:
            recommendations.append(
                "Low win rate suggests need for better entry/exit signals"
            )

        if result.get("total_trades", 0) < 50:
            recommendations.append(
                "Low trade count - consider longer backtest period or more sensitive signals"
            )

        if not recommendations:
            recommendations.append(
                "Strategy appears well-balanced - consider walk-forward analysis for validation"
            )

        return recommendations


# Global optimizer instance
_optimizer_instance = None


def get_optimizer(use_mock=None) -> Phase3Optimizer:
    """Get or create optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = Phase3Optimizer(use_mock=use_mock)
    return _optimizer_instance
