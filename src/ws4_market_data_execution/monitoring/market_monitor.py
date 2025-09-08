"""
Market Monitor

This module implements comprehensive real-time market monitoring that tracks
market conditions, volatility, liquidity, and system health to support
trading decisions and risk management in the True-Asset-ALLUSE system.
"""

from typing import Dict, Any, Optional, List, Callable, Set
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading
import time
from dataclasses import dataclass, asdict
import statistics
import uuid

from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws2_protocol_engine.escalation.escalation_manager import EscalationManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Market condition states."""
    NORMAL = "normal"
    VOLATILE = "volatile"
    HIGHLY_VOLATILE = "highly_volatile"
    LOW_LIQUIDITY = "low_liquidity"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringFrequency(Enum):
    """Monitoring frequency levels."""
    REAL_TIME = "real_time"      # Every second
    HIGH = "high"                # Every 5 seconds
    MEDIUM = "medium"            # Every 30 seconds
    LOW = "low"                  # Every 5 minutes


@dataclass
class MarketMetrics:
    """Market metrics snapshot."""
    timestamp: datetime
    symbol: str
    price: Decimal
    volume: int
    bid: Decimal
    ask: Decimal
    spread: Decimal
    spread_percentage: Decimal
    volatility_1min: Decimal
    volatility_5min: Decimal
    volatility_15min: Decimal
    price_change_1min: Decimal
    price_change_5min: Decimal
    price_change_15min: Decimal
    volume_avg_ratio: Decimal
    liquidity_score: Decimal
    market_condition: MarketCondition


@dataclass
class MarketAlert:
    """Market alert structure."""
    alert_id: str
    symbol: str
    alert_type: str
    severity: AlertSeverity
    message: str
    metrics: MarketMetrics
    threshold_breached: str
    threshold_value: Decimal
    current_value: Decimal
    timestamp: datetime
    acknowledged: bool
    metadata: Dict[str, Any]


@dataclass
class MonitoringRule:
    """Market monitoring rule."""
    rule_id: str
    name: str
    symbol: str
    rule_type: str
    threshold: Decimal
    comparison: str  # "greater_than", "less_than", "equal_to", "not_equal_to"
    severity: AlertSeverity
    frequency: MonitoringFrequency
    enabled: bool
    callback: Optional[Callable[[MarketAlert], None]]
    metadata: Dict[str, Any]


class MarketMonitor:
    """
    Comprehensive Market Monitor.
    
    Provides real-time market monitoring, condition analysis, volatility tracking,
    liquidity assessment, and intelligent alerting for the True-Asset-ALLUSE system.
    Integrates with the Protocol Engine for risk management escalation.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 escalation_manager: EscalationManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize market monitor.
        
        Args:
            audit_manager: Audit trail manager
            escalation_manager: Protocol escalation manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.escalation_manager = escalation_manager
        self.config = config or {}
        
        # Configuration parameters
        self.volatility_window_1min = self.config.get("volatility_window_1min", 60)
        self.volatility_window_5min = self.config.get("volatility_window_5min", 300)
        self.volatility_window_15min = self.config.get("volatility_window_15min", 900)
        self.volume_avg_window = self.config.get("volume_avg_window", 20)
        self.max_alerts_per_minute = self.config.get("max_alerts_per_minute", 10)
        self.alert_cooldown_seconds = self.config.get("alert_cooldown_seconds", 60)
        
        # Default thresholds
        self.default_thresholds = {
            "volatility_warning": Decimal("0.02"),      # 2% volatility warning
            "volatility_critical": Decimal("0.05"),     # 5% volatility critical
            "spread_warning": Decimal("0.01"),          # 1% spread warning
            "spread_critical": Decimal("0.03"),         # 3% spread critical
            "volume_low": Decimal("0.5"),               # 50% of average volume
            "price_change_warning": Decimal("0.03"),    # 3% price change warning
            "price_change_critical": Decimal("0.07"),   # 7% price change critical
            "liquidity_low": Decimal("0.3")             # 30% liquidity score
        }
        
        # Market data storage
        self.current_metrics = {}  # symbol -> MarketMetrics
        self.historical_data = {}  # symbol -> List[price_data]
        self.monitoring_rules = {}  # rule_id -> MonitoringRule
        self.active_alerts = {}    # alert_id -> MarketAlert
        self.alert_history = {}    # alert_id -> MarketAlert
        
        # Monitoring state
        self.monitored_symbols = set()
        self.monitoring_frequencies = {}  # symbol -> MonitoringFrequency
        
        # Threading and processing
        self.monitor_lock = threading.RLock()
        self.monitor_thread = None
        self.running = False
        
        # Alert rate limiting
        self.alert_counts = {}  # minute_timestamp -> count
        self.last_alert_times = {}  # rule_id -> timestamp
        
        # Performance metrics
        self.metrics = {
            "total_alerts": 0,
            "alerts_by_severity": {
                "info": 0,
                "warning": 0,
                "critical": 0,
                "emergency": 0
            },
            "symbols_monitored": 0,
            "rules_active": 0,
            "monitoring_uptime": 0,
            "last_update": None,
            "processing_times": []
        }
        
        logger.info("Market Monitor initialized")
    
    def start(self) -> Dict[str, Any]:
        """Start market monitoring."""
        try:
            if self.running:
                return {"success": False, "error": "Market monitor already running"}
            
            self.running = True
            
            # Initialize default monitoring rules
            self._initialize_default_rules()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Market Monitor started")
            
            return {
                "success": True,
                "monitored_symbols": len(self.monitored_symbols),
                "active_rules": len([r for r in self.monitoring_rules.values() if r.enabled]),
                "start_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting market monitor: {str(e)}", exc_info=True)
            self.running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop market monitoring."""
        try:
            if not self.running:
                return {"success": False, "error": "Market monitor not running"}
            
            self.running = False
            
            # Wait for monitoring thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)
            
            logger.info("Market Monitor stopped")
            
            return {
                "success": True,
                "total_alerts_generated": self.metrics["total_alerts"],
                "stop_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping market monitor: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_symbol_monitoring(self, 
                            symbol: str,
                            frequency: MonitoringFrequency = MonitoringFrequency.MEDIUM) -> Dict[str, Any]:
        """Add symbol to monitoring."""
        try:
            with self.monitor_lock:
                self.monitored_symbols.add(symbol)
                self.monitoring_frequencies[symbol] = frequency
                
                # Initialize historical data storage
                if symbol not in self.historical_data:
                    self.historical_data[symbol] = []
            
            self.metrics["symbols_monitored"] = len(self.monitored_symbols)
            
            logger.info(f"Added symbol {symbol} to monitoring with {frequency.value} frequency")
            
            return {
                "success": True,
                "symbol": symbol,
                "frequency": frequency.value,
                "total_monitored": len(self.monitored_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error adding symbol monitoring: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def remove_symbol_monitoring(self, symbol: str) -> Dict[str, Any]:
        """Remove symbol from monitoring."""
        try:
            with self.monitor_lock:
                self.monitored_symbols.discard(symbol)
                self.monitoring_frequencies.pop(symbol, None)
                
                # Remove symbol-specific rules
                rules_to_remove = [rule_id for rule_id, rule in self.monitoring_rules.items() 
                                 if rule.symbol == symbol]
                
                for rule_id in rules_to_remove:
                    del self.monitoring_rules[rule_id]
            
            self.metrics["symbols_monitored"] = len(self.monitored_symbols)
            self.metrics["rules_active"] = len([r for r in self.monitoring_rules.values() if r.enabled])
            
            logger.info(f"Removed symbol {symbol} from monitoring")
            
            return {
                "success": True,
                "symbol": symbol,
                "rules_removed": len(rules_to_remove),
                "total_monitored": len(self.monitored_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error removing symbol monitoring: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def add_monitoring_rule(self, rule: MonitoringRule) -> Dict[str, Any]:
        """Add custom monitoring rule."""
        try:
            with self.monitor_lock:
                self.monitoring_rules[rule.rule_id] = rule
                
                # Ensure symbol is being monitored
                if rule.symbol not in self.monitored_symbols:
                    self.add_symbol_monitoring(rule.symbol, rule.frequency)
            
            self.metrics["rules_active"] = len([r for r in self.monitoring_rules.values() if r.enabled])
            
            logger.info(f"Added monitoring rule {rule.rule_id} for {rule.symbol}")
            
            return {
                "success": True,
                "rule_id": rule.rule_id,
                "symbol": rule.symbol,
                "rule_type": rule.rule_type,
                "total_rules": len(self.monitoring_rules)
            }
            
        except Exception as e:
            logger.error(f"Error adding monitoring rule: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "rule_id": rule.rule_id
            }
    
    def remove_monitoring_rule(self, rule_id: str) -> Dict[str, Any]:
        """Remove monitoring rule."""
        try:
            with self.monitor_lock:
                if rule_id not in self.monitoring_rules:
                    return {
                        "success": False,
                        "error": "Rule not found",
                        "rule_id": rule_id
                    }
                
                rule = self.monitoring_rules[rule_id]
                del self.monitoring_rules[rule_id]
            
            self.metrics["rules_active"] = len([r for r in self.monitoring_rules.values() if r.enabled])
            
            logger.info(f"Removed monitoring rule {rule_id}")
            
            return {
                "success": True,
                "rule_id": rule_id,
                "symbol": rule.symbol,
                "total_rules": len(self.monitoring_rules)
            }
            
        except Exception as e:
            logger.error(f"Error removing monitoring rule: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "rule_id": rule_id
            }
    
    def get_current_metrics(self, symbol: str) -> Optional[MarketMetrics]:
        """Get current market metrics for symbol."""
        try:
            with self.monitor_lock:
                return self.current_metrics.get(symbol)
                
        except Exception as e:
            logger.error(f"Error getting current metrics for {symbol}: {str(e)}")
            return None
    
    def get_active_alerts(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get active alerts."""
        try:
            with self.monitor_lock:
                if symbol:
                    alerts = {alert_id: alert for alert_id, alert in self.active_alerts.items() 
                            if alert.symbol == symbol}
                else:
                    alerts = self.active_alerts.copy()
            
            return {
                "success": True,
                "alerts": {alert_id: asdict(alert) for alert_id, alert in alerts.items()},
                "total_alerts": len(alerts),
                "symbol_filter": symbol
            }
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge alert."""
        try:
            with self.monitor_lock:
                if alert_id not in self.active_alerts:
                    return {
                        "success": False,
                        "error": "Alert not found",
                        "alert_id": alert_id
                    }
                
                alert = self.active_alerts[alert_id]
                alert.acknowledged = True
                
                # Move to history
                self.alert_history[alert_id] = alert
                del self.active_alerts[alert_id]
            
            logger.info(f"Acknowledged alert {alert_id}")
            
            return {
                "success": True,
                "alert_id": alert_id,
                "acknowledgment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "alert_id": alert_id
            }
    
    def update_market_data(self, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update market data for symbol."""
        try:
            start_time = time.time()
            
            # Calculate metrics
            metrics = self._calculate_market_metrics(symbol, price_data)
            
            with self.monitor_lock:
                self.current_metrics[symbol] = metrics
                
                # Store historical data
                if symbol not in self.historical_data:
                    self.historical_data[symbol] = []
                
                self.historical_data[symbol].append({
                    "timestamp": datetime.now(),
                    "price": price_data.get("price", Decimal("0")),
                    "volume": price_data.get("volume", 0),
                    "bid": price_data.get("bid", Decimal("0")),
                    "ask": price_data.get("ask", Decimal("0"))
                })
                
                # Keep only recent data
                max_history = 1000
                if len(self.historical_data[symbol]) > max_history:
                    self.historical_data[symbol] = self.historical_data[symbol][-max_history:]
            
            # Check monitoring rules
            self._check_monitoring_rules(symbol, metrics)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self.metrics["processing_times"].append(processing_time)
            if len(self.metrics["processing_times"]) > 100:
                self.metrics["processing_times"] = self.metrics["processing_times"][-100:]
            
            return {
                "success": True,
                "symbol": symbol,
                "metrics": asdict(metrics),
                "processing_time_ms": processing_time * 1000
            }
            
        except Exception as e:
            logger.error(f"Error updating market data for {symbol}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def _initialize_default_rules(self):
        """Initialize default monitoring rules."""
        try:
            # Default rules for common market conditions
            default_rules = [
                {
                    "rule_type": "volatility_warning",
                    "threshold": self.default_thresholds["volatility_warning"],
                    "comparison": "greater_than",
                    "severity": AlertSeverity.WARNING
                },
                {
                    "rule_type": "volatility_critical",
                    "threshold": self.default_thresholds["volatility_critical"],
                    "comparison": "greater_than",
                    "severity": AlertSeverity.CRITICAL
                },
                {
                    "rule_type": "spread_warning",
                    "threshold": self.default_thresholds["spread_warning"],
                    "comparison": "greater_than",
                    "severity": AlertSeverity.WARNING
                },
                {
                    "rule_type": "price_change_critical",
                    "threshold": self.default_thresholds["price_change_critical"],
                    "comparison": "greater_than",
                    "severity": AlertSeverity.CRITICAL
                }
            ]
            
            for rule_config in default_rules:
                rule = MonitoringRule(
                    rule_id=f"default_{rule_config['rule_type']}_{uuid.uuid4().hex[:8]}",
                    name=f"Default {rule_config['rule_type'].replace('_', ' ').title()}",
                    symbol="*",  # Apply to all symbols
                    rule_type=rule_config["rule_type"],
                    threshold=rule_config["threshold"],
                    comparison=rule_config["comparison"],
                    severity=rule_config["severity"],
                    frequency=MonitoringFrequency.MEDIUM,
                    enabled=True,
                    callback=None,
                    metadata={"default": True}
                )
                
                self.monitoring_rules[rule.rule_id] = rule
            
            logger.info(f"Initialized {len(default_rules)} default monitoring rules")
            
        except Exception as e:
            logger.error(f"Error initializing default rules: {str(e)}")
    
    def _calculate_market_metrics(self, symbol: str, price_data: Dict[str, Any]) -> MarketMetrics:
        """Calculate market metrics for symbol."""
        try:
            now = datetime.now()
            price = Decimal(str(price_data.get("price", 0)))
            volume = int(price_data.get("volume", 0))
            bid = Decimal(str(price_data.get("bid", 0)))
            ask = Decimal(str(price_data.get("ask", 0)))
            
            # Calculate spread
            spread = ask - bid if ask > bid else Decimal("0")
            spread_percentage = (spread / bid) if bid > 0 else Decimal("0")
            
            # Get historical data for calculations
            historical = self.historical_data.get(symbol, [])
            
            # Calculate volatility (simplified - would use proper statistical methods)
            volatility_1min = self._calculate_volatility(historical, 60)
            volatility_5min = self._calculate_volatility(historical, 300)
            volatility_15min = self._calculate_volatility(historical, 900)
            
            # Calculate price changes
            price_change_1min = self._calculate_price_change(historical, 60)
            price_change_5min = self._calculate_price_change(historical, 300)
            price_change_15min = self._calculate_price_change(historical, 900)
            
            # Calculate volume ratio
            volume_avg_ratio = self._calculate_volume_ratio(historical, volume)
            
            # Calculate liquidity score
            liquidity_score = self._calculate_liquidity_score(spread_percentage, volume, volume_avg_ratio)
            
            # Determine market condition
            market_condition = self._determine_market_condition(
                volatility_5min, price_change_5min, liquidity_score
            )
            
            return MarketMetrics(
                timestamp=now,
                symbol=symbol,
                price=price,
                volume=volume,
                bid=bid,
                ask=ask,
                spread=spread,
                spread_percentage=spread_percentage,
                volatility_1min=volatility_1min,
                volatility_5min=volatility_5min,
                volatility_15min=volatility_15min,
                price_change_1min=price_change_1min,
                price_change_5min=price_change_5min,
                price_change_15min=price_change_15min,
                volume_avg_ratio=volume_avg_ratio,
                liquidity_score=liquidity_score,
                market_condition=market_condition
            )
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {str(e)}")
            # Return default metrics on error
            return MarketMetrics(
                timestamp=datetime.now(),
                symbol=symbol,
                price=Decimal("0"),
                volume=0,
                bid=Decimal("0"),
                ask=Decimal("0"),
                spread=Decimal("0"),
                spread_percentage=Decimal("0"),
                volatility_1min=Decimal("0"),
                volatility_5min=Decimal("0"),
                volatility_15min=Decimal("0"),
                price_change_1min=Decimal("0"),
                price_change_5min=Decimal("0"),
                price_change_15min=Decimal("0"),
                volume_avg_ratio=Decimal("1"),
                liquidity_score=Decimal("1"),
                market_condition=MarketCondition.NORMAL
            )
    
    def _calculate_volatility(self, historical: List[Dict], window_seconds: int) -> Decimal:
        """Calculate volatility over time window."""
        try:
            if not historical:
                return Decimal("0")
            
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            recent_prices = [
                float(data["price"]) for data in historical 
                if data["timestamp"] >= cutoff_time and data["price"] > 0
            ]
            
            if len(recent_prices) < 2:
                return Decimal("0")
            
            # Calculate standard deviation of price changes
            price_changes = [
                (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
                for i in range(1, len(recent_prices))
            ]
            
            if not price_changes:
                return Decimal("0")
            
            volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
            return Decimal(str(volatility))
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return Decimal("0")
    
    def _calculate_price_change(self, historical: List[Dict], window_seconds: int) -> Decimal:
        """Calculate price change over time window."""
        try:
            if not historical:
                return Decimal("0")
            
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            recent_data = [data for data in historical if data["timestamp"] >= cutoff_time]
            
            if len(recent_data) < 2:
                return Decimal("0")
            
            oldest_price = recent_data[0]["price"]
            current_price = recent_data[-1]["price"]
            
            if oldest_price == 0:
                return Decimal("0")
            
            price_change = (current_price - oldest_price) / oldest_price
            return price_change
            
        except Exception as e:
            logger.error(f"Error calculating price change: {str(e)}")
            return Decimal("0")
    
    def _calculate_volume_ratio(self, historical: List[Dict], current_volume: int) -> Decimal:
        """Calculate current volume vs average volume ratio."""
        try:
            if not historical:
                return Decimal("1")
            
            recent_volumes = [data["volume"] for data in historical[-self.volume_avg_window:]]
            
            if not recent_volumes:
                return Decimal("1")
            
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            
            if avg_volume == 0:
                return Decimal("1")
            
            return Decimal(str(current_volume / avg_volume))
            
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {str(e)}")
            return Decimal("1")
    
    def _calculate_liquidity_score(self, spread_pct: Decimal, volume: int, volume_ratio: Decimal) -> Decimal:
        """Calculate liquidity score (0-1, higher is better)."""
        try:
            # Simple liquidity scoring based on spread and volume
            spread_score = max(Decimal("0"), Decimal("1") - spread_pct * 10)  # Penalize wide spreads
            volume_score = min(Decimal("1"), volume_ratio)  # Reward high volume
            
            liquidity_score = (spread_score + volume_score) / 2
            return max(Decimal("0"), min(Decimal("1"), liquidity_score))
            
        except Exception as e:
            logger.error(f"Error calculating liquidity score: {str(e)}")
            return Decimal("0.5")
    
    def _determine_market_condition(self, volatility: Decimal, price_change: Decimal, liquidity: Decimal) -> MarketCondition:
        """Determine overall market condition."""
        try:
            # High volatility conditions
            if volatility > self.default_thresholds["volatility_critical"]:
                return MarketCondition.HIGHLY_VOLATILE
            elif volatility > self.default_thresholds["volatility_warning"]:
                return MarketCondition.VOLATILE
            
            # Low liquidity condition
            if liquidity < self.default_thresholds["liquidity_low"]:
                return MarketCondition.LOW_LIQUIDITY
            
            # Trending conditions
            if abs(price_change) > self.default_thresholds["price_change_warning"]:
                if price_change > 0:
                    return MarketCondition.TRENDING_UP
                else:
                    return MarketCondition.TRENDING_DOWN
            
            # Crisis condition (multiple factors)
            if (volatility > self.default_thresholds["volatility_warning"] and 
                liquidity < self.default_thresholds["liquidity_low"] and
                abs(price_change) > self.default_thresholds["price_change_warning"]):
                return MarketCondition.CRISIS
            
            # Default to normal
            return MarketCondition.NORMAL
            
        except Exception as e:
            logger.error(f"Error determining market condition: {str(e)}")
            return MarketCondition.NORMAL
    
    def _check_monitoring_rules(self, symbol: str, metrics: MarketMetrics):
        """Check monitoring rules against current metrics."""
        try:
            with self.monitor_lock:
                applicable_rules = [
                    rule for rule in self.monitoring_rules.values()
                    if rule.enabled and (rule.symbol == symbol or rule.symbol == "*")
                ]
            
            for rule in applicable_rules:
                try:
                    self._evaluate_rule(rule, metrics)
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error checking monitoring rules: {str(e)}")
    
    def _evaluate_rule(self, rule: MonitoringRule, metrics: MarketMetrics):
        """Evaluate single monitoring rule."""
        try:
            # Check rate limiting
            if not self._check_rate_limit(rule):
                return
            
            # Get metric value based on rule type
            metric_value = self._get_metric_value(rule.rule_type, metrics)
            
            if metric_value is None:
                return
            
            # Evaluate condition
            condition_met = False
            
            if rule.comparison == "greater_than":
                condition_met = metric_value > rule.threshold
            elif rule.comparison == "less_than":
                condition_met = metric_value < rule.threshold
            elif rule.comparison == "equal_to":
                condition_met = metric_value == rule.threshold
            elif rule.comparison == "not_equal_to":
                condition_met = metric_value != rule.threshold
            
            if condition_met:
                self._generate_alert(rule, metrics, metric_value)
                
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")
    
    def _get_metric_value(self, rule_type: str, metrics: MarketMetrics) -> Optional[Decimal]:
        """Get metric value for rule type."""
        try:
            metric_map = {
                "volatility_1min": metrics.volatility_1min,
                "volatility_5min": metrics.volatility_5min,
                "volatility_15min": metrics.volatility_15min,
                "volatility_warning": metrics.volatility_5min,
                "volatility_critical": metrics.volatility_5min,
                "spread_percentage": metrics.spread_percentage,
                "spread_warning": metrics.spread_percentage,
                "price_change_1min": abs(metrics.price_change_1min),
                "price_change_5min": abs(metrics.price_change_5min),
                "price_change_15min": abs(metrics.price_change_15min),
                "price_change_warning": abs(metrics.price_change_5min),
                "price_change_critical": abs(metrics.price_change_5min),
                "volume_ratio": metrics.volume_avg_ratio,
                "liquidity_score": metrics.liquidity_score
            }
            
            return metric_map.get(rule_type)
            
        except Exception as e:
            logger.error(f"Error getting metric value for {rule_type}: {str(e)}")
            return None
    
    def _check_rate_limit(self, rule: MonitoringRule) -> bool:
        """Check if rule is rate limited."""
        try:
            now = datetime.now()
            
            # Check cooldown period
            if rule.rule_id in self.last_alert_times:
                time_since_last = (now - self.last_alert_times[rule.rule_id]).total_seconds()
                if time_since_last < self.alert_cooldown_seconds:
                    return False
            
            # Check alerts per minute limit
            current_minute = now.replace(second=0, microsecond=0)
            minute_count = self.alert_counts.get(current_minute, 0)
            
            if minute_count >= self.max_alerts_per_minute:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False
    
    def _generate_alert(self, rule: MonitoringRule, metrics: MarketMetrics, current_value: Decimal):
        """Generate market alert."""
        try:
            alert_id = f"alert_{uuid.uuid4().hex[:8]}"
            
            alert = MarketAlert(
                alert_id=alert_id,
                symbol=metrics.symbol,
                alert_type=rule.rule_type,
                severity=rule.severity,
                message=f"{rule.name}: {rule.rule_type} threshold breached for {metrics.symbol}",
                metrics=metrics,
                threshold_breached=rule.rule_type,
                threshold_value=rule.threshold,
                current_value=current_value,
                timestamp=datetime.now(),
                acknowledged=False,
                metadata=rule.metadata.copy()
            )
            
            with self.monitor_lock:
                self.active_alerts[alert_id] = alert
            
            # Update rate limiting
            now = datetime.now()
            current_minute = now.replace(second=0, microsecond=0)
            self.alert_counts[current_minute] = self.alert_counts.get(current_minute, 0) + 1
            self.last_alert_times[rule.rule_id] = now
            
            # Update metrics
            self.metrics["total_alerts"] += 1
            self.metrics["alerts_by_severity"][rule.severity.value] += 1
            
            # Log alert
            self.audit_manager.log_system_event(
                event_type="market_alert_generated",
                event_data={
                    "alert_id": alert_id,
                    "symbol": metrics.symbol,
                    "alert_type": rule.rule_type,
                    "severity": rule.severity.value,
                    "threshold": float(rule.threshold),
                    "current_value": float(current_value)
                },
                severity=rule.severity.value
            )
            
            # Trigger callback if provided
            if rule.callback:
                try:
                    rule.callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {str(e)}")
            
            # Escalate to protocol engine if critical
            if rule.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                self._escalate_to_protocol_engine(alert)
            
            logger.warning(f"Generated {rule.severity.value} alert: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error generating alert: {str(e)}")
    
    def _escalate_to_protocol_engine(self, alert: MarketAlert):
        """Escalate critical alerts to protocol engine."""
        try:
            escalation_data = {
                "alert_id": alert.alert_id,
                "symbol": alert.symbol,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "current_value": float(alert.current_value),
                "threshold_value": float(alert.threshold_value),
                "market_condition": alert.metrics.market_condition.value
            }
            
            # This would integrate with the actual escalation manager
            # For now, just log the escalation
            logger.critical(f"Escalating alert {alert.alert_id} to Protocol Engine: {escalation_data}")
            
        except Exception as e:
            logger.error(f"Error escalating to protocol engine: {str(e)}")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Market monitoring loop started")
        
        while self.running:
            try:
                # Clean up old alert counts
                self._cleanup_alert_counts()
                
                # Update monitoring metrics
                self._update_monitoring_metrics()
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                time.sleep(5)  # Longer sleep on error
        
        logger.info("Market monitoring loop stopped")
    
    def _cleanup_alert_counts(self):
        """Clean up old alert count data."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=5)
            
            keys_to_remove = [
                timestamp for timestamp in self.alert_counts.keys()
                if timestamp < cutoff_time
            ]
            
            for key in keys_to_remove:
                del self.alert_counts[key]
                
        except Exception as e:
            logger.error(f"Error cleaning up alert counts: {str(e)}")
    
    def _update_monitoring_metrics(self):
        """Update monitoring performance metrics."""
        try:
            self.metrics["symbols_monitored"] = len(self.monitored_symbols)
            self.metrics["rules_active"] = len([r for r in self.monitoring_rules.values() if r.enabled])
            self.metrics["last_update"] = datetime.now().isoformat()
            
            # Calculate average processing time
            if self.metrics["processing_times"]:
                avg_processing_time = sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"])
                self.metrics["average_processing_time_ms"] = avg_processing_time * 1000
            
        except Exception as e:
            logger.error(f"Error updating monitoring metrics: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        try:
            return {
                "success": True,
                "running": self.running,
                "monitored_symbols": list(self.monitored_symbols),
                "active_rules": len([r for r in self.monitoring_rules.values() if r.enabled]),
                "total_rules": len(self.monitoring_rules),
                "active_alerts": len(self.active_alerts),
                "alert_history_count": len(self.alert_history),
                "metrics": self.metrics.copy(),
                "current_market_conditions": {
                    symbol: metrics.market_condition.value 
                    for symbol, metrics in self.current_metrics.items()
                },
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

