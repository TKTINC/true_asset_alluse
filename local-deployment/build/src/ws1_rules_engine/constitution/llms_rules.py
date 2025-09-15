"""
LLMS Rules - Constitution §17

This module implements the LLMS (Leap Ladder Management System/Service) rules
that define how LEAP options are managed for growth and hedging purposes.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class LLMSLadderType(str, Enum):
    """LLMS ladder types."""
    GROWTH = "growth"
    HEDGE = "hedge"


class LLMSRules:
    """LLMS rules per Constitution §17."""
    
    # LEAP duration ranges
    GROWTH_LEAP_MIN_MONTHS = 12  # 12 months minimum
    GROWTH_LEAP_MAX_MONTHS = 18  # 18 months maximum
    HEDGE_LEAP_MIN_MONTHS = 6    # 6 months minimum
    HEDGE_LEAP_MAX_MONTHS = 12   # 12 months maximum
    
    # Allocation from reinvestment
    REINVESTMENT_LEAP_PCT = Decimal("0.25")  # 25% of reinvestment to LEAPs
    
    # Ladder management
    LADDER_REVIEW_FREQUENCY_DAYS = 90  # Quarterly review
    REBALANCE_THRESHOLD = Decimal("0.20")  # 20% deviation triggers rebalance
    
    # Growth LEAP parameters
    GROWTH_LEAP_DELTA_MIN = Decimal("0.60")  # 60Δ minimum
    GROWTH_LEAP_DELTA_MAX = Decimal("0.80")  # 80Δ maximum
    
    # Hedge LEAP parameters  
    HEDGE_LEAP_DELTA_MIN = Decimal("0.20")   # 20Δ minimum
    HEDGE_LEAP_DELTA_MAX = Decimal("0.40")   # 40Δ maximum
    
    # Profit taking
    PROFIT_TAKE_THRESHOLD = Decimal("2.00")  # 200% gain
    PARTIAL_PROFIT_THRESHOLD = Decimal("1.00")  # 100% gain
    PARTIAL_PROFIT_PCT = Decimal("0.50")     # Take 50% profits
    
    # Stop loss
    STOP_LOSS_THRESHOLD = Decimal("-0.50")   # -50% loss
    
    # Permitted instruments (Mag-7 + major indices)
    GROWTH_INSTRUMENTS = [
        "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "TSLA", "META",  # Mag-7
        "SPY", "QQQ", "IWM"  # Major indices
    ]
    
    HEDGE_INSTRUMENTS = [
        "SPY", "QQQ", "IWM",  # Index puts for hedging
        "VIX"  # VIX calls for volatility hedge
    ]
    
    def __init__(self):
        """Initialize LLMS rules."""
        pass
    
    def get_ladder_allocation(self, 
                            reinvestment_amount: Decimal,
                            account_type: str) -> Dict[str, Decimal]:
        """
        Calculate LEAP ladder allocation from reinvestment.
        
        Args:
            reinvestment_amount: Total reinvestment amount
            account_type: Account type (rev_acc or com_acc)
            
        Returns:
            LEAP allocation breakdown
        """
        leap_budget = reinvestment_amount * self.REINVESTMENT_LEAP_PCT
        
        # Split between growth and hedge LEAPs
        if account_type in ["rev_acc", "com_acc"]:
            growth_allocation = leap_budget * Decimal("0.70")  # 70% growth
            hedge_allocation = leap_budget * Decimal("0.30")   # 30% hedge
        else:
            # Gen-Acc doesn't reinvest, so no LEAP allocation
            growth_allocation = Decimal("0")
            hedge_allocation = Decimal("0")
        
        return {
            "total_leap_budget": leap_budget,
            "growth_allocation": growth_allocation,
            "hedge_allocation": hedge_allocation,
            "growth_pct": 0.70 if account_type in ["rev_acc", "com_acc"] else 0,
            "hedge_pct": 0.30 if account_type in ["rev_acc", "com_acc"] else 0
        }
    
    def get_growth_leap_parameters(self, 
                                 symbol: str,
                                 current_price: Decimal,
                                 target_allocation: Decimal) -> Dict[str, Any]:
        """
        Get growth LEAP parameters for a symbol.
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            target_allocation: Target allocation amount
            
        Returns:
            Growth LEAP parameters
        """
        if symbol not in self.GROWTH_INSTRUMENTS:
            raise ValueError(f"Symbol {symbol} not permitted for growth LEAPs")
        
        # Calculate target strike range based on delta
        # This is simplified - actual implementation would use option pricing
        strike_min = current_price * (Decimal("1.0") - self.GROWTH_LEAP_DELTA_MAX + Decimal("0.5"))
        strike_max = current_price * (Decimal("1.0") - self.GROWTH_LEAP_DELTA_MIN + Decimal("0.5"))
        
        return {
            "symbol": symbol,
            "strategy": "long_calls",
            "ladder_type": LLMSLadderType.GROWTH.value,
            "target_allocation": float(target_allocation),
            "delta_range": (float(self.GROWTH_LEAP_DELTA_MIN), float(self.GROWTH_LEAP_DELTA_MAX)),
            "duration_months": (self.GROWTH_LEAP_MIN_MONTHS, self.GROWTH_LEAP_MAX_MONTHS),
            "strike_range": (float(strike_min), float(strike_max)),
            "profit_targets": {
                "partial": float(self.PARTIAL_PROFIT_THRESHOLD),
                "full": float(self.PROFIT_TAKE_THRESHOLD)
            },
            "stop_loss": float(self.STOP_LOSS_THRESHOLD)
        }
    
    def get_hedge_leap_parameters(self,
                                symbol: str, 
                                current_price: Decimal,
                                target_allocation: Decimal) -> Dict[str, Any]:
        """
        Get hedge LEAP parameters for a symbol.
        
        Args:
            symbol: Stock/index symbol
            current_price: Current price
            target_allocation: Target allocation amount
            
        Returns:
            Hedge LEAP parameters
        """
        if symbol not in self.HEDGE_INSTRUMENTS:
            raise ValueError(f"Symbol {symbol} not permitted for hedge LEAPs")
        
        # For hedge LEAPs, we typically use puts (except VIX calls)
        if symbol == "VIX":
            strategy = "long_calls"
            strike_adjustment = Decimal("1.1")  # Slightly OTM calls
        else:
            strategy = "long_puts"
            strike_adjustment = Decimal("0.9")  # Slightly OTM puts
        
        target_strike = current_price * strike_adjustment
        
        return {
            "symbol": symbol,
            "strategy": strategy,
            "ladder_type": LLMSLadderType.HEDGE.value,
            "target_allocation": float(target_allocation),
            "delta_range": (float(self.HEDGE_LEAP_DELTA_MIN), float(self.HEDGE_LEAP_DELTA_MAX)),
            "duration_months": (self.HEDGE_LEAP_MIN_MONTHS, self.HEDGE_LEAP_MAX_MONTHS),
            "target_strike": float(target_strike),
            "profit_targets": {
                "partial": float(self.PARTIAL_PROFIT_THRESHOLD),
                "full": float(self.PROFIT_TAKE_THRESHOLD)
            },
            "stop_loss": float(self.STOP_LOSS_THRESHOLD)
        }
    
    def should_rebalance_ladder(self,
                              current_allocation: Dict[str, Decimal],
                              target_allocation: Dict[str, Decimal]) -> bool:
        """
        Determine if LEAP ladder should be rebalanced.
        
        Args:
            current_allocation: Current allocation by symbol
            target_allocation: Target allocation by symbol
            
        Returns:
            True if rebalancing is needed
        """
        for symbol in target_allocation:
            if symbol not in current_allocation:
                return True
            
            target = target_allocation[symbol]
            current = current_allocation[symbol]
            
            if target > 0:
                deviation = abs(current - target) / target
                if deviation >= self.REBALANCE_THRESHOLD:
                    return True
        
        return False
    
    def get_profit_taking_action(self, 
                               position_pnl_pct: Decimal) -> Dict[str, Any]:
        """
        Determine profit taking action based on P&L.
        
        Args:
            position_pnl_pct: Position P&L as percentage
            
        Returns:
            Profit taking recommendation
        """
        if position_pnl_pct >= self.PROFIT_TAKE_THRESHOLD:
            return {
                "action": "take_full_profits",
                "percentage": 1.0,
                "reason": f"P&L {position_pnl_pct:.1%} ≥ {self.PROFIT_TAKE_THRESHOLD:.0%} threshold"
            }
        elif position_pnl_pct >= self.PARTIAL_PROFIT_THRESHOLD:
            return {
                "action": "take_partial_profits",
                "percentage": float(self.PARTIAL_PROFIT_PCT),
                "reason": f"P&L {position_pnl_pct:.1%} ≥ {self.PARTIAL_PROFIT_THRESHOLD:.0%} threshold"
            }
        else:
            return {
                "action": "hold",
                "percentage": 0.0,
                "reason": f"P&L {position_pnl_pct:.1%} below profit taking thresholds"
            }
    
    def should_stop_out(self, position_pnl_pct: Decimal) -> bool:
        """
        Determine if position should be stopped out.
        
        Args:
            position_pnl_pct: Position P&L as percentage
            
        Returns:
            True if position should be stopped out
        """
        return position_pnl_pct <= self.STOP_LOSS_THRESHOLD
    
    def get_ai_optimization_rules(self) -> Dict[str, Any]:
        """Get AI optimization rules per Constitution §13."""
        return {
            "purpose": "AI analyzes historical LEAP ladder performance",
            "output": "Suggests refinements to allocation, timing, strikes",
            "approval_required": True,
            "trading_decisions": False,
            "review_frequency": "quarterly",
            "metrics_analyzed": [
                "historical_performance",
                "correlation_analysis", 
                "volatility_patterns",
                "optimal_entry_timing",
                "strike_selection_efficiency"
            ],
            "human_approval_required_for": [
                "allocation_changes",
                "new_instruments",
                "strategy_modifications",
                "risk_parameter_changes"
            ]
        }
    
    def get_reporting_requirements(self) -> Dict[str, List[str]]:
        """Get LLMS reporting requirements."""
        return {
            "quarterly": [
                "ladder_performance_summary",
                "allocation_vs_target",
                "profit_loss_breakdown",
                "rebalancing_actions",
                "ai_optimization_suggestions"
            ],
            "annual": [
                "full_ladder_review",
                "strategy_effectiveness_analysis",
                "risk_adjusted_returns",
                "correlation_with_main_portfolio"
            ]
        }
    
    def get_all_rules(self) -> Dict[str, Any]:
        """Get all LLMS rules."""
        return {
            "version": "1.3",
            "ladder_types": [t.value for t in LLMSLadderType],
            "duration_ranges": {
                "growth_months": (self.GROWTH_LEAP_MIN_MONTHS, self.GROWTH_LEAP_MAX_MONTHS),
                "hedge_months": (self.HEDGE_LEAP_MIN_MONTHS, self.HEDGE_LEAP_MAX_MONTHS)
            },
            "allocation": {
                "reinvestment_pct": float(self.REINVESTMENT_LEAP_PCT),
                "growth_hedge_split": {"growth": 0.70, "hedge": 0.30}
            },
            "delta_ranges": {
                "growth": (float(self.GROWTH_LEAP_DELTA_MIN), float(self.GROWTH_LEAP_DELTA_MAX)),
                "hedge": (float(self.HEDGE_LEAP_DELTA_MIN), float(self.HEDGE_LEAP_DELTA_MAX))
            },
            "instruments": {
                "growth": self.GROWTH_INSTRUMENTS,
                "hedge": self.HEDGE_INSTRUMENTS
            },
            "management": {
                "review_frequency_days": self.LADDER_REVIEW_FREQUENCY_DAYS,
                "rebalance_threshold": float(self.REBALANCE_THRESHOLD),
                "profit_take_threshold": float(self.PROFIT_TAKE_THRESHOLD),
                "partial_profit_threshold": float(self.PARTIAL_PROFIT_THRESHOLD),
                "stop_loss_threshold": float(self.STOP_LOSS_THRESHOLD)
            },
            "ai_optimization": self.get_ai_optimization_rules(),
            "reporting": self.get_reporting_requirements()
        }
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate LLMS rules compliance.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        violations = []
        
        # Validate ladder type
        if "ladder_type" in context:
            ladder_type = context["ladder_type"]
            if ladder_type not in [t.value for t in LLMSLadderType]:
                violations.append(f"Invalid ladder type: {ladder_type}")
        
        # Validate instruments
        if "symbol" in context and "ladder_type" in context:
            symbol = context["symbol"]
            ladder_type = context["ladder_type"]
            
            if ladder_type == LLMSLadderType.GROWTH.value:
                if symbol not in self.GROWTH_INSTRUMENTS:
                    violations.append(f"Symbol {symbol} not permitted for growth LEAPs")
            elif ladder_type == LLMSLadderType.HEDGE.value:
                if symbol not in self.HEDGE_INSTRUMENTS:
                    violations.append(f"Symbol {symbol} not permitted for hedge LEAPs")
        
        # Validate delta ranges
        if "delta" in context and "ladder_type" in context:
            delta = Decimal(str(context["delta"]))
            ladder_type = context["ladder_type"]
            
            if ladder_type == LLMSLadderType.GROWTH.value:
                if not (self.GROWTH_LEAP_DELTA_MIN <= delta <= self.GROWTH_LEAP_DELTA_MAX):
                    violations.append(f"Growth LEAP delta {delta} not in range {self.GROWTH_LEAP_DELTA_MIN}-{self.GROWTH_LEAP_DELTA_MAX}")
            elif ladder_type == LLMSLadderType.HEDGE.value:
                if not (self.HEDGE_LEAP_DELTA_MIN <= delta <= self.HEDGE_LEAP_DELTA_MAX):
                    violations.append(f"Hedge LEAP delta {delta} not in range {self.HEDGE_LEAP_DELTA_MIN}-{self.HEDGE_LEAP_DELTA_MAX}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "section": "§17 LLMS Rules"
        }

