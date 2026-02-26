"""
Backtest wrapper methods for Jesse REST API client.

Contains the client method variants: backtest, cached_backtest, backtest_with_retry.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from jesse_mcp.core.cache import (
    get_backtest_cache,
    JESSE_CACHE_ENABLED,
)

logger = logging.getLogger("jesse-mcp.rest-client")


def backtest(
    session,
    base_url: str,
    routes: List[Dict[str, str]],
    start_date: str,
    end_date: str,
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
    data_routes: Optional[List[Dict[str, str]]] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    include_trades: bool = False,
    include_equity_curve: bool = False,
    include_logs: bool = False,
    auto_import_candles: bool = False,
    auto_import_max_candles: int = 50000,
    fast_mode: bool = True,
    candles_module=None,
    backtest_helpers=None,
    backtest_api=None,
) -> Dict[str, Any]:
    """Run a backtest via Jesse REST API."""
    from jesse_mcp.core.rest import candles

    candles_mod = candles_module or candles

    try:
        logger.info(f"Starting backtest via REST API with {len(routes)} routes")

        validation_error = candles_mod.validate_candle_data(
            session,
            base_url,
            routes,
            exchange,
            exchange_type,
            start_date,
            end_date,
            auto_import_candles=auto_import_candles,
            auto_import_max_candles=auto_import_max_candles,
        )
        if validation_error:
            return validation_error

        from jesse_mcp.core.rest import backtest as bt_mod

        bt_helpers = backtest_helpers or bt_mod
        bt_api = backtest_api or bt_mod

        payload = bt_helpers.build_backtest_payload(
            routes=routes,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            exchange_type=exchange_type,
            data_routes=data_routes,
            include_logs=include_logs,
            include_trades=include_trades,
            fast_mode=fast_mode,
        )

        result = bt_api.execute_backtest(session, base_url, payload)

        is_valid, message = bt_helpers.validate_backtest_result(result)
        if not is_valid:
            logger.warning(f"⚠️  Backtest result validation failed: {message}")
            return {
                "error": f"Invalid backtest result: {message}",
                "success": False,
                "raw_result": result,
            }

        logger.info(f"✅ Backtest completed for {len(routes)} routes")
        return result

    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        return {"error": str(e), "success": False}


def cached_backtest(
    session,
    base_url: str,
    routes: List[Dict[str, str]],
    start_date: str,
    end_date: str,
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
    data_routes: Optional[List[Dict[str, str]]] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    include_trades: bool = False,
    include_equity_curve: bool = False,
    include_logs: bool = False,
    auto_import_candles: bool = False,
    auto_import_max_candles: int = 50000,
    fast_mode: bool = True,
    backtest_func=None,
) -> Dict[str, Any]:
    """Run a backtest with caching support (1 hour TTL by default)."""
    if not JESSE_CACHE_ENABLED:
        bt_func = backtest_func or backtest
        return bt_func(
            session=session,
            base_url=base_url,
            routes=routes,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            data_routes=data_routes,
            hyperparameters=hyperparameters,
            include_trades=include_trades,
            include_equity_curve=include_equity_curve,
            include_logs=include_logs,
        )

    cache = get_backtest_cache()
    route_key = json.dumps(routes, sort_keys=True)
    cache_key = cache._hash_key(
        route_key,
        start_date,
        end_date,
        exchange,
        starting_balance,
        fee,
        leverage,
        exchange_type,
        json.dumps(data_routes or [], sort_keys=True) if data_routes else "",
        json.dumps(hyperparameters or {}, sort_keys=True) if hyperparameters else "",
    )

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"✅ Cache hit for backtest with {len(routes)} routes")
        return cached

    bt_func = backtest_func or backtest
    result = bt_func(
        session=session,
        base_url=base_url,
        routes=routes,
        start_date=start_date,
        end_date=end_date,
        exchange=exchange,
        starting_balance=starting_balance,
        fee=fee,
        leverage=leverage,
        exchange_type=exchange_type,
        data_routes=data_routes,
        hyperparameters=hyperparameters,
        include_trades=include_trades,
        include_equity_curve=include_equity_curve,
        include_logs=include_logs,
        auto_import_candles=auto_import_candles,
        auto_import_max_candles=auto_import_max_candles,
        fast_mode=fast_mode,
    )

    if "error" not in result:
        cache.set(cache_key, result)
        logger.debug(f"Cached backtest result for {len(routes)} routes")

    return result


def backtest_with_retry(
    session,
    base_url: str,
    routes: List[Dict[str, str]],
    start_date: str,
    end_date: str,
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
    data_routes: Optional[List[Dict[str, str]]] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    auto_import_candles: bool = False,
    auto_import_max_candles: int = 50000,
    fast_mode: bool = True,
    backtest_func=None,
    is_retryable_func=None,
) -> Dict[str, Any]:
    """Run a backtest with retry logic for transient errors."""
    import time

    from jesse_mcp.core.rest import backtest as bt_mod

    bt_func = backtest_func or backtest
    is_retryable = is_retryable_func or bt_mod.is_retryable_error

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Backtest attempt {attempt + 1}/{max_retries}: {len(routes)} routes")

            result = bt_func(
                session=session,
                base_url=base_url,
                routes=routes,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                starting_balance=starting_balance,
                fee=fee,
                leverage=leverage,
                exchange_type=exchange_type,
                data_routes=data_routes,
                hyperparameters=hyperparameters,
                auto_import_candles=auto_import_candles,
                auto_import_max_candles=auto_import_max_candles,
                fast_mode=fast_mode,
            )

            if "error" not in result and result.get("success", True):
                logger.info(f"✅ Backtest succeeded on attempt {attempt + 1}/{max_retries}")
                return result

            error_msg = result.get("error", "Unknown error")
            if is_retryable(error_msg):
                last_error = error_msg
                if attempt < max_retries - 1:
                    delay = initial_delay * (2**attempt)
                    logger.warning(f"⚠️  Retryable error: {error_msg}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
            else:
                logger.error(f"❌ Non-retryable error: {error_msg}")
                return result

        except Exception as e:
            last_error = str(e)
            logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2**attempt)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
                continue

    logger.error(f"❌ All {max_retries} retry attempts failed. Last error: {last_error}")
    return {
        "error": f"Backtest failed after {max_retries} retries: {last_error}",
        "success": False,
    }
