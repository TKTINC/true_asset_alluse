#!/usr/bin/env python3
"""
Simple test server to verify FastAPI setup works
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Create a simple FastAPI app
app = FastAPI(title="True-Asset-ALLUSE Test Server")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>True-Asset-ALLUSE Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .success { color: green; font-size: 24px; }
        </style>
    </head>
    <body>
        <h1>🚀 True-Asset-ALLUSE</h1>
        <p class="success">✅ Server is working!</p>
        <p>This confirms your setup is correct.</p>
        <p><a href="/docs">API Documentation</a></p>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Test server is working"}

if __name__ == "__main__":
    print("🧪 Starting test server...")
    print("📊 Test page: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("")
    print("Press Ctrl+C to stop")
    print("")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

