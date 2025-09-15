"""
Predictive Analytics Engine - ML Intelligence System

This module implements predictive analytics for forecasting market conditions,
performance patterns, and system behavior to provide forward-looking insights.

IMPORTANT: This system provides ADVISORY forecasts only. All wealth management
decisions remain 100% rules-based per Constitution v1.3.

Mission: "Autopilot for Wealth.....Engineered for compounding income and corpus"
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from src.ws1_rules_engine.constitution.week_classification import WeekType, WeekPerformance
from src.ws1_rules_engine.audit import AuditTrailManager

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions that can be made."""
    WEEKLY_PERFORMANCE = "weekly_performance"
    MARKET_VOLATILITY = "market_volatility"
    WEEK_TYPE_FORECAST = "week_type_forecast"
    RISK_LEVEL_FORECAST = "risk_level_forecast"
    PROTOCOL_ESCALATION = "protocol_escalation"
    PORTFOLIO_DRAWDOWN = "portfolio_drawdown"
    MARKET_REGIME_CHANGE = "market_regime_change"
    SEASONAL_PERFORMANCE = "seasonal_performance"


@dataclass
class Prediction:
    """A single prediction."""
    prediction_type: PredictionType
    predicted_value: float
    confidence: float
    prediction_horizon: timedelta
    features_used: List[str]
    model_accuracy: float
    created_at: datetime
    valid_until: datetime


@dataclass
class Forecast:
    """A forecast containing multiple predictions."""
    forecast_id: str
    forecast_name: str
    predictions: List[Prediction]
    forecast_horizon: timedelta
    overall_confidence: float
    key_assumptions: List[str]
    risk_factors: List[str]
    created_at: datetime
    updated_at: datetime


class PredictiveAnalyticsEngine:
    """
    Predictive analytics system that forecasts market conditions, performance,
    and system behavior based on historical patterns and current conditions.
    
    ADVISORY ONLY: Provides forecasts and predictions but does not make
    any wealth management decisions. All decisions remain rules-based.
    """
    
    def __init__(self,
                 audit_manager: AuditTrailManager,
                 prediction_horizon_days: int = 7,
                 min_training_samples: int = 100):
        """Initialize the predictive analytics engine."""
        self.audit_manager = audit_manager
        self.prediction_horizon_days = prediction_horizon_days
        self.min_training_samples = min_training_samples
        
        # Prediction models
        self.models: Dict[PredictionType, Any] = {}
        self.scalers: Dict[PredictionType, StandardScaler] = {}
        self.model_metrics: Dict[PredictionType, Dict[str, float]] = {}
        
        # Historical data for training
        self.training_data: List[Dict[str, Any]] = []
        
        # Forecasts storage
        self.active_forecasts: List[Forecast] = []
        self.forecast_counter = 0
        
        # Feature definitions
        self.feature_definitions = self._define_features()
        
        # Initialize models
        self._initialize_models()
        
        logger.info("PredictiveAnalyticsEngine initialized successfully")
    
    def _define_features(self) -> Dict[PredictionType, List[str]]:
        """Define features for each prediction type."""
        return {
            PredictionType.WEEKLY_PERFORMANCE: [
                'market_return_1w', 'market_return_4w', 'market_volatility',
                'vix_level', 'vix_change', 'sector_rotation', 'earnings_density',
                'options_expiration', 'week_type_encoded', 'seasonal_factor'
            ],
            PredictionType.MARKET_VOLATILITY: [
                'current_volatility', 'volatility_ma_5d', 'volatility_ma_20d',
                'vix_level', 'vix_term_structure', 'market_stress_index',
                'correlation_level', 'volume_ratio', 'options_activity'
            ],
            PredictionType.WEEK_TYPE_FORECAST: [
                'market_volatility', 'earnings_density', 'options_expiration',
                'economic_events', 'holiday_proximity', 'fomc_proximity',
                'seasonal_factor', 'market_momentum', 'sector_dispersion'
            ],
            PredictionType.RISK_LEVEL_FORECAST: [
                'portfolio_volatility', 'market_correlation', 'concentration_risk',
                'liquidity_conditions', 'market_stress_index', 'vix_level',
                'portfolio_beta', 'sector_exposure', 'position_sizes'
            ],
            PredictionType.PROTOCOL_ESCALATION: [
                'current_protocol_level', 'portfolio_drawdown', 'market_stress',
                'volatility_regime', 'liquidity_conditions', 'correlation_breakdown',
                'time_in_current_level', 'recent_escalations', 'system_performance'
            ],
            PredictionType.PORTFOLIO_DRAWDOWN: [
                'current_drawdown', 'portfolio_volatility', 'market_correlation',
                'concentration_risk', 'market_stress_index', 'vix_level',
                'portfolio_beta', 'position_count', 'capital_utilization'
            ],
            PredictionType.MARKET_REGIME_CHANGE: [
                'market_volatility', 'volatility_trend', 'correlation_level',
                'correlation_trend', 'vix_level', 'vix_trend', 'yield_curve_slope',
                'credit_spreads', 'sector_rotation', 'momentum_factor'
            ],
            PredictionType.SEASONAL_PERFORMANCE: [
                'month', 'quarter', 'week_of_year', 'day_of_week',
                'historical_seasonal_return', 'market_volatility',
                'earnings_season', 'holiday_effect', 'year_end_effect'
            ]
        }
    
    def _initialize_models(self):
        """Initialize prediction models."""
        for prediction_type in PredictionType:
            # Use different models for different prediction types
            if prediction_type in [PredictionType.WEEK_TYPE_FORECAST, PredictionType.PROTOCOL_ESCALATION]:
                # Classification tasks
                from sklearn.ensemble import RandomForestClassifier
                self.models[prediction_type] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                # Regression tasks - use Gradient Boosting for better performance
                self.models[prediction_type] = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            
            # Initialize scaler
            self.scalers[prediction_type] = StandardScaler()
            
            # Initialize metrics
            self.model_metrics[prediction_type] = {
                'accuracy': 0.0,
                'mse': 0.0,
                'mae': 0.0,
                'r2': 0.0,
                'training_samples': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def add_training_data(self, data: Dict[str, Any]):
        """Add training data for model improvement."""
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow()
            
            self.training_data.append(data)
            
            # Trigger model retraining if we have enough data
            if len(self.training_data) % 50 == 0:  # Every 50 data points
                await self._retrain_models()
            
            # Log the data addition
            await self.audit_manager.log_event(
                event_type="PREDICTIVE_TRAINING_DATA_ADDED",
                details={
                    'timestamp': data['timestamp'].isoformat(),
                    'data_keys': list(data.keys())
                },
                metadata={'training_data_count': len(self.training_data)}
            )
            
        except Exception as e:
            logger.error(f"Error adding training data: {str(e)}")
    
    async def _retrain_models(self):
        """Retrain all prediction models."""
        try:
            for prediction_type in PredictionType:
                await self._train_model(prediction_type)
            
            logger.info("Model retraining completed successfully")
            
        except Exception as e:
            logger.error(f"Error retraining models: {str(e)}")
    
    async def _train_model(self, prediction_type: PredictionType):
        """Train a specific prediction model."""
        try:
            if len(self.training_data) < self.min_training_samples:
                return
            
            # Prepare training data
            X, y = self._prepare_training_data(prediction_type)
            
            if len(X) == 0:
                return
            
            # Use time series split for validation
            tscv = TimeSeriesSplit(n_splits=3)
            
            # Scale features
            X_scaled = self.scalers[prediction_type].fit_transform(X)
            
            # Train model
            self.models[prediction_type].fit(X_scaled, y)
            
            # Cross-validation for performance metrics
            cv_scores = cross_val_score(
                self.models[prediction_type], X_scaled, y, 
                cv=tscv, scoring='neg_mean_squared_error'
            )
            
            # Calculate metrics
            y_pred = self.models[prediction_type].predict(X_scaled)
            
            if prediction_type in [PredictionType.WEEK_TYPE_FORECAST, PredictionType.PROTOCOL_ESCALATION]:
                # Classification metrics
                from sklearn.metrics import accuracy_score
                accuracy = accuracy_score(y, y_pred.round())
                mse = mean_squared_error(y, y_pred)
                mae = mean_absolute_error(y, y_pred)
                r2 = 0.0  # Not applicable for classification
            else:
                # Regression metrics
                accuracy = 0.0  # Not applicable for regression
                mse = mean_squared_error(y, y_pred)
                mae = mean_absolute_error(y, y_pred)
                r2 = r2_score(y, y_pred)
            
            # Update metrics
            self.model_metrics[prediction_type] = {
                'accuracy': accuracy,
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'cv_score': -cv_scores.mean(),
                'training_samples': len(X),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Model {prediction_type.value} trained with {len(X)} samples")
            
        except Exception as e:
            logger.error(f"Error training model {prediction_type.value}: {str(e)}")
    
    def _prepare_training_data(self, prediction_type: PredictionType) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for a specific prediction type."""
        try:
            feature_names = self.feature_definitions[prediction_type]
            
            # Convert training data to DataFrame
            data_rows = []
            for data in self.training_data:
                row = {}
                
                # Extract features
                for feature in feature_names:
                    if feature in data:
                        row[feature] = data[feature]
                    elif feature == 'week_type_encoded':
                        row[feature] = self._encode_week_type(data.get('week_type'))
                    elif feature == 'seasonal_factor':
                        row[feature] = self._calculate_seasonal_factor(data.get('timestamp'))
                    elif feature.startswith('market_return_'):
                        # Handle different return periods
                        period = feature.split('_')[-1]
                        row[feature] = data.get(f'market_return_{period}', 0.0)
                    else:
                        row[feature] = 0.0  # Default value
                
                # Extract target variable
                if prediction_type == PredictionType.WEEKLY_PERFORMANCE:
                    row['target'] = data.get('weekly_return', 0.0)
                elif prediction_type == PredictionType.MARKET_VOLATILITY:
                    row['target'] = data.get('future_volatility', data.get('market_volatility', 0.0))
                elif prediction_type == PredictionType.WEEK_TYPE_FORECAST:
                    row['target'] = self._encode_week_type(data.get('future_week_type'))
                elif prediction_type == PredictionType.RISK_LEVEL_FORECAST:
                    row['target'] = data.get('future_risk_level', 0.0)
                elif prediction_type == PredictionType.PROTOCOL_ESCALATION:
                    row['target'] = data.get('protocol_escalated', 0)
                elif prediction_type == PredictionType.PORTFOLIO_DRAWDOWN:
                    row['target'] = data.get('future_drawdown', 0.0)
                elif prediction_type == PredictionType.MARKET_REGIME_CHANGE:
                    row['target'] = data.get('regime_changed', 0)
                elif prediction_type == PredictionType.SEASONAL_PERFORMANCE:
                    row['target'] = data.get('seasonal_return', 0.0)
                
                data_rows.append(row)
            
            if not data_rows:
                return np.array([]), np.array([])
            
            df = pd.DataFrame(data_rows)
            
            # Separate features and target
            X = df[feature_names].fillna(0).values
            y = df['target'].fillna(0).values
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing training data for {prediction_type.value}: {str(e)}")
            return np.array([]), np.array([])
    
    def _encode_week_type(self, week_type) -> int:
        """Encode week type as integer."""
        if isinstance(week_type, WeekType):
            encoding = {
                WeekType.NORMAL: 0,
                WeekType.VOLATILE: 1,
                WeekType.TRENDING: 2,
                WeekType.CONSOLIDATION: 3,
                WeekType.EARNINGS: 4,
                WeekType.EXPIRATION: 5,
                WeekType.HOLIDAY: 6,
                WeekType.EVENT_DRIVEN: 7,
                WeekType.CRISIS: 8,
                WeekType.RECOVERY: 9
            }
            return encoding.get(week_type, 0)
        return 0
    
    def _calculate_seasonal_factor(self, timestamp: Optional[datetime]) -> float:
        """Calculate seasonal factor based on timestamp."""
        if not timestamp:
            return 0.0
        
        # Simple seasonal factor based on month
        seasonal_factors = {
            1: 0.1,   # January effect
            2: -0.05, # February
            3: 0.05,  # March
            4: 0.02,  # April  
            5: -0.02, # May (sell in May)
            6: -0.05, # June
            7: 0.0,   # July
            8: -0.1,  # August
            9: -0.05, # September
            10: 0.05, # October
            11: 0.1,  # November
            12: 0.15  # December (Santa rally)
        }
        
        return seasonal_factors.get(timestamp.month, 0.0)
    
    async def make_prediction(self,
                            prediction_type: PredictionType,
                            current_data: Dict[str, Any],
                            horizon_days: Optional[int] = None) -> Optional[Prediction]:
        """Make a single prediction."""
        try:
            if prediction_type not in self.models:
                return None
            
            # Check if model is trained
            if self.model_metrics[prediction_type]['training_samples'] < self.min_training_samples:
                return None
            
            # Prepare features
            features = self._prepare_prediction_features(prediction_type, current_data)
            
            if not features:
                return None
            
            # Scale features
            features_array = np.array([list(features.values())])
            features_scaled = self.scalers[prediction_type].transform(features_array)
            
            # Make prediction
            predicted_value = self.models[prediction_type].predict(features_scaled)[0]
            
            # Calculate confidence based on model performance
            model_metrics = self.model_metrics[prediction_type]
            if prediction_type in [PredictionType.WEEK_TYPE_FORECAST, PredictionType.PROTOCOL_ESCALATION]:
                confidence = model_metrics['accuracy']
            else:
                confidence = max(0.0, model_metrics['r2'])
            
            # Determine prediction horizon
            if horizon_days is None:
                horizon_days = self.prediction_horizon_days
            
            prediction = Prediction(
                prediction_type=prediction_type,
                predicted_value=float(predicted_value),
                confidence=confidence,
                prediction_horizon=timedelta(days=horizon_days),
                features_used=list(features.keys()),
                model_accuracy=confidence,
                created_at=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=horizon_days)
            )
            
            # Log the prediction
            await self.audit_manager.log_event(
                event_type="PREDICTION_MADE",
                details={
                    'prediction_type': prediction_type.value,
                    'predicted_value': predicted_value,
                    'confidence': confidence,
                    'horizon_days': horizon_days
                },
                metadata={'features_used': list(features.keys())}
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction for {prediction_type.value}: {str(e)}")
            return None
    
    def _prepare_prediction_features(self,
                                   prediction_type: PredictionType,
                                   current_data: Dict[str, Any]) -> Dict[str, float]:
        """Prepare features for prediction."""
        try:
            feature_names = self.feature_definitions[prediction_type]
            features = {}
            
            for feature in feature_names:
                if feature in current_data:
                    features[feature] = float(current_data[feature])
                elif feature == 'week_type_encoded':
                    features[feature] = float(self._encode_week_type(current_data.get('week_type')))
                elif feature == 'seasonal_factor':
                    features[feature] = self._calculate_seasonal_factor(current_data.get('timestamp'))
                elif feature.startswith('current_'):
                    # Handle current_ prefixed features
                    base_feature = feature.replace('current_', '')
                    features[feature] = float(current_data.get(base_feature, 0.0))
                else:
                    features[feature] = 0.0  # Default value
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing prediction features: {str(e)}")
            return {}
    
    async def create_forecast(self,
                            forecast_name: str,
                            current_data: Dict[str, Any],
                            prediction_types: Optional[List[PredictionType]] = None,
                            horizon_days: Optional[int] = None) -> Optional[Forecast]:
        """Create a comprehensive forecast."""
        try:
            if prediction_types is None:
                prediction_types = list(PredictionType)
            
            if horizon_days is None:
                horizon_days = self.prediction_horizon_days
            
            # Make predictions
            predictions = []
            for pred_type in prediction_types:
                prediction = await self.make_prediction(pred_type, current_data, horizon_days)
                if prediction:
                    predictions.append(prediction)
            
            if not predictions:
                return None
            
            # Calculate overall confidence
            overall_confidence = sum(p.confidence for p in predictions) / len(predictions)
            
            # Generate key assumptions
            key_assumptions = self._generate_key_assumptions(current_data, predictions)
            
            # Generate risk factors
            risk_factors = self._generate_risk_factors(current_data, predictions)
            
            # Create forecast
            self.forecast_counter += 1
            forecast = Forecast(
                forecast_id=f"forecast_{self.forecast_counter}_{int(datetime.utcnow().timestamp())}",
                forecast_name=forecast_name,
                predictions=predictions,
                forecast_horizon=timedelta(days=horizon_days),
                overall_confidence=overall_confidence,
                key_assumptions=key_assumptions,
                risk_factors=risk_factors,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store forecast
            self.active_forecasts.append(forecast)
            
            # Keep only recent forecasts
            cutoff_time = datetime.utcnow() - timedelta(days=30)
            self.active_forecasts = [
                f for f in self.active_forecasts
                if f.created_at >= cutoff_time
            ]
            
            # Log forecast creation
            await self.audit_manager.log_event(
                event_type="FORECAST_CREATED",
                details={
                    'forecast_id': forecast.forecast_id,
                    'forecast_name': forecast_name,
                    'prediction_count': len(predictions),
                    'overall_confidence': overall_confidence,
                    'horizon_days': horizon_days
                }
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error creating forecast: {str(e)}")
            return None
    
    def _generate_key_assumptions(self,
                                current_data: Dict[str, Any],
                                predictions: List[Prediction]) -> List[str]:
        """Generate key assumptions for the forecast."""
        assumptions = [
            "Market conditions remain within historical ranges",
            "No major external shocks or black swan events",
            "System continues to operate under current Constitution v1.3",
            "Historical patterns continue to be relevant"
        ]
        
        # Add data-specific assumptions
        if current_data.get('market_volatility', 0.0) > 0.25:
            assumptions.append("High volatility environment persists")
        
        if current_data.get('vix_level', 0.0) > 30:
            assumptions.append("Elevated fear levels in market continue")
        
        # Add prediction-specific assumptions
        high_confidence_predictions = [p for p in predictions if p.confidence > 0.8]
        if high_confidence_predictions:
            assumptions.append(f"High confidence in {len(high_confidence_predictions)} key predictions")
        
        return assumptions
    
    def _generate_risk_factors(self,
                             current_data: Dict[str, Any],
                             predictions: List[Prediction]) -> List[str]:
        """Generate risk factors for the forecast."""
        risk_factors = [
            "Model predictions based on historical data may not capture future regime changes",
            "Unexpected market events could invalidate predictions",
            "Model accuracy may degrade in extreme market conditions"
        ]
        
        # Add data-specific risk factors
        if current_data.get('market_volatility', 0.0) > 0.3:
            risk_factors.append("Extremely high volatility may lead to model breakdown")
        
        if current_data.get('correlation_level', 0.0) > 0.8:
            risk_factors.append("High correlation environment may reduce diversification benefits")
        
        # Add confidence-based risk factors
        low_confidence_predictions = [p for p in predictions if p.confidence < 0.6]
        if low_confidence_predictions:
            risk_factors.append(f"Low confidence in {len(low_confidence_predictions)} predictions increases uncertainty")
        
        return risk_factors
    
    async def update_forecast(self, forecast_id: str, current_data: Dict[str, Any]) -> Optional[Forecast]:
        """Update an existing forecast with new data."""
        try:
            # Find the forecast
            forecast = None
            for f in self.active_forecasts:
                if f.forecast_id == forecast_id:
                    forecast = f
                    break
            
            if not forecast:
                return None
            
            # Create new predictions
            new_predictions = []
            prediction_types = [p.prediction_type for p in forecast.predictions]
            
            for pred_type in prediction_types:
                prediction = await self.make_prediction(
                    pred_type, current_data, 
                    forecast.forecast_horizon.days
                )
                if prediction:
                    new_predictions.append(prediction)
            
            if not new_predictions:
                return None
            
            # Update forecast
            forecast.predictions = new_predictions
            forecast.overall_confidence = sum(p.confidence for p in new_predictions) / len(new_predictions)
            forecast.key_assumptions = self._generate_key_assumptions(current_data, new_predictions)
            forecast.risk_factors = self._generate_risk_factors(current_data, new_predictions)
            forecast.updated_at = datetime.utcnow()
            
            # Log forecast update
            await self.audit_manager.log_event(
                event_type="FORECAST_UPDATED",
                details={
                    'forecast_id': forecast_id,
                    'prediction_count': len(new_predictions),
                    'overall_confidence': forecast.overall_confidence
                }
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error updating forecast: {str(e)}")
            return None
    
    async def get_active_forecasts(self) -> List[Forecast]:
        """Get all active forecasts."""
        # Filter out expired forecasts
        current_time = datetime.utcnow()
        active = []
        
        for forecast in self.active_forecasts:
            # Check if any predictions are still valid
            valid_predictions = [
                p for p in forecast.predictions
                if p.valid_until > current_time
            ]
            
            if valid_predictions:
                # Update forecast with only valid predictions
                forecast.predictions = valid_predictions
                active.append(forecast)
        
        self.active_forecasts = active
        return active
    
    async def get_prediction_accuracy(self, prediction_type: PredictionType) -> Dict[str, float]:
        """Get accuracy metrics for a prediction type."""
        return self.model_metrics.get(prediction_type, {})
    
    async def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get overall model performance summary."""
        summary = {
            'total_models': len(self.models),
            'training_data_points': len(self.training_data),
            'active_forecasts': len(await self.get_active_forecasts()),
            'model_performance': {}
        }
        
        for pred_type, metrics in self.model_metrics.items():
            summary['model_performance'][pred_type.value] = {
                'training_samples': metrics['training_samples'],
                'accuracy_or_r2': metrics.get('accuracy', metrics.get('r2', 0.0)),
                'last_updated': metrics['last_updated'],
                'is_trained': metrics['training_samples'] >= self.min_training_samples
            }
        
        return summary
    
    async def clear_old_data(self, days_to_keep: int = 90):
        """Clear old training data and forecasts."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clear old training data
        original_count = len(self.training_data)
        self.training_data = [
            data for data in self.training_data
            if data.get('timestamp', datetime.utcnow()) >= cutoff_date
        ]
        
        cleared_training = original_count - len(self.training_data)
        
        # Clear old forecasts
        original_forecasts = len(self.active_forecasts)
        forecast_cutoff = datetime.utcnow() - timedelta(days=30)  # Keep forecasts for 30 days
        self.active_forecasts = [
            f for f in self.active_forecasts
            if f.created_at >= forecast_cutoff
        ]
        
        cleared_forecasts = original_forecasts - len(self.active_forecasts)
        
        logger.info(f"Cleared {cleared_training} old training data entries and {cleared_forecasts} old forecasts")
        
        return {
            'training_data_cleared': cleared_training,
            'forecasts_cleared': cleared_forecasts
        }

