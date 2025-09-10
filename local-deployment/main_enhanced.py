"""
True-Asset-ALLUSE Enhanced Local Deployment
Main application with real service integrations
"""

import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, List

from config_enhanced import config, DEFAULT_SYMBOLS
from services.ibkr_service import ibkr_service
from services.databento_service import databento_service
from services.openai_service import openai_service
from services.news_service import news_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="Enhanced local deployment with real service integrations"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Data models
class ChatMessage(BaseModel):
    message: str

class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    action: str
    order_type: str

# Application state
app_state = {
    "system_status": "initializing",
    "last_portfolio_update": None,
    "last_market_update": None,
    "last_news_update": None,
    "portfolio_data": {},
    "market_data": {},
    "news_data": {},
    "volatility_data": {},
    "service_health": {}
}

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting True-Asset-ALLUSE Enhanced Local Deployment")
    
    # Connect to services
    await ibkr_service.connect()
    await databento_service.connect()
    await openai_service.connect()
    await news_service.connect()
    
    # Start background tasks
    asyncio.create_task(update_portfolio_data())
    asyncio.create_task(update_market_data())
    asyncio.create_task(update_news_data())
    asyncio.create_task(update_service_health())
    
    app_state["system_status"] = "running"
    logger.info("System is now running")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down True-Asset-ALLUSE")
    await ibkr_service.disconnect()

# Background tasks
async def update_portfolio_data():
    """Periodically update portfolio data"""
    while True:
        logger.info("Updating portfolio data...")
        app_state["portfolio_data"] = await ibkr_service.get_portfolio_summary()
        app_state["last_portfolio_update"] = datetime.now().isoformat()
        await asyncio.sleep(config.portfolio_refresh_interval)

async def update_market_data():
    """Periodically update market data"""
    while True:
        logger.info("Updating market data...")
        app_state["volatility_data"] = await databento_service.get_volatility_data()
        
        # Update quotes for key symbols
        market_quotes = {}
        for symbol in DEFAULT_SYMBOLS:
            market_quotes[symbol] = await databento_service.get_real_time_quote(symbol)
        
        app_state["market_data"] = market_quotes
        app_state["last_market_update"] = datetime.now().isoformat()
        await asyncio.sleep(config.market_data_refresh_interval)

async def update_news_data():
    """Periodically update news data"""
    while True:
        logger.info("Updating news data...")
        app_state["news_data"] = await news_service.get_market_sentiment_summary()
        app_state["last_news_update"] = datetime.now().isoformat()
        await asyncio.sleep(config.news_refresh_interval)

async def update_service_health():
    """Periodically update service health status"""
    while True:
        logger.info("Updating service health...")
        app_state["service_health"] = {
            "ibkr": await ibkr_service.health_check(),
            "databento": await databento_service.health_check(),
            "openai": await openai_service.health_check(),
            "news": await news_service.health_check()
        }
        await asyncio.sleep(config.health_check_interval)

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main dashboard"""
    return templates.TemplateResponse("index_enhanced.html", {"request": request})

@app.get("/api/v1/system-status")
async def get_system_status() -> Dict[str, Any]:
    """Get current system status and data"""
    return {
        "system_status": app_state["system_status"],
        "service_health": app_state["service_health"],
        "last_updates": {
            "portfolio": app_state["last_portfolio_update"],
            "market": app_state["last_market_update"],
            "news": app_state["last_news_update"]
        }
    }

@app.get("/api/v1/portfolio")
async def get_portfolio() -> Dict[str, Any]:
    """Get portfolio data"""
    return app_state["portfolio_data"]

@app.get("/api/v1/market-data")
async def get_market_data() -> Dict[str, Any]:
    """Get market data"""
    return {
        "quotes": app_state["market_data"],
        "volatility": app_state["volatility_data"]
    }

@app.get("/api/v1/news-sentiment")
async def get_news_sentiment() -> Dict[str, Any]:
    """Get news and sentiment data"""
    return app_state["news_data"]

@app.post("/api/v1/chat")
async def chat_with_ai(message: ChatMessage) -> Dict[str, Any]:
    """Chat with the AI assistant"""
    context_data = {
        "portfolio": app_state["portfolio_data"],
        "market": app_state["volatility_data"]
    }
    
    response = await openai_service.chat_response(message.message, context_data)
    return response

@app.get("/api/v1/ai-analysis/portfolio")
async def get_ai_portfolio_analysis() -> Dict[str, str]:
    """Get AI-powered portfolio analysis"""
    analysis = await openai_service.get_portfolio_analysis(app_state["portfolio_data"])
    return {"analysis": analysis}

@app.get("/api/v1/ai-analysis/risk")
async def get_ai_risk_assessment() -> Dict[str, str]:
    """Get AI-powered risk assessment"""
    assessment = await openai_service.get_risk_assessment(
        app_state["portfolio_data"],
        app_state["volatility_data"]
    )
    return {"assessment": assessment}

@app.post("/api/v1/place-order")
async def place_order(order: OrderRequest) -> Dict[str, Any]:
    """Place a paper trading order"""
    if not config.paper_trading_only:
        raise HTTPException(status_code=403, detail="Live trading not enabled in this demo")
    
    # Simplified contract creation for demo
    contract_data = {"symbol": order.symbol, "sec_type": "STK"}
    order_data = order.dict()
    
    result = await ibkr_service.place_paper_order(contract_data, order_data)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

# Main entry point for local execution
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "main_enhanced:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
        log_level="info"
    )


