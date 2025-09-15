#!/usr/bin/env python3
"""
True-Asset-ALLUSE Local Launcher

This script launches the real True-Asset-ALLUSE application
using the actual source code from /src
"""

import os
import sys
import json
from pathlib import Path

# Add the dist directory to Python path
dist_dir = Path(__file__).parent
sys.path.insert(0, str(dist_dir))

# Load configuration
config_file = dist_dir / "config.json"
with open(config_file) as f:
    config = json.load(f)

# Set environment variables
os.environ["TRUE_ASSET_MODE"] = config["mode"]
os.environ["TRUE_ASSET_DEBUG"] = "true"
os.environ["TRUE_ASSET_DATABASE_URL"] = config["database_url"]
os.environ["TRUE_ASSET_API_HOST"] = config["api_host"]
os.environ["TRUE_ASSET_API_PORT"] = str(config["api_port"])

# Import and run the real application
if __name__ == "__main__":
    import uvicorn
    from src.main import app
    
    print("🚀 True-Asset-ALLUSE Starting...")
    print(f"📊 Mode: {config['mode'].upper()}")
    print(f"🌐 URL: http://{config['api_host']}:{config['api_port']}")
    print(f"📚 API Docs: http://{config['api_host']}:{config['api_port']}/docs")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    uvicorn.run(
        app,
        host=config["api_host"],
        port=config["api_port"],
        log_level=config["log_level"].lower(),
        reload=config["debug"]
    )
