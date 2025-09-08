"""
Trading Interface Backend

This module implements the backend for the trading interface, providing
API endpoints for order management, position tracking, and trade execution.
"""

from fastapi import APIRouter, Depends

from src.ws6_user_interface.authentication import AuthManager, rbac, Role
from src.ws4_market_data_execution.execution_engine import TradeExecutionEngine

class TradingAPI:
    """
    Trading Interface API.
    """
    
    def __init__(self, auth_manager: AuthManager, execution_engine: TradeExecutionEngine):
        self.router = APIRouter()
        self.auth_manager = auth_manager
        self.execution_engine = execution_engine
        
        self._register_routes()
    
    def _register_routes(self):
        """Register all trading API routes."""
        self.router.post("/orders", dependencies=[Depends(self.auth_manager.get_current_user)])(self.create_order)
        self.router.get("/orders", dependencies=[Depends(self.auth_manager.get_current_user)])(self.get_orders)
        self.router.get("/positions", dependencies=[Depends(self.auth_manager.get_current_user)])(self.get_positions)
    
    def create_order(self, order: dict):
        """Create new trade order."""
        # Add pre-trade compliance checks here
        return self.execution_engine.submit_order(order)
    
    def get_orders(self):
        """Get all trade orders."""
        return self.execution_engine.get_all_orders()
    
    def get_positions(self):
        """Get all positions."""
        return self.execution_engine.get_all_positions()
    
    def get_router(self) -> APIRouter:
        """Get the trading API router."""
        return self.router


