"""
Time Series Analysis Utilities for WS8 ML Intelligence

Utilities for time series analysis, seasonality detection, and temporal pattern recognition.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


@dataclass
class SeasonalPattern:
    """Container for seasonal pattern information."""
    pattern_type: str  # 'daily', 'weekly', 'monthly', 'quarterly'
    strength: float  # 0-1, strength of the seasonal pattern
    phase: float  # Phase offset
    period: int  # Period length
    confidence: float  # Confidence in the pattern
    description: str


@dataclass
class TrendAnalysis:
    """Container for trend analysis results."""
    trend_direction: str  # 'up', 'down', 'sideways'
    trend_strength: float  # 0-1, strength of the trend
    trend_duration: int  # Number of periods
    slope: float  # Trend slope
    r_squared: float  # Goodness of fit
    confidence: float  # Confidence in the trend


class TimeSeriesAnalyzer:
    """
    Analyzes time series data for trends, patterns, and anomalies.
    
    Provides comprehensive time series analysis including trend detection,
    seasonality analysis, and pattern recognition.
    """
    
    def __init__(self,
                 min_periods: int = 10,
                 trend_threshold: float = 0.1):
        """Initialize the time series analyzer."""
        self.min_periods = min_periods
        self.trend_threshold = trend_threshold
        
        logger.info("TimeSeriesAnalyzer initialized successfully")
    
    def analyze_trend(self, 
                     values: List[float], 
                     timestamps: Optional[List[datetime]] = None) -> TrendAnalysis:
        """Analyze trend in time series data."""
        try:
            if len(values) < self.min_periods:
                return TrendAnalysis(
                    trend_direction='unknown',
                    trend_strength=0.0,
                    trend_duration=0,
                    slope=0.0,
                    r_squared=0.0,
                    confidence=0.0
                )
            
            # Create time index if not provided
            if timestamps is None:
                x = np.arange(len(values))
            else:
                # Convert timestamps to numeric (days since first timestamp)
                first_timestamp = timestamps[0]
                x = np.array([(ts - first_timestamp).total_seconds() / 86400 for ts in timestamps])
            
            y = np.array(values)
            
            # Remove NaN values
            mask = ~np.isnan(y)
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) < 3:
                return TrendAnalysis(
                    trend_direction='unknown',
                    trend_strength=0.0,
                    trend_duration=0,
                    slope=0.0,
                    r_squared=0.0,
                    confidence=0.0
                )
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
            r_squared = r_value ** 2
            
            # Determine trend direction
            if abs(slope) < self.trend_threshold:
                trend_direction = 'sideways'
                trend_strength = 0.0
            elif slope > 0:
                trend_direction = 'up'
                trend_strength = min(1.0, abs(slope) / np.std(y_clean))
            else:
                trend_direction = 'down'
                trend_strength = min(1.0, abs(slope) / np.std(y_clean))
            
            # Calculate confidence based on R² and p-value
            confidence = r_squared * (1 - p_value) if p_value < 1.0 else 0.0
            
            return TrendAnalysis(
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                trend_duration=len(x_clean),
                slope=slope,
                r_squared=r_squared,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {str(e)}")
            return TrendAnalysis(
                trend_direction='error',
                trend_strength=0.0,
                trend_duration=0,
                slope=0.0,
                r_squared=0.0,
                confidence=0.0
            )
    
    def detect_change_points(self, 
                           values: List[float], 
                           min_segment_length: int = 5) -> List[int]:
        """Detect change points in time series data."""
        try:
            if len(values) < min_segment_length * 2:
                return []
            
            values_array = np.array(values)
            change_points = []
            
            # Simple change point detection using variance
            window_size = max(5, len(values) // 10)
            
            for i in range(window_size, len(values) - window_size):
                # Calculate variance before and after potential change point
                before = values_array[max(0, i - window_size):i]
                after = values_array[i:min(len(values), i + window_size)]
                
                if len(before) > 2 and len(after) > 2:
                    var_before = np.var(before)
                    var_after = np.var(after)
                    mean_before = np.mean(before)
                    mean_after = np.mean(after)
                    
                    # Check for significant change in mean or variance
                    mean_change = abs(mean_after - mean_before) / (np.std(values_array) + 1e-8)
                    var_ratio = max(var_after, var_before) / (min(var_after, var_before) + 1e-8)
                    
                    if mean_change > 1.5 or var_ratio > 2.0:
                        change_points.append(i)
            
            # Remove nearby change points
            if change_points:
                filtered_points = [change_points[0]]
                for point in change_points[1:]:
                    if point - filtered_points[-1] >= min_segment_length:
                        filtered_points.append(point)
                change_points = filtered_points
            
            return change_points
            
        except Exception as e:
            logger.error(f"Error detecting change points: {str(e)}")
            return []
    
    def calculate_volatility_regime(self, 
                                  values: List[float], 
                                  window_size: int = 20) -> List[str]:
        """Calculate volatility regime for each point in the series."""
        try:
            if len(values) < window_size:
                return ['unknown'] * len(values)
            
            values_array = np.array(values)
            regimes = []
            
            # Calculate rolling volatility
            rolling_vol = []
            for i in range(len(values)):
                start_idx = max(0, i - window_size + 1)
                end_idx = i + 1
                window_data = values_array[start_idx:end_idx]
                
                if len(window_data) > 1:
                    vol = np.std(window_data)
                    rolling_vol.append(vol)
                else:
                    rolling_vol.append(0.0)
            
            # Determine regime thresholds
            vol_array = np.array(rolling_vol)
            vol_25 = np.percentile(vol_array, 25)
            vol_75 = np.percentile(vol_array, 75)
            
            # Classify regimes
            for vol in rolling_vol:
                if vol <= vol_25:
                    regimes.append('low_vol')
                elif vol >= vol_75:
                    regimes.append('high_vol')
                else:
                    regimes.append('medium_vol')
            
            return regimes
            
        except Exception as e:
            logger.error(f"Error calculating volatility regime: {str(e)}")
            return ['error'] * len(values)
    
    def calculate_momentum_indicators(self, 
                                    values: List[float], 
                                    periods: List[int] = None) -> Dict[str, List[float]]:
        """Calculate momentum indicators for the time series."""
        try:
            if periods is None:
                periods = [5, 10, 20]
            
            values_array = np.array(values)
            indicators = {}
            
            # Rate of change for different periods
            for period in periods:
                roc = []
                for i in range(len(values)):
                    if i >= period:
                        current = values_array[i]
                        past = values_array[i - period]
                        if past != 0:
                            change = (current - past) / abs(past)
                        else:
                            change = 0.0
                        roc.append(change)
                    else:
                        roc.append(0.0)
                
                indicators[f'roc_{period}'] = roc
            
            # Moving average convergence divergence (simplified)
            if len(values) >= 26:
                ema_12 = self._calculate_ema(values, 12)
                ema_26 = self._calculate_ema(values, 26)
                macd = [e12 - e26 for e12, e26 in zip(ema_12, ema_26)]
                indicators['macd'] = macd
            
            # Relative Strength Index (simplified)
            if len(values) >= 14:
                rsi = self._calculate_rsi(values, 14)
                indicators['rsi'] = rsi
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {str(e)}")
            return {}
    
    def _calculate_ema(self, values: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        alpha = 2.0 / (period + 1)
        ema = [values[0]]  # Start with first value
        
        for i in range(1, len(values)):
            ema_value = alpha * values[i] + (1 - alpha) * ema[-1]
            ema.append(ema_value)
        
        return ema
    
    def _calculate_rsi(self, values: List[float], period: int) -> List[float]:
        """Calculate Relative Strength Index."""
        if len(values) < period + 1:
            return [50.0] * len(values)  # Neutral RSI
        
        # Calculate price changes
        changes = [values[i] - values[i-1] for i in range(1, len(values))]
        
        rsi = [50.0]  # Start with neutral
        
        # Calculate initial average gain and loss
        gains = [max(0, change) for change in changes[:period]]
        losses = [max(0, -change) for change in changes[:period]]
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        # Calculate RSI for remaining periods
        for i in range(period, len(changes)):
            gain = max(0, changes[i])
            loss = max(0, -changes[i])
            
            # Update averages
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            # Calculate RSI
            if avg_loss == 0:
                rsi_value = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100.0 - (100.0 / (1 + rs))
            
            rsi.append(rsi_value)
        
        return rsi


class SeasonalityDetector:
    """
    Detects seasonal patterns in time series data.
    
    Identifies daily, weekly, monthly, and quarterly patterns
    and quantifies their strength and significance.
    """
    
    def __init__(self,
                 min_cycles: int = 2,
                 significance_threshold: float = 0.05):
        """Initialize the seasonality detector."""
        self.min_cycles = min_cycles
        self.significance_threshold = significance_threshold
        
        logger.info("SeasonalityDetector initialized successfully")
    
    def detect_weekly_seasonality(self, 
                                 values: List[float], 
                                 timestamps: List[datetime]) -> Optional[SeasonalPattern]:
        """Detect weekly seasonal patterns."""
        try:
            if len(values) < 14:  # Need at least 2 weeks
                return None
            
            # Group by day of week
            df = pd.DataFrame({
                'value': values,
                'timestamp': timestamps,
                'day_of_week': [ts.weekday() for ts in timestamps]
            })
            
            # Calculate average for each day of week
            daily_means = df.groupby('day_of_week')['value'].mean()
            daily_stds = df.groupby('day_of_week')['value'].std()
            
            # Test for significant differences between days
            day_groups = [df[df['day_of_week'] == day]['value'].values for day in range(7)]
            day_groups = [group for group in day_groups if len(group) > 0]
            
            if len(day_groups) < 2:
                return None
            
            # ANOVA test
            try:
                f_stat, p_value = stats.f_oneway(*day_groups)
                
                if p_value > self.significance_threshold:
                    return None
                
                # Calculate pattern strength
                overall_mean = np.mean(values)
                pattern_variance = np.var(daily_means.values)
                total_variance = np.var(values)
                
                strength = min(1.0, pattern_variance / (total_variance + 1e-8))
                confidence = 1 - p_value
                
                # Find peak day
                peak_day = daily_means.idxmax()
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                description = f"Weekly pattern with peak on {day_names[peak_day]}"
                
                return SeasonalPattern(
                    pattern_type='weekly',
                    strength=strength,
                    phase=float(peak_day),
                    period=7,
                    confidence=confidence,
                    description=description
                )
                
            except Exception:
                return None
            
        except Exception as e:
            logger.error(f"Error detecting weekly seasonality: {str(e)}")
            return None
    
    def detect_monthly_seasonality(self, 
                                  values: List[float], 
                                  timestamps: List[datetime]) -> Optional[SeasonalPattern]:
        """Detect monthly seasonal patterns."""
        try:
            if len(timestamps) < 60:  # Need at least 2 months of data
                return None
            
            # Group by month
            df = pd.DataFrame({
                'value': values,
                'timestamp': timestamps,
                'month': [ts.month for ts in timestamps]
            })
            
            # Calculate average for each month
            monthly_means = df.groupby('month')['value'].mean()
            
            # Need data for multiple months
            if len(monthly_means) < 3:
                return None
            
            # Test for seasonal pattern using autocorrelation
            # Create monthly time series
            monthly_data = []
            for month in range(1, 13):
                month_values = df[df['month'] == month]['value'].values
                if len(month_values) > 0:
                    monthly_data.append(np.mean(month_values))
                else:
                    monthly_data.append(np.nan)
            
            # Remove NaN values
            valid_months = [i for i, val in enumerate(monthly_data) if not np.isnan(val)]
            if len(valid_months) < 3:
                return None
            
            valid_values = [monthly_data[i] for i in valid_months]
            
            # Calculate pattern strength
            pattern_variance = np.var(valid_values)
            total_variance = np.var(values)
            
            strength = min(1.0, pattern_variance / (total_variance + 1e-8))
            
            # Find peak month
            peak_month_idx = np.argmax(valid_values)
            peak_month = valid_months[peak_month_idx] + 1
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            description = f"Monthly pattern with peak in {month_names[peak_month-1]}"
            
            # Simple confidence based on pattern strength
            confidence = min(1.0, strength * 2)
            
            return SeasonalPattern(
                pattern_type='monthly',
                strength=strength,
                phase=float(peak_month),
                period=12,
                confidence=confidence,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error detecting monthly seasonality: {str(e)}")
            return None
    
    def detect_intraday_seasonality(self, 
                                   values: List[float], 
                                   timestamps: List[datetime]) -> Optional[SeasonalPattern]:
        """Detect intraday seasonal patterns."""
        try:
            if len(values) < 24:  # Need at least 24 hours of data
                return None
            
            # Group by hour
            df = pd.DataFrame({
                'value': values,
                'timestamp': timestamps,
                'hour': [ts.hour for ts in timestamps]
            })
            
            # Calculate average for each hour
            hourly_means = df.groupby('hour')['value'].mean()
            
            # Need data for multiple hours
            if len(hourly_means) < 6:
                return None
            
            # Test for significant differences between hours
            hour_groups = [df[df['hour'] == hour]['value'].values for hour in range(24)]
            hour_groups = [group for group in hour_groups if len(group) > 0]
            
            if len(hour_groups) < 3:
                return None
            
            # Calculate pattern strength
            pattern_variance = np.var(hourly_means.values)
            total_variance = np.var(values)
            
            strength = min(1.0, pattern_variance / (total_variance + 1e-8))
            
            # Find peak hour
            peak_hour = hourly_means.idxmax()
            
            # Determine market session
            if 9 <= peak_hour <= 16:
                session = "market hours"
            elif 4 <= peak_hour <= 9:
                session = "pre-market"
            else:
                session = "after hours"
            
            description = f"Intraday pattern with peak at {peak_hour:02d}:00 ({session})"
            
            # Simple confidence based on pattern strength and data coverage
            confidence = min(1.0, strength * len(hour_groups) / 24)
            
            return SeasonalPattern(
                pattern_type='intraday',
                strength=strength,
                phase=float(peak_hour),
                period=24,
                confidence=confidence,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error detecting intraday seasonality: {str(e)}")
            return None
    
    def detect_all_seasonality(self, 
                              values: List[float], 
                              timestamps: List[datetime]) -> List[SeasonalPattern]:
        """Detect all types of seasonal patterns."""
        patterns = []
        
        # Detect different seasonal patterns
        weekly = self.detect_weekly_seasonality(values, timestamps)
        if weekly and weekly.confidence > 0.3:
            patterns.append(weekly)
        
        monthly = self.detect_monthly_seasonality(values, timestamps)
        if monthly and monthly.confidence > 0.3:
            patterns.append(monthly)
        
        intraday = self.detect_intraday_seasonality(values, timestamps)
        if intraday and intraday.confidence > 0.3:
            patterns.append(intraday)
        
        # Sort by strength
        patterns.sort(key=lambda p: p.strength, reverse=True)
        
        return patterns
    
    def get_seasonal_adjustment(self, 
                              values: List[float], 
                              timestamps: List[datetime],
                              pattern: SeasonalPattern) -> List[float]:
        """Apply seasonal adjustment to remove seasonal pattern."""
        try:
            if pattern.pattern_type == 'weekly':
                # Group by day of week and calculate adjustment factors
                df = pd.DataFrame({
                    'value': values,
                    'day_of_week': [ts.weekday() for ts in timestamps]
                })
                
                daily_means = df.groupby('day_of_week')['value'].mean()
                overall_mean = np.mean(values)
                
                # Calculate adjustment factors
                adjustments = {}
                for day in range(7):
                    if day in daily_means.index:
                        adjustments[day] = daily_means[day] - overall_mean
                    else:
                        adjustments[day] = 0.0
                
                # Apply adjustments
                adjusted_values = []
                for i, ts in enumerate(timestamps):
                    day = ts.weekday()
                    adjusted_values.append(values[i] - adjustments[day])
                
                return adjusted_values
            
            elif pattern.pattern_type == 'monthly':
                # Similar logic for monthly adjustment
                df = pd.DataFrame({
                    'value': values,
                    'month': [ts.month for ts in timestamps]
                })
                
                monthly_means = df.groupby('month')['value'].mean()
                overall_mean = np.mean(values)
                
                adjustments = {}
                for month in range(1, 13):
                    if month in monthly_means.index:
                        adjustments[month] = monthly_means[month] - overall_mean
                    else:
                        adjustments[month] = 0.0
                
                adjusted_values = []
                for i, ts in enumerate(timestamps):
                    month = ts.month
                    adjusted_values.append(values[i] - adjustments[month])
                
                return adjusted_values
            
            else:
                # For other patterns, return original values
                return values.copy()
            
        except Exception as e:
            logger.error(f"Error applying seasonal adjustment: {str(e)}")
            return values.copy()

