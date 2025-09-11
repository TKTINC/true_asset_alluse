#!/usr/bin/env python3
"""
True-Asset-ALLUSE Local Deployment Script
Deploys and runs the built application
"""

import os
import sys
import json
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

class TrueAssetDeployer:
    """Deployment manager for True-Asset-ALLUSE"""
    
    def __init__(self, mode="mock"):
        self.mode = mode
        self.deployment_dir = Path(__file__).parent
        self.dist_dir = self.deployment_dir / "dist"
        self.logs_dir = self.deployment_dir / "logs"
        self.pid_file = self.deployment_dir / "app.pid"
        
        # Deployment metadata
        self.deployment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log(self, message, level="INFO"):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
    def validate_build(self):
        """Validate that build artifacts exist"""
        self.log("🔍 Validating build artifacts...")
        
        required_files = [
            self.dist_dir / "app.py",
            self.dist_dir / "config.json"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                raise Exception(f"Required build artifact not found: {file_path}")
            self.log(f"   ✅ Found: {file_path.name}")
            
        # Validate configuration
        config_file = self.dist_dir / "config.json"
        config = json.loads(config_file.read_text())
        
        if config["mode"] != self.mode:
            self.log(f"   ⚠️  Build mode ({config['mode']}) differs from deployment mode ({self.mode})")
            
        self.log("   ✅ Build artifacts validated")
        return config
        
    def check_port_availability(self, port):
        """Check if the specified port is available"""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
            
    def stop_existing_deployment(self):
        """Stop any existing deployment"""
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                self.pid_file.unlink()
                self.log("   ✅ Stopped existing deployment")
            except (ProcessLookupError, ValueError):
                self.pid_file.unlink()
                self.log("   ✅ Cleaned up stale PID file")
        else:
            self.log("   ℹ️  No existing deployment found")
            
    def start_application(self, config):
        """Start the application server"""
        self.log("🚀 Starting True-Asset-ALLUSE application...")
        
        app_file = self.dist_dir / "app.py"
        
        # Check port availability
        port = config["port"]
        if not self.check_port_availability(port):
            self.log(f"   ⚠️  Port {port} is busy, trying alternative ports...")
            for alt_port in range(port + 1, port + 10):
                if self.check_port_availability(alt_port):
                    port = alt_port
                    config["port"] = port
                    # Update config file
                    config_file = self.dist_dir / "config.json"
                    config_file.write_text(json.dumps(config, indent=2))
                    break
            else:
                raise Exception("No available ports found")
                
        self.log(f"   🌐 Server will start on: http://{config['host']}:{port}")
        self.log(f"   📊 Dashboard: http://{config['host']}:{port}/dashboard")
        self.log(f"   📚 API Docs: http://{config['host']}:{port}/docs")
        
        # Start the application
        try:
            process = subprocess.Popen(
                [sys.executable, str(app_file)],
                cwd=str(self.dist_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Save PID
            self.pid_file.write_text(str(process.pid))
            
            # Wait a moment to check if it started successfully
            time.sleep(3)
            
            if process.poll() is None:
                self.log("   ✅ Application started successfully")
                self.log(f"   🆔 Process ID: {process.pid}")
                
                # Show startup output
                self.log("")
                self.log("📋 Application startup output:")
                self.log("=" * 50)
                
                # Read initial output
                try:
                    for _ in range(10):  # Read first 10 lines
                        line = process.stdout.readline()
                        if line:
                            print(line.strip())
                        else:
                            break
                except:
                    pass
                    
                self.log("=" * 50)
                self.log("")
                self.log("🎉 Deployment completed successfully!")
                self.log(f"🌐 Access your application at: http://{config['host']}:{port}")
                self.log("")
                self.log("To stop the application, run: python deploy.py --stop")
                
                return True
            else:
                error_output = process.stdout.read() if process.stdout else "No error output"
                raise Exception(f"Application failed to start: {error_output}")
                
        except Exception as e:
            if self.pid_file.exists():
                self.pid_file.unlink()
            raise Exception(f"Failed to start application: {e}")
            
    def stop_application(self):
        """Stop the running application"""
        self.log("🛑 Stopping True-Asset-ALLUSE application...")
        
        if not self.pid_file.exists():
            self.log("   ℹ️  No running application found")
            return True
            
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # Check if process still exists
                    time.sleep(1)
                except ProcessLookupError:
                    break
            else:
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                    
            self.pid_file.unlink()
            self.log("   ✅ Application stopped successfully")
            return True
            
        except (ProcessLookupError, ValueError):
            self.pid_file.unlink()
            self.log("   ✅ Cleaned up stale process")
            return True
        except Exception as e:
            self.log(f"   ❌ Error stopping application: {e}", "ERROR")
            return False
            
    def get_status(self):
        """Get deployment status"""
        self.log("📊 Checking deployment status...")
        
        if not self.pid_file.exists():
            self.log("   ❌ Application is not running")
            return False
            
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            
            # Try to get config
            config_file = self.dist_dir / "config.json"
            if config_file.exists():
                config = json.loads(config_file.read_text())
                self.log(f"   ✅ Application is running (PID: {pid})")
                self.log(f"   🌐 URL: http://{config['host']}:{config['port']}")
                self.log(f"   🎯 Mode: {config['mode']}")
                return True
            else:
                self.log(f"   ⚠️  Application running but config not found (PID: {pid})")
                return True
                
        except (ProcessLookupError, ValueError):
            self.pid_file.unlink()
            self.log("   ❌ Application is not running (cleaned up stale PID)")
            return False
            
    def deploy(self):
        """Execute deployment process"""
        try:
            self.log("🚀 Starting True-Asset-ALLUSE deployment...")
            self.log(f"📋 Deployment ID: {self.deployment_id}")
            self.log(f"🎯 Mode: {self.mode}")
            self.log("")
            
            # Validate build
            config = self.validate_build()
            
            # Stop existing deployment
            self.stop_existing_deployment()
            
            # Start application
            self.start_application(config)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Deployment failed: {e}", "ERROR")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="True-Asset-ALLUSE Deployment System")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock",
                       help="Deployment mode (default: mock)")
    parser.add_argument("--stop", action="store_true",
                       help="Stop the running application")
    parser.add_argument("--status", action="store_true",
                       help="Check deployment status")
    
    args = parser.parse_args()
    
    deployer = TrueAssetDeployer(mode=args.mode)
    
    if args.stop:
        success = deployer.stop_application()
    elif args.status:
        success = deployer.get_status()
    else:
        success = deployer.deploy()
    
    sys.exit(0 if success else 1)

