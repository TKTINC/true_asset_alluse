"""
Liquidity Validator - Constitution v1.3 Compliance

This module implements the liquidity guards per GPT-5 feedback:
- Absolute: OI ≥ 500, avg daily option vol ≥ 100, spread ≤ 5% of mid
- Relative: reject if order size > 10% of ADV for that option

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class LiquidityMetrics:
    """Liquidity metrics for an option."""
    symbol: str
    strike: Decimal
    expiration: str
    option_type: str  # "call" or "put"
    open_interest: int
    daily_volume: int
    avg_daily_volume: int
    bid: Decimal
    ask: Decimal
    mid: Decimal
    spread: Decimal
    spread_percentage: Decimal
    last_updated: datetime


@dataclass
class LiquidityValidationResult:
    """Liquidity validation result."""
    valid: bool
    violations: List[str]
    metrics: LiquidityMetrics
    order_size: int
    adv_percentage: Decimal
    recommendation: str


class LiquidityValidator:
    """Liquidity validator per Constitution v1.3."""
    
    # Constitution v1.3 - Liquidity Requirements (GPT-5 Corrected)
    MIN_OPEN_INTEREST = 500  # OI ≥ 500
    MIN_DAILY_VOLUME = 100   # avg daily option vol ≥ 100
    MAX_SPREAD_PCT = Decimal("0.05")  # spread ≤ 5% of mid
    MAX_ORDER_SIZE_PCT = Decimal("0.10")  # order size ≤ 10% of ADV
    
    def __init__(self):
        """Initialize liquidity validator."""
        self.liquidity_cache = {}  # symbol -> LiquidityMetrics
        self.cache_duration_minutes = 5  # Cache for 5 minutes
    
    def validate_option_liquidity(
        self,
        symbol: str,
        strike: Decimal,
        expiration: str,
        option_type: str,
        order_size: int,
        market_data: Dict[str, Any]
    ) -> LiquidityValidationResult:
        """
        Validate option liquidity against Constitution requirements.
        
        Args:
            symbol: Underlying symbol
            strike: Option strike price
            expiration: Option expiration date
            option_type: "call" or "put"
            order_size: Proposed order size (contracts)
            market_data: Current market data
            
        Returns:
            LiquidityValidationResult
        """
        try:
            # Extract market data
            open_interest = market_data.get("open_interest", 0)
            daily_volume = market_data.get("daily_volume", 0)
            avg_daily_volume = market_data.get("avg_daily_volume", daily_volume)
            bid = Decimal(str(market_data.get("bid", 0)))
            ask = Decimal(str(market_data.get("ask", 0)))
            
            # Calculate derived metrics
            mid = (bid + ask) / 2 if bid > 0 and ask > 0 else Decimal("0")
            spread = ask - bid if ask > bid else Decimal("0")
            spread_percentage = (spread / mid) if mid > 0 else Decimal("1.0")
            
            # Create metrics object
            metrics = LiquidityMetrics(
                symbol=symbol,
                strike=strike,
                expiration=expiration,
                option_type=option_type,
                open_interest=open_interest,
                daily_volume=daily_volume,
                avg_daily_volume=avg_daily_volume,
                bid=bid,
                ask=ask,
                mid=mid,
                spread=spread,
                spread_percentage=spread_percentage,
                last_updated=datetime.now()
            )
            
            # Validate liquidity requirements
            violations = []
            
            # 1. Open Interest requirement
            if open_interest < self.MIN_OPEN_INTEREST:
                violations.append(
                    f"Open interest {open_interest} < required {self.MIN_OPEN_INTEREST}"
                )
            
            # 2. Daily volume requirement
            if avg_daily_volume < self.MIN_DAILY_VOLUME:
                violations.append(
                    f"Avg daily volume {avg_daily_volume} < required {self.MIN_DAILY_VOLUME}"
                )
            
            # 3. Spread requirement
            if spread_percentage > self.MAX_SPREAD_PCT:
                violations.append(
                    f"Spread {spread_percentage:.1%} > max allowed {self.MAX_SPREAD_PCT:.1%}"
                )
            
            # 4. Order size vs ADV requirement
            adv_percentage = Decimal("0")
            if avg_daily_volume > 0:
                adv_percentage = Decimal(str(order_size)) / Decimal(str(avg_daily_volume))
                if adv_percentage > self.MAX_ORDER_SIZE_PCT:
                    violations.append(
                        f"Order size {order_size} is {adv_percentage:.1%} of ADV, "
                        f"max allowed {self.MAX_ORDER_SIZE_PCT:.1%}"
                    )
            
            # Determine recommendation
            if not violations:
                recommendation = "APPROVED"
                logger.info(f"Liquidity validation passed for {symbol} {strike}{option_type[0].upper()}")
            else:
                recommendation = "REJECTED"
                logger.warning(f"Liquidity validation failed for {symbol} {strike}{option_type[0].upper()}: {violations}")
            
            return LiquidityValidationResult(
                valid=len(violations) == 0,
                violations=violations,
                metrics=metrics,
                order_size=order_size,
                adv_percentage=adv_percentage,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error validating liquidity for {symbol} {strike}{option_type[0].upper()}: {e}")
            return LiquidityValidationResult(
                valid=False,
                violations=[f"Validation error: {str(e)}"],
                metrics=None,
                order_size=order_size,
                adv_percentage=Decimal("0"),
                recommendation="ERROR"
            )
    
    def batch_validate_liquidity(
        self,
        orders: List[Dict[str, Any]],
        market_data_batch: Dict[str, Dict[str, Any]]
    ) -> Dict[str, LiquidityValidationResult]:
        """
        Batch validate liquidity for multiple orders.
        
        Args:
            orders: List of order dicts with symbol, strike, expiration, etc.
            market_data_batch: Market data keyed by option identifier
            
        Returns:
            Dict mapping order IDs to validation results
        """
        results = {}
        
        for order in orders:
            try:
                order_id = order.get("order_id", "unknown")
                symbol = order.get("symbol")
                strike = Decimal(str(order.get("strike", 0)))
                expiration = order.get("expiration")
                option_type = order.get("option_type", "call")
                order_size = order.get("quantity", 0)
                
                # Create option identifier for market data lookup
                option_id = f"{symbol}_{strike}_{expiration}_{option_type}"
                market_data = market_data_batch.get(option_id, {})
                
                # Validate liquidity
                result = self.validate_option_liquidity(
                    symbol, strike, expiration, option_type, order_size, market_data
                )
                
                results[order_id] = result
                
            except Exception as e:
                logger.error(f"Error in batch liquidity validation for order {order.get('order_id')}: {e}")
                results[order.get("order_id", "unknown")] = LiquidityValidationResult(
                    valid=False,
                    violations=[f"Batch validation error: {str(e)}"],
                    metrics=None,
                    order_size=order.get("quantity", 0),
                    adv_percentage=Decimal("0"),
                    recommendation="ERROR"
                )
        
        return results
    
    def get_liquidity_summary(self, validation_results: List[LiquidityValidationResult]) -> Dict[str, Any]:
        """
        Get summary statistics from liquidity validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Summary statistics
        """
        if not validation_results:
            return {
                "total_validations": 0,
                "approved": 0,
                "rejected": 0,
                "approval_rate": 0.0,
                "common_violations": [],
                "avg_spread_percentage": 0.0,
                "avg_open_interest": 0,
                "avg_daily_volume": 0
            }
        
        approved = sum(1 for r in validation_results if r.valid)
        rejected = len(validation_results) - approved
        
        # Collect violation types
        all_violations = []
        for result in validation_results:
            all_violations.extend(result.violations)
        
        # Count violation types
        violation_counts = {}
        for violation in all_violations:
            violation_type = violation.split()[0]  # First word
            violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1
        
        # Calculate averages (only for valid metrics)
        valid_metrics = [r.metrics for r in validation_results if r.metrics]
        
        avg_spread_percentage = 0.0
        avg_open_interest = 0
        avg_daily_volume = 0
        
        if valid_metrics:
            avg_spread_percentage = float(sum(m.spread_percentage for m in valid_metrics) / len(valid_metrics))
            avg_open_interest = sum(m.open_interest for m in valid_metrics) // len(valid_metrics)
            avg_daily_volume = sum(m.avg_daily_volume for m in valid_metrics) // len(valid_metrics)
        
        return {
            "total_validations": len(validation_results),
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / len(validation_results),
            "common_violations": sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "avg_spread_percentage": avg_spread_percentage,
            "avg_open_interest": avg_open_interest,
            "avg_daily_volume": avg_daily_volume,
            "requirements": {
                "min_open_interest": self.MIN_OPEN_INTEREST,
                "min_daily_volume": self.MIN_DAILY_VOLUME,
                "max_spread_pct": float(self.MAX_SPREAD_PCT),
                "max_order_size_pct": float(self.MAX_ORDER_SIZE_PCT)
            }
        }
    
    def update_liquidity_cache(self, symbol: str, metrics: LiquidityMetrics) -> None:
        """Update liquidity cache with new metrics."""
        cache_key = f"{symbol}_{metrics.strike}_{metrics.expiration}_{metrics.option_type}"
        self.liquidity_cache[cache_key] = metrics
        
        # Clean old cache entries
        cutoff_time = datetime.now() - timedelta(minutes=self.cache_duration_minutes)
        expired_keys = [
            key for key, cached_metrics in self.liquidity_cache.items()
            if cached_metrics.last_updated < cutoff_time
        ]
        
        for key in expired_keys:
            del self.liquidity_cache[key]
    
    def get_cached_liquidity(self, symbol: str, strike: Decimal, expiration: str, option_type: str) -> Optional[LiquidityMetrics]:
        """Get cached liquidity metrics if available and current."""
        cache_key = f"{symbol}_{strike}_{expiration}_{option_type}"
        cached_metrics = self.liquidity_cache.get(cache_key)
        
        if cached_metrics:
            # Check if cache is still valid
            age_minutes = (datetime.now() - cached_metrics.last_updated).total_seconds() / 60
            if age_minutes < self.cache_duration_minutes:
                return cached_metrics
            else:
                # Remove expired cache entry
                del self.liquidity_cache[cache_key]
        
        return None


# Global liquidity validator instance
liquidity_validator = LiquidityValidator()

