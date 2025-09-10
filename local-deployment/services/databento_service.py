"""
Databento Market Data Integration Service
Real-time and historical market data for True-Asset-ALLUSE
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

try:
    import databento as db
    DATABENTO_AVAILABLE = True
except ImportError:
    DATABENTO_AVAILABLE = False
    logging.warning("databento library not available. Databento integration disabled.")

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance library not available. Yahoo Finance fallback disabled.")

from config_enhanced import config, DEFAULT_SYMBOLS

logger = logging.getLogger(__name__)

class DatabentoService:
    """Databento service for real-time market data integration"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.cache = {}
        self.last_update = {}
        self.subscription_active = False
        
        if not DATABENTO_AVAILABLE:
            logger.warning("Databento service initialized without databento library")
    
    async def connect(self) -> bool:
        """Connect to Databento API"""
        if not DATABENTO_AVAILABLE or not config.databento_enabled or not config.databento_api_key:
            logger.info("Databento integration disabled or API key not provided")
            return False
        
        try:
            self.client = db.Historical(key=config.databento_api_key)
            
            # Test connection with a simple request
            test_data = self.client.metadata.list_datasets()
            
            self.connected = True
            logger.info("Connected to Databento API successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Databento: {e}")
            self.connected = False
            return False
    
    async def get_real_time_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        if not self.connected:
            return await self._get_fallback_quote(symbol)
        
        try:
            # For demo purposes, we'll use historical data as "real-time"
            # In production, you'd use the live client
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            data = self.client.timeseries.get_range(
                dataset=config.databento_dataset,
                symbols=[symbol],
                schema="trades",
                start=start_date,
                end=end_date,
                limit=1
            )
            
            if not data.empty:
                latest = data.iloc[-1]
                
                quote_data = {
                    "symbol": symbol,
                    "last_price": float(latest.get("price", 0)) / 1e9,  # Databento uses nano precision
                    "volume": int(latest.get("size", 0)),
                    "timestamp": latest.get("ts_event", datetime.now()).isoformat(),
                    "exchange": latest.get("publisher_id", "UNKNOWN"),
                    "data_source": "Databento"
                }
                
                self.cache[symbol] = quote_data
                self.last_update[symbol] = datetime.now()
                
                return quote_data
            
            return await self._get_fallback_quote(symbol)
            
        except Exception as e:
            logger.error(f"Failed to get real-time quote for {symbol}: {e}")
            return await self._get_fallback_quote(symbol)
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical data for a symbol"""
        if not self.connected:
            return await self._get_fallback_historical(symbol, days)
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            data = self.client.timeseries.get_range(
                dataset=config.databento_dataset,
                symbols=[symbol],
                schema="ohlcv-1d",
                start=start_date,
                end=end_date
            )
            
            if not data.empty:
                # Convert Databento data to standard format
                df = pd.DataFrame({
                    "Date": pd.to_datetime(data["ts_event"]),
                    "Open": data["open"] / 1e9,
                    "High": data["high"] / 1e9,
                    "Low": data["low"] / 1e9,
                    "Close": data["close"] / 1e9,
                    "Volume": data["volume"]
                })
                
                return df.set_index("Date")
            
            return await self._get_fallback_historical(symbol, days)
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return await self._get_fallback_historical(symbol, days)
    
    async def get_options_data(self, symbol: str, expiry: str = None) -> List[Dict[str, Any]]:
        """Get options data for a symbol"""
        if not self.connected:
            return await self._get_fallback_options(symbol)
        
        try:
            # Databento options data would require specific dataset
            # For demo, we'll generate realistic options data
            underlying_price = await self.get_real_time_quote(symbol)
            base_price = underlying_price.get("last_price", 100)
            
            options = []
            
            # Generate options around current price
            strikes = [base_price * (1 + i * 0.05) for i in range(-5, 6)]
            
            for strike in strikes:
                for option_type in ["CALL", "PUT"]:
                    # Simple option pricing model for demo
                    intrinsic = max(base_price - strike, 0) if option_type == "CALL" else max(strike - base_price, 0)
                    time_value = abs(base_price - strike) * 0.02  # Simplified time value
                    option_price = intrinsic + time_value
                    
                    # Simple Greeks calculation
                    delta = 0.5 if option_type == "CALL" else -0.5
                    if abs(base_price - strike) > base_price * 0.1:
                        delta *= 0.3  # Out of the money
                    
                    options.append({
                        "symbol": symbol,
                        "strike": round(strike, 2),
                        "option_type": option_type,
                        "expiry": expiry or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                        "price": round(option_price, 2),
                        "delta": round(delta, 3),
                        "gamma": round(abs(delta) * 0.1, 4),
                        "theta": round(-option_price * 0.01, 3),
                        "vega": round(option_price * 0.2, 3),
                        "implied_volatility": round(0.2 + abs(base_price - strike) / base_price, 3),
                        "volume": int(abs(base_price - strike) * 100),
                        "open_interest": int(abs(base_price - strike) * 500),
                        "data_source": "Databento_Calculated"
                    })
            
            return options[:20]  # Limit to 20 options
            
        except Exception as e:
            logger.error(f"Failed to get options data for {symbol}: {e}")
            return await self._get_fallback_options(symbol)
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            now = datetime.now()
            
            # Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
            is_open = (
                now.weekday() < 5 and  # Monday to Friday
                9.5 <= now.hour + now.minute/60 <= 16  # 9:30 AM to 4:00 PM
            )
            
            return {
                "is_open": is_open,
                "status": "OPEN" if is_open else "CLOSED",
                "next_open": "9:30 AM ET" if not is_open else None,
                "next_close": "4:00 PM ET" if is_open else None,
                "timezone": "US/Eastern",
                "data_source": "Databento" if self.connected else "Local_Calculation"
            }
            
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return {
                "is_open": False,
                "status": "UNKNOWN",
                "error": str(e)
            }
    
    async def get_volatility_data(self) -> Dict[str, Any]:
        """Get VIX and volatility data"""
        try:
            vix_data = await self.get_real_time_quote("VIX")
            
            # Calculate volatility metrics
            vix_level = vix_data.get("last_price", 20.0)
            
            if vix_level < 15:
                volatility_regime = "Low"
                market_sentiment = "Complacent"
            elif vix_level < 25:
                volatility_regime = "Normal"
                market_sentiment = "Neutral"
            elif vix_level < 35:
                volatility_regime = "Elevated"
                market_sentiment = "Cautious"
            else:
                volatility_regime = "High"
                market_sentiment = "Fearful"
            
            return {
                "vix_level": vix_level,
                "volatility_regime": volatility_regime,
                "market_sentiment": market_sentiment,
                "escalation_threshold": config.vix_escalation_threshold,
                "protocol_escalation": vix_level > config.vix_escalation_threshold,
                "timestamp": datetime.now().isoformat(),
                "data_source": "Databento" if self.connected else "Fallback"
            }
            
        except Exception as e:
            logger.error(f"Failed to get volatility data: {e}")
            return {
                "vix_level": 20.0,
                "volatility_regime": "Normal",
                "market_sentiment": "Neutral",
                "error": str(e)
            }
    
    async def _get_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback to Yahoo Finance for quotes"""
        if not YFINANCE_AVAILABLE:
            return self._get_mock_quote(symbol)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "last_price": info.get("currentPrice", info.get("regularMarketPrice", 100.0)),
                "bid": info.get("bid", 0),
                "ask": info.get("ask", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "timestamp": datetime.now().isoformat(),
                "data_source": "Yahoo_Finance_Fallback"
            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance fallback failed for {symbol}: {e}")
            return self._get_mock_quote(symbol)
    
    async def _get_fallback_historical(self, symbol: str, days: int) -> pd.DataFrame:
        """Fallback to Yahoo Finance for historical data"""
        if not YFINANCE_AVAILABLE:
            return self._get_mock_historical(symbol, days)
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{days}d")
            
            return data
            
        except Exception as e:
            logger.error(f"Yahoo Finance historical fallback failed for {symbol}: {e}")
            return self._get_mock_historical(symbol, days)
    
    async def _get_fallback_options(self, symbol: str) -> List[Dict[str, Any]]:
        """Fallback options data"""
        return self._get_mock_options(symbol)
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Generate mock quote data"""
        base_prices = {
            "AAPL": 175.50,
            "MSFT": 380.25,
            "GOOGL": 140.80,
            "TSLA": 250.30,
            "SPY": 450.75,
            "QQQ": 375.20,
            "VIX": 18.50
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add small random fluctuation
        import random
        fluctuation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + fluctuation)
        
        return {
            "symbol": symbol,
            "last_price": round(current_price, 2),
            "bid": round(current_price * 0.999, 2),
            "ask": round(current_price * 1.001, 2),
            "volume": random.randint(1000000, 10000000),
            "timestamp": datetime.now().isoformat(),
            "data_source": "Mock_Data"
        }
    
    def _get_mock_historical(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate mock historical data"""
        import random
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_price = self._get_mock_quote(symbol)["last_price"]
        
        prices = []
        current_price = base_price
        
        for _ in range(days):
            change = random.uniform(-0.05, 0.05)
            current_price *= (1 + change)
            prices.append(current_price)
        
        return pd.DataFrame({
            "Open": prices,
            "High": [p * random.uniform(1.0, 1.02) for p in prices],
            "Low": [p * random.uniform(0.98, 1.0) for p in prices],
            "Close": prices,
            "Volume": [random.randint(1000000, 10000000) for _ in prices]
        }, index=dates)
    
    def _get_mock_options(self, symbol: str) -> List[Dict[str, Any]]:
        """Generate mock options data"""
        base_price = self._get_mock_quote(symbol)["last_price"]
        options = []
        
        strikes = [base_price * (1 + i * 0.05) for i in range(-3, 4)]
        
        for strike in strikes:
            for option_type in ["CALL", "PUT"]:
                options.append({
                    "symbol": symbol,
                    "strike": round(strike, 2),
                    "option_type": option_type,
                    "expiry": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "price": round(abs(base_price - strike) * 0.1 + 2.0, 2),
                    "delta": 0.5 if option_type == "CALL" else -0.5,
                    "data_source": "Mock_Data"
                })
        
        return options
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Databento service health"""
        if not DATABENTO_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "databento library not installed",
                "connected": False
            }
        
        if not config.databento_enabled:
            return {
                "status": "disabled",
                "message": "Databento integration disabled in configuration",
                "connected": False
            }
        
        if not config.databento_api_key:
            return {
                "status": "no_api_key",
                "message": "Databento API key not provided",
                "connected": False
            }
        
        if not self.connected:
            connected = await self.connect()
            if not connected:
                return {
                    "status": "connection_failed",
                    "message": "Failed to connect to Databento API",
                    "connected": False
                }
        
        try:
            # Test with a simple quote request
            test_quote = await self.get_real_time_quote("AAPL")
            
            return {
                "status": "healthy",
                "message": "Connected to Databento API",
                "connected": True,
                "dataset": config.databento_dataset,
                "last_test_symbol": "AAPL",
                "last_test_price": test_quote.get("last_price"),
                "fallback_available": YFINANCE_AVAILABLE
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Databento API error: {e}",
                "connected": False
            }

# Global service instance
databento_service = DatabentoService()

