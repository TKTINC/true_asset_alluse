"""
Assignment Protocol - Constitution v1.3 Compliance

This module implements the assignment and covered call protocol per GPT-5 feedback:
- Friday 3pm ITM checks for assignment risk
- CC pivot rules and recovery logic
- Assignment handling and position management

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AssignmentRisk(Enum):
    """Assignment risk levels."""
    LOW = "low"           # OTM by >5%
    MEDIUM = "medium"     # OTM by 1-5%
    HIGH = "high"         # ITM by 0-3%
    CRITICAL = "critical" # ITM by >3%


class CCPivotAction(Enum):
    """Covered call pivot actions."""
    HOLD = "hold"                    # Hold current position
    ROLL_UP = "roll_up"             # Roll up and out
    ROLL_OUT = "roll_out"           # Roll out same strike
    CLOSE_CC = "close_cc"           # Close covered call
    ACCEPT_ASSIGNMENT = "accept_assignment"  # Accept assignment


@dataclass
class AssignmentCheck:
    """Assignment risk check result."""
    symbol: str
    position_id: str
    strike: Decimal
    expiration: datetime
    current_price: Decimal
    moneyness: Decimal  # (current_price - strike) / strike
    risk_level: AssignmentRisk
    time_to_expiration_hours: float
    assignment_probability: Decimal
    recommended_action: CCPivotAction
    urgency: str


@dataclass
class CCPivotPlan:
    """Covered call pivot execution plan."""
    original_position: Dict[str, Any]
    pivot_action: CCPivotAction
    new_strike: Optional[Decimal]
    new_expiration: Optional[datetime]
    estimated_cost: Decimal
    estimated_credit: Decimal
    net_cost: Decimal
    execution_priority: str
    risk_mitigation: List[str]


class AssignmentProtocol:
    """Assignment and covered call protocol manager."""
    
    # Assignment risk thresholds
    LOW_RISK_OTM_PCT = Decimal("0.05")      # >5% OTM = low risk
    MEDIUM_RISK_OTM_PCT = Decimal("0.01")   # 1-5% OTM = medium risk
    HIGH_RISK_ITM_PCT = Decimal("0.03")     # 0-3% ITM = high risk
    CRITICAL_RISK_ITM_PCT = Decimal("0.03") # >3% ITM = critical risk
    
    # Friday 3pm check time
    FRIDAY_CHECK_TIME = time(15, 0)  # 3:00 PM
    
    # Assignment probability model parameters
    BASE_ASSIGNMENT_PROB = {
        AssignmentRisk.LOW: Decimal("0.05"),      # 5%
        AssignmentRisk.MEDIUM: Decimal("0.20"),   # 20%
        AssignmentRisk.HIGH: Decimal("0.60"),     # 60%
        AssignmentRisk.CRITICAL: Decimal("0.90")  # 90%
    }
    
    def __init__(self):
        """Initialize assignment protocol manager."""
        pass
    
    def check_assignment_risk(
        self,
        position: Dict[str, Any],
        current_market_data: Dict[str, Any],
        check_time: Optional[datetime] = None
    ) -> AssignmentCheck:
        """
        Check assignment risk for a short option position.
        
        Args:
            position: Position details (symbol, strike, expiration, etc.)
            current_market_data: Current market data
            check_time: Time of check (defaults to now)
            
        Returns:
            AssignmentCheck with risk assessment
        """
        try:
            check_time = check_time or datetime.now()
            
            # Extract position details
            symbol = position.get("symbol")
            position_id = position.get("position_id")
            strike = Decimal(str(position.get("strike", 0)))
            expiration = position.get("expiration")
            option_type = position.get("option_type", "call")
            
            # Extract market data
            current_price = Decimal(str(current_market_data.get("current_price", 0)))
            
            # Calculate moneyness and time to expiration
            if option_type.lower() == "call":
                # For calls: ITM when current_price > strike
                moneyness = (current_price - strike) / strike
            else:
                # For puts: ITM when current_price < strike
                moneyness = (strike - current_price) / strike
            
            # Calculate time to expiration
            if isinstance(expiration, str):
                expiration = datetime.fromisoformat(expiration)
            
            time_to_expiration = expiration - check_time
            time_to_expiration_hours = time_to_expiration.total_seconds() / 3600
            
            # Determine risk level based on moneyness
            if moneyness <= -self.LOW_RISK_OTM_PCT:  # >5% OTM
                risk_level = AssignmentRisk.LOW
            elif moneyness <= -self.MEDIUM_RISK_OTM_PCT:  # 1-5% OTM
                risk_level = AssignmentRisk.MEDIUM
            elif moneyness <= self.HIGH_RISK_ITM_PCT:  # 0-3% ITM
                risk_level = AssignmentRisk.HIGH
            else:  # >3% ITM
                risk_level = AssignmentRisk.CRITICAL
            
            # Calculate assignment probability
            base_prob = self.BASE_ASSIGNMENT_PROB[risk_level]
            
            # Adjust for time to expiration (higher probability closer to expiration)
            if time_to_expiration_hours < 24:  # Less than 1 day
                time_multiplier = Decimal("1.5")
            elif time_to_expiration_hours < 72:  # Less than 3 days
                time_multiplier = Decimal("1.2")
            else:
                time_multiplier = Decimal("1.0")
            
            assignment_probability = min(base_prob * time_multiplier, Decimal("0.95"))
            
            # Determine recommended action
            recommended_action = self._determine_cc_pivot_action(
                risk_level, moneyness, time_to_expiration_hours, assignment_probability
            )
            
            # Determine urgency
            if risk_level == AssignmentRisk.CRITICAL or time_to_expiration_hours < 4:
                urgency = "IMMEDIATE"
            elif risk_level == AssignmentRisk.HIGH or time_to_expiration_hours < 24:
                urgency = "HIGH"
            elif risk_level == AssignmentRisk.MEDIUM:
                urgency = "MEDIUM"
            else:
                urgency = "LOW"
            
            logger.info(
                f"Assignment check for {symbol} {strike}{option_type[0].upper()}: "
                f"Risk {risk_level.value}, Probability {assignment_probability:.1%}, "
                f"Action {recommended_action.value}"
            )
            
            return AssignmentCheck(
                symbol=symbol,
                position_id=position_id,
                strike=strike,
                expiration=expiration,
                current_price=current_price,
                moneyness=moneyness,
                risk_level=risk_level,
                time_to_expiration_hours=time_to_expiration_hours,
                assignment_probability=assignment_probability,
                recommended_action=recommended_action,
                urgency=urgency
            )
            
        except Exception as e:
            logger.error(f"Error checking assignment risk: {e}")
            raise
    
    def _determine_cc_pivot_action(
        self,
        risk_level: AssignmentRisk,
        moneyness: Decimal,
        time_to_expiration_hours: float,
        assignment_probability: Decimal
    ) -> CCPivotAction:
        """Determine the appropriate covered call pivot action."""
        
        # Critical risk - immediate action required
        if risk_level == AssignmentRisk.CRITICAL:
            if time_to_expiration_hours < 4:  # Very close to expiration
                return CCPivotAction.ACCEPT_ASSIGNMENT
            else:
                return CCPivotAction.CLOSE_CC
        
        # High risk - defensive action
        elif risk_level == AssignmentRisk.HIGH:
            if time_to_expiration_hours < 24:  # Less than 1 day
                return CCPivotAction.ROLL_OUT
            else:
                return CCPivotAction.ROLL_UP
        
        # Medium risk - monitor and prepare
        elif risk_level == AssignmentRisk.MEDIUM:
            if time_to_expiration_hours < 72:  # Less than 3 days
                return CCPivotAction.ROLL_OUT
            else:
                return CCPivotAction.HOLD
        
        # Low risk - hold position
        else:
            return CCPivotAction.HOLD
    
    def create_cc_pivot_plan(
        self,
        assignment_check: AssignmentCheck,
        market_data: Dict[str, Any],
        account_context: Dict[str, Any]
    ) -> CCPivotPlan:
        """
        Create a covered call pivot execution plan.
        
        Args:
            assignment_check: Assignment risk check result
            market_data: Current market data
            account_context: Account context and constraints
            
        Returns:
            CCPivotPlan with execution details
        """
        try:
            action = assignment_check.recommended_action
            current_strike = assignment_check.strike
            current_price = assignment_check.current_price
            
            # Initialize plan variables
            new_strike = None
            new_expiration = None
            estimated_cost = Decimal("0")
            estimated_credit = Decimal("0")
            risk_mitigation = []
            
            # Determine new parameters based on action
            if action == CCPivotAction.ROLL_UP:
                # Roll up to next resistance level or 5% OTM
                new_strike = current_price * Decimal("1.05")  # 5% OTM
                new_expiration = assignment_check.expiration + timedelta(weeks=1)
                estimated_cost = new_strike * Decimal("0.02")  # Estimate 2% of strike
                risk_mitigation.append("Reduce assignment risk by rolling up")
                risk_mitigation.append("Extend time to expiration")
                
            elif action == CCPivotAction.ROLL_OUT:
                # Roll out same strike to next expiration
                new_strike = current_strike
                new_expiration = assignment_check.expiration + timedelta(weeks=1)
                estimated_credit = current_strike * Decimal("0.01")  # Estimate 1% credit
                risk_mitigation.append("Extend time to expiration")
                risk_mitigation.append("Collect additional premium")
                
            elif action == CCPivotAction.CLOSE_CC:
                # Close covered call position
                estimated_cost = current_strike * Decimal("0.03")  # Estimate 3% to close
                risk_mitigation.append("Eliminate assignment risk")
                risk_mitigation.append("Retain underlying shares")
                
            elif action == CCPivotAction.ACCEPT_ASSIGNMENT:
                # Accept assignment and sell shares
                estimated_credit = current_strike  # Receive strike price for shares
                risk_mitigation.append("Realize profit on underlying shares")
                risk_mitigation.append("Free up capital for new positions")
                
            # Calculate net cost/credit
            net_cost = estimated_cost - estimated_credit
            
            # Determine execution priority
            if assignment_check.urgency == "IMMEDIATE":
                execution_priority = "IMMEDIATE"
            elif assignment_check.urgency == "HIGH":
                execution_priority = "HIGH"
            else:
                execution_priority = "NORMAL"
            
            logger.info(
                f"CC pivot plan created: {action.value} for {assignment_check.symbol}, "
                f"net cost ${net_cost:,.2f}, priority {execution_priority}"
            )
            
            return CCPivotPlan(
                original_position={
                    "symbol": assignment_check.symbol,
                    "position_id": assignment_check.position_id,
                    "strike": assignment_check.strike,
                    "expiration": assignment_check.expiration
                },
                pivot_action=action,
                new_strike=new_strike,
                new_expiration=new_expiration,
                estimated_cost=estimated_cost,
                estimated_credit=estimated_credit,
                net_cost=net_cost,
                execution_priority=execution_priority,
                risk_mitigation=risk_mitigation
            )
            
        except Exception as e:
            logger.error(f"Error creating CC pivot plan: {e}")
            raise
    
    def friday_3pm_check(
        self,
        positions: List[Dict[str, Any]],
        market_data: Dict[str, Dict[str, Any]],
        check_time: Optional[datetime] = None
    ) -> List[AssignmentCheck]:
        """
        Perform Friday 3pm assignment risk checks.
        
        Args:
            positions: List of short option positions
            market_data: Market data for all positions
            check_time: Check time (defaults to now)
            
        Returns:
            List of assignment checks for positions at risk
        """
        check_time = check_time or datetime.now()
        
        # Only perform check on Fridays at/after 3pm
        if check_time.weekday() != 4:  # Not Friday
            logger.info("Friday 3pm check skipped - not Friday")
            return []
        
        if check_time.time() < self.FRIDAY_CHECK_TIME:
            logger.info("Friday 3pm check skipped - before 3pm")
            return []
        
        assignment_checks = []
        
        for position in positions:
            try:
                symbol = position.get("symbol")
                position_market_data = market_data.get(symbol, {})
                
                # Only check short positions expiring today or Monday
                if self._is_weekend_expiration_risk(position, check_time):
                    assignment_check = self.check_assignment_risk(
                        position, position_market_data, check_time
                    )
                    
                    # Only include positions with medium+ risk
                    if assignment_check.risk_level in [
                        AssignmentRisk.MEDIUM, AssignmentRisk.HIGH, AssignmentRisk.CRITICAL
                    ]:
                        assignment_checks.append(assignment_check)
                        
            except Exception as e:
                logger.error(f"Error in Friday 3pm check for position {position.get('position_id')}: {e}")
                continue
        
        logger.info(f"Friday 3pm check completed: {len(assignment_checks)} positions at risk")
        return assignment_checks
    
    def _is_weekend_expiration_risk(self, position: Dict[str, Any], check_time: datetime) -> bool:
        """Check if position has weekend expiration risk."""
        expiration = position.get("expiration")
        if isinstance(expiration, str):
            expiration = datetime.fromisoformat(expiration)
        
        # Check if expiring today (Friday) or Monday
        days_to_expiration = (expiration.date() - check_time.date()).days
        return days_to_expiration <= 3  # Friday, Saturday, Sunday, Monday
    
    def get_assignment_summary(self, assignment_checks: List[AssignmentCheck]) -> Dict[str, Any]:
        """Get summary of assignment risk across positions."""
        if not assignment_checks:
            return {
                "total_positions": 0,
                "risk_breakdown": {},
                "avg_assignment_probability": 0.0,
                "immediate_action_required": 0,
                "high_priority_actions": 0
            }
        
        # Risk level breakdown
        risk_breakdown = {}
        for risk_level in AssignmentRisk:
            risk_breakdown[risk_level.value] = sum(
                1 for check in assignment_checks if check.risk_level == risk_level
            )
        
        # Calculate averages
        avg_assignment_probability = sum(
            float(check.assignment_probability) for check in assignment_checks
        ) / len(assignment_checks)
        
        # Count urgent actions
        immediate_action_required = sum(
            1 for check in assignment_checks if check.urgency == "IMMEDIATE"
        )
        
        high_priority_actions = sum(
            1 for check in assignment_checks if check.urgency in ["IMMEDIATE", "HIGH"]
        )
        
        return {
            "total_positions": len(assignment_checks),
            "risk_breakdown": risk_breakdown,
            "avg_assignment_probability": avg_assignment_probability,
            "immediate_action_required": immediate_action_required,
            "high_priority_actions": high_priority_actions,
            "check_time": datetime.now().isoformat(),
            "friday_3pm_protocol": "Constitution v1.3 - Assignment Protocol"
        }


# Global assignment protocol manager
assignment_protocol = AssignmentProtocol()

