"""
Protocol Escalation System

This module implements the 4-level protocol escalation system based on ATR breaches
as defined in Constitution v1.3 §6.Protocol-Engine.

Escalation Levels:
- Level 0: Normal operations (5-minute monitoring)
- Level 1: Enhanced monitoring (1-minute) at 1× ATR breach
- Level 2: Recovery mode (30-second) at 2× ATR breach
- Level 3: Preservation mode (real-time) at 3× ATR breach
"""

from .protocol_levels import ProtocolLevel, ProtocolState
from .escalation_manager import ProtocolEscalationManager
from .monitoring_system import MonitoringSystem
from .alert_system import AlertSystem

__all__ = [
    "ProtocolLevel",
    "ProtocolState", 
    "ProtocolEscalationManager",
    "MonitoringSystem",
    "AlertSystem"
]

