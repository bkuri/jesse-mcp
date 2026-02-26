"""
Backtest helper functions for Jesse REST API client.

Contains utility functions for building payloads, validating results, etc.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from jesse_mcp.core.rest.config import map_exchange_name

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


def estimate_max_backtest_time(
    start_date: str,
    end_date: str,
    timeframe: str = "1h",
    safety_factor: float = 3.0,
) -> float:
    """Estimate maximum backtest time based on candle count."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
    except ValueError:
        days = 30

    minutes = TIMEFRAME_MINUTES.get(timeframe, 60)
    warmup_candles = 240
    trading_candles = (days * 24 * 60) // minutes if minutes > 0 else days * 24
    total_candles = trading_candles + warmup_candles

    CONSERVATIVE_CANDLES_PER_SEC = 500
    estimated_time = total_candles / CONSERVATIVE_CANDLES_PER_SEC
    max_time = estimated_time * safety_factor

    MIN_TIMEOUT = 30
    MAX_TIMEOUT = 600
    max_time = max(MIN_TIMEOUT, min(max_time, MAX_TIMEOUT))

    logger.info(
        f"📊 Estimated backtest time: {total_candles} candles, "
        f"~{estimated_time:.1f}s expected, {max_time:.1f}s max timeout"
    )
    return max_time


def validate_backtest_result(result: Dict[str, Any]) -> tuple:
    """Validate that backtest result is complete and usable."""
    if not isinstance(result, dict):
        return False, "Result is not a dictionary"

    if "error" in result:
        return False, f"Error in result: {result.get('error')}"

    if result.get("status") == "processing":
        return False, "Backtest still processing (incomplete)"

    if not result:
        return False, "Result is empty"

    metric_fields = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "total_trades"]
    has_metrics = any(f in result for f in metric_fields)
    if not has_metrics and not result.get("success") and result.get("status") != "finished":
        return False, f"Result missing all metric fields: {', '.join(metric_fields)}"

    for field in metric_fields:
        if field in result and result[field] is not None:
            try:
                value = float(result[field])
                if value != value:
                    return False, f"Field {field} contains NaN"
            except (TypeError, ValueError):
                return False, f"Field {field} is not numeric: {result[field]}"

    return True, "Result validation passed"


def is_retryable_error(error_msg: str) -> bool:
    """Determine if an error is retryable (transient)."""
    retryable_keywords = [
        "timeout",
        "rate limit",
        "temporary",
        "temporarily unavailable",
        "connection",
        "temporarily",
        "service unavailable",
        "gateway timeout",
    ]
    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in retryable_keywords)


def build_backtest_payload(
    routes: List[Dict[str, str]],
    start_date: str,
    end_date: str,
    exchange: str,
    starting_balance: float,
    exchange_type: str,
    data_routes: Optional[List[Dict[str, str]]] = None,
    include_logs: bool = False,
    include_trades: bool = False,
    fast_mode: bool = True,
) -> Dict[str, Any]:
    """Build backtest payload matching Jesse 1.13.x format."""
    formatted_routes = [
        {
            "strategy": r["strategy"],
            "symbol": r["symbol"],
            "timeframe": r["timeframe"],
        }
        for r in routes
    ]

    formatted_data_routes = []
    if data_routes:
        formatted_data_routes = [
            {"symbol": dr["symbol"], "timeframe": dr["timeframe"]} for dr in data_routes
        ]

    exchange_name = map_exchange_name(exchange, exchange_type)

    config = {
        "warm_up_candles": 240,
        "fast_mode": fast_mode,
        "logging": {
            "shorter_period_candles": False,
            "balance_update": True,
            "position_closed": True,
            "position_increased": True,
            "position_opened": True,
            "order_submission": True,
            "order_execution": True,
            "trading_candles": True,
            "order_cancellation": True,
        },
        "exchanges": {
            "Coinbase Spot": {
                "fee": 0.0003,
                "name": "Coinbase Spot",
                "type": "spot",
                "balance": 10000,
            },
            "Binance Perpetual Futures": {
                "name": "Binance Perpetual Futures",
                "futures_leverage": 2,
                "type": "futures",
                "fee": 0.0004,
                "futures_leverage_mode": "cross",
                "balance": starting_balance,
            },
            "Bybit USDC Perpetual": {
                "name": "Bybit USDC Perpetual",
                "futures_leverage": 2,
                "type": "futures",
                "fee": 0.00055,
                "futures_leverage_mode": "cross",
                "balance": starting_balance,
            },
            "Bitfinex Spot": {
                "fee": 0.002,
                "name": "Bitfinex Spot",
                "type": "spot",
                "balance": starting_balance,
            },
            "Binance US Spot": {
                "fee": 0.001,
                "name": "Binance US Spot",
                "type": "spot",
                "balance": starting_balance,
            },
            "Bybit Spot": {
                "fee": 0.001,
                "name": "Bybit Spot",
                "type": "spot",
                "balance": starting_balance,
            },
            "Bybit USDT Perpetual": {
                "name": "Bybit USDT Perpetual",
                "futures_leverage": 2,
                "type": "futures",
                "fee": 0.00055,
                "futures_leverage_mode": "cross",
                "balance": starting_balance,
            },
            "Binance Spot": {
                "fee": 0.001,
                "name": "Binance Spot",
                "type": "spot",
                "balance": starting_balance,
            },
            "Gate USDT Perpetual": {
                "name": "Gate USDT Perpetual",
                "futures_leverage": 2,
                "type": "futures",
                "fee": 0.0005,
                "futures_leverage_mode": "cross",
                "balance": starting_balance,
            },
        },
    }

    return {
        "id": str(uuid.uuid4()),
        "exchange": exchange_name,
        "routes": formatted_routes,
        "data_routes": formatted_data_routes,
        "config": config,
        "start_date": start_date,
        "finish_date": end_date,
        "debug_mode": include_logs,
        "export_csv": False,
        "export_json": include_trades,
        "export_chart": False,
        "export_tradingview": False,
        "fast_mode": True,
        "benchmark": False,
    }
