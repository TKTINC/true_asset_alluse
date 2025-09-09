"""
Personalized Dashboard Intelligence Engine

This module creates personalized, adaptive dashboards that learn from user behavior
and present the most relevant information based on context, preferences, and usage patterns.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class WidgetType(Enum):
    """Types of dashboard widgets."""
    PERFORMANCE_SUMMARY = "performance_summary"
    POSITION_OVERVIEW = "position_overview"
    RISK_METRICS = "risk_metrics"
    MARKET_INTELLIGENCE = "market_intelligence"
    PROTOCOL_STATUS = "protocol_status"
    NEWS_SENTIMENT = "news_sentiment"
    TRADE_HISTORY = "trade_history"
    ANALYTICS_CHART = "analytics_chart"
    ALERTS_PANEL = "alerts_panel"
    QUICK_ACTIONS = "quick_actions"
    EARNINGS_CALENDAR = "earnings_calendar"
    VOLATILITY_MONITOR = "volatility_monitor"


class WidgetSize(Enum):
    """Widget size options."""
    SMALL = "small"      # 1x1
    MEDIUM = "medium"    # 2x1
    LARGE = "large"      # 2x2
    WIDE = "wide"        # 3x1
    EXTRA_LARGE = "xl"   # 3x2


class UserRole(Enum):
    """User roles for dashboard customization."""
    TRADER = "trader"
    PORTFOLIO_MANAGER = "portfolio_manager"
    RISK_MANAGER = "risk_manager"
    ANALYST = "analyst"
    EXECUTIVE = "executive"
    INVESTOR = "investor"


@dataclass
class WidgetConfig:
    """Configuration for a dashboard widget."""
    widget_id: str
    widget_type: WidgetType
    title: str
    size: WidgetSize
    position: Dict[str, int]  # {"x": 0, "y": 0}
    data_source: str
    refresh_interval: int  # seconds
    visible: bool = True
    customizable: bool = True
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    user_preferences: Dict[str, Any] = None


@dataclass
class DashboardLayout:
    """Complete dashboard layout configuration."""
    layout_id: str
    user_id: str
    layout_name: str
    widgets: List[WidgetConfig]
    grid_columns: int
    grid_rows: int
    theme: str
    auto_refresh: bool
    created_at: datetime
    last_modified: datetime
    usage_stats: Dict[str, Any] = None


@dataclass
class UserBehavior:
    """User behavior tracking for personalization."""
    user_id: str
    widget_interactions: Dict[str, int]  # widget_id -> interaction_count
    time_spent: Dict[str, float]  # widget_id -> seconds
    preferred_timeframes: List[str]
    frequently_viewed_symbols: List[str]
    peak_usage_hours: List[int]
    device_preferences: Dict[str, Any]
    last_updated: datetime


class PersonalizedDashboardEngine:
    """
    Personalized Dashboard Intelligence Engine.
    
    Creates adaptive dashboards that learn from user behavior and automatically
    optimize layout, content, and presentation based on individual preferences.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize personalized dashboard engine."""
        self.config = config or {}
        self.user_behaviors: Dict[str, UserBehavior] = {}
        self.dashboard_layouts: Dict[str, DashboardLayout] = {}
        self.widget_templates = self._initialize_widget_templates()
        self.role_based_layouts = self._initialize_role_based_layouts()
        
        logger.info("Personalized Dashboard Engine initialized")
    
    def _initialize_widget_templates(self) -> Dict[WidgetType, Dict[str, Any]]:
        """Initialize widget templates with default configurations."""
        return {
            WidgetType.PERFORMANCE_SUMMARY: {
                "title": "Performance Summary",
                "default_size": WidgetSize.LARGE,
                "data_source": "performance_service",
                "refresh_interval": 60,
                "chart_type": "line_chart",
                "metrics": ["daily_pnl", "cumulative_return", "sharpe_ratio"]
            },
            WidgetType.POSITION_OVERVIEW: {
                "title": "Position Overview",
                "default_size": WidgetSize.MEDIUM,
                "data_source": "position_service",
                "refresh_interval": 30,
                "chart_type": "pie_chart",
                "metrics": ["total_positions", "net_delta", "largest_position"]
            },
            WidgetType.RISK_METRICS: {
                "title": "Risk Dashboard",
                "default_size": WidgetSize.MEDIUM,
                "data_source": "risk_service",
                "refresh_interval": 60,
                "chart_type": "gauge",
                "metrics": ["var_95", "portfolio_volatility", "beta"]
            },
            WidgetType.MARKET_INTELLIGENCE: {
                "title": "Market Intelligence",
                "default_size": WidgetSize.WIDE,
                "data_source": "ws9_market_intelligence",
                "refresh_interval": 300,
                "chart_type": "sentiment_chart",
                "metrics": ["market_sentiment", "vix_level", "key_themes"]
            },
            WidgetType.PROTOCOL_STATUS: {
                "title": "Protocol Status",
                "default_size": WidgetSize.SMALL,
                "data_source": "ws2_protocol_engine",
                "refresh_interval": 15,
                "chart_type": "status_indicator",
                "metrics": ["current_level", "escalation_history", "active_alerts"]
            },
            WidgetType.NEWS_SENTIMENT: {
                "title": "News & Sentiment",
                "default_size": WidgetSize.MEDIUM,
                "data_source": "ws9_news_sentiment",
                "refresh_interval": 180,
                "chart_type": "news_feed",
                "metrics": ["sentiment_score", "news_count", "key_events"]
            },
            WidgetType.TRADE_HISTORY: {
                "title": "Recent Trades",
                "default_size": WidgetSize.MEDIUM,
                "data_source": "trade_service",
                "refresh_interval": 60,
                "chart_type": "table",
                "metrics": ["recent_trades", "trade_count", "win_rate"]
            },
            WidgetType.ANALYTICS_CHART: {
                "title": "Analytics",
                "default_size": WidgetSize.LARGE,
                "data_source": "analytics_service",
                "refresh_interval": 120,
                "chart_type": "customizable",
                "metrics": ["user_defined"]
            },
            WidgetType.ALERTS_PANEL: {
                "title": "Active Alerts",
                "default_size": WidgetSize.SMALL,
                "data_source": "alert_service",
                "refresh_interval": 10,
                "chart_type": "alert_list",
                "metrics": ["active_alerts", "alert_priority", "alert_count"]
            },
            WidgetType.QUICK_ACTIONS: {
                "title": "Quick Actions",
                "default_size": WidgetSize.SMALL,
                "data_source": "action_service",
                "refresh_interval": 0,  # Static
                "chart_type": "button_panel",
                "metrics": ["available_actions"]
            },
            WidgetType.EARNINGS_CALENDAR: {
                "title": "Earnings Calendar",
                "default_size": WidgetSize.MEDIUM,
                "data_source": "earnings_service",
                "refresh_interval": 3600,
                "chart_type": "calendar",
                "metrics": ["upcoming_earnings", "earnings_impact"]
            },
            WidgetType.VOLATILITY_MONITOR: {
                "title": "Volatility Monitor",
                "default_size": WidgetSize.MEDIUM,
                "data_source": "volatility_service",
                "refresh_interval": 60,
                "chart_type": "volatility_surface",
                "metrics": ["vix_level", "term_structure", "skew"]
            }
        }
    
    def _initialize_role_based_layouts(self) -> Dict[UserRole, List[WidgetType]]:
        """Initialize default layouts for different user roles."""
        return {
            UserRole.TRADER: [
                WidgetType.POSITION_OVERVIEW,
                WidgetType.PERFORMANCE_SUMMARY,
                WidgetType.PROTOCOL_STATUS,
                WidgetType.ALERTS_PANEL,
                WidgetType.QUICK_ACTIONS,
                WidgetType.MARKET_INTELLIGENCE,
                WidgetType.TRADE_HISTORY,
                WidgetType.VOLATILITY_MONITOR
            ],
            UserRole.PORTFOLIO_MANAGER: [
                WidgetType.PERFORMANCE_SUMMARY,
                WidgetType.POSITION_OVERVIEW,
                WidgetType.RISK_METRICS,
                WidgetType.ANALYTICS_CHART,
                WidgetType.MARKET_INTELLIGENCE,
                WidgetType.EARNINGS_CALENDAR,
                WidgetType.NEWS_SENTIMENT
            ],
            UserRole.RISK_MANAGER: [
                WidgetType.RISK_METRICS,
                WidgetType.PROTOCOL_STATUS,
                WidgetType.ALERTS_PANEL,
                WidgetType.POSITION_OVERVIEW,
                WidgetType.VOLATILITY_MONITOR,
                WidgetType.ANALYTICS_CHART,
                WidgetType.MARKET_INTELLIGENCE
            ],
            UserRole.ANALYST: [
                WidgetType.ANALYTICS_CHART,
                WidgetType.MARKET_INTELLIGENCE,
                WidgetType.NEWS_SENTIMENT,
                WidgetType.PERFORMANCE_SUMMARY,
                WidgetType.EARNINGS_CALENDAR,
                WidgetType.VOLATILITY_MONITOR,
                WidgetType.POSITION_OVERVIEW
            ],
            UserRole.EXECUTIVE: [
                WidgetType.PERFORMANCE_SUMMARY,
                WidgetType.RISK_METRICS,
                WidgetType.MARKET_INTELLIGENCE,
                WidgetType.PROTOCOL_STATUS,
                WidgetType.ANALYTICS_CHART,
                WidgetType.NEWS_SENTIMENT
            ],
            UserRole.INVESTOR: [
                WidgetType.PERFORMANCE_SUMMARY,
                WidgetType.POSITION_OVERVIEW,
                WidgetType.MARKET_INTELLIGENCE,
                WidgetType.NEWS_SENTIMENT,
                WidgetType.EARNINGS_CALENDAR,
                WidgetType.RISK_METRICS
            ]
        }
    
    async def create_personalized_dashboard(self, user_id: str, user_role: UserRole = None, 
                                          preferences: Dict[str, Any] = None) -> DashboardLayout:
        """
        Create a personalized dashboard for a user.
        
        Args:
            user_id: User identifier
            user_role: User's role for initial layout
            preferences: User preferences override
            
        Returns:
            DashboardLayout: Personalized dashboard configuration
        """
        try:
            # Get or create user behavior profile
            user_behavior = await self._get_user_behavior(user_id)
            
            # Determine initial widget set
            if user_role:
                initial_widgets = self.role_based_layouts.get(user_role, self.role_based_layouts[UserRole.TRADER])
            else:
                initial_widgets = self._infer_preferred_widgets(user_behavior)
            
            # Create widget configurations
            widgets = []
            position_x, position_y = 0, 0
            
            for i, widget_type in enumerate(initial_widgets):
                widget_config = await self._create_widget_config(
                    widget_type, user_id, user_behavior, position_x, position_y
                )
                widgets.append(widget_config)
                
                # Calculate next position
                position_x += widget_config.size.value.count('x') if 'x' in widget_config.size.value else 2
                if position_x >= 6:  # Wrap to next row
                    position_x = 0
                    position_y += 1
            
            # Apply user preferences
            if preferences:
                widgets = self._apply_user_preferences(widgets, preferences)
            
            # Create dashboard layout
            layout = DashboardLayout(
                layout_id=f"dashboard_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                layout_name=f"Personalized Dashboard - {user_role.value if user_role else 'Custom'}",
                widgets=widgets,
                grid_columns=6,
                grid_rows=max(4, position_y + 2),
                theme=preferences.get("theme", "professional") if preferences else "professional",
                auto_refresh=preferences.get("auto_refresh", True) if preferences else True,
                created_at=datetime.utcnow(),
                last_modified=datetime.utcnow(),
                usage_stats={"views": 0, "interactions": 0, "time_spent": 0}
            )
            
            # Store layout
            self.dashboard_layouts[layout.layout_id] = layout
            
            logger.info(f"Created personalized dashboard for user {user_id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error creating personalized dashboard: {e}")
            return await self._create_default_dashboard(user_id)
    
    async def optimize_dashboard_layout(self, user_id: str, layout_id: str) -> DashboardLayout:
        """
        Optimize dashboard layout based on user behavior analytics.
        
        Args:
            user_id: User identifier
            layout_id: Dashboard layout identifier
            
        Returns:
            DashboardLayout: Optimized dashboard layout
        """
        try:
            # Get current layout and user behavior
            layout = self.dashboard_layouts.get(layout_id)
            if not layout:
                raise ValueError(f"Layout {layout_id} not found")
            
            user_behavior = await self._get_user_behavior(user_id)
            
            # Analyze widget usage patterns
            widget_scores = self._calculate_widget_scores(layout.widgets, user_behavior)
            
            # Reorder widgets by importance
            optimized_widgets = self._reorder_widgets_by_importance(layout.widgets, widget_scores)
            
            # Optimize widget sizes based on usage
            optimized_widgets = self._optimize_widget_sizes(optimized_widgets, widget_scores)
            
            # Recalculate positions
            optimized_widgets = self._recalculate_positions(optimized_widgets)
            
            # Update layout
            layout.widgets = optimized_widgets
            layout.last_modified = datetime.utcnow()
            
            logger.info(f"Optimized dashboard layout {layout_id} for user {user_id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error optimizing dashboard layout: {e}")
            return layout  # Return original layout on error
    
    async def add_anomaly_highlights(self, layout_id: str, anomalies: List[Dict[str, Any]]) -> DashboardLayout:
        """
        Add anomaly highlights to dashboard widgets.
        
        Args:
            layout_id: Dashboard layout identifier
            anomalies: List of detected anomalies
            
        Returns:
            DashboardLayout: Updated layout with anomaly highlights
        """
        try:
            layout = self.dashboard_layouts.get(layout_id)
            if not layout:
                raise ValueError(f"Layout {layout_id} not found")
            
            # Process anomalies and map to widgets
            for anomaly in anomalies:
                relevant_widgets = self._find_relevant_widgets(layout.widgets, anomaly)
                
                for widget in relevant_widgets:
                    # Add anomaly highlight to widget preferences
                    if not widget.user_preferences:
                        widget.user_preferences = {}
                    
                    if "anomaly_highlights" not in widget.user_preferences:
                        widget.user_preferences["anomaly_highlights"] = []
                    
                    widget.user_preferences["anomaly_highlights"].append({
                        "type": anomaly.get("type", "unknown"),
                        "severity": anomaly.get("severity", "medium"),
                        "message": anomaly.get("message", "Anomaly detected"),
                        "timestamp": anomaly.get("timestamp", datetime.utcnow().isoformat()),
                        "data": anomaly.get("data", {})
                    })
            
            layout.last_modified = datetime.utcnow()
            
            logger.info(f"Added {len(anomalies)} anomaly highlights to layout {layout_id}")
            return layout
            
        except Exception as e:
            logger.error(f"Error adding anomaly highlights: {e}")
            return layout
    
    async def get_contextual_widgets(self, user_id: str, context: Dict[str, Any]) -> List[WidgetConfig]:
        """
        Get contextually relevant widgets based on current market conditions and user context.
        
        Args:
            user_id: User identifier
            context: Current context (market conditions, time of day, etc.)
            
        Returns:
            List[WidgetConfig]: Contextually relevant widgets
        """
        try:
            user_behavior = await self._get_user_behavior(user_id)
            
            # Determine context-based widget priorities
            contextual_widgets = []
            
            # Market hours context
            if context.get("market_hours", False):
                contextual_widgets.extend([
                    WidgetType.POSITION_OVERVIEW,
                    WidgetType.PROTOCOL_STATUS,
                    WidgetType.ALERTS_PANEL,
                    WidgetType.MARKET_INTELLIGENCE
                ])
            
            # High volatility context
            if context.get("high_volatility", False):
                contextual_widgets.extend([
                    WidgetType.RISK_METRICS,
                    WidgetType.VOLATILITY_MONITOR,
                    WidgetType.PROTOCOL_STATUS
                ])
            
            # Earnings season context
            if context.get("earnings_season", False):
                contextual_widgets.extend([
                    WidgetType.EARNINGS_CALENDAR,
                    WidgetType.NEWS_SENTIMENT,
                    WidgetType.POSITION_OVERVIEW
                ])
            
            # Protocol escalation context
            if context.get("protocol_escalation", False):
                contextual_widgets.extend([
                    WidgetType.PROTOCOL_STATUS,
                    WidgetType.RISK_METRICS,
                    WidgetType.ALERTS_PANEL,
                    WidgetType.MARKET_INTELLIGENCE
                ])
            
            # Remove duplicates and create widget configs
            unique_widgets = list(set(contextual_widgets))
            widget_configs = []
            
            for i, widget_type in enumerate(unique_widgets):
                widget_config = await self._create_widget_config(
                    widget_type, user_id, user_behavior, i % 3, i // 3
                )
                widget_configs.append(widget_config)
            
            return widget_configs
            
        except Exception as e:
            logger.error(f"Error getting contextual widgets: {e}")
            return []
    
    async def track_user_interaction(self, user_id: str, widget_id: str, 
                                   interaction_type: str, duration: float = None):
        """
        Track user interaction with dashboard widgets for personalization learning.
        
        Args:
            user_id: User identifier
            widget_id: Widget identifier
            interaction_type: Type of interaction (view, click, hover, etc.)
            duration: Time spent on interaction
        """
        try:
            user_behavior = await self._get_user_behavior(user_id)
            
            # Update interaction count
            if widget_id not in user_behavior.widget_interactions:
                user_behavior.widget_interactions[widget_id] = 0
            user_behavior.widget_interactions[widget_id] += 1
            
            # Update time spent
            if duration and widget_id not in user_behavior.time_spent:
                user_behavior.time_spent[widget_id] = 0
            if duration:
                user_behavior.time_spent[widget_id] += duration
            
            # Update peak usage hours
            current_hour = datetime.utcnow().hour
            if current_hour not in user_behavior.peak_usage_hours:
                user_behavior.peak_usage_hours.append(current_hour)
            
            user_behavior.last_updated = datetime.utcnow()
            
            # Store updated behavior
            self.user_behaviors[user_id] = user_behavior
            
        except Exception as e:
            logger.error(f"Error tracking user interaction: {e}")
    
    # Helper methods
    
    async def _get_user_behavior(self, user_id: str) -> UserBehavior:
        """Get or create user behavior profile."""
        if user_id not in self.user_behaviors:
            self.user_behaviors[user_id] = UserBehavior(
                user_id=user_id,
                widget_interactions={},
                time_spent={},
                preferred_timeframes=["1D", "1W"],
                frequently_viewed_symbols=[],
                peak_usage_hours=[],
                device_preferences={},
                last_updated=datetime.utcnow()
            )
        
        return self.user_behaviors[user_id]
    
    def _infer_preferred_widgets(self, user_behavior: UserBehavior) -> List[WidgetType]:
        """Infer preferred widgets from user behavior."""
        # Default to trader layout if no behavior data
        if not user_behavior.widget_interactions:
            return self.role_based_layouts[UserRole.TRADER]
        
        # Sort widgets by interaction frequency
        sorted_widgets = sorted(
            user_behavior.widget_interactions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Convert widget IDs back to types (simplified)
        preferred_types = []
        for widget_id, _ in sorted_widgets[:8]:  # Top 8 widgets
            # Extract widget type from ID (assuming format: "type_userid_timestamp")
            widget_type_str = widget_id.split('_')[0]
            try:
                widget_type = WidgetType(widget_type_str)
                preferred_types.append(widget_type)
            except ValueError:
                continue
        
        # Fill with defaults if needed
        while len(preferred_types) < 6:
            for default_type in self.role_based_layouts[UserRole.TRADER]:
                if default_type not in preferred_types:
                    preferred_types.append(default_type)
                    break
        
        return preferred_types[:8]
    
    async def _create_widget_config(self, widget_type: WidgetType, user_id: str, 
                                  user_behavior: UserBehavior, pos_x: int, pos_y: int) -> WidgetConfig:
        """Create widget configuration."""
        template = self.widget_templates[widget_type]
        
        # Determine size based on user behavior
        size = self._determine_optimal_size(widget_type, user_behavior)
        
        return WidgetConfig(
            widget_id=f"{widget_type.value}_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            widget_type=widget_type,
            title=template["title"],
            size=size,
            position={"x": pos_x, "y": pos_y},
            data_source=template["data_source"],
            refresh_interval=template["refresh_interval"],
            visible=True,
            customizable=True,
            priority=1,
            user_preferences={
                "chart_type": template["chart_type"],
                "metrics": template["metrics"]
            }
        )
    
    def _determine_optimal_size(self, widget_type: WidgetType, user_behavior: UserBehavior) -> WidgetSize:
        """Determine optimal widget size based on user behavior."""
        template = self.widget_templates[widget_type]
        default_size = template["default_size"]
        
        # Check if user has interacted with this widget type frequently
        widget_interactions = sum(
            count for widget_id, count in user_behavior.widget_interactions.items()
            if widget_type.value in widget_id
        )
        
        # Increase size for frequently used widgets
        if widget_interactions > 50:
            if default_size == WidgetSize.SMALL:
                return WidgetSize.MEDIUM
            elif default_size == WidgetSize.MEDIUM:
                return WidgetSize.LARGE
        
        return default_size
    
    def _apply_user_preferences(self, widgets: List[WidgetConfig], 
                              preferences: Dict[str, Any]) -> List[WidgetConfig]:
        """Apply user preferences to widget configurations."""
        for widget in widgets:
            if widget.widget_type.value in preferences:
                widget_prefs = preferences[widget.widget_type.value]
                
                # Update widget preferences
                if not widget.user_preferences:
                    widget.user_preferences = {}
                
                widget.user_preferences.update(widget_prefs)
                
                # Update visibility
                if "visible" in widget_prefs:
                    widget.visible = widget_prefs["visible"]
                
                # Update size
                if "size" in widget_prefs:
                    try:
                        widget.size = WidgetSize(widget_prefs["size"])
                    except ValueError:
                        pass  # Keep default size
        
        return widgets
    
    def _calculate_widget_scores(self, widgets: List[WidgetConfig], 
                               user_behavior: UserBehavior) -> Dict[str, float]:
        """Calculate importance scores for widgets based on user behavior."""
        scores = {}
        
        for widget in widgets:
            score = 0.0
            
            # Interaction frequency score
            interactions = user_behavior.widget_interactions.get(widget.widget_id, 0)
            score += interactions * 0.4
            
            # Time spent score
            time_spent = user_behavior.time_spent.get(widget.widget_id, 0)
            score += (time_spent / 3600) * 0.3  # Convert to hours
            
            # Priority score
            score += (4 - widget.priority) * 0.2  # Higher priority = higher score
            
            # Recency score
            if interactions > 0:
                score += 0.1  # Bonus for any recent interaction
            
            scores[widget.widget_id] = score
        
        return scores
    
    def _reorder_widgets_by_importance(self, widgets: List[WidgetConfig], 
                                     scores: Dict[str, float]) -> List[WidgetConfig]:
        """Reorder widgets by importance scores."""
        return sorted(widgets, key=lambda w: scores.get(w.widget_id, 0), reverse=True)
    
    def _optimize_widget_sizes(self, widgets: List[WidgetConfig], 
                             scores: Dict[str, float]) -> List[WidgetConfig]:
        """Optimize widget sizes based on importance scores."""
        for widget in widgets:
            score = scores.get(widget.widget_id, 0)
            
            # Increase size for high-scoring widgets
            if score > 10 and widget.size == WidgetSize.SMALL:
                widget.size = WidgetSize.MEDIUM
            elif score > 20 and widget.size == WidgetSize.MEDIUM:
                widget.size = WidgetSize.LARGE
        
        return widgets
    
    def _recalculate_positions(self, widgets: List[WidgetConfig]) -> List[WidgetConfig]:
        """Recalculate widget positions after reordering."""
        position_x, position_y = 0, 0
        
        for widget in widgets:
            widget.position = {"x": position_x, "y": position_y}
            
            # Calculate next position based on widget size
            if widget.size in [WidgetSize.LARGE, WidgetSize.EXTRA_LARGE]:
                position_x += 2
            elif widget.size == WidgetSize.WIDE:
                position_x += 3
            else:
                position_x += 1
            
            # Wrap to next row if needed
            if position_x >= 6:
                position_x = 0
                position_y += 2 if widget.size in [WidgetSize.LARGE, WidgetSize.EXTRA_LARGE] else 1
        
        return widgets
    
    def _find_relevant_widgets(self, widgets: List[WidgetConfig], 
                             anomaly: Dict[str, Any]) -> List[WidgetConfig]:
        """Find widgets relevant to a specific anomaly."""
        relevant_widgets = []
        anomaly_type = anomaly.get("type", "")
        
        # Map anomaly types to relevant widget types
        anomaly_widget_map = {
            "performance": [WidgetType.PERFORMANCE_SUMMARY, WidgetType.ANALYTICS_CHART],
            "risk": [WidgetType.RISK_METRICS, WidgetType.PROTOCOL_STATUS],
            "position": [WidgetType.POSITION_OVERVIEW, WidgetType.TRADE_HISTORY],
            "market": [WidgetType.MARKET_INTELLIGENCE, WidgetType.VOLATILITY_MONITOR],
            "protocol": [WidgetType.PROTOCOL_STATUS, WidgetType.ALERTS_PANEL],
            "volatility": [WidgetType.VOLATILITY_MONITOR, WidgetType.RISK_METRICS]
        }
        
        relevant_types = anomaly_widget_map.get(anomaly_type, [])
        
        for widget in widgets:
            if widget.widget_type in relevant_types:
                relevant_widgets.append(widget)
        
        return relevant_widgets
    
    async def _create_default_dashboard(self, user_id: str) -> DashboardLayout:
        """Create a default dashboard layout."""
        return await self.create_personalized_dashboard(user_id, UserRole.TRADER)
    
    def get_dashboard_layout_dict(self, layout: DashboardLayout) -> Dict[str, Any]:
        """Convert dashboard layout to dictionary for API responses."""
        return asdict(layout)
    
    def get_user_behavior_dict(self, user_behavior: UserBehavior) -> Dict[str, Any]:
        """Convert user behavior to dictionary for API responses."""
        return asdict(user_behavior)
    
    def get_available_widget_types(self) -> List[str]:
        """Get list of available widget types."""
        return [wt.value for wt in WidgetType]
    
    def get_available_widget_sizes(self) -> List[str]:
        """Get list of available widget sizes."""
        return [ws.value for ws in WidgetSize]

