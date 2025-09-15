"""
Roll Economics Calculator

This module implements the economic analysis for roll decisions,
calculating the cost-benefit of rolling positions vs. closing them.
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
import logging
import math

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class RollEconomicsCalculator:
    """
    Calculator for roll economics and cost-benefit analysis.
    
    Analyzes the financial implications of rolling options positions
    vs. closing them, considering transaction costs, time decay, and
    market conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize roll economics calculator.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        
        # Transaction cost configuration
        self.commission_per_contract = Decimal(str(self.config.get("commission_per_contract", 0.65)))
        self.bid_ask_spread_cost = Decimal(str(self.config.get("bid_ask_spread_cost", 0.5)))  # Half spread
        self.regulatory_fees = Decimal(str(self.config.get("regulatory_fees", 0.02)))
        
        # Roll decision thresholds
        self.min_credit_threshold = Decimal(str(self.config.get("min_credit_threshold", 0.10)))  # $0.10
        self.max_debit_threshold = Decimal(str(self.config.get("max_debit_threshold", 0.50)))   # $0.50
        self.time_decay_factor = Decimal(str(self.config.get("time_decay_factor", 0.8)))
        
        logger.info("Roll Economics Calculator initialized")
    
    def calculate_roll_economics(self, 
                               current_position: Dict[str, Any],
                               target_position: Dict[str, Any],
                               market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive roll economics.
        
        Args:
            current_position: Current position details
            target_position: Target roll position details
            market_data: Current market data
            
        Returns:
            Roll economics analysis
        """
        try:
            # Extract position details
            current_strike = Decimal(str(current_position["strike_price"]))
            current_expiry = current_position["expiry_date"]
            current_premium = Decimal(str(current_position.get("current_premium", 0)))
            current_quantity = int(current_position["quantity"])
            
            target_strike = Decimal(str(target_position["strike_price"]))
            target_expiry = target_position["expiry_date"]
            target_premium = Decimal(str(target_position.get("premium", 0)))
            
            # Calculate transaction costs
            transaction_costs = self._calculate_transaction_costs(current_quantity)
            
            # Calculate roll credit/debit
            roll_credit_debit = self._calculate_roll_credit_debit(
                current_premium, target_premium, current_quantity
            )
            
            # Calculate time value analysis
            time_analysis = self._calculate_time_value_analysis(
                current_expiry, target_expiry, current_premium, target_premium
            )
            
            # Calculate delta impact
            delta_impact = self._calculate_delta_impact(
                current_position, target_position, market_data
            )
            
            # Calculate probability analysis
            probability_analysis = self._calculate_probability_analysis(
                current_position, target_position, market_data
            )
            
            # Calculate net economics
            net_economics = self._calculate_net_economics(
                roll_credit_debit, transaction_costs, time_analysis
            )
            
            # Make roll recommendation
            recommendation = self._make_roll_recommendation(
                net_economics, delta_impact, probability_analysis, market_data
            )
            
            return {
                "success": True,
                "current_position": current_position,
                "target_position": target_position,
                "roll_credit_debit": {
                    "per_contract": float(roll_credit_debit["per_contract"]),
                    "total": float(roll_credit_debit["total"]),
                    "type": roll_credit_debit["type"]
                },
                "transaction_costs": {
                    "per_contract": float(transaction_costs["per_contract"]),
                    "total": float(transaction_costs["total"]),
                    "breakdown": {k: float(v) for k, v in transaction_costs["breakdown"].items()}
                },
                "time_analysis": time_analysis,
                "delta_impact": delta_impact,
                "probability_analysis": probability_analysis,
                "net_economics": {
                    "net_credit_debit": float(net_economics["net_credit_debit"]),
                    "break_even_move": float(net_economics["break_even_move"]),
                    "roi_estimate": float(net_economics["roi_estimate"])
                },
                "recommendation": recommendation,
                "calculation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating roll economics: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "calculation_timestamp": datetime.now().isoformat()
            }
    
    def _calculate_transaction_costs(self, quantity: int) -> Dict[str, Any]:
        """Calculate total transaction costs for the roll."""
        try:
            # Costs for closing current position and opening new position
            total_contracts = quantity * 2  # Close + Open
            
            commission_cost = self.commission_per_contract * total_contracts
            spread_cost = self.bid_ask_spread_cost * total_contracts
            regulatory_cost = self.regulatory_fees * total_contracts
            
            total_cost = commission_cost + spread_cost + regulatory_cost
            per_contract_cost = total_cost / quantity
            
            return {
                "per_contract": per_contract_cost,
                "total": total_cost,
                "breakdown": {
                    "commission": commission_cost,
                    "bid_ask_spread": spread_cost,
                    "regulatory_fees": regulatory_cost
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating transaction costs: {str(e)}")
            return {
                "per_contract": Decimal("0"),
                "total": Decimal("0"),
                "breakdown": {}
            }
    
    def _calculate_roll_credit_debit(self, 
                                   current_premium: Decimal,
                                   target_premium: Decimal,
                                   quantity: int) -> Dict[str, Any]:
        """Calculate roll credit or debit."""
        try:
            # Credit = money received, Debit = money paid
            # For rolling: Credit if target_premium > current_premium (we receive net credit)
            per_contract = target_premium - current_premium
            total = per_contract * quantity
            
            roll_type = "credit" if per_contract > 0 else "debit" if per_contract < 0 else "even"
            
            return {
                "per_contract": per_contract,
                "total": total,
                "type": roll_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating roll credit/debit: {str(e)}")
            return {
                "per_contract": Decimal("0"),
                "total": Decimal("0"),
                "type": "unknown"
            }
    
    def _calculate_time_value_analysis(self, 
                                     current_expiry: date,
                                     target_expiry: date,
                                     current_premium: Decimal,
                                     target_premium: Decimal) -> Dict[str, Any]:
        """Calculate time value and decay analysis."""
        try:
            today = date.today()
            
            # Days to expiration
            current_dte = (current_expiry - today).days
            target_dte = (target_expiry - today).days
            additional_dte = target_dte - current_dte
            
            # Time value estimates (simplified)
            current_time_value = current_premium * self.time_decay_factor
            target_time_value = target_premium * self.time_decay_factor
            
            # Daily theta estimates (simplified)
            current_theta = current_time_value / max(current_dte, 1) if current_dte > 0 else Decimal("0")
            target_theta = target_time_value / max(target_dte, 1) if target_dte > 0 else Decimal("0")
            
            return {
                "current_dte": current_dte,
                "target_dte": target_dte,
                "additional_dte": additional_dte,
                "current_time_value": float(current_time_value),
                "target_time_value": float(target_time_value),
                "current_theta_estimate": float(current_theta),
                "target_theta_estimate": float(target_theta),
                "time_value_gained": float(target_time_value - current_time_value)
            }
            
        except Exception as e:
            logger.error(f"Error calculating time value analysis: {str(e)}")
            return {}
    
    def _calculate_delta_impact(self, 
                              current_position: Dict[str, Any],
                              target_position: Dict[str, Any],
                              market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate delta impact of the roll."""
        try:
            current_delta = Decimal(str(current_position.get("delta", 0)))
            target_delta = Decimal(str(target_position.get("delta", 0)))
            
            delta_change = target_delta - current_delta
            
            # Estimate dollar impact per $1 move
            quantity = int(current_position["quantity"])
            delta_dollar_impact = delta_change * quantity * 100  # Options are per 100 shares
            
            # Risk assessment
            risk_level = "low"
            if abs(delta_change) > Decimal("0.10"):
                risk_level = "high"
            elif abs(delta_change) > Decimal("0.05"):
                risk_level = "medium"
            
            return {
                "current_delta": float(current_delta),
                "target_delta": float(target_delta),
                "delta_change": float(delta_change),
                "dollar_impact_per_move": float(delta_dollar_impact),
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Error calculating delta impact: {str(e)}")
            return {}
    
    def _calculate_probability_analysis(self, 
                                      current_position: Dict[str, Any],
                                      target_position: Dict[str, Any],
                                      market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate probability analysis for roll success."""
        try:
            current_strike = Decimal(str(current_position["strike_price"]))
            target_strike = Decimal(str(target_position["strike_price"]))
            current_price = Decimal(str(market_data.get("current_price", 0)))
            
            # Distance from current price
            current_distance = abs(current_price - current_strike) / current_price
            target_distance = abs(current_price - target_strike) / current_price
            
            # Simplified probability estimates (would use Black-Scholes in production)
            # These are rough estimates based on distance from current price
            current_prob_otm = min(float(current_distance * 2), 0.95)
            target_prob_otm = min(float(target_distance * 2), 0.95)
            
            # Success probability (staying OTM)
            success_probability = target_prob_otm
            
            return {
                "current_distance_pct": float(current_distance * 100),
                "target_distance_pct": float(target_distance * 100),
                "current_prob_otm": current_prob_otm,
                "target_prob_otm": target_prob_otm,
                "success_probability": success_probability,
                "risk_assessment": "low" if success_probability > 0.7 else "medium" if success_probability > 0.5 else "high"
            }
            
        except Exception as e:
            logger.error(f"Error calculating probability analysis: {str(e)}")
            return {}
    
    def _calculate_net_economics(self, 
                               roll_credit_debit: Dict[str, Any],
                               transaction_costs: Dict[str, Any],
                               time_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate net economics of the roll."""
        try:
            credit_debit = roll_credit_debit["total"]
            costs = transaction_costs["total"]
            
            # Net credit/debit after costs
            net_credit_debit = credit_debit - costs
            
            # Break-even calculation (simplified)
            # This would be more complex in production with proper Greeks
            break_even_move = abs(net_credit_debit) / 100  # Rough estimate
            
            # ROI estimate based on margin requirements (simplified)
            # In production, this would use actual margin requirements
            estimated_margin = Decimal("1000")  # Placeholder
            roi_estimate = (net_credit_debit / estimated_margin) * 100 if estimated_margin > 0 else Decimal("0")
            
            return {
                "net_credit_debit": net_credit_debit,
                "break_even_move": break_even_move,
                "roi_estimate": roi_estimate
            }
            
        except Exception as e:
            logger.error(f"Error calculating net economics: {str(e)}")
            return {
                "net_credit_debit": Decimal("0"),
                "break_even_move": Decimal("0"),
                "roi_estimate": Decimal("0")
            }
    
    def _make_roll_recommendation(self, 
                                net_economics: Dict[str, Any],
                                delta_impact: Dict[str, Any],
                                probability_analysis: Dict[str, Any],
                                market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make roll recommendation based on analysis."""
        try:
            net_credit_debit = net_economics["net_credit_debit"]
            success_probability = probability_analysis.get("success_probability", 0.5)
            delta_risk = delta_impact.get("risk_level", "medium")
            
            # Decision logic
            recommendation = "hold"  # Default
            confidence = 0.5
            reasons = []
            
            # Economic analysis
            if net_credit_debit > self.min_credit_threshold:
                recommendation = "roll"
                confidence += 0.2
                reasons.append(f"Favorable economics: ${float(net_credit_debit):.2f} net credit")
            elif net_credit_debit < -self.max_debit_threshold:
                recommendation = "close"
                confidence += 0.2
                reasons.append(f"Unfavorable economics: ${float(abs(net_credit_debit)):.2f} net debit")
            
            # Probability analysis
            if success_probability > 0.7:
                if recommendation != "close":
                    recommendation = "roll"
                confidence += 0.2
                reasons.append(f"High success probability: {success_probability:.1%}")
            elif success_probability < 0.4:
                recommendation = "close"
                confidence += 0.2
                reasons.append(f"Low success probability: {success_probability:.1%}")
            
            # Delta risk analysis
            if delta_risk == "low":
                confidence += 0.1
                reasons.append("Low delta risk")
            elif delta_risk == "high":
                confidence -= 0.1
                reasons.append("High delta risk")
            
            # Market conditions (simplified)
            volatility = market_data.get("implied_volatility", 0.2)
            if volatility > 0.3:
                confidence -= 0.1
                reasons.append("High volatility environment")
            
            confidence = max(0.1, min(0.9, confidence))
            
            return {
                "action": recommendation,
                "confidence": confidence,
                "reasons": reasons,
                "economic_score": float(net_credit_debit),
                "probability_score": success_probability,
                "overall_score": confidence
            }
            
        except Exception as e:
            logger.error(f"Error making roll recommendation: {str(e)}")
            return {
                "action": "hold",
                "confidence": 0.5,
                "reasons": ["Error in analysis"],
                "economic_score": 0.0,
                "probability_score": 0.5,
                "overall_score": 0.5
            }
    
    def calculate_roll_scenarios(self, 
                               current_position: Dict[str, Any],
                               target_strikes: List[Decimal],
                               target_expiry: date,
                               market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate roll economics for multiple target strikes.
        
        Args:
            current_position: Current position details
            target_strikes: List of potential target strikes
            target_expiry: Target expiration date
            market_data: Current market data
            
        Returns:
            Analysis of all roll scenarios
        """
        try:
            scenarios = []
            
            for strike in target_strikes:
                # Create target position for this strike
                target_position = {
                    "strike_price": float(strike),
                    "expiry_date": target_expiry,
                    "premium": market_data.get(f"premium_{strike}", 0),
                    "delta": market_data.get(f"delta_{strike}", 0)
                }
                
                # Calculate economics for this scenario
                scenario_result = self.calculate_roll_economics(
                    current_position, target_position, market_data
                )
                
                if scenario_result.get("success"):
                    scenarios.append({
                        "target_strike": float(strike),
                        "economics": scenario_result,
                        "score": scenario_result["recommendation"]["overall_score"]
                    })
            
            # Sort by overall score
            scenarios.sort(key=lambda x: x["score"], reverse=True)
            
            # Find best scenario
            best_scenario = scenarios[0] if scenarios else None
            
            return {
                "success": True,
                "scenarios": scenarios,
                "best_scenario": best_scenario,
                "total_scenarios": len(scenarios),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating roll scenarios: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def get_roll_thresholds(self) -> Dict[str, Any]:
        """Get current roll decision thresholds."""
        return {
            "min_credit_threshold": float(self.min_credit_threshold),
            "max_debit_threshold": float(self.max_debit_threshold),
            "time_decay_factor": float(self.time_decay_factor),
            "transaction_costs": {
                "commission_per_contract": float(self.commission_per_contract),
                "bid_ask_spread_cost": float(self.bid_ask_spread_cost),
                "regulatory_fees": float(self.regulatory_fees)
            }
        }

