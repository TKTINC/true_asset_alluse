"""
Progressive Web App (PWA) Manager

This module implements Progressive Web App functionality for the True-Asset-ALLUSE system,
including service workers, push notifications, offline capabilities, and app-like experience.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import asyncio
from dataclasses import dataclass, asdict
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of push notifications."""
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    PROTOCOL_ESCALATION = "protocol_escalation"
    ANOMALY_ALERT = "anomaly_alert"
    PATTERN_MATCH = "pattern_match"
    RISK_ALERT = "risk_alert"
    SYSTEM_STATUS = "system_status"
    PERFORMANCE_UPDATE = "performance_update"
    ACCOUNT_ALERT = "account_alert"
    MARKET_ALERT = "market_alert"
    CONSTITUTION_VIOLATION = "constitution_violation"
    HEDGE_DEPLOYMENT = "hedge_deployment"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PushNotification:
    """Push notification data structure."""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    body: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    actions: Optional[List[Dict[str, str]]] = None
    icon: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    tag: Optional[str] = None
    require_interaction: bool = False


@dataclass
class PWAConfig:
    """PWA configuration."""
    app_name: str = "True-Asset-ALLUSE"
    app_short_name: str = "ALLUSE"
    app_description: str = "Autopilot for Wealth - Engineered for compounding income and corpus"
    theme_color: str = "#1a365d"
    background_color: str = "#ffffff"
    display: str = "standalone"
    orientation: str = "portrait-primary"
    start_url: str = "/"
    scope: str = "/"
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@trueasset.com"
    notification_icon: str = "/static/icons/notification-icon.png"
    badge_icon: str = "/static/icons/badge-icon.png"


class PWAManager:
    """
    Progressive Web App Manager.
    
    Manages PWA functionality including service workers, push notifications,
    offline capabilities, and app-like user experience.
    """
    
    def __init__(self, config: PWAConfig = None):
        """Initialize PWA Manager."""
        self.config = config or PWAConfig()
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.notification_queue: List[PushNotification] = []
        self.notification_history: List[PushNotification] = []
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        
        # Notification templates
        self.notification_templates = self._initialize_notification_templates()
        
        logger.info("PWA Manager initialized")
    
    def _initialize_notification_templates(self) -> Dict[NotificationType, Dict[str, str]]:
        """Initialize notification templates."""
        return {
            NotificationType.TRADE_ENTRY: {
                "title": "Trade Entry: {symbol}",
                "body": "Entered {position_type} position in {symbol} at ${price}. Delta: {delta}",
                "icon": "/static/icons/trade-entry.png"
            },
            NotificationType.TRADE_EXIT: {
                "title": "Trade Exit: {symbol}",
                "body": "Exited {position_type} position in {symbol} at ${price}. P&L: ${pnl}",
                "icon": "/static/icons/trade-exit.png"
            },
            NotificationType.PROTOCOL_ESCALATION: {
                "title": "Protocol Escalation: Level {level}",
                "body": "System escalated to Protocol Level {level}. Reason: {reason}",
                "icon": "/static/icons/protocol-alert.png"
            },
            NotificationType.ANOMALY_ALERT: {
                "title": "Market Anomaly Detected",
                "body": "{anomaly_type}: {description}. Confidence: {confidence}%",
                "icon": "/static/icons/anomaly-alert.png"
            },
            NotificationType.PATTERN_MATCH: {
                "title": "Pattern Match: {pattern_name}",
                "body": "Detected {pattern_name} with {confidence}% confidence. Expected outcome: {outcome}",
                "icon": "/static/icons/pattern-match.png"
            },
            NotificationType.RISK_ALERT: {
                "title": "Risk Alert: {risk_type}",
                "body": "{description}. Current exposure: {exposure}",
                "icon": "/static/icons/risk-alert.png"
            },
            NotificationType.SYSTEM_STATUS: {
                "title": "System Status: {status}",
                "body": "{message}",
                "icon": "/static/icons/system-status.png"
            },
            NotificationType.PERFORMANCE_UPDATE: {
                "title": "Performance Update",
                "body": "Weekly P&L: ${pnl} ({percentage}%). Total return: {total_return}%",
                "icon": "/static/icons/performance.png"
            },
            NotificationType.ACCOUNT_ALERT: {
                "title": "Account Alert: {account_name}",
                "body": "{message}. Current balance: ${balance}",
                "icon": "/static/icons/account-alert.png"
            },
            NotificationType.MARKET_ALERT: {
                "title": "Market Alert: {market_condition}",
                "body": "{description}. VIX: {vix}, SPX: ${spx}",
                "icon": "/static/icons/market-alert.png"
            },
            NotificationType.CONSTITUTION_VIOLATION: {
                "title": "Constitution Violation",
                "body": "Potential violation in {section}: {description}",
                "icon": "/static/icons/constitution-alert.png"
            },
            NotificationType.HEDGE_DEPLOYMENT: {
                "title": "Hedge Deployment",
                "body": "Deployed {hedge_type} hedge. Coverage: {coverage}%, Cost: ${cost}",
                "icon": "/static/icons/hedge-deployment.png"
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize PWA functionality."""
        try:
            # Generate service worker
            await self._generate_service_worker()
            
            # Generate web app manifest
            await self._generate_manifest()
            
            # Initialize push notification service
            await self._initialize_push_service()
            
            self.is_initialized = True
            logger.info("PWA Manager successfully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PWA Manager: {e}")
            return False
    
    async def _generate_service_worker(self):
        """Generate service worker JavaScript file."""
        service_worker_content = f"""
// True-Asset-ALLUSE Service Worker
const CACHE_NAME = 'true-asset-alluse-v1';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/dashboard',
    '/portfolio',
    '/performance'
];

// Install event
self.addEventListener('install', event => {{
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {{
                return cache.addAll(urlsToCache);
            }})
    );
}});

// Fetch event
self.addEventListener('fetch', event => {{
    event.respondWith(
        caches.match(event.request)
            .then(response => {{
                // Return cached version or fetch from network
                return response || fetch(event.request);
            }})
    );
}});

// Push event
self.addEventListener('push', event => {{
    const options = {{
        body: event.data ? event.data.text() : 'New notification from True-Asset-ALLUSE',
        icon: '{self.config.notification_icon}',
        badge: '{self.config.badge_icon}',
        vibrate: [100, 50, 100],
        data: {{
            dateOfArrival: Date.now(),
            primaryKey: 1
        }},
        actions: [
            {{
                action: 'explore',
                title: 'View Details',
                icon: '/static/icons/view-icon.png'
            }},
            {{
                action: 'close',
                title: 'Dismiss',
                icon: '/static/icons/close-icon.png'
            }}
        ]
    }};

    if (event.data) {{
        const notificationData = event.data.json();
        options.title = notificationData.title || 'True-Asset-ALLUSE';
        options.body = notificationData.body || options.body;
        options.icon = notificationData.icon || options.icon;
        options.data = notificationData.data || options.data;
        options.requireInteraction = notificationData.requireInteraction || false;
        
        if (notificationData.actions) {{
            options.actions = notificationData.actions;
        }}
    }}

    event.waitUntil(
        self.registration.showNotification(options.title || 'True-Asset-ALLUSE', options)
    );
}});

// Notification click event
self.addEventListener('notificationclick', event => {{
    event.notification.close();

    if (event.action === 'explore') {{
        // Open the app to relevant page
        event.waitUntil(
            clients.openWindow('/dashboard')
        );
    }} else if (event.action === 'close') {{
        // Just close the notification
        return;
    }} else {{
        // Default action - open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }}
}});

// Background sync
self.addEventListener('sync', event => {{
    if (event.tag === 'background-sync') {{
        event.waitUntil(doBackgroundSync());
    }}
}});

function doBackgroundSync() {{
    // Sync data when connection is restored
    return fetch('/api/v1/sync')
        .then(response => response.json())
        .then(data => {{
            // Handle sync data
            console.log('Background sync completed:', data);
        }})
        .catch(error => {{
            console.error('Background sync failed:', error);
        }});
}}
"""
        
        # Write service worker file
        sw_path = Path("src/ws6_user_interface/dashboard/static/js/sw.js")
        sw_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sw_path, 'w') as f:
            f.write(service_worker_content)
        
        logger.info("Service worker generated successfully")
    
    async def _generate_manifest(self):
        """Generate web app manifest."""
        manifest = {
            "name": self.config.app_name,
            "short_name": self.config.app_short_name,
            "description": self.config.app_description,
            "start_url": self.config.start_url,
            "scope": self.config.scope,
            "display": self.config.display,
            "orientation": self.config.orientation,
            "theme_color": self.config.theme_color,
            "background_color": self.config.background_color,
            "icons": [
                {
                    "src": "/static/icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "categories": ["finance", "business", "productivity"],
            "lang": "en-US",
            "dir": "ltr"
        }
        
        # Write manifest file
        manifest_path = Path("src/ws6_user_interface/dashboard/static/manifest.json")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info("Web app manifest generated successfully")
    
    async def _initialize_push_service(self):
        """Initialize push notification service."""
        try:
            # In a real implementation, this would set up VAPID keys
            # and configure the push notification service
            logger.info("Push notification service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize push service: {e}")
    
    async def subscribe_user(self, user_id: str, subscription_data: Dict[str, Any]) -> bool:
        """
        Subscribe user to push notifications.
        
        Args:
            user_id: User identifier
            subscription_data: Push subscription data from browser
            
        Returns:
            bool: True if subscription successful
        """
        try:
            self.subscriptions[user_id] = {
                "subscription": subscription_data,
                "created_at": datetime.utcnow(),
                "active": True
            }
            
            # Set default preferences
            self.user_preferences[user_id] = {
                "enabled_notifications": [nt.value for nt in NotificationType],
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "priority_filter": NotificationPriority.NORMAL.value,
                "sound_enabled": True,
                "vibration_enabled": True
            }
            
            logger.info(f"User {user_id} subscribed to push notifications")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id}: {e}")
            return False
    
    async def unsubscribe_user(self, user_id: str) -> bool:
        """Unsubscribe user from push notifications."""
        try:
            if user_id in self.subscriptions:
                self.subscriptions[user_id]["active"] = False
                logger.info(f"User {user_id} unsubscribed from push notifications")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe user {user_id}: {e}")
            return False
    
    async def send_notification(self, notification: PushNotification) -> bool:
        """
        Send push notification to user(s).
        
        Args:
            notification: Notification to send
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Add to queue and history
            self.notification_queue.append(notification)
            self.notification_history.append(notification)
            
            # Keep history limited to last 1000 notifications
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-1000:]
            
            # Send to specific user or all subscribed users
            target_users = [notification.user_id] if notification.user_id else list(self.subscriptions.keys())
            
            sent_count = 0
            for user_id in target_users:
                if await self._send_to_user(user_id, notification):
                    sent_count += 1
            
            logger.info(f"Notification sent to {sent_count} users: {notification.title}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def _send_to_user(self, user_id: str, notification: PushNotification) -> bool:
        """Send notification to specific user."""
        try:
            # Check if user is subscribed and active
            if user_id not in self.subscriptions or not self.subscriptions[user_id]["active"]:
                return False
            
            # Check user preferences
            user_prefs = self.user_preferences.get(user_id, {})
            
            # Check if notification type is enabled
            enabled_types = user_prefs.get("enabled_notifications", [])
            if notification.type.value not in enabled_types:
                return False
            
            # Check priority filter
            priority_filter = NotificationPriority(user_prefs.get("priority_filter", "normal"))
            if notification.priority.value < priority_filter.value:
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(user_prefs):
                # Only send critical notifications during quiet hours
                if notification.priority != NotificationPriority.CRITICAL:
                    return False
            
            # In a real implementation, this would send the actual push notification
            # using the Web Push Protocol and the user's subscription data
            logger.debug(f"Sending notification to user {user_id}: {notification.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False
    
    def _is_quiet_hours(self, user_prefs: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours."""
        try:
            quiet_hours = user_prefs.get("quiet_hours", {})
            if not quiet_hours:
                return False
            
            now = datetime.now().time()
            start_time = datetime.strptime(quiet_hours["start"], "%H:%M").time()
            end_time = datetime.strptime(quiet_hours["end"], "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:
                # Quiet hours span midnight
                return now >= start_time or now <= end_time
                
        except Exception:
            return False
    
    async def create_notification(self, 
                                notification_type: NotificationType,
                                data: Dict[str, Any],
                                user_id: Optional[str] = None,
                                priority: NotificationPriority = NotificationPriority.NORMAL) -> PushNotification:
        """
        Create notification from template and data.
        
        Args:
            notification_type: Type of notification
            data: Data to populate template
            user_id: Target user ID (None for all users)
            priority: Notification priority
            
        Returns:
            PushNotification: Created notification
        """
        template = self.notification_templates.get(notification_type, {})
        
        # Format title and body with data
        title = template.get("title", "True-Asset-ALLUSE Notification").format(**data)
        body = template.get("body", "New notification").format(**data)
        
        # Create notification
        notification = PushNotification(
            id=str(uuid.uuid4()),
            type=notification_type,
            priority=priority,
            title=title,
            body=body,
            data=data,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            icon=template.get("icon", self.config.notification_icon),
            badge=self.config.badge_icon,
            require_interaction=(priority == NotificationPriority.CRITICAL)
        )
        
        return notification
    
    async def send_trade_notification(self, trade_data: Dict[str, Any], is_entry: bool = True):
        """Send trade entry/exit notification."""
        notification_type = NotificationType.TRADE_ENTRY if is_entry else NotificationType.TRADE_EXIT
        priority = NotificationPriority.HIGH if abs(float(trade_data.get("pnl", 0))) > 1000 else NotificationPriority.NORMAL
        
        notification = await self.create_notification(notification_type, trade_data, priority=priority)
        await self.send_notification(notification)
    
    async def send_protocol_escalation(self, level: int, reason: str):
        """Send protocol escalation notification."""
        data = {"level": level, "reason": reason}
        priority = NotificationPriority.CRITICAL if level >= 3 else NotificationPriority.HIGH
        
        notification = await self.create_notification(NotificationType.PROTOCOL_ESCALATION, data, priority=priority)
        await self.send_notification(notification)
    
    async def send_anomaly_alert(self, anomaly_data: Dict[str, Any]):
        """Send anomaly detection alert."""
        severity = anomaly_data.get("severity", "MEDIUM")
        priority = NotificationPriority.CRITICAL if severity == "CRITICAL" else NotificationPriority.HIGH
        
        notification = await self.create_notification(NotificationType.ANOMALY_ALERT, anomaly_data, priority=priority)
        await self.send_notification(notification)
    
    async def send_pattern_match(self, pattern_data: Dict[str, Any]):
        """Send pattern match notification."""
        confidence = float(pattern_data.get("confidence", 0))
        priority = NotificationPriority.HIGH if confidence > 0.8 else NotificationPriority.NORMAL
        
        notification = await self.create_notification(NotificationType.PATTERN_MATCH, pattern_data, priority=priority)
        await self.send_notification(notification)
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences."""
        return self.user_preferences.get(user_id, {})
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user notification preferences."""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}
            
            self.user_preferences[user_id].update(preferences)
            logger.info(f"Updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return False
    
    def get_notification_history(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history."""
        history = self.notification_history
        
        if user_id:
            history = [n for n in history if n.user_id == user_id or n.user_id is None]
        
        # Return most recent notifications
        recent_history = sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [asdict(notification) for notification in recent_history]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get PWA and notification statistics."""
        return {
            "pwa_enabled": self.is_initialized,
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": len([s for s in self.subscriptions.values() if s["active"]]),
            "notifications_sent_today": len([n for n in self.notification_history 
                                           if n.timestamp.date() == datetime.now().date()]),
            "total_notifications": len(self.notification_history),
            "notification_types": {nt.value: len([n for n in self.notification_history if n.type == nt]) 
                                 for nt in NotificationType}
        }

