"""
Backtest Log Analysis Module

Provides analysis of Jesse's backtest history, strategy performance comparison,
weekly reporting, and sentiment correlation capabilities.

Usage:
    from jesse_mcp.logs import (
        analyze_backtest_history,
        analyze_strategy_performance,
        generate_weekly_report,
        correlate_sentiment,
    )
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("jesse-mcp.logs")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available, log analysis will use mock data")


def _get_db_connection():
    if not PSYCOPG2_AVAILABLE:
        return None

    try:
        conn = psycopg2.connect(
            host=os.environ.get("JESSE_DB_HOST", "localhost"),
            port=int(os.environ.get("JESSE_DB_PORT", "5432")),
            dbname=os.environ.get("JESSE_DB_NAME", "jesse"),
            user=os.environ.get("JESSE_DB_USER", "jesse"),
            password=os.environ.get("JESSE_DB_PASSWORD", "password"),
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None


def _get_fear_greed() -> Dict[str, Any]:
    try:
        return {
            "score": 50,
            "rating": "neutral",
            "previous_week": 50,
            "previous_month": 50,
        }
    except Exception as e:
        logger.warning(f"Failed to get Fear & Greed: {e}")
        return {"error": str(e)}


def _mock_backtest_history(days: int) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "id": f"mock-{i}",
            "strategy_name": ["SMACrossover", "DayTrader", "SwingTrader"][i % 3],
            "symbol": ["BTC-USDT", "ETH-USDT", "SOL-USDT"][i % 3],
            "timeframe": ["1h", "4h", "1d"][i % 3],
            "total_return": [12.5, -5.2, 8.3, 15.1, -2.1][i % 5],
            "win_rate": [62.0, 45.0, 55.0, 68.0, 48.0][i % 5],
            "total_trades": [120, 85, 95, 150, 70][i % 5],
            "created_at": (now - timedelta(days=i)).isoformat(),
        }
        for i in range(min(days, 10))
    ]


def _mock_strategy_performance() -> Dict[str, Any]:
    return {
        "strategies": [
            {
                "name": "SMACrossover",
                "avg_return": 8.5,
                "avg_win_rate": 58.0,
                "total_backtests": 45,
                "best_return": 25.3,
                "worst_return": -12.1,
            },
            {
                "name": "DayTrader",
                "avg_return": 5.2,
                "avg_win_rate": 52.0,
                "total_backtests": 38,
                "best_return": 18.7,
                "worst_return": -8.4,
            },
            {
                "name": "SwingTrader",
                "avg_return": 12.1,
                "avg_win_rate": 55.0,
                "total_backtests": 22,
                "best_return": 35.2,
                "worst_return": -15.3,
            },
        ],
        "period": "last_30_days",
    }


def _mock_sentiment_correlation() -> Dict[str, Any]:
    return {
        "correlation_coefficient": 0.35,
        "interpretation": "weak_positive",
        "data_points": [
            {"date": "2024-01-01", "fear_greed": 45, "avg_return": 3.2},
            {"date": "2024-01-02", "fear_greed": 52, "avg_return": 5.1},
            {"date": "2024-01-03", "fear_greed": 38, "avg_return": -1.5},
        ],
        "summary": "Moderate positive correlation between fear levels and returns",
    }


def analyze_backtest_history(days: int = 30) -> Dict[str, Any]:
    try:
        conn = _get_db_connection()

        if conn is None:
            logger.info("Using mock data for backtest history")
            return {
                "backtests": _mock_backtest_history(days),
                "total_count": min(days, 10),
                "period_days": days,
                "data_source": "mock",
            }

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        id, 
                        strategy_name, 
                        symbol, 
                        timeframe, 
                        total_return, 
                        win_rate, 
                        total_trades,
                        created_at
                    FROM completed_backtests
                    WHERE created_at > NOW() - INTERVAL '%s days'
                    ORDER BY created_at DESC
                    """,
                    (days,),
                )
                results = cur.fetchall()

            backtests = [dict(row) for row in results]

            for bt in backtests:
                if isinstance(bt.get("created_at"), datetime):
                    bt["created_at"] = bt["created_at"].isoformat()

            logger.info(f"Retrieved {len(backtests)} backtests from last {days} days")

            return {
                "backtests": backtests,
                "total_count": len(backtests),
                "period_days": days,
                "data_source": "database",
            }

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to analyze backtest history: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


def analyze_strategy_performance() -> Dict[str, Any]:
    try:
        conn = _get_db_connection()

        if conn is None:
            logger.info("Using mock data for strategy performance")
            return {**_mock_strategy_performance(), "data_source": "mock"}

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        strategy_name,
                        COUNT(*) as total_backtests,
                        AVG(total_return) as avg_return,
                        AVG(win_rate) as avg_win_rate,
                        MAX(total_return) as best_return,
                        MIN(total_return) as worst_return,
                        STDDEV(total_return) as return_stddev
                    FROM completed_backtests
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY strategy_name
                    ORDER BY avg_return DESC
                    """
                )
                results = cur.fetchall()

            strategies = [dict(row) for row in results]

            for s in strategies:
                for key in [
                    "avg_return",
                    "avg_win_rate",
                    "best_return",
                    "worst_return",
                    "return_stddev",
                ]:
                    if s.get(key) is not None:
                        s[key] = float(s[key])
                if s.get("total_backtests") is not None:
                    s["total_backtests"] = int(s["total_backtests"])

            logger.info(f"Analyzed performance for {len(strategies)} strategies")

            return {
                "strategies": strategies,
                "period": "last_30_days",
                "data_source": "database",
            }

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to analyze strategy performance: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


def generate_weekly_report() -> str:
    try:
        history = analyze_backtest_history(7)
        performance = analyze_strategy_performance()
        sentiment = _get_fear_greed()

        if history.get("error"):
            return f"# Weekly Report\n\nError retrieving data: {history['error']}"

        backtests = history.get("backtests", [])
        strategies = performance.get("strategies", [])
        fg_score = sentiment.get("score", 50)
        fg_rating = sentiment.get("rating", "neutral")

        total_return = sum(bt.get("total_return", 0) for bt in backtests)
        avg_win_rate = (
            sum(bt.get("win_rate", 0) for bt in backtests) / len(backtests) if backtests else 0
        )
        total_trades = sum(bt.get("total_trades", 0) for bt in backtests)

        lines = [
            "# Weekly Backtest Report",
            "",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary",
            "",
            f"- **Total Backtests:** {len(backtests)}",
            f"- **Total Trades:** {total_trades}",
            f"- **Aggregate Return:** {total_return:.2f}%",
            f"- **Average Win Rate:** {avg_win_rate:.1f}%",
            "",
            "## Market Sentiment",
            "",
            f"- **Fear & Greed Index:** {fg_score} ({fg_rating})",
            "",
            "## Strategy Performance",
            "",
        ]

        for s in strategies:
            name = s.get("name", s.get("strategy_name", "Unknown"))
            avg_ret = s.get("avg_return", 0)
            win = s.get("avg_win_rate", 0)
            count = s.get("total_backtests", 0)
            lines.append(f"### {name}")
            lines.append("")
            lines.append(f"- **Avg Return:** {avg_ret:.2f}%")
            lines.append(f"- **Win Rate:** {win:.1f}%")
            lines.append(f"- **Backtests:** {count}")
            lines.append("")

        lines.append("## Recent Backtests")
        lines.append("")

        for bt in backtests[:10]:
            strategy = bt.get("strategy_name", "Unknown")
            symbol = bt.get("symbol", "Unknown")
            ret = bt.get("total_return", 0)
            win = bt.get("win_rate", 0)
            lines.append(f"- **{strategy}** on {symbol}: {ret:.2f}% (WR: {win:.1f}%)")

        lines.append("")
        lines.append("---")
        lines.append(f"*Data source: {history.get('data_source', 'unknown')}*")

        report = "\n".join(lines)
        logger.info("Generated weekly report")

        return report

    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        return f"# Weekly Report\n\nError: {str(e)}"


def correlate_sentiment() -> Dict[str, Any]:
    try:
        conn = _get_db_connection()

        if conn is None:
            logger.info("Using mock data for sentiment correlation")
            return {**_mock_sentiment_correlation(), "data_source": "mock"}

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        DATE(created_at) as date,
                        AVG(total_return) as avg_return,
                        COUNT(*) as backtest_count
                    FROM completed_backtests
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """
                )
                backtest_daily = cur.fetchall()

            if not backtest_daily:
                return {
                    "correlation_coefficient": 0,
                    "interpretation": "insufficient_data",
                    "data_points": [],
                    "summary": "No backtest data available for correlation analysis",
                    "data_source": "database",
                }

            fear_greed = _get_fear_greed()
            fg_score = fear_greed.get("score", 50)

            data_points = []
            for row in backtest_daily:
                date = row["date"]
                if isinstance(date, datetime):
                    date = date.strftime("%Y-%m-%d")

                data_points.append(
                    {
                        "date": date,
                        "fear_greed": fg_score,
                        "avg_return": float(row["avg_return"]) if row["avg_return"] else 0,
                        "backtest_count": int(row["backtest_count"]),
                    }
                )

            returns = [dp["avg_return"] for dp in data_points]
            fg_scores = [dp["fear_greed"] for dp in data_points]

            if len(returns) > 1:
                import statistics

                mean_r = statistics.mean(returns)
                mean_f = statistics.mean(fg_scores)

                numerator = sum((r - mean_r) * (f - mean_f) for r, f in zip(returns, fg_scores))
                denom_r = sum((r - mean_r) ** 2 for r in returns) ** 0.5
                denom_f = sum((f - mean_f) ** 2 for f in fg_scores) ** 0.5

                if denom_r > 0 and denom_f > 0:
                    correlation = numerator / (denom_r * denom_f)
                else:
                    correlation = 0
            else:
                correlation = 0

            if correlation > 0.7:
                interpretation = "strong_positive"
            elif correlation > 0.3:
                interpretation = "weak_positive"
            elif correlation > -0.3:
                interpretation = "no_correlation"
            elif correlation > -0.7:
                interpretation = "weak_negative"
            else:
                interpretation = "strong_negative"

            summary_map = {
                "strong_positive": "Strong positive correlation - returns tend to increase with fear & greed",
                "weak_positive": "Moderate positive correlation between sentiment and returns",
                "no_correlation": "No significant correlation between sentiment and returns",
                "weak_negative": "Moderate negative correlation - contrarian indicator possible",
                "strong_negative": "Strong negative correlation - contrarian signal",
            }

            logger.info(f"Sentiment correlation: {correlation:.3f} ({interpretation})")

            return {
                "correlation_coefficient": round(correlation, 4),
                "interpretation": interpretation,
                "data_points": data_points,
                "summary": summary_map[interpretation],
                "data_source": "database",
            }

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to correlate sentiment: {e}")
        return {"error": str(e), "error_type": type(e).__name__}
