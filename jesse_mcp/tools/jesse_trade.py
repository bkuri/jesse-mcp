"""
jesse.trade Community API Tools

Browse, search, and analyze community-published strategies from jesse.trade.
Uses the public jesse.trade REST API (api2.jesse.trade) to access community
strategy data including source code, metrics, and rankings.

Requires JESSE_TRADE_API_KEY environment variable (Bearer token from
jesse.trade session).

API endpoints reverse-engineered from jesse.trade:
- GET /strategies/periods — list available backtest periods
- GET /strategies?period=X&sort_by=Y — browse community strategies
- GET /strategies/{slug}/metrics?period=X&symbol=Y&timeframe=Z — detailed metrics
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("jesse-mcp.community")

_BASE_URL = "https://api2.jesse.trade"


def _get_headers() -> Dict[str, str]:
    """Build auth headers from environment variable."""
    token = os.environ.get("JESSE_TRADE_API_KEY", "")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _strip_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact metrics dict without bulky equity_curve data."""
    stripped = {k: v for k, v in metrics.items() if k != "equity_curve"}
    # Sanitize NaN/Infinity values
    import math

    for k, v in stripped.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            stripped[k] = 0
    return stripped


def register_jesse_trade_tools(mcp):
    """Register jesse.trade community API tools with the MCP server."""

    @mcp.tool
    @tool_error_handler
    def list_periods() -> Dict[str, Any]:
        """
        List all available backtest periods on jesse.trade.

        Returns monthly and quarterly periods (e.g. 'January 2026', 'Q1 of 2026').
        Use this to find valid period values for browse_community_strategies()
        and get_strategy_metrics().

        Returns:
            Dict with 'periods' list of period strings and 'count'
        """
        r = requests.get(f"{_BASE_URL}/strategies/periods", headers=_get_headers(), timeout=30)
        r.raise_for_status()
        data = r.json()
        periods = data.get("periods", [])
        return {
            "periods": periods,
            "count": len(periods),
            "monthly": [p for p in periods if not p.startswith("Q") and "-" not in p.split()[-1]],
            "quarterly": [p for p in periods if p.startswith("Q")],
        }

    @mcp.tool
    @tool_error_handler
    def browse_community_strategies(
        period: str,
        sort_by: str = "Sharpe Ratio",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Browse community strategies from jesse.trade sorted by performance metrics.

        Returns strategies with their key metrics (Sharpe, return, drawdown, win rate)
        and metadata (name, author, symbols, timeframes). Use this to discover
        strategies worth investigating further with get_strategy_metrics() or
        get_strategy_code().

        Args:
            period: Backtest period, e.g. 'December 2025', 'Q1 of 2026'. Use list_periods() for valid values.
            sort_by: Sort metric. Options: 'Sharpe Ratio', 'Total Return', 'Win Rate', 'Net Profit', 'Total Trades'.
            limit: Max strategies to return (default 50, max 100)
        """
        sort_options = {
            "sharpe ratio": "Sharpe Ratio",
            "total return": "Total Return",
            "win rate": "Win Rate",
            "net profit": "Net Profit",
            "total trades": "Total Trades",
        }
        sort_key = sort_options.get(sort_by.lower(), sort_by)
        limit = max(1, min(limit, 100))

        r = requests.get(
            f"{_BASE_URL}/strategies",
            headers=_get_headers(),
            params={"period": period, "sort_by": sort_key},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        strategies = data.get("strategies", [])[:limit]

        results = []
        for s in strategies:
            m = s.get("strategy_metrics", {})
            results.append(
                {
                    "name": s.get("name"),
                    "slug": s.get("slug"),
                    "author": s.get("user", {}).get("name") if isinstance(s.get("user"), dict) else None,
                    "symbol": s.get("symbol"),
                    "timeframe": s.get("timeframe"),
                    "exchange": m.get("exchange"),
                    "sharpe_ratio": m.get("sharpe_ratio", 0),
                    "sortino_ratio": m.get("sortino_ratio", 0),
                    "total_return_pct": m.get("net_profit_percentage", 0),
                    "annual_return_pct": m.get("annual_return", 0),
                    "max_drawdown_pct": m.get("max_drawdown", 0),
                    "win_rate": m.get("win_rate", 0),
                    "total_trades": m.get("total_completed_trades", 0),
                    "calmar_ratio": m.get("calmar_ratio", 0),
                    "type": s.get("type"),
                    "price": s.get("price", 0),
                    "views": s.get("views", 0),
                    "backtest_symbols": s.get("backtest_symbols", []),
                    "backtest_timeframes": s.get("backtest_timeframes", []),
                }
            )

        return {
            "period": period,
            "sort_by": sort_key,
            "strategies": results,
            "count": len(results),
        }

    @mcp.tool
    @tool_error_handler
    def get_strategy_metrics(
        slug: str,
        period: str,
        symbol: str = "BTC-USDT",
        timeframe: str = "1h",
        include_equity_curve: bool = False,
    ) -> Dict[str, Any]:
        """
        Get detailed backtest metrics for a specific community strategy.

        Returns comprehensive performance data including Sharpe, Sortino, Calmar
        ratios, trade statistics, streaks, and optionally the full equity curve.
        Use after browse_community_strategies() to deep-dive on promising strategies.

        Args:
            slug: Strategy slug from jesse.trade URL (e.g. 'rsi-trend', 'trend-following')
            period: Backtest period (e.g. 'December 2025'). Use list_periods() for valid values.
            symbol: Trading pair (default 'BTC-USDT')
            timeframe: Candle timeframe (default '1h')
            include_equity_curve: Include full equity curve data (default False, can be large)
        """
        r = requests.get(
            f"{_BASE_URL}/strategies/{slug}/metrics",
            headers=_get_headers(),
            params={"period": period, "symbol": symbol, "timeframe": timeframe},
            timeout=30,
        )
        r.raise_for_status()
        metrics = r.json()

        if "message" in metrics:
            return {"error": metrics["message"], "slug": slug, "period": period}

        result = _strip_metrics(metrics)
        if include_equity_curve and "equity_curve" in metrics:
            result["equity_curve"] = metrics["equity_curve"]

        return result

    @mcp.tool
    @tool_error_handler
    def get_strategy_code(slug: str) -> Dict[str, Any]:
        """
        Get the full Python source code for a community strategy.

        Returns the complete strategy code, description, and metadata from
        jesse.trade. Use this to review a strategy's logic before testing it
        locally with backtest().

        Args:
            slug: Strategy slug from jesse.trade URL (e.g. 'rsi-trend')
        """
        r = requests.get(
            f"{_BASE_URL}/strategies",
            headers=_get_headers(),
            params={"period": "December 2025"},  # need a period to get the list
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        strategies = data.get("strategies", [])

        for s in strategies:
            if s.get("slug") == slug:
                return {
                    "name": s.get("name"),
                    "slug": s.get("slug"),
                    "description": s.get("description", ""),
                    "code": s.get("code", ""),
                    "author": s.get("user", {}).get("name") if isinstance(s.get("user"), dict) else None,
                    "username": s.get("user", {}).get("username") if isinstance(s.get("user"), dict) else None,
                    "symbol": s.get("symbol"),
                    "timeframe": s.get("timeframe"),
                    "exchange": s.get("strategy_metrics", {}).get("exchange"),
                    "backtest_symbols": s.get("backtest_symbols", []),
                    "backtest_timeframes": s.get("backtest_timeframes", []),
                    "type": s.get("type"),
                    "price": s.get("price", 0),
                    "created_at": s.get("created_at"),
                    "updated_at": s.get("updated_at"),
                }

        return {"error": f"Strategy '{slug}' not found in latest period results", "slug": slug}

    @mcp.tool
    @tool_error_handler
    def compare_community_strategies(
        slugs: List[str],
        period: str,
        symbol: str = "BTC-USDT",
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """
        Compare multiple community strategies side by side using their backtest metrics.

        Fetches metrics for each strategy and returns a comparison table sorted
        by Sharpe ratio. Useful for quickly identifying which community strategies
        are worth further investigation.

        Args:
            slugs: List of strategy slugs to compare (e.g. ['rsi-trend', 'simple-bollinger-bands-strategy'])
            period: Backtest period for comparison (e.g. 'December 2025')
            symbol: Trading pair (default 'BTC-USDT')
            timeframe: Candle timeframe (default '1h')
        """
        results = []
        for slug in slugs:
            r = requests.get(
                f"{_BASE_URL}/strategies/{slug}/metrics",
                headers=_get_headers(),
                params={"period": period, "symbol": symbol, "timeframe": timeframe},
                timeout=30,
            )
            if r.status_code == 200:
                metrics = r.json()
                if "message" not in metrics:
                    results.append({"slug": slug, **_strip_metrics(metrics)})
                else:
                    results.append({"slug": slug, "error": metrics["message"]})
            else:
                results.append({"slug": slug, "error": f"HTTP {r.status_code}"})

        # Sort by Sharpe ratio descending
        results.sort(key=lambda x: x.get("sharpe_ratio", float("-inf")), reverse=True)

        return {
            "period": period,
            "symbol": symbol,
            "timeframe": timeframe,
            "strategies": results,
            "count": len(results),
            "best_by_sharpe": results[0].get("slug") if results else None,
        }

    logger.info("✅ jesse.trade community tools registered")
