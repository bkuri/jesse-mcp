"""
Exchange configuration for Jesse REST API client.

Contains symbol patterns, timeframes, and other exchange-specific settings.
"""

import re
from typing import Dict, Any

EXCHANGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "Binance": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,5}$",
        "symbol_format": "BTC-USDT",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Bybit": {
        "symbol_pattern": r"^[A-Z]{3,10}[A-Z]{3,5}$",
        "symbol_format": "BTCUSDT",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "OKX": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,5}(-[A-Z]{3,10})?$",
        "symbol_format": "BTC-USDT-SWAP",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Coinbase": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,4}$",
        "symbol_format": "BTC-USD",
        "timeframes": ["1m", "5m", "15m", "1h", "6h", "1d"],
        "supports_futures": False,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Gate": {
        "symbol_pattern": r"^[A-Z]{2,10}_[A-Z]{3,5}$",
        "symbol_format": "BTC_USDT",
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "8h", "1d", "1w", "1M"],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
    "Hyperliquid": {
        "symbol_pattern": r"^[A-Z]{2,10}$",
        "symbol_format": "BTC",
        "timeframes": [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
        ],
        "supports_futures": True,
        "supports_spot": False,
        "api_prefix": None,
    },
    "Apex": {
        "symbol_pattern": r"^[A-Z]{2,10}-[A-Z]{3,5}$",
        "symbol_format": "BTC-USDT",
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        "supports_futures": True,
        "supports_spot": False,
        "api_prefix": None,
    },
    "Bitfinex": {
        "symbol_pattern": r"^[tT][A-Z]{3,6}[A-Z]{3,6}$|^[A-Z]{2,6}/[A-Z]{3,6}$",
        "symbol_format": "tBTCUST",
        "timeframes": [
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "3h",
            "6h",
            "12h",
            "1d",
            "1w",
            "1M",
        ],
        "supports_futures": True,
        "supports_spot": True,
        "api_prefix": None,
    },
}


def list_supported_exchanges() -> list[str]:
    """Get list of supported exchanges."""
    return list(EXCHANGE_CONFIG.keys())


def get_exchange_config(exchange: str) -> Dict[str, Any]:
    """Get configuration for a specific exchange."""
    config = EXCHANGE_CONFIG.get(exchange)
    if config is None:
        return {
            "error": f"Unknown exchange: {exchange}",
            "valid_exchanges": list(EXCHANGE_CONFIG.keys()),
        }
    return {"exchange": exchange, **config}


def validate_symbol(exchange: str, symbol: str) -> Dict[str, Any]:
    """Validate a trading symbol format for a specific exchange."""
    import logging

    logger = logging.getLogger("jesse-mcp.rest-client")

    config = EXCHANGE_CONFIG.get(exchange)
    if config is None:
        return {
            "valid": False,
            "error": f"Unknown exchange: {exchange}",
            "valid_exchanges": list(EXCHANGE_CONFIG.keys()),
        }

    pattern = config.get("symbol_pattern", "")
    if not pattern:
        return {
            "valid": True,
            "warning": "No validation pattern defined for this exchange",
            "symbol": symbol,
            "expected_format": config.get("symbol_format"),
        }

    if re.match(pattern, symbol):
        logger.info(f"✅ Symbol validated: {symbol} for {exchange}")
        return {
            "valid": True,
            "symbol": symbol,
            "exchange": exchange,
            "expected_format": config.get("symbol_format"),
        }
    else:
        logger.warning(f"⚠️ Invalid symbol format: {symbol} for {exchange}")
        return {
            "valid": False,
            "error": f"Symbol '{symbol}' does not match expected format for {exchange}",
            "symbol": symbol,
            "exchange": exchange,
            "expected_format": config.get("symbol_format"),
            "pattern": pattern,
        }


def validate_timeframe(exchange: str, timeframe: str) -> Dict[str, Any]:
    """Validate a timeframe for a specific exchange."""
    config = EXCHANGE_CONFIG.get(exchange)
    if config is None:
        return {
            "valid": False,
            "error": f"Unknown exchange: {exchange}",
            "valid_exchanges": list(EXCHANGE_CONFIG.keys()),
        }

    supported = config.get("timeframes", [])
    if timeframe in supported:
        return {"valid": True, "timeframe": timeframe, "exchange": exchange}
    else:
        return {
            "valid": False,
            "error": f"Timeframe '{timeframe}' not supported by {exchange}",
            "timeframe": timeframe,
            "exchange": exchange,
            "supported_timeframes": supported,
        }


def map_exchange_name(exchange: str, exchange_type: str = "futures") -> str:
    """Map exchange name to Jesse's full exchange name format."""
    exchange_map = {
        "Binance": {
            "spot": "Binance Spot",
            "futures": "Binance Perpetual Futures",
        },
        "Bybit": {
            "spot": "Bybit Spot",
            "futures": "Bybit USDT Perpetual",
        },
        "OKX": {
            "spot": "OKX Spot",
            "futures": "OKX USDT Perpetual",
        },
        "Coinbase": {
            "spot": "Coinbase Spot",
            "futures": "Coinbase Futures",
        },
        "Gate": {
            "spot": "Gate Spot",
            "futures": "Gate USDT Perpetual",
        },
        "Bitfinex": {
            "spot": "Bitfinex Spot",
            "futures": "Bitfinex Futures",
        },
        "Hyperliquid": {
            "spot": "Hyperliquid",
            "futures": "Hyperliquid",
        },
        "Apex": {
            "spot": "Apex Spot",
            "futures": "Apex Futures",
        },
    }

    if exchange in exchange_map:
        return exchange_map[exchange].get(exchange_type, exchange_map[exchange]["futures"])

    return exchange
