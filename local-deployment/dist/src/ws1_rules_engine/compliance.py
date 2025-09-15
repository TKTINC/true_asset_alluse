"""
Compliance Checker

This module implements the compliance checking system that verifies
adherence to Constitution v1.3 rules and generates compliance reports.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from .constitution import ConstitutionV13

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """
    Compliance Checker for Constitution v1.3.
    
    Provides comprehensive compliance checking and reporting
    to ensure all system operations adhere to constitutional rules.
    """
    
    def __init__(self, constitution: ConstitutionV13):
        """
        Initialize compliance checker.
        
        Args:
            constitution: Constitution v1.3 instance
        """
        self.constitution = constitution
        logger.info(f"Compliance Checker initialized with Constitution v{constitution.VERSION}")
    
    def check_account_compliance(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check account compliance against Constitution rules.
        
        Args:
            account_data: Account data to check
            
        Returns:
            Compliance check result
        """
        try:
            violations = []
            warnings = []
            
            account_type = account_data.get("account_type")
            current_balance = account_data.get("current_balance")
            positions = account_data.get("positions", [])
            
            if not account_type:
                violations.append("Account type is required")
                return self._format_compliance_result(False, violations, warnings)
            
            # Check account split ratios
            if "total_capital" in account_data and "account_balances" in account_data:
                split_result = self._check_account_split_compliance(
                    account_data["total_capital"],
                    account_data["account_balances"]
                )
                violations.extend(split_result["violations"])
                warnings.extend(split_result["warnings"])
            
            # Check position compliance
            for position in positions:
                position_result = self._check_position_compliance(position, account_type)
                violations.extend(position_result["violations"])
                warnings.extend(position_result["warnings"])
            
            # Check capital deployment
            if current_balance and positions:
                deployment_result = self._check_capital_deployment_compliance(
                    current_balance, positions
                )
                violations.extend(deployment_result["violations"])
                warnings.extend(deployment_result["warnings"])
            
            # Check forking compliance
            if current_balance:
                fork_result = self._check_fork_compliance(account_type, current_balance)
                violations.extend(fork_result["violations"])
                warnings.extend(fork_result["warnings"])
            
            return self._format_compliance_result(
                len(violations) == 0, violations, warnings, account_type
            )
            
        except Exception as e:
            logger.error(f"Error checking account compliance: {str(e)}", exc_info=True)
            return self._format_compliance_result(
                False, [f"Compliance check error: {str(e)}"], []
            )
    
    def check_trading_compliance(self, trading_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check trading activity compliance against Constitution rules.
        
        Args:
            trading_data: Trading data to check
            
        Returns:
            Compliance check result
        """
        try:
            violations = []
            warnings = []
            
            account_type = trading_data.get("account_type")
            trades = trading_data.get("trades", [])
            trading_date = trading_data.get("trading_date")
            
            # Check trading schedule compliance
            if trading_date and account_type:
                schedule_result = self._check_trading_schedule_compliance(
                    account_type, trading_date, trades
                )
                violations.extend(schedule_result["violations"])
                warnings.extend(schedule_result["warnings"])
            
            # Check individual trade compliance
            for trade in trades:
                trade_result = self._check_individual_trade_compliance(trade, account_type)
                violations.extend(trade_result["violations"])
                warnings.extend(trade_result["warnings"])
            
            return self._format_compliance_result(
                len(violations) == 0, violations, warnings, account_type
            )
            
        except Exception as e:
            logger.error(f"Error checking trading compliance: {str(e)}", exc_info=True)
            return self._format_compliance_result(
                False, [f"Compliance check error: {str(e)}"], []
            )
    
    def check_protocol_compliance(self, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check Protocol Engine compliance against Constitution §6.
        
        Args:
            protocol_data: Protocol data to check
            
        Returns:
            Compliance check result
        """
        try:
            violations = []
            warnings = []
            
            protocol_level = protocol_data.get("protocol_level")
            monitoring_frequency = protocol_data.get("monitoring_frequency")
            atr_breach_multiple = protocol_data.get("atr_breach_multiple")
            actions_taken = protocol_data.get("actions_taken", [])
            
            # Get protocol rules
            protocol_rules = self.constitution.get_protocol_engine_rules()
            
            # Check protocol level appropriateness
            if protocol_level and atr_breach_multiple is not None:
                expected_level = self._determine_expected_protocol_level(atr_breach_multiple)
                if protocol_level != expected_level:
                    violations.append(f"Protocol level {protocol_level} inconsistent with ATR breach {atr_breach_multiple}×")
            
            # Check monitoring frequency
            if protocol_level and monitoring_frequency:
                expected_frequency = protocol_rules["protocol_levels"][protocol_level]["monitoring_frequency"]
                if monitoring_frequency != expected_frequency:
                    violations.append(f"Monitoring frequency {monitoring_frequency}s incorrect for {protocol_level}")
            
            # Check required actions
            if protocol_level and actions_taken is not None:
                required_actions = self._get_required_protocol_actions(protocol_level)
                missing_actions = set(required_actions) - set(actions_taken)
                if missing_actions:
                    violations.append(f"Missing required actions for {protocol_level}: {list(missing_actions)}")
            
            return self._format_compliance_result(
                len(violations) == 0, violations, warnings
            )
            
        except Exception as e:
            logger.error(f"Error checking protocol compliance: {str(e)}", exc_info=True)
            return self._format_compliance_result(
                False, [f"Compliance check error: {str(e)}"], []
            )
    
    def generate_compliance_report(self, 
                                 report_period: Tuple[datetime, datetime],
                                 account_data: List[Dict[str, Any]],
                                 trading_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report.
        
        Args:
            report_period: (start_date, end_date) tuple
            account_data: List of account data
            trading_data: List of trading data
            
        Returns:
            Comprehensive compliance report
        """
        try:
            start_date, end_date = report_period
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    "constitution_version": self.constitution.VERSION
                },
                "executive_summary": {},
                "account_compliance": [],
                "trading_compliance": [],
                "violations_summary": {},
                "recommendations": []
            }
            
            # Check account compliance
            total_violations = 0
            total_warnings = 0
            
            for account in account_data:
                result = self.check_account_compliance(account)
                report["account_compliance"].append(result)
                total_violations += len(result.get("violations", []))
                total_warnings += len(result.get("warnings", []))
            
            # Check trading compliance
            for trading in trading_data:
                result = self.check_trading_compliance(trading)
                report["trading_compliance"].append(result)
                total_violations += len(result.get("violations", []))
                total_warnings += len(result.get("warnings", []))
            
            # Generate executive summary
            report["executive_summary"] = {
                "overall_compliance": total_violations == 0,
                "total_violations": total_violations,
                "total_warnings": total_warnings,
                "accounts_checked": len(account_data),
                "trading_sessions_checked": len(trading_data),
                "compliance_score": max(0, 100 - (total_violations * 10) - (total_warnings * 2))
            }
            
            # Generate recommendations
            if total_violations > 0:
                report["recommendations"].append("Address all violations immediately to ensure Constitution compliance")
            if total_warnings > 5:
                report["recommendations"].append("Review warning patterns to prevent future violations")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _check_account_split_compliance(self, 
                                      total_capital: float,
                                      account_balances: Dict[str, float]) -> Dict[str, List[str]]:
        """Check account split ratio compliance."""
        violations = []
        warnings = []
        
        try:
            expected_ratios = self.constitution.get_account_split_ratios()
            total_val = Decimal(str(total_capital))
            
            for account_type, expected_ratio in expected_ratios.items():
                actual_balance = Decimal(str(account_balances.get(account_type, 0)))
                actual_ratio = actual_balance / total_val if total_val > 0 else Decimal("0")
                
                deviation = abs(actual_ratio - expected_ratio)
                if deviation > Decimal("0.05"):  # 5% tolerance
                    violations.append(f"{account_type} ratio {actual_ratio:.1%} deviates from target {expected_ratio:.1%}")
                elif deviation > Decimal("0.02"):  # 2% warning threshold
                    warnings.append(f"{account_type} ratio {actual_ratio:.1%} approaching target {expected_ratio:.1%}")
        
        except Exception as e:
            violations.append(f"Error checking account split: {str(e)}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_position_compliance(self, position: Dict[str, Any], account_type: str) -> Dict[str, List[str]]:
        """Check individual position compliance."""
        violations = []
        warnings = []
        
        try:
            strategy = position.get("strategy")
            symbol = position.get("symbol")
            delta = position.get("delta")
            dte = position.get("dte")
            
            # Check strategy compliance
            if account_type == "gen_acc" and strategy not in ["csp", "cc"]:
                violations.append(f"Gen-Acc position {symbol} has invalid strategy {strategy}")
            elif account_type == "rev_acc" and strategy not in ["csp", "cc"]:
                violations.append(f"Rev-Acc position {symbol} has invalid strategy {strategy}")
            elif account_type == "com_acc" and strategy != "cc":
                violations.append(f"Com-Acc position {symbol} has invalid strategy {strategy}")
            
            # Check delta ranges
            if delta is not None and strategy in ["csp", "cc"]:
                try:
                    delta_min, delta_max = self.constitution.get_delta_ranges(account_type, strategy)
                    delta_val = Decimal(str(delta))
                    if not (delta_min <= delta_val <= delta_max):
                        violations.append(f"Position {symbol} delta {delta_val} outside range {delta_min}-{delta_max}")
                except ValueError:
                    pass  # Invalid combination, will be caught by strategy check
            
            # Check DTE ranges
            if dte is not None:
                dte_ranges = self.constitution.get_dte_ranges(account_type)
                normal_range = dte_ranges["normal"]
                if not (normal_range[0] <= dte <= normal_range[1]):
                    violations.append(f"Position {symbol} DTE {dte} outside range {normal_range}")
        
        except Exception as e:
            violations.append(f"Error checking position {position.get('symbol', 'unknown')}: {str(e)}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_capital_deployment_compliance(self, 
                                           current_balance: float,
                                           positions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Check capital deployment compliance."""
        violations = []
        warnings = []
        
        try:
            balance_val = Decimal(str(current_balance))
            total_position_value = sum(Decimal(str(p.get("value", 0))) for p in positions)
            
            deployment_pct = total_position_value / balance_val if balance_val > 0 else Decimal("0")
            
            min_deployment = self.constitution.global_params.MIN_CAPITAL_DEPLOYMENT
            max_deployment = self.constitution.global_params.MAX_CAPITAL_DEPLOYMENT
            
            if deployment_pct < min_deployment:
                warnings.append(f"Capital deployment {deployment_pct:.1%} below minimum {min_deployment:.1%}")
            elif deployment_pct > max_deployment:
                violations.append(f"Capital deployment {deployment_pct:.1%} exceeds maximum {max_deployment:.1%}")
        
        except Exception as e:
            violations.append(f"Error checking capital deployment: {str(e)}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_fork_compliance(self, account_type: str, current_balance: float) -> Dict[str, List[str]]:
        """Check forking compliance."""
        violations = []
        warnings = []
        
        try:
            fork_thresholds = self.constitution.get_fork_thresholds()
            balance_val = Decimal(str(current_balance))
            
            if account_type in fork_thresholds:
                threshold = fork_thresholds[account_type]
                if balance_val >= threshold:
                    warnings.append(f"{account_type} balance {balance_val} ≥ fork threshold {threshold}")
        
        except Exception as e:
            violations.append(f"Error checking fork compliance: {str(e)}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_trading_schedule_compliance(self,
                                         account_type: str,
                                         trading_date: str,
                                         trades: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Check trading schedule compliance."""
        violations = []
        warnings = []
        
        try:
            schedule = self.constitution.get_weekly_schedule()
            account_schedule = schedule.get(account_type)
            
            if not account_schedule:
                return {"violations": violations, "warnings": warnings}
            
            # Check trading day
            if isinstance(trading_date, str):
                trading_date_obj = datetime.fromisoformat(trading_date).date()
            else:
                trading_date_obj = trading_date
            
            weekday = trading_date_obj.strftime("%A").lower()
            expected_day = account_schedule["day"]
            
            if weekday != expected_day:
                warnings.append(f"Trading on {weekday}, {account_type} typically trades on {expected_day}")
            
            # Check trading times
            start_time = account_schedule["start_time"]
            end_time = account_schedule["end_time"]
            
            for trade in trades:
                trade_time = trade.get("time")
                if trade_time:
                    if isinstance(trade_time, str):
                        trade_time = datetime.fromisoformat(trade_time).time()
                    
                    if not (start_time <= trade_time <= end_time):
                        violations.append(f"Trade at {trade_time} outside {account_type} window {start_time}-{end_time}")
        
        except Exception as e:
            violations.append(f"Error checking trading schedule: {str(e)}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_individual_trade_compliance(self, 
                                         trade: Dict[str, Any],
                                         account_type: str) -> Dict[str, List[str]]:
        """Check individual trade compliance."""
        violations = []
        warnings = []
        
        try:
            # This would contain detailed trade validation logic
            # For now, basic checks
            if not trade.get("symbol"):
                violations.append("Trade missing symbol")
            
            if not trade.get("quantity") or trade["quantity"] <= 0:
                violations.append("Trade has invalid quantity")
        
        except Exception as e:
            violations.append(f"Error checking trade: {str(e)}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _determine_expected_protocol_level(self, atr_breach_multiple: float) -> str:
        """Determine expected protocol level based on ATR breach."""
        if atr_breach_multiple >= 3.0:
            return "level_3"
        elif atr_breach_multiple >= 2.0:
            return "level_2"
        elif atr_breach_multiple >= 1.0:
            return "level_1"
        else:
            return "level_0"
    
    def _get_required_protocol_actions(self, protocol_level: str) -> List[str]:
        """Get required actions for protocol level."""
        action_map = {
            "level_0": ["normal_monitoring"],
            "level_1": ["enhanced_monitoring", "alert_risk_management"],
            "level_2": ["prep_roll", "calculate_exit_scenarios"],
            "level_3": ["immediate_exit", "enter_safe_mode"]
        }
        return action_map.get(protocol_level, [])
    
    def _format_compliance_result(self,
                                compliant: bool,
                                violations: List[str],
                                warnings: List[str],
                                context: Optional[str] = None) -> Dict[str, Any]:
        """Format compliance check result."""
        return {
            "compliant": compliant,
            "violations": violations,
            "warnings": warnings,
            "violation_count": len(violations),
            "warning_count": len(warnings),
            "context": context,
            "checked_at": datetime.now().isoformat(),
            "constitution_version": self.constitution.VERSION
        }

