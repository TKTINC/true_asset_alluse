"""
Local Deployment Configuration for True-Asset-ALLUSE
Extends production configuration with local overrides and mode selection
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Base directory
BASE_DIR = Path(__file__).parent

class LocalSettings:
    """Local deployment settings that can work with production code"""
    
    # Local deployment specific settings
    deployment_mode: str = "mock"  # "mock" or "live"
    local_deployment: bool = True
    
    # Database settings (use SQLite for local)
    database_url: str = f"sqlite:///{BASE_DIR}/data/true_asset_alluse.db"
    
    # API settings for local
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    debug: bool = True
    app_version: str = "1.0.0-local"
    constitution_version: str = "1.3"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    
    # Mock data settings
    mock_portfolio_value: float = 1247850.00
    mock_daily_pnl: float = 12450.00
    mock_positions_count: int = 8
    
    # Live service settings (only used in live mode)
    databento_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    # IBKR settings for paper trading
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497  # Paper trading port
    ibkr_client_id: int = 1
    paper_trading_only: bool = True
    
    # Service refresh intervals (seconds)
    portfolio_refresh_interval: int = 30
    market_data_refresh_interval: int = 15
    news_refresh_interval: int = 300  # 5 minutes
    health_check_interval: int = 60
    
    # News API settings
    news_enabled: bool = True
    news_sources: str = "bloomberg,reuters,cnbc"

# Global settings instance
_local_settings: Optional[LocalSettings] = None

def get_local_settings(mode: str = "mock") -> LocalSettings:
    """Get local settings with specified mode"""
    global _local_settings
    
    if _local_settings is None:
        _local_settings = LocalSettings()
    
    # Override mode
    _local_settings.deployment_mode = mode
    
    # Load environment variables for live mode
    if mode == "live":
        _local_settings.databento_api_key = os.getenv("DATABENTO_API_KEY")
        _local_settings.openai_api_key = os.getenv("OPENAI_API_KEY")
        _local_settings.news_api_key = os.getenv("NEWS_API_KEY")
        _local_settings.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    return _local_settings

# Default symbols for demo
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "NFLX"]

# Mock data for demo mode
MOCK_PORTFOLIO_DATA = {
    "total_value": 1247850.00,
    "daily_pnl": 12450.00,
    "daily_pnl_percent": 1.01,
    "portfolio_delta": 0.234,
    "active_positions": 8,
    "positions": [
        {
            "symbol": "AAPL",
            "sec_type": "STK",
            "position": 500,
            "market_value": 187500.00,
            "unrealized_pnl": 2500.00
        },
        {
            "symbol": "MSFT",
            "sec_type": "STK", 
            "position": 300,
            "market_value": 142800.00,
            "unrealized_pnl": 1800.00
        },
        {
            "symbol": "GOOGL",
            "sec_type": "STK",
            "position": 200,
            "market_value": 156000.00,
            "unrealized_pnl": -800.00
        },
        {
            "symbol": "TSLA",
            "sec_type": "STK",
            "position": 400,
            "market_value": 98400.00,
            "unrealized_pnl": 3200.00
        },
        {
            "symbol": "NVDA",
            "sec_type": "STK",
            "position": 150,
            "market_value": 134250.00,
            "unrealized_pnl": 4250.00
        },
        {
            "symbol": "AMZN",
            "sec_type": "STK",
            "position": 250,
            "market_value": 167500.00,
            "unrealized_pnl": 1500.00
        },
        {
            "symbol": "META",
            "sec_type": "STK",
            "position": 180,
            "market_value": 89100.00,
            "unrealized_pnl": -900.00
        },
        {
            "symbol": "NFLX",
            "sec_type": "STK",
            "position": 120,
            "market_value": 72300.00,
            "unrealized_pnl": -100.00
        }
    ],
    "last_updated": "2024-12-19T10:30:00Z",
    "data_source": "Mock_Data"
}

MOCK_MARKET_DATA = {
    "AAPL": {"price": 375.00, "change": 2.50, "change_percent": 0.67, "volume": 45678900},
    "MSFT": {"price": 476.00, "change": 1.80, "change_percent": 0.38, "volume": 23456789},
    "GOOGL": {"price": 780.00, "change": -3.20, "change_percent": -0.41, "volume": 12345678},
    "TSLA": {"price": 246.00, "change": 8.40, "change_percent": 3.53, "volume": 67890123},
    "NVDA": {"price": 895.00, "change": 12.50, "change_percent": 1.42, "volume": 34567890},
    "AMZN": {"price": 670.00, "change": 4.20, "change_percent": 0.63, "volume": 19876543},
    "META": {"price": 495.00, "change": -2.10, "change_percent": -0.42, "volume": 28765432},
    "NFLX": {"price": 602.50, "change": -1.50, "change_percent": -0.25, "volume": 15432109}
}

MOCK_NEWS_DATA = {
    "overall_sentiment": "positive",
    "sentiment_score": 0.15,
    "confidence": 0.75,
    "article_count": 15,
    "positive_articles": 8,
    "negative_articles": 3,
    "neutral_articles": 4,
    "positive_percentage": 53.3,
    "negative_percentage": 20.0,
    "top_categories": [
        {"category": "general", "count": 8},
        {"category": "earnings", "count": 4},
        {"category": "monetary_policy", "count": 3}
    ],
    "high_impact_news": [
        {
            "headline": "Federal Reserve maintains current interest rate policy",
            "description": "The Fed decided to keep rates unchanged, citing stable inflation trends",
            "sentiment": {"classification": "neutral", "compound_score": 0.05},
            "impact_score": 0.8
        },
        {
            "headline": "Tech sector shows strong earnings growth",
            "description": "Major technology companies report better than expected quarterly results",
            "sentiment": {"classification": "positive", "compound_score": 0.6},
            "impact_score": 0.7
        }
    ],
    "timestamp": "2024-12-19T10:30:00Z",
    "data_source": "Mock_Data"
}

MOCK_VOLATILITY_DATA = {
    "vix": 18.45,
    "vix_change": -0.85,
    "market_regime": "normal",
    "volatility_percentile": 35.2,
    "expected_move": 1.8,
    "timestamp": "2024-12-19T10:30:00Z",
    "data_source": "Mock_Data"
}

def get_mock_data() -> Dict[str, Any]:
    """Get all mock data for demo mode"""
    return {
        "portfolio": MOCK_PORTFOLIO_DATA,
        "market": MOCK_MARKET_DATA,
        "news": MOCK_NEWS_DATA,
        "volatility": MOCK_VOLATILITY_DATA
    }

# Local Paths
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(exist_ok=True)

