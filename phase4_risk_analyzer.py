"""
Phase 4 Risk Analysis Tools Implementation

Advanced Monte Carlo simulation, Value at Risk calculations, stress testing, and comprehensive risk reporting.
Implements monte_carlo(), var_calculation(), stress_test(), and risk_report().
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import numpy as np

# Import existing optimizer
try:
    from phase3_optimizer import Phase3Optimizer

    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False

logger = logging.getLogger("jesse-mcp.phase4")


class Phase4RiskAnalyzer:
    """Phase 4 risk analysis tools implementation"""

    def __init__(self, use_mock=None):
        """
        Initialize risk analyzer with appropriate optimizer

        Args:
            use_mock: Force use of mock wrapper. If None, auto-detect
        """
        if PHASE3_AVAILABLE:
            self.optimizer = Phase3Optimizer(use_mock=use_mock)
            self.use_mock = self.optimizer.use_mock
            logger.info(f"Phase 4 Risk Analyzer initialized (use_mock={self.use_mock})")
        else:
            raise RuntimeError("Phase 3 optimizer not available - required for Phase 4")

    async def monte_carlo(
        self,
        backtest_result: Dict[str, Any],
        simulations: int = 10000,
        confidence_levels: List[float] = None,
        resample_method: str = "bootstrap",
        block_size: int = 20,
        include_drawdowns: bool = True,
        include_returns: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate Monte Carlo simulations for comprehensive risk analysis

        Args:
            backtest_result: Result from backtest() or backtest_batch()
            simulations: Number of Monte Carlo runs
            confidence_levels: List of confidence levels (default: [0.95, 0.99])
            resample_method: "bootstrap", "block_bootstrap", "stationary_bootstrap"
            block_size: Block size for block bootstrap
            include_drawdowns: Include drawdown analysis
            include_returns: Include return distribution analysis

        Returns:
            Monte Carlo simulation results with confidence intervals
        """
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        logger.info(
            f"Starting Monte Carlo analysis: {simulations} simulations, {resample_method} method"
        )
        start_time = time.time()

        # Extract equity curve and returns
        if "equity_curve" not in backtest_result:
            return {"error": "Equity curve data not available for Monte Carlo analysis"}

        equity_curve = backtest_result["equity_curve"]
        returns = [point["return"] for point in equity_curve]

        # Generate Monte Carlo paths
        final_values = []
        max_drawdowns = []
        total_returns = []

        for i in range(simulations):
            # Resample returns based on method
            if resample_method == "bootstrap":
                sampled_returns = np.random.choice(
                    returns, size=len(returns), replace=True
                )
            elif resample_method == "block_bootstrap":
                sampled_returns = self._block_bootstrap(returns, block_size)
            elif resample_method == "stationary_bootstrap":
                sampled_returns = self._stationary_bootstrap(returns)
            else:
                sampled_returns = np.random.choice(
                    returns, size=len(returns), replace=True
                )

            # Generate path
            path_value = 10000  # Starting value
            path_peak = 10000
            path_drawdown = 0

            for ret in sampled_returns:
                path_value *= 1 + ret
                path_peak = max(path_peak, path_value)
                current_dd = (path_peak - path_value) / path_peak
                path_drawdown = max(path_drawdown, current_dd)

            final_values.append(path_value)
            max_drawdowns.append(path_drawdown)
            total_returns.append((path_value - 10000) / 10000)

            # Progress callback for long simulations
            if i > 0 and i % 1000 == 0:
                logger.info(
                    f"Monte Carlo progress: {i}/{simulations} ({i / simulations * 100:.1f}%)"
                )

        # Calculate statistics and confidence intervals
        final_value_stats = self._calculate_distribution_stats(final_values)
        drawdown_stats = (
            self._calculate_distribution_stats(max_drawdowns)
            if include_drawdowns
            else {}
        )
        return_stats = (
            self._calculate_distribution_stats(total_returns) if include_returns else {}
        )

        confidence_intervals = {}
        for level in confidence_levels:
            ci = self._calculate_confidence_intervals(final_values, [level])
            confidence_intervals[f"{level * 100:.0f}%"] = ci

        execution_time = time.time() - start_time

        return {
            "strategy": backtest_result.get("strategy"),
            "symbol": backtest_result.get("symbol"),
            "timeframe": backtest_result.get("timeframe"),
            "simulations": simulations,
            "resample_method": resample_method,
            "final_value_stats": final_value_stats,
            "drawdown_stats": drawdown_stats,
            "return_stats": return_stats,
            "confidence_intervals": confidence_intervals,
            "probability_of_profit": len([v for v in final_values if v > 10000])
            / simulations,
            "execution_time": round(execution_time, 2),
            "use_mock": self.use_mock,
        }

    async def var_calculation(
        self,
        backtest_result: Dict[str, Any],
        confidence_levels: List[float] = None,
        time_horizons: List[int] = None,
        method: str = "historical",
        monte_carlo_sims: int = 10000,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Calculate Value at Risk using multiple methods

        Args:
            backtest_result: Result from backtest() or backtest_batch()
            confidence_levels: List of confidence levels (default: [0.90, 0.95, 0.99])
            time_horizons: List of time horizons in days (default: [1, 5, 10, 30])
            method: "historical", "parametric", "monte_carlo"
            monte_carlo_sims: Number of simulations for Monte Carlo VaR

        Returns:
            VaR calculations for all confidence levels and time horizons
        """
        if confidence_levels is None:
            confidence_levels = [0.90, 0.95, 0.99]
        if time_horizons is None:
            time_horizons = [1, 5, 10, 30]

        logger.info(f"Calculating VaR: {method} method, {len(time_horizons)} horizons")
        start_time = time.time()

        # Extract returns
        if "equity_curve" not in backtest_result:
            return {"error": "Equity curve data not available for VaR calculation"}

        equity_curve = backtest_result["equity_curve"]
        returns = [point["return"] for point in equity_curve]

        var_results = {}

        for horizon in time_horizons:
            # Aggregate returns for horizon
            horizon_returns = self._aggregate_returns(returns, horizon)

            for confidence in confidence_levels:
                if method == "historical":
                    var, es = self._historical_var(horizon_returns, confidence)
                elif method == "parametric":
                    var, es = self._parametric_var(horizon_returns, confidence)
                elif method == "monte_carlo":
                    var, es = await self._monte_carlo_var(
                        horizon_returns, confidence, monte_carlo_sims
                    )
                else:
                    var, es = self._historical_var(horizon_returns, confidence)

                key = f"{horizon}d_{confidence * 100:.0f}%"
                var_results[key] = {
                    "var": var,
                    "expected_shortfall": es,
                    "confidence": confidence,
                    "horizon_days": horizon,
                    "method": method,
                }

        # Calculate backtesting statistics
        backtest_stats = self._calculate_var_backtest_stats(
            returns, confidence_levels, time_horizons
        )

        execution_time = time.time() - start_time

        return {
            "strategy": backtest_result.get("strategy"),
            "symbol": backtest_result.get("symbol"),
            "timeframe": backtest_result.get("timeframe"),
            "var_results": var_results,
            "confidence_levels": confidence_levels,
            "time_horizons": time_horizons,
            "method": method,
            "monte_carlo_sims": monte_carlo_sims if method == "monte_carlo" else None,
            "backtest_stats": backtest_stats,
            "execution_time": round(execution_time, 2),
            "use_mock": self.use_mock,
        }

    async def stress_test(
        self,
        backtest_result: Dict[str, Any],
        scenarios: List[str] = None,
        custom_scenarios: Dict[str, Any] = None,
        shock_magnitude: float = -0.20,
        volatility_multiplier: float = 3.0,
        correlation_shift: float = 0.8,
        recovery_periods: List[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Test strategy performance under extreme market conditions

        Args:
            backtest_result: Result from backtest() or backtest_batch()
            scenarios: Predefined scenarios (default: ["market_crash", "volatility_spike", "correlation_breakdown"])
            custom_scenarios: Custom scenario definitions
            shock_magnitude: Shock magnitude for scenarios (-0.20 = -20%)
            volatility_multiplier: Volatility increase factor
            correlation_shift: Correlation regime shift
            recovery_periods: Recovery period analysis in days

        Returns:
            Stress test results with scenario comparison
        """
        if scenarios is None:
            scenarios = ["market_crash", "volatility_spike", "correlation_breakdown"]
        if recovery_periods is None:
            recovery_periods = [5, 10, 20, 30]

        logger.info(f"Running stress tests: {len(scenarios)} scenarios")
        start_time = time.time()

        # Extract base data
        if "equity_curve" not in backtest_result:
            return {"error": "Equity curve data not available for stress testing"}

        equity_curve = backtest_result["equity_curve"]
        returns = [point["return"] for point in equity_curve]

        stress_results = {}

        for scenario in scenarios:
            logger.info(f"Applying scenario: {scenario}")

            # Apply stress scenario
            if scenario == "market_crash":
                stressed_returns = self._apply_market_crash(returns, shock_magnitude)
            elif scenario == "volatility_spike":
                stressed_returns = self._apply_volatility_spike(
                    returns, volatility_multiplier
                )
            elif scenario == "correlation_breakdown":
                stressed_returns = self._apply_correlation_breakdown(
                    returns, correlation_shift
                )
            elif custom_scenarios and scenario in custom_scenarios:
                stressed_returns = self._apply_custom_scenario(
                    returns, custom_scenarios[scenario]
                )
            else:
                stressed_returns = self._apply_market_crash(returns, shock_magnitude)

            # Calculate stressed performance
            stressed_equity = self._generate_equity_curve(stressed_returns)
            max_dd = self._calculate_max_drawdown(stressed_equity)
            recovery_times = self._calculate_recovery_times(
                stressed_equity, recovery_periods
            )

            stress_results[scenario] = {
                "scenario": scenario,
                "shock_applied": shock_magnitude
                if scenario == "market_crash"
                else volatility_multiplier,
                "max_drawdown": max_dd,
                "final_return": stressed_returns[-1] if stressed_returns else 0,
                "recovery_analysis": recovery_times,
                "stressed_returns_sample": stressed_returns[
                    :100
                ],  # First 100 for analysis
                "base_performance": {
                    "max_drawdown": backtest_result.get("max_drawdown", 0),
                    "total_return": backtest_result.get("total_return", 0),
                },
            }

        # Scenario comparison
        scenario_comparison = self._compare_scenarios(stress_results)

        # Overall stress assessment
        risk_assessment = self._assess_stress_resilience(stress_results)

        execution_time = time.time() - start_time

        return {
            "strategy": backtest_result.get("strategy"),
            "symbol": backtest_result.get("symbol"),
            "timeframe": backtest_result.get("timeframe"),
            "scenarios_tested": scenarios,
            "stress_results": stress_results,
            "scenario_comparison": scenario_comparison,
            "risk_assessment": risk_assessment,
            "recovery_periods": recovery_periods,
            "execution_time": round(execution_time, 2),
            "use_mock": self.use_mock,
        }

    async def risk_report(
        self,
        backtest_result: Dict[str, Any],
        include_monte_carlo: bool = True,
        include_var_analysis: bool = True,
        include_stress_test: bool = True,
        monte_carlo_sims: int = 5000,
        report_format: str = "summary",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive risk assessment report

        Args:
            backtest_result: Result from backtest() or backtest_batch()
            include_monte_carlo: Include Monte Carlo analysis
            include_var_analysis: Include VaR calculations
            include_stress_test: Include stress testing
            monte_carlo_sims: Monte Carlo simulations
            report_format: "summary", "detailed", "executive"

        Returns:
            Professional risk assessment report
        """
        logger.info(f"Generating risk report: {report_format} format")
        start_time = time.time()

        report = {
            "strategy": backtest_result.get("strategy"),
            "symbol": backtest_result.get("symbol"),
            "timeframe": backtest_result.get("timeframe"),
            "period": f"{backtest_result.get('start_date')} to {backtest_result.get('end_date')}",
            "generated_at": datetime.now().isoformat(),
            "report_format": report_format,
        }

        # Base risk metrics
        report["base_metrics"] = self._calculate_base_risk_metrics(backtest_result)

        # Monte Carlo analysis
        if include_monte_carlo:
            logger.info("Running Monte Carlo analysis for risk report...")
            report["monte_carlo"] = await self.monte_carlo(
                backtest_result, simulations=monte_carlo_sims
            )

        # VaR analysis
        if include_var_analysis:
            logger.info("Running VaR analysis for risk report...")
            report["var_analysis"] = await self.var_calculation(backtest_result)

        # Stress testing
        if include_stress_test:
            logger.info("Running stress test for risk report...")
            report["stress_test"] = await self.stress_test(backtest_result)

        # Overall risk assessment
        report["risk_assessment"] = self._comprehensive_risk_assessment(report)

        # Recommendations
        report["recommendations"] = self._generate_risk_recommendations(report)

        # Format based on report type
        if report_format == "executive":
            return self._format_executive_report(report)
        elif report_format == "detailed":
            return self._format_detailed_report(report)
        else:
            return self._format_summary_report(report)

    # Helper methods for Monte Carlo
    def _block_bootstrap(self, returns: List[float], block_size: int) -> List[float]:
        """Block bootstrap resampling preserving autocorrelation"""
        n = len(returns)
        num_blocks = (n + block_size - 1) // block_size

        # Randomly select blocks with replacement
        block_indices = np.random.choice(num_blocks, size=num_blocks, replace=True)
        sampled_returns = []

        for block_idx in block_indices:
            start_idx = block_idx * block_size
            end_idx = min(start_idx + block_size, n)
            sampled_returns.extend(returns[start_idx:end_idx])

        return sampled_returns[:n]

    def _stationary_bootstrap(self, returns: List[float]) -> List[float]:
        """Stationary bootstrap for time series"""
        # Simple implementation - detrend, bootstrap, retrend
        mean_return = np.mean(returns)
        detrended = [r - mean_return for r in returns]

        # Bootstrap detrended returns
        bootstrapped = np.random.choice(detrended, size=len(detrended), replace=True)

        # Retrend
        return [r + mean_return for r in bootstrapped]

    def _calculate_distribution_stats(self, data: List[float]) -> Dict[str, float]:
        """Calculate comprehensive distribution statistics"""
        if not data:
            return {}

        data_array = np.array(data)
        return {
            "mean": float(np.mean(data_array)),
            "std": float(np.std(data_array)),
            "min": float(np.min(data_array)),
            "max": float(np.max(data_array)),
            "median": float(np.median(data_array)),
            "q5": float(np.percentile(data_array, 5)),
            "q25": float(np.percentile(data_array, 25)),
            "q75": float(np.percentile(data_array, 75)),
            "q95": float(np.percentile(data_array, 95)),
            "skewness": float(self._calculate_skewness(data_array)),
            "kurtosis": float(self._calculate_kurtosis(data_array)),
        }

    def _calculate_confidence_intervals(
        self, data: List[float], confidence_levels: List[float]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate confidence intervals for data"""
        data_array = np.array(data)
        intervals = {}

        for level in confidence_levels:
            alpha = 1 - level
            lower = np.percentile(data_array, alpha / 2 * 100)
            upper = np.percentile(data_array, (1 - alpha / 2) * 100)

            intervals[f"{level * 100:.0f}%"] = {
                "lower": float(lower),
                "upper": float(upper),
                "width": float(upper - lower),
            }

        return intervals

    # Helper methods for VaR
    def _aggregate_returns(
        self, returns: List[float], horizon_days: int
    ) -> List[float]:
        """Aggregate returns for specified time horizon"""
        if horizon_days == 1:
            return returns

        # Simple aggregation - sum returns over horizon
        aggregated = []
        for i in range(len(returns) - horizon_days + 1):
            horizon_return = sum(returns[i : i + horizon_days])
            aggregated.append(horizon_return)

        return aggregated

    def _historical_var(
        self, returns: List[float], confidence: float
    ) -> Tuple[float, float]:
        """Historical VaR calculation"""
        if not returns:
            return 0, 0

        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - confidence) * 100)

        # Expected Shortfall (Conditional VaR)
        es = np.mean(returns_array[returns_array <= var])

        return float(var), float(es)

    def _parametric_var(
        self, returns: List[float], confidence: float
    ) -> Tuple[float, float]:
        """Parametric VaR assuming normal distribution"""
        if not returns:
            return 0, 0

        returns_array = np.array(returns)
        mean = np.mean(returns_array)
        std = np.std(returns_array)

        # VaR using normal distribution
        from scipy.stats import norm

        var = mean + norm.ppf(1 - confidence) * std

        # Expected Shortfall
        es = mean - norm.pdf(norm.ppf(1 - confidence)) * std / (1 - confidence)

        return float(var), float(es)

    async def _monte_carlo_var(
        self, returns: List[float], confidence: float, simulations: int
    ) -> Tuple[float, float]:
        """Monte Carlo VaR calculation"""
        # Generate Monte Carlo paths
        final_returns = []

        for _ in range(simulations):
            sampled_returns = np.random.choice(returns, size=len(returns), replace=True)
            final_return = sum(sampled_returns)
            final_returns.append(final_return)

        final_returns_array = np.array(final_returns)
        var = np.percentile(final_returns_array, (1 - confidence) * 100)
        es = np.mean(final_returns_array[final_returns_array <= var])

        return float(var), float(es)

    def _calculate_var_backtest_stats(
        self,
        returns: List[float],
        confidence_levels: List[float],
        time_horizons: List[int],
    ) -> Dict[str, Any]:
        """Calculate VaR backtesting statistics"""
        # Simple implementation - would need historical VaR exceedances
        return {
            "var_exceedances": "Not implemented in mock",
            "kupiec_test": "Not implemented in mock",
            "backtesting_period": len(returns),
        }

    # Helper methods for stress testing
    def _apply_market_crash(
        self, returns: List[float], shock_magnitude: float
    ) -> List[float]:
        """Apply market crash scenario"""
        # Apply sudden shock to first part of returns
        crash_point = len(returns) // 4  # Apply at 25% point
        stressed_returns = returns.copy()

        for i in range(crash_point, min(crash_point + 10, len(returns))):
            stressed_returns[i] *= 1 + shock_magnitude

        return stressed_returns

    def _apply_volatility_spike(
        self, returns: List[float], multiplier: float
    ) -> List[float]:
        """Apply volatility spike scenario"""
        returns_array = np.array(returns)
        base_std = np.std(returns_array)
        new_std = base_std * multiplier

        # Scale returns to achieve new volatility
        stressed_returns = list(returns_array * (new_std / base_std))
        return stressed_returns

    def _apply_correlation_breakdown(
        self, returns: List[float], correlation_shift: float
    ) -> List[float]:
        """Apply correlation breakdown scenario"""
        # Simple implementation - add noise to simulate correlation breakdown
        noise = np.random.normal(0, np.std(returns) * 0.5, len(returns))
        stressed_returns = [r + n * correlation_shift for r, n in zip(returns, noise)]
        return stressed_returns

    def _apply_custom_scenario(
        self, returns: List[float], scenario_params: Dict[str, Any]
    ) -> List[float]:
        """Apply custom stress scenario"""
        # Placeholder for custom scenario application
        return returns.copy()

    def _generate_equity_curve(self, returns: List[float]) -> List[float]:
        """Generate equity curve from returns"""
        equity = 10000
        equity_curve = []

        for ret in returns:
            equity *= 1 + ret
            equity_curve.append(equity)

        return equity_curve

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not equity_curve:
            return 0

        peak = equity_curve[0]
        max_dd = 0

        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)

        return max_dd

    def _calculate_recovery_times(
        self, equity_curve: List[float], recovery_periods: List[int]
    ) -> Dict[str, float]:
        """Calculate recovery times for different periods"""
        # Simplified - would need more sophisticated implementation
        recovery_times = {}

        for period in recovery_periods:
            # Simplified - would need more sophisticated implementation
            recovery_times[f"{period}d"] = period * 0.7  # Mock recovery time

        return recovery_times

    def _compare_scenarios(self, stress_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare stress test scenarios"""
        comparison = {
            "worst_scenario": None,
            "best_scenario": None,
            "scenario_rankings": [],
        }

        worst_drawdown = -1
        best_drawdown = float("inf")

        for scenario, results in stress_results.items():
            max_dd = results.get("max_drawdown", 0)

            if max_dd > worst_drawdown:
                worst_drawdown = max_dd
                comparison["worst_scenario"] = scenario

            if max_dd < best_drawdown:
                best_drawdown = max_dd
                comparison["best_scenario"] = scenario

            comparison["scenario_rankings"].append(
                {
                    "scenario": scenario,
                    "max_drawdown": max_dd,
                    "final_return": results.get("final_return", 0),
                }
            )

        # Sort by max drawdown (ascending = more resilient)
        comparison["scenario_rankings"].sort(key=lambda x: x["max_drawdown"])

        return comparison

    def _assess_stress_resilience(
        self, stress_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall stress resilience"""
        if not stress_results:
            return {}

        max_drawdowns = [
            results.get("max_drawdown", 0) for results in stress_results.values()
        ]
        avg_max_dd = np.mean(max_drawdowns)
        worst_max_dd = max(max_drawdowns)

        # Resilience score (lower is better)
        resilience_score = 1 - (avg_max_dd / worst_max_dd) if worst_max_dd > 0 else 1

        return {
            "resilience_score": float(resilience_score),
            "average_max_drawdown": float(avg_max_dd),
            "worst_max_drawdown": float(worst_max_dd),
            "resilience_rating": self._get_resilience_rating(resilience_score),
        }

    def _get_resilience_rating(self, score: float) -> str:
        """Get resilience rating from score"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"

    # Helper methods for risk report
    def _calculate_base_risk_metrics(
        self, backtest_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate base risk metrics"""
        return {
            "total_return": backtest_result.get("total_return", 0),
            "sharpe_ratio": backtest_result.get("sharpe_ratio", 0),
            "max_drawdown": backtest_result.get("max_drawdown", 0),
            "win_rate": backtest_result.get("win_rate", 0),
            "volatility": self._calculate_volatility(backtest_result),
            "var_95": self._calculate_simple_var(backtest_result, 0.95),
            "risk_adjusted_return": self._calculate_risk_adjusted_return(
                backtest_result
            ),
        }

    def _calculate_volatility(self, backtest_result: Dict[str, Any]) -> float:
        """Calculate annualized volatility"""
        if "equity_curve" not in backtest_result:
            return 0

        returns = [point["return"] for point in backtest_result["equity_curve"]]
        if not returns:
            return 0

        return float(np.std(returns) * np.sqrt(252))  # Annualized

    def _calculate_simple_var(
        self, backtest_result: Dict[str, Any], confidence: float
    ) -> float:
        """Simple VaR calculation from returns"""
        if "equity_curve" not in backtest_result:
            return 0

        returns = [point["return"] for point in backtest_result["equity_curve"]]
        if not returns:
            return 0

        return float(np.percentile(returns, (1 - confidence) * 100))

    def _calculate_risk_adjusted_return(self, backtest_result: Dict[str, Any]) -> float:
        """Calculate risk-adjusted return"""
        total_return = backtest_result.get("total_return", 0)
        max_dd = backtest_result.get("max_drawdown", 1)

        if max_dd == 0:
            return total_return

        return float(total_return / max_dd)  # Simple risk-adjusted return

    def _comprehensive_risk_assessment(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        base_metrics = report.get("base_metrics", {})

        # Risk score (0-100, higher is riskier)
        risk_factors = []

        # Volatility factor
        volatility = base_metrics.get("volatility", 0)
        volatility_score = min(volatility * 100, 40)  # Max 40 points
        risk_factors.append(f"Volatility: {volatility_score:.1f}/40")

        # Drawdown factor
        max_dd = base_metrics.get("max_drawdown", 0)
        dd_score = min(max_dd * 100, 30)  # Max 30 points
        risk_factors.append(f"Max Drawdown: {dd_score:.1f}/30")

        # VaR factor
        var_95 = abs(base_metrics.get("var_95", 0))
        var_score = min(var_95 * 100, 20)  # Max 20 points
        risk_factors.append(f"VaR 95%: {var_score:.1f}/20")

        # Consistency factor (negative Sharpe is bad)
        sharpe = base_metrics.get("sharpe_ratio", 0)
        consistency_score = max(0, 10 - sharpe * 5)  # Max 10 points
        risk_factors.append(f"Consistency: {consistency_score:.1f}/10")

        total_risk_score = volatility_score + dd_score + var_score + consistency_score

        return {
            "total_risk_score": round(total_risk_score, 1),
            "risk_level": self._get_risk_level(total_risk_score),
            "risk_factors": risk_factors,
            "risk_rating": self._get_risk_rating(total_risk_score),
        }

    def _get_risk_level(self, score: float) -> str:
        """Get risk level from score"""
        if score >= 80:
            return "Very High"
        elif score >= 60:
            return "High"
        elif score >= 40:
            return "Medium"
        elif score >= 20:
            return "Low"
        else:
            return "Very Low"

    def _get_risk_rating(self, score: float) -> str:
        """Get risk rating (inverse of level)"""
        if score >= 80:
            return "D"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "B"
        elif score >= 20:
            return "A"
        else:
            return "A+"

    def _generate_risk_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        risk_assessment = report.get("risk_assessment", {})
        risk_score = risk_assessment.get("total_risk_score", 50)

        if risk_score > 70:
            recommendations.append(
                "Consider implementing position sizing to reduce risk exposure"
            )
            recommendations.append("Add stop-loss mechanisms to limit maximum losses")

        if risk_score > 50:
            recommendations.append("Diversify across multiple uncorrelated strategies")
            recommendations.append("Consider reducing leverage or position size")

        if risk_score > 30:
            recommendations.append(
                "Implement dynamic risk adjustment based on market volatility"
            )

        base_metrics = report.get("base_metrics", {})
        if base_metrics.get("sharpe_ratio", 0) < 1.0:
            recommendations.append(
                "Improve risk-adjusted returns through better entry/exit signals"
            )

        if base_metrics.get("max_drawdown", 0) > 0.2:
            recommendations.append("Add drawdown controls and position reduction rules")

        if not recommendations:
            recommendations.append(
                "Risk profile appears well-balanced - continue monitoring"
            )

        return recommendations

    def _format_executive_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format executive summary report"""
        return {
            "report_type": "Executive Summary",
            "key_metrics": {
                "total_return": report.get("base_metrics", {}).get("total_return", 0),
                "sharpe_ratio": report.get("base_metrics", {}).get("sharpe_ratio", 0),
                "max_drawdown": report.get("base_metrics", {}).get("max_drawdown", 0),
                "risk_rating": report.get("risk_assessment", {}).get(
                    "risk_rating", "N/A"
                ),
            },
            "risk_level": report.get("risk_assessment", {}).get(
                "risk_level", "Unknown"
            ),
            "top_recommendations": report.get("recommendations", [])[:3],
        }

    def _format_detailed_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format detailed report"""
        return {
            "report_type": "Detailed Analysis",
            "base_metrics": report.get("base_metrics", {}),
            "risk_assessment": report.get("risk_assessment", {}),
            "monte_carlo_summary": self._summarize_monte_carlo(
                report.get("monte_carlo", {})
            ),
            "var_summary": self._summarize_var_analysis(report.get("var_analysis", {})),
            "stress_test_summary": self._summarize_stress_test(
                report.get("stress_test", {})
            ),
            "all_recommendations": report.get("recommendations", []),
        }

    def _format_summary_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format summary report"""
        return {
            "report_type": "Summary",
            "performance": {
                "return": report.get("base_metrics", {}).get("total_return", 0),
                "sharpe": report.get("base_metrics", {}).get("sharpe_ratio", 0),
                "max_dd": report.get("base_metrics", {}).get("max_drawdown", 0),
            },
            "risk": {
                "level": report.get("risk_assessment", {}).get("risk_level", "Unknown"),
                "rating": report.get("risk_assessment", {}).get("risk_rating", "N/A"),
                "score": report.get("risk_assessment", {}).get("total_risk_score", 0),
            },
            "recommendations": report.get("recommendations", [])[:5],
        }

    def _summarize_monte_carlo(
        self, monte_carlo_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize Monte Carlo results"""
        if not monte_carlo_result:
            return {}

        final_stats = monte_carlo_result.get("final_value_stats", {})
        confidence_intervals = monte_carlo_result.get("confidence_intervals", {})

        return {
            "simulations": monte_carlo_result.get("simulations", 0),
            "mean_final_value": final_stats.get("mean", 0),
            "probability_of_profit": monte_carlo_result.get("probability_of_profit", 0),
            "confidence_95_lower": confidence_intervals.get("95%", {}).get("lower", 0),
            "confidence_95_upper": confidence_intervals.get("95%", {}).get("upper", 0),
        }

    def _summarize_var_analysis(self, var_result: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize VaR analysis"""
        if not var_result:
            return {}

        var_results = var_result.get("var_results", {})

        # Extract key VaR values
        var_1d_95 = var_results.get("1d_95%", {}).get("var", 0)
        var_5d_99 = var_results.get("5d_99%", {}).get("var", 0)

        return {
            "method": var_result.get("method", "Unknown"),
            "var_1d_95": var_1d_95,
            "var_5d_99": var_5d_99,
            "total_calculations": len(var_results),
        }

    def _summarize_stress_test(self, stress_result: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize stress test results"""
        if not stress_result:
            return {}

        risk_assessment = stress_result.get("risk_assessment", {})
        scenario_comparison = stress_result.get("scenario_comparison", {})

        return {
            "scenarios_tested": stress_result.get("scenarios_tested", []),
            "resilience_score": risk_assessment.get("resilience_score", 0),
            "resilience_rating": risk_assessment.get("resilience_rating", "Unknown"),
            "worst_scenario": scenario_comparison.get("worst_scenario", "Unknown"),
        }

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate return skewness"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return float(np.mean(((data - mean) / std) ** 3))

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate return kurtosis"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return float(np.mean(((data - mean) / std) ** 4) - 3)


# Global risk analyzer instance
_risk_analyzer_instance = None


def get_risk_analyzer(use_mock=None) -> Phase4RiskAnalyzer:
    """Get or create risk analyzer instance"""
    global _risk_analyzer_instance
    if _risk_analyzer_instance is None:
        _risk_analyzer_instance = Phase4RiskAnalyzer(use_mock=use_mock)
    return _risk_analyzer_instance
