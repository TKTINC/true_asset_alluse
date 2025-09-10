# True-Asset-ALLUSE: Enhanced Local Deployment Guide (Live Services)

## 🚀 Overview

This guide provides step-by-step instructions for setting up and running the **enhanced local deployment** of True-Asset-ALLUSE on your MacBook Air. This version connects to **real financial services** to provide a working demonstration of the system with live data.

**Key Features of this Deployment:**
- **Live Market Data**: Connects to Databento for real-time quotes and historical data.
- **Real AI Analysis**: Integrates with OpenAI for genuine portfolio insights and chat.
- **Live News & Sentiment**: Pulls real financial news and performs sentiment analysis.
- **Paper Trading**: Connects to Interactive Brokers (IBKR) TWS for paper trading.
- **Local Operation**: Runs entirely on your local machine with minimal setup.

**Monthly Cost:** ~$180-600 (depending on API usage) vs. $1,500+ for full cloud deployment.

---

## 📋 Prerequisites

Before you begin, ensure you have the following:

1. **MacBook Air** with macOS.
2. **Homebrew** package manager installed (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`).
3. **Interactive Brokers (IBKR) Trader Workstation (TWS)** installed and running on your machine. ([Download here](https://www.interactivebrokers.com/en/index.php?f=1604)).
4. **API Keys** for the following services:
   - **Databento**: [https://databento.com/](https://databento.com/)
   - **OpenAI**: [https://platform.openai.com/](https://platform.openai.com/)
   - **News API**: [https://newsapi.org/](https://newsapi.org/)
   - **Alpha Vantage** (optional fallback): [https://www.alphavantage.co/](https://www.alphavantage.co/)

---

## ⚙️ One-Time Setup (10 minutes)

Follow these steps to set up the local environment. You only need to do this once.

### Step 1: Clone the Repository

If you haven't already, clone the main repository to your local machine:

```bash
git clone https://github.com/TKTINC/true_asset_alluse.git
cd true_asset_alluse/local-deployment
```

### Step 2: Run the Automated Setup Script

This script will install Python, create a virtual environment, and install all required dependencies.

```bash
chmod +x setup_macos_enhanced.sh
./setup_macos_enhanced.sh
```

### Step 3: Configure API Keys

The setup script creates a `.env.local` file. Open this file in a text editor and add your API keys from the prerequisite step.

```bash
# .env.local

DATABENTO_API_KEY="YOUR_DATABENTO_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
NEWS_API_KEY="YOUR_NEWS_API_KEY"
ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"
```

### Step 4: Configure IBKR Trader Workstation (TWS)

1. **Launch TWS** on your MacBook Air.
2. **Log in** to your **paper trading account**.
3. Go to **File > Global Configuration > API > Settings**.
4. **Enable ActiveX and Socket Clients**.
5. **Set Socket port** to `7497` (for paper trading).
6. **Add `127.0.0.1`** to the list of trusted IPs.

---

## ▶️ Running the Application

Once the setup is complete, you can start and stop the application easily.

### Step 1: Start the Server

Make sure you are in the `local-deployment` directory and run:

```bash
./start_server.sh
```

This will activate the virtual environment and launch the application server.

### Step 2: Open in Browser

Open your web browser and navigate to:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

### Step 3: Log In

Use the following credentials to log in:
- **Username**: `admin`
- **Password**: `password`

### Step 4: Stop the Server

When you are finished, you can stop the server by running:

```bash
./stop_server.sh
```

---

## 🚀 Demonstration Walkthrough

Here is a suggested flow for demonstrating the system to investors or potential team members:

1. **Dashboard Overview**: Start with the main dashboard. Highlight the **live portfolio value**, **daily P&L**, and **portfolio delta**, explaining that this data is coming directly from your IBKR paper trading account.

2. **AI Assistant Interaction**: Use the chat interface to ask questions about the portfolio. For example:
   - "What is the current risk exposure of my portfolio?"
   - "Analyze the performance of my AAPL position."
   - "What is the current market sentiment?"
   Explain that these are real responses from the OpenAI API based on live data.

3. **Market Sentiment**: Show the market sentiment widget and explain that it's based on real-time news analysis from News API. Click on high-impact news to show the system's ability to filter for important events.

4. **System Health**: Point out the system health widget, showing the live connection status of all integrated services (IBKR, Databento, OpenAI, News API).

5. **Positions Table**: Go through the active positions, explaining that these are real positions from the IBKR paper account. Show how the P&L updates in near real-time.

6. **Live Market Data**: Explain that all the data is being fed in real-time from Databento, a professional-grade market data provider.

---

## 🔧 Troubleshooting

- **Connection Errors**: Ensure TWS is running and configured correctly. Check that your API keys in `.env.local` are correct.
- **Slow Performance**: Live API calls can sometimes be slow. This is expected and demonstrates the reality of working with external services.
- **No Data**: Make sure you have positions in your IBKR paper trading account for the system to display.

---

## 🌟 Conclusion

This enhanced local deployment provides a powerful and credible demonstration of True-Asset-ALLUSE's capabilities. By using real financial services, you can showcase the system's true potential and business value to any audience, from investors to technical experts.


