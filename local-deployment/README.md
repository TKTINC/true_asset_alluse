# True-Asset-ALLUSE Local Deployment

## Quick Start

The True-Asset-ALLUSE system can be deployed locally in both mock and live modes with a complete build and deployment pipeline.

### 🚀 One-Command Deployment

```bash
# Build and deploy in mock mode
python3 build.py --mode mock && python3 deploy.py --mode mock

# Build and deploy in live mode  
python3 build.py --mode live && python3 deploy.py --mode live
```

### 🏥 Health Monitoring

```bash
# Run comprehensive health check
python3 health_check.py --mode mock

# Continuous monitoring
python3 health_check.py --mode mock --continuous
```

## System Status

✅ **Build System**: Complete with dependency management and validation  
✅ **Deployment System**: Automated deployment with process management  
✅ **Health Monitoring**: Comprehensive endpoint and database monitoring  
✅ **Mock Mode**: Fully functional with demo data  
✅ **Live Mode**: Production-ready configuration  

## Key Features

- **Automated Build Process**: Compiles all workstreams and creates deployable artifacts
- **Dual Mode Support**: Mock mode for development, live mode for production
- **Health Monitoring**: Real-time endpoint testing and performance monitoring
- **Database Management**: SQLite database with automated schema creation
- **Process Management**: PID-based application lifecycle management
- **Comprehensive Logging**: Detailed logs for build, deployment, and health operations

## Access Points

Once deployed, access the system at:

- **🏠 Home**: http://127.0.0.1:8000/
- **📊 Dashboard**: http://127.0.0.1:8000/dashboard  
- **📚 API Docs**: http://127.0.0.1:8000/docs
- **🏥 Health**: http://127.0.0.1:8000/health

## System Architecture

The system includes these workstreams:

- **WS1-WS6**: Core trading and portfolio management
- **WS7**: Natural Language Processing  
- **WS8**: ML Intelligence
- **WS9**: Market Intelligence
- **WS12**: Visualization Intelligence
- **WS16**: Enhanced Conversational AI

## File Structure

```
local-deployment/
├── build.py              # 🔨 Build system
├── deploy.py             # 🚀 Deployment manager  
├── health_check.py       # 🏥 Health monitoring
├── setup.sh              # ⚙️ Environment setup
├── requirements.txt      # 📦 Dependencies
├── DEPLOYMENT_GUIDE.md   # 📖 Comprehensive guide
├── dist/                 # 📦 Deployment artifacts
├── database/             # 🗄️ SQLite database
└── logs/                 # 📝 System logs
```

## Quick Commands

```bash
# Build
python3 build.py --mode [mock|live]

# Deploy  
python3 deploy.py --mode [mock|live]

# Stop
python3 deploy.py --stop

# Health Check
python3 health_check.py --mode [mock|live]

# Status
python3 deploy.py --status
```

## Documentation

📖 **[Complete Deployment Guide](DEPLOYMENT_GUIDE.md)** - Comprehensive documentation covering:
- Detailed build and deployment processes
- Configuration options
- Troubleshooting guide
- API reference
- Performance benchmarks
- Security considerations

## Requirements

- Python 3.8+
- pip package manager
- SQLite3
- Internet connection (for live mode)

## Support

For detailed instructions, troubleshooting, and advanced configuration, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).

---

**True-Asset-ALLUSE** - Intelligent Wealth Management System  
*Engineered for Compounding Income and Corpus*

