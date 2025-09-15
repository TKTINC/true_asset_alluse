#!/usr/bin/env python3
"""
True-Asset-ALLUSE Health Check and Verification Script
Comprehensive health monitoring and system verification
"""

import os
import sys
import time
import json
import sqlite3
import requests
import subprocess
from pathlib import Path
from datetime import datetime

class TrueAssetHealthChecker:
    """Health check and verification manager for True-Asset-ALLUSE"""
    
    def __init__(self, mode="mock"):
        self.mode = mode
        self.deployment_dir = Path(__file__).parent
        self.dist_dir = self.deployment_dir / "dist"
        self.db_dir = self.deployment_dir / "database"
        self.logs_dir = self.deployment_dir / "logs"
        
        # Configuration
        self.config_file = self.dist_dir / "config.json"
        self.db_file = self.db_dir / "true_asset_alluse.db"
        
        # Default server configuration
        self.host = "127.0.0.1"
        self.port = 8000
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Health check endpoints
        self.health_endpoints = [
            {"path": "/", "name": "Home Page", "expected_status": 200},
            {"path": "/health", "name": "Health Check", "expected_status": 200},
            {"path": "/portfolio", "name": "Portfolio API", "expected_status": 200},
            {"path": "/dashboard", "name": "Dashboard", "expected_status": 200},
            {"path": "/api/v1/system/info", "name": "System Info API", "expected_status": 200},
            {"path": "/docs", "name": "API Documentation", "expected_status": 200}
        ]
        
        self.check_log = []
        
    def log(self, message, level="INFO"):
        """Log health check messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.check_log.append(log_entry)
        
    def load_configuration(self):
        """Load application configuration"""
        self.log("📋 Loading application configuration...")
        
        if not self.config_file.exists():
            raise Exception(f"Configuration file not found: {self.config_file}")
            
        try:
            config = json.loads(self.config_file.read_text())
            self.host = config.get("host", "127.0.0.1")
            self.port = config.get("port", 8000)
            self.base_url = f"http://{self.host}:{self.port}"
            
            self.log(f"   ✅ Configuration loaded")
            self.log(f"   🌐 Base URL: {self.base_url}")
            self.log(f"   🎯 Mode: {config.get('mode', 'unknown')}")
            
            return config
            
        except Exception as e:
            raise Exception(f"Failed to load configuration: {e}")
            
    def check_application_running(self):
        """Check if the application is running"""
        self.log("🔍 Checking if application is running...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("   ✅ Application is running and responding")
                return True
            else:
                self.log(f"   ❌ Application responding with status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"   ❌ Application not responding: {e}", "ERROR")
            return False
            
    def run_endpoint_health_checks(self):
        """Run health checks on all endpoints"""
        self.log("🏥 Running endpoint health checks...")
        
        results = {}
        healthy_count = 0
        
        for endpoint in self.health_endpoints:
            path = endpoint["path"]
            name = endpoint["name"]
            expected_status = endpoint["expected_status"]
            
            self.log(f"   🔍 Testing {name} ({path})...")
            
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == expected_status:
                    self.log(f"      ✅ {name} - Status: {response.status_code}, Time: {response_time:.3f}s")
                    results[path] = {
                        "name": name,
                        "status": "healthy",
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "content_length": len(response.content)
                    }
                    healthy_count += 1
                else:
                    self.log(f"      ❌ {name} - Expected: {expected_status}, Got: {response.status_code}", "ERROR")
                    results[path] = {
                        "name": name,
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "expected_status": expected_status,
                        "error": f"Unexpected status code"
                    }
                    
            except requests.exceptions.RequestException as e:
                self.log(f"      ❌ {name} - Connection error: {e}", "ERROR")
                results[path] = {
                    "name": name,
                    "status": "error",
                    "error": str(e)
                }
                
        self.log(f"   📊 Health check summary: {healthy_count}/{len(self.health_endpoints)} endpoints healthy")
        return results, healthy_count
        
    def check_database_health(self):
        """Check database connectivity and integrity"""
        self.log("🗄️  Checking database health...")
        
        if not self.db_file.exists():
            self.log("   ❌ Database file not found", "ERROR")
            return False
            
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT COUNT(*) FROM portfolio")
            portfolio_count = cursor.fetchone()[0]
            self.log(f"   ✅ Database connected - {portfolio_count} portfolio entries")
            
            # Test system configuration table
            cursor.execute("SELECT COUNT(*) FROM system_config")
            config_count = cursor.fetchone()[0]
            self.log(f"   ✅ System configuration - {config_count} entries")
            
            # Test data integrity - check for valid portfolio data
            cursor.execute("""
                SELECT COUNT(*) FROM portfolio 
                WHERE market_value > 0 AND quantity > 0
            """)
            valid_entries = cursor.fetchone()[0]
            self.log(f"   ✅ Data integrity - {valid_entries} valid portfolio entries")
            
            # Get top holdings
            cursor.execute("""
                SELECT symbol, SUM(market_value) as total_value 
                FROM portfolio 
                GROUP BY symbol 
                ORDER BY total_value DESC 
                LIMIT 3
            """)
            top_holdings = cursor.fetchall()
            
            self.log("   📊 Top holdings:")
            for symbol, value in top_holdings:
                self.log(f"      💰 {symbol}: ${value:,.2f}")
                
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"   ❌ Database health check failed: {e}", "ERROR")
            return False
            
    def run_performance_tests(self):
        """Run performance tests on key endpoints"""
        self.log("⚡ Running performance tests...")
        
        test_endpoints = ["/", "/portfolio", "/health"]
        performance_results = {}
        
        for endpoint in test_endpoints:
            url = f"{self.base_url}{endpoint}"
            response_times = []
            
            self.log(f"   🏃 Testing {endpoint} performance (5 requests)...")
            
            # Run 5 requests to get average response time
            for i in range(5):
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=5)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_times.append(end_time - start_time)
                        
                except requests.exceptions.RequestException:
                    pass
                    
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                performance_results[endpoint] = {
                    "avg_response_time": avg_time,
                    "max_response_time": max_time,
                    "min_response_time": min_time,
                    "requests_tested": len(response_times),
                    "success_rate": len(response_times) / 5
                }
                
                self.log(f"      ⏱️  Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
                
                # Performance warnings
                if avg_time > 1.0:
                    self.log(f"      ⚠️  Slow response time for {endpoint}", "WARNING")
                elif avg_time < 0.1:
                    self.log(f"      🚀 Excellent response time for {endpoint}")
            else:
                self.log(f"      ❌ No successful requests for {endpoint}", "ERROR")
                performance_results[endpoint] = {
                    "error": "No successful requests",
                    "success_rate": 0
                }
                
        return performance_results
        
    def check_system_resources(self):
        """Check system resource usage"""
        self.log("💻 Checking system resources...")
        
        try:
            # Check disk space
            disk_usage = os.statvfs(self.deployment_dir)
            free_space = disk_usage.f_bavail * disk_usage.f_frsize
            total_space = disk_usage.f_blocks * disk_usage.f_frsize
            used_percentage = ((total_space - free_space) / total_space) * 100
            
            self.log(f"   💾 Disk usage: {used_percentage:.1f}% ({free_space / (1024**3):.1f}GB free)")
            
            if used_percentage > 90:
                self.log("   ⚠️  High disk usage", "WARNING")
            
            # Check if application process is running
            try:
                result = subprocess.run(
                    ["ps", "aux"], 
                    capture_output=True, 
                    text=True
                )
                
                app_processes = [line for line in result.stdout.split('\n') if 'app.py' in line]
                
                if app_processes:
                    self.log(f"   🔄 Found {len(app_processes)} application process(es)")
                    for process in app_processes:
                        parts = process.split()
                        if len(parts) >= 11:
                            pid = parts[1]
                            cpu = parts[2]
                            mem = parts[3]
                            self.log(f"      📊 PID {pid}: CPU {cpu}%, Memory {mem}%")
                else:
                    self.log("   ⚠️  No application processes found", "WARNING")
                    
            except Exception as e:
                self.log(f"   ⚠️  Could not check process status: {e}", "WARNING")
                
            return True
            
        except Exception as e:
            self.log(f"   ❌ System resource check failed: {e}", "ERROR")
            return False
            
    def generate_health_report(self, config, endpoint_results, healthy_count, db_healthy, performance_results):
        """Generate comprehensive health report"""
        self.log("📊 Generating health report...")
        
        report = {
            "health_check_info": {
                "timestamp": datetime.now().isoformat(),
                "mode": self.mode,
                "base_url": self.base_url,
                "config": config
            },
            "endpoint_health": {
                "results": endpoint_results,
                "summary": {
                    "total_endpoints": len(self.health_endpoints),
                    "healthy_endpoints": healthy_count,
                    "health_percentage": (healthy_count / len(self.health_endpoints)) * 100
                }
            },
            "database_health": {
                "status": "healthy" if db_healthy else "unhealthy"
            },
            "performance_tests": performance_results,
            "overall_status": "healthy" if (healthy_count >= len(self.health_endpoints) * 0.8 and db_healthy) else "unhealthy",
            "check_log": self.check_log
        }
        
        # Save report to file
        report_file = self.logs_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.write_text(json.dumps(report, indent=2))
        
        self.log(f"   ✅ Health report saved: {report_file}")
        
        # Print summary
        self.log("")
        self.log("📋 HEALTH CHECK SUMMARY")
        self.log("=" * 50)
        self.log(f"🎯 Mode: {self.mode.upper()}")
        self.log(f"🌐 URL: {self.base_url}")
        self.log(f"🏥 Endpoints: {healthy_count}/{len(self.health_endpoints)} healthy ({(healthy_count/len(self.health_endpoints)*100):.1f}%)")
        self.log(f"🗄️  Database: {'✅ Healthy' if db_healthy else '❌ Unhealthy'}")
        self.log(f"⚡ Performance: {len([r for r in performance_results.values() if r.get('success_rate', 0) > 0.8])}/{len(performance_results)} endpoints performing well")
        self.log(f"📊 Overall Status: {'✅ HEALTHY' if report['overall_status'] == 'healthy' else '❌ UNHEALTHY'}")
        self.log(f"📝 Report: {report_file}")
        
        return report
        
    def run_health_check(self):
        """Execute comprehensive health check"""
        start_time = time.time()
        
        try:
            self.log("🏥 Starting True-Asset-ALLUSE health check...")
            self.log(f"🎯 Mode: {self.mode}")
            self.log("")
            
            # Load configuration
            config = self.load_configuration()
            time.sleep(0.5)
            
            # Check if application is running
            app_running = self.check_application_running()
            if not app_running:
                self.log("❌ Application is not running - cannot perform full health check", "ERROR")
                return False, None
            time.sleep(0.5)
            
            # Run endpoint health checks
            endpoint_results, healthy_count = self.run_endpoint_health_checks()
            time.sleep(0.5)
            
            # Check database health
            db_healthy = self.check_database_health()
            time.sleep(0.5)
            
            # Run performance tests
            performance_results = self.run_performance_tests()
            time.sleep(0.5)
            
            # Check system resources
            self.check_system_resources()
            time.sleep(0.5)
            
            # Generate report
            report = self.generate_health_report(
                config, endpoint_results, healthy_count, 
                db_healthy, performance_results
            )
            
            check_time = time.time() - start_time
            self.log("")
            self.log(f"🎉 Health check completed!")
            self.log(f"⏱️  Total time: {check_time:.2f} seconds")
            
            # Determine overall success
            overall_healthy = report['overall_status'] == 'healthy'
            
            return overall_healthy, report
            
        except Exception as e:
            self.log(f"❌ Health check failed: {e}", "ERROR")
            return False, None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="True-Asset-ALLUSE Health Check")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock",
                       help="Application mode to check (default: mock)")
    parser.add_argument("--continuous", action="store_true",
                       help="Run continuous health monitoring")
    parser.add_argument("--interval", type=int, default=60,
                       help="Interval for continuous monitoring in seconds (default: 60)")
    
    args = parser.parse_args()
    
    checker = TrueAssetHealthChecker(mode=args.mode)
    
    if args.continuous:
        print(f"🔄 Starting continuous health monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                success, report = checker.run_health_check()
                print(f"\n⏰ Next check in {args.interval} seconds...\n")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Health monitoring stopped")
    else:
        success, report = checker.run_health_check()
        sys.exit(0 if success else 1)

