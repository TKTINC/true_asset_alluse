"""
Position Size Validator

This module implements validation for position sizing rules per
Constitution §0 (Global Parameters) and account-specific limits.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from ..constitution import ConstitutionV13

logger = logging.getLogger(__name__)


class PositionSizeValidator:
    """Validator for position sizing rules."""
    
    def __init__(self, constitution: ConstitutionV13):
        """
        Initialize position size validator.
        
        Args:
            constitution: Constitution v1.3 instance
        """
        self.constitution = constitution
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate position sizing rules.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        try:
            violations = []
            warnings = []
            
            # Extract context parameters
            account_type = context.get("account_type")
            available_capital = context.get("available_capital")
            position_value = context.get("position_value")
            symbol = context.get("symbol")
            quantity = context.get("quantity")
            option_price = context.get("option_price")
            
            # Validate capital deployment
            if available_capital and position_value:
                deployment_result = self._validate_capital_deployment(
                    available_capital, position_value
                )
                violations.extend(deployment_result["violations"])
                warnings.extend(deployment_result["warnings"])
            
            # Validate per-symbol exposure
            if available_capital and position_value and symbol:
                symbol_result = self._validate_per_symbol_exposure(
                    available_capital, position_value, symbol, context
                )
                violations.extend(symbol_result["violations"])
                warnings.extend(symbol_result["warnings"])
            
            # Validate order granularity
            if quantity and option_price:
                granularity_result = self._validate_order_granularity(
                    quantity, option_price
                )
                violations.extend(granularity_result["violations"])
                warnings.extend(granularity_result["warnings"])
            
            # Validate margin usage
            margin_used = context.get("margin_used")
            total_capital = context.get("total_capital")
            if margin_used and total_capital:
                margin_result = self._validate_margin_usage(margin_used, total_capital)
                violations.extend(margin_result["violations"])
                warnings.extend(margin_result["warnings"])
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "warnings": warnings,
                "validator": "position_sizing"
            }
            
        except Exception as e:
            logger.error(f"Error in position size validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "validator": "position_sizing"
            }
    
    def _validate_capital_deployment(self, 
                                   available_capital: float,
                                   position_value: float) -> Dict[str, List[str]]:
        """Validate capital deployment against 95-100% rule."""
        violations = []
        warnings = []
        
        capital_val = Decimal(str(available_capital))
        position_val = Decimal(str(position_value))
        
        deployment_pct = position_val / capital_val if capital_val > 0 else Decimal("0")
        
        min_deployment = self.constitution.global_params.MIN_CAPITAL_DEPLOYMENT
        max_deployment = self.constitution.global_params.MAX_CAPITAL_DEPLOYMENT
        
        if deployment_pct < min_deployment:
            warnings.append(f"Capital deployment {deployment_pct:.1%} below minimum {min_deployment:.1%}")
        elif deployment_pct > max_deployment:
            violations.append(f"Capital deployment {deployment_pct:.1%} exceeds maximum {max_deployment:.1%}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _validate_per_symbol_exposure(self,
                                    available_capital: float,
                                    position_value: float,
                                    symbol: str,
                                    context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate per-symbol exposure against 25% limit."""
        violations = []
        warnings = []
        
        capital_val = Decimal(str(available_capital))
        position_val = Decimal(str(position_value))
        
        # Get existing exposure for this symbol
        existing_exposure = context.get("existing_symbol_exposure", {}).get(symbol, 0)
        existing_val = Decimal(str(existing_exposure))
        
        total_symbol_exposure = existing_val + position_val
        exposure_pct = total_symbol_exposure / capital_val if capital_val > 0 else Decimal("0")
        
        max_per_symbol = self.constitution.global_params.MAX_PER_SYMBOL_EXPOSURE
        
        if exposure_pct > max_per_symbol:
            violations.append(f"Symbol {symbol} exposure {exposure_pct:.1%} exceeds limit {max_per_symbol:.1%}")
        elif exposure_pct > max_per_symbol * Decimal("0.8"):  # 80% of limit
            warnings.append(f"Symbol {symbol} exposure {exposure_pct:.1%} approaching limit {max_per_symbol:.1%}")
        
        return {"violations": violations, "warnings": warnings}
    
    def _validate_order_granularity(self,
                                  quantity: int,
                                  option_price: float) -> Dict[str, List[str]]:
        """Validate order granularity and slicing."""
        violations = []
        warnings = []
        
        slice_threshold = self.constitution.global_params.ORDER_SLICE_THRESHOLD
        
        if quantity > slice_threshold:
            warnings.append(f"Order size {quantity} > slice threshold {slice_threshold}, consider slicing")
        
        # Validate minimum order size
        if quantity <= 0:
            violations.append("Order quantity must be positive")
        
        # Validate option price
        if option_price <= 0:
            violations.append("Option price must be positive")
        
        return {"violations": violations, "warnings": warnings}
    
    def _validate_margin_usage(self,
                             margin_used: float,
                             total_capital: float) -> Dict[str, List[str]]:
        """Validate margin usage against limits."""
        violations = []
        warnings = []
        
        margin_val = Decimal(str(margin_used))
        capital_val = Decimal(str(total_capital))
        
        margin_pct = margin_val / capital_val if capital_val > 0 else Decimal("0")
        max_margin = self.constitution.global_params.MAX_MARGIN_USE
        
        if margin_pct > max_margin:
            violations.append(f"Margin usage {margin_pct:.1%} exceeds limit {max_margin:.1%}")
        elif margin_pct > max_margin * Decimal("0.8"):  # 80% of limit
            warnings.append(f"Margin usage {margin_pct:.1%} approaching limit {max_margin:.1%}")
        
        return {"violations": violations, "warnings": warnings}

