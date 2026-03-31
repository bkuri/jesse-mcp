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
    limiter = get_rate_limiter()
    if not limiter.acquire():
        return {"error": "Rate limit exceeded", "success": False}
    response = session.post(f"{base_url}/optimization", json=payload, timeout=timeout)
    if response.status_code == 422:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = {"error": "Unknown 422 error"}
        logger.error(f"Jesse API optimization 422: {error_detail}")
        raise RuntimeError(f"Jesse API optimization error: {error_detail}")
    response.raise_for_status()
    return response.json()


def rate_limited_monte_carlo(
    session: requests.Session,
    base_url: str,
    payload: dict,
    timeout: int = 600,
) -> Dict[str, Any]:
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
        if name == "n_trials":
            continue
        hp = {"name": name}
        if isinstance(spec, (list, tuple)) and len(spec) == 2:
            if isinstance(spec[0], float) or isinstance(spec[1], float):
                hp["type"] = "float"
                hp["min"] = spec[0]
                hp["max"] = spec[1]
            else:
                hp["type"] = "int"
                hp["min"] = spec[0]
                hp["max"] = spec[1]
        elif isinstance(spec, dict):
            hp["type"] = spec.get("type", "int")
            hp["min"] = spec.get("min", 1)
            hp["max"] = spec.get("max", 100)
            hp["default"] = spec.get("default", (hp["min"] + hp["max"]) // 2)
        else:
            hp["type"] = str(spec.get("type", "str"))
            hp["default"] = spec.get("default", "")
        hyperparameters.append(hp)

    n_trials = param_space.get("n_trials") if isinstance(param_space.get("n_trials"), int) else 50

    return {
        "id": str(uuid.uuid4()),
        "exchange": exchange,
        "routes": routes,
        "data_routes": data_routes,
        "config": config,
        "training_start_date": start_date,
        "training_finish_date": end_date,
        "testing_start_date": end_date,
        "testing_finish_date": end_date,
        "optimal_total": n_trials,
        "fast_mode": False,
        "cpu_cores": 1,
        "hyperparameters": hyperparameters,
        "state": {},
    }


def cancel_optimization(
    session: requests.Session,
    base_url: str,
    optimization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel a running optimization."""
    try:
        payload = {}
        if optimization_id:
            payload["id"] = optimization_id

        response = session.post(
            f"{base_url}/optimization/cancel",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"Optimization cancel response: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to cancel optimization: {e}")
        return {"error": str(e), "success": False}


def cancel_monte_carlo(
    session: requests.Session,
    base_url: str,
    monte_carlo_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel a running Monte Carlo simulation."""
    try:
        payload = {}
        if monte_carlo_id:
            payload["id"] = monte_carlo_id

        response = session.post(
            f"{base_url}/monte-carlo/cancel",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"Monte Carlo cancel response: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to cancel Monte Carlo: {e}")
        return {"error": str(e), "success": False}


def get_optimization_session(
    session: requests.Session,
    base_url: str,
    session_id: str,
) -> Dict[str, Any]:
    """Get details of a specific optimization session."""
    try:
        response = session.post(
            f"{base_url}/optimization/sessions/{session_id}",
            json={},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get optimization session: {e}")
        return {"error": str(e), "success": False}


def get_monte_carlo_sessions(
    session: requests.Session,
    base_url: str,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get list of Monte Carlo sessions."""
    try:
        response = session.post(
            f"{base_url}/monte-carlo/sessions",
            json={"limit": limit},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get Monte Carlo sessions: {e}")
        return {"error": str(e), "sessions": []}


def build_monte_carlo_payload(
    backtest_result: Dict[str, Any],
    simulations: int = 10000,
    block_size: int = 20,
    confidence_levels: Optional[list] = None,
) -> Dict[str, Any]:
    payload = {
        "backtest_result": backtest_result,
        "simulations": simulations,
        "block_size": block_size,
    }
    if confidence_levels:
        payload["confidence_levels"] = confidence_levels
    return payload
