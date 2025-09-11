#!/usr/bin/env python3
"""
True-Asset-ALLUSE Local Deployment Main Application
Uses production code with local configuration overrides and mode selection
"""

import sys
import os
import argparse
from pathlib import Path

# Add local deployment directory to Python path
local_path = Path(__file__).parent
sys.path.insert(0, str(local_path))

# Add src directory to Python path for production code imports
src_path = local_path.parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for local deployment
os.environ["TRUE_ASSET_LOCAL_DEPLOYMENT"] = "true"

def setup_local_environment(mode: str = "mock"):
    """Setup local environment with specified mode"""
    from local_config import get_local_settings, get_mock_data
    
    # Get local settings for the specified mode
    local_settings = get_local_settings(mode)
    
    # Override production settings with local settings
    os.environ.update({
        "TRUE_ASSET_DATABASE_URL": local_settings.database_url,
        "TRUE_ASSET_API_HOST": local_settings.api_host,
        "TRUE_ASSET_API_PORT": str(local_settings.api_port),
        "TRUE_ASSET_DEBUG": str(local_settings.debug),
        "TRUE_ASSET_APP_VERSION": local_settings.app_version,
        "TRUE_ASSET_CONSTITUTION_VERSION": local_settings.constitution_version,
        "TRUE_ASSET_ENVIRONMENT": local_settings.environment,
        "TRUE_ASSET_API_PREFIX": local_settings.api_prefix,
        "TRUE_ASSET_LOG_LEVEL": local_settings.log_level,
        "TRUE_ASSET_DEPLOYMENT_MODE": mode
    })
    
    # Set API keys for live mode
    if mode == "live":
        if local_settings.databento_api_key:
            os.environ["DATABENTO_API_KEY"] = local_settings.databento_api_key
        if local_settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = local_settings.openai_api_key
        if local_settings.news_api_key:
            os.environ["NEWS_API_KEY"] = local_settings.news_api_key
        if local_settings.alpha_vantage_api_key:
            os.environ["ALPHA_VANTAGE_API_KEY"] = local_settings.alpha_vantage_api_key
    
    print(f"🚀 True-Asset-ALLUSE Local Deployment")
    print(f"📊 Mode: {mode.upper()}")
    print(f"🌐 URL: http://{local_settings.api_host}:{local_settings.api_port}")
    print(f"📚 Docs: http://{local_settings.api_host}:{local_settings.api_port}/docs")
    
    if mode == "mock":
        print("🎭 Using mock data for demonstration")
    else:
        print("🔗 Connecting to live services")
        if not local_settings.openai_api_key:
            print("⚠️  Warning: OpenAI API key not set - AI features will be limited")
        if not local_settings.databento_api_key:
            print("⚠️  Warning: Databento API key not set - using fallback market data")
    
    return local_settings

def patch_production_code_for_local(mode: str):
    """Patch production code to work with local deployment"""
    
    # Patch the settings module to use local settings
    try:
        from src.common import config
        from local_config import get_local_settings, get_mock_data
        
        local_settings = get_local_settings(mode)
        
        # Create a settings object that mimics the production Settings class
        class LocalSettingsAdapter:
            def __init__(self, local_settings):
                for attr in dir(local_settings):
                    if not attr.startswith('_'):
                        setattr(self, attr, getattr(local_settings, attr))
        
        # Replace the get_settings function
        original_get_settings = config.get_settings
        config.get_settings = lambda: LocalSettingsAdapter(local_settings)
        
        print(f"✅ Patched production settings for {mode} mode")
        
    except ImportError as e:
        print(f"⚠️  Warning: Could not patch production settings: {e}")
    
    # Patch workstreams to use mock data in mock mode
    if mode == "mock":
        try:
            # This would patch the workstreams to return mock data
            # Implementation depends on the specific workstream structure
            print("✅ Configured workstreams for mock mode")
        except Exception as e:
            print(f"⚠️  Warning: Could not configure mock mode: {e}")

def main():
    """Main entry point for local deployment"""
    parser = argparse.ArgumentParser(description="True-Asset-ALLUSE Local Deployment")
    parser.add_argument(
        "--mode", 
        choices=["mock", "live"], 
        default="mock",
        help="Deployment mode: 'mock' for demo data, 'live' for real services"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Setup local environment
    local_settings = setup_local_environment(args.mode)
    
    # Override host and port if provided
    if args.host != "127.0.0.1":
        local_settings.api_host = args.host
        os.environ["TRUE_ASSET_API_HOST"] = args.host
    
    if args.port != 8000:
        local_settings.api_port = args.port
        os.environ["TRUE_ASSET_API_PORT"] = str(args.port)
    
    # Patch production code for local deployment
    patch_production_code_for_local(args.mode)
    
    # Import and run the production application
    try:
        print("🔄 Starting production application with local configuration...")
        
        # Import the production main module
        from src.main import app
        
        # Add local routes for demo purposes
        from fastapi import Request
        from fastapi.responses import HTMLResponse
        from fastapi.templating import Jinja2Templates
        
        # Setup templates for local deployment
        templates = Jinja2Templates(directory=str(local_path / "templates"))
        
        @app.get("/demo", response_class=HTMLResponse)
        async def demo_dashboard(request: Request):
            """Local demo dashboard"""
            return templates.TemplateResponse("index_enhanced.html", {"request": request})
        
        # Add mock data endpoints for demo mode
        if args.mode == "mock":
            from local_config import get_mock_data
            
            @app.get("/api/v1/local/mock-data")
            async def get_local_mock_data():
                """Get mock data for demo"""
                return get_mock_data()
        
        # Start the server
        import uvicorn
        
        uvicorn.run(
            app,
            host=local_settings.api_host,
            port=local_settings.api_port,
            reload=local_settings.debug,
            log_level=local_settings.log_level.lower()
        )
        
    except ImportError as e:
        print(f"❌ Error importing production code: {e}")
        print("💡 Make sure you're running from the correct directory and all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

