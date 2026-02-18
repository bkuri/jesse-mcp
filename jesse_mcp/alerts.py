"""
ntfy Alerting Integration

Provides push notifications for Jesse MCP trading alerts via ntfy.sh.

Usage:
    from jesse_mcp.alerts import send_ntfy_alert, alert_on_consensus, send_daily_summary

    send_ntfy_alert("Trade signal detected", priority="high", tags=[" trading", "btc"])
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import requests

logger = logging.getLogger("jesse-mcp.alerts")

NTFY_URL = os.environ.get("NTFY_URL", "https://ntfy.kuri.casa")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "jesse")
NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "tk_1vk4maedoxiw0kk66tbi8esfha8hc")

VALID_PRIORITIES = {"min", "low", "default", "high", "urgent", "max"}


def send_ntfy_alert(
    message: str,
    priority: str = "default",
    tags: Optional[List[str]] = None,
    title: Optional[str] = "Jesse MCP Alert",
) -> Dict[str, Any]:
    if priority not in VALID_PRIORITIES:
        logger.warning(f"Invalid priority '{priority}', using 'default'")
        priority = "default"

    url = f"{NTFY_URL}/{NTFY_TOPIC}"
    headers = {
        "Authorization": f"Bearer {NTFY_TOKEN}",
        "Priority": priority,
        "Title": title,
    }

    if tags:
        headers["Tags"] = ",".join(tags)

    try:
        response = requests.post(url, data=message, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Alert sent successfully: {message[:50]}...")
        return {
            "success": True,
            "status_code": response.status_code,
            "message": message,
            "priority": priority,
            "tags": tags,
        }
    except requests.exceptions.Timeout:
        logger.error("Alert request timed out")
        return {"error": "Request timed out", "error_type": "TimeoutError"}
    except requests.exceptions.HTTPError as e:
        logger.error(f"Alert HTTP error: {e}")
        return {"error": str(e), "error_type": "HTTPError"}
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


def _get_mock_backtest_result(strategy: str) -> Dict[str, Any]:
    import random

    return {
        "strategy": strategy,
        "total_return": random.uniform(-20, 30),
        "win_rate": random.uniform(30, 70),
        "total_trades": random.randint(10, 100),
        "sharpe_ratio": random.uniform(-1, 3),
        "max_drawdown": random.uniform(5, 30),
        "signal": random.choice(["buy", "sell", "neutral"]),
    }


def alert_on_consensus(
    strategies: List[str],
    threshold: float = 0.7,
    symbol: str = "BTC-USDT",
    timeframe: str = "1h",
) -> Dict[str, Any]:
    if not strategies:
        return {"error": "No strategies provided", "error_type": "ValueError"}

    if not 0 <= threshold <= 1:
        return {"error": "Threshold must be between 0 and 1", "error_type": "ValueError"}

    results = []
    for strategy in strategies:
        try:
            result = _get_mock_backtest_result(strategy)
            result["symbol"] = symbol
            result["timeframe"] = timeframe
            results.append(result)
        except Exception as e:
            logger.warning(f"Failed to get backtest for {strategy}: {e}")

    if not results:
        return {"error": "No backtest results obtained", "error_type": "RuntimeError"}

    buy_signals = [r for r in results if r.get("signal") == "buy"]
    sell_signals = [r for r in results if r.get("signal") == "sell"]

    buy_ratio = len(buy_signals) / len(results)
    sell_ratio = len(sell_signals) / len(results)

    consensus = None
    consensus_ratio = 0.0

    if buy_ratio >= threshold:
        consensus = "buy"
        consensus_ratio = buy_ratio
    elif sell_ratio >= threshold:
        consensus = "sell"
        consensus_ratio = sell_ratio

    response = {
        "strategies_checked": len(strategies),
        "results": results,
        "buy_ratio": buy_ratio,
        "sell_ratio": sell_ratio,
        "threshold": threshold,
        "consensus": consensus,
        "consensus_ratio": consensus_ratio,
        "alert_sent": False,
    }

    if consensus:
        direction = "BULLISH" if consensus == "buy" else "BEARISH"
        message = (
            f"🔔 Strategy Consensus Alert\n\n"
            f"**{direction}** consensus detected!\n\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {timeframe}\n"
            f"Agreement: {consensus_ratio:.0%} ({int(consensus_ratio * len(results))}/{len(results)} strategies)\n"
            f"Threshold: {threshold:.0%}\n\n"
            f"Strategies: {', '.join(strategies)}"
        )

        priority = "high" if consensus_ratio >= 0.9 else "default"
        tags = [consensus, symbol.lower().replace("-", ""), "consensus"]

        alert_result = send_ntfy_alert(
            message, priority=priority, tags=tags, title=f"Jesse Consensus: {symbol}"
        )
        response["alert_sent"] = alert_result.get("success", False)
        response["alert_result"] = alert_result

        logger.info(f"Consensus alert sent: {consensus} at {consensus_ratio:.0%}")

    return response


def send_daily_summary(report: str, priority: str = "default") -> Dict[str, Any]:
    if not report or not report.strip():
        return {"error": "Report cannot be empty", "error_type": "ValueError"}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title = f"Jesse Daily Summary - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    message = f"📊 Daily Trading Summary\n\nGenerated: {timestamp}\n\n{report}"

    tags = ["daily", "summary", "report"]

    result = send_ntfy_alert(message, priority=priority, tags=tags, title=title)

    if result.get("success"):
        logger.info("Daily summary sent successfully")
    else:
        logger.error(f"Failed to send daily summary: {result.get('error')}")

    return result


if __name__ == "__main__":
    print("Testing ntfy alert integration...")
    print(f"URL: {NTFY_URL}/{NTFY_TOPIC}")

    test_result = send_ntfy_alert(
        "Test alert from Jesse MCP alerts module",
        priority="low",
        tags=["test", "jesse-mcp"],
        title="Jesse MCP Test",
    )
    print(f"Test result: {test_result}")
