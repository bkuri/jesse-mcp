"""
Configuration Management for Hierarchical Trading System

Provides:
- Global risk profiles (Conservative, Moderate, Aggressive)
- Per-strategy overrides
- Dynamic news source priorities
- Portfolio limits management
- Configuration validation and testing
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskProfile(Enum):
    """Risk profile levels"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class TradingStage(Enum):
    """Trading stages"""

    EXPLORATION = "exploration"
    PAPER = "paper"
    LIVE = "live"


class NewsSource(Enum):
    """Available news sources"""

    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    COINDESK = "coindesk"
    CRYPTOPANIC = "cryptopanic"
    TWITTER = "twitter"
    REDDIT = "reddit"
    TELEGRAM = "telegram"


@dataclass
class RiskSettings:
    """Risk configuration settings"""

    max_portfolio_risk: float = 0.02  # 2% max portfolio risk
    max_position_size: float = 0.1  # 10% max per position
    max_leverage: float = 1.0  # 1x leverage default
    max_drawdown: float = 0.15  # 15% max drawdown
    stop_loss: float = 0.02  # 2% stop loss
    take_profit: float = 0.04  # 4% take profit
    max_correlation: float = 0.7  # 70% max correlation
    var_confidence: float = 0.95  # 95% VaR
    emergency_stop: float = 0.25  # 25% emergency stop


@dataclass
class NewsPriority:
    """News source priority configuration"""

    source: NewsSource
    priority: int  # Lower number = higher priority
    weight: float  # Weight in scoring (0-1)
    enabled: bool = True
    filters: List[str] = field(default_factory=list)  # Keyword filters


@dataclass
class StrategyConfig:
    """Per-strategy configuration"""

    name: str
    risk_profile: RiskProfile
    risk_overrides: Optional[RiskSettings] = None
    news_priorities: List[NewsPriority] = field(default_factory=list)
    enabled: bool = True
    stage: TradingStage = TradingStage.EXPLORATION
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioLimits:
    """Portfolio-wide limits"""

    max_total_positions: int = 10
    max_open_positions: int = 5
    max_daily_trades: int = 20
    max_weekly_trades: int = 50
    max_monthly_trades: int = 200
    position_timeout_hours: int = 72
    min_account_balance: float = 1000
    max_account_usage: float = 0.95


@dataclass
class TradingConfig:
    """Complete trading configuration"""

    global_risk_profile: RiskProfile
    global_risk_settings: RiskSettings
    news_priorities: List[NewsPriority]
    portfolio_limits: PortfolioLimits
    strategies: Dict[str, StrategyConfig]
    stage: TradingStage = TradingStage.EXPLORATION
    zai_glm_config: Dict[str, Any] = field(default_factory=dict)
    mcp_config: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """Manages hierarchical trading configuration"""

    # Default risk profiles
    DEFAULT_RISK_PROFILES = {
        RiskProfile.CONSERVATIVE: RiskSettings(
            max_portfolio_risk=0.01,  # 1%
            max_position_size=0.05,  # 5%
            max_leverage=1.0,
            max_drawdown=0.10,  # 10%
            stop_loss=0.015,  # 1.5%
            take_profit=0.025,  # 2.5%
            max_correlation=0.5,  # 50%
            var_confidence=0.99,  # 99% VaR
            emergency_stop=0.15,  # 15%
        ),
        RiskProfile.MODERATE: RiskSettings(
            max_portfolio_risk=0.02,  # 2%
            max_position_size=0.10,  # 10%
            max_leverage=2.0,
            max_drawdown=0.15,  # 15%
            stop_loss=0.02,  # 2%
            take_profit=0.04,  # 4%
            max_correlation=0.7,  # 70%
            var_confidence=0.95,  # 95% VaR
            emergency_stop=0.25,  # 25%
        ),
        RiskProfile.AGGRESSIVE: RiskSettings(
            max_portfolio_risk=0.04,  # 4%
            max_position_size=0.20,  # 20%
            max_leverage=5.0,
            max_drawdown=0.25,  # 25%
            stop_loss=0.03,  # 3%
            take_profit=0.06,  # 6%
            max_correlation=0.8,  # 80%
            var_confidence=0.90,  # 90% VaR
            emergency_stop=0.35,  # 35%
        ),
    }

    # Default news priorities
    DEFAULT_NEWS_PRIORITIES = [
        NewsPriority(NewsSource.REUTERS, 1, 0.25),
        NewsPriority(NewsSource.BLOOMBERG, 2, 0.20),
        NewsPriority(NewsSource.COINDESK, 3, 0.15),
        NewsPriority(NewsSource.CRYPTOPANIC, 4, 0.15),
        NewsPriority(NewsSource.TWITTER, 5, 0.10),
        NewsPriority(NewsSource.REDDIT, 6, 0.10),
        NewsPriority(NewsSource.TELEGRAM, 7, 0.05),
    ]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self._config: Optional[TradingConfig] = None

    def load_config(self, config_path: Optional[str] = None) -> TradingConfig:
        """Load configuration from file

        Args:
            config_path: Path to config file (overrides instance path)

        Returns:
            TradingConfig instance
        """
        path = Path(config_path) if config_path else self.config_path
        if not path or not path.exists():
            logger.info("Config file not found, creating default configuration")
            return self.create_default_config()

        try:
            with open(path, "r") as f:
                data = json.load(f)
            self._config = self._parse_config(data)
            logger.info(f"Loaded configuration from {path}")
            return self._config
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            return self.create_default_config()

    def save_config(
        self, config: TradingConfig, config_path: Optional[str] = None
    ) -> bool:
        """Save configuration to file

        Args:
            config: Configuration to save
            config_path: Path to save to (overrides instance path)

        Returns:
            True if successful
        """
        path = Path(config_path) if config_path else self.config_path
        if not path:
            logger.error("No config path specified")
            return False

        try:
            data = self._serialize_config(config)
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved configuration to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
            return False

    def create_default_config(self) -> TradingConfig:
        """Create default configuration

        Returns:
            Default TradingConfig
        """
        self._config = TradingConfig(
            global_risk_profile=RiskProfile.MODERATE,
            global_risk_settings=self.DEFAULT_RISK_PROFILES[RiskProfile.MODERATE],
            news_priorities=self.DEFAULT_NEWS_PRIORITIES.copy(),
            portfolio_limits=PortfolioLimits(),
            strategies={},
        )
        return self._config

    def get_strategy_config(self, strategy_name: str) -> StrategyConfig:
        """Get configuration for a specific strategy

        Args:
            strategy_name: Strategy name

        Returns:
            StrategyConfig with merged global and strategy-specific settings
        """
        if not self._config:
            self._config = self.load_config()

        if strategy_name not in self._config.strategies:
            # Create default strategy config
            strategy_config = StrategyConfig(
                name=strategy_name,
                risk_profile=self._config.global_risk_profile,
                news_priorities=self._config.news_priorities.copy(),
            )
            self._config.strategies[strategy_name] = strategy_config

        return self._config.strategies[strategy_name]

    def get_effective_risk_settings(self, strategy_name: str) -> RiskSettings:
        """Get effective risk settings for a strategy (global + overrides)

        Args:
            strategy_name: Strategy name

        Returns:
            Merged RiskSettings
        """
        if not self._config:
            self._config = self.load_config()

        strategy_config = self.get_strategy_config(strategy_name)
        global_settings = self._config.global_risk_settings

        if strategy_config.risk_overrides:
            # Merge strategy overrides with global settings
            effective = RiskSettings()
            for field_name in RiskSettings.__dataclass_fields__:
                global_value = getattr(global_settings, field_name)
                override_value = getattr(strategy_config.risk_overrides, field_name)
                setattr(
                    effective,
                    field_name,
                    override_value if override_value != global_value else global_value,
                )
            return effective
        else:
            # Use global settings for this risk profile
            return self.DEFAULT_RISK_PROFILES[strategy_config.risk_profile]

    def update_news_priority(
        self, source: NewsSource, priority: int, weight: float
    ) -> bool:
        """Update news source priority

        Args:
            source: News source to update
            priority: New priority (lower = higher)
            weight: New weight (0-1)

        Returns:
            True if successful
        """
        if not self._config:
            self.load_config()

        # Find and update the news priority
        for news_prio in self._config.news_priorities:
            if news_prio.source == source:
                news_prio.priority = priority
                news_prio.weight = weight
                logger.info(
                    f"Updated {source.value} priority to {priority}, weight to {weight}"
                )
                return True

        # Add new priority if not found
        self._config.news_priorities.append(NewsPriority(source, priority, weight))
        logger.info(f"Added new {source.value} priority")
        return True

    def validate_config(self, config: TradingConfig) -> List[str]:
        """Validate configuration for consistency and errors

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Validate risk settings
        if config.global_risk_settings.max_position_size > 1.0:
            errors.append("Max position size cannot exceed 100%")
        if config.global_risk_settings.max_leverage < 1.0:
            errors.append("Max leverage must be at least 1x")
        if (
            config.global_risk_settings.stop_loss
            >= config.global_risk_settings.take_profit
        ):
            errors.append("Stop loss must be less than take profit")

        # Validate portfolio limits
        if (
            config.portfolio_limits.max_open_positions
            > config.portfolio_limits.max_total_positions
        ):
            errors.append("Max open positions cannot exceed max total positions")
        if (
            config.portfolio_limits.max_daily_trades
            > config.portfolio_limits.max_weekly_trades
        ):
            errors.append("Max daily trades cannot exceed max weekly trades")

        # Validate news priorities
        priorities = [p.priority for p in config.news_priorities if p.enabled]
        if len(set(priorities)) != len(priorities):
            errors.append("News source priorities must be unique")

        total_weight = sum(p.weight for p in config.news_priorities if p.enabled)
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"News weights must sum to 1.0 (current: {total_weight:.3f})")

        return errors

    def _parse_config(self, data: Dict[str, Any]) -> TradingConfig:
        """Parse configuration data from dict

        Args:
            data: Configuration data

        Returns:
            TradingConfig instance
        """
        # Parse risk settings
        risk_data = data.get("global_risk_settings", {})
        risk_settings = RiskSettings(**risk_data)

        # Parse news priorities
        news_data = data.get("news_priorities", [])
        news_priorities = [
            NewsPriority(
                source=NewsSource(n["source"]),
                priority=n["priority"],
                weight=n["weight"],
                enabled=n.get("enabled", True),
                filters=n.get("filters", []),
            )
            for n in news_data
        ]

        # Parse portfolio limits
        portfolio_data = data.get("portfolio_limits", {})
        portfolio_limits = PortfolioLimits(**portfolio_data)

        # Parse strategies
        strategies = {}
        for name, strat_data in data.get("strategies", {}).items():
            risk_overrides = None
            if "risk_overrides" in strat_data:
                risk_overrides = RiskSettings(**strat_data["risk_overrides"])

            strategies[name] = StrategyConfig(
                name=name,
                risk_profile=RiskProfile(strat_data["risk_profile"]),
                risk_overrides=risk_overrides,
                news_priorities=[
                    NewsPriority(
                        source=NewsSource(n["source"]),
                        priority=n["priority"],
                        weight=n["weight"],
                        enabled=n.get("enabled", True),
                        filters=n.get("filters", []),
                    )
                    for n in strat_data.get("news_priorities", [])
                ],
                enabled=strat_data.get("enabled", True),
                stage=TradingStage(strat_data.get("stage", "exploration")),
                custom_params=strat_data.get("custom_params", {}),
            )

        return TradingConfig(
            global_risk_profile=RiskProfile(data["global_risk_profile"]),
            global_risk_settings=risk_settings,
            news_priorities=news_priorities,
            portfolio_limits=portfolio_limits,
            strategies=strategies,
            stage=TradingStage(data.get("stage", "exploration")),
            zai_glm_config=data.get("zai_glm_config", {}),
            mcp_config=data.get("mcp_config", {}),
        )

    def _serialize_config(self, config: TradingConfig) -> Dict[str, Any]:
        """Serialize configuration to dict

        Args:
            config: Configuration to serialize

        Returns:
            Dictionary representation
        """
        return {
            "global_risk_profile": config.global_risk_profile.value,
            "global_risk_settings": {
                "max_portfolio_risk": config.global_risk_settings.max_portfolio_risk,
                "max_position_size": config.global_risk_settings.max_position_size,
                "max_leverage": config.global_risk_settings.max_leverage,
                "max_drawdown": config.global_risk_settings.max_drawdown,
                "stop_loss": config.global_risk_settings.stop_loss,
                "take_profit": config.global_risk_settings.take_profit,
                "max_correlation": config.global_risk_settings.max_correlation,
                "var_confidence": config.global_risk_settings.var_confidence,
                "emergency_stop": config.global_risk_settings.emergency_stop,
            },
            "news_priorities": [
                {
                    "source": p.source.value,
                    "priority": p.priority,
                    "weight": p.weight,
                    "enabled": p.enabled,
                    "filters": p.filters,
                }
                for p in config.news_priorities
            ],
            "portfolio_limits": {
                "max_total_positions": config.portfolio_limits.max_total_positions,
                "max_open_positions": config.portfolio_limits.max_open_positions,
                "max_daily_trades": config.portfolio_limits.max_daily_trades,
                "max_weekly_trades": config.portfolio_limits.max_weekly_trades,
                "max_monthly_trades": config.portfolio_limits.max_monthly_trades,
                "position_timeout_hours": config.portfolio_limits.position_timeout_hours,
                "min_account_balance": config.portfolio_limits.min_account_balance,
                "max_account_usage": config.portfolio_limits.max_account_usage,
            },
            "strategies": {
                name: {
                    "risk_profile": strat.risk_profile.value,
                    "risk_overrides": {
                        "max_portfolio_risk": strat.risk_overrides.max_portfolio_risk,
                        "max_position_size": strat.risk_overrides.max_position_size,
                        "max_leverage": strat.risk_overrides.max_leverage,
                        "max_drawdown": strat.risk_overrides.max_drawdown,
                        "stop_loss": strat.risk_overrides.stop_loss,
                        "take_profit": strat.risk_overrides.take_profit,
                        "max_correlation": strat.risk_overrides.max_correlation,
                        "var_confidence": strat.risk_overrides.var_confidence,
                        "emergency_stop": strat.risk_overrides.emergency_stop,
                    }
                    if strat.risk_overrides
                    else None,
                    "news_priorities": [
                        {
                            "source": p.source.value,
                            "priority": p.priority,
                            "weight": p.weight,
                            "enabled": p.enabled,
                            "filters": p.filters,
                        }
                        for p in strat.news_priorities
                    ],
                    "enabled": strat.enabled,
                    "stage": strat.stage.value,
                    "custom_params": strat.custom_params,
                }
                for name, strat in config.strategies.items()
            },
            "stage": config.stage.value,
            "zai_glm_config": config.zai_glm_config,
            "mcp_config": config.mcp_config,
        }
