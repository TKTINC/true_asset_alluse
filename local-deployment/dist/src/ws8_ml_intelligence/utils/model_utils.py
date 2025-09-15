"""
Model Utilities for WS8 ML Intelligence

Utilities for model validation, performance tracking, and model management.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Container for model performance metrics."""
    model_name: str
    model_type: str  # 'classification' or 'regression'
    
    # Common metrics
    training_samples: int
    validation_samples: int
    training_time: float
    
    # Classification metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Regression metrics
    mse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    
    # Cross-validation metrics
    cv_mean: Optional[float] = None
    cv_std: Optional[float] = None
    
    # Timestamps
    trained_at: datetime = None
    validated_at: datetime = None


@dataclass
class ValidationResult:
    """Result of model validation."""
    is_valid: bool
    metrics: ModelMetrics
    issues: List[str]
    recommendations: List[str]
    confidence_score: float


class ModelValidator:
    """
    Validates ML models for performance, stability, and reliability.
    
    Provides comprehensive validation including cross-validation,
    performance benchmarking, and stability testing.
    """
    
    def __init__(self,
                 min_training_samples: int = 100,
                 min_accuracy_threshold: float = 0.6,
                 min_r2_threshold: float = 0.3):
        """Initialize the model validator."""
        self.min_training_samples = min_training_samples
        self.min_accuracy_threshold = min_accuracy_threshold
        self.min_r2_threshold = min_r2_threshold
        
        logger.info("ModelValidator initialized successfully")
    
    def validate_classification_model(self,
                                    model: Any,
                                    X_train: np.ndarray,
                                    y_train: np.ndarray,
                                    X_val: np.ndarray,
                                    y_val: np.ndarray,
                                    model_name: str) -> ValidationResult:
        """Validate a classification model."""
        try:
            start_time = datetime.utcnow()
            issues = []
            recommendations = []
            
            # Check training data size
            if len(X_train) < self.min_training_samples:
                issues.append(f"Insufficient training data: {len(X_train)} < {self.min_training_samples}")
            
            # Train the model
            training_start = datetime.utcnow()
            model.fit(X_train, y_train)
            training_time = (datetime.utcnow() - training_start).total_seconds()
            
            # Make predictions
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)
            
            # Calculate metrics
            train_accuracy = accuracy_score(y_train, y_train_pred)
            val_accuracy = accuracy_score(y_val, y_val_pred)
            
            precision = precision_score(y_val, y_val_pred, average='weighted', zero_division=0)
            recall = recall_score(y_val, y_val_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_val, y_val_pred, average='weighted', zero_division=0)
            
            # Cross-validation
            cv_scores = None
            cv_mean = None
            cv_std = None
            
            try:
                tscv = TimeSeriesSplit(n_splits=3)
                cv_scores = cross_val_score(model, X_train, y_train, cv=tscv, scoring='accuracy')
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
            except Exception as e:
                logger.warning(f"Cross-validation failed: {str(e)}")
            
            # Performance checks
            if val_accuracy < self.min_accuracy_threshold:
                issues.append(f"Low validation accuracy: {val_accuracy:.3f} < {self.min_accuracy_threshold}")
                recommendations.append("Consider feature engineering or model tuning")
            
            # Overfitting check
            if train_accuracy - val_accuracy > 0.2:
                issues.append(f"Potential overfitting: train_acc={train_accuracy:.3f}, val_acc={val_accuracy:.3f}")
                recommendations.append("Consider regularization or more training data")
            
            # Create metrics
            metrics = ModelMetrics(
                model_name=model_name,
                model_type='classification',
                training_samples=len(X_train),
                validation_samples=len(X_val),
                training_time=training_time,
                accuracy=val_accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                cv_mean=cv_mean,
                cv_std=cv_std,
                trained_at=start_time,
                validated_at=datetime.utcnow()
            )
            
            # Determine if model is valid
            is_valid = (
                len(issues) == 0 and
                val_accuracy >= self.min_accuracy_threshold and
                len(X_train) >= self.min_training_samples
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(metrics, issues)
            
            return ValidationResult(
                is_valid=is_valid,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error validating classification model: {str(e)}")
            return ValidationResult(
                is_valid=False,
                metrics=ModelMetrics(model_name, 'classification', 0, 0, 0.0),
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Check model and data compatibility"],
                confidence_score=0.0
            )
    
    def validate_regression_model(self,
                                model: Any,
                                X_train: np.ndarray,
                                y_train: np.ndarray,
                                X_val: np.ndarray,
                                y_val: np.ndarray,
                                model_name: str) -> ValidationResult:
        """Validate a regression model."""
        try:
            start_time = datetime.utcnow()
            issues = []
            recommendations = []
            
            # Check training data size
            if len(X_train) < self.min_training_samples:
                issues.append(f"Insufficient training data: {len(X_train)} < {self.min_training_samples}")
            
            # Train the model
            training_start = datetime.utcnow()
            model.fit(X_train, y_train)
            training_time = (datetime.utcnow() - training_start).total_seconds()
            
            # Make predictions
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)
            
            # Calculate metrics
            train_r2 = r2_score(y_train, y_train_pred)
            val_r2 = r2_score(y_val, y_val_pred)
            
            mse = mean_squared_error(y_val, y_val_pred)
            mae = mean_absolute_error(y_val, y_val_pred)
            
            # Cross-validation
            cv_scores = None
            cv_mean = None
            cv_std = None
            
            try:
                tscv = TimeSeriesSplit(n_splits=3)
                cv_scores = cross_val_score(model, X_train, y_train, cv=tscv, scoring='r2')
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
            except Exception as e:
                logger.warning(f"Cross-validation failed: {str(e)}")
            
            # Performance checks
            if val_r2 < self.min_r2_threshold:
                issues.append(f"Low R² score: {val_r2:.3f} < {self.min_r2_threshold}")
                recommendations.append("Consider feature engineering or different model")
            
            # Overfitting check
            if train_r2 - val_r2 > 0.3:
                issues.append(f"Potential overfitting: train_r2={train_r2:.3f}, val_r2={val_r2:.3f}")
                recommendations.append("Consider regularization or more training data")
            
            # Prediction quality check
            if np.isnan(y_val_pred).any() or np.isinf(y_val_pred).any():
                issues.append("Model produces invalid predictions (NaN or Inf)")
                recommendations.append("Check input data quality and model stability")
            
            # Create metrics
            metrics = ModelMetrics(
                model_name=model_name,
                model_type='regression',
                training_samples=len(X_train),
                validation_samples=len(X_val),
                training_time=training_time,
                mse=mse,
                mae=mae,
                r2_score=val_r2,
                cv_mean=cv_mean,
                cv_std=cv_std,
                trained_at=start_time,
                validated_at=datetime.utcnow()
            )
            
            # Determine if model is valid
            is_valid = (
                len(issues) == 0 and
                val_r2 >= self.min_r2_threshold and
                len(X_train) >= self.min_training_samples
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(metrics, issues)
            
            return ValidationResult(
                is_valid=is_valid,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error validating regression model: {str(e)}")
            return ValidationResult(
                is_valid=False,
                metrics=ModelMetrics(model_name, 'regression', 0, 0, 0.0),
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Check model and data compatibility"],
                confidence_score=0.0
            )
    
    def _calculate_confidence_score(self, metrics: ModelMetrics, issues: List[str]) -> float:
        """Calculate overall confidence score for the model."""
        base_score = 1.0
        
        # Penalty for issues
        base_score -= len(issues) * 0.2
        
        # Performance-based scoring
        if metrics.model_type == 'classification' and metrics.accuracy is not None:
            performance_score = metrics.accuracy
        elif metrics.model_type == 'regression' and metrics.r2_score is not None:
            performance_score = max(0.0, metrics.r2_score)
        else:
            performance_score = 0.5
        
        # Cross-validation stability
        cv_stability = 1.0
        if metrics.cv_std is not None and metrics.cv_mean is not None:
            if metrics.cv_mean > 0:
                cv_stability = max(0.0, 1.0 - metrics.cv_std / abs(metrics.cv_mean))
        
        # Training data adequacy
        data_adequacy = min(1.0, metrics.training_samples / (self.min_training_samples * 2))
        
        # Combine scores
        confidence_score = (
            base_score * 0.3 +
            performance_score * 0.4 +
            cv_stability * 0.2 +
            data_adequacy * 0.1
        )
        
        return max(0.0, min(1.0, confidence_score))


class PerformanceTracker:
    """
    Tracks model performance over time and detects degradation.
    
    Monitors model predictions and actual outcomes to identify
    when models need retraining or replacement.
    """
    
    def __init__(self,
                 tracking_window_days: int = 30,
                 degradation_threshold: float = 0.1):
        """Initialize the performance tracker."""
        self.tracking_window_days = tracking_window_days
        self.degradation_threshold = degradation_threshold
        
        # Performance history
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("PerformanceTracker initialized successfully")
    
    def record_prediction(self,
                         model_name: str,
                         prediction: float,
                         actual: Optional[float] = None,
                         features: Optional[Dict[str, float]] = None,
                         timestamp: Optional[datetime] = None):
        """Record a model prediction for tracking."""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            if model_name not in self.performance_history:
                self.performance_history[model_name] = []
            
            record = {
                'timestamp': timestamp,
                'prediction': prediction,
                'actual': actual,
                'features': features or {},
                'error': None if actual is None else abs(prediction - actual),
                'squared_error': None if actual is None else (prediction - actual) ** 2
            }
            
            self.performance_history[model_name].append(record)
            
            # Clean old records
            cutoff_time = timestamp - timedelta(days=self.tracking_window_days * 2)
            self.performance_history[model_name] = [
                r for r in self.performance_history[model_name]
                if r['timestamp'] >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error recording prediction: {str(e)}")
    
    def update_actual_outcome(self,
                            model_name: str,
                            prediction_timestamp: datetime,
                            actual_value: float,
                            tolerance_minutes: int = 60):
        """Update a prediction record with the actual outcome."""
        try:
            if model_name not in self.performance_history:
                return
            
            # Find matching prediction within tolerance
            for record in self.performance_history[model_name]:
                time_diff = abs((record['timestamp'] - prediction_timestamp).total_seconds() / 60)
                
                if time_diff <= tolerance_minutes and record['actual'] is None:
                    record['actual'] = actual_value
                    record['error'] = abs(record['prediction'] - actual_value)
                    record['squared_error'] = (record['prediction'] - actual_value) ** 2
                    break
            
        except Exception as e:
            logger.error(f"Error updating actual outcome: {str(e)}")
    
    def get_performance_metrics(self, model_name: str, days_back: int = None) -> Dict[str, float]:
        """Get performance metrics for a model."""
        try:
            if model_name not in self.performance_history:
                return {}
            
            if days_back is None:
                days_back = self.tracking_window_days
            
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            # Filter records with actual outcomes
            records = [
                r for r in self.performance_history[model_name]
                if r['timestamp'] >= cutoff_time and r['actual'] is not None
            ]
            
            if not records:
                return {}
            
            # Calculate metrics
            errors = [r['error'] for r in records]
            squared_errors = [r['squared_error'] for r in records]
            predictions = [r['prediction'] for r in records]
            actuals = [r['actual'] for r in records]
            
            metrics = {
                'sample_count': len(records),
                'mae': np.mean(errors),
                'mse': np.mean(squared_errors),
                'rmse': np.sqrt(np.mean(squared_errors)),
                'mean_prediction': np.mean(predictions),
                'mean_actual': np.mean(actuals),
                'prediction_std': np.std(predictions),
                'actual_std': np.std(actuals)
            }
            
            # R² score
            if len(actuals) > 1:
                ss_res = sum(squared_errors)
                ss_tot = sum((a - np.mean(actuals)) ** 2 for a in actuals)
                metrics['r2_score'] = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            # Bias
            residuals = [p - a for p, a in zip(predictions, actuals)]
            metrics['bias'] = np.mean(residuals)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def detect_performance_degradation(self, model_name: str) -> Dict[str, Any]:
        """Detect if model performance has degraded."""
        try:
            # Get recent and historical performance
            recent_metrics = self.get_performance_metrics(model_name, days_back=7)
            historical_metrics = self.get_performance_metrics(model_name, days_back=30)
            
            if not recent_metrics or not historical_metrics:
                return {
                    'degradation_detected': False,
                    'reason': 'Insufficient data for comparison'
                }
            
            degradation_signals = []
            
            # Check MAE increase
            if 'mae' in recent_metrics and 'mae' in historical_metrics:
                mae_increase = (recent_metrics['mae'] - historical_metrics['mae']) / historical_metrics['mae']
                if mae_increase > self.degradation_threshold:
                    degradation_signals.append(f"MAE increased by {mae_increase:.1%}")
            
            # Check R² decrease
            if 'r2_score' in recent_metrics and 'r2_score' in historical_metrics:
                r2_decrease = historical_metrics['r2_score'] - recent_metrics['r2_score']
                if r2_decrease > self.degradation_threshold:
                    degradation_signals.append(f"R² decreased by {r2_decrease:.3f}")
            
            # Check bias increase
            if 'bias' in recent_metrics and 'bias' in historical_metrics:
                bias_change = abs(recent_metrics['bias']) - abs(historical_metrics['bias'])
                if bias_change > self.degradation_threshold:
                    degradation_signals.append(f"Bias increased by {bias_change:.3f}")
            
            return {
                'degradation_detected': len(degradation_signals) > 0,
                'signals': degradation_signals,
                'recent_metrics': recent_metrics,
                'historical_metrics': historical_metrics,
                'recommendation': 'Consider model retraining' if degradation_signals else 'Performance stable'
            }
            
        except Exception as e:
            logger.error(f"Error detecting performance degradation: {str(e)}")
            return {
                'degradation_detected': False,
                'error': str(e)
            }
    
    def get_model_health_report(self, model_name: str) -> Dict[str, Any]:
        """Get comprehensive health report for a model."""
        try:
            performance_metrics = self.get_performance_metrics(model_name)
            degradation_check = self.detect_performance_degradation(model_name)
            
            # Determine health status
            if not performance_metrics:
                health_status = 'UNKNOWN'
                health_score = 0.0
            elif degradation_check['degradation_detected']:
                health_status = 'DEGRADED'
                health_score = 0.3
            elif performance_metrics.get('r2_score', 0) > 0.7:
                health_status = 'EXCELLENT'
                health_score = 0.9
            elif performance_metrics.get('r2_score', 0) > 0.5:
                health_status = 'GOOD'
                health_score = 0.7
            else:
                health_status = 'POOR'
                health_score = 0.4
            
            return {
                'model_name': model_name,
                'health_status': health_status,
                'health_score': health_score,
                'performance_metrics': performance_metrics,
                'degradation_check': degradation_check,
                'total_predictions': len(self.performance_history.get(model_name, [])),
                'predictions_with_outcomes': performance_metrics.get('sample_count', 0),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {
                'model_name': model_name,
                'health_status': 'ERROR',
                'health_score': 0.0,
                'error': str(e)
            }
    
    def get_all_models_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked models."""
        try:
            summary = {
                'total_models': len(self.performance_history),
                'models': {},
                'overall_health': 'UNKNOWN'
            }
            
            health_scores = []
            
            for model_name in self.performance_history.keys():
                health_report = self.get_model_health_report(model_name)
                summary['models'][model_name] = {
                    'health_status': health_report['health_status'],
                    'health_score': health_report['health_score'],
                    'total_predictions': health_report['total_predictions'],
                    'predictions_with_outcomes': health_report['predictions_with_outcomes']
                }
                
                if health_report['health_score'] > 0:
                    health_scores.append(health_report['health_score'])
            
            # Overall health
            if health_scores:
                avg_health = np.mean(health_scores)
                if avg_health > 0.8:
                    summary['overall_health'] = 'EXCELLENT'
                elif avg_health > 0.6:
                    summary['overall_health'] = 'GOOD'
                elif avg_health > 0.4:
                    summary['overall_health'] = 'FAIR'
                else:
                    summary['overall_health'] = 'POOR'
                
                summary['average_health_score'] = avg_health
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating models summary: {str(e)}")
            return {
                'total_models': 0,
                'models': {},
                'overall_health': 'ERROR',
                'error': str(e)
            }

