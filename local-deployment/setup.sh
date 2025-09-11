#!/bin/bash
# True-Asset-ALLUSE Complete Local Setup
# Build and deployment system for macOS/Linux

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
VENV_NAME="true_asset_venv"
PYTHON_MIN_VERSION="3.8"

echo ""
echo -e "${BLUE}🚀 True-Asset-ALLUSE Complete Setup${NC}"
echo -e "${BLUE}Intelligent Wealth Management System${NC}"
echo -e "${BLUE}Engineered for Compounding Income and Corpus${NC}"
echo ""

# Parse command line arguments
MODE="mock"
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE     Deployment mode: mock or live (default: mock)"
            echo "  --clean         Clean existing installation"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Setup in mock mode"
            echo "  $0 --mode live        # Setup in live mode"
            echo "  $0 --clean --mode mock # Clean setup in mock mode"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

log_info "Setup configuration:"
log_info "  Mode: $MODE"
log_info "  Clean install: $CLEAN"
echo ""

# Clean existing installation if requested
if [ "$CLEAN" = true ]; then
    log_info "🧹 Cleaning existing installation..."
    
    # Remove virtual environment
    if [ -d "$VENV_NAME" ]; then
        rm -rf "$VENV_NAME"
        log_success "Removed existing virtual environment"
    fi
    
    # Remove build artifacts
    if [ -d "build" ]; then
        rm -rf build
        log_success "Removed build directory"
    fi
    
    if [ -d "dist" ]; then
        rm -rf dist
        log_success "Removed dist directory"
    fi
    
    if [ -d "database" ]; then
        rm -rf database
        log_success "Removed database directory"
    fi
    
    if [ -d "logs" ]; then
        rm -rf logs
        log_success "Removed logs directory"
    fi
    
    # Remove PID file
    if [ -f "app.pid" ]; then
        rm -f app.pid
        log_success "Removed PID file"
    fi
    
    echo ""
fi

# Check system requirements
log_info "🔍 Checking system requirements..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    log_error "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_VERSION_CHECK=$(python3 -c "import sys; print(sys.version_info >= (3, 8))")

if [ "$PYTHON_VERSION_CHECK" != "True" ]; then
    log_error "Python $PYTHON_VERSION found, but Python $PYTHON_MIN_VERSION+ is required"
    exit 1
fi

log_success "Python $PYTHON_VERSION found"

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    log_error "pip is not available"
    log_error "Please install pip for Python 3"
    exit 1
fi

log_success "pip is available"

# Check virtual environment support
if ! python3 -m venv --help &> /dev/null; then
    log_error "Python venv module is not available"
    log_error "Please install python3-venv package"
    exit 1
fi

log_success "Virtual environment support available"
echo ""

# Create virtual environment
log_info "🐍 Setting up Python virtual environment..."

if [ -d "$VENV_NAME" ]; then
    log_warning "Virtual environment already exists"
else
    python3 -m venv "$VENV_NAME"
    log_success "Created virtual environment: $VENV_NAME"
fi

# Activate virtual environment
source "$VENV_NAME/bin/activate"
log_success "Activated virtual environment"

# Upgrade pip
log_info "📦 Upgrading pip..."
python -m pip install --upgrade pip --quiet
log_success "pip upgraded"

# Install dependencies
log_info "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    log_success "Base dependencies installed"
else
    log_error "requirements.txt not found"
    exit 1
fi

# Install mode-specific dependencies
if [ "$MODE" = "live" ]; then
    log_info "📡 Installing live mode dependencies..."
    
    # Optional dependencies for live mode
    LIVE_DEPS=(
        "databento==0.18.0"
        "openai==1.3.7"
        "newsapi-python==0.2.6"
        "ib-insync==0.9.86"
    )
    
    for dep in "${LIVE_DEPS[@]}"; do
        if pip install "$dep" --quiet 2>/dev/null; then
            log_success "Installed: $dep"
        else
            log_warning "Failed to install: $dep (optional)"
        fi
    done
fi

echo ""

# Build the application
log_info "🏗️  Building True-Asset-ALLUSE application..."
echo ""

if python build.py --mode "$MODE"; then
    log_success "Build completed successfully"
else
    log_error "Build failed"
    exit 1
fi

echo ""

# Create convenience scripts
log_info "📝 Creating convenience scripts..."

# Create start script
cat > start.sh << EOF
#!/bin/bash
# Start True-Asset-ALLUSE

cd "\$(dirname "\$0")"

if [ ! -d "$VENV_NAME" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

source "$VENV_NAME/bin/activate"

MODE=\${1:-$MODE}

echo "🚀 Starting True-Asset-ALLUSE in \$MODE mode..."
python deploy.py --mode "\$MODE"
EOF

chmod +x start.sh

# Create stop script
cat > stop.sh << EOF
#!/bin/bash
# Stop True-Asset-ALLUSE

cd "\$(dirname "\$0")"

if [ ! -d "$VENV_NAME" ]; then
    echo "❌ Virtual environment not found."
    exit 1
fi

source "$VENV_NAME/bin/activate"
python deploy.py --stop
EOF

chmod +x stop.sh

# Create status script
cat > status.sh << EOF
#!/bin/bash
# Check True-Asset-ALLUSE status

cd "\$(dirname "\$0")"

if [ ! -d "$VENV_NAME" ]; then
    echo "❌ Virtual environment not found."
    exit 1
fi

source "$VENV_NAME/bin/activate"
python deploy.py --status
EOF

chmod +x status.sh

log_success "Created convenience scripts: start.sh, stop.sh, status.sh"

# Create .env template for live mode
if [ "$MODE" = "live" ]; then
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# True-Asset-ALLUSE Live Mode Configuration
# Copy this file and add your API keys

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Databento Configuration  
DATABENTO_API_KEY=your_databento_api_key_here

# News API Configuration
NEWS_API_KEY=your_news_api_key_here

# Interactive Brokers Configuration
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# System Configuration
LOG_LEVEL=INFO
DEBUG=false
EOF
        log_success "Created .env template for live mode configuration"
        log_warning "Please edit .env file and add your API keys before starting in live mode"
    fi
fi

echo ""
log_success "🎉 Setup completed successfully!"
echo ""
log_info "📋 Next steps:"
log_info "  1. To start the application:"
log_info "     ./start.sh $MODE"
echo ""
log_info "  2. To stop the application:"
log_info "     ./stop.sh"
echo ""
log_info "  3. To check status:"
log_info "     ./status.sh"
echo ""

if [ "$MODE" = "live" ]; then
    log_info "  4. For live mode, edit .env file with your API keys first"
    echo ""
fi

log_info "🌐 Once started, access your application at:"
log_info "     http://127.0.0.1:8000"
log_info "     http://127.0.0.1:8000/dashboard"
log_info "     http://127.0.0.1:8000/docs"
echo ""

log_success "True-Asset-ALLUSE is ready for deployment! 🚀"

