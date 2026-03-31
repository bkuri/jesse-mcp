"""
Phase 6: Live & Paper Trading Tools

Provides live and paper trading session management for the Jesse MCP server:
- Live trading plugin check
- Live/paper session start, cancel, status
- Orders, equity curve, logs retrieval
- Paper trading session management
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from jesse_mcp.tools._utils import (
    get_client,
    get_strategies_path,
    require_jesse,
    tool_error_handler,
)

logger = logging.getLogger("jesse-mcp.phase6")


def register_live_tools(mcp):
    """Register live and paper trading tools with the MCP server."""

    # ==================== LIVE TRADING TOOLS ====================

    @mcp.tool
    @tool_error_handler
    def live_check_plugin() -> Dict[str, Any]:
        """
        Check if jesse-live plugin is installed and available.

        Returns:
            Dict with 'available' boolean and optional 'error' message
        """
        client = get_client()
        return client.check_live_plugin_available()

    @mcp.tool
    @tool_error_handler
    def live_start_paper_trading(
        strategy: str,
        symbol: str,
        timeframe: str,
        exchange: str,
        exchange_api_key_id: str,
        notification_api_key_id: str = "",
        debug_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Start a PAPER trading session (simulated, no real money).

        Paper trading simulates trades without using real funds.
        Use this to test strategies before going live.

        Args:
            strategy: Strategy name (must exist in strategies directory)
            symbol: Trading symbol (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h", "1d")
            exchange: Exchange name (e.g., "Binance", "Bybit")
            exchange_api_key_id: ID of stored exchange API key in Jesse
            notification_api_key_id: ID of stored notification config (optional)
            debug_mode: Enable debug logging

        Returns:
            Dict with session_id and status, or error details
        """
        from jesse_mcp.core.live_config import PAPER_TRADING_INFO
        from jesse_mcp.core.strategy_validation.certification import (
            get_strategy_certification,
            CERTIFICATION_MIN_TESTS,
            CERTIFICATION_PASS_RATE,
        )

        logger.info(PAPER_TRADING_INFO)

        require_jesse()
        strategies_path = get_strategies_path()

        cert_status = get_strategy_certification(strategy, strategies_path)

        if not cert_status.is_certified:
            if cert_status.test_count > 0:
                logger.warning(
                    f"⚠️  Paper trading with uncertified strategy '{strategy}': "
                    f"{cert_status.test_pass_count}/{cert_status.test_count} tests passed ({cert_status.pass_rate:.0%})"
                )
            else:
                logger.warning(
                    f"⚠️  Paper trading with untested strategy '{strategy}'. "
                    f"Recommend testing with backtests first."
                )

        client = get_client()
        result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=True,
            debug_mode=debug_mode,
        )
        result["mode"] = "paper"
        if not cert_status.is_certified:
            if cert_status.test_count > 0:
                result["warning"] = (
                    f"Strategy '{strategy}' not certified: "
                    f"{cert_status.test_pass_count}/{cert_status.test_count} tests ({cert_status.pass_rate:.0%}). "
                    f"Need {CERTIFICATION_MIN_TESTS - cert_status.test_count} more tests at {CERTIFICATION_PASS_RATE:.0%}+ pass rate."
                )
            else:
                result["warning"] = (
                    f"Strategy '{strategy}' has no recorded backtests. "
                    f"Backtest recommended before paper trading."
                )
        return result

    @mcp.tool
    @tool_error_handler
    def live_start_live_trading(
        strategy: str,
        symbol: str,
        timeframe: str,
        exchange: str,
        exchange_api_key_id: str,
        confirmation: str,
        notification_api_key_id: str = "",
        debug_mode: bool = False,
        permission: str = "confirm_required",
    ) -> Dict[str, Any]:
        """
        Start LIVE trading with REAL MONEY.

        ⚠️  WARNING: This will execute real trades with real funds. ⚠️

        RISKS:
        - Your funds are at risk of total loss
        - Automated trading can result in significant losses
        - No guarantee of profit

        REQUIREMENTS:
        1. Thoroughly backtested strategy
        2. Successful paper trading first
        3. Understanding of strategy's risk profile
        4. Capital you can afford to lose

        Args:
            strategy: Strategy name (must exist in strategies directory)
            symbol: Trading symbol (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h", "1d")
            exchange: Exchange name (e.g., "Binance", "Bybit")
            exchange_api_key_id: ID of stored exchange API key in Jesse
            confirmation: REQUIRED: Must be exactly "I UNDERSTAND THE RISKS"
            notification_api_key_id: ID of stored notification config (optional)
            debug_mode: Enable debug logging
            permission: Agent permission level ("paper_only", "confirm_required", "full_autonomous")

        Returns:
            Dict with session_id and status, or error details
        """
        from jesse_mcp.core.live_config import (
            LiveTradingConfig,
            AgentPermission,
            LIVE_TRADING_WARNING,
            LiveSessionRequest,
        )

        config = LiveTradingConfig.from_env()

        if confirmation != config.confirmation_phrase:
            return {
                "error": f"Invalid confirmation. Required: '{config.confirmation_phrase}'",
                "warning": LIVE_TRADING_WARNING,
            }

        require_jesse()
        strategies_path = get_strategies_path()

        from jesse_mcp.core.strategy_validation.certification import (
            check_live_trading_allowed,
            CERTIFICATION_MIN_TESTS,
            CERTIFICATION_PASS_RATE,
        )

        check_result = check_live_trading_allowed(strategy, strategies_path)

        if not check_result["allowed"]:
            status = check_result["status"]
            return {
                "error": f"Cannot start live trading: Strategy '{strategy}' is not certified",
                "status": "blocked",
                "reason": check_result["reason"],
                "certification": {
                    "is_certified": status.is_certified,
                    "test_count": status.test_count,
                    "test_pass_count": status.test_pass_count,
                    "pass_rate": status.pass_rate,
                    "min_tests_required": CERTIFICATION_MIN_TESTS,
                    "min_pass_rate_required": CERTIFICATION_PASS_RATE,
                },
                "recommendation": check_result["recommendation"],
            }

        try:
            perm = AgentPermission(permission)
        except ValueError:
            perm = AgentPermission.CONFIRM_REQUIRED

        request = LiveSessionRequest(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=False,
            debug_mode=debug_mode,
            permission=perm,
            confirmation=confirmation,
        )

        validation = request.validate_for_live_mode(config)
        if not validation.get("valid"):
            return {"error": validation.get("error"), "warning": LIVE_TRADING_WARNING}

        logger.warning(LIVE_TRADING_WARNING)

        client = get_client()
        result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            notification_api_key_id=notification_api_key_id,
            paper_mode=False,
            debug_mode=debug_mode,
        )
        result["mode"] = "live"
        result["warning"] = "REAL MONEY TRADING - Monitor closely!"
        return result

    @mcp.tool
    @tool_error_handler
    def live_cancel_session(session_id: str, paper_mode: bool = True) -> Dict[str, Any]:
        """
        Cancel a running live/paper trading session.

        Args:
            session_id: Session ID to cancel
            paper_mode: True if paper trading session, False if live

        Returns:
            Dict with cancellation status
        """
        client = get_client()
        return client.cancel_live_session(session_id, paper_mode)

    @mcp.tool
    @tool_error_handler
    def live_get_sessions(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get list of live trading sessions.

        Args:
            limit: Maximum number of sessions to return (default: 50)
            offset: Offset for pagination (default: 0)

        Returns:
            Dict with sessions list
        """
        client = get_client()
        return client.get_live_sessions(limit, offset)

    @mcp.tool
    @tool_error_handler
    def live_get_status(session_id: str) -> Dict[str, Any]:
        """
        Get status of a specific live trading session.

        Args:
            session_id: Session ID to check

        Returns:
            Dict with session details and current status
        """
        client = get_client()
        return client.get_live_session(session_id)

    @mcp.tool
    @tool_error_handler
    def live_get_orders(session_id: str) -> Dict[str, Any]:
        """
        Get orders from a live trading session.

        Args:
            session_id: Session ID

        Returns:
            Dict with orders list
        """
        client = get_client()
        return client.get_live_orders(session_id)

    @mcp.tool
    @tool_error_handler
    def live_get_equity_curve(
        session_id: str,
        from_ms: Optional[int] = None,
        to_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get real-time equity curve (P&L) for a session.

        Args:
            session_id: Session ID
            from_ms: Start time in milliseconds (optional)
            to_ms: End time in milliseconds (optional)

        Returns:
            Dict with equity curve data points
        """
        client = get_client()
        return client.get_live_equity_curve(session_id, from_ms, to_ms)

    @mcp.tool
    @tool_error_handler
    def live_get_logs(session_id: str, log_type: str = "all") -> Dict[str, Any]:
        """
        Get logs from a live trading session.

        Args:
            session_id: Session ID
            log_type: Log type filter ("all", "info", "error", "warning")

        Returns:
            Dict with log entries
        """
        client = get_client()
        return client.get_live_logs(session_id, log_type)

    # ==================== PAPER TRADING TOOLS ====================

    @mcp.tool
    @tool_error_handler
    def paper_start(
        strategy: str,
        symbol: str,
        timeframe: str = "1h",
        exchange: str = "Binance Spot",
        exchange_api_key_id: str = "",
        starting_balance: float = 10000,
        leverage: float = 1,
        fee: float = 0.001,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a paper trading session.

        Paper trading simulates trades without using real funds.
        Use this to test strategies before going live.

        Args:
            strategy: Strategy name (e.g., 'SMACrossover', 'DayTrader')
            symbol: Trading pair (e.g., 'BTC-USDT')
            timeframe: Candle timeframe (default: '1h')
            exchange: Exchange name (default: 'Binance')
            exchange_api_key_id: ID of stored exchange API key in Jesse
            starting_balance: Initial capital (default: 10000)
            leverage: Futures leverage (default: 1)
            fee: Trading fee rate (default: 0.001)
            session_id: Optional custom session ID (auto-generated if not provided)

        Returns:
            Dict with session_id, status, and configuration
        """
        client = get_client()

        config = {
            "starting_balance": starting_balance,
            "fee": fee,
            "futures_leverage": leverage,
        }

        result = client.start_live_session(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            exchange_api_key_id=exchange_api_key_id,
            paper_mode=True,
            config=config,
        )

        if "error" not in result:
            result["mode"] = "paper"
            result["starting_balance"] = starting_balance
            result["leverage"] = leverage
            result["fee"] = fee

        return result

    @mcp.tool
    @tool_error_handler
    def paper_stop(session_id: str) -> Dict[str, Any]:
        """
        Stop a paper trading session and return final metrics.

        Args:
            session_id: Session ID to stop

        Returns:
            Dict with stopped_at, duration, and final_metrics
        """
        client = get_client()

        result = client.cancel_live_session(session_id, paper_mode=True)

        if "error" not in result:
            session = client.get_live_session(session_id)
            result["stopped_at"] = datetime.utcnow().isoformat()
            result["final_metrics"] = session.get("session", {}).get("metrics", {})

        return result

    @mcp.tool
    @tool_error_handler
    def paper_status(session_id: str) -> Dict[str, Any]:
        """
        Get current status of a paper trading session.

        Args:
            session_id: Session ID to check

        Returns:
            Dict with session status, equity, positions, and metrics
        """
        client = get_client()
        return client.get_live_session(session_id)

    @mcp.tool
    @tool_error_handler
    def paper_get_trades(
        session_id: str, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get trades executed in a paper trading session.

        Args:
            session_id: Session ID
            limit: Maximum number of trades to return (default: 100)
            offset: Offset for pagination (default: 0)

        Returns:
            Dict with total_trades and trades list
        """
        client = get_client()
        result = client.get_closed_trades(session_id, limit)

        trades = result.get("data", [])
        if offset > 0:
            trades = trades[offset:]

        return {
            "session_id": session_id,
            "total_trades": len(result.get("data", [])),
            "trades": trades,
        }

    @mcp.tool
    @tool_error_handler
    def paper_get_equity(session_id: str, resolution: str = "1h") -> Dict[str, Any]:
        """
        Get equity curve data for a paper trading session.

        Args:
            session_id: Session ID
            resolution: Resolution of equity curve data (default: '1h')

        Returns:
            Dict with equity_curve containing timestamp, equity, drawdown data
        """
        client = get_client()

        timeframe_map = {
            "1m": 60000,
            "5m": 300000,
            "15m": 900000,
            "1h": 3600000,
            "4h": 14400000,
            "1d": 86400000,
        }
        max_points = 1000

        result = client.get_live_equity_curve(
            session_id,
            timeframe=resolution,
            max_points=max_points,
        )

        return {
            "session_id": session_id,
            "resolution": resolution,
            "equity_curve": result.get("data", []),
        }

    @mcp.tool
    @tool_error_handler
    def paper_get_metrics(session_id: str) -> Dict[str, Any]:
        """
        Get calculated performance metrics for a paper trading session.

        Args:
            session_id: Session ID

        Returns:
            Dict with metrics: total_return, sharpe_ratio, max_drawdown, win_rate, etc.
        """
        client = get_client()
        session = client.get_live_session(session_id)

        session_data = session.get("session", {})
        metrics = session_data.get("metrics", {})

        return {
            "session_id": session_id,
            "metrics": metrics,
        }

    @mcp.tool
    @tool_error_handler
    def paper_list_sessions() -> Dict[str, Any]:
        """
        List all paper trading sessions.

        Returns:
            Dict with sessions list and total count
        """
        client = get_client()
        return client.get_live_sessions()

    @mcp.tool
    @tool_error_handler
    def paper_update_session(
        session_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update session parameters (limited to safe modifications).

        Args:
            session_id: Session ID to update
            notes: Notes text to associate with session

        Returns:
            Dict with update status
        """
        client = get_client()

        if notes is not None:
            return client.update_live_session_notes(session_id, notes)

        return {"session_id": session_id, "status": "no_updates"}
