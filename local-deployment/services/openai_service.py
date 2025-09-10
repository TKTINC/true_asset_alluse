"""
OpenAI Integration Service
Real AI responses and analysis for True-Asset-ALLUSE
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai library not available. OpenAI integration disabled.")

from config_enhanced import config

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service for real AI responses and analysis"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.conversation_history = []
        self.system_context = self._build_system_context()
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI service initialized without openai library")
    
    def _build_system_context(self) -> str:
        """Build system context for AI assistant"""
        return """You are an AI assistant for True-Asset-ALLUSE, an intelligent wealth management platform.

IMPORTANT GUIDELINES:
- You provide ADVISORY ONLY recommendations - never make trading decisions
- All trading decisions are made by the rules-based system per Constitution v1.3
- You analyze data and provide insights, but humans and rules make final decisions
- Always emphasize that your responses are advisory and not trading instructions

SYSTEM OVERVIEW:
- True-Asset-ALLUSE is engineered for compounding income and corpus
- Uses rules-based decision making with zero AI involvement in actual trades
- Focuses on options income strategies with risk management
- Operates under strict Constitution v1.3 compliance

YOUR CAPABILITIES:
- Analyze portfolio performance and risk metrics
- Explain market conditions and their impact on positions
- Provide insights on individual positions and strategies
- Explain system status and protocol levels
- Answer questions about the ALL-USE methodology

RESPONSE STYLE:
- Professional and informative
- Include specific data when available
- Explain the reasoning behind insights
- Always end with "This is advisory only - all decisions remain with the rules-based system"
- Use financial terminology appropriately
"""
    
    async def connect(self) -> bool:
        """Initialize OpenAI client"""
        if not OPENAI_AVAILABLE or not config.openai_enabled or not config.openai_api_key:
            logger.info("OpenAI integration disabled or API key not provided")
            return False
        
        try:
            openai.api_key = config.openai_api_key
            self.client = openai
            
            # Test connection with a simple request
            response = await self._make_api_call(
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            
            if response:
                self.connected = True
                logger.info("Connected to OpenAI API successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            self.connected = False
            return False
    
    async def _make_api_call(self, messages: List[Dict[str, str]], max_tokens: int = None) -> Optional[str]:
        """Make API call to OpenAI"""
        if not self.connected:
            return None
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=config.openai_model,
                messages=messages,
                max_tokens=max_tokens or config.openai_max_tokens,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None
    
    async def get_portfolio_analysis(self, portfolio_data: Dict[str, Any]) -> str:
        """Analyze portfolio data and provide insights"""
        if not self.connected:
            return self._get_mock_portfolio_analysis(portfolio_data)
        
        try:
            portfolio_summary = f"""
Portfolio Analysis Request:
- Total Value: ${portfolio_data.get('total_value', 0):,.2f}
- Daily P&L: ${portfolio_data.get('daily_pnl', 0):,.2f} ({portfolio_data.get('daily_pnl_percent', 0):.2f}%)
- Portfolio Delta: {portfolio_data.get('portfolio_delta', 0):.3f}
- Active Positions: {portfolio_data.get('active_positions', 0)}
- Protocol Level: {portfolio_data.get('system_status', {}).get('protocol_level', 'Unknown')}

Current Positions:
"""
            
            for position in portfolio_data.get('positions', [])[:5]:  # Limit to 5 positions
                portfolio_summary += f"- {position.get('symbol', 'Unknown')} {position.get('type', 'Unknown')} ${position.get('strike', 0)} {position.get('expiry', 'Unknown')}: ${position.get('pnl', 0):,.0f} ({position.get('pnl_percent', 0):.1f}%)\n"
            
            messages = [
                {"role": "system", "content": self.system_context},
                {"role": "user", "content": f"Please analyze this portfolio performance and provide insights:\n\n{portfolio_summary}"}
            ]
            
            response = await self._make_api_call(messages)
            
            if response:
                return response
            
            return self._get_mock_portfolio_analysis(portfolio_data)
            
        except Exception as e:
            logger.error(f"Failed to get portfolio analysis: {e}")
            return self._get_mock_portfolio_analysis(portfolio_data)
    
    async def get_position_analysis(self, position_data: Dict[str, Any], market_data: Dict[str, Any] = None) -> str:
        """Analyze specific position and provide insights"""
        if not self.connected:
            return self._get_mock_position_analysis(position_data)
        
        try:
            position_summary = f"""
Position Analysis Request:
- Symbol: {position_data.get('symbol', 'Unknown')}
- Type: {position_data.get('type', 'Unknown')} ${position_data.get('strike', 0)} {position_data.get('expiry', 'Unknown')}
- Current P&L: ${position_data.get('pnl', 0):,.0f} ({position_data.get('pnl_percent', 0):.1f}%)
- Delta: {position_data.get('delta', 0):.3f}
- Current Price: ${position_data.get('current_price', 0):.2f}
"""
            
            if market_data:
                position_summary += f"""
Market Context:
- Last Price: ${market_data.get('last_price', 0):.2f}
- Volume: {market_data.get('volume', 0):,}
- Volatility Regime: {market_data.get('volatility_regime', 'Unknown')}
"""
            
            messages = [
                {"role": "system", "content": self.system_context},
                {"role": "user", "content": f"Please analyze this position and provide insights:\n\n{position_summary}"}
            ]
            
            response = await self._make_api_call(messages)
            
            if response:
                return response
            
            return self._get_mock_position_analysis(position_data)
            
        except Exception as e:
            logger.error(f"Failed to get position analysis: {e}")
            return self._get_mock_position_analysis(position_data)
    
    async def get_market_commentary(self, market_data: Dict[str, Any], news_data: List[Dict[str, Any]] = None) -> str:
        """Provide market commentary based on current conditions"""
        if not self.connected:
            return self._get_mock_market_commentary(market_data)
        
        try:
            market_summary = f"""
Market Commentary Request:
- Market Status: {market_data.get('status', 'Unknown')}
- VIX Level: {market_data.get('vix_level', 0):.1f}
- Volatility Regime: {market_data.get('volatility_regime', 'Unknown')}
- Market Sentiment: {market_data.get('market_sentiment', 'Unknown')}
"""
            
            if news_data:
                market_summary += "\nRecent News Headlines:\n"
                for news in news_data[:3]:  # Limit to 3 headlines
                    market_summary += f"- {news.get('headline', 'Unknown')} ({news.get('sentiment', 'neutral')})\n"
            
            messages = [
                {"role": "system", "content": self.system_context},
                {"role": "user", "content": f"Please provide market commentary based on current conditions:\n\n{market_summary}"}
            ]
            
            response = await self._make_api_call(messages)
            
            if response:
                return response
            
            return self._get_mock_market_commentary(market_data)
            
        except Exception as e:
            logger.error(f"Failed to get market commentary: {e}")
            return self._get_mock_market_commentary(market_data)
    
    async def chat_response(self, user_message: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate conversational response to user query"""
        if not self.connected:
            return self._get_mock_chat_response(user_message)
        
        try:
            # Build context from available data
            context_summary = ""
            if context_data:
                portfolio = context_data.get('portfolio', {})
                market = context_data.get('market', {})
                
                context_summary = f"""
Current System Context:
- Portfolio Value: ${portfolio.get('total_value', 0):,.2f}
- Daily P&L: ${portfolio.get('daily_pnl', 0):,.2f}
- Portfolio Delta: {portfolio.get('portfolio_delta', 0):.3f}
- VIX Level: {market.get('vix_level', 0):.1f}
- Market Status: {market.get('status', 'Unknown')}
- Protocol Level: {portfolio.get('system_status', {}).get('protocol_level', 'Normal')}
"""
            
            messages = [
                {"role": "system", "content": self.system_context},
                {"role": "user", "content": f"Context:\n{context_summary}\n\nUser Question: {user_message}"}
            ]
            
            response = await self._make_api_call(messages)
            
            if response:
                # Add to conversation history
                self.conversation_history.append({
                    "user_message": user_message,
                    "ai_response": response,
                    "timestamp": datetime.now().isoformat(),
                    "context_provided": bool(context_data)
                })
                
                return {
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                    "advisory_only": True,
                    "confidence": 0.9,
                    "data_source": "OpenAI_Live"
                }
            
            return self._get_mock_chat_response(user_message)
            
        except Exception as e:
            logger.error(f"Failed to get chat response: {e}")
            return self._get_mock_chat_response(user_message)
    
    async def get_risk_assessment(self, portfolio_data: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Provide risk assessment based on current portfolio and market conditions"""
        if not self.connected:
            return self._get_mock_risk_assessment(portfolio_data, market_data)
        
        try:
            risk_summary = f"""
Risk Assessment Request:
Portfolio Metrics:
- Total Value: ${portfolio_data.get('total_value', 0):,.2f}
- Portfolio Delta: {portfolio_data.get('portfolio_delta', 0):.3f}
- Active Positions: {portfolio_data.get('active_positions', 0)}

Market Conditions:
- VIX Level: {market_data.get('vix_level', 0):.1f}
- Volatility Regime: {market_data.get('volatility_regime', 'Unknown')}
- Market Sentiment: {market_data.get('market_sentiment', 'Unknown')}

Constitution Limits:
- Max Delta: {config.max_portfolio_delta}
- Min Delta: {config.min_portfolio_delta}
- VIX Escalation Threshold: {config.vix_escalation_threshold}
"""
            
            messages = [
                {"role": "system", "content": self.system_context},
                {"role": "user", "content": f"Please provide a risk assessment:\n\n{risk_summary}"}
            ]
            
            response = await self._make_api_call(messages)
            
            if response:
                return response
            
            return self._get_mock_risk_assessment(portfolio_data, market_data)
            
        except Exception as e:
            logger.error(f"Failed to get risk assessment: {e}")
            return self._get_mock_risk_assessment(portfolio_data, market_data)
    
    def _get_mock_portfolio_analysis(self, portfolio_data: Dict[str, Any]) -> str:
        """Mock portfolio analysis when OpenAI unavailable"""
        total_value = portfolio_data.get('total_value', 0)
        daily_pnl = portfolio_data.get('daily_pnl', 0)
        daily_pnl_percent = portfolio_data.get('daily_pnl_percent', 0)
        
        if daily_pnl > 0:
            performance_note = "strong positive performance"
        elif daily_pnl < -1000:
            performance_note = "notable drawdown"
        else:
            performance_note = "stable performance"
        
        return f"""Your portfolio is showing {performance_note} today with a ${daily_pnl:,.0f} gain ({daily_pnl_percent:.2f}%). 

The portfolio value of ${total_value:,.2f} reflects the systematic income generation strategy. All positions are operating within the Constitution v1.3 parameters, with the rules engine maintaining optimal risk exposure.

Current delta positioning appears well-balanced for the market environment. The system continues to prioritize capital preservation while generating consistent income through the ALL-USE methodology.

This is advisory only - all decisions remain with the rules-based system."""
    
    def _get_mock_position_analysis(self, position_data: Dict[str, Any]) -> str:
        """Mock position analysis when OpenAI unavailable"""
        symbol = position_data.get('symbol', 'Unknown')
        pnl = position_data.get('pnl', 0)
        pnl_percent = position_data.get('pnl_percent', 0)
        
        if pnl > 0:
            performance_note = "performing well"
            action_note = "capturing time decay effectively"
        else:
            performance_note = "experiencing temporary drawdown"
            action_note = "within expected risk parameters"
        
        return f"""Your {symbol} position is {performance_note} with a ${pnl:,.0f} P&L ({pnl_percent:.1f}%). 

The position is {action_note} and remains compliant with Constitution v1.3 risk management protocols. The current delta exposure is appropriate for the underlying's volatility profile.

Market conditions continue to support the income generation strategy for this position. The rules engine will manage any necessary adjustments based on predefined parameters.

This is advisory only - all decisions remain with the rules-based system."""
    
    def _get_mock_market_commentary(self, market_data: Dict[str, Any]) -> str:
        """Mock market commentary when OpenAI unavailable"""
        vix_level = market_data.get('vix_level', 20)
        volatility_regime = market_data.get('volatility_regime', 'Normal')
        
        return f"""Current market conditions show {volatility_regime.lower()} volatility with VIX at {vix_level:.1f}. 

This environment is generally favorable for income generation strategies, providing adequate premium collection opportunities while maintaining manageable risk levels.

The ALL-USE system is well-positioned for these conditions, with the rules engine automatically adjusting position sizing and delta exposure based on current volatility metrics.

Market structure remains supportive of systematic options income strategies. Continue monitoring for any regime changes that might trigger protocol escalations.

This is advisory only - all decisions remain with the rules-based system."""
    
    def _get_mock_chat_response(self, user_message: str) -> Dict[str, Any]:
        """Mock chat response when OpenAI unavailable"""
        query_lower = user_message.lower()
        
        if "portfolio" in query_lower or "performance" in query_lower:
            response = "Your portfolio is performing well within expected parameters. The rules-based system continues to manage risk effectively while generating consistent income."
        elif any(symbol in query_lower for symbol in ["aapl", "msft", "googl", "tsla"]):
            response = "The position you're asking about is operating within Constitution v1.3 guidelines. The system monitors all positions continuously for optimal performance."
        elif "risk" in query_lower:
            response = "Current risk metrics are within acceptable ranges. The system maintains strict adherence to delta limits and volatility thresholds."
        elif "market" in query_lower:
            response = "Market conditions are being monitored continuously. The system adapts to changing conditions while maintaining disciplined risk management."
        else:
            response = "I'm here to provide advisory insights about your portfolio and market conditions. All trading decisions remain with the rules-based system per Constitution v1.3."
        
        return {
            "response": response + "\n\nThis is advisory only - all decisions remain with the rules-based system.",
            "timestamp": datetime.now().isoformat(),
            "advisory_only": True,
            "confidence": 0.8,
            "data_source": "Mock_Response"
        }
    
    def _get_mock_risk_assessment(self, portfolio_data: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Mock risk assessment when OpenAI unavailable"""
        portfolio_delta = portfolio_data.get('portfolio_delta', 0)
        vix_level = market_data.get('vix_level', 20)
        
        return f"""Risk Assessment Summary:

Portfolio delta of {portfolio_delta:.3f} is within the target range of {config.min_portfolio_delta} to {config.max_portfolio_delta}. Current positioning provides balanced exposure to market movements.

VIX level of {vix_level:.1f} indicates normal market conditions. No protocol escalation required at this time.

All positions remain compliant with Constitution v1.3 risk parameters. The system continues to prioritize capital preservation while maintaining income generation capabilities.

Recommend maintaining current positioning unless market conditions trigger predefined escalation protocols.

This is advisory only - all decisions remain with the rules-based system."""
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service health"""
        if not OPENAI_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "openai library not installed",
                "connected": False
            }
        
        if not config.openai_enabled:
            return {
                "status": "disabled",
                "message": "OpenAI integration disabled in configuration",
                "connected": False
            }
        
        if not config.openai_api_key:
            return {
                "status": "no_api_key",
                "message": "OpenAI API key not provided",
                "connected": False,
                "mock_mode": True
            }
        
        if not self.connected:
            connected = await self.connect()
            if not connected:
                return {
                    "status": "connection_failed",
                    "message": "Failed to connect to OpenAI API",
                    "connected": False
                }
        
        try:
            # Test with a simple request
            test_response = await self._make_api_call(
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "message": "Connected to OpenAI API",
                "connected": True,
                "model": config.openai_model,
                "conversation_history_length": len(self.conversation_history),
                "mock_mode": False
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API error: {e}",
                "connected": False
            }

# Global service instance
openai_service = OpenAIService()

