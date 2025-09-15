"""
Market Intelligence Context Provider

This module provides market intelligence context to other workstreams,
especially for explaining protocol escalations and providing trading narratives.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

from .news_sentiment.lite_sentiment_engine import LiteSentimentEngine, SentimentScore

logger = logging.getLogger(__name__)


class MarketIntelligenceContextProvider:
    """
    Provides market intelligence context to other workstreams.
    
    Integrates with WS1 (Rules Engine), WS2 (Protocol Engine), and WS7 (Natural Language)
    to provide contextual explanations and trading narratives.
    """
    
    def __init__(self):
        """Initialize context provider."""
        self.sentiment_engine = LiteSentimentEngine()
        self.is_initialized = False
        
        logger.info("Market Intelligence Context Provider initialized")
    
    async def initialize(self) -> bool:
        """Initialize the context provider."""
        try:
            self.is_initialized = True
            logger.info("Market Intelligence Context Provider ready")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize context provider: {e}")
            return False
    
    async def get_protocol_escalation_context(self, level: int, reason: str, affected_symbols: List[str] = None) -> Dict[str, Any]:
        """
        Provide context for protocol escalation events.
        
        Args:
            level: Protocol escalation level
            reason: Technical reason for escalation
            affected_symbols: Symbols that may be affected
            
        Returns:
            Dict containing escalation context and explanation
        """
        try:
            # Get market context
            market_context = await self.sentiment_engine.get_market_context()
            
            # Get symbol-specific context if provided
            symbol_contexts = {}
            if affected_symbols:
                for symbol in affected_symbols[:5]:  # Limit to 5 symbols
                    symbol_contexts[symbol] = await self.sentiment_engine.get_symbol_sentiment(symbol)
            
            # Generate human-readable explanation
            explanation = await self.sentiment_engine.explain_protocol_escalation(level, reason)
            
            # Determine if escalation is news-driven
            news_driven = False
            if market_context.market_sentiment in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                news_driven = True
            
            return {
                "escalation_level": level,
                "technical_reason": reason,
                "human_explanation": explanation,
                "market_context": {
                    "sentiment": market_context.market_sentiment.name,
                    "vix_context": market_context.vix_context,
                    "key_themes": market_context.key_market_themes,
                    "earnings_context": market_context.earnings_season_context
                },
                "symbol_contexts": {
                    symbol: {
                        "sentiment": context.overall_sentiment.name,
                        "confidence": context.confidence,
                        "earnings_context": context.earnings_context,
                        "volatility_context": context.volatility_context
                    }
                    for symbol, context in symbol_contexts.items()
                },
                "news_driven": news_driven,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting protocol escalation context: {e}")
            return {
                "escalation_level": level,
                "technical_reason": reason,
                "human_explanation": f"Protocol escalated to Level {level} due to {reason}",
                "error": "Unable to retrieve full market context",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_trading_narrative(self, action: str, symbol: str, details: Dict[str, Any]) -> str:
        """
        Generate trading narrative with market context.
        
        Args:
            action: Trading action (entry, exit, roll, etc.)
            symbol: Symbol being traded
            details: Trade details (price, delta, etc.)
            
        Returns:
            str: Human-readable trading narrative
        """
        try:
            # Get symbol sentiment
            sentiment = await self.sentiment_engine.get_symbol_sentiment(symbol)
            
            # Get market context
            market_context = await self.sentiment_engine.get_market_context()
            
            # Build narrative
            narrative_parts = []
            
            # Basic action description
            if action == "entry":
                narrative_parts.append(f"Entered position in {symbol} at ${details.get('price', 'N/A')}")
            elif action == "exit":
                narrative_parts.append(f"Exited position in {symbol} at ${details.get('price', 'N/A')}")
            elif action == "roll":
                narrative_parts.append(f"Rolled {symbol} position to new expiration")
            
            # Add delta context if available
            if 'delta' in details:
                narrative_parts.append(f"Position delta: {details['delta']}")
            
            # Add sentiment context
            if sentiment.overall_sentiment != SentimentScore.NEUTRAL:
                sentiment_desc = "positive" if sentiment.overall_sentiment.value > 0 else "negative"
                narrative_parts.append(f"Current {symbol} sentiment is {sentiment_desc}")
            
            # Add earnings context if relevant
            if sentiment.earnings_context:
                narrative_parts.append(sentiment.earnings_context)
            
            # Add market context if relevant
            if market_context.market_sentiment in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                narrative_parts.append("Market sentiment is currently negative")
            elif market_context.market_sentiment in [SentimentScore.POSITIVE, SentimentScore.VERY_POSITIVE]:
                narrative_parts.append("Market sentiment is currently positive")
            
            # Add volatility context
            if "elevated" in market_context.vix_context.lower():
                narrative_parts.append("Operating in elevated volatility environment")
            
            return ". ".join(narrative_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating trading narrative: {e}")
            return f"{action.title()} {symbol} position"
    
    async def get_earnings_context_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Get earnings-specific context for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict containing earnings context
        """
        try:
            sentiment = await self.sentiment_engine.get_symbol_sentiment(symbol)
            earnings_context = await self.sentiment_engine.get_earnings_context(symbol)
            
            return {
                "symbol": symbol,
                "earnings_context": earnings_context,
                "sentiment": sentiment.overall_sentiment.name,
                "confidence": sentiment.confidence,
                "news_count": sentiment.news_count,
                "key_themes": sentiment.key_themes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting earnings context for {symbol}: {e}")
            return {
                "symbol": symbol,
                "earnings_context": f"Unable to retrieve earnings context for {symbol}",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_volatility_explanation(self, vix_level: float = None, symbols: List[str] = None) -> str:
        """
        Get explanation for current volatility conditions.
        
        Args:
            vix_level: Current VIX level
            symbols: Symbols to provide context for
            
        Returns:
            str: Volatility explanation with market context
        """
        try:
            market_context = await self.sentiment_engine.get_market_context()
            
            explanation_parts = []
            
            # VIX level context
            if vix_level:
                if vix_level > 30:
                    explanation_parts.append(f"VIX at {vix_level} indicates high market fear")
                elif vix_level > 20:
                    explanation_parts.append(f"VIX at {vix_level} shows elevated uncertainty")
                else:
                    explanation_parts.append(f"VIX at {vix_level} suggests relatively calm markets")
            
            # Market context
            explanation_parts.append(market_context.vix_context)
            
            # Key themes
            if market_context.key_market_themes:
                themes_str = ", ".join(market_context.key_market_themes[:3])
                explanation_parts.append(f"Key market themes: {themes_str}")
            
            # Symbol-specific context if provided
            if symbols:
                for symbol in symbols[:3]:  # Limit to 3 symbols
                    volatility_context = await self.sentiment_engine.get_volatility_context(symbol)
                    if volatility_context and "unable" not in volatility_context.lower():
                        explanation_parts.append(f"{symbol}: {volatility_context}")
            
            return ". ".join(explanation_parts) + "."
            
        except Exception as e:
            logger.error(f"Error getting volatility explanation: {e}")
            return f"Current VIX level: {vix_level or 'N/A'}"
    
    async def get_market_summary_for_dashboard(self) -> Dict[str, Any]:
        """
        Get market summary for dashboard display.
        
        Returns:
            Dict containing market summary for UI
        """
        try:
            market_context = await self.sentiment_engine.get_market_context()
            
            # Determine market mood emoji and color
            sentiment_map = {
                SentimentScore.VERY_POSITIVE: {"emoji": "🚀", "color": "success", "text": "Very Bullish"},
                SentimentScore.POSITIVE: {"emoji": "📈", "color": "success", "text": "Bullish"},
                SentimentScore.NEUTRAL: {"emoji": "➡️", "color": "secondary", "text": "Neutral"},
                SentimentScore.NEGATIVE: {"emoji": "📉", "color": "warning", "text": "Bearish"},
                SentimentScore.VERY_NEGATIVE: {"emoji": "🔻", "color": "danger", "text": "Very Bearish"}
            }
            
            sentiment_info = sentiment_map.get(market_context.market_sentiment, sentiment_map[SentimentScore.NEUTRAL])
            
            return {
                "market_mood": {
                    "sentiment": market_context.market_sentiment.name,
                    "emoji": sentiment_info["emoji"],
                    "color": sentiment_info["color"],
                    "text": sentiment_info["text"]
                },
                "volatility_status": market_context.vix_context,
                "earnings_status": market_context.earnings_season_context,
                "key_themes": market_context.key_market_themes[:5],  # Top 5 themes
                "last_updated": market_context.timestamp.isoformat(),
                "summary_text": self._generate_market_summary_text(market_context)
            }
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {
                "market_mood": {
                    "sentiment": "NEUTRAL",
                    "emoji": "➡️",
                    "color": "secondary",
                    "text": "Neutral"
                },
                "volatility_status": "Unable to determine",
                "earnings_status": "Unable to determine",
                "key_themes": [],
                "last_updated": datetime.utcnow().isoformat(),
                "summary_text": "Market intelligence temporarily unavailable"
            }
    
    def _generate_market_summary_text(self, market_context) -> str:
        """Generate a concise market summary text."""
        sentiment_text = {
            SentimentScore.VERY_POSITIVE: "very bullish",
            SentimentScore.POSITIVE: "bullish",
            SentimentScore.NEUTRAL: "neutral",
            SentimentScore.NEGATIVE: "bearish",
            SentimentScore.VERY_NEGATIVE: "very bearish"
        }
        
        summary = f"Market sentiment is {sentiment_text.get(market_context.market_sentiment, 'neutral')}"
        
        if "elevated" in market_context.vix_context.lower():
            summary += " with elevated volatility"
        
        if market_context.key_market_themes:
            summary += f". Key themes: {', '.join(market_context.key_market_themes[:2])}"
        
        return summary + "."
    
    async def get_contextual_intelligence(self, symbols: List[str] = None, include_market: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive contextual intelligence.
        
        Args:
            symbols: Optional symbols to include
            include_market: Whether to include market-wide context
            
        Returns:
            Dict containing comprehensive intelligence
        """
        try:
            intelligence = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbols": {},
                "market": None
            }
            
            # Get symbol-specific intelligence
            if symbols:
                for symbol in symbols:
                    sentiment = await self.sentiment_engine.get_symbol_sentiment(symbol)
                    intelligence["symbols"][symbol] = {
                        "sentiment": sentiment.overall_sentiment.name,
                        "confidence": sentiment.confidence,
                        "news_count": sentiment.news_count,
                        "key_themes": sentiment.key_themes,
                        "earnings_context": sentiment.earnings_context,
                        "volatility_context": sentiment.volatility_context
                    }
            
            # Get market-wide intelligence
            if include_market:
                market_summary = await self.get_market_summary_for_dashboard()
                intelligence["market"] = market_summary
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error getting contextual intelligence: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "symbols": {},
                "market": None,
                "error": "Unable to retrieve intelligence"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context provider statistics."""
        return {
            "initialized": self.is_initialized,
            "cache_size": len(self.sentiment_engine.sentiment_cache),
            "last_market_update": (
                self.sentiment_engine.market_context_cache.timestamp.isoformat()
                if self.sentiment_engine.market_context_cache else None
            )
        }

