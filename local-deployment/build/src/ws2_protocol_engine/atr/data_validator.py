"""
ATR Data Validator

This module implements comprehensive data validation and quality checks
for ATR calculation to ensure reliable risk management decisions.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import statistics

logger = logging.getLogger(__name__)


class ATRDataValidator:
    """
    Data validator for ATR calculation inputs and outputs.
    
    Performs comprehensive validation and quality checks to ensure
    data integrity for risk management decisions.
    """
    
    def __init__(self):
        """Initialize ATR data validator."""
        self.min_data_points = 15  # Minimum for reliable ATR
        self.max_price_change_pct = 0.50  # 50% max daily change
        self.min_volume_threshold = 1000  # Minimum daily volume
        self.max_gap_days = 5  # Maximum gap in trading days
        self.outlier_threshold = 3.0  # Standard deviations for outlier detection
    
    def validate_price_data(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive validation of price data for ATR calculation.
        
        Args:
            price_data: List of price dictionaries
            
        Returns:
            Validation result with detailed analysis
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "quality_score": 100,
                "data_points": len(price_data),
                "validation_details": {}
            }
            
            if not price_data:
                validation_result.update({
                    "valid": False,
                    "errors": ["Price data is empty"],
                    "quality_score": 0
                })
                return validation_result
            
            # Basic structure validation
            structure_result = self._validate_data_structure(price_data)
            validation_result["validation_details"]["structure"] = structure_result
            validation_result["errors"].extend(structure_result["errors"])
            validation_result["warnings"].extend(structure_result["warnings"])
            
            if structure_result["errors"]:
                validation_result["valid"] = False
                validation_result["quality_score"] = 0
                return validation_result
            
            # Data completeness validation
            completeness_result = self._validate_data_completeness(price_data)
            validation_result["validation_details"]["completeness"] = completeness_result
            validation_result["warnings"].extend(completeness_result["warnings"])
            
            # Price relationship validation
            relationship_result = self._validate_price_relationships(price_data)
            validation_result["validation_details"]["relationships"] = relationship_result
            validation_result["errors"].extend(relationship_result["errors"])
            validation_result["warnings"].extend(relationship_result["warnings"])
            
            # Outlier detection
            outlier_result = self._detect_outliers(price_data)
            validation_result["validation_details"]["outliers"] = outlier_result
            validation_result["warnings"].extend(outlier_result["warnings"])
            
            # Volume validation
            volume_result = self._validate_volume_data(price_data)
            validation_result["validation_details"]["volume"] = volume_result
            validation_result["warnings"].extend(volume_result["warnings"])
            
            # Date continuity validation
            continuity_result = self._validate_date_continuity(price_data)
            validation_result["validation_details"]["continuity"] = continuity_result
            validation_result["warnings"].extend(continuity_result["warnings"])
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(validation_result["validation_details"])
            validation_result["quality_score"] = quality_score
            
            # Determine if data is valid for ATR calculation
            if validation_result["errors"]:
                validation_result["valid"] = False
            elif len(price_data) < self.min_data_points:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Insufficient data points: {len(price_data)} < {self.min_data_points}")
            elif quality_score < 50:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Data quality too low: {quality_score}% < 50%")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating price data: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "quality_score": 0,
                "data_points": len(price_data) if price_data else 0
            }
    
    def _validate_data_structure(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate basic data structure."""
        errors = []
        warnings = []
        required_fields = ['date', 'high', 'low', 'close']
        optional_fields = ['volume', 'open']
        
        for i, data_point in enumerate(price_data):
            if not isinstance(data_point, dict):
                errors.append(f"Data point {i} is not a dictionary")
                continue
            
            # Check required fields
            for field in required_fields:
                if field not in data_point:
                    errors.append(f"Missing required field '{field}' in data point {i}")
                elif field == 'date':
                    # Validate date format
                    try:
                        if isinstance(data_point[field], str):
                            datetime.strptime(data_point[field], "%Y-%m-%d")
                        elif not isinstance(data_point[field], date):
                            errors.append(f"Invalid date format in data point {i}")
                    except ValueError:
                        errors.append(f"Invalid date format in data point {i}: {data_point[field]}")
                else:
                    # Validate numeric fields
                    if not isinstance(data_point[field], (int, float)):
                        try:
                            float(data_point[field])
                        except (ValueError, TypeError):
                            errors.append(f"Invalid {field} value in data point {i}: {data_point[field]}")
                    elif data_point[field] <= 0:
                        errors.append(f"Non-positive {field} value in data point {i}: {data_point[field]}")
            
            # Check optional fields
            for field in optional_fields:
                if field in data_point and field == 'volume':
                    if not isinstance(data_point[field], (int, float)) or data_point[field] < 0:
                        warnings.append(f"Invalid volume in data point {i}: {data_point[field]}")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "required_fields_present": len(errors) == 0
        }
    
    def _validate_data_completeness(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data completeness and sufficiency."""
        warnings = []
        
        data_points = len(price_data)
        
        if data_points < self.min_data_points:
            warnings.append(f"Data points ({data_points}) below recommended minimum ({self.min_data_points})")
        
        # Check for missing volume data
        volume_missing = sum(1 for d in price_data if 'volume' not in d or d.get('volume', 0) == 0)
        if volume_missing > 0:
            volume_missing_pct = (volume_missing / data_points) * 100
            if volume_missing_pct > 20:
                warnings.append(f"High percentage of missing volume data: {volume_missing_pct:.1f}%")
        
        return {
            "warnings": warnings,
            "data_points": data_points,
            "volume_missing_pct": (volume_missing / data_points) * 100 if data_points > 0 else 0
        }
    
    def _validate_price_relationships(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate price relationships (High >= Low, Close within range)."""
        errors = []
        warnings = []
        
        for i, data_point in enumerate(price_data):
            try:
                high = float(data_point['high'])
                low = float(data_point['low'])
                close = float(data_point['close'])
                
                # High must be >= Low
                if high < low:
                    errors.append(f"High < Low in data point {i}: {high} < {low}")
                
                # Close should be within High-Low range
                if not (low <= close <= high):
                    warnings.append(f"Close outside High-Low range in data point {i}: {close} not in [{low}, {high}]")
                
                # Check for extreme price changes (if previous data available)
                if i > 0:
                    prev_close = float(price_data[i-1]['close'])
                    price_change_pct = abs(close - prev_close) / prev_close
                    
                    if price_change_pct > self.max_price_change_pct:
                        warnings.append(f"Large price change in data point {i}: {price_change_pct:.1%}")
                
            except (KeyError, ValueError, TypeError) as e:
                errors.append(f"Error validating price relationships in data point {i}: {str(e)}")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
    
    def _detect_outliers(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect outliers in price data using statistical methods."""
        warnings = []
        outliers_detected = []
        
        try:
            # Extract price changes for outlier detection
            price_changes = []
            for i in range(1, len(price_data)):
                try:
                    current_close = float(price_data[i]['close'])
                    previous_close = float(price_data[i-1]['close'])
                    change_pct = (current_close - previous_close) / previous_close
                    price_changes.append(change_pct)
                except (KeyError, ValueError, TypeError):
                    continue
            
            if len(price_changes) < 5:
                return {"warnings": warnings, "outliers_detected": outliers_detected}
            
            # Calculate statistics
            mean_change = statistics.mean(price_changes)
            stdev_change = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
            
            if stdev_change == 0:
                return {"warnings": warnings, "outliers_detected": outliers_detected}
            
            # Detect outliers using z-score
            for i, change in enumerate(price_changes):
                z_score = abs(change - mean_change) / stdev_change
                if z_score > self.outlier_threshold:
                    outliers_detected.append({
                        "data_point": i + 1,
                        "price_change_pct": change,
                        "z_score": z_score,
                        "date": price_data[i + 1].get('date', 'unknown')
                    })
            
            if outliers_detected:
                warnings.append(f"Detected {len(outliers_detected)} statistical outliers in price data")
        
        except Exception as e:
            warnings.append(f"Error in outlier detection: {str(e)}")
        
        return {
            "warnings": warnings,
            "outliers_detected": outliers_detected,
            "outlier_count": len(outliers_detected)
        }
    
    def _validate_volume_data(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate volume data quality."""
        warnings = []
        
        volumes = []
        zero_volume_count = 0
        
        for data_point in price_data:
            volume = data_point.get('volume', 0)
            try:
                volume = int(volume) if volume is not None else 0
                volumes.append(volume)
                if volume == 0:
                    zero_volume_count += 1
            except (ValueError, TypeError):
                zero_volume_count += 1
                volumes.append(0)
        
        if volumes:
            avg_volume = sum(volumes) / len(volumes)
            zero_volume_pct = (zero_volume_count / len(volumes)) * 100
            
            if zero_volume_pct > 10:
                warnings.append(f"High percentage of zero volume days: {zero_volume_pct:.1f}%")
            
            if avg_volume < self.min_volume_threshold:
                warnings.append(f"Low average volume: {avg_volume:.0f} < {self.min_volume_threshold}")
            
            # Check for volume outliers
            non_zero_volumes = [v for v in volumes if v > 0]
            if len(non_zero_volumes) > 1:
                try:
                    median_volume = statistics.median(non_zero_volumes)
                    high_volume_threshold = median_volume * 10
                    
                    high_volume_days = sum(1 for v in non_zero_volumes if v > high_volume_threshold)
                    if high_volume_days > len(non_zero_volumes) * 0.05:  # More than 5%
                        warnings.append(f"Unusual volume spikes detected: {high_volume_days} days")
                except Exception:
                    pass
        
        return {
            "warnings": warnings,
            "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
            "zero_volume_pct": zero_volume_pct if volumes else 0
        }
    
    def _validate_date_continuity(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate date continuity and identify gaps."""
        warnings = []
        gaps_detected = []
        
        try:
            dates = []
            for data_point in price_data:
                date_str = data_point.get('date', '')
                try:
                    if isinstance(date_str, str):
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                    elif isinstance(date_str, date):
                        date_obj = date_str
                    else:
                        continue
                    dates.append(date_obj)
                except ValueError:
                    continue
            
            if len(dates) < 2:
                return {"warnings": warnings, "gaps_detected": gaps_detected}
            
            # Sort dates to ensure chronological order
            dates.sort()
            
            # Check for gaps (excluding weekends)
            for i in range(1, len(dates)):
                current_date = dates[i]
                previous_date = dates[i-1]
                
                # Calculate business days between dates
                days_diff = (current_date - previous_date).days
                
                # Account for weekends (rough approximation)
                business_days_diff = days_diff - (days_diff // 7) * 2
                
                if business_days_diff > self.max_gap_days:
                    gaps_detected.append({
                        "start_date": previous_date.strftime("%Y-%m-%d"),
                        "end_date": current_date.strftime("%Y-%m-%d"),
                        "days_gap": days_diff,
                        "business_days_gap": business_days_diff
                    })
            
            if gaps_detected:
                warnings.append(f"Detected {len(gaps_detected)} significant gaps in trading dates")
        
        except Exception as e:
            warnings.append(f"Error validating date continuity: {str(e)}")
        
        return {
            "warnings": warnings,
            "gaps_detected": gaps_detected,
            "gap_count": len(gaps_detected)
        }
    
    def _calculate_quality_score(self, validation_details: Dict[str, Any]) -> int:
        """Calculate overall data quality score (0-100)."""
        try:
            score = 100
            
            # Deduct points for various issues
            structure_errors = len(validation_details.get("structure", {}).get("errors", []))
            relationship_errors = len(validation_details.get("relationships", {}).get("errors", []))
            
            # Major deductions for errors
            score -= structure_errors * 20
            score -= relationship_errors * 15
            
            # Minor deductions for warnings
            total_warnings = sum(
                len(details.get("warnings", []))
                for details in validation_details.values()
                if isinstance(details, dict)
            )
            score -= min(total_warnings * 2, 30)  # Cap warning deduction at 30 points
            
            # Deductions for data quality issues
            completeness = validation_details.get("completeness", {})
            volume_missing_pct = completeness.get("volume_missing_pct", 0)
            score -= int(volume_missing_pct / 2)  # Deduct 1 point per 2% missing volume
            
            outliers = validation_details.get("outliers", {})
            outlier_count = outliers.get("outlier_count", 0)
            score -= min(outlier_count * 3, 20)  # Cap outlier deduction at 20 points
            
            gaps = validation_details.get("continuity", {})
            gap_count = gaps.get("gap_count", 0)
            score -= min(gap_count * 5, 25)  # Cap gap deduction at 25 points
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 50  # Default to middle score on error
    
    def validate_atr_result(self, atr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate ATR calculation result.
        
        Args:
            atr_result: ATR calculation result
            
        Returns:
            Validation result
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "atr_quality": "good"
            }
            
            if not isinstance(atr_result, dict):
                validation_result.update({
                    "valid": False,
                    "errors": ["ATR result is not a dictionary"],
                    "atr_quality": "invalid"
                })
                return validation_result
            
            # Check for calculation errors
            if "error" in atr_result:
                validation_result.update({
                    "valid": False,
                    "errors": [f"ATR calculation error: {atr_result['error']}"],
                    "atr_quality": "invalid"
                })
                return validation_result
            
            # Validate ATR value
            atr_value = atr_result.get("atr")
            if atr_value is None:
                validation_result.update({
                    "valid": False,
                    "errors": ["ATR value is missing"],
                    "atr_quality": "invalid"
                })
                return validation_result
            
            try:
                atr_float = float(atr_value)
                if atr_float <= 0:
                    validation_result["errors"].append("ATR value must be positive")
                    validation_result["valid"] = False
                elif atr_float < 0.01:
                    validation_result["warnings"].append("ATR value is very low, may indicate low volatility")
                    validation_result["atr_quality"] = "low_volatility"
                elif atr_float > 100:
                    validation_result["warnings"].append("ATR value is very high, may indicate extreme volatility")
                    validation_result["atr_quality"] = "high_volatility"
            except (ValueError, TypeError):
                validation_result.update({
                    "valid": False,
                    "errors": ["ATR value is not numeric"],
                    "atr_quality": "invalid"
                })
                return validation_result
            
            # Validate data points used
            data_points_used = atr_result.get("data_points_used", 0)
            if data_points_used < self.min_data_points:
                validation_result["warnings"].append(f"ATR calculated with insufficient data points: {data_points_used}")
                validation_result["atr_quality"] = "insufficient_data"
            
            # Validate calculation method
            method = atr_result.get("method")
            if method not in ["sma", "ema", "wilder"]:
                validation_result["warnings"].append(f"Unknown ATR calculation method: {method}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating ATR result: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "errors": [f"ATR result validation error: {str(e)}"],
                "warnings": [],
                "atr_quality": "invalid"
            }

