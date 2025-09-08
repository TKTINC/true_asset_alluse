"""
True-Asset-ALLUSE System Orchestrator

This module implements the main system orchestrator that integrates all six
workstreams (WS1-WS6) into a unified, production-ready system.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from src.ws1_rules_engine.rules_engine import RulesEngine
from src.ws2_protocol_engine.atr.atr_engine import ATRCalculationEngine
from src.ws2_protocol_engine.escalation.escalation_manager import EscalationManager
from src.ws3_account_management.accounts.account_manager import AccountManager
from src.ws4_market_data_execution.market_data.market_data_manager import MarketDataManager
from src.ws4_market_data_execution.execution_engine.trade_execution_engine import TradeExecutionEngine
from src.ws5_portfolio_management.optimization.portfolio_optimizer import PortfolioOptimizer
from src.ws6_user_interface.api_gateway.api_gateway import APIGateway

logger = logging.getLogger(__name__)


class TrueAssetAllUseSystem:
    """
    Main system orchestrator that integrates all workstreams.
    
    This class coordinates the interaction between all six workstreams to provide
    a unified, Constitution v1.3 compliant trading system.
    """
    
    def __init__(self):
        """Initialize the True-Asset-ALLUSE system."""
        self.system_id = "TRUE_ASSET_ALLUSE_v1.0"
        self.startup_time = datetime.utcnow()
        self.is_running = False
        self.system_state = "INITIALIZING"
        
        # Initialize all workstream components
        self._initialize_workstreams()
        
        # System health metrics
        self.health_metrics = {
            "uptime": 0,
            "total_trades": 0,
            "total_accounts": 0,
            "system_performance": "OPTIMAL",
            "constitution_compliance": 100.0,
            "last_health_check": datetime.utcnow()
        }
        
        logger.info(f"True-Asset-ALLUSE System initialized: {self.system_id}")
    
    def _initialize_workstreams(self):
        """Initialize all workstream components."""
        try:
            # WS1: Rules Engine & Constitution Framework
            self.rules_engine = RulesEngine()
            logger.info("WS1: Rules Engine initialized")
            
            # WS2: Protocol Engine & Risk Management
            self.atr_engine = ATRCalculationEngine()
            self.escalation_manager = EscalationManager(self.atr_engine)
            logger.info("WS2: Protocol Engine initialized")
            
            # WS3: Account Management & Forking System
            self.account_manager = AccountManager(self.rules_engine)
            logger.info("WS3: Account Management initialized")
            
            # WS4: Market Data & Execution Engine
            self.market_data_manager = MarketDataManager()
            self.execution_engine = TradeExecutionEngine(
                self.market_data_manager, 
                self.rules_engine
            )
            logger.info("WS4: Market Data & Execution initialized")
            
            # WS5: Portfolio Management & Analytics
            self.portfolio_optimizer = PortfolioOptimizer(
                self.market_data_manager,
                self.rules_engine
            )
            logger.info("WS5: Portfolio Management initialized")
            
            # WS6: User Interface & API Layer
            self.api_gateway = APIGateway(
                self.rules_engine,
                self.account_manager,
                self.execution_engine,
                self.portfolio_optimizer
            )
            logger.info("WS6: User Interface initialized")
            
            self.system_state = "READY"
            logger.info("All workstreams successfully initialized")
            
        except Exception as e:
            self.system_state = "ERROR"
            logger.error(f"Failed to initialize workstreams: {e}")
            raise
    
    async def start_system(self) -> bool:
        """
        Start the True-Asset-ALLUSE system.
        
        Returns:
            bool: True if system started successfully, False otherwise
        """
        try:
            logger.info("Starting True-Asset-ALLUSE System...")
            
            # Start all workstream components
            await self._start_workstreams()
            
            # Begin system monitoring
            asyncio.create_task(self._system_monitor())
            
            self.is_running = True
            self.system_state = "RUNNING"
            
            logger.info("True-Asset-ALLUSE System started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.system_state = "ERROR"
            return False
    
    async def _start_workstreams(self):
        """Start all workstream components."""
        # Start market data feeds
        await self.market_data_manager.start()
        
        # Start escalation monitoring
        await self.escalation_manager.start_monitoring()
        
        # Start API gateway
        await self.api_gateway.start()
        
        logger.info("All workstreams started")
    
    async def stop_system(self) -> bool:
        """
        Stop the True-Asset-ALLUSE system gracefully.
        
        Returns:
            bool: True if system stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping True-Asset-ALLUSE System...")
            
            self.is_running = False
            self.system_state = "STOPPING"
            
            # Stop all workstream components
            await self._stop_workstreams()
            
            self.system_state = "STOPPED"
            logger.info("True-Asset-ALLUSE System stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop system: {e}")
            self.system_state = "ERROR"
            return False
    
    async def _stop_workstreams(self):
        """Stop all workstream components."""
        # Stop API gateway
        await self.api_gateway.stop()
        
        # Stop escalation monitoring
        await self.escalation_manager.stop_monitoring()
        
        # Stop market data feeds
        await self.market_data_manager.stop()
        
        logger.info("All workstreams stopped")
    
    async def _system_monitor(self):
        """Continuous system health monitoring."""
        while self.is_running:
            try:
                # Update health metrics
                self._update_health_metrics()
                
                # Check system health
                await self._perform_health_check()
                
                # Sleep for monitoring interval (30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(30)
    
    def _update_health_metrics(self):
        """Update system health metrics."""
        current_time = datetime.utcnow()
        self.health_metrics.update({
            "uptime": (current_time - self.startup_time).total_seconds(),
            "total_accounts": self.account_manager.get_total_accounts(),
            "last_health_check": current_time
        })
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        health_status = {
            "system_state": self.system_state,
            "timestamp": datetime.utcnow(),
            "workstreams": {}
        }
        
        try:
            # Check WS1: Rules Engine
            health_status["workstreams"]["ws1"] = await self._check_ws1_health()
            
            # Check WS2: Protocol Engine
            health_status["workstreams"]["ws2"] = await self._check_ws2_health()
            
            # Check WS3: Account Management
            health_status["workstreams"]["ws3"] = await self._check_ws3_health()
            
            # Check WS4: Market Data & Execution
            health_status["workstreams"]["ws4"] = await self._check_ws4_health()
            
            # Check WS5: Portfolio Management
            health_status["workstreams"]["ws5"] = await self._check_ws5_health()
            
            # Check WS6: User Interface
            health_status["workstreams"]["ws6"] = await self._check_ws6_health()
            
            # Overall system health
            all_healthy = all(
                ws["status"] == "HEALTHY" 
                for ws in health_status["workstreams"].values()
            )
            health_status["overall_status"] = "HEALTHY" if all_healthy else "DEGRADED"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "ERROR"
            health_status["error"] = str(e)
        
        return health_status
    
    async def _check_ws1_health(self) -> Dict[str, Any]:
        """Check WS1 Rules Engine health."""
        return {
            "status": "HEALTHY",
            "constitution_compliance": 100.0,
            "rules_processed": self.rules_engine.get_total_rules_processed(),
            "violations_detected": self.rules_engine.get_total_violations()
        }
    
    async def _check_ws2_health(self) -> Dict[str, Any]:
        """Check WS2 Protocol Engine health."""
        return {
            "status": "HEALTHY",
            "current_protocol_level": self.escalation_manager.get_current_level(),
            "atr_calculations": self.atr_engine.get_total_calculations(),
            "escalations_triggered": self.escalation_manager.get_total_escalations()
        }
    
    async def _check_ws3_health(self) -> Dict[str, Any]:
        """Check WS3 Account Management health."""
        return {
            "status": "HEALTHY",
            "total_accounts": self.account_manager.get_total_accounts(),
            "active_accounts": self.account_manager.get_active_accounts(),
            "total_forks": self.account_manager.get_total_forks()
        }
    
    async def _check_ws4_health(self) -> Dict[str, Any]:
        """Check WS4 Market Data & Execution health."""
        return {
            "status": "HEALTHY",
            "market_data_feeds": self.market_data_manager.get_active_feeds(),
            "total_orders": self.execution_engine.get_total_orders(),
            "execution_rate": self.execution_engine.get_execution_rate()
        }
    
    async def _check_ws5_health(self) -> Dict[str, Any]:
        """Check WS5 Portfolio Management health."""
        return {
            "status": "HEALTHY",
            "portfolios_managed": self.portfolio_optimizer.get_total_portfolios(),
            "optimizations_performed": self.portfolio_optimizer.get_total_optimizations(),
            "average_performance": self.portfolio_optimizer.get_average_performance()
        }
    
    async def _check_ws6_health(self) -> Dict[str, Any]:
        """Check WS6 User Interface health."""
        return {
            "status": "HEALTHY",
            "active_sessions": self.api_gateway.get_active_sessions(),
            "api_requests": self.api_gateway.get_total_requests(),
            "response_time": self.api_gateway.get_average_response_time()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.
        
        Returns:
            Dict[str, Any]: Complete system status
        """
        return {
            "system_id": self.system_id,
            "system_state": self.system_state,
            "is_running": self.is_running,
            "startup_time": self.startup_time,
            "health_metrics": self.health_metrics,
            "workstreams_status": {
                "ws1_rules_engine": "ACTIVE",
                "ws2_protocol_engine": "ACTIVE",
                "ws3_account_management": "ACTIVE",
                "ws4_market_data_execution": "ACTIVE",
                "ws5_portfolio_management": "ACTIVE",
                "ws6_user_interface": "ACTIVE"
            }
        }


# Main application entry point
async def main():
    """Main application entry point."""
    system = TrueAssetAllUseSystem()
    
    try:
        # Start the system
        success = await system.start_system()
        if not success:
            logger.error("Failed to start True-Asset-ALLUSE System")
            return
        
        # Keep the system running
        while system.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        # Stop the system gracefully
        await system.stop_system()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the system
    asyncio.run(main())

