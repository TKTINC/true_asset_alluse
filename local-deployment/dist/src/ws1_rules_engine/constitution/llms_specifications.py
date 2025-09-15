"""
LLMS Specifications - Constitution v1.3 Compliance

This module implements the LEAP Ladder Management System (LLMS) specifications
per GPT-5 feedback:
- Delta ranges: 0.25-0.35Δ calls, 10-20% OTM puts
- Laddering and roll rules
- Separate hedge vs compounding ledgers

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMSLadderType(Enum):
    """LLMS ladder types."""
    HEDGE_LADDER = "hedge_ladder"           # Hedge-focused LEAP ladder
    COMPOUNDING_LADDER = "compounding_ladder"  # Compounding-focused LEAP ladder


class LLMSPositionType(Enum):
    """LLMS position types."""
    LEAP_CALL = "leap_call"     # Long LEAP call
    LEAP_PUT = "leap_put"       # Long LEAP put
    SHORT_CALL = "short_call"   # Short call against LEAP
    SHORT_PUT = "short_put"     # Short put in ladder


@dataclass
class LLMSParameters:
    """LLMS parameter specifications."""
    # Call specifications
    call_delta_min: Decimal = Decimal("0.25")  # 0.25Δ minimum
    call_delta_max: Decimal = Decimal("0.35")  # 0.35Δ maximum
    call_delta_target: Decimal = Decimal("0.30")  # 0.30Δ target
    
    # Put specifications  
    put_otm_min_pct: Decimal = Decimal("0.10")  # 10% OTM minimum
    put_otm_max_pct: Decimal = Decimal("0.20")  # 20% OTM maximum
    put_otm_target_pct: Decimal = Decimal("0.15")  # 15% OTM target
    
    # Time specifications
    min_dte: int = 365  # Minimum 1 year DTE for LEAPs
    max_dte: int = 730  # Maximum 2 years DTE
    target_dte: int = 545  # Target ~18 months DTE
    
    # Roll specifications
    roll_delta_threshold: Decimal = Decimal("0.50")  # Roll when delta > 0.50
    roll_dte_threshold: int = 90  # Roll when DTE < 90 days
    
    # Allocation specifications
    hedge_allocation_pct: Decimal = Decimal("0.25")  # 25% to hedge ladder
    compounding_allocation_pct: Decimal = Decimal("0.75")  # 75% to compounding


@dataclass
class LLMSPosition:
    """LLMS position structure."""
    position_id: str
    ladder_type: LLMSLadderType
    position_type: LLMSPositionType
    symbol: str
    strike: Decimal
    expiration: datetime
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    delta: Decimal
    theta: Decimal
    vega: Decimal
    gamma: Decimal
    days_to_expiration: int
    unrealized_pnl: Decimal
    allocation_percentage: Decimal
    created_date: datetime
    last_updated: datetime


@dataclass
class LLMSLadder:
    """LLMS ladder structure."""
    ladder_id: str
    ladder_type: LLMSLadderType
    symbol: str
    positions: List[LLMSPosition]
    total_allocation: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    performance_metrics: Dict[str, Any]
    created_date: datetime
    last_rebalanced: datetime


class LLMSSpecifications:
    """LEAP Ladder Management System specifications manager."""
    
    def __init__(self):
        """Initialize LLMS specifications."""
        self.parameters = LLMSParameters()
        self.active_ladders = {}  # ladder_id -> LLMSLadder
        self.position_registry = {}  # position_id -> LLMSPosition
    
    def validate_leap_call_specs(
        self,
        symbol: str,
        strike: Decimal,
        expiration: datetime,
        current_price: Decimal,
        delta: Decimal,
        days_to_expiration: int
    ) -> Dict[str, Any]:
        """
        Validate LEAP call against LLMS specifications.
        
        Args:
            symbol: Underlying symbol
            strike: Option strike price
            expiration: Option expiration date
            current_price: Current underlying price
            delta: Option delta
            days_to_expiration: Days to expiration
            
        Returns:
            Validation result
        """
        violations = []
        
        try:
            # Validate delta range
            if delta < self.parameters.call_delta_min:
                violations.append(
                    f"Delta {delta:.3f} < minimum {self.parameters.call_delta_min:.3f}"
                )
            elif delta > self.parameters.call_delta_max:
                violations.append(
                    f"Delta {delta:.3f} > maximum {self.parameters.call_delta_max:.3f}"
                )
            
            # Validate DTE range
            if days_to_expiration < self.parameters.min_dte:
                violations.append(
                    f"DTE {days_to_expiration} < minimum {self.parameters.min_dte}"
                )
            elif days_to_expiration > self.parameters.max_dte:
                violations.append(
                    f"DTE {days_to_expiration} > maximum {self.parameters.max_dte}"
                )
            
            # Calculate moneyness
            moneyness = (current_price - strike) / strike
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "specifications": {
                    "delta_range": f"{self.parameters.call_delta_min:.3f}-{self.parameters.call_delta_max:.3f}",
                    "delta_target": float(self.parameters.call_delta_target),
                    "dte_range": f"{self.parameters.min_dte}-{self.parameters.max_dte}",
                    "dte_target": self.parameters.target_dte,
                    "current_delta": float(delta),
                    "current_dte": days_to_expiration,
                    "moneyness": float(moneyness)
                },
                "rule": "Constitution v1.3 - LLMS: LEAP calls 0.25-0.35Δ, 1-2 years DTE"
            }
            
        except Exception as e:
            logger.error(f"Error validating LEAP call specs: {e}")
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "specifications": None,
                "rule": "Constitution v1.3 - LLMS LEAP Call Specifications"
            }
    
    def validate_leap_put_specs(
        self,
        symbol: str,
        strike: Decimal,
        expiration: datetime,
        current_price: Decimal,
        days_to_expiration: int
    ) -> Dict[str, Any]:
        """
        Validate LEAP put against LLMS specifications.
        
        Args:
            symbol: Underlying symbol
            strike: Option strike price
            expiration: Option expiration date
            current_price: Current underlying price
            days_to_expiration: Days to expiration
            
        Returns:
            Validation result
        """
        violations = []
        
        try:
            # Calculate OTM percentage
            otm_percentage = (current_price - strike) / current_price
            
            # Validate OTM range
            if otm_percentage < self.parameters.put_otm_min_pct:
                violations.append(
                    f"OTM {otm_percentage:.1%} < minimum {self.parameters.put_otm_min_pct:.1%}"
                )
            elif otm_percentage > self.parameters.put_otm_max_pct:
                violations.append(
                    f"OTM {otm_percentage:.1%} > maximum {self.parameters.put_otm_max_pct:.1%}"
                )
            
            # Validate DTE range
            if days_to_expiration < self.parameters.min_dte:
                violations.append(
                    f"DTE {days_to_expiration} < minimum {self.parameters.min_dte}"
                )
            elif days_to_expiration > self.parameters.max_dte:
                violations.append(
                    f"DTE {days_to_expiration} > maximum {self.parameters.max_dte}"
                )
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "specifications": {
                    "otm_range": f"{self.parameters.put_otm_min_pct:.1%}-{self.parameters.put_otm_max_pct:.1%}",
                    "otm_target": f"{self.parameters.put_otm_target_pct:.1%}",
                    "dte_range": f"{self.parameters.min_dte}-{self.parameters.max_dte}",
                    "dte_target": self.parameters.target_dte,
                    "current_otm": f"{otm_percentage:.1%}",
                    "current_dte": days_to_expiration,
                    "strike": float(strike),
                    "current_price": float(current_price)
                },
                "rule": "Constitution v1.3 - LLMS: LEAP puts 10-20% OTM, 1-2 years DTE"
            }
            
        except Exception as e:
            logger.error(f"Error validating LEAP put specs: {e}")
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "specifications": None,
                "rule": "Constitution v1.3 - LLMS LEAP Put Specifications"
            }
    
    def check_roll_criteria(
        self,
        position: LLMSPosition,
        current_market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if LEAP position meets roll criteria.
        
        Args:
            position: LLMS position to check
            current_market_data: Current market data
            
        Returns:
            Roll criteria check result
        """
        try:
            current_delta = Decimal(str(current_market_data.get("delta", 0)))
            current_dte = position.days_to_expiration
            
            roll_triggers = []
            roll_required = False
            
            # Check delta threshold
            if position.position_type == LLMSPositionType.LEAP_CALL:
                if current_delta > self.parameters.roll_delta_threshold:
                    roll_triggers.append(f"Delta {current_delta:.3f} > threshold {self.parameters.roll_delta_threshold:.3f}")
                    roll_required = True
            
            # Check DTE threshold
            if current_dte < self.parameters.roll_dte_threshold:
                roll_triggers.append(f"DTE {current_dte} < threshold {self.parameters.roll_dte_threshold}")
                roll_required = True
            
            # Determine roll recommendation
            if roll_required:
                if current_dte < 30:  # Very close to expiration
                    recommendation = "IMMEDIATE_ROLL"
                    priority = "CRITICAL"
                elif current_dte < 60:  # Close to expiration
                    recommendation = "URGENT_ROLL"
                    priority = "HIGH"
                else:
                    recommendation = "SCHEDULED_ROLL"
                    priority = "MEDIUM"
            else:
                recommendation = "HOLD"
                priority = "LOW"
            
            return {
                "roll_required": roll_required,
                "roll_triggers": roll_triggers,
                "recommendation": recommendation,
                "priority": priority,
                "current_delta": float(current_delta),
                "current_dte": current_dte,
                "thresholds": {
                    "delta_threshold": float(self.parameters.roll_delta_threshold),
                    "dte_threshold": self.parameters.roll_dte_threshold
                },
                "position_id": position.position_id,
                "rule": "Constitution v1.3 - LLMS Roll Criteria"
            }
            
        except Exception as e:
            logger.error(f"Error checking roll criteria for position {position.position_id}: {e}")
            return {
                "roll_required": False,
                "roll_triggers": [f"Check error: {str(e)}"],
                "recommendation": "MANUAL_REVIEW",
                "priority": "HIGH",
                "rule": "Constitution v1.3 - LLMS Roll Criteria"
            }
    
    def calculate_ladder_allocation(
        self,
        total_capital: Decimal,
        ladder_type: LLMSLadderType
    ) -> Dict[str, Any]:
        """
        Calculate allocation for LLMS ladder.
        
        Args:
            total_capital: Total available capital
            ladder_type: Type of ladder (hedge or compounding)
            
        Returns:
            Allocation calculation result
        """
        try:
            if ladder_type == LLMSLadderType.HEDGE_LADDER:
                allocation_pct = self.parameters.hedge_allocation_pct
                purpose = "Risk hedging and portfolio protection"
            else:  # COMPOUNDING_LADDER
                allocation_pct = self.parameters.compounding_allocation_pct
                purpose = "Capital compounding and growth"
            
            allocation_amount = total_capital * allocation_pct
            
            return {
                "ladder_type": ladder_type.value,
                "allocation_percentage": float(allocation_pct),
                "allocation_amount": float(allocation_amount),
                "total_capital": float(total_capital),
                "purpose": purpose,
                "specifications": {
                    "hedge_allocation": f"{self.parameters.hedge_allocation_pct:.1%}",
                    "compounding_allocation": f"{self.parameters.compounding_allocation_pct:.1%}",
                    "total_allocation": "100%"
                },
                "rule": "Constitution v1.3 - LLMS: 25% hedge, 75% compounding allocation"
            }
            
        except Exception as e:
            logger.error(f"Error calculating ladder allocation: {e}")
            return {
                "ladder_type": ladder_type.value,
                "allocation_percentage": 0.0,
                "allocation_amount": 0.0,
                "error": str(e),
                "rule": "Constitution v1.3 - LLMS Allocation"
            }
    
    def create_ladder_structure(
        self,
        ladder_type: LLMSLadderType,
        symbol: str,
        allocation: Decimal
    ) -> LLMSLadder:
        """
        Create new LLMS ladder structure.
        
        Args:
            ladder_type: Type of ladder to create
            symbol: Primary symbol for the ladder
            allocation: Capital allocation for the ladder
            
        Returns:
            New LLMSLadder instance
        """
        ladder_id = f"{ladder_type.value}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        ladder = LLMSLadder(
            ladder_id=ladder_id,
            ladder_type=ladder_type,
            symbol=symbol,
            positions=[],
            total_allocation=allocation,
            current_value=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            performance_metrics={
                "inception_date": datetime.now().isoformat(),
                "total_return": 0.0,
                "annualized_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "positions_count": 0
            },
            created_date=datetime.now(),
            last_rebalanced=datetime.now()
        )
        
        self.active_ladders[ladder_id] = ladder
        
        logger.info(f"Created LLMS ladder: {ladder_id} with ${allocation:,.2f} allocation")
        return ladder
    
    def get_llms_summary(self) -> Dict[str, Any]:
        """Get comprehensive LLMS summary."""
        total_ladders = len(self.active_ladders)
        total_positions = len(self.position_registry)
        
        # Calculate totals by ladder type
        hedge_ladders = [l for l in self.active_ladders.values() if l.ladder_type == LLMSLadderType.HEDGE_LADDER]
        compounding_ladders = [l for l in self.active_ladders.values() if l.ladder_type == LLMSLadderType.COMPOUNDING_LADDER]
        
        total_hedge_allocation = sum(l.total_allocation for l in hedge_ladders)
        total_compounding_allocation = sum(l.total_allocation for l in compounding_ladders)
        total_allocation = total_hedge_allocation + total_compounding_allocation
        
        return {
            "total_ladders": total_ladders,
            "total_positions": total_positions,
            "hedge_ladders": len(hedge_ladders),
            "compounding_ladders": len(compounding_ladders),
            "allocations": {
                "total_allocation": float(total_allocation),
                "hedge_allocation": float(total_hedge_allocation),
                "compounding_allocation": float(total_compounding_allocation),
                "hedge_percentage": float(total_hedge_allocation / total_allocation) if total_allocation > 0 else 0.0,
                "compounding_percentage": float(total_compounding_allocation / total_allocation) if total_allocation > 0 else 0.0
            },
            "specifications": {
                "call_delta_range": f"{self.parameters.call_delta_min:.3f}-{self.parameters.call_delta_max:.3f}",
                "put_otm_range": f"{self.parameters.put_otm_min_pct:.1%}-{self.parameters.put_otm_max_pct:.1%}",
                "dte_range": f"{self.parameters.min_dte}-{self.parameters.max_dte} days",
                "roll_thresholds": {
                    "delta": float(self.parameters.roll_delta_threshold),
                    "dte": self.parameters.roll_dte_threshold
                }
            },
            "rule": "Constitution v1.3 - LEAP Ladder Management System (LLMS)"
        }


# Global LLMS specifications manager
llms_specifications = LLMSSpecifications()

