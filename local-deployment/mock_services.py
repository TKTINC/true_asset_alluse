"""
Mock Services for True-Asset-ALLUSE Local Deployment
Provides realistic data without external dependencies
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

class MockMarketDataService:
    """Mock market data service for local deployment"""
    
    def __init__(self):
        self.base_prices = {
            "AAPL": 175.50,
            "MSFT": 380.25,
            "GOOGL": 140.80,
            "TSLA": 250.30,
            "SPY": 450.75,
            "QQQ": 375.20,
            "VIX": 18.50
        }
        self.last_update = datetime.now()
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price with realistic fluctuation"""
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Add realistic price movement (±2%)
        fluctuation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + fluctuation)
        
        return round(current_price, 2)
    
    def get_option_data(self, symbol: str, strike: float, option_type: str, expiry: str) -> Dict[str, Any]:
        """Get mock option data"""
        underlying_price = self.get_current_price(symbol)
        
        # Simple option pricing mock
        if option_type.lower() == "put":
            intrinsic = max(strike - underlying_price, 0)
            time_value = random.uniform(0.5, 3.0)
        else:  # call
            intrinsic = max(underlying_price - strike, 0)
            time_value = random.uniform(0.5, 3.0)
        
        option_price = intrinsic + time_value
        
        # Mock Greeks
        delta = random.uniform(-0.8, 0.8) if option_type.lower() == "put" else random.uniform(0.2, 0.8)
        gamma = random.uniform(0.01, 0.05)
        theta = random.uniform(-0.1, -0.01)
        vega = random.uniform(0.1, 0.3)
        
        return {
            "symbol": symbol,
            "strike": strike,
            "option_type": option_type,
            "expiry": expiry,
            "price": round(option_price, 2),
            "underlying_price": underlying_price,
            "delta": round(delta, 3),
            "gamma": round(gamma, 4),
            "theta": round(theta, 3),
            "vega": round(vega, 3),
            "implied_volatility": round(random.uniform(0.15, 0.45), 3),
            "volume": random.randint(100, 5000),
            "open_interest": random.randint(500, 10000)
        }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status"""
        now = datetime.now()
        
        # Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
        is_open = (
            now.weekday() < 5 and  # Monday to Friday
            9.5 <= now.hour + now.minute/60 <= 16  # 9:30 AM to 4:00 PM
        )
        
        return {
            "is_open": is_open,
            "status": "OPEN" if is_open else "CLOSED",
            "next_open": "9:30 AM ET" if not is_open else None,
            "next_close": "4:00 PM ET" if is_open else None,
            "timezone": "US/Eastern"
        }

class MockAIService:
    """Mock AI service for local deployment"""
    
    def __init__(self):
        self.conversation_history = []
        self.responses = {
            # Portfolio queries
            "portfolio": [
                "Your portfolio is performing well today with a +$12,450 gain (+1.01%). All positions are within optimal risk parameters.",
                "Current portfolio value is $1,247,850 with a weekly return of +0.85%. The system is operating in Normal protocol level.",
                "Portfolio delta is -0.28, well within the target range of -0.15 to -0.45. Risk management is optimal."
            ],
            
            # Position-specific queries
            "aapl": [
                "Your AAPL Dec 15 $175 Put is up +$425 (+28.8%). Based on current market conditions, rolling to January would be advantageous.",
                "AAPL position shows strong performance with delta of -0.35. The position is capturing 65% of maximum profit potential.",
                "AAPL earnings are approaching. Historical analysis suggests maintaining current position with potential roll opportunity."
            ],
            
            "msft": [
                "MSFT position is currently down -$125 (-5.2%) but within expected range. Delta of -0.28 provides good downside protection.",
                "Microsoft's recent cloud earnings beat expectations. Consider holding position through expiration for optimal theta decay.",
                "MSFT volatility has decreased, benefiting the short put position. Time decay is working in your favor."
            ],
            
            "googl": [
                "GOOGL position is performing excellently with +$850 (+42.1%) gain. This represents strong alpha generation.",
                "Google's AI developments are driving positive sentiment. Current position captures this momentum effectively.",
                "GOOGL delta of -0.31 provides balanced exposure. Consider taking profits if position reaches 50% max profit."
            ],
            
            "tsla": [
                "TSLA call position shows +$320 (+15.6%) gain with delta of 0.45. Electric vehicle sector momentum continues.",
                "Tesla's production numbers exceeded expectations. The call position benefits from positive gamma exposure.",
                "TSLA volatility remains elevated, providing good premium collection opportunities for future positions."
            ],
            
            # Risk and system queries
            "risk": [
                "Current portfolio delta is -0.28, within the target range of -0.15 to -0.45. Protocol Level is Normal with all systems active.",
                "Risk metrics are optimal: Sharpe ratio 2.1, max drawdown 3.2%, VaR 1.8%. All Constitution v1.3 parameters are compliant.",
                "System health is excellent: Rules Engine (Active), Market Data (Connected), AI Assistant (Advisory Mode)."
            ],
            
            "performance": [
                "Weekly return of +0.85% is tracking well above the target of 0.5-1.0%. Year-to-date performance is strong.",
                "Risk-adjusted returns show a Sharpe ratio of 2.1, significantly outperforming market benchmarks.",
                "The system has generated consistent weekly returns with low volatility, demonstrating effective risk management."
            ],
            
            "system": [
                "All systems are operational: Rules Engine (Active), Constitution v1.3 (Compliant), Market Data (Connected).",
                "Protocol Level is Normal. No escalations detected. All workstreams functioning optimally.",
                "System uptime is 99.9% with all components healthy. AI Assistant is in Advisory Mode as designed."
            ],
            
            # Market analysis
            "market": [
                "Current market conditions show moderate volatility with VIX at 18.5. Options premiums are attractive for income generation.",
                "Market sentiment is cautiously optimistic with tech sector outperforming. Our positions are well-positioned for this environment.",
                "Economic indicators suggest continued market stability. The ALL-USE strategy is optimal for current conditions."
            ],
            
            # Default responses
            "default": [
                "I'm here to help with your portfolio questions. Try asking about portfolio performance, specific positions, or system status.",
                "You can ask me about individual positions (AAPL, MSFT, GOOGL, TSLA), overall performance, or risk metrics.",
                "I provide advisory insights only. All trading decisions remain with the rules-based system per Constitution v1.3."
            ]
        }
    
    def get_response(self, query: str) -> Dict[str, Any]:
        """Generate AI response based on query"""
        query_lower = query.lower()
        
        # Determine response category
        category = "default"
        for key in self.responses.keys():
            if key in query_lower:
                category = key
                break
        
        # Get random response from category
        responses = self.responses[category]
        response = random.choice(responses)
        
        # Add to conversation history
        self.conversation_history.append({
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "category": category
        })
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "advisory_only": True,
            "confidence": random.uniform(0.85, 0.98),
            "category": category
        }
    
    def get_market_insight(self) -> str:
        """Get general market insight"""
        insights = [
            "Market volatility is within normal ranges, providing good opportunities for premium collection.",
            "Tech sector momentum continues with strong earnings reports driving positive sentiment.",
            "Options market shows healthy liquidity with tight bid-ask spreads across major names.",
            "VIX levels suggest complacency, which historically provides good entry points for protective strategies.",
            "Economic data supports continued market stability with moderate growth expectations."
        ]
        return random.choice(insights)

class MockNewsService:
    """Mock news and sentiment service"""
    
    def __init__(self):
        self.news_items = [
            {
                "headline": "Apple Reports Strong Q4 Earnings, iPhone Sales Beat Expectations",
                "sentiment": "positive",
                "relevance": 0.9,
                "timestamp": datetime.now() - timedelta(hours=2),
                "source": "Financial Times",
                "impact": "bullish"
            },
            {
                "headline": "Microsoft Cloud Revenue Grows 25% Year-over-Year",
                "sentiment": "positive",
                "relevance": 0.8,
                "timestamp": datetime.now() - timedelta(hours=4),
                "source": "Reuters",
                "impact": "bullish"
            },
            {
                "headline": "Google AI Advances Drive Search Revenue Growth",
                "sentiment": "positive",
                "relevance": 0.85,
                "timestamp": datetime.now() - timedelta(hours=6),
                "source": "Bloomberg",
                "impact": "bullish"
            },
            {
                "headline": "Tesla Delivers Record Number of Vehicles in Q4",
                "sentiment": "positive",
                "relevance": 0.9,
                "timestamp": datetime.now() - timedelta(hours=8),
                "source": "CNBC",
                "impact": "bullish"
            },
            {
                "headline": "Fed Signals Potential Rate Cuts in 2024",
                "sentiment": "positive",
                "relevance": 0.7,
                "timestamp": datetime.now() - timedelta(hours=12),
                "source": "Wall Street Journal",
                "impact": "bullish"
            }
        ]
    
    def get_relevant_news(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relevant news items"""
        if symbol:
            # Filter news by symbol relevance
            relevant_news = [
                item for item in self.news_items 
                if symbol.upper() in item["headline"].upper()
            ]
            return relevant_news[:3]  # Return top 3
        
        return self.news_items[:5]  # Return top 5 general news
    
    def get_sentiment_score(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment score for a symbol"""
        # Mock sentiment scores
        sentiment_scores = {
            "AAPL": {"score": 0.75, "label": "positive"},
            "MSFT": {"score": 0.68, "label": "positive"},
            "GOOGL": {"score": 0.72, "label": "positive"},
            "TSLA": {"score": 0.65, "label": "positive"},
        }
        
        base_score = sentiment_scores.get(symbol, {"score": 0.5, "label": "neutral"})
        
        # Add some randomness
        score_variation = random.uniform(-0.1, 0.1)
        final_score = max(0, min(1, base_score["score"] + score_variation))
        
        if final_score > 0.6:
            label = "positive"
        elif final_score < 0.4:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "symbol": symbol,
            "score": round(final_score, 3),
            "label": label,
            "confidence": random.uniform(0.7, 0.95),
            "timestamp": datetime.now().isoformat()
        }

# Service instances
market_data_service = MockMarketDataService()
ai_service = MockAIService()
news_service = MockNewsService()

# Utility functions
def get_mock_portfolio_data() -> Dict[str, Any]:
    """Get complete mock portfolio data"""
    return {
        "total_value": 1247850.00,
        "daily_pnl": 12450.00,
        "daily_pnl_percent": 1.01,
        "weekly_return": 0.85,
        "active_positions": 4,
        "positions": [
            {
                "symbol": "AAPL",
                "type": "Put",
                "strike": 175,
                "expiry": "Dec 15",
                "pnl": 425,
                "pnl_percent": 28.8,
                "delta": -0.35,
                "current_price": market_data_service.get_current_price("AAPL")
            },
            {
                "symbol": "MSFT",
                "type": "Put",
                "strike": 380,
                "expiry": "Jan 19",
                "pnl": -125,
                "pnl_percent": -5.2,
                "delta": -0.28,
                "current_price": market_data_service.get_current_price("MSFT")
            },
            {
                "symbol": "GOOGL",
                "type": "Put",
                "strike": 140,
                "expiry": "Dec 22",
                "pnl": 850,
                "pnl_percent": 42.1,
                "delta": -0.31,
                "current_price": market_data_service.get_current_price("GOOGL")
            },
            {
                "symbol": "TSLA",
                "type": "Call",
                "strike": 250,
                "expiry": "Jan 12",
                "pnl": 320,
                "pnl_percent": 15.6,
                "delta": 0.45,
                "current_price": market_data_service.get_current_price("TSLA")
            }
        ],
        "system_status": {
            "rules_engine": "Active",
            "constitution": "Compliant",
            "market_data": "Connected",
            "ai_assistant": "Advisory Mode",
            "portfolio_delta": -0.28,
            "protocol_level": "Normal"
        },
        "market_status": market_data_service.get_market_status(),
        "last_update": datetime.now().isoformat()
    }

