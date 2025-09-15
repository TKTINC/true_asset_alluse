"""
Alert System

This module implements the alert and notification system for protocol
escalation events, breach detection, and system status changes.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .escalation_manager import EscalationEvent
from .protocol_levels import ProtocolLevel

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    LOG = "log"


@dataclass
class Alert:
    """Alert message structure."""
    alert_id: str
    timestamp: datetime
    priority: AlertPriority
    title: str
    message: str
    source: str
    event_type: str
    metadata: Dict[str, Any]
    channels: List[AlertChannel]
    recipients: List[str]
    sent: bool = False
    sent_at: Optional[datetime] = None
    delivery_attempts: int = 0
    last_error: Optional[str] = None


class AlertSystem:
    """
    Alert and notification system for protocol escalation events.
    
    Handles different types of alerts with configurable channels and priorities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize alert system.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        
        # Alert storage
        self.alerts = []  # List[Alert]
        self.alert_handlers = {}  # AlertChannel -> Callable
        
        # Configuration
        self.max_alerts = self.config.get("max_alerts", 1000)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.retry_delay = self.config.get("retry_delay", 60)  # seconds
        
        # Rate limiting
        self.rate_limits = self.config.get("rate_limits", {
            AlertPriority.INFO: 60,      # 1 per minute
            AlertPriority.WARNING: 30,   # 1 per 30 seconds
            AlertPriority.CRITICAL: 10,  # 1 per 10 seconds
            AlertPriority.EMERGENCY: 0   # No limit
        })
        
        self.last_alert_times = {}  # (priority, event_type) -> datetime
        
        # Initialize default handlers
        self._initialize_handlers()
        
        logger.info("Alert System initialized")
    
    def _initialize_handlers(self):
        """Initialize default alert handlers."""
        # Log handler (always available)
        self.alert_handlers[AlertChannel.LOG] = self._handle_log_alert
        
        # Email handler (if configured)
        if self.config.get("email_enabled"):
            self.alert_handlers[AlertChannel.EMAIL] = self._handle_email_alert
        
        # Webhook handler (if configured)
        if self.config.get("webhook_enabled"):
            self.alert_handlers[AlertChannel.WEBHOOK] = self._handle_webhook_alert
    
    def register_handler(self, channel: AlertChannel, handler: Callable):
        """
        Register custom alert handler.
        
        Args:
            channel: Alert channel
            handler: Handler function
        """
        self.alert_handlers[channel] = handler
        logger.info(f"Registered alert handler for {channel.value}")
    
    def send_escalation_alert(self, escalation_event: EscalationEvent) -> bool:
        """
        Send alert for protocol escalation event.
        
        Args:
            escalation_event: Escalation event
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Determine priority based on escalation level
            priority_map = {
                ProtocolLevel.NORMAL: AlertPriority.INFO,
                ProtocolLevel.ENHANCED: AlertPriority.WARNING,
                ProtocolLevel.RECOVERY: AlertPriority.CRITICAL,
                ProtocolLevel.PRESERVATION: AlertPriority.EMERGENCY
            }
            
            priority = priority_map.get(escalation_event.to_level, AlertPriority.WARNING)
            
            # Create alert message
            title = f"Protocol Escalated to {escalation_event.to_level.name}"
            message = self._format_escalation_message(escalation_event)
            
            # Determine channels based on priority
            channels = self._get_channels_for_priority(priority)
            
            # Get recipients
            recipients = self._get_recipients_for_priority(priority)
            
            # Create alert
            alert = Alert(
                alert_id=f"escalation_{escalation_event.event_id}",
                timestamp=escalation_event.timestamp,
                priority=priority,
                title=title,
                message=message,
                source="protocol_escalation",
                event_type="escalation",
                metadata=asdict(escalation_event),
                channels=channels,
                recipients=recipients
            )
            
            return self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error sending escalation alert: {str(e)}", exc_info=True)
            return False
    
    def send_de_escalation_alert(self, escalation_event: EscalationEvent) -> bool:
        """Send alert for protocol de-escalation event."""
        try:
            priority = AlertPriority.INFO
            
            title = f"Protocol De-escalated to {escalation_event.to_level.name}"
            message = self._format_de_escalation_message(escalation_event)
            
            channels = [AlertChannel.LOG, AlertChannel.EMAIL]
            recipients = self._get_recipients_for_priority(priority)
            
            alert = Alert(
                alert_id=f"de_escalation_{escalation_event.event_id}",
                timestamp=escalation_event.timestamp,
                priority=priority,
                title=title,
                message=message,
                source="protocol_escalation",
                event_type="de_escalation",
                metadata=asdict(escalation_event),
                channels=channels,
                recipients=recipients
            )
            
            return self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error sending de-escalation alert: {str(e)}", exc_info=True)
            return False
    
    def send_breach_alert(self, 
                         position_id: str,
                         symbol: str,
                         atr_breach_multiple: float,
                         position_loss_pct: float) -> bool:
        """Send alert for position breach detection."""
        try:
            # Determine priority based on breach severity
            if atr_breach_multiple >= 3.0 or position_loss_pct >= 5.0:
                priority = AlertPriority.EMERGENCY
            elif atr_breach_multiple >= 2.0 or position_loss_pct >= 3.0:
                priority = AlertPriority.CRITICAL
            else:
                priority = AlertPriority.WARNING
            
            title = f"Position Breach Detected: {symbol}"
            message = f"""
Position Breach Alert

Position ID: {position_id}
Symbol: {symbol}
ATR Breach Multiple: {atr_breach_multiple:.2f}x
Position Loss: {position_loss_pct:.2f}%

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This position has breached risk thresholds and requires immediate attention.
"""
            
            channels = self._get_channels_for_priority(priority)
            recipients = self._get_recipients_for_priority(priority)
            
            alert = Alert(
                alert_id=f"breach_{position_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                priority=priority,
                title=title,
                message=message,
                source="position_monitoring",
                event_type="breach_detected",
                metadata={
                    "position_id": position_id,
                    "symbol": symbol,
                    "atr_breach_multiple": atr_breach_multiple,
                    "position_loss_pct": position_loss_pct
                },
                channels=channels,
                recipients=recipients
            )
            
            return self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error sending breach alert: {str(e)}", exc_info=True)
            return False
    
    def send_system_alert(self, 
                         title: str,
                         message: str,
                         priority: AlertPriority = AlertPriority.INFO,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send general system alert."""
        try:
            channels = self._get_channels_for_priority(priority)
            recipients = self._get_recipients_for_priority(priority)
            
            alert = Alert(
                alert_id=f"system_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                priority=priority,
                title=title,
                message=message,
                source="system",
                event_type="system_alert",
                metadata=metadata or {},
                channels=channels,
                recipients=recipients
            )
            
            return self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error sending system alert: {str(e)}", exc_info=True)
            return False
    
    def _send_alert(self, alert: Alert) -> bool:
        """Send alert through configured channels."""
        try:
            # Check rate limiting
            if not self._check_rate_limit(alert):
                logger.info(f"Alert {alert.alert_id} rate limited")
                return False
            
            # Add to alert history
            self.alerts.append(alert)
            
            # Trim alert history if needed
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
            
            # Send through each channel
            success = True
            for channel in alert.channels:
                if channel in self.alert_handlers:
                    try:
                        handler_result = self.alert_handlers[channel](alert)
                        if not handler_result:
                            success = False
                            logger.warning(f"Failed to send alert {alert.alert_id} via {channel.value}")
                    except Exception as e:
                        success = False
                        alert.last_error = str(e)
                        logger.error(f"Error sending alert {alert.alert_id} via {channel.value}: {str(e)}")
                else:
                    logger.warning(f"No handler registered for channel {channel.value}")
            
            # Update alert status
            if success:
                alert.sent = True
                alert.sent_at = datetime.now()
            
            alert.delivery_attempts += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}", exc_info=True)
            return False
    
    def _check_rate_limit(self, alert: Alert) -> bool:
        """Check if alert is within rate limits."""
        try:
            rate_limit = self.rate_limits.get(alert.priority, 0)
            
            if rate_limit == 0:  # No rate limit
                return True
            
            key = (alert.priority, alert.event_type)
            now = datetime.now()
            
            if key in self.last_alert_times:
                time_since_last = (now - self.last_alert_times[key]).total_seconds()
                if time_since_last < rate_limit:
                    return False
            
            self.last_alert_times[key] = now
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow alert on error
    
    def _get_channels_for_priority(self, priority: AlertPriority) -> List[AlertChannel]:
        """Get alert channels based on priority."""
        channel_map = {
            AlertPriority.INFO: [AlertChannel.LOG],
            AlertPriority.WARNING: [AlertChannel.LOG, AlertChannel.EMAIL],
            AlertPriority.CRITICAL: [AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.WEBHOOK],
            AlertPriority.EMERGENCY: [AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.WEBHOOK, AlertChannel.SMS]
        }
        
        return channel_map.get(priority, [AlertChannel.LOG])
    
    def _get_recipients_for_priority(self, priority: AlertPriority) -> List[str]:
        """Get recipients based on priority."""
        recipients_config = self.config.get("recipients", {})
        
        return recipients_config.get(priority.value, [])
    
    def _format_escalation_message(self, event: EscalationEvent) -> str:
        """Format escalation event message."""
        return f"""
PROTOCOL ESCALATION ALERT

Event ID: {event.event_id}
Timestamp: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Escalation: {event.from_level.name} → {event.to_level.name}
Trigger: {event.trigger_reason}

Position Details:
- Position ID: {event.position_id or 'N/A'}
- ATR Breach: {event.atr_breach_multiple:.2f}x
- Position Loss: {event.position_loss_pct:.2f}%

Auto-Actions Taken:
{chr(10).join(f'- {action}' for action in event.auto_actions_taken) if event.auto_actions_taken else '- None'}

This escalation requires immediate attention and monitoring.
"""
    
    def _format_de_escalation_message(self, event: EscalationEvent) -> str:
        """Format de-escalation event message."""
        return f"""
PROTOCOL DE-ESCALATION NOTICE

Event ID: {event.event_id}
Timestamp: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

De-escalation: {event.from_level.name} → {event.to_level.name}
Reason: {event.trigger_reason}

Risk conditions have improved and protocol level has been reduced.
"""
    
    def _handle_log_alert(self, alert: Alert) -> bool:
        """Handle log alert."""
        try:
            log_level_map = {
                AlertPriority.INFO: logging.INFO,
                AlertPriority.WARNING: logging.WARNING,
                AlertPriority.CRITICAL: logging.ERROR,
                AlertPriority.EMERGENCY: logging.CRITICAL
            }
            
            log_level = log_level_map.get(alert.priority, logging.INFO)
            
            logger.log(log_level, f"ALERT [{alert.priority.value.upper()}] {alert.title}: {alert.message}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling log alert: {str(e)}")
            return False
    
    def _handle_email_alert(self, alert: Alert) -> bool:
        """Handle email alert."""
        try:
            email_config = self.config.get("email", {})
            
            if not email_config.get("enabled", False):
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config.get("from_address")
            msg['Subject'] = f"[{alert.priority.value.upper()}] {alert.title}"
            
            # Add recipients
            recipients = alert.recipients or email_config.get("default_recipients", [])
            if not recipients:
                logger.warning("No email recipients configured")
                return False
            
            msg['To'] = ", ".join(recipients)
            
            # Add message body
            body = f"""
Alert Details:
- Priority: {alert.priority.value.upper()}
- Source: {alert.source}
- Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{alert.message}

Alert ID: {alert.alert_id}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            smtp_server = smtplib.SMTP(
                email_config.get("smtp_host", "localhost"),
                email_config.get("smtp_port", 587)
            )
            
            if email_config.get("use_tls", True):
                smtp_server.starttls()
            
            if email_config.get("username") and email_config.get("password"):
                smtp_server.login(email_config["username"], email_config["password"])
            
            smtp_server.send_message(msg)
            smtp_server.quit()
            
            logger.info(f"Email alert sent: {alert.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}", exc_info=True)
            return False
    
    def _handle_webhook_alert(self, alert: Alert) -> bool:
        """Handle webhook alert."""
        try:
            webhook_config = self.config.get("webhook", {})
            
            if not webhook_config.get("enabled", False):
                return False
            
            import requests
            
            # Prepare webhook payload
            payload = {
                "alert_id": alert.alert_id,
                "timestamp": alert.timestamp.isoformat(),
                "priority": alert.priority.value,
                "title": alert.title,
                "message": alert.message,
                "source": alert.source,
                "event_type": alert.event_type,
                "metadata": alert.metadata
            }
            
            # Send webhook
            response = requests.post(
                webhook_config["url"],
                json=payload,
                headers=webhook_config.get("headers", {}),
                timeout=webhook_config.get("timeout", 30)
            )
            
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {str(e)}", exc_info=True)
            return False
    
    def get_alert_history(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert history for specified time period."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]
            
            # Group by priority
            priority_counts = {}
            for priority in AlertPriority:
                priority_counts[priority.value] = sum(
                    1 for alert in recent_alerts
                    if alert.priority == priority
                )
            
            # Group by event type
            event_type_counts = {}
            for alert in recent_alerts:
                event_type = alert.event_type
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            return {
                "total_alerts": len(recent_alerts),
                "priority_breakdown": priority_counts,
                "event_type_breakdown": event_type_counts,
                "recent_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "timestamp": alert.timestamp.isoformat(),
                        "priority": alert.priority.value,
                        "title": alert.title,
                        "source": alert.source,
                        "event_type": alert.event_type,
                        "sent": alert.sent
                    }
                    for alert in recent_alerts[-50:]  # Last 50 alerts
                ],
                "analysis_period_hours": hours,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting alert history: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert system statistics."""
        try:
            total_alerts = len(self.alerts)
            sent_alerts = sum(1 for alert in self.alerts if alert.sent)
            failed_alerts = total_alerts - sent_alerts
            
            # Calculate success rate
            success_rate = (sent_alerts / total_alerts * 100) if total_alerts > 0 else 0
            
            # Channel statistics
            channel_stats = {}
            for channel in AlertChannel:
                channel_stats[channel.value] = {
                    "enabled": channel in self.alert_handlers,
                    "handler_registered": channel in self.alert_handlers
                }
            
            return {
                "total_alerts": total_alerts,
                "sent_alerts": sent_alerts,
                "failed_alerts": failed_alerts,
                "success_rate_pct": success_rate,
                "registered_channels": len(self.alert_handlers),
                "channel_statistics": channel_stats,
                "rate_limits": {priority.value: limit for priority, limit in self.rate_limits.items()},
                "statistics_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "statistics_timestamp": datetime.now().isoformat()
            }

