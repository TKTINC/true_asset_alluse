"""
ATR Calculation Engine

This module implements the ATR (Average True Range) calculation engine
with multiple data sources and fallback mechanisms for robust risk management.
"""

from .atr_engine import ATRCalculationEngine
from .data_sources import ATRDataSource, YahooFinanceSource, AlphaVantageSource, IEXCloudSource
from .atr_calculator import ATRCalculator
from .data_validator import ATRDataValidator

__all__ = [
    "ATRCalculationEngine",
    "ATRDataSource",
    "YahooFinanceSource", 
    "AlphaVantageSource",
    "IEXCloudSource",
    "ATRCalculator",
    "ATRDataValidator"
]

