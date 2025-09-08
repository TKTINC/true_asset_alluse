"""
Unit tests for Adaptive Learning Engine
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import numpy as np

from src.ws8_ml_intelligence.learning_engine.adaptive_learning_engine import (
    AdaptiveLearningEngine, LearningData, LearningMode, LearningInsight
)
from src.ws1_rules_engine.constitution.week_classification import WeekType, WeekPerformance
from src.ws1_rules_engine.audit import AuditTrailManager


@pytest.fixture
def mock_audit_manager():
    """Create mock audit manager."""
    audit_manager = Mock(spec=AuditTrailManager)
    audit_manager.log_event = AsyncMock()
    return audit_manager


@pytest.fixture
def learning_engine(mock_audit_manager):
    """Create learning engine instance."""
    return AdaptiveLearningEngine(mock_audit_manager)


@pytest.fixture
def sample_learning_data():
    """Create sample learning data."""
    return LearningData(
        timestamp=datetime.utcnow(),
        week_type=WeekType.NORMAL,
        week_performance=WeekPerformance.AVERAGE,
        market_data={
            'market_return': 0.01,
            'market_volatility': 0.15,
            'vix_level': 20.0,
            'volume_ratio': 1.2
        },
        performance_metrics={
            'weekly_return': 0.008,
            'sharpe_ratio': 1.5,
            'max_drawdown': 0.02
        },
        risk_metrics={
            'portfolio_volatility': 0.12,
            'var_95': 0.03,
            'concentration_risk': 0.25
        },
        protocol_level='L0',
        system_actions=['position_opened', 'risk_checked'],
        outcomes={
            'weekly_return': 0.008,
            'realized_volatility': 0.11,
            'protocol_success_score': 0.8
        }
    )


class TestAdaptiveLearningEngine:
    """Test cases for Adaptive Learning Engine."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_audit_manager):
        """Test learning engine initialization."""
        engine = AdaptiveLearningEngine(mock_audit_manager)
        
        assert engine.audit_manager == mock_audit_manager
        assert len(engine.models) == len(LearningMode)
        assert len(engine.scalers) == len(LearningMode)
        assert len(engine.learning_data) == 0
        assert len(engine.insights_cache) == 0
    
    @pytest.mark.asyncio
    async def test_add_learning_data(self, learning_engine, sample_learning_data):
        """Test adding learning data."""
        await learning_engine.add_learning_data(sample_learning_data)
        
        assert len(learning_engine.learning_data) == 1
        assert learning_engine.learning_data[0] == sample_learning_data
        
        # Verify audit log was called
        learning_engine.audit_manager.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_week_type_encoding(self, learning_engine):
        """Test week type encoding."""
        # Test all week types
        week_types = [
            WeekType.NORMAL, WeekType.VOLATILE, WeekType.TRENDING,
            WeekType.CONSOLIDATION, WeekType.EARNINGS, WeekType.EXPIRATION,
            WeekType.HOLIDAY, WeekType.EVENT_DRIVEN, WeekType.CRISIS, WeekType.RECOVERY
        ]
        
        for week_type in week_types:
            encoded = learning_engine._encode_week_type(week_type)
            assert isinstance(encoded, int)
            assert 0 <= encoded <= 9
    
    @pytest.mark.asyncio
    async def test_protocol_level_encoding(self, learning_engine):
        """Test protocol level encoding."""
        levels = ['L0', 'L1', 'L2', 'L3']
        expected = [0, 1, 2, 3]
        
        for level, expected_val in zip(levels, expected):
            encoded = learning_engine._encode_protocol_level(level)
            assert encoded == expected_val
    
    @pytest.mark.asyncio
    async def test_feature_columns_definition(self, learning_engine):
        """Test feature columns are properly defined."""
        for mode in LearningMode:
            assert mode in learning_engine.feature_columns
            assert len(learning_engine.feature_columns[mode]) > 0
            
            # Check that all feature names are strings
            for feature in learning_engine.feature_columns[mode]:
                assert isinstance(feature, str)
                assert len(feature) > 0
    
    @pytest.mark.asyncio
    async def test_model_initialization(self, learning_engine):
        """Test that models are properly initialized."""
        for mode in LearningMode:
            assert mode in learning_engine.models
            assert mode in learning_engine.scalers
            
            # Check model has required methods
            model = learning_engine.models[mode]
            assert hasattr(model, 'fit')
            assert hasattr(model, 'predict')
    
    @pytest.mark.asyncio
    async def test_prepare_training_data_insufficient_data(self, learning_engine):
        """Test training data preparation with insufficient data."""
        # Test with empty data
        X, y = learning_engine._prepare_training_data(LearningMode.WEEK_TYPE_LEARNING)
        assert len(X) == 0
        assert len(y) == 0
    
    @pytest.mark.asyncio
    async def test_prepare_training_data_with_data(self, learning_engine, sample_learning_data):
        """Test training data preparation with actual data."""
        # Add multiple data points
        for i in range(5):
            data = LearningData(
                timestamp=datetime.utcnow() - timedelta(days=i),
                week_type=WeekType.NORMAL if i % 2 == 0 else WeekType.VOLATILE,
                week_performance=WeekPerformance.AVERAGE,
                market_data={
                    'market_return': 0.01 * (i + 1),
                    'market_volatility': 0.15 + 0.01 * i,
                    'vix_level': 20.0 + i,
                    'volume_ratio': 1.0 + 0.1 * i
                },
                performance_metrics={
                    'weekly_return': 0.008 + 0.001 * i,
                    'sharpe_ratio': 1.5 - 0.1 * i,
                    'max_drawdown': 0.02 + 0.005 * i
                },
                risk_metrics={
                    'portfolio_volatility': 0.12 + 0.01 * i,
                    'var_95': 0.03 + 0.005 * i,
                    'concentration_risk': 0.25 + 0.05 * i
                },
                protocol_level='L0',
                system_actions=[],
                outcomes={
                    'weekly_return': 0.008 + 0.001 * i,
                    'realized_volatility': 0.11 + 0.01 * i,
                    'protocol_success_score': 0.8 - 0.05 * i
                }
            )
            learning_engine.learning_data.append(data)
        
        # Test preparation for different modes
        for mode in LearningMode:
            X, y = learning_engine._prepare_training_data(mode)
            
            if len(X) > 0:  # Some modes might not have sufficient data
                assert X.shape[0] == len(learning_engine.learning_data)
                assert len(y) == len(learning_engine.learning_data)
                assert X.shape[1] == len(learning_engine.feature_columns[mode])
    
    @pytest.mark.asyncio
    async def test_predict_week_type_no_model(self, learning_engine):
        """Test week type prediction with no trained model."""
        market_data = {
            'market_volatility': 0.2,
            'vix_level': 25.0,
            'earnings_density': 0.1
        }
        
        week_type, confidence = await learning_engine.predict_week_type(market_data)
        
        # Should return default values when no model is trained
        assert week_type == WeekType.NORMAL
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_predict_performance_no_model(self, learning_engine):
        """Test performance prediction with no trained model."""
        market_data = {'market_volatility': 0.15}
        portfolio_data = {'portfolio_beta': 1.0}
        
        performance, confidence = await learning_engine.predict_performance(market_data, portfolio_data)
        
        # Should return default values when no model is trained
        assert performance == 0.0
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_get_model_performance_empty(self, learning_engine):
        """Test getting model performance when no models are trained."""
        performance = await learning_engine.get_model_performance()
        
        # Should return empty dict when no models are trained
        assert isinstance(performance, dict)
        assert len(performance) == 0
    
    @pytest.mark.asyncio
    async def test_clear_learning_data(self, learning_engine):
        """Test clearing old learning data."""
        # Add some old and recent data
        old_data = LearningData(
            timestamp=datetime.utcnow() - timedelta(days=40),
            week_type=WeekType.NORMAL,
            week_performance=WeekPerformance.AVERAGE,
            market_data={},
            performance_metrics={},
            risk_metrics={},
            protocol_level='L0',
            system_actions=[],
            outcomes={}
        )
        
        recent_data = LearningData(
            timestamp=datetime.utcnow() - timedelta(days=10),
            week_type=WeekType.NORMAL,
            week_performance=WeekPerformance.AVERAGE,
            market_data={},
            performance_metrics={},
            risk_metrics={},
            protocol_level='L0',
            system_actions=[],
            outcomes={}
        )
        
        learning_engine.learning_data.extend([old_data, recent_data])
        
        # Clear data older than 30 days
        cleared_count = await learning_engine.clear_learning_data(keep_recent_days=30)
        
        assert cleared_count == 1
        assert len(learning_engine.learning_data) == 1
        assert learning_engine.learning_data[0] == recent_data
    
    @pytest.mark.asyncio
    async def test_insights_cache_management(self, learning_engine):
        """Test insights cache management."""
        # Create mock insights
        insights = []
        for i in range(150):  # More than the cache limit of 100
            insight = LearningInsight(
                insight_type="test",
                confidence=0.8,
                description=f"Test insight {i}",
                supporting_data={},
                recommendations=[],
                generated_at=datetime.utcnow()
            )
            insights.append(insight)
        
        learning_engine.insights_cache = insights
        
        # Trigger cache cleanup by adding data
        await learning_engine.add_learning_data(sample_learning_data)
        
        # Should keep only the last 100 insights
        assert len(learning_engine.insights_cache) <= 100


class TestLearningData:
    """Test cases for LearningData dataclass."""
    
    def test_learning_data_creation(self):
        """Test creating LearningData instance."""
        data = LearningData(
            timestamp=datetime.utcnow(),
            week_type=WeekType.NORMAL,
            week_performance=WeekPerformance.AVERAGE,
            market_data={'test': 1.0},
            performance_metrics={'test': 2.0},
            risk_metrics={'test': 3.0},
            protocol_level='L0',
            system_actions=['test_action'],
            outcomes={'test': 4.0}
        )
        
        assert isinstance(data.timestamp, datetime)
        assert data.week_type == WeekType.NORMAL
        assert data.week_performance == WeekPerformance.AVERAGE
        assert data.market_data['test'] == 1.0
        assert data.performance_metrics['test'] == 2.0
        assert data.risk_metrics['test'] == 3.0
        assert data.protocol_level == 'L0'
        assert data.system_actions == ['test_action']
        assert data.outcomes['test'] == 4.0


class TestLearningInsight:
    """Test cases for LearningInsight dataclass."""
    
    def test_learning_insight_creation(self):
        """Test creating LearningInsight instance."""
        insight = LearningInsight(
            insight_type="test_insight",
            confidence=0.85,
            description="Test description",
            supporting_data={'key': 'value'},
            recommendations=['recommendation1', 'recommendation2'],
            generated_at=datetime.utcnow()
        )
        
        assert insight.insight_type == "test_insight"
        assert insight.confidence == 0.85
        assert insight.description == "Test description"
        assert insight.supporting_data['key'] == 'value'
        assert len(insight.recommendations) == 2
        assert isinstance(insight.generated_at, datetime)

