"""
Delta Range Validator

This module implements validation for option delta ranges per
account-specific rules in Constitution sections §2, §3, and §4.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from ..constitution import ConstitutionV13

logger = logging.getLogger(__name__)


class DeltaRangeValidator:
    """Validator for option delta ranges."""
    
    def __init__(self, constitution: ConstitutionV13):
        """
        Initialize delta range validator.
        
        Args:
            constitution: Constitution v1.3 instance
        """
        self.constitution = constitution
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate option delta ranges.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        try:
            violations = []
            warnings = []
            
            account_type = context.get("account_type")
            strategy = context.get("strategy")
            delta = context.get("delta")
            
            if not all([account_type, strategy, delta is not None]):
                return {
                    "valid": True,
                    "violations": [],
                    "warnings": ["Incomplete delta validation parameters"],
                    "validator": "delta_range"
                }
            
            try:
                delta_min, delta_max = self.constitution.get_delta_ranges(account_type, strategy)
            except ValueError as e:
                violations.append(str(e))
                return {
                    "valid": False,
                    "violations": violations,
                    "validator": "delta_range"
                }
            
            delta_val = Decimal(str(delta))
            
            if not (delta_min <= delta_val <= delta_max):
                violations.append(f"Delta {delta_val} not in {account_type} {strategy} range {delta_min}-{delta_max}")
            
            # Warning if delta is at the edge of range
            range_size = delta_max - delta_min
            if range_size > 0:
                if abs(delta_val - delta_min) / range_size < Decimal("0.1"):
                    warnings.append(f"Delta {delta_val} near minimum {delta_min}")
                elif abs(delta_val - delta_max) / range_size < Decimal("0.1"):
                    warnings.append(f"Delta {delta_val} near maximum {delta_max}")
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "warnings": warnings,
                "validator": "delta_range"
            }
            
        except Exception as e:
            logger.error(f"Error in delta range validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "validator": "delta_range"
            }

