"""
Data Processing Utilities for WS8 ML Intelligence

Utilities for processing market data, system data, and feature extraction
for machine learning models.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessedData:
    """Container for processed data."""
    features: Dict[str, float]
    metadata: Dict[str, Any]
    timestamp: datetime
    data_quality_score: float


class DataProcessor:
    """
    Processes raw market and system data for ML models.
    
    Handles data cleaning, normalization, feature engineering,
    and quality assessment.
    """
    
    def __init__(self,
                 lookback_periods: int = 20,
                 quality_threshold: float = 0.7):
        """Initialize the data processor."""
        self.lookback_periods = lookback_periods
        self.quality_threshold = quality_threshold
        
        # Data storage for rolling calculations
        self.historical_data: List[Dict[str, Any]] = []
        
        logger.info("DataProcessor initialized successfully")
    
    def process_market_data(self, raw_data: Dict[str, Any]) -> ProcessedData:
        """Process raw market data into features."""
        try:
            # Add to historical data
            if 'timestamp' not in raw_data:
                raw_data['timestamp'] = datetime.utcnow()
            
            self.historical_data.append(raw_data.copy())
            
            # Keep only recent data
            if len(self.historical_data) > self.lookback_periods * 2:
                self.historical_data = self.historical_data[-self.lookback_periods * 2:]
            
            # Extract basic features
            features = self._extract_basic_features(raw_data)
            
            # Add technical indicators if enough history
            if len(self.historical_data) >= self.lookback_periods:
                technical_features = self._calculate_technical_indicators()
                features.update(technical_features)
            
            # Add time-based features
            time_features = self._extract_time_features(raw_data['timestamp'])
            features.update(time_features)
            
            # Calculate data quality
            quality_score = self._assess_data_quality(raw_data, features)
            
            # Create metadata
            metadata = {
                'source': 'market_data',
                'raw_data_keys': list(raw_data.keys()),
                'feature_count': len(features),
                'historical_data_points': len(self.historical_data)
            }
            
            return ProcessedData(
                features=features,
                metadata=metadata,
                timestamp=raw_data['timestamp'],
                data_quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Error processing market data: {str(e)}")
            return ProcessedData(
                features={},
                metadata={'error': str(e)},
                timestamp=datetime.utcnow(),
                data_quality_score=0.0
            )
    
    def _extract_basic_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract basic features from raw data."""
        features = {}
        
        # Direct numeric features
        numeric_fields = [
            'market_return', 'market_volatility', 'vix_level', 'vix_change',
            'volume_ratio', 'bid_ask_spread', 'realized_volatility',
            'implied_volatility', 'correlation_level', 'sector_rotation'
        ]
        
        for field in numeric_fields:
            if field in data and isinstance(data[field], (int, float)):
                features[field] = float(data[field])
        
        # Derived features
        if 'market_return' in features and 'market_volatility' in features:
            # Risk-adjusted return
            if features['market_volatility'] > 0:
                features['risk_adjusted_return'] = features['market_return'] / features['market_volatility']
            else:
                features['risk_adjusted_return'] = 0.0
        
        if 'vix_level' in features:
            # VIX regime indicator
            features['vix_regime'] = 1.0 if features['vix_level'] > 25 else 0.0
            features['vix_normalized'] = min(1.0, features['vix_level'] / 50.0)  # Normalize to 0-1
        
        return features
    
    def _calculate_technical_indicators(self) -> Dict[str, float]:
        """Calculate technical indicators from historical data."""
        try:
            features = {}
            
            if len(self.historical_data) < 5:
                return features
            
            # Convert to DataFrame for easier calculations
            df = pd.DataFrame(self.historical_data)
            
            # Moving averages
            if 'market_return' in df.columns:
                returns = df['market_return'].fillna(0)
                features['return_ma_5'] = returns.rolling(5).mean().iloc[-1]
                features['return_ma_10'] = returns.rolling(10).mean().iloc[-1]
                
                if len(returns) >= 20:
                    features['return_ma_20'] = returns.rolling(20).mean().iloc[-1]
            
            # Volatility indicators
            if 'market_volatility' in df.columns:
                volatility = df['market_volatility'].fillna(0)
                features['volatility_ma_5'] = volatility.rolling(5).mean().iloc[-1]
                features['volatility_trend'] = volatility.diff().rolling(5).mean().iloc[-1]
            
            # VIX indicators
            if 'vix_level' in df.columns:
                vix = df['vix_level'].fillna(0)
                features['vix_ma_5'] = vix.rolling(5).mean().iloc[-1]
                features['vix_momentum'] = vix.diff().rolling(3).mean().iloc[-1]
            
            # Correlation stability
            if 'correlation_level' in df.columns:
                correlation = df['correlation_level'].fillna(0)
                features['correlation_stability'] = 1.0 - correlation.rolling(5).std().iloc[-1]
            
            return features
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return {}
    
    def _extract_time_features(self, timestamp: datetime) -> Dict[str, float]:
        """Extract time-based features."""
        features = {}
        
        # Day of week (0 = Monday, 6 = Sunday)
        features['day_of_week'] = float(timestamp.weekday())
        
        # Week of year
        features['week_of_year'] = float(timestamp.isocalendar()[1])
        
        # Month
        features['month'] = float(timestamp.month)
        
        # Quarter
        features['quarter'] = float((timestamp.month - 1) // 3 + 1)
        
        # Hour (for intraday patterns)
        features['hour'] = float(timestamp.hour)
        
        # Market session indicators (assuming ET timezone)
        market_hour = timestamp.hour
        features['pre_market'] = 1.0 if 4 <= market_hour < 9.5 else 0.0
        features['market_hours'] = 1.0 if 9.5 <= market_hour < 16 else 0.0
        features['after_hours'] = 1.0 if 16 <= market_hour < 20 else 0.0
        
        # End of month/quarter/year effects
        days_in_month = (timestamp.replace(month=timestamp.month % 12 + 1, day=1) - timedelta(days=1)).day
        features['end_of_month'] = 1.0 if timestamp.day >= days_in_month - 2 else 0.0
        
        features['end_of_quarter'] = 1.0 if timestamp.month in [3, 6, 9, 12] and features['end_of_month'] else 0.0
        
        return features
    
    def _assess_data_quality(self, raw_data: Dict[str, Any], features: Dict[str, float]) -> float:
        """Assess the quality of the processed data."""
        quality_factors = []
        
        # Completeness - how many expected fields are present
        expected_fields = ['market_return', 'market_volatility', 'vix_level']
        present_fields = sum(1 for field in expected_fields if field in raw_data)
        completeness = present_fields / len(expected_fields)
        quality_factors.append(completeness)
        
        # Validity - check for reasonable values
        validity_score = 1.0
        
        if 'market_volatility' in features:
            if features['market_volatility'] < 0 or features['market_volatility'] > 2.0:
                validity_score *= 0.5
        
        if 'vix_level' in features:
            if features['vix_level'] < 0 or features['vix_level'] > 100:
                validity_score *= 0.5
        
        quality_factors.append(validity_score)
        
        # Freshness - how recent is the data
        if 'timestamp' in raw_data:
            age_minutes = (datetime.utcnow() - raw_data['timestamp']).total_seconds() / 60
            freshness = max(0.0, 1.0 - age_minutes / 1440)  # Decay over 24 hours
            quality_factors.append(freshness)
        
        # Feature richness - how many features were extracted
        feature_richness = min(1.0, len(features) / 20.0)  # Expect ~20 features
        quality_factors.append(feature_richness)
        
        return sum(quality_factors) / len(quality_factors)


class FeatureExtractor:
    """
    Advanced feature extraction for specific ML tasks.
    
    Provides specialized feature extraction methods for different
    types of analysis and prediction tasks.
    """
    
    def __init__(self):
        """Initialize the feature extractor."""
        self.feature_history: Dict[str, List[float]] = {}
        logger.info("FeatureExtractor initialized successfully")
    
    def extract_volatility_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features specifically for volatility analysis."""
        features = {}
        
        # Current volatility metrics
        if 'realized_volatility' in data:
            features['realized_vol'] = float(data['realized_volatility'])
        
        if 'implied_volatility' in data:
            features['implied_vol'] = float(data['implied_volatility'])
        
        # VIX-based features
        if 'vix_level' in data:
            vix = float(data['vix_level'])
            features['vix_level'] = vix
            features['vix_regime_low'] = 1.0 if vix < 15 else 0.0
            features['vix_regime_medium'] = 1.0 if 15 <= vix <= 25 else 0.0
            features['vix_regime_high'] = 1.0 if vix > 25 else 0.0
        
        # Volatility term structure
        if 'vix_9d' in data and 'vix_30d' in data:
            features['vol_term_structure'] = float(data['vix_9d']) - float(data['vix_30d'])
        
        # Volatility skew
        if 'volatility_skew' in data:
            features['vol_skew'] = float(data['volatility_skew'])
        
        return features
    
    def extract_performance_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for performance prediction."""
        features = {}
        
        # Return-based features
        return_fields = ['daily_return', 'weekly_return', 'monthly_return']
        for field in return_fields:
            if field in data:
                features[field] = float(data[field])
        
        # Risk-adjusted metrics
        if 'sharpe_ratio' in data:
            features['sharpe_ratio'] = float(data['sharpe_ratio'])
        
        if 'sortino_ratio' in data:
            features['sortino_ratio'] = float(data['sortino_ratio'])
        
        # Drawdown metrics
        if 'max_drawdown' in data:
            features['max_drawdown'] = float(data['max_drawdown'])
        
        if 'current_drawdown' in data:
            features['current_drawdown'] = float(data['current_drawdown'])
        
        # Win rate and consistency
        if 'win_rate' in data:
            features['win_rate'] = float(data['win_rate'])
        
        if 'return_consistency' in data:
            features['return_consistency'] = float(data['return_consistency'])
        
        return features
    
    def extract_risk_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for risk analysis."""
        features = {}
        
        # Portfolio risk metrics
        risk_fields = [
            'portfolio_volatility', 'portfolio_beta', 'portfolio_var',
            'concentration_risk', 'liquidity_risk', 'correlation_risk'
        ]
        
        for field in risk_fields:
            if field in data:
                features[field] = float(data[field])
        
        # Greek exposures
        greek_fields = ['delta_exposure', 'gamma_exposure', 'theta_exposure', 'vega_exposure']
        for field in greek_fields:
            if field in data:
                features[field] = float(data[field])
        
        # Position sizing metrics
        if 'position_count' in data:
            features['position_count'] = float(data['position_count'])
        
        if 'capital_utilization' in data:
            features['capital_utilization'] = float(data['capital_utilization'])
        
        # Market stress indicators
        if 'market_stress_index' in data:
            features['market_stress'] = float(data['market_stress_index'])
        
        return features
    
    def extract_seasonal_features(self, timestamp: datetime) -> Dict[str, float]:
        """Extract seasonal and calendar features."""
        features = {}
        
        # Basic time features
        features['month'] = float(timestamp.month)
        features['day_of_year'] = float(timestamp.timetuple().tm_yday)
        features['week_of_year'] = float(timestamp.isocalendar()[1])
        features['day_of_week'] = float(timestamp.weekday())
        
        # Seasonal indicators
        features['is_january'] = 1.0 if timestamp.month == 1 else 0.0
        features['is_december'] = 1.0 if timestamp.month == 12 else 0.0
        features['is_q1'] = 1.0 if timestamp.month in [1, 2, 3] else 0.0
        features['is_q4'] = 1.0 if timestamp.month in [10, 11, 12] else 0.0
        
        # Holiday proximity (simplified)
        # This would be enhanced with actual holiday calendar
        features['near_holiday'] = 0.0  # Placeholder
        
        # Options expiration (third Friday of month)
        third_friday = self._get_third_friday(timestamp.year, timestamp.month)
        days_to_expiration = (third_friday - timestamp.date()).days
        features['days_to_opex'] = float(max(0, days_to_expiration))
        features['is_opex_week'] = 1.0 if abs(days_to_expiration) <= 3 else 0.0
        
        return features
    
    def _get_third_friday(self, year: int, month: int) -> datetime:
        """Get the third Friday of a given month."""
        from calendar import monthrange
        
        # Find first day of month and its weekday
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate third Friday
        # Friday is weekday 4, so we need to find the first Friday and add 14 days
        days_to_first_friday = (4 - first_weekday) % 7
        first_friday = 1 + days_to_first_friday
        third_friday = first_friday + 14
        
        # Make sure it's within the month
        days_in_month = monthrange(year, month)[1]
        if third_friday > days_in_month:
            third_friday -= 7
        
        return datetime(year, month, third_friday).date()
    
    def update_feature_history(self, feature_name: str, value: float, max_history: int = 50):
        """Update feature history for trend analysis."""
        if feature_name not in self.feature_history:
            self.feature_history[feature_name] = []
        
        self.feature_history[feature_name].append(value)
        
        # Keep only recent history
        if len(self.feature_history[feature_name]) > max_history:
            self.feature_history[feature_name] = self.feature_history[feature_name][-max_history:]
    
    def get_trend_features(self, feature_name: str) -> Dict[str, float]:
        """Get trend-based features for a given feature."""
        features = {}
        
        if feature_name not in self.feature_history or len(self.feature_history[feature_name]) < 5:
            return features
        
        values = self.feature_history[feature_name]
        
        # Trend direction
        recent_avg = np.mean(values[-5:])
        older_avg = np.mean(values[-10:-5]) if len(values) >= 10 else np.mean(values[:-5])
        
        features[f'{feature_name}_trend'] = recent_avg - older_avg
        features[f'{feature_name}_trend_strength'] = abs(recent_avg - older_avg) / (np.std(values) + 1e-8)
        
        # Momentum
        if len(values) >= 3:
            features[f'{feature_name}_momentum'] = values[-1] - values[-3]
        
        # Volatility
        features[f'{feature_name}_volatility'] = np.std(values)
        
        # Mean reversion indicator
        current_value = values[-1]
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        if std_value > 0:
            features[f'{feature_name}_zscore'] = (current_value - mean_value) / std_value
        
        return features

