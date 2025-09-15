"""
ATR Calculation Engine

This is the main ATR calculation engine that orchestrates data sources,
validation, and calculation to provide robust ATR values for the Protocol Engine.

The engine implements multiple fallback mechanisms and quality checks to ensure
reliable ATR calculations for risk management decisions.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import logging
from decimal import Decimal
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from .atr_calculator import ATRCalculator
from .data_sources import (
    DataSourceManager, YahooFinanceSource, AlphaVantageSource, 
    IEXCloudSource, InteractiveBrokersSource
)
from .data_validator import ATRDataValidator
from src.common.config import get_settings

logger = logging.getLogger(__name__)


class ATRCalculationEngine:
    """
    Main ATR Calculation Engine with multi-source data and fallback mechanisms.
    
    This engine provides robust ATR calculation by:
    1. Using multiple data sources with automatic fallback
    2. Validating data quality before calculation
    3. Supporting multiple ATR calculation methods
    4. Caching results for performance
    5. Providing detailed calculation metadata
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ATR Calculation Engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.settings = get_settings()
        
        # Initialize components
        self.calculator = ATRCalculator()
        self.validator = ATRDataValidator()
        self.data_manager = DataSourceManager()
        
        # Configuration
        self.default_period = self.config.get("default_atr_period", 14)
        self.default_method = self.config.get("default_atr_method", "wilder")
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.cache_duration = self.config.get("cache_duration", 300)  # 5 minutes
        self.parallel_enabled = self.config.get("parallel_enabled", True)
        
        # Cache storage
        self.cache = {}
        
        # Initialize data sources
        self._initialize_data_sources()
        
        logger.info("ATR Calculation Engine initialized")
    
    def _initialize_data_sources(self):
        """Initialize and configure data sources."""
        try:
            # Always add Yahoo Finance (free, reliable)
            yahoo_source = YahooFinanceSource()
            self.data_manager.add_source(yahoo_source)
            
            # Add Alpha Vantage if API key available
            alpha_vantage_key = self.settings.ALPHA_VANTAGE_API_KEY
            if alpha_vantage_key:
                alpha_source = AlphaVantageSource(alpha_vantage_key)
                self.data_manager.add_source(alpha_source)
                logger.info("Alpha Vantage data source added")
            
            # Add IEX Cloud if API key available
            iex_key = self.settings.IEX_CLOUD_API_KEY
            if iex_key:
                iex_source = IEXCloudSource(iex_key, sandbox=self.settings.IEX_CLOUD_SANDBOX)
                self.data_manager.add_source(iex_source)
                logger.info("IEX Cloud data source added")
            
            # Add Interactive Brokers (will be implemented in WS4)
            ib_source = InteractiveBrokersSource()
            self.data_manager.add_source(ib_source)
            
            logger.info(f"Initialized {len(self.data_manager.sources)} data sources")
            
        except Exception as e:
            logger.error(f"Error initializing data sources: {str(e)}", exc_info=True)
    
    def calculate_atr(self, 
                     symbol: str,
                     period: Optional[int] = None,
                     method: Optional[str] = None,
                     period_days: int = 30,
                     end_date: Optional[date] = None,
                     force_refresh: bool = False) -> Dict[str, Any]:
        """
        Calculate ATR for a given symbol with comprehensive error handling.
        
        Args:
            symbol: Trading symbol (e.g., 'SPY', 'QQQ')
            period: ATR period (default from config)
            method: ATR calculation method ('sma', 'ema', 'wilder')
            period_days: Days of price data to retrieve
            end_date: End date for data (default: today)
            force_refresh: Force refresh of cached data
            
        Returns:
            ATR calculation result with metadata
        """
        try:
            # Use defaults if not specified
            period = period or self.default_period
            method = method or self.default_method
            end_date = end_date or date.today()
            
            # Generate cache key
            cache_key = self._generate_cache_key(symbol, period, method, period_days, end_date)
            
            # Check cache if enabled and not forcing refresh
            if self.cache_enabled and not force_refresh and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                cache_age = (datetime.now() - cached_result["cached_at"]).total_seconds()
                
                if cache_age < self.cache_duration:
                    logger.info(f"Returning cached ATR for {symbol}")
                    cached_result["from_cache"] = True
                    return cached_result
            
            logger.info(f"Calculating ATR for {symbol} (period={period}, method={method})")
            
            # Step 1: Get price data with fallback
            price_data_result = self.data_manager.get_price_data_with_fallback(
                symbol=symbol,
                period_days=period_days,
                end_date=end_date
            )
            
            if not price_data_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to retrieve price data: {price_data_result.get('error')}",
                    "symbol": symbol,
                    "attempted_sources": price_data_result.get("attempted_sources", []),
                    "calculation_timestamp": datetime.now().isoformat()
                }
            
            price_data = price_data_result["data"]
            
            # Step 2: Validate price data quality
            validation_result = self.validator.validate_price_data(price_data)
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Price data validation failed: {'; '.join(validation_result['errors'])}",
                    "symbol": symbol,
                    "validation_result": validation_result,
                    "data_source": price_data_result.get("source"),
                    "calculation_timestamp": datetime.now().isoformat()
                }
            
            # Step 3: Calculate ATR
            atr_result = self.calculator.calculate_atr(
                price_data=price_data,
                period=period,
                method=method
            )
            
            # Step 4: Validate ATR result
            atr_validation = self.validator.validate_atr_result(atr_result)
            
            if not atr_validation["valid"]:
                return {
                    "success": False,
                    "error": f"ATR calculation validation failed: {'; '.join(atr_validation['errors'])}",
                    "symbol": symbol,
                    "atr_result": atr_result,
                    "atr_validation": atr_validation,
                    "calculation_timestamp": datetime.now().isoformat()
                }
            
            # Step 5: Compile comprehensive result
            result = {
                "success": True,
                "symbol": symbol,
                "atr": atr_result["atr"],
                "period": period,
                "method": method,
                "calculation_details": atr_result,
                "data_quality": {
                    "validation_result": validation_result,
                    "quality_score": validation_result["quality_score"],
                    "data_points": len(price_data),
                    "data_source": price_data_result.get("source"),
                    "fallback_used": price_data_result.get("fallback_used", False)
                },
                "atr_validation": atr_validation,
                "metadata": {
                    "calculation_timestamp": datetime.now().isoformat(),
                    "data_start_date": price_data[0]["date"] if price_data else None,
                    "data_end_date": price_data[-1]["date"] if price_data else None,
                    "attempted_sources": price_data_result.get("attempted_sources", [])
                },
                "from_cache": False
            }
            
            # Cache result if enabled
            if self.cache_enabled:
                result["cached_at"] = datetime.now()
                self.cache[cache_key] = result.copy()
                logger.debug(f"Cached ATR result for {symbol}")
            
            logger.info(f"Successfully calculated ATR for {symbol}: {atr_result['atr']:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating ATR for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"ATR calculation error: {str(e)}",
                "symbol": symbol,
                "calculation_timestamp": datetime.now().isoformat()
            }
    
    def calculate_multiple_symbols(self, 
                                 symbols: List[str],
                                 period: Optional[int] = None,
                                 method: Optional[str] = None,
                                 period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate ATR for multiple symbols, optionally in parallel.
        
        Args:
            symbols: List of trading symbols
            period: ATR period
            method: ATR calculation method
            period_days: Days of price data to retrieve
            
        Returns:
            ATR results for all symbols
        """
        try:
            logger.info(f"Calculating ATR for {len(symbols)} symbols")
            
            results = {}
            
            if self.parallel_enabled and len(symbols) > 1:
                # Parallel calculation
                with ThreadPoolExecutor(max_workers=min(len(symbols), 5)) as executor:
                    future_to_symbol = {
                        executor.submit(
                            self.calculate_atr, 
                            symbol, 
                            period, 
                            method, 
                            period_days
                        ): symbol 
                        for symbol in symbols
                    }
                    
                    for future in future_to_symbol:
                        symbol = future_to_symbol[future]
                        try:
                            result = future.result(timeout=60)  # 60 second timeout
                            results[symbol] = result
                        except Exception as e:
                            logger.error(f"Error calculating ATR for {symbol}: {str(e)}")
                            results[symbol] = {
                                "success": False,
                                "error": str(e),
                                "symbol": symbol
                            }
            else:
                # Sequential calculation
                for symbol in symbols:
                    result = self.calculate_atr(symbol, period, method, period_days)
                    results[symbol] = result
            
            # Compile summary statistics
            successful_calculations = sum(1 for r in results.values() if r.get("success"))
            failed_calculations = len(symbols) - successful_calculations
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "total_symbols": len(symbols),
                    "successful_calculations": successful_calculations,
                    "failed_calculations": failed_calculations,
                    "success_rate": successful_calculations / len(symbols) if symbols else 0
                },
                "calculation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating ATR for multiple symbols: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "symbols": symbols,
                "calculation_timestamp": datetime.now().isoformat()
            }
    
    def get_atr_with_confidence(self, 
                              symbol: str,
                              period: Optional[int] = None,
                              method: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ATR with confidence assessment based on data quality.
        
        Args:
            symbol: Trading symbol
            period: ATR period
            method: ATR calculation method
            
        Returns:
            ATR result with confidence assessment
        """
        try:
            result = self.calculate_atr(symbol, period, method)
            
            if not result.get("success"):
                return result
            
            # Calculate confidence based on data quality
            quality_score = result["data_quality"]["quality_score"]
            data_points = result["data_quality"]["data_points"]
            fallback_used = result["data_quality"]["fallback_used"]
            
            # Confidence calculation
            confidence = quality_score  # Start with quality score
            
            # Adjust for data sufficiency
            if data_points < 20:
                confidence -= 10
            elif data_points > 50:
                confidence += 5
            
            # Adjust for fallback usage
            if fallback_used:
                confidence -= 5
            
            # Adjust for ATR validation quality
            atr_quality = result["atr_validation"].get("atr_quality", "good")
            if atr_quality == "low_volatility":
                confidence -= 5
            elif atr_quality == "high_volatility":
                confidence -= 10
            elif atr_quality == "insufficient_data":
                confidence -= 15
            
            confidence = max(0, min(100, confidence))
            
            # Determine confidence level
            if confidence >= 90:
                confidence_level = "very_high"
            elif confidence >= 75:
                confidence_level = "high"
            elif confidence >= 60:
                confidence_level = "medium"
            elif confidence >= 40:
                confidence_level = "low"
            else:
                confidence_level = "very_low"
            
            result["confidence"] = {
                "score": confidence,
                "level": confidence_level,
                "factors": {
                    "data_quality_score": quality_score,
                    "data_points": data_points,
                    "fallback_used": fallback_used,
                    "atr_quality": atr_quality
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting ATR with confidence for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def test_data_sources(self) -> Dict[str, Any]:
        """Test all configured data sources."""
        logger.info("Testing all data sources")
        return self.data_manager.test_all_sources()
    
    def clear_cache(self):
        """Clear ATR calculation cache."""
        self.cache.clear()
        logger.info("ATR calculation cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache_enabled:
            return {"cache_enabled": False}
        
        now = datetime.now()
        valid_entries = 0
        expired_entries = 0
        
        for cached_result in self.cache.values():
            cache_age = (now - cached_result["cached_at"]).total_seconds()
            if cache_age < self.cache_duration:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "cache_enabled": True,
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_duration": self.cache_duration
        }
    
    def _generate_cache_key(self, 
                          symbol: str, 
                          period: int, 
                          method: str, 
                          period_days: int, 
                          end_date: date) -> str:
        """Generate cache key for ATR calculation."""
        return f"atr_{symbol}_{period}_{method}_{period_days}_{end_date.strftime('%Y%m%d')}"
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive engine status."""
        try:
            data_source_test = self.test_data_sources()
            cache_stats = self.get_cache_stats()
            
            return {
                "engine_status": "operational",
                "data_sources": data_source_test,
                "cache_stats": cache_stats,
                "configuration": {
                    "default_period": self.default_period,
                    "default_method": self.default_method,
                    "cache_enabled": self.cache_enabled,
                    "parallel_enabled": self.parallel_enabled
                },
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting engine status: {str(e)}", exc_info=True)
            return {
                "engine_status": "error",
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }

