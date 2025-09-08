"""
API Router

This module implements the main API router that includes all sub-routers
for the different backend services.
"""

from fastapi import APIRouter

from src.ws6_user_interface.trading_backend.router import trading_router
from src.ws6_user_interface.reporting_backend.router import reporting_router

api_router = APIRouter()

api_router.include_router(trading_router, prefix="/trading", tags=["Trading"])
api_router.include_router(reporting_router, prefix="/reporting", tags=["Reporting"])


