"""
Account Management & Forking System (WS3)

This module implements the three-tiered account structure (Gen/Rev/Com) and
intelligent forking system that creates Mini ALL-USE systems based on
account performance and capital thresholds.
"""

from .accounts import AccountManager, AccountType, AccountState
from .forking import ForkingEngine, ForkingDecisionEngine
from .merging import MergingEngine, ConsolidationEngine
from .performance import PerformanceAttributionSystem

__all__ = [
    "AccountManager",
    "AccountType", 
    "AccountState",
    "ForkingEngine",
    "ForkingDecisionEngine",
    "MergingEngine",
    "ConsolidationEngine",
    "PerformanceAttributionSystem"
]

