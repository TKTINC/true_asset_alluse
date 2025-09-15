"""
Protocol Engine Rules - Constitution §6

This module implements the Protocol Engine rules that provide ATR-based
risk management with 4-level escalation system. The Protocol Engine
monitors positions and escalates risk management based on market conditions.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class ProtocolLevel(str, Enum):
    """Protocol escalation levels."""
    LEVEL_0 = "level_0"  # Normal operations
    LEVEL_1 = "level_1"  # Enhanced monitoring  
    LEVEL_2 = "level_2"  # Recovery mode
    LEVEL_3 = "level_3"  # Preservation mode


class ProtocolEngineRules:
    """Protocol Engine rules per Constitution §6."""
    
    # ATR-based triggers
    LEVEL_1_TRIGGER = Decimal("1.0")   # 1× ATR(5) breach
    LEVEL_2_TRIGGER = Decimal("2.0")   # 2× ATR(5) breach  
    LEVEL_3_TRIGGER = Decimal("3.0")   # 3× ATR(5) breach
    
    # Monitoring frequencies (seconds)
    MONITORING_FREQUENCIES = {
        ProtocolLevel.LEVEL_0: 300,  # 5 minutes
        ProtocolLevel.LEVEL_1: 60,   # 1 minute
        ProtocolLevel.LEVEL_2: 30,   # 30 seconds
        ProtocolLevel.LEVEL_3: 1     # Real-time
    }
    
    # Actions per level
    LEVEL_ACTIONS = {
        ProtocolLevel.LEVEL_0: "normal_operations",
        ProtocolLevel.LEVEL_1: "enhanced_monitoring", 
        ProtocolLevel.LEVEL_2: "prep_roll_or_exit",
        ProtocolLevel.LEVEL_3: "immediate_exit"
    }
    
    # Exit conditions
    STOP_LOSS_MULTIPLIER = Decimal("3.0")  # 3× ATR stop-loss
    MAX_LOSS_PCT = Decimal("0.05")         # 5% max loss per position
    
    def __init__(self):
        """Initialize Protocol Engine rules."""
        pass
    
    def get_protocol_levels(self) -> Dict[str, Dict[str, Any]]:
        """Get all protocol levels and their definitions."""
        return {
            "level_0": {
                "name": "Normal Operations",
                "trigger": "No breach",
                "monitoring_frequency": self.MONITORING_FREQUENCIES[ProtocolLevel.LEVEL_0],
                "action": self.LEVEL_ACTIONS[ProtocolLevel.LEVEL_0],
                "description": "Standard 5-minute monitoring cycle"
            },
            "level_1": {
                "name": "Enhanced Monitoring",
                "trigger": f"Spot ≤ Strike - {self.LEVEL_1_TRIGGER}× ATR(5)",
                "monitoring_frequency": self.MONITORING_FREQUENCIES[ProtocolLevel.LEVEL_1],
                "action": self.LEVEL_ACTIONS[ProtocolLevel.LEVEL_1],
                "description": "Increased monitoring to 1-minute intervals"
            },
            "level_2": {
                "name": "Recovery Mode",
                "trigger": f"Spot ≤ Strike - {self.LEVEL_2_TRIGGER}× ATR(5)",
                "monitoring_frequency": self.MONITORING_FREQUENCIES[ProtocolLevel.LEVEL_2],
                "action": self.LEVEL_ACTIONS[ProtocolLevel.LEVEL_2],
                "description": "Prep roll within delta band or exit"
            },
            "level_3": {
                "name": "Preservation Mode",
                "trigger": f"Spot ≤ Strike - {self.LEVEL_3_TRIGGER}× ATR(5)",
                "monitoring_frequency": self.MONITORING_FREQUENCIES[ProtocolLevel.LEVEL_3],
                "action": self.LEVEL_ACTIONS[ProtocolLevel.LEVEL_3],
                "description": "Immediate market exit, enter SAFE mode"
            }
        }
    
    def calculate_protocol_level(self, 
                               spot_price: Decimal,
                               strike_price: Decimal, 
                               atr_5: Decimal,
                               position_type: str = "csp") -> ProtocolLevel:
        """
        Calculate current protocol level based on market conditions.
        
        Args:
            spot_price: Current spot price
            strike_price: Option strike price
            atr_5: 5-day ATR
            position_type: Position type (csp, cc, etc.)
            
        Returns:
            Current protocol level
        """
        if position_type == "csp":
            # For CSPs, breach is when spot falls below strike
            breach_amount = strike_price - spot_price
        elif position_type == "cc":
            # For CCs, breach is when spot rises above strike
            breach_amount = spot_price - strike_price
        else:
            # Default to CSP logic
            breach_amount = strike_price - spot_price
        
        if breach_amount <= 0:
            return ProtocolLevel.LEVEL_0
        
        # Calculate ATR multiples
        atr_multiple = breach_amount / atr_5 if atr_5 > 0 else Decimal("0")
        
        if atr_multiple >= self.LEVEL_3_TRIGGER:
            return ProtocolLevel.LEVEL_3
        elif atr_multiple >= self.LEVEL_2_TRIGGER:
            return ProtocolLevel.LEVEL_2
        elif atr_multiple >= self.LEVEL_1_TRIGGER:
            return ProtocolLevel.LEVEL_1
        else:
            return ProtocolLevel.LEVEL_0
    
    def get_required_actions(self, protocol_level: ProtocolLevel) -> List[str]:
        """
        Get required actions for a protocol level.
        
        Args:
            protocol_level: Current protocol level
            
        Returns:
            List of required actions
        """
        actions = []
        
        if protocol_level == ProtocolLevel.LEVEL_0:
            actions = [
                "Continue normal operations",
                "Monitor positions every 5 minutes"
            ]
        elif protocol_level == ProtocolLevel.LEVEL_1:
            actions = [
                "Increase monitoring to 1-minute intervals",
                "Prepare for potential roll or exit",
                "Alert risk management"
            ]
        elif protocol_level == ProtocolLevel.LEVEL_2:
            actions = [
                "Monitor every 30 seconds",
                "Prepare roll within delta band",
                "Calculate exit scenarios",
                "Consider early closure"
            ]
        elif protocol_level == ProtocolLevel.LEVEL_3:
            actions = [
                "Real-time monitoring",
                "Execute immediate market exit",
                "Enter SAFE mode",
                "Halt new position opening",
                "Generate incident report"
            ]
        
        return actions
    
    def should_exit_position(self,
                           spot_price: Decimal,
                           strike_price: Decimal,
                           atr_5: Decimal,
                           position_pnl: Decimal,
                           position_value: Decimal,
                           position_type: str = "csp") -> Dict[str, Any]:
        """
        Determine if position should be exited based on protocol rules.
        
        Args:
            spot_price: Current spot price
            strike_price: Option strike price
            atr_5: 5-day ATR
            position_pnl: Current position P&L
            position_value: Position notional value
            position_type: Position type
            
        Returns:
            Exit decision and reasoning
        """
        exit_reasons = []
        should_exit = False
        
        # Check ATR-based stop loss
        if position_type == "csp":
            breach_amount = strike_price - spot_price
        else:
            breach_amount = spot_price - strike_price
        
        if breach_amount > 0 and atr_5 > 0:
            atr_multiple = breach_amount / atr_5
            if atr_multiple >= self.STOP_LOSS_MULTIPLIER:
                exit_reasons.append(f"ATR stop-loss triggered: {atr_multiple:.2f}× ATR ≥ {self.STOP_LOSS_MULTIPLIER}×")
                should_exit = True
        
        # Check percentage-based stop loss
        if position_value > 0:
            loss_pct = abs(position_pnl) / position_value
            if position_pnl < 0 and loss_pct >= self.MAX_LOSS_PCT:
                exit_reasons.append(f"Max loss exceeded: {loss_pct:.2%} ≥ {self.MAX_LOSS_PCT:.1%}")
                should_exit = True
        
        # Check protocol level
        protocol_level = self.calculate_protocol_level(spot_price, strike_price, atr_5, position_type)
        if protocol_level == ProtocolLevel.LEVEL_3:
            exit_reasons.append("Protocol Level 3 triggered - immediate exit required")
            should_exit = True
        
        return {
            "should_exit": should_exit,
            "exit_reasons": exit_reasons,
            "protocol_level": protocol_level.value,
            "atr_multiple": float(breach_amount / atr_5) if atr_5 > 0 else 0,
            "loss_pct": float(abs(position_pnl) / position_value) if position_value > 0 else 0
        }
    
    def get_roll_parameters(self,
                          current_strike: Decimal,
                          spot_price: Decimal,
                          atr_5: Decimal,
                          account_type: str) -> Dict[str, Any]:
        """
        Get roll parameters based on account type and market conditions.
        
        Args:
            current_strike: Current option strike
            spot_price: Current spot price
            atr_5: 5-day ATR
            account_type: Account type (gen_acc, rev_acc, com_acc)
            
        Returns:
            Roll parameters
        """
        # Import account-specific delta ranges
        from .account_rules import GenAccRules, RevAccRules, ComAccRules
        
        if account_type == "gen_acc":
            rules = GenAccRules()
            delta_min, delta_max = rules.DELTA_MIN, rules.DELTA_MAX
        elif account_type == "rev_acc":
            rules = RevAccRules()
            delta_min, delta_max = rules.DELTA_MIN, rules.DELTA_MAX
        elif account_type == "com_acc":
            rules = ComAccRules()
            delta_min, delta_max = rules.DELTA_MIN, rules.DELTA_MAX
        else:
            # Default to Gen-Acc ranges
            delta_min, delta_max = Decimal("0.40"), Decimal("0.45")
        
        # Calculate suggested new strike based on delta band
        # This is a simplified calculation - actual implementation would use
        # option pricing models to determine strikes within delta range
        strike_adjustment = atr_5 * Decimal("0.5")  # Conservative adjustment
        
        return {
            "target_delta_min": float(delta_min),
            "target_delta_max": float(delta_max),
            "suggested_strike_adjustment": float(strike_adjustment),
            "roll_urgency": "high" if self.calculate_protocol_level(spot_price, current_strike, atr_5) >= ProtocolLevel.LEVEL_2 else "normal"
        }
    
    def get_all_rules(self) -> Dict[str, Any]:
        """Get all Protocol Engine rules."""
        return {
            "version": "1.3",
            "protocol_levels": self.get_protocol_levels(),
            "atr_triggers": {
                "level_1": float(self.LEVEL_1_TRIGGER),
                "level_2": float(self.LEVEL_2_TRIGGER),
                "level_3": float(self.LEVEL_3_TRIGGER)
            },
            "monitoring_frequencies": {
                level.value: freq for level, freq in self.MONITORING_FREQUENCIES.items()
            },
            "exit_rules": {
                "stop_loss_multiplier": float(self.STOP_LOSS_MULTIPLIER),
                "max_loss_pct": float(self.MAX_LOSS_PCT)
            },
            "description": "ATR-based 4-level escalation system for risk management"
        }
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Protocol Engine rules compliance.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        violations = []
        
        # Validate monitoring frequency
        if "protocol_level" in context:
            level = context["protocol_level"]
            if level not in [l.value for l in ProtocolLevel]:
                violations.append(f"Invalid protocol level: {level}")
        
        # Validate ATR calculations
        if all(k in context for k in ["spot_price", "strike_price", "atr_5"]):
            spot = Decimal(str(context["spot_price"]))
            strike = Decimal(str(context["strike_price"]))
            atr = Decimal(str(context["atr_5"]))
            
            if atr <= 0:
                violations.append(f"ATR must be positive, got {atr}")
            
            if spot <= 0 or strike <= 0:
                violations.append(f"Prices must be positive: spot={spot}, strike={strike}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "section": "§6 Protocol Engine"
        }

