"""
Application Configuration

Centralized configuration management for True-Asset-ALLUSE using Pydantic settings.
All configuration values are loaded from environment variables with sensible defaults.
"""

import os
from functools import lru_cache
from typing import Optional, List
from enum import Enum

from pydantic import BaseSettings, Field, validator
from pydantic.networks import PostgresDsn, RedisDsn


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProtocolLevel(str, Enum):
    """Protocol escalation levels per Constitution."""
    NORMAL = "normal"
    ENHANCED = "enhanced"
    RECOVERY = "recovery"
    PRESERVATION = "preservation"


class Settings(BaseSettings):
    """Application settings."""
    
    # Application Settings
    app_name: str = Field(default="true-asset-alluse", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # Database Configuration
    database_url: PostgresDsn = Field(
        default="postgresql://postgres:password@localhost:5432/true_asset_alluse",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Interactive Brokers Configuration
    ibkr_host: str = Field(default="127.0.0.1", env="IBKR_HOST")
    ibkr_port: int = Field(default=7497, env="IBKR_PORT")
    ibkr_client_id: int = Field(default=1, env="IBKR_CLIENT_ID")
    ibkr_paper_trading: bool = Field(default=True, env="IBKR_PAPER_TRADING")
    ibkr_account_id: Optional[str] = Field(default=None, env="IBKR_ACCOUNT_ID")
    
    # Market Data Configuration
    market_data_provider: str = Field(default="ibkr", env="MARKET_DATA_PROVIDER")
    market_data_timeout: int = Field(default=30, env="MARKET_DATA_TIMEOUT")
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # Constitution Configuration
    constitution_version: str = Field(default="1.3", env="CONSTITUTION_VERSION")
    constitution_strict_mode: bool = Field(default=True, env="CONSTITUTION_STRICT_MODE")
    
    # Risk Management Configuration
    default_protocol_level: ProtocolLevel = Field(
        default=ProtocolLevel.NORMAL,
        env="DEFAULT_PROTOCOL_LEVEL"
    )
    max_position_size_percent: int = Field(default=100, env="MAX_POSITION_SIZE_PERCENT")
    atr_lookback_days: int = Field(default=20, env="ATR_LOOKBACK_DAYS")
    vix_circuit_breaker_level: float = Field(default=30.0, env="VIX_CIRCUIT_BREAKER_LEVEL")
    
    # Account Configuration
    initial_capital_minimum: int = Field(default=200000, env="INITIAL_CAPITAL_MINIMUM")
    gen_acc_fork_threshold: int = Field(default=100000, env="GEN_ACC_FORK_THRESHOLD")
    rev_acc_fork_threshold: int = Field(default=500000, env="REV_ACC_FORK_THRESHOLD")
    
    # Account Split Ratios (Constitution mandated)
    gen_acc_ratio: float = Field(default=0.40, description="Gen-Acc allocation ratio")
    rev_acc_ratio: float = Field(default=0.30, description="Rev-Acc allocation ratio")
    com_acc_ratio: float = Field(default=0.30, description="Com-Acc allocation ratio")
    
    # Monitoring & Alerting
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    datadog_api_key: Optional[str] = Field(default=None, env="DATADOG_API_KEY")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # AI Configuration (Advisory Only)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    ai_advisory_enabled: bool = Field(default=True, env="AI_ADVISORY_ENABLED")
    
    # Celery Configuration
    celery_broker_url: RedisDsn = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    celery_result_backend: RedisDsn = Field(
        default="redis://localhost:6379/2",
        env="CELERY_RESULT_BACKEND"
    )
    
    # Testing Configuration
    test_database_url: Optional[PostgresDsn] = Field(
        default=None,
        env="TEST_DATABASE_URL"
    )
    
    @validator("debug", pre=True)
    def parse_debug(cls, v):
        """Parse debug flag from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    @validator("constitution_strict_mode", pre=True)
    def parse_strict_mode(cls, v):
        """Parse strict mode flag from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    @validator("ibkr_paper_trading", pre=True)
    def parse_paper_trading(cls, v):
        """Parse paper trading flag from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    @validator("ai_advisory_enabled", pre=True)
    def parse_ai_advisory(cls, v):
        """Parse AI advisory flag from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    @validator("gen_acc_ratio", "rev_acc_ratio", "com_acc_ratio")
    def validate_account_ratios(cls, v, values):
        """Validate account allocation ratios sum to 1.0."""
        if "gen_acc_ratio" in values and "rev_acc_ratio" in values:
            total = values["gen_acc_ratio"] + values["rev_acc_ratio"] + v
            if abs(total - 1.0) > 0.001:  # Allow for floating point precision
                raise ValueError("Account ratios must sum to 1.0")
        return v
    
    @validator("max_position_size_percent")
    def validate_position_size(cls, v):
        """Validate position size percentage."""
        if not 1 <= v <= 100:
            raise ValueError("Position size must be between 1% and 100%")
        return v
    
    @validator("initial_capital_minimum")
    def validate_minimum_capital(cls, v):
        """Validate minimum capital requirement."""
        if v < 100000:  # $100K minimum per Constitution
            raise ValueError("Minimum capital must be at least $100,000")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Export commonly used settings
settings = get_settings()

