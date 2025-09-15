"""
ATR Calculator

This module implements the mathematical calculation of Average True Range (ATR)
using various methods and periods. ATR is critical for the Protocol Engine's
risk management system.

ATR Formula:
True Range (TR) = max(High - Low, |High - Previous Close|, |Low - Previous Close|)
ATR = Simple Moving Average or Exponential Moving Average of TR over N periods
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, getcontext
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class ATRCalculator:
    """
    ATR Calculator implementing various ATR calculation methods.
    
    Supports both Simple Moving Average (SMA) and Exponential Moving Average (EMA)
    methods for ATR calculation with configurable periods.
    """
    
    def __init__(self):
        """Initialize ATR Calculator."""
        self.supported_methods = ["sma", "ema", "wilder"]
        self.default_period = 14
        self.min_data_points = 2  # Minimum data points needed
        
    def calculate_true_range(self, 
                           high: float, 
                           low: float, 
                           previous_close: float) -> Decimal:
        """
        Calculate True Range for a single period.
        
        Args:
            high: High price for the period
            low: Low price for the period
            previous_close: Previous period's closing price
            
        Returns:
            True Range value
        """
        try:
            high_dec = Decimal(str(high))
            low_dec = Decimal(str(low))
            prev_close_dec = Decimal(str(previous_close))
            
            # TR = max(H-L, |H-PC|, |L-PC|)
            hl_range = high_dec - low_dec
            h_pc_range = abs(high_dec - prev_close_dec)
            l_pc_range = abs(low_dec - prev_close_dec)
            
            true_range = max(hl_range, h_pc_range, l_pc_range)
            
            return true_range
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating true range: {str(e)}")
            return Decimal("0")
    
    def calculate_atr_sma(self, 
                         price_data: List[Dict[str, float]], 
                         period: int = 14) -> Dict[str, Any]:
        """
        Calculate ATR using Simple Moving Average method.
        
        Args:
            price_data: List of price dictionaries with 'high', 'low', 'close'
            period: ATR period (default 14)
            
        Returns:
            ATR calculation result
        """
        try:
            if len(price_data) < period + 1:
                return {
                    "atr": None,
                    "error": f"Insufficient data: need {period + 1}, got {len(price_data)}",
                    "method": "sma"
                }
            
            true_ranges = []
            
            # Calculate True Range for each period
            for i in range(1, len(price_data)):
                current = price_data[i]
                previous = price_data[i-1]
                
                tr = self.calculate_true_range(
                    current['high'],
                    current['low'], 
                    previous['close']
                )
                true_ranges.append(float(tr))
            
            # Calculate ATR as SMA of True Ranges
            if len(true_ranges) >= period:
                recent_trs = true_ranges[-period:]
                atr = Decimal(str(sum(recent_trs))) / Decimal(str(period))
                
                return {
                    "atr": float(atr),
                    "true_ranges": true_ranges,
                    "period": period,
                    "method": "sma",
                    "data_points_used": len(true_ranges),
                    "calculation_date": datetime.now().isoformat()
                }
            else:
                return {
                    "atr": None,
                    "error": f"Insufficient true ranges: need {period}, got {len(true_ranges)}",
                    "method": "sma"
                }
                
        except Exception as e:
            logger.error(f"Error calculating ATR SMA: {str(e)}", exc_info=True)
            return {
                "atr": None,
                "error": str(e),
                "method": "sma"
            }
    
    def calculate_atr_ema(self, 
                         price_data: List[Dict[str, float]], 
                         period: int = 14,
                         smoothing_factor: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate ATR using Exponential Moving Average method.
        
        Args:
            price_data: List of price dictionaries
            period: ATR period (default 14)
            smoothing_factor: EMA smoothing factor (default 2/(period+1))
            
        Returns:
            ATR calculation result
        """
        try:
            if len(price_data) < period + 1:
                return {
                    "atr": None,
                    "error": f"Insufficient data: need {period + 1}, got {len(price_data)}",
                    "method": "ema"
                }
            
            if smoothing_factor is None:
                smoothing_factor = 2.0 / (period + 1)
            
            true_ranges = []
            
            # Calculate True Range for each period
            for i in range(1, len(price_data)):
                current = price_data[i]
                previous = price_data[i-1]
                
                tr = self.calculate_true_range(
                    current['high'],
                    current['low'],
                    previous['close']
                )
                true_ranges.append(float(tr))
            
            if len(true_ranges) < period:
                return {
                    "atr": None,
                    "error": f"Insufficient true ranges: need {period}, got {len(true_ranges)}",
                    "method": "ema"
                }
            
            # Initialize ATR with SMA of first 'period' true ranges
            initial_atr = sum(true_ranges[:period]) / period
            atr = initial_atr
            
            # Apply EMA to remaining true ranges
            for tr in true_ranges[period:]:
                atr = (tr * smoothing_factor) + (atr * (1 - smoothing_factor))
            
            return {
                "atr": atr,
                "true_ranges": true_ranges,
                "period": period,
                "method": "ema",
                "smoothing_factor": smoothing_factor,
                "initial_atr": initial_atr,
                "data_points_used": len(true_ranges),
                "calculation_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating ATR EMA: {str(e)}", exc_info=True)
            return {
                "atr": None,
                "error": str(e),
                "method": "ema"
            }
    
    def calculate_atr_wilder(self, 
                           price_data: List[Dict[str, float]], 
                           period: int = 14) -> Dict[str, Any]:
        """
        Calculate ATR using Wilder's smoothing method (original ATR method).
        
        Wilder's method uses a modified EMA with smoothing factor = 1/period
        
        Args:
            price_data: List of price dictionaries
            period: ATR period (default 14)
            
        Returns:
            ATR calculation result
        """
        try:
            if len(price_data) < period + 1:
                return {
                    "atr": None,
                    "error": f"Insufficient data: need {period + 1}, got {len(price_data)}",
                    "method": "wilder"
                }
            
            true_ranges = []
            
            # Calculate True Range for each period
            for i in range(1, len(price_data)):
                current = price_data[i]
                previous = price_data[i-1]
                
                tr = self.calculate_true_range(
                    current['high'],
                    current['low'],
                    previous['close']
                )
                true_ranges.append(float(tr))
            
            if len(true_ranges) < period:
                return {
                    "atr": None,
                    "error": f"Insufficient true ranges: need {period}, got {len(true_ranges)}",
                    "method": "wilder"
                }
            
            # Initialize ATR with SMA of first 'period' true ranges
            initial_atr = sum(true_ranges[:period]) / period
            atr = initial_atr
            
            # Apply Wilder's smoothing to remaining true ranges
            # ATR = ((Previous ATR * (period - 1)) + Current TR) / period
            for tr in true_ranges[period:]:
                atr = ((atr * (period - 1)) + tr) / period
            
            return {
                "atr": atr,
                "true_ranges": true_ranges,
                "period": period,
                "method": "wilder",
                "initial_atr": initial_atr,
                "data_points_used": len(true_ranges),
                "calculation_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating ATR Wilder: {str(e)}", exc_info=True)
            return {
                "atr": None,
                "error": str(e),
                "method": "wilder"
            }
    
    def calculate_atr(self, 
                     price_data: List[Dict[str, float]], 
                     period: int = 14,
                     method: str = "wilder") -> Dict[str, Any]:
        """
        Calculate ATR using specified method.
        
        Args:
            price_data: List of price dictionaries with 'high', 'low', 'close'
            period: ATR period (default 14)
            method: Calculation method ('sma', 'ema', 'wilder')
            
        Returns:
            ATR calculation result
        """
        if method not in self.supported_methods:
            return {
                "atr": None,
                "error": f"Unsupported method: {method}. Supported: {self.supported_methods}",
                "method": method
            }
        
        if method == "sma":
            return self.calculate_atr_sma(price_data, period)
        elif method == "ema":
            return self.calculate_atr_ema(price_data, period)
        elif method == "wilder":
            return self.calculate_atr_wilder(price_data, period)
    
    def calculate_multiple_periods(self, 
                                 price_data: List[Dict[str, float]], 
                                 periods: List[int] = [5, 14, 21],
                                 method: str = "wilder") -> Dict[str, Any]:
        """
        Calculate ATR for multiple periods.
        
        Args:
            price_data: List of price dictionaries
            periods: List of periods to calculate (default [5, 14, 21])
            method: Calculation method
            
        Returns:
            ATR results for all periods
        """
        results = {}
        
        for period in periods:
            result = self.calculate_atr(price_data, period, method)
            results[f"atr_{period}"] = result
        
        return {
            "multi_period_atr": results,
            "periods": periods,
            "method": method,
            "calculation_date": datetime.now().isoformat()
        }
    
    def validate_price_data(self, price_data: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Validate price data for ATR calculation.
        
        Args:
            price_data: List of price dictionaries
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        if not price_data:
            errors.append("Price data is empty")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        required_fields = ['high', 'low', 'close']
        
        for i, data_point in enumerate(price_data):
            # Check required fields
            for field in required_fields:
                if field not in data_point:
                    errors.append(f"Missing '{field}' in data point {i}")
                elif not isinstance(data_point[field], (int, float)):
                    errors.append(f"Invalid '{field}' type in data point {i}: expected number")
                elif data_point[field] <= 0:
                    errors.append(f"Invalid '{field}' value in data point {i}: must be positive")
            
            # Validate price relationships
            if all(field in data_point for field in required_fields):
                high = data_point['high']
                low = data_point['low']
                close = data_point['close']
                
                if high < low:
                    errors.append(f"High < Low in data point {i}: {high} < {low}")
                
                if not (low <= close <= high):
                    warnings.append(f"Close price outside High-Low range in data point {i}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data_points": len(price_data)
        }
    
    def get_atr_statistics(self, atr_results: List[float]) -> Dict[str, float]:
        """
        Calculate statistics for ATR values.
        
        Args:
            atr_results: List of ATR values
            
        Returns:
            ATR statistics
        """
        if not atr_results:
            return {}
        
        atr_array = np.array(atr_results)
        
        return {
            "mean": float(np.mean(atr_array)),
            "median": float(np.median(atr_array)),
            "std": float(np.std(atr_array)),
            "min": float(np.min(atr_array)),
            "max": float(np.max(atr_array)),
            "percentile_25": float(np.percentile(atr_array, 25)),
            "percentile_75": float(np.percentile(atr_array, 75)),
            "count": len(atr_results)
        }

