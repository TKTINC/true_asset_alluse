"""
True-Asset-ALLUSE Local Configuration
Optimized for MacBook Air deployment
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database Configuration (SQLite for local deployment)
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/true_asset_alluse.db"

# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 8000
DEBUG = True

# Mock Data Configuration
MOCK_DATA_ENABLED = True
MOCK_PORTFOLIO_VALUE = 1247850.00
MOCK_DAILY_PNL = 12450.00
MOCK_WEEKLY_RETURN = 0.85

# AI Configuration (Optional - can work without OpenAI key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_ENABLED = bool(OPENAI_API_KEY)

# Security (Local development keys)
SECRET_KEY = "local-development-secret-key-not-for-production"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock Market Data
MOCK_POSITIONS = [
    {
        "symbol": "AAPL",
        "type": "Put",
        "strike": 175,
        "expiry": "Dec 15",
        "pnl": 425,
        "pnl_percent": 28.8,
        "delta": -0.35
    },
    {
        "symbol": "MSFT",
        "type": "Put",
        "strike": 380,
        "expiry": "Jan 19",
        "pnl": -125,
        "pnl_percent": -5.2,
        "delta": -0.28
    },
    {
        "symbol": "GOOGL",
        "type": "Put",
        "strike": 140,
        "expiry": "Dec 22",
        "pnl": 850,
        "pnl_percent": 42.1,
        "delta": -0.31
    },
    {
        "symbol": "TSLA",
        "type": "Call",
        "strike": 250,
        "expiry": "Jan 12",
        "pnl": 320,
        "pnl_percent": 15.6,
        "delta": 0.45
    }
]

# System Status
SYSTEM_STATUS = {
    "rules_engine": "Active",
    "constitution": "Compliant",
    "market_data": "Connected",
    "ai_assistant": "Advisory Mode" if AI_ENABLED else "Offline",
    "portfolio_delta": -0.28,
    "protocol_level": "Normal"
}

# Local Paths
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(exist_ok=True)

