"""
Live trading methods for Jesse REST API client.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("jesse-mcp.rest-client")


def check_live_plugin_available(session: requests.Session, base_url: str) -> Dict[str, Any]:
    """Check if jesse-live plugin is installed and available."""
    try:
        response = session.get(f"{base_url}/live/sessions", timeout=10)
        if response.status_code == 200:
            logger.info("✅ jesse-live plugin is available")
            return {"available": True}
        elif response.status_code == 404:
            logger.warning("⚠️ jesse-live plugin not installed")
            return {"available": False, "error": "jesse-live plugin not installed"}
        else:
            return {"available": False, "error": f"Unexpected status: {response.status_code}"}
    except Exception as e:
        logger.error(f"❌ Failed to check live plugin: {e}")
        return {"available": False, "error": str(e)}


def start_live_session(
    session: requests.Session,
    base_url: str,
    strategy: str,
    symbol: str,
    timeframe: str,
    exchange: str,
    exchange_api_key_id: str,
    notification_api_key_id: str = "",
    paper_mode: bool = True,
    debug_mode: bool = False,
    config: Optional[Dict[str, Any]] = None,
    routes: Optional[List[Dict[str, str]]] = None,
    data_routes: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Start a live or paper trading session."""
    try:
        mode = "paper" if paper_mode else "LIVE"
        logger.info(f"🚀 Starting {mode} trading session: {strategy} on {symbol}")

        if routes is None:
            routes = [
                {
                    "exchange": exchange,
                    "strategy": strategy,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

        if data_routes is None:
            data_routes = [
                {
                    "exchange": exchange,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

        default_config = {
            "warm_up_candles": 240,
            "logging": {"output_type": "json"},
        }
        if config:
            default_config.update(config)

        payload = {
            "id": str(uuid.uuid4()),
            "exchange": exchange,
            "exchange_api_key_id": exchange_api_key_id,
            "notification_api_key_id": notification_api_key_id,
            "routes": routes,
            "data_routes": data_routes,
            "config": default_config,
            "debug_mode": debug_mode,
            "paper_mode": paper_mode,
        }

        response = session.post(
            f"{base_url}/live",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        result["session_id"] = payload["id"]
        result["paper_mode"] = paper_mode

        logger.info(f"✅ {mode.upper()} trading session started: {payload['id']}")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to start live session: {e}")
        return {"error": str(e), "success": False}


def cancel_live_session(
    session: requests.Session,
    base_url: str,
    session_id: str,
    paper_mode: bool = True,
) -> Dict[str, Any]:
    """Cancel a running live trading session."""
    try:
        mode = "paper" if paper_mode else "LIVE"
        logger.info(f"🛑 Cancelling {mode} session: {session_id}")

        payload = {
            "id": session_id,
            "paper_mode": paper_mode,
        }

        response = session.post(
            f"{base_url}/live/cancel",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ Session cancelled: {session_id}")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to cancel session: {e}")
        return {"error": str(e), "success": False}


def get_live_sessions(
    session: requests.Session,
    base_url: str,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get list of live trading sessions."""
    try:
        logger.info("📋 Fetching live sessions")

        payload = {"limit": limit, "offset": offset}

        response = session.post(
            f"{base_url}/live/sessions",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        sessions = result.get("sessions", result.get("data", []))
        count = len(sessions) if isinstance(sessions, list) else 0
        logger.info(f"✅ Found {count} live sessions")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to get live sessions: {e}")
        return {"error": str(e), "sessions": []}


def get_live_session(
    session: requests.Session,
    base_url: str,
    session_id: str,
) -> Dict[str, Any]:
    """Get a specific live session by ID."""
    try:
        logger.info(f"📊 Fetching live session: {session_id}")

        payload = {"id": session_id}

        response = session.post(
            f"{base_url}/live/sessions/{session_id}",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ Retrieved session: {session_id}")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to get live session: {e}")
        return {"error": str(e), "session": None}


def get_live_logs(
    session: requests.Session,
    base_url: str,
    session_id: str,
    log_type: str = "all",
    start_time: int = 0,
) -> Dict[str, Any]:
    """Get logs for a live trading session."""
    try:
        logger.info(f"📜 Fetching logs for session: {session_id}")

        payload = {
            "id": session_id,
            "type": log_type,
            "start_time": start_time,
        }

        response = session.post(
            f"{base_url}/live/logs",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        logs = result.get("data", [])
        count = len(logs) if isinstance(logs, list) else 0
        logger.info(f"✅ Retrieved {count} log entries")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to get live logs: {e}")
        return {"error": str(e), "data": []}


def get_live_orders(
    session: requests.Session,
    base_url: str,
    session_id: str,
) -> Dict[str, Any]:
    """Get orders for a live trading session."""
    try:
        logger.info(f"📦 Fetching orders for session: {session_id}")

        payload = {"id": session_id}

        response = session.post(
            f"{base_url}/live/orders",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        orders = result.get("orders", result.get("data", []))
        count = len(orders) if isinstance(orders, list) else 0
        logger.info(f"✅ Retrieved {count} orders")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to get live orders: {e}")
        return {"error": str(e), "orders": []}


def get_closed_trades(
    session: requests.Session,
    base_url: str,
    session_id: str,
    limit: int = 100,
) -> Dict[str, Any]:
    """Get closed/completed trades for a live trading session."""
    try:
        logger.info(f"📊 Fetching closed trades for session: {session_id}")

        params = {
            "session_id": session_id,
            "limit": min(limit, 1000),
        }

        response = session.get(
            f"{base_url}/closed-trades/list",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        trades = result.get("data", [])
        count = len(trades) if isinstance(trades, list) else 0
        logger.info(f"✅ Retrieved {count} closed trades")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to get closed trades: {e}")
        return {"error": str(e), "data": []}


def get_live_equity_curve(
    session: requests.Session,
    base_url: str,
    session_id: str,
    from_ms: Optional[int] = None,
    to_ms: Optional[int] = None,
    timeframe: str = "auto",
    max_points: int = 1000,
) -> Dict[str, Any]:
    """Get equity curve for a live trading session."""
    try:
        logger.info(f"📈 Fetching equity curve for session: {session_id}")

        params = {
            "session_id": session_id,
            "timeframe": timeframe,
            "max_points": max_points,
        }
        if from_ms is not None:
            params["from_ms"] = from_ms
        if to_ms is not None:
            params["to_ms"] = to_ms

        response = session.get(
            f"{base_url}/live/equity-curve",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ Retrieved equity curve")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to get equity curve: {e}")
        return {"error": str(e), "data": []}


def update_live_session_notes(
    session: requests.Session,
    base_url: str,
    session_id: str,
    notes: str,
) -> Dict[str, Any]:
    """Update notes for a live trading session."""
    try:
        logger.info(f"📝 Updating notes for session: {session_id}")

        payload = {"id": session_id, "notes": notes}

        response = session.post(
            f"{base_url}/live/sessions/{session_id}/notes",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ Updated session notes")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to update session notes: {e}")
        return {"error": str(e), "success": False}


def purge_live_sessions(
    session: requests.Session,
    base_url: str,
    days_old: Optional[int] = None,
) -> Dict[str, Any]:
    """Purge old live trading sessions from database."""
    try:
        logger.info(f"🧹 Purging old live sessions")

        payload = {}
        if days_old is not None:
            payload["days_old"] = days_old

        response = session.post(
            f"{base_url}/live/purge-sessions",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        deleted = result.get("deleted_count", 0)
        logger.info(f"✅ Purged {deleted} sessions")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to purge sessions: {e}")
        return {"error": str(e), "deleted_count": 0}
