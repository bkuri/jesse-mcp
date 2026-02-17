"""
News and Opportunity Discovery Engine

Integrates multiple news sources with dynamic priority management:
- Real-time news aggregation from multiple sources
- Dynamic priority weighting based on market impact
- Sentiment analysis and opportunity scoring
- News-driven trading signal generation
- Configurable source priorities and filters
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class NewsCategory(Enum):
    """News categories for classification"""

    MARKET_NEWS = "market_news"
    REGULATORY = "regulatory"
    TECHNOLOGY = "technology"
    PARTNERSHIP = "partnership"
    SECURITY = "security"
    ADOPTION = "adoption"
    MACRO_ECONOMIC = "macro_economic"
    EARNINGS = "earnings"


class SentimentLevel(Enum):
    """Sentiment classification levels"""

    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class NewsItem:
    """Individual news item with metadata"""

    id: str
    source: str
    title: str
    content: str
    url: str
    timestamp: datetime
    category: NewsCategory
    sentiment: SentimentLevel
    sentiment_score: float  # -1.0 to 1.0
    relevance_score: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 1.0
    mentioned_symbols: List[str]
    keywords: List[str]
    priority_weight: float


@dataclass
class TradingOpportunity:
    """Trading opportunity derived from news"""

    symbol: str
    opportunity_type: str  # 'long', 'short', 'volatility'
    confidence: float  # 0.0 to 1.0
    expected_move: float  # Expected price move percentage
    timeframe: str  # '5m', '15m', '1h', '4h', '1d'
    news_items: List[NewsItem]
    risk_level: str  # 'low', 'medium', 'high'
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    position_size: float  # Recommended position size


class NewsDiscoveryEngine:
    """News and opportunity discovery engine with dynamic priorities."""

    def __init__(self, config_manager):
        """Initialize news discovery engine

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self._config = config_manager.load_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.news_cache: Dict[str, NewsItem] = {}
        self.opportunities: List[TradingOpportunity] = []

    async def initialize(self):
        """Initialize async session and connections"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Jesse-MCP-News-Engine/1.0"},
        )

    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()

    async def fetch_news_from_source(
        self, source_name: str, source_config: Dict[str, Any]
    ) -> List[NewsItem]:
        """Fetch news from a specific source

        Args:
            source_name: Name of the news source
            source_config: Configuration for the source

        Returns:
            List of news items
        """
        try:
            # This would implement actual API calls to news sources
            # For now, return mock data
            logger.info(f"Fetching news from {source_name}")

            # Mock implementation - replace with actual API calls
            mock_news = [
                NewsItem(
                    id=f"{source_name}_{i}",
                    source=source_name,
                    title=f"Market Update {i} from {source_name}",
                    content=f"Sample news content about market movements...",
                    url=f"https://{source_name}.com/news/{i}",
                    timestamp=datetime.now() - timedelta(minutes=i * 10),
                    category=NewsCategory.MARKET_NEWS,
                    sentiment=SentimentLevel.NEUTRAL,
                    sentiment_score=0.0,
                    relevance_score=0.7,
                    impact_score=0.5,
                    mentioned_symbols=["BTC", "ETH"],
                    keywords=["market", "trading", "crypto"],
                    priority_weight=source_config.get("weight", 0.1),
                )
                for i in range(5)
            ]

            return mock_news

        except Exception as e:
            logger.error(f"Failed to fetch news from {source_name}: {e}")
            return []

    async def aggregate_news(self) -> List[NewsItem]:
        """Aggregate news from all configured sources

        Returns:
            List of aggregated news items
        """
        all_news = []

        # Get news priorities from config
        news_priorities = self._config.news_priorities
        enabled_sources = [p for p in news_priorities if p.enabled]

        # Sort by priority (lower number = higher priority)
        enabled_sources.sort(key=lambda x: x.priority)

        # Fetch news from each source
        tasks = []
        for news_prio in enabled_sources:
            source_config = {
                "weight": news_prio.weight,
                "filters": news_prio.filters,
                "priority": news_prio.priority,
            }
            task = self.fetch_news_from_source(news_prio.source.value, source_config)
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_news.extend(result)
                else:
                    logger.error(f"News fetch error: {result}")

        # Sort by timestamp and priority weight
        all_news.sort(key=lambda x: (x.timestamp, -x.priority_weight), reverse=True)

        # Update cache
        for item in all_news:
            self.news_cache[item.id] = item

        logger.info(
            f"Aggregated {len(all_news)} news items from {len(enabled_sources)} sources"
        )
        return all_news

    def analyze_sentiment(self, text: str) -> Tuple[SentimentLevel, float]:
        """Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Tuple of (sentiment_level, sentiment_score)
        """
        # Mock sentiment analysis - replace with actual NLP model
        positive_words = ["bullish", "up", "gain", "profit", "growth", "adoption"]
        negative_words = ["bearish", "down", "loss", "decline", "risk", "concern"]

        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count > neg_count + 1:
            return SentimentLevel.BULLISH, min(0.8, 0.1 * (pos_count - neg_count))
        elif neg_count > pos_count + 1:
            return SentimentLevel.BEARISH, max(-0.8, -0.1 * (neg_count - pos_count))
        else:
            return SentimentLevel.NEUTRAL, 0.0

    def calculate_relevance_score(
        self, news_item: NewsItem, target_symbols: List[str]
    ) -> float:
        """Calculate relevance score for target symbols

        Args:
            news_item: News item to score
            target_symbols: List of target trading symbols

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0

        # Symbol mentions
        mentioned_symbols = set(news_item.mentioned_symbols)
        target_set = set(target_symbols)
        symbol_overlap = len(mentioned_symbols & target_set)
        if symbol_overlap > 0:
            score += 0.4 * (symbol_overlap / len(target_symbols))

        # Category relevance
        high_relevance_categories = {
            NewsCategory.MARKET_NEWS,
            NewsCategory.REGULATORY,
            NewsCategory.PARTNERSHIP,
            NewsCategory.ADOPTION,
        }
        if news_item.category in high_relevance_categories:
            score += 0.3

        # Keyword relevance
        trading_keywords = ["price", "trading", "volume", "market", "exchange"]
        keyword_matches = sum(
            1 for kw in trading_keywords if kw in news_item.content.lower()
        )
        if keyword_matches > 0:
            score += 0.3 * min(1.0, keyword_matches / len(trading_keywords))

        return min(1.0, score)

    def identify_opportunities(
        self, news_items: List[NewsItem], target_symbols: List[str]
    ) -> List[TradingOpportunity]:
        """Identify trading opportunities from news

        Args:
            news_items: List of news items to analyze
            target_symbols: List of target trading symbols

        Returns:
            List of trading opportunities
        """
        opportunities = []

        # Group news by symbol
        symbol_news = {}
        for item in news_items:
            for symbol in item.mentioned_symbols:
                if symbol in target_symbols:
                    if symbol not in symbol_news:
                        symbol_news[symbol] = []
                    symbol_news[symbol].append(item)

        # Analyze each symbol
        for symbol, items in symbol_news.items():
            if not items:
                continue

            # Calculate aggregate sentiment and impact
            avg_sentiment = sum(item.sentiment_score for item in items) / len(items)
            avg_impact = sum(item.impact_score for item in items) / len(items)
            max_relevance = max(item.relevance_score for item in items)

            # Determine opportunity type and confidence
            confidence = (
                abs(avg_sentiment) * 0.5 + avg_impact * 0.3 + max_relevance * 0.2
            )

            if confidence < 0.3:  # Skip low confidence opportunities
                continue

            if avg_sentiment > 0.2:
                opp_type = "long"
                expected_move = abs(avg_sentiment) * avg_impact * 5.0  # Up to 5% move
            elif avg_sentiment < -0.2:
                opp_type = "short"
                expected_move = abs(avg_sentiment) * avg_impact * 5.0
            else:
                opp_type = "volatility"
                expected_move = avg_impact * 3.0

            # Determine risk level
            if confidence > 0.7 and avg_impact > 0.6:
                risk_level = "high"
            elif confidence > 0.5:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Create opportunity
            opportunity = TradingOpportunity(
                symbol=symbol,
                opportunity_type=opp_type,
                confidence=confidence,
                expected_move=expected_move,
                timeframe="1h",  # Default timeframe
                news_items=items[:3],  # Top 3 relevant news items
                risk_level=risk_level,
                entry_conditions={
                    "sentiment_threshold": avg_sentiment,
                    "impact_threshold": avg_impact,
                    "min_confidence": confidence,
                },
                exit_conditions={
                    "profit_target": expected_move,
                    "stop_loss": expected_move * 0.5,
                    "time_limit": "24h",
                },
                position_size=self._calculate_position_size(confidence, risk_level),
            )

            opportunities.append(opportunity)

        # Sort by confidence
        opportunities.sort(key=lambda x: x.confidence, reverse=True)

        logger.info(
            f"Identified {len(opportunities)} trading opportunities from {len(news_items)} news items"
        )
        return opportunities

    def _calculate_position_size(self, confidence: float, risk_level: str) -> float:
        """Calculate recommended position size based on confidence and risk

        Args:
            confidence: Opportunity confidence (0.0 to 1.0)
            risk_level: Risk level ('low', 'medium', 'high')

        Returns:
            Recommended position size as percentage of portfolio
        """
        base_size = confidence * 0.1  # Base 10% max position

        risk_multipliers = {"low": 1.5, "medium": 1.0, "high": 0.5}

        return min(0.2, base_size * risk_multipliers.get(risk_level, 1.0))

    async def update_priorities(self, market_conditions: Dict[str, Any]):
        """Update news source priorities based on market conditions

        Args:
            market_conditions: Current market condition metrics
        """
        volatility = market_conditions.get("volatility", 0.5)
        volume = market_conditions.get("volume", 0.5)

        # Adjust priorities based on market conditions
        for news_prio in self._config.news_priorities:
            # Increase weight for real-time sources in high volatility
            if news_prio.source in ["twitter", "cryptopanic"] and volatility > 0.7:
                news_prio.weight = min(0.3, news_prio.weight * 1.2)

            # Increase weight for institutional sources in high volume
            elif news_prio.source in ["reuters", "bloomberg"] and volume > 0.7:
                news_prio.weight = min(0.3, news_prio.weight * 1.1)

        # Renormalize weights
        total_weight = sum(p.weight for p in self._config.news_priorities if p.enabled)
        if total_weight > 0:
            for news_prio in self._config.news_priorities:
                if news_prio.enabled:
                    news_prio.weight = news_prio.weight / total_weight

        logger.info("Updated news source priorities based on market conditions")

    async def run_discovery_cycle(
        self, target_symbols: List[str]
    ) -> List[TradingOpportunity]:
        """Run a complete news discovery cycle

        Args:
            target_symbols: List of symbols to monitor

        Returns:
            List of trading opportunities
        """
        logger.info("Starting news discovery cycle")

        # Aggregate news
        news_items = await self.aggregate_news()

        # Analyze sentiment and relevance for each item
        for item in news_items:
            if item.sentiment_score == 0.0:  # Only analyze if not already done
                sentiment, score = self.analyze_sentiment(item.content)
                item.sentiment = sentiment
                item.sentiment_score = score

            item.relevance_score = self.calculate_relevance_score(item, target_symbols)

        # Filter relevant news
        relevant_news = [item for item in news_items if item.relevance_score > 0.3]

        # Identify opportunities
        opportunities = self.identify_opportunities(relevant_news, target_symbols)

        # Update stored opportunities
        self.opportunities = opportunities

        logger.info(
            f"Discovery cycle complete: {len(opportunities)} opportunities identified"
        )
        return opportunities

    def get_top_opportunities(self, limit: int = 10) -> List[TradingOpportunity]:
        """Get top N opportunities by confidence

        Args:
            limit: Maximum number of opportunities to return

        Returns:
            List of top opportunities
        """
        return self.opportunities[:limit]

    def get_opportunities_by_symbol(self, symbol: str) -> List[TradingOpportunity]:
        """Get opportunities for a specific symbol

        Args:
            symbol: Trading symbol

        Returns:
            List of opportunities for the symbol
        """
        return [opp for opp in self.opportunities if opp.symbol == symbol]
