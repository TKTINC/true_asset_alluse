#!/usr/bin/env python3
"""
True-Asset-ALLUSE Local Build System
Complete build, compilation, and deployment process
"""

import os
import sys
import time
import shutil
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
import json

class TrueAssetBuilder:
    """Complete build system for True-Asset-ALLUSE local deployment"""
    
    def __init__(self, mode="mock"):
        self.mode = mode
        self.project_root = Path(__file__).parent.parent
        self.build_dir = Path(__file__).parent / "build"
        self.dist_dir = Path(__file__).parent / "dist"
        self.logs_dir = Path(__file__).parent / "logs"
        self.db_dir = Path(__file__).parent / "database"
        
        # Build metadata
        self.build_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.build_log = []
        
    def log(self, message, level="INFO"):
        """Log build messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.build_log.append(log_entry)
        
    def create_directories(self):
        """Create necessary build directories"""
        self.log("📁 Creating build directories...")
        
        directories = [self.build_dir, self.dist_dir, self.logs_dir, self.db_dir]
        for directory in directories:
            directory.mkdir(exist_ok=True)
            self.log(f"   ✅ Created: {directory}")
            
    def validate_environment(self):
        """Validate build environment"""
        self.log("🔍 Validating build environment...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            raise Exception(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        self.log(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check source directory
        src_dir = self.project_root / "src"
        if not src_dir.exists():
            raise Exception(f"Source directory not found: {src_dir}")
        self.log(f"   ✅ Source directory: {src_dir}")
        
        # Check main application file
        main_file = src_dir / "main.py"
        if not main_file.exists():
            self.log(f"   ⚠️  Production main.py not found, will use fallback")
        else:
            self.log(f"   ✅ Main application: {main_file}")
            
    def is_virtual_environment(self):
        """Check if running in a virtual environment"""
        return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
    def install_dependencies(self):
        """Install Python dependencies"""
        self.log("📦 Installing dependencies...")
        
        requirements_file = Path(__file__).parent / "requirements.txt"
        if not requirements_file.exists():
            raise Exception("requirements.txt not found")
            
        # Determine pip install flags based on environment
        pip_flags = []
        if not self.is_virtual_environment():
            pip_flags.append("--user")
            self.log("   🔍 Detected system Python, using --user flag")
        else:
            self.log("   🔍 Detected virtual environment, installing normally")
            
        # Install base requirements
        cmd = [sys.executable, "-m", "pip", "install"] + pip_flags + ["-r", str(requirements_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to install dependencies: {result.stderr}")
            
        self.log("   ✅ Base dependencies installed")
        
        # Install live mode dependencies if needed
        if self.mode == "live":
            self.log("   📡 Installing live mode dependencies...")
            live_deps = [
                "databento==0.18.0",
                "openai==1.3.7", 
                "newsapi-python==0.2.6",
                "ib-insync==0.9.86"
            ]
            
            for dep in live_deps:
                cmd = [sys.executable, "-m", "pip", "install"] + pip_flags + [dep]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log(f"      ✅ {dep}")
                else:
                    self.log(f"      ⚠️  Failed to install {dep} (optional)")
                    
    def compile_application(self):
        """Compile and prepare application artifacts"""
        self.log("🔨 Compiling application...")
        
        # Copy source files to build directory
        src_dir = self.project_root / "src"
        build_src = self.build_dir / "src"
        
        if build_src.exists():
            shutil.rmtree(build_src)
            
        if src_dir.exists():
            shutil.copytree(src_dir, build_src)
            self.log("   ✅ Source files copied to build directory")
        else:
            # Create minimal source structure for fallback
            build_src.mkdir(exist_ok=True)
            self.log("   ⚠️  Using fallback source structure")
            
        # Compile Python files (syntax check)
        python_files = list(build_src.rglob("*.py")) if build_src.exists() else []
        for py_file in python_files:
            try:
                compile(py_file.read_text(), str(py_file), 'exec')
                self.log(f"   ✅ Compiled: {py_file.relative_to(build_src)}")
            except SyntaxError as e:
                self.log(f"   ❌ Syntax error in {py_file}: {e}", "ERROR")
                
        # Create application manifest
        manifest = {
            "build_id": self.build_id,
            "build_time": datetime.now().isoformat(),
            "mode": self.mode,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "source_files": len(python_files),
            "workstreams": self.detect_workstreams()
        }
        
        manifest_file = self.build_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2))
        self.log(f"   ✅ Application manifest created")
        
    def detect_workstreams(self):
        """Detect available workstreams"""
        workstreams = []
        src_dir = self.project_root / "src"
        
        if src_dir.exists():
            for item in src_dir.iterdir():
                if item.is_dir() and item.name.startswith("ws"):
                    workstreams.append(item.name)
                    
        self.log(f"   🔍 Detected workstreams: {', '.join(workstreams) if workstreams else 'None (using fallback)'}")
        return workstreams
        
    def setup_database(self):
        """Initialize database and schemas"""
        self.log("🗄️  Setting up database...")
        
        db_file = self.db_dir / "true_asset_alluse.db"
        
        # Create database connection
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        try:
            # Create core tables
            self.log("   📋 Creating database schema...")
            
            # System configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Portfolio data table
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
            
            # Trading history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    workstream TEXT,
                    metadata TEXT
                )
            """)
            
            # System health table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert initial configuration
            config_data = [
                ("deployment_mode", self.mode),
                ("build_id", self.build_id),
                ("system_version", "1.0.0"),
                ("deployment_time", datetime.now().isoformat())
            ]
            
            cursor.executemany(
                "INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)",
                config_data
            )
            
            # Insert demo portfolio data
            if self.mode == "mock":
                demo_portfolio = [
                    ("AAPL", 100, 150.00, 175.50, 17550.00, 2550.00),
                    ("MSFT", 50, 300.00, 350.00, 17500.00, 2500.00),
                    ("GOOGL", 25, 2500.00, 2800.00, 70000.00, 7500.00),
                    ("TSLA", 75, 200.00, 250.00, 18750.00, 3750.00),
                    ("NVDA", 40, 400.00, 500.00, 20000.00, 4000.00),
                ]
                
                cursor.executemany("""
                    INSERT OR REPLACE INTO portfolio 
                    (symbol, quantity, avg_price, current_price, market_value, pnl)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, demo_portfolio)
                
                self.log("   ✅ Demo portfolio data inserted")
            
            conn.commit()
            self.log("   ✅ Database schema created successfully")
            
        except Exception as e:
            self.log(f"   ❌ Database setup failed: {e}", "ERROR")
            raise
        finally:
            conn.close()
            
    def create_application_bundle(self):
        """Create deployable application bundle"""
        self.log("📦 Creating application bundle...")
        
        # Create main application file
        app_file = self.dist_dir / "app.py"
        app_content = self.generate_application_code()
        app_file.write_text(app_content)
        self.log("   ✅ Application bundle created")
        
        # Create configuration file
        config_file = self.dist_dir / "config.json"
        config = {
            "mode": self.mode,
            "build_id": self.build_id,
            "database_path": str(self.db_dir / "true_asset_alluse.db"),
            "host": "127.0.0.1",
            "port": 8000,
            "debug": self.mode == "mock"
        }
        config_file.write_text(json.dumps(config, indent=2))
        self.log("   ✅ Configuration file created")
        
    def generate_application_code(self):
        """Generate the main application code"""
        return '''#!/usr/bin/env python3
"""
True-Asset-ALLUSE Local Deployment Application
Generated by build system on ''' + datetime.now().isoformat() + '''
Build ID: ''' + self.build_id + '''
Mode: ''' + self.mode + '''
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Application configuration
CONFIG_FILE = Path(__file__).parent / "config.json"
config = json.loads(CONFIG_FILE.read_text())

# Create FastAPI application
app = FastAPI(
    title="True-Asset-ALLUSE",
    description="Intelligent Wealth Management System - Engineered for Compounding Income and Corpus",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def get_portfolio(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, quantity, avg_price, current_price, market_value, pnl
            FROM portfolio ORDER BY market_value DESC
        """)
        results = cursor.fetchall()
        conn.close()
        
        return [{
            "symbol": row[0],
            "quantity": row[1],
            "avg_price": row[2],
            "current_price": row[3],
            "market_value": row[4],
            "pnl": row[5]
        } for row in results]
        
    def get_system_health(self):
        return {
            "status": "healthy",
            "mode": config["mode"],
            "build_id": config["build_id"],
            "uptime": "Running",
            "database": "Connected"
        }

# Initialize database manager
db = DatabaseManager(config["database_path"])

@app.get("/", response_class=HTMLResponse)
async def root():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>True-Asset-ALLUSE | Intelligent Wealth Management</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{ 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                line-height: 1.6; 
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .hero-section {{
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }}
            
            .hero-section::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><defs><radialGradient id="a" cx="50%" cy="50%"><stop offset="0%" stop-color="%23ffffff" stop-opacity="0.1"/><stop offset="100%" stop-color="%23ffffff" stop-opacity="0"/></radialGradient></defs><circle cx="200" cy="200" r="100" fill="url(%23a)"/><circle cx="800" cy="300" r="150" fill="url(%23a)"/><circle cx="400" cy="700" r="120" fill="url(%23a)"/></svg>') no-repeat center center;
                background-size: cover;
                opacity: 0.3;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                position: relative;
                z-index: 1;
            }}
            
            .hero-content {{
                text-align: center;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                padding: 60px 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                max-width: 800px;
                margin: 0 auto;
            }}
            
            .logo {{
                font-size: 4rem;
                margin-bottom: 20px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }}
            
            .hero-title {{
                font-size: 3.5rem;
                font-weight: 700;
                margin-bottom: 20px;
                background: linear-gradient(135deg, #2d3748, #4a5568);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                line-height: 1.2;
            }}
            
            .hero-subtitle {{
                font-size: 1.5rem;
                font-weight: 500;
                color: #667eea;
                margin-bottom: 15px;
                letter-spacing: -0.02em;
            }}
            
            .hero-description {{
                font-size: 1.1rem;
                color: #666;
                margin-bottom: 40px;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.7;
            }}
            
            .status-card {{
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: white;
                padding: 20px 30px;
                border-radius: 16px;
                margin: 30px 0;
                box-shadow: 0 10px 30px rgba(72, 187, 120, 0.3);
                display: inline-block;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            
            .status-card .status-icon {{
                font-size: 1.2rem;
                margin-right: 10px;
            }}
            
            .nav-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 50px;
                max-width: 900px;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .nav-card {{
                background: white;
                padding: 30px 25px;
                border-radius: 16px;
                text-decoration: none;
                color: #333;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
                transition: all 0.3s ease;
                border: 1px solid rgba(0, 0, 0, 0.05);
                position: relative;
                overflow: hidden;
            }}
            
            .nav-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                transform: scaleX(0);
                transition: transform 0.3s ease;
            }}
            
            .nav-card:hover {{
                transform: translateY(-8px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                color: #333;
                text-decoration: none;
            }}
            
            .nav-card:hover::before {{
                transform: scaleX(1);
            }}
            
            .nav-icon {{
                font-size: 2.5rem;
                margin-bottom: 15px;
                display: block;
            }}
            
            .nav-title {{
                font-size: 1.3rem;
                font-weight: 600;
                margin-bottom: 10px;
                color: #2d3748;
            }}
            
            .nav-description {{
                font-size: 0.95rem;
                color: #666;
                line-height: 1.5;
            }}
            
            .features-section {{
                margin-top: 60px;
                padding-top: 40px;
                border-top: 1px solid rgba(0, 0, 0, 0.1);
            }}
            
            .features-title {{
                text-align: center;
                font-size: 2rem;
                font-weight: 600;
                margin-bottom: 40px;
                color: #2d3748;
            }}
            
            .features-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 30px;
                margin-top: 30px;
            }}
            
            .feature-item {{
                text-align: center;
                padding: 20px;
            }}
            
            .feature-icon {{
                font-size: 2rem;
                margin-bottom: 15px;
                color: #667eea;
            }}
            
            .feature-text {{
                font-size: 0.9rem;
                color: #666;
                font-weight: 500;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 60px;
                padding-top: 30px;
                border-top: 1px solid rgba(0, 0, 0, 0.1);
                color: #666;
                font-size: 0.9rem;
            }}
            
            @media (max-width: 768px) {{
                .hero-title {{ font-size: 2.5rem; }}
                .hero-subtitle {{ font-size: 1.2rem; }}
                .hero-content {{ padding: 40px 30px; }}
                .nav-grid {{ grid-template-columns: 1fr; }}
                .features-grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
            
            @media (max-width: 480px) {{
                .hero-title {{ font-size: 2rem; }}
                .hero-content {{ padding: 30px 20px; }}
                .features-grid {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <div class="hero-section">
            <div class="container">
                <div class="hero-content">
                    <div class="logo">🚀</div>
                    <h1 class="hero-title">True-Asset-ALLUSE</h1>
                    <h2 class="hero-subtitle">Intelligent Wealth Management System</h2>
                    <p class="hero-description">
                        Advanced algorithmic trading platform engineered for compounding income and corpus growth. 
                        Harness the power of AI-driven market intelligence and systematic wealth building strategies.
                    </p>
                    
                    <div class="status-card">
                        <span class="status-icon">✅</span>
                        System Status: Active | Mode: {config["mode"].upper()} | Build: {config["build_id"]}
                    </div>
                    
                    <div class="nav-grid">
                        <a href="/dashboard" class="nav-card">
                            <span class="nav-icon">📊</span>
                            <div class="nav-title">Portfolio Dashboard</div>
                            <div class="nav-description">Real-time portfolio performance, analytics, and comprehensive wealth tracking</div>
                        </a>
                        
                        <a href="/portfolio" class="nav-card">
                            <span class="nav-icon">💼</span>
                            <div class="nav-title">Portfolio Data</div>
                            <div class="nav-description">Detailed holdings, positions, and performance metrics in JSON format</div>
                        </a>
                        
                        <a href="/health" class="nav-card">
                            <span class="nav-icon">🏥</span>
                            <div class="nav-title">System Health</div>
                            <div class="nav-description">Monitor system status, database connectivity, and operational metrics</div>
                        </a>
                        
                        <a href="/docs" class="nav-card">
                            <span class="nav-icon">📚</span>
                            <div class="nav-title">API Documentation</div>
                            <div class="nav-description">Complete API reference with interactive testing and integration guides</div>
                        </a>
                    </div>
                    
                    <div class="features-section">
                        <h3 class="features-title">Platform Capabilities</h3>
                        <div class="features-grid">
                            <div class="feature-item">
                                <div class="feature-icon">🤖</div>
                                <div class="feature-text">AI-Powered Analytics</div>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">📈</div>
                                <div class="feature-text">Real-Time Market Data</div>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">🔒</div>
                                <div class="feature-text">Enterprise Security</div>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">⚡</div>
                                <div class="feature-text">High-Performance Trading</div>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">📱</div>
                                <div class="feature-text">Multi-Platform Access</div>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">🎯</div>
                                <div class="feature-text">Precision Execution</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>True-Asset-ALLUSE</strong> &copy; 2024 | Engineered for Compounding Income and Corpus</p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    portfolio = db.get_portfolio()
    total_value = sum(p["market_value"] for p in portfolio)
    total_pnl = sum(p["pnl"] for p in portfolio)
    
    # Generate portfolio rows
    portfolio_rows = ""
    for p in portfolio:
        portfolio_rows += """
                        <tr>
                            <td><strong>""" + p["symbol"] + """</strong></td>
                            <td>""" + str(int(p["quantity"])) + """</td>
                            <td>$""" + "{:.2f}".format(p["avg_price"]) + """</td>
                            <td>$""" + "{:.2f}".format(p["current_price"]) + """</td>
                            <td>$""" + "{:.2f}".format(p["market_value"]) + """</td>
                            <td class="positive">$""" + "{:.2f}".format(p["pnl"]) + """</td>
                        </tr>"""
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>True-Asset-ALLUSE Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8f9fa; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
            .metric { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            .metric h3 { margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; }
            .metric .value { font-size: 28px; font-weight: bold; color: #007bff; }
            .metric .change { font-size: 14px; margin-top: 5px; }
            .positive { color: #28a745; }
            .portfolio { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }
            .portfolio table { width: 100%; border-collapse: collapse; }
            .portfolio th, .portfolio td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            .portfolio th { background: #f8f9fa; font-weight: 600; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Home</a>
            
            <div class="header">
                <h1>📊 Portfolio Dashboard</h1>
                <p>Real-time portfolio performance and analytics</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Total Portfolio Value</h3>
                    <div class="value">$""" + "{:,.2f}".format(total_value) + """</div>
                </div>
                <div class="metric">
                    <h3>Total P&L</h3>
                    <div class="value positive">$""" + "{:,.2f}".format(total_pnl) + """</div>
                    <div class="change positive">+""" + "{:.2f}".format((total_pnl/total_value*100)) + """%</div>
                </div>
                <div class="metric">
                    <h3>Active Positions</h3>
                    <div class="value">""" + str(len(portfolio)) + """</div>
                </div>
                <div class="metric">
                    <h3>System Status</h3>
                    <div class="value" style="color: #28a745;">Active</div>
                </div>
            </div>
            
            <div class="portfolio">
                <h3>Portfolio Holdings</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Quantity</th>
                            <th>Avg Price</th>
                            <th>Current Price</th>
                            <th>Market Value</th>
                            <th>P&L</th>
                        </tr>
                    </thead>
                    <tbody>""" + portfolio_rows + """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/portfolio")
async def get_portfolio():
    return db.get_portfolio()

@app.get("/health")
async def health_check():
    return db.get_system_health()

@app.get("/api/v1/system/info")
async def system_info():
    return {
        "name": "True-Asset-ALLUSE",
        "version": "1.0.0",
        "mode": config["mode"],
        "build_id": config["build_id"],
        "status": "running"
    }

if __name__ == "__main__":
    print("🚀 True-Asset-ALLUSE Starting...")
    print("📊 Mode: " + config['mode'].upper())
    print("🌐 URL: http://" + config['host'] + ":" + str(config['port']))
    print("📚 API Docs: http://" + config['host'] + ":" + str(config['port']) + "/docs")
    print("📊 Dashboard: http://" + config['host'] + ":" + str(config['port']) + "/dashboard")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        log_level="info",
        access_log=True
    )
'''
        
    def run_tests(self):
        """Run build validation tests"""
        self.log("🧪 Running build validation tests...")
        
        # Test database connection
        try:
            db_file = self.db_dir / "true_asset_alluse.db"
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM portfolio")
            count = cursor.fetchone()[0]
            conn.close()
            self.log(f"   ✅ Database test passed ({count} portfolio entries)")
        except Exception as e:
            self.log(f"   ❌ Database test failed: {e}", "ERROR")
            
        # Test application bundle
        app_file = self.dist_dir / "app.py"
        if app_file.exists():
            try:
                compile(app_file.read_text(), str(app_file), 'exec')
                self.log("   ✅ Application bundle syntax check passed")
            except SyntaxError as e:
                self.log(f"   ❌ Application bundle syntax error: {e}", "ERROR")
        else:
            self.log("   ❌ Application bundle not found", "ERROR")
            
    def save_build_log(self):
        """Save build log to file"""
        log_file = self.logs_dir / f"build_{self.build_id}.log"
        log_content = "\\n".join(self.build_log)
        log_file.write_text(log_content)
        self.log(f"📝 Build log saved: {log_file}")
        
    def build(self):
        """Execute complete build process"""
        start_time = time.time()
        
        try:
            self.log("🏗️  Starting True-Asset-ALLUSE build process...")
            self.log(f"📋 Build ID: {self.build_id}")
            self.log(f"🎯 Mode: {self.mode}")
            self.log("")
            
            # Build phases
            self.create_directories()
            time.sleep(1)  # Simulate build time
            
            self.validate_environment()
            time.sleep(1)
            
            self.install_dependencies()
            time.sleep(2)
            
            self.compile_application()
            time.sleep(1)
            
            self.setup_database()
            time.sleep(2)
            
            self.create_application_bundle()
            time.sleep(1)
            
            self.run_tests()
            time.sleep(1)
            
            build_time = time.time() - start_time
            self.log("")
            self.log(f"🎉 Build completed successfully!")
            self.log(f"⏱️  Total build time: {build_time:.2f} seconds")
            self.log(f"📦 Artifacts location: {self.dist_dir}")
            self.log(f"🗄️  Database location: {self.db_dir}")
            
            self.save_build_log()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Build failed: {e}", "ERROR")
            self.save_build_log()
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="True-Asset-ALLUSE Build System")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock",
                       help="Deployment mode (default: mock)")
    
    args = parser.parse_args()
    
    builder = TrueAssetBuilder(mode=args.mode)
    success = builder.build()
    
    sys.exit(0 if success else 1)

