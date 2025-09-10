#!/bin/bash

# True-Asset-ALLUSE Local Deployment Setup Script
# Optimized for MacBook Air
# Author: True-Asset-ALLUSE Team

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11"
PROJECT_NAME="true-asset-alluse-local"
VENV_NAME="venv"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  TRUE-ASSET-ALLUSE LOCAL DEPLOYMENT SETUP"
    echo "  Optimized for MacBook Air"
    echo "=================================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

install_homebrew() {
    if ! check_command brew; then
        print_step "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        print_success "Homebrew installed successfully"
    else
        print_info "Homebrew already installed"
    fi
}

install_python() {
    if ! check_command python3; then
        print_step "Installing Python ${PYTHON_VERSION}..."
        brew install python@${PYTHON_VERSION}
        print_success "Python ${PYTHON_VERSION} installed successfully"
    else
        print_info "Python already installed: $(python3 --version)"
    fi
}

setup_virtual_environment() {
    print_step "Setting up Python virtual environment..."
    
    # Remove existing venv if it exists
    if [ -d "$VENV_NAME" ]; then
        rm -rf "$VENV_NAME"
        print_info "Removed existing virtual environment"
    fi
    
    # Create new virtual environment
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Virtual environment created and activated"
}

install_dependencies() {
    print_step "Installing Python dependencies..."
    
    # Ensure we're in the virtual environment
    source "$VENV_NAME/bin/activate"
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_success "Dependencies installed successfully"
}

create_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p static
    
    print_success "Directories created"
}

setup_database() {
    print_step "Setting up local database..."
    
    # Ensure we're in the virtual environment
    source "$VENV_NAME/bin/activate"
    
    # Create a simple database initialization script
    python3 -c "
import sqlite3
import os
from pathlib import Path

# Create data directory if it doesn't exist
Path('data').mkdir(exist_ok=True)

# Create database
conn = sqlite3.connect('data/true_asset_alluse.db')
cursor = conn.cursor()

# Create a simple users table for demo
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Create a simple portfolio table for demo
cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_value REAL,
        daily_pnl REAL,
        weekly_return REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

conn.commit()
conn.close()

print('Database initialized successfully')
"
    
    print_success "Database setup completed"
}

create_launch_script() {
    print_step "Creating launch script..."
    
    cat > start_server.sh << 'EOF'
#!/bin/bash

# True-Asset-ALLUSE Local Server Launcher

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "🚀 Starting True-Asset-ALLUSE Local Deployment"
echo "=================================================="
echo -e "${NC}"

# Activate virtual environment
source venv/bin/activate

# Check if all dependencies are installed
python3 -c "import fastapi, uvicorn, sqlalchemy" 2>/dev/null || {
    echo "Dependencies not found. Please run setup_macos.sh first."
    exit 1
}

# Start the server
echo -e "${GREEN}Starting server...${NC}"
echo "📊 Portfolio Value: $1,247,850.00"
echo "💰 Daily P&L: +$12,450.00"
echo "🤖 AI Assistant: Mock Mode"
echo "🌐 Access URL: http://127.0.0.1:8000"
echo "🔑 Demo Login: admin / password"
echo "=================================================="

python3 main.py
EOF

    chmod +x start_server.sh
    
    print_success "Launch script created"
}

create_stop_script() {
    print_step "Creating stop script..."
    
    cat > stop_server.sh << 'EOF'
#!/bin/bash

# True-Asset-ALLUSE Local Server Stopper

echo "🛑 Stopping True-Asset-ALLUSE Local Deployment..."

# Find and kill the process
pkill -f "python3 main.py" || pkill -f "uvicorn"

echo "✅ Server stopped successfully"
EOF

    chmod +x stop_server.sh
    
    print_success "Stop script created"
}

create_readme() {
    print_step "Creating README..."
    
    cat > README_LOCAL.md << 'EOF'
# True-Asset-ALLUSE Local Deployment

## Quick Start

1. **Setup** (one-time):
   ```bash
   ./setup_macos.sh
   ```

2. **Start Server**:
   ```bash
   ./start_server.sh
   ```

3. **Access Application**:
   - Open browser to: http://127.0.0.1:8000
   - Login with: admin / password

4. **Stop Server**:
   ```bash
   ./stop_server.sh
   ```

## Features

- ✅ Full portfolio dashboard
- ✅ AI Assistant (mock mode)
- ✅ Real-time portfolio data
- ✅ System status monitoring
- ✅ Responsive design
- ✅ Local SQLite database

## System Requirements

- macOS 10.15+ (Catalina or later)
- 4GB RAM minimum
- 1GB free disk space
- Internet connection (for initial setup)

## Demo Data

The local deployment includes realistic demo data:
- Portfolio Value: $1,247,850
- Daily P&L: +$12,450 (+1.01%)
- Weekly Return: +0.85%
- 4 Active Positions (AAPL, MSFT, GOOGL, TSLA)

## Troubleshooting

### Port Already in Use
```bash
./stop_server.sh
./start_server.sh
```

### Dependencies Issues
```bash
./setup_macos.sh
```

### Reset Database
```bash
rm -f data/true_asset_alluse.db
./setup_macos.sh
```

## Architecture

- **Backend**: FastAPI + SQLite
- **Frontend**: HTML + Tailwind CSS + Alpine.js
- **AI**: Mock responses (OpenAI integration available)
- **Data**: Simulated market data

## Next Steps

1. Add OpenAI API key for real AI responses
2. Connect to live market data feeds
3. Deploy to cloud infrastructure
4. Add more advanced trading features

---

**True-Asset-ALLUSE: Autopilot for Wealth. Engineered for compounding income and corpus.**
EOF
    
    print_success "README created"
}

# Main execution
main() {
    print_header
    
    print_info "Checking system requirements..."
    
    # Check if we're on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS only"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "main.py" ]]; then
        print_error "Please run this script from the True-Asset-ALLUSE local deployment directory"
        exit 1
    fi
    
    print_info "System check passed. Starting setup..."
    
    # Installation steps
    install_homebrew
    install_python
    setup_virtual_environment
    install_dependencies
    create_directories
    setup_database
    create_launch_script
    create_stop_script
    create_readme
    
    print_header
    print_success "Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Start the server: ./start_server.sh"
    echo "  2. Open browser to: http://127.0.0.1:8000"
    echo "  3. Login with: admin / password"
    echo ""
    print_info "For help, see README_LOCAL.md"
    echo ""
}

# Run main function
main "$@"

