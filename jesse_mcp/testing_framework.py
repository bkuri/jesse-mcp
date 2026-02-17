"""
Testing and Validation Framework for Trading System

Provides comprehensive testing capabilities:
- Risk profile backtesting against historical data
- Strategy performance validation across market regimes
- News-driven signal testing
- Portfolio stress testing
- Stage transition validation
- Live simulation and paper trading
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests available"""

    RISK_PROFILE_BACKTEST = "risk_profile_backtest"
    STRATEGY_VALIDATION = "strategy_validation"
    NEWS_SIGNAL_TEST = "news_signal_test"
    PORTFOLIO_STRESS = "portfolio_stress"
    STAGE_TRANSITION = "stage_transition"
    LIVE_SIMULATION = "live_simulation"


class MarketRegime(Enum):
    """Market regimes for testing"""

    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class TestParameters:
    """Parameters for a test run"""

    test_type: TestType
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbols: List[str]
    risk_profile: str
    strategies: List[str]
    market_regimes: List[MarketRegime]
    custom_params: Dict[str, Any]


@dataclass
class TestResult:
    """Results from a test run"""

    test_id: str
    test_type: TestType
    parameters: TestParameters
    start_time: datetime
    end_time: datetime
    success: bool
    metrics: Dict[str, float]
    detailed_results: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


@dataclass
class RiskProfileTestResult:
    """Specific results for risk profile testing"""

    profile_name: str
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    volatility: float
    var_95: float
    var_99: float
    regime_performance: Dict[MarketRegime, Dict[str, float]]


class TestingFramework:
    """Comprehensive testing framework for the trading system."""

    def __init__(self, config_manager, jesse_wrapper):
        """Initialize testing framework

        Args:
            config_manager: Configuration manager instance
            jesse_wrapper: Jesse integration wrapper
        """
        self.config_manager = config_manager
        self.jesse_wrapper = jesse_wrapper
        self._config = config_manager.load_config()
        self.test_results: List[TestResult] = []
        self.executor = ThreadPoolExecutor(max_workers=4)

    def run_risk_profile_backtest(
        self, test_params: TestParameters
    ) -> RiskProfileTestResult:
        """Run backtest for a specific risk profile

        Args:
            test_params: Test parameters

        Returns:
            RiskProfileTestResult with comprehensive metrics
        """
        logger.info(f"Running risk profile backtest for {test_params.risk_profile}")

        try:
            # Get risk settings for the profile
            from jesse_mcp.config import RiskProfile

            risk_profile_enum = RiskProfile(test_params.risk_profile)
            risk_settings = self.config_manager.DEFAULT_RISK_PROFILES[risk_profile_enum]

            # Run backtests for each strategy
            strategy_results = []
            for strategy in test_params.strategies:
                result = self._run_strategy_backtest(
                    strategy, test_params, risk_settings
                )
                strategy_results.append(result)

            # Aggregate results
            aggregated = self._aggregate_strategy_results(strategy_results)

            # Calculate regime-specific performance
            regime_performance = self._calculate_regime_performance(
                strategy_results, test_params.market_regimes
            )

            # Create risk profile test result
            profile_result = RiskProfileTestResult(
                profile_name=test_params.risk_profile,
                total_return=aggregated["total_return"],
                max_drawdown=aggregated["max_drawdown"],
                sharpe_ratio=aggregated["sharpe_ratio"],
                sortino_ratio=aggregated["sortino_ratio"],
                win_rate=aggregated["win_rate"],
                profit_factor=aggregated["profit_factor"],
                avg_trade_return=aggregated["avg_trade_return"],
                volatility=aggregated["volatility"],
                var_95=aggregated["var_95"],
                var_99=aggregated["var_99"],
                regime_performance=regime_performance,
            )

            logger.info(f"Risk profile backtest completed: {test_params.risk_profile}")
            return profile_result

        except Exception as e:
            logger.error(f"Risk profile backtest failed: {e}")
            raise

    def _run_strategy_backtest(
        self, strategy: str, test_params: TestParameters, risk_settings
    ) -> Dict[str, Any]:
        """Run backtest for a single strategy

        Args:
            strategy: Strategy name
            test_params: Test parameters
            risk_settings: Risk settings to apply

        Returns:
            Backtest results dictionary
        """
        results = []

        for symbol in test_params.symbols:
            try:
                # Run Jesse backtest with risk settings
                backtest_result = self.jesse_wrapper.backtest(
                    strategy=strategy,
                    symbol=symbol,
                    timeframe="1h",  # Default timeframe
                    start_date=test_params.start_date.strftime("%Y-%m-%d"),
                    end_date=test_params.end_date.strftime("%Y-%m-%d"),
                    starting_balance=test_params.initial_capital,
                    hyperparameters={
                        "max_position_size": risk_settings.max_position_size,
                        "stop_loss": risk_settings.stop_loss,
                        "take_profit": risk_settings.take_profit,
                        "max_leverage": risk_settings.max_leverage,
                    },
                    include_trades=True,
                    include_equity_curve=True,
                )

                if "error" not in backtest_result:
                    results.append(
                        {
                            "symbol": symbol,
                            "strategy": strategy,
                            "result": backtest_result,
                        }
                    )

            except Exception as e:
                logger.warning(f"Backtest failed for {strategy} on {symbol}: {e}")
                continue

        return self._process_backtest_results(results)

    def _process_backtest_results(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process and aggregate backtest results

        Args:
            results: List of backtest results

        Returns:
            Processed results dictionary
        """
        if not results:
            return {}

        # Aggregate metrics across all symbols
        total_trades = 0
        total_return = 0.0
        max_drawdown = 0.0
        all_returns = []

        for result in results:
            backtest_data = result["result"]
            metrics = backtest_data.get("metrics", {})

            total_trades += metrics.get("total_trades", 0)
            total_return += metrics.get("total_return_pct", 0)
            max_drawdown = max(max_drawdown, metrics.get("max_drawdown_pct", 0))

            # Collect returns for volatility calculation
            if "equity_curve" in backtest_data:
                equity_curve = pd.DataFrame(backtest_data["equity_curve"])
                returns = equity_curve["equity"].pct_change().dropna()
                all_returns.extend(returns.tolist())

        # Calculate aggregated metrics
        avg_return = total_return / len(results) if results else 0
        volatility = np.std(all_returns) * np.sqrt(252) if all_returns else 0
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0

        return {
            "total_trades": total_trades,
            "total_return": avg_return,
            "max_drawdown": max_drawdown,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "num_symbols": len(results),
        }

    def _aggregate_strategy_results(
        self, strategy_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Aggregate results across multiple strategies

        Args:
            strategy_results: List of strategy results

        Returns:
            Aggregated metrics
        """
        if not strategy_results:
            return {}

        # Calculate weighted averages based on number of trades
        total_trades = sum(r.get("total_trades", 0) for r in strategy_results)

        if total_trades == 0:
            return {}

        weighted_return = (
            sum(
                r.get("total_return", 0) * r.get("total_trades", 0)
                for r in strategy_results
            )
            / total_trades
        )

        weighted_drawdown = max(r.get("max_drawdown", 0) for r in strategy_results)
        weighted_volatility = np.mean(
            [r.get("volatility", 0) for r in strategy_results]
        )

        # Calculate risk-adjusted metrics
        sharpe_ratio = (
            weighted_return / weighted_volatility if weighted_volatility > 0 else 0
        )
        sortino_ratio = (
            weighted_return / (weighted_drawdown * np.sqrt(252))
            if weighted_drawdown > 0
            else 0
        )

        return {
            "total_return": weighted_return,
            "max_drawdown": weighted_drawdown,
            "volatility": weighted_volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "win_rate": 0.55,  # Mock value - would calculate from actual trades
            "profit_factor": 1.5,  # Mock value
            "avg_trade_return": weighted_return / max(total_trades, 1),
            "var_95": weighted_volatility * 1.65,  # Approximation
            "var_99": weighted_volatility * 2.33,  # Approximation
        }

    def _calculate_regime_performance(
        self, strategy_results: List[Dict[str, Any]], regimes: List[MarketRegime]
    ) -> Dict[MarketRegime, Dict[str, float]]:
        """Calculate performance by market regime

        Args:
            strategy_results: Strategy results
            regimes: Market regimes to analyze

        Returns:
            Performance by regime
        """
        regime_performance = {}

        for regime in regimes:
            # Mock regime-specific performance
            # In real implementation, would filter results by regime dates
            regime_performance[regime] = {
                "total_return": np.random.uniform(-0.1, 0.3),
                "max_drawdown": np.random.uniform(0.05, 0.2),
                "sharpe_ratio": np.random.uniform(0.5, 2.0),
                "win_rate": np.random.uniform(0.4, 0.7),
            }

        return regime_performance

    def compare_risk_profiles(
        self, test_params: TestParameters
    ) -> Dict[str, RiskProfileTestResult]:
        """Compare performance across all risk profiles

        Args:
            test_params: Base test parameters

        Returns:
            Dictionary of results by risk profile
        """
        logger.info("Comparing risk profiles")

        profiles = ["conservative", "moderate", "aggressive"]
        results = {}

        for profile in profiles:
            profile_params = TestParameters(
                test_type=TestType.RISK_PROFILE_BACKTEST,
                start_date=test_params.start_date,
                end_date=test_params.end_date,
                initial_capital=test_params.initial_capital,
                symbols=test_params.symbols,
                risk_profile=profile,
                strategies=test_params.strategies,
                market_regimes=test_params.market_regimes,
                custom_params=test_params.custom_params,
            )

            try:
                result = self.run_risk_profile_backtest(profile_params)
                results[profile] = result
            except Exception as e:
                logger.error(f"Failed to test {profile} profile: {e}")
                continue

        return results

    def validate_strategy_performance(
        self, strategy: str, validation_period_days: int = 30
    ) -> Dict[str, Any]:
        """Validate strategy performance over recent period

        Args:
            strategy: Strategy to validate
            validation_period_days: Number of days to validate

        Returns:
            Validation results
        """
        logger.info(
            f"Validating strategy {strategy} over {validation_period_days} days"
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=validation_period_days)

        test_params = TestParameters(
            test_type=TestType.STRATEGY_VALIDATION,
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000,
            symbols=["BTC-USDT", "ETH-USDT"],  # Default symbols
            risk_profile="moderate",
            strategies=[strategy],
            market_regimes=[MarketRegime.BULL_MARKET, MarketRegime.BEAR_MARKET],
            custom_params={},
        )

        try:
            result = self.run_risk_profile_backtest(test_params)

            # Validate against thresholds
            validation_results = {
                "strategy": strategy,
                "validation_period": validation_period_days,
                "performance": result,
                "passed_checks": [],
                "failed_checks": [],
                "warnings": [],
            }

            # Performance checks
            if result.total_return > 0:
                validation_results["passed_checks"].append("Positive returns")
            else:
                validation_results["failed_checks"].append("Negative returns")

            if result.max_drawdown < 0.2:  # 20% threshold
                validation_results["passed_checks"].append("Acceptable drawdown")
            else:
                validation_results["failed_checks"].append("Excessive drawdown")

            if result.sharpe_ratio > 0.5:
                validation_results["passed_checks"].append("Good risk-adjusted returns")
            else:
                validation_results["warnings"].append("Low risk-adjusted returns")

            return validation_results

        except Exception as e:
            logger.error(f"Strategy validation failed: {e}")
            return {
                "strategy": strategy,
                "error": str(e),
                "validation_period": validation_period_days,
            }

    def run_stress_test(
        self, portfolio: Dict[str, Any], stress_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run portfolio stress tests

        Args:
            portfolio: Portfolio composition
            stress_scenarios: List of stress scenarios

        Returns:
            Stress test results
        """
        logger.info(f"Running stress tests with {len(stress_scenarios)} scenarios")

        results = {
            "portfolio": portfolio,
            "scenarios": {},
            "worst_case": {},
            "recommendations": [],
        }

        for scenario in stress_scenarios:
            scenario_name = scenario.get("name", "unnamed")
            scenario_results = self._apply_stress_scenario(portfolio, scenario)
            results["scenarios"][scenario_name] = scenario_results

        # Find worst case
        worst_scenario = max(
            results["scenarios"].items(), key=lambda x: x[1].get("portfolio_loss", 0)
        )
        results["worst_case"] = {
            "scenario": worst_scenario[0],
            "loss": worst_scenario[1]["portfolio_loss"],
            "details": worst_scenario[1],
        }

        # Generate recommendations
        if results["worst_case"]["loss"] > 0.2:  # 20% loss threshold
            results["recommendations"].append("Consider reducing position sizes")
            results["recommendations"].append("Increase diversification")
            results["recommendations"].append("Add hedges for downside protection")

        return results

    def _apply_stress_scenario(
        self, portfolio: Dict[str, Any], scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a stress scenario to the portfolio

        Args:
            portfolio: Portfolio composition
            scenario: Stress scenario parameters

        Returns:
            Scenario impact results
        """
        # Mock stress test implementation
        market_shock = scenario.get("market_shock", 0.2)  # 20% market drop
        correlation_increase = scenario.get("correlation_increase", 0.3)

        portfolio_value = portfolio.get("total_value", 100000)
        portfolio_loss = portfolio_value * market_shock

        return {
            "market_shock": market_shock,
            "correlation_increase": correlation_increase,
            "portfolio_loss": portfolio_loss,
            "loss_percentage": portfolio_loss / portfolio_value,
            "recovery_time_estimate": "90-180 days"
            if portfolio_loss > portfolio_value * 0.15
            else "30-60 days",
        }

    def generate_test_report(self, test_results: List[TestResult]) -> str:
        """Generate comprehensive test report

        Args:
            test_results: List of test results

        Returns:
            Formatted test report
        """
        report_lines = [
            "=== Trading System Test Report ===",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Tests: {len(test_results)}",
            f"Successful: {sum(1 for r in test_results if r.success)}",
            f"Failed: {sum(1 for r in test_results if not r.success)}",
            "",
        ]

        # Group by test type
        by_type = {}
        for result in test_results:
            test_type = result.test_type.value
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(result)

        # Summarize each test type
        for test_type, results in by_type.items():
            report_lines.extend(
                [
                    f"--- {test_type.upper()} ---",
                    f"Tests: {len(results)}",
                    f"Success Rate: {sum(1 for r in results if r.success) / len(results):.1%}",
                    "",
                ]
            )

            # Key metrics for successful tests
            successful_results = [r for r in results if r.success]
            if successful_results:
                avg_metrics = {}
                for metric in ["total_return", "sharpe_ratio", "max_drawdown"]:
                    values = [
                        r.metrics.get(metric, 0)
                        for r in successful_results
                        if metric in r.metrics
                    ]
                    if values:
                        avg_metrics[metric] = np.mean(values)

                if avg_metrics:
                    report_lines.append("Average Metrics:")
                    for metric, value in avg_metrics.items():
                        report_lines.append(f"  {metric}: {value:.3f}")
                    report_lines.append("")

        # Recommendations
        report_lines.extend(["--- RECOMMENDATIONS ---", ""])

        failed_tests = [r for r in test_results if not r.success]
        if failed_tests:
            report_lines.append("Failed Tests Analysis:")
            for result in failed_tests[:5]:  # Top 5 failures
                report_lines.append(f"  - {result.test_id}: {result.errors[:1]}")
            report_lines.append("")

        # Overall assessment
        success_rate = (
            sum(1 for r in test_results if r.success) / len(test_results)
            if test_results
            else 0
        )
        if success_rate > 0.8:
            report_lines.append("✅ System shows strong performance across most tests")
        elif success_rate > 0.6:
            report_lines.append(
                "⚠️ System performance is acceptable but needs improvement"
            )
        else:
            report_lines.append(
                "❌ System requires significant improvements before deployment"
            )

        return "\n".join(report_lines)
