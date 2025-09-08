"""
Consolidation Engine

This module implements the intelligent consolidation decision engine
that determines when and how to merge accounts for optimal performance,
risk management, and operational efficiency.
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict
import uuid

from src.ws3_account_management.accounts import AccountType, AccountState, Account
from src.ws1_rules_engine.audit import AuditTrailManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class ConsolidationTrigger(Enum):
    """Types of consolidation triggers."""
    UNDERPERFORMANCE = "underperformance"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    RISK_MANAGEMENT = "risk_management"
    CAPITAL_OPTIMIZATION = "capital_optimization"
    MANUAL_REQUEST = "manual_request"
    SYSTEM_OPTIMIZATION = "system_optimization"


class ConsolidationStrategy(Enum):
    """Consolidation strategies."""
    MERGE_TO_PARENT = "merge_to_parent"
    MERGE_TO_SIBLING = "merge_to_sibling"
    MERGE_TO_NEW = "merge_to_new"
    PARTIAL_CONSOLIDATION = "partial_consolidation"


class ConsolidationUrgency(Enum):
    """Consolidation urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ConsolidationOpportunity:
    """Consolidation opportunity assessment."""
    opportunity_id: str
    source_account_ids: List[str]
    target_account_id: Optional[str]
    trigger_type: ConsolidationTrigger
    strategy: ConsolidationStrategy
    urgency: ConsolidationUrgency
    total_value: Decimal
    expected_savings: Decimal
    risk_reduction: Decimal
    performance_improvement: Decimal
    operational_benefits: List[str]
    consolidation_risks: List[str]
    prerequisites: List[str]
    estimated_completion_time: timedelta
    confidence_score: Decimal
    recommendation: str
    timestamp: datetime


@dataclass
class ConsolidationDecision:
    """Final consolidation decision."""
    decision_id: str
    opportunity_id: str
    decision: str  # "approve", "defer", "reject"
    source_accounts: List[str]
    target_account: Optional[str]
    consolidation_plan: Dict[str, Any]
    timeline: Dict[str, datetime]
    risk_mitigation: List[str]
    success_criteria: List[str]
    rollback_plan: Dict[str, Any]
    approval_required: bool
    decision_timestamp: datetime


class ConsolidationEngine:
    """
    Intelligent consolidation engine for account merging decisions.
    
    Analyzes account performance, operational efficiency, and risk factors
    to identify optimal consolidation opportunities that improve overall
    system performance while maintaining safety and compliance.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize consolidation engine.
        
        Args:
            audit_manager: Audit trail manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.config = config or {}
        
        # Consolidation parameters
        self.min_confidence_threshold = Decimal(str(self.config.get("min_confidence_threshold", 0.75)))
        self.max_concurrent_consolidations = self.config.get("max_concurrent_consolidations", 3)
        self.consolidation_cooldown_hours = self.config.get("consolidation_cooldown_hours", 48)
        
        # Performance thresholds
        self.underperformance_threshold = Decimal(str(self.config.get("underperformance_threshold", -0.05)))  # -5%
        self.efficiency_threshold = Decimal(str(self.config.get("efficiency_threshold", 0.10)))  # 10% savings
        
        # Risk assessment weights
        self.risk_weights = {
            "performance_risk": 0.3,
            "operational_risk": 0.2,
            "market_risk": 0.2,
            "consolidation_risk": 0.3
        }
        
        # Opportunity and decision storage
        self.consolidation_opportunities = {}  # opportunity_id -> ConsolidationOpportunity
        self.consolidation_decisions = {}      # decision_id -> ConsolidationDecision
        self.active_consolidations = set()     # Set of account_ids currently consolidating
        
        logger.info("Consolidation Engine initialized")
    
    def assess_consolidation_opportunities(self, 
                                         accounts: List[Account],
                                         performance_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess consolidation opportunities across multiple accounts.
        
        Args:
            accounts: List of accounts to analyze
            performance_data: Optional performance data
            
        Returns:
            Consolidation opportunities assessment
        """
        try:
            opportunities = []
            
            # Group accounts by hierarchy and type
            account_groups = self._group_accounts_for_analysis(accounts)
            
            # Analyze each group for consolidation opportunities
            for group_type, account_group in account_groups.items():
                group_opportunities = self._analyze_account_group(account_group, performance_data)
                opportunities.extend(group_opportunities)
            
            # Rank opportunities by potential benefit
            ranked_opportunities = self._rank_consolidation_opportunities(opportunities)
            
            # Store opportunities
            for opportunity in ranked_opportunities:
                self.consolidation_opportunities[opportunity.opportunity_id] = opportunity
            
            return {
                "total_opportunities": len(opportunities),
                "high_priority_opportunities": len([o for o in opportunities if o.urgency == ConsolidationUrgency.HIGH]),
                "recommended_opportunities": len([o for o in opportunities if o.recommendation == "proceed"]),
                "opportunities": [asdict(o) for o in ranked_opportunities[:10]],  # Top 10
                "assessment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing consolidation opportunities: {str(e)}", exc_info=True)
            return {
                "total_opportunities": 0,
                "error": str(e),
                "assessment_timestamp": datetime.now().isoformat()
            }
    
    def _group_accounts_for_analysis(self, accounts: List[Account]) -> Dict[str, List[Account]]:
        """Group accounts for consolidation analysis."""
        groups = {
            "siblings": [],      # Accounts with same parent
            "parent_child": [],  # Parent-child relationships
            "same_type": [],     # Same account type
            "underperforming": [] # Underperforming accounts
        }
        
        # Group by parent relationships
        parent_groups = {}
        for account in accounts:
            if account.parent_account_id:
                if account.parent_account_id not in parent_groups:
                    parent_groups[account.parent_account_id] = []
                parent_groups[account.parent_account_id].append(account)
        
        # Add sibling groups (accounts with same parent)
        for parent_id, children in parent_groups.items():
            if len(children) > 1:
                groups["siblings"].extend(children)
        
        # Group by account type
        type_groups = {}
        for account in accounts:
            account_type = account.account_type
            if account_type not in type_groups:
                type_groups[account_type] = []
            type_groups[account_type].append(account)
        
        # Add same-type groups
        for account_type, type_accounts in type_groups.items():
            if len(type_accounts) > 1:
                groups["same_type"].extend(type_accounts)
        
        return groups
    
    def _analyze_account_group(self, 
                             accounts: List[Account],
                             performance_data: Optional[Dict[str, Any]]) -> List[ConsolidationOpportunity]:
        """Analyze a group of accounts for consolidation opportunities."""
        opportunities = []
        
        try:
            if len(accounts) < 2:
                return opportunities
            
            # Analyze different consolidation scenarios
            scenarios = [
                self._analyze_underperformance_consolidation(accounts, performance_data),
                self._analyze_operational_efficiency_consolidation(accounts),
                self._analyze_risk_management_consolidation(accounts),
                self._analyze_capital_optimization_consolidation(accounts)
            ]
            
            # Filter and validate opportunities
            for scenario_opportunities in scenarios:
                for opportunity in scenario_opportunities:
                    if self._validate_consolidation_opportunity(opportunity):
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing account group: {str(e)}")
            return opportunities
    
    def _analyze_underperformance_consolidation(self, 
                                              accounts: List[Account],
                                              performance_data: Optional[Dict[str, Any]]) -> List[ConsolidationOpportunity]:
        """Analyze consolidation opportunities based on underperformance."""
        opportunities = []
        
        try:
            # Identify underperforming accounts
            underperforming = []
            performing = []
            
            for account in accounts:
                # Simplified performance check (would use real performance data)
                performance_score = self._calculate_account_performance_score(account, performance_data)
                
                if performance_score < self.underperformance_threshold:
                    underperforming.append((account, performance_score))
                else:
                    performing.append((account, performance_score))
            
            # Create consolidation opportunities for underperforming accounts
            if underperforming and performing:
                # Find best performing account as target
                best_performer = max(performing, key=lambda x: x[1])
                target_account = best_performer[0]
                
                for underperforming_account, score in underperforming:
                    opportunity = self._create_consolidation_opportunity(
                        source_accounts=[underperforming_account.account_id],
                        target_account=target_account.account_id,
                        trigger=ConsolidationTrigger.UNDERPERFORMANCE,
                        strategy=ConsolidationStrategy.MERGE_TO_SIBLING,
                        performance_improvement=abs(score - best_performer[1])
                    )
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing underperformance consolidation: {str(e)}")
            return opportunities
    
    def _analyze_operational_efficiency_consolidation(self, accounts: List[Account]) -> List[ConsolidationOpportunity]:
        """Analyze consolidation opportunities based on operational efficiency."""
        opportunities = []
        
        try:
            # Calculate operational costs for each account
            total_operational_cost = Decimal("0")
            account_costs = {}
            
            for account in accounts:
                # Simplified operational cost calculation
                base_cost = Decimal("100")  # Base monthly cost per account
                position_cost = Decimal(str(len(account.positions))) * Decimal("10")  # Cost per position
                monitoring_cost = Decimal("50")  # Monitoring cost
                
                account_cost = base_cost + position_cost + monitoring_cost
                account_costs[account.account_id] = account_cost
                total_operational_cost += account_cost
            
            # Calculate potential savings from consolidation
            if len(accounts) > 1:
                # Consolidated operational cost (economies of scale)
                consolidated_base_cost = Decimal("150")  # Higher base but shared
                total_positions = sum(len(account.positions) for account in accounts)
                consolidated_position_cost = Decimal(str(total_positions)) * Decimal("8")  # Reduced per-position cost
                consolidated_monitoring_cost = Decimal("75")  # Shared monitoring
                
                consolidated_cost = consolidated_base_cost + consolidated_position_cost + consolidated_monitoring_cost
                potential_savings = total_operational_cost - consolidated_cost
                
                if potential_savings >= self.efficiency_threshold * total_operational_cost:
                    # Find best target account (largest)
                    target_account = max(accounts, key=lambda a: a.current_value)
                    source_accounts = [a.account_id for a in accounts if a.account_id != target_account.account_id]
                    
                    opportunity = self._create_consolidation_opportunity(
                        source_accounts=source_accounts,
                        target_account=target_account.account_id,
                        trigger=ConsolidationTrigger.OPERATIONAL_EFFICIENCY,
                        strategy=ConsolidationStrategy.MERGE_TO_SIBLING,
                        expected_savings=potential_savings
                    )
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing operational efficiency consolidation: {str(e)}")
            return opportunities
    
    def _analyze_risk_management_consolidation(self, accounts: List[Account]) -> List[ConsolidationOpportunity]:
        """Analyze consolidation opportunities based on risk management."""
        opportunities = []
        
        try:
            # Calculate risk metrics for each account
            high_risk_accounts = []
            
            for account in accounts:
                risk_score = self._calculate_account_risk_score(account)
                
                if risk_score > 0.7:  # High risk threshold
                    high_risk_accounts.append((account, risk_score))
            
            # If we have high-risk accounts, consider consolidation
            if high_risk_accounts:
                # Find lower-risk accounts as potential targets
                low_risk_accounts = [
                    account for account in accounts
                    if self._calculate_account_risk_score(account) < 0.5
                ]
                
                if low_risk_accounts:
                    target_account = min(low_risk_accounts, key=lambda a: self._calculate_account_risk_score(a))
                    
                    for high_risk_account, risk_score in high_risk_accounts:
                        risk_reduction = risk_score - self._calculate_account_risk_score(target_account)
                        
                        opportunity = self._create_consolidation_opportunity(
                            source_accounts=[high_risk_account.account_id],
                            target_account=target_account.account_id,
                            trigger=ConsolidationTrigger.RISK_MANAGEMENT,
                            strategy=ConsolidationStrategy.MERGE_TO_SIBLING,
                            risk_reduction=risk_reduction
                        )
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing risk management consolidation: {str(e)}")
            return opportunities
    
    def _analyze_capital_optimization_consolidation(self, accounts: List[Account]) -> List[ConsolidationOpportunity]:
        """Analyze consolidation opportunities based on capital optimization."""
        opportunities = []
        
        try:
            # Calculate capital utilization for each account
            underutilized_accounts = []
            
            for account in accounts:
                utilization = self._calculate_capital_utilization(account)
                
                if utilization < 0.5:  # Less than 50% utilization
                    underutilized_accounts.append((account, utilization))
            
            # Group underutilized accounts for consolidation
            if len(underutilized_accounts) >= 2:
                # Sort by utilization (lowest first)
                underutilized_accounts.sort(key=lambda x: x[1])
                
                # Create consolidation opportunity
                source_accounts = [acc[0].account_id for acc in underutilized_accounts[:-1]]
                target_account = underutilized_accounts[-1][0]  # Best utilized as target
                
                total_value = sum(acc[0].current_value for acc in underutilized_accounts)
                
                opportunity = self._create_consolidation_opportunity(
                    source_accounts=source_accounts,
                    target_account=target_account.account_id,
                    trigger=ConsolidationTrigger.CAPITAL_OPTIMIZATION,
                    strategy=ConsolidationStrategy.MERGE_TO_SIBLING,
                    total_value=total_value
                )
                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing capital optimization consolidation: {str(e)}")
            return opportunities
    
    def _create_consolidation_opportunity(self, 
                                        source_accounts: List[str],
                                        target_account: Optional[str],
                                        trigger: ConsolidationTrigger,
                                        strategy: ConsolidationStrategy,
                                        total_value: Optional[Decimal] = None,
                                        expected_savings: Optional[Decimal] = None,
                                        risk_reduction: Optional[Decimal] = None,
                                        performance_improvement: Optional[Decimal] = None) -> ConsolidationOpportunity:
        """Create a consolidation opportunity."""
        
        opportunity_id = f"consol_{uuid.uuid4().hex[:8]}"
        
        # Calculate metrics if not provided
        if total_value is None:
            total_value = Decimal("0")  # Would calculate from actual accounts
        
        if expected_savings is None:
            expected_savings = Decimal("0")
        
        if risk_reduction is None:
            risk_reduction = Decimal("0")
        
        if performance_improvement is None:
            performance_improvement = Decimal("0")
        
        # Determine urgency
        urgency = self._calculate_consolidation_urgency(trigger, expected_savings, risk_reduction)
        
        # Calculate confidence score
        confidence_score = self._calculate_consolidation_confidence(
            trigger, expected_savings, risk_reduction, performance_improvement
        )
        
        # Determine recommendation
        recommendation = "proceed" if confidence_score >= self.min_confidence_threshold else "defer"
        
        return ConsolidationOpportunity(
            opportunity_id=opportunity_id,
            source_account_ids=source_accounts,
            target_account_id=target_account,
            trigger_type=trigger,
            strategy=strategy,
            urgency=urgency,
            total_value=total_value,
            expected_savings=expected_savings,
            risk_reduction=risk_reduction,
            performance_improvement=performance_improvement,
            operational_benefits=self._identify_operational_benefits(trigger, strategy),
            consolidation_risks=self._identify_consolidation_risks(trigger, strategy),
            prerequisites=self._identify_consolidation_prerequisites(source_accounts, target_account),
            estimated_completion_time=timedelta(hours=4),  # Estimated consolidation time
            confidence_score=confidence_score,
            recommendation=recommendation,
            timestamp=datetime.now()
        )
    
    def _calculate_account_performance_score(self, 
                                           account: Account,
                                           performance_data: Optional[Dict[str, Any]]) -> Decimal:
        """Calculate account performance score."""
        try:
            if performance_data and account.account_id in performance_data:
                return Decimal(str(performance_data[account.account_id].get("performance_score", 0)))
            
            # Simplified performance calculation
            account_age_days = (datetime.now() - account.created_date).days
            if account_age_days == 0:
                return Decimal("0")
            
            # Simple performance metric based on value growth
            value_growth = (account.current_value - account.initial_capital) / account.initial_capital
            annualized_return = value_growth * Decimal("365") / Decimal(str(account_age_days))
            
            return annualized_return
            
        except Exception as e:
            logger.error(f"Error calculating account performance score: {str(e)}")
            return Decimal("0")
    
    def _calculate_account_risk_score(self, account: Account) -> Decimal:
        """Calculate account risk score."""
        try:
            # Simplified risk calculation
            base_risk = Decimal("0.3")
            
            # Risk based on position count
            position_risk = min(Decimal("0.3"), Decimal(str(len(account.positions))) * Decimal("0.02"))
            
            # Risk based on capital utilization
            utilization = self._calculate_capital_utilization(account)
            utilization_risk = max(Decimal("0"), utilization - Decimal("0.8")) * Decimal("2")
            
            total_risk = base_risk + position_risk + utilization_risk
            return min(Decimal("1"), total_risk)
            
        except Exception as e:
            logger.error(f"Error calculating account risk score: {str(e)}")
            return Decimal("0.5")
    
    def _calculate_capital_utilization(self, account: Account) -> Decimal:
        """Calculate capital utilization for account."""
        try:
            if account.current_value == 0:
                return Decimal("0")
            
            return account.reserved_capital / account.current_value
            
        except Exception as e:
            logger.error(f"Error calculating capital utilization: {str(e)}")
            return Decimal("0")
    
    def _calculate_consolidation_urgency(self, 
                                       trigger: ConsolidationTrigger,
                                       expected_savings: Decimal,
                                       risk_reduction: Decimal) -> ConsolidationUrgency:
        """Calculate consolidation urgency."""
        try:
            urgency_score = 0
            
            # Urgency based on trigger type
            trigger_urgency = {
                ConsolidationTrigger.UNDERPERFORMANCE: 3,
                ConsolidationTrigger.RISK_MANAGEMENT: 4,
                ConsolidationTrigger.OPERATIONAL_EFFICIENCY: 2,
                ConsolidationTrigger.CAPITAL_OPTIMIZATION: 1,
                ConsolidationTrigger.MANUAL_REQUEST: 2,
                ConsolidationTrigger.SYSTEM_OPTIMIZATION: 1
            }
            
            urgency_score += trigger_urgency.get(trigger, 1)
            
            # Adjust based on benefits
            if expected_savings > Decimal("1000"):  # $1000+ savings
                urgency_score += 1
            
            if risk_reduction > Decimal("0.3"):  # 30%+ risk reduction
                urgency_score += 2
            
            # Convert to urgency level
            if urgency_score >= 6:
                return ConsolidationUrgency.CRITICAL
            elif urgency_score >= 4:
                return ConsolidationUrgency.HIGH
            elif urgency_score >= 2:
                return ConsolidationUrgency.MEDIUM
            else:
                return ConsolidationUrgency.LOW
                
        except Exception as e:
            logger.error(f"Error calculating consolidation urgency: {str(e)}")
            return ConsolidationUrgency.MEDIUM
    
    def _calculate_consolidation_confidence(self, 
                                          trigger: ConsolidationTrigger,
                                          expected_savings: Decimal,
                                          risk_reduction: Decimal,
                                          performance_improvement: Decimal) -> Decimal:
        """Calculate confidence score for consolidation."""
        try:
            confidence_factors = {
                "trigger_reliability": 0.3,
                "benefit_magnitude": 0.4,
                "risk_assessment": 0.3
            }
            
            # Trigger reliability
            trigger_confidence = {
                ConsolidationTrigger.UNDERPERFORMANCE: 0.8,
                ConsolidationTrigger.OPERATIONAL_EFFICIENCY: 0.9,
                ConsolidationTrigger.RISK_MANAGEMENT: 0.7,
                ConsolidationTrigger.CAPITAL_OPTIMIZATION: 0.8,
                ConsolidationTrigger.MANUAL_REQUEST: 0.6,
                ConsolidationTrigger.SYSTEM_OPTIMIZATION: 0.7
            }
            
            trigger_score = trigger_confidence.get(trigger, 0.5)
            
            # Benefit magnitude
            savings_score = min(1.0, float(expected_savings) / 5000)  # Scale to $5000 max
            risk_score = min(1.0, float(risk_reduction) * 2)  # Scale risk reduction
            performance_score = min(1.0, float(performance_improvement) * 10)  # Scale performance
            
            benefit_score = (savings_score + risk_score + performance_score) / 3
            
            # Risk assessment (simplified)
            risk_assessment_score = 0.8  # Base risk assessment confidence
            
            # Calculate weighted confidence
            confidence = (
                trigger_score * confidence_factors["trigger_reliability"] +
                benefit_score * confidence_factors["benefit_magnitude"] +
                risk_assessment_score * confidence_factors["risk_assessment"]
            )
            
            return Decimal(str(min(1.0, max(0.0, confidence))))
            
        except Exception as e:
            logger.error(f"Error calculating consolidation confidence: {str(e)}")
            return Decimal("0.5")
    
    def _identify_operational_benefits(self, 
                                     trigger: ConsolidationTrigger,
                                     strategy: ConsolidationStrategy) -> List[str]:
        """Identify operational benefits of consolidation."""
        benefits = [
            "Reduced operational overhead",
            "Simplified account management",
            "Improved capital efficiency"
        ]
        
        if trigger == ConsolidationTrigger.OPERATIONAL_EFFICIENCY:
            benefits.extend([
                "Lower monitoring costs",
                "Reduced administrative burden",
                "Streamlined reporting"
            ])
        
        if trigger == ConsolidationTrigger.RISK_MANAGEMENT:
            benefits.extend([
                "Improved risk diversification",
                "Enhanced risk monitoring",
                "Better risk-adjusted returns"
            ])
        
        return benefits
    
    def _identify_consolidation_risks(self, 
                                    trigger: ConsolidationTrigger,
                                    strategy: ConsolidationStrategy) -> List[str]:
        """Identify risks of consolidation."""
        risks = [
            "Temporary account unavailability during consolidation",
            "Position transfer complexity",
            "Performance attribution challenges"
        ]
        
        if strategy == ConsolidationStrategy.MERGE_TO_NEW:
            risks.extend([
                "New account setup complexity",
                "Increased setup time",
                "Additional validation requirements"
            ])
        
        return risks
    
    def _identify_consolidation_prerequisites(self, 
                                            source_accounts: List[str],
                                            target_account: Optional[str]) -> List[str]:
        """Identify prerequisites for consolidation."""
        prerequisites = [
            "All accounts must be in stable state",
            "No pending transactions or orders",
            "Sufficient system resources for consolidation",
            "Backup and recovery procedures in place"
        ]
        
        if target_account:
            prerequisites.append("Target account must have sufficient capacity")
        
        return prerequisites
    
    def _validate_consolidation_opportunity(self, opportunity: ConsolidationOpportunity) -> bool:
        """Validate consolidation opportunity."""
        try:
            # Basic validation checks
            if not opportunity.source_account_ids:
                return False
            
            if opportunity.confidence_score < Decimal("0.3"):  # Minimum confidence
                return False
            
            if opportunity.urgency == ConsolidationUrgency.CRITICAL and opportunity.confidence_score < Decimal("0.6"):
                return False  # Critical urgency requires higher confidence
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating consolidation opportunity: {str(e)}")
            return False
    
    def _rank_consolidation_opportunities(self, opportunities: List[ConsolidationOpportunity]) -> List[ConsolidationOpportunity]:
        """Rank consolidation opportunities by priority."""
        try:
            def priority_score(opp):
                urgency_weights = {
                    ConsolidationUrgency.CRITICAL: 4,
                    ConsolidationUrgency.HIGH: 3,
                    ConsolidationUrgency.MEDIUM: 2,
                    ConsolidationUrgency.LOW: 1
                }
                
                urgency_score = urgency_weights.get(opp.urgency, 1)
                confidence_score = float(opp.confidence_score) * 10
                benefit_score = float(opp.expected_savings + opp.risk_reduction * 1000 + opp.performance_improvement * 1000)
                
                return urgency_score * 100 + confidence_score * 10 + benefit_score
            
            return sorted(opportunities, key=priority_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error ranking consolidation opportunities: {str(e)}")
            return opportunities
    
    def make_consolidation_decision(self, opportunity_id: str) -> Dict[str, Any]:
        """Make final consolidation decision."""
        try:
            opportunity = self.consolidation_opportunities.get(opportunity_id)
            if not opportunity:
                return {
                    "success": False,
                    "error": f"Consolidation opportunity {opportunity_id} not found"
                }
            
            # Create consolidation decision
            decision = ConsolidationDecision(
                decision_id=f"consol_decision_{uuid.uuid4().hex[:8]}",
                opportunity_id=opportunity_id,
                decision="approve" if opportunity.recommendation == "proceed" else "defer",
                source_accounts=opportunity.source_account_ids,
                target_account=opportunity.target_account_id,
                consolidation_plan=self._create_consolidation_plan(opportunity),
                timeline=self._create_consolidation_timeline(opportunity),
                risk_mitigation=opportunity.consolidation_risks,
                success_criteria=self._define_success_criteria(opportunity),
                rollback_plan=self._create_rollback_plan(opportunity),
                approval_required=opportunity.confidence_score < Decimal("0.8"),
                decision_timestamp=datetime.now()
            )
            
            # Store decision
            self.consolidation_decisions[decision.decision_id] = decision
            
            # Log decision
            self.audit_manager.log_system_event(
                event_type="consolidation_decision",
                event_data=asdict(decision),
                severity="info"
            )
            
            return {
                "success": True,
                "decision": asdict(decision),
                "decision_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making consolidation decision: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "opportunity_id": opportunity_id
            }
    
    def _create_consolidation_plan(self, opportunity: ConsolidationOpportunity) -> Dict[str, Any]:
        """Create detailed consolidation plan."""
        return {
            "phase_1": "Validate prerequisites and prepare accounts",
            "phase_2": "Transfer positions and capital",
            "phase_3": "Update account hierarchy and metadata",
            "phase_4": "Validate consolidation and cleanup",
            "estimated_duration": str(opportunity.estimated_completion_time),
            "resource_requirements": ["system_capacity", "operator_availability"]
        }
    
    def _create_consolidation_timeline(self, opportunity: ConsolidationOpportunity) -> Dict[str, datetime]:
        """Create consolidation timeline."""
        now = datetime.now()
        return {
            "decision_made": now,
            "preparation_start": now + timedelta(hours=1),
            "execution_start": now + timedelta(hours=2),
            "estimated_completion": now + opportunity.estimated_completion_time,
            "validation_deadline": now + opportunity.estimated_completion_time + timedelta(hours=1)
        }
    
    def _define_success_criteria(self, opportunity: ConsolidationOpportunity) -> List[str]:
        """Define success criteria for consolidation."""
        return [
            "All positions successfully transferred",
            "Capital allocation correctly updated",
            "Account hierarchy properly maintained",
            "Performance attribution preserved",
            "No data loss during consolidation"
        ]
    
    def _create_rollback_plan(self, opportunity: ConsolidationOpportunity) -> Dict[str, Any]:
        """Create rollback plan for consolidation."""
        return {
            "rollback_triggers": [
                "Data integrity issues",
                "Position transfer failures",
                "System errors during consolidation"
            ],
            "rollback_steps": [
                "Halt consolidation process",
                "Restore account states from backup",
                "Validate data integrity",
                "Resume normal operations"
            ],
            "rollback_time_limit": "2 hours from consolidation start"
        }
    
    def get_consolidation_status(self) -> Dict[str, Any]:
        """Get consolidation system status."""
        try:
            recent_opportunities = [
                opp for opp in self.consolidation_opportunities.values()
                if (datetime.now() - opp.timestamp).total_seconds() < 86400
            ]
            
            recent_decisions = [
                dec for dec in self.consolidation_decisions.values()
                if (datetime.now() - dec.decision_timestamp).total_seconds() < 86400
            ]
            
            return {
                "total_opportunities": len(self.consolidation_opportunities),
                "recent_opportunities": len(recent_opportunities),
                "total_decisions": len(self.consolidation_decisions),
                "recent_decisions": len(recent_decisions),
                "active_consolidations": len(self.active_consolidations),
                "system_capacity": f"{len(self.active_consolidations)}/{self.max_concurrent_consolidations}",
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting consolidation status: {str(e)}")
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }

