"""
Hedge Deployment - Constitution v1.3 Compliance

This module implements the L2 hedge deployment rules:
"At L2, place 1% SPX puts + 0.5% VIX calls of sleeve equity; 
budget = greater of 5–10% of quarterly gains OR 1% of sleeve equity"

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class HedgeAllocation:
    """Hedge allocation calculation result."""
    spx_puts_allocation: Decimal  # 1% of sleeve equity
    vix_calls_allocation: Decimal  # 0.5% of sleeve equity
    total_hedge_budget: Decimal
    budget_source: str  # "quarterly_gains" or "sleeve_equity"
    spx_puts_percentage: Decimal  # Percentage of sleeve equity
    vix_calls_percentage: Decimal  # Percentage of sleeve equity


@dataclass
class HedgeDeploymentPlan:
    """Hedge deployment execution plan."""
    allocation: HedgeAllocation
    spx_puts_details: Dict[str, Any]
    vix_calls_details: Dict[str, Any]
    execution_priority: str
    risk_budget_remaining: Decimal
    deployment_approved: bool


class HedgeDeployment:
    """Hedge deployment manager per Constitution v1.3."""
    
    # Constitution v1.3 - Hedge Sizing Rules
    SPX_PUTS_PCT = Decimal("0.01")    # 1% of sleeve equity
    VIX_CALLS_PCT = Decimal("0.005")  # 0.5% of sleeve equity
    
    # Budget calculation rules
    MIN_QUARTERLY_GAINS_PCT = Decimal("0.05")  # 5% of quarterly gains
    MAX_QUARTERLY_GAINS_PCT = Decimal("0.10")  # 10% of quarterly gains
    FALLBACK_SLEEVE_EQUITY_PCT = Decimal("0.01")  # 1% of sleeve equity
    
    # Hedge parameters
    SPX_PUTS_OTM_PCT = Decimal("0.10")  # 10% OTM
    VIX_CALLS_STRIKE_BUFFER = Decimal("5.0")  # +$5 above current VIX
    
    def __init__(self):
        """Initialize hedge deployment manager."""
        pass
    
    def calculate_hedge_allocation(
        self,
        sleeve_equity: Decimal,
        quarterly_gains: Decimal,
        current_vix: Decimal,
        spx_current_price: Decimal
    ) -> HedgeAllocation:
        """
        Calculate hedge allocation per Constitution rules.
        
        Args:
            sleeve_equity: Current sleeve equity value
            quarterly_gains: Quarterly gains for budget calculation
            current_vix: Current VIX level
            spx_current_price: Current SPX price
            
        Returns:
            HedgeAllocation with calculated amounts
        """
        try:
            # Calculate hedge allocations (fixed percentages)
            spx_puts_allocation = sleeve_equity * self.SPX_PUTS_PCT
            vix_calls_allocation = sleeve_equity * self.VIX_CALLS_PCT
            
            # Calculate budget options
            quarterly_gains_budget_min = quarterly_gains * self.MIN_QUARTERLY_GAINS_PCT
            quarterly_gains_budget_max = quarterly_gains * self.MAX_QUARTERLY_GAINS_PCT
            sleeve_equity_budget = sleeve_equity * self.FALLBACK_SLEEVE_EQUITY_PCT
            
            # Use greater of quarterly gains range OR sleeve equity fallback
            if quarterly_gains > 0:
                # Use mid-point of quarterly gains range
                quarterly_gains_budget = (quarterly_gains_budget_min + quarterly_gains_budget_max) / 2
                if quarterly_gains_budget >= sleeve_equity_budget:
                    total_hedge_budget = quarterly_gains_budget
                    budget_source = "quarterly_gains"
                else:
                    total_hedge_budget = sleeve_equity_budget
                    budget_source = "sleeve_equity"
            else:
                total_hedge_budget = sleeve_equity_budget
                budget_source = "sleeve_equity"
            
            logger.info(
                f"Hedge allocation calculated: SPX puts ${spx_puts_allocation:,.2f}, "
                f"VIX calls ${vix_calls_allocation:,.2f}, "
                f"budget ${total_hedge_budget:,.2f} from {budget_source}"
            )
            
            return HedgeAllocation(
                spx_puts_allocation=spx_puts_allocation,
                vix_calls_allocation=vix_calls_allocation,
                total_hedge_budget=total_hedge_budget,
                budget_source=budget_source,
                spx_puts_percentage=self.SPX_PUTS_PCT,
                vix_calls_percentage=self.VIX_CALLS_PCT
            )
            
        except Exception as e:
            logger.error(f"Error calculating hedge allocation: {e}")
            raise
    
    def create_deployment_plan(
        self,
        sleeve_equity: Decimal,
        quarterly_gains: Decimal,
        current_vix: Decimal,
        spx_current_price: Decimal,
        protocol_level: int = 2
    ) -> HedgeDeploymentPlan:
        """
        Create hedge deployment plan for L2 escalation.
        
        Args:
            sleeve_equity: Current sleeve equity
            quarterly_gains: Quarterly gains
            current_vix: Current VIX level
            spx_current_price: Current SPX price
            protocol_level: Current protocol level
            
        Returns:
            HedgeDeploymentPlan with execution details
        """
        try:
            # Calculate allocation
            allocation = self.calculate_hedge_allocation(
                sleeve_equity, quarterly_gains, current_vix, spx_current_price
            )
            
            # Calculate strike prices
            spx_put_strike = spx_current_price * (Decimal("1.0") - self.SPX_PUTS_OTM_PCT)
            vix_call_strike = current_vix + self.VIX_CALLS_STRIKE_BUFFER
            
            # SPX puts details
            spx_puts_details = {
                "symbol": "SPX",
                "option_type": "put",
                "strike": float(spx_put_strike),
                "allocation": float(allocation.spx_puts_allocation),
                "percentage_of_sleeve": float(self.SPX_PUTS_PCT),
                "otm_percentage": float(self.SPX_PUTS_OTM_PCT),
                "current_underlying": float(spx_current_price)
            }
            
            # VIX calls details
            vix_calls_details = {
                "symbol": "VIX",
                "option_type": "call",
                "strike": float(vix_call_strike),
                "allocation": float(allocation.vix_calls_allocation),
                "percentage_of_sleeve": float(self.VIX_CALLS_PCT),
                "strike_buffer": float(self.VIX_CALLS_STRIKE_BUFFER),
                "current_underlying": float(current_vix)
            }
            
            # Determine execution priority
            if protocol_level >= 2:
                execution_priority = "IMMEDIATE"
                deployment_approved = True
            else:
                execution_priority = "DEFERRED"
                deployment_approved = False
            
            # Calculate remaining risk budget
            total_hedge_cost = allocation.spx_puts_allocation + allocation.vix_calls_allocation
            risk_budget_remaining = allocation.total_hedge_budget - total_hedge_cost
            
            logger.info(
                f"Hedge deployment plan created: Priority {execution_priority}, "
                f"Total cost ${total_hedge_cost:,.2f}, "
                f"Budget remaining ${risk_budget_remaining:,.2f}"
            )
            
            return HedgeDeploymentPlan(
                allocation=allocation,
                spx_puts_details=spx_puts_details,
                vix_calls_details=vix_calls_details,
                execution_priority=execution_priority,
                risk_budget_remaining=risk_budget_remaining,
                deployment_approved=deployment_approved
            )
            
        except Exception as e:
            logger.error(f"Error creating hedge deployment plan: {e}")
            raise
    
    def validate_hedge_deployment(
        self,
        deployment_plan: HedgeDeploymentPlan,
        current_protocol_level: int,
        available_capital: Decimal
    ) -> Dict[str, Any]:
        """
        Validate hedge deployment against Constitution rules.
        
        Args:
            deployment_plan: Proposed deployment plan
            current_protocol_level: Current protocol level
            available_capital: Available capital for hedging
            
        Returns:
            Validation result
        """
        violations = []
        actions = []
        
        try:
            # Validate protocol level requirement
            if current_protocol_level < 2:
                violations.append(f"Hedge deployment requires Protocol Level 2+, current: {current_protocol_level}")
            
            # Validate budget availability
            total_hedge_cost = (
                deployment_plan.allocation.spx_puts_allocation + 
                deployment_plan.allocation.vix_calls_allocation
            )
            
            if total_hedge_cost > available_capital:
                violations.append(
                    f"Insufficient capital: need ${total_hedge_cost:,.2f}, "
                    f"available ${available_capital:,.2f}"
                )
            
            # Validate allocation percentages
            if deployment_plan.allocation.spx_puts_percentage != self.SPX_PUTS_PCT:
                violations.append(
                    f"SPX puts allocation {deployment_plan.allocation.spx_puts_percentage:.1%} "
                    f"!= required {self.SPX_PUTS_PCT:.1%}"
                )
            
            if deployment_plan.allocation.vix_calls_percentage != self.VIX_CALLS_PCT:
                violations.append(
                    f"VIX calls allocation {deployment_plan.allocation.vix_calls_percentage:.1%} "
                    f"!= required {self.VIX_CALLS_PCT:.1%}"
                )
            
            # Determine actions
            if not violations:
                actions.extend([
                    "Deploy SPX puts hedge",
                    "Deploy VIX calls hedge",
                    "Monitor hedge performance",
                    "Update risk metrics"
                ])
            else:
                actions.extend([
                    "Block hedge deployment",
                    "Review capital allocation",
                    "Manual intervention required"
                ])
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "actions": actions,
                "deployment_plan": {
                    "spx_puts_allocation": float(deployment_plan.allocation.spx_puts_allocation),
                    "vix_calls_allocation": float(deployment_plan.allocation.vix_calls_allocation),
                    "total_budget": float(deployment_plan.allocation.total_hedge_budget),
                    "budget_source": deployment_plan.allocation.budget_source,
                    "execution_priority": deployment_plan.execution_priority,
                    "approved": deployment_plan.deployment_approved
                },
                "rule": "Constitution v1.3 - L2 Hedge Deployment: 1% SPX puts + 0.5% VIX calls"
            }
            
        except Exception as e:
            logger.error(f"Error validating hedge deployment: {e}")
            return {
                "valid": False,
                "violations": [f"Validation error: {str(e)}"],
                "actions": ["Manual review required"],
                "deployment_plan": None,
                "rule": "Constitution v1.3 - L2 Hedge Deployment"
            }


# Global hedge deployment manager
hedge_deployment = HedgeDeployment()

