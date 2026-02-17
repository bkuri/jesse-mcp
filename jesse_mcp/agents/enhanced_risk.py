"""
Enhanced Risk Management Agent with Hierarchical Configuration

Integrates with the new configuration system to provide:
- Risk profile-based analysis
- Dynamic portfolio limit management
- Stage-aware risk assessment
- News-driven risk adjustments
"""

from typing import Dict, Any, List, Optional
import logging
from jesse_mcp.agents.base import BaseJesseAgent
from jesse_mcp.config import (
    ConfigurationManager,
    RiskProfile,
    TradingStage,
    RiskSettings,
    PortfolioLimits,
)

logger = logging.getLogger(__name__)


class EnhancedRiskAgent(BaseJesseAgent):
    """Enhanced risk management agent with hierarchical configuration support.

    This agent provides:
    - Risk profile-based analysis (Conservative, Moderate, Aggressive)
    - Stage-aware risk assessment (Exploration, Paper, Live)
    - Dynamic portfolio limit enforcement
    - News-driven risk adjustments
    - Real-time risk monitoring and alerts
    """

    def __init__(self, config_manager: Optional[ConfigurationManager] = None):
        """Initialize enhanced risk agent

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config_manager = config_manager or ConfigurationManager()
        self._config = self.config_manager.load_config()

    @property
    def system_prompt(self) -> str:
        """Return enhanced system prompt for hierarchical risk management."""
        return """You are an Enhanced Risk Management Expert for the Jesse trading platform with hierarchical configuration capabilities.

Your expertise includes:
- Multi-tier risk profile management (Conservative, Moderate, Aggressive)
- Stage-based risk assessment (Exploration → Paper → Live)
- Dynamic portfolio limit enforcement and monitoring
- News-driven risk adjustments and sentiment analysis
- Real-time risk metrics calculation and alerting
- Correlation analysis and concentration risk management
- Value-at-Risk (VaR) and stress testing across risk profiles
- Position sizing optimization based on risk tolerance
- Leverage risk assessment and margin management
- Emergency stop and circuit breaker implementation

When analyzing risk:
1. Apply the appropriate risk profile settings (Conservative/Moderate/Aggressive)
2. Consider the current trading stage (Exploration/Paper/Live)
3. Enforce portfolio limits and position sizing rules
4. Analyze news sentiment and adjust risk parameters dynamically
5. Monitor real-time risk metrics and trigger alerts
6. Provide specific risk mitigation strategies
7. Recommend portfolio rebalancing when needed

Always provide:
- Current risk metrics vs. profile thresholds
- Portfolio concentration and correlation analysis
- News sentiment impact on risk parameters
- Specific actionable risk controls
- Expected impact on returns and volatility
- Stage-appropriate risk recommendations

Focus on dynamic, adaptive risk management that responds to market conditions while maintaining profile discipline."""

    def analyze_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> str:
        """Analyze portfolio risk using hierarchical configuration.

        Args:
            portfolio_data: Portfolio positions, balances, and metrics

        Returns:
            Comprehensive risk analysis with profile-specific insights
        """
        message = (
            f"Analyze portfolio risk using hierarchical configuration: {portfolio_data}. "
            f"Provide: 1) Risk profile compliance analysis, "
            f"2) Portfolio limit adherence check, "
            f"3) Concentration and correlation risk, "
            f"4) Stage-appropriate risk assessment, "
            f"5) News sentiment impact on current positions, "
            f"6) Specific risk mitigation recommendations"
        )
        self.add_to_history("user", message)
        return message

    def validate_risk_profile_compliance(
        self, strategy_name: str, proposed_trades: List[Dict[str, Any]]
    ) -> str:
        """Validate trades against risk profile settings.

        Args:
            strategy_name: Strategy proposing trades
            proposed_trades: List of proposed trade configurations

        Returns:
            Compliance analysis and approval/rejection recommendations
        """
        risk_settings = self.config_manager.get_effective_risk_settings(strategy_name)

        message = (
            f"Validate {len(proposed_trades)} proposed trades for strategy '{strategy_name}' "
            f"against risk profile settings. Risk limits: max_position={risk_settings.max_position_size:.2%}, "
            f"max_portfolio_risk={risk_settings.max_portfolio_risk:.2%}, "
            f"max_leverage={risk_settings.max_leverage}x. "
            f"Provide: 1) Trade-by-trade compliance check, "
            f"2) Portfolio-level risk aggregation, "
            f"3) Approval/rejection recommendations with reasons, "
            f"4) Required position size adjustments"
        )
        self.add_to_history("user", message)
        return message

    def assess_stage_transition_risk(
        self, from_stage: TradingStage, to_stage: TradingStage
    ) -> str:
        """Assess risks of transitioning between trading stages.

        Args:
            from_stage: Current trading stage
            to_stage: Target trading stage

        Returns:
            Stage transition risk analysis and requirements
        """
        message = (
            f"Assess risks of transitioning from {from_stage.value} to {to_stage.value} stage. "
            f"Provide: 1) Risk parameter changes required, "
            f"2) Additional safeguards needed for higher-risk stages, "
            f"3) Performance thresholds that must be met, "
            f"4) Monitoring and alert requirements, "
            f"5) Rollback criteria and procedures"
        )
        self.add_to_history("user", message)
        return message

    def dynamic_risk_adjustment(
        self, news_sentiment: Dict[str, float], market_volatility: float
    ) -> str:
        """Adjust risk parameters based on news and market conditions.

        Args:
            news_sentiment: Sentiment scores by news source
            market_volatility: Current market volatility index

        Returns:
            Dynamic risk adjustment recommendations
        """
        message = (
            f"Adjust risk parameters based on current conditions: "
            f"news_sentiment={news_sentiment}, market_volatility={market_volatility:.2f}. "
            f"Provide: 1) Risk parameter adjustments (position sizes, stops), "
            f"2) Portfolio limit modifications, "
            f"3) News source priority reweighting if needed, "
            f"4) Temporary risk controls for high volatility periods, "
            f"5) Alert thresholds for monitoring"
        )
        self.add_to_history("user", message)
        return message

    def portfolio_limit_monitoring(self, current_metrics: Dict[str, Any]) -> str:
        """Monitor and enforce portfolio limits in real-time.

        Args:
            current_metrics: Current portfolio metrics and usage

        Returns:
            Limit compliance status and enforcement actions
        """
        limits = self._config.portfolio_limits

        message = (
            f"Monitor portfolio limits compliance: {current_metrics}. "
            f"Limits: max_positions={limits.max_total_positions}, max_open={limits.max_open_positions}, "
            f"max_daily_trades={limits.max_daily_trades}, max_account_usage={limits.max_account_usage:.1%}. "
            f"Provide: 1) Current usage vs. limits for each metric, "
            f"2) Approaching limit warnings, "
            f"3) Violation alerts and required actions, "
            f"4) Recommendations for limit adjustments if needed"
        )
        self.add_to_history("user", message)
        return message

    def stress_test_with_news_scenarios(
        self, portfolio: Dict[str, Any], news_scenarios: List[Dict[str, Any]]
    ) -> str:
        """Perform stress testing with news-driven scenarios.

        Args:
            portfolio: Current portfolio composition
            news_scenarios: List of news event scenarios

        Returns:
            Stress test results with news impact analysis
        """
        message = (
            f"Stress test portfolio {portfolio} against {len(news_scenarios)} news scenarios. "
            f"Provide: 1) Portfolio impact per scenario, "
            f"2) Worst-case loss estimates, "
            f"3) Correlation breakdown effects, "
            f"4) News sentiment amplification factors, "
            f"5) Risk mitigation strategies for each scenario type"
        )
        self.add_to_history("user", message)
        return message

    def recommend_risk_profile_adjustment(
        self, strategy_name: str, performance_metrics: Dict[str, float]
    ) -> str:
        """Recommend risk profile adjustments based on performance.

        Args:
            strategy_name: Strategy to analyze
            performance_metrics: Recent performance metrics

        Returns:
            Risk profile adjustment recommendations
        """
        current_config = self.config_manager.get_strategy_config(strategy_name)

        message = (
            f"Analyze risk profile suitability for strategy '{strategy_name}' "
            f"(current: {current_config.risk_profile.value}) based on performance: {performance_metrics}. "
            f"Provide: 1) Performance vs. risk profile analysis, "
            f"2) Recommended profile changes (Conservative/Moderate/Aggressive), "
            f"3) Specific parameter adjustments needed, "
            f"4) Expected impact on risk/return profile, "
            f"5) Implementation timeline and monitoring requirements"
        )
        self.add_to_history("user", message)
        return message

    def emergency_risk_assessment(
        self, market_event: str, portfolio_impact: Dict[str, float]
    ) -> str:
        """Provide emergency risk assessment for market events.

        Args:
            market_event: Description of market event
            portfolio_impact: Estimated portfolio impact

        Returns:
            Emergency risk assessment and immediate actions
        """
        message = (
            f"Emergency risk assessment for market event: {market_event}. "
            f"Portfolio impact: {portfolio_impact}. "
            f"Provide: 1) Immediate risk control actions needed, "
            f"2) Emergency stop triggers and levels, "
            f"3) Position liquidation priorities, "
            f"4) Circuit breaker activation criteria, "
            f"5) Communication and monitoring procedures"
        )
        self.add_to_history("user", message)
        return message

    def correlation_risk_monitoring(
        self, portfolio_correlations: Dict[str, float]
    ) -> str:
        """Monitor and manage portfolio correlation risk.

        Args:
            portfolio_correlations: Correlation matrix of portfolio assets

        Returns:
            Correlation risk analysis and diversification recommendations
        """
        max_correlation = self._config.global_risk_settings.max_correlation

        message = (
            f"Analyze portfolio correlation risk: {portfolio_correlations}. "
            f"Max allowed correlation: {max_correlation:.1%}. "
            f"Provide: 1) High correlation pairs identification, "
            f"2) Concentration risk hotspots, "
            f"3) Diversification recommendations, "
            f"4) Hedge pair suggestions, "
            f"5) Correlation monitoring thresholds"
        )
        self.add_to_history("user", message)
        return message
