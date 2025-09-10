#!/bin/bash
# True-Asset-ALLUSE Enhanced Local Deployment Setup for macOS

# --- Configuration ---
PYTHON_VERSION="3.11"
VENV_DIR="venv_enhanced"
REQUIREMENTS_FILE="requirements_enhanced.txt"

# --- Colors ---
GREEN=\'\033[0;32m\'
YELLOW=\'\033[1;33m\'
RED=\'\033[0;31m\'
NC=\'\033[0m\'

# --- Helper Functions ---
echo_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

echo_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# --- Main Script ---
echo_info "Starting True-Asset-ALLUSE Enhanced Local Deployment Setup..."

# 1. Check for Homebrew
echo_info "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    echo_error "Homebrew not found. Please install Homebrew first: https://brew.sh/"
    exit 1
fi
echo_success "Homebrew found."

# 2. Install Python
echo_info "Installing Python ${PYTHON_VERSION} via Homebrew..."
brew install python@${PYTHON_VERSION}
echo_success "Python ${PYTHON_VERSION} installed."

# 3. Create Virtual Environment
echo_info "Creating Python virtual environment in ./${VENV_DIR}..."
python${PYTHON_VERSION} -m venv ${VENV_DIR}
echo_success "Virtual environment created."

# 4. Activate Virtual Environment
echo_info "Activating virtual environment..."
source ${VENV_DIR}/bin/activate
echo_success "Virtual environment activated."

# 5. Install Dependencies
echo_info "Installing required Python packages from ${REQUIREMENTS_FILE}..."
pip install --upgrade pip
pip install -r ${REQUIREMENTS_FILE}
echo_success "All dependencies installed successfully."

# 6. Create .env.local file
ENV_FILE=".env.local"
echo_info "Creating ${ENV_FILE} for your API keys..."
if [ ! -f "${ENV_FILE}" ]; then
    echo "# --- API Keys for Enhanced Local Deployment ---" > ${ENV_FILE}
    echo "# Please replace with your actual API keys" >> ${ENV_FILE}
    echo "" >> ${ENV_FILE}
    echo "# Databento API Key (https://databento.com/)" >> ${ENV_FILE}
    echo "DATABENTO_API_KEY=\"YOUR_DATABENTO_API_KEY\"" >> ${ENV_FILE}
    echo "" >> ${ENV_FILE}
    echo "# OpenAI API Key (https://platform.openai.com/)" >> ${ENV_FILE}
    echo "OPENAI_API_KEY=\"YOUR_OPENAI_API_KEY\"" >> ${ENV_FILE}
    echo "" >> ${ENV_FILE}
    echo "# News API Key (https://newsapi.org/)" >> ${ENV_FILE}
    echo "NEWS_API_KEY=\"YOUR_NEWS_API_KEY\"" >> ${ENV_FILE}
    echo "" >> ${ENV_FILE}
    echo "# Alpha Vantage API Key (https://www.alphavantage.co/)" >> ${ENV_FILE}
    echo "ALPHA_VANTAGE_API_KEY=\"YOUR_ALPHA_VANTAGE_API_KEY\"" >> ${ENV_FILE}
    echo_success "${ENV_FILE} created. Please edit it with your API keys."
else
    echo_info "${ENV_FILE} already exists. Skipping creation."
fi

# 7. Create Start and Stop Scripts
START_SCRIPT="start_server.sh"
STOP_SCRIPT="stop_server.sh"

echo_info "Creating start and stop scripts..."

# Start Script
cat << EOF > ${START_SCRIPT}
#!/bin/bash
source ${VENV_DIR}/bin/activate
echo "Starting True-Asset-ALLUSE Enhanced Local Server..."
python main_enhanced.py
EOF
chmod +x ${START_SCRIPT}

# Stop Script
cat << EOF > ${STOP_SCRIPT}
#!/bin/bash
echo "Stopping True-Asset-ALLUSE Server..."
pkill -f "python main_enhanced.py"
echo "Server stopped."
EOF
chmod +x ${STOP_SCRIPT}

echo_success "Start and stop scripts created."

# --- Final Instructions ---
echo_info "-----------------------------------------------------"
echo_success "Setup complete!"
echo_info ""
echo_info "Next Steps:"
echo_info "1. Edit the .env.local file and add your API keys."
echo_info "2. Make sure Interactive Brokers TWS is running on your machine."
echo_info "3. Run ./start_server.sh to launch the application."
echo_info "4. Open http://127.0.0.1:8000 in your browser."
echo_info ""
echo_info "To stop the server, run ./stop_server.sh"
echo_info "-----------------------------------------------------"


