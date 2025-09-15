#!/usr/bin/env python3
"""
True-Asset-ALLUSE Real Build System

This build system properly uses the actual source code from /src
instead of generating fake inline code.
"""

import os
import sys
import shutil
import json
import time
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
import logging

class RealTrueAssetBuilder:
    """Build system that uses the actual True-Asset-ALLUSE source code"""
    
    def __init__(self, mode="mock"):
        self.mode = mode
        self.build_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.project_root = Path(__file__).parent.parent
        self.local_deployment_dir = Path(__file__).parent
        self.dist_dir = self.local_deployment_dir / "dist"
        self.logs_dir = self.local_deployment_dir / "logs"
        self.db_dir = self.local_deployment_dir / "database"
        
        # Setup logging
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"build_{self.build_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log(self, message):
        """Log a message with timestamp"""
        self.logger.info(message)
        
    def create_directories(self):
        """Create necessary build directories"""
        self.log("📁 Creating build directories...")
        
        directories = [
            self.dist_dir,
            self.logs_dir,
            self.db_dir,
            self.dist_dir / "src",
            self.dist_dir / "templates",
            self.dist_dir / "static"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"   ✅ Created: {directory}")
            
    def validate_source_code(self):
        """Validate that the source code exists and is properly structured"""
        self.log("🔍 Validating source code structure...")
        
        required_files = [
            self.project_root / "src" / "main.py",
            self.project_root / "src" / "common" / "config.py",
            self.project_root / "src" / "common" / "database.py",
            self.project_root / "src" / "ws6_user_interface" / "dashboard" / "dashboard_app.py"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                raise Exception(f"Required source file not found: {file_path}")
            self.log(f"   ✅ Found: {file_path.relative_to(self.project_root)}")
            
        # Check for workstreams
        src_dir = self.project_root / "src"
        workstreams = []
        for item in src_dir.iterdir():
            if item.is_dir() and item.name.startswith("ws"):
                workstreams.append(item.name)
                
        self.log(f"   🔍 Detected workstreams: {', '.join(sorted(workstreams))}")
        return workstreams
        
    def copy_source_code(self):
        """Copy the actual source code to the build directory"""
        self.log("📋 Copying source code...")
        
        src_source = self.project_root / "src"
        src_dest = self.dist_dir / "src"
        
        # Remove existing src directory in dist
        if src_dest.exists():
            shutil.rmtree(src_dest)
            
        # Copy the entire src directory
        shutil.copytree(src_source, src_dest)
        self.log(f"   ✅ Copied source code: {src_source} -> {src_dest}")
        
        # Copy templates
        templates_src = self.project_root / "local-deployment" / "templates"
        templates_dst = self.dist_dir / "templates"
        if templates_src.exists():
            self.log("📄 Copying HTML templates...")
            shutil.copytree(templates_src, templates_dst, dirs_exist_ok=True)
            self.log(f"   ✅ Copied templates: {templates_src} -> {templates_dst}")
        
        # Copy integrated application
        integrated_app_src = self.project_root / "local-deployment" / "integrated_app.py"
        integrated_app_dst = self.dist_dir / "integrated_app.py"
        if integrated_app_src.exists():
            self.log("🔗 Copying integrated application...")
            shutil.copy2(integrated_app_src, integrated_app_dst)
            self.log(f"   ✅ Copied integrated app: {integrated_app_src} -> {integrated_app_dst}")
            
    def install_dependencies(self):
        """Install Python dependencies"""
        self.log("📦 Installing dependencies...")
        
        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        requirements_file = self.local_deployment_dir / "requirements.txt"
        if not requirements_file.exists():
            self.log("   ⚠️  No requirements.txt found, creating basic one...")
            self.create_basic_requirements()
            
        # Install base requirements
        pip_flags = [] if in_venv else ["--user"]
        cmd = [sys.executable, "-m", "pip", "install"] + pip_flags + ["-r", str(requirements_file)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to install dependencies: {result.stderr}")
            
        self.log("   ✅ Dependencies installed")
        
    def create_basic_requirements(self):
        """Create a basic requirements.txt file for local deployment"""
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0",
            "pydantic-settings>=2.0.0",
            "sqlalchemy>=2.0.0",
            "alembic>=1.12.0",
            "psycopg2-binary>=2.9.0",
            "redis>=5.0.0",
            "celery>=5.3.0",
            "python-multipart>=0.0.6",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-dotenv>=1.0.0",
            "requests>=2.31.0",
            "httpx>=0.25.0",
            "websockets>=12.0",
            "jinja2>=3.1.0",  # For template rendering
            "aiofiles>=23.0.0"  # For static file serving
        ]
        
        if self.mode == "live":
            requirements.extend([
                "openai>=1.3.7",
                "newsapi-python>=0.2.6",
                "ib-insync>=0.9.86"
            ])
            
        requirements_file = self.local_deployment_dir / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(requirements))
            
    def create_local_config(self):
        """Create local configuration for deployment"""
        self.log("⚙️  Creating local configuration...")
        
        config = {
            "mode": self.mode,
            "build_id": self.build_id,
            "environment": "local",
            "debug": True,
            "api_host": "127.0.0.1",
            "api_port": 8000,
            "api_prefix": "/api/v1",
            "database_url": f"sqlite:///{self.db_dir}/true_asset_alluse.db",
            "log_level": "INFO",
            "app_version": "1.0.0",
            "constitution_version": "1.3"
        }
        
        config_file = self.dist_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.log(f"   ✅ Configuration created: {config_file}")
        return config
        
    def setup_database(self):
        """Setup SQLite database with demo data"""
        self.log("🗄️  Setting up database...")
        
        db_file = self.db_dir / "true_asset_alluse.db"
        
        # Create database connection
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        try:
            # Create portfolio table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL,
                    market_value REAL,
                    pnl REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert demo data
            demo_data = [
                ("GOOGL", 25, 2500.00, 2800.00, 70000.00, 7500.00),
                ("NVDA", 40, 400.00, 500.00, 20000.00, 4000.00),
                ("TSLA", 75, 200.00, 250.00, 18750.00, 3750.00),
                ("AAPL", 100, 150.00, 175.50, 17550.00, 2550.00),
                ("MSFT", 50, 300.00, 350.00, 17500.00, 2500.00)
            ]
            
            cursor.executemany("""
                INSERT OR REPLACE INTO portfolio 
                (symbol, quantity, avg_price, current_price, market_value, pnl)
                VALUES (?, ?, ?, ?, ?, ?)
            """, demo_data)
            
            conn.commit()
            self.log("   ✅ Database setup completed")
            
        finally:
            conn.close()
            
    def create_launcher_script(self):
        """Create a launcher script that uses the real main.py"""
        self.log("🚀 Creating launcher script...")
        
        launcher_content = f'''#!/usr/bin/env python3
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
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = config["database_url"]
os.environ["API_HOST"] = config["api_host"]
os.environ["API_PORT"] = str(config["api_port"])

# Import and run the real application
if __name__ == "__main__":
    import uvicorn
    from src.main import app
    
    print("🚀 True-Asset-ALLUSE Starting...")
    print(f"📊 Mode: {{config['mode'].upper()}}")
    print(f"🌐 URL: http://{{config['api_host']}}:{{config['api_port']}}")
    print(f"📚 API Docs: http://{{config['api_host']}}:{{config['api_port']}}/docs")
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
'''
        
        launcher_file = self.dist_dir / "app.py"
        with open(launcher_file, 'w') as f:
            f.write(launcher_content)
            
        # Make it executable
        os.chmod(launcher_file, 0o755)
        self.log(f"   ✅ Launcher script created: {launcher_file}")
        
    def run_tests(self):
        """Run build validation tests"""
        self.log("🧪 Running build validation tests...")
        
        # Test 1: Check if source files exist
        src_dir = self.dist_dir / "src"
        if not src_dir.exists():
            raise Exception("Source directory not found in build")
            
        main_file = src_dir / "main.py"
        if not main_file.exists():
            raise Exception("main.py not found in build")
            
        self.log("   ✅ Source files validation passed")
        
        # Test 2: Check database
        db_file = self.db_dir / "true_asset_alluse.db"
        if not db_file.exists():
            raise Exception("Database file not found")
            
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM portfolio")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.log(f"   ✅ Database test passed ({count} portfolio entries)")
        
        # Test 3: Check configuration
        config_file = self.dist_dir / "config.json"
        if not config_file.exists():
            raise Exception("Configuration file not found")
            
        with open(config_file) as f:
            config = json.load(f)
            
        required_keys = ["mode", "build_id", "api_host", "api_port"]
        for key in required_keys:
            if key not in config:
                raise Exception(f"Missing configuration key: {key}")
                
        self.log("   ✅ Configuration validation passed")
        
    def build(self):
        """Execute the complete build process"""
        start_time = time.time()
        
        try:
            self.log("🏗️  Starting True-Asset-ALLUSE REAL build process...")
            self.log(f"📋 Build ID: {self.build_id}")
            self.log(f"🎯 Mode: {self.mode}")
            self.log("")
            
            # Build phases
            self.create_directories()
            workstreams = self.validate_source_code()
            self.copy_source_code()
            self.install_dependencies()
            config = self.create_local_config()
            self.setup_database()
            self.create_launcher_script()
            self.run_tests()
            
            build_time = time.time() - start_time
            
            self.log("")
            self.log("🎉 Build completed successfully!")
            self.log(f"⏱️  Total build time: {build_time:.2f} seconds")
            self.log(f"📦 Artifacts location: {self.dist_dir}")
            self.log(f"🗄️  Database location: {self.db_dir}")
            self.log(f"📝 Build log saved: {self.logs_dir}/build_{self.build_id}.log")
            self.log("")
            self.log("🚀 To run the application:")
            self.log(f"   cd {self.dist_dir}")
            self.log("   python3 app.py")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Build failed: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="True-Asset-ALLUSE Real Build System")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock",
                       help="Deployment mode (default: mock)")
    
    args = parser.parse_args()
    
    builder = RealTrueAssetBuilder(mode=args.mode)
    success = builder.build()
    
    sys.exit(0 if success else 1)

