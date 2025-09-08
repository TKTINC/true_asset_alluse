"""
Roll Cost Threshold - Constitution v1.3 Compliance

This module implements the 50% roll cost threshold rule:
"Do not roll if cost > 50% of original credit → escalate to L3"

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RollCostAnalysis:
    """Roll cost analysis result."""
    original_credit: Decimal
    roll_cost: Decimal
    cost_percentage: Decimal
    threshold_exceeded: bool
    recommendation: str
    escalation_required: bool


class RollCostThreshold:
    """Roll cost threshold validator per Constitution v1.3."""
    
    # Constitution v1.3 - Roll Economics Rule
    MAX_ROLL_COST_PCT = Decimal("0.50")  # 50% of original credit
    
    def __init__(self):
        """Initialize roll cost threshold validator."""
        pass
    
    def analyze_roll_cost(
        self, 
        original_credit: Decimal, 
        roll_debit: Decimal,
        position_context: Optional[Dict[str, Any]] = None
    ) -> RollCostAnalysis:
        """
        Analyze roll cost against the 50% threshold.
        
        Args:
            original_credit: Original credit received when opening position
            roll_debit: Cost (debit) to roll the position
            position_context: Additional position context
            
        Returns:
            RollCostAnalysis with recommendation
        """
        try:
            # Calculate cost percentage
            if original_credit <= 0:
                logger.error(f"Invalid original credit: {original_credit}")
                raise ValueError("Original credit must be positive")
            
            cost_percentage = roll_debit / original_credit
            threshold_exceeded = cost_percentage > self.MAX_ROLL_COST_PCT
            
            # Determine recommendation
            if threshold_exceeded:
                recommendation = "DO_NOT_ROLL_ESCALATE_L3"
                escalation_required = True
                logger.warning(
                    f"Roll cost {cost_percentage:.1%} exceeds {self.MAX_ROLL_COST_PCT:.1%} threshold - "
                    f"escalating to L3"
                )
            else:
                recommendation = "ROLL_APPROVED"
                escalation_required = False
                logger.info(
                    f"Roll cost {cost_percentage:.1%} within {self.MAX_ROLL_COST_PCT:.1%} threshold - "
                    f"roll approved"
                )
            
            return RollCostAnalysis(
                original_credit=original_credit,
                roll_cost=roll_debit,
                cost_percentage=cost_percentage,
                threshold_exceeded=threshold_exceeded,
                recommendation=recommendation,
                escalation_required=escalation_required
            )
            
        except Exception as e:
            logger.error(f"Error analyzing roll cost: {e}")
            raise
    
    def validate_roll_decision(
        self,
        position_id: str,
        original_credit: Decimal,
        proposed_roll_cost: Decimal,
        current_protocol_level: int = 0
    ) -> Dict[str, Any]:
        """
        Validate a roll decision against Constitution rules.
        
        Args:
            position_id: Position identifier
            original_credit: Original credit received
            proposed_roll_cost: Proposed cost to roll
            current_protocol_level: Current protocol level
            
        Returns:
            Validation result with action recommendations
        """
        try:
            analysis = self.analyze_roll_cost(original_credit, proposed_roll_cost)
            
            violations = []
            actions = []
            
            if analysis.threshold_exceeded:
                violations.append(
                    f"Roll cost {analysis.cost_percentage:.1%} exceeds "
                    f"{self.MAX_ROLL_COST_PCT:.1%} threshold"
                )
                actions.extend([
                    "Block roll execution",
                    "Escalate to Protocol Level 3",
                    "Initiate stop-loss procedures",
                    "Consider position closure"
                ])
            else:
                actions.append("Approve roll execution")
            
            return {
                "valid": not analysis.threshold_exceeded,
                "violations": violations,
                "actions": actions,
                "analysis": {
                    "position_id": position_id,
                    "original_credit": float(analysis.original_credit),
                    "roll_cost": float(analysis.roll_cost),
                    "cost_percentage": float(analysis.cost_percentage),
                    "threshold": float(self.MAX_ROLL_COST_PCT),
                    "recommendation": analysis.recommendation,
                    "escalation_required": analysis.escalation_required
                },
                "rule": "Constitution v1.3 - Roll Economics: Do not roll if cost > 50% of original credit"
            }
            
        except Exception as e:
            logger.error(f"Error validating roll decision for {position_id}: {e}")
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "actions": ["Manual review required"],
                "analysis": None,
                "rule": "Constitution v1.3 - Roll Economics"
            }
    
    def get_roll_cost_metrics(self, positions: list) -> Dict[str, Any]:
        """
        Get roll cost metrics across multiple positions.
        
        Args:
            positions: List of position dicts with roll cost data
            
        Returns:
            Aggregate roll cost metrics
        """
        if not positions:
            return {
                "total_positions": 0,
                "rolls_analyzed": 0,
                "rolls_approved": 0,
                "rolls_blocked": 0,
                "avg_cost_percentage": 0.0,
                "max_cost_percentage": 0.0,
                "threshold_violations": 0
            }
        
        rolls_analyzed = 0
        rolls_approved = 0
        rolls_blocked = 0
        cost_percentages = []
        threshold_violations = 0
        
        for position in positions:
            if "original_credit" in position and "roll_cost" in position:
                try:
                    analysis = self.analyze_roll_cost(
                        Decimal(str(position["original_credit"])),
                        Decimal(str(position["roll_cost"]))
                    )
                    
                    rolls_analyzed += 1
                    cost_percentages.append(float(analysis.cost_percentage))
                    
                    if analysis.threshold_exceeded:
                        rolls_blocked += 1
                        threshold_violations += 1
                    else:
                        rolls_approved += 1
                        
                except Exception as e:
                    logger.warning(f"Error analyzing position {position.get('id', 'unknown')}: {e}")
                    continue
        
        return {
            "total_positions": len(positions),
            "rolls_analyzed": rolls_analyzed,
            "rolls_approved": rolls_approved,
            "rolls_blocked": rolls_blocked,
            "avg_cost_percentage": sum(cost_percentages) / len(cost_percentages) if cost_percentages else 0.0,
            "max_cost_percentage": max(cost_percentages) if cost_percentages else 0.0,
            "threshold_violations": threshold_violations,
            "threshold": float(self.MAX_ROLL_COST_PCT)
        }


# Global roll cost threshold validator
roll_cost_threshold = RollCostThreshold()

