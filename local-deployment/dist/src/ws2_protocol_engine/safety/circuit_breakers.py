"""
Circuit Breaker System

This module implements circuit breakers that automatically halt trading
when extreme market conditions or system anomalies are detected.
"""

from typing import Dict, Any, Optional, List, Callable
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class CircuitBreakerType(Enum):
    """Types of circuit breakers."""
    PORTFOLIO_LOSS = "portfolio_loss"
    POSITION_LOSS = "position_loss"
    VOLATILITY_SPIKE = "volatility_spike"
    VOLUME_ANOMALY = "volume_anomaly"
    SYSTEM_ERROR = "system_error"
    MARKET_HALT = "market_halt"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"


class CircuitBreakerStatus(Enum):
    """Circuit breaker status states."""
    ARMED = "armed"
    TRIGGERED = "triggered"
    COOLING_DOWN = "cooling_down"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""
    breaker_type: CircuitBreakerType
    name: str
    description: str
    threshold: Decimal
    lookback_period: int  # seconds
    cooldown_period: int  # seconds
    auto_reset: bool
    severity: str  # "low", "medium", "high", "critical"
    enabled: bool = True


@dataclass
class CircuitBreakerEvent:
    """Circuit breaker trigger event."""
    event_id: str
    timestamp: datetime
    breaker_type: CircuitBreakerType
    breaker_name: str
    trigger_value: Decimal
    threshold: Decimal
    severity: str
    description: str
    auto_actions_taken: List[str]
    metadata: Dict[str, Any]


class CircuitBreakerSystem:
    """
    Comprehensive circuit breaker system for trading protection.
    
    Monitors various market and system conditions and automatically
    halts trading when dangerous conditions are detected.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize circuit breaker system.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        
        # Circuit breaker configurations
        self.breakers = self._initialize_circuit_breakers()
        
        # State tracking
        self.breaker_states = {}  # breaker_type -> CircuitBreakerStatus
        self.trigger_history = []  # List[CircuitBreakerEvent]
        self.last_trigger_times = {}  # breaker_type -> datetime
        self.cooldown_timers = {}  # breaker_type -> datetime
        
        # Monitoring data
        self.monitoring_data = {}  # breaker_type -> List[data_points]
        self.max_history_points = self.config.get("max_history_points", 1000)
        
        # Action callbacks
        self.action_callbacks = {}  # action_name -> Callable
        
        # Initialize all breakers as armed
        for breaker_type in self.breakers:
            self.breaker_states[breaker_type] = CircuitBreakerStatus.ARMED
        
        logger.info("Circuit Breaker System initialized with {} breakers".format(len(self.breakers)))
    
    def _initialize_circuit_breakers(self) -> Dict[CircuitBreakerType, CircuitBreakerConfig]:
        """Initialize circuit breaker configurations."""
        return {
            CircuitBreakerType.PORTFOLIO_LOSS: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.PORTFOLIO_LOSS,
                name="Portfolio Loss Limit",
                description="Triggers when portfolio loss exceeds threshold",
                threshold=Decimal("0.05"),  # 5% portfolio loss
                lookback_period=300,  # 5 minutes
                cooldown_period=1800,  # 30 minutes
                auto_reset=False,
                severity="critical"
            ),
            
            CircuitBreakerType.POSITION_LOSS: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.POSITION_LOSS,
                name="Individual Position Loss",
                description="Triggers when single position loss exceeds threshold",
                threshold=Decimal("0.10"),  # 10% position loss
                lookback_period=60,  # 1 minute
                cooldown_period=600,  # 10 minutes
                auto_reset=True,
                severity="high"
            ),
            
            CircuitBreakerType.VOLATILITY_SPIKE: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.VOLATILITY_SPIKE,
                name="Volatility Spike",
                description="Triggers on extreme volatility increases",
                threshold=Decimal("2.0"),  # 2x normal volatility
                lookback_period=180,  # 3 minutes
                cooldown_period=900,  # 15 minutes
                auto_reset=True,
                severity="high"
            ),
            
            CircuitBreakerType.VOLUME_ANOMALY: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.VOLUME_ANOMALY,
                name="Volume Anomaly",
                description="Triggers on unusual volume patterns",
                threshold=Decimal("5.0"),  # 5x normal volume
                lookback_period=120,  # 2 minutes
                cooldown_period=600,  # 10 minutes
                auto_reset=True,
                severity="medium"
            ),
            
            CircuitBreakerType.SYSTEM_ERROR: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.SYSTEM_ERROR,
                name="System Error Rate",
                description="Triggers on high system error rates",
                threshold=Decimal("0.10"),  # 10% error rate
                lookback_period=300,  # 5 minutes
                cooldown_period=1800,  # 30 minutes
                auto_reset=False,
                severity="critical"
            ),
            
            CircuitBreakerType.LIQUIDITY_CRISIS: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.LIQUIDITY_CRISIS,
                name="Liquidity Crisis",
                description="Triggers when market liquidity drops severely",
                threshold=Decimal("0.50"),  # 50% liquidity reduction
                lookback_period=600,  # 10 minutes
                cooldown_period=1800,  # 30 minutes
                auto_reset=False,
                severity="critical"
            ),
            
            CircuitBreakerType.CORRELATION_BREAKDOWN: CircuitBreakerConfig(
                breaker_type=CircuitBreakerType.CORRELATION_BREAKDOWN,
                name="Correlation Breakdown",
                description="Triggers when asset correlations break down",
                threshold=Decimal("0.30"),  # 30% correlation drop
                lookback_period=900,  # 15 minutes
                cooldown_period=1800,  # 30 minutes
                auto_reset=True,
                severity="high"
            )
        }
    
    def register_action_callback(self, action_name: str, callback: Callable):
        """Register callback for circuit breaker actions."""
        self.action_callbacks[action_name] = callback
        logger.info(f"Registered circuit breaker action callback: {action_name}")
    
    def update_monitoring_data(self, 
                             breaker_type: CircuitBreakerType,
                             value: Decimal,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update monitoring data and check for circuit breaker triggers.
        
        Args:
            breaker_type: Type of circuit breaker
            value: Current monitoring value
            metadata: Optional metadata
            
        Returns:
            Update result with trigger information
        """
        try:
            if breaker_type not in self.breakers:
                return {
                    "success": False,
                    "error": f"Unknown circuit breaker type: {breaker_type}"
                }
            
            # Add data point
            if breaker_type not in self.monitoring_data:
                self.monitoring_data[breaker_type] = []
            
            data_point = {
                "timestamp": datetime.now(),
                "value": value,
                "metadata": metadata or {}
            }
            
            self.monitoring_data[breaker_type].append(data_point)
            
            # Trim history if needed
            if len(self.monitoring_data[breaker_type]) > self.max_history_points:
                self.monitoring_data[breaker_type] = self.monitoring_data[breaker_type][-self.max_history_points:]
            
            # Check for trigger
            trigger_result = self._check_circuit_breaker_trigger(breaker_type, value, metadata)
            
            return {
                "success": True,
                "breaker_type": breaker_type.value,
                "current_value": float(value),
                "trigger_result": trigger_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating monitoring data for {breaker_type}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "breaker_type": breaker_type.value if breaker_type else "unknown"
            }
    
    def _check_circuit_breaker_trigger(self, 
                                     breaker_type: CircuitBreakerType,
                                     current_value: Decimal,
                                     metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if circuit breaker should trigger."""
        try:
            breaker_config = self.breakers[breaker_type]
            current_status = self.breaker_states.get(breaker_type, CircuitBreakerStatus.ARMED)
            
            # Skip if breaker is not armed
            if current_status != CircuitBreakerStatus.ARMED:
                return {
                    "triggered": False,
                    "reason": f"Breaker status is {current_status.value}",
                    "current_status": current_status.value
                }
            
            # Skip if breaker is disabled
            if not breaker_config.enabled:
                return {
                    "triggered": False,
                    "reason": "Breaker is disabled",
                    "current_status": current_status.value
                }
            
            # Check cooldown period
            if breaker_type in self.cooldown_timers:
                cooldown_end = self.cooldown_timers[breaker_type]
                if datetime.now() < cooldown_end:
                    return {
                        "triggered": False,
                        "reason": "Breaker in cooldown period",
                        "cooldown_ends": cooldown_end.isoformat()
                    }
            
            # Check threshold breach
            threshold_breached = self._evaluate_threshold_breach(breaker_type, current_value)
            
            if threshold_breached:
                # Trigger circuit breaker
                trigger_event = self._trigger_circuit_breaker(breaker_type, current_value, metadata)
                
                return {
                    "triggered": True,
                    "trigger_event": asdict(trigger_event),
                    "new_status": self.breaker_states[breaker_type].value
                }
            else:
                return {
                    "triggered": False,
                    "reason": "Threshold not breached",
                    "current_value": float(current_value),
                    "threshold": float(breaker_config.threshold)
                }
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker trigger: {str(e)}", exc_info=True)
            return {
                "triggered": False,
                "reason": f"Error in trigger check: {str(e)}"
            }
    
    def _evaluate_threshold_breach(self, breaker_type: CircuitBreakerType, current_value: Decimal) -> bool:
        """Evaluate if threshold has been breached."""
        try:
            breaker_config = self.breakers[breaker_type]
            threshold = breaker_config.threshold
            
            # Different evaluation logic based on breaker type
            if breaker_type in [CircuitBreakerType.PORTFOLIO_LOSS, CircuitBreakerType.POSITION_LOSS]:
                # Loss breakers: trigger if loss exceeds threshold
                return current_value >= threshold
            
            elif breaker_type in [CircuitBreakerType.VOLATILITY_SPIKE, CircuitBreakerType.VOLUME_ANOMALY]:
                # Spike breakers: trigger if value exceeds threshold multiplier
                return current_value >= threshold
            
            elif breaker_type == CircuitBreakerType.SYSTEM_ERROR:
                # Error rate breaker: trigger if error rate exceeds threshold
                return current_value >= threshold
            
            elif breaker_type == CircuitBreakerType.LIQUIDITY_CRISIS:
                # Liquidity breaker: trigger if liquidity drops below threshold
                return current_value <= threshold
            
            elif breaker_type == CircuitBreakerType.CORRELATION_BREAKDOWN:
                # Correlation breaker: trigger if correlation drops below threshold
                return current_value <= threshold
            
            else:
                # Default: simple threshold comparison
                return current_value >= threshold
            
        except Exception as e:
            logger.error(f"Error evaluating threshold breach: {str(e)}")
            return False
    
    def _trigger_circuit_breaker(self, 
                               breaker_type: CircuitBreakerType,
                               trigger_value: Decimal,
                               metadata: Optional[Dict[str, Any]]) -> CircuitBreakerEvent:
        """Trigger a circuit breaker."""
        try:
            breaker_config = self.breakers[breaker_type]
            
            # Create trigger event
            event = CircuitBreakerEvent(
                event_id=f"cb_{breaker_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                breaker_type=breaker_type,
                breaker_name=breaker_config.name,
                trigger_value=trigger_value,
                threshold=breaker_config.threshold,
                severity=breaker_config.severity,
                description=f"{breaker_config.description} - Triggered at {float(trigger_value)}",
                auto_actions_taken=[],
                metadata=metadata or {}
            )
            
            # Update breaker state
            self.breaker_states[breaker_type] = CircuitBreakerStatus.TRIGGERED
            self.last_trigger_times[breaker_type] = datetime.now()
            
            # Set cooldown timer
            cooldown_end = datetime.now() + timedelta(seconds=breaker_config.cooldown_period)
            self.cooldown_timers[breaker_type] = cooldown_end
            
            # Execute auto-actions
            auto_actions = self._execute_circuit_breaker_actions(breaker_type, event)
            event.auto_actions_taken = auto_actions
            
            # Add to trigger history
            self.trigger_history.append(event)
            
            # Trim trigger history
            if len(self.trigger_history) > 100:
                self.trigger_history = self.trigger_history[-100:]
            
            logger.critical(f"CIRCUIT BREAKER TRIGGERED: {breaker_config.name} - {event.description}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error triggering circuit breaker: {str(e)}", exc_info=True)
            raise
    
    def _execute_circuit_breaker_actions(self, 
                                       breaker_type: CircuitBreakerType,
                                       event: CircuitBreakerEvent) -> List[str]:
        """Execute automatic actions for circuit breaker trigger."""
        actions_taken = []
        
        try:
            # Define actions based on breaker type and severity
            action_map = {
                CircuitBreakerType.PORTFOLIO_LOSS: ["halt_all_trading", "close_risky_positions", "send_emergency_alert"],
                CircuitBreakerType.POSITION_LOSS: ["close_position", "reduce_position_size", "send_alert"],
                CircuitBreakerType.VOLATILITY_SPIKE: ["reduce_position_sizes", "increase_monitoring", "send_alert"],
                CircuitBreakerType.VOLUME_ANOMALY: ["pause_new_orders", "increase_monitoring", "send_alert"],
                CircuitBreakerType.SYSTEM_ERROR: ["halt_all_trading", "system_diagnostics", "send_emergency_alert"],
                CircuitBreakerType.LIQUIDITY_CRISIS: ["halt_all_trading", "close_illiquid_positions", "send_emergency_alert"],
                CircuitBreakerType.CORRELATION_BREAKDOWN: ["reduce_correlated_positions", "increase_monitoring", "send_alert"]
            }
            
            actions = action_map.get(breaker_type, ["send_alert"])
            
            for action in actions:
                if action in self.action_callbacks:
                    try:
                        callback_result = self.action_callbacks[action](event)
                        if callback_result.get("success", False):
                            actions_taken.append(action)
                            logger.info(f"Circuit breaker action executed: {action}")
                        else:
                            logger.warning(f"Circuit breaker action failed: {action} - {callback_result.get('error')}")
                    except Exception as e:
                        logger.error(f"Error executing circuit breaker action {action}: {str(e)}")
                else:
                    logger.warning(f"No callback registered for circuit breaker action: {action}")
            
        except Exception as e:
            logger.error(f"Error executing circuit breaker actions: {str(e)}", exc_info=True)
        
        return actions_taken
    
    def reset_circuit_breaker(self, breaker_type: CircuitBreakerType, force: bool = False) -> bool:
        """
        Reset a circuit breaker.
        
        Args:
            breaker_type: Type of circuit breaker to reset
            force: Force reset even if in cooldown
            
        Returns:
            True if reset successful
        """
        try:
            if breaker_type not in self.breakers:
                logger.warning(f"Unknown circuit breaker type: {breaker_type}")
                return False
            
            current_status = self.breaker_states.get(breaker_type, CircuitBreakerStatus.ARMED)
            
            # Check if reset is allowed
            if not force:
                if breaker_type in self.cooldown_timers:
                    cooldown_end = self.cooldown_timers[breaker_type]
                    if datetime.now() < cooldown_end:
                        logger.warning(f"Cannot reset {breaker_type.value}: still in cooldown until {cooldown_end}")
                        return False
            
            # Reset breaker
            self.breaker_states[breaker_type] = CircuitBreakerStatus.ARMED
            
            # Clear cooldown timer
            if breaker_type in self.cooldown_timers:
                del self.cooldown_timers[breaker_type]
            
            logger.info(f"Circuit breaker reset: {breaker_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting circuit breaker {breaker_type}: {str(e)}", exc_info=True)
            return False
    
    def enable_circuit_breaker(self, breaker_type: CircuitBreakerType) -> bool:
        """Enable a circuit breaker."""
        try:
            if breaker_type not in self.breakers:
                return False
            
            self.breakers[breaker_type].enabled = True
            logger.info(f"Circuit breaker enabled: {breaker_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling circuit breaker {breaker_type}: {str(e)}")
            return False
    
    def disable_circuit_breaker(self, breaker_type: CircuitBreakerType) -> bool:
        """Disable a circuit breaker."""
        try:
            if breaker_type not in self.breakers:
                return False
            
            self.breakers[breaker_type].enabled = False
            logger.info(f"Circuit breaker disabled: {breaker_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling circuit breaker {breaker_type}: {str(e)}")
            return False
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers."""
        try:
            breaker_status = {}
            
            for breaker_type, config in self.breakers.items():
                current_status = self.breaker_states.get(breaker_type, CircuitBreakerStatus.ARMED)
                last_trigger = self.last_trigger_times.get(breaker_type)
                cooldown_end = self.cooldown_timers.get(breaker_type)
                
                # Get recent monitoring data
                recent_data = []
                if breaker_type in self.monitoring_data:
                    recent_data = self.monitoring_data[breaker_type][-10:]  # Last 10 data points
                
                breaker_status[breaker_type.value] = {
                    "name": config.name,
                    "description": config.description,
                    "enabled": config.enabled,
                    "status": current_status.value,
                    "threshold": float(config.threshold),
                    "severity": config.severity,
                    "last_trigger": last_trigger.isoformat() if last_trigger else None,
                    "cooldown_ends": cooldown_end.isoformat() if cooldown_end else None,
                    "recent_values": [
                        {
                            "timestamp": dp["timestamp"].isoformat(),
                            "value": float(dp["value"])
                        }
                        for dp in recent_data
                    ]
                }
            
            # Overall system status
            any_triggered = any(status == CircuitBreakerStatus.TRIGGERED for status in self.breaker_states.values())
            critical_triggered = any(
                status == CircuitBreakerStatus.TRIGGERED and self.breakers[breaker_type].severity == "critical"
                for breaker_type, status in self.breaker_states.items()
            )
            
            overall_status = "critical" if critical_triggered else "warning" if any_triggered else "normal"
            
            return {
                "overall_status": overall_status,
                "total_breakers": len(self.breakers),
                "armed_breakers": sum(1 for s in self.breaker_states.values() if s == CircuitBreakerStatus.ARMED),
                "triggered_breakers": sum(1 for s in self.breaker_states.values() if s == CircuitBreakerStatus.TRIGGERED),
                "disabled_breakers": sum(1 for c in self.breakers.values() if not c.enabled),
                "breaker_details": breaker_status,
                "recent_triggers": len([e for e in self.trigger_history if (datetime.now() - e.timestamp).total_seconds() < 3600]),  # Last hour
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting circuit breaker status: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }
    
    def get_trigger_history(self, hours: int = 24) -> Dict[str, Any]:
        """Get circuit breaker trigger history."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_triggers = [
                event for event in self.trigger_history
                if event.timestamp >= cutoff_time
            ]
            
            # Group by breaker type
            triggers_by_type = {}
            for event in recent_triggers:
                breaker_type = event.breaker_type.value
                if breaker_type not in triggers_by_type:
                    triggers_by_type[breaker_type] = []
                triggers_by_type[breaker_type].append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "trigger_value": float(event.trigger_value),
                    "threshold": float(event.threshold),
                    "severity": event.severity,
                    "description": event.description,
                    "actions_taken": event.auto_actions_taken
                })
            
            return {
                "total_triggers": len(recent_triggers),
                "triggers_by_type": triggers_by_type,
                "analysis_period_hours": hours,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trigger history: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }

