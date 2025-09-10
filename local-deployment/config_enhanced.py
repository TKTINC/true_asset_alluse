"""
True-Asset-ALLUSE Enhanced Local Configuration
Real Service Integrations for Working Financial System Demo
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field

# Base directory
BASE_DIR = Path(__file__).parent

class EnhancedLocalConfig(BaseSettings):
    """Enhanced configuration with real service integrations"""
    
    # Application Settings
    app_name: str = "True-Asset-ALLUSE Enhanced Local"
    app_version: str = "2.0.0"
    debug: bool = True
    
    # Server Configuration
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # Database Configuration (SQLite for local)
    database_url: str = f"sqlite:///{BASE_DIR}/data/true_asset_alluse_enhanced.db"
    
    # Interactive Brokers Configuration
    ibkr_enabled: bool = Field(default=False, description="Enable IBKR integration")
    ibkr_host: str = "localhost"
    ibkr_port: int = 7497  # Paper trading port (7496 for live)
    ibkr_client_id: int = 1
    paper_trading_only: bool = True
    ibkr_timeout: int = 30
    
    # Databento Market Data Configuration
    databento_enabled: bool = Field(default=False, description="Enable Databento integration")
    databento_api_key: Optional[str] = Field(default=None, env="DATABENTO_API_KEY")
    databento_dataset: str = "XNAS.ITCH"  # NASDAQ data
    real_time_enabled: bool = True
    
    # OpenAI Configuration
    openai_enabled: bool = Field(default=False, description="Enable OpenAI integration")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 1000
    ai_mock_mode: bool = True  # Will be set to False when OpenAI key is provided
    
    # News API Configuration
    news_enabled: bool = Field(default=False, description="Enable News API integration")
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")
    news_sources: str = "bloomberg,reuters,financial-times,cnbc"
    
    # Alpha Vantage Configuration (Backup market data)
    alpha_vantage_enabled: bool = Field(default=False, description="Enable Alpha Vantage integration")
    alpha_vantage_api_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    
    # Security Configuration
    secret_key: str = "enhanced-local-development-secret-key-not-for-production"
    access_token_expire_minutes: int = 30
    
    # Service Health Check Configuration
    health_check_interval: int = 60  # seconds
    max_retry_attempts: int = 3
    service_timeout: int = 10  # seconds
    
    # Data Refresh Configuration
    portfolio_refresh_interval: int = 5  # seconds
    market_data_refresh_interval: int = 1  # seconds
    news_refresh_interval: int = 300  # 5 minutes
    
    # Risk Management Configuration
    max_portfolio_delta: float = 0.5
    min_portfolio_delta: float = -0.5
    vix_escalation_threshold: float = 30.0
    
    # Mock Data Configuration (fallback when services unavailable)
    mock_portfolio_value: float = 1247850.00
    mock_daily_pnl: float = 12450.00
    mock_weekly_return: float = 0.85
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Auto-enable services based on API key availability
        if self.openai_api_key:
            self.openai_enabled = True
            self.ai_mock_mode = False
        
        if self.databento_api_key:
            self.databento_enabled = True
        
        if self.news_api_key:
            self.news_enabled = True
        
        if self.alpha_vantage_api_key:
            self.alpha_vantage_enabled = True
        
        # Create directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            BASE_DIR / "data",
            BASE_DIR / "logs",
            BASE_DIR / "static",
            BASE_DIR / "templates",
            BASE_DIR / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    @property
    def service_status(self) -> Dict[str, Any]:
        """Get current service configuration status"""
        return {
            "ibkr": {
                "enabled": self.ibkr_enabled,
                "mode": "paper" if self.paper_trading_only else "live",
                "host": f"{self.ibkr_host}:{self.ibkr_port}"
            },
            "databento": {
                "enabled": self.databento_enabled,
                "dataset": self.databento_dataset if self.databento_enabled else None
            },
            "openai": {
                "enabled": self.openai_enabled,
                "model": self.openai_model if self.openai_enabled else None,
                "mock_mode": self.ai_mock_mode
            },
            "news": {
                "enabled": self.news_enabled,
                "sources": self.news_sources.split(",") if self.news_enabled else []
            },
            "alpha_vantage": {
                "enabled": self.alpha_vantage_enabled
            }
        }
    
    @property
    def is_production_ready(self) -> bool:
        """Check if configuration is ready for production demo"""
        return (
            self.openai_enabled and 
            (self.databento_enabled or self.alpha_vantage_enabled) and
            self.news_enabled
        )

# Global configuration instance
config = EnhancedLocalConfig()

# Service URLs and Endpoints
SERVICE_ENDPOINTS = {
    "ibkr": {
        "paper_trading": "localhost:7497",
        "live_trading": "localhost:7496"
    },
    "databento": {
        "api_base": "https://hist.databento.com",
        "live_base": "https://live.databento.com"
    },
    "openai": {
        "api_base": "https://api.openai.com/v1"
    },
    "news_api": {
        "api_base": "https://newsapi.org/v2"
    },
    "alpha_vantage": {
        "api_base": "https://www.alphavantage.co"
    }
}

# Default symbols for demonstration
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "SPY", "QQQ"]

# Options chains for demonstration
DEFAULT_OPTIONS = [
    {"symbol": "AAPL", "strike": 175, "type": "PUT", "expiry": "2024-12-15"},
    {"symbol": "MSFT", "strike": 380, "type": "PUT", "expiry": "2025-01-19"},
    {"symbol": "GOOGL", "strike": 140, "type": "PUT", "expiry": "2024-12-22"},
    {"symbol": "TSLA", "strike": 250, "type": "CALL", "expiry": "2025-01-12"}
]

# System health thresholds
HEALTH_THRESHOLDS = {
    "api_response_time": 5.0,  # seconds
    "data_staleness": 300,     # seconds
    "error_rate": 0.05,        # 5%
    "memory_usage": 0.8        # 80%
}

