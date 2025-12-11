"""Strategy Optimization Agent for Jesse trading platform."""

from jesse_mcp.agents.base import BaseJesseAgent


class StrategyOptimizationAgent(BaseJesseAgent):
    """Agent specialized in analyzing and improving trading strategies.

    This agent focuses on:
    - Analyzing backtest results for performance weaknesses
    - Identifying under-performing trading pairs
    - Recommending improvements to strategy logic
    - Suggesting position sizing adjustments
    - Tracking optimization history and effectiveness
    """

    @property
    def system_prompt(self) -> str:
        """Return the specialized system prompt for strategy optimization."""
        return """You are a Strategy Optimization Expert for the Jesse trading platform.

Your expertise includes:
- Deep analysis of backtest results (profit factor, win rate, drawdown, Sharpe ratio)
- Identifying profitable vs unprofitable trading pairs
- Optimizing entry/exit logic and indicator parameters
- Adjusting position sizing and risk management
- Detecting market regime changes affecting strategy performance
- Suggesting concrete improvements with expected impact estimates

When analyzing strategies:
1. First, run comprehensive backtests across multiple timeframes
2. Identify the top and bottom performing pairs
3. Analyze what makes successful pairs different
4. Suggest specific, testable improvements
5. Recommend A/B testing new ideas against current baseline
6. Track optimization iterations and their results

Always provide:
- Current performance metrics
- Identified weaknesses or opportunities
- Specific, actionable recommendations
- Expected improvements if recommendations are implemented
- Testing methodology to validate improvements

Focus on sustainable improvements that work across different market conditions."""

    def suggest_improvements(self, strategy_name: str, pair: str) -> str:
        """Suggest specific improvements for a strategy/pair combination.

        Args:
            strategy_name: Name of the strategy to optimize
            pair: Trading pair to analyze (e.g., 'BTCUSDT')

        Returns:
            Analysis and recommendations for improvement
        """
        message = (
            f"Analyze the strategy '{strategy_name}' on pair '{pair}' and "
            f"suggest specific improvements. Include: "
            f"1) Current performance metrics, "
            f"2) Identified weaknesses, "
            f"3) Specific changes to test, "
            f"4) Expected improvements"
        )
        self.add_to_history("user", message)
        return message

    def compare_strategies(self, strategy1: str, strategy2: str) -> str:
        """Compare two strategies to identify best practices.

        Args:
            strategy1: First strategy name
            strategy2: Second strategy name

        Returns:
            Comparative analysis and insights
        """
        message = (
            f"Compare '{strategy1}' and '{strategy2}' strategies. "
            f"Analyze: 1) Performance metrics comparison, "
            f"2) Risk profile differences, "
            f"3) Which performs better in different market conditions, "
            f"4) Key differences in logic/parameters that drive performance"
        )
        self.add_to_history("user", message)
        return message

    def optimize_pair_selection(self, strategy_name: str) -> str:
        """Analyze which pairs to trade for a given strategy.

        Args:
            strategy_name: Strategy to optimize pair selection for

        Returns:
            Analysis of best-performing pairs and recommendations
        """
        message = (
            f"Analyze which trading pairs work best with '{strategy_name}'. "
            f"Provide: 1) Performance ranking of pairs, "
            f"2) Common characteristics of profitable pairs, "
            f"3) Pairs to avoid, "
            f"4) Recommended pair selection for future trading"
        )
        self.add_to_history("user", message)
        return message

    def analyze_optimization_impact(self, change_description: str) -> str:
        """Estimate the impact of a proposed change.

        Args:
            change_description: Description of the proposed change

        Returns:
            Impact analysis and testing recommendations
        """
        message = (
            f"Analyze the potential impact of this change: {change_description}. "
            f"Provide: 1) Expected benefits and risks, "
            f"2) Testing methodology, "
            f"3) Key metrics to monitor, "
            f"4) Success criteria"
        )
        self.add_to_history("user", message)
        return message
