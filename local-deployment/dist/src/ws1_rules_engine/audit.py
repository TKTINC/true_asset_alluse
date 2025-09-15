"""
Audit Trail Manager

This module implements the audit trail system that logs all rule executions
and provides immutable audit records for compliance and debugging.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class AuditTrailManager:
    """
    Audit Trail Manager for rule execution logging.
    
    Provides immutable audit trail of all rule executions, decisions,
    and system state changes for compliance and debugging purposes.
    """
    
    def __init__(self):
        """Initialize audit trail manager."""
        self.audit_records = []  # In production, this would be a database
        logger.info("Audit Trail Manager initialized")
    
    def log_rule_execution(self,
                          rule_section: str,
                          context: Dict[str, Any],
                          result: Dict[str, Any],
                          constitution_version: str = "1.3") -> str:
        """
        Log a rule execution to the audit trail.
        
        Args:
            rule_section: Constitution section (e.g., "§2.Gen-Acc.Entry")
            context: Execution context
            result: Execution result
            constitution_version: Constitution version
            
        Returns:
            Audit record ID
        """
        try:
            audit_id = str(uuid4())
            timestamp = datetime.now()
            
            audit_record = {
                "audit_id": audit_id,
                "timestamp": timestamp.isoformat(),
                "rule_section": rule_section,
                "constitution_version": constitution_version,
                "context": self._sanitize_context(context),
                "result": result,
                "success": result.get("approved", False),
                "violations": result.get("violations", []),
                "warnings": result.get("warnings", [])
            }
            
            # Store audit record
            self.audit_records.append(audit_record)
            
            # Log to application logger
            log_level = logging.WARNING if not audit_record["success"] else logging.INFO
            logger.log(
                log_level,
                f"Rule execution: {rule_section} - {'APPROVED' if audit_record['success'] else 'REJECTED'}",
                extra={
                    "audit_id": audit_id,
                    "rule_section": rule_section,
                    "violations": audit_record["violations"]
                }
            )
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Error logging rule execution: {str(e)}", exc_info=True)
            return ""
    
    def log_system_event(self,
                        event_type: str,
                        event_data: Dict[str, Any],
                        severity: str = "info") -> str:
        """
        Log a system event to the audit trail.
        
        Args:
            event_type: Type of event (state_change, error, etc.)
            event_data: Event data
            severity: Event severity (info, warning, error, critical)
            
        Returns:
            Audit record ID
        """
        try:
            audit_id = str(uuid4())
            timestamp = datetime.now()
            
            audit_record = {
                "audit_id": audit_id,
                "timestamp": timestamp.isoformat(),
                "event_type": event_type,
                "severity": severity,
                "event_data": self._sanitize_context(event_data),
                "record_type": "system_event"
            }
            
            self.audit_records.append(audit_record)
            
            # Log to application logger
            log_level_map = {
                "info": logging.INFO,
                "warning": logging.WARNING,
                "error": logging.ERROR,
                "critical": logging.CRITICAL
            }
            
            logger.log(
                log_level_map.get(severity, logging.INFO),
                f"System event: {event_type}",
                extra={
                    "audit_id": audit_id,
                    "event_type": event_type,
                    "severity": severity
                }
            )
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}", exc_info=True)
            return ""
    
    def get_audit_trail(self,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       rule_section: Optional[str] = None,
                       success_only: Optional[bool] = None,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail records with optional filtering.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            rule_section: Rule section filter
            success_only: Filter by success status
            limit: Maximum number of records to return
            
        Returns:
            List of audit records
        """
        try:
            filtered_records = self.audit_records.copy()
            
            # Apply filters
            if start_date:
                filtered_records = [
                    r for r in filtered_records
                    if datetime.fromisoformat(r["timestamp"]) >= start_date
                ]
            
            if end_date:
                filtered_records = [
                    r for r in filtered_records
                    if datetime.fromisoformat(r["timestamp"]) <= end_date
                ]
            
            if rule_section:
                filtered_records = [
                    r for r in filtered_records
                    if r.get("rule_section", "").startswith(rule_section)
                ]
            
            if success_only is not None:
                filtered_records = [
                    r for r in filtered_records
                    if r.get("success") == success_only
                ]
            
            # Sort by timestamp (newest first)
            filtered_records.sort(
                key=lambda x: x["timestamp"],
                reverse=True
            )
            
            # Apply limit
            if limit:
                filtered_records = filtered_records[:limit]
            
            return filtered_records
            
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}", exc_info=True)
            return []
    
    def get_violation_summary(self,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get summary of rule violations over a time period.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Violation summary
        """
        try:
            records = self.get_audit_trail(start_date=start_date, end_date=end_date)
            
            total_executions = len([r for r in records if "rule_section" in r])
            failed_executions = len([r for r in records if not r.get("success", True)])
            
            # Count violations by rule section
            violation_counts = {}
            for record in records:
                if not record.get("success", True) and "rule_section" in record:
                    section = record["rule_section"]
                    violation_counts[section] = violation_counts.get(section, 0) + 1
            
            # Count violation types
            violation_types = {}
            for record in records:
                for violation in record.get("violations", []):
                    violation_types[violation] = violation_types.get(violation, 0) + 1
            
            return {
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "summary": {
                    "total_executions": total_executions,
                    "successful_executions": total_executions - failed_executions,
                    "failed_executions": failed_executions,
                    "success_rate": (total_executions - failed_executions) / total_executions if total_executions > 0 else 0
                },
                "violations_by_section": violation_counts,
                "violation_types": violation_types
            }
            
        except Exception as e:
            logger.error(f"Error generating violation summary: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def export_audit_trail(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          format: str = "json") -> str:
        """
        Export audit trail to specified format.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            records = self.get_audit_trail(start_date=start_date, end_date=end_date)
            
            if format.lower() == "json":
                return json.dumps(records, indent=2, default=str)
            elif format.lower() == "csv":
                # Simple CSV export (in production, would use proper CSV library)
                if not records:
                    return "No records found"
                
                headers = list(records[0].keys())
                csv_lines = [",".join(headers)]
                
                for record in records:
                    values = [str(record.get(h, "")) for h in headers]
                    csv_lines.append(",".join(values))
                
                return "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting audit trail: {str(e)}", exc_info=True)
            return f"Export error: {str(e)}"
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context data for audit logging.
        
        Args:
            context: Raw context data
            
        Returns:
            Sanitized context data
        """
        try:
            # Remove sensitive information and ensure JSON serializable
            sanitized = {}
            
            for key, value in context.items():
                if key.lower() in ["password", "secret", "token", "key"]:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (str, int, float, bool, type(None))):
                    sanitized[key] = value
                elif isinstance(value, (list, dict)):
                    sanitized[key] = json.loads(json.dumps(value, default=str))
                else:
                    sanitized[key] = str(value)
            
            return sanitized
            
        except Exception as e:
            logger.warning(f"Error sanitizing context: {str(e)}")
            return {"sanitization_error": str(e)}
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics."""
        try:
            total_records = len(self.audit_records)
            rule_executions = len([r for r in self.audit_records if "rule_section" in r])
            system_events = len([r for r in self.audit_records if r.get("record_type") == "system_event"])
            
            if self.audit_records:
                oldest_record = min(self.audit_records, key=lambda x: x["timestamp"])
                newest_record = max(self.audit_records, key=lambda x: x["timestamp"])
            else:
                oldest_record = newest_record = None
            
            return {
                "total_records": total_records,
                "rule_executions": rule_executions,
                "system_events": system_events,
                "oldest_record": oldest_record["timestamp"] if oldest_record else None,
                "newest_record": newest_record["timestamp"] if newest_record else None
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {str(e)}", exc_info=True)
            return {"error": str(e)}

