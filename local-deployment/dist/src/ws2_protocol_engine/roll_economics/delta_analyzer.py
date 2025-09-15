"""
Delta Band Analyzer

This module implements delta band analysis for determining optimal
roll timing based on option delta movements and target ranges.
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
import logging
import statistics

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class DeltaBandAnalyzer:
    """
    Analyzer for option delta bands and roll timing optimization.
    
    Determines optimal roll timing based on delta movement patterns,
    target delta ranges, and market conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize delta band analyzer.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        
        # Delta band configuration
        self.target_delta_range = {
            "min": Decimal(str(self.config.get("target_delta_min", 0.15))),
            "max": Decimal(str(self.config.get("target_delta_max", 0.35))),
            "optimal": Decimal(str(self.config.get("target_delta_optimal", 0.25)))
        }
        
        # Roll trigger thresholds
        self.roll_trigger_delta = Decimal(str(self.config.get("roll_trigger_delta", 0.50)))
        self.emergency_roll_delta = Decimal(str(self.config.get("emergency_roll_delta", 0.70)))
        
        # Analysis parameters
        self.lookback_days = self.config.get("lookback_days", 5)
        self.delta_smoothing_factor = Decimal(str(self.config.get("delta_smoothing_factor", 0.3)))
        
        logger.info("Delta Band Analyzer initialized")
    
    def analyze_delta_position(self, 
                             position: Dict[str, Any],
                             market_data: Dict[str, Any],
                             historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze current delta position and roll timing.
        
        Args:
            position: Current position details
            market_data: Current market data
            historical_data: Optional historical delta data
            
        Returns:
            Delta analysis and roll timing recommendation
        """
        try:
            current_delta = Decimal(str(position.get("delta", 0)))
            current_price = Decimal(str(market_data.get("current_price", 0)))
            strike_price = Decimal(str(position.get("strike_price", 0)))
            
            # Calculate basic delta metrics
            delta_metrics = self._calculate_delta_metrics(current_delta, strike_price, current_price)
            
            # Analyze delta trend if historical data available
            delta_trend = self._analyze_delta_trend(historical_data) if historical_data else {}
            
            # Determine roll urgency
            roll_urgency = self._determine_roll_urgency(current_delta, delta_trend)
            
            # Calculate optimal target deltas
            target_deltas = self._calculate_target_deltas(position, market_data)
            
            # Analyze delta band positioning
            band_analysis = self._analyze_delta_bands(current_delta, target_deltas)
            
            # Generate roll timing recommendation
            timing_recommendation = self._generate_timing_recommendation(
                delta_metrics, roll_urgency, band_analysis
            )
            
            return {
                "success": True,
                "current_delta": float(current_delta),
                "delta_metrics": delta_metrics,
                "delta_trend": delta_trend,
                "roll_urgency": roll_urgency,
                "target_deltas": target_deltas,
                "band_analysis": band_analysis,
                "timing_recommendation": timing_recommendation,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing delta position: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _calculate_delta_metrics(self, 
                               current_delta: Decimal,
                               strike_price: Decimal,
                               current_price: Decimal) -> Dict[str, Any]:
        """Calculate basic delta metrics."""
        try:
            # Delta distance from target range
            target_min = self.target_delta_range["min"]
            target_max = self.target_delta_range["max"]
            target_optimal = self.target_delta_range["optimal"]
            
            # Distance calculations
            distance_from_optimal = abs(current_delta - target_optimal)
            distance_from_range = Decimal("0")
            
            if current_delta < target_min:
                distance_from_range = target_min - current_delta
                range_position = "below"
            elif current_delta > target_max:
                distance_from_range = current_delta - target_max
                range_position = "above"
            else:
                range_position = "within"
            
            # Moneyness calculation
            moneyness = current_price / strike_price if strike_price > 0 else Decimal("1")
            
            # Delta efficiency (how close to optimal)
            delta_efficiency = 1 - float(distance_from_optimal / target_optimal)
            delta_efficiency = max(0, min(1, delta_efficiency))
            
            return {
                "distance_from_optimal": float(distance_from_optimal),
                "distance_from_range": float(distance_from_range),
                "range_position": range_position,
                "moneyness": float(moneyness),
                "delta_efficiency": delta_efficiency,
                "in_target_range": range_position == "within"
            }
            
        except Exception as e:
            logger.error(f"Error calculating delta metrics: {str(e)}")
            return {}
    
    def _analyze_delta_trend(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze delta trend from historical data."""
        try:
            if not historical_data or len(historical_data) < 2:
                return {"trend": "insufficient_data"}
            
            # Extract delta values and timestamps
            deltas = []
            timestamps = []
            
            for data_point in historical_data[-self.lookback_days:]:
                if "delta" in data_point and "timestamp" in data_point:
                    deltas.append(float(data_point["delta"]))
                    timestamps.append(datetime.fromisoformat(data_point["timestamp"]))
            
            if len(deltas) < 2:
                return {"trend": "insufficient_data"}
            
            # Calculate trend metrics
            delta_changes = [deltas[i] - deltas[i-1] for i in range(1, len(deltas))]
            avg_change = statistics.mean(delta_changes)
            volatility = statistics.stdev(delta_changes) if len(delta_changes) > 1 else 0
            
            # Determine trend direction
            if avg_change > 0.01:
                trend_direction = "increasing"
            elif avg_change < -0.01:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            # Calculate trend strength
            trend_strength = min(abs(avg_change) * 10, 1.0)  # Normalize to 0-1
            
            # Predict next delta (simple linear extrapolation)
            if len(deltas) >= 2:
                predicted_delta = deltas[-1] + avg_change
            else:
                predicted_delta = deltas[-1]
            
            return {
                "trend": trend_direction,
                "strength": trend_strength,
                "avg_daily_change": avg_change,
                "volatility": volatility,
                "predicted_next_delta": predicted_delta,
                "data_points": len(deltas),
                "time_span_days": (timestamps[-1] - timestamps[0]).days if len(timestamps) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing delta trend: {str(e)}")
            return {"trend": "error", "error": str(e)}
    
    def _determine_roll_urgency(self, 
                              current_delta: Decimal,
                              delta_trend: Dict[str, Any]) -> Dict[str, Any]:
        """Determine urgency of rolling based on delta and trend."""
        try:
            urgency_level = "low"
            urgency_score = 0.0
            reasons = []
            
            # Check absolute delta thresholds
            if current_delta >= self.emergency_roll_delta:
                urgency_level = "emergency"
                urgency_score = 1.0
                reasons.append(f"Delta {float(current_delta):.3f} exceeds emergency threshold {float(self.emergency_roll_delta):.3f}")
            elif current_delta >= self.roll_trigger_delta:
                urgency_level = "high"
                urgency_score = 0.8
                reasons.append(f"Delta {float(current_delta):.3f} exceeds roll trigger {float(self.roll_trigger_delta):.3f}")
            elif current_delta >= self.target_delta_range["max"]:
                urgency_level = "medium"
                urgency_score = 0.6
                reasons.append(f"Delta {float(current_delta):.3f} above target range")
            
            # Consider trend impact
            trend_direction = delta_trend.get("trend", "stable")
            trend_strength = delta_trend.get("strength", 0)
            
            if trend_direction == "increasing" and trend_strength > 0.5:
                urgency_score += 0.2
                reasons.append("Strong increasing delta trend")
            elif trend_direction == "decreasing" and current_delta > self.target_delta_range["max"]:
                urgency_score -= 0.1
                reasons.append("Delta trending down from high levels")
            
            # Predicted delta impact
            predicted_delta = delta_trend.get("predicted_next_delta")
            if predicted_delta and Decimal(str(predicted_delta)) > self.roll_trigger_delta:
                urgency_score += 0.1
                reasons.append("Predicted delta will exceed trigger")
            
            # Final urgency level adjustment
            if urgency_score >= 0.9:
                urgency_level = "emergency"
            elif urgency_score >= 0.7:
                urgency_level = "high"
            elif urgency_score >= 0.4:
                urgency_level = "medium"
            else:
                urgency_level = "low"
            
            return {
                "level": urgency_level,
                "score": min(1.0, max(0.0, urgency_score)),
                "reasons": reasons,
                "recommended_action": self._get_action_for_urgency(urgency_level)
            }
            
        except Exception as e:
            logger.error(f"Error determining roll urgency: {str(e)}")
            return {
                "level": "medium",
                "score": 0.5,
                "reasons": ["Error in urgency calculation"],
                "recommended_action": "monitor"
            }
    
    def _get_action_for_urgency(self, urgency_level: str) -> str:
        """Get recommended action based on urgency level."""
        action_map = {
            "emergency": "roll_immediately",
            "high": "roll_today",
            "medium": "roll_soon",
            "low": "monitor"
        }
        return action_map.get(urgency_level, "monitor")
    
    def _calculate_target_deltas(self, 
                               position: Dict[str, Any],
                               market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal target deltas for roll."""
        try:
            current_price = Decimal(str(market_data.get("current_price", 0)))
            option_type = position.get("option_type", "call").lower()
            
            # Calculate target strikes based on delta targets
            target_strikes = {}
            
            for delta_name, target_delta in self.target_delta_range.items():
                # Simplified strike calculation (would use Black-Scholes in production)
                if option_type == "call":
                    # For calls, higher delta means closer to ITM (lower strike)
                    strike_adjustment = (Decimal("0.5") - target_delta) * current_price * Decimal("0.1")
                    target_strike = current_price + strike_adjustment
                else:  # put
                    # For puts, higher delta means closer to ITM (higher strike)
                    strike_adjustment = (target_delta - Decimal("0.5")) * current_price * Decimal("0.1")
                    target_strike = current_price + strike_adjustment
                
                target_strikes[delta_name] = {
                    "delta": float(target_delta),
                    "estimated_strike": float(target_strike),
                    "distance_from_current": float(abs(target_strike - current_price) / current_price * 100)
                }
            
            return {
                "target_range": {
                    "min_delta": float(self.target_delta_range["min"]),
                    "max_delta": float(self.target_delta_range["max"]),
                    "optimal_delta": float(self.target_delta_range["optimal"])
                },
                "target_strikes": target_strikes,
                "current_price": float(current_price),
                "option_type": option_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating target deltas: {str(e)}")
            return {}
    
    def _analyze_delta_bands(self, 
                           current_delta: Decimal,
                           target_deltas: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current position relative to delta bands."""
        try:
            target_range = target_deltas.get("target_range", {})
            min_delta = Decimal(str(target_range.get("min_delta", 0.15)))
            max_delta = Decimal(str(target_range.get("max_delta", 0.35)))
            optimal_delta = Decimal(str(target_range.get("optimal_delta", 0.25)))
            
            # Band positioning
            if current_delta < min_delta:
                band_position = "below_range"
                band_score = float((current_delta / min_delta) * 0.5)  # 0-0.5 for below range
            elif current_delta > max_delta:
                band_position = "above_range"
                excess = current_delta - max_delta
                band_score = max(0.5, 1.0 - float(excess / optimal_delta))  # Decreasing score above range
            else:
                band_position = "within_range"
                # Score based on distance from optimal
                distance_from_optimal = abs(current_delta - optimal_delta)
                max_distance = max(optimal_delta - min_delta, max_delta - optimal_delta)
                band_score = 1.0 - float(distance_from_optimal / max_distance)
            
            # Band health assessment
            if band_score >= 0.8:
                band_health = "excellent"
            elif band_score >= 0.6:
                band_health = "good"
            elif band_score >= 0.4:
                band_health = "fair"
            else:
                band_health = "poor"
            
            return {
                "position": band_position,
                "score": band_score,
                "health": band_health,
                "distance_from_optimal": float(abs(current_delta - optimal_delta)),
                "optimal_delta": float(optimal_delta),
                "range_boundaries": {
                    "min": float(min_delta),
                    "max": float(max_delta)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing delta bands: {str(e)}")
            return {}
    
    def _generate_timing_recommendation(self, 
                                      delta_metrics: Dict[str, Any],
                                      roll_urgency: Dict[str, Any],
                                      band_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive timing recommendation."""
        try:
            urgency_level = roll_urgency.get("level", "medium")
            urgency_score = roll_urgency.get("score", 0.5)
            band_score = band_analysis.get("score", 0.5)
            in_target_range = delta_metrics.get("in_target_range", False)
            
            # Determine primary recommendation
            if urgency_level == "emergency":
                recommendation = "roll_immediately"
                confidence = 0.95
            elif urgency_level == "high":
                recommendation = "roll_today"
                confidence = 0.85
            elif urgency_level == "medium" and not in_target_range:
                recommendation = "roll_soon"
                confidence = 0.70
            elif urgency_level == "medium" and band_score < 0.6:
                recommendation = "consider_roll"
                confidence = 0.60
            else:
                recommendation = "monitor"
                confidence = 0.50
            
            # Adjust confidence based on band analysis
            if band_analysis.get("health") == "excellent":
                confidence = max(0.3, confidence - 0.2)  # Less urgent if in good position
            elif band_analysis.get("health") == "poor":
                confidence = min(0.95, confidence + 0.2)  # More urgent if in poor position
            
            # Generate specific timing guidance
            timing_guidance = self._generate_timing_guidance(recommendation, urgency_level)
            
            # Compile reasons
            reasons = roll_urgency.get("reasons", [])
            if band_analysis.get("position") == "above_range":
                reasons.append("Delta above target range")
            elif band_analysis.get("position") == "below_range":
                reasons.append("Delta below target range")
            
            return {
                "action": recommendation,
                "confidence": confidence,
                "urgency_level": urgency_level,
                "timing_guidance": timing_guidance,
                "reasons": reasons,
                "metrics_summary": {
                    "urgency_score": urgency_score,
                    "band_score": band_score,
                    "overall_score": (urgency_score + band_score) / 2
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating timing recommendation: {str(e)}")
            return {
                "action": "monitor",
                "confidence": 0.5,
                "urgency_level": "medium",
                "timing_guidance": "Monitor position and reassess",
                "reasons": ["Error in recommendation generation"],
                "metrics_summary": {}
            }
    
    def _generate_timing_guidance(self, recommendation: str, urgency_level: str) -> str:
        """Generate specific timing guidance text."""
        guidance_map = {
            "roll_immediately": "Execute roll within the next hour. Delta has reached critical levels.",
            "roll_today": "Execute roll before market close today. High urgency due to delta breach.",
            "roll_soon": "Plan to execute roll within 1-2 trading days. Monitor for further delta movement.",
            "consider_roll": "Evaluate roll opportunity. Position is approaching suboptimal delta range.",
            "monitor": "Continue monitoring. Position is within acceptable parameters."
        }
        
        return guidance_map.get(recommendation, "Monitor position and reassess as needed.")
    
    def calculate_optimal_roll_strikes(self, 
                                     current_position: Dict[str, Any],
                                     market_data: Dict[str, Any],
                                     expiry_date: date) -> Dict[str, Any]:
        """
        Calculate optimal roll strikes based on delta targets.
        
        Args:
            current_position: Current position details
            market_data: Current market data
            expiry_date: Target expiry date
            
        Returns:
            Optimal strike recommendations
        """
        try:
            current_price = Decimal(str(market_data.get("current_price", 0)))
            option_type = current_position.get("option_type", "call").lower()
            
            # Calculate strikes for each target delta
            optimal_strikes = []
            
            for delta_target in [0.15, 0.20, 0.25, 0.30, 0.35]:
                delta_decimal = Decimal(str(delta_target))
                
                # Simplified strike calculation (production would use Black-Scholes)
                if option_type == "call":
                    strike_adjustment = (Decimal("0.5") - delta_decimal) * current_price * Decimal("0.15")
                    estimated_strike = current_price + strike_adjustment
                else:  # put
                    strike_adjustment = (delta_decimal - Decimal("0.5")) * current_price * Decimal("0.15")
                    estimated_strike = current_price + strike_adjustment
                
                # Round to nearest strike increment (typically $5 or $10)
                strike_increment = Decimal("5")  # $5 increments
                rounded_strike = round(estimated_strike / strike_increment) * strike_increment
                
                optimal_strikes.append({
                    "target_delta": delta_target,
                    "estimated_strike": float(rounded_strike),
                    "distance_pct": float(abs(rounded_strike - current_price) / current_price * 100),
                    "recommendation_score": self._score_strike_option(delta_decimal, rounded_strike, current_price)
                })
            
            # Sort by recommendation score
            optimal_strikes.sort(key=lambda x: x["recommendation_score"], reverse=True)
            
            return {
                "success": True,
                "optimal_strikes": optimal_strikes,
                "best_strike": optimal_strikes[0] if optimal_strikes else None,
                "current_price": float(current_price),
                "expiry_date": expiry_date.isoformat(),
                "calculation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimal roll strikes: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "calculation_timestamp": datetime.now().isoformat()
            }
    
    def _score_strike_option(self, target_delta: Decimal, strike: Decimal, current_price: Decimal) -> float:
        """Score a strike option based on delta target optimality."""
        try:
            # Distance from optimal delta
            optimal_delta = self.target_delta_range["optimal"]
            delta_score = 1.0 - float(abs(target_delta - optimal_delta) / optimal_delta)
            
            # Distance from current price (prefer reasonable OTM)
            price_distance = abs(strike - current_price) / current_price
            distance_score = 1.0 - min(float(price_distance), 0.5) * 2  # Penalize too far OTM
            
            # Combined score
            combined_score = (delta_score * 0.7) + (distance_score * 0.3)
            
            return max(0.0, min(1.0, combined_score))
            
        except Exception as e:
            logger.error(f"Error scoring strike option: {str(e)}")
            return 0.5
    
    def get_delta_configuration(self) -> Dict[str, Any]:
        """Get current delta band configuration."""
        return {
            "target_delta_range": {
                "min": float(self.target_delta_range["min"]),
                "max": float(self.target_delta_range["max"]),
                "optimal": float(self.target_delta_range["optimal"])
            },
            "roll_triggers": {
                "roll_trigger_delta": float(self.roll_trigger_delta),
                "emergency_roll_delta": float(self.emergency_roll_delta)
            },
            "analysis_parameters": {
                "lookback_days": self.lookback_days,
                "delta_smoothing_factor": float(self.delta_smoothing_factor)
            }
        }

