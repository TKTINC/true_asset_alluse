"""
Timing Validator

This module implements validation for trading timing rules per
Constitution §1 (Weekly Cadence) and account-specific schedules.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, time, date
import logging

from ..constitution import ConstitutionV13

logger = logging.getLogger(__name__)


class TimingValidator:
    """Validator for trading timing rules."""
    
    def __init__(self, constitution: ConstitutionV13):
        """
        Initialize timing validator.
        
        Args:
            constitution: Constitution v1.3 instance
        """
        self.constitution = constitution
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate trading timing rules.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        try:
            violations = []
            warnings = []
            
            account_type = context.get("account_type")
            trading_time = context.get("trading_time")
            trading_date = context.get("trading_date")
            
            if not account_type:
                return {
                    "valid": True,
                    "violations": [],
                    "warnings": ["No account type provided for timing validation"],
                    "validator": "timing"
                }
            
            # Get weekly schedule for account type
            schedule = self.constitution.get_weekly_schedule()
            account_schedule = schedule.get(account_type)
            
            if not account_schedule:
                violations.append(f"No schedule found for account type: {account_type}")
                return {
                    "valid": False,
                    "violations": violations,
                    "validator": "timing"
                }
            
            # Validate trading day
            if trading_date:
                if isinstance(trading_date, str):
                    trading_date = datetime.fromisoformat(trading_date).date()
                
                weekday = trading_date.strftime("%A").lower()
                expected_day = account_schedule["day"]
                
                if weekday != expected_day:
                    warnings.append(f"Trading on {weekday}, {account_type} typically trades on {expected_day}")
            
            # Validate trading time
            if trading_time:
                if isinstance(trading_time, str):
                    trading_time = datetime.fromisoformat(trading_time).time()
                
                start_time = account_schedule["start_time"]
                end_time = account_schedule["end_time"]
                
                if not (start_time <= trading_time <= end_time):
                    violations.append(f"Trading time {trading_time} outside {account_type} window {start_time}-{end_time}")
            
            # Check for market holidays
            if trading_date:
                if self._is_market_holiday(trading_date):
                    violations.append(f"Trading date {trading_date} is a market holiday")
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "warnings": warnings,
                "validator": "timing"
            }
            
        except Exception as e:
            logger.error(f"Error in timing validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "validator": "timing"
            }
    
    def _is_market_holiday(self, trading_date: date) -> bool:
        """Check if date is a market holiday (simplified implementation)."""
        # This is a simplified implementation
        # In production, would use a proper market calendar
        weekday = trading_date.weekday()
        return weekday >= 5  # Saturday (5) or Sunday (6)

