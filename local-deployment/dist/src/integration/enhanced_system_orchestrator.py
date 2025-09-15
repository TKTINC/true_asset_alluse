"""
Enhanced System Orchestrator

This module integrates WS9 (Market Intelligence), WS12 (Visualization Intelligence),
and WS16 (Enhanced Conversational AI) with the existing system to create a unified,
intelligent wealth management platform.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import logging
import asyncio
import json

# Import existing workstreams
from ..ws1_rules_engine.rules_engine import RulesEngine
from ..ws2_protocol_engine.escalation.escalation_manager import EscalationManager
from ..ws3_account_management.accounts.account_manager import AccountManager
from ..ws4_market_data_execution.market_data.market_data_manager import MarketDataManager
from ..ws5_portfolio_management.optimization.portfolio_optimizer import PortfolioOptimizer
from ..ws6_user_interface.api_gateway.api_gateway import APIGateway
from ..ws7_natural_language.chatbot.wealth_chatbot import WealthChatbot
from ..ws8_ml_intelligence.intelligence_coordinator import IntelligenceCoordinator

# Import new workstreams
from ..ws9_market_intelligence.context_provider import MarketIntelligenceContextProvider
from ..ws12_visualization_intelligence.report_generator.intelligent_report_engine import IntelligentReportEngine
from ..ws12_visualization_intelligence.dashboard_intelligence.personalized_dashboard import PersonalizedDashboardEngine
from ..ws16_enhanced_conversational_ai.advanced_nlp.enhanced_query_processor import EnhancedQueryProcessor

logger = logging.getLogger(__name__)


class EnhancedSystemOrchestrator:
    """
    Enhanced System Orchestrator for True-Asset-ALLUSE.
    
    Integrates all workstreams including the new WS9, WS12, and WS16 to create
    a unified, intelligent, and beautiful wealth management platform.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize enhanced system orchestrator."""
        self.config = config or {}
        self.is_initialized = False
        
        # Core workstreams (WS1-WS8)
        self.rules_engine = None
        self.protocol_engine = None
        self.account_manager = None
        self.market_data_manager = None
        self.portfolio_optimizer = None
        self.api_gateway = None
        self.wealth_chatbot = None
        self.intelligence_coordinator = None
        
        # New workstreams (WS9, WS12, WS16)
        self.market_intelligence = None
        self.report_engine = None
        self.dashboard_engine = None
        self.enhanced_query_processor = None
        
        # Integration components
        self.event_bus = {}
        self.data_cache = {}
        self.active_sessions = {}
        
        logger.info("Enhanced System Orchestrator initialized")
    
    async def initialize(self) -> bool:
        """Initialize all workstreams and integration components."""
        try:
            logger.info("Initializing Enhanced System Orchestrator...")
            
            # Initialize core workstreams
            await self._initialize_core_workstreams()
            
            # Initialize new workstreams
            await self._initialize_new_workstreams()
            
            # Setup integration and event handling
            await self._setup_integration()
            
            self.is_initialized = True
            logger.info("Enhanced System Orchestrator initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced System Orchestrator: {e}")
            return False
    
    async def _initialize_core_workstreams(self):
        """Initialize core workstreams (WS1-WS8)."""
        logger.info("Initializing core workstreams...")
        
        # WS1: Rules Engine
        self.rules_engine = RulesEngine(self.config.get("rules_engine", {}))
        await self.rules_engine.initialize()
        
        # WS2: Protocol Engine
        self.protocol_engine = EscalationManager(self.config.get("protocol_engine", {}))
        await self.protocol_engine.initialize()
        
        # WS3: Account Management
        self.account_manager = AccountManager(self.config.get("account_manager", {}))
        await self.account_manager.initialize()
        
        # WS4: Market Data & Execution
        self.market_data_manager = MarketDataManager(self.config.get("market_data", {}))
        await self.market_data_manager.initialize()
        
        # WS5: Portfolio Management
        self.portfolio_optimizer = PortfolioOptimizer(self.config.get("portfolio", {}))
        await self.portfolio_optimizer.initialize()
        
        # WS6: User Interface
        self.api_gateway = APIGateway(self.config.get("api_gateway", {}))
        await self.api_gateway.initialize()
        
        # WS7: Natural Language Interface
        self.wealth_chatbot = WealthChatbot(self.config.get("chatbot", {}))
        await self.wealth_chatbot.initialize()
        
        # WS8: ML Intelligence
        self.intelligence_coordinator = IntelligenceCoordinator(self.config.get("ml_intelligence", {}))
        await self.intelligence_coordinator.initialize()
        
        logger.info("Core workstreams initialized successfully")
    
    async def _initialize_new_workstreams(self):
        """Initialize new workstreams (WS9, WS12, WS16)."""
        logger.info("Initializing new workstreams...")
        
        # WS9: Market Intelligence & Sentiment
        self.market_intelligence = MarketIntelligenceContextProvider()
        await self.market_intelligence.initialize()
        
        # WS12: Visualization & Reporting Intelligence
        self.report_engine = IntelligentReportEngine(self.config.get("report_engine", {}))
        self.dashboard_engine = PersonalizedDashboardEngine(self.config.get("dashboard_engine", {}))
        
        # WS16: Enhanced Conversational AI
        self.enhanced_query_processor = EnhancedQueryProcessor(self.config.get("enhanced_nlp", {}))
        
        logger.info("New workstreams initialized successfully")
    
    async def _setup_integration(self):
        """Setup integration between workstreams."""
        logger.info("Setting up workstream integration...")
        
        # Setup event handlers for cross-workstream communication
        await self._setup_event_handlers()
        
        # Setup data flow pipelines
        await self._setup_data_pipelines()
        
        # Setup real-time synchronization
        await self._setup_real_time_sync()
        
        logger.info("Workstream integration setup complete")
    
    async def _setup_event_handlers(self):
        """Setup event handlers for workstream communication."""
        
        # Protocol escalation events -> Market Intelligence context
        self.event_bus["protocol_escalation"] = self._handle_protocol_escalation_event
        
        # Market intelligence updates -> Dashboard updates
        self.event_bus["market_intelligence_update"] = self._handle_market_intelligence_update
        
        # User interactions -> Personalization learning
        self.event_bus["user_interaction"] = self._handle_user_interaction_event
        
        # Performance updates -> Report generation
        self.event_bus["performance_update"] = self._handle_performance_update_event
        
        # Anomaly detection -> Dashboard highlights
        self.event_bus["anomaly_detected"] = self._handle_anomaly_detection_event
    
    async def _setup_data_pipelines(self):
        """Setup data flow pipelines between workstreams."""
        
        # Market data -> Market intelligence -> Dashboard
        self.data_pipelines = {
            "market_data_flow": {
                "source": "market_data_manager",
                "processors": ["market_intelligence"],
                "destinations": ["dashboard_engine", "report_engine"]
            },
            "performance_flow": {
                "source": "portfolio_optimizer",
                "processors": ["intelligence_coordinator"],
                "destinations": ["report_engine", "dashboard_engine"]
            },
            "risk_flow": {
                "source": "rules_engine",
                "processors": ["market_intelligence"],
                "destinations": ["dashboard_engine", "enhanced_query_processor"]
            }
        }
    
    async def _setup_real_time_sync(self):
        """Setup real-time synchronization between components."""
        
        # Start background tasks for real-time updates
        asyncio.create_task(self._market_intelligence_sync_loop())
        asyncio.create_task(self._dashboard_update_loop())
        asyncio.create_task(self._report_generation_loop())
    
    # Event handlers
    
    async def _handle_protocol_escalation_event(self, event_data: Dict[str, Any]):
        """Handle protocol escalation events with market intelligence context."""
        try:
            level = event_data.get("level")
            reason = event_data.get("reason")
            affected_symbols = event_data.get("affected_symbols", [])
            
            # Get market intelligence context
            context = await self.market_intelligence.get_protocol_escalation_context(
                level, reason, affected_symbols
            )
            
            # Update dashboard with escalation context
            if self.dashboard_engine:
                await self.dashboard_engine.add_anomaly_highlights(
                    event_data.get("dashboard_id", "default"),
                    [{
                        "type": "protocol_escalation",
                        "severity": "high" if level >= 2 else "medium",
                        "message": context.get("human_explanation", reason),
                        "data": context
                    }]
                )
            
            # Generate escalation report
            if self.report_engine:
                # This would trigger an automated escalation report
                pass
            
            logger.info(f"Handled protocol escalation event: Level {level}")
            
        except Exception as e:
            logger.error(f"Error handling protocol escalation event: {e}")
    
    async def _handle_market_intelligence_update(self, event_data: Dict[str, Any]):
        """Handle market intelligence updates."""
        try:
            # Update dashboard with new market intelligence
            market_summary = await self.market_intelligence.get_market_summary_for_dashboard()
            
            # Broadcast to active dashboard sessions
            for session_id, session_data in self.active_sessions.items():
                if session_data.get("dashboard_active"):
                    # Update dashboard with new market data
                    pass
            
            logger.info("Handled market intelligence update")
            
        except Exception as e:
            logger.error(f"Error handling market intelligence update: {e}")
    
    async def _handle_user_interaction_event(self, event_data: Dict[str, Any]):
        """Handle user interaction events for personalization."""
        try:
            user_id = event_data.get("user_id")
            widget_id = event_data.get("widget_id")
            interaction_type = event_data.get("interaction_type")
            duration = event_data.get("duration")
            
            # Track interaction for dashboard personalization
            if self.dashboard_engine:
                await self.dashboard_engine.track_user_interaction(
                    user_id, widget_id, interaction_type, duration
                )
            
            logger.debug(f"Tracked user interaction: {user_id} -> {widget_id}")
            
        except Exception as e:
            logger.error(f"Error handling user interaction event: {e}")
    
    async def _handle_performance_update_event(self, event_data: Dict[str, Any]):
        """Handle performance update events."""
        try:
            # Trigger report generation if significant performance change
            performance_change = event_data.get("performance_change", 0)
            
            if abs(performance_change) > 0.02:  # 2% threshold
                # Generate performance alert report
                if self.report_engine:
                    report = await self.report_engine.generate_daily_summary()
                    # Send to relevant users
            
            logger.info(f"Handled performance update: {performance_change:.2%}")
            
        except Exception as e:
            logger.error(f"Error handling performance update event: {e}")
    
    async def _handle_anomaly_detection_event(self, event_data: Dict[str, Any]):
        """Handle anomaly detection events."""
        try:
            anomaly_type = event_data.get("type")
            severity = event_data.get("severity")
            
            # Add anomaly highlights to all active dashboards
            for session_id, session_data in self.active_sessions.items():
                dashboard_id = session_data.get("dashboard_id")
                if dashboard_id and self.dashboard_engine:
                    await self.dashboard_engine.add_anomaly_highlights(
                        dashboard_id, [event_data]
                    )
            
            logger.info(f"Handled anomaly detection: {anomaly_type} ({severity})")
            
        except Exception as e:
            logger.error(f"Error handling anomaly detection event: {e}")
    
    # Background sync loops
    
    async def _market_intelligence_sync_loop(self):
        """Background loop for market intelligence synchronization."""
        while self.is_initialized:
            try:
                # Update market intelligence every 5 minutes
                await asyncio.sleep(300)
                
                if self.market_intelligence:
                    # Force refresh market context
                    await self.market_intelligence.get_market_summary_for_dashboard(force_refresh=True)
                    
                    # Emit update event
                    await self._emit_event("market_intelligence_update", {
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"Error in market intelligence sync loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _dashboard_update_loop(self):
        """Background loop for dashboard updates."""
        while self.is_initialized:
            try:
                # Update dashboards every 30 seconds
                await asyncio.sleep(30)
                
                # Update active dashboards with fresh data
                for session_id, session_data in self.active_sessions.items():
                    if session_data.get("dashboard_active"):
                        # Refresh dashboard data
                        pass
                
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(30)
    
    async def _report_generation_loop(self):
        """Background loop for automated report generation."""
        while self.is_initialized:
            try:
                # Generate daily reports at market close
                current_time = datetime.utcnow()
                if current_time.hour == 21 and current_time.minute == 0:  # 9 PM UTC (4 PM EST)
                    if self.report_engine:
                        daily_report = await self.report_engine.generate_daily_summary()
                        # Store and distribute report
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in report generation loop: {e}")
                await asyncio.sleep(300)
    
    # Public API methods
    
    async def process_enhanced_query(self, query: str, user_id: str, session_id: str, 
                                   language: str = "en") -> Dict[str, Any]:
        """
        Process enhanced conversational query.
        
        Args:
            query: Natural language query
            user_id: User identifier
            session_id: Session identifier
            language: Query language
            
        Returns:
            Dict containing response and data
        """
        try:
            if not self.enhanced_query_processor:
                raise ValueError("Enhanced query processor not initialized")
            
            # Create query context
            from ..ws16_enhanced_conversational_ai.advanced_nlp.enhanced_query_processor import QueryContext, Language
            
            context = QueryContext(
                user_id=user_id,
                session_id=session_id,
                conversation_history=self._get_conversation_history(session_id),
                user_preferences=self._get_user_preferences(user_id),
                current_portfolio=await self._get_current_portfolio(user_id),
                market_context=await self._get_market_context(),
                timestamp=datetime.utcnow(),
                language=Language(language)
            )
            
            # Process query
            response = await self.enhanced_query_processor.process_complex_query(query, context)
            
            # Convert to API response format
            return {
                "response_text": response.response_text,
                "data": response.data,
                "visualizations": response.visualizations,
                "follow_up_suggestions": response.follow_up_suggestions,
                "confidence": response.confidence,
                "processing_time": response.processing_time,
                "requires_clarification": response.requires_clarification,
                "clarification_questions": response.clarification_questions or []
            }
            
        except Exception as e:
            logger.error(f"Error processing enhanced query: {e}")
            return {
                "response_text": f"I apologize, but I encountered an error: {str(e)}",
                "data": {},
                "visualizations": [],
                "follow_up_suggestions": [],
                "confidence": 0.0,
                "processing_time": 0.0,
                "requires_clarification": True,
                "clarification_questions": ["Could you please rephrase your question?"]
            }
    
    async def generate_intelligent_report(self, report_type: str, user_id: str, 
                                        parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate intelligent report.
        
        Args:
            report_type: Type of report to generate
            user_id: User identifier
            parameters: Report parameters
            
        Returns:
            Dict containing report data
        """
        try:
            if not self.report_engine:
                raise ValueError("Report engine not initialized")
            
            # Generate report based on type
            if report_type == "daily_summary":
                report = await self.report_engine.generate_daily_summary()
            elif report_type == "weekly_performance":
                report = await self.report_engine.generate_weekly_performance()
            elif report_type == "position_analysis":
                symbol = parameters.get("symbol") if parameters else None
                report = await self.report_engine.generate_position_analysis(symbol)
            elif report_type == "market_intelligence":
                report = await self.report_engine.generate_market_intelligence_report()
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Convert to API response format
            return self.report_engine.get_report_as_dict(report)
            
        except Exception as e:
            logger.error(f"Error generating intelligent report: {e}")
            return {
                "error": f"Failed to generate report: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_personalized_dashboard(self, user_id: str, user_role: str = None, 
                                       preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get personalized dashboard for user.
        
        Args:
            user_id: User identifier
            user_role: User role for initial layout
            preferences: User preferences
            
        Returns:
            Dict containing dashboard configuration
        """
        try:
            if not self.dashboard_engine:
                raise ValueError("Dashboard engine not initialized")
            
            # Convert user role string to enum
            from ..ws12_visualization_intelligence.dashboard_intelligence.personalized_dashboard import UserRole
            
            role_enum = None
            if user_role:
                try:
                    role_enum = UserRole(user_role.lower())
                except ValueError:
                    role_enum = UserRole.TRADER  # Default
            
            # Create personalized dashboard
            dashboard = await self.dashboard_engine.create_personalized_dashboard(
                user_id, role_enum, preferences
            )
            
            # Convert to API response format
            return self.dashboard_engine.get_dashboard_layout_dict(dashboard)
            
        except Exception as e:
            logger.error(f"Error getting personalized dashboard: {e}")
            return {
                "error": f"Failed to create dashboard: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_market_intelligence_summary(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Get market intelligence summary.
        
        Args:
            symbols: Optional symbols to focus on
            
        Returns:
            Dict containing market intelligence
        """
        try:
            if not self.market_intelligence:
                raise ValueError("Market intelligence not initialized")
            
            # Get comprehensive intelligence
            intelligence = await self.market_intelligence.get_contextual_intelligence(
                symbols=symbols, include_market=True
            )
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error getting market intelligence: {e}")
            return {
                "error": f"Failed to get market intelligence: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Helper methods
    
    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit event to event bus."""
        if event_type in self.event_bus:
            handler = self.event_bus[event_type]
            await handler(event_data)
    
    def _get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session."""
        session_data = self.active_sessions.get(session_id, {})
        return session_data.get("conversation_history", [])
    
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        # This would fetch from user preferences service
        return {
            "theme": "professional",
            "language": "en",
            "timezone": "UTC",
            "preferred_charts": ["line_chart", "bar_chart"]
        }
    
    async def _get_current_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get current portfolio for user."""
        # This would fetch from portfolio service
        return {
            "total_value": 100000.00,
            "positions": 8,
            "net_delta": 0.23,
            "daily_pnl": 1250.00
        }
    
    async def _get_market_context(self) -> Dict[str, Any]:
        """Get current market context."""
        if self.market_intelligence:
            return await self.market_intelligence.get_market_summary_for_dashboard()
        return {}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "system_initialized": self.is_initialized,
            "workstreams": {
                "ws1_rules_engine": self.rules_engine is not None,
                "ws2_protocol_engine": self.protocol_engine is not None,
                "ws3_account_management": self.account_manager is not None,
                "ws4_market_data": self.market_data_manager is not None,
                "ws5_portfolio_management": self.portfolio_optimizer is not None,
                "ws6_user_interface": self.api_gateway is not None,
                "ws7_natural_language": self.wealth_chatbot is not None,
                "ws8_ml_intelligence": self.intelligence_coordinator is not None,
                "ws9_market_intelligence": self.market_intelligence is not None,
                "ws12_visualization_intelligence": {
                    "report_engine": self.report_engine is not None,
                    "dashboard_engine": self.dashboard_engine is not None
                },
                "ws16_enhanced_conversational_ai": self.enhanced_query_processor is not None
            },
            "active_sessions": len(self.active_sessions),
            "timestamp": datetime.utcnow().isoformat()
        }

