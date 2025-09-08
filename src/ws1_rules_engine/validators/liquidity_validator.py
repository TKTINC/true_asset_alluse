"""
Liquidity Validator

This module implements validation for liquidity requirements per
Constitution §8 (Liquidity & Data Validation).
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from ..constitution import ConstitutionV13

logger = logging.getLogger(__name__)


class LiquidityValidator:
    """Validator for liquidity requirements."""
    
    def __init__(self, constitution: ConstitutionV13):
        """
        Initialize liquidity validator.
        
        Args:
            constitution: Constitution v1.3 instance
        """
        self.constitution = constitution
    
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate liquidity requirements.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        try:
            violations = []
            warnings = []
            
            # Extract liquidity parameters
            open_interest = context.get("open_interest")
            daily_volume = context.get("daily_volume")
            bid_price = context.get("bid_price")
            ask_price = context.get("ask_price")
            mid_price = context.get("mid_price")
            order_size = context.get("order_size")
            avg_daily_volume = context.get("avg_daily_volume")
            
            # Get liquidity requirements
            requirements = self.constitution.get_liquidity_requirements()
            
            # Validate open interest
            if open_interest is not None:
                if open_interest < requirements["min_open_interest"]:
                    violations.append(f"Open interest {open_interest} < minimum {requirements['min_open_interest']}")
            
            # Validate daily volume
            if daily_volume is not None:
                if daily_volume < requirements["min_daily_volume"]:
                    violations.append(f"Daily volume {daily_volume} < minimum {requirements['min_daily_volume']}")
            
            # Validate bid-ask spread
            if bid_price is not None and ask_price is not None:
                spread = Decimal(str(ask_price)) - Decimal(str(bid_price))
                if mid_price and mid_price > 0:
                    spread_pct = spread / Decimal(str(mid_price))
                    max_spread_pct = requirements["max_spread_pct"]
                    
                    if spread_pct > max_spread_pct:
                        violations.append(f"Spread {spread_pct:.2%} > maximum {max_spread_pct:.1%}")
                    elif spread_pct > max_spread_pct * Decimal("0.8"):
                        warnings.append(f"Spread {spread_pct:.2%} approaching maximum {max_spread_pct:.1%}")
            
            # Validate order size vs average daily volume
            if order_size is not None and avg_daily_volume is not None and avg_daily_volume > 0:
                order_size_pct = Decimal(str(order_size)) / Decimal(str(avg_daily_volume))
                max_order_size_pct = requirements["max_order_size_pct"]
                
                if order_size_pct > max_order_size_pct:
                    violations.append(f"Order size {order_size_pct:.1%} of ADV > maximum {max_order_size_pct:.1%}")
                elif order_size_pct > max_order_size_pct * Decimal("0.8"):
                    warnings.append(f"Order size {order_size_pct:.1%} of ADV approaching maximum {max_order_size_pct:.1%}")
            
            # Additional liquidity checks
            if context.get("market_hours"):
                if not self._is_market_hours():
                    warnings.append("Trading outside regular market hours may have reduced liquidity")
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "warnings": warnings,
                "validator": "liquidity"
            }
            
        except Exception as e:
            logger.error(f"Error in liquidity validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "validator": "liquidity"
            }
    
    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours (simplified)."""
        # This is a simplified implementation
        # In production, would check actual market hours
        from datetime import datetime, time
        now = datetime.now().time()
        market_open = time(9, 30)
        market_close = time(16, 0)
        return market_open <= now <= market_close

