"""
Constitution v1.3 Main Implementation

This module provides the main ConstitutionV13 class that serves as the single
source of truth for all constitutional rules and parameters. Every trading
decision must be validated against these rules.

The Constitution is treated as immutable law - no changes are allowed without
proper governance process (proposal → simulation → human approval → version increment).
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, time, date
from enum import Enum

from .global_parameters import GlobalParameters
from .account_rules import GenAccRules, RevAccRules, ComAccRules
from .protocol_rules import ProtocolEngineRules
from .hedging_rules import HedgingRules
from .llms_rules import LLMSRules


class ConstitutionV13:
    """
    Constitution v1.3 - The immutable law of True-Asset-ALLUSE.
    
    This class provides structured access to all constitutional rules
    and serves as the single source of truth for system behavior.
    """
    
    VERSION = "1.3"
    
    def __init__(self):
        """Initialize Constitution v1.3 with all rule sets."""
        self.global_params = GlobalParameters()
        self.gen_acc_rules = GenAccRules()
        self.rev_acc_rules = RevAccRules()
        self.com_acc_rules = ComAccRules()
        self.protocol_rules = ProtocolEngineRules()
        self.hedging_rules = HedgingRules()
        self.llms_rules = LLMSRules()
        
        # Constitution metadata
        self.created_at = datetime.now()
        self.changelog = self._get_changelog()
    
    def _get_changelog(self) -> List[str]:
        """Get Constitution v1.3 changelog from v1.2."""
        return [
            "LLMS (Leap Ladder Management System/Service) Added:",
            "- Manages lifecycle of LEAPs (growth + hedge)",
            "- Defines entry, laddering, lifecycle management, optimization, and reporting",
            "Clarified AI Optimization: 'LLMS Optimization' = AI-assisted LEAP ladder analysis, requires human approval",
            "Story alignment: Constitution and System Story both reference LLMS explicitly"
        ]
    
    def get_account_split_ratios(self) -> Dict[str, Decimal]:
        """Get the mandated 40/30/30 account split ratios."""
        return {
            "gen_acc": self.global_params.GEN_ACC_RATIO,
            "rev_acc": self.global_params.REV_ACC_RATIO,
            "com_acc": self.global_params.COM_ACC_RATIO
        }
    
    def get_weekly_schedule(self) -> Dict[str, Dict[str, Any]]:
        """Get the weekly trading schedule per Constitution §1."""
        return {
            "gen_acc": {
                "day": "thursday",
                "start_time": time(9, 45),
                "end_time": time(11, 0),
                "action": "Open 0-1DTE CSPs, 40-45Δ",
                "instruments": ["AAPL", "MSFT", "AMZN", "GOOG", "SPY", "QQQ", "IWM"],
                "alt_mode": "1-3DTE for stress-test"
            },
            "rev_acc": {
                "day": "wednesday", 
                "start_time": time(9, 45),
                "end_time": time(11, 0),
                "action": "Open 3-5DTE CSPs, 30-35Δ",
                "instruments": ["NVDA", "TSLA"]
            },
            "com_acc": {
                "day": "monday",
                "start_time": time(9, 45),
                "end_time": time(11, 0),
                "action": "Write 5DTE CCs, 20-25Δ",
                "instruments": ["AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "TSLA", "META"]  # Mag-7
            },
            "all_accounts": {
                "day": "friday",
                "start_time": time(14, 30),
                "end_time": time(15, 45),
                "action": "Manage/close to avoid pin risk",
                "report_cutoff": time(16, 30)
            }
        }
    
    def get_position_sizing_rules(self, account_type: str) -> Dict[str, Any]:
        """Get position sizing rules per account type."""
        base_rules = {
            "capital_deployment": "95-100%",
            "per_symbol_limit": "≤25% of sleeve notional",
            "order_granularity": "auto-calculated by sleeve size",
            "slice_threshold": ">50 contracts"
        }
        
        if account_type == "gen_acc":
            return {**base_rules, **self.gen_acc_rules.get_sizing_rules()}
        elif account_type == "rev_acc":
            return {**base_rules, **self.rev_acc_rules.get_sizing_rules()}
        elif account_type == "com_acc":
            return {**base_rules, **self.com_acc_rules.get_sizing_rules()}
        else:
            raise ValueError(f"Unknown account type: {account_type}")
    
    def get_delta_ranges(self, account_type: str, strategy: str) -> Tuple[Decimal, Decimal]:
        """Get delta ranges for account type and strategy."""
        if account_type == "gen_acc":
            if strategy in ["csp", "cc"]:
                return (Decimal("0.40"), Decimal("0.45"))
        elif account_type == "rev_acc":
            if strategy in ["csp", "cc"]:
                return (Decimal("0.30"), Decimal("0.35"))
        elif account_type == "com_acc":
            if strategy == "cc":
                return (Decimal("0.20"), Decimal("0.25"))
        
        raise ValueError(f"Invalid account_type/strategy combination: {account_type}/{strategy}")
    
    def get_dte_ranges(self, account_type: str) -> Dict[str, Any]:
        """Get DTE (Days to Expiration) ranges per account type."""
        if account_type == "gen_acc":
            return {
                "normal": (0, 1),
                "stress_test": (1, 3),
                "description": "0-1DTE normal, 1-3DTE stress-test only"
            }
        elif account_type == "rev_acc":
            return {
                "normal": (3, 5),
                "description": "3-5DTE"
            }
        elif account_type == "com_acc":
            return {
                "normal": (5, 5),
                "description": "5DTE"
            }
        
        raise ValueError(f"Unknown account type: {account_type}")
    
    def get_fork_thresholds(self) -> Dict[str, Decimal]:
        """Get account forking thresholds per Constitution §2-3."""
        return {
            "gen_acc": Decimal("100000"),  # +$100K increments
            "rev_acc": Decimal("500000")   # +$500K increments
        }
    
    def get_liquidity_requirements(self) -> Dict[str, Any]:
        """Get liquidity requirements per Constitution §8."""
        return {
            "min_open_interest": 500,
            "min_daily_volume": 100,
            "max_spread_pct": Decimal("0.05"),  # 5% of mid
            "max_order_size_pct": Decimal("0.10")  # 10% of ADV
        }
    
    def get_circuit_breaker_levels(self) -> Dict[str, Any]:
        """Get VIX-based circuit breaker levels per Constitution §6."""
        return {
            "hedged_week": Decimal("50"),    # VIX >50 → Hedged Week
            "safe_mode": Decimal("65"),      # VIX >65 → SAFE mode
            "kill_switch": Decimal("80")     # VIX >80 → Kill switch
        }
    
    def get_protocol_engine_rules(self) -> Dict[str, Any]:
        """Get Protocol Engine rules per Constitution §6."""
        return self.protocol_rules.get_all_rules()
    
    def get_hedging_rules(self) -> Dict[str, Any]:
        """Get hedging rules per Constitution §5."""
        return self.hedging_rules.get_all_rules()
    
    def get_llms_rules(self) -> Dict[str, Any]:
        """Get LLMS rules per Constitution §17."""
        return self.llms_rules.get_all_rules()
    
    def get_assignment_protocol(self) -> Dict[str, Any]:
        """Get assignment protocol per Constitution §7."""
        return {
            "prep_time": "Friday 3pm if ITM >95%",
            "action_on_assignment": "Switch to CC 20Δ, 5DTE",
            "resume_csp_condition": "After shares called away",
            "logging_required": True
        }
    
    def get_tax_and_reinvestment_rules(self) -> Dict[str, Any]:
        """Get tax and reinvestment rules per Constitution §10."""
        return {
            "gen_acc": {
                "reinvest": False,
                "action": "Profits accumulate until fork"
            },
            "rev_acc": {
                "reinvest": True,
                "frequency": "quarterly",
                "tax_reserve": Decimal("0.30"),  # 30%
                "reinvest_split": {
                    "contracts": Decimal("0.75"),  # 75%
                    "leaps": Decimal("0.25")       # 25%
                }
            },
            "com_acc": {
                "reinvest": True,
                "frequency": "quarterly", 
                "tax_reserve": Decimal("0.30"),  # 30%
                "reinvest_split": {
                    "contracts": Decimal("0.75"),  # 75%
                    "leaps": Decimal("0.25")       # 25%
                }
            }
        }
    
    def get_reporting_requirements(self) -> Dict[str, List[str]]:
        """Get reporting requirements per Constitution §11."""
        return {
            "weekly": ["trades", "forks", "income", "week_type"],
            "monthly": ["CAGR_YTD", "drawdown", "sharpe_ratio", "sortino_ratio"],
            "quarterly": ["tax_ledger", "reinvestments", "hedge_summary"],
            "natural_language": ["AI answers user queries about system behavior"]
        }
    
    def get_week_types(self) -> List[str]:
        """Get possible week types per Constitution §12."""
        return [
            "Calm-Income",
            "Roll", 
            "Assignment",
            "Preservation",
            "Hedged",
            "Earnings-Filter"
        ]
    
    def get_ai_augmentation_rules(self) -> Dict[str, Any]:
        """Get AI augmentation rules per Constitution §13."""
        return {
            "natural_language_reports": {
                "purpose": "AI translates ledger into user-facing answers",
                "trading_decisions": False
            },
            "anomaly_detection": {
                "purpose": "Monitor vol/correlation/news",
                "output": "Advisory alerts only",
                "trading_decisions": False
            },
            "llms_optimization": {
                "purpose": "AI analyzes historical LEAP ladder performance",
                "output": "Suggests refinements",
                "approval_required": True,
                "trading_decisions": False
            }
        }
    
    def get_compliance_requirements(self) -> Dict[str, Any]:
        """Get compliance requirements per Constitution §14."""
        return {
            "custody": "Non-custodial, software-only PoC",
            "capital": "Company capital only",
            "self_modifying_code": False,
            "secrets_management": True,
            "ci_scans": True,
            "ops_runbook_required": True
        }
    
    def get_governance_rules(self) -> Dict[str, Any]:
        """Get governance rules per Constitution §15."""
        return {
            "constitution_immutable": True,
            "change_process": [
                "proposal",
                "simulation/backtest", 
                "human_approval",
                "version_increment"
            ],
            "changelog_required": True
        }
    
    def get_acceptance_criteria(self) -> List[str]:
        """Get acceptance criteria per Constitution §16."""
        return [
            "Two weekly cycles in paper, one live cycle",
            "Weekly report must generate",
            "Idempotent order flow verified",
            "SAFE→ACTIVE tested",
            "Fork→mini→merge executed at least once in sim"
        ]
    
    def validate_rule_compliance(self, rule_section: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate compliance with a specific constitutional rule.
        
        Args:
            rule_section: Constitution section (e.g., "§2.Gen-Acc.Entry")
            context: Context data for validation
            
        Returns:
            Dict with validation result and details
        """
        try:
            # Parse rule section
            section_parts = rule_section.split(".")
            if len(section_parts) < 2:
                return {
                    "valid": False,
                    "error": f"Invalid rule section format: {rule_section}",
                    "details": {}
                }
            
            section = section_parts[0]
            subsection = section_parts[1] if len(section_parts) > 1 else None
            
            # Route to appropriate validation method
            if section == "§0":
                return self._validate_global_parameters(context)
            elif section == "§1":
                return self._validate_weekly_cadence(context)
            elif section == "§2" and subsection == "Gen-Acc":
                return self._validate_gen_acc_rules(context)
            elif section == "§3" and subsection == "Rev-Acc":
                return self._validate_rev_acc_rules(context)
            elif section == "§4" and subsection == "Com-Acc":
                return self._validate_com_acc_rules(context)
            elif section == "§6":
                return self._validate_protocol_engine(context)
            elif section == "§8":
                return self._validate_liquidity_requirements(context)
            else:
                return {
                    "valid": False,
                    "error": f"Unknown rule section: {rule_section}",
                    "details": {}
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "details": {"exception": str(e)}
            }
    
    def _validate_global_parameters(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate global parameters per Constitution §0."""
        # Implementation will be added based on specific validation needs
        return {"valid": True, "details": {"section": "§0 Global Parameters"}}
    
    def _validate_weekly_cadence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate weekly cadence per Constitution §1."""
        # Implementation will be added based on specific validation needs
        return {"valid": True, "details": {"section": "§1 Weekly Cadence"}}
    
    def _validate_gen_acc_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Gen-Acc rules per Constitution §2."""
        return self.gen_acc_rules.validate(context)
    
    def _validate_rev_acc_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Rev-Acc rules per Constitution §3."""
        return self.rev_acc_rules.validate(context)
    
    def _validate_com_acc_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Com-Acc rules per Constitution §4."""
        return self.com_acc_rules.validate(context)
    
    def _validate_protocol_engine(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Protocol Engine rules per Constitution §6."""
        return self.protocol_rules.validate(context)
    
    def _validate_liquidity_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate liquidity requirements per Constitution §8."""
        # Implementation will be added based on specific validation needs
        return {"valid": True, "details": {"section": "§8 Liquidity Requirements"}}

