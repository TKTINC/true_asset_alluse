"""
Account Manager

This module implements the main account management system that handles
the three-tiered account structure (Gen/Rev/Com) with state management,
validation, and performance tracking.
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
import logging
import uuid
from dataclasses import dataclass, asdict

from .account_types import AccountType, AccountState, AccountTypeManager, AccountConfig
from .account_validator import AccountValidator
from .account_tracker import AccountPerformanceTracker
from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws2_protocol_engine.escalation import ProtocolEscalationManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """Account data structure."""
    account_id: str
    account_type: AccountType
    account_state: AccountState
    name: str
    created_date: datetime
    initial_capital: Decimal
    current_value: Decimal
    available_capital: Decimal
    reserved_capital: Decimal
    parent_account_id: Optional[str]
    child_account_ids: List[str]
    positions: List[str]  # Position IDs
    performance_metrics: Dict[str, Any]
    last_updated: datetime
    metadata: Dict[str, Any]


@dataclass
class AccountStateChange:
    """Account state change event."""
    change_id: str
    account_id: str
    timestamp: datetime
    from_state: AccountState
    to_state: AccountState
    reason: str
    triggered_by: str
    metadata: Dict[str, Any]


class AccountManager:
    """
    Main Account Manager for three-tiered account system.
    
    Manages Gen-Acc, Rev-Acc, and Com-Acc accounts with proper
    state transitions, validation, and performance tracking.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 escalation_manager: Optional[ProtocolEscalationManager] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Account Manager.
        
        Args:
            audit_manager: Audit trail manager
            escalation_manager: Optional protocol escalation manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.escalation_manager = escalation_manager
        self.config = config or {}
        
        # Initialize managers
        self.account_type_manager = AccountTypeManager()
        self.account_validator = AccountValidator()
        self.performance_tracker = AccountPerformanceTracker()
        
        # Account storage
        self.accounts = {}  # account_id -> Account
        self.state_changes = []  # List[AccountStateChange]
        
        # Configuration
        self.max_accounts = self.config.get("max_accounts", 1000)
        self.state_change_history_limit = self.config.get("state_change_history_limit", 10000)
        
        logger.info("Account Manager initialized")
    
    def create_account(self, 
                      account_type: AccountType,
                      initial_capital: Decimal,
                      name: Optional[str] = None,
                      parent_account_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create new account.
        
        Args:
            account_type: Type of account to create
            initial_capital: Initial capital amount
            name: Optional account name
            parent_account_id: Optional parent account ID (for forked accounts)
            metadata: Optional metadata
            
        Returns:
            Account creation result
        """
        try:
            # Validate account type and capital
            config = self.account_type_manager.get_account_config(account_type)
            if not config:
                return {
                    "success": False,
                    "error": f"Invalid account type: {account_type}"
                }
            
            if initial_capital < config.min_capital:
                return {
                    "success": False,
                    "error": f"Initial capital ${float(initial_capital):,.2f} below minimum ${float(config.min_capital):,.2f}"
                }
            
            # Check account limits
            if len(self.accounts) >= self.max_accounts:
                return {
                    "success": False,
                    "error": f"Maximum accounts limit ({self.max_accounts}) reached"
                }
            
            # Generate account ID
            account_id = f"{account_type.value}_{uuid.uuid4().hex[:8]}"
            
            # Generate account name if not provided
            if not name:
                name = f"{config.name} #{len([a for a in self.accounts.values() if a.account_type == account_type]) + 1}"
            
            # Create account
            account = Account(
                account_id=account_id,
                account_type=account_type,
                account_state=AccountState.SAFE,  # Start in SAFE mode
                name=name,
                created_date=datetime.now(),
                initial_capital=initial_capital,
                current_value=initial_capital,
                available_capital=initial_capital,
                reserved_capital=Decimal("0"),
                parent_account_id=parent_account_id,
                child_account_ids=[],
                positions=[],
                performance_metrics={},
                last_updated=datetime.now(),
                metadata=metadata or {}
            )
            
            # Store account
            self.accounts[account_id] = account
            
            # Update parent account if applicable
            if parent_account_id and parent_account_id in self.accounts:
                parent_account = self.accounts[parent_account_id]
                parent_account.child_account_ids.append(account_id)
                parent_account.last_updated = datetime.now()
            
            # Initialize performance tracking
            self.performance_tracker.initialize_account_tracking(account_id, account_type, initial_capital)
            
            # Log account creation
            self.audit_manager.log_system_event(
                event_type="account_created",
                event_data={
                    "account_id": account_id,
                    "account_type": account_type.value,
                    "initial_capital": float(initial_capital),
                    "parent_account_id": parent_account_id,
                    "name": name
                },
                severity="info"
            )
            
            logger.info(f"Created account {account_id}: {name} ({account_type.value}) with ${float(initial_capital):,.2f}")
            
            return {
                "success": True,
                "account_id": account_id,
                "account": asdict(account),
                "creation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID."""
        return self.accounts.get(account_id)
    
    def update_account_value(self, 
                           account_id: str,
                           new_value: Decimal,
                           available_capital: Optional[Decimal] = None,
                           reserved_capital: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Update account value and capital allocation.
        
        Args:
            account_id: Account ID
            new_value: New account value
            available_capital: Optional available capital
            reserved_capital: Optional reserved capital
            
        Returns:
            Update result
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return {
                    "success": False,
                    "error": f"Account {account_id} not found"
                }
            
            previous_value = account.current_value
            
            # Update values
            account.current_value = new_value
            if available_capital is not None:
                account.available_capital = available_capital
            if reserved_capital is not None:
                account.reserved_capital = reserved_capital
            account.last_updated = datetime.now()
            
            # Update performance tracking
            self.performance_tracker.update_account_value(account_id, new_value)
            
            # Check for forking opportunity
            fork_check = self._check_forking_opportunity(account)
            
            # Validate account constraints
            validation_result = self._validate_account_state(account)
            
            # Log significant value changes
            value_change_pct = float((new_value - previous_value) / previous_value * 100) if previous_value > 0 else 0
            if abs(value_change_pct) >= 5.0:  # Log changes >= 5%
                self.audit_manager.log_system_event(
                    event_type="account_value_change",
                    event_data={
                        "account_id": account_id,
                        "previous_value": float(previous_value),
                        "new_value": float(new_value),
                        "change_pct": value_change_pct,
                        "available_capital": float(available_capital) if available_capital else None,
                        "reserved_capital": float(reserved_capital) if reserved_capital else None
                    },
                    severity="info" if abs(value_change_pct) < 10 else "warning"
                )
            
            return {
                "success": True,
                "account_id": account_id,
                "previous_value": float(previous_value),
                "new_value": float(new_value),
                "value_change_pct": value_change_pct,
                "fork_opportunity": fork_check,
                "validation_result": validation_result,
                "update_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating account value for {account_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id
            }
    
    def change_account_state(self, 
                           account_id: str,
                           new_state: AccountState,
                           reason: str,
                           triggered_by: str = "system") -> Dict[str, Any]:
        """
        Change account state.
        
        Args:
            account_id: Account ID
            new_state: New account state
            reason: Reason for state change
            triggered_by: Who/what triggered the change
            
        Returns:
            State change result
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return {
                    "success": False,
                    "error": f"Account {account_id} not found"
                }
            
            previous_state = account.account_state
            
            # Validate state transition
            if not self._is_valid_state_transition(previous_state, new_state):
                return {
                    "success": False,
                    "error": f"Invalid state transition from {previous_state.value} to {new_state.value}"
                }
            
            # Update account state
            account.account_state = new_state
            account.last_updated = datetime.now()
            
            # Create state change record
            state_change = AccountStateChange(
                change_id=f"state_{uuid.uuid4().hex[:8]}",
                account_id=account_id,
                timestamp=datetime.now(),
                from_state=previous_state,
                to_state=new_state,
                reason=reason,
                triggered_by=triggered_by,
                metadata={}
            )
            
            self.state_changes.append(state_change)
            
            # Trim state change history
            if len(self.state_changes) > self.state_change_history_limit:
                self.state_changes = self.state_changes[-self.state_change_history_limit:]
            
            # Log state change
            self.audit_manager.log_system_event(
                event_type="account_state_change",
                event_data=asdict(state_change),
                severity="info" if new_state != AccountState.ERROR else "error"
            )
            
            logger.info(f"Account {account_id} state changed: {previous_state.value} → {new_state.value} ({reason})")
            
            return {
                "success": True,
                "account_id": account_id,
                "previous_state": previous_state.value,
                "new_state": new_state.value,
                "reason": reason,
                "state_change_id": state_change.change_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error changing account state for {account_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id
            }
    
    def _is_valid_state_transition(self, from_state: AccountState, to_state: AccountState) -> bool:
        """Check if state transition is valid."""
        # Define valid state transitions
        valid_transitions = {
            AccountState.SAFE: [AccountState.ACTIVE, AccountState.SUSPENDED, AccountState.CLOSED],
            AccountState.ACTIVE: [AccountState.SAFE, AccountState.FORKING, AccountState.MERGING, AccountState.SUSPENDED, AccountState.ERROR],
            AccountState.FORKING: [AccountState.ACTIVE, AccountState.SAFE, AccountState.ERROR],
            AccountState.MERGING: [AccountState.ACTIVE, AccountState.SAFE, AccountState.CLOSED, AccountState.ERROR],
            AccountState.SUSPENDED: [AccountState.SAFE, AccountState.ACTIVE, AccountState.CLOSED],
            AccountState.CLOSED: [],  # No transitions from closed
            AccountState.ERROR: [AccountState.SAFE, AccountState.SUSPENDED, AccountState.CLOSED]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def _check_forking_opportunity(self, account: Account) -> Dict[str, Any]:
        """Check if account is eligible for forking."""
        try:
            can_fork = self.account_type_manager.can_fork(account.account_type, account.current_value)
            
            if can_fork:
                next_tier = self.account_type_manager.get_next_tier(account.account_type)
                fork_threshold = self.account_type_manager.get_fork_threshold(account.account_type)
                
                return {
                    "eligible": True,
                    "current_value": float(account.current_value),
                    "fork_threshold": float(fork_threshold),
                    "next_tier": next_tier.value if next_tier else None,
                    "excess_capital": float(account.current_value - fork_threshold)
                }
            else:
                return {
                    "eligible": False,
                    "reason": "Below fork threshold or forking disabled"
                }
                
        except Exception as e:
            logger.error(f"Error checking forking opportunity: {str(e)}")
            return {
                "eligible": False,
                "reason": f"Error in forking check: {str(e)}"
            }
    
    def _validate_account_state(self, account: Account) -> Dict[str, Any]:
        """Validate account against type constraints."""
        try:
            # Get position information (simplified - would integrate with position management)
            position_count = len(account.positions)
            largest_position_pct = Decimal("0")  # Would calculate from actual positions
            
            # Validate constraints
            validation_result = self.account_type_manager.validate_account_constraints(
                account.account_type,
                account.current_value,
                position_count,
                largest_position_pct
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating account state: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get comprehensive account summary."""
        try:
            account = self.get_account(account_id)
            if not account:
                return {
                    "success": False,
                    "error": f"Account {account_id} not found"
                }
            
            # Get account configuration
            config = self.account_type_manager.get_account_config(account.account_type)
            
            # Get performance metrics
            performance = self.performance_tracker.get_account_performance(account_id)
            
            # Get recent state changes
            recent_state_changes = [
                asdict(sc) for sc in self.state_changes
                if sc.account_id == account_id
            ][-10:]  # Last 10 state changes
            
            # Calculate utilization metrics
            capital_utilization = float(account.reserved_capital / account.current_value * 100) if account.current_value > 0 else 0
            position_utilization = len(account.positions) / config.max_positions * 100 if config else 0
            
            return {
                "success": True,
                "account": asdict(account),
                "account_config": asdict(config) if config else {},
                "performance_metrics": performance,
                "utilization_metrics": {
                    "capital_utilization_pct": capital_utilization,
                    "position_utilization_pct": position_utilization,
                    "available_capital": float(account.available_capital),
                    "reserved_capital": float(account.reserved_capital)
                },
                "recent_state_changes": recent_state_changes,
                "forking_status": self._check_forking_opportunity(account),
                "summary_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting account summary for {account_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id
            }
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[Account]:
        """Get all accounts of specified type."""
        return [account for account in self.accounts.values() if account.account_type == account_type]
    
    def get_accounts_by_state(self, account_state: AccountState) -> List[Account]:
        """Get all accounts in specified state."""
        return [account for account in self.accounts.values() if account.account_state == account_state]
    
    def get_account_hierarchy(self, account_id: str) -> Dict[str, Any]:
        """Get account hierarchy (parent and children)."""
        try:
            account = self.get_account(account_id)
            if not account:
                return {
                    "success": False,
                    "error": f"Account {account_id} not found"
                }
            
            # Get parent account
            parent_account = None
            if account.parent_account_id:
                parent_account = self.get_account(account.parent_account_id)
            
            # Get child accounts
            child_accounts = []
            for child_id in account.child_account_ids:
                child_account = self.get_account(child_id)
                if child_account:
                    child_accounts.append(child_account)
            
            return {
                "success": True,
                "account": asdict(account),
                "parent_account": asdict(parent_account) if parent_account else None,
                "child_accounts": [asdict(child) for child in child_accounts],
                "hierarchy_depth": self._calculate_hierarchy_depth(account_id),
                "total_hierarchy_value": self._calculate_total_hierarchy_value(account_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting account hierarchy for {account_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id
            }
    
    def _calculate_hierarchy_depth(self, account_id: str, visited: Optional[set] = None) -> int:
        """Calculate depth of account hierarchy."""
        if visited is None:
            visited = set()
        
        if account_id in visited:
            return 0  # Prevent infinite recursion
        
        visited.add(account_id)
        account = self.get_account(account_id)
        
        if not account or not account.child_account_ids:
            return 1
        
        max_child_depth = 0
        for child_id in account.child_account_ids:
            child_depth = self._calculate_hierarchy_depth(child_id, visited.copy())
            max_child_depth = max(max_child_depth, child_depth)
        
        return 1 + max_child_depth
    
    def _calculate_total_hierarchy_value(self, account_id: str, visited: Optional[set] = None) -> Decimal:
        """Calculate total value of account hierarchy."""
        if visited is None:
            visited = set()
        
        if account_id in visited:
            return Decimal("0")  # Prevent infinite recursion
        
        visited.add(account_id)
        account = self.get_account(account_id)
        
        if not account:
            return Decimal("0")
        
        total_value = account.current_value
        
        for child_id in account.child_account_ids:
            child_value = self._calculate_total_hierarchy_value(child_id, visited.copy())
            total_value += child_value
        
        return total_value
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall account management system status."""
        try:
            # Account type breakdown
            type_breakdown = {}
            state_breakdown = {}
            
            for account in self.accounts.values():
                # Type breakdown
                account_type = account.account_type.value
                type_breakdown[account_type] = type_breakdown.get(account_type, 0) + 1
                
                # State breakdown
                account_state = account.account_state.value
                state_breakdown[account_state] = state_breakdown.get(account_state, 0) + 1
            
            # Calculate total values
            total_value = sum(account.current_value for account in self.accounts.values())
            total_available = sum(account.available_capital for account in self.accounts.values())
            total_reserved = sum(account.reserved_capital for account in self.accounts.values())
            
            # Recent activity
            recent_state_changes = len([
                sc for sc in self.state_changes
                if (datetime.now() - sc.timestamp).total_seconds() < 3600  # Last hour
            ])
            
            return {
                "total_accounts": len(self.accounts),
                "account_type_breakdown": type_breakdown,
                "account_state_breakdown": state_breakdown,
                "total_system_value": float(total_value),
                "total_available_capital": float(total_available),
                "total_reserved_capital": float(total_reserved),
                "capital_utilization_pct": float(total_reserved / total_value * 100) if total_value > 0 else 0,
                "recent_state_changes": recent_state_changes,
                "system_health": "healthy" if len([a for a in self.accounts.values() if a.account_state == AccountState.ERROR]) == 0 else "degraded",
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }

