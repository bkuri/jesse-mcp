#!/usr/bin/env python3
"""
Jesse MCP Server - CLI entry point

Usage:
    jesse-mcp                                    # Start with stdio transport
    jesse-mcp --transport http --port 8000      # Start with HTTP transport
    jesse-mcp --cache-warm BTC-USDT             # Warm candle cache
    jesse-mcp --cache-stats                     # Show cache statistics
    jesse-mcp --cache-clear                     # Clear candle cache
    jesse-mcp --version                         # Show version
    jesse-mcp --help                            # Show help
"""

import argparse
import sys
import os


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        prog="jesse-mcp",
        description="Jesse MCP Server - MCP tools for Jesse trading framework",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version",
    )

    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="HTTP port (default: 8000)",
    )

    # Cache operations
    cache_group = parser.add_argument_group("Cache Operations")

    cache_group.add_argument(
        "--cache-warm",
        metavar="SYMBOL",
        help="Warm candle cache for symbol (e.g., BTC-USDT)",
    )

    cache_group.add_argument(
        "--cache-warm-all",
        action="store_true",
        help="Warm cache for all symbols with existing candles",
    )

    cache_group.add_argument(
        "--cache-stats",
        action="store_true",
        help="Show candle cache statistics",
    )

    cache_group.add_argument(
        "--cache-clear",
        action="store_true",
        help="Clear candle cache",
    )

    cache_group.add_argument(
        "--exchange",
        "-e",
        default="Binance Spot",
        help="Exchange name for cache operations (default: Binance Spot)",
    )

    cache_group.add_argument(
        "--timeframe",
        default="1h",
        help="Timeframe for cache warm (default: 1h)",
    )

    args = parser.parse_args()

    if args.version:
        from jesse_mcp import __version__

        print(f"jesse-mcp {__version__}")
        return 0

    if args.cache_stats:
        return _cache_stats()

    if args.cache_clear:
        return _cache_clear()

    if args.cache_warm:
        return _cache_warm(args.cache_warm, args.exchange, args.timeframe)

    if args.cache_warm_all:
        return _cache_warm_all(args.exchange, args.timeframe)

    try:
        from jesse_mcp.server import main as server_main

        if args.transport == "http":
            os.environ["JESSE_MCP_TRANSPORT"] = "http"
            os.environ["JESSE_MCP_PORT"] = str(args.port)

        server_main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _cache_stats() -> int:
    """Show cache statistics"""
    try:
        from jesse_mcp.core.candle_cache import get_candle_cache

        cache = get_candle_cache()
        stats = cache.stats()

        print("Candle Cache Statistics")
        print("=" * 40)
        print(f"Memory items:  {stats['memory_items']}")
        print(f"Memory hits:   {stats['memory_hits']}")
        print(f"Redis hits:    {stats['redis_hits']}")
        print(f"API calls:     {stats['api_calls']}")
        print(f"Evictions:     {stats['evictions']}")
        print(f"Hit rate:      {stats['hit_rate']}")
        print(f"Redis enabled: {stats['redis_enabled']}")
        return 0
    except Exception as e:
        print(f"Error getting cache stats: {e}", file=sys.stderr)
        return 1


def _cache_clear() -> int:
    """Clear candle cache"""
    try:
        from jesse_mcp.core.candle_cache import get_candle_cache

        cache = get_candle_cache()
        cache.clear()
        print("✅ Candle cache cleared")
        return 0
    except Exception as e:
        print(f"Error clearing cache: {e}", file=sys.stderr)
        return 1


def _cache_warm(symbol: str, exchange: str, timeframe: str) -> int:
    """Warm cache for specific symbol"""
    try:
        from jesse_mcp.core.candle_cache import warm_cache_from_jesse

        count = warm_cache_from_jesse(exchange, symbol, timeframe)
        if count > 0:
            print(f"✅ Warmed cache with {count} candles for {symbol}")
        else:
            print(f"⚠️ No candles found for {symbol} on {exchange}")
        return 0 if count > 0 else 1
    except Exception as e:
        print(f"Error warming cache: {e}", file=sys.stderr)
        return 1


def _cache_warm_all(exchange: str, timeframe: str) -> int:
    """Warm cache for all symbols with existing candles"""
    try:
        from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client
        from jesse_mcp.core.candle_cache import get_candle_cache, warm_cache_from_jesse

        client = get_jesse_rest_client()

        result = client.get_existing_candles()

        if "data" not in result:
            print(f"⚠️ Could not get existing candles: {result.get('error', 'Unknown error')}")
            return 1

        total = 0
        for item in result["data"]:
            if item.get("exchange") == exchange:
                symbol = item.get("symbol")
                if symbol:
                    count = warm_cache_from_jesse(exchange, symbol, timeframe)
                    if count > 0:
                        print(f"  ✅ {symbol}: {count} candles")
                        total += count

        print(f"\n✅ Total: {total} candles cached")
        return 0
    except Exception as e:
        print(f"Error warming all caches: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
