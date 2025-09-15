"""
WS1: Rules Engine & Constitution Framework

This workstream implements the core rules engine that enforces Constitution v1.3
with 100% deterministic rule execution. No AI wealth management decisions are made here -
only rule validation, compliance checking, and audit trail generation.

Components:
- Constitution v1.3 parser and rule engine
- Trading rule validation system
- Position sizing calculator (95-100% capital deployment)
- Compliance audit trail system
- Rule violation detection and prevention

All wealth management decisions are deterministic and traceable to specific Constitution sections.
"""

from .constitution import ConstitutionV13
from .rules_engine import RulesEngine
from .validators import (
    AccountTypeValidator,
    PositionSizeValidator,
    TimingValidator,
    DeltaRangeValidator,
    LiquidityValidator
)
from .audit import AuditTrailManager
from .compliance import ComplianceChecker

__all__ = [
    "ConstitutionV13",
    "RulesEngine", 
    "AccountTypeValidator",
    "PositionSizeValidator",
    "TimingValidator",
    "DeltaRangeValidator",
    "LiquidityValidator",
    "AuditTrailManager",
    "ComplianceChecker"
]

