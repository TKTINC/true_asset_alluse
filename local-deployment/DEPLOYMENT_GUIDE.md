# True-Asset-ALLUSE Local Deployment Guide

## Overview

This guide provides complete instructions for building, deploying, and managing the True-Asset-ALLUSE system locally. The system supports both **mock** and **live** modes with comprehensive build processes, health monitoring, and deployment verification.

## System Architecture

The True-Asset-ALLUSE system consists of multiple workstreams:

- **WS1-WS6**: Core trading and portfolio management
- **WS7**: Natural Language Processing
- **WS8**: ML Intelligence
- **WS9**: Market Intelligence
- **WS12**: Visualization Intelligence
- **WS16**: Enhanced Conversational AI

## Prerequisites

- Python 3.8 or higher
- pip package manager
- SQLite3
- Internet connection (for live mode dependencies)

## Quick Start

### 1. Build the Application

```bash
# Build in mock mode (default)
python3 build.py --mode mock

# Build in live mode
python3 build.py --mode live
```

### 2. Deploy the Application

```bash
# Deploy mock mode
python3 deploy.py --mode mock

# Deploy live mode
python3 deploy.py --mode live
```

### 3. Verify Health

```bash
# Run health check
python3 health_check.py --mode mock

# Continuous monitoring
python3 health_check.py --mode mock --continuous
```

## Detailed Instructions

### Build Process

The build system (`build.py`) performs the following operations:

1. **Environment Validation**: Checks Python version and source directory
2. **Dependency Installation**: Installs required packages with `--user` flag
3. **Source Compilation**: Compiles all Python files and validates syntax
4. **Database Setup**: Creates SQLite database with demo data
5. **Application Bundle**: Generates deployable application with configuration
6. **Validation Tests**: Runs syntax and database connectivity tests

#### Build Options

```bash
# Mock mode (default) - includes demo data, debug enabled
python3 build.py --mode mock

# Live mode - production settings, debug disabled
python3 build.py --mode live
```

#### Build Artifacts

After successful build, the following artifacts are created:

- `dist/app.py` - Main application file
- `dist/config.json` - Application configuration
- `database/true_asset_alluse.db` - SQLite database
- `build/` - Compiled source files
- `logs/build_*.log` - Build logs

### Deployment Process

The deployment system (`deploy.py`) handles:

1. **Artifact Validation**: Verifies build artifacts exist
2. **Port Management**: Checks port availability and finds alternatives
3. **Process Management**: Starts/stops application with PID tracking
4. **Status Monitoring**: Provides deployment status information

#### Deployment Commands

```bash
# Deploy application
python3 deploy.py --mode [mock|live]

# Stop running application
python3 deploy.py --stop

# Check deployment status
python3 deploy.py --status
```

#### Application URLs

Once deployed, the application is accessible at:

- **Home Page**: http://127.0.0.1:8000/
- **Dashboard**: http://127.0.0.1:8000/dashboard
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

### Health Monitoring

The health check system (`health_check.py`) provides comprehensive monitoring:

1. **Endpoint Testing**: Tests all application endpoints
2. **Database Verification**: Checks database connectivity and data integrity
3. **Performance Testing**: Measures response times
4. **System Resources**: Monitors disk usage and process status
5. **Report Generation**: Creates detailed health reports

#### Health Check Commands

```bash
# Single health check
python3 health_check.py --mode [mock|live]

# Continuous monitoring (60-second intervals)
python3 health_check.py --mode [mock|live] --continuous

# Custom monitoring interval
python3 health_check.py --mode [mock|live] --continuous --interval 30
```

#### Health Check Endpoints

The system monitors these endpoints:

- `/` - Home page
- `/health` - Health check API
- `/portfolio` - Portfolio data API
- `/dashboard` - Dashboard interface
- `/api/v1/system/info` - System information
- `/docs` - API documentation

## Configuration

### Mock Mode Configuration

```json
{
  "mode": "mock",
  "build_id": "20250911_174431",
  "database_path": "/path/to/database/true_asset_alluse.db",
  "host": "127.0.0.1",
  "port": 8000,
  "debug": true
}
```

### Live Mode Configuration

```json
{
  "mode": "live",
  "build_id": "20250911_174800",
  "database_path": "/path/to/database/true_asset_alluse.db",
  "host": "127.0.0.1",
  "port": 8000,
  "debug": false
}
```

## Database Schema

The system uses SQLite with the following tables:

### system_config
- Stores system configuration parameters
- Keys: deployment_mode, build_id, system_version, deployment_time

### portfolio
- Portfolio holdings data
- Fields: symbol, quantity, avg_price, current_price, market_value, pnl

### trades
- Trading history
- Fields: symbol, action, quantity, price, timestamp, workstream, metadata

### system_health
- System health monitoring data
- Fields: component, status, message, timestamp

## Troubleshooting

### Common Issues

#### Build Failures

1. **Permission Denied**: Use `--user` flag for pip installations
2. **Missing Dependencies**: Check internet connection and package availability
3. **Syntax Errors**: Review source code for compilation errors

#### Deployment Issues

1. **Port Already in Use**: System automatically finds alternative ports
2. **Application Won't Start**: Check build artifacts and configuration
3. **Database Errors**: Verify database file exists and is accessible

#### Health Check Failures

1. **Connection Refused**: Ensure application is running
2. **Endpoint Errors**: Check application logs for specific errors
3. **Database Issues**: Verify database connectivity and schema

### Log Files

All operations generate detailed logs:

- `logs/build_*.log` - Build process logs
- `logs/health_report_*.json` - Health check reports
- Application logs are displayed in console during deployment

### Process Management

```bash
# Check running processes
ps aux | grep app.py

# Stop all instances (if deploy.py --stop doesn't work)
pkill -f app.py

# Check port usage
netstat -tulpn | grep 8000
```

## API Reference

### Health Check Endpoint

```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{
  "status": "healthy",
  "mode": "mock",
  "build_id": "20250911_174431",
  "uptime": "Running",
  "database": "Connected"
}
```

### Portfolio API

```bash
curl http://127.0.0.1:8000/portfolio
```

Returns array of portfolio holdings with current market values.

### System Information

```bash
curl http://127.0.0.1:8000/api/v1/system/info
```

Response:
```json
{
  "name": "True-Asset-ALLUSE",
  "version": "1.0.0",
  "mode": "mock",
  "build_id": "20250911_174431",
  "status": "running"
}
```

## Performance Benchmarks

Based on health check results:

- **Home Page**: ~2ms average response time
- **Portfolio API**: ~2ms average response time
- **Health Check**: ~1ms average response time
- **Database Queries**: Sub-millisecond for portfolio data

## Security Considerations

### Mock Mode
- Debug mode enabled
- Demo data included
- Suitable for development and testing

### Live Mode
- Debug mode disabled
- Production-ready configuration
- Requires proper API keys for external services

## Maintenance

### Regular Tasks

1. **Health Monitoring**: Run periodic health checks
2. **Log Rotation**: Clean up old log files
3. **Database Backup**: Backup SQLite database regularly
4. **Dependency Updates**: Keep packages updated

### Backup Procedures

```bash
# Backup database
cp database/true_asset_alluse.db database/backup_$(date +%Y%m%d).db

# Backup configuration
cp dist/config.json dist/config_backup_$(date +%Y%m%d).json
```

## Support and Development

### File Structure

```
local-deployment/
├── build.py              # Build system
├── deploy.py             # Deployment manager
├── health_check.py       # Health monitoring
├── setup.sh              # Environment setup
├── requirements.txt      # Python dependencies
├── README.md             # Basic documentation
├── DEPLOYMENT_GUIDE.md   # This comprehensive guide
├── dist/                 # Deployment artifacts
├── build/                # Build artifacts
├── database/             # SQLite database
└── logs/                 # System logs
```

### Development Workflow

1. Make changes to source code in `../src/`
2. Run build process: `python3 build.py --mode mock`
3. Deploy for testing: `python3 deploy.py --mode mock`
4. Run health checks: `python3 health_check.py --mode mock`
5. Test functionality via web interface or API
6. For production: repeat with `--mode live`

### Contributing

When making changes to the deployment system:

1. Test both mock and live modes
2. Verify health checks pass
3. Update documentation as needed
4. Test build and deployment processes

## Conclusion

This deployment system provides a robust, production-ready solution for running the True-Asset-ALLUSE system locally. The comprehensive build, deployment, and monitoring tools ensure reliable operation in both development and production environments.

For additional support or questions, refer to the system documentation or contact the development team.

