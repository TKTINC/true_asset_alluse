"""
System Health Monitoring and Alerting

This module implements comprehensive system health monitoring and alerting
for the True-Asset-ALLUSE system.
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


@dataclass
class HealthMetric:
    """Health metric data structure."""
    name: str
    value: float
    threshold: float
    status: str
    timestamp: datetime
    alert_level: AlertLevel


@dataclass
class SystemAlert:
    """System alert data structure."""
    alert_id: str
    alert_level: AlertLevel
    component: str
    message: str
    timestamp: datetime
    acknowledged: bool = False


class SystemHealthMonitor:
    """
    Comprehensive system health monitoring and alerting.
    
    This class monitors all aspects of the True-Asset-ALLUSE system
    and provides real-time health status and alerting.
    """
    
    def __init__(self, system_orchestrator):
        """Initialize the system health monitor."""
        self.system = system_orchestrator
        self.is_monitoring = False
        self.monitoring_interval = 30  # seconds
        
        # Health metrics storage
        self.health_metrics = {}
        self.metric_history = {}
        self.active_alerts = []
        self.alert_history = []
        
        # Thresholds for various metrics
        self.thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 1.0,
            "error_rate": 5.0,
            "connection_failures": 10,
            "queue_depth": 1000
        }
        
        # Alert channels
        self.alert_channels = {
            "email": True,
            "webhook": True,
            "log": True,
            "sms": False  # Disabled by default
        }
        
        logger.info("System Health Monitor initialized")
    
    async def start_monitoring(self):
        """Start the health monitoring process."""
        if self.is_monitoring:
            logger.warning("Health monitoring is already running")
            return
        
        self.is_monitoring = True
        logger.info("Starting system health monitoring...")
        
        # Start monitoring tasks
        asyncio.create_task(self._system_metrics_monitor())
        asyncio.create_task(self._workstream_health_monitor())
        asyncio.create_task(self._performance_monitor())
        asyncio.create_task(self._alert_processor())
        
        logger.info("System health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring process."""
        self.is_monitoring = False
        logger.info("System health monitoring stopped")
    
    async def _system_metrics_monitor(self):
        """Monitor system-level metrics."""
        while self.is_monitoring:
            try:
                # CPU usage
                cpu_usage = psutil.cpu_percent(interval=1)
                await self._record_metric("cpu_usage", cpu_usage, self.thresholds["cpu_usage"])
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_usage = memory.percent
                await self._record_metric("memory_usage", memory_usage, self.thresholds["memory_usage"])
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_usage = (disk.used / disk.total) * 100
                await self._record_metric("disk_usage", disk_usage, self.thresholds["disk_usage"])
                
                # Network I/O
                network = psutil.net_io_counters()
                await self._record_metric("network_bytes_sent", network.bytes_sent, float('inf'))
                await self._record_metric("network_bytes_recv", network.bytes_recv, float('inf'))
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"System metrics monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _workstream_health_monitor(self):
        """Monitor workstream-specific health."""
        while self.is_monitoring:
            try:
                if self.system and hasattr(self.system, '_perform_health_check'):
                    health_status = await self.system._perform_health_check()
                    
                    # Process workstream health
                    for ws_name, ws_health in health_status.get("workstreams", {}).items():
                        status = ws_health.get("status", "UNKNOWN")
                        
                        if status != "HEALTHY":
                            await self._create_alert(
                                AlertLevel.WARNING,
                                ws_name,
                                f"Workstream {ws_name} status: {status}"
                            )
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Workstream health monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _performance_monitor(self):
        """Monitor system performance metrics."""
        while self.is_monitoring:
            try:
                # Response time monitoring
                response_time = await self._measure_system_response_time()
                await self._record_metric("response_time", response_time, self.thresholds["response_time"])
                
                # Error rate monitoring
                error_rate = await self._calculate_error_rate()
                await self._record_metric("error_rate", error_rate, self.thresholds["error_rate"])
                
                # Connection monitoring
                connection_failures = await self._count_connection_failures()
                await self._record_metric("connection_failures", connection_failures, self.thresholds["connection_failures"])
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _alert_processor(self):
        """Process and dispatch alerts."""
        while self.is_monitoring:
            try:
                # Process active alerts
                for alert in self.active_alerts:
                    if not alert.acknowledged:
                        await self._dispatch_alert(alert)
                
                # Clean up old alerts
                await self._cleanup_old_alerts()
                
                await asyncio.sleep(10)  # Check alerts every 10 seconds
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(10)
    
    async def _record_metric(self, metric_name: str, value: float, threshold: float):
        """Record a health metric."""
        timestamp = datetime.utcnow()
        
        # Determine status
        if value > threshold:
            status = "CRITICAL" if value > threshold * 1.2 else "WARNING"
            alert_level = AlertLevel.CRITICAL if value > threshold * 1.2 else AlertLevel.WARNING
        else:
            status = "HEALTHY"
            alert_level = AlertLevel.INFO
        
        # Create metric
        metric = HealthMetric(
            name=metric_name,
            value=value,
            threshold=threshold,
            status=status,
            timestamp=timestamp,
            alert_level=alert_level
        )
        
        # Store metric
        self.health_metrics[metric_name] = metric
        
        # Store in history
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = []
        
        self.metric_history[metric_name].append(metric)
        
        # Keep only last 1000 entries
        if len(self.metric_history[metric_name]) > 1000:
            self.metric_history[metric_name] = self.metric_history[metric_name][-1000:]
        
        # Create alert if necessary
        if status in ["WARNING", "CRITICAL"]:
            await self._create_alert(
                alert_level,
                "SYSTEM",
                f"{metric_name} is {status}: {value:.2f} (threshold: {threshold:.2f})"
            )
    
    async def _create_alert(self, level: AlertLevel, component: str, message: str):
        """Create a new system alert."""
        alert_id = f"{component}_{int(time.time())}"
        
        alert = SystemAlert(
            alert_id=alert_id,
            alert_level=level,
            component=component,
            message=message,
            timestamp=datetime.utcnow()
        )
        
        # Add to active alerts
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        logger.warning(f"ALERT [{level.value}] {component}: {message}")
    
    async def _dispatch_alert(self, alert: SystemAlert):
        """Dispatch an alert through configured channels."""
        try:
            # Log alert
            if self.alert_channels.get("log", False):
                logger.critical(f"ALERT DISPATCH: [{alert.alert_level.value}] {alert.component}: {alert.message}")
            
            # Email alert (placeholder)
            if self.alert_channels.get("email", False):
                await self._send_email_alert(alert)
            
            # Webhook alert (placeholder)
            if self.alert_channels.get("webhook", False):
                await self._send_webhook_alert(alert)
            
            # SMS alert (placeholder)
            if self.alert_channels.get("sms", False):
                await self._send_sms_alert(alert)
            
            # Mark as acknowledged
            alert.acknowledged = True
            
        except Exception as e:
            logger.error(f"Alert dispatch error: {e}")
    
    async def _send_email_alert(self, alert: SystemAlert):
        """Send email alert (placeholder)."""
        # In a real implementation, this would send an actual email
        logger.info(f"EMAIL ALERT: {alert.message}")
    
    async def _send_webhook_alert(self, alert: SystemAlert):
        """Send webhook alert (placeholder)."""
        # In a real implementation, this would make an HTTP request
        logger.info(f"WEBHOOK ALERT: {alert.message}")
    
    async def _send_sms_alert(self, alert: SystemAlert):
        """Send SMS alert (placeholder)."""
        # In a real implementation, this would send an SMS
        logger.info(f"SMS ALERT: {alert.message}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Remove old active alerts
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp > cutoff_time or not alert.acknowledged
        ]
        
        # Keep only last 1000 alerts in history
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    async def _measure_system_response_time(self) -> float:
        """Measure system response time."""
        # Placeholder implementation
        return 0.1  # 100ms
    
    async def _calculate_error_rate(self) -> float:
        """Calculate system error rate."""
        # Placeholder implementation
        return 0.5  # 0.5% error rate
    
    async def _count_connection_failures(self) -> int:
        """Count connection failures."""
        # Placeholder implementation
        return 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current system health status.
        
        Returns:
            Dict[str, Any]: Complete health status
        """
        current_time = datetime.utcnow()
        
        # Calculate overall health score
        healthy_metrics = sum(1 for metric in self.health_metrics.values() if metric.status == "HEALTHY")
        total_metrics = len(self.health_metrics)
        health_score = (healthy_metrics / total_metrics * 100) if total_metrics > 0 else 100
        
        # Determine overall status
        if health_score >= 95:
            overall_status = "EXCELLENT"
        elif health_score >= 85:
            overall_status = "GOOD"
        elif health_score >= 70:
            overall_status = "FAIR"
        else:
            overall_status = "POOR"
        
        return {
            "timestamp": current_time,
            "overall_status": overall_status,
            "health_score": health_score,
            "is_monitoring": self.is_monitoring,
            "metrics": {
                name: {
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "status": metric.status,
                    "timestamp": metric.timestamp
                }
                for name, metric in self.health_metrics.items()
            },
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "critical_alerts": len([a for a in self.active_alerts if a.alert_level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in self.active_alerts if a.alert_level == AlertLevel.WARNING])
        }
    
    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get metric history for a specific metric.
        
        Args:
            metric_name: Name of the metric
            hours: Number of hours of history to return
            
        Returns:
            List[Dict[str, Any]]: Metric history
        """
        if metric_name not in self.metric_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            {
                "value": metric.value,
                "status": metric.status,
                "timestamp": metric.timestamp
            }
            for metric in self.metric_history[metric_name]
            if metric.timestamp > cutoff_time
        ]
    
    def get_alerts(self, hours: int = 24, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        """
        Get system alerts.
        
        Args:
            hours: Number of hours of alerts to return
            level: Filter by alert level
            
        Returns:
            List[Dict[str, Any]]: System alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        alerts = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]
        
        if level:
            alerts = [alert for alert in alerts if alert.alert_level == level]
        
        return [
            {
                "alert_id": alert.alert_id,
                "level": alert.alert_level.value,
                "component": alert.component,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "acknowledged": alert.acknowledged
            }
            for alert in alerts
        ]


# Health monitoring utilities
def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration to human-readable format."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.2f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.2f} hours"
    else:
        return f"{seconds/86400:.2f} days"

