"""
WS6: User Interface & API Layer

This module implements the user-facing components of the True-Asset-ALLUSE
system, including the API gateway, web dashboard, trading interface, and
reporting tools.
"""

from .api_gateway import APIGateway
from .authentication import AuthManager, rbac
from .dashboard import DashboardApp
from .trading_backend import TradingAPI
from .reporting_backend import ReportingAPI

__all__ = [
    "APIGateway",
    "AuthManager",
    "rbac",
    "DashboardApp",
    "TradingAPI",
    "ReportingAPI"
]


