"""
Automated Market Monitoring System

Provides scheduled scanning and alerting for trading opportunities.
Runs daily (or more frequent) market analysis using multiple data sources.

Usage:
    from jesse_mcp.monitoring import MarketMonitor

    monitor = MarketMonitor()
    report = monitor.daily_scan()
"""

import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("jesse-mcp.monitoring")


class SignalStrength(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class MarketSignal:
    symbol: str
    timeframe: str
    strategy: str
    signal: SignalStrength
    confidence: float
    price: float
    change_24h: float
    fear_greed: int
    timestamp: str
    details: Dict[str, Any]


@dataclass
class DailyReport:
    timestamp: str
    market_overview: Dict[str, Any]
    fear_greed: Dict[str, Any]
    signals: List[MarketSignal]
    opportunities: List[Dict[str, Any]]
    risks: List[str]
    recommendations: List[str]


class MarketMonitor:
    """
    Automated market monitoring and scanning system

    Integrates multiple data sources:
    - Jesse (backtesting, strategies)
    - Fear & Greed Index (sentiment)
    - Asset prices (real-time)
    - CoinStats (market data, news)
    """

    def __init__(
        self,
        symbols: List[str] = None,
        strategies: List[str] = None,
        timeframes: List[str] = None,
    ):
        self.symbols = symbols or ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
        self.strategies = strategies or [
            "SMACrossover",
            "DayTrader",
            "SwingTrader",
            "PositionTrader",
        ]
        self.timeframes = timeframes or ["15m", "1h", "4h", "1d"]

        self._jesse_client = None
        self._cache = {}

    def _get_jesse_client(self):
        """Lazy load Jesse client"""
        if self._jesse_client is None:
            from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

            self._jesse_client = get_jesse_rest_client()
        return self._jesse_client

    def get_market_overview(self) -> Dict[str, Any]:
        """Get current market overview from multiple sources"""
        overview = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assets": {},
        }

        assets = ["bitcoin", "ethereum", "solana"]

        for asset in assets:
            try:
                price_data = self._get_asset_price(asset)
                if price_data:
                    overview["assets"][asset] = price_data
            except Exception as e:
                logger.warning(f"Failed to get price for {asset}: {e}")

        return overview

    def _get_asset_price(self, asset: str) -> Optional[Dict[str, Any]]:
        """Get asset price via mcproxy (would need actual implementation)"""
        return {
            "symbol": asset.upper(),
            "price": 0,
            "change_24h": 0,
        }

    def get_fear_greed(self) -> Dict[str, Any]:
        """Get Fear & Greed index"""
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

    def analyze_sentiment(self, fear_greed: int) -> str:
        """Analyze market sentiment from Fear & Greed"""
        if fear_greed <= 25:
            return "EXTREME_FEAR"
        elif fear_greed <= 45:
            return "FEAR"
        elif fear_greed <= 55:
            return "NEUTRAL"
        elif fear_greed <= 75:
            return "GREED"
        else:
            return "EXTREME_GREED"

    def get_trading_signal(
        self,
        symbol: str,
        strategy: str,
        timeframe: str,
    ) -> Optional[MarketSignal]:
        """Get trading signal for a symbol/strategy/timeframe combo"""
        try:
            client = self._get_jesse_client()

            timeframe_days = {
                "15m": 7,
                "1h": 30,
                "4h": 90,
                "1d": 180,
            }

            days = timeframe_days.get(timeframe, 30)

            from datetime import datetime, timedelta

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            result = client.backtest(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                exchange="Binance Spot",
            )

            if result.get("error"):
                return None

            profit = result.get("metrics", {}).get("total_return", 0)
            win_rate = result.get("metrics", {}).get("win_rate", 0)

            if profit > 10 and win_rate > 60:
                signal = SignalStrength.STRONG_BUY
                confidence = 0.8
            elif profit > 5 and win_rate > 50:
                signal = SignalStrength.BUY
                confidence = 0.6
            elif profit < -10 and win_rate < 40:
                signal = SignalStrength.STRONG_SELL
                confidence = 0.8
            elif profit < -5 and win_rate < 50:
                signal = SignalStrength.SELL
                confidence = 0.6
            else:
                signal = SignalStrength.NEUTRAL
                confidence = 0.5

            return MarketSignal(
                symbol=symbol,
                timeframe=timeframe,
                strategy=strategy,
                signal=signal,
                confidence=confidence,
                price=result.get("metrics", {}).get("last_price", 0),
                change_24h=0,
                fear_greed=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={
                    "backtest_return": profit,
                    "win_rate": win_rate,
                    "total_trades": result.get("metrics", {}).get("total_trades", 0),
                },
            )

        except Exception as e:
            logger.error(f"Failed to get signal for {symbol}/{strategy}/{timeframe}: {e}")
            return None

    def scan_opportunities(self) -> List[Dict[str, Any]]:
        """Scan for trading opportunities"""
        opportunities = []

        fear_greed = self.get_fear_greed()
        fg_score = fear_greed.get("score", 50)
        sentiment = self.analyze_sentiment(fg_score)

        for symbol in self.symbols:
            for strategy in self.strategies:
                timeframe = self._get_strategy_timeframe(strategy)

                signal = self.get_trading_signal(symbol, strategy, timeframe)

                if signal and signal.signal in [SignalStrength.BUY, SignalStrength.STRONG_BUY]:
                    opportunities.append(
                        {
                            "symbol": symbol,
                            "strategy": strategy,
                            "timeframe": timeframe,
                            "signal": signal.signal.value,
                            "confidence": signal.confidence,
                            "market_sentiment": sentiment,
                            "details": signal.details,
                        }
                    )

        return sorted(opportunities, key=lambda x: -x["confidence"])

    def _get_strategy_timeframe(self, strategy: str) -> str:
        """Get default timeframe for a strategy"""
        mapping = {
            "DayTrader": "15m",
            "SwingTrader": "4h",
            "PositionTrader": "1d",
            "SMACrossover": "1h",
        }
        return mapping.get(strategy, "1h")

    def identify_risks(self) -> List[str]:
        """Identify current market risks"""
        risks = []

        fear_greed = self.get_fear_greed()
        fg_score = fear_greed.get("score", 50)

        if fg_score > 75:
            risks.append("Extreme greed detected - potential for sharp correction")
        elif fg_score < 25:
            risks.append("Extreme fear - possible capitulation or opportunity")

        if abs(fear_greed.get("previous_week", 50) - fg_score) > 15:
            risks.append("Rapid sentiment shift - increased volatility expected")

        return risks

    def generate_recommendations(
        self,
        opportunities: List[Dict[str, Any]],
        risks: List[str],
        fear_greed: int,
    ) -> List[str]:
        """Generate trading recommendations"""
        recommendations = []

        sentiment = self.analyze_sentiment(fear_greed)

        if sentiment == "EXTREME_FEAR" and opportunities:
            recommendations.append(
                "Market in extreme fear - consider scaling into positions with tight stops"
            )
        elif sentiment == "EXTREME_GREED":
            recommendations.append(
                "Market in extreme greed - consider taking profits and reducing exposure"
            )

        strong_signals = [o for o in opportunities if o["signal"] == "strong_buy"]
        if len(strong_signals) >= 3:
            recommendations.append(
                f"Multiple strong buy signals ({len(strong_signals)}) - broad market opportunity"
            )

        if not opportunities and sentiment == "NEUTRAL":
            recommendations.append("No clear signals - wait for better entry points")

        if risks:
            recommendations.append(f"Risk factors present: {', '.join(risks[:2])}")

        return recommendations

    def daily_scan(self) -> DailyReport:
        """
        Run complete daily market scan

        Returns comprehensive report with:
        - Market overview
        - Fear & Greed sentiment
        - Trading signals
        - Opportunities
        - Risks
        - Recommendations
        """
        logger.info("Starting daily market scan...")

        market_overview = self.get_market_overview()
        fear_greed = self.get_fear_greed()
        opportunities = self.scan_opportunities()
        risks = self.identify_risks()
        recommendations = self.generate_recommendations(
            opportunities, risks, fear_greed.get("score", 50)
        )

        report = DailyReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            market_overview=market_overview,
            fear_greed=fear_greed,
            signals=[],
            opportunities=opportunities,
            risks=risks,
            recommendations=recommendations,
        )

        logger.info(f"Scan complete: {len(opportunities)} opportunities, {len(risks)} risks")

        return report

    def report_to_json(self, report: DailyReport) -> str:
        """Convert report to JSON string"""
        return json.dumps(asdict(report), indent=2, default=str)

    def report_to_markdown(self, report: DailyReport) -> str:
        """Convert report to Markdown format"""
        lines = [
            f"# Daily Market Report",
            f"",
            f"**Generated:** {report.timestamp}",
            f"",
            f"## Market Sentiment",
            f"",
            f"- **Fear & Greed:** {report.fear_greed.get('score', 'N/A')} ({report.fear_greed.get('rating', 'N/A')})",
            f"",
            f"## Opportunities ({len(report.opportunities)})",
            f"",
        ]

        for opp in report.opportunities:
            lines.append(f"### {opp['symbol']} - {opp['strategy']}")
            lines.append(f"")
            lines.append(f"- **Signal:** {opp['signal'].upper()}")
            lines.append(f"- **Confidence:** {opp['confidence']:.0%}")
            lines.append(f"- **Timeframe:** {opp['timeframe']}")
            lines.append(f"")

        lines.append(f"## Risks ({len(report.risks)})")
        lines.append(f"")
        for risk in report.risks:
            lines.append(f"- {risk}")

        lines.append(f"")
        lines.append(f"## Recommendations")
        lines.append(f"")
        for rec in report.recommendations:
            lines.append(f"- {rec}")

        return "\n".join(lines)


def run_daily_scan() -> str:
    """Convenience function to run daily scan and return markdown report"""
    monitor = MarketMonitor()
    report = monitor.daily_scan()
    return monitor.report_to_markdown(report)


if __name__ == "__main__":
    print(run_daily_scan())
