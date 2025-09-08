"""
Databento Market Data Provider

This module implements the Databento market data provider for the True-Asset-ALLUSE system.
Databento provides institutional-grade market data with high-frequency, low-latency feeds.
"""

from typing import Dict, Any, Optional, List, Callable
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import json
import websockets
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class DatabentoDataset(Enum):
    """Databento dataset types."""
    XNAS_ITCH = "XNAS.ITCH"  # NASDAQ TotalView-ITCH
    XNYS_PILLAR = "XNYS.PILLAR"  # NYSE Pillar
    OPRA_PILLAR = "OPRA.PILLAR"  # Options data
    DBEQ_BASIC = "DBEQ.BASIC"  # Databento Equities Basic
    IFEU_IMPACT = "IFEU.IMPACT"  # ICE Futures Europe


class DatabentoSchema(Enum):
    """Databento schema types."""
    MBO = "mbo"  # Market by Order
    MBP_1 = "mbp-1"  # Market by Price (L1)
    MBP_10 = "mbp-10"  # Market by Price (L2)
    TBBO = "tbbo"  # Top of Book
    TRADES = "trades"  # Trade messages
    OHLCV_1S = "ohlcv-1s"  # OHLCV 1-second bars
    OHLCV_1M = "ohlcv-1m"  # OHLCV 1-minute bars


@dataclass
class DatabentoConfig:
    """Databento configuration."""
    api_key: str
    dataset: str = "XNAS.ITCH"
    schema: str = "tbbo"
    symbols: List[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    live_gateway: str = "bo1"
    historical_gateway: str = "https://hist.databento.com"
    live_gateway_url: str = "wss://live.databento.com/v0/live"


class DatabentoProvider:
    """
    Databento market data provider implementation.
    
    Provides real-time and historical market data from Databento's
    institutional-grade data feeds with microsecond timestamps.
    """
    
    def __init__(self, config: DatabentoConfig):
        """Initialize Databento provider."""
        self.config = config
        self.session = None
        self.websocket = None
        self.is_connected = False
        self.subscriptions = set()
        self.callbacks = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Data quality metrics
        self.message_count = 0
        self.last_heartbeat = None
        self.latency_samples = []
        
        logger.info("Databento provider initialized")
    
    async def connect(self) -> bool:
        """
        Connect to Databento live data feed.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Create HTTP session for API calls
            self.session = aiohttp.ClientSession()
            
            # Connect to live WebSocket feed
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            self.websocket = await websockets.connect(
                self.config.live_gateway_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            
            # Authenticate
            auth_message = {
                "action": "auth",
                "key": self.config.api_key
            }
            await self.websocket.send(json.dumps(auth_message))
            
            # Wait for authentication response
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("success"):
                self.is_connected = True
                self.reconnect_attempts = 0
                logger.info("Successfully connected to Databento live feed")
                
                # Start message handler
                asyncio.create_task(self._handle_messages())
                
                return True
            else:
                logger.error(f"Databento authentication failed: {auth_response}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Databento: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Databento."""
        try:
            self.is_connected = False
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            if self.session:
                await self.session.close()
                self.session = None
            
            logger.info("Disconnected from Databento")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Databento: {e}")
    
    async def subscribe_symbols(self, symbols: List[str], schema: str = "tbbo") -> bool:
        """
        Subscribe to real-time data for symbols.
        
        Args:
            symbols: List of symbols to subscribe to
            schema: Data schema type
            
        Returns:
            bool: True if subscription successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to Databento")
                return False
            
            subscribe_message = {
                "action": "subscribe",
                "dataset": self.config.dataset,
                "schema": schema,
                "symbols": symbols
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            
            # Add to subscriptions
            for symbol in symbols:
                self.subscriptions.add(f"{symbol}:{schema}")
            
            logger.info(f"Subscribed to {len(symbols)} symbols with schema {schema}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to symbols: {e}")
            return False
    
    async def unsubscribe_symbols(self, symbols: List[str], schema: str = "tbbo") -> bool:
        """
        Unsubscribe from symbols.
        
        Args:
            symbols: List of symbols to unsubscribe from
            schema: Data schema type
            
        Returns:
            bool: True if unsubscription successful
        """
        try:
            if not self.is_connected:
                return False
            
            unsubscribe_message = {
                "action": "unsubscribe",
                "dataset": self.config.dataset,
                "schema": schema,
                "symbols": symbols
            }
            
            await self.websocket.send(json.dumps(unsubscribe_message))
            
            # Remove from subscriptions
            for symbol in symbols:
                self.subscriptions.discard(f"{symbol}:{schema}")
            
            logger.info(f"Unsubscribed from {len(symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from symbols: {e}")
            return False
    
    def register_callback(self, data_type: str, callback: Callable):
        """Register callback for data type."""
        if data_type not in self.callbacks:
            self.callbacks[data_type] = []
        self.callbacks[data_type].append(callback)
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode Databento message: {e}")
                except Exception as e:
                    logger.error(f"Error processing Databento message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Databento WebSocket connection closed")
            self.is_connected = False
            await self._attempt_reconnect()
        except Exception as e:
            logger.error(f"Error in Databento message handler: {e}")
            self.is_connected = False
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming market data message."""
        try:
            message_type = data.get("schema", "unknown")
            self.message_count += 1
            
            # Update latency metrics
            if "ts_recv" in data:
                receive_time = datetime.utcnow().timestamp() * 1_000_000_000  # nanoseconds
                latency = receive_time - data["ts_recv"]
                self.latency_samples.append(latency)
                
                # Keep only last 1000 samples
                if len(self.latency_samples) > 1000:
                    self.latency_samples = self.latency_samples[-1000:]
            
            # Route message to appropriate handlers
            if message_type == "tbbo":
                await self._handle_quote_message(data)
            elif message_type == "trades":
                await self._handle_trade_message(data)
            elif message_type in ["ohlcv-1s", "ohlcv-1m"]:
                await self._handle_bar_message(data)
            elif message_type == "status":
                await self._handle_status_message(data)
            
        except Exception as e:
            logger.error(f"Error processing Databento message: {e}")
    
    async def _handle_quote_message(self, data: Dict[str, Any]):
        """Handle quote/TBBO message."""
        try:
            quote_data = {
                "symbol": data.get("symbol", ""),
                "bid_price": Decimal(str(data.get("bid_px", 0))) / 1_000_000_000,  # Convert from fixed-point
                "ask_price": Decimal(str(data.get("ask_px", 0))) / 1_000_000_000,
                "bid_size": data.get("bid_sz", 0),
                "ask_size": data.get("ask_sz", 0),
                "timestamp": datetime.fromtimestamp(data.get("ts_recv", 0) / 1_000_000_000),
                "provider": "databento"
            }
            
            # Call registered callbacks
            if "quote" in self.callbacks:
                for callback in self.callbacks["quote"]:
                    await callback(quote_data)
                    
        except Exception as e:
            logger.error(f"Error handling Databento quote: {e}")
    
    async def _handle_trade_message(self, data: Dict[str, Any]):
        """Handle trade message."""
        try:
            trade_data = {
                "symbol": data.get("symbol", ""),
                "price": Decimal(str(data.get("px", 0))) / 1_000_000_000,
                "size": data.get("sz", 0),
                "timestamp": datetime.fromtimestamp(data.get("ts_recv", 0) / 1_000_000_000),
                "side": data.get("side", ""),
                "provider": "databento"
            }
            
            # Call registered callbacks
            if "trade" in self.callbacks:
                for callback in self.callbacks["trade"]:
                    await callback(trade_data)
                    
        except Exception as e:
            logger.error(f"Error handling Databento trade: {e}")
    
    async def _handle_bar_message(self, data: Dict[str, Any]):
        """Handle OHLCV bar message."""
        try:
            bar_data = {
                "symbol": data.get("symbol", ""),
                "open": Decimal(str(data.get("open", 0))) / 1_000_000_000,
                "high": Decimal(str(data.get("high", 0))) / 1_000_000_000,
                "low": Decimal(str(data.get("low", 0))) / 1_000_000_000,
                "close": Decimal(str(data.get("close", 0))) / 1_000_000_000,
                "volume": data.get("volume", 0),
                "timestamp": datetime.fromtimestamp(data.get("ts_recv", 0) / 1_000_000_000),
                "provider": "databento"
            }
            
            # Call registered callbacks
            if "bar" in self.callbacks:
                for callback in self.callbacks["bar"]:
                    await callback(bar_data)
                    
        except Exception as e:
            logger.error(f"Error handling Databento bar: {e}")
    
    async def _handle_status_message(self, data: Dict[str, Any]):
        """Handle status/heartbeat message."""
        self.last_heartbeat = datetime.utcnow()
        logger.debug(f"Databento heartbeat: {data}")
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to Databento."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached for Databento")
            return
        
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 60)  # Exponential backoff
        
        logger.info(f"Attempting Databento reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts} in {wait_time}s")
        await asyncio.sleep(wait_time)
        
        if await self.connect():
            # Re-subscribe to previous subscriptions
            symbols_by_schema = {}
            for subscription in self.subscriptions:
                symbol, schema = subscription.split(":")
                if schema not in symbols_by_schema:
                    symbols_by_schema[schema] = []
                symbols_by_schema[schema].append(symbol)
            
            for schema, symbols in symbols_by_schema.items():
                await self.subscribe_symbols(symbols, schema)
    
    async def get_historical_data(self, symbols: List[str], start_date: str, end_date: str, schema: str = "trades") -> List[Dict[str, Any]]:
        """
        Get historical market data.
        
        Args:
            symbols: List of symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            schema: Data schema type
            
        Returns:
            List of historical data records
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.config.historical_gateway}/v0/timeseries.get_range"
            
            params = {
                "dataset": self.config.dataset,
                "schema": schema,
                "symbols": ",".join(symbols),
                "start": start_date,
                "end": end_date,
                "encoding": "json"
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data)} historical records from Databento")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Databento historical data request failed: {response.status} - {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting Databento historical data: {e}")
            return []
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        avg_latency = 0
        if self.latency_samples:
            avg_latency = sum(self.latency_samples) / len(self.latency_samples) / 1_000_000  # Convert to milliseconds
        
        return {
            "provider": "databento",
            "connected": self.is_connected,
            "subscriptions": len(self.subscriptions),
            "messages_received": self.message_count,
            "average_latency_ms": round(avg_latency, 3),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "reconnect_attempts": self.reconnect_attempts
        }

