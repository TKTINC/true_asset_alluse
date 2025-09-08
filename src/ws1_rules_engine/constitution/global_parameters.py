"""
Global Parameters - Constitution §0

This module defines all global parameters that apply across the entire
True-Asset-ALLUSE system as specified in Constitution v1.3 §0.
"""

from decimal import Decimal
from typing import Dict, Any


class GlobalParameters:
    """Global parameters per Constitution v1.3 §0."""
    
    # Base Split (40/30/30 → Gen/Rev/Com)
    GEN_ACC_RATIO = Decimal("0.40")
    REV_ACC_RATIO = Decimal("0.30") 
    COM_ACC_RATIO = Decimal("0.30")
    
    # Position Sizing
    MIN_CAPITAL_DEPLOYMENT = Decimal("0.95")  # 95%
    MAX_CAPITAL_DEPLOYMENT = Decimal("1.00")  # 100%
    MAX_PER_SYMBOL_EXPOSURE = Decimal("0.25")  # 25% of sleeve notional
    
    # Order Management
    ORDER_SLICE_THRESHOLD = 50  # contracts
    MAX_SLIPPAGE_PCT = Decimal("0.05")  # 5% worse than mid
    CANCEL_REPLACE_TIMEOUT = 3  # seconds
    
    # Risk Limits
    MAX_MARGIN_USE = Decimal("0.60")  # 60%
    DRAWDOWN_PIVOT_THRESHOLD = Decimal("0.15")  # 15% from high
    VIX_DRAWDOWN_THRESHOLD = Decimal("30.0")  # VIX <30 for pivot
    
    # Monitoring Frequency (seconds)
    MONITORING_FREQUENCIES = {
        "level_0": 300,  # 5 minutes
        "level_1": 60,   # 1 minute  
        "level_2": 30,   # 30 seconds during rolls
        "level_3": 1     # real-time until exit
    }
    
    # Circuit Breakers
    VIX_HEDGED_WEEK = Decimal("50.0")   # VIX >50 → Hedged Week
    VIX_SAFE_MODE = Decimal("65.0")     # VIX >65 → SAFE mode
    VIX_KILL_SWITCH = Decimal("80.0")   # VIX >80 → Kill switch
    
    # Forking Thresholds
    GEN_ACC_FORK_THRESHOLD = Decimal("100000")  # $100K
    REV_ACC_FORK_THRESHOLD = Decimal("500000")  # $500K
    
    # Liquidity Requirements
    MIN_OPEN_INTEREST = 500
    MIN_DAILY_VOLUME = 100
    MAX_SPREAD_PCT = Decimal("0.05")      # 5% of mid
    MAX_ORDER_SIZE_PCT = Decimal("0.10")  # 10% of ADV
    
    # Tax and Reinvestment
    TAX_RESERVE_PCT = Decimal("0.30")     # 30%
    REINVEST_CONTRACTS_PCT = Decimal("0.75")  # 75%
    REINVEST_LEAPS_PCT = Decimal("0.25")      # 25%
    
    def __init__(self):
        """Initialize global parameters."""
        self._validate_ratios()
    
    def _validate_ratios(self):
        """Validate that account ratios sum to 1.0."""
        total = self.GEN_ACC_RATIO + self.REV_ACC_RATIO + self.COM_ACC_RATIO
        if abs(total - Decimal("1.0")) > Decimal("0.001"):
            raise ValueError(f"Account ratios must sum to 1.0, got {total}")
        
        reinvest_total = self.REINVEST_CONTRACTS_PCT + self.REINVEST_LEAPS_PCT
        if abs(reinvest_total - Decimal("1.0")) > Decimal("0.001"):
            raise ValueError(f"Reinvestment ratios must sum to 1.0, got {reinvest_total}")
    
    def get_account_split(self, total_capital: Decimal) -> Dict[str, Decimal]:
        """
        Calculate account split based on total capital.
        
        Args:
            total_capital: Total capital to split
            
        Returns:
            Dict with account allocations
        """
        return {
            "gen_acc": total_capital * self.GEN_ACC_RATIO,
            "rev_acc": total_capital * self.REV_ACC_RATIO,
            "com_acc": total_capital * self.COM_ACC_RATIO
        }
    
    def get_position_sizing_limits(self, sleeve_capital: Decimal) -> Dict[str, Decimal]:
        """
        Get position sizing limits for a sleeve.
        
        Args:
            sleeve_capital: Capital available in the sleeve
            
        Returns:
            Dict with sizing limits
        """
        return {
            "min_deployment": sleeve_capital * self.MIN_CAPITAL_DEPLOYMENT,
            "max_deployment": sleeve_capital * self.MAX_CAPITAL_DEPLOYMENT,
            "max_per_symbol": sleeve_capital * self.MAX_PER_SYMBOL_EXPOSURE
        }
    
    def get_monitoring_frequency(self, protocol_level: str) -> int:
        """
        Get monitoring frequency for protocol level.
        
        Args:
            protocol_level: Protocol level (level_0, level_1, level_2, level_3)
            
        Returns:
            Monitoring frequency in seconds
        """
        return self.MONITORING_FREQUENCIES.get(protocol_level, 300)
    
    def get_circuit_breaker_level(self, vix_level: Decimal) -> str:
        """
        Determine circuit breaker level based on VIX.
        
        Args:
            vix_level: Current VIX level
            
        Returns:
            Circuit breaker level
        """
        if vix_level >= self.VIX_KILL_SWITCH:
            return "kill_switch"
        elif vix_level >= self.VIX_SAFE_MODE:
            return "safe_mode"
        elif vix_level >= self.VIX_HEDGED_WEEK:
            return "hedged_week"
        else:
            return "normal"
    
    def should_pivot_to_drawdown_mode(self, drawdown_pct: Decimal, vix_level: Decimal) -> bool:
        """
        Check if system should pivot to drawdown mode.
        
        Per Constitution: if sleeve equity ≤ –15% from high AND VIX <30 
        → suspend CSPs, CC-only until recovery.
        
        Args:
            drawdown_pct: Current drawdown percentage (positive value)
            vix_level: Current VIX level
            
        Returns:
            True if should pivot to drawdown mode
        """
        return (drawdown_pct >= self.DRAWDOWN_PIVOT_THRESHOLD and 
                vix_level < self.VIX_DRAWDOWN_THRESHOLD)
    
    def validate_liquidity(self, 
                          open_interest: int,
                          daily_volume: int, 
                          bid_ask_spread: Decimal,
                          mid_price: Decimal,
                          order_size: int,
                          avg_daily_volume: int) -> Dict[str, Any]:
        """
        Validate liquidity requirements per Constitution §8.
        
        Args:
            open_interest: Option open interest
            daily_volume: Daily option volume
            bid_ask_spread: Bid-ask spread
            mid_price: Mid price
            order_size: Proposed order size
            avg_daily_volume: Average daily volume
            
        Returns:
            Validation result
        """
        violations = []
        
        if open_interest < self.MIN_OPEN_INTEREST:
            violations.append(f"Open interest {open_interest} < {self.MIN_OPEN_INTEREST}")
        
        if daily_volume < self.MIN_DAILY_VOLUME:
            violations.append(f"Daily volume {daily_volume} < {self.MIN_DAILY_VOLUME}")
        
        if mid_price > 0:
            spread_pct = bid_ask_spread / mid_price
            if spread_pct > self.MAX_SPREAD_PCT:
                violations.append(f"Spread {spread_pct:.3%} > {self.MAX_SPREAD_PCT:.1%}")
        
        if avg_daily_volume > 0:
            order_size_pct = Decimal(order_size) / Decimal(avg_daily_volume)
            if order_size_pct > self.MAX_ORDER_SIZE_PCT:
                violations.append(f"Order size {order_size_pct:.1%} > {self.MAX_ORDER_SIZE_PCT:.1%}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "details": {
                "open_interest": open_interest,
                "daily_volume": daily_volume,
                "spread_pct": float(bid_ask_spread / mid_price) if mid_price > 0 else 0,
                "order_size_pct": float(Decimal(order_size) / Decimal(avg_daily_volume)) if avg_daily_volume > 0 else 0
            }
        }
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """Get all global parameters as a dictionary."""
        return {
            "version": "1.3",
            "account_ratios": {
                "gen_acc": float(self.GEN_ACC_RATIO),
                "rev_acc": float(self.REV_ACC_RATIO),
                "com_acc": float(self.COM_ACC_RATIO)
            },
            "position_sizing": {
                "min_deployment_pct": float(self.MIN_CAPITAL_DEPLOYMENT),
                "max_deployment_pct": float(self.MAX_CAPITAL_DEPLOYMENT),
                "max_per_symbol_pct": float(self.MAX_PER_SYMBOL_EXPOSURE)
            },
            "order_management": {
                "slice_threshold": self.ORDER_SLICE_THRESHOLD,
                "max_slippage_pct": float(self.MAX_SLIPPAGE_PCT),
                "cancel_replace_timeout": self.CANCEL_REPLACE_TIMEOUT
            },
            "risk_limits": {
                "max_margin_use": float(self.MAX_MARGIN_USE),
                "drawdown_pivot_threshold": float(self.DRAWDOWN_PIVOT_THRESHOLD),
                "vix_drawdown_threshold": float(self.VIX_DRAWDOWN_THRESHOLD)
            },
            "monitoring_frequencies": self.MONITORING_FREQUENCIES,
            "circuit_breakers": {
                "vix_hedged_week": float(self.VIX_HEDGED_WEEK),
                "vix_safe_mode": float(self.VIX_SAFE_MODE),
                "vix_kill_switch": float(self.VIX_KILL_SWITCH)
            },
            "forking_thresholds": {
                "gen_acc": float(self.GEN_ACC_FORK_THRESHOLD),
                "rev_acc": float(self.REV_ACC_FORK_THRESHOLD)
            },
            "liquidity_requirements": {
                "min_open_interest": self.MIN_OPEN_INTEREST,
                "min_daily_volume": self.MIN_DAILY_VOLUME,
                "max_spread_pct": float(self.MAX_SPREAD_PCT),
                "max_order_size_pct": float(self.MAX_ORDER_SIZE_PCT)
            },
            "tax_and_reinvestment": {
                "tax_reserve_pct": float(self.TAX_RESERVE_PCT),
                "reinvest_contracts_pct": float(self.REINVEST_CONTRACTS_PCT),
                "reinvest_leaps_pct": float(self.REINVEST_LEAPS_PCT)
            }
        }

