"""
Custom Exceptions for True-Asset-ALLUSE

Defines custom exception classes for different types of errors that can occur
in the True-Asset-ALLUSE system, providing structured error handling.
"""

from typing import Optional, Dict, Any


class TrueAssetException(Exception):
    """Base exception class for True-Asset-ALLUSE."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConstitutionViolationError(TrueAssetException):
    """Raised when a Constitution rule is violated."""
    
    def __init__(
        self,
        message: str,
        rule_section: str,
        violation_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="CONSTITUTION_VIOLATION",
            status_code=400,
            details={
                "rule_section": rule_section,
                "violation_details": violation_details or {}
            }
        )


class RiskManagementError(TrueAssetException):
    """Raised when risk management rules are violated."""
    
    def __init__(
        self,
        message: str,
        risk_level: str,
        current_metrics: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="RISK_MANAGEMENT_ERROR",
            status_code=400,
            details={
                "risk_level": risk_level,
                "current_metrics": current_metrics or {}
            }
        )


class AccountManagementError(TrueAssetException):
    """Raised when account management operations fail."""
    
    def __init__(
        self,
        message: str,
        account_id: Optional[str] = None,
        operation: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="ACCOUNT_MANAGEMENT_ERROR",
            status_code=400,
            details={
                "account_id": account_id,
                "operation": operation
            }
        )


class TradingEngineError(TrueAssetException):
    """Raised when trading engine operations fail."""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="TRADING_ENGINE_ERROR",
            status_code=400,
            details={
                "order_id": order_id,
                "symbol": symbol
            }
        )


class BrokerIntegrationError(TrueAssetException):
    """Raised when broker integration fails."""
    
    def __init__(
        self,
        message: str,
        broker: str = "IBKR",
        error_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="BROKER_INTEGRATION_ERROR",
            status_code=503,
            details={
                "broker": broker,
                "error_details": error_details or {}
            }
        )


class MarketDataError(TrueAssetException):
    """Raised when market data operations fail."""
    
    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        data_type: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="MARKET_DATA_ERROR",
            status_code=503,
            details={
                "symbol": symbol,
                "data_type": data_type
            }
        )


class ProtocolEscalationError(TrueAssetException):
    """Raised when protocol escalation fails."""
    
    def __init__(
        self,
        message: str,
        current_level: str,
        target_level: str,
        escalation_reason: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="PROTOCOL_ESCALATION_ERROR",
            status_code=400,
            details={
                "current_level": current_level,
                "target_level": target_level,
                "escalation_reason": escalation_reason
            }
        )


class StateManagementError(TrueAssetException):
    """Raised when state management operations fail."""
    
    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        target_state: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="STATE_MANAGEMENT_ERROR",
            status_code=400,
            details={
                "current_state": current_state,
                "target_state": target_state
            }
        )


class ValidationError(TrueAssetException):
    """Raised when data validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={
                "field": field,
                "value": str(value) if value is not None else None
            }
        )


class ConfigurationError(TrueAssetException):
    """Raised when configuration is invalid."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={
                "config_key": config_key
            }
        )


class DatabaseError(TrueAssetException):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details={
                "operation": operation,
                "table": table
            }
        )


class AuthenticationError(TrueAssetException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        auth_method: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details={
                "auth_method": auth_method
            }
        )


class AuthorizationError(TrueAssetException):
    """Raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details={
                "required_permission": required_permission
            }
        )

