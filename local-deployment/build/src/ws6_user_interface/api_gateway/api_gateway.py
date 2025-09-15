"""
API Gateway

This module implements the main API gateway for the True-Asset-ALLUSE
system, providing a unified entry point for all API requests and routing
them to the appropriate backend services.
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .router import api_router
from src.ws6_user_interface.authentication import AuthManager

class APIGateway:
    """
    Main API Gateway application.
    """
    
    def __init__(self, auth_manager: AuthManager):
        self.app = FastAPI(
            title="True-Asset-ALLUSE API Gateway",
            description="The main API gateway for the True-Asset-ALLUSE system.",
            version="1.0.0"
        )
        self.auth_manager = auth_manager
        
        self._configure_middleware()
        self._include_routers()
    
    def _configure_middleware(self):
        """Configure FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for now
            allow_credentials=True,
            allow_methods=["*"]
        )
        # Add other middleware here (e.g., logging, authentication)
    
    def _include_routers(self):
        """Include all API routers."""
        self.app.include_router(api_router, prefix="/api/v1")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app


