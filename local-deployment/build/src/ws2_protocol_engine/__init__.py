"""
WS2: Protocol Engine & Risk Management

This workstream implements the ATR-based risk management system with 4-level
protocol escalation that monitors positions and escalates risk management
based on market conditions.

Core Components:
- ATR Calculation Engine: Multi-source ATR calculation with fallbacks
- Protocol Escalation System: 4-level escalation (Normal→Enhanced→Recovery→Preservation)
- Roll Economics Calculator: Roll decision making and execution logic
- Circuit Breaker System: VIX-based safety mechanisms
- Risk Management Framework: Comprehensive risk monitoring and control

Integration with WS1:
- Uses Rules Engine for validation
- Leverages Protocol Engine rules from Constitution v1.3
- Integrates with audit trail for risk event logging
"""

from .atr import ATRCalculationEngine, ATRDataSource
from .escalation import ProtocolEscalationManager, ProtocolLevel
from .roll_economics import RollEconomicsCalculator
from .circuit_breakers import CircuitBreakerManager
from .protocol_engine import ProtocolEngine

__version__ = "1.0.0"
__all__ = [
    "ATRCalculationEngine",
    "ATRDataSource", 
    "ProtocolEscalationManager",
    "ProtocolLevel",
    "RollEconomicsCalculator",
    "CircuitBreakerManager",
    "ProtocolEngine"
]

