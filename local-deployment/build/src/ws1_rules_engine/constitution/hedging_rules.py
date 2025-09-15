"""
Hedging Rules - Constitution §5

This module implements the hedging rules that define when and how
the system implements protective hedges during market stress.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class HedgingRules:
    """Hedging rules per Constitution §5."""
    
    # Hedge budget allocation
    HEDGE_BUDGET_MIN_PCT = Decimal("0.05")  # 5% minimum
    HEDGE_BUDGET_MAX_PCT = Decimal("0.10")  # 10% maximum
    
    # VIX-based triggers
    VIX_HEDGED_WEEK = Decimal("50.0")   # VIX >50 → Hedged Week
    VIX_SAFE_MODE = Decimal("65.0")     # VIX >65 → SAFE mode
    VIX_KILL_SWITCH = Decimal("80.0")   # VIX >80 → Kill switch
    
    # Hedge instruments
    PRIMARY_HEDGE_INSTRUMENT = "SPX"    # SPX puts
    SECONDARY_HEDGE_INSTRUMENT = "VIX"  # VIX calls
    
    # Hedge parameters
    SPX_PUT_DELTA_TARGET = Decimal("0.10")  # 10Δ SPX puts
    VIX_CALL_STRIKE_BUFFER = Decimal("5.0")  # VIX strike = current + 5
    
    # Hedge duration
    MIN_HEDGE_DTE = 14  # 2 weeks minimum
    MAX_HEDGE_DTE = 45  # ~6 weeks maximum
    
    # Rebalancing
    REBALANCE_THRESHOLD = Decimal("0.20")  # 20% deviation triggers rebalance
    
    def __init__(self):
        """Initialize hedging rules."""
        pass
    
    def get_hedge_budget(self, total_capital: Decimal) -> Dict[str, Decimal]:
        """
        Calculate hedge budget allocation.
        
        Args:
            total_capital: Total account capital
            
        Returns:
            Hedge budget allocation
        """
        min_budget = total_capital * self.HEDGE_BUDGET_MIN_PCT
        max_budget = total_capital * self.HEDGE_BUDGET_MAX_PCT
        
        return {
            "min_budget": min_budget,
            "max_budget": max_budget,
            "recommended_budget": min_budget,  # Start conservative
            "budget_pct_min": float(self.HEDGE_BUDGET_MIN_PCT),
            "budget_pct_max": float(self.HEDGE_BUDGET_MAX_PCT)
        }
    
    def should_activate_hedged_week(self, vix_level: Decimal) -> bool:
        """
        Determine if Hedged Week should be activated.
        
        Args:
            vix_level: Current VIX level
            
        Returns:
            True if Hedged Week should be activated
        """
        return vix_level >= self.VIX_HEDGED_WEEK
    
    def should_enter_safe_mode(self, vix_level: Decimal) -> bool:
        """
        Determine if system should enter SAFE mode.
        
        Args:
            vix_level: Current VIX level
            
        Returns:
            True if SAFE mode should be activated
        """
        return vix_level >= self.VIX_SAFE_MODE
    
    def should_activate_kill_switch(self, vix_level: Decimal) -> bool:
        """
        Determine if kill switch should be activated.
        
        Args:
            vix_level: Current VIX level
            
        Returns:
            True if kill switch should be activated
        """
        return vix_level >= self.VIX_KILL_SWITCH
    
    def get_hedge_strategy(self, vix_level: Decimal, hedge_budget: Decimal) -> Dict[str, Any]:
        """
        Get hedge strategy based on VIX level and available budget.
        
        Args:
            vix_level: Current VIX level
            hedge_budget: Available hedge budget
            
        Returns:
            Hedge strategy parameters
        """
        strategy = {
            "vix_level": float(vix_level),
            "budget": float(hedge_budget),
            "instruments": [],
            "allocation": {},
            "urgency": "normal"
        }
        
        if vix_level >= self.VIX_KILL_SWITCH:
            strategy.update({
                "action": "kill_switch_activated",
                "urgency": "critical",
                "description": "All trading halted, liquidate positions"
            })
        elif vix_level >= self.VIX_SAFE_MODE:
            strategy.update({
                "action": "safe_mode",
                "urgency": "high",
                "instruments": [self.PRIMARY_HEDGE_INSTRUMENT, self.SECONDARY_HEDGE_INSTRUMENT],
                "allocation": {
                    "spx_puts": 0.7,  # 70% to SPX puts
                    "vix_calls": 0.3  # 30% to VIX calls
                },
                "description": "Maximum hedge deployment"
            })
        elif vix_level >= self.VIX_HEDGED_WEEK:
            strategy.update({
                "action": "hedged_week",
                "urgency": "elevated",
                "instruments": [self.PRIMARY_HEDGE_INSTRUMENT],
                "allocation": {
                    "spx_puts": 1.0  # 100% to SPX puts
                },
                "description": "Protective SPX puts deployment"
            })
        else:
            strategy.update({
                "action": "no_hedge_required",
                "description": "VIX below hedging threshold"
            })
        
        return strategy
    
    def get_spx_put_parameters(self, 
                              spx_price: Decimal,
                              hedge_budget: Decimal,
                              target_dte: Optional[int] = None) -> Dict[str, Any]:
        """
        Get SPX put hedge parameters.
        
        Args:
            spx_price: Current SPX price
            hedge_budget: Available budget for SPX puts
            target_dte: Target days to expiration
            
        Returns:
            SPX put parameters
        """
        if target_dte is None:
            target_dte = self.MIN_HEDGE_DTE
        
        # Estimate strike based on delta target
        # This is simplified - actual implementation would use option pricing
        estimated_strike = spx_price * (Decimal("1.0") - self.SPX_PUT_DELTA_TARGET)
        
        return {
            "instrument": self.PRIMARY_HEDGE_INSTRUMENT,
            "strategy": "long_puts",
            "target_delta": float(self.SPX_PUT_DELTA_TARGET),
            "estimated_strike": float(estimated_strike),
            "target_dte": target_dte,
            "budget": float(hedge_budget),
            "description": f"{self.SPX_PUT_DELTA_TARGET:.0%}Δ SPX puts, {target_dte}DTE"
        }
    
    def get_vix_call_parameters(self,
                               vix_level: Decimal,
                               hedge_budget: Decimal,
                               target_dte: Optional[int] = None) -> Dict[str, Any]:
        """
        Get VIX call hedge parameters.
        
        Args:
            vix_level: Current VIX level
            hedge_budget: Available budget for VIX calls
            target_dte: Target days to expiration
            
        Returns:
            VIX call parameters
        """
        if target_dte is None:
            target_dte = self.MIN_HEDGE_DTE
        
        # Strike = current VIX + buffer
        target_strike = vix_level + self.VIX_CALL_STRIKE_BUFFER
        
        return {
            "instrument": self.SECONDARY_HEDGE_INSTRUMENT,
            "strategy": "long_calls",
            "target_strike": float(target_strike),
            "strike_buffer": float(self.VIX_CALL_STRIKE_BUFFER),
            "target_dte": target_dte,
            "budget": float(hedge_budget),
            "description": f"VIX calls @ {target_strike:.0f}, {target_dte}DTE"
        }
    
    def should_rebalance_hedges(self,
                               current_hedge_value: Decimal,
                               target_hedge_value: Decimal) -> bool:
        """
        Determine if hedges should be rebalanced.
        
        Args:
            current_hedge_value: Current hedge portfolio value
            target_hedge_value: Target hedge portfolio value
            
        Returns:
            True if rebalancing is needed
        """
        if target_hedge_value == 0:
            return False
        
        deviation = abs(current_hedge_value - target_hedge_value) / target_hedge_value
        return deviation >= self.REBALANCE_THRESHOLD
    
    def get_hedge_exit_conditions(self) -> Dict[str, Any]:
        """Get conditions for exiting hedge positions."""
        return {
            "vix_normalization": {
                "trigger": f"VIX < {self.VIX_HEDGED_WEEK}",
                "action": "Begin hedge exit process",
                "timeline": "Gradual over 1-2 weeks"
            },
            "profit_taking": {
                "trigger": "Hedge P&L > 200% of premium paid",
                "action": "Take partial profits",
                "percentage": "50% of position"
            },
            "time_decay": {
                "trigger": "DTE < 7 days",
                "action": "Evaluate roll vs. exit",
                "condition": "Based on VIX level"
            },
            "portfolio_protection": {
                "trigger": "Main portfolio recovered losses",
                "action": "Reduce hedge exposure",
                "percentage": "25-50% reduction"
            }
        }
    
    def get_all_rules(self) -> Dict[str, Any]:
        """Get all hedging rules."""
        return {
            "version": "1.3",
            "hedge_budget": {
                "min_pct": float(self.HEDGE_BUDGET_MIN_PCT),
                "max_pct": float(self.HEDGE_BUDGET_MAX_PCT)
            },
            "vix_triggers": {
                "hedged_week": float(self.VIX_HEDGED_WEEK),
                "safe_mode": float(self.VIX_SAFE_MODE),
                "kill_switch": float(self.VIX_KILL_SWITCH)
            },
            "instruments": {
                "primary": self.PRIMARY_HEDGE_INSTRUMENT,
                "secondary": self.SECONDARY_HEDGE_INSTRUMENT
            },
            "parameters": {
                "spx_put_delta": float(self.SPX_PUT_DELTA_TARGET),
                "vix_call_buffer": float(self.VIX_CALL_STRIKE_BUFFER),
                "min_dte": self.MIN_HEDGE_DTE,
                "max_dte": self.MAX_HEDGE_DTE
            },
            "rebalancing": {
                "threshold": float(self.REBALANCE_THRESHOLD)
            },
            "exit_conditions": self.get_hedge_exit_conditions()
        }
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate hedging rules compliance.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        violations = []
        
        # Validate hedge budget
        if "hedge_budget_pct" in context:
            budget_pct = Decimal(str(context["hedge_budget_pct"]))
            if not (self.HEDGE_BUDGET_MIN_PCT <= budget_pct <= self.HEDGE_BUDGET_MAX_PCT):
                violations.append(f"Hedge budget {budget_pct:.1%} not in range {self.HEDGE_BUDGET_MIN_PCT:.1%}-{self.HEDGE_BUDGET_MAX_PCT:.1%}")
        
        # Validate VIX levels
        if "vix_level" in context:
            vix = Decimal(str(context["vix_level"]))
            if vix < 0:
                violations.append(f"VIX level cannot be negative: {vix}")
        
        # Validate hedge instruments
        if "hedge_instrument" in context:
            instrument = context["hedge_instrument"]
            valid_instruments = [self.PRIMARY_HEDGE_INSTRUMENT, self.SECONDARY_HEDGE_INSTRUMENT]
            if instrument not in valid_instruments:
                violations.append(f"Invalid hedge instrument {instrument}, must be one of {valid_instruments}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "section": "§5 Hedging Rules"
        }

