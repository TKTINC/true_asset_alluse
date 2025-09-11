#!/bin/bash
# Quick Setup for True-Asset-ALLUSE Local Demo
# Focuses on getting basic functionality working quickly

set -e  # Exit on any error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() { echo -e "${YELLOW}[INFO] $1${NC}"; }
echo_success() { echo -e "${GREEN}[SUCCESS] $1${NC}"; }
echo_error() { echo -e "${RED}[ERROR] $1${NC}"; }

echo_info "🚀 Quick Setup for True-Asset-ALLUSE Local Demo"
echo_info "This will install minimal dependencies for a working demo"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo_error "Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo_info "Found Python $PYTHON_VERSION"

# Create virtual environment
VENV_DIR="venv_demo"
if [ -d "$VENV_DIR" ]; then
    echo_info "Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

echo_info "Creating fresh virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate virtual environment
echo_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo_info "Upgrading pip..."
pip install --upgrade pip

# Install minimal requirements
echo_info "Installing minimal requirements..."
pip install -r requirements_minimal.txt

echo_success "✅ Basic dependencies installed!"

# Create simple start script
cat << 'EOF' > start_demo.sh
#!/bin/bash
# Simple demo start script

# Check if virtual environment exists
if [ ! -d "venv_demo" ]; then
    echo "❌ Virtual environment not found. Please run ./quick_setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv_demo/bin/activate

# Set mode
MODE=${1:-mock}

echo "🚀 Starting True-Asset-ALLUSE Demo in $MODE mode..."
echo "📊 Demo will be available at: http://127.0.0.1:8000/demo"
echo ""

# Start the application
python local_main.py --mode $MODE
EOF

chmod +x start_demo.sh

# Create stop script
cat << 'EOF' > stop_demo.sh
#!/bin/bash
echo "🛑 Stopping True-Asset-ALLUSE Demo..."
pkill -f "python local_main.py" || echo "No running demo found"
echo "✅ Demo stopped"
EOF

chmod +x stop_demo.sh

echo ""
echo_success "🎉 Quick setup complete!"
echo ""
echo_info "To start the demo:"
echo_info "  ./start_demo.sh mock    # For mock data demo"
echo_info "  ./start_demo.sh live    # For live data (requires API keys)"
echo ""
echo_info "To stop the demo:"
echo_info "  ./stop_demo.sh"
echo ""
echo_info "Demo URL: http://127.0.0.1:8000/demo"
echo ""

