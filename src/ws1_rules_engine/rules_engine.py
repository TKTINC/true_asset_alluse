"""
Rules Engine - Core WS1 Component

This module implements the main Rules Engine that orchestrates all constitutional
rules and provides the primary interface for rule validation and enforcement.

The Rules Engine is the central component that ensures 100% deterministic
rule execution with zero AI wealth management decisions.
"""

from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, time
import logging
from enum import Enum

from .constitution import ConstitutionV13
from .validators import (
    AccountTypeValidator,
    PositionSizeValidator, 
    TimingValidator,
    DeltaRangeValidator,
    LiquidityValidator
)
from .audit import AuditTrailManager
from .compliance import ComplianceChecker
from ..common.exceptions import RuleViolationError, ValidationError

logger = logging.getLogger(__name__)


class RuleExecutionResult(str, Enum):
    """Rule execution results."""
    APPROVED = "approved"
    REJECTED = "rejected"
    WARNING = "warning"
    ERROR = "error"


class RulesEngine:
    """
    Main Rules Engine implementing Constitution v1.3.
    
    This engine provides the primary interface for:
    - Rule validation and enforcement
    - Trading decision approval/rejection
    - Compliance checking
    - Audit trail generation
    
    All decisions are deterministic and traceable to Constitution sections.
    """
    
    def __init__(self, audit_manager: Optional[AuditTrailManager] = None):
        """
        Initialize Rules Engine.
        
        Args:
            audit_manager: Optional audit trail manager
        """
        self.constitution = ConstitutionV13()
        self.audit_manager = audit_manager or AuditTrailManager()
        self.compliance_checker = ComplianceChecker(self.constitution)
        
        # Initialize validators
        self.account_validator = AccountTypeValidator(self.constitution)
        self.position_validator = PositionSizeValidator(self.constitution)
        self.timing_validator = TimingValidator(self.constitution)
        self.delta_validator = DeltaRangeValidator(self.constitution)
        self.liquidity_validator = LiquidityValidator(self.constitution)
        
        logger.info(f"Rules Engine initialized with Constitution v{self.constitution.VERSION}")
    
    def validate_trading_decision(self, 
                                decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a trading decision against all applicable rules.
        
        Args:
            decision_context: Context containing all decision parameters
            
        Returns:
            Validation result with approval/rejection and reasoning
        """
        try:
            # Extract key parameters
            account_type = decision_context.get("account_type")
            action = decision_context.get("action")  # open, close, roll
            strategy = decision_context.get("strategy")  # csp, cc, leap
            
            logger.info(f"Validating trading decision: {action} {strategy} for {account_type}")
            
            # Run all applicable validations
            validation_results = []
            
            # 1. Account type validation
            if account_type:
                result = self.account_validator.validate(decision_context)
                validation_results.append(("account_type", result))
            
            # 2. Position sizing validation
            result = self.position_validator.validate(decision_context)
            validation_results.append(("position_sizing", result))
            
            # 3. Timing validation
            result = self.timing_validator.validate(decision_context)
            validation_results.append(("timing", result))
            
            # 4. Delta range validation (for options)
            if strategy in ["csp", "cc", "leap_call", "leap_put"]:
                result = self.delta_validator.validate(decision_context)
                validation_results.append(("delta_range", result))
            
            # 5. Liquidity validation
            result = self.liquidity_validator.validate(decision_context)
            validation_results.append(("liquidity", result))
            
            # 6. Constitutional rule validation
            rule_section = decision_context.get("rule_section")
            if rule_section:
                result = self.constitution.validate_rule_compliance(rule_section, decision_context)
                validation_results.append(("constitutional", result))
            
            # Aggregate results
            overall_result = self._aggregate_validation_results(validation_results)
            
            # Log to audit trail
            self.audit_manager.log_rule_execution(
                rule_section=rule_section or "general_validation",
                context=decision_context,
                result=overall_result,
                constitution_version=self.constitution.VERSION
            )
            
            return overall_result
            
        except Exception as e:
            logger.error(f"Error validating trading decision: {str(e)}", exc_info=True)
            return {
                "result": RuleExecutionResult.ERROR.value,
                "approved": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_position_entry(self,
                              account_type: str,
                              symbol: str,
                              strategy: str,
                              quantity: int,
                              strike_price: Optional[Decimal] = None,
                              expiry_date: Optional[date] = None,
                              delta: Optional[Decimal] = None,
                              premium: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Validate position entry against Constitution rules.
        
        Args:
            account_type: Account type (gen_acc, rev_acc, com_acc)
            symbol: Trading symbol
            strategy: Strategy (csp, cc, leap_call, leap_put)
            quantity: Position quantity
            strike_price: Option strike price
            expiry_date: Option expiry date
            delta: Option delta
            premium: Option premium
            
        Returns:
            Validation result
        """
        context = {
            "action": "open",
            "account_type": account_type,
            "symbol": symbol,
            "strategy": strategy,
            "quantity": quantity,
            "strike_price": float(strike_price) if strike_price else None,
            "expiry_date": expiry_date.isoformat() if expiry_date else None,
            "delta": float(delta) if delta else None,
            "premium": float(premium) if premium else None,
            "timestamp": datetime.now().isoformat(),
            "rule_section": self._get_rule_section(account_type, "entry")
        }
        
        return self.validate_trading_decision(context)
    
    def validate_position_exit(self,
                             position_id: str,
                             account_type: str,
                             exit_reason: str,
                             current_price: Decimal,
                             pnl: Decimal) -> Dict[str, Any]:
        """
        Validate position exit against Constitution rules.
        
        Args:
            position_id: Position identifier
            account_type: Account type
            exit_reason: Reason for exit (protocol, profit_take, assignment, etc.)
            current_price: Current market price
            pnl: Position P&L
            
        Returns:
            Validation result
        """
        context = {
            "action": "close",
            "position_id": position_id,
            "account_type": account_type,
            "exit_reason": exit_reason,
            "current_price": float(current_price),
            "pnl": float(pnl),
            "timestamp": datetime.now().isoformat(),
            "rule_section": self._get_rule_section(account_type, "exit")
        }
        
        return self.validate_trading_decision(context)
    
    def validate_roll_decision(self,
                             position_id: str,
                             account_type: str,
                             current_strike: Decimal,
                             new_strike: Decimal,
                             current_expiry: date,
                             new_expiry: date,
                             atr_breach_multiple: Decimal) -> Dict[str, Any]:
        """
        Validate position roll against Protocol Engine rules.
        
        Args:
            position_id: Position identifier
            account_type: Account type
            current_strike: Current strike price
            new_strike: New strike price
            current_expiry: Current expiry date
            new_expiry: New expiry date
            atr_breach_multiple: ATR breach multiple triggering roll
            
        Returns:
            Validation result
        """
        context = {
            "action": "roll",
            "position_id": position_id,
            "account_type": account_type,
            "current_strike": float(current_strike),
            "new_strike": float(new_strike),
            "current_expiry": current_expiry.isoformat(),
            "new_expiry": new_expiry.isoformat(),
            "atr_breach_multiple": float(atr_breach_multiple),
            "timestamp": datetime.now().isoformat(),
            "rule_section": "§6.Protocol-Engine.Roll"
        }
        
        return self.validate_trading_decision(context)
    
    def validate_account_fork(self,
                            parent_account_id: str,
                            account_type: str,
                            current_balance: Decimal,
                            fork_threshold: Decimal) -> Dict[str, Any]:
        """
        Validate account forking against Constitution rules.
        
        Args:
            parent_account_id: Parent account identifier
            account_type: Account type (gen_acc, rev_acc)
            current_balance: Current account balance
            fork_threshold: Fork threshold amount
            
        Returns:
            Validation result
        """
        context = {
            "action": "fork",
            "parent_account_id": parent_account_id,
            "account_type": account_type,
            "current_balance": float(current_balance),
            "fork_threshold": float(fork_threshold),
            "timestamp": datetime.now().isoformat(),
            "rule_section": self._get_rule_section(account_type, "fork")
        }
        
        return self.validate_trading_decision(context)
    
    def validate_hedge_deployment(self,
                                vix_level: Decimal,
                                hedge_budget: Decimal,
                                hedge_strategy: str) -> Dict[str, Any]:
        """
        Validate hedge deployment against hedging rules.
        
        Args:
            vix_level: Current VIX level
            hedge_budget: Available hedge budget
            hedge_strategy: Hedge strategy (spx_puts, vix_calls)
            
        Returns:
            Validation result
        """
        context = {
            "action": "hedge",
            "vix_level": float(vix_level),
            "hedge_budget": float(hedge_budget),
            "hedge_strategy": hedge_strategy,
            "timestamp": datetime.now().isoformat(),
            "rule_section": "§5.Hedging"
        }
        
        return self.validate_trading_decision(context)
    
    def check_system_state_transition(self,
                                    current_state: str,
                                    target_state: str,
                                    trigger_reason: str) -> Dict[str, Any]:
        """
        Validate system state transition.
        
        Args:
            current_state: Current system state
            target_state: Target system state
            trigger_reason: Reason for state transition
            
        Returns:
            Validation result
        """
        context = {
            "action": "state_transition",
            "current_state": current_state,
            "target_state": target_state,
            "trigger_reason": trigger_reason,
            "timestamp": datetime.now().isoformat(),
            "rule_section": "§9.State-Machine"
        }
        
        return self.validate_trading_decision(context)
    
    def get_position_sizing_recommendation(self,
                                         account_type: str,
                                         available_capital: Decimal,
                                         symbol: str,
                                         option_price: Decimal) -> Dict[str, Any]:
        """
        Get position sizing recommendation based on Constitution rules.
        
        Args:
            account_type: Account type
            available_capital: Available capital
            symbol: Trading symbol
            option_price: Option price per contract
            
        Returns:
            Position sizing recommendation
        """
        try:
            # Get position sizing rules for account type
            sizing_rules = self.constitution.get_position_sizing_rules(account_type)
            
            # Calculate deployment range
            min_deployment = available_capital * self.constitution.global_params.MIN_CAPITAL_DEPLOYMENT
            max_deployment = available_capital * self.constitution.global_params.MAX_CAPITAL_DEPLOYMENT
            
            # Calculate per-symbol limit
            max_per_symbol = available_capital * self.constitution.global_params.MAX_PER_SYMBOL_EXPOSURE
            
            # Calculate contract quantities
            contract_value = option_price * 100  # Options are per 100 shares
            
            max_contracts_by_deployment = int(max_deployment / contract_value)
            max_contracts_by_symbol = int(max_per_symbol / contract_value)
            
            recommended_contracts = min(max_contracts_by_deployment, max_contracts_by_symbol)
            
            return {
                "recommended_contracts": recommended_contracts,
                "max_contracts_by_deployment": max_contracts_by_deployment,
                "max_contracts_by_symbol": max_contracts_by_symbol,
                "deployment_range": {
                    "min": float(min_deployment),
                    "max": float(max_deployment)
                },
                "per_symbol_limit": float(max_per_symbol),
                "contract_value": float(contract_value),
                "sizing_rules": sizing_rules,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating position sizing: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "recommended_contracts": 0
            }
    
    def _aggregate_validation_results(self, 
                                    validation_results: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Aggregate multiple validation results into overall decision.
        
        Args:
            validation_results: List of (validator_name, result) tuples
            
        Returns:
            Aggregated validation result
        """
        all_valid = True
        all_violations = []
        warnings = []
        validator_results = {}
        
        for validator_name, result in validation_results:
            validator_results[validator_name] = result
            
            if not result.get("valid", False):
                all_valid = False
                violations = result.get("violations", [])
                all_violations.extend([f"{validator_name}: {v}" for v in violations])
            
            # Collect warnings
            if "warnings" in result:
                warnings.extend([f"{validator_name}: {w}" for w in result["warnings"]])
        
        # Determine overall result
        if all_valid:
            if warnings:
                overall_result = RuleExecutionResult.WARNING.value
            else:
                overall_result = RuleExecutionResult.APPROVED.value
        else:
            overall_result = RuleExecutionResult.REJECTED.value
        
        return {
            "result": overall_result,
            "approved": all_valid,
            "violations": all_violations,
            "warnings": warnings,
            "validator_results": validator_results,
            "constitution_version": self.constitution.VERSION,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_rule_section(self, account_type: str, action: str) -> str:
        """
        Get Constitution rule section for account type and action.
        
        Args:
            account_type: Account type
            action: Action type (entry, exit, fork, etc.)
            
        Returns:
            Constitution rule section
        """
        section_map = {
            "gen_acc": "§2.Gen-Acc",
            "rev_acc": "§3.Rev-Acc", 
            "com_acc": "§4.Com-Acc"
        }
        
        base_section = section_map.get(account_type, "§0.Global")
        return f"{base_section}.{action.title()}"
    
    def get_constitution_summary(self) -> Dict[str, Any]:
        """Get summary of Constitution v1.3 rules."""
        return {
            "version": self.constitution.VERSION,
            "account_split_ratios": self.constitution.get_account_split_ratios(),
            "weekly_schedule": self.constitution.get_weekly_schedule(),
            "fork_thresholds": self.constitution.get_fork_thresholds(),
            "circuit_breaker_levels": self.constitution.get_circuit_breaker_levels(),
            "liquidity_requirements": self.constitution.get_liquidity_requirements(),
            "protocol_engine_rules": self.constitution.get_protocol_engine_rules(),
            "hedging_rules": self.constitution.get_hedging_rules(),
            "llms_rules": self.constitution.get_llms_rules(),
            "changelog": self.constitution.changelog
        }
    
    def get_audit_trail(self, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       rule_section: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get audit trail of rule executions.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            rule_section: Rule section filter
            
        Returns:
            List of audit trail entries
        """
        return self.audit_manager.get_audit_trail(
            start_date=start_date,
            end_date=end_date,
            rule_section=rule_section
        )

