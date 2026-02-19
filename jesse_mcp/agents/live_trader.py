"""
Trading Agent for Autonomous Live Trading

Provides agent-based trading with:
- Permission levels (paper_only, confirm_required, full_autonomous)
- Strategy → backtest → optimize → live workflow
- Monitoring and alerting hooks
- Auto-recovery mechanisms
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime

from jesse_mcp.core.live_config import (
    AgentPermission,
    LiveTradingConfig,
    LiveSessionRequest,
    LIVE_TRADING_WARNING,
    PAPER_TRADING_INFO,
)
from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

logger = logging.getLogger("jesse-mcp.trading-agent")


class TradingAgent:
    """
    Agent for autonomous trading operations.

    Permission levels:
    - PAPER_ONLY: Can only start paper trading sessions
    - CONFIRM_REQUIRED: Can start live trading but requires user confirmation
    - FULL_AUTONOMOUS: Can trade live without confirmation (highest risk)

    Example:
        agent = TradingAgent(permission=AgentPermission.PAPER_ONLY)
        result = await agent.execute_strategy_workflow(
            strategy="SMACrossover",
            symbol="BTC-USDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2024-01-01",
            go_live=True,
        )
    """

    def __init__(
        self,
        permission: AgentPermission = AgentPermission.PAPER_ONLY,
        config: Optional[LiveTradingConfig] = None,
    ):
        """
        Initialize trading agent.

        Args:
            permission: Permission level for this agent
            config: Trading configuration (defaults to from_env())
        """
        self.permission = permission
        self.config = config or LiveTradingConfig.from_env()
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    @property
    def can_trade_live(self) -> bool:
        """Check if agent has permission to trade live."""
        return self.permission != AgentPermission.PAPER_ONLY

    @property
    def requires_confirmation(self) -> bool:
        """Check if agent requires confirmation for live trading."""
        return self.permission == AgentPermission.CONFIRM_REQUIRED

    def check_permission(self, require_live: bool = False) -> Dict[str, Any]:
        """
        Check agent permission level.

        Args:
            require_live: If True, check if agent can trade live

        Returns:
            Dict with 'allowed' boolean and optional 'error'
        """
        if require_live and not self.can_trade_live:
            return {
                "allowed": False,
                "error": f"Agent permission '{self.permission.value}' does not allow live trading",
            }
        return {"allowed": True}

    async def execute_strategy_workflow(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        go_live: bool = False,
        exchange_api_key_id: Optional[str] = None,
        notification_api_key_id: str = "",
        confirmation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute full trading workflow: backtest → optimize → paper/live.

        This is the recommended way to deploy a strategy:
        1. Run backtest to validate strategy
        2. Optionally optimize parameters
        3. Start paper trading (always first for live)
        4. Optionally promote to live trading

        Args:
            strategy: Strategy name
            symbol: Trading symbol (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h")
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            exchange: Exchange name
            starting_balance: Initial balance
            go_live: If True, proceed to live trading after paper
            exchange_api_key_id: Exchange API key ID (required for live)
            notification_api_key_id: Notification config ID
            confirmation: Confirmation phrase (required for live with CONFIRM_REQUIRED)

        Returns:
            Dict with workflow results
        """
        results = {
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "steps": {},
        }

        client = get_jesse_rest_client()

        # Step 1: Backtest
        logger.info(f"📊 Step 1: Running backtest for {strategy}")
        backtest_result = client.backtest(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
        )
        results["steps"]["backtest"] = {
            "status": "completed" if "error" not in backtest_result else "failed",
            "metrics": {
                "total_return": backtest_result.get("total_return"),
                "sharpe_ratio": backtest_result.get("sharpe_ratio"),
                "max_drawdown": backtest_result.get("max_drawdown"),
                "win_rate": backtest_result.get("win_rate"),
            },
        }

        if "error" in backtest_result:
            results["error"] = f"Backtest failed: {backtest_result['error']}"
            return results

        # Check if strategy is viable
        total_return = backtest_result.get("total_return", 0)
        if total_return <= 0:
            results["warning"] = "Strategy has negative or zero returns. Proceed with caution."

        # Step 2: Start paper trading
        logger.info(f"📈 Step 2: Starting paper trading for {strategy}")
        if not exchange_api_key_id:
            results["warning"] = "No exchange_api_key_id provided. Cannot start trading session."
            results["steps"]["paper_trading"] = {"status": "skipped", "reason": "missing_api_key"}
            return results

        paper_result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=True,
        )

        if "error" in paper_result:
            results["steps"]["paper_trading"] = {"status": "failed", "error": paper_result["error"]}
            return results

        session_id = paper_result.get("session_id")
        results["steps"]["paper_trading"] = {
            "status": "started",
            "session_id": session_id,
        }
        self._active_sessions[session_id] = {
            "strategy": strategy,
            "symbol": symbol,
            "paper_mode": True,
            "started_at": datetime.utcnow().isoformat(),
        }

        # Step 3: Optionally go live
        if go_live:
            permission_check = self.check_permission(require_live=True)
            if not permission_check["allowed"]:
                results["steps"]["live_trading"] = {
                    "status": "failed",
                    "error": permission_check["error"],
                }
                return results

            if self.requires_confirmation:
                if confirmation != self.config.confirmation_phrase:
                    results["steps"]["live_trading"] = {
                        "status": "failed",
                        "error": f"Invalid confirmation. Required: '{self.config.confirmation_phrase}'",
                    }
                    return results

            # Cancel paper session first
            if session_id:
                client.cancel_live_session(session_id, paper_mode=True)

            logger.warning(LIVE_TRADING_WARNING)
            live_result = client.start_live_session(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                exchange=exchange,
                exchange_api_key_id=exchange_api_key_id,
                notification_api_key_id=notification_api_key_id,
                paper_mode=False,
            )

            if "error" in live_result:
                results["steps"]["live_trading"] = {
                    "status": "failed",
                    "error": live_result["error"],
                }
                return results

            live_session_id = live_result.get("session_id")
            results["steps"]["live_trading"] = {
                "status": "started",
                "session_id": live_session_id,
                "warning": "REAL MONEY TRADING - Monitor closely!",
            }
            self._active_sessions[live_session_id] = {
                "strategy": strategy,
                "symbol": symbol,
                "paper_mode": False,
                "started_at": datetime.utcnow().isoformat(),
            }

        return results

    async def monitor_session(
        self, session_id: str, interval_seconds: int = 60
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream session updates periodically.

        Args:
            session_id: Session ID to monitor
            interval_seconds: Update interval (default: 60)

        Yields:
            Dict with session status updates
        """
        client = get_jesse_rest_client()

        while True:
            try:
                status = client.get_live_session(session_id)
                equity = client.get_live_equity_curve(session_id)
                orders = client.get_live_orders(session_id)

                update = {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status.get("status", "unknown"),
                    "equity": equity.get("data", [])[-1:] if equity.get("data") else [],
                    "orders_count": len(orders.get("orders", [])),
                }

                # Check for alerts
                alerts = self._check_alerts(session_id, status, equity)
                if alerts:
                    update["alerts"] = alerts

                yield update

                # Check if session ended
                if status.get("status") in ["completed", "cancelled", "error"]:
                    break

            except Exception as e:
                yield {"session_id": session_id, "error": str(e)}

            await asyncio.sleep(interval_seconds)

    def _check_alerts(self, session_id: str, status: Dict, equity: Dict) -> List[Dict[str, Any]]:
        """Check for alert conditions."""
        alerts = []

        equity_data = equity.get("data", [])
        if not equity_data:
            return alerts

        current_equity = equity_data[-1].get("value", 0) if equity_data else 0
        initial_equity = equity_data[0].get("value", 0) if len(equity_data) > 1 else current_equity

        if initial_equity > 0:
            pnl_pct = (current_equity - initial_equity) / initial_equity

            if pnl_pct <= -self.config.max_daily_loss_pct:
                alerts.append(
                    {
                        "type": "max_loss",
                        "severity": "critical",
                        "message": f"Loss {pnl_pct:.2%} exceeds max {self.config.max_daily_loss_pct:.2%}",
                    }
                )

            if pnl_pct <= -self.config.max_drawdown_pct:
                alerts.append(
                    {
                        "type": "max_drawdown",
                        "severity": "critical",
                        "message": f"Drawdown {pnl_pct:.2%} exceeds max {self.config.max_drawdown_pct:.2%}",
                    }
                )

        return alerts

    async def handle_session_alert(
        self, session_id: str, alert_type: str, action: str = "notify"
    ) -> Dict[str, Any]:
        """
        Handle alerts from live session.

        Args:
            session_id: Session ID
            alert_type: Alert type (e.g., "max_loss", "max_drawdown")
            action: Action to take ("notify", "stop", "reduce")

        Returns:
            Dict with action result
        """
        client = get_jesse_rest_client()
        result = {"session_id": session_id, "alert_type": alert_type, "action": action}

        if action == "stop" and self.config.auto_stop_on_max_loss:
            session_info = self._active_sessions.get(session_id, {})
            cancel_result = client.cancel_live_session(
                session_id, paper_mode=session_info.get("paper_mode", True)
            )
            result["cancel_result"] = cancel_result
            result["status"] = "stopped"

        elif action == "notify":
            result["status"] = "notified"

        return result

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions managed by this agent."""
        return self._active_sessions.copy()


def get_trading_agent(
    permission: str = "paper_only",
) -> TradingAgent:
    """
    Get a trading agent with specified permission level.

    Args:
        permission: Permission level ("paper_only", "confirm_required", "full_autonomous")

    Returns:
        TradingAgent instance
    """
    try:
        perm = AgentPermission(permission)
    except ValueError:
        perm = AgentPermission.PAPER_ONLY

    return TradingAgent(permission=perm)
