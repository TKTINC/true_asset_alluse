"""
Intelligence Coordinator - ML Intelligence System

This module coordinates all ML intelligence components and provides a unified
interface for the adaptive learning, anomaly detection, pattern recognition,
and predictive analytics engines.

IMPORTANT: This system provides ADVISORY insights only. All wealth management
decisions remain 100% rules-based per Constitution v1.3.

Mission: "Autopilot for Wealth.....Engineered for compounding income and corpus"
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
import json

from .learning_engine.adaptive_learning_engine import AdaptiveLearningEngine, LearningData, LearningInsight
from .anomaly_detection.market_anomaly_detector import MarketAnomalyDetector, AnomalyAlert, AnomalyType
from .pattern_recognition.pattern_engine import PatternRecognitionEngine, PatternMatch, PatternType
from .predictive_analytics.predictive_engine import PredictiveAnalyticsEngine, Forecast, PredictionType

from src.ws1_rules_engine.audit import AuditTrailManager

logger = logging.getLogger(__name__)


class IntelligenceMode(Enum):
    """Intelligence operation modes."""
    LEARNING = "learning"
    MONITORING = "monitoring"
    FORECASTING = "forecasting"
    COMPREHENSIVE = "comprehensive"


@dataclass
class IntelligenceReport:
    """Comprehensive intelligence report."""
    report_id: str
    report_type: str
    generated_at: datetime
    
    # Learning insights
    learning_insights: List[LearningInsight]
    
    # Anomaly alerts
    anomaly_alerts: List[AnomalyAlert]
    
    # Pattern matches
    pattern_matches: List[PatternMatch]
    
    # Forecasts
    forecasts: List[Forecast]
    
    # Summary and recommendations
    key_findings: List[str]
    recommendations: List[str]
    confidence_score: float
    risk_assessment: str


@dataclass
class SystemIntelligence:
    """Current system intelligence state."""
    timestamp: datetime
    
    # Current conditions
    market_conditions: Dict[str, Any]
    system_performance: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    
    # Intelligence insights
    active_patterns: List[str]
    anomaly_count: int
    forecast_confidence: float
    learning_progress: Dict[str, float]
    
    # Recommendations
    immediate_actions: List[str]
    monitoring_priorities: List[str]
    risk_factors: List[str]


class IntelligenceCoordinator:
    """
    Coordinates all ML intelligence components to provide comprehensive
    insights and recommendations for the wealth management system.
    
    ADVISORY ONLY: Provides intelligence insights and recommendations but
    does not make any wealth management decisions. All decisions remain rules-based.
    """
    
    def __init__(self,
                 audit_manager: AuditTrailManager,
                 update_frequency_minutes: int = 60,
                 report_generation_frequency_hours: int = 24):
        """Initialize the intelligence coordinator."""
        self.audit_manager = audit_manager
        self.update_frequency_minutes = update_frequency_minutes
        self.report_generation_frequency_hours = report_generation_frequency_hours
        
        # Initialize component engines
        self.learning_engine = AdaptiveLearningEngine(audit_manager)
        self.anomaly_detector = MarketAnomalyDetector(audit_manager)
        self.pattern_engine = PatternRecognitionEngine(audit_manager)
        self.predictive_engine = PredictiveAnalyticsEngine(audit_manager)
        
        # Intelligence state
        self.current_intelligence: Optional[SystemIntelligence] = None
        self.intelligence_reports: List[IntelligenceReport] = []
        self.report_counter = 0
        
        # Operation mode
        self.operation_mode = IntelligenceMode.COMPREHENSIVE
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        
        logger.info("IntelligenceCoordinator initialized successfully")
    
    async def start_intelligence_system(self):
        """Start the intelligence system with background tasks."""
        try:
            # Start background monitoring
            monitoring_task = asyncio.create_task(self._background_monitoring())
            report_task = asyncio.create_task(self._background_reporting())
            
            self.background_tasks.extend([monitoring_task, report_task])
            
            # Initial intelligence update
            await self._update_system_intelligence()
            
            logger.info("Intelligence system started successfully")
            
        except Exception as e:
            logger.error(f"Error starting intelligence system: {str(e)}")
    
    async def stop_intelligence_system(self):
        """Stop the intelligence system and cleanup background tasks."""
        try:
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            self.background_tasks.clear()
            
            logger.info("Intelligence system stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping intelligence system: {str(e)}")
    
    async def _background_monitoring(self):
        """Background task for continuous monitoring."""
        try:
            while True:
                await self._update_system_intelligence()
                await asyncio.sleep(self.update_frequency_minutes * 60)
        except asyncio.CancelledError:
            logger.info("Background monitoring task cancelled")
        except Exception as e:
            logger.error(f"Error in background monitoring: {str(e)}")
    
    async def _background_reporting(self):
        """Background task for periodic report generation."""
        try:
            while True:
                await self._generate_periodic_report()
                await asyncio.sleep(self.report_generation_frequency_hours * 3600)
        except asyncio.CancelledError:
            logger.info("Background reporting task cancelled")
        except Exception as e:
            logger.error(f"Error in background reporting: {str(e)}")
    
    async def process_market_data(self, market_data: Dict[str, Any]):
        """Process new market data through all intelligence components."""
        try:
            timestamp = datetime.utcnow()
            
            # Add timestamp if not present
            if 'timestamp' not in market_data:
                market_data['timestamp'] = timestamp
            
            # Process through anomaly detection
            await self.anomaly_detector.add_market_data(market_data)
            
            # Process through pattern recognition
            await self.pattern_engine.add_historical_data(market_data)
            
            # Process through predictive analytics
            await self.predictive_engine.add_training_data(market_data)
            
            # Update system intelligence
            await self._update_system_intelligence()
            
            # Log data processing
            await self.audit_manager.log_event(
                event_type="INTELLIGENCE_MARKET_DATA_PROCESSED",
                details={
                    'timestamp': timestamp.isoformat(),
                    'data_keys': list(market_data.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing market data: {str(e)}")
    
    async def process_system_data(self, system_data: Dict[str, Any]):
        """Process new system performance data through all intelligence components."""
        try:
            timestamp = datetime.utcnow()
            
            # Add timestamp if not present
            if 'timestamp' not in system_data:
                system_data['timestamp'] = timestamp
            
            # Process through anomaly detection
            await self.anomaly_detector.add_system_data(system_data)
            
            # Create learning data for adaptive learning
            if self._is_complete_learning_data(system_data):
                learning_data = self._create_learning_data(system_data)
                await self.learning_engine.add_learning_data(learning_data)
            
            # Process through pattern recognition
            await self.pattern_engine.add_historical_data(system_data)
            
            # Process through predictive analytics
            await self.predictive_engine.add_training_data(system_data)
            
            # Update system intelligence
            await self._update_system_intelligence()
            
            # Log data processing
            await self.audit_manager.log_event(
                event_type="INTELLIGENCE_SYSTEM_DATA_PROCESSED",
                details={
                    'timestamp': timestamp.isoformat(),
                    'data_keys': list(system_data.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing system data: {str(e)}")
    
    def _is_complete_learning_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains enough information for learning."""
        required_fields = ['week_type', 'week_performance', 'weekly_return']
        return all(field in data for field in required_fields)
    
    def _create_learning_data(self, data: Dict[str, Any]) -> LearningData:
        """Create learning data from system data."""
        from src.ws1_rules_engine.constitution.week_classification import WeekType, WeekPerformance
        
        return LearningData(
            timestamp=data.get('timestamp', datetime.utcnow()),
            week_type=data.get('week_type', WeekType.NORMAL),
            week_performance=data.get('week_performance', WeekPerformance.AVERAGE),
            market_data={
                'market_return': data.get('market_return', 0.0),
                'market_volatility': data.get('market_volatility', 0.0),
                'vix_level': data.get('vix_level', 0.0),
                'volume_ratio': data.get('volume_ratio', 1.0)
            },
            performance_metrics={
                'weekly_return': data.get('weekly_return', 0.0),
                'sharpe_ratio': data.get('sharpe_ratio', 0.0),
                'max_drawdown': data.get('max_drawdown', 0.0)
            },
            risk_metrics={
                'portfolio_volatility': data.get('portfolio_volatility', 0.0),
                'var_95': data.get('var_95', 0.0),
                'concentration_risk': data.get('concentration_risk', 0.0)
            },
            protocol_level=data.get('protocol_level', 'L0'),
            system_actions=data.get('system_actions', []),
            outcomes={
                'weekly_return': data.get('weekly_return', 0.0),
                'realized_volatility': data.get('realized_volatility', 0.0),
                'protocol_success_score': data.get('protocol_success_score', 0.5)
            }
        )
    
    async def _update_system_intelligence(self):
        """Update the current system intelligence state."""
        try:
            timestamp = datetime.utcnow()
            
            # Get recent insights and alerts
            learning_insights = self.learning_engine.insights_cache[-5:]  # Last 5 insights
            anomaly_alerts = await self.anomaly_detector.get_recent_alerts(hours_back=24)
            pattern_matches = await self.pattern_engine.get_recent_matches(hours_back=24)
            active_forecasts = await self.predictive_engine.get_active_forecasts()
            
            # Calculate metrics
            anomaly_count = len(anomaly_alerts)
            forecast_confidence = (
                sum(f.overall_confidence for f in active_forecasts) / len(active_forecasts)
                if active_forecasts else 0.0
            )
            
            # Get learning progress
            model_performance = await self.learning_engine.get_model_performance()
            learning_progress = {
                mode: perf.r2_score if hasattr(perf, 'r2_score') else perf.accuracy
                for mode, perf in model_performance.items()
            }
            
            # Generate recommendations
            immediate_actions = self._generate_immediate_actions(
                anomaly_alerts, pattern_matches, active_forecasts
            )
            monitoring_priorities = self._generate_monitoring_priorities(
                anomaly_alerts, pattern_matches
            )
            risk_factors = self._generate_risk_factors(
                anomaly_alerts, pattern_matches, active_forecasts
            )
            
            # Create system intelligence
            self.current_intelligence = SystemIntelligence(
                timestamp=timestamp,
                market_conditions={
                    'volatility_regime': 'normal',  # Would be determined from data
                    'trend_direction': 'neutral',
                    'correlation_level': 'moderate'
                },
                system_performance={
                    'learning_models_trained': len(model_performance),
                    'anomaly_detection_active': True,
                    'pattern_recognition_active': True,
                    'forecasting_active': len(active_forecasts) > 0
                },
                risk_metrics={
                    'anomaly_count_24h': anomaly_count,
                    'high_confidence_patterns': len([m for m in pattern_matches if m.match_confidence > 0.8]),
                    'forecast_reliability': forecast_confidence
                },
                active_patterns=[m.pattern.name for m in pattern_matches[:3]],
                anomaly_count=anomaly_count,
                forecast_confidence=forecast_confidence,
                learning_progress=learning_progress,
                immediate_actions=immediate_actions,
                monitoring_priorities=monitoring_priorities,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error updating system intelligence: {str(e)}")
    
    def _generate_immediate_actions(self,
                                  anomaly_alerts: List[AnomalyAlert],
                                  pattern_matches: List[PatternMatch],
                                  forecasts: List[Forecast]) -> List[str]:
        """Generate immediate action recommendations."""
        actions = []
        
        # High severity anomalies
        high_severity_anomalies = [
            alert for alert in anomaly_alerts
            if alert.severity.value in ['high', 'critical']
        ]
        
        if high_severity_anomalies:
            actions.append(f"Review {len(high_severity_anomalies)} high-severity anomalies")
        
        # High confidence pattern matches
        high_confidence_patterns = [
            match for match in pattern_matches
            if match.match_confidence > 0.8
        ]
        
        if high_confidence_patterns:
            actions.append(f"Monitor {len(high_confidence_patterns)} high-confidence pattern matches")
        
        # Low confidence forecasts
        low_confidence_forecasts = [
            forecast for forecast in forecasts
            if forecast.overall_confidence < 0.6
        ]
        
        if low_confidence_forecasts:
            actions.append("Review forecasting models due to low confidence predictions")
        
        if not actions:
            actions.append("Continue normal monitoring - no immediate actions required")
        
        return actions
    
    def _generate_monitoring_priorities(self,
                                      anomaly_alerts: List[AnomalyAlert],
                                      pattern_matches: List[PatternMatch]) -> List[str]:
        """Generate monitoring priority recommendations."""
        priorities = []
        
        # Anomaly types to monitor
        anomaly_types = set(alert.anomaly_type for alert in anomaly_alerts)
        for anomaly_type in anomaly_types:
            priorities.append(f"Monitor {anomaly_type.value.replace('_', ' ')} conditions")
        
        # Pattern types to watch
        pattern_types = set(match.pattern.pattern_type for match in pattern_matches)
        for pattern_type in pattern_types:
            priorities.append(f"Track {pattern_type.value.replace('_', ' ')} patterns")
        
        # Default priorities
        if not priorities:
            priorities.extend([
                "Monitor market volatility conditions",
                "Track system performance metrics",
                "Watch for correlation breakdowns"
            ])
        
        return priorities[:5]  # Limit to top 5
    
    def _generate_risk_factors(self,
                             anomaly_alerts: List[AnomalyAlert],
                             pattern_matches: List[PatternMatch],
                             forecasts: List[Forecast]) -> List[str]:
        """Generate risk factor assessments."""
        risk_factors = []
        
        # Anomaly-based risks
        if len(anomaly_alerts) > 5:
            risk_factors.append("Multiple anomalies detected - increased system uncertainty")
        
        # Pattern-based risks
        low_confidence_patterns = [
            match for match in pattern_matches
            if match.match_confidence < 0.6
        ]
        
        if len(low_confidence_patterns) > len(pattern_matches) / 2:
            risk_factors.append("Many low-confidence pattern matches - pattern reliability concerns")
        
        # Forecast-based risks
        for forecast in forecasts:
            if forecast.overall_confidence < 0.5:
                risk_factors.append(f"Low confidence forecast: {forecast.forecast_name}")
        
        # Default risk factors
        if not risk_factors:
            risk_factors.extend([
                "Model predictions based on historical data may not capture regime changes",
                "Extreme market conditions may reduce model effectiveness"
            ])
        
        return risk_factors
    
    async def generate_intelligence_report(self,
                                         report_type: str = "comprehensive",
                                         include_forecasts: bool = True) -> IntelligenceReport:
        """Generate a comprehensive intelligence report."""
        try:
            self.report_counter += 1
            timestamp = datetime.utcnow()
            
            # Gather data from all components
            learning_insights = self.learning_engine.insights_cache[-10:]  # Last 10 insights
            anomaly_alerts = await self.anomaly_detector.get_recent_alerts(hours_back=48)
            pattern_matches = await self.pattern_engine.get_recent_matches(hours_back=48)
            
            forecasts = []
            if include_forecasts:
                forecasts = await self.predictive_engine.get_active_forecasts()
            
            # Generate key findings
            key_findings = self._generate_key_findings(
                learning_insights, anomaly_alerts, pattern_matches, forecasts
            )
            
            # Generate recommendations
            recommendations = self._generate_comprehensive_recommendations(
                learning_insights, anomaly_alerts, pattern_matches, forecasts
            )
            
            # Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(
                learning_insights, anomaly_alerts, pattern_matches, forecasts
            )
            
            # Generate risk assessment
            risk_assessment = self._generate_risk_assessment(
                anomaly_alerts, pattern_matches, forecasts
            )
            
            # Create report
            report = IntelligenceReport(
                report_id=f"intel_report_{self.report_counter}_{int(timestamp.timestamp())}",
                report_type=report_type,
                generated_at=timestamp,
                learning_insights=learning_insights,
                anomaly_alerts=anomaly_alerts,
                pattern_matches=pattern_matches,
                forecasts=forecasts,
                key_findings=key_findings,
                recommendations=recommendations,
                confidence_score=confidence_score,
                risk_assessment=risk_assessment
            )
            
            # Store report
            self.intelligence_reports.append(report)
            
            # Keep only recent reports
            cutoff_time = timestamp - timedelta(days=30)
            self.intelligence_reports = [
                r for r in self.intelligence_reports
                if r.generated_at >= cutoff_time
            ]
            
            # Log report generation
            await self.audit_manager.log_event(
                event_type="INTELLIGENCE_REPORT_GENERATED",
                details={
                    'report_id': report.report_id,
                    'report_type': report_type,
                    'insights_count': len(learning_insights),
                    'anomalies_count': len(anomaly_alerts),
                    'patterns_count': len(pattern_matches),
                    'forecasts_count': len(forecasts),
                    'confidence_score': confidence_score
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating intelligence report: {str(e)}")
            raise
    
    def _generate_key_findings(self,
                             insights: List[LearningInsight],
                             alerts: List[AnomalyAlert],
                             matches: List[PatternMatch],
                             forecasts: List[Forecast]) -> List[str]:
        """Generate key findings from intelligence data."""
        findings = []
        
        # Learning insights findings
        if insights:
            high_confidence_insights = [i for i in insights if i.confidence > 0.8]
            if high_confidence_insights:
                findings.append(f"Identified {len(high_confidence_insights)} high-confidence learning insights")
        
        # Anomaly findings
        if alerts:
            critical_alerts = [a for a in alerts if a.severity.value == 'critical']
            if critical_alerts:
                findings.append(f"Detected {len(critical_alerts)} critical anomalies requiring attention")
        
        # Pattern findings
        if matches:
            strong_patterns = [m for m in matches if m.match_strength > 0.8]
            if strong_patterns:
                findings.append(f"Found {len(strong_patterns)} strong pattern matches")
        
        # Forecast findings
        if forecasts:
            reliable_forecasts = [f for f in forecasts if f.overall_confidence > 0.7]
            if reliable_forecasts:
                findings.append(f"Generated {len(reliable_forecasts)} reliable forecasts")
        
        # Default finding
        if not findings:
            findings.append("System operating within normal parameters")
        
        return findings
    
    def _generate_comprehensive_recommendations(self,
                                             insights: List[LearningInsight],
                                             alerts: List[AnomalyAlert],
                                             matches: List[PatternMatch],
                                             forecasts: List[Forecast]) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = []
        
        # Always include the advisory note
        recommendations.append("ADVISORY ONLY: All recommendations are for information purposes - decisions remain rules-based per Constitution v1.3")
        
        # Learning-based recommendations
        for insight in insights[-3:]:  # Last 3 insights
            if insight.recommendations:
                recommendations.extend(insight.recommendations[:2])  # Top 2 per insight
        
        # Anomaly-based recommendations
        for alert in alerts[-3:]:  # Last 3 alerts
            if alert.recommendations:
                recommendations.extend(alert.recommendations[:2])  # Top 2 per alert
        
        # Pattern-based recommendations
        for match in matches[-3:]:  # Last 3 matches
            if match.recommendations:
                recommendations.extend(match.recommendations[:2])  # Top 2 per match
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limit to top 10
    
    def _calculate_overall_confidence(self,
                                    insights: List[LearningInsight],
                                    alerts: List[AnomalyAlert],
                                    matches: List[PatternMatch],
                                    forecasts: List[Forecast]) -> float:
        """Calculate overall confidence score."""
        confidence_scores = []
        
        # Learning insights confidence
        if insights:
            avg_insight_confidence = sum(i.confidence for i in insights) / len(insights)
            confidence_scores.append(avg_insight_confidence)
        
        # Anomaly detection confidence (inverse of alert count)
        if alerts:
            # More alerts = lower confidence in normal conditions
            anomaly_confidence = max(0.0, 1.0 - len(alerts) / 10.0)
            confidence_scores.append(anomaly_confidence)
        else:
            confidence_scores.append(0.8)  # No anomalies = good confidence
        
        # Pattern matching confidence
        if matches:
            avg_pattern_confidence = sum(m.match_confidence for m in matches) / len(matches)
            confidence_scores.append(avg_pattern_confidence)
        
        # Forecasting confidence
        if forecasts:
            avg_forecast_confidence = sum(f.overall_confidence for f in forecasts) / len(forecasts)
            confidence_scores.append(avg_forecast_confidence)
        
        # Calculate weighted average
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.5  # Neutral confidence
    
    def _generate_risk_assessment(self,
                                alerts: List[AnomalyAlert],
                                matches: List[PatternMatch],
                                forecasts: List[Forecast]) -> str:
        """Generate overall risk assessment."""
        risk_score = 0.0
        
        # Anomaly risk
        critical_alerts = len([a for a in alerts if a.severity.value == 'critical'])
        high_alerts = len([a for a in alerts if a.severity.value == 'high'])
        risk_score += critical_alerts * 0.3 + high_alerts * 0.2
        
        # Pattern risk (low confidence patterns increase risk)
        low_confidence_patterns = len([m for m in matches if m.match_confidence < 0.6])
        risk_score += low_confidence_patterns * 0.1
        
        # Forecast risk (low confidence forecasts increase risk)
        low_confidence_forecasts = len([f for f in forecasts if f.overall_confidence < 0.6])
        risk_score += low_confidence_forecasts * 0.15
        
        # Determine risk level
        if risk_score >= 1.0:
            return "HIGH - Multiple risk factors detected, increased monitoring recommended"
        elif risk_score >= 0.5:
            return "MEDIUM - Some risk factors present, maintain vigilant monitoring"
        else:
            return "LOW - System operating within normal risk parameters"
    
    async def _generate_periodic_report(self):
        """Generate periodic intelligence report."""
        try:
            report = await self.generate_intelligence_report("periodic")
            logger.info(f"Generated periodic intelligence report: {report.report_id}")
        except Exception as e:
            logger.error(f"Error generating periodic report: {str(e)}")
    
    async def get_current_intelligence(self) -> Optional[SystemIntelligence]:
        """Get current system intelligence state."""
        return self.current_intelligence
    
    async def get_recent_reports(self, days_back: int = 7) -> List[IntelligenceReport]:
        """Get recent intelligence reports."""
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)
        
        return [
            report for report in self.intelligence_reports
            if report.generated_at >= cutoff_time
        ]
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            # Get component statuses
            learning_performance = await self.learning_engine.get_model_performance()
            anomaly_stats = await self.anomaly_detector.get_anomaly_statistics()
            pattern_stats = await self.pattern_engine.get_pattern_statistics()
            predictive_stats = await self.predictive_engine.get_model_performance_summary()
            
            return {
                'intelligence_coordinator': {
                    'status': 'active',
                    'operation_mode': self.operation_mode.value,
                    'background_tasks_running': len(self.background_tasks),
                    'reports_generated': len(self.intelligence_reports),
                    'last_intelligence_update': self.current_intelligence.timestamp.isoformat() if self.current_intelligence else None
                },
                'learning_engine': {
                    'models_trained': len(learning_performance),
                    'insights_generated': len(self.learning_engine.insights_cache),
                    'learning_data_points': len(self.learning_engine.learning_data)
                },
                'anomaly_detector': anomaly_stats,
                'pattern_engine': pattern_stats,
                'predictive_engine': predictive_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {'error': str(e)}
    
    async def export_intelligence_data(self) -> Dict[str, Any]:
        """Export intelligence data for backup or analysis."""
        try:
            return {
                'current_intelligence': asdict(self.current_intelligence) if self.current_intelligence else None,
                'recent_reports': [asdict(report) for report in self.intelligence_reports[-10:]],
                'system_status': await self.get_system_status(),
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting intelligence data: {str(e)}")
            return {'error': str(e)}

