"""
True-Asset-ALLUSE Local Deployment
Main Application Entry Point
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
from datetime import datetime, timedelta
import local_config as config

# Initialize FastAPI app
app = FastAPI(
    title="True-Asset-ALLUSE Local",
    description="Intelligent Wealth Management Platform - Local Deployment",
    version="1.0.0"
)

# Security
security = HTTPBearer(auto_error=False)

# Templates and Static Files
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str

class PortfolioData(BaseModel):
    total_value: float
    daily_pnl: float
    daily_pnl_percent: float
    weekly_return: float
    active_positions: int
    positions: List[Dict[str, Any]]
    system_status: Dict[str, str]

# Mock Authentication
DEMO_USERS = {
    "admin": "password",
    "demo": "demo123",
    "investor": "investor"
}

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Simple token verification for demo purposes"""
    if not credentials:
        return None
    # In a real app, verify JWT token here
    return {"username": "demo_user"}

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main application"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    """Authenticate user"""
    if login_data.username in DEMO_USERS and DEMO_USERS[login_data.username] == login_data.password:
        return {
            "access_token": f"demo-token-{login_data.username}",
            "token_type": "bearer",
            "user": {
                "username": login_data.username,
                "role": "investor" if login_data.username == "investor" else "admin"
            }
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@app.get("/api/portfolio")
async def get_portfolio(user: Optional[dict] = Depends(verify_token)):
    """Get portfolio data"""
    return PortfolioData(
        total_value=config.MOCK_PORTFOLIO_VALUE,
        daily_pnl=config.MOCK_DAILY_PNL,
        daily_pnl_percent=round((config.MOCK_DAILY_PNL / config.MOCK_PORTFOLIO_VALUE) * 100, 2),
        weekly_return=config.MOCK_WEEKLY_RETURN,
        active_positions=len(config.MOCK_POSITIONS),
        positions=config.MOCK_POSITIONS,
        system_status=config.SYSTEM_STATUS
    )

@app.post("/api/chat")
async def chat_with_ai(message: ChatMessage, user: Optional[dict] = Depends(verify_token)):
    """Chat with AI Assistant"""
    
    # Mock AI responses based on common queries
    responses = {
        "portfolio": "Your portfolio is performing well today with a +$12,450 gain (+1.01%). All positions are within optimal risk parameters.",
        "aapl": "Your AAPL Dec 15 $175 Put is up +$425 (+28.8%). Based on current market conditions, rolling to January would be advantageous.",
        "risk": "Current portfolio delta is -0.28, within the target range of -0.15 to -0.45. Protocol Level is Normal with all systems active.",
        "performance": "Weekly return of +0.85% is tracking well above the target of 0.5-1.0%. Year-to-date performance is strong.",
        "system": "All systems are operational: Rules Engine (Active), Constitution v1.3 (Compliant), Market Data (Connected)."
    }
    
    # Simple keyword matching for demo
    query = message.message.lower()
    response = "I'm here to help with your portfolio questions. Try asking about portfolio performance, specific positions, or system status."
    
    for keyword, mock_response in responses.items():
        if keyword in query:
            response = mock_response
            break
    
    return {
        "response": response,
        "timestamp": datetime.now().isoformat(),
        "advisory_only": True
    }

@app.get("/api/system/status")
async def get_system_status():
    """Get system health status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": config.SYSTEM_STATUS,
        "uptime": "Local deployment - Always available"
    }

@app.get("/api/system/info")
async def get_system_info():
    """Get system information"""
    return {
        "name": "True-Asset-ALLUSE",
        "version": "1.0.0-local",
        "description": "Intelligent Wealth Management Platform",
        "tagline": "Autopilot for Wealth. Engineered for compounding income and corpus.",
        "deployment": "Local MacBook Air",
        "ai_enabled": config.AI_ENABLED,
        "mock_data": config.MOCK_DATA_ENABLED
    }

if __name__ == "__main__":
    print("🚀 Starting True-Asset-ALLUSE Local Deployment")
    print(f"📊 Portfolio Value: ${config.MOCK_PORTFOLIO_VALUE:,.2f}")
    print(f"💰 Daily P&L: +${config.MOCK_DAILY_PNL:,.2f}")
    print(f"🤖 AI Assistant: {'Enabled' if config.AI_ENABLED else 'Mock Mode'}")
    print(f"🌐 Access URL: http://{config.API_HOST}:{config.API_PORT}")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level="info"
    )

