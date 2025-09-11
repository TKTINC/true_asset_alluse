#!/bin/bash
# True-Asset-ALLUSE Local Deployment Start Script
# Supports both mock and live modes

# Default mode
MODE="mock"

# Parse command line arguments
if [ "$1" = "live" ]; then
    MODE="live"
elif [ "$1" = "mock" ]; then
    MODE="mock"
elif [ ! -z "$1" ]; then
    echo "Usage: $0 [mock|live]"
    echo "  mock - Use mock data for demonstration (default)"
    echo "  live - Connect to real services (requires API keys)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv_enhanced" ]; then
    echo "❌ Virtual environment not found. Please run ./setup_macos_enhanced.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv_enhanced/bin/activate

# Load environment variables if in live mode
if [ "$MODE" = "live" ]; then
    if [ -f ".env.local" ]; then
        echo "🔑 Loading API keys from .env.local..."
        export $(cat .env.local | grep -v '^#' | xargs)
    else
        echo "⚠️  Warning: .env.local file not found. Live mode may not work properly."
        echo "💡 Create .env.local with your API keys or run in mock mode."
    fi
fi

echo "🚀 Starting True-Asset-ALLUSE in $MODE mode..."
echo "📊 Dashboard: http://127.0.0.1:8000/demo"
echo "📚 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python local_main.py --mode $MODE

