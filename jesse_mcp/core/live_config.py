"""
Live Trading Configuration and Safety Models

Provides safety mechanisms for live trading including:
- Agent permission levels
- Position size limits
- Confirmation requirements
- Risk warnings
"""

import os
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class AgentPermission(str, Enum):
    """
    Permission levels for autonomous trading agents.

    PAPER_ONLY: Can only start paper trading (simulated)
    CONFIRM_REQUIRED: Can start live trading but requires explicit confirmation
    FULL_AUTONOMOUS: Can trade live without confirmation (highest risk)
    """

    PAPER_ONLY = "paper_only"
    CONFIRM_REQUIRED = "confirm_required"
    FULL_AUTONOMOUS = "full_autonomous"


class LiveTradingConfig(BaseModel):
    """
    Configuration for live trading safety mechanisms.

    These settings control risk management and agent permissions.
    """

    default_permission: AgentPermission = Field(
        default=AgentPermission.PAPER_ONLY,
        description="Default permission level for trading agents",
    )

    max_position_size_pct: float = Field(
        default=0.1,
        ge=0.01,
        le=1.0,
        description="Maximum position size as percentage of portfolio (0.01-1.0)",
    )

    max_daily_loss_pct: float = Field(
        default=0.05,
        ge=0.01,
        le=0.5,
        description="Maximum daily loss as percentage before auto-stop (0.01-0.5)",
    )

    max_drawdown_pct: float = Field(
        default=0.15, ge=0.05, le=0.5, description="Maximum drawdown before auto-stop (0.05-0.5)"
    )

    require_confirmation_phrase: bool = Field(
        default=True, description="Require explicit confirmation phrase for live trading"
    )

    confirmation_phrase: str = Field(
        default="I UNDERSTAND THE RISKS",
        description="Required confirmation phrase for live trading",
    )

    enable_alerts: bool = Field(default=True, description="Enable alerts for trading events")

    auto_stop_on_max_loss: bool = Field(
        default=True, description="Automatically stop session when max loss reached"
    )

    paper_mode_default: bool = Field(
        default=True, description="Default to paper mode unless explicitly overridden"
    )

    @classmethod
    def from_env(cls) -> "LiveTradingConfig":
        """Create config from environment variables."""
        return cls(
            default_permission=AgentPermission(os.getenv("JESSE_DEFAULT_PERMISSION", "paper_only")),
            max_position_size_pct=float(os.getenv("JESSE_MAX_POSITION_SIZE", "0.1")),
            max_daily_loss_pct=float(os.getenv("JESSE_MAX_DAILY_LOSS", "0.05")),
            max_drawdown_pct=float(os.getenv("JESSE_MAX_DRAWDOWN", "0.15")),
            require_confirmation_phrase=os.getenv("JESSE_REQUIRE_CONFIRMATION", "true").lower()
            == "true",
            enable_alerts=os.getenv("JESSE_ENABLE_ALERTS", "true").lower() == "true",
            auto_stop_on_max_loss=os.getenv("JESSE_AUTO_STOP_ON_LOSS", "true").lower() == "true",
        )


class LiveSessionRequest(BaseModel):
    """
    Validated request for starting a live trading session.

    This model validates all parameters before a session is started.
    """

    strategy: str = Field(..., min_length=1, description="Strategy name")
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    timeframe: str = Field(..., min_length=1, description="Candle timeframe")
    exchange: str = Field(..., min_length=1, description="Exchange name")
    exchange_api_key_id: str = Field(..., min_length=1, description="Exchange API key ID")
    notification_api_key_id: str = Field(default="", description="Notification config ID")

    paper_mode: bool = Field(default=True, description="Paper trading mode")
    debug_mode: bool = Field(default=False, description="Debug mode")

    permission: AgentPermission = Field(
        default=AgentPermission.PAPER_ONLY, description="Agent permission level"
    )

    confirmation: Optional[str] = Field(
        default=None, description="Confirmation phrase for live trading"
    )

    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")

    def validate_for_live_mode(self, trading_config: LiveTradingConfig) -> Dict[str, Any]:
        """
        Validate request for live trading mode.

        Args:
            trading_config: Global trading configuration

        Returns:
            Dict with 'valid' boolean and optional 'error' message
        """
        if self.paper_mode:
            return {"valid": True}

        if self.permission == AgentPermission.PAPER_ONLY:
            return {
                "valid": False,
                "error": "Agent only has PAPER_ONLY permission. Cannot start live trading.",
            }

        if trading_config.require_confirmation_phrase:
            if self.confirmation != trading_config.confirmation_phrase:
                return {
                    "valid": False,
                    "error": f"Invalid confirmation phrase. Required: '{trading_config.confirmation_phrase}'",
                }

        return {"valid": True}


LIVE_TRADING_WARNING = """
⚠️  WARNING: LIVE TRADING MODE ⚠️

You are about to start a LIVE trading session with REAL MONEY.

RISKS:
- Your funds are at risk of total loss
- Automated trading can result in significant losses
- Market conditions can change rapidly
- No guarantee of profit

BEFORE PROCEEDING:
1. You have thoroughly backtested this strategy
2. You have paper-traded successfully first
3. You understand the strategy's risk profile
4. You can afford to lose the allocated capital

To confirm, you must provide the confirmation phrase.
"""

PAPER_TRADING_INFO = """
📊 Starting PAPER TRADING session (simulated)

This is a simulation - no real money will be traded.
Use this mode to test strategies before going live.
"""


def get_live_trading_config() -> LiveTradingConfig:
    """Get the global live trading configuration."""
    return LiveTradingConfig.from_env()
