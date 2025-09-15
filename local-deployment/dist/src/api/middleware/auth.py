"""
Authentication Middleware for True-Asset-ALLUSE

Provides authentication and authorization for API endpoints.
For PoC phase, this implements basic authentication.
"""

from typing import Callable, Optional

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from src.common.config import get_settings
from src.common.exceptions import AuthenticationError, AuthorizationError

logger = structlog.get_logger(__name__)
settings = get_settings()


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and authorization."""
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle authentication."""
        
        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication in development mode
        if settings.debug:
            logger.debug(
                "Skipping authentication in debug mode",
                path=request.url.path
            )
            return await call_next(request)
        
        try:
            # Extract authentication token
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise AuthenticationError("Missing Authorization header")
            
            # Validate token format
            if not auth_header.startswith("Bearer "):
                raise AuthenticationError("Invalid Authorization header format")
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Validate token (simplified for PoC)
            user = await self._validate_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            
            # Add user to request state
            request.state.user = user
            
            logger.debug(
                "Authentication successful",
                user_id=user.get("id"),
                path=request.url.path
            )
            
            return await call_next(request)
            
        except (AuthenticationError, AuthorizationError) as e:
            logger.warning(
                "Authentication failed",
                path=request.url.path,
                error=str(e)
            )
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        except Exception as e:
            logger.error(
                "Authentication error",
                path=request.url.path,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal authentication error"
            )
    
    async def _validate_token(self, token: str) -> Optional[dict]:
        """
        Validate authentication token.
        
        For PoC phase, this is a simplified implementation.
        In production, this would validate JWT tokens or API keys.
        """
        # Simplified validation for PoC
        if token == "dev-token-123":
            return {
                "id": "dev-user",
                "username": "developer",
                "permissions": ["read", "write", "admin"]
            }
        
        # In production, implement proper JWT validation here
        return None

