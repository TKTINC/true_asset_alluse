"""
Account-Specific Rules - Constitution §2, §3, §4

This module implements the specific rules for each account type:
- Gen-Acc (Generator) - Constitution §2
- Rev-Acc (Revenue) - Constitution §3  
- Com-Acc (Compounding) - Constitution §4

Each account type has distinct strategies, timing, and management rules.
"""

from decimal import Decimal
from datetime import time, datetime
from typing import Dict, List, Any, Tuple
from enum import Enum


class AccountType(str, Enum):
    """Account types."""
    GEN_ACC = "gen_acc"
    REV_ACC = "rev_acc"
    COM_ACC = "com_acc"


class GenAccRules:
    """Gen-Acc (Generator) rules per Constitution §2."""
    
    # Strategy parameters
    DELTA_MIN = Decimal("0.40")
    DELTA_MAX = Decimal("0.45")
    DTE_NORMAL = (0, 1)  # 0-1DTE
    DTE_STRESS_TEST = (1, 3)  # 1-3DTE for stress-testing
    
    # Timing
    TRADING_DAY = "thursday"
    START_TIME = time(9, 45)
    END_TIME = time(11, 0)
    
    # Instruments
    PERMITTED_INSTRUMENTS = [
        "AAPL", "MSFT", "AMZN", "GOOG", "SPY", "QQQ", "IWM"
    ]
    
    # Roll trigger
    ATR_ROLL_MULTIPLIER = Decimal("1.0")  # 1× ATR(5)
    
    # Assignment handling
    ASSIGNMENT_CC_DELTA_MIN = Decimal("0.20")
    ASSIGNMENT_CC_DELTA_MAX = Decimal("0.25")
    ASSIGNMENT_CC_DTE = 5
    
    # Forking
    FORK_THRESHOLD = Decimal("100000")  # $100K increments
    FORK_TYPE = "mini_alluse"
    FORK_MAX_DURATION_YEARS = 3
    FORK_MAX_MULTIPLE = Decimal("3.0")
    
    def __init__(self):
        """Initialize Gen-Acc rules."""
        pass
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters for Gen-Acc."""
        return {
            "primary_strategy": "csp",  # Cash-Secured Puts
            "secondary_strategy": "cc",  # Covered Calls (after assignment)
            "delta_range": (float(self.DELTA_MIN), float(self.DELTA_MAX)),
            "dte_normal": self.DTE_NORMAL,
            "dte_stress_test": self.DTE_STRESS_TEST,
            "permitted_instruments": self.PERMITTED_INSTRUMENTS
        }
    
    def get_timing_rules(self) -> Dict[str, Any]:
        """Get timing rules for Gen-Acc."""
        return {
            "trading_day": self.TRADING_DAY,
            "start_time": self.START_TIME,
            "end_time": self.END_TIME,
            "description": "Thursday 9:45-11:00"
        }
    
    def get_sizing_rules(self) -> Dict[str, Any]:
        """Get position sizing rules for Gen-Acc."""
        return {
            "capital_deployment": "95-100%",
            "diversification": "across 6-7 tickers",
            "per_symbol_limit": "≤25% of sleeve notional"
        }
    
    def get_roll_rules(self) -> Dict[str, Any]:
        """Get roll rules for Gen-Acc."""
        return {
            "trigger": f"spot ≤ strike - {self.ATR_ROLL_MULTIPLIER}× ATR(5)",
            "atr_multiplier": float(self.ATR_ROLL_MULTIPLIER),
            "action": "prep roll"
        }
    
    def get_assignment_rules(self) -> Dict[str, Any]:
        """Get assignment handling rules for Gen-Acc."""
        return {
            "action": "switch to CCs",
            "cc_delta_range": (float(self.ASSIGNMENT_CC_DELTA_MIN), float(self.ASSIGNMENT_CC_DELTA_MAX)),
            "cc_dte": self.ASSIGNMENT_CC_DTE,
            "exit_condition": "break-even or within 5% of pre-drawdown equity"
        }
    
    def get_pivot_rules(self) -> Dict[str, Any]:
        """Get pivot rules for drawdown scenarios."""
        return {
            "trigger": "drawdown ≥15%",
            "action": "CSPs suspended, CC-only until recovery"
        }
    
    def get_fork_rules(self) -> Dict[str, Any]:
        """Get forking rules for Gen-Acc."""
        return {
            "threshold": float(self.FORK_THRESHOLD),
            "increment": "each +$100K over base",
            "fork_type": self.FORK_TYPE,
            "max_duration_years": self.FORK_MAX_DURATION_YEARS,
            "max_multiple": float(self.FORK_MAX_MULTIPLE),
            "merge_target": "Com-Acc",
            "reinvesting": False
        }
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Gen-Acc rules compliance.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        violations = []
        
        # Validate delta range
        if "delta" in context:
            delta = Decimal(str(context["delta"]))
            if not (self.DELTA_MIN <= delta <= self.DELTA_MAX):
                violations.append(f"Delta {delta} not in range {self.DELTA_MIN}-{self.DELTA_MAX}")
        
        # Validate DTE
        if "dte" in context:
            dte = context["dte"]
            stress_test_mode = context.get("stress_test_mode", False)
            
            if stress_test_mode:
                if not (self.DTE_STRESS_TEST[0] <= dte <= self.DTE_STRESS_TEST[1]):
                    violations.append(f"DTE {dte} not in stress-test range {self.DTE_STRESS_TEST}")
            else:
                if not (self.DTE_NORMAL[0] <= dte <= self.DTE_NORMAL[1]):
                    violations.append(f"DTE {dte} not in normal range {self.DTE_NORMAL}")
        
        # Validate instrument
        if "symbol" in context:
            symbol = context["symbol"]
            if symbol not in self.PERMITTED_INSTRUMENTS:
                violations.append(f"Symbol {symbol} not in permitted instruments: {self.PERMITTED_INSTRUMENTS}")
        
        # Validate timing
        if "trading_time" in context:
            trading_time = context["trading_time"]
            if isinstance(trading_time, str):
                trading_time = datetime.fromisoformat(trading_time).time()
            
            if not (self.START_TIME <= trading_time <= self.END_TIME):
                violations.append(f"Trading time {trading_time} not in window {self.START_TIME}-{self.END_TIME}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "account_type": "gen_acc",
            "section": "§2"
        }


class RevAccRules:
    """Rev-Acc (Revenue) rules per Constitution §3."""
    
    # Strategy parameters
    DELTA_MIN = Decimal("0.30")
    DELTA_MAX = Decimal("0.35")
    DTE_MIN = 3
    DTE_MAX = 5
    
    # Timing
    TRADING_DAY = "wednesday"
    START_TIME = time(9, 45)
    END_TIME = time(11, 0)
    
    # Instruments (NVDA/TSLA only)
    PERMITTED_INSTRUMENTS = ["NVDA", "TSLA"]
    
    # Roll trigger
    ATR_ROLL_MULTIPLIER = Decimal("1.5")  # 1.5× ATR(5)
    
    # Assignment handling
    ASSIGNMENT_CC_DELTA_MIN = Decimal("0.20")
    ASSIGNMENT_CC_DELTA_MAX = Decimal("0.25")
    ASSIGNMENT_CC_DTE = 5
    
    # Quarterly reinvestment
    TAX_RESERVE_PCT = Decimal("0.30")  # 30%
    REINVEST_PCT = Decimal("0.70")     # 70%
    REINVEST_CONTRACTS_PCT = Decimal("0.75")  # 75% to contracts
    REINVEST_LEAPS_PCT = Decimal("0.25")      # 25% to LEAPs
    
    # Forking
    FORK_THRESHOLD = Decimal("500000")  # $500K increments
    FORK_TYPE = "full_alluse"
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters for Rev-Acc."""
        return {
            "primary_strategy": "csp",
            "secondary_strategy": "cc",
            "delta_range": (float(self.DELTA_MIN), float(self.DELTA_MAX)),
            "dte_range": (self.DTE_MIN, self.DTE_MAX),
            "permitted_instruments": self.PERMITTED_INSTRUMENTS
        }
    
    def get_timing_rules(self) -> Dict[str, Any]:
        """Get timing rules for Rev-Acc."""
        return {
            "trading_day": self.TRADING_DAY,
            "start_time": self.START_TIME,
            "end_time": self.END_TIME,
            "description": "Wednesday 9:45-11:00"
        }
    
    def get_sizing_rules(self) -> Dict[str, Any]:
        """Get position sizing rules for Rev-Acc."""
        return {
            "capital_deployment": "95-100%",
            "focus": "NVDA/TSLA concentrated",
            "per_symbol_limit": "≤25% of sleeve notional"
        }
    
    def get_roll_rules(self) -> Dict[str, Any]:
        """Get roll rules for Rev-Acc."""
        return {
            "trigger": f"spot ≤ strike - {self.ATR_ROLL_MULTIPLIER}× ATR(5)",
            "atr_multiplier": float(self.ATR_ROLL_MULTIPLIER),
            "action": "prep/roll"
        }
    
    def get_assignment_rules(self) -> Dict[str, Any]:
        """Get assignment handling rules for Rev-Acc."""
        return {
            "action": "switch to CC-only until recovery",
            "cc_delta_range": (float(self.ASSIGNMENT_CC_DELTA_MIN), float(self.ASSIGNMENT_CC_DELTA_MAX)),
            "cc_dte": self.ASSIGNMENT_CC_DTE
        }
    
    def get_reinvestment_rules(self) -> Dict[str, Any]:
        """Get quarterly reinvestment rules for Rev-Acc."""
        return {
            "frequency": "quarterly",
            "tax_reserve_pct": float(self.TAX_RESERVE_PCT),
            "reinvest_pct": float(self.REINVEST_PCT),
            "allocation": {
                "contracts_pct": float(self.REINVEST_CONTRACTS_PCT),
                "leaps_pct": float(self.REINVEST_LEAPS_PCT)
            },
            "llms_managed": True
        }
    
    def get_fork_rules(self) -> Dict[str, Any]:
        """Get forking rules for Rev-Acc."""
        return {
            "threshold": float(self.FORK_THRESHOLD),
            "increment": "each +$500K over base",
            "fork_type": self.FORK_TYPE,
            "creates": "new 40/30/30 ALL-USE account with own subs"
        }
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Rev-Acc rules compliance."""
        violations = []
        
        # Validate delta range
        if "delta" in context:
            delta = Decimal(str(context["delta"]))
            if not (self.DELTA_MIN <= delta <= self.DELTA_MAX):
                violations.append(f"Delta {delta} not in range {self.DELTA_MIN}-{self.DELTA_MAX}")
        
        # Validate DTE
        if "dte" in context:
            dte = context["dte"]
            if not (self.DTE_MIN <= dte <= self.DTE_MAX):
                violations.append(f"DTE {dte} not in range {self.DTE_MIN}-{self.DTE_MAX}")
        
        # Validate instrument
        if "symbol" in context:
            symbol = context["symbol"]
            if symbol not in self.PERMITTED_INSTRUMENTS:
                violations.append(f"Symbol {symbol} not in permitted instruments: {self.PERMITTED_INSTRUMENTS}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "account_type": "rev_acc",
            "section": "§3"
        }


class ComAccRules:
    """Com-Acc (Compounding) rules per Constitution §4."""
    
    # Strategy parameters (Covered Calls only)
    DELTA_MIN = Decimal("0.20")
    DELTA_MAX = Decimal("0.25")
    DTE = 5
    
    # Timing
    TRADING_DAY = "monday"
    START_TIME = time(9, 45)
    END_TIME = time(11, 0)
    
    # Instruments (Mag-7)
    PERMITTED_INSTRUMENTS = [
        "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "TSLA", "META"
    ]
    
    # Profit taking
    PROFIT_TAKE_THRESHOLD = Decimal("0.65")  # 65% premium decay
    
    # Earnings handling
    EARNINGS_COVERAGE_MAX = Decimal("0.50")  # ≤50% coverage
    
    # Quarterly reinvestment (same as Rev-Acc)
    TAX_RESERVE_PCT = Decimal("0.30")  # 30%
    REINVEST_PCT = Decimal("0.70")     # 70%
    REINVEST_CONTRACTS_PCT = Decimal("0.75")  # 75% to contracts
    REINVEST_LEAPS_PCT = Decimal("0.25")      # 25% to LEAPs
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters for Com-Acc."""
        return {
            "primary_strategy": "cc",  # Covered Calls only
            "delta_range": (float(self.DELTA_MIN), float(self.DELTA_MAX)),
            "dte": self.DTE,
            "permitted_instruments": self.PERMITTED_INSTRUMENTS
        }
    
    def get_timing_rules(self) -> Dict[str, Any]:
        """Get timing rules for Com-Acc."""
        return {
            "trading_day": self.TRADING_DAY,
            "start_time": self.START_TIME,
            "end_time": self.END_TIME,
            "description": "Monday 9:45-11:00"
        }
    
    def get_sizing_rules(self) -> Dict[str, Any]:
        """Get position sizing rules for Com-Acc."""
        return {
            "strategy": "Covered Calls on Mag-7 holdings",
            "instruments": "Mag-7 explicitly defined",
            "per_symbol_limit": "≤25% of sleeve notional"
        }
    
    def get_profit_take_rules(self) -> Dict[str, Any]:
        """Get profit taking rules for Com-Acc."""
        return {
            "threshold": float(self.PROFIT_TAKE_THRESHOLD),
            "description": f"Close if ≥{self.PROFIT_TAKE_THRESHOLD:.0%} premium decay"
        }
    
    def get_earnings_rules(self) -> Dict[str, Any]:
        """Get earnings handling rules for Com-Acc."""
        return {
            "max_coverage": float(self.EARNINGS_COVERAGE_MAX),
            "description": f"Reduce CC coverage to ≤{self.EARNINGS_COVERAGE_MAX:.0%} during earnings weeks"
        }
    
    def get_reinvestment_rules(self) -> Dict[str, Any]:
        """Get quarterly reinvestment rules for Com-Acc."""
        return {
            "frequency": "quarterly",
            "tax_reserve_pct": float(self.TAX_RESERVE_PCT),
            "reinvest_pct": float(self.REINVEST_PCT),
            "allocation": {
                "contracts_pct": float(self.REINVEST_CONTRACTS_PCT),
                "leaps_pct": float(self.REINVEST_LEAPS_PCT)
            },
            "llms_managed": True
        }
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Com-Acc rules compliance."""
        violations = []
        
        # Validate delta range
        if "delta" in context:
            delta = Decimal(str(context["delta"]))
            if not (self.DELTA_MIN <= delta <= self.DELTA_MAX):
                violations.append(f"Delta {delta} not in range {self.DELTA_MIN}-{self.DELTA_MAX}")
        
        # Validate DTE
        if "dte" in context:
            dte = context["dte"]
            if dte != self.DTE:
                violations.append(f"DTE {dte} must be exactly {self.DTE}")
        
        # Validate instrument
        if "symbol" in context:
            symbol = context["symbol"]
            if symbol not in self.PERMITTED_INSTRUMENTS:
                violations.append(f"Symbol {symbol} not in Mag-7: {self.PERMITTED_INSTRUMENTS}")
        
        # Validate strategy
        if "strategy" in context:
            strategy = context["strategy"]
            if strategy != "cc":
                violations.append(f"Com-Acc only supports Covered Calls, got {strategy}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "account_type": "com_acc",
            "section": "§4"
        }

