#!/usr/bin/env python3
"""
True-Asset-ALLUSE Local Deployment Main Application
Uses production code with local configuration overrides and mode selection
"""

import sys
import os
import argparse
from pathlib import Path

# Get the absolute paths
local_path = Path(__file__).parent.absolute()
project_root = local_path.parent.absolute()
src_path = project_root / "src"

# Debug path information
print(f"🔍 Local path: {local_path}")
print(f"🔍 Project root: {project_root}")
print(f"🔍 Src path: {src_path}")
print(f"🔍 Src exists: {src_path.exists()}")

# Add paths to Python path
sys.path.insert(0, str(local_path))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Verify src directory structure
if src_path.exists():
    print(f"✅ Found src directory")
    main_py = src_path / "main.py"
    if main_py.exists():
        print(f"✅ Found src/main.py")
    else:
        print(f"❌ src/main.py not found")
        print(f"📁 Contents of src/: {list(src_path.iterdir()) if src_path.exists() else 'N/A'}")
else:
    print(f"❌ src directory not found at {src_path}")
    print(f"📁 Contents of project root: {list(project_root.iterdir())}")

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
    
    # Try to import production settings
    try:
        # Try different import approaches
        try:
            from src.common import config
            print("✅ Successfully imported src.common.config")
        except ImportError:
            # Try importing from the project root
            import common.config as config
            print("✅ Successfully imported common.config")
        
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
        return True
        
    except ImportError as e:
        print(f"⚠️  Warning: Could not patch production settings: {e}")
        print(f"💡 Will run in simplified local mode")
        return False

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
    production_import_success = False
    try:
        print("🔄 Attempting to import production application...")
        
        # Try different import approaches
        try:
            from src.main import app
            print("✅ Successfully imported production app from src.main")
            production_import_success = True
        except ImportError:
            try:
                import main
                app = main.app
                print("✅ Successfully imported production app from main")
                production_import_success = True
            except ImportError:
                print("❌ Could not import production application")
                production_import_success = False
        
        if production_import_success:
            # Add local routes for demo purposes
            from fastapi import Request
            from fastapi.responses import HTMLResponse, JSONResponse
            
            @app.get("/demo", response_class=HTMLResponse)
            async def demo_dashboard(request: Request):
                """Local demo dashboard"""
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>True-Asset-ALLUSE Local Demo</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .header { text-align: center; margin-bottom: 30px; }
                        .status { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
                        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                        .metric { background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; }
                        .metric h3 { margin: 0 0 10px 0; color: #333; }
                        .metric .value { font-size: 24px; font-weight: bold; color: #007bff; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚀 True-Asset-ALLUSE</h1>
                            <h2>Intelligent Wealth Management System</h2>
                            <p>Running in """ + args.mode.upper() + """ mode</p>
                        </div>
                        
                        <div class="status">
                            <h3>✅ System Status: Active</h3>
                            <p>Production code successfully loaded and running locally</p>
                        </div>
                        
                        <div class="metrics">
                            <div class="metric">
                                <h3>Portfolio Value</h3>
                                <div class="value">$1,247,850</div>
                            </div>
                            <div class="metric">
                                <h3>Daily P&L</h3>
                                <div class="value">+$12,450</div>
                            </div>
                            <div class="metric">
                                <h3>Active Positions</h3>
                                <div class="value">8</div>
                            </div>
                            <div class="metric">
                                <h3>System Health</h3>
                                <div class="value">100%</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 30px; text-align: center;">
                            <p><strong>API Documentation:</strong> <a href="/docs">/docs</a></p>
                            <p><strong>Health Check:</strong> <a href="/health">/health</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            # Add mock data endpoints for demo mode
            if args.mode == "mock":
                from local_config import get_mock_data
                
                @app.get("/api/v1/local/mock-data")
                async def get_local_mock_data():
                    """Get mock data for demo"""
                    return get_mock_data()
        
    except Exception as e:
        print(f"❌ Error setting up production application: {e}")
        production_import_success = False
    
    # Fallback: Create a simple FastAPI app if production import fails
    if not production_import_success:
        print("🔄 Creating fallback local application...")
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import HTMLResponse, JSONResponse
            
            app = FastAPI(
                title="True-Asset-ALLUSE Local Demo",
                description="Local demonstration of True-Asset-ALLUSE system",
                version="1.0.0-local"
            )
            
            @app.get("/", response_class=HTMLResponse)
            async def root():
                return """
                <h1>True-Asset-ALLUSE Local Demo</h1>
                <p>Running in fallback mode</p>
                <p><a href="/demo">Demo Dashboard</a></p>
                <p><a href="/docs">API Documentation</a></p>
                """
            
            @app.get("/demo", response_class=HTMLResponse)
            async def demo_dashboard():
                return """
                <!DOCTYPE html>
                <html>
                <head><title>True-Asset-ALLUSE Demo</title></head>
                <body>
                    <h1>True-Asset-ALLUSE Demo</h1>
                    <p>This is a simplified local demo running in fallback mode.</p>
                    <p>The production code could not be imported, but this demonstrates the concept.</p>
                </body>
                </html>
                """
            
            @app.get("/health")
            async def health():
                return {"status": "healthy", "mode": "local-fallback"}
            
            print("✅ Fallback application created successfully")
            
        except Exception as e:
            print(f"❌ Error creating fallback application: {e}")
            sys.exit(1)
    
    # Start the server
    try:
        import uvicorn
        
        print(f"🚀 Starting server on http://{local_settings.api_host}:{local_settings.api_port}")
        print(f"📊 Demo Dashboard: http://{local_settings.api_host}:{local_settings.api_port}/demo")
        print(f"📚 API Docs: http://{local_settings.api_host}:{local_settings.api_port}/docs")
        print("")
        print("Press Ctrl+C to stop the server")
        print("")
        
        # Run the server with proper configuration
        uvicorn.run(
            app,
            host=local_settings.api_host,
            port=local_settings.api_port,
            reload=False,  # Disable reload to avoid import string issues
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Trying alternative server startup...")
        
        # Alternative startup method
        try:
            import uvicorn
            config = uvicorn.Config(
                app=app,
                host=local_settings.api_host,
                port=local_settings.api_port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            server.run()
        except Exception as e2:
            print(f"❌ Alternative startup also failed: {e2}")
            print("💡 Please check if port 8000 is already in use")
            sys.exit(1)

if __name__ == "__main__":
    main()

