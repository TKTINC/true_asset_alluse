"""
Predictive Analytics Module - WS8 ML Intelligence

This module implements predictive analytics capabilities for forecasting
market conditions, performance patterns, and system behavior.

ADVISORY ONLY: All predictive analytics provide insights and forecasts
but do not make wealth management decisions.
"""

from .predictive_engine import PredictiveAnalyticsEngine, PredictionType, Prediction, Forecast

__all__ = [
    'PredictiveAnalyticsEngine',
    'PredictionType',
    'Prediction', 
    'Forecast'
]

