# True-Asset-ALLUSE: Local Deployment Guide

This guide provides a step-by-step walkthrough for setting up and running the True-Asset-ALLUSE local deployment on your MacBook Air.

---

## 1. Prerequisites

Before you begin, ensure you have the following installed on your MacBook Air:

- **macOS**: 10.15 (Catalina) or later
- **Homebrew**: The missing package manager for macOS. If you don't have it, the setup script will install it for you.
- **Terminal**: The default macOS terminal or iTerm2.
- **Internet Connection**: Required for initial setup and dependency installation.

---

## 2. One-Time Setup

This process will set up your local environment, install all necessary dependencies, and prepare the application for launch. You only need to do this once.

1. **Open Terminal** on your MacBook Air.
2. **Navigate to the project directory**:
   ```bash
   cd /path/to/true_asset_alluse_local
   ```
3. **Run the setup script**:
   ```bash
   ./setup_macos.sh
   ```

**What the script does:**
- ✅ Installs Homebrew (if not present)
- ✅ Installs Python 3.11
- ✅ Creates a Python virtual environment
- ✅ Installs all required dependencies
- ✅ Sets up a local SQLite database
- ✅ Creates launch and stop scripts

---

## 3. Running the Application

Once the setup is complete, you can start the local server at any time.

1. **Open Terminal** and navigate to the project directory.
2. **Run the start script**:
   ```bash
   ./start_server.sh
   ```

**You should see output like this:**
```
🚀 Starting True-Asset-ALLUSE Local Deployment
==================================================
Starting server...
📊 Portfolio Value: $1,247,850.00
💰 Daily P&L: +$12,450.00
🤖 AI Assistant: Mock Mode
🌐 Access URL: http://127.0.0.1:8000
🔑 Demo Login: admin / password
==================================================
```

3. **Open your web browser** (Chrome, Safari, Firefox) and navigate to:
   [http://127.0.0.1:8000](http://127.0.0.1:8000)

4. **Login with the demo credentials**:
   - **Username**: `admin`
   - **Password**: `password`

---

## 4. Demo Walkthrough

Now that the application is running, here's a suggested demo flow to showcase its capabilities:

### **Step 1: Explore the Dashboard**
- **Review the key metrics**: Total Portfolio Value, Today's P&L, Weekly Return.
- **Examine the Current Positions**: See the mock data for AAPL, MSFT, GOOGL, TSLA.
- **Check the System Status**: Verify that all components are active and compliant.

### **Step 2: Interact with the AI Assistant**
- **Navigate to the AI Assistant** from the sidebar.
- **Ask questions about the portfolio**:
  - "How is my portfolio performing today?"
  - "Tell me about the AAPL position."
  - "What is the current risk level?"
- **Observe the AI's advisory responses**.

### **Step 3: Explore Other Sections**
- **Click on Trading, Accounts, and Risk Management** to see the placeholder interfaces.
- **Explain the future capabilities** of these sections.

### **Step 4: Showcase Responsive Design**
- **Resize your browser window** to demonstrate how the interface adapts to different screen sizes.
- **Open the developer tools** (Cmd+Option+I) and toggle the device toolbar to simulate a mobile view.

---

## 5. Stopping the Application

When you're finished with your demo, you can stop the local server.

1. **Open Terminal** and navigate to the project directory.
2. **Run the stop script**:
   ```bash
   ./stop_server.sh
   ```

**You should see output like this:**
```
🛑 Stopping True-Asset-ALLUSE Local Deployment...
✅ Server stopped successfully
```

---

## 6. Troubleshooting

### **Port 8000 Already in Use**
If you get an error that the port is already in use, it means another process is using it. Run the stop script to kill any lingering processes:
```bash
./stop_server.sh
```
Then try starting the server again.

### **Dependencies Not Found**
If you get an error about missing dependencies, run the setup script again to reinstall them:
```bash
./setup_macos.sh
```

### **Reset the Database**
If you want to reset the database to its initial state, you can delete the database file and run the setup script again:
```bash
rm -f data/true_asset_alluse.db
./setup_macos.sh
```

---

This local deployment provides a powerful and cost-effective way to demonstrate the True-Asset-ALLUSE platform without the need for a full cloud deployment. It's perfect for investor presentations, team onboarding, and strategic planning.

