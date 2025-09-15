"""
Protocol Escalation Manager

This module implements the main escalation manager that orchestrates
the 4-level protocol escalation system based on ATR breaches and
position performance.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio
from dataclasses import dataclass, asdict
import json

from .protocol_levels import ProtocolLevel, ProtocolState, ProtocolLevelManager
from .monitoring_system import MonitoringSystem
from .alert_system import AlertSystem
from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws2_protocol_engine.atr import ATRCalculationEngine

logger = logging.getLogger(__name__)


@dataclass
class PositionRiskMetrics:
    """Risk metrics for a position."""
    position_id: str
    symbol: str
    account_type: str
    entry_price: Decimal
    current_price: Decimal
    atr_value: Decimal
    atr_breach_multiple: float
    position_loss_pct: float
    time_in_breach: int  # seconds
    last_updated: datetime


@dataclass
class EscalationEvent:
    """Escalation event record."""
    event_id: str
    timestamp: datetime
    event_type: str  # 'escalation', 'de_escalation', 'breach_detected', 'breach_resolved'
    from_level: ProtocolLevel
    to_level: ProtocolLevel
    trigger_reason: str
    position_id: Optional[str]
    atr_breach_multiple: float
    position_loss_pct: float
    auto_actions_taken: List[str]
    metadata: Dict[str, Any]


class ProtocolEscalationManager:
    """
    Main Protocol Escalation Manager.
    
    Orchestrates the 4-level escalation system by:
    1. Monitoring position risk metrics
    2. Detecting ATR breaches and position losses
    3. Escalating/de-escalating protocol levels
    4. Triggering appropriate auto-actions
    5. Managing alerts and notifications
    """
    
    def __init__(self, 
                 atr_engine: ATRCalculationEngine,
                 audit_manager: AuditTrailManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Protocol Escalation Manager.
        
        Args:
            atr_engine: ATR calculation engine
            audit_manager: Audit trail manager
            config: Optional configuration
        """
        self.atr_engine = atr_engine
        self.audit_manager = audit_manager
        self.config = config or {}
        
        # Initialize components
        self.level_manager = ProtocolLevelManager()
        self.monitoring_system = MonitoringSystem()
        self.alert_system = AlertSystem()
        
        # State tracking
        self.active_positions = {}  # position_id -> PositionRiskMetrics
        self.breach_history = {}    # position_id -> List[datetime]
        self.escalation_events = [] # List[EscalationEvent]
        self.current_state = ProtocolState.ACTIVE
        
        # Configuration
        self.max_breach_history = self.config.get("max_breach_history", 100)
        self.breach_resolution_threshold = self.config.get("breach_resolution_threshold", 0.5)
        self.auto_actions_enabled = self.config.get("auto_actions_enabled", True)
        
        # Callbacks for auto-actions
        self.action_callbacks = {}
        
        logger.info("Protocol Escalation Manager initialized")
    
    def register_action_callback(self, action_name: str, callback: Callable):
        """
        Register callback for auto-actions.
        
        Args:
            action_name: Name of the action
            callback: Callback function to execute
        """
        self.action_callbacks[action_name] = callback
        logger.info(f"Registered action callback: {action_name}")
    
    def add_position_monitoring(self, 
                              position_id: str,
                              symbol: str,
                              account_type: str,
                              entry_price: Decimal) -> bool:
        """
        Add position to monitoring system.
        
        Args:
            position_id: Unique position identifier
            symbol: Trading symbol
            account_type: Account type (gen_acc, rev_acc, com_acc)
            entry_price: Position entry price
            
        Returns:
            True if position added successfully
        """
        try:
            # Get current ATR for the symbol
            atr_result = self.atr_engine.calculate_atr(symbol)
            
            if not atr_result.get("success"):
                logger.error(f"Failed to get ATR for {symbol}: {atr_result.get('error')}")
                return False
            
            atr_value = Decimal(str(atr_result["atr"]))
            
            # Create risk metrics
            risk_metrics = PositionRiskMetrics(
                position_id=position_id,
                symbol=symbol,
                account_type=account_type,
                entry_price=entry_price,
                current_price=entry_price,  # Initialize with entry price
                atr_value=atr_value,
                atr_breach_multiple=0.0,
                position_loss_pct=0.0,
                time_in_breach=0,
                last_updated=datetime.now()
            )
            
            self.active_positions[position_id] = risk_metrics
            self.breach_history[position_id] = []
            
            logger.info(f"Added position {position_id} to monitoring: {symbol} @ {entry_price}")
            
            # Log to audit trail
            self.audit_manager.log_system_event(
                event_type="position_monitoring_started",
                event_data={
                    "position_id": position_id,
                    "symbol": symbol,
                    "account_type": account_type,
                    "entry_price": float(entry_price),
                    "atr_value": float(atr_value)
                },
                severity="info"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding position monitoring for {position_id}: {str(e)}", exc_info=True)
            return False
    
    def update_position_price(self, position_id: str, current_price: Decimal) -> Dict[str, Any]:
        """
        Update position price and check for escalation conditions.
        
        Args:
            position_id: Position identifier
            current_price: Current market price
            
        Returns:
            Update result with escalation information
        """
        try:
            if position_id not in self.active_positions:
                return {
                    "success": False,
                    "error": f"Position {position_id} not found in monitoring system"
                }
            
            risk_metrics = self.active_positions[position_id]
            
            # Update price and calculate metrics
            risk_metrics.current_price = current_price
            risk_metrics.last_updated = datetime.now()
            
            # Calculate position loss percentage
            price_change = current_price - risk_metrics.entry_price
            risk_metrics.position_loss_pct = float(abs(price_change) / risk_metrics.entry_price * 100)
            
            # Calculate ATR breach multiple
            price_move_abs = abs(price_change)
            risk_metrics.atr_breach_multiple = float(price_move_abs / risk_metrics.atr_value)
            
            # Check for breach conditions
            breach_detected = self._check_breach_conditions(risk_metrics)
            
            result = {
                "success": True,
                "position_id": position_id,
                "current_price": float(current_price),
                "position_loss_pct": risk_metrics.position_loss_pct,
                "atr_breach_multiple": risk_metrics.atr_breach_multiple,
                "breach_detected": breach_detected,
                "current_protocol_level": self.level_manager.current_level.name,
                "timestamp": datetime.now().isoformat()
            }
            
            # Handle breach detection
            if breach_detected:
                escalation_result = self._handle_breach_detection(risk_metrics)
                result.update(escalation_result)
            else:
                # Check for de-escalation opportunity
                de_escalation_result = self._check_de_escalation(risk_metrics)
                result.update(de_escalation_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating position price for {position_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "position_id": position_id
            }
    
    def _check_breach_conditions(self, risk_metrics: PositionRiskMetrics) -> bool:
        """Check if position has breach conditions."""
        current_config = self.level_manager.get_current_level_config()
        
        # Check ATR breach
        atr_breach = risk_metrics.atr_breach_multiple >= 1.0
        
        # Check position loss breach
        loss_breach = risk_metrics.position_loss_pct >= current_config.max_position_loss_pct
        
        return atr_breach or loss_breach
    
    def _handle_breach_detection(self, risk_metrics: PositionRiskMetrics) -> Dict[str, Any]:
        """Handle breach detection and potential escalation."""
        try:
            position_id = risk_metrics.position_id
            
            # Update breach history
            now = datetime.now()
            self.breach_history[position_id].append(now)
            
            # Calculate time in breach
            if len(self.breach_history[position_id]) > 1:
                first_breach = self.breach_history[position_id][0]
                risk_metrics.time_in_breach = int((now - first_breach).total_seconds())
            else:
                risk_metrics.time_in_breach = 0
            
            # Check if escalation is needed
            target_level = self.level_manager.should_escalate(
                atr_breach_multiple=risk_metrics.atr_breach_multiple,
                position_loss_pct=risk_metrics.position_loss_pct,
                time_in_breach=risk_metrics.time_in_breach
            )
            
            result = {
                "breach_handling": "detected",
                "time_in_breach": risk_metrics.time_in_breach,
                "escalation_needed": target_level is not None
            }
            
            if target_level:
                escalation_success = self._execute_escalation(risk_metrics, target_level)
                result["escalation_executed"] = escalation_success
                result["new_protocol_level"] = target_level.name if escalation_success else None
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling breach detection: {str(e)}", exc_info=True)
            return {"breach_handling": "error", "error": str(e)}
    
    def _check_de_escalation(self, risk_metrics: PositionRiskMetrics) -> Dict[str, Any]:
        """Check for de-escalation opportunities."""
        try:
            position_id = risk_metrics.position_id
            
            # Check if breach has been resolved
            breach_resolved = not self._check_breach_conditions(risk_metrics)
            
            if not breach_resolved:
                return {"de_escalation_check": "breach_still_active"}
            
            # Calculate time since breach resolved
            if position_id in self.breach_history and self.breach_history[position_id]:
                last_breach = self.breach_history[position_id][-1]
                time_since_resolved = int((datetime.now() - last_breach).total_seconds())
                
                # Clear breach history if resolved for sufficient time
                current_config = self.level_manager.get_current_level_config()
                if time_since_resolved > current_config.de_escalation_delay:
                    self.breach_history[position_id] = []
                    risk_metrics.time_in_breach = 0
            else:
                time_since_resolved = 0
            
            # Check if de-escalation is appropriate
            target_level = self.level_manager.should_de_escalate(
                atr_breach_multiple=risk_metrics.atr_breach_multiple,
                position_loss_pct=risk_metrics.position_loss_pct,
                time_since_breach_resolved=time_since_resolved
            )
            
            result = {
                "de_escalation_check": "completed",
                "breach_resolved": breach_resolved,
                "time_since_resolved": time_since_resolved,
                "de_escalation_needed": target_level is not None
            }
            
            if target_level:
                de_escalation_success = self._execute_de_escalation(target_level)
                result["de_escalation_executed"] = de_escalation_success
                result["new_protocol_level"] = target_level.name if de_escalation_success else None
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking de-escalation: {str(e)}", exc_info=True)
            return {"de_escalation_check": "error", "error": str(e)}
    
    def _execute_escalation(self, risk_metrics: PositionRiskMetrics, target_level: ProtocolLevel) -> bool:
        """Execute protocol escalation."""
        try:
            previous_level = self.level_manager.current_level
            
            # Perform escalation
            escalation_success = self.level_manager.escalate_to_level(target_level)
            
            if not escalation_success:
                return False
            
            # Get new level configuration
            new_config = self.level_manager.get_current_level_config()
            
            # Execute auto-actions
            auto_actions_taken = []
            if self.auto_actions_enabled:
                auto_actions_taken = self._execute_auto_actions(new_config.auto_actions, risk_metrics)
            
            # Create escalation event
            event = EscalationEvent(
                event_id=f"escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{risk_metrics.position_id}",
                timestamp=datetime.now(),
                event_type="escalation",
                from_level=previous_level,
                to_level=target_level,
                trigger_reason=f"ATR breach: {risk_metrics.atr_breach_multiple:.2f}x, Loss: {risk_metrics.position_loss_pct:.2f}%",
                position_id=risk_metrics.position_id,
                atr_breach_multiple=risk_metrics.atr_breach_multiple,
                position_loss_pct=risk_metrics.position_loss_pct,
                auto_actions_taken=auto_actions_taken,
                metadata=asdict(risk_metrics)
            )
            
            self.escalation_events.append(event)
            
            # Send alerts
            self.alert_system.send_escalation_alert(event)
            
            # Log to audit trail
            self.audit_manager.log_system_event(
                event_type="protocol_escalation",
                event_data=asdict(event),
                severity="warning" if target_level.value < 3 else "critical"
            )
            
            logger.warning(f"Protocol escalated to {target_level.name} due to {event.trigger_reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing escalation: {str(e)}", exc_info=True)
            return False
    
    def _execute_de_escalation(self, target_level: ProtocolLevel) -> bool:
        """Execute protocol de-escalation."""
        try:
            previous_level = self.level_manager.current_level
            
            # Perform de-escalation
            de_escalation_success = self.level_manager.de_escalate_to_level(target_level)
            
            if not de_escalation_success:
                return False
            
            # Create de-escalation event
            event = EscalationEvent(
                event_id=f"de_escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                event_type="de_escalation",
                from_level=previous_level,
                to_level=target_level,
                trigger_reason="Breach conditions resolved",
                position_id=None,
                atr_breach_multiple=0.0,
                position_loss_pct=0.0,
                auto_actions_taken=[],
                metadata={}
            )
            
            self.escalation_events.append(event)
            
            # Send alerts
            self.alert_system.send_de_escalation_alert(event)
            
            # Log to audit trail
            self.audit_manager.log_system_event(
                event_type="protocol_de_escalation",
                event_data=asdict(event),
                severity="info"
            )
            
            logger.info(f"Protocol de-escalated to {target_level.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing de-escalation: {str(e)}", exc_info=True)
            return False
    
    def _execute_auto_actions(self, auto_actions: Dict[str, bool], risk_metrics: PositionRiskMetrics) -> List[str]:
        """Execute auto-actions based on protocol level."""
        actions_taken = []
        
        try:
            for action_name, enabled in auto_actions.items():
                if not enabled:
                    continue
                
                if action_name in self.action_callbacks:
                    try:
                        callback = self.action_callbacks[action_name]
                        callback_result = callback(risk_metrics)
                        
                        if callback_result.get("success", False):
                            actions_taken.append(action_name)
                            logger.info(f"Auto-action executed: {action_name}")
                        else:
                            logger.warning(f"Auto-action failed: {action_name} - {callback_result.get('error')}")
                    
                    except Exception as e:
                        logger.error(f"Error executing auto-action {action_name}: {str(e)}")
                else:
                    logger.warning(f"No callback registered for auto-action: {action_name}")
        
        except Exception as e:
            logger.error(f"Error executing auto-actions: {str(e)}", exc_info=True)
        
        return actions_taken
    
    def remove_position_monitoring(self, position_id: str) -> bool:
        """Remove position from monitoring system."""
        try:
            if position_id in self.active_positions:
                del self.active_positions[position_id]
                
            if position_id in self.breach_history:
                del self.breach_history[position_id]
            
            logger.info(f"Removed position {position_id} from monitoring")
            
            # Log to audit trail
            self.audit_manager.log_system_event(
                event_type="position_monitoring_stopped",
                event_data={"position_id": position_id},
                severity="info"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing position monitoring for {position_id}: {str(e)}")
            return False
    
    def get_escalation_status(self) -> Dict[str, Any]:
        """Get current escalation system status."""
        try:
            current_config = self.level_manager.get_current_level_config()
            
            # Calculate system-wide risk metrics
            total_positions = len(self.active_positions)
            positions_in_breach = sum(
                1 for metrics in self.active_positions.values()
                if self._check_breach_conditions(metrics)
            )
            
            avg_atr_breach = 0.0
            avg_position_loss = 0.0
            
            if self.active_positions:
                avg_atr_breach = sum(m.atr_breach_multiple for m in self.active_positions.values()) / total_positions
                avg_position_loss = sum(m.position_loss_pct for m in self.active_positions.values()) / total_positions
            
            return {
                "current_protocol_level": self.level_manager.current_level.name,
                "current_protocol_level_value": self.level_manager.current_level.value,
                "current_state": self.current_state.value,
                "monitoring_frequency": current_config.monitoring_frequency,
                "positions_monitored": total_positions,
                "positions_in_breach": positions_in_breach,
                "breach_percentage": (positions_in_breach / total_positions * 100) if total_positions > 0 else 0,
                "avg_atr_breach_multiple": avg_atr_breach,
                "avg_position_loss_pct": avg_position_loss,
                "escalation_events_today": len([
                    e for e in self.escalation_events
                    if e.timestamp.date() == datetime.now().date()
                ]),
                "last_escalation_time": self.level_manager.last_escalation_time.isoformat() if self.level_manager.last_escalation_time else None,
                "auto_actions_enabled": self.auto_actions_enabled,
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting escalation status: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }
    
    def get_position_risk_summary(self) -> Dict[str, Any]:
        """Get summary of all monitored positions."""
        try:
            position_summaries = {}
            
            for position_id, metrics in self.active_positions.items():
                position_summaries[position_id] = {
                    "symbol": metrics.symbol,
                    "account_type": metrics.account_type,
                    "entry_price": float(metrics.entry_price),
                    "current_price": float(metrics.current_price),
                    "position_loss_pct": metrics.position_loss_pct,
                    "atr_breach_multiple": metrics.atr_breach_multiple,
                    "time_in_breach": metrics.time_in_breach,
                    "breach_detected": self._check_breach_conditions(metrics),
                    "last_updated": metrics.last_updated.isoformat()
                }
            
            return {
                "position_summaries": position_summaries,
                "total_positions": len(position_summaries),
                "summary_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting position risk summary: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "summary_timestamp": datetime.now().isoformat()
            }

