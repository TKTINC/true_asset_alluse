"""
Market Data Manager

This module implements the central market data management system that
orchestrates real-time market data feeds, validation, caching, and
distribution across the True-Asset-ALLUSE system.
"""

from typing import Dict, Any, Optional, List, Callable, Set
from decimal import Decimal, getcontext
from datetime import datetime, date, time, timedelta
from enum import Enum
import logging
import asyncio
import threading
from dataclasses import dataclass, asdict
import uuid
import json
import time as time_module

from src.ws1_rules_engine.audit import AuditTrailManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class MarketDataType(Enum):
    """Types of market data."""
    QUOTE = "quote"
    TRADE = "trade"
    OPTION_CHAIN = "option_chain"
    GREEKS = "greeks"
    VOLUME = "volume"
    OPEN_INTEREST = "open_interest"
    IMPLIED_VOLATILITY = "implied_volatility"
    HISTORICAL = "historical"


class DataProvider(Enum):
    """Market data providers."""
    INTERACTIVE_BROKERS = "interactive_brokers"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"
    POLYGON = "polygon"
    QUANDL = "quandl"


class MarketState(Enum):
    """Market states."""
    PRE_MARKET = "pre_market"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    AFTER_HOURS = "after_hours"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


@dataclass
class MarketDataPoint:
    """Individual market data point."""
    symbol: str
    data_type: MarketDataType
    timestamp: datetime
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    last: Optional[Decimal]
    volume: Optional[int]
    open_interest: Optional[int]
    implied_volatility: Optional[Decimal]
    delta: Optional[Decimal]
    gamma: Optional[Decimal]
    theta: Optional[Decimal]
    vega: Optional[Decimal]
    rho: Optional[Decimal]
    provider: DataProvider
    quality_score: Decimal
    metadata: Dict[str, Any]


@dataclass
class OptionChainData:
    """Option chain data structure."""
    underlying_symbol: str
    expiration_date: date
    strike_prices: List[Decimal]
    calls: Dict[Decimal, MarketDataPoint]  # strike -> call data
    puts: Dict[Decimal, MarketDataPoint]   # strike -> put data
    timestamp: datetime
    provider: DataProvider


@dataclass
class MarketDataSubscription:
    """Market data subscription."""
    subscription_id: str
    symbols: Set[str]
    data_types: Set[MarketDataType]
    callback: Callable[[MarketDataPoint], None]
    active: bool
    created_timestamp: datetime
    last_update: Optional[datetime]


class MarketDataManager:
    """
    Central market data management system.
    
    Orchestrates real-time market data feeds from multiple providers,
    validates data quality, manages caching and distribution, and
    provides unified market data access across the system.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize market data manager.
        
        Args:
            audit_manager: Audit trail manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.config = config or {}
        
        # Configuration parameters
        self.primary_provider = DataProvider(self.config.get("primary_provider", "interactive_brokers"))
        self.fallback_providers = [DataProvider(p) for p in self.config.get("fallback_providers", ["yahoo_finance", "alpha_vantage"])]
        self.data_quality_threshold = Decimal(str(self.config.get("data_quality_threshold", 0.8)))
        self.cache_duration_seconds = self.config.get("cache_duration_seconds", 60)
        self.max_subscriptions = self.config.get("max_subscriptions", 1000)
        
        # Market data storage
        self.current_data = {}  # symbol -> MarketDataPoint
        self.option_chains = {}  # underlying_symbol -> OptionChainData
        self.subscriptions = {}  # subscription_id -> MarketDataSubscription
        self.provider_connections = {}  # provider -> connection_object
        
        # Market state tracking
        self.current_market_state = MarketState.MARKET_CLOSE
        self.market_hours = self._initialize_market_hours()
        
        # Threading and async support
        self.data_lock = threading.RLock()
        self.update_thread = None
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "data_points_received": 0,
            "data_points_validated": 0,
            "data_points_cached": 0,
            "subscriptions_active": 0,
            "provider_failures": {},
            "last_update": None
        }
        
        logger.info("Market Data Manager initialized")
    
    def start(self) -> Dict[str, Any]:
        """Start market data manager."""
        try:
            if self.running:
                return {"success": False, "error": "Market data manager already running"}
            
            self.running = True
            
            # Initialize provider connections
            self._initialize_providers()
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Update market state
            self._update_market_state()
            
            logger.info("Market Data Manager started")
            
            return {
                "success": True,
                "primary_provider": self.primary_provider.value,
                "fallback_providers": [p.value for p in self.fallback_providers],
                "market_state": self.current_market_state.value,
                "start_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting market data manager: {str(e)}", exc_info=True)
            self.running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop market data manager."""
        try:
            if not self.running:
                return {"success": False, "error": "Market data manager not running"}
            
            self.running = False
            
            # Close provider connections
            self._close_provider_connections()
            
            # Wait for update thread to finish
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=5)
            
            logger.info("Market Data Manager stopped")
            
            return {
                "success": True,
                "stop_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping market data manager: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def subscribe_to_data(self, 
                         symbols: List[str],
                         data_types: List[MarketDataType],
                         callback: Callable[[MarketDataPoint], None]) -> Dict[str, Any]:
        """
        Subscribe to market data for specific symbols and data types.
        
        Args:
            symbols: List of symbols to subscribe to
            data_types: List of data types to receive
            callback: Callback function for data updates
            
        Returns:
            Subscription result
        """
        try:
            if len(self.subscriptions) >= self.max_subscriptions:
                return {
                    "success": False,
                    "error": f"Maximum subscriptions ({self.max_subscriptions}) reached"
                }
            
            subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
            
            subscription = MarketDataSubscription(
                subscription_id=subscription_id,
                symbols=set(symbols),
                data_types=set(data_types),
                callback=callback,
                active=True,
                created_timestamp=datetime.now(),
                last_update=None
            )
            
            with self.data_lock:
                self.subscriptions[subscription_id] = subscription
                self.metrics["subscriptions_active"] = len([s for s in self.subscriptions.values() if s.active])
            
            # Request data from providers for new symbols
            self._request_data_from_providers(symbols, data_types)
            
            logger.info(f"Created market data subscription {subscription_id} for {len(symbols)} symbols")
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "symbols": symbols,
                "data_types": [dt.value for dt in data_types],
                "created_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating market data subscription: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def unsubscribe_from_data(self, subscription_id: str) -> Dict[str, Any]:
        """Unsubscribe from market data."""
        try:
            with self.data_lock:
                if subscription_id not in self.subscriptions:
                    return {
                        "success": False,
                        "error": f"Subscription {subscription_id} not found"
                    }
                
                subscription = self.subscriptions[subscription_id]
                subscription.active = False
                
                self.metrics["subscriptions_active"] = len([s for s in self.subscriptions.values() if s.active])
            
            logger.info(f"Deactivated market data subscription {subscription_id}")
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "unsubscribed_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error unsubscribing from market data: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "subscription_id": subscription_id
            }
    
    def get_current_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current market data for symbol."""
        try:
            with self.data_lock:
                return self.current_data.get(symbol)
                
        except Exception as e:
            logger.error(f"Error getting current data for {symbol}: {str(e)}")
            return None
    
    def get_option_chain(self, underlying_symbol: str, expiration_date: Optional[date] = None) -> Optional[OptionChainData]:
        """Get option chain data for underlying symbol."""
        try:
            with self.data_lock:
                chain_key = f"{underlying_symbol}_{expiration_date.isoformat() if expiration_date else 'nearest'}"
                return self.option_chains.get(chain_key)
                
        except Exception as e:
            logger.error(f"Error getting option chain for {underlying_symbol}: {str(e)}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """Get current quotes for multiple symbols."""
        try:
            with self.data_lock:
                return {symbol: self.current_data[symbol] for symbol in symbols if symbol in self.current_data}
                
        except Exception as e:
            logger.error(f"Error getting multiple quotes: {str(e)}")
            return {}
    
    def request_historical_data(self, 
                               symbol: str,
                               start_date: date,
                               end_date: date,
                               interval: str = "1min") -> Dict[str, Any]:
        """Request historical market data."""
        try:
            # This would integrate with provider APIs for historical data
            # For now, return a placeholder structure
            
            historical_data = {
                "symbol": symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": interval,
                "data_points": [],  # Would contain actual historical data
                "provider": self.primary_provider.value,
                "request_timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "historical_data": historical_data
            }
            
        except Exception as e:
            logger.error(f"Error requesting historical data for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def _initialize_providers(self):
        """Initialize connections to market data providers."""
        try:
            # Initialize primary provider
            self._initialize_provider(self.primary_provider)
            
            # Initialize fallback providers
            for provider in self.fallback_providers:
                self._initialize_provider(provider)
                
        except Exception as e:
            logger.error(f"Error initializing providers: {str(e)}")
    
    def _initialize_provider(self, provider: DataProvider):
        """Initialize connection to specific provider."""
        try:
            if provider == DataProvider.INTERACTIVE_BROKERS:
                # Would initialize IB TWS API connection
                connection = {"type": "ib_tws", "status": "connected", "last_heartbeat": datetime.now()}
                
            elif provider == DataProvider.YAHOO_FINANCE:
                # Would initialize Yahoo Finance API
                connection = {"type": "yahoo", "status": "connected", "last_heartbeat": datetime.now()}
                
            elif provider == DataProvider.ALPHA_VANTAGE:
                # Would initialize Alpha Vantage API
                connection = {"type": "alpha_vantage", "status": "connected", "last_heartbeat": datetime.now()}
                
            else:
                # Generic provider initialization
                connection = {"type": "generic", "status": "connected", "last_heartbeat": datetime.now()}
            
            self.provider_connections[provider] = connection
            logger.info(f"Initialized connection to {provider.value}")
            
        except Exception as e:
            logger.error(f"Error initializing provider {provider.value}: {str(e)}")
            self.metrics["provider_failures"][provider.value] = self.metrics["provider_failures"].get(provider.value, 0) + 1
    
    def _close_provider_connections(self):
        """Close all provider connections."""
        try:
            for provider, connection in self.provider_connections.items():
                try:
                    # Would close actual provider connections
                    connection["status"] = "disconnected"
                    logger.info(f"Closed connection to {provider.value}")
                except Exception as e:
                    logger.error(f"Error closing connection to {provider.value}: {str(e)}")
            
            self.provider_connections.clear()
            
        except Exception as e:
            logger.error(f"Error closing provider connections: {str(e)}")
    
    def _update_loop(self):
        """Main update loop for market data."""
        logger.info("Market data update loop started")
        
        while self.running:
            try:
                # Update market state
                self._update_market_state()
                
                # Process data from providers
                self._process_provider_data()
                
                # Distribute data to subscribers
                self._distribute_data()
                
                # Update metrics
                self._update_metrics()
                
                # Sleep for update interval
                time_module.sleep(1)  # 1 second update interval
                
            except Exception as e:
                logger.error(f"Error in market data update loop: {str(e)}", exc_info=True)
                time_module.sleep(5)  # Longer sleep on error
        
        logger.info("Market data update loop stopped")
    
    def _update_market_state(self):
        """Update current market state."""
        try:
            now = datetime.now()
            current_time = now.time()
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            
            # Weekend check
            if current_weekday >= 5:  # Saturday or Sunday
                self.current_market_state = MarketState.WEEKEND
                return
            
            # Market hours check (simplified - would use actual market calendar)
            market_open = time(9, 30)  # 9:30 AM
            market_close = time(16, 0)  # 4:00 PM
            pre_market_start = time(4, 0)  # 4:00 AM
            after_hours_end = time(20, 0)  # 8:00 PM
            
            if pre_market_start <= current_time < market_open:
                self.current_market_state = MarketState.PRE_MARKET
            elif market_open <= current_time < market_close:
                self.current_market_state = MarketState.MARKET_OPEN
            elif market_close <= current_time < after_hours_end:
                self.current_market_state = MarketState.AFTER_HOURS
            else:
                self.current_market_state = MarketState.MARKET_CLOSE
                
        except Exception as e:
            logger.error(f"Error updating market state: {str(e)}")
    
    def _process_provider_data(self):
        """Process incoming data from providers."""
        try:
            # This would process real data from provider APIs
            # For now, simulate some data processing
            
            if self.current_market_state == MarketState.MARKET_OPEN:
                # Simulate processing market data during market hours
                self.metrics["data_points_received"] += 10
                self.metrics["data_points_validated"] += 8
                self.metrics["data_points_cached"] += 8
                
        except Exception as e:
            logger.error(f"Error processing provider data: {str(e)}")
    
    def _distribute_data(self):
        """Distribute data to active subscribers."""
        try:
            with self.data_lock:
                active_subscriptions = [s for s in self.subscriptions.values() if s.active]
            
            # Would distribute actual data to subscribers
            # For now, just update subscription timestamps
            for subscription in active_subscriptions:
                subscription.last_update = datetime.now()
                
        except Exception as e:
            logger.error(f"Error distributing data: {str(e)}")
    
    def _update_metrics(self):
        """Update performance metrics."""
        try:
            self.metrics["last_update"] = datetime.now().isoformat()
            self.metrics["subscriptions_active"] = len([s for s in self.subscriptions.values() if s.active])
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    def _request_data_from_providers(self, symbols: List[str], data_types: List[MarketDataType]):
        """Request data from providers for specific symbols and types."""
        try:
            # Would make actual requests to provider APIs
            logger.info(f"Requesting data for {len(symbols)} symbols from providers")
            
        except Exception as e:
            logger.error(f"Error requesting data from providers: {str(e)}")
    
    def _initialize_market_hours(self) -> Dict[str, Any]:
        """Initialize market hours configuration."""
        return {
            "regular_hours": {
                "open": time(9, 30),
                "close": time(16, 0)
            },
            "pre_market": {
                "start": time(4, 0),
                "end": time(9, 30)
            },
            "after_hours": {
                "start": time(16, 0),
                "end": time(20, 0)
            },
            "timezone": "US/Eastern"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get market data system status."""
        try:
            provider_status = {}
            for provider, connection in self.provider_connections.items():
                provider_status[provider.value] = {
                    "status": connection.get("status", "unknown"),
                    "last_heartbeat": connection.get("last_heartbeat", "never"),
                    "failures": self.metrics["provider_failures"].get(provider.value, 0)
                }
            
            return {
                "running": self.running,
                "market_state": self.current_market_state.value,
                "primary_provider": self.primary_provider.value,
                "provider_status": provider_status,
                "metrics": self.metrics.copy(),
                "subscriptions": {
                    "total": len(self.subscriptions),
                    "active": len([s for s in self.subscriptions.values() if s.active])
                },
                "data_cache": {
                    "symbols_cached": len(self.current_data),
                    "option_chains_cached": len(self.option_chains)
                },
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }
    
    def validate_data_quality(self, data_point: MarketDataPoint) -> bool:
        """Validate market data quality."""
        try:
            # Basic validation checks
            if data_point.quality_score < self.data_quality_threshold:
                return False
            
            # Price validation
            if data_point.bid and data_point.ask:
                if data_point.bid >= data_point.ask:
                    return False
                
                # Check for reasonable spread
                spread_pct = (data_point.ask - data_point.bid) / data_point.bid
                if spread_pct > Decimal("0.10"):  # 10% spread threshold
                    return False
            
            # Timestamp validation
            now = datetime.now()
            if (now - data_point.timestamp).total_seconds() > 300:  # 5 minutes old
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating data quality: {str(e)}")
            return False

