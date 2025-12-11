"""Risk Management Agent for Jesse trading platform."""

from jesse_mcp.agents.base import BaseJesseAgent


class RiskManagementAgent(BaseJesseAgent):
    """Agent specialized in analyzing and mitigating trading risks.

    This agent focuses on:
    - Portfolio concentration and correlation analysis
    - Drawdown and leverage risk assessment
    - Asset-specific risk identification
    - Hedging strategy recommendations
    - Portfolio-level risk metric calculation
    """

    @property
    def system_prompt(self) -> str:
        """Return the specialized system prompt for risk management."""
        return """You are a Risk Management Expert for the Jesse trading platform.

Your expertise includes:
- Portfolio concentration risk analysis
- Correlation and diversification assessment
- Maximum drawdown and recovery time analysis
- Value-at-Risk (VaR) and expected shortfall calculations
- Stress testing under extreme market conditions
- Position sizing relative to account risk tolerance
- Leverage and margin risk evaluation
- Hedging strategy design
- Risk-adjusted performance metrics (Sharpe ratio, Sortino ratio)

When analyzing portfolio risk:
1. Calculate aggregate portfolio metrics (correlation, concentration)
2. Identify concentrated positions or correlated assets
3. Analyze drawdown history and recovery patterns
4. Perform stress tests with historical and hypothetical scenarios
5. Suggest diversification or hedging approaches
6. Recommend position sizing adjustments for risk targets

Always provide:
- Current risk metrics and their implications
- Risk hotspots (concentrated positions, high correlations, etc.)
- Specific risk mitigation strategies
- Expected impact on returns and volatility
- Acceptable risk tolerance parameters for the portfolio

Focus on practical, implementable risk controls that balance protection with returns."""

    def analyze_portfolio_risk(self, pairs: list[str]) -> str:
        """Analyze risk profile of a trading portfolio.

        Args:
            pairs: List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])

        Returns:
            Portfolio risk analysis and recommendations
        """
        pairs_str = ", ".join(pairs)
        message = (
            f"Analyze the portfolio risk of trading pairs: {pairs_str}. "
            f"Provide: 1) Correlation analysis, "
            f"2) Concentration risk assessment, "
            f"3) Diversification recommendations, "
            f"4) Optimal position sizes to manage risk"
        )
        self.add_to_history("user", message)
        return message

    def stress_test_portfolio(self, pairs: list[str], scenario: str) -> str:
        """Perform stress testing on portfolio under market scenarios.

        Args:
            pairs: Trading pairs to stress test
            scenario: Market scenario (e.g., 'market crash', 'flash crash', 'liquidity crisis')

        Returns:
            Stress test analysis and resilience recommendations
        """
        pairs_str = ", ".join(pairs)
        message = (
            f"Stress test the portfolio of {pairs_str} under a {scenario} scenario. "
            f"Show: 1) Expected losses, 2) Portfolio drawdown, "
            f"3) Correlation breakdowns, 4) Risk mitigation strategies"
        )
        self.add_to_history("user", message)
        return message

    def assess_leverage_risk(self, strategy_name: str, leverage: float) -> str:
        """Assess risks of trading with leverage.

        Args:
            strategy_name: Strategy using leverage
            leverage: Leverage multiplier (e.g., 2.0 for 2x)

        Returns:
            Leverage risk assessment and recommendations
        """
        message = (
            f"Analyze the leverage risk of '{strategy_name}' using {leverage}x leverage. "
            f"Provide: 1) Liquidation risk analysis, "
            f"2) Margin requirement implications, "
            f"3) Safe leverage levels, "
            f"4) Risk controls needed"
        )
        self.add_to_history("user", message)
        return message

    def recommend_hedges(self, pair: str, risk_type: str) -> str:
        """Recommend hedging strategies for specific risks.

        Args:
            pair: Trading pair to hedge (e.g., 'BTCUSDT')
            risk_type: Type of risk (e.g., 'downside', 'volatility', 'correlation')

        Returns:
            Hedging strategy recommendations
        """
        message = (
            f"Recommend hedging strategies for '{pair}' against {risk_type} risk. "
            f"Include: 1) Hedging instruments or pairs, "
            f"2) Hedge sizing, "
            f"3) Cost-benefit analysis, "
            f"4) Implementation approach"
        )
        self.add_to_history("user", message)
        return message

    def analyze_drawdown_recovery(self, strategy_name: str) -> str:
        """Analyze historical drawdowns and recovery patterns.

        Args:
            strategy_name: Strategy to analyze

        Returns:
            Drawdown analysis and recovery insights
        """
        message = (
            f"Analyze the drawdown and recovery patterns of '{strategy_name}'. "
            f"Show: 1) Historical max drawdown, "
            f"2) Average recovery time, "
            f"3) Drawdown triggers and causes, "
            f"4) Strategies to reduce future drawdowns"
        )
        self.add_to_history("user", message)
        return message
