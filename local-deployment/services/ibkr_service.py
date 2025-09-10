"""
Interactive Brokers Integration Service
Real paper trading account connection for True-Asset-ALLUSE
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

try:
    from ib_insync import IB, Stock, Option, Contract, PortfolioItem
    from ib_insync.util import df
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    logging.warning("ib_insync not available. IBKR integration disabled.")

from config_enhanced import config

logger = logging.getLogger(__name__)

class IBKRService:
    """Interactive Brokers service for real paper trading integration"""
    
    def __init__(self):
        self.ib = None
        self.connected = False
        self.portfolio_cache = {}
        self.positions_cache = []
        self.last_update = None
        
        if not IBKR_AVAILABLE:
            logger.warning("IBKR service initialized without ib_insync library")
    
    async def connect(self) -> bool:
        """Connect to Interactive Brokers TWS/Gateway"""
        if not IBKR_AVAILABLE or not config.ibkr_enabled:
            logger.info("IBKR integration disabled or unavailable")
            return False
        
        try:
            self.ib = IB()
            
            # Connect to TWS/Gateway
            await self.ib.connectAsync(
                host=config.ibkr_host,
                port=config.ibkr_port,
                clientId=config.ibkr_client_id,
                timeout=config.ibkr_timeout
            )
            
            self.connected = True
            logger.info(f"Connected to IBKR at {config.ibkr_host}:{config.ibkr_port}")
            
            # Verify paper trading mode
            if config.paper_trading_only:
                account_summary = await self.get_account_summary()
                if account_summary and "Paper" not in str(account_summary.get("AccountType", "")):
                    logger.warning("Connected to live account but paper_trading_only is True")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary information"""
        if not self.connected:
            return {}
        
        try:
            account_values = self.ib.accountSummary()
            
            summary = {}
            for item in account_values:
                summary[item.tag] = item.value
            
            return {
                "account_id": summary.get("AccountCode", "Unknown"),
                "account_type": summary.get("AccountType", "Unknown"),
                "net_liquidation": float(summary.get("NetLiquidation", 0)),
                "total_cash": float(summary.get("TotalCashValue", 0)),
                "buying_power": float(summary.get("BuyingPower", 0)),
                "day_trades_remaining": int(summary.get("DayTradesRemaining", 0)),
                "currency": summary.get("Currency", "USD")
            }
            
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            return {}
    
    async def get_portfolio_positions(self) -> List[Dict[str, Any]]:
        """Get current portfolio positions"""
        if not self.connected:
            return []
        
        try:
            portfolio_items = self.ib.portfolio()
            positions = []
            
            for item in portfolio_items:
                contract = item.contract
                
                position_data = {
                    "symbol": contract.symbol,
                    "sec_type": contract.secType,
                    "exchange": contract.exchange,
                    "currency": contract.currency,
                    "position": item.position,
                    "market_price": item.marketPrice,
                    "market_value": item.marketValue,
                    "average_cost": item.averageCost,
                    "unrealized_pnl": item.unrealizedPNL,
                    "realized_pnl": item.realizedPNL,
                    "account": item.account
                }
                
                # Add option-specific data
                if contract.secType == "OPT":
                    position_data.update({
                        "strike": contract.strike,
                        "expiry": contract.lastTradeDateOrContractMonth,
                        "right": contract.right,  # PUT or CALL
                        "multiplier": contract.multiplier
                    })
                
                positions.append(position_data)
            
            self.positions_cache = positions
            self.last_update = datetime.now()
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get portfolio positions: {e}")
            return []
    
    async def get_market_data(self, symbol: str, sec_type: str = "STK") -> Dict[str, Any]:
        """Get real-time market data for a symbol"""
        if not self.connected:
            return {}
        
        try:
            if sec_type == "STK":
                contract = Stock(symbol, "SMART", "USD")
            else:
                # For options, would need more parameters
                return {}
            
            # Request market data
            self.ib.reqMktData(contract)
            await asyncio.sleep(1)  # Wait for data
            
            ticker = self.ib.ticker(contract)
            
            return {
                "symbol": symbol,
                "last_price": ticker.last,
                "bid": ticker.bid,
                "ask": ticker.ask,
                "bid_size": ticker.bidSize,
                "ask_size": ticker.askSize,
                "volume": ticker.volume,
                "high": ticker.high,
                "low": ticker.low,
                "close": ticker.close,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return {}
    
    async def get_option_chain(self, symbol: str, expiry: str = None) -> List[Dict[str, Any]]:
        """Get option chain for a symbol"""
        if not self.connected:
            return []
        
        try:
            stock = Stock(symbol, "SMART", "USD")
            
            # Get option chains
            chains = await self.ib.reqSecDefOptParamsAsync(
                stock.symbol, "", stock.secType, stock.conId
            )
            
            options = []
            for chain in chains:
                for expiration in chain.expirations[:3]:  # Limit to first 3 expirations
                    for strike in chain.strikes[::5]:  # Every 5th strike to limit data
                        for right in ["C", "P"]:
                            option = Option(
                                symbol, expiration, strike, right, "SMART"
                            )
                            
                            # Get option details
                            details = await self.ib.reqContractDetailsAsync(option)
                            if details:
                                options.append({
                                    "symbol": symbol,
                                    "expiry": expiration,
                                    "strike": strike,
                                    "right": right,
                                    "contract_id": details[0].contract.conId,
                                    "multiplier": details[0].contract.multiplier
                                })
            
            return options[:20]  # Limit to 20 options for demo
            
        except Exception as e:
            logger.error(f"Failed to get option chain for {symbol}: {e}")
            return []
    
    async def place_paper_order(self, contract_data: Dict[str, Any], order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a paper trading order (demo only)"""
        if not self.connected or not config.paper_trading_only:
            return {"error": "Paper trading not available"}
        
        try:
            # This is a demo implementation - would need full order logic for production
            order_id = f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Demo paper order placed: {order_id}")
            
            return {
                "order_id": order_id,
                "status": "Submitted",
                "symbol": contract_data.get("symbol"),
                "action": order_data.get("action"),
                "quantity": order_data.get("quantity"),
                "order_type": order_data.get("order_type"),
                "timestamp": datetime.now().isoformat(),
                "note": "This is a demo order - no actual trade executed"
            }
            
        except Exception as e:
            logger.error(f"Failed to place paper order: {e}")
            return {"error": str(e)}
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        if not self.connected:
            return self._get_mock_portfolio_summary()
        
        try:
            account_summary = await self.get_account_summary()
            positions = await self.get_portfolio_positions()
            
            # Calculate portfolio metrics
            total_value = account_summary.get("net_liquidation", 0)
            total_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)
            
            # Calculate portfolio delta (simplified)
            portfolio_delta = 0
            for pos in positions:
                if pos.get("sec_type") == "OPT":
                    # Simplified delta calculation - would need real Greeks
                    delta = 0.5 if pos.get("right") == "C" else -0.5
                    portfolio_delta += delta * pos.get("position", 0)
            
            return {
                "total_value": total_value,
                "daily_pnl": total_pnl,
                "daily_pnl_percent": (total_pnl / total_value * 100) if total_value > 0 else 0,
                "portfolio_delta": portfolio_delta,
                "active_positions": len(positions),
                "positions": positions,
                "account_info": account_summary,
                "last_update": datetime.now().isoformat(),
                "data_source": "IBKR_Live"
            }
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return self._get_mock_portfolio_summary()
    
    def _get_mock_portfolio_summary(self) -> Dict[str, Any]:
        """Fallback mock portfolio data when IBKR unavailable"""
        return {
            "total_value": config.mock_portfolio_value,
            "daily_pnl": config.mock_daily_pnl,
            "daily_pnl_percent": (config.mock_daily_pnl / config.mock_portfolio_value * 100),
            "portfolio_delta": -0.28,
            "active_positions": 4,
            "positions": [
                {
                    "symbol": "AAPL",
                    "sec_type": "OPT",
                    "strike": 175,
                    "expiry": "20241215",
                    "right": "P",
                    "position": -10,
                    "market_value": 4250,
                    "unrealized_pnl": 425,
                    "market_price": 4.25
                }
            ],
            "account_info": {
                "account_id": "DEMO123456",
                "account_type": "Paper Trading",
                "net_liquidation": config.mock_portfolio_value
            },
            "last_update": datetime.now().isoformat(),
            "data_source": "Mock_Data"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check IBKR service health"""
        if not IBKR_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "ib_insync library not installed",
                "connected": False
            }
        
        if not config.ibkr_enabled:
            return {
                "status": "disabled",
                "message": "IBKR integration disabled in configuration",
                "connected": False
            }
        
        if not self.connected:
            # Try to reconnect
            connected = await self.connect()
            if not connected:
                return {
                    "status": "disconnected",
                    "message": f"Cannot connect to TWS at {config.ibkr_host}:{config.ibkr_port}",
                    "connected": False
                }
        
        try:
            # Test connection with a simple request
            account_summary = await self.get_account_summary()
            
            return {
                "status": "healthy",
                "message": "Connected to IBKR TWS",
                "connected": True,
                "account_id": account_summary.get("account_id", "Unknown"),
                "account_type": account_summary.get("account_type", "Unknown"),
                "last_update": self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"IBKR connection error: {e}",
                "connected": False
            }

# Global service instance
ibkr_service = IBKRService()

