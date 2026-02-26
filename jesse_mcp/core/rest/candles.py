"""
Candles management methods for Jesse REST API client.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from jesse_mcp.core.rate_limiter import get_rate_limiter
from .config import map_exchange_name

logger = logging.getLogger("jesse-mcp.rest-client")

TIMEFRAME_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "6h": 360,
    "8h": 480,
    "12h": 720,
    "1d": 1440,
    "3d": 4320,
    "1w": 10080,
}


def get_existing_candles(
    session: requests.Session,
    base_url: str,
    exchange: Optional[str] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Get list of existing candles with date ranges."""
    try:
        logger.info("📊 Fetching existing candles info")

        payload = {}
        if exchange:
            payload["exchange"] = exchange
        if symbol:
            payload["symbol"] = symbol

        response = session.post(
            f"{base_url}/candles/existing",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        candles = result.get("candles", result.get("data", []))
        count = len(candles) if isinstance(candles, list) else 0
        logger.info(f"✅ Found {count} existing candle datasets")

        return result

    except Exception as e:
        logger.error(f"❌ Failed to get existing candles: {e}")
        return {"error": str(e), "candles": []}


def validate_candle_data(
    session: requests.Session,
    base_url: str,
    routes: List[Dict[str, str]],
    exchange: str,
    exchange_type: str,
    start_date: str,
    end_date: str,
    auto_import_candles: bool = False,
    auto_import_max_candles: int = 50000,
) -> Optional[Dict[str, Any]]:
    """Validate that candle data exists for the requested backtest."""
    try:
        candles_response = session.post(
            f"{base_url}/candles/existing",
            json={},
            timeout=10,
        )
        candles_response.raise_for_status()
        data = candles_response.json().get("data", [])

        exchange_name = map_exchange_name(exchange, exchange_type)

        missing = []
        for route in routes:
            symbol = route["symbol"]
            timeframe = route["timeframe"]

            found = False
            for candle in data:
                if candle["exchange"] == exchange_name and candle["symbol"] == symbol:
                    candle_start = candle.get("start_date", "")
                    candle_end = candle.get("end_date", "")

                    if candle_start and candle_end:
                        if candle_start <= end_date and candle_end >= start_date:
                            found = True
                            break

            if not found:
                missing.append(
                    {
                        "exchange": exchange_name,
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )

        if missing:
            if auto_import_candles:
                logger.info(f"🔄 Auto-importing missing candles for {len(missing)} route(s)...")

                for m in missing:
                    import_result = import_candles(
                        session,
                        base_url,
                        exchange=m["exchange"],
                        symbol=m["symbol"],
                        timeframe=m["timeframe"],
                        start_date=start_date,
                        end_date=end_date,
                        max_candles=auto_import_max_candles,
                    )

                    if import_result.get("success"):
                        logger.info(
                            f"✅ Imported {import_result.get('candles_imported', '?')} candles for {m['symbol']} {m['timeframe']}"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Failed to import: {import_result.get('error', 'Unknown error')}"
                        )

                candles_response = session.post(
                    f"{base_url}/candles/existing",
                    json={},
                    timeout=10,
                )
                candles_response.raise_for_status()
                data = candles_response.json().get("data", [])

                still_missing = []
                for m in missing:
                    found = False
                    for candle in data:
                        if candle["exchange"] == m["exchange"] and candle["symbol"] == m["symbol"]:
                            candle_start = candle.get("start_date", "")
                            candle_end = candle.get("end_date", "")
                            if candle_start <= end_date and candle_end >= start_date:
                                found = True
                                break
                    if not found:
                        still_missing.append(f"{m['exchange']} {m['symbol']} {m['timeframe']}")

                if still_missing:
                    error_msg = (
                        f"Still missing candle data after auto-import: {', '.join(still_missing)}. "
                        f"Please import candles manually using the candles_import tool."
                    )
                    return {
                        "error": error_msg,
                        "error_type": "NoCandleDataError",
                        "success": False,
                        "missing_data": still_missing,
                    }

                logger.info(f"✅ Candle data validated after auto-import")
                return None
            else:
                error_details = []
                for m in missing:
                    available = []
                    for candle in data:
                        if candle["symbol"] == m["symbol"]:
                            available.append(
                                f"{candle['exchange']} ({candle.get('start_date', '?')}-{candle.get('end_date', '?')})"
                            )

                    if available:
                        error_details.append(
                            f"{m['exchange']} {m['symbol']} {m['timeframe']} (available: {', '.join(available)})"
                        )
                    else:
                        error_details.append(
                            f"{m['exchange']} {m['symbol']} {m['timeframe']} (no data at all)"
                        )

                error_msg = (
                    f"No candle data found for requested date range. "
                    f"Set auto_import_candles=True to automatically import, "
                    f"or import manually using the candles_import tool.\n"
                    f"Missing: {'; '.join(error_details)}"
                )
                logger.error(f"❌ {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "NoCandleDataError",
                    "success": False,
                    "missing_data": error_details,
                }

        logger.info(f"✅ Candle data validated for all routes")
        return None

    except Exception as e:
        logger.warning(f"⚠️ Could not validate candle data: {e}")
        return None


def import_candles(
    session: requests.Session,
    base_url: str,
    exchange: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    max_candles: int = 50000,
) -> Dict[str, Any]:
    """Import candles from exchange via Jesse API."""
    candle_id = str(uuid.uuid4())

    minutes = TIMEFRAME_MINUTES.get(timeframe, 60)

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
        estimated_candles = (days * 24 * 60) // minutes
    except:
        estimated_candles = max_candles

    if estimated_candles > max_candles:
        extra_days = (estimated_candles - max_candles) * minutes // (24 * 60)
        start_obj = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=extra_days)
        start_date = start_obj.strftime("%Y-%m-%d")
        logger.info(f"⚠️ Limited candles to {max_candles}, adjusted start date to {start_date}")

    try:
        response = session.post(
            f"{base_url}/candles/import",
            json={
                "id": candle_id,
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "finish_date": end_date,
            },
            timeout=30,
        )
        response.raise_for_status()

        max_wait = 120
        waited = 0

        while waited < max_wait:
            time.sleep(2)
            waited += 2

            status_resp = session.get(
                f"{base_url}/candles/import/{candle_id}",
                timeout=10,
            )

            if status_resp.status_code == 200:
                status_data = status_resp.json()
                if status_data.get("status") == "completed":
                    return {
                        "success": True,
                        "candles_imported": status_data.get("imported_count", 0),
                    }
                elif status_data.get("status") == "failed":
                    return {
                        "success": False,
                        "error": status_data.get("error", "Import failed"),
                    }

        return {
            "success": False,
            "error": "Import timed out",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def get_candles(
    session: requests.Session,
    base_url: str,
    exchange: str,
    symbol: str,
    timeframe: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Get candle data for a specific exchange/symbol/timeframe."""
    try:
        logger.info(f"📊 Fetching candles: {exchange} {symbol} {timeframe}")

        payload = {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
        }

        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        response = session.post(
            f"{base_url}/candles/get",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        candles = result.get("candles", result.get("data", []))
        count = len(candles) if isinstance(candles, list) else 0
        logger.info(f"✅ Retrieved {count} candles")

        return result

    except Exception as e:
        logger.error(f"❌ Failed to get candles: {e}")
        return {"error": str(e), "candles": []}


def delete_candles(
    session: requests.Session,
    base_url: str,
    exchange: str,
    symbol: str,
    timeframe: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete candle data for a specific exchange/symbol."""
    try:
        logger.info(f"🗑️ Deleting candles: {exchange} {symbol}")

        payload = {
            "exchange": exchange,
            "symbol": symbol,
        }

        if timeframe:
            payload["timeframe"] = timeframe

        response = session.post(
            f"{base_url}/candles/delete",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success", False):
            logger.info(f"✅ Candles deleted for {exchange} {symbol}")
        else:
            logger.warning(f"⚠️ Delete response: {result.get('message', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"❌ Failed to delete candles: {e}")
        return {"error": str(e), "success": False}


def clear_candles_cache(session: requests.Session, base_url: str) -> Dict[str, Any]:
    """Clear the candles database cache."""
    try:
        logger.info("🧹 Clearing candles cache")

        response = session.post(
            f"{base_url}/candles/clear-cache",
            json={},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success", False):
            logger.info("✅ Candles cache cleared")
        else:
            logger.warning(f"⚠️ Cache clear response: {result.get('message', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"❌ Failed to clear candles cache: {e}")
        return {"error": str(e), "success": False}
