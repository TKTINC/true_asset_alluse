"""
API Gateway

This module implements the main API gateway for the True-Asset-ALLUSE
system, providing a unified entry point for all API requests and routing
them to the appropriate backend services.
"""

from .api_gateway import APIGateway
from .router import api_router

__all__ = [
    "APIGateway",
    "api_router"
]


