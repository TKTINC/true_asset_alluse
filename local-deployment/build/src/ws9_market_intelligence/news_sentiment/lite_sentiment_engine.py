"""
Lite Sentiment Engine

This module implements a lightweight sentiment analysis engine for contextual
news and market intelligence. Focuses on providing trading context around
earnings and volatility spikes without deep feed processing.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
import asyncio
import aiohttp
import json
import re
from decimal import Decimal

logger = logging.getLogger(__name__)


class SentimentScore(Enum):
    """Sentiment scoring levels."""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


class NewsSource(Enum):
    """News sources for sentiment analysis."""
    FINANCIAL_NEWS = "financial_news"
    EARNINGS_REPORTS = "earnings_reports"
    SEC_FILINGS = "sec_filings"
    SOCIAL_MEDIA = "social_media"
    ANALYST_REPORTS = "analyst_reports"


@dataclass
class SentimentSummary:
    """Sentiment summary for a symbol or market."""
    symbol: str
    overall_sentiment: SentimentScore
    confidence: float
    news_count: int
    key_themes: List[str]
    earnings_context: Optional[str]
    volatility_context: Optional[str]
    timestamp: datetime
    sources: List[NewsSource]


@dataclass
class NewsItem:
    """Individual news item."""
    title: str
    summary: str
    source: NewsSource
    sentiment: SentimentScore
    relevance: float
    timestamp: datetime
    url: Optional[str] = None
    symbols: List[str] = None


@dataclass
class MarketContext:
    """Market context summary."""
    market_sentiment: SentimentScore
    vix_context: str
    earnings_season_context: str
    key_market_themes: List[str]
    protocol_escalation_context: Optional[str]
    timestamp: datetime


class LiteSentimentEngine:
    """
    Lightweight Sentiment Analysis Engine.
    
    Provides contextual news and sentiment summaries for trading context,
    especially around earnings and volatility spikes. Designed to be lite
    and focused rather than comprehensive.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize lite sentiment engine."""
        self.config = config or {}
        self.sentiment_cache: Dict[str, SentimentSummary] = {}
        self.market_context_cache: Optional[MarketContext] = None
        self.cache_duration = timedelta(minutes=15)  # 15-minute cache
        
        # Simple keyword-based sentiment analysis (can be enhanced with ML later)
        self.positive_keywords = {
            'earnings beat', 'strong results', 'guidance raised', 'bullish', 'outperform',
            'buy rating', 'upgrade', 'positive outlook', 'strong demand', 'growth',
            'beat expectations', 'revenue growth', 'profit increase', 'expansion'
        }
        
        self.negative_keywords = {
            'earnings miss', 'weak results', 'guidance lowered', 'bearish', 'underperform',
            'sell rating', 'downgrade', 'negative outlook', 'weak demand', 'decline',
            'miss expectations', 'revenue drop', 'profit decrease', 'contraction',
            'volatility spike', 'market stress', 'uncertainty', 'risk-off'
        }
        
        self.volatility_keywords = {
            'vix spike', 'volatility surge', 'market turbulence', 'uncertainty',
            'risk-off', 'flight to quality', 'market stress', 'panic selling'
        }
        
        self.earnings_keywords = {
            'earnings', 'quarterly results', 'guidance', 'eps', 'revenue',
            'earnings call', 'financial results', 'quarterly report'
        }
        
        logger.info("Lite Sentiment Engine initialized")
    
    async def get_symbol_sentiment(self, symbol: str, force_refresh: bool = False) -> SentimentSummary:
        """
        Get sentiment summary for a specific symbol.
        
        Args:
            symbol: Stock symbol
            force_refresh: Force refresh of cached data
            
        Returns:
            SentimentSummary: Sentiment analysis for the symbol
        """
        try:
            # Check cache first
            if not force_refresh and symbol in self.sentiment_cache:
                cached_summary = self.sentiment_cache[symbol]
                if datetime.utcnow() - cached_summary.timestamp < self.cache_duration:
                    return cached_summary
            
            # Fetch fresh sentiment data
            news_items = await self._fetch_symbol_news(symbol)
            sentiment_summary = self._analyze_sentiment(symbol, news_items)
            
            # Cache the result
            self.sentiment_cache[symbol] = sentiment_summary
            
            return sentiment_summary
            
        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")
            # Return neutral sentiment on error
            return SentimentSummary(
                symbol=symbol,
                overall_sentiment=SentimentScore.NEUTRAL,
                confidence=0.0,
                news_count=0,
                key_themes=[],
                earnings_context=None,
                volatility_context=None,
                timestamp=datetime.utcnow(),
                sources=[]
            )
    
    async def get_market_context(self, force_refresh: bool = False) -> MarketContext:
        """
        Get overall market context and sentiment.
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            MarketContext: Overall market sentiment and context
        """
        try:
            # Check cache first
            if not force_refresh and self.market_context_cache:
                if datetime.utcnow() - self.market_context_cache.timestamp < self.cache_duration:
                    return self.market_context_cache
            
            # Fetch fresh market context
            market_news = await self._fetch_market_news()
            market_context = self._analyze_market_context(market_news)
            
            # Cache the result
            self.market_context_cache = market_context
            
            return market_context
            
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            # Return neutral context on error
            return MarketContext(
                market_sentiment=SentimentScore.NEUTRAL,
                vix_context="No volatility data available",
                earnings_season_context="No earnings data available",
                key_market_themes=[],
                protocol_escalation_context=None,
                timestamp=datetime.utcnow()
            )
    
    async def get_earnings_context(self, symbol: str) -> str:
        """
        Get earnings-specific context for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            str: Earnings context summary
        """
        try:
            sentiment_summary = await self.get_symbol_sentiment(symbol)
            
            if sentiment_summary.earnings_context:
                return sentiment_summary.earnings_context
            
            # Check if earnings are upcoming
            earnings_news = [item for item in await self._fetch_symbol_news(symbol) 
                           if any(keyword in item.title.lower() or keyword in item.summary.lower() 
                                 for keyword in self.earnings_keywords)]
            
            if earnings_news:
                return f"Earnings-related news detected for {symbol}. {len(earnings_news)} relevant items found."
            
            return f"No immediate earnings context for {symbol}"
            
        except Exception as e:
            logger.error(f"Error getting earnings context for {symbol}: {e}")
            return f"Unable to retrieve earnings context for {symbol}"
    
    async def get_volatility_context(self, symbol: str = None) -> str:
        """
        Get volatility-specific context.
        
        Args:
            symbol: Optional specific symbol, otherwise market-wide
            
        Returns:
            str: Volatility context summary
        """
        try:
            if symbol:
                sentiment_summary = await self.get_symbol_sentiment(symbol)
                if sentiment_summary.volatility_context:
                    return sentiment_summary.volatility_context
            
            market_context = await self.get_market_context()
            return market_context.vix_context
            
        except Exception as e:
            logger.error(f"Error getting volatility context: {e}")
            return "Unable to retrieve volatility context"
    
    async def explain_protocol_escalation(self, level: int, reason: str) -> str:
        """
        Provide context for why a protocol escalation occurred.
        
        Args:
            level: Protocol escalation level
            reason: Technical reason for escalation
            
        Returns:
            str: Human-readable explanation with market context
        """
        try:
            market_context = await self.get_market_context()
            
            explanation = f"Protocol escalated to Level {level} due to {reason}. "
            
            # Add market context
            if market_context.market_sentiment in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                explanation += "Current market sentiment is negative, which may be contributing to increased volatility. "
            
            if "volatility" in reason.lower() or "vix" in reason.lower():
                explanation += f"Market volatility context: {market_context.vix_context} "
            
            if market_context.key_market_themes:
                explanation += f"Key market themes: {', '.join(market_context.key_market_themes[:3])}. "
            
            return explanation.strip()
            
        except Exception as e:
            logger.error(f"Error explaining protocol escalation: {e}")
            return f"Protocol escalated to Level {level} due to {reason}."
    
    async def _fetch_symbol_news(self, symbol: str) -> List[NewsItem]:
        """Fetch news items for a specific symbol."""
        # In a real implementation, this would fetch from actual news APIs
        # For now, we'll simulate with some sample data
        
        sample_news = [
            NewsItem(
                title=f"{symbol} Reports Strong Q3 Earnings",
                summary=f"{symbol} beat analyst expectations with strong revenue growth",
                source=NewsSource.EARNINGS_REPORTS,
                sentiment=SentimentScore.POSITIVE,
                relevance=0.9,
                timestamp=datetime.utcnow() - timedelta(hours=2),
                symbols=[symbol]
            ),
            NewsItem(
                title=f"Analyst Upgrades {symbol} on Strong Fundamentals",
                summary=f"Major investment bank upgrades {symbol} to buy rating",
                source=NewsSource.ANALYST_REPORTS,
                sentiment=SentimentScore.POSITIVE,
                relevance=0.8,
                timestamp=datetime.utcnow() - timedelta(hours=4),
                symbols=[symbol]
            )
        ]
        
        return sample_news
    
    async def _fetch_market_news(self) -> List[NewsItem]:
        """Fetch general market news."""
        # In a real implementation, this would fetch from actual news APIs
        # For now, we'll simulate with some sample data
        
        sample_market_news = [
            NewsItem(
                title="VIX Spikes as Market Uncertainty Grows",
                summary="Volatility index rises amid concerns about economic outlook",
                source=NewsSource.FINANCIAL_NEWS,
                sentiment=SentimentScore.NEGATIVE,
                relevance=0.9,
                timestamp=datetime.utcnow() - timedelta(hours=1),
                symbols=["VIX", "SPY"]
            ),
            NewsItem(
                title="Fed Officials Signal Cautious Approach",
                summary="Federal Reserve maintains dovish stance on interest rates",
                source=NewsSource.FINANCIAL_NEWS,
                sentiment=SentimentScore.NEUTRAL,
                relevance=0.8,
                timestamp=datetime.utcnow() - timedelta(hours=3),
                symbols=["SPY", "QQQ"]
            )
        ]
        
        return sample_market_news
    
    def _analyze_sentiment(self, symbol: str, news_items: List[NewsItem]) -> SentimentSummary:
        """Analyze sentiment from news items."""
        if not news_items:
            return SentimentSummary(
                symbol=symbol,
                overall_sentiment=SentimentScore.NEUTRAL,
                confidence=0.0,
                news_count=0,
                key_themes=[],
                earnings_context=None,
                volatility_context=None,
                timestamp=datetime.utcnow(),
                sources=[]
            )
        
        # Calculate weighted sentiment
        total_sentiment = 0
        total_weight = 0
        earnings_items = []
        volatility_items = []
        themes = set()
        sources = set()
        
        for item in news_items:
            weight = item.relevance
            total_sentiment += item.sentiment.value * weight
            total_weight += weight
            sources.add(item.source)
            
            # Check for earnings context
            if any(keyword in item.title.lower() or keyword in item.summary.lower() 
                   for keyword in self.earnings_keywords):
                earnings_items.append(item)
            
            # Check for volatility context
            if any(keyword in item.title.lower() or keyword in item.summary.lower() 
                   for keyword in self.volatility_keywords):
                volatility_items.append(item)
            
            # Extract themes (simplified)
            if item.sentiment == SentimentScore.POSITIVE:
                themes.add("positive_sentiment")
            elif item.sentiment == SentimentScore.NEGATIVE:
                themes.add("negative_sentiment")
        
        # Calculate overall sentiment
        if total_weight > 0:
            avg_sentiment = total_sentiment / total_weight
            if avg_sentiment >= 1.5:
                overall_sentiment = SentimentScore.VERY_POSITIVE
            elif avg_sentiment >= 0.5:
                overall_sentiment = SentimentScore.POSITIVE
            elif avg_sentiment <= -1.5:
                overall_sentiment = SentimentScore.VERY_NEGATIVE
            elif avg_sentiment <= -0.5:
                overall_sentiment = SentimentScore.NEGATIVE
            else:
                overall_sentiment = SentimentScore.NEUTRAL
        else:
            overall_sentiment = SentimentScore.NEUTRAL
        
        # Generate context summaries
        earnings_context = None
        if earnings_items:
            earnings_context = f"Earnings-related news: {len(earnings_items)} items found"
        
        volatility_context = None
        if volatility_items:
            volatility_context = f"Volatility-related news: {len(volatility_items)} items found"
        
        confidence = min(total_weight / len(news_items), 1.0) if news_items else 0.0
        
        return SentimentSummary(
            symbol=symbol,
            overall_sentiment=overall_sentiment,
            confidence=confidence,
            news_count=len(news_items),
            key_themes=list(themes),
            earnings_context=earnings_context,
            volatility_context=volatility_context,
            timestamp=datetime.utcnow(),
            sources=list(sources)
        )
    
    def _analyze_market_context(self, news_items: List[NewsItem]) -> MarketContext:
        """Analyze overall market context from news items."""
        if not news_items:
            return MarketContext(
                market_sentiment=SentimentScore.NEUTRAL,
                vix_context="No market data available",
                earnings_season_context="No earnings data available",
                key_market_themes=[],
                protocol_escalation_context=None,
                timestamp=datetime.utcnow()
            )
        
        # Calculate market sentiment
        total_sentiment = 0
        total_weight = 0
        vix_items = []
        earnings_items = []
        themes = set()
        
        for item in news_items:
            weight = item.relevance
            total_sentiment += item.sentiment.value * weight
            total_weight += weight
            
            # Check for VIX/volatility context
            if "vix" in item.title.lower() or "volatility" in item.title.lower():
                vix_items.append(item)
            
            # Check for earnings context
            if any(keyword in item.title.lower() for keyword in self.earnings_keywords):
                earnings_items.append(item)
            
            # Extract themes
            if "fed" in item.title.lower() or "federal reserve" in item.title.lower():
                themes.add("monetary_policy")
            if "earnings" in item.title.lower():
                themes.add("earnings_season")
            if "volatility" in item.title.lower() or "vix" in item.title.lower():
                themes.add("market_volatility")
        
        # Calculate overall market sentiment
        if total_weight > 0:
            avg_sentiment = total_sentiment / total_weight
            if avg_sentiment >= 1.5:
                market_sentiment = SentimentScore.VERY_POSITIVE
            elif avg_sentiment >= 0.5:
                market_sentiment = SentimentScore.POSITIVE
            elif avg_sentiment <= -1.5:
                market_sentiment = SentimentScore.VERY_NEGATIVE
            elif avg_sentiment <= -0.5:
                market_sentiment = SentimentScore.NEGATIVE
            else:
                market_sentiment = SentimentScore.NEUTRAL
        else:
            market_sentiment = SentimentScore.NEUTRAL
        
        # Generate context summaries
        vix_context = "Normal volatility conditions"
        if vix_items:
            vix_context = f"Elevated volatility detected - {len(vix_items)} VIX-related news items"
        
        earnings_context = "Outside earnings season"
        if earnings_items:
            earnings_context = f"Earnings season activity - {len(earnings_items)} earnings-related items"
        
        return MarketContext(
            market_sentiment=market_sentiment,
            vix_context=vix_context,
            earnings_season_context=earnings_context,
            key_market_themes=list(themes),
            protocol_escalation_context=None,
            timestamp=datetime.utcnow()
        )
    
    def get_sentiment_summary_dict(self, sentiment_summary: SentimentSummary) -> Dict[str, Any]:
        """Convert sentiment summary to dictionary for API responses."""
        return asdict(sentiment_summary)
    
    def get_market_context_dict(self, market_context: MarketContext) -> Dict[str, Any]:
        """Convert market context to dictionary for API responses."""
        return asdict(market_context)
    
    async def get_contextual_summary(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Get a contextual summary for trading context.
        
        Args:
            symbols: Optional list of symbols to focus on
            
        Returns:
            Dict containing contextual trading intelligence
        """
        try:
            market_context = await self.get_market_context()
            
            summary = {
                "market_context": self.get_market_context_dict(market_context),
                "symbol_sentiments": {},
                "trading_context": {
                    "overall_market_mood": market_context.market_sentiment.name,
                    "volatility_environment": market_context.vix_context,
                    "earnings_environment": market_context.earnings_season_context,
                    "key_themes": market_context.key_market_themes
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add symbol-specific sentiment if requested
            if symbols:
                for symbol in symbols:
                    sentiment = await self.get_symbol_sentiment(symbol)
                    summary["symbol_sentiments"][symbol] = self.get_sentiment_summary_dict(sentiment)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating contextual summary: {e}")
            return {
                "error": "Unable to generate contextual summary",
                "timestamp": datetime.utcnow().isoformat()
            }

