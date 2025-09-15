"""
Trading Interface Router

This module implements the API router for the trading interface.
"""

from fastapi import APIRouter

from .trading_backend import TradingAPI

trading_router = APIRouter()

# This is a placeholder - in a real application, you would inject the
# TradingAPI instance here
# trading_router.include_router(TradingAPI(None, None).get_router())


