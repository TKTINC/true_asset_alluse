#!/usr/bin/env python3
"""
True-Asset-ALLUSE Integrated Web Application

This module provides a unified web interface that combines the FastAPI backend
with professional HTML templates for a complete wealth management platform.

This version is designed to work with the actual source structure and can be
used for both local development and cloud deployment.
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Import the main FastAPI app
from main import app as fastapi_app

# Setup paths
src_dir = Path(__file__).parent
templates_dir = src_dir / "ws6_user_interface" / "dashboard" / "templates"

# Setup templates
templates = Jinja2Templates(directory=str(templates_dir))

# Database helper functions
def ensure_database_exists():
    """Ensure database exists and create it if it doesn't."""
    # For source version, use a local database in the project root
    db_path = src_dir.parent / "database" / "true_asset_alluse.db"
    
    if not db_path.exists():
        print("🗄️  Database not found, creating...")
        # Create database directory
        db_path.parent.mkdir(exist_ok=True)
        
        # Create and populate database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create portfolio table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL NOT NULL,
                market_value REAL NOT NULL,
                pnl REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sample portfolio data
        portfolio_data = [
            ("GOOGL", 50, 2800.00, 3100.00, 155000, 15000),
            ("NVDA", 100, 450.00, 520.00, 52000, 7000),
            ("TSLA", 80, 250.00, 290.00, 23200, 3200),
            ("AAPL", 200, 180.00, 195.00, 39000, 3000),
            ("MSFT", 150, 350.00, 380.00, 57000, 4500),
            ("AMZN", 30, 3200.00, 3400.00, 102000, 6000),
            ("META", 60, 320.00, 350.00, 21000, 1800),
            ("NFLX", 40, 400.00, 450.00, 18000, 2000),
            ("AMD", 120, 100.00, 115.00, 13800, 1800),
            ("CRM", 50, 220.00, 240.00, 12000, 1000)
        ]
        
        cursor.executemany("""
            INSERT INTO portfolio (symbol, quantity, avg_price, current_price, market_value, pnl)
            VALUES (?, ?, ?, ?, ?, ?)
        """, portfolio_data)
        
        conn.commit()
        conn.close()
        print("✅ Database created and populated with sample data")
    
    return str(db_path)

def get_db_connection():
    """Get database connection."""
    db_path = ensure_database_exists()
    return sqlite3.connect(db_path)

def get_portfolio_data():
    """Get portfolio data from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, quantity, avg_price, current_price, market_value, pnl
        FROM portfolio
        ORDER BY market_value DESC
    """)
    
    holdings = []
    for row in cursor.fetchall():
        symbol, quantity, avg_price, current_price, market_value, pnl = row
        pnl_percent = (pnl / (market_value - pnl)) * 100 if (market_value - pnl) > 0 else 0
        
        holdings.append({
            'symbol': symbol,
            'quantity': quantity,
            'avg_price': avg_price,
            'current_price': current_price,
            'market_value': market_value,
            'pnl': pnl,
            'pnl_percent': pnl_percent
        })
    
    conn.close()
    
    # Calculate totals
    total_value = sum(h['market_value'] for h in holdings)
    total_pnl = sum(h['pnl'] for h in holdings)
    total_invested = total_value - total_pnl
    total_pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    return {
        'holdings': holdings,
        'total_value': total_value,
        'total_pnl': total_pnl,
        'total_pnl_percent': total_pnl_percent,
        'total_invested': total_invested,
        'holdings_count': len(holdings)
    }

def get_system_status():
    """Get system status information."""
    return {
        'mode': 'MOCK',
        'status': 'Operational',
        'workstreams_active': 14,
        'last_update': 'Real-time',
        'build_version': '2.0.0'
    }

# Create the integrated app by mounting the FastAPI app
app = FastAPI(
    title="True-Asset-ALLUSE Integrated Platform",
    description="Professional Wealth Management Platform",
    version="2.0.0"
)

# Add web routes
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Professional landing page with portfolio overview."""
    portfolio = get_portfolio_data()
    system_status = get_system_status()
    
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "portfolio": portfolio,
        "system_status": system_status
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Real-time portfolio dashboard."""
    portfolio = get_portfolio_data()
    system_status = get_system_status()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "portfolio": portfolio,
        "system_status": system_status
    })

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_view(request: Request):
    """Detailed portfolio holdings view."""
    portfolio = get_portfolio_data()
    system_status = get_system_status()
    
    return templates.TemplateResponse("portfolio.html", {
        "request": request,
        "portfolio": portfolio,
        "system_status": system_status
    })

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_view(request: Request):
    """Advanced analytics and insights."""
    portfolio = get_portfolio_data()
    system_status = get_system_status()
    
    # Calculate analytics
    holdings = portfolio['holdings']
    best_performer = max(holdings, key=lambda x: x['pnl_percent']) if holdings else None
    avg_return = sum(h['pnl_percent'] for h in holdings) / len(holdings) if holdings else 0
    
    analytics = {
        'total_invested': portfolio['total_invested'],
        'best_performer': best_performer,
        'avg_return': avg_return,
        'risk_score': 7.2,  # Mock risk score
        'sharpe_ratio': 1.8,  # Mock Sharpe ratio
    }
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "portfolio": portfolio,
        "system_status": system_status,
        "analytics": analytics
    })

# Mount the original FastAPI app for API endpoints
app.mount("/api", fastapi_app)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mode": "MOCK",
        "database": "connected",
        "templates": "loaded"
    }

if __name__ == "__main__":
    print("🚀 True-Asset-ALLUSE Integrated Platform Starting...")
    print("📊 Mode: MOCK")
    print("🌐 Web Interface: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/api/docs")
    print("📊 Dashboard: http://127.0.0.1:8000/dashboard")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "integrated_web_app:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )

