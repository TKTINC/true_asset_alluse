"""
Week Classification System - Constitution v1.3 Compliance

This module implements the week typing and classification system per GPT-5 feedback:
- Week classification based on market conditions and performance
- Natural language explanations for week types
- Integration with reporting and analytics

Per GPT-5 feedback for Constitution compliance.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WeekType(Enum):
    """Week classification types."""
    NORMAL = "normal"                    # Normal market week
    VOLATILE = "volatile"                # High volatility week
    TRENDING = "trending"                # Strong trending week
    CONSOLIDATION = "consolidation"      # Sideways/consolidation week
    EARNINGS = "earnings"                # Heavy earnings week
    EXPIRATION = "expiration"            # Options expiration week
    HOLIDAY = "holiday"                  # Holiday-shortened week
    EVENT_DRIVEN = "event_driven"        # Major event/announcement week
    CRISIS = "crisis"                    # Market crisis/stress week
    RECOVERY = "recovery"                # Post-crisis recovery week


class WeekPerformance(Enum):
    """Week performance classification."""
    EXCELLENT = "excellent"              # >2% weekly return
    GOOD = "good"                       # 1-2% weekly return
    SATISFACTORY = "satisfactory"        # 0.5-1% weekly return
    NEUTRAL = "neutral"                 # -0.5% to 0.5% weekly return
    POOR = "poor"                       # -1% to -0.5% weekly return
    VERY_POOR = "very_poor"             # <-1% weekly return


@dataclass
class WeekMetrics:
    """Week performance and market metrics."""
    week_start: datetime
    week_end: datetime
    portfolio_return: Decimal
    benchmark_return: Decimal
    volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    trades_executed: int
    positions_opened: int
    positions_closed: int
    premium_collected: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    vix_average: Decimal
    vix_max: Decimal
    market_correlation: Decimal


@dataclass
class WeekClassification:
    """Complete week classification result."""
    week_id: str
    week_start: datetime
    week_end: datetime
    week_type: WeekType
    performance: WeekPerformance
    metrics: WeekMetrics
    classification_factors: List[str]
    natural_language_summary: str
    key_events: List[str]
    lessons_learned: List[str]
    recommendations: List[str]
    confidence_score: Decimal
    created_timestamp: datetime


class WeekClassificationSystem:
    """Week classification and analysis system."""
    
    # Performance thresholds
    EXCELLENT_THRESHOLD = Decimal("0.02")      # 2%
    GOOD_THRESHOLD = Decimal("0.01")           # 1%
    SATISFACTORY_THRESHOLD = Decimal("0.005")  # 0.5%
    NEUTRAL_THRESHOLD = Decimal("0.005")       # ±0.5%
    POOR_THRESHOLD = Decimal("-0.01")          # -1%
    
    # Volatility thresholds
    HIGH_VOLATILITY_THRESHOLD = Decimal("0.25")  # 25% annualized
    NORMAL_VOLATILITY_THRESHOLD = Decimal("0.15") # 15% annualized
    
    # VIX thresholds
    HIGH_VIX_THRESHOLD = Decimal("30")         # VIX > 30
    ELEVATED_VIX_THRESHOLD = Decimal("20")     # VIX > 20
    
    def __init__(self):
        """Initialize week classification system."""
        self.classification_history = {}  # week_id -> WeekClassification
        self.classification_rules = self._initialize_classification_rules()
    
    def classify_week(
        self,
        week_start: datetime,
        week_end: datetime,
        portfolio_data: Dict[str, Any],
        market_data: Dict[str, Any],
        trading_data: Dict[str, Any]
    ) -> WeekClassification:
        """
        Classify a trading week based on performance and market conditions.
        
        Args:
            week_start: Start of the week
            week_end: End of the week
            portfolio_data: Portfolio performance data
            market_data: Market condition data
            trading_data: Trading activity data
            
        Returns:
            WeekClassification result
        """
        week_id = f"week_{week_start.strftime('%Y%m%d')}"
        
        try:
            # Calculate week metrics
            metrics = self._calculate_week_metrics(
                week_start, week_end, portfolio_data, market_data, trading_data
            )
            
            # Determine week type
            week_type = self._determine_week_type(metrics, market_data)
            
            # Determine performance classification
            performance = self._classify_performance(metrics.portfolio_return)
            
            # Identify classification factors
            classification_factors = self._identify_classification_factors(metrics, market_data)
            
            # Generate natural language summary
            natural_language_summary = self._generate_natural_language_summary(
                week_type, performance, metrics, classification_factors
            )
            
            # Extract key events
            key_events = self._extract_key_events(market_data, trading_data)
            
            # Generate lessons learned
            lessons_learned = self._generate_lessons_learned(week_type, performance, metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(week_type, performance, metrics)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(metrics, market_data)
            
            # Create classification
            classification = WeekClassification(
                week_id=week_id,
                week_start=week_start,
                week_end=week_end,
                week_type=week_type,
                performance=performance,
                metrics=metrics,
                classification_factors=classification_factors,
                natural_language_summary=natural_language_summary,
                key_events=key_events,
                lessons_learned=lessons_learned,
                recommendations=recommendations,
                confidence_score=confidence_score,
                created_timestamp=datetime.now()
            )
            
            # Store classification
            self.classification_history[week_id] = classification
            
            logger.info(f"Week classified: {week_id} as {week_type.value} with {performance.value} performance")
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying week {week_id}: {e}")
            raise
    
    def _calculate_week_metrics(
        self,
        week_start: datetime,
        week_end: datetime,
        portfolio_data: Dict[str, Any],
        market_data: Dict[str, Any],
        trading_data: Dict[str, Any]
    ) -> WeekMetrics:
        """Calculate comprehensive week metrics."""
        try:
            # Portfolio metrics
            portfolio_return = Decimal(str(portfolio_data.get("weekly_return", 0)))
            benchmark_return = Decimal(str(market_data.get("benchmark_return", 0)))
            volatility = Decimal(str(portfolio_data.get("volatility", 0)))
            max_drawdown = Decimal(str(portfolio_data.get("max_drawdown", 0)))
            sharpe_ratio = Decimal(str(portfolio_data.get("sharpe_ratio", 0)))
            
            # Trading metrics
            trades_executed = trading_data.get("trades_executed", 0)
            positions_opened = trading_data.get("positions_opened", 0)
            positions_closed = trading_data.get("positions_closed", 0)
            premium_collected = Decimal(str(trading_data.get("premium_collected", 0)))
            realized_pnl = Decimal(str(trading_data.get("realized_pnl", 0)))
            unrealized_pnl = Decimal(str(trading_data.get("unrealized_pnl", 0)))
            
            # Market metrics
            vix_average = Decimal(str(market_data.get("vix_average", 20)))
            vix_max = Decimal(str(market_data.get("vix_max", 25)))
            market_correlation = Decimal(str(portfolio_data.get("market_correlation", 0.5)))
            
            return WeekMetrics(
                week_start=week_start,
                week_end=week_end,
                portfolio_return=portfolio_return,
                benchmark_return=benchmark_return,
                volatility=volatility,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                trades_executed=trades_executed,
                positions_opened=positions_opened,
                positions_closed=positions_closed,
                premium_collected=premium_collected,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                vix_average=vix_average,
                vix_max=vix_max,
                market_correlation=market_correlation
            )
            
        except Exception as e:
            logger.error(f"Error calculating week metrics: {e}")
            raise
    
    def _determine_week_type(self, metrics: WeekMetrics, market_data: Dict[str, Any]) -> WeekType:
        """Determine week type based on market conditions and metrics."""
        try:
            # Check for specific week types
            
            # Crisis week - high VIX and large drawdown
            if metrics.vix_max > Decimal("40") and metrics.max_drawdown > Decimal("0.05"):
                return WeekType.CRISIS
            
            # Volatile week - high volatility
            if metrics.volatility > self.HIGH_VOLATILITY_THRESHOLD:
                return WeekType.VOLATILE
            
            # Earnings week - check if major earnings
            if market_data.get("major_earnings_count", 0) > 10:
                return WeekType.EARNINGS
            
            # Expiration week - check if options expiration
            if market_data.get("is_expiration_week", False):
                return WeekType.EXPIRATION
            
            # Holiday week - check if holiday
            if market_data.get("is_holiday_week", False):
                return WeekType.HOLIDAY
            
            # Event-driven week - major events
            if market_data.get("major_events_count", 0) > 0:
                return WeekType.EVENT_DRIVEN
            
            # Trending week - strong directional move
            if abs(metrics.portfolio_return) > Decimal("0.03") and metrics.sharpe_ratio > Decimal("1.0"):
                return WeekType.TRENDING
            
            # Recovery week - positive after negative
            if metrics.portfolio_return > Decimal("0.01") and market_data.get("previous_week_negative", False):
                return WeekType.RECOVERY
            
            # Consolidation week - low volatility, small moves
            if metrics.volatility < self.NORMAL_VOLATILITY_THRESHOLD and abs(metrics.portfolio_return) < Decimal("0.005"):
                return WeekType.CONSOLIDATION
            
            # Default to normal
            return WeekType.NORMAL
            
        except Exception as e:
            logger.error(f"Error determining week type: {e}")
            return WeekType.NORMAL
    
    def _classify_performance(self, portfolio_return: Decimal) -> WeekPerformance:
        """Classify week performance based on returns."""
        if portfolio_return >= self.EXCELLENT_THRESHOLD:
            return WeekPerformance.EXCELLENT
        elif portfolio_return >= self.GOOD_THRESHOLD:
            return WeekPerformance.GOOD
        elif portfolio_return >= self.SATISFACTORY_THRESHOLD:
            return WeekPerformance.SATISFACTORY
        elif portfolio_return >= -self.NEUTRAL_THRESHOLD:
            return WeekPerformance.NEUTRAL
        elif portfolio_return >= self.POOR_THRESHOLD:
            return WeekPerformance.POOR
        else:
            return WeekPerformance.VERY_POOR
    
    def _identify_classification_factors(self, metrics: WeekMetrics, market_data: Dict[str, Any]) -> List[str]:
        """Identify key factors that influenced the week classification."""
        factors = []
        
        # Performance factors
        if abs(metrics.portfolio_return) > Decimal("0.02"):
            factors.append(f"Large portfolio move: {metrics.portfolio_return:.1%}")
        
        # Volatility factors
        if metrics.volatility > self.HIGH_VOLATILITY_THRESHOLD:
            factors.append(f"High volatility: {metrics.volatility:.1%}")
        
        # VIX factors
        if metrics.vix_max > self.HIGH_VIX_THRESHOLD:
            factors.append(f"Elevated VIX: max {metrics.vix_max:.1f}")
        
        # Trading activity factors
        if metrics.trades_executed > 50:
            factors.append(f"High trading activity: {metrics.trades_executed} trades")
        
        # Market correlation factors
        if metrics.market_correlation > Decimal("0.8"):
            factors.append(f"High market correlation: {metrics.market_correlation:.2f}")
        elif metrics.market_correlation < Decimal("0.2"):
            factors.append(f"Low market correlation: {metrics.market_correlation:.2f}")
        
        # Premium collection factors
        if metrics.premium_collected > Decimal("10000"):
            factors.append(f"High premium collection: ${metrics.premium_collected:,.0f}")
        
        return factors
    
    def _generate_natural_language_summary(
        self,
        week_type: WeekType,
        performance: WeekPerformance,
        metrics: WeekMetrics,
        factors: List[str]
    ) -> str:
        """Generate natural language summary of the week."""
        try:
            # Performance description
            performance_descriptions = {
                WeekPerformance.EXCELLENT: "exceptional performance",
                WeekPerformance.GOOD: "strong performance",
                WeekPerformance.SATISFACTORY: "solid performance",
                WeekPerformance.NEUTRAL: "neutral performance",
                WeekPerformance.POOR: "disappointing performance",
                WeekPerformance.VERY_POOR: "poor performance"
            }
            
            # Week type description
            week_type_descriptions = {
                WeekType.NORMAL: "normal market conditions",
                WeekType.VOLATILE: "volatile market conditions",
                WeekType.TRENDING: "trending market conditions",
                WeekType.CONSOLIDATION: "consolidating market conditions",
                WeekType.EARNINGS: "earnings-heavy week",
                WeekType.EXPIRATION: "options expiration week",
                WeekType.HOLIDAY: "holiday-shortened week",
                WeekType.EVENT_DRIVEN: "event-driven market week",
                WeekType.CRISIS: "market crisis conditions",
                WeekType.RECOVERY: "market recovery conditions"
            }
            
            summary = f"This was a {week_type_descriptions[week_type]} week with {performance_descriptions[performance]}. "
            summary += f"The portfolio returned {metrics.portfolio_return:.2%} compared to the benchmark's {metrics.benchmark_return:.2%}. "
            
            if metrics.trades_executed > 0:
                summary += f"We executed {metrics.trades_executed} trades, "
                summary += f"opened {metrics.positions_opened} new positions, "
                summary += f"and closed {metrics.positions_closed} positions. "
            
            if metrics.premium_collected > 0:
                summary += f"Premium collected totaled ${metrics.premium_collected:,.0f}. "
            
            if factors:
                summary += f"Key factors included: {', '.join(factors[:3])}."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating natural language summary: {e}")
            return f"Week classification: {week_type.value} with {performance.value} performance."
    
    def _extract_key_events(self, market_data: Dict[str, Any], trading_data: Dict[str, Any]) -> List[str]:
        """Extract key events from the week."""
        events = []
        
        # Market events
        if market_data.get("fed_announcement"):
            events.append("Federal Reserve announcement")
        
        if market_data.get("earnings_releases"):
            events.append(f"{len(market_data['earnings_releases'])} major earnings releases")
        
        if market_data.get("economic_data_releases"):
            events.append("Key economic data releases")
        
        # Trading events
        if trading_data.get("large_position_changes"):
            events.append("Significant position adjustments")
        
        if trading_data.get("risk_events"):
            events.append("Risk management events")
        
        return events
    
    def _generate_lessons_learned(self, week_type: WeekType, performance: WeekPerformance, metrics: WeekMetrics) -> List[str]:
        """Generate lessons learned from the week."""
        lessons = []
        
        # Performance-based lessons
        if performance == WeekPerformance.EXCELLENT:
            lessons.append("Strategy performed exceptionally well in these conditions")
            lessons.append("Consider increasing position sizes in similar market environments")
        elif performance == WeekPerformance.VERY_POOR:
            lessons.append("Strategy struggled in these market conditions")
            lessons.append("Review risk management and position sizing")
        
        # Week type-based lessons
        if week_type == WeekType.VOLATILE:
            lessons.append("High volatility periods require careful position management")
            lessons.append("Consider reducing position sizes during volatile periods")
        elif week_type == WeekType.CONSOLIDATION:
            lessons.append("Consolidation periods favor premium collection strategies")
            lessons.append("Focus on high-probability, short-term trades")
        
        # Metrics-based lessons
        if metrics.sharpe_ratio < Decimal("0.5"):
            lessons.append("Risk-adjusted returns were suboptimal")
            lessons.append("Review risk management procedures")
        
        return lessons
    
    def _generate_recommendations(self, week_type: WeekType, performance: WeekPerformance, metrics: WeekMetrics) -> List[str]:
        """Generate recommendations for future similar weeks."""
        recommendations = []
        
        # Performance-based recommendations
        if performance in [WeekPerformance.POOR, WeekPerformance.VERY_POOR]:
            recommendations.append("Implement tighter risk controls")
            recommendations.append("Consider reducing position sizes")
        elif performance == WeekPerformance.EXCELLENT:
            recommendations.append("Document successful strategies for replication")
            recommendations.append("Consider scaling successful approaches")
        
        # Week type-based recommendations
        if week_type == WeekType.VOLATILE:
            recommendations.append("Increase monitoring frequency during volatile periods")
            recommendations.append("Implement dynamic position sizing based on volatility")
        elif week_type == WeekType.EARNINGS:
            recommendations.append("Avoid new positions before major earnings")
            recommendations.append("Consider earnings calendar in position planning")
        
        return recommendations
    
    def _calculate_confidence_score(self, metrics: WeekMetrics, market_data: Dict[str, Any]) -> Decimal:
        """Calculate confidence score for the classification."""
        try:
            confidence_factors = []
            
            # Data quality factors
            if metrics.trades_executed > 5:
                confidence_factors.append(0.2)  # Sufficient trading activity
            
            if market_data.get("data_quality_score", 0.8) > 0.8:
                confidence_factors.append(0.3)  # High data quality
            
            # Consistency factors
            if abs(metrics.portfolio_return - metrics.benchmark_return) < Decimal("0.05"):
                confidence_factors.append(0.2)  # Reasonable vs benchmark
            
            # Completeness factors
            if len(market_data.keys()) > 10:
                confidence_factors.append(0.3)  # Comprehensive market data
            
            confidence_score = Decimal(str(sum(confidence_factors)))
            return min(confidence_score, Decimal("1.0"))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return Decimal("0.5")  # Default moderate confidence
    
    def _initialize_classification_rules(self) -> Dict[str, Any]:
        """Initialize classification rules and thresholds."""
        return {
            "performance_thresholds": {
                "excellent": self.EXCELLENT_THRESHOLD,
                "good": self.GOOD_THRESHOLD,
                "satisfactory": self.SATISFACTORY_THRESHOLD,
                "neutral": self.NEUTRAL_THRESHOLD,
                "poor": self.POOR_THRESHOLD
            },
            "volatility_thresholds": {
                "high": self.HIGH_VOLATILITY_THRESHOLD,
                "normal": self.NORMAL_VOLATILITY_THRESHOLD
            },
            "vix_thresholds": {
                "high": self.HIGH_VIX_THRESHOLD,
                "elevated": self.ELEVATED_VIX_THRESHOLD
            }
        }
    
    def get_week_classification(self, week_id: str) -> Optional[WeekClassification]:
        """Get classification for a specific week."""
        return self.classification_history.get(week_id)
    
    def get_classification_summary(self) -> Dict[str, Any]:
        """Get summary of all week classifications."""
        if not self.classification_history:
            return {
                "total_weeks": 0,
                "week_types": {},
                "performance_distribution": {},
                "average_return": 0.0,
                "rule": "Constitution v1.3 - Week Classification System"
            }
        
        classifications = list(self.classification_history.values())
        
        # Week type distribution
        week_types = {}
        for classification in classifications:
            week_type = classification.week_type.value
            week_types[week_type] = week_types.get(week_type, 0) + 1
        
        # Performance distribution
        performance_distribution = {}
        for classification in classifications:
            performance = classification.performance.value
            performance_distribution[performance] = performance_distribution.get(performance, 0) + 1
        
        # Average return
        total_return = sum(c.metrics.portfolio_return for c in classifications)
        average_return = float(total_return / len(classifications))
        
        return {
            "total_weeks": len(classifications),
            "week_types": week_types,
            "performance_distribution": performance_distribution,
            "average_return": average_return,
            "classification_rules": self.classification_rules,
            "rule": "Constitution v1.3 - Week Classification System"
        }


# Global week classification system
week_classification_system = WeekClassificationSystem()

