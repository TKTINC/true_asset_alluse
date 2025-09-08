"""
Pattern Recognition Engine - ML Intelligence System

This module implements pattern recognition for market patterns, system behavior
patterns, and performance patterns to provide insights and improve understanding.

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
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import scipy.signal as signal
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

from src.ws1_rules_engine.constitution.week_classification import WeekType, WeekPerformance
from src.ws1_rules_engine.audit import AuditTrailManager

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be recognized."""
    MARKET_REGIME = "market_regime"
    VOLATILITY_PATTERN = "volatility_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    RISK_PATTERN = "risk_pattern"
    WEEK_TYPE_PATTERN = "week_type_pattern"
    PROTOCOL_PATTERN = "protocol_pattern"
    SEASONAL_PATTERN = "seasonal_pattern"
    CORRELATION_PATTERN = "correlation_pattern"


@dataclass
class Pattern:
    """A recognized pattern."""
    pattern_type: PatternType
    pattern_id: str
    name: str
    description: str
    confidence: float
    characteristics: Dict[str, Any]
    historical_occurrences: int
    success_rate: float
    average_duration: timedelta
    created_at: datetime


@dataclass
class PatternMatch:
    """A match of current data to a known pattern."""
    pattern: Pattern
    match_confidence: float
    match_strength: float
    current_data: Dict[str, Any]
    expected_outcomes: Dict[str, float]
    recommendations: List[str]
    matched_at: datetime


class PatternRecognitionEngine:
    """
    Pattern recognition system that identifies recurring patterns in market data,
    system behavior, and performance metrics.
    
    ADVISORY ONLY: Provides pattern insights and recommendations but does not make
    any wealth management decisions. All decisions remain rules-based.
    """
    
    def __init__(self,
                 audit_manager: AuditTrailManager,
                 min_pattern_occurrences: int = 5,
                 pattern_confidence_threshold: float = 0.7):
        """Initialize the pattern recognition engine."""
        self.audit_manager = audit_manager
        self.min_pattern_occurrences = min_pattern_occurrences
        self.pattern_confidence_threshold = pattern_confidence_threshold
        
        # Pattern storage
        self.recognized_patterns: Dict[PatternType, List[Pattern]] = {}
        self.pattern_matches: List[PatternMatch] = []
        
        # Historical data for pattern recognition
        self.historical_data: List[Dict[str, Any]] = []
        
        # Pattern recognition models
        self.clustering_models: Dict[PatternType, Any] = {}
        self.scalers: Dict[PatternType, StandardScaler] = {}
        
        # Initialize pattern storage
        for pattern_type in PatternType:
            self.recognized_patterns[pattern_type] = []
        
        logger.info("PatternRecognitionEngine initialized successfully")
    
    async def add_historical_data(self, data: Dict[str, Any]):
        """Add historical data for pattern recognition."""
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow()
            
            self.historical_data.append(data)
            
            # Trigger pattern recognition if we have enough data
            if len(self.historical_data) % 50 == 0:  # Every 50 data points
                await self._recognize_patterns()
            
            # Log the data addition
            await self.audit_manager.log_event(
                event_type="PATTERN_HISTORICAL_DATA_ADDED",
                details={
                    'timestamp': data['timestamp'].isoformat(),
                    'data_keys': list(data.keys())
                },
                metadata={'historical_data_count': len(self.historical_data)}
            )
            
        except Exception as e:
            logger.error(f"Error adding historical data: {str(e)}")
    
    async def _recognize_patterns(self):
        """Recognize patterns in historical data."""
        try:
            for pattern_type in PatternType:
                await self._recognize_pattern_type(pattern_type)
            
            logger.info("Pattern recognition completed successfully")
            
        except Exception as e:
            logger.error(f"Error in pattern recognition: {str(e)}")
    
    async def _recognize_pattern_type(self, pattern_type: PatternType):
        """Recognize patterns for a specific pattern type."""
        try:
            if len(self.historical_data) < self.min_pattern_occurrences * 2:
                return
            
            # Prepare data for this pattern type
            pattern_data = self._prepare_pattern_data(pattern_type)
            
            if len(pattern_data) == 0:
                return
            
            # Apply clustering to identify patterns
            patterns = await self._cluster_patterns(pattern_type, pattern_data)
            
            # Validate and store patterns
            for pattern in patterns:
                if pattern.confidence >= self.pattern_confidence_threshold:
                    # Check if pattern already exists
                    existing_pattern = self._find_similar_pattern(pattern)
                    
                    if existing_pattern:
                        # Update existing pattern
                        await self._update_pattern(existing_pattern, pattern)
                    else:
                        # Add new pattern
                        self.recognized_patterns[pattern_type].append(pattern)
                        
                        await self.audit_manager.log_event(
                            event_type="PATTERN_RECOGNIZED",
                            details={
                                'pattern_type': pattern_type.value,
                                'pattern_id': pattern.pattern_id,
                                'confidence': pattern.confidence,
                                'occurrences': pattern.historical_occurrences
                            }
                        )
            
        except Exception as e:
            logger.error(f"Error recognizing patterns for {pattern_type.value}: {str(e)}")
    
    def _prepare_pattern_data(self, pattern_type: PatternType) -> List[Dict[str, Any]]:
        """Prepare data for pattern recognition based on pattern type."""
        try:
            pattern_data = []
            
            for data_point in self.historical_data:
                if pattern_type == PatternType.MARKET_REGIME:
                    pattern_data.append({
                        'market_return': data_point.get('market_return', 0.0),
                        'market_volatility': data_point.get('market_volatility', 0.0),
                        'vix_level': data_point.get('vix_level', 0.0),
                        'correlation_level': data_point.get('correlation_level', 0.0),
                        'timestamp': data_point['timestamp']
                    })
                
                elif pattern_type == PatternType.VOLATILITY_PATTERN:
                    pattern_data.append({
                        'realized_volatility': data_point.get('realized_volatility', 0.0),
                        'implied_volatility': data_point.get('implied_volatility', 0.0),
                        'volatility_skew': data_point.get('volatility_skew', 0.0),
                        'vix_change': data_point.get('vix_change', 0.0),
                        'timestamp': data_point['timestamp']
                    })
                
                elif pattern_type == PatternType.PERFORMANCE_PATTERN:
                    pattern_data.append({
                        'weekly_return': data_point.get('weekly_return', 0.0),
                        'sharpe_ratio': data_point.get('sharpe_ratio', 0.0),
                        'max_drawdown': data_point.get('max_drawdown', 0.0),
                        'win_rate': data_point.get('win_rate', 0.0),
                        'timestamp': data_point['timestamp']
                    })
                
                elif pattern_type == PatternType.WEEK_TYPE_PATTERN:
                    if 'week_type' in data_point:
                        pattern_data.append({
                            'week_type': self._encode_week_type(data_point['week_type']),
                            'week_performance': self._encode_week_performance(data_point.get('week_performance')),
                            'market_volatility': data_point.get('market_volatility', 0.0),
                            'earnings_density': data_point.get('earnings_density', 0.0),
                            'timestamp': data_point['timestamp']
                        })
                
                elif pattern_type == PatternType.SEASONAL_PATTERN:
                    timestamp = data_point['timestamp']
                    pattern_data.append({
                        'month': timestamp.month,
                        'quarter': (timestamp.month - 1) // 3 + 1,
                        'day_of_week': timestamp.weekday(),
                        'week_of_year': timestamp.isocalendar()[1],
                        'performance': data_point.get('weekly_return', 0.0),
                        'timestamp': timestamp
                    })
            
            return pattern_data
            
        except Exception as e:
            logger.error(f"Error preparing pattern data for {pattern_type.value}: {str(e)}")
            return []
    
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
    
    def _encode_week_performance(self, week_performance) -> int:
        """Encode week performance as integer."""
        if isinstance(week_performance, WeekPerformance):
            encoding = {
                WeekPerformance.POOR: 0,
                WeekPerformance.BELOW_AVERAGE: 1,
                WeekPerformance.AVERAGE: 2,
                WeekPerformance.ABOVE_AVERAGE: 3,
                WeekPerformance.EXCELLENT: 4
            }
            return encoding.get(week_performance, 2)
        return 2
    
    async def _cluster_patterns(self, pattern_type: PatternType, pattern_data: List[Dict[str, Any]]) -> List[Pattern]:
        """Use clustering to identify patterns."""
        try:
            if len(pattern_data) < self.min_pattern_occurrences:
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame(pattern_data)
            
            # Remove timestamp for clustering
            feature_columns = [col for col in df.columns if col != 'timestamp']
            X = df[feature_columns].fillna(0).values
            
            if X.shape[1] == 0:
                return []
            
            # Scale the data
            if pattern_type not in self.scalers:
                self.scalers[pattern_type] = StandardScaler()
            
            X_scaled = self.scalers[pattern_type].fit_transform(X)
            
            # Determine optimal number of clusters
            max_clusters = min(10, len(pattern_data) // self.min_pattern_occurrences)
            if max_clusters < 2:
                return []
            
            best_score = -1
            best_n_clusters = 2
            
            for n_clusters in range(2, max_clusters + 1):
                try:
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    cluster_labels = kmeans.fit_predict(X_scaled)
                    
                    if len(set(cluster_labels)) > 1:  # Need at least 2 clusters
                        score = silhouette_score(X_scaled, cluster_labels)
                        if score > best_score:
                            best_score = score
                            best_n_clusters = n_clusters
                except:
                    continue
            
            # Apply best clustering
            kmeans = KMeans(n_clusters=best_n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Store the model
            self.clustering_models[pattern_type] = kmeans
            
            # Create patterns from clusters
            patterns = []
            for cluster_id in range(best_n_clusters):
                cluster_mask = cluster_labels == cluster_id
                cluster_data = df[cluster_mask]
                
                if len(cluster_data) >= self.min_pattern_occurrences:
                    pattern = await self._create_pattern_from_cluster(
                        pattern_type, cluster_id, cluster_data, feature_columns
                    )
                    if pattern:
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error clustering patterns for {pattern_type.value}: {str(e)}")
            return []
    
    async def _create_pattern_from_cluster(self,
                                         pattern_type: PatternType,
                                         cluster_id: int,
                                         cluster_data: pd.DataFrame,
                                         feature_columns: List[str]) -> Optional[Pattern]:
        """Create a pattern from cluster data."""
        try:
            # Calculate pattern characteristics
            characteristics = {}
            for col in feature_columns:
                characteristics[f"{col}_mean"] = float(cluster_data[col].mean())
                characteristics[f"{col}_std"] = float(cluster_data[col].std())
                characteristics[f"{col}_min"] = float(cluster_data[col].min())
                characteristics[f"{col}_max"] = float(cluster_data[col].max())
            
            # Calculate pattern metrics
            occurrences = len(cluster_data)
            
            # Calculate success rate (if performance data available)
            success_rate = 0.5  # Default
            if 'weekly_return' in cluster_data.columns:
                positive_returns = (cluster_data['weekly_return'] > 0).sum()
                success_rate = positive_returns / len(cluster_data)
            elif 'performance' in cluster_data.columns:
                positive_performance = (cluster_data['performance'] > 0).sum()
                success_rate = positive_performance / len(cluster_data)
            
            # Calculate average duration (simplified)
            if len(cluster_data) > 1:
                timestamps = sorted(cluster_data['timestamp'].tolist())
                durations = []
                for i in range(1, len(timestamps)):
                    duration = timestamps[i] - timestamps[i-1]
                    durations.append(duration)
                
                if durations:
                    average_duration = sum(durations, timedelta()) / len(durations)
                else:
                    average_duration = timedelta(days=7)  # Default to 1 week
            else:
                average_duration = timedelta(days=7)
            
            # Calculate confidence based on cluster quality
            confidence = min(0.95, max(0.5, best_score if 'best_score' in locals() else 0.7))
            
            # Generate pattern description
            description = self._generate_pattern_description(pattern_type, characteristics)
            
            pattern = Pattern(
                pattern_type=pattern_type,
                pattern_id=f"{pattern_type.value}_{cluster_id}_{int(datetime.utcnow().timestamp())}",
                name=f"{pattern_type.value.replace('_', ' ').title()} Pattern {cluster_id}",
                description=description,
                confidence=confidence,
                characteristics=characteristics,
                historical_occurrences=occurrences,
                success_rate=success_rate,
                average_duration=average_duration,
                created_at=datetime.utcnow()
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error creating pattern from cluster: {str(e)}")
            return None
    
    def _generate_pattern_description(self, pattern_type: PatternType, characteristics: Dict[str, Any]) -> str:
        """Generate a human-readable description of the pattern."""
        try:
            if pattern_type == PatternType.MARKET_REGIME:
                volatility = characteristics.get('market_volatility_mean', 0.0)
                returns = characteristics.get('market_return_mean', 0.0)
                
                if volatility > 0.25:
                    regime = "High Volatility"
                elif abs(returns) > 0.02:
                    regime = "Trending" if returns > 0 else "Declining"
                else:
                    regime = "Low Volatility"
                
                return f"{regime} market regime with average volatility of {volatility:.1%} and returns of {returns:.1%}"
            
            elif pattern_type == PatternType.PERFORMANCE_PATTERN:
                returns = characteristics.get('weekly_return_mean', 0.0)
                sharpe = characteristics.get('sharpe_ratio_mean', 0.0)
                
                performance_level = "Strong" if returns > 0.01 else "Weak" if returns < -0.01 else "Moderate"
                
                return f"{performance_level} performance pattern with average weekly return of {returns:.1%} and Sharpe ratio of {sharpe:.2f}"
            
            elif pattern_type == PatternType.SEASONAL_PATTERN:
                month = characteristics.get('month_mean', 6)
                performance = characteristics.get('performance_mean', 0.0)
                
                season = "Strong" if performance > 0.005 else "Weak" if performance < -0.005 else "Neutral"
                
                return f"{season} seasonal pattern around month {int(month)} with average performance of {performance:.1%}"
            
            else:
                return f"Pattern in {pattern_type.value.replace('_', ' ')} with {len(characteristics)} characteristics"
                
        except Exception as e:
            logger.error(f"Error generating pattern description: {str(e)}")
            return f"Pattern in {pattern_type.value.replace('_', ' ')}"
    
    def _find_similar_pattern(self, new_pattern: Pattern) -> Optional[Pattern]:
        """Find if a similar pattern already exists."""
        try:
            existing_patterns = self.recognized_patterns[new_pattern.pattern_type]
            
            for existing_pattern in existing_patterns:
                # Calculate similarity based on characteristics
                similarity = self._calculate_pattern_similarity(new_pattern, existing_pattern)
                
                if similarity > 0.8:  # 80% similarity threshold
                    return existing_pattern
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding similar pattern: {str(e)}")
            return None
    
    def _calculate_pattern_similarity(self, pattern1: Pattern, pattern2: Pattern) -> float:
        """Calculate similarity between two patterns."""
        try:
            if pattern1.pattern_type != pattern2.pattern_type:
                return 0.0
            
            # Compare characteristics
            common_keys = set(pattern1.characteristics.keys()) & set(pattern2.characteristics.keys())
            
            if not common_keys:
                return 0.0
            
            similarities = []
            for key in common_keys:
                if key.endswith('_mean'):
                    val1 = pattern1.characteristics[key]
                    val2 = pattern2.characteristics[key]
                    
                    # Normalize similarity (closer to 1 means more similar)
                    if val1 == 0 and val2 == 0:
                        similarities.append(1.0)
                    elif val1 == 0 or val2 == 0:
                        similarities.append(0.0)
                    else:
                        similarity = 1.0 - abs(val1 - val2) / max(abs(val1), abs(val2))
                        similarities.append(max(0.0, similarity))
            
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating pattern similarity: {str(e)}")
            return 0.0
    
    async def _update_pattern(self, existing_pattern: Pattern, new_pattern: Pattern):
        """Update an existing pattern with new information."""
        try:
            # Update occurrences
            total_occurrences = existing_pattern.historical_occurrences + new_pattern.historical_occurrences
            
            # Weighted average of characteristics
            weight_existing = existing_pattern.historical_occurrences / total_occurrences
            weight_new = new_pattern.historical_occurrences / total_occurrences
            
            updated_characteristics = {}
            for key in existing_pattern.characteristics:
                if key in new_pattern.characteristics:
                    updated_characteristics[key] = (
                        existing_pattern.characteristics[key] * weight_existing +
                        new_pattern.characteristics[key] * weight_new
                    )
                else:
                    updated_characteristics[key] = existing_pattern.characteristics[key]
            
            # Update pattern
            existing_pattern.characteristics = updated_characteristics
            existing_pattern.historical_occurrences = total_occurrences
            existing_pattern.success_rate = (
                existing_pattern.success_rate * weight_existing +
                new_pattern.success_rate * weight_new
            )
            existing_pattern.confidence = min(0.95, existing_pattern.confidence + 0.05)  # Increase confidence slightly
            
            await self.audit_manager.log_event(
                event_type="PATTERN_UPDATED",
                details={
                    'pattern_id': existing_pattern.pattern_id,
                    'new_occurrences': total_occurrences,
                    'updated_confidence': existing_pattern.confidence
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating pattern: {str(e)}")
    
    async def match_current_data(self, current_data: Dict[str, Any]) -> List[PatternMatch]:
        """Match current data against recognized patterns."""
        try:
            matches = []
            
            for pattern_type, patterns in self.recognized_patterns.items():
                for pattern in patterns:
                    match = await self._match_pattern(pattern, current_data)
                    if match and match.match_confidence > 0.6:  # 60% confidence threshold
                        matches.append(match)
            
            # Sort by match confidence
            matches.sort(key=lambda x: x.match_confidence, reverse=True)
            
            # Store matches
            self.pattern_matches.extend(matches)
            
            # Keep only recent matches
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            self.pattern_matches = [
                match for match in self.pattern_matches
                if match.matched_at >= cutoff_time
            ]
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching current data: {str(e)}")
            return []
    
    async def _match_pattern(self, pattern: Pattern, current_data: Dict[str, Any]) -> Optional[PatternMatch]:
        """Match current data against a specific pattern."""
        try:
            # Prepare current data for matching
            pattern_data = self._prepare_current_data_for_pattern(pattern.pattern_type, current_data)
            
            if not pattern_data:
                return None
            
            # Calculate match confidence
            match_confidence = self._calculate_match_confidence(pattern, pattern_data)
            
            if match_confidence < 0.5:  # Minimum threshold
                return None
            
            # Calculate match strength
            match_strength = self._calculate_match_strength(pattern, pattern_data)
            
            # Generate expected outcomes
            expected_outcomes = self._generate_expected_outcomes(pattern, current_data)
            
            # Generate recommendations
            recommendations = self._generate_pattern_recommendations(pattern, match_confidence)
            
            match = PatternMatch(
                pattern=pattern,
                match_confidence=match_confidence,
                match_strength=match_strength,
                current_data=pattern_data,
                expected_outcomes=expected_outcomes,
                recommendations=recommendations,
                matched_at=datetime.utcnow()
            )
            
            return match
            
        except Exception as e:
            logger.error(f"Error matching pattern: {str(e)}")
            return None
    
    def _prepare_current_data_for_pattern(self, pattern_type: PatternType, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare current data for pattern matching."""
        try:
            if pattern_type == PatternType.MARKET_REGIME:
                return {
                    'market_return': current_data.get('market_return', 0.0),
                    'market_volatility': current_data.get('market_volatility', 0.0),
                    'vix_level': current_data.get('vix_level', 0.0),
                    'correlation_level': current_data.get('correlation_level', 0.0)
                }
            
            elif pattern_type == PatternType.PERFORMANCE_PATTERN:
                return {
                    'weekly_return': current_data.get('weekly_return', 0.0),
                    'sharpe_ratio': current_data.get('sharpe_ratio', 0.0),
                    'max_drawdown': current_data.get('max_drawdown', 0.0),
                    'win_rate': current_data.get('win_rate', 0.0)
                }
            
            elif pattern_type == PatternType.SEASONAL_PATTERN:
                timestamp = current_data.get('timestamp', datetime.utcnow())
                return {
                    'month': timestamp.month,
                    'quarter': (timestamp.month - 1) // 3 + 1,
                    'day_of_week': timestamp.weekday(),
                    'week_of_year': timestamp.isocalendar()[1]
                }
            
            else:
                # Generic approach
                return {k: v for k, v in current_data.items() if isinstance(v, (int, float))}
                
        except Exception as e:
            logger.error(f"Error preparing current data for pattern: {str(e)}")
            return {}
    
    def _calculate_match_confidence(self, pattern: Pattern, current_data: Dict[str, Any]) -> float:
        """Calculate how well current data matches a pattern."""
        try:
            confidences = []
            
            for key, value in current_data.items():
                mean_key = f"{key}_mean"
                std_key = f"{key}_std"
                
                if mean_key in pattern.characteristics and std_key in pattern.characteristics:
                    mean = pattern.characteristics[mean_key]
                    std = pattern.characteristics[std_key]
                    
                    if std > 0:
                        # Calculate z-score and convert to confidence
                        z_score = abs(value - mean) / std
                        confidence = max(0.0, 1.0 - z_score / 3.0)  # Within 3 std devs
                        confidences.append(confidence)
            
            if not confidences:
                return 0.0
            
            # Weight by pattern's own confidence
            match_confidence = sum(confidences) / len(confidences)
            weighted_confidence = match_confidence * pattern.confidence
            
            return min(1.0, weighted_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating match confidence: {str(e)}")
            return 0.0
    
    def _calculate_match_strength(self, pattern: Pattern, current_data: Dict[str, Any]) -> float:
        """Calculate the strength of the pattern match."""
        try:
            # Strength is based on how many characteristics match well
            strong_matches = 0
            total_characteristics = 0
            
            for key, value in current_data.items():
                mean_key = f"{key}_mean"
                std_key = f"{key}_std"
                
                if mean_key in pattern.characteristics and std_key in pattern.characteristics:
                    mean = pattern.characteristics[mean_key]
                    std = pattern.characteristics[std_key]
                    
                    total_characteristics += 1
                    
                    if std > 0:
                        z_score = abs(value - mean) / std
                        if z_score <= 1.0:  # Within 1 standard deviation
                            strong_matches += 1
            
            if total_characteristics == 0:
                return 0.0
            
            return strong_matches / total_characteristics
            
        except Exception as e:
            logger.error(f"Error calculating match strength: {str(e)}")
            return 0.0
    
    def _generate_expected_outcomes(self, pattern: Pattern, current_data: Dict[str, Any]) -> Dict[str, float]:
        """Generate expected outcomes based on pattern match."""
        try:
            outcomes = {}
            
            # Base outcomes on pattern's historical success rate
            outcomes['success_probability'] = pattern.success_rate
            
            if pattern.pattern_type == PatternType.PERFORMANCE_PATTERN:
                expected_return = pattern.characteristics.get('weekly_return_mean', 0.0)
                outcomes['expected_weekly_return'] = expected_return
                outcomes['expected_volatility'] = pattern.characteristics.get('weekly_return_std', 0.0)
            
            elif pattern.pattern_type == PatternType.MARKET_REGIME:
                outcomes['expected_market_return'] = pattern.characteristics.get('market_return_mean', 0.0)
                outcomes['expected_volatility'] = pattern.characteristics.get('market_volatility_mean', 0.0)
            
            # Add duration expectation
            outcomes['expected_duration_days'] = pattern.average_duration.days
            
            return outcomes
            
        except Exception as e:
            logger.error(f"Error generating expected outcomes: {str(e)}")
            return {}
    
    def _generate_pattern_recommendations(self, pattern: Pattern, match_confidence: float) -> List[str]:
        """Generate recommendations based on pattern match."""
        try:
            recommendations = []
            
            # Base recommendations
            if match_confidence > 0.8:
                recommendations.append(f"High confidence match to {pattern.name}")
                recommendations.append("Consider adjusting monitoring frequency")
            elif match_confidence > 0.6:
                recommendations.append(f"Moderate confidence match to {pattern.name}")
                recommendations.append("Monitor pattern development closely")
            
            # Pattern-specific recommendations
            if pattern.pattern_type == PatternType.MARKET_REGIME:
                if pattern.characteristics.get('market_volatility_mean', 0.0) > 0.25:
                    recommendations.append("High volatility regime detected - consider risk management measures")
                else:
                    recommendations.append("Low volatility regime - may be suitable for position scaling")
            
            elif pattern.pattern_type == PatternType.PERFORMANCE_PATTERN:
                if pattern.success_rate > 0.7:
                    recommendations.append("Historically successful pattern - maintain current strategy")
                else:
                    recommendations.append("Lower success rate pattern - consider defensive measures")
            
            # Add general advisory note
            recommendations.append("ADVISORY ONLY: All decisions remain rules-based per Constitution v1.3")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating pattern recommendations: {str(e)}")
            return ["Monitor pattern development", "Maintain rules-based decision making"]
    
    async def get_recognized_patterns(self, pattern_type: Optional[PatternType] = None) -> Dict[str, List[Pattern]]:
        """Get all recognized patterns, optionally filtered by type."""
        if pattern_type:
            return {pattern_type.value: self.recognized_patterns[pattern_type]}
        else:
            return {pt.value: patterns for pt, patterns in self.recognized_patterns.items()}
    
    async def get_recent_matches(self, hours_back: int = 24) -> List[PatternMatch]:
        """Get recent pattern matches."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        return [
            match for match in self.pattern_matches
            if match.matched_at >= cutoff_time
        ]
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern recognition statistics."""
        total_patterns = sum(len(patterns) for patterns in self.recognized_patterns.values())
        
        patterns_by_type = {
            pt.value: len(patterns) for pt, patterns in self.recognized_patterns.items()
        }
        
        recent_matches = await self.get_recent_matches(24)
        
        return {
            'total_patterns': total_patterns,
            'patterns_by_type': patterns_by_type,
            'historical_data_points': len(self.historical_data),
            'recent_matches_24h': len(recent_matches),
            'average_pattern_confidence': self._calculate_average_confidence(),
            'most_successful_patterns': self._get_most_successful_patterns()
        }
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence across all patterns."""
        all_patterns = []
        for patterns in self.recognized_patterns.values():
            all_patterns.extend(patterns)
        
        if not all_patterns:
            return 0.0
        
        return sum(p.confidence for p in all_patterns) / len(all_patterns)
    
    def _get_most_successful_patterns(self) -> List[Dict[str, Any]]:
        """Get the most successful patterns."""
        all_patterns = []
        for patterns in self.recognized_patterns.values():
            all_patterns.extend(patterns)
        
        # Sort by success rate
        all_patterns.sort(key=lambda p: p.success_rate, reverse=True)
        
        return [
            {
                'pattern_id': p.pattern_id,
                'pattern_type': p.pattern_type.value,
                'name': p.name,
                'success_rate': p.success_rate,
                'confidence': p.confidence,
                'occurrences': p.historical_occurrences
            }
            for p in all_patterns[:5]  # Top 5
        ]

