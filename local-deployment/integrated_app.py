#!/usr/bin/env python3
"""
True-Asset-ALLUSE Integrated Application

This module creates a unified application that combines:
- FastAPI backend API (for data and business logic)
- Flask frontend dashboard (for web UI)
- Professional web interface with real data integration
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# Add the dist directory to Python path
dist_dir = Path(__file__).parent
sys.path.insert(0, str(dist_dir))

# Load configuration
config_file = dist_dir / "config.json"
with open(config_file) as f:
    config = json.load(f)

# Set environment variables
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = config["database_url"]
os.environ["API_HOST"] = config["api_host"]
os.environ["API_PORT"] = str(config["api_port"])

# Import the FastAPI app
from src.main import app as fastapi_app
from src.api.v1.router import api_router

# Create integrated application
app = FastAPI(
    title="True-Asset-ALLUSE Integrated Platform",
    description="Intelligent Wealth Management System with Web Interface",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory=str(dist_dir / "templates"))

# Database helper functions
def get_db_connection():
    """Get database connection."""
    db_path = Path(__file__).parent.parent / "database" / "true_asset_alluse.db"
    return sqlite3.connect(str(db_path))

def get_portfolio_data():
    """Get portfolio data from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, quantity, avg_price, current_price, market_value, pnl
        FROM portfolio
        ORDER BY market_value DESC
    """)
    
    portfolio = []
    total_value = 0
    total_pnl = 0
    
    for row in cursor.fetchall():
        symbol, quantity, avg_price, current_price, market_value, pnl = row
        portfolio.append({
            'symbol': symbol,
            'quantity': quantity,
            'avg_price': avg_price,
            'current_price': current_price,
            'market_value': market_value,
            'pnl': pnl,
            'pnl_percent': (pnl / (avg_price * quantity)) * 100 if avg_price and quantity else 0
        })
        total_value += market_value or 0
        total_pnl += pnl or 0
    
    conn.close()
    
    return {
        'holdings': portfolio,
        'total_value': total_value,
        'total_pnl': total_pnl,
        'total_pnl_percent': (total_pnl / (total_value - total_pnl)) * 100 if total_value > total_pnl else 0,
        'total_positions': len(portfolio)
    }

def get_system_status():
    """Get system status information."""
    return {
        'status': 'Active',
        'mode': config['mode'].upper(),
        'build_id': config['build_id'],
        'environment': 'development',
        'workstreams_active': 14,
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# Web Interface Routes
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Professional landing page."""
    portfolio = get_portfolio_data()
    system_status = get_system_status()
    
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "portfolio": portfolio,
        "system_status": system_status,
        "title": "True-Asset-ALLUSE | Intelligent Wealth Management"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    portfolio = get_portfolio_data()
    system_status = get_system_status()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "portfolio": portfolio,
        "system_status": system_status,
        "title": "Dashboard | True-Asset-ALLUSE"
    })

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio details page."""
    portfolio = get_portfolio_data()
    
    return templates.TemplateResponse("portfolio.html", {
        "request": request,
        "portfolio": portfolio,
        "title": "Portfolio | True-Asset-ALLUSE"
    })

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics and insights page."""
    portfolio = get_portfolio_data()
    
    # Calculate analytics
    analytics = {
        'best_performer': max(portfolio['holdings'], key=lambda x: x['pnl_percent']) if portfolio['holdings'] else None,
        'worst_performer': min(portfolio['holdings'], key=lambda x: x['pnl_percent']) if portfolio['holdings'] else None,
        'avg_return': sum(h['pnl_percent'] for h in portfolio['holdings']) / len(portfolio['holdings']) if portfolio['holdings'] else 0,
        'total_invested': portfolio['total_value'] - portfolio['total_pnl']
    }
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "portfolio": portfolio,
        "analytics": analytics,
        "title": "Analytics | True-Asset-ALLUSE"
    })

# API Routes (JSON responses)
@app.get("/api/portfolio")
async def api_portfolio():
    """API endpoint for portfolio data."""
    return get_portfolio_data()

@app.get("/api/system/status")
async def api_system_status():
    """API endpoint for system status."""
    return get_system_status()

@app.get("/api/health")
async def api_health():
    """API health check."""
    return {
        "status": "healthy",
        "service": "true-asset-alluse-integrated",
        "timestamp": datetime.now().isoformat()
    }

# Include the original FastAPI routes under /api/v1
app.mount("/api/v1", fastapi_app)

if __name__ == "__main__":
    print("🚀 True-Asset-ALLUSE Integrated Platform Starting...")
    print(f"📊 Mode: {config['mode'].upper()}")
    print(f"🌐 Web Interface: http://{config['api_host']}:{config['api_port']}")
    print(f"📚 API Docs: http://{config['api_host']}:{config['api_port']}/docs")
    print(f"📊 Dashboard: http://{config['api_host']}:{config['api_port']}/dashboard")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    uvicorn.run(
        app,
        host=config["api_host"],
        port=config["api_port"],
        log_level="info",
        reload=False
    )

