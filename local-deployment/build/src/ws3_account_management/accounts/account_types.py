"""
Account Types and States

This module defines the three-tiered account structure and states
as specified in Constitution v1.3 §1.Account-Types.
"""

from enum import Enum, IntEnum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, getcontext
import logging

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class AccountType(Enum):
    """
    Three-tiered account structure as defined in Constitution v1.3.
    
    Gen-Acc: Generation Account (starting account)
    Rev-Acc: Revenue Account (forked from Gen-Acc at $100K)
    Com-Acc: Commercial Account (forked from Rev-Acc at $500K)
    """
    GEN_ACC = "gen_acc"     # Generation Account
    REV_ACC = "rev_acc"     # Revenue Account  
    COM_ACC = "com_acc"     # Commercial Account


class AccountState(Enum):
    """Account operational states."""
    SAFE = "safe"                   # SAFE mode (no trading)
    ACTIVE = "active"               # Active trading
    FORKING = "forking"             # In process of forking
    MERGING = "merging"             # In process of merging
    SUSPENDED = "suspended"         # Temporarily suspended
    CLOSED = "closed"               # Permanently closed
    ERROR = "error"                 # Error state


class AccountTier(IntEnum):
    """Account tier hierarchy for forking logic."""
    GENERATION = 1      # Gen-Acc (Tier 1)
    REVENUE = 2         # Rev-Acc (Tier 2)
    COMMERCIAL = 3      # Com-Acc (Tier 3)


@dataclass
class AccountConfig:
    """Configuration for account type."""
    account_type: AccountType
    tier: AccountTier
    name: str
    description: str
    min_capital: Decimal
    fork_threshold: Optional[Decimal]
    max_positions: int
    max_position_size_pct: Decimal
    risk_multiplier: Decimal
    protocol_sensitivity: Decimal
    hedging_enabled: bool
    llms_allocation_pct: Decimal
    auto_fork_enabled: bool
    merge_back_enabled: bool
    special_rules: Dict[str, Any]


class AccountTypeManager:
    """Manager for account type configurations and rules."""
    
    def __init__(self):
        """Initialize account type manager."""
        self.account_configs = self._initialize_account_configs()
        
    def _initialize_account_configs(self) -> Dict[AccountType, AccountConfig]:
        """Initialize account type configurations per Constitution v1.3."""
        return {
            AccountType.GEN_ACC: AccountConfig(
                account_type=AccountType.GEN_ACC,
                tier=AccountTier.GENERATION,
                name="Generation Account",
                description="Starting account for new capital deployment",
                min_capital=Decimal("10000"),      # $10K minimum
                fork_threshold=Decimal("100000"),  # Fork at $100K
                max_positions=10,                  # Maximum 10 positions
                max_position_size_pct=Decimal("0.15"),  # 15% max position size
                risk_multiplier=Decimal("1.0"),    # Standard risk
                protocol_sensitivity=Decimal("1.0"), # Standard protocol sensitivity
                hedging_enabled=True,
                llms_allocation_pct=Decimal("0.25"), # 25% to LLMS
                auto_fork_enabled=True,
                merge_back_enabled=True,
                special_rules={
                    "new_trader_protection": True,
                    "conservative_sizing": True,
                    "enhanced_monitoring": True
                }
            ),
            
            AccountType.REV_ACC: AccountConfig(
                account_type=AccountType.REV_ACC,
                tier=AccountTier.REVENUE,
                name="Revenue Account",
                description="Intermediate account forked from Gen-Acc at $100K",
                min_capital=Decimal("100000"),     # $100K minimum (fork threshold)
                fork_threshold=Decimal("500000"),  # Fork at $500K
                max_positions=20,                  # Maximum 20 positions
                max_position_size_pct=Decimal("0.20"),  # 20% max position size
                risk_multiplier=Decimal("1.2"),    # 20% higher risk tolerance
                protocol_sensitivity=Decimal("0.9"), # Slightly less sensitive
                hedging_enabled=True,
                llms_allocation_pct=Decimal("0.25"), # 25% to LLMS
                auto_fork_enabled=True,
                merge_back_enabled=True,
                special_rules={
                    "intermediate_scaling": True,
                    "enhanced_roll_frequency": True,
                    "moderate_risk_tolerance": True
                }
            ),
            
            AccountType.COM_ACC: AccountConfig(
                account_type=AccountType.COM_ACC,
                tier=AccountTier.COMMERCIAL,
                name="Commercial Account",
                description="Advanced account forked from Rev-Acc at $500K",
                min_capital=Decimal("500000"),     # $500K minimum (fork threshold)
                fork_threshold=None,               # No further forking
                max_positions=50,                  # Maximum 50 positions
                max_position_size_pct=Decimal("0.25"),  # 25% max position size
                risk_multiplier=Decimal("1.5"),    # 50% higher risk tolerance
                protocol_sensitivity=Decimal("0.8"), # Less sensitive to protocol changes
                hedging_enabled=True,
                llms_allocation_pct=Decimal("0.25"), # 25% to LLMS
                auto_fork_enabled=False,           # No further auto-forking
                merge_back_enabled=False,          # No merging back
                special_rules={
                    "commercial_scaling": True,
                    "advanced_strategies": True,
                    "maximum_risk_tolerance": True,
                    "institutional_features": True
                }
            )
        }
    
    def get_account_config(self, account_type: AccountType) -> AccountConfig:
        """Get configuration for account type."""
        return self.account_configs.get(account_type)
    
    def get_fork_threshold(self, account_type: AccountType) -> Optional[Decimal]:
        """Get fork threshold for account type."""
        config = self.get_account_config(account_type)
        return config.fork_threshold if config else None
    
    def can_fork(self, account_type: AccountType, current_value: Decimal) -> bool:
        """Check if account can fork based on value and type."""
        config = self.get_account_config(account_type)
        
        if not config or not config.auto_fork_enabled:
            return False
        
        fork_threshold = config.fork_threshold
        if not fork_threshold:
            return False
        
        return current_value >= fork_threshold
    
    def get_next_tier(self, account_type: AccountType) -> Optional[AccountType]:
        """Get next tier account type for forking."""
        tier_map = {
            AccountType.GEN_ACC: AccountType.REV_ACC,
            AccountType.REV_ACC: AccountType.COM_ACC,
            AccountType.COM_ACC: None  # No further forking
        }
        return tier_map.get(account_type)
    
    def get_risk_parameters(self, account_type: AccountType) -> Dict[str, Any]:
        """Get risk parameters for account type."""
        config = self.get_account_config(account_type)
        
        if not config:
            return {}
        
        return {
            "max_positions": config.max_positions,
            "max_position_size_pct": float(config.max_position_size_pct),
            "risk_multiplier": float(config.risk_multiplier),
            "protocol_sensitivity": float(config.protocol_sensitivity),
            "hedging_enabled": config.hedging_enabled,
            "llms_allocation_pct": float(config.llms_allocation_pct)
        }
    
    def validate_account_constraints(self, 
                                   account_type: AccountType,
                                   account_value: Decimal,
                                   position_count: int,
                                   largest_position_pct: Decimal) -> Dict[str, Any]:
        """Validate account against type constraints."""
        try:
            config = self.get_account_config(account_type)
            
            if not config:
                return {
                    "valid": False,
                    "errors": [f"Unknown account type: {account_type}"]
                }
            
            errors = []
            warnings = []
            
            # Check minimum capital
            if account_value < config.min_capital:
                errors.append(f"Account value ${float(account_value):,.2f} below minimum ${float(config.min_capital):,.2f}")
            
            # Check position count
            if position_count > config.max_positions:
                errors.append(f"Position count {position_count} exceeds maximum {config.max_positions}")
            
            # Check position size
            if largest_position_pct > config.max_position_size_pct:
                errors.append(f"Largest position {float(largest_position_pct)*100:.1f}% exceeds maximum {float(config.max_position_size_pct)*100:.1f}%")
            
            # Check for fork opportunity
            fork_threshold = config.fork_threshold
            if fork_threshold and account_value >= fork_threshold and config.auto_fork_enabled:
                warnings.append(f"Account eligible for forking to {self.get_next_tier(account_type).value}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "account_config": {
                    "type": account_type.value,
                    "tier": config.tier.value,
                    "name": config.name,
                    "min_capital": float(config.min_capital),
                    "fork_threshold": float(fork_threshold) if fork_threshold else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating account constraints: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    def get_account_type_summary(self) -> Dict[str, Any]:
        """Get summary of all account types."""
        return {
            account_type.value: {
                "tier": config.tier.value,
                "name": config.name,
                "description": config.description,
                "min_capital": float(config.min_capital),
                "fork_threshold": float(config.fork_threshold) if config.fork_threshold else None,
                "max_positions": config.max_positions,
                "max_position_size_pct": float(config.max_position_size_pct),
                "risk_multiplier": float(config.risk_multiplier),
                "auto_fork_enabled": config.auto_fork_enabled,
                "special_features": list(config.special_rules.keys())
            }
            for account_type, config in self.account_configs.items()
        }
    
    def calculate_optimal_account_type(self, 
                                     current_value: Decimal,
                                     risk_tolerance: str = "medium") -> Dict[str, Any]:
        """Calculate optimal account type based on current value and risk tolerance."""
        try:
            # Risk tolerance multipliers
            risk_multipliers = {
                "conservative": 0.8,
                "medium": 1.0,
                "aggressive": 1.2
            }
            
            risk_mult = Decimal(str(risk_multipliers.get(risk_tolerance, 1.0)))
            
            # Find appropriate account type based on value
            if current_value >= Decimal("500000") * risk_mult:
                optimal_type = AccountType.COM_ACC
                confidence = 0.9
                reason = "Value supports Commercial Account operations"
            elif current_value >= Decimal("100000") * risk_mult:
                optimal_type = AccountType.REV_ACC
                confidence = 0.8
                reason = "Value supports Revenue Account operations"
            else:
                optimal_type = AccountType.GEN_ACC
                confidence = 0.7
                reason = "Starting with Generation Account"
            
            config = self.get_account_config(optimal_type)
            
            return {
                "optimal_account_type": optimal_type.value,
                "confidence": confidence,
                "reason": reason,
                "account_details": {
                    "name": config.name,
                    "tier": config.tier.value,
                    "min_capital": float(config.min_capital),
                    "max_positions": config.max_positions,
                    "risk_multiplier": float(config.risk_multiplier)
                },
                "next_milestone": {
                    "threshold": float(config.fork_threshold) if config.fork_threshold else None,
                    "next_tier": self.get_next_tier(optimal_type).value if self.get_next_tier(optimal_type) else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimal account type: {str(e)}", exc_info=True)
            return {
                "optimal_account_type": AccountType.GEN_ACC.value,
                "confidence": 0.5,
                "reason": f"Error in calculation: {str(e)}",
                "account_details": {},
                "next_milestone": {}
            }

