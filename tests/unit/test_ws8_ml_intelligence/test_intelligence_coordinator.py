"""
Unit tests for Intelligence Coordinator
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.ws8_ml_intelligence.intelligence_coordinator import (
    IntelligenceCoordinator, IntelligenceReport, SystemIntelligence, IntelligenceMode
)
from src.ws8_ml_intelligence.learning_engine.adaptive_learning_engine import LearningInsight
from src.ws8_ml_intelligence.anomaly_detection.market_anomaly_detector import AnomalyAlert, AnomalyType, AnomalySeverity
from src.ws8_ml_intelligence.pattern_recognition.pattern_engine import PatternMatch, Pattern, PatternType
from src.ws8_ml_intelligence.predictive_analytics.predictive_engine import Forecast
from src.ws1_rules_engine.audit import AuditTrailManager


@pytest.fixture
def mock_audit_manager():
    """Create mock audit manager."""
    audit_manager = Mock(spec=AuditTrailManager)
    audit_manager.log_event = AsyncMock()
    return audit_manager


@pytest.fixture
def intelligence_coordinator(mock_audit_manager):
    """Create intelligence coordinator instance."""
    return IntelligenceCoordinator(mock_audit_manager)


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    return {
        'timestamp': datetime.utcnow(),
        'market_return': 0.01,
        'market_volatility': 0.15,
        'vix_level': 22.0,
        'volume_ratio': 1.2,
        'correlation_level': 0.7
    }


@pytest.fixture
def sample_system_data():
    """Create sample system data."""
    return {
        'timestamp': datetime.utcnow(),
        'week_type': 'normal',
        'week_performance': 'average',
        'weekly_return': 0.008,
        'sharpe_ratio': 1.5,
        'max_drawdown': 0.02,
        'portfolio_volatility': 0.12,
        'protocol_level': 'L0',
        'system_actions': ['position_opened'],
        'protocol_success_score': 0.8
    }


@pytest.fixture
def sample_learning_insight():
    """Create sample learning insight."""
    return LearningInsight(
        insight_type="performance_pattern",
        confidence=0.85,
        description="Strong performance pattern detected",
        supporting_data={'pattern_strength': 0.9},
        recommendations=['Continue current strategy', 'Monitor closely'],
        generated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_anomaly_alert():
    """Create sample anomaly alert."""
    return AnomalyAlert(
        anomaly_type=AnomalyType.MARKET_VOLATILITY,
        severity=AnomalySeverity.HIGH,
        confidence=0.8,
        description="High volatility anomaly detected",
        detected_at=datetime.utcnow(),
        affected_metrics={'volatility': 0.3},
        historical_context={'mean': 0.15},
        recommendations=['Increase monitoring', 'Review risk parameters'],
        alert_id="alert_123"
    )


@pytest.fixture
def sample_pattern_match():
    """Create sample pattern match."""
    pattern = Pattern(
        pattern_type=PatternType.MARKET_REGIME,
        pattern_id="pattern_123",
        name="High Volatility Regime",
        description="Market in high volatility state",
        confidence=0.8,
        characteristics={'volatility_mean': 0.25},
        historical_occurrences=15,
        success_rate=0.7,
        average_duration=timedelta(days=5),
        created_at=datetime.utcnow()
    )
    
    return PatternMatch(
        pattern=pattern,
        match_confidence=0.85,
        match_strength=0.9,
        current_data={'volatility': 0.26},
        expected_outcomes={'success_probability': 0.7},
        recommendations=['Monitor pattern development'],
        matched_at=datetime.utcnow()
    )


@pytest.fixture
def sample_forecast():
    """Create sample forecast."""
    return Forecast(
        forecast_id="forecast_123",
        forecast_name="Weekly Performance Forecast",
        predictions=[],  # Simplified for testing
        forecast_horizon=timedelta(days=7),
        overall_confidence=0.75,
        key_assumptions=['Market conditions remain stable'],
        risk_factors=['Model uncertainty'],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestIntelligenceCoordinator:
    """Test cases for Intelligence Coordinator."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_audit_manager):
        """Test intelligence coordinator initialization."""
        coordinator = IntelligenceCoordinator(mock_audit_manager)
        
        assert coordinator.audit_manager == mock_audit_manager
        assert coordinator.update_frequency_minutes == 60
        assert coordinator.report_generation_frequency_hours == 24
        assert coordinator.operation_mode == IntelligenceMode.COMPREHENSIVE
        assert coordinator.current_intelligence is None
        assert len(coordinator.intelligence_reports) == 0
        assert len(coordinator.background_tasks) == 0
        
        # Check that component engines are initialized
        assert coordinator.learning_engine is not None
        assert coordinator.anomaly_detector is not None
        assert coordinator.pattern_engine is not None
        assert coordinator.predictive_engine is not None
    
    @pytest.mark.asyncio
    async def test_initialization_custom_params(self, mock_audit_manager):
        """Test initialization with custom parameters."""
        coordinator = IntelligenceCoordinator(
            mock_audit_manager,
            update_frequency_minutes=30,
            report_generation_frequency_hours=12
        )
        
        assert coordinator.update_frequency_minutes == 30
        assert coordinator.report_generation_frequency_hours == 12
    
    @pytest.mark.asyncio
    async def test_process_market_data(self, intelligence_coordinator, sample_market_data):
        """Test processing market data."""
        with patch.object(intelligence_coordinator.anomaly_detector, 'add_market_data', new_callable=AsyncMock) as mock_anomaly, \
             patch.object(intelligence_coordinator.pattern_engine, 'add_historical_data', new_callable=AsyncMock) as mock_pattern, \
             patch.object(intelligence_coordinator.predictive_engine, 'add_training_data', new_callable=AsyncMock) as mock_predictive, \
             patch.object(intelligence_coordinator, '_update_system_intelligence', new_callable=AsyncMock) as mock_update:
            
            await intelligence_coordinator.process_market_data(sample_market_data)
            
            # Verify all components were called
            mock_anomaly.assert_called_once_with(sample_market_data)
            mock_pattern.assert_called_once_with(sample_market_data)
            mock_predictive.assert_called_once_with(sample_market_data)
            mock_update.assert_called_once()
            
            # Verify audit log was called
            intelligence_coordinator.audit_manager.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_system_data(self, intelligence_coordinator, sample_system_data):
        """Test processing system data."""
        with patch.object(intelligence_coordinator.anomaly_detector, 'add_system_data', new_callable=AsyncMock) as mock_anomaly, \
             patch.object(intelligence_coordinator.learning_engine, 'add_learning_data', new_callable=AsyncMock) as mock_learning, \
             patch.object(intelligence_coordinator.pattern_engine, 'add_historical_data', new_callable=AsyncMock) as mock_pattern, \
             patch.object(intelligence_coordinator.predictive_engine, 'add_training_data', new_callable=AsyncMock) as mock_predictive, \
             patch.object(intelligence_coordinator, '_update_system_intelligence', new_callable=AsyncMock) as mock_update:
            
            await intelligence_coordinator.process_system_data(sample_system_data)
            
            # Verify components were called
            mock_anomaly.assert_called_once_with(sample_system_data)
            mock_learning.assert_called_once()  # Should be called due to complete learning data
            mock_pattern.assert_called_once_with(sample_system_data)
            mock_predictive.assert_called_once_with(sample_system_data)
            mock_update.assert_called_once()
            
            # Verify audit log was called
            intelligence_coordinator.audit_manager.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_is_complete_learning_data(self, intelligence_coordinator):
        """Test checking for complete learning data."""
        # Complete data
        complete_data = {
            'week_type': 'normal',
            'week_performance': 'average',
            'weekly_return': 0.008
        }
        assert intelligence_coordinator._is_complete_learning_data(complete_data) is True
        
        # Incomplete data
        incomplete_data = {
            'week_type': 'normal',
            'weekly_return': 0.008
            # Missing week_performance
        }
        assert intelligence_coordinator._is_complete_learning_data(incomplete_data) is False
        
        # Empty data
        assert intelligence_coordinator._is_complete_learning_data({}) is False
    
    @pytest.mark.asyncio
    async def test_update_system_intelligence(self, intelligence_coordinator):
        """Test updating system intelligence."""
        # Mock component responses
        with patch.object(intelligence_coordinator.anomaly_detector, 'get_recent_alerts', new_callable=AsyncMock) as mock_alerts, \
             patch.object(intelligence_coordinator.pattern_engine, 'get_recent_matches', new_callable=AsyncMock) as mock_patterns, \
             patch.object(intelligence_coordinator.predictive_engine, 'get_active_forecasts', new_callable=AsyncMock) as mock_forecasts, \
             patch.object(intelligence_coordinator.learning_engine, 'get_model_performance', new_callable=AsyncMock) as mock_performance:
            
            mock_alerts.return_value = []
            mock_patterns.return_value = []
            mock_forecasts.return_value = []
            mock_performance.return_value = {}
            
            await intelligence_coordinator._update_system_intelligence()
            
            # Check that system intelligence was created
            assert intelligence_coordinator.current_intelligence is not None
            assert isinstance(intelligence_coordinator.current_intelligence, SystemIntelligence)
            assert isinstance(intelligence_coordinator.current_intelligence.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_generate_intelligence_report(self, intelligence_coordinator, sample_learning_insight, 
                                              sample_anomaly_alert, sample_pattern_match, sample_forecast):
        """Test generating intelligence report."""
        # Set up mock data
        intelligence_coordinator.learning_engine.insights_cache = [sample_learning_insight]
        
        with patch.object(intelligence_coordinator.anomaly_detector, 'get_recent_alerts', new_callable=AsyncMock) as mock_alerts, \
             patch.object(intelligence_coordinator.pattern_engine, 'get_recent_matches', new_callable=AsyncMock) as mock_patterns, \
             patch.object(intelligence_coordinator.predictive_engine, 'get_active_forecasts', new_callable=AsyncMock) as mock_forecasts:
            
            mock_alerts.return_value = [sample_anomaly_alert]
            mock_patterns.return_value = [sample_pattern_match]
            mock_forecasts.return_value = [sample_forecast]
            
            report = await intelligence_coordinator.generate_intelligence_report("test_report")
            
            # Verify report structure
            assert isinstance(report, IntelligenceReport)
            assert report.report_type == "test_report"
            assert len(report.learning_insights) == 1
            assert len(report.anomaly_alerts) == 1
            assert len(report.pattern_matches) == 1
            assert len(report.forecasts) == 1
            assert len(report.key_findings) > 0
            assert len(report.recommendations) > 0
            assert 0.0 <= report.confidence_score <= 1.0
            assert report.risk_assessment in ["LOW", "MEDIUM", "HIGH"]
            
            # Verify report was stored
            assert len(intelligence_coordinator.intelligence_reports) == 1
            
            # Verify audit log was called
            intelligence_coordinator.audit_manager.log_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_immediate_actions(self, intelligence_coordinator, sample_anomaly_alert, 
                                            sample_pattern_match, sample_forecast):
        """Test generating immediate actions."""
        # High severity anomaly
        high_severity_alert = sample_anomaly_alert
        high_severity_alert.severity = AnomalySeverity.CRITICAL
        
        # High confidence pattern
        high_confidence_pattern = sample_pattern_match
        high_confidence_pattern.match_confidence = 0.9
        
        # Low confidence forecast
        low_confidence_forecast = sample_forecast
        low_confidence_forecast.overall_confidence = 0.4
        
        actions = intelligence_coordinator._generate_immediate_actions(
            [high_severity_alert], [high_confidence_pattern], [low_confidence_forecast]
        )
        
        assert len(actions) > 0
        assert any("high-severity" in action.lower() for action in actions)
        assert any("high-confidence" in action.lower() for action in actions)
        assert any("low confidence" in action.lower() for action in actions)
    
    @pytest.mark.asyncio
    async def test_generate_monitoring_priorities(self, intelligence_coordinator, sample_anomaly_alert, 
                                                sample_pattern_match):
        """Test generating monitoring priorities."""
        priorities = intelligence_coordinator._generate_monitoring_priorities(
            [sample_anomaly_alert], [sample_pattern_match]
        )
        
        assert len(priorities) > 0
        assert len(priorities) <= 5  # Should limit to top 5
        
        # Should include anomaly and pattern types
        priority_text = " ".join(priorities).lower()
        assert "volatility" in priority_text or "market" in priority_text
    
    @pytest.mark.asyncio
    async def test_generate_risk_factors(self, intelligence_coordinator, sample_anomaly_alert, 
                                       sample_pattern_match, sample_forecast):
        """Test generating risk factors."""
        # Create multiple anomalies to trigger risk
        anomalies = [sample_anomaly_alert] * 6  # More than 5
        
        # Low confidence pattern
        low_confidence_pattern = sample_pattern_match
        low_confidence_pattern.match_confidence = 0.4
        
        # Low confidence forecast
        low_confidence_forecast = sample_forecast
        low_confidence_forecast.overall_confidence = 0.4
        
        risk_factors = intelligence_coordinator._generate_risk_factors(
            anomalies, [low_confidence_pattern], [low_confidence_forecast]
        )
        
        assert len(risk_factors) > 0
        
        # Should mention multiple anomalies
        risk_text = " ".join(risk_factors).lower()
        assert "anomal" in risk_text or "uncertainty" in risk_text
    
    @pytest.mark.asyncio
    async def test_calculate_overall_confidence(self, intelligence_coordinator, sample_learning_insight,
                                              sample_anomaly_alert, sample_pattern_match, sample_forecast):
        """Test calculating overall confidence score."""
        confidence = intelligence_coordinator._calculate_overall_confidence(
            [sample_learning_insight], [sample_anomaly_alert], [sample_pattern_match], [sample_forecast]
        )
        
        assert 0.0 <= confidence <= 1.0
        
        # Test with empty inputs
        confidence_empty = intelligence_coordinator._calculate_overall_confidence([], [], [], [])
        assert confidence_empty == 0.5  # Should return neutral confidence
    
    @pytest.mark.asyncio
    async def test_generate_risk_assessment(self, intelligence_coordinator, sample_anomaly_alert,
                                          sample_pattern_match, sample_forecast):
        """Test generating risk assessment."""
        # Low risk scenario
        low_risk_assessment = intelligence_coordinator._generate_risk_assessment([], [], [])
        assert "LOW" in low_risk_assessment
        
        # High risk scenario
        critical_alert = sample_anomaly_alert
        critical_alert.severity = AnomalySeverity.CRITICAL
        
        high_risk_assessment = intelligence_coordinator._generate_risk_assessment(
            [critical_alert] * 3, [], []  # Multiple critical alerts
        )
        assert "HIGH" in high_risk_assessment
    
    @pytest.mark.asyncio
    async def test_get_current_intelligence(self, intelligence_coordinator):
        """Test getting current intelligence."""
        # Initially should be None
        intelligence = await intelligence_coordinator.get_current_intelligence()
        assert intelligence is None
        
        # After update should return intelligence
        with patch.object(intelligence_coordinator, '_update_system_intelligence', new_callable=AsyncMock):
            await intelligence_coordinator._update_system_intelligence()
            
            if intelligence_coordinator.current_intelligence:
                intelligence = await intelligence_coordinator.get_current_intelligence()
                assert isinstance(intelligence, SystemIntelligence)
    
    @pytest.mark.asyncio
    async def test_get_recent_reports(self, intelligence_coordinator):
        """Test getting recent reports."""
        # Create test reports
        old_report = IntelligenceReport(
            report_id="old_report",
            report_type="test",
            generated_at=datetime.utcnow() - timedelta(days=10),
            learning_insights=[],
            anomaly_alerts=[],
            pattern_matches=[],
            forecasts=[],
            key_findings=[],
            recommendations=[],
            confidence_score=0.5,
            risk_assessment="LOW"
        )
        
        recent_report = IntelligenceReport(
            report_id="recent_report",
            report_type="test",
            generated_at=datetime.utcnow() - timedelta(days=2),
            learning_insights=[],
            anomaly_alerts=[],
            pattern_matches=[],
            forecasts=[],
            key_findings=[],
            recommendations=[],
            confidence_score=0.7,
            risk_assessment="MEDIUM"
        )
        
        intelligence_coordinator.intelligence_reports.extend([old_report, recent_report])
        
        # Get recent reports (last 7 days)
        recent_reports = await intelligence_coordinator.get_recent_reports(days_back=7)
        
        assert len(recent_reports) == 1
        assert recent_reports[0].report_id == "recent_report"
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, intelligence_coordinator):
        """Test getting system status."""
        with patch.object(intelligence_coordinator.learning_engine, 'get_model_performance', new_callable=AsyncMock) as mock_learning, \
             patch.object(intelligence_coordinator.anomaly_detector, 'get_anomaly_statistics', new_callable=AsyncMock) as mock_anomaly, \
             patch.object(intelligence_coordinator.pattern_engine, 'get_pattern_statistics', new_callable=AsyncMock) as mock_pattern, \
             patch.object(intelligence_coordinator.predictive_engine, 'get_model_performance_summary', new_callable=AsyncMock) as mock_predictive:
            
            mock_learning.return_value = {}
            mock_anomaly.return_value = {'total_alerts': 0}
            mock_pattern.return_value = {'total_patterns': 0}
            mock_predictive.return_value = {'total_models': 0}
            
            status = await intelligence_coordinator.get_system_status()
            
            assert 'intelligence_coordinator' in status
            assert 'learning_engine' in status
            assert 'anomaly_detector' in status
            assert 'pattern_engine' in status
            assert 'predictive_engine' in status
            
            # Check coordinator status
            coordinator_status = status['intelligence_coordinator']
            assert coordinator_status['status'] == 'active'
            assert coordinator_status['operation_mode'] == IntelligenceMode.COMPREHENSIVE.value
    
    @pytest.mark.asyncio
    async def test_export_intelligence_data(self, intelligence_coordinator):
        """Test exporting intelligence data."""
        with patch.object(intelligence_coordinator, 'get_system_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {'test': 'status'}
            
            export_data = await intelligence_coordinator.export_intelligence_data()
            
            assert 'current_intelligence' in export_data
            assert 'recent_reports' in export_data
            assert 'system_status' in export_data
            assert 'export_timestamp' in export_data
            
            # Check timestamp format
            assert isinstance(export_data['export_timestamp'], str)


class TestIntelligenceReport:
    """Test cases for IntelligenceReport dataclass."""
    
    def test_intelligence_report_creation(self):
        """Test creating IntelligenceReport instance."""
        report = IntelligenceReport(
            report_id="test_report_123",
            report_type="comprehensive",
            generated_at=datetime.utcnow(),
            learning_insights=[],
            anomaly_alerts=[],
            pattern_matches=[],
            forecasts=[],
            key_findings=["Finding 1", "Finding 2"],
            recommendations=["Recommendation 1"],
            confidence_score=0.85,
            risk_assessment="MEDIUM"
        )
        
        assert report.report_id == "test_report_123"
        assert report.report_type == "comprehensive"
        assert isinstance(report.generated_at, datetime)
        assert len(report.key_findings) == 2
        assert len(report.recommendations) == 1
        assert report.confidence_score == 0.85
        assert report.risk_assessment == "MEDIUM"


class TestSystemIntelligence:
    """Test cases for SystemIntelligence dataclass."""
    
    def test_system_intelligence_creation(self):
        """Test creating SystemIntelligence instance."""
        intelligence = SystemIntelligence(
            timestamp=datetime.utcnow(),
            market_conditions={'volatility': 'normal'},
            system_performance={'status': 'good'},
            risk_metrics={'risk_level': 'low'},
            active_patterns=['pattern1', 'pattern2'],
            anomaly_count=2,
            forecast_confidence=0.8,
            learning_progress={'model1': 0.7},
            immediate_actions=['action1'],
            monitoring_priorities=['priority1'],
            risk_factors=['factor1']
        )
        
        assert isinstance(intelligence.timestamp, datetime)
        assert intelligence.market_conditions['volatility'] == 'normal'
        assert intelligence.system_performance['status'] == 'good'
        assert intelligence.risk_metrics['risk_level'] == 'low'
        assert len(intelligence.active_patterns) == 2
        assert intelligence.anomaly_count == 2
        assert intelligence.forecast_confidence == 0.8
        assert intelligence.learning_progress['model1'] == 0.7
        assert len(intelligence.immediate_actions) == 1
        assert len(intelligence.monitoring_priorities) == 1
        assert len(intelligence.risk_factors) == 1

