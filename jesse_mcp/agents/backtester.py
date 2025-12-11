"""Backtesting and Analysis Agent for Jesse trading platform."""

from jesse_mcp.agents.base import BaseJesseAgent


class BacktestingAgent(BaseJesseAgent):
    """Agent specialized in backtesting strategies and extracting insights.

    This agent focuses on:
    - Designing effective backtest scenarios
    - Comparing multiple strategy configurations
    - Extracting actionable performance metrics
    - Stress testing with historical scenarios
    - Generating comprehensive analysis reports
    """

    @property
    def system_prompt(self) -> str:
        """Return the specialized system prompt for backtesting and analysis."""
        return """You are a Backtesting and Analysis Expert for the Jesse trading platform.

Your expertise includes:
- Designing comprehensive backtest scenarios
- Comparing strategy performance across timeframes and market conditions
- Extracting key metrics: Sharpe ratio, profit factor, win rate, etc.
- Identifying data quality and survivorship bias issues
- Monte Carlo simulation for robustness analysis
- Walk-forward optimization to avoid overfitting
- Batch backtesting across multiple pairs and configurations
- Analyzing regime-dependent performance
- Factor analysis for performance attribution

When backtesting strategies:
1. Design tests across multiple timeframes (daily, 4h, 1h, 15m)
2. Include diverse market conditions (trending, ranging, volatile)
3. Validate against multiple data sources when possible
4. Use walk-forward testing to avoid overfitting
5. Perform Monte Carlo simulations for robustness
6. Extract both quantitative and qualitative insights
7. Identify edge cases and stress scenarios

Always provide:
- Performance metrics with context (what they mean)
- Risk-adjusted returns (Sharpe, Sortino ratios)
- Drawdown analysis and recovery patterns
- Trade distribution and quality analysis
- Regime-dependent performance
- Statistical significance of results
- Key findings and actionable insights

Focus on statistically significant, implementable findings that generalize to live trading."""

    def backtest_strategy(
        self, strategy_name: str, pair: str, start_date: str, end_date: str
    ) -> str:
        """Design and run a comprehensive backtest.

        Args:
            strategy_name: Strategy to backtest
            pair: Trading pair (e.g., 'BTCUSDT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Backtest results and analysis
        """
        message = (
            f"Run a comprehensive backtest of '{strategy_name}' on {pair} "
            f"from {start_date} to {end_date}. Analyze: "
            f"1) Performance metrics (returns, Sharpe, win rate), "
            f"2) Trade quality and distribution, "
            f"3) Drawdown patterns, "
            f"4) Key insights and recommendations"
        )
        self.add_to_history("user", message)
        return message

    def compare_timeframes(self, strategy_name: str, pair: str) -> str:
        """Compare strategy performance across different timeframes.

        Args:
            strategy_name: Strategy to test
            pair: Trading pair

        Returns:
            Cross-timeframe comparison analysis
        """
        message = (
            f"Compare performance of '{strategy_name}' on {pair} across timeframes "
            f"(1m, 5m, 15m, 1h, 4h, 1d). Show: "
            f"1) Performance metrics for each timeframe, "
            f"2) Trade frequency and quality differences, "
            f"3) Optimal timeframe(s), "
            f"4) Timeframe-specific insights"
        )
        self.add_to_history("user", message)
        return message

    def optimize_parameters(
        self, strategy_name: str, pair: str, param_name: str, param_range: str
    ) -> str:
        """Find optimal parameter values through systematic testing.

        Args:
            strategy_name: Strategy with parameter to optimize
            pair: Trading pair
            param_name: Parameter name (e.g., 'period', 'threshold')
            param_range: Range to test (e.g., '10-100')

        Returns:
            Parameter optimization results
        """
        message = (
            f"Optimize the '{param_name}' parameter of '{strategy_name}' "
            f"on {pair} over range {param_range}. Provide: "
            f"1) Performance curve across parameter values, "
            f"2) Optimal value(s), "
            f"3) Sensitivity analysis, "
            f"4) Robustness of optimum across market conditions"
        )
        self.add_to_history("user", message)
        return message

    def monte_carlo_analysis(self, strategy_name: str, pair: str) -> str:
        """Perform Monte Carlo simulation for strategy robustness.

        Args:
            strategy_name: Strategy to analyze
            pair: Trading pair

        Returns:
            Monte Carlo analysis and robustness assessment
        """
        message = (
            f"Perform Monte Carlo analysis of '{strategy_name}' on {pair}. "
            f"Show: 1) Distribution of outcomes, "
            f"2) Confidence intervals, "
            f"3) Worst-case scenarios, "
            f"4) Robustness assessment"
        )
        self.add_to_history("user", message)
        return message

    def analyze_regime_performance(self, strategy_name: str, pair: str) -> str:
        """Analyze strategy performance in different market regimes.

        Args:
            strategy_name: Strategy to analyze
            pair: Trading pair

        Returns:
            Regime-dependent performance analysis
        """
        message = (
            f"Analyze '{strategy_name}' on {pair} across different market regimes "
            f"(trending up, trending down, ranging, volatile). Show: "
            f"1) Performance in each regime, "
            f"2) Regime detection indicators, "
            f"3) Regime-specific improvements, "
            f"4) Switching or adaptation recommendations"
        )
        self.add_to_history("user", message)
        return message

    def validate_statistical_significance(self, strategy_name: str, pair: str) -> str:
        """Validate that backtest results are statistically significant.

        Args:
            strategy_name: Strategy to validate
            pair: Trading pair

        Returns:
            Statistical significance assessment
        """
        message = (
            f"Validate the statistical significance of '{strategy_name}' "
            f"on {pair}. Assess: "
            f"1) Minimum sample size requirements, "
            f"2) Significance of edge (vs. random), "
            f"3) Overfitting risk, "
            f"4) Confidence in live trading potential"
        )
        self.add_to_history("user", message)
        return message
