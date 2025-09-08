"""
Report Generator

This module implements the comprehensive report generation system that
creates custom, professional reports for portfolio analysis, performance
measurement, and risk management for the True-Asset-ALLUSE system.
"""

from typing import Dict, Any, Optional, List, Callable, Set
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import threading
import time
from dataclasses import dataclass, asdict
import uuid
import pandas as pd
from fpdf import FPDF

from src.ws1_rules_engine.audit import AuditTrailManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Report output formats."""
    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    JSON = "json"


class ReportSection(Enum):
    """Report sections."""
    SUMMARY = "summary"
    PERFORMANCE = "performance"
    RISK = "risk"
    OPTIMIZATION = "optimization"
    ATTRIBUTION = "attribution"
    HOLDINGS = "holdings"
    TRANSACTIONS = "transactions"


@dataclass
class ReportDefinition:
    """Report definition structure."""
    report_id: str
    name: str
    description: str
    portfolio_id: str
    sections: List[ReportSection]
    output_format: ReportFormat
    start_date: date
    end_date: date
    created_timestamp: datetime


class ReportGenerator:
    """
    Comprehensive Report Generator.
    
    Creates custom, professional reports for portfolio analysis, performance
    measurement, and risk management. Supports multiple output formats and
    customizable report sections.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator.
        
        Args:
            audit_manager: Audit trail manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.config = config or {}
        
        # Configuration parameters
        self.report_output_dir = self.config.get("report_output_dir", "/tmp/reports")
        self.default_format = ReportFormat(self.config.get("default_format", "pdf"))
        
        # Report management
        self.report_definitions = {}  # report_id -> ReportDefinition
        self.generated_reports = {}  # report_id -> file_path
        
        # Threading and processing
        self.generator_lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            "total_reports_generated": 0,
            "reports_by_format": {
                "pdf": 0,
                "html": 0,
                "csv": 0,
                "json": 0
            },
            "average_generation_time": 0,
            "last_report_generated": None
        }
        
        logger.info("Report Generator initialized")
    
    def create_report_definition(self, report_def: ReportDefinition) -> Dict[str, Any]:
        """Create new report definition."""
        try:
            with self.generator_lock:
                self.report_definitions[report_def.report_id] = report_def
            
            logger.info(f"Created report definition: {report_def.report_id}")
            
            return {
                "success": True,
                "report_id": report_def.report_id,
                "name": report_def.name,
                "format": report_def.output_format.value,
                "created_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating report definition: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "report_id": report_def.report_id
            }
    
    def generate_report(self, 
                        report_id: str,
                        report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate report based on its definition.
        
        Args:
            report_id: ID of the report to generate
            report_data: Data for the report sections
            
        Returns:
            Report generation result
        """
        try:
            start_time = time.time()
            
            if report_id not in self.report_definitions:
                return {"success": False, "error": "Report definition not found"}
            
            report_def = self.report_definitions[report_id]
            
            # Generate report based on format
            if report_def.output_format == ReportFormat.PDF:
                file_path = self._generate_pdf_report(report_def, report_data)
            elif report_def.output_format == ReportFormat.HTML:
                file_path = self._generate_html_report(report_def, report_data)
            else:
                return {"success": False, "error": "Report format not supported"}
            
            with self.generator_lock:
                self.generated_reports[report_id] = file_path
            
            # Log report generation
            self.audit_manager.log_system_event(
                event_type="report_generated",
                event_data={
                    "report_id": report_id,
                    "format": report_def.output_format.value,
                    "file_path": file_path
                },
                severity="info"
            )
            
            generation_time = time.time() - start_time
            self.metrics["total_reports_generated"] += 1
            self.metrics["reports_by_format"][report_def.output_format.value] += 1
            self.metrics["average_generation_time"] = (
                (self.metrics["average_generation_time"] * (self.metrics["total_reports_generated"] - 1) + generation_time) / 
                self.metrics["total_reports_generated"]
            )
            self.metrics["last_report_generated"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "report_id": report_id,
                "file_path": file_path,
                "generation_time_seconds": generation_time
            }
            
        except Exception as e:
            logger.error(f"Error generating report {report_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "report_id": report_id
            }
    
    def _generate_pdf_report(self, 
                             report_def: ReportDefinition,
                             report_data: Dict[str, Any]) -> str:
        """Generate PDF report."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Report header
        pdf.cell(200, 10, txt=report_def.name, ln=1, align="C")
        pdf.cell(200, 10, txt=f"Portfolio: {report_def.portfolio_id}", ln=1, align="C")
        pdf.cell(200, 10, txt=f"Period: {report_def.start_date} to {report_def.end_date}", ln=1, align="C")
        pdf.ln(10)
        
        # Report sections
        for section in report_def.sections:
            if section == ReportSection.SUMMARY:
                self._add_summary_section_pdf(pdf, report_data.get("summary"))
            elif section == ReportSection.PERFORMANCE:
                self._add_performance_section_pdf(pdf, report_data.get("performance"))
            # Add other sections...
        
        file_path = f"{self.report_output_dir}/{report_def.report_id}.pdf"
        pdf.output(file_path)
        return file_path
    
    def _generate_html_report(self, 
                              report_def: ReportDefinition,
                              report_data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html = f"<html><head><title>{report_def.name}</title></head><body>"
        html += f"<h1>{report_def.name}</h1>"
        html += f"<h2>Portfolio: {report_def.portfolio_id}</h2>"
        html += f"<h3>Period: {report_def.start_date} to {report_def.end_date}</h3>"
        
        # Report sections
        for section in report_def.sections:
            if section == ReportSection.SUMMARY:
                html += self._add_summary_section_html(report_data.get("summary"))
            elif section == ReportSection.PERFORMANCE:
                html += self._add_performance_section_html(report_data.get("performance"))
            # Add other sections...
            
        html += "</body></html>"
        
        file_path = f"{self.report_output_dir}/{report_def.report_id}.html"
        with open(file_path, "w") as f:
            f.write(html)
        return file_path
    
    def _add_summary_section_pdf(self, pdf: FPDF, data: Dict[str, Any]):
        pdf.set_font("Arial", "B", size=14)
        pdf.cell(200, 10, txt="Portfolio Summary", ln=1)
        pdf.set_font("Arial", size=12)
        
        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=1)
        pdf.ln(10)
    
    def _add_performance_section_pdf(self, pdf: FPDF, data: Dict[str, Any]):
        pdf.set_font("Arial", "B", size=14)
        pdf.cell(200, 10, txt="Performance Analysis", ln=1)
        pdf.set_font("Arial", size=12)
        
        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=1)
        pdf.ln(10)
    
    def _add_summary_section_html(self, data: Dict[str, Any]) -> str:
        html = "<h2>Portfolio Summary</h2>"
        html += "<ul>"
        for key, value in data.items():
            html += f"<li><b>{key}:</b> {value}</li>"
        html += "</ul>"
        return html
    
    def _add_performance_section_html(self, data: Dict[str, Any]) -> str:
        html = "<h2>Performance Analysis</h2>"
        html += "<ul>"
        for key, value in data.items():
            html += f"<li><b>{key}:</b> {value}</li>"
        html += "</ul>"
        return html
    
    def get_generator_status(self) -> Dict[str, Any]:
        """Get report generator status."""
        try:
            return {
                "success": True,
                "total_reports_generated": self.metrics["total_reports_generated"],
                "metrics": self.metrics.copy(),
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting generator status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


