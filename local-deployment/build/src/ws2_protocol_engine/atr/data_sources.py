"""
ATR Data Sources

This module implements multiple data source providers for ATR calculation
with fallback mechanisms to ensure robust data availability.

Supported Data Sources:
- Yahoo Finance (free, reliable)
- Alpha Vantage (API key required)
- IEX Cloud (API key required)
- Interactive Brokers (via TWS API)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import requests
import logging
import time
from decimal import Decimal
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


class ATRDataSource(ABC):
    """Abstract base class for ATR data sources."""
    
    def __init__(self, name: str, priority: int = 1):
        """
        Initialize data source.
        
        Args:
            name: Data source name
            priority: Priority level (lower = higher priority)
        """
        self.name = name
        self.priority = priority
        self.last_request_time = None
        self.rate_limit_delay = 1.0  # seconds between requests
        self.max_retries = 3
        self.timeout = 30  # seconds
    
    @abstractmethod
    def get_price_data(self, 
                      symbol: str, 
                      period_days: int = 30,
                      end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get price data for ATR calculation.
        
        Args:
            symbol: Trading symbol
            period_days: Number of days of data to retrieve
            end_date: End date for data (default: today)
            
        Returns:
            Price data result
        """
        pass
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        
        self.last_request_time = time.time()
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Validate trading symbol format."""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic symbol validation
        symbol = symbol.strip().upper()
        return len(symbol) >= 1 and symbol.isalnum()
    
    def is_available(self) -> bool:
        """Check if data source is available."""
        try:
            # Simple connectivity test
            test_result = self.get_price_data("SPY", period_days=5)
            return test_result.get("success", False)
        except Exception:
            return False


class YahooFinanceSource(ATRDataSource):
    """Yahoo Finance data source implementation."""
    
    def __init__(self):
        super().__init__("Yahoo Finance", priority=1)
        self.rate_limit_delay = 0.5  # Yahoo is more lenient
    
    def get_price_data(self, 
                      symbol: str, 
                      period_days: int = 30,
                      end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get price data from Yahoo Finance."""
        try:
            self._rate_limit()
            
            if not self._validate_symbol(symbol):
                return {
                    "success": False,
                    "error": f"Invalid symbol: {symbol}",
                    "source": self.name
                }
            
            symbol = symbol.upper()
            
            # Calculate date range
            if end_date is None:
                end_date = date.today()
            
            start_date = end_date - timedelta(days=period_days + 10)  # Extra buffer
            
            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval="1d"
            )
            
            if hist_data.empty:
                return {
                    "success": False,
                    "error": f"No data available for {symbol}",
                    "source": self.name
                }
            
            # Convert to required format
            price_data = []
            for index, row in hist_data.iterrows():
                price_data.append({
                    "date": index.strftime("%Y-%m-%d"),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']) if pd.notna(row['Volume']) else 0
                })
            
            # Sort by date to ensure chronological order
            price_data.sort(key=lambda x: x["date"])
            
            return {
                "success": True,
                "data": price_data,
                "symbol": symbol,
                "source": self.name,
                "period_days": period_days,
                "data_points": len(price_data),
                "start_date": price_data[0]["date"] if price_data else None,
                "end_date": price_data[-1]["date"] if price_data else None,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": self.name,
                "symbol": symbol
            }


class AlphaVantageSource(ATRDataSource):
    """Alpha Vantage data source implementation."""
    
    def __init__(self, api_key: str):
        super().__init__("Alpha Vantage", priority=2)
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.0  # Alpha Vantage free tier: 5 calls per minute
    
    def get_price_data(self, 
                      symbol: str, 
                      period_days: int = 30,
                      end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get price data from Alpha Vantage."""
        try:
            self._rate_limit()
            
            if not self._validate_symbol(symbol):
                return {
                    "success": False,
                    "error": f"Invalid symbol: {symbol}",
                    "source": self.name
                }
            
            symbol = symbol.upper()
            
            # Alpha Vantage parameters
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "compact" if period_days <= 100 else "full"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                return {
                    "success": False,
                    "error": data["Error Message"],
                    "source": self.name
                }
            
            if "Note" in data:
                return {
                    "success": False,
                    "error": "API rate limit exceeded",
                    "source": self.name
                }
            
            # Extract time series data
            time_series_key = "Time Series (Daily)"
            if time_series_key not in data:
                return {
                    "success": False,
                    "error": "Invalid response format",
                    "source": self.name
                }
            
            time_series = data[time_series_key]
            
            # Convert to required format
            price_data = []
            for date_str, daily_data in time_series.items():
                try:
                    price_data.append({
                        "date": date_str,
                        "high": float(daily_data["2. high"]),
                        "low": float(daily_data["3. low"]),
                        "close": float(daily_data["4. close"]),
                        "volume": int(daily_data["5. volume"])
                    })
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid data point for {date_str}: {e}")
                    continue
            
            # Sort by date and limit to requested period
            price_data.sort(key=lambda x: x["date"])
            
            if end_date:
                end_date_str = end_date.strftime("%Y-%m-%d")
                price_data = [d for d in price_data if d["date"] <= end_date_str]
            
            if period_days and len(price_data) > period_days:
                price_data = price_data[-period_days:]
            
            return {
                "success": True,
                "data": price_data,
                "symbol": symbol,
                "source": self.name,
                "period_days": period_days,
                "data_points": len(price_data),
                "start_date": price_data[0]["date"] if price_data else None,
                "end_date": price_data[-1]["date"] if price_data else None,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Alpha Vantage request error for {symbol}: {str(e)}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "source": self.name
            }
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": self.name
            }


class IEXCloudSource(ATRDataSource):
    """IEX Cloud data source implementation."""
    
    def __init__(self, api_key: str, sandbox: bool = False):
        super().__init__("IEX Cloud", priority=3)
        self.api_key = api_key
        self.sandbox = sandbox
        self.base_url = "https://sandbox-api.iexapis.com/stable" if sandbox else "https://cloud.iexapis.com/stable"
        self.rate_limit_delay = 0.1  # IEX Cloud is fast
    
    def get_price_data(self, 
                      symbol: str, 
                      period_days: int = 30,
                      end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get price data from IEX Cloud."""
        try:
            self._rate_limit()
            
            if not self._validate_symbol(symbol):
                return {
                    "success": False,
                    "error": f"Invalid symbol: {symbol}",
                    "source": self.name
                }
            
            symbol = symbol.upper()
            
            # Determine range parameter
            if period_days <= 5:
                range_param = "5d"
            elif period_days <= 30:
                range_param = "1m"
            elif period_days <= 90:
                range_param = "3m"
            elif period_days <= 180:
                range_param = "6m"
            elif period_days <= 365:
                range_param = "1y"
            else:
                range_param = "2y"
            
            # IEX Cloud API endpoint
            url = f"{self.base_url}/stock/{symbol}/chart/{range_param}"
            
            params = {
                "token": self.api_key,
                "includeToday": "true"
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or not isinstance(data, list):
                return {
                    "success": False,
                    "error": "No data available",
                    "source": self.name
                }
            
            # Convert to required format
            price_data = []
            for daily_data in data:
                try:
                    # Skip days with null values
                    if not all(daily_data.get(k) is not None for k in ['high', 'low', 'close']):
                        continue
                    
                    price_data.append({
                        "date": daily_data["date"],
                        "high": float(daily_data["high"]),
                        "low": float(daily_data["low"]),
                        "close": float(daily_data["close"]),
                        "volume": int(daily_data.get("volume", 0))
                    })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid data point: {e}")
                    continue
            
            # Sort by date and apply filters
            price_data.sort(key=lambda x: x["date"])
            
            if end_date:
                end_date_str = end_date.strftime("%Y-%m-%d")
                price_data = [d for d in price_data if d["date"] <= end_date_str]
            
            if period_days and len(price_data) > period_days:
                price_data = price_data[-period_days:]
            
            return {
                "success": True,
                "data": price_data,
                "symbol": symbol,
                "source": self.name,
                "period_days": period_days,
                "data_points": len(price_data),
                "start_date": price_data[0]["date"] if price_data else None,
                "end_date": price_data[-1]["date"] if price_data else None,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"IEX Cloud request error for {symbol}: {str(e)}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "source": self.name
            }
        except Exception as e:
            logger.error(f"IEX Cloud error for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "source": self.name
            }


class InteractiveBrokersSource(ATRDataSource):
    """Interactive Brokers data source implementation (placeholder)."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497):
        super().__init__("Interactive Brokers", priority=0)  # Highest priority
        self.host = host
        self.port = port
        self.rate_limit_delay = 0.1
    
    def get_price_data(self, 
                      symbol: str, 
                      period_days: int = 30,
                      end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get price data from Interactive Brokers TWS API."""
        # This is a placeholder implementation
        # In production, this would use the IB API client
        
        logger.info(f"IB data source called for {symbol} (placeholder implementation)")
        
        return {
            "success": False,
            "error": "Interactive Brokers integration not yet implemented",
            "source": self.name,
            "symbol": symbol,
            "note": "This will be implemented in WS4: Market Data & Execution Engine"
        }


class DataSourceManager:
    """Manager for multiple ATR data sources with fallback logic."""
    
    def __init__(self):
        """Initialize data source manager."""
        self.sources = []
        self.fallback_enabled = True
        self.cache_duration = 300  # 5 minutes cache
        self.cache = {}
    
    def add_source(self, source: ATRDataSource):
        """Add a data source."""
        self.sources.append(source)
        # Sort by priority (lower number = higher priority)
        self.sources.sort(key=lambda x: x.priority)
        logger.info(f"Added data source: {source.name} (priority: {source.priority})")
    
    def get_price_data_with_fallback(self, 
                                   symbol: str, 
                                   period_days: int = 30,
                                   end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get price data with automatic fallback to alternative sources.
        
        Args:
            symbol: Trading symbol
            period_days: Number of days of data
            end_date: End date for data
            
        Returns:
            Price data result with fallback information
        """
        if not self.sources:
            return {
                "success": False,
                "error": "No data sources configured",
                "attempted_sources": []
            }
        
        attempted_sources = []
        last_error = None
        
        for source in self.sources:
            try:
                logger.info(f"Attempting to get data for {symbol} from {source.name}")
                
                result = source.get_price_data(symbol, period_days, end_date)
                attempted_sources.append({
                    "source": source.name,
                    "success": result.get("success", False),
                    "error": result.get("error")
                })
                
                if result.get("success"):
                    logger.info(f"Successfully retrieved data for {symbol} from {source.name}")
                    result["attempted_sources"] = attempted_sources
                    result["fallback_used"] = len(attempted_sources) > 1
                    return result
                else:
                    last_error = result.get("error", "Unknown error")
                    logger.warning(f"Failed to get data from {source.name}: {last_error}")
                    
                    if not self.fallback_enabled:
                        break
                        
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                attempted_sources.append({
                    "source": source.name,
                    "success": False,
                    "error": error_msg
                })
                logger.error(f"Exception with {source.name}: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "error": f"All data sources failed. Last error: {last_error}",
            "attempted_sources": attempted_sources,
            "symbol": symbol
        }
    
    def test_all_sources(self) -> Dict[str, Any]:
        """Test all configured data sources."""
        test_results = {}
        
        for source in self.sources:
            try:
                logger.info(f"Testing data source: {source.name}")
                result = source.get_price_data("SPY", period_days=5)
                test_results[source.name] = {
                    "available": result.get("success", False),
                    "error": result.get("error"),
                    "priority": source.priority,
                    "data_points": result.get("data_points", 0) if result.get("success") else 0
                }
            except Exception as e:
                test_results[source.name] = {
                    "available": False,
                    "error": str(e),
                    "priority": source.priority,
                    "data_points": 0
                }
        
        return {
            "test_results": test_results,
            "total_sources": len(self.sources),
            "available_sources": sum(1 for r in test_results.values() if r["available"]),
            "tested_at": datetime.now().isoformat()
        }

