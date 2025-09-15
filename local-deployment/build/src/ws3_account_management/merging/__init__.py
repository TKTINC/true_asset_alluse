"""
Account Merging & Consolidation

This module implements the intelligent account merging system that
consolidates accounts when beneficial for performance, risk management,
or operational efficiency.
"""

from .merging_engine import MergingEngine
from .consolidation_engine import ConsolidationEngine
from .merge_validator import MergeValidator
from .conflict_resolver import ConflictResolver

__all__ = [
    "MergingEngine",
    "ConsolidationEngine",
    "MergeValidator", 
    "ConflictResolver"
]

