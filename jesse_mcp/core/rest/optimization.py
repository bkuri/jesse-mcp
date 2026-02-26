"""
Optimization methods for Jesse REST API client.
"""

import logging
import uuid
from typing import Any, Dict, Optional

import requests

from jesse_mcp.core.rate_limiter import get_rate_limiter

logger = logging.getLogger("jesse-mcp.rest-client")


def rate_limited_optimization(
    session: requests.Session,
    base_url: str,
    payload: dict,
    timeout: int = 600,
) -> Dict[str, Any]:
    """Submit optimization request with rate limiting."""
    limiter = get_rate_limiter()
    if not limiter.acquire():
        return {"error": "Rate limit exceeded", "success": False}
    response = session.post(f"{base_url}/optimization", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def rate_limited_monte_carlo(
    session: requests.Session,
    base_url: str,
    payload: dict,
    timeout: int = 600,
) -> Dict[str, Any]:
    """Submit Monte Carlo simulation request with rate limiting."""
    limiter = get_rate_limiter()
    if not limiter.acquire():
        return {"error": "Rate limit exceeded", "success": False}
    response = session.post(f"{base_url}/monte-carlo", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_optimization_payload(
    strategy: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    param_space: Dict[str, Any],
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
) -> Dict[str, Any]:
    """Build optimization payload matching Jesse 1.13.x format."""
    routes = [
        {
            "exchange": exchange,
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
        }
    ]

    data_routes = [
        {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
        }
    ]

    config = {
        "starting_balance": starting_balance,
        "fee": fee,
        "futures_leverage": leverage,
        "type": exchange_type,
        "warm_up_candles": 240,
        "logging": {
            "balance": True,
            "trades": False,
            "signals": False,
        },
        "exchanges": {
            exchange: {
                "name": exchange,
                "fee": fee,
                "type": exchange_type,
                "balance": starting_balance,
                "futures_leverage": int(leverage),
                "futures_leverage_mode": "cross",
            }
        },
    }

    hyperparameters = []
    for name, spec in param_space.items():
        hp = {"name": name}
        if spec.get("type") == "int":
            hp["type"] = "int"
            hp["min"] = spec.get("min", 1)
            hp["max"] = spec.get("max", 100)
            hp["default"] = spec.get("default", (hp["min"] + hp["max"]) // 2)
        elif spec.get("type") == "float":
            hp["type"] = "float"
            hp["min"] = spec.get("min", 0.0)
            hp["max"] = spec.get("max", 1.0)
            hp["default"] = spec.get("default", (hp["min"] + hp["max"]) / 2)
        else:
            hp["type"] = str(spec.get("type", "str"))
            hp["default"] = spec.get("default", "")
        hyperparameters.append(hp)

    return {
        "id": str(uuid.uuid4()),
        "exchange": exchange,
        "routes": routes,
        "data_routes": data_routes,
        "config": config,
        "start_date": start_date,
        "finish_date": end_date,
        "hyperparameters": hyperparameters,
        "n_trials": param_space.get("n_trials", 50),
        "max_cpus": 1,
    }


def build_monte_carlo_payload(
    backtest_result: Dict[str, Any],
    simulations: int = 10000,
    block_size: int = 20,
    confidence_levels: Optional[list] = None,
) -> Dict[str, Any]:
    """Build Monte Carlo simulation payload."""
    payload = {
        "backtest_result": backtest_result,
        "simulations": simulations,
        "block_size": block_size,
    }

    if confidence_levels:
        payload["confidence_levels"] = confidence_levels

    return payload
