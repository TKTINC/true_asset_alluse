"""
WS8: Machine Learning & Intelligence Engine

This workstream implements the adaptive learning and intelligence system
for the True-Asset-ALLUSE wealth management autopilot system.

Components:
- Learning Engine: Learns from historical patterns and week types
- Anomaly Detection: Identifies unusual market behavior and system anomalies
- Pattern Recognition: Recognizes market patterns and conditions
- Predictive Analytics: Provides predictive insights for decision making

Mission: "Autopilot for Wealth.....Engineered for compounding income and corpus"

IMPORTANT: This ML system provides ADVISORY insights only. All wealth management
decisions remain 100% rules-based per Constitution v1.3. ML provides intelligence
to enhance understanding, not to make decisions.
"""

from .learning_engine.adaptive_learning_engine import (
    AdaptiveLearningEngine, LearningData, LearningInsight, LearningMode
)
from .anomaly_detection.market_anomaly_detector import (
    MarketAnomalyDetector, AnomalyAlert, AnomalyType, AnomalySeverity
)
from .pattern_recognition.pattern_engine import (
    PatternRecognitionEngine, Pattern, PatternMatch, PatternType
)
from .predictive_analytics.predictive_engine import (
    PredictiveAnalyticsEngine, Prediction, Forecast, PredictionType
)
from .intelligence_coordinator import (
    IntelligenceCoordinator, IntelligenceReport, SystemIntelligence, IntelligenceMode
)

__all__ = [
    # Core engines
    'AdaptiveLearningEngine',
    'MarketAnomalyDetector', 
    'PatternRecognitionEngine',
    'PredictiveAnalyticsEngine',
    'IntelligenceCoordinator',
    
    # Data structures
    'LearningData',
    'LearningInsight',
    'AnomalyAlert',
    'Pattern',
    'PatternMatch',
    'Prediction',
    'Forecast',
    'IntelligenceReport',
    'SystemIntelligence',
    
    # Enums
    'LearningMode',
    'AnomalyType',
    'AnomalySeverity',
    'PatternType',
    'PredictionType',
    'IntelligenceMode'
]

