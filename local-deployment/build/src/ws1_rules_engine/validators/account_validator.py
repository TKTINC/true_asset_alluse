"""
Account Type Validator

This module implements validation for account-specific rules per
Constitution sections §2 (Gen-Acc), §3 (Rev-Acc), and §4 (Com-Acc).
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, date, time
import logging

from ..constitution import ConstitutionV13

logger = logging.getLogger(__name__)


class AccountTypeValidator:
    """Validator for account-specific rules."""
    
    def __init__(self, constitution: ConstitutionV13):
        """
        Initialize account validator.
        
        Args:
            constitution: Constitution v1.3 instance
        """
        self.constitution = constitution
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate account-specific rules.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        try:
            account_type = context.get("account_type")
            if not account_type:
                return {
                    "valid": False,
                    "violations": ["Account type is required"],
                    "validator": "account_type"
                }
            
            # Route to specific account validator
            if account_type == "gen_acc":
                return self._validate_gen_acc(context)
            elif account_type == "rev_acc":
                return self._validate_rev_acc(context)
            elif account_type == "com_acc":
                return self._validate_com_acc(context)
            else:
                return {
                    "valid": False,
                    "violations": [f"Unknown account type: {account_type}"],
                    "validator": "account_type"
                }
                
        except Exception as e:
            logger.error(f"Error in account validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "validator": "account_type"
            }
    
    def _validate_gen_acc(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Gen-Acc specific rules per Constitution §2."""
        violations = []
        warnings = []
        
        strategy = context.get("strategy")
        symbol = context.get("symbol")
        delta = context.get("delta")
        dte = context.get("dte")
        action = context.get("action")
        
        # Get Gen-Acc rules
        gen_rules = self.constitution.gen_acc_rules
        
        # Validate strategy
        if strategy and action == "open":
            if strategy not in ["csp", "cc"]:
                violations.append(f"Gen-Acc only supports CSP/CC strategies, got {strategy}")
        
        # Validate instruments
        if symbol:
            if symbol not in gen_rules.PERMITTED_INSTRUMENTS:
                violations.append(f"Symbol {symbol} not permitted for Gen-Acc: {gen_rules.PERMITTED_INSTRUMENTS}")
        
        # Validate delta range
        if delta is not None:
            delta_val = Decimal(str(delta))
            if not (gen_rules.DELTA_MIN <= delta_val <= gen_rules.DELTA_MAX):
                violations.append(f"Delta {delta} not in Gen-Acc range {gen_rules.DELTA_MIN}-{gen_rules.DELTA_MAX}")
        
        # Validate DTE
        if dte is not None:
            stress_test_mode = context.get("stress_test_mode", False)
            if stress_test_mode:
                if not (gen_rules.DTE_STRESS_TEST[0] <= dte <= gen_rules.DTE_STRESS_TEST[1]):
                    violations.append(f"DTE {dte} not in stress-test range {gen_rules.DTE_STRESS_TEST}")
            else:
                if not (gen_rules.DTE_NORMAL[0] <= dte <= gen_rules.DTE_NORMAL[1]):
                    violations.append(f"DTE {dte} not in normal range {gen_rules.DTE_NORMAL}")
        
        # Validate timing
        trading_time = context.get("trading_time")
        if trading_time:
            if isinstance(trading_time, str):
                trading_time = datetime.fromisoformat(trading_time).time()
            
            if not (gen_rules.START_TIME <= trading_time <= gen_rules.END_TIME):
                violations.append(f"Trading time {trading_time} not in Gen-Acc window {gen_rules.START_TIME}-{gen_rules.END_TIME}")
        
        # Check trading day
        trading_date = context.get("trading_date")
        if trading_date:
            if isinstance(trading_date, str):
                trading_date = datetime.fromisoformat(trading_date).date()
            
            weekday = trading_date.strftime("%A").lower()
            if weekday != gen_rules.TRADING_DAY:
                warnings.append(f"Trading on {weekday}, Gen-Acc typically trades on {gen_rules.TRADING_DAY}")
        
        # Validate fork conditions
        if action == "fork":
            current_balance = context.get("current_balance")
            if current_balance:
                balance_val = Decimal(str(current_balance))
                if balance_val < gen_rules.FORK_THRESHOLD:
                    violations.append(f"Balance {balance_val} below fork threshold {gen_rules.FORK_THRESHOLD}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "account_type": "gen_acc",
            "validator": "account_type",
            "section": "§2"
        }
    
    def _validate_rev_acc(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Rev-Acc specific rules per Constitution §3."""
        violations = []
        warnings = []
        
        strategy = context.get("strategy")
        symbol = context.get("symbol")
        delta = context.get("delta")
        dte = context.get("dte")
        action = context.get("action")
        
        # Get Rev-Acc rules
        rev_rules = self.constitution.rev_acc_rules
        
        # Validate strategy
        if strategy and action == "open":
            if strategy not in ["csp", "cc"]:
                violations.append(f"Rev-Acc only supports CSP/CC strategies, got {strategy}")
        
        # Validate instruments (NVDA/TSLA only)
        if symbol:
            if symbol not in rev_rules.PERMITTED_INSTRUMENTS:
                violations.append(f"Symbol {symbol} not permitted for Rev-Acc: {rev_rules.PERMITTED_INSTRUMENTS}")
        
        # Validate delta range
        if delta is not None:
            delta_val = Decimal(str(delta))
            if not (rev_rules.DELTA_MIN <= delta_val <= rev_rules.DELTA_MAX):
                violations.append(f"Delta {delta} not in Rev-Acc range {rev_rules.DELTA_MIN}-{rev_rules.DELTA_MAX}")
        
        # Validate DTE
        if dte is not None:
            if not (rev_rules.DTE_MIN <= dte <= rev_rules.DTE_MAX):
                violations.append(f"DTE {dte} not in Rev-Acc range {rev_rules.DTE_MIN}-{rev_rules.DTE_MAX}")
        
        # Validate timing
        trading_time = context.get("trading_time")
        if trading_time:
            if isinstance(trading_time, str):
                trading_time = datetime.fromisoformat(trading_time).time()
            
            if not (rev_rules.START_TIME <= trading_time <= rev_rules.END_TIME):
                violations.append(f"Trading time {trading_time} not in Rev-Acc window {rev_rules.START_TIME}-{rev_rules.END_TIME}")
        
        # Check trading day
        trading_date = context.get("trading_date")
        if trading_date:
            if isinstance(trading_date, str):
                trading_date = datetime.fromisoformat(trading_date).date()
            
            weekday = trading_date.strftime("%A").lower()
            if weekday != rev_rules.TRADING_DAY:
                warnings.append(f"Trading on {weekday}, Rev-Acc typically trades on {rev_rules.TRADING_DAY}")
        
        # Validate fork conditions
        if action == "fork":
            current_balance = context.get("current_balance")
            if current_balance:
                balance_val = Decimal(str(current_balance))
                if balance_val < rev_rules.FORK_THRESHOLD:
                    violations.append(f"Balance {balance_val} below fork threshold {rev_rules.FORK_THRESHOLD}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "account_type": "rev_acc",
            "validator": "account_type",
            "section": "§3"
        }
    
    def _validate_com_acc(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Com-Acc specific rules per Constitution §4."""
        violations = []
        warnings = []
        
        strategy = context.get("strategy")
        symbol = context.get("symbol")
        delta = context.get("delta")
        dte = context.get("dte")
        action = context.get("action")
        
        # Get Com-Acc rules
        com_rules = self.constitution.com_acc_rules
        
        # Validate strategy (Covered Calls only)
        if strategy and action == "open":
            if strategy != "cc":
                violations.append(f"Com-Acc only supports Covered Calls, got {strategy}")
        
        # Validate instruments (Mag-7 only)
        if symbol:
            if symbol not in com_rules.PERMITTED_INSTRUMENTS:
                violations.append(f"Symbol {symbol} not in Mag-7: {com_rules.PERMITTED_INSTRUMENTS}")
        
        # Validate delta range
        if delta is not None:
            delta_val = Decimal(str(delta))
            if not (com_rules.DELTA_MIN <= delta_val <= com_rules.DELTA_MAX):
                violations.append(f"Delta {delta} not in Com-Acc range {com_rules.DELTA_MIN}-{com_rules.DELTA_MAX}")
        
        # Validate DTE (must be exactly 5)
        if dte is not None:
            if dte != com_rules.DTE:
                violations.append(f"DTE {dte} must be exactly {com_rules.DTE} for Com-Acc")
        
        # Validate timing
        trading_time = context.get("trading_time")
        if trading_time:
            if isinstance(trading_time, str):
                trading_time = datetime.fromisoformat(trading_time).time()
            
            if not (com_rules.START_TIME <= trading_time <= com_rules.END_TIME):
                violations.append(f"Trading time {trading_time} not in Com-Acc window {com_rules.START_TIME}-{com_rules.END_TIME}")
        
        # Check trading day
        trading_date = context.get("trading_date")
        if trading_date:
            if isinstance(trading_date, str):
                trading_date = datetime.fromisoformat(trading_date).date()
            
            weekday = trading_date.strftime("%A").lower()
            if weekday != com_rules.TRADING_DAY:
                warnings.append(f"Trading on {weekday}, Com-Acc typically trades on {com_rules.TRADING_DAY}")
        
        # Validate earnings coverage
        earnings_week = context.get("earnings_week", False)
        coverage_pct = context.get("coverage_pct")
        if earnings_week and coverage_pct:
            coverage_val = Decimal(str(coverage_pct))
            if coverage_val > com_rules.EARNINGS_COVERAGE_MAX:
                violations.append(f"Earnings week coverage {coverage_val:.1%} > max {com_rules.EARNINGS_COVERAGE_MAX:.1%}")
        
        # Validate profit taking
        premium_decay_pct = context.get("premium_decay_pct")
        if premium_decay_pct:
            decay_val = Decimal(str(premium_decay_pct))
            if decay_val >= com_rules.PROFIT_TAKE_THRESHOLD:
                warnings.append(f"Premium decay {decay_val:.1%} ≥ profit take threshold {com_rules.PROFIT_TAKE_THRESHOLD:.1%}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "account_type": "com_acc",
            "validator": "account_type",
            "section": "§4"
        }

