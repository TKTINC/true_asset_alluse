"""
Wealth Chatbot - Natural Language Interface

This module implements the LLM-powered chatbot that provides conversational
access to the True-Asset-ALLUSE wealth management system. Users can ask
questions about their portfolio, performance, risk, and system operations
in natural language.

Mission: "Autopilot for Wealth.....Engineered for compounding income and corpus"
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import json
import openai
import asyncio
from contextlib import asynccontextmanager

from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws3_account_management.accounts.account_manager import AccountManager
from src.ws5_portfolio_management.performance.performance_analyzer import PerformanceAnalyzer
from src.ws5_portfolio_management.risk.portfolio_risk_manager import PortfolioRiskManager

logger = logging.getLogger(__name__)


class ConversationType(Enum):
    """Types of conversations the chatbot can handle."""
    PORTFOLIO_INQUIRY = "portfolio_inquiry"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    ACCOUNT_MANAGEMENT = "account_management"
    SYSTEM_STATUS = "system_status"
    EDUCATIONAL = "educational"
    GENERAL_WEALTH = "general_wealth"


@dataclass
class ChatContext:
    """Chat conversation context."""
    user_id: str
    account_id: Optional[str]
    conversation_id: str
    conversation_type: ConversationType
    context_data: Dict[str, Any]
    created_at: datetime
    last_updated: datetime


@dataclass
class ChatResponse:
    """Chatbot response structure."""
    response_text: str
    response_type: ConversationType
    confidence: float
    data_sources: List[str]
    suggested_actions: List[str]
    follow_up_questions: List[str]
    timestamp: datetime


class WealthChatbot:
    """
    LLM-powered chatbot for natural language interaction with the
    True-Asset-ALLUSE wealth management system.
    
    Provides conversational access to:
    - Portfolio performance and analytics
    - Risk assessment and monitoring
    - Account management and status
    - System operations and health
    - Wealth management education
    """
    
    def __init__(self, 
                 account_manager: AccountManager,
                 performance_analyzer: PerformanceAnalyzer,
                 risk_manager: PortfolioRiskManager,
                 audit_manager: AuditTrailManager,
                 openai_api_key: Optional[str] = None):
        """Initialize the wealth chatbot."""
        self.account_manager = account_manager
        self.performance_analyzer = performance_analyzer
        self.risk_manager = risk_manager
        self.audit_manager = audit_manager
        
        # Initialize OpenAI client
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Conversation contexts
        self.active_contexts: Dict[str, ChatContext] = {}
        
        # System prompt for wealth management context
        self.system_prompt = self._build_system_prompt()
        
        logger.info("WealthChatbot initialized successfully")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """
You are a sophisticated AI assistant for the True-Asset-ALLUSE wealth management system.

MISSION: "Autopilot for Wealth.....Engineered for compounding income and corpus"

CORE PRINCIPLES:
- This is a wealth management autopilot system, NOT a trading system
- Focus on compounding income and corpus growth
- 100% rules-based operation with zero AI in wealth management decisions
- Constitution v1.3 compliant with L0-L3 protocol levels
- Three-tiered account structure: Gen-Acc, Rev-Acc, Com-Acc

YOUR ROLE:
- Explain portfolio performance and analytics in clear, natural language
- Help users understand their wealth management strategy
- Provide insights into risk management and protocol escalations
- Educate users about the system's Constitution-based approach
- Answer questions about account management and forking
- Explain week classifications and their impact on performance

COMMUNICATION STYLE:
- Professional yet approachable
- Focus on wealth building and compounding
- Use clear, jargon-free explanations
- Provide actionable insights
- Always emphasize the long-term wealth building mission

CAPABILITIES:
- Access real-time portfolio data and performance metrics
- Explain risk assessments and protocol levels
- Describe account status and forking opportunities
- Provide educational content about wealth management
- Generate natural language reports and summaries

Remember: You're helping users understand and optimize their wealth management autopilot system.
"""
    
    async def chat(self, 
                   user_id: str,
                   message: str,
                   account_id: Optional[str] = None,
                   conversation_id: Optional[str] = None) -> ChatResponse:
        """
        Process a chat message and generate a response.
        
        Args:
            user_id: User identifier
            message: User's message
            account_id: Optional account context
            conversation_id: Optional conversation context
            
        Returns:
            ChatResponse with the bot's response
        """
        try:
            # Get or create conversation context
            context = await self._get_or_create_context(
                user_id, account_id, conversation_id
            )
            
            # Classify the conversation type
            conversation_type = await self._classify_conversation(message)
            context.conversation_type = conversation_type
            
            # Gather relevant data based on conversation type
            context_data = await self._gather_context_data(
                context, message
            )
            context.context_data.update(context_data)
            
            # Generate LLM response
            response = await self._generate_llm_response(
                context, message
            )
            
            # Update context
            context.last_updated = datetime.utcnow()
            self.active_contexts[context.conversation_id] = context
            
            # Log the interaction
            await self._log_interaction(context, message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return ChatResponse(
                response_text="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                response_type=ConversationType.GENERAL_WEALTH,
                confidence=0.0,
                data_sources=[],
                suggested_actions=["Try rephrasing your question"],
                follow_up_questions=[],
                timestamp=datetime.utcnow()
            )
    
    async def _get_or_create_context(self,
                                   user_id: str,
                                   account_id: Optional[str],
                                   conversation_id: Optional[str]) -> ChatContext:
        """Get existing or create new conversation context."""
        if conversation_id and conversation_id in self.active_contexts:
            return self.active_contexts[conversation_id]
        
        # Create new context
        new_conversation_id = conversation_id or f"chat_{user_id}_{datetime.utcnow().timestamp()}"
        
        context = ChatContext(
            user_id=user_id,
            account_id=account_id,
            conversation_id=new_conversation_id,
            conversation_type=ConversationType.GENERAL_WEALTH,
            context_data={},
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        self.active_contexts[new_conversation_id] = context
        return context
    
    async def _classify_conversation(self, message: str) -> ConversationType:
        """Classify the type of conversation based on the message."""
        message_lower = message.lower()
        
        # Portfolio-related keywords
        if any(word in message_lower for word in ['portfolio', 'holdings', 'positions', 'assets']):
            return ConversationType.PORTFOLIO_INQUIRY
        
        # Performance-related keywords
        if any(word in message_lower for word in ['performance', 'returns', 'gains', 'profit', 'loss']):
            return ConversationType.PERFORMANCE_ANALYSIS
        
        # Risk-related keywords
        if any(word in message_lower for word in ['risk', 'volatility', 'drawdown', 'var', 'protocol']):
            return ConversationType.RISK_ASSESSMENT
        
        # Account-related keywords
        if any(word in message_lower for word in ['account', 'forking', 'gen-acc', 'rev-acc', 'com-acc']):
            return ConversationType.ACCOUNT_MANAGEMENT
        
        # System-related keywords
        if any(word in message_lower for word in ['system', 'status', 'health', 'constitution']):
            return ConversationType.SYSTEM_STATUS
        
        # Educational keywords
        if any(word in message_lower for word in ['how', 'what', 'why', 'explain', 'learn']):
            return ConversationType.EDUCATIONAL
        
        return ConversationType.GENERAL_WEALTH
    
    async def _gather_context_data(self,
                                 context: ChatContext,
                                 message: str) -> Dict[str, Any]:
        """Gather relevant data based on conversation type."""
        data = {}
        
        try:
            if context.account_id:
                # Get account information
                account_info = await self._get_account_summary(context.account_id)
                data['account'] = account_info
                
                # Get performance data for performance-related conversations
                if context.conversation_type == ConversationType.PERFORMANCE_ANALYSIS:
                    performance_data = await self._get_performance_summary(context.account_id)
                    data['performance'] = performance_data
                
                # Get risk data for risk-related conversations
                if context.conversation_type == ConversationType.RISK_ASSESSMENT:
                    risk_data = await self._get_risk_summary(context.account_id)
                    data['risk'] = risk_data
        
        except Exception as e:
            logger.error(f"Error gathering context data: {str(e)}")
        
        return data
    
    async def _get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get account summary information."""
        # This would integrate with the account manager
        return {
            'account_id': account_id,
            'account_type': 'Gen-Acc',  # Would be retrieved from account manager
            'balance': Decimal('50000.00'),  # Would be retrieved from account manager
            'status': 'ACTIVE'
        }
    
    async def _get_performance_summary(self, account_id: str) -> Dict[str, Any]:
        """Get performance summary information."""
        # This would integrate with the performance analyzer
        return {
            'total_return': Decimal('0.15'),  # 15%
            'weekly_return': Decimal('0.02'),  # 2%
            'sharpe_ratio': Decimal('1.8'),
            'max_drawdown': Decimal('-0.05')  # -5%
        }
    
    async def _get_risk_summary(self, account_id: str) -> Dict[str, Any]:
        """Get risk summary information."""
        # This would integrate with the risk manager
        return {
            'current_protocol_level': 'L0',
            'var_95': Decimal('-0.03'),  # -3%
            'portfolio_volatility': Decimal('0.12'),  # 12%
            'risk_score': 'MODERATE'
        }
    
    async def _generate_llm_response(self,
                                   context: ChatContext,
                                   message: str) -> ChatResponse:
        """Generate response using LLM."""
        try:
            # Build the conversation prompt
            conversation_prompt = self._build_conversation_prompt(context, message)
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": conversation_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # Generate suggested actions and follow-up questions
            suggested_actions = self._generate_suggested_actions(context.conversation_type)
            follow_up_questions = self._generate_follow_up_questions(context.conversation_type)
            
            return ChatResponse(
                response_text=response_text,
                response_type=context.conversation_type,
                confidence=0.9,  # Would be calculated based on context quality
                data_sources=list(context.context_data.keys()),
                suggested_actions=suggested_actions,
                follow_up_questions=follow_up_questions,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return ChatResponse(
                response_text="I'm having trouble processing your request. Could you please rephrase your question?",
                response_type=context.conversation_type,
                confidence=0.0,
                data_sources=[],
                suggested_actions=["Try rephrasing your question"],
                follow_up_questions=[],
                timestamp=datetime.utcnow()
            )
    
    def _build_conversation_prompt(self, context: ChatContext, message: str) -> str:
        """Build the conversation prompt with context."""
        prompt_parts = [
            f"User message: {message}",
            f"Conversation type: {context.conversation_type.value}",
        ]
        
        if context.context_data:
            prompt_parts.append("Relevant data:")
            for key, value in context.context_data.items():
                prompt_parts.append(f"- {key}: {json.dumps(value, default=str)}")
        
        return "\n".join(prompt_parts)
    
    def _generate_suggested_actions(self, conversation_type: ConversationType) -> List[str]:
        """Generate suggested actions based on conversation type."""
        actions_map = {
            ConversationType.PORTFOLIO_INQUIRY: [
                "View detailed portfolio breakdown",
                "Check recent position changes",
                "Review asset allocation"
            ],
            ConversationType.PERFORMANCE_ANALYSIS: [
                "Generate performance report",
                "Compare to benchmarks",
                "View historical performance"
            ],
            ConversationType.RISK_ASSESSMENT: [
                "Review risk metrics",
                "Check protocol level status",
                "View risk decomposition"
            ],
            ConversationType.ACCOUNT_MANAGEMENT: [
                "Check forking opportunities",
                "Review account status",
                "View account hierarchy"
            ],
            ConversationType.SYSTEM_STATUS: [
                "Check system health",
                "Review recent alerts",
                "View system performance"
            ]
        }
        
        return actions_map.get(conversation_type, ["Ask another question"])
    
    def _generate_follow_up_questions(self, conversation_type: ConversationType) -> List[str]:
        """Generate follow-up questions based on conversation type."""
        questions_map = {
            ConversationType.PORTFOLIO_INQUIRY: [
                "Would you like to see your largest positions?",
                "Are you interested in recent portfolio changes?",
                "Would you like to understand your asset allocation?"
            ],
            ConversationType.PERFORMANCE_ANALYSIS: [
                "Would you like to see performance by time period?",
                "Are you interested in risk-adjusted returns?",
                "Would you like to compare to benchmarks?"
            ],
            ConversationType.RISK_ASSESSMENT: [
                "Would you like to understand your current protocol level?",
                "Are you interested in stress test results?",
                "Would you like to see risk decomposition?"
            ]
        }
        
        return questions_map.get(conversation_type, ["What else would you like to know?"])
    
    async def _log_interaction(self,
                             context: ChatContext,
                             message: str,
                             response: ChatResponse):
        """Log the chat interaction for audit purposes."""
        try:
            await self.audit_manager.log_event(
                event_type="CHAT_INTERACTION",
                account_id=context.account_id,
                details={
                    'user_id': context.user_id,
                    'conversation_id': context.conversation_id,
                    'conversation_type': context.conversation_type.value,
                    'user_message': message,
                    'response_confidence': float(response.confidence),
                    'data_sources': response.data_sources
                },
                metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'response_type': response.response_type.value
                }
            )
        except Exception as e:
            logger.error(f"Error logging chat interaction: {str(e)}")
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[ChatContext]:
        """Get conversation history."""
        return self.active_contexts.get(conversation_id)
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation context."""
        if conversation_id in self.active_contexts:
            del self.active_contexts[conversation_id]
            return True
        return False
    
    async def get_active_conversations(self, user_id: str) -> List[ChatContext]:
        """Get all active conversations for a user."""
        return [
            context for context in self.active_contexts.values()
            if context.user_id == user_id
        ]

