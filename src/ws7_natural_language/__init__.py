"""
WS7: Natural Language Interface & Chatbot

This workstream implements the natural language interface and chatbot system
for the True-Asset-ALLUSE wealth management autopilot system.

Components:
- Chatbot: LLM-powered conversational interface
- Report Narrator: Natural language report generation
- Conversation Engine: Context-aware conversation management
- NLP Processor: Natural language processing and understanding

Mission: "Autopilot for Wealth.....Engineered for compounding income and corpus"
"""

from .chatbot.wealth_chatbot import WealthChatbot
from .report_narrator.narrative_generator import NarrativeReportGenerator
from .conversation_engine.conversation_manager import ConversationManager
from .nlp_processor.nlp_engine import NLPEngine

__all__ = [
    'WealthChatbot',
    'NarrativeReportGenerator', 
    'ConversationManager',
    'NLPEngine'
]

