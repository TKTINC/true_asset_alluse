"""
Reporting & Analytics UI Backend

This module implements the backend for the reporting and analytics UI,
providing API endpoints for report generation, data visualization, and
portfolio analytics.
"""

from fastapi import APIRouter, Depends

from src.ws6_user_interface.authentication import AuthManager, rbac, Role
from src.ws5_portfolio_management.reporting import ReportGenerator

class ReportingAPI:
    """
    Reporting & Analytics UI API.
    """
    
    def __init__(self, auth_manager: AuthManager, report_generator: ReportGenerator):
        self.router = APIRouter()
        self.auth_manager = auth_manager
        self.report_generator = report_generator
        
        self._register_routes()
    
    def _register_routes(self):
        """Register all reporting API routes."""
        self.router.post("/reports", dependencies=[Depends(self.auth_manager.get_current_user)])(self.create_report)
        self.router.get("/reports", dependencies=[Depends(self.auth_manager.get_current_user)])(self.get_reports)
    
    def create_report(self, report_def: dict):
        """Create new report."""
        return self.report_generator.generate_report(report_def["report_id"], report_def["report_data"])
    
    def get_reports(self):
        """Get all reports."""
        return self.report_generator.get_all_reports()
    
    def get_router(self) -> APIRouter:
        """Get the reporting API router."""
        return self.router


