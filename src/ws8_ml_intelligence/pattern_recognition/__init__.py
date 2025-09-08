"""
Pattern Recognition Module - WS8 ML Intelligence

This module implements pattern recognition capabilities for identifying
market patterns, trading patterns, and system behavior patterns.

ADVISORY ONLY: All pattern recognition provides insights and recommendations
but does not make wealth management decisions.
"""

from .pattern_engine import PatternRecognitionEngine, PatternType, Pattern, PatternMatch

__all__ = [
    'PatternRecognitionEngine',
    'PatternType', 
    'Pattern',
    'PatternMatch'
]

