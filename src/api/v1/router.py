"""
Main API Router for True-Asset-ALLUSE v1

Aggregates all API endpoint routers and provides the main API router
for inclusion in the FastAPI application.
"""

from fastapi import APIRouter

# Import endpoint routers (will be created in subsequent phases)
# from src.api.v1.endpoints.accounts import router as accounts_router
# from src.api.v1.endpoints.positions import router as positions_router
# from src.api.v1.endpoints.orders import router as orders_router
# from src.api.v1.endpoints.rules import router as rules_router
# from src.api.v1.endpoints.protocol import router as protocol_router
# from src.api.v1.endpoints.reports import router as reports_router

# Create main API router
api_router = APIRouter()

# Health check endpoint (temporary until other routers are implemented)
@api_router.get("/health")
async def api_health():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "message": "True-Asset-ALLUSE API v1 is operational"
    }

# Include endpoint routers (will be uncommented as they are implemented)
# api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
# api_router.include_router(positions_router, prefix="/positions", tags=["positions"])
# api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
# api_router.include_router(rules_router, prefix="/rules", tags=["rules"])
# api_router.include_router(protocol_router, prefix="/protocol", tags=["protocol"])
# api_router.include_router(reports_router, prefix="/reports", tags=["reports"])

