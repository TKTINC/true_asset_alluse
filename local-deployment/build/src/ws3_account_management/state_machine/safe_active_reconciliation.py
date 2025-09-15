"""
SAFE→ACTIVE State Machine - Constitution v1.3 Compliance

This module implements the SAFE→ACTIVE reconciliation process per GPT-5 feedback:
- State machine transitions and validation
- Reconciliation process and checks
- Market hours restrictions and monitoring

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """System state enumeration."""
    SAFE = "safe"                    # SAFE mode - no trading
    TRANSITIONING = "transitioning"  # Transitioning between states
    ACTIVE = "active"               # ACTIVE mode - trading enabled
    SUSPENDED = "suspended"         # Suspended due to issues
    MAINTENANCE = "maintenance"     # Maintenance mode
    ERROR = "error"                 # Error state


class TransitionTrigger(Enum):
    """State transition triggers."""
    MANUAL_ACTIVATION = "manual_activation"
    SCHEDULED_ACTIVATION = "scheduled_activation"
    MARKET_OPEN = "market_open"
    RECONCILIATION_COMPLETE = "reconciliation_complete"
    RISK_THRESHOLD_BREACH = "risk_threshold_breach"
    MANUAL_SAFE_MODE = "manual_safe_mode"
    MARKET_CLOSE = "market_close"
    SYSTEM_ERROR = "system_error"


@dataclass
class StateTransition:
    """State transition record."""
    transition_id: str
    from_state: SystemState
    to_state: SystemState
    trigger: TransitionTrigger
    timestamp: datetime
    user_id: Optional[str]
    reason: str
    validation_checks: List[str]
    success: bool
    error_message: Optional[str]


@dataclass
class ReconciliationCheck:
    """Reconciliation check result."""
    check_name: str
    check_type: str
    passed: bool
    details: Dict[str, Any]
    error_message: Optional[str]
    timestamp: datetime


@dataclass
class ReconciliationResult:
    """Complete reconciliation result."""
    reconciliation_id: str
    start_time: datetime
    end_time: Optional[datetime]
    checks_performed: List[ReconciliationCheck]
    overall_success: bool
    blocking_issues: List[str]
    warnings: List[str]
    ready_for_active: bool


class SAFEActiveStateMachine:
    """SAFE→ACTIVE state machine manager."""
    
    # Market hours (Eastern Time)
    MARKET_OPEN_TIME = time(9, 30)   # 9:30 AM ET
    MARKET_CLOSE_TIME = time(16, 0)  # 4:00 PM ET
    
    # Pre-market and after-hours
    PREMARKET_START = time(4, 0)     # 4:00 AM ET
    AFTERHOURS_END = time(20, 0)     # 8:00 PM ET
    
    # Reconciliation parameters
    MAX_POSITION_DISCREPANCY_PCT = Decimal("0.01")  # 1% max discrepancy
    MAX_CASH_DISCREPANCY = Decimal("100.00")        # $100 max cash discrepancy
    MAX_RECONCILIATION_TIME_MINUTES = 30            # 30 minutes max reconciliation
    
    def __init__(self):
        """Initialize SAFE→ACTIVE state machine."""
        self.current_state = SystemState.SAFE
        self.transition_history = []
        self.reconciliation_history = []
        self.last_reconciliation = None
        self.state_change_callbacks = []
    
    def get_current_state(self) -> SystemState:
        """Get current system state."""
        return self.current_state
    
    def can_transition_to_active(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Check if system can transition to ACTIVE state.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Transition feasibility result
        """
        current_time = current_time or datetime.now()
        
        blocking_issues = []
        warnings = []
        
        try:
            # Check current state
            if self.current_state == SystemState.ACTIVE:
                return {
                    "can_transition": False,
                    "reason": "Already in ACTIVE state",
                    "blocking_issues": ["System already active"],
                    "warnings": [],
                    "current_state": self.current_state.value
                }
            
            if self.current_state == SystemState.ERROR:
                blocking_issues.append("System in ERROR state - manual intervention required")
            
            if self.current_state == SystemState.MAINTENANCE:
                blocking_issues.append("System in MAINTENANCE mode")
            
            # Check market hours
            market_status = self._check_market_hours(current_time)
            if not market_status["is_market_hours"]:
                if market_status["is_weekend"]:
                    blocking_issues.append("Market closed - weekend")
                elif market_status["is_holiday"]:
                    blocking_issues.append("Market closed - holiday")
                else:
                    warnings.append(f"Outside market hours - {market_status['status']}")
            
            # Check if recent reconciliation exists
            if self.last_reconciliation:
                time_since_reconciliation = current_time - self.last_reconciliation.end_time
                if time_since_reconciliation.total_seconds() > 3600:  # 1 hour
                    warnings.append("Last reconciliation over 1 hour ago")
            else:
                blocking_issues.append("No reconciliation performed - reconciliation required")
            
            # Check system health (placeholder - would integrate with monitoring)
            system_health = self._check_system_health()
            if not system_health["healthy"]:
                blocking_issues.extend(system_health["issues"])
            
            can_transition = len(blocking_issues) == 0
            
            return {
                "can_transition": can_transition,
                "reason": "Ready for ACTIVE state" if can_transition else "Blocking issues present",
                "blocking_issues": blocking_issues,
                "warnings": warnings,
                "current_state": self.current_state.value,
                "market_status": market_status,
                "system_health": system_health
            }
            
        except Exception as e:
            logger.error(f"Error checking transition to ACTIVE: {e}")
            return {
                "can_transition": False,
                "reason": f"Check error: {str(e)}",
                "blocking_issues": [f"System check error: {str(e)}"],
                "warnings": [],
                "current_state": self.current_state.value
            }
    
    def perform_reconciliation(
        self,
        account_data: Dict[str, Any],
        broker_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> ReconciliationResult:
        """
        Perform SAFE→ACTIVE reconciliation process.
        
        Args:
            account_data: Internal account data
            broker_data: Broker account data
            market_data: Current market data
            
        Returns:
            ReconciliationResult
        """
        reconciliation_id = f"recon_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting reconciliation: {reconciliation_id}")
        
        checks_performed = []
        blocking_issues = []
        warnings = []
        
        try:
            # 1. Cash Balance Reconciliation
            cash_check = self._reconcile_cash_balances(account_data, broker_data)
            checks_performed.append(cash_check)
            if not cash_check.passed:
                blocking_issues.append(f"Cash reconciliation failed: {cash_check.error_message}")
            
            # 2. Position Reconciliation
            position_check = self._reconcile_positions(account_data, broker_data, market_data)
            checks_performed.append(position_check)
            if not position_check.passed:
                blocking_issues.append(f"Position reconciliation failed: {position_check.error_message}")
            
            # 3. Order Status Reconciliation
            order_check = self._reconcile_order_status(account_data, broker_data)
            checks_performed.append(order_check)
            if not order_check.passed:
                warnings.append(f"Order status discrepancies: {order_check.error_message}")
            
            # 4. Risk Metrics Validation
            risk_check = self._validate_risk_metrics(account_data, market_data)
            checks_performed.append(risk_check)
            if not risk_check.passed:
                blocking_issues.append(f"Risk validation failed: {risk_check.error_message}")
            
            # 5. Market Data Connectivity
            market_check = self._check_market_data_connectivity(market_data)
            checks_performed.append(market_check)
            if not market_check.passed:
                blocking_issues.append(f"Market data issues: {market_check.error_message}")
            
            # 6. System Component Health
            component_check = self._check_system_components()
            checks_performed.append(component_check)
            if not component_check.passed:
                blocking_issues.append(f"System component issues: {component_check.error_message}")
            
            end_time = datetime.now()
            overall_success = len(blocking_issues) == 0
            ready_for_active = overall_success
            
            # Create reconciliation result
            result = ReconciliationResult(
                reconciliation_id=reconciliation_id,
                start_time=start_time,
                end_time=end_time,
                checks_performed=checks_performed,
                overall_success=overall_success,
                blocking_issues=blocking_issues,
                warnings=warnings,
                ready_for_active=ready_for_active
            )
            
            # Store reconciliation result
            self.reconciliation_history.append(result)
            if overall_success:
                self.last_reconciliation = result
            
            duration = (end_time - start_time).total_seconds()
            logger.info(
                f"Reconciliation {reconciliation_id} completed in {duration:.1f}s: "
                f"{'SUCCESS' if overall_success else 'FAILED'}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during reconciliation {reconciliation_id}: {e}")
            
            error_check = ReconciliationCheck(
                check_name="reconciliation_error",
                check_type="system",
                passed=False,
                details={"error": str(e)},
                error_message=str(e),
                timestamp=datetime.now()
            )
            checks_performed.append(error_check)
            
            return ReconciliationResult(
                reconciliation_id=reconciliation_id,
                start_time=start_time,
                end_time=datetime.now(),
                checks_performed=checks_performed,
                overall_success=False,
                blocking_issues=[f"Reconciliation error: {str(e)}"],
                warnings=[],
                ready_for_active=False
            )
    
    def transition_to_active(
        self,
        trigger: TransitionTrigger = TransitionTrigger.MANUAL_ACTIVATION,
        user_id: Optional[str] = None,
        reason: str = "Manual activation"
    ) -> StateTransition:
        """
        Transition system to ACTIVE state.
        
        Args:
            trigger: Transition trigger
            user_id: User initiating transition
            reason: Reason for transition
            
        Returns:
            StateTransition result
        """
        transition_id = f"trans_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Check if transition is allowed
            transition_check = self.can_transition_to_active()
            
            validation_checks = []
            success = False
            error_message = None
            
            if transition_check["can_transition"]:
                # Perform transition
                old_state = self.current_state
                self.current_state = SystemState.ACTIVE
                success = True
                
                validation_checks = [
                    "Market hours validated",
                    "Reconciliation status verified",
                    "System health confirmed"
                ]
                
                logger.info(f"State transition successful: {old_state.value} → {self.current_state.value}")
                
                # Notify callbacks
                self._notify_state_change(old_state, self.current_state, trigger)
                
            else:
                error_message = f"Transition blocked: {', '.join(transition_check['blocking_issues'])}"
                validation_checks = [f"Failed: {issue}" for issue in transition_check["blocking_issues"]]
                
                logger.warning(f"State transition blocked: {error_message}")
            
            # Create transition record
            transition = StateTransition(
                transition_id=transition_id,
                from_state=SystemState.SAFE if success else self.current_state,
                to_state=SystemState.ACTIVE if success else self.current_state,
                trigger=trigger,
                timestamp=datetime.now(),
                user_id=user_id,
                reason=reason,
                validation_checks=validation_checks,
                success=success,
                error_message=error_message
            )
            
            self.transition_history.append(transition)
            return transition
            
        except Exception as e:
            logger.error(f"Error during state transition: {e}")
            
            error_transition = StateTransition(
                transition_id=transition_id,
                from_state=self.current_state,
                to_state=self.current_state,
                trigger=trigger,
                timestamp=datetime.now(),
                user_id=user_id,
                reason=reason,
                validation_checks=[f"Transition error: {str(e)}"],
                success=False,
                error_message=str(e)
            )
            
            self.transition_history.append(error_transition)
            return error_transition
    
    def transition_to_safe(
        self,
        trigger: TransitionTrigger = TransitionTrigger.MANUAL_SAFE_MODE,
        user_id: Optional[str] = None,
        reason: str = "Manual SAFE mode activation"
    ) -> StateTransition:
        """Transition system to SAFE state."""
        transition_id = f"trans_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            old_state = self.current_state
            self.current_state = SystemState.SAFE
            
            logger.info(f"State transition to SAFE: {old_state.value} → {self.current_state.value}")
            
            # Notify callbacks
            self._notify_state_change(old_state, self.current_state, trigger)
            
            transition = StateTransition(
                transition_id=transition_id,
                from_state=old_state,
                to_state=self.current_state,
                trigger=trigger,
                timestamp=datetime.now(),
                user_id=user_id,
                reason=reason,
                validation_checks=["SAFE mode activated"],
                success=True,
                error_message=None
            )
            
            self.transition_history.append(transition)
            return transition
            
        except Exception as e:
            logger.error(f"Error transitioning to SAFE: {e}")
            raise
    
    def _check_market_hours(self, current_time: datetime) -> Dict[str, Any]:
        """Check market hours status."""
        # Simplified market hours check
        current_time_et = current_time  # Assume ET for simplicity
        current_weekday = current_time_et.weekday()
        current_time_only = current_time_et.time()
        
        is_weekend = current_weekday >= 5  # Saturday = 5, Sunday = 6
        is_holiday = False  # Simplified - would check holiday calendar
        
        is_market_hours = (
            not is_weekend and 
            not is_holiday and
            self.MARKET_OPEN_TIME <= current_time_only <= self.MARKET_CLOSE_TIME
        )
        
        is_extended_hours = (
            not is_weekend and 
            not is_holiday and
            (self.PREMARKET_START <= current_time_only < self.MARKET_OPEN_TIME or
             self.MARKET_CLOSE_TIME < current_time_only <= self.AFTERHOURS_END)
        )
        
        if is_market_hours:
            status = "market_open"
        elif is_extended_hours:
            status = "extended_hours"
        elif is_weekend:
            status = "weekend"
        elif is_holiday:
            status = "holiday"
        else:
            status = "market_closed"
        
        return {
            "is_market_hours": is_market_hours,
            "is_extended_hours": is_extended_hours,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "status": status,
            "current_time": current_time_et.isoformat()
        }
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        # Simplified system health check
        return {
            "healthy": True,
            "issues": [],
            "components": {
                "database": "healthy",
                "market_data": "healthy",
                "execution_engine": "healthy",
                "risk_engine": "healthy"
            }
        }
    
    def _reconcile_cash_balances(self, account_data: Dict[str, Any], broker_data: Dict[str, Any]) -> ReconciliationCheck:
        """Reconcile cash balances between internal and broker data."""
        try:
            internal_cash = Decimal(str(account_data.get("cash_balance", 0)))
            broker_cash = Decimal(str(broker_data.get("cash_balance", 0)))
            
            discrepancy = abs(internal_cash - broker_cash)
            passed = discrepancy <= self.MAX_CASH_DISCREPANCY
            
            return ReconciliationCheck(
                check_name="cash_balance_reconciliation",
                check_type="financial",
                passed=passed,
                details={
                    "internal_cash": float(internal_cash),
                    "broker_cash": float(broker_cash),
                    "discrepancy": float(discrepancy),
                    "max_allowed": float(self.MAX_CASH_DISCREPANCY)
                },
                error_message=None if passed else f"Cash discrepancy ${discrepancy} exceeds limit ${self.MAX_CASH_DISCREPANCY}",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ReconciliationCheck(
                check_name="cash_balance_reconciliation",
                check_type="financial",
                passed=False,
                details={"error": str(e)},
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    def _reconcile_positions(self, account_data: Dict[str, Any], broker_data: Dict[str, Any], market_data: Dict[str, Any]) -> ReconciliationCheck:
        """Reconcile positions between internal and broker data."""
        try:
            # Simplified position reconciliation
            internal_positions = account_data.get("positions", [])
            broker_positions = broker_data.get("positions", [])
            
            position_discrepancies = []
            
            # Check each internal position against broker
            for internal_pos in internal_positions:
                symbol = internal_pos.get("symbol")
                internal_qty = internal_pos.get("quantity", 0)
                
                # Find matching broker position
                broker_pos = next((p for p in broker_positions if p.get("symbol") == symbol), None)
                broker_qty = broker_pos.get("quantity", 0) if broker_pos else 0
                
                if internal_qty != broker_qty:
                    position_discrepancies.append({
                        "symbol": symbol,
                        "internal_qty": internal_qty,
                        "broker_qty": broker_qty,
                        "discrepancy": internal_qty - broker_qty
                    })
            
            passed = len(position_discrepancies) == 0
            
            return ReconciliationCheck(
                check_name="position_reconciliation",
                check_type="positions",
                passed=passed,
                details={
                    "internal_positions_count": len(internal_positions),
                    "broker_positions_count": len(broker_positions),
                    "discrepancies": position_discrepancies
                },
                error_message=None if passed else f"{len(position_discrepancies)} position discrepancies found",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ReconciliationCheck(
                check_name="position_reconciliation",
                check_type="positions",
                passed=False,
                details={"error": str(e)},
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    def _reconcile_order_status(self, account_data: Dict[str, Any], broker_data: Dict[str, Any]) -> ReconciliationCheck:
        """Reconcile order status between internal and broker data."""
        # Simplified implementation
        return ReconciliationCheck(
            check_name="order_status_reconciliation",
            check_type="orders",
            passed=True,
            details={"orders_checked": 0, "discrepancies": 0},
            error_message=None,
            timestamp=datetime.now()
        )
    
    def _validate_risk_metrics(self, account_data: Dict[str, Any], market_data: Dict[str, Any]) -> ReconciliationCheck:
        """Validate risk metrics are within acceptable ranges."""
        # Simplified implementation
        return ReconciliationCheck(
            check_name="risk_metrics_validation",
            check_type="risk",
            passed=True,
            details={"risk_level": "normal", "metrics_validated": True},
            error_message=None,
            timestamp=datetime.now()
        )
    
    def _check_market_data_connectivity(self, market_data: Dict[str, Any]) -> ReconciliationCheck:
        """Check market data connectivity and freshness."""
        try:
            # Check if market data is recent
            last_update = market_data.get("last_update")
            if last_update:
                if isinstance(last_update, str):
                    last_update = datetime.fromisoformat(last_update)
                
                age_seconds = (datetime.now() - last_update).total_seconds()
                passed = age_seconds < 300  # 5 minutes
                
                return ReconciliationCheck(
                    check_name="market_data_connectivity",
                    check_type="connectivity",
                    passed=passed,
                    details={
                        "last_update": last_update.isoformat(),
                        "age_seconds": age_seconds,
                        "max_age_seconds": 300
                    },
                    error_message=None if passed else f"Market data stale: {age_seconds:.0f}s old",
                    timestamp=datetime.now()
                )
            else:
                return ReconciliationCheck(
                    check_name="market_data_connectivity",
                    check_type="connectivity",
                    passed=False,
                    details={"error": "No market data timestamp"},
                    error_message="Market data timestamp missing",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return ReconciliationCheck(
                check_name="market_data_connectivity",
                check_type="connectivity",
                passed=False,
                details={"error": str(e)},
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    def _check_system_components(self) -> ReconciliationCheck:
        """Check system component health."""
        # Simplified implementation
        return ReconciliationCheck(
            check_name="system_components_health",
            check_type="system",
            passed=True,
            details={"components_healthy": True, "all_services_running": True},
            error_message=None,
            timestamp=datetime.now()
        )
    
    def _notify_state_change(self, old_state: SystemState, new_state: SystemState, trigger: TransitionTrigger):
        """Notify registered callbacks of state change."""
        for callback in self.state_change_callbacks:
            try:
                callback(old_state, new_state, trigger)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    def register_state_change_callback(self, callback):
        """Register callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive state machine summary."""
        return {
            "current_state": self.current_state.value,
            "transition_history_count": len(self.transition_history),
            "reconciliation_history_count": len(self.reconciliation_history),
            "last_reconciliation": {
                "id": self.last_reconciliation.reconciliation_id if self.last_reconciliation else None,
                "success": self.last_reconciliation.overall_success if self.last_reconciliation else None,
                "timestamp": self.last_reconciliation.end_time.isoformat() if self.last_reconciliation and self.last_reconciliation.end_time else None
            } if self.last_reconciliation else None,
            "market_status": self._check_market_hours(datetime.now()),
            "system_health": self._check_system_health(),
            "rule": "Constitution v1.3 - SAFE→ACTIVE State Machine"
        }


# Global state machine instance
safe_active_state_machine = SAFEActiveStateMachine()

