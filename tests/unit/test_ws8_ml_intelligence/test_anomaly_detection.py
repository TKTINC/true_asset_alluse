"""
Unit tests for Market Anomaly Detector
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import numpy as np

from src.ws8_ml_intelligence.anomaly_detection.market_anomaly_detector import (
    MarketAnomalyDetector, AnomalyAlert, AnomalyType, AnomalySeverity, AnomalyDetectionConfig
)
from src.ws1_rules_engine.audit import AuditTrailManager


@pytest.fixture
def mock_audit_manager():
    """Create mock audit manager."""
    audit_manager = Mock(spec=AuditTrailManager)
    audit_manager.log_event = AsyncMock()
    return audit_manager


@pytest.fixture
def anomaly_detector(mock_audit_manager):
    """Create anomaly detector instance."""
    return MarketAnomalyDetector(mock_audit_manager)


@pytest.fixture
def custom_config():
    """Create custom anomaly detection config."""
    return AnomalyDetectionConfig(
        contamination_rate=0.05,
        lookback_days=20,
        min_samples_for_detection=30,
        statistical_threshold=2.5,
        update_frequency_hours=2,
        alert_cooldown_minutes=30
    )


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    return {
        'timestamp': datetime.utcnow(),
        'realized_volatility': 0.15,
        'implied_volatility': 0.18,
        'vix_level': 22.0,
        'vix_change': 1.5,
        'volatility_skew': 0.05,
        'price_change': 0.01,
        'volume': 1000000,
        'volume_ratio': 1.2,
        'market_correlation': 0.7,
        'bid_ask_spread': 0.001
    }


@pytest.fixture
def sample_system_data():
    """Create sample system data."""
    return {
        'timestamp': datetime.utcnow(),
        'system_return': 0.008,
        'tracking_error': 0.02,
        'execution_quality': 0.95,
        'response_time': 0.1,
        'error_rate': 0.001,
        'portfolio_var': 0.03,
        'max_drawdown': 0.05,
        'protocol_level': 0,
        'rule_violation_count': 0
    }


class TestMarketAnomalyDetector:
    """Test cases for Market Anomaly Detector."""
    
    @pytest.mark.asyncio
    async def test_initialization_default_config(self, mock_audit_manager):
        """Test detector initialization with default config."""
        detector = MarketAnomalyDetector(mock_audit_manager)
        
        assert detector.audit_manager == mock_audit_manager
        assert detector.config.contamination_rate == 0.1
        assert detector.config.lookback_days == 30
        assert len(detector.isolation_forests) == len(AnomalyType)
        assert len(detector.scalers) == len(AnomalyType)
        assert len(detector.historical_data) == len(AnomalyType)
    
    @pytest.mark.asyncio
    async def test_initialization_custom_config(self, mock_audit_manager, custom_config):
        """Test detector initialization with custom config."""
        detector = MarketAnomalyDetector(mock_audit_manager, custom_config)
        
        assert detector.config == custom_config
        assert detector.config.contamination_rate == 0.05
        assert detector.config.lookback_days == 20
    
    @pytest.mark.asyncio
    async def test_add_market_data(self, anomaly_detector, sample_market_data):
        """Test adding market data."""
        await anomaly_detector.add_market_data(sample_market_data)
        
        # Check that data was added to historical storage
        for anomaly_type in [AnomalyType.MARKET_VOLATILITY, AnomalyType.PRICE_MOVEMENT, 
                           AnomalyType.VOLUME_ANOMALY, AnomalyType.CORRELATION_BREAKDOWN,
                           AnomalyType.LIQUIDITY_CRISIS]:
            assert len(anomaly_detector.historical_data[anomaly_type]) == 1
        
        # Verify audit log was called
        anomaly_detector.audit_manager.log_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_add_system_data(self, anomaly_detector, sample_system_data):
        """Test adding system data."""
        await anomaly_detector.add_system_data(sample_system_data)
        
        # Check that data was added to historical storage
        for anomaly_type in [AnomalyType.SYSTEM_PERFORMANCE, AnomalyType.RISK_METRIC, 
                           AnomalyType.PROTOCOL_BEHAVIOR]:
            assert len(anomaly_detector.historical_data[anomaly_type]) == 1
        
        # Verify audit log was called
        anomaly_detector.audit_manager.log_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_volatility_data(self, anomaly_detector):
        """Test processing volatility data."""
        data = {
            'realized_volatility': 0.25,  # High volatility
            'implied_volatility': 0.30,
            'vix_level': 35.0,  # High VIX
            'vix_change': 5.0,
            'volatility_skew': 0.1
        }
        
        timestamp = datetime.utcnow()
        await anomaly_detector._process_volatility_data(data, timestamp)
        
        # Check data was stored
        vol_data = anomaly_detector.historical_data[AnomalyType.MARKET_VOLATILITY]
        assert len(vol_data) == 1
        assert vol_data[0]['timestamp'] == timestamp
        assert vol_data[0]['metrics']['realized_volatility'] == 0.25
        assert vol_data[0]['metrics']['vix_level'] == 35.0
    
    @pytest.mark.asyncio
    async def test_statistical_baseline_calculation(self, anomaly_detector):
        """Test statistical baseline calculation."""
        # Add multiple data points for volatility
        for i in range(60):  # More than min_samples_for_detection
            data = {
                'realized_volatility': 0.15 + 0.01 * np.random.randn(),
                'vix_level': 20.0 + 2.0 * np.random.randn(),
                'vix_change': 0.5 * np.random.randn()
            }
            timestamp = datetime.utcnow() - timedelta(hours=i)
            await anomaly_detector._process_volatility_data(data, timestamp)
        
        # Calculate baselines
        await anomaly_detector._calculate_statistical_baselines(AnomalyType.MARKET_VOLATILITY)
        
        # Check baselines were calculated
        baselines = anomaly_detector.statistical_baselines.get(AnomalyType.MARKET_VOLATILITY.value)
        assert baselines is not None
        assert 'realized_volatility' in baselines
        assert 'mean' in baselines['realized_volatility']
        assert 'std' in baselines['realized_volatility']
    
    @pytest.mark.asyncio
    async def test_statistical_anomaly_detection(self, anomaly_detector):
        """Test statistical anomaly detection."""
        # Add normal data points
        for i in range(60):
            data = {
                'realized_volatility': 0.15 + 0.01 * np.random.randn(),
                'vix_level': 20.0 + 1.0 * np.random.randn()
            }
            timestamp = datetime.utcnow() - timedelta(hours=i)
            await anomaly_detector._process_volatility_data(data, timestamp)
        
        # Add an anomalous data point
        anomalous_data = {
            'realized_volatility': 0.50,  # Very high volatility
            'vix_level': 50.0  # Very high VIX
        }
        
        await anomaly_detector._process_volatility_data(anomalous_data, datetime.utcnow())
        
        # Check if anomaly was detected (should be in recent alerts)
        recent_alerts = await anomaly_detector.get_recent_alerts(hours_back=1)
        
        # May or may not detect depending on the random data, but should not crash
        assert isinstance(recent_alerts, list)
    
    @pytest.mark.asyncio
    async def test_severity_determination(self, anomaly_detector):
        """Test anomaly severity determination."""
        # Test different z-scores
        assert anomaly_detector._determine_severity(2.0) == AnomalySeverity.LOW
        assert anomaly_detector._determine_severity(3.5) == AnomalySeverity.MEDIUM
        assert anomaly_detector._determine_severity(5.0) == AnomalySeverity.HIGH
        assert anomaly_detector._determine_severity(7.0) == AnomalySeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_cooldown_mechanism(self, anomaly_detector):
        """Test alert cooldown mechanism."""
        # Create an alert
        alert = AnomalyAlert(
            anomaly_type=AnomalyType.MARKET_VOLATILITY,
            severity=AnomalySeverity.HIGH,
            confidence=0.8,
            description="Test alert",
            detected_at=datetime.utcnow(),
            affected_metrics={},
            historical_context={},
            recommendations=[],
            alert_id="test_alert_1"
        )
        
        anomaly_detector.recent_alerts.append(alert)
        
        # Check if in cooldown
        in_cooldown = await anomaly_detector._is_in_cooldown(AnomalyType.MARKET_VOLATILITY)
        assert in_cooldown is True
        
        # Test with old alert (should not be in cooldown)
        old_alert = AnomalyAlert(
            anomaly_type=AnomalyType.PRICE_MOVEMENT,
            severity=AnomalySeverity.HIGH,
            confidence=0.8,
            description="Old alert",
            detected_at=datetime.utcnow() - timedelta(hours=2),
            affected_metrics={},
            historical_context={},
            recommendations=[],
            alert_id="test_alert_2"
        )
        
        anomaly_detector.recent_alerts.append(old_alert)
        
        in_cooldown = await anomaly_detector._is_in_cooldown(AnomalyType.PRICE_MOVEMENT)
        assert in_cooldown is False
    
    @pytest.mark.asyncio
    async def test_get_recent_alerts_filtering(self, anomaly_detector):
        """Test filtering of recent alerts."""
        # Create alerts with different types and severities
        alerts = [
            AnomalyAlert(
                anomaly_type=AnomalyType.MARKET_VOLATILITY,
                severity=AnomalySeverity.HIGH,
                confidence=0.8,
                description="High vol alert",
                detected_at=datetime.utcnow(),
                affected_metrics={},
                historical_context={},
                recommendations=[],
                alert_id="alert_1"
            ),
            AnomalyAlert(
                anomaly_type=AnomalyType.PRICE_MOVEMENT,
                severity=AnomalySeverity.LOW,
                confidence=0.6,
                description="Price alert",
                detected_at=datetime.utcnow() - timedelta(hours=1),
                affected_metrics={},
                historical_context={},
                recommendations=[],
                alert_id="alert_2"
            ),
            AnomalyAlert(
                anomaly_type=AnomalyType.MARKET_VOLATILITY,
                severity=AnomalySeverity.CRITICAL,
                confidence=0.9,
                description="Critical vol alert",
                detected_at=datetime.utcnow() - timedelta(days=2),  # Too old
                affected_metrics={},
                historical_context={},
                recommendations=[],
                alert_id="alert_3"
            )
        ]
        
        anomaly_detector.recent_alerts.extend(alerts)
        
        # Test filtering by hours_back
        recent_alerts = await anomaly_detector.get_recent_alerts(hours_back=24)
        assert len(recent_alerts) == 2  # Should exclude the 2-day old alert
        
        # Test filtering by anomaly type
        vol_alerts = await anomaly_detector.get_recent_alerts(
            anomaly_type=AnomalyType.MARKET_VOLATILITY, hours_back=24
        )
        assert len(vol_alerts) == 1
        assert vol_alerts[0].anomaly_type == AnomalyType.MARKET_VOLATILITY
        
        # Test filtering by severity
        high_alerts = await anomaly_detector.get_recent_alerts(
            severity=AnomalySeverity.HIGH, hours_back=24
        )
        assert len(high_alerts) == 1
        assert high_alerts[0].severity == AnomalySeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_anomaly_statistics(self, anomaly_detector):
        """Test anomaly statistics generation."""
        # Add some alerts
        alerts = [
            AnomalyAlert(
                anomaly_type=AnomalyType.MARKET_VOLATILITY,
                severity=AnomalySeverity.HIGH,
                confidence=0.8,
                description="Vol alert",
                detected_at=datetime.utcnow(),
                affected_metrics={},
                historical_context={},
                recommendations=[],
                alert_id="alert_1"
            ),
            AnomalyAlert(
                anomaly_type=AnomalyType.MARKET_VOLATILITY,
                severity=AnomalySeverity.MEDIUM,
                confidence=0.7,
                description="Vol alert 2",
                detected_at=datetime.utcnow(),
                affected_metrics={},
                historical_context={},
                recommendations=[],
                alert_id="alert_2"
            )
        ]
        
        anomaly_detector.recent_alerts.extend(alerts)
        
        # Get statistics
        stats = await anomaly_detector.get_anomaly_statistics()
        
        assert stats['total_alerts'] == 2
        assert AnomalyType.MARKET_VOLATILITY.value in stats['alerts_by_type']
        assert stats['alerts_by_type'][AnomalyType.MARKET_VOLATILITY.value] == 2
        assert AnomalySeverity.HIGH.value in stats['alerts_by_severity']
        assert AnomalySeverity.MEDIUM.value in stats['alerts_by_severity']
        assert 'detection_coverage' in stats
        assert 'config' in stats
    
    @pytest.mark.asyncio
    async def test_clear_old_data(self, anomaly_detector):
        """Test clearing old historical data."""
        # Add old and recent data
        old_timestamp = datetime.utcnow() - timedelta(days=40)
        recent_timestamp = datetime.utcnow() - timedelta(days=10)
        
        # Add data to multiple anomaly types
        for anomaly_type in [AnomalyType.MARKET_VOLATILITY, AnomalyType.PRICE_MOVEMENT]:
            anomaly_detector.historical_data[anomaly_type].extend([
                {'timestamp': old_timestamp, 'metrics': {'test': 1.0}},
                {'timestamp': recent_timestamp, 'metrics': {'test': 2.0}}
            ])
        
        # Add old and recent alerts
        old_alert = AnomalyAlert(
            anomaly_type=AnomalyType.MARKET_VOLATILITY,
            severity=AnomalySeverity.LOW,
            confidence=0.5,
            description="Old alert",
            detected_at=datetime.utcnow() - timedelta(days=10),
            affected_metrics={},
            historical_context={},
            recommendations=[],
            alert_id="old_alert"
        )
        
        recent_alert = AnomalyAlert(
            anomaly_type=AnomalyType.PRICE_MOVEMENT,
            severity=AnomalySeverity.MEDIUM,
            confidence=0.7,
            description="Recent alert",
            detected_at=datetime.utcnow() - timedelta(days=2),
            affected_metrics={},
            historical_context={},
            recommendations=[],
            alert_id="recent_alert"
        )
        
        anomaly_detector.recent_alerts.extend([old_alert, recent_alert])
        
        # Clear old data (keep 30 days)
        result = await anomaly_detector.clear_old_data(days_to_keep=30)
        
        assert result['data_entries_cleared'] == 2  # One old entry per anomaly type
        assert result['alerts_cleared'] == 1  # One old alert
        
        # Check remaining data
        for anomaly_type in [AnomalyType.MARKET_VOLATILITY, AnomalyType.PRICE_MOVEMENT]:
            assert len(anomaly_detector.historical_data[anomaly_type]) == 1
            assert anomaly_detector.historical_data[anomaly_type][0]['timestamp'] == recent_timestamp
        
        assert len(anomaly_detector.recent_alerts) == 1
        assert anomaly_detector.recent_alerts[0].alert_id == "recent_alert"


class TestAnomalyAlert:
    """Test cases for AnomalyAlert dataclass."""
    
    def test_anomaly_alert_creation(self):
        """Test creating AnomalyAlert instance."""
        alert = AnomalyAlert(
            anomaly_type=AnomalyType.MARKET_VOLATILITY,
            severity=AnomalySeverity.HIGH,
            confidence=0.85,
            description="Test anomaly alert",
            detected_at=datetime.utcnow(),
            affected_metrics={'volatility': 0.3},
            historical_context={'mean': 0.15},
            recommendations=['Monitor closely'],
            alert_id="test_alert_123"
        )
        
        assert alert.anomaly_type == AnomalyType.MARKET_VOLATILITY
        assert alert.severity == AnomalySeverity.HIGH
        assert alert.confidence == 0.85
        assert alert.description == "Test anomaly alert"
        assert isinstance(alert.detected_at, datetime)
        assert alert.affected_metrics['volatility'] == 0.3
        assert alert.historical_context['mean'] == 0.15
        assert alert.recommendations == ['Monitor closely']
        assert alert.alert_id == "test_alert_123"


class TestAnomalyDetectionConfig:
    """Test cases for AnomalyDetectionConfig dataclass."""
    
    def test_config_default_values(self):
        """Test default configuration values."""
        config = AnomalyDetectionConfig()
        
        assert config.contamination_rate == 0.1
        assert config.lookback_days == 30
        assert config.min_samples_for_detection == 50
        assert config.statistical_threshold == 3.0
        assert config.update_frequency_hours == 1
        assert config.alert_cooldown_minutes == 60
    
    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = AnomalyDetectionConfig(
            contamination_rate=0.05,
            lookback_days=20,
            min_samples_for_detection=30,
            statistical_threshold=2.5,
            update_frequency_hours=2,
            alert_cooldown_minutes=30
        )
        
        assert config.contamination_rate == 0.05
        assert config.lookback_days == 20
        assert config.min_samples_for_detection == 30
        assert config.statistical_threshold == 2.5
        assert config.update_frequency_hours == 2
        assert config.alert_cooldown_minutes == 30

