"""
Market Anomaly Detector - ML Intelligence System

This module implements anomaly detection for unusual market behavior and system
anomalies. It helps identify when market conditions or system behavior deviate
significantly from normal patterns.

IMPORTANT: This system provides ADVISORY insights only. All wealth management
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
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from src.ws1_rules_engine.audit import AuditTrailManager

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    MARKET_VOLATILITY = "market_volatility"
    PRICE_MOVEMENT = "price_movement"
    VOLUME_ANOMALY = "volume_anomaly"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    SYSTEM_PERFORMANCE = "system_performance"
    RISK_METRIC = "risk_metric"
    PROTOCOL_BEHAVIOR = "protocol_behavior"


class AnomalySeverity(Enum):
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyAlert:
    """Anomaly detection alert."""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    confidence: float
    description: str
    detected_at: datetime
    affected_metrics: Dict[str, float]
    historical_context: Dict[str, Any]
    recommendations: List[str]
    alert_id: str


@dataclass
class AnomalyDetectionConfig:
    """Configuration for anomaly detection."""
    contamination_rate: float = 0.1  # Expected proportion of anomalies
    lookback_days: int = 30  # Days of historical data to consider
    min_samples_for_detection: int = 50  # Minimum samples needed
    statistical_threshold: float = 3.0  # Standard deviations for statistical anomalies
    update_frequency_hours: int = 1  # How often to update models
    alert_cooldown_minutes: int = 60  # Minimum time between similar alerts


class MarketAnomalyDetector:
    """
    Detects anomalies in market behavior and system performance.
    
    Uses multiple detection methods:
    - Isolation Forest for multivariate anomalies
    - Statistical methods for univariate anomalies
    - DBSCAN clustering for pattern anomalies
    - Time series analysis for temporal anomalies
    
    ADVISORY ONLY: Provides alerts and insights but does not make
    any wealth management decisions.
    """
    
    def __init__(self,
                 audit_manager: AuditTrailManager,
                 config: Optional[AnomalyDetectionConfig] = None):
        """Initialize the anomaly detector."""
        self.audit_manager = audit_manager
        self.config = config or AnomalyDetectionConfig()
        
        # Detection models
        self.isolation_forests: Dict[AnomalyType, IsolationForest] = {}
        self.scalers: Dict[AnomalyType, StandardScaler] = {}
        
        # Historical data storage
        self.historical_data: Dict[AnomalyType, List[Dict[str, Any]]] = {}
        
        # Alert management
        self.recent_alerts: List[AnomalyAlert] = []
        self.alert_counter = 0
        
        # Statistical baselines
        self.statistical_baselines: Dict[str, Dict[str, float]] = {}
        
        # Initialize detection models
        self._initialize_detection_models()
        
        logger.info("MarketAnomalyDetector initialized successfully")
    
    def _initialize_detection_models(self):
        """Initialize anomaly detection models."""
        for anomaly_type in AnomalyType:
            # Isolation Forest for each anomaly type
            self.isolation_forests[anomaly_type] = IsolationForest(
                contamination=self.config.contamination_rate,
                random_state=42,
                n_jobs=-1
            )
            
            # Scaler for each anomaly type
            self.scalers[anomaly_type] = StandardScaler()
            
            # Initialize historical data storage
            self.historical_data[anomaly_type] = []
    
    async def add_market_data(self, market_data: Dict[str, Any]):
        """Add market data for anomaly detection."""
        try:
            timestamp = datetime.utcnow()
            
            # Process different types of market data
            await self._process_volatility_data(market_data, timestamp)
            await self._process_price_data(market_data, timestamp)
            await self._process_volume_data(market_data, timestamp)
            await self._process_correlation_data(market_data, timestamp)
            await self._process_liquidity_data(market_data, timestamp)
            
            # Update models if enough data
            await self._update_models_if_needed()
            
        except Exception as e:
            logger.error(f"Error adding market data: {str(e)}")
    
    async def add_system_data(self, system_data: Dict[str, Any]):
        """Add system performance data for anomaly detection."""
        try:
            timestamp = datetime.utcnow()
            
            # Process system performance data
            await self._process_system_performance_data(system_data, timestamp)
            await self._process_risk_metric_data(system_data, timestamp)
            await self._process_protocol_behavior_data(system_data, timestamp)
            
            # Update models if enough data
            await self._update_models_if_needed()
            
        except Exception as e:
            logger.error(f"Error adding system data: {str(e)}")
    
    async def _process_volatility_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process volatility data for anomaly detection."""
        volatility_metrics = {
            'realized_volatility': data.get('realized_volatility', 0.0),
            'implied_volatility': data.get('implied_volatility', 0.0),
            'vix_level': data.get('vix_level', 0.0),
            'vix_change': data.get('vix_change', 0.0),
            'volatility_skew': data.get('volatility_skew', 0.0),
            'volatility_term_structure': data.get('volatility_term_structure', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.MARKET_VOLATILITY].append({
            'timestamp': timestamp,
            'metrics': volatility_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.MARKET_VOLATILITY,
            volatility_metrics,
            timestamp
        )
    
    async def _process_price_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process price movement data for anomaly detection."""
        price_metrics = {
            'price_change': data.get('price_change', 0.0),
            'price_acceleration': data.get('price_acceleration', 0.0),
            'gap_size': data.get('gap_size', 0.0),
            'intraday_range': data.get('intraday_range', 0.0),
            'price_momentum': data.get('price_momentum', 0.0),
            'reversal_magnitude': data.get('reversal_magnitude', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.PRICE_MOVEMENT].append({
            'timestamp': timestamp,
            'metrics': price_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.PRICE_MOVEMENT,
            price_metrics,
            timestamp
        )
    
    async def _process_volume_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process volume data for anomaly detection."""
        volume_metrics = {
            'volume': data.get('volume', 0.0),
            'volume_ratio': data.get('volume_ratio', 1.0),
            'volume_spike': data.get('volume_spike', 0.0),
            'dark_pool_ratio': data.get('dark_pool_ratio', 0.0),
            'block_trade_ratio': data.get('block_trade_ratio', 0.0),
            'options_volume_ratio': data.get('options_volume_ratio', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.VOLUME_ANOMALY].append({
            'timestamp': timestamp,
            'metrics': volume_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.VOLUME_ANOMALY,
            volume_metrics,
            timestamp
        )
    
    async def _process_correlation_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process correlation data for anomaly detection."""
        correlation_metrics = {
            'market_correlation': data.get('market_correlation', 0.0),
            'sector_correlation': data.get('sector_correlation', 0.0),
            'correlation_stability': data.get('correlation_stability', 0.0),
            'correlation_breakdown_score': data.get('correlation_breakdown_score', 0.0),
            'diversification_ratio': data.get('diversification_ratio', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.CORRELATION_BREAKDOWN].append({
            'timestamp': timestamp,
            'metrics': correlation_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.CORRELATION_BREAKDOWN,
            correlation_metrics,
            timestamp
        )
    
    async def _process_liquidity_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process liquidity data for anomaly detection."""
        liquidity_metrics = {
            'bid_ask_spread': data.get('bid_ask_spread', 0.0),
            'market_depth': data.get('market_depth', 0.0),
            'liquidity_ratio': data.get('liquidity_ratio', 1.0),
            'execution_difficulty': data.get('execution_difficulty', 0.0),
            'slippage_cost': data.get('slippage_cost', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.LIQUIDITY_CRISIS].append({
            'timestamp': timestamp,
            'metrics': liquidity_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.LIQUIDITY_CRISIS,
            liquidity_metrics,
            timestamp
        )
    
    async def _process_system_performance_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process system performance data for anomaly detection."""
        performance_metrics = {
            'system_return': data.get('system_return', 0.0),
            'tracking_error': data.get('tracking_error', 0.0),
            'execution_quality': data.get('execution_quality', 1.0),
            'response_time': data.get('response_time', 0.0),
            'error_rate': data.get('error_rate', 0.0),
            'system_load': data.get('system_load', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.SYSTEM_PERFORMANCE].append({
            'timestamp': timestamp,
            'metrics': performance_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.SYSTEM_PERFORMANCE,
            performance_metrics,
            timestamp
        )
    
    async def _process_risk_metric_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process risk metrics data for anomaly detection."""
        risk_metrics = {
            'portfolio_var': data.get('portfolio_var', 0.0),
            'portfolio_cvar': data.get('portfolio_cvar', 0.0),
            'max_drawdown': data.get('max_drawdown', 0.0),
            'risk_budget_utilization': data.get('risk_budget_utilization', 0.0),
            'concentration_risk': data.get('concentration_risk', 0.0),
            'tail_risk': data.get('tail_risk', 0.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.RISK_METRIC].append({
            'timestamp': timestamp,
            'metrics': risk_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.RISK_METRIC,
            risk_metrics,
            timestamp
        )
    
    async def _process_protocol_behavior_data(self, data: Dict[str, Any], timestamp: datetime):
        """Process protocol behavior data for anomaly detection."""
        protocol_metrics = {
            'protocol_level': data.get('protocol_level', 0),
            'escalation_frequency': data.get('escalation_frequency', 0.0),
            'rule_violation_count': data.get('rule_violation_count', 0),
            'override_frequency': data.get('override_frequency', 0.0),
            'decision_latency': data.get('decision_latency', 0.0),
            'constitution_compliance': data.get('constitution_compliance', 1.0)
        }
        
        # Add to historical data
        self.historical_data[AnomalyType.PROTOCOL_BEHAVIOR].append({
            'timestamp': timestamp,
            'metrics': protocol_metrics
        })
        
        # Check for immediate anomalies
        await self._check_statistical_anomaly(
            AnomalyType.PROTOCOL_BEHAVIOR,
            protocol_metrics,
            timestamp
        )
    
    async def _check_statistical_anomaly(self,
                                       anomaly_type: AnomalyType,
                                       metrics: Dict[str, float],
                                       timestamp: datetime):
        """Check for statistical anomalies using z-score method."""
        try:
            # Get historical data for this anomaly type
            historical = self.historical_data[anomaly_type]
            
            if len(historical) < self.config.min_samples_for_detection:
                return
            
            # Calculate statistical baselines if not exists
            if anomaly_type.value not in self.statistical_baselines:
                await self._calculate_statistical_baselines(anomaly_type)
            
            baselines = self.statistical_baselines.get(anomaly_type.value, {})
            
            # Check each metric for anomalies
            anomalous_metrics = {}
            max_z_score = 0.0
            
            for metric_name, current_value in metrics.items():
                if metric_name in baselines:
                    mean = baselines[metric_name]['mean']
                    std = baselines[metric_name]['std']
                    
                    if std > 0:
                        z_score = abs((current_value - mean) / std)
                        
                        if z_score > self.config.statistical_threshold:
                            anomalous_metrics[metric_name] = {
                                'current_value': current_value,
                                'historical_mean': mean,
                                'historical_std': std,
                                'z_score': z_score
                            }
                            max_z_score = max(max_z_score, z_score)
            
            # Generate alert if anomalies found
            if anomalous_metrics:
                severity = self._determine_severity(max_z_score)
                await self._generate_anomaly_alert(
                    anomaly_type,
                    severity,
                    anomalous_metrics,
                    timestamp
                )
                
        except Exception as e:
            logger.error(f"Error checking statistical anomaly: {str(e)}")
    
    async def _calculate_statistical_baselines(self, anomaly_type: AnomalyType):
        """Calculate statistical baselines for an anomaly type."""
        try:
            historical = self.historical_data[anomaly_type]
            
            if len(historical) < self.config.min_samples_for_detection:
                return
            
            # Extract metrics from historical data
            metrics_data = {}
            for entry in historical:
                for metric_name, value in entry['metrics'].items():
                    if metric_name not in metrics_data:
                        metrics_data[metric_name] = []
                    metrics_data[metric_name].append(value)
            
            # Calculate mean and std for each metric
            baselines = {}
            for metric_name, values in metrics_data.items():
                if len(values) > 1:
                    baselines[metric_name] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'median': np.median(values),
                        'samples': len(values)
                    }
            
            self.statistical_baselines[anomaly_type.value] = baselines
            
        except Exception as e:
            logger.error(f"Error calculating statistical baselines: {str(e)}")
    
    def _determine_severity(self, max_z_score: float) -> AnomalySeverity:
        """Determine anomaly severity based on z-score."""
        if max_z_score >= 5.0:
            return AnomalySeverity.CRITICAL
        elif max_z_score >= 4.0:
            return AnomalySeverity.HIGH
        elif max_z_score >= 3.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    async def _generate_anomaly_alert(self,
                                    anomaly_type: AnomalyType,
                                    severity: AnomalySeverity,
                                    anomalous_metrics: Dict[str, Any],
                                    timestamp: datetime):
        """Generate an anomaly alert."""
        try:
            # Check cooldown period
            if await self._is_in_cooldown(anomaly_type):
                return
            
            # Generate alert ID
            self.alert_counter += 1
            alert_id = f"ANOMALY_{anomaly_type.value}_{self.alert_counter}_{int(timestamp.timestamp())}"
            
            # Create description
            description = self._create_anomaly_description(anomaly_type, anomalous_metrics)
            
            # Generate recommendations
            recommendations = self._generate_anomaly_recommendations(anomaly_type, severity)
            
            # Create alert
            alert = AnomalyAlert(
                anomaly_type=anomaly_type,
                severity=severity,
                confidence=min(max([m['z_score'] for m in anomalous_metrics.values()]) / 5.0, 1.0),
                description=description,
                detected_at=timestamp,
                affected_metrics={k: v['current_value'] for k, v in anomalous_metrics.items()},
                historical_context=self._get_historical_context(anomaly_type),
                recommendations=recommendations,
                alert_id=alert_id
            )
            
            # Store alert
            self.recent_alerts.append(alert)
            
            # Keep only recent alerts (last 100)
            self.recent_alerts = self.recent_alerts[-100:]
            
            # Log the alert
            await self.audit_manager.log_event(
                event_type="ANOMALY_DETECTED",
                details={
                    'alert_id': alert_id,
                    'anomaly_type': anomaly_type.value,
                    'severity': severity.value,
                    'confidence': alert.confidence,
                    'affected_metrics': list(anomalous_metrics.keys())
                },
                metadata={'alert_data': anomalous_metrics}
            )
            
            logger.warning(f"Anomaly detected: {anomaly_type.value} - {severity.value} - {alert_id}")
            
        except Exception as e:
            logger.error(f"Error generating anomaly alert: {str(e)}")
    
    async def _is_in_cooldown(self, anomaly_type: AnomalyType) -> bool:
        """Check if anomaly type is in cooldown period."""
        cooldown_time = datetime.utcnow() - timedelta(minutes=self.config.alert_cooldown_minutes)
        
        for alert in self.recent_alerts:
            if (alert.anomaly_type == anomaly_type and 
                alert.detected_at > cooldown_time):
                return True
        
        return False
    
    def _create_anomaly_description(self,
                                  anomaly_type: AnomalyType,
                                  anomalous_metrics: Dict[str, Any]) -> str:
        """Create a description for the anomaly."""
        metric_descriptions = []
        
        for metric_name, data in anomalous_metrics.items():
            current = data['current_value']
            mean = data['historical_mean']
            z_score = data['z_score']
            
            if current > mean:
                direction = "above"
            else:
                direction = "below"
            
            metric_descriptions.append(
                f"{metric_name}: {current:.4f} ({z_score:.1f}σ {direction} normal)"
            )
        
        return f"{anomaly_type.value.replace('_', ' ').title()} anomaly detected. " + \
               f"Unusual values: {', '.join(metric_descriptions)}"
    
    def _generate_anomaly_recommendations(self,
                                        anomaly_type: AnomalyType,
                                        severity: AnomalySeverity) -> List[str]:
        """Generate recommendations for an anomaly."""
        base_recommendations = [
            "Monitor the situation closely",
            "Review recent system and market conditions",
            "Consider increasing monitoring frequency"
        ]
        
        if severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
            base_recommendations.extend([
                "Alert system administrators",
                "Consider manual review of system operations",
                "Prepare for potential protocol escalation"
            ])
        
        # Add anomaly-specific recommendations
        if anomaly_type == AnomalyType.MARKET_VOLATILITY:
            base_recommendations.extend([
                "Review volatility-based risk parameters",
                "Monitor VIX levels and volatility term structure",
                "Consider hedging strategies if appropriate"
            ])
        elif anomaly_type == AnomalyType.LIQUIDITY_CRISIS:
            base_recommendations.extend([
                "Review position sizes and liquidity requirements",
                "Monitor bid-ask spreads and market depth",
                "Consider reducing position sizes if necessary"
            ])
        elif anomaly_type == AnomalyType.SYSTEM_PERFORMANCE:
            base_recommendations.extend([
                "Check system resources and performance metrics",
                "Review recent system changes or updates",
                "Consider system maintenance if needed"
            ])
        
        return base_recommendations
    
    def _get_historical_context(self, anomaly_type: AnomalyType) -> Dict[str, Any]:
        """Get historical context for an anomaly type."""
        historical = self.historical_data[anomaly_type]
        
        if not historical:
            return {}
        
        # Calculate recent trends
        recent_data = historical[-10:]  # Last 10 data points
        
        context = {
            'total_samples': len(historical),
            'recent_samples': len(recent_data),
            'data_period_days': (datetime.utcnow() - historical[0]['timestamp']).days if historical else 0
        }
        
        # Add statistical baselines if available
        if anomaly_type.value in self.statistical_baselines:
            context['baselines'] = self.statistical_baselines[anomaly_type.value]
        
        return context
    
    async def _update_models_if_needed(self):
        """Update ML models if enough new data is available."""
        try:
            for anomaly_type in AnomalyType:
                historical = self.historical_data[anomaly_type]
                
                if len(historical) >= self.config.min_samples_for_detection:
                    # Update statistical baselines
                    await self._calculate_statistical_baselines(anomaly_type)
                    
                    # Train isolation forest if enough data
                    if len(historical) >= 100:  # Need more data for ML models
                        await self._train_isolation_forest(anomaly_type)
        
        except Exception as e:
            logger.error(f"Error updating models: {str(e)}")
    
    async def _train_isolation_forest(self, anomaly_type: AnomalyType):
        """Train isolation forest model for an anomaly type."""
        try:
            historical = self.historical_data[anomaly_type]
            
            # Prepare training data
            training_data = []
            for entry in historical:
                row = list(entry['metrics'].values())
                training_data.append(row)
            
            if not training_data:
                return
            
            # Convert to numpy array
            X = np.array(training_data)
            
            # Scale the data
            X_scaled = self.scalers[anomaly_type].fit_transform(X)
            
            # Train isolation forest
            self.isolation_forests[anomaly_type].fit(X_scaled)
            
            logger.info(f"Trained isolation forest for {anomaly_type.value} with {len(training_data)} samples")
            
        except Exception as e:
            logger.error(f"Error training isolation forest for {anomaly_type.value}: {str(e)}")
    
    async def detect_anomalies_batch(self,
                                   data_batch: List[Dict[str, Any]],
                                   anomaly_type: AnomalyType) -> List[bool]:
        """Detect anomalies in a batch of data."""
        try:
            if anomaly_type not in self.isolation_forests:
                return [False] * len(data_batch)
            
            # Prepare data
            batch_data = []
            for data in data_batch:
                if anomaly_type == AnomalyType.MARKET_VOLATILITY:
                    row = [
                        data.get('realized_volatility', 0.0),
                        data.get('implied_volatility', 0.0),
                        data.get('vix_level', 0.0),
                        data.get('vix_change', 0.0)
                    ]
                else:
                    # Generic approach - use all numeric values
                    row = [v for v in data.values() if isinstance(v, (int, float))]
                
                batch_data.append(row)
            
            if not batch_data:
                return [False] * len(data_batch)
            
            # Scale and predict
            X = np.array(batch_data)
            X_scaled = self.scalers[anomaly_type].transform(X)
            
            # Predict anomalies (-1 = anomaly, 1 = normal)
            predictions = self.isolation_forests[anomaly_type].predict(X_scaled)
            
            # Convert to boolean (True = anomaly)
            return [pred == -1 for pred in predictions]
            
        except Exception as e:
            logger.error(f"Error in batch anomaly detection: {str(e)}")
            return [False] * len(data_batch)
    
    async def get_recent_alerts(self,
                              anomaly_type: Optional[AnomalyType] = None,
                              severity: Optional[AnomalySeverity] = None,
                              hours_back: int = 24) -> List[AnomalyAlert]:
        """Get recent anomaly alerts."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        alerts = [
            alert for alert in self.recent_alerts
            if alert.detected_at >= cutoff_time
        ]
        
        if anomaly_type:
            alerts = [alert for alert in alerts if alert.anomaly_type == anomaly_type]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.detected_at, reverse=True)
    
    async def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics."""
        total_alerts = len(self.recent_alerts)
        
        if total_alerts == 0:
            return {
                'total_alerts': 0,
                'alerts_by_type': {},
                'alerts_by_severity': {},
                'detection_coverage': {}
            }
        
        # Count by type
        alerts_by_type = {}
        for alert in self.recent_alerts:
            type_name = alert.anomaly_type.value
            alerts_by_type[type_name] = alerts_by_type.get(type_name, 0) + 1
        
        # Count by severity
        alerts_by_severity = {}
        for alert in self.recent_alerts:
            severity_name = alert.severity.value
            alerts_by_severity[severity_name] = alerts_by_severity.get(severity_name, 0) + 1
        
        # Detection coverage
        detection_coverage = {}
        for anomaly_type in AnomalyType:
            historical_count = len(self.historical_data[anomaly_type])
            detection_coverage[anomaly_type.value] = {
                'historical_samples': historical_count,
                'model_trained': historical_count >= self.config.min_samples_for_detection,
                'baseline_calculated': anomaly_type.value in self.statistical_baselines
            }
        
        return {
            'total_alerts': total_alerts,
            'alerts_by_type': alerts_by_type,
            'alerts_by_severity': alerts_by_severity,
            'detection_coverage': detection_coverage,
            'config': {
                'contamination_rate': self.config.contamination_rate,
                'lookback_days': self.config.lookback_days,
                'statistical_threshold': self.config.statistical_threshold
            }
        }
    
    async def clear_old_data(self, days_to_keep: int = 30):
        """Clear old historical data."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        total_cleared = 0
        for anomaly_type in AnomalyType:
            original_count = len(self.historical_data[anomaly_type])
            
            self.historical_data[anomaly_type] = [
                entry for entry in self.historical_data[anomaly_type]
                if entry['timestamp'] >= cutoff_date
            ]
            
            cleared_count = original_count - len(self.historical_data[anomaly_type])
            total_cleared += cleared_count
        
        # Clear old alerts
        alert_cutoff = datetime.utcnow() - timedelta(days=7)  # Keep alerts for 7 days
        original_alert_count = len(self.recent_alerts)
        self.recent_alerts = [
            alert for alert in self.recent_alerts
            if alert.detected_at >= alert_cutoff
        ]
        
        cleared_alerts = original_alert_count - len(self.recent_alerts)
        
        logger.info(f"Cleared {total_cleared} old data entries and {cleared_alerts} old alerts")
        
        return {
            'data_entries_cleared': total_cleared,
            'alerts_cleared': cleared_alerts
        }

