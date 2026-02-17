"""
Main Trading System Orchestrator

Coordinates all components of the configurable trading system:
- Configuration management
- Risk management
- News discovery
- Strategy execution
- Testing and validation
- Stage transitions
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass

from jesse_mcp.config import ConfigurationManager, TradingStage, RiskProfile
from jesse_mcp.agents.enhanced_risk import EnhancedRiskAgent
from jesse_mcp.news_engine import NewsDiscoveryEngine
from jesse_mcp.testing_framework import TestingFramework, TestType, TestParameters
from jesse_mcp.core.integrations import get_jesse_wrapper

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    """Current system status"""

    stage: TradingStage
    active_strategies: List[str]
    current_positions: Dict[str, Any]
    portfolio_value: float
    daily_pnl: float
    risk_metrics: Dict[str, float]
    last_update: datetime
    alerts: List[str]


class TradingSystemOrchestrator:
    """Main orchestrator for the configurable trading system."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the trading system

        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigurationManager(config_path)
        self._config = self.config_manager.load_config()

        # Initialize components
        self.risk_agent = EnhancedRiskAgent(self.config_manager)
        self.news_engine = NewsDiscoveryEngine(self.config_manager)
        self.testing_framework = TestingFramework(
            self.config_manager, get_jesse_wrapper()
        )

        # System state
        self._status = SystemStatus(
            stage=self._config.stage,
            active_strategies=[],
            current_positions={},
            portfolio_value=0.0,
            daily_pnl=0.0,
            risk_metrics={},
            last_update=datetime.now(),
            alerts=[],
        )

        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing trading system")

        # Initialize async components
        await self.news_engine.initialize()

        # Validate configuration
        errors = self.config_manager.validate_config(self._config)
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            raise ValueError(f"Invalid configuration: {errors}")

        logger.info("Trading system initialized successfully")

    async def start(self):
        """Start the trading system"""
        if self._running:
            logger.warning("Trading system already running")
            return

        logger.info(f"Starting trading system in {self._config.stage.value} stage")
        self._running = True

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._news_discovery_loop()),
            asyncio.create_task(self._risk_management_loop()),
        ]

        logger.info("Trading system started")

    async def stop(self):
        """Stop the trading system"""
        if not self._running:
            return

        logger.info("Stopping trading system")
        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close components
        await self.news_engine.close()

        logger.info("Trading system stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Update system status
                await self._update_system_status()

                # Check for alerts
                await self._check_alerts()

                # Sleep for monitoring interval
                await asyncio.sleep(60)  # 1 minute

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)

    async def _news_discovery_loop(self):
        """News discovery and opportunity identification loop"""
        while self._running:
            try:
                # Get target symbols from active strategies
                target_symbols = await self._get_target_symbols()

                if target_symbols:
                    # Run news discovery cycle
                    opportunities = await self.news_engine.run_discovery_cycle(
                        target_symbols
                    )

                    # Process opportunities
                    await self._process_opportunities(opportunities)

                # Sleep for news discovery interval
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"News discovery loop error: {e}")
                await asyncio.sleep(60)

    async def _risk_management_loop(self):
        """Risk management and monitoring loop"""
        while self._running:
            try:
                # Monitor portfolio risk
                portfolio_data = await self._get_portfolio_data()
                risk_analysis = self.risk_agent.analyze_portfolio_risk(portfolio_data)

                # Update risk metrics
                self._status.risk_metrics = await self._extract_risk_metrics(
                    risk_analysis
                )

                # Check portfolio limits
                limit_status = self.risk_agent.portfolio_limit_monitoring(
                    portfolio_data
                )

                # Sleep for risk management interval
                await asyncio.sleep(120)  # 2 minutes

            except Exception as e:
                logger.error(f"Risk management loop error: {e}")
                await asyncio.sleep(30)

    async def _update_system_status(self):
        """Update system status"""
        try:
            # Get current portfolio data
            portfolio_data = await self._get_portfolio_data()

            self._status.current_positions = portfolio_data.get("positions", {})
            self._status.portfolio_value = portfolio_data.get("total_value", 0.0)
            self._status.daily_pnl = portfolio_data.get("daily_pnl", 0.0)
            self._status.last_update = datetime.now()

            # Update active strategies
            self._status.active_strategies = [
                name
                for name, config in self._config.strategies.items()
                if config.enabled and config.stage == self._config.stage
            ]

        except Exception as e:
            logger.error(f"Failed to update system status: {e}")

    async def _check_alerts(self):
        """Check for system alerts"""
        alerts = []

        # Check portfolio value alerts
        if (
            self._status.portfolio_value
            < self._config.portfolio_limits.min_account_balance
        ):
            alerts.append(
                f"Portfolio value below minimum: ${self._status.portfolio_value:.2f}"
            )

        # Check drawdown alerts
        max_drawdown = self._status.risk_metrics.get("max_drawdown", 0.0)
        if max_drawdown > self._config.global_risk_settings.max_drawdown:
            alerts.append(f"Maximum drawdown exceeded: {max_drawdown:.1%}")

        # Check position limits
        num_positions = len(self._status.current_positions)
        if num_positions > self._config.portfolio_limits.max_open_positions:
            alerts.append(f"Position limit exceeded: {num_positions} positions")

        self._status.alerts = alerts

        if alerts:
            logger.warning(f"System alerts: {alerts}")

    async def _get_target_symbols(self) -> List[str]:
        """Get target symbols from active strategies"""
        # Mock implementation - would extract from strategy configurations
        return ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

    async def _get_portfolio_data(self) -> Dict[str, Any]:
        """Get current portfolio data"""
        # Mock implementation - would query actual portfolio
        return {
            "positions": {
                "BTC-USDT": {"size": 0.5, "value": 25000},
                "ETH-USDT": {"size": 10, "value": 20000},
            },
            "total_value": 50000,
            "daily_pnl": 150.50,
            "cash": 5000,
        }

    async def _process_opportunities(self, opportunities: List):
        """Process trading opportunities"""
        for opportunity in opportunities[:5]:  # Top 5 opportunities
            try:
                # Validate opportunity against risk settings
                validation = await self._validate_opportunity(opportunity)

                if validation.get("approved", False):
                    # Execute trade if in live stage
                    if self._config.stage == TradingStage.LIVE:
                        await self._execute_opportunity(opportunity)
                    else:
                        logger.info(f"Paper trading opportunity: {opportunity.symbol}")

            except Exception as e:
                logger.error(f"Failed to process opportunity {opportunity.symbol}: {e}")

    async def _validate_opportunity(self, opportunity) -> Dict[str, Any]:
        """Validate trading opportunity against risk settings"""
        # Mock validation
        return {
            "approved": opportunity.confidence > 0.6,
            "risk_score": opportunity.confidence,
            "position_size": opportunity.position_size,
        }

    async def _execute_opportunity(self, opportunity):
        """Execute trading opportunity"""
        # Mock execution
        logger.info(
            f"Executing {opportunity.opportunity_type} trade on {opportunity.symbol}"
        )

    async def _extract_risk_metrics(self, risk_analysis: str) -> Dict[str, float]:
        """Extract risk metrics from analysis"""
        # Mock extraction
        return {
            "max_drawdown": 0.05,
            "portfolio_var": 0.02,
            "correlation_risk": 0.3,
            "leverage_ratio": 1.2,
        }

    async def transition_stage(self, new_stage: TradingStage) -> bool:
        """Transition to a new trading stage

        Args:
            new_stage: Target trading stage

        Returns:
            True if transition successful
        """
        logger.info(
            f"Transitioning from {self._config.stage.value} to {new_stage.value}"
        )

        try:
            # Assess transition risks
            risk_assessment = self.risk_agent.assess_stage_transition_risk(
                self._config.stage, new_stage
            )

            # Run validation tests for new stage
            if new_stage in [TradingStage.PAPER, TradingStage.LIVE]:
                validation_results = await self._run_stage_validation(new_stage)

                if not validation_results.get("passed", False):
                    logger.error(f"Stage validation failed: {validation_results}")
                    return False

            # Update configuration
            self._config.stage = new_stage
            self._status.stage = new_stage

            # Save configuration
            self.config_manager.save_config(self._config)

            logger.info(f"Successfully transitioned to {new_stage.value} stage")
            return True

        except Exception as e:
            logger.error(f"Stage transition failed: {e}")
            return False

    async def _run_stage_validation(self, stage: TradingStage) -> Dict[str, Any]:
        """Run validation tests for stage transition"""
        try:
            # Define test parameters
            test_params = TestParameters(
                test_type=TestType.STAGE_TRANSITION,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                initial_capital=10000,
                symbols=["BTC-USDT", "ETH-USDT"],
                risk_profile="moderate",
                strategies=list(self._config.strategies.keys()),
                market_regimes=[],  # Would determine from recent data
                custom_params={"stage": stage.value},
            )

            # Run tests
            results = []
            for strategy_name in self._config.strategies.keys():
                result = self.testing_framework.validate_strategy_performance(
                    strategy_name
                )
                results.append(result)

            # Check overall pass rate
            passed = sum(1 for r in results if r.get("passed_checks", [])) > 0

            return {
                "passed": passed,
                "results": results,
                "pass_rate": sum(1 for r in results if r.get("passed_checks", []))
                / len(results)
                if results
                else 0,
            }

        except Exception as e:
            logger.error(f"Stage validation failed: {e}")
            return {"passed": False, "error": str(e)}

    async def run_comprehensive_test(
        self, test_period_days: int = 90
    ) -> Dict[str, Any]:
        """Run comprehensive system testing

        Args:
            test_period_days: Number of days to test

        Returns:
            Comprehensive test results
        """
        logger.info(f"Running comprehensive test for {test_period_days} days")

        try:
            # Define test parameters
            test_params = TestParameters(
                test_type=TestType.RISK_PROFILE_BACKTEST,
                start_date=datetime.now() - timedelta(days=test_period_days),
                end_date=datetime.now(),
                initial_capital=10000,
                symbols=["BTC-USDT", "ETH-USDT", "SOL-USDT"],
                risk_profile="moderate",
                strategies=list(self._config.strategies.keys()),
                market_regimes=[],  # Would determine from data
                custom_params={},
            )

            # Compare risk profiles
            profile_results = self.testing_framework.compare_risk_profiles(test_params)

            # Run stress tests
            portfolio = {
                "total_value": 100000,
                "positions": {"BTC-USDT": 0.3, "ETH-USDT": 0.2},
            }
            stress_scenarios = [
                {"name": "market_crash", "market_shock": 0.3},
                {"name": "crypto_winter", "market_shock": 0.5},
                {
                    "name": "liquidity_crisis",
                    "market_shock": 0.2,
                    "correlation_increase": 0.5,
                },
            ]
            stress_results = self.testing_framework.run_stress_test(
                portfolio, stress_scenarios
            )

            # Generate report
            test_results = []
            for profile, result in profile_results.items():
                test_results.append(
                    type(
                        "TestResult",
                        (),
                        {
                            "test_type": TestType.RISK_PROFILE_BACKTEST,
                            "success": result.total_return > 0,
                            "metrics": {
                                "total_return": result.total_return,
                                "sharpe_ratio": result.sharpe_ratio,
                                "max_drawdown": result.max_drawdown,
                            },
                        },
                    )()
                )

            report = self.testing_framework.generate_test_report(test_results)

            return {
                "profile_results": profile_results,
                "stress_results": stress_results,
                "report": report,
                "recommendations": self._generate_test_recommendations(
                    profile_results, stress_results
                ),
            }

        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            return {"error": str(e)}

    def _generate_test_recommendations(
        self, profile_results: Dict, stress_results: Dict
    ) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Analyze risk profile performance
        best_profile = max(
            profile_results.items(),
            key=lambda x: x[1].sharpe_ratio if hasattr(x[1], "sharpe_ratio") else 0,
        )
        recommendations.append(
            f"Best performing risk profile: {best_profile[0]} (Sharpe: {best_profile[1].sharpe_ratio:.2f})"
        )

        # Analyze stress test results
        worst_loss = stress_results.get("worst_case", {}).get("loss", 0)
        if worst_loss > 20000:  # $20k loss threshold
            recommendations.append(
                "Consider reducing position sizes to improve stress test resilience"
            )

        # General recommendations
        recommendations.append("Monitor correlation risk during market stress periods")
        recommendations.append("Implement dynamic position sizing based on volatility")

        return recommendations

    def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        return self._status

    def get_configuration(self):
        """Get current configuration"""
        return self._config

    async def update_configuration(self, updates: Dict[str, Any]) -> bool:
        """Update system configuration

        Args:
            updates: Configuration updates

        Returns:
            True if update successful
        """
        try:
            # Apply updates to configuration
            for key, value in updates.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)

            # Validate updated configuration
            errors = self.config_manager.validate_config(self._config)
            if errors:
                logger.error(f"Configuration update validation failed: {errors}")
                return False

            # Save configuration
            success = self.config_manager.save_config(self._config)
            if success:
                logger.info("Configuration updated successfully")

            return success

        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            return False
