# 🚀 True-Asset-ALLUSE Local Demo - Quick Start Guide

## Problem Solved
If you encountered dependency issues with the full setup, this quick start gets you running in under 5 minutes with minimal dependencies.

## ⚡ Quick Setup (5 minutes)

### 1. Run Quick Setup
```bash
cd local-deployment/
./quick_setup.sh
```

This will:
- Create a fresh virtual environment
- Install only essential dependencies
- Create simple start/stop scripts

### 2. Start the Demo
```bash
# For mock data demo (no API keys needed)
./start_demo.sh mock

# For live data demo (requires API keys)
./start_demo.sh live
```

### 3. Open Demo
Open your browser to: **http://127.0.0.1:8000/demo**

### 4. Stop the Demo
```bash
./stop_demo.sh
```

## 🎯 What You Get

### Mock Mode
- ✅ Working FastAPI application
- ✅ Professional demo dashboard
- ✅ Portfolio metrics display
- ✅ System health indicators
- ✅ API documentation at `/docs`

### Live Mode (Optional)
- ✅ All mock mode features
- ✅ Real API integrations (when configured)
- ✅ Live market data
- ✅ Actual AI responses

## 🔧 Troubleshooting

### If Dependencies Fail to Install
```bash
# Try with Python 3.8+ specifically
python3.8 -m venv venv_demo
source venv_demo/bin/activate
pip install --upgrade pip
pip install -r requirements_minimal.txt
```

### If Demo Won't Start
```bash
# Check if virtual environment is activated
source venv_demo/bin/activate

# Check if dependencies are installed
pip list | grep fastapi

# Try running directly
python local_main.py --mode mock
```

### If Port 8000 is Busy
The demo will automatically try different ports. Check the console output for the actual URL.

## 📊 Demo Features

### Dashboard Displays
- **Portfolio Value**: $1,247,850 (demo data)
- **Daily P&L**: +$12,450 (demo data)
- **Active Positions**: 8 positions
- **System Health**: 100% operational

### Available Endpoints
- `/demo` - Main dashboard
- `/docs` - API documentation
- `/health` - System health check
- `/api/v1/local/mock-data` - Mock data endpoint (mock mode)

## 🚀 Next Steps

### For Investors/Demos
1. Use mock mode for presentations
2. Show the professional dashboard
3. Demonstrate API documentation
4. Explain the system architecture

### For Development
1. Start with mock mode
2. Add API keys for live mode
3. Extend with additional features
4. Deploy to production when ready

## 💡 Why This Works

This quick setup:
- ✅ **Minimal Dependencies**: Only essential packages
- ✅ **Fast Installation**: Under 5 minutes
- ✅ **Reliable**: Fewer things that can go wrong
- ✅ **Professional**: Still shows a complete system
- ✅ **Extensible**: Can add more features later

Perfect for investor demos, team presentations, and initial development!

