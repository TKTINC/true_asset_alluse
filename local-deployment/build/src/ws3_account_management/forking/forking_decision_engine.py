"""
Forking Decision Engine

This module implements the intelligent decision engine that determines
when and how to fork accounts based on Constitution v1.3 rules and
current market conditions.
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict

from src.ws3_account_management.accounts import AccountType, AccountState, Account
from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws2_protocol_engine.escalation import ProtocolEscalationManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class ForkingTrigger(Enum):
    """Types of forking triggers."""
    THRESHOLD_BREACH = "threshold_breach"
    PERFORMANCE_TARGET = "performance_target"
    TIME_BASED = "time_based"
    MANUAL_REQUEST = "manual_request"
    RISK_MANAGEMENT = "risk_management"


class ForkingUrgency(Enum):
    """Forking urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ForkingOpportunity:
    """Forking opportunity assessment."""
    opportunity_id: str
    account_id: str
    current_account_type: AccountType
    target_account_type: AccountType
    trigger_type: ForkingTrigger
    urgency: ForkingUrgency
    current_value: Decimal
    threshold_value: Decimal
    excess_capital: Decimal
    recommended_fork_amount: Decimal
    confidence_score: Decimal
    risk_assessment: Dict[str, Any]
    market_conditions: Dict[str, Any]
    timing_recommendation: str
    estimated_completion_time: timedelta
    potential_benefits: List[str]
    potential_risks: List[str]
    prerequisites: List[str]
    timestamp: datetime


@dataclass
class ForkingDecision:
    """Final forking decision."""
    decision_id: str
    opportunity_id: str
    account_id: str
    decision: str  # "approve", "defer", "reject"
    fork_amount: Decimal
    target_account_type: AccountType
    reasoning: str
    conditions: List[str]
    timeline: Dict[str, datetime]
    risk_mitigation: List[str]
    approval_required: bool
    decision_timestamp: datetime


class ForkingDecisionEngine:
    """
    Intelligent forking decision engine.
    
    Analyzes account performance, market conditions, and risk factors
    to make optimal forking decisions that maximize system performance
    while maintaining safety and compliance.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 escalation_manager: Optional[ProtocolEscalationManager] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize forking decision engine.
        
        Args:
            audit_manager: Audit trail manager
            escalation_manager: Optional protocol escalation manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.escalation_manager = escalation_manager
        self.config = config or {}
        
        # Decision parameters
        self.min_confidence_threshold = Decimal(str(self.config.get("min_confidence_threshold", 0.7)))
        self.max_concurrent_forks = self.config.get("max_concurrent_forks", 5)
        self.fork_cooldown_hours = self.config.get("fork_cooldown_hours", 24)
        
        # Forking thresholds (Constitution v1.3)
        self.forking_thresholds = {
            AccountType.GEN_ACC: Decimal("100000"),  # $100K Gen-Acc → Rev-Acc
            AccountType.REV_ACC: Decimal("500000"),  # $500K Rev-Acc → Com-Acc
            AccountType.COM_ACC: None                # No further forking
        }
        
        # Risk assessment parameters
        self.risk_factors = {
            "market_volatility": 0.3,
            "account_performance": 0.4,
            "system_load": 0.2,
            "timing_factors": 0.1
        }
        
        # Decision history
        self.forking_opportunities = {}  # opportunity_id -> ForkingOpportunity
        self.forking_decisions = {}      # decision_id -> ForkingDecision
        self.active_forks = set()        # Set of account_ids currently forking
        
        logger.info("Forking Decision Engine initialized")
    
    def assess_forking_opportunity(self, 
                                 account: Account,
                                 market_data: Optional[Dict[str, Any]] = None,
                                 force_assessment: bool = False) -> Dict[str, Any]:
        """
        Assess forking opportunity for an account.
        
        Args:
            account: Account to assess
            market_data: Optional market data
            force_assessment: Force assessment even if recently assessed
            
        Returns:
            Forking opportunity assessment
        """
        try:
            # Check if account can fork
            if account.account_type == AccountType.COM_ACC:
                return {
                    "has_opportunity": False,
                    "reason": "Commercial accounts cannot fork further"
                }
            
            threshold = self.forking_thresholds.get(account.account_type)
            if not threshold:
                return {
                    "has_opportunity": False,
                    "reason": f"No forking threshold defined for {account.account_type.value}"
                }
            
            # Check threshold breach
            if account.current_value < threshold:
                return {
                    "has_opportunity": False,
                    "reason": f"Account value ${float(account.current_value):,.2f} below threshold ${float(threshold):,.2f}",
                    "progress_to_threshold": float(account.current_value / threshold * 100)
                }
            
            # Check if account is already forking
            if account.account_id in self.active_forks:
                return {
                    "has_opportunity": False,
                    "reason": "Account is already in forking process"
                }
            
            # Check account state
            if account.account_state not in [AccountState.ACTIVE, AccountState.SAFE]:
                return {
                    "has_opportunity": False,
                    "reason": f"Account state {account.account_state.value} not suitable for forking"
                }
            
            # Calculate forking parameters
            excess_capital = account.current_value - threshold
            target_account_type = self._get_target_account_type(account.account_type)
            
            # Assess market conditions
            market_assessment = self._assess_market_conditions(market_data)
            
            # Calculate risk assessment
            risk_assessment = self._assess_forking_risks(account, market_assessment)
            
            # Determine urgency
            urgency = self._calculate_forking_urgency(account, excess_capital, risk_assessment)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(account, risk_assessment, market_assessment)
            
            # Determine recommended fork amount
            recommended_amount = self._calculate_recommended_fork_amount(account, excess_capital, risk_assessment)
            
            # Create forking opportunity
            opportunity = ForkingOpportunity(
                opportunity_id=f"fork_{account.account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                account_id=account.account_id,
                current_account_type=account.account_type,
                target_account_type=target_account_type,
                trigger_type=ForkingTrigger.THRESHOLD_BREACH,
                urgency=urgency,
                current_value=account.current_value,
                threshold_value=threshold,
                excess_capital=excess_capital,
                recommended_fork_amount=recommended_amount,
                confidence_score=confidence_score,
                risk_assessment=risk_assessment,
                market_conditions=market_assessment,
                timing_recommendation=self._get_timing_recommendation(market_assessment, risk_assessment),
                estimated_completion_time=timedelta(hours=2),  # Estimated fork completion time
                potential_benefits=self._identify_forking_benefits(account, target_account_type),
                potential_risks=self._identify_forking_risks(account, risk_assessment),
                prerequisites=self._identify_forking_prerequisites(account),
                timestamp=datetime.now()
            )
            
            # Store opportunity
            self.forking_opportunities[opportunity.opportunity_id] = opportunity
            
            return {
                "has_opportunity": True,
                "opportunity": asdict(opportunity),
                "recommendation": "proceed" if confidence_score >= self.min_confidence_threshold else "defer",
                "assessment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing forking opportunity for {account.account_id}: {str(e)}", exc_info=True)
            return {
                "has_opportunity": False,
                "reason": f"Assessment error: {str(e)}",
                "error": True
            }
    
    def make_forking_decision(self, 
                            opportunity_id: str,
                            override_conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make final forking decision based on opportunity assessment.
        
        Args:
            opportunity_id: Forking opportunity ID
            override_conditions: Optional override conditions
            
        Returns:
            Forking decision
        """
        try:
            opportunity = self.forking_opportunities.get(opportunity_id)
            if not opportunity:
                return {
                    "success": False,
                    "error": f"Forking opportunity {opportunity_id} not found"
                }
            
            # Check if opportunity is still valid
            if (datetime.now() - opportunity.timestamp).total_seconds() > 3600:  # 1 hour expiry
                return {
                    "success": False,
                    "error": "Forking opportunity has expired"
                }
            
            # Apply override conditions if provided
            if override_conditions:
                opportunity = self._apply_override_conditions(opportunity, override_conditions)
            
            # Make decision based on confidence and risk
            decision_logic = self._evaluate_decision_logic(opportunity)
            
            # Create forking decision
            decision = ForkingDecision(
                decision_id=f"decision_{opportunity.opportunity_id}",
                opportunity_id=opportunity_id,
                account_id=opportunity.account_id,
                decision=decision_logic["decision"],
                fork_amount=decision_logic["fork_amount"],
                target_account_type=opportunity.target_account_type,
                reasoning=decision_logic["reasoning"],
                conditions=decision_logic["conditions"],
                timeline=decision_logic["timeline"],
                risk_mitigation=decision_logic["risk_mitigation"],
                approval_required=decision_logic["approval_required"],
                decision_timestamp=datetime.now()
            )
            
            # Store decision
            self.forking_decisions[decision.decision_id] = decision
            
            # Log decision
            self.audit_manager.log_system_event(
                event_type="forking_decision",
                event_data=asdict(decision),
                severity="info"
            )
            
            logger.info(f"Forking decision made for {opportunity.account_id}: {decision.decision}")
            
            return {
                "success": True,
                "decision": asdict(decision),
                "next_steps": self._get_next_steps(decision),
                "decision_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making forking decision for {opportunity_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "opportunity_id": opportunity_id
            }
    
    def _get_target_account_type(self, current_type: AccountType) -> AccountType:
        """Get target account type for forking."""
        type_progression = {
            AccountType.GEN_ACC: AccountType.REV_ACC,
            AccountType.REV_ACC: AccountType.COM_ACC
        }
        return type_progression.get(current_type, current_type)
    
    def _assess_market_conditions(self, market_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess current market conditions for forking timing."""
        # Default market assessment (would integrate with real market data)
        default_assessment = {
            "volatility_level": "medium",
            "trend_direction": "neutral",
            "liquidity_conditions": "good",
            "market_stress_level": 0.3,
            "optimal_timing_score": 0.7,
            "recommended_delay_hours": 0
        }
        
        if not market_data:
            return default_assessment
        
        # Process market data (simplified implementation)
        try:
            volatility = market_data.get("volatility", 0.2)
            volume = market_data.get("volume", 1.0)
            trend = market_data.get("trend", 0.0)
            
            # Calculate market stress
            stress_level = min(1.0, volatility * 2)
            
            # Determine optimal timing
            timing_score = max(0.1, 1.0 - stress_level)
            
            return {
                "volatility_level": "high" if volatility > 0.3 else "medium" if volatility > 0.15 else "low",
                "trend_direction": "bullish" if trend > 0.1 else "bearish" if trend < -0.1 else "neutral",
                "liquidity_conditions": "good" if volume > 0.8 else "fair" if volume > 0.5 else "poor",
                "market_stress_level": stress_level,
                "optimal_timing_score": timing_score,
                "recommended_delay_hours": max(0, int((1 - timing_score) * 24))
            }
            
        except Exception as e:
            logger.warning(f"Error processing market data: {str(e)}")
            return default_assessment
    
    def _assess_forking_risks(self, account: Account, market_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks associated with forking."""
        try:
            risks = {
                "market_risk": market_assessment["market_stress_level"],
                "liquidity_risk": 0.1 if market_assessment["liquidity_conditions"] == "good" else 0.3,
                "operational_risk": 0.05,  # Base operational risk
                "timing_risk": 1.0 - market_assessment["optimal_timing_score"],
                "account_specific_risk": 0.1  # Base account risk
            }
            
            # Adjust for account performance (simplified)
            account_age_days = (datetime.now() - account.created_date).days
            if account_age_days < 30:
                risks["account_specific_risk"] += 0.2  # Higher risk for new accounts
            
            # Calculate overall risk score
            overall_risk = sum(
                risks[risk_type] * weight
                for risk_type, weight in self.risk_factors.items()
                if risk_type in risks
            )
            
            risks["overall_risk_score"] = min(1.0, overall_risk)
            risks["risk_level"] = "high" if overall_risk > 0.7 else "medium" if overall_risk > 0.4 else "low"
            
            return risks
            
        except Exception as e:
            logger.error(f"Error assessing forking risks: {str(e)}")
            return {
                "overall_risk_score": 0.5,
                "risk_level": "medium",
                "error": str(e)
            }
    
    def _calculate_forking_urgency(self, 
                                 account: Account,
                                 excess_capital: Decimal,
                                 risk_assessment: Dict[str, Any]) -> ForkingUrgency:
        """Calculate forking urgency level."""
        try:
            threshold = self.forking_thresholds[account.account_type]
            excess_ratio = float(excess_capital / threshold)
            risk_score = risk_assessment.get("overall_risk_score", 0.5)
            
            # Calculate urgency score
            urgency_score = excess_ratio * (1 - risk_score)
            
            if urgency_score > 0.5:
                return ForkingUrgency.HIGH
            elif urgency_score > 0.3:
                return ForkingUrgency.MEDIUM
            elif urgency_score > 0.1:
                return ForkingUrgency.LOW
            else:
                return ForkingUrgency.LOW
                
        except Exception as e:
            logger.error(f"Error calculating forking urgency: {str(e)}")
            return ForkingUrgency.MEDIUM
    
    def _calculate_confidence_score(self, 
                                  account: Account,
                                  risk_assessment: Dict[str, Any],
                                  market_assessment: Dict[str, Any]) -> Decimal:
        """Calculate confidence score for forking decision."""
        try:
            # Base confidence factors
            factors = {
                "account_stability": 0.8,  # Account stability factor
                "market_conditions": market_assessment.get("optimal_timing_score", 0.7),
                "risk_level": 1.0 - risk_assessment.get("overall_risk_score", 0.5),
                "system_readiness": 0.9   # System readiness factor
            }
            
            # Adjust for account age and performance
            account_age_days = (datetime.now() - account.created_date).days
            if account_age_days > 90:
                factors["account_stability"] = min(1.0, factors["account_stability"] + 0.1)
            
            # Calculate weighted confidence
            confidence = sum(factors.values()) / len(factors)
            
            return Decimal(str(min(1.0, max(0.0, confidence))))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return Decimal("0.5")
    
    def _calculate_recommended_fork_amount(self, 
                                         account: Account,
                                         excess_capital: Decimal,
                                         risk_assessment: Dict[str, Any]) -> Decimal:
        """Calculate recommended fork amount."""
        try:
            threshold = self.forking_thresholds[account.account_type]
            risk_score = risk_assessment.get("overall_risk_score", 0.5)
            
            # Base fork amount is the threshold amount
            base_amount = threshold
            
            # Adjust based on excess capital and risk
            if excess_capital > threshold * Decimal("0.5"):  # 50% excess
                # Fork more aggressively if significant excess
                additional_amount = min(excess_capital * Decimal("0.3"), threshold * Decimal("0.2"))
                base_amount += additional_amount
            
            # Adjust for risk (reduce amount if high risk)
            risk_adjustment = Decimal(str(1.0 - (risk_score * 0.2)))
            recommended_amount = base_amount * risk_adjustment
            
            # Ensure minimum viable fork amount
            min_fork_amount = threshold * Decimal("0.8")
            recommended_amount = max(recommended_amount, min_fork_amount)
            
            # Ensure we don't fork more than available
            max_fork_amount = account.available_capital * Decimal("0.9")  # Leave 10% buffer
            recommended_amount = min(recommended_amount, max_fork_amount)
            
            return recommended_amount
            
        except Exception as e:
            logger.error(f"Error calculating recommended fork amount: {str(e)}")
            return self.forking_thresholds[account.account_type]
    
    def _get_timing_recommendation(self, 
                                 market_assessment: Dict[str, Any],
                                 risk_assessment: Dict[str, Any]) -> str:
        """Get timing recommendation for forking."""
        try:
            timing_score = market_assessment.get("optimal_timing_score", 0.7)
            risk_score = risk_assessment.get("overall_risk_score", 0.5)
            
            if timing_score > 0.8 and risk_score < 0.3:
                return "immediate"
            elif timing_score > 0.6 and risk_score < 0.5:
                return "within_24_hours"
            elif timing_score > 0.4:
                return "within_week"
            else:
                return "defer_until_conditions_improve"
                
        except Exception as e:
            logger.error(f"Error getting timing recommendation: {str(e)}")
            return "within_24_hours"
    
    def _identify_forking_benefits(self, account: Account, target_type: AccountType) -> List[str]:
        """Identify potential benefits of forking."""
        benefits = [
            f"Upgrade to {target_type.value} with enhanced capabilities",
            "Increased position limits and sizing flexibility",
            "Enhanced risk management parameters",
            "Access to advanced trading strategies"
        ]
        
        if target_type == AccountType.REV_ACC:
            benefits.extend([
                "20% higher risk tolerance",
                "Increased to 20 maximum positions",
                "Enhanced roll frequency capabilities"
            ])
        elif target_type == AccountType.COM_ACC:
            benefits.extend([
                "50% higher risk tolerance",
                "Increased to 50 maximum positions",
                "Access to institutional features",
                "Advanced strategy capabilities"
            ])
        
        return benefits
    
    def _identify_forking_risks(self, account: Account, risk_assessment: Dict[str, Any]) -> List[str]:
        """Identify potential risks of forking."""
        risks = [
            "Temporary account unavailability during fork process",
            "Capital allocation complexity",
            "Increased operational overhead"
        ]
        
        risk_level = risk_assessment.get("risk_level", "medium")
        if risk_level == "high":
            risks.extend([
                "High market volatility may affect fork timing",
                "Increased market risk exposure",
                "Potential liquidity constraints"
            ])
        
        return risks
    
    def _identify_forking_prerequisites(self, account: Account) -> List[str]:
        """Identify prerequisites for forking."""
        prerequisites = [
            "Account must be in ACTIVE or SAFE state",
            "Sufficient available capital for fork amount",
            "No pending transactions or orders",
            "System resources available for fork process"
        ]
        
        if account.account_state != AccountState.ACTIVE:
            prerequisites.append("Account must be activated before forking")
        
        if len(account.positions) > 0:
            prerequisites.append("Review and validate all open positions")
        
        return prerequisites
    
    def _apply_override_conditions(self, 
                                 opportunity: ForkingOpportunity,
                                 override_conditions: Dict[str, Any]) -> ForkingOpportunity:
        """Apply override conditions to forking opportunity."""
        # Create a copy and apply overrides
        updated_opportunity = opportunity
        
        if "fork_amount" in override_conditions:
            updated_opportunity.recommended_fork_amount = Decimal(str(override_conditions["fork_amount"]))
        
        if "urgency" in override_conditions:
            updated_opportunity.urgency = ForkingUrgency(override_conditions["urgency"])
        
        if "confidence_adjustment" in override_conditions:
            adjustment = Decimal(str(override_conditions["confidence_adjustment"]))
            updated_opportunity.confidence_score = max(Decimal("0"), min(Decimal("1"), 
                                                                        updated_opportunity.confidence_score + adjustment))
        
        return updated_opportunity
    
    def _evaluate_decision_logic(self, opportunity: ForkingOpportunity) -> Dict[str, Any]:
        """Evaluate decision logic for forking opportunity."""
        try:
            confidence = opportunity.confidence_score
            risk_score = opportunity.risk_assessment.get("overall_risk_score", 0.5)
            urgency = opportunity.urgency
            
            # Decision logic
            if confidence >= self.min_confidence_threshold and risk_score < 0.6:
                decision = "approve"
                reasoning = f"High confidence ({float(confidence):.2f}) and acceptable risk ({risk_score:.2f})"
            elif confidence >= Decimal("0.5") and urgency in [ForkingUrgency.HIGH, ForkingUrgency.CRITICAL]:
                decision = "approve"
                reasoning = f"Urgent forking required despite moderate confidence ({float(confidence):.2f})"
            elif risk_score > 0.8:
                decision = "reject"
                reasoning = f"Risk score too high ({risk_score:.2f}) for safe forking"
            else:
                decision = "defer"
                reasoning = f"Confidence ({float(confidence):.2f}) or risk ({risk_score:.2f}) not optimal for immediate forking"
            
            # Timeline
            timeline = {
                "decision_made": datetime.now(),
                "earliest_execution": datetime.now() + timedelta(hours=1),
                "recommended_execution": datetime.now() + timedelta(hours=2),
                "latest_execution": datetime.now() + timedelta(days=7)
            }
            
            # Conditions
            conditions = []
            if decision == "approve":
                conditions = [
                    "Account must remain in stable state",
                    "Market conditions must not deteriorate significantly",
                    "System resources must be available"
                ]
            
            # Risk mitigation
            risk_mitigation = [
                "Monitor account during fork process",
                "Maintain minimum capital buffer",
                "Validate all prerequisites before execution"
            ]
            
            return {
                "decision": decision,
                "fork_amount": opportunity.recommended_fork_amount,
                "reasoning": reasoning,
                "conditions": conditions,
                "timeline": timeline,
                "risk_mitigation": risk_mitigation,
                "approval_required": risk_score > 0.6 or confidence < Decimal("0.6")
            }
            
        except Exception as e:
            logger.error(f"Error evaluating decision logic: {str(e)}")
            return {
                "decision": "defer",
                "fork_amount": opportunity.recommended_fork_amount,
                "reasoning": f"Decision evaluation error: {str(e)}",
                "conditions": [],
                "timeline": {},
                "risk_mitigation": [],
                "approval_required": True
            }
    
    def _get_next_steps(self, decision: ForkingDecision) -> List[str]:
        """Get next steps based on forking decision."""
        if decision.decision == "approve":
            return [
                "Validate all prerequisites",
                "Reserve capital for forking",
                "Schedule fork execution",
                "Notify relevant systems",
                "Begin fork process"
            ]
        elif decision.decision == "defer":
            return [
                "Monitor conditions for improvement",
                "Re-assess in 24 hours",
                "Address identified risks",
                "Update market data",
                "Prepare for future execution"
            ]
        else:  # reject
            return [
                "Document rejection reasons",
                "Monitor for condition changes",
                "Consider alternative strategies",
                "Schedule future re-assessment",
                "Notify stakeholders"
            ]
    
    def get_forking_status(self) -> Dict[str, Any]:
        """Get overall forking system status."""
        try:
            # Count opportunities by status
            recent_opportunities = [
                opp for opp in self.forking_opportunities.values()
                if (datetime.now() - opp.timestamp).total_seconds() < 86400  # Last 24 hours
            ]
            
            # Count decisions by type
            recent_decisions = [
                dec for dec in self.forking_decisions.values()
                if (datetime.now() - dec.decision_timestamp).total_seconds() < 86400
            ]
            
            decision_breakdown = {}
            for decision in recent_decisions:
                decision_type = decision.decision
                decision_breakdown[decision_type] = decision_breakdown.get(decision_type, 0) + 1
            
            return {
                "total_opportunities_assessed": len(self.forking_opportunities),
                "recent_opportunities": len(recent_opportunities),
                "total_decisions_made": len(self.forking_decisions),
                "recent_decisions": len(recent_decisions),
                "decision_breakdown": decision_breakdown,
                "active_forks": len(self.active_forks),
                "max_concurrent_forks": self.max_concurrent_forks,
                "system_capacity": f"{len(self.active_forks)}/{self.max_concurrent_forks}",
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting forking status: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }

