"""
MCP Tools for Specialized Agents

Exposes agent methods as MCP tools for direct LLM access via the MCP protocol.
No need for Python function calls - everything goes through MCP.
"""

import json
import logging
from typing import Optional, List
from fastmcp import FastMCP

from jesse_mcp.agents import (
    StrategyOptimizationAgent,
    RiskManagementAgent,
    BacktestingAgent,
)

logger = logging.getLogger("jesse-mcp-agents")

# Global agent instances (one per agent type)
_strategy_agent: Optional[StrategyOptimizationAgent] = None
_risk_agent: Optional[RiskManagementAgent] = None
_backtest_agent: Optional[BacktestingAgent] = None


def get_strategy_agent() -> StrategyOptimizationAgent:
    """Get or create strategy optimization agent."""
    global _strategy_agent
    if _strategy_agent is None:
        _strategy_agent = StrategyOptimizationAgent()
        logger.info("✅ Strategy Optimization Agent initialized")
    return _strategy_agent


def get_risk_agent() -> RiskManagementAgent:
    """Get or create risk management agent."""
    global _risk_agent
    if _risk_agent is None:
        _risk_agent = RiskManagementAgent()
        logger.info("✅ Risk Management Agent initialized")
    return _risk_agent


def get_backtest_agent() -> BacktestingAgent:
    """Get or create backtesting agent."""
    global _backtest_agent
    if _backtest_agent is None:
        _backtest_agent = BacktestingAgent()
        logger.info("✅ Backtesting Agent initialized")
    return _backtest_agent


def register_agent_tools(mcp: FastMCP) -> None:
    """Register all agent tools with FastMCP."""

    # ==================== STRATEGY OPTIMIZATION TOOLS ====================

    @mcp.tool
    def strategy_suggest_improvements(strategy_name: str, pair: str) -> str:
        """
        Get specific improvement suggestions for a trading strategy.

        Analyzes current performance and recommends concrete changes to test.

        Args:
            strategy_name: Name of the strategy to analyze
            pair: Trading pair to test on (e.g., 'BTCUSDT')

        Returns:
            Detailed improvement recommendations with expected impact
        """
        agent = get_strategy_agent()
        return agent.suggest_improvements(strategy_name, pair)

    @mcp.tool
    def strategy_compare_strategies(strategy1: str, strategy2: str) -> str:
        """
        Compare two strategies to identify best practices.

        Analyzes performance differences and key differentiators.

        Args:
            strategy1: First strategy name
            strategy2: Second strategy name

        Returns:
            Comparative analysis with insights on what makes one perform better
        """
        agent = get_strategy_agent()
        return agent.compare_strategies(strategy1, strategy2)

    @mcp.tool
    def strategy_optimize_pair_selection(strategy_name: str) -> str:
        """
        Find the best trading pairs for a given strategy.

        Analyzes performance across pairs to recommend the best ones.

        Args:
            strategy_name: Strategy to optimize pair selection for

        Returns:
            Ranked list of pairs with performance metrics and recommendations
        """
        agent = get_strategy_agent()
        return agent.optimize_pair_selection(strategy_name)

    @mcp.tool
    def strategy_analyze_optimization_impact(change_description: str) -> str:
        """
        Estimate the impact of a proposed strategy change.

        Analyzes expected benefits, risks, and testing methodology.

        Args:
            change_description: Description of the proposed change

        Returns:
            Impact analysis with testing recommendations
        """
        agent = get_strategy_agent()
        return agent.analyze_optimization_impact(change_description)

    # ==================== RISK MANAGEMENT TOOLS ====================

    @mcp.tool
    def risk_analyze_portfolio(pairs: List[str]) -> str:
        """
        Analyze risk profile of a trading portfolio.

        Evaluates correlation, concentration, and diversification.

        Args:
            pairs: List of trading pairs to analyze

        Returns:
            Portfolio risk analysis with recommendations
        """
        agent = get_risk_agent()
        return agent.analyze_portfolio_risk(pairs)

    @mcp.tool
    def risk_stress_test(pairs: List[str], scenario: str) -> str:
        """
        Stress test a portfolio under extreme market scenarios.

        Tests resilience to market crashes, liquidity crises, etc.

        Args:
            pairs: Trading pairs to stress test
            scenario: Market scenario (e.g., 'market crash', 'flash crash')

        Returns:
            Stress test results and risk mitigation strategies
        """
        agent = get_risk_agent()
        return agent.stress_test_portfolio(pairs, scenario)

    @mcp.tool
    def risk_assess_leverage(strategy_name: str, leverage: float) -> str:
        """
        Assess the risks of trading with leverage.

        Evaluates liquidation risk, margin requirements, and safe levels.

        Args:
            strategy_name: Strategy using leverage
            leverage: Leverage multiplier (e.g., 2.0 for 2x)

        Returns:
            Leverage risk assessment with recommendations
        """
        agent = get_risk_agent()
        return agent.assess_leverage_risk(strategy_name, leverage)

    @mcp.tool
    def risk_recommend_hedges(pair: str, risk_type: str) -> str:
        """
        Recommend hedging strategies for specific risks.

        Suggests hedging instruments and positioning.

        Args:
            pair: Trading pair to hedge (e.g., 'BTCUSDT')
            risk_type: Type of risk (e.g., 'downside', 'volatility', 'correlation')

        Returns:
            Hedging strategy recommendations with sizing and cost-benefit analysis
        """
        agent = get_risk_agent()
        return agent.recommend_hedges(pair, risk_type)

    @mcp.tool
    def risk_analyze_drawdown_recovery(strategy_name: str) -> str:
        """
        Analyze historical drawdowns and recovery patterns.

        Examines when and why losses occur and recovery timelines.

        Args:
            strategy_name: Strategy to analyze

        Returns:
            Drawdown analysis with recovery insights and improvement suggestions
        """
        agent = get_risk_agent()
        return agent.analyze_drawdown_recovery(strategy_name)

    # ==================== BACKTESTING TOOLS ====================

    @mcp.tool
    def backtest_comprehensive(
        strategy_name: str,
        pair: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """
        Run a comprehensive backtest of a trading strategy.

        Tests performance, extracts metrics, and provides analysis.

        Args:
            strategy_name: Strategy to backtest
            pair: Trading pair (e.g., 'BTCUSDT')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Comprehensive backtest results and analysis
        """
        agent = get_backtest_agent()
        return agent.backtest_strategy(strategy_name, pair, start_date, end_date)

    @mcp.tool
    def backtest_compare_timeframes(strategy_name: str, pair: str) -> str:
        """
        Compare strategy performance across different timeframes.

        Tests 1m, 5m, 15m, 1h, 4h, 1d to find optimal timeframe.

        Args:
            strategy_name: Strategy to test
            pair: Trading pair

        Returns:
            Cross-timeframe comparison with optimal timeframe recommendation
        """
        agent = get_backtest_agent()
        return agent.compare_timeframes(strategy_name, pair)

    @mcp.tool
    def backtest_optimize_parameters(
        strategy_name: str,
        pair: str,
        param_name: str,
        param_range: str,
    ) -> str:
        """
        Find optimal parameter values through systematic testing.

        Tests parameter ranges to identify best settings.

        Args:
            strategy_name: Strategy with parameter to optimize
            pair: Trading pair
            param_name: Parameter name (e.g., 'period', 'threshold')
            param_range: Range to test (e.g., '10-100')

        Returns:
            Parameter optimization results with sensitivity analysis
        """
        agent = get_backtest_agent()
        return agent.optimize_parameters(strategy_name, pair, param_name, param_range)

    @mcp.tool
    def backtest_monte_carlo(strategy_name: str, pair: str) -> str:
        """
        Perform Monte Carlo simulation for strategy robustness analysis.

        Tests many outcome variations to assess robustness.

        Args:
            strategy_name: Strategy to analyze
            pair: Trading pair

        Returns:
            Monte Carlo analysis with confidence intervals and risk assessment
        """
        agent = get_backtest_agent()
        return agent.monte_carlo_analysis(strategy_name, pair)

    @mcp.tool
    def backtest_analyze_regimes(strategy_name: str, pair: str) -> str:
        """
        Analyze strategy performance in different market regimes.

        Tests performance in trending, ranging, and volatile markets.

        Args:
            strategy_name: Strategy to analyze
            pair: Trading pair

        Returns:
            Regime-dependent performance analysis with adaptation suggestions
        """
        agent = get_backtest_agent()
        return agent.analyze_regime_performance(strategy_name, pair)

    @mcp.tool
    def backtest_validate_significance(strategy_name: str, pair: str) -> str:
        """
        Validate that backtest results are statistically significant.

        Ensures results are real, not luck or overfitting.

        Args:
            strategy_name: Strategy to validate
            pair: Trading pair

        Returns:
            Statistical significance assessment and confidence metrics
        """
        agent = get_backtest_agent()
        return agent.validate_statistical_significance(strategy_name, pair)

    # ==================== MARKET MONITORING TOOLS ====================

    @mcp.tool
    def monitor_daily_scan(symbols: str = "BTC-USDT,ETH-USDT") -> dict:
        """
        Run daily market scan to identify trading opportunities.

        Scans multiple symbols and strategies to find signals.

        Args:
            symbols: Comma-separated list of symbols to scan

        Returns:
            Daily report with opportunities, risks, and recommendations
        """
        from jesse_mcp.monitoring import MarketMonitor

        symbol_list = [s.strip() for s in symbols.split(",")]
        monitor = MarketMonitor(symbols=symbol_list)
        report = monitor.daily_scan()
        return json.loads(monitor.report_to_json(report))

    @mcp.tool
    def monitor_get_sentiment() -> dict:
        """
        Get current market sentiment from Fear & Greed Index.

        Returns:
            Fear & Greed score and rating with historical context
        """
        from jesse_mcp.monitoring import MarketMonitor

        monitor = MarketMonitor()
        fg = monitor.get_fear_greed()
        sentiment = monitor.analyze_sentiment(fg.get("score", 50))
        return {
            "fear_greed": fg,
            "sentiment": sentiment,
            "timestamp": fg.get("timestamp", ""),
        }

    @mcp.tool
    def monitor_scan_opportunities(
        symbols: str = "BTC-USDT,ETH-USDT",
        strategies: str = "SMACrossover,SwingTrader,PositionTrader",
    ) -> dict:
        """
        Scan for trading opportunities across symbols and strategies.

        Args:
            symbols: Comma-separated list of symbols
            strategies: Comma-separated list of strategies

        Returns:
            List of trading opportunities with signals and confidence
        """
        from jesse_mcp.monitoring import MarketMonitor

        symbol_list = [s.strip() for s in symbols.split(",")]
        strategy_list = [s.strip() for s in strategies.split(",")]

        monitor = MarketMonitor(symbols=symbol_list, strategies=strategy_list)
        opportunities = monitor.scan_opportunities()

        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": __import__("datetime")
            .datetime.now(__import__("datetime").timezone.utc)
            .isoformat(),
        }

    @mcp.tool
    def monitor_get_risks() -> dict:
        """
        Identify current market risks and warning signs.

        Returns:
            List of identified risks with severity levels
        """
        from jesse_mcp.monitoring import MarketMonitor

        monitor = MarketMonitor()
        risks = monitor.identify_risks()
        fg = monitor.get_fear_greed()

        return {
            "risks": risks,
            "fear_greed_score": fg.get("score", 50),
            "risk_level": "high" if len(risks) >= 3 else "medium" if len(risks) >= 1 else "low",
        }

    logger.info("✅ All 19 agent tools registered with MCP")
