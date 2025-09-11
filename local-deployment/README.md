# 🚀 True-Asset-ALLUSE Local Deployment

**Intelligent Wealth Management System - Engineered for Compounding Income and Corpus**

Complete build and deployment system for running True-Asset-ALLUSE locally on your machine.

## 🎯 Overview

This local deployment system provides a complete, production-like build and deployment process for True-Asset-ALLUSE. Unlike simple demo scripts, this system:

- ✅ **Complete Build Process** - Compiles, validates, and prepares application artifacts
- ✅ **Database Setup** - Initializes SQLite database with proper schemas and demo data
- ✅ **Service Orchestration** - Manages application lifecycle and health checks
- ✅ **Professional Deployment** - Real deployment process, just running locally
- ✅ **Dual Mode Support** - Mock mode (demo data) and Live mode (real APIs)

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (required)
- **pip** (Python package manager)
- **macOS or Linux** (Windows support via WSL)

### One-Command Setup
```bash
# Setup and build (mock mode)
./setup.sh

# Setup and build (live mode with real APIs)
./setup.sh --mode live
```

### Start the Application
```bash
# Start in mock mode (demo data)
./start.sh mock

# Start in live mode (real APIs - requires API keys)
./start.sh live
```

### Access the Application
- **Main Interface**: http://127.0.0.1:8000
- **Dashboard**: http://127.0.0.1:8000/dashboard  
- **API Documentation**: http://127.0.0.1:8000/docs

### Stop the Application
```bash
./stop.sh
```

## 🎭 Mock vs Live Mode

### Mock Mode (Default)
- ✅ **No API Keys Required** - Works out of the box
- ✅ **Demo Portfolio Data** - $143,800 portfolio with realistic positions
- ✅ **Perfect for Demos** - Investor presentations and team onboarding

### Live Mode (Advanced)
- 🔑 **API Keys Required** - Real service integrations
- 📡 **Live Market Data** - Real-time quotes via Databento
- 🤖 **AI Analysis** - Actual OpenAI GPT responses

## 🔧 Troubleshooting

### Common Issues
- **Port in use**: Script will auto-find available port
- **Python version**: Requires Python 3.8+
- **Dependencies**: Run `./setup.sh --clean` to reset

For detailed instructions, see the full documentation in this README.

