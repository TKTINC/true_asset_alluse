"""
Notification Service

This module provides system-wide notification capabilities, integrating with
all workstreams to send real-time alerts and updates through the PWA system.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import logging
import asyncio
from dataclasses import dataclass

from .pwa_manager import PWAManager, NotificationType, NotificationPriority, PushNotification

logger = logging.getLogger(__name__)


class SystemEvent(Enum):
    """System events that trigger notifications."""
    # Trading events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_ROLLED = "position_rolled"
    POSITION_ASSIGNED = "position_assigned"
    
    # Risk management events
    PROTOCOL_ESCALATION = "protocol_escalation"
    PROTOCOL_DEESCALATION = "protocol_deescalation"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    HEDGE_DEPLOYED = "hedge_deployed"
    HEDGE_REMOVED = "hedge_removed"
    
    # Market events
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    VOLATILITY_SPIKE = "volatility_spike"
    EARNINGS_ANNOUNCEMENT = "earnings_announcement"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    CONSTITUTION_VIOLATION = "constitution_violation"
    
    # Account events
    ACCOUNT_FORKED = "account_forked"
    ACCOUNT_MERGED = "account_merged"
    BALANCE_THRESHOLD = "balance_threshold"
    
    # Performance events
    WEEKLY_PERFORMANCE = "weekly_performance"
    MONTHLY_PERFORMANCE = "monthly_performance"
    DRAWDOWN_ALERT = "drawdown_alert"
    PROFIT_TARGET = "profit_target"
    
    # ML Intelligence events
    ANOMALY_DETECTED = "anomaly_detected"
    PATTERN_MATCHED = "pattern_matched"
    FORECAST_GENERATED = "forecast_generated"
    LEARNING_INSIGHT = "learning_insight"


@dataclass
class EventSubscription:
    """Event subscription configuration."""
    event_type: SystemEvent
    callback: Callable
    user_id: Optional[str] = None
    priority_filter: NotificationPriority = NotificationPriority.NORMAL
    enabled: bool = True


class NotificationService:
    """
    System-wide notification service.
    
    Coordinates notifications across all workstreams and manages
    event subscriptions, filtering, and delivery through PWA.
    """
    
    def __init__(self, pwa_manager: PWAManager):
        """Initialize notification service."""
        self.pwa_manager = pwa_manager
        self.event_subscriptions: Dict[SystemEvent, List[EventSubscription]] = {}
        self.event_handlers: Dict[SystemEvent, Callable] = {}
        self.is_running = False
        
        # Initialize event handlers
        self._initialize_event_handlers()
        
        logger.info("Notification Service initialized")
    
    def _initialize_event_handlers(self):
        """Initialize event handlers for different system events."""
        self.event_handlers = {
            # Trading events
            SystemEvent.POSITION_OPENED: self._handle_position_opened,
            SystemEvent.POSITION_CLOSED: self._handle_position_closed,
            SystemEvent.POSITION_ROLLED: self._handle_position_rolled,
            SystemEvent.POSITION_ASSIGNED: self._handle_position_assigned,
            
            # Risk management events
            SystemEvent.PROTOCOL_ESCALATION: self._handle_protocol_escalation,
            SystemEvent.PROTOCOL_DEESCALATION: self._handle_protocol_deescalation,
            SystemEvent.RISK_LIMIT_BREACH: self._handle_risk_limit_breach,
            SystemEvent.HEDGE_DEPLOYED: self._handle_hedge_deployed,
            
            # Market events
            SystemEvent.MARKET_OPEN: self._handle_market_open,
            SystemEvent.MARKET_CLOSE: self._handle_market_close,
            SystemEvent.VOLATILITY_SPIKE: self._handle_volatility_spike,
            
            # System events
            SystemEvent.SYSTEM_STARTUP: self._handle_system_startup,
            SystemEvent.SYSTEM_ERROR: self._handle_system_error,
            SystemEvent.CONSTITUTION_VIOLATION: self._handle_constitution_violation,
            
            # Account events
            SystemEvent.ACCOUNT_FORKED: self._handle_account_forked,
            SystemEvent.BALANCE_THRESHOLD: self._handle_balance_threshold,
            
            # Performance events
            SystemEvent.WEEKLY_PERFORMANCE: self._handle_weekly_performance,
            SystemEvent.DRAWDOWN_ALERT: self._handle_drawdown_alert,
            
            # ML Intelligence events
            SystemEvent.ANOMALY_DETECTED: self._handle_anomaly_detected,
            SystemEvent.PATTERN_MATCHED: self._handle_pattern_matched,
            SystemEvent.FORECAST_GENERATED: self._handle_forecast_generated
        }
    
    async def start(self):
        """Start the notification service."""
        self.is_running = True
        logger.info("Notification Service started")
    
    async def stop(self):
        """Stop the notification service."""
        self.is_running = False
        logger.info("Notification Service stopped")
    
    def subscribe_to_event(self, event_type: SystemEvent, callback: Callable, 
                          user_id: Optional[str] = None, 
                          priority_filter: NotificationPriority = NotificationPriority.NORMAL):
        """Subscribe to system event."""
        subscription = EventSubscription(
            event_type=event_type,
            callback=callback,
            user_id=user_id,
            priority_filter=priority_filter
        )
        
        if event_type not in self.event_subscriptions:
            self.event_subscriptions[event_type] = []
        
        self.event_subscriptions[event_type].append(subscription)
        logger.info(f"Subscribed to event: {event_type.value}")
    
    async def emit_event(self, event_type: SystemEvent, event_data: Dict[str, Any]):
        """
        Emit system event and trigger notifications.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        try:
            if not self.is_running:
                return
            
            logger.info(f"Emitting event: {event_type.value}")
            
            # Call event handler
            if event_type in self.event_handlers:
                await self.event_handlers[event_type](event_data)
            
            # Notify subscribers
            if event_type in self.event_subscriptions:
                for subscription in self.event_subscriptions[event_type]:
                    if subscription.enabled:
                        try:
                            await subscription.callback(event_data)
                        except Exception as e:
                            logger.error(f"Error in event subscription callback: {e}")
            
        except Exception as e:
            logger.error(f"Error emitting event {event_type.value}: {e}")
    
    # Event Handlers
    
    async def _handle_position_opened(self, event_data: Dict[str, Any]):
        """Handle position opened event."""
        await self.pwa_manager.send_trade_notification(event_data, is_entry=True)
    
    async def _handle_position_closed(self, event_data: Dict[str, Any]):
        """Handle position closed event."""
        await self.pwa_manager.send_trade_notification(event_data, is_entry=False)
    
    async def _handle_position_rolled(self, event_data: Dict[str, Any]):
        """Handle position rolled event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.TRADE_ENTRY,
            {
                "symbol": event_data.get("symbol", ""),
                "position_type": "ROLLED",
                "price": event_data.get("new_price", 0),
                "delta": event_data.get("new_delta", 0),
                "roll_credit": event_data.get("roll_credit", 0)
            },
            priority=NotificationPriority.NORMAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_position_assigned(self, event_data: Dict[str, Any]):
        """Handle position assignment event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.TRADE_EXIT,
            {
                "symbol": event_data.get("symbol", ""),
                "position_type": "ASSIGNED",
                "price": event_data.get("assignment_price", 0),
                "pnl": event_data.get("assignment_pnl", 0)
            },
            priority=NotificationPriority.HIGH
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_protocol_escalation(self, event_data: Dict[str, Any]):
        """Handle protocol escalation event."""
        level = event_data.get("level", 0)
        reason = event_data.get("reason", "Unknown")
        await self.pwa_manager.send_protocol_escalation(level, reason)
    
    async def _handle_protocol_deescalation(self, event_data: Dict[str, Any]):
        """Handle protocol de-escalation event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.SYSTEM_STATUS,
            {
                "status": "DEESCALATED",
                "message": f"Protocol de-escalated to Level {event_data.get('level', 0)}"
            },
            priority=NotificationPriority.NORMAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_risk_limit_breach(self, event_data: Dict[str, Any]):
        """Handle risk limit breach event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.RISK_ALERT,
            {
                "risk_type": event_data.get("risk_type", "UNKNOWN"),
                "description": event_data.get("description", "Risk limit breached"),
                "exposure": event_data.get("current_exposure", 0)
            },
            priority=NotificationPriority.CRITICAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_hedge_deployed(self, event_data: Dict[str, Any]):
        """Handle hedge deployment event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.HEDGE_DEPLOYMENT,
            {
                "hedge_type": event_data.get("hedge_type", "VIX_CALL"),
                "coverage": event_data.get("coverage_percentage", 0),
                "cost": event_data.get("hedge_cost", 0)
            },
            priority=NotificationPriority.HIGH
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_market_open(self, event_data: Dict[str, Any]):
        """Handle market open event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.MARKET_ALERT,
            {
                "market_condition": "MARKET_OPEN",
                "description": "Market is now open for trading",
                "vix": event_data.get("vix", 0),
                "spx": event_data.get("spx", 0)
            },
            priority=NotificationPriority.LOW
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_market_close(self, event_data: Dict[str, Any]):
        """Handle market close event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.MARKET_ALERT,
            {
                "market_condition": "MARKET_CLOSE",
                "description": "Market has closed for the day",
                "vix": event_data.get("vix", 0),
                "spx": event_data.get("spx", 0)
            },
            priority=NotificationPriority.LOW
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_volatility_spike(self, event_data: Dict[str, Any]):
        """Handle volatility spike event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.MARKET_ALERT,
            {
                "market_condition": "VOLATILITY_SPIKE",
                "description": f"VIX spiked to {event_data.get('vix', 0)}",
                "vix": event_data.get("vix", 0),
                "spx": event_data.get("spx", 0)
            },
            priority=NotificationPriority.HIGH
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_system_startup(self, event_data: Dict[str, Any]):
        """Handle system startup event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.SYSTEM_STATUS,
            {
                "status": "STARTED",
                "message": "True-Asset-ALLUSE system has started successfully"
            },
            priority=NotificationPriority.NORMAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_system_error(self, event_data: Dict[str, Any]):
        """Handle system error event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.SYSTEM_STATUS,
            {
                "status": "ERROR",
                "message": f"System error: {event_data.get('error', 'Unknown error')}"
            },
            priority=NotificationPriority.CRITICAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_constitution_violation(self, event_data: Dict[str, Any]):
        """Handle Constitution violation event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.CONSTITUTION_VIOLATION,
            {
                "section": event_data.get("section", "Unknown"),
                "description": event_data.get("description", "Constitution violation detected")
            },
            priority=NotificationPriority.CRITICAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_account_forked(self, event_data: Dict[str, Any]):
        """Handle account forked event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.ACCOUNT_ALERT,
            {
                "account_name": event_data.get("new_account_name", ""),
                "message": f"Account forked from {event_data.get('parent_account', '')}",
                "balance": event_data.get("initial_balance", 0)
            },
            priority=NotificationPriority.NORMAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_balance_threshold(self, event_data: Dict[str, Any]):
        """Handle balance threshold event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.ACCOUNT_ALERT,
            {
                "account_name": event_data.get("account_name", ""),
                "message": f"Balance threshold {event_data.get('threshold_type', '')} reached",
                "balance": event_data.get("current_balance", 0)
            },
            priority=NotificationPriority.HIGH
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_weekly_performance(self, event_data: Dict[str, Any]):
        """Handle weekly performance event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.PERFORMANCE_UPDATE,
            {
                "pnl": event_data.get("weekly_pnl", 0),
                "percentage": event_data.get("weekly_percentage", 0),
                "total_return": event_data.get("total_return", 0)
            },
            priority=NotificationPriority.NORMAL
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_drawdown_alert(self, event_data: Dict[str, Any]):
        """Handle drawdown alert event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.RISK_ALERT,
            {
                "risk_type": "DRAWDOWN",
                "description": f"Drawdown of {event_data.get('drawdown_percentage', 0)}% detected",
                "exposure": event_data.get("current_value", 0)
            },
            priority=NotificationPriority.HIGH
        )
        await self.pwa_manager.send_notification(notification)
    
    async def _handle_anomaly_detected(self, event_data: Dict[str, Any]):
        """Handle anomaly detection event."""
        await self.pwa_manager.send_anomaly_alert(event_data)
    
    async def _handle_pattern_matched(self, event_data: Dict[str, Any]):
        """Handle pattern match event."""
        await self.pwa_manager.send_pattern_match(event_data)
    
    async def _handle_forecast_generated(self, event_data: Dict[str, Any]):
        """Handle forecast generation event."""
        notification = await self.pwa_manager.create_notification(
            NotificationType.SYSTEM_STATUS,
            {
                "status": "FORECAST_READY",
                "message": f"New {event_data.get('forecast_type', '')} forecast generated with {event_data.get('confidence', 0)}% confidence"
            },
            priority=NotificationPriority.LOW
        )
        await self.pwa_manager.send_notification(notification)
    
    # Convenience methods for common notifications
    
    async def notify_trade_entry(self, symbol: str, position_type: str, price: float, delta: float):
        """Notify trade entry."""
        await self.emit_event(SystemEvent.POSITION_OPENED, {
            "symbol": symbol,
            "position_type": position_type,
            "price": price,
            "delta": delta
        })
    
    async def notify_trade_exit(self, symbol: str, position_type: str, price: float, pnl: float):
        """Notify trade exit."""
        await self.emit_event(SystemEvent.POSITION_CLOSED, {
            "symbol": symbol,
            "position_type": position_type,
            "price": price,
            "pnl": pnl
        })
    
    async def notify_protocol_change(self, level: int, reason: str, is_escalation: bool = True):
        """Notify protocol level change."""
        event_type = SystemEvent.PROTOCOL_ESCALATION if is_escalation else SystemEvent.PROTOCOL_DEESCALATION
        await self.emit_event(event_type, {
            "level": level,
            "reason": reason
        })
    
    async def notify_anomaly(self, anomaly_type: str, description: str, confidence: float, severity: str = "MEDIUM"):
        """Notify anomaly detection."""
        await self.emit_event(SystemEvent.ANOMALY_DETECTED, {
            "anomaly_type": anomaly_type,
            "description": description,
            "confidence": confidence,
            "severity": severity
        })
    
    async def notify_pattern(self, pattern_name: str, confidence: float, outcome: str):
        """Notify pattern match."""
        await self.emit_event(SystemEvent.PATTERN_MATCHED, {
            "pattern_name": pattern_name,
            "confidence": confidence,
            "outcome": outcome
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics."""
        return {
            "service_running": self.is_running,
            "total_subscriptions": sum(len(subs) for subs in self.event_subscriptions.values()),
            "event_types": len(self.event_subscriptions),
            "pwa_stats": self.pwa_manager.get_stats()
        }

