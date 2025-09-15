"""
Reporting & Analytics UI Router

This module implements the API router for the reporting and analytics UI.
"""

from fastapi import APIRouter

from .reporting_backend import ReportingAPI

reporting_router = APIRouter()

# This is a placeholder - in a real application, you would inject the
# ReportingAPI instance here
# reporting_router.include_router(ReportingAPI(None, None).get_router())


