# True-Asset-ALLUSE: Enhanced Local Deployment Guide (Production Code)

## 🚀 Overview

This guide provides step-by-step instructions for setting up and running the **enhanced local deployment** of True-Asset-ALLUSE on your MacBook Air. This version uses the **actual production code** from the `src/` directory with local configuration overrides, ensuring you see the real system.

**Key Features of this Deployment:**
- **Production Code**: Uses the actual True-Asset-ALLUSE system (all 11 workstreams)
- **Mode Selection**: Choose between `mock` (demo data) or `live` (real services)
- **Real System**: Investors see the actual product, not a separate demo
- **Easy Switching**: Toggle between modes with a single parameter
- **Local Operation**: Runs entirely on your local machine with minimal setup

**Monthly Cost:** 
- **Mock Mode**: $0 (perfect for initial demos)
- **Live Mode**: ~$180-600 (depending on API usage)

---

## 📋 Prerequisites

Before you begin, ensure you have the following:

1. **MacBook Air** with macOS.
2. **Homebrew** package manager installed.
3. **Interactive Brokers (IBKR) Trader Workstation (TWS)** (only for live mode).
4. **API Keys** (only for live mode):
   - **Databento**: [https://databento.com/](https://databento.com/)
   - **OpenAI**: [https://platform.openai.com/](https://platform.openai.com/)
   - **News API**: [https://newsapi.org/](https://newsapi.org/)
   - **Alpha Vantage** (optional): [https://www.alphavantage.co/](https://www.alphavantage.co/)

---

## ⚙️ One-Time Setup (10 minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/TKTINC/true_asset_alluse.git
cd true_asset_alluse/local-deployment
```

### Step 2: Run the Automated Setup Script

```bash
chmod +x setup_macos_enhanced.sh
./setup_macos_enhanced.sh
```

### Step 3: Configure API Keys (Optional - for Live Mode)

If you want to use live mode, edit the `.env.local` file:

```bash
# .env.local (only needed for live mode)

DATABENTO_API_KEY="YOUR_DATABENTO_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
NEWS_API_KEY="YOUR_NEWS_API_KEY"
ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"
```

---

## ▶️ Running the Application

### Quick Start (Mock Mode)

For immediate demonstration without any API setup:

```bash
./start_server.sh mock
```

This starts the system with realistic demo data - perfect for investor presentations.

### Live Mode (Real Services)

For full demonstration with real financial data:

```bash
./start_server.sh live
```

This connects to actual financial services and shows live data.

### Access the Application

Open your web browser and navigate to:

- **Dashboard**: [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)
- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Stop the Server

Press `Ctrl+C` in the terminal or run:

```bash
./stop_server.sh
```

---

## 🎯 Mode Comparison

### Mock Mode (`./start_server.sh mock`)
✅ **Instant startup** - No API dependencies  
✅ **Always works** - No external service issues  
✅ **Realistic data** - Professional-looking demo  
✅ **Zero cost** - Perfect for initial presentations  
✅ **Full UI** - Complete system demonstration  

**Perfect for:**
- Initial investor presentations
- Team onboarding
- System walkthroughs
- Quick demonstrations

### Live Mode (`./start_server.sh live`)
✅ **Real data** - Actual market information  
✅ **Live connections** - Working financial integrations  
✅ **AI responses** - Genuine OpenAI-powered analysis  
✅ **Market sentiment** - Real news and sentiment analysis  
✅ **Credible demo** - Shows actual business value  

**Perfect for:**
- Technical due diligence
- CTO demonstrations
- Proof of concept validation
- Investment committee presentations

---

## 🚀 Demonstration Walkthrough

### For Mock Mode Demos:
1. **System Overview**: "This is the actual True-Asset-ALLUSE production system running locally with demo data"
2. **Portfolio Dashboard**: Show the $1.2M portfolio with realistic positions
3. **AI Assistant**: Demonstrate the conversational interface
4. **System Architecture**: Explain that this is the real system, just with mock data
5. **Production Ready**: "The same code runs in production with live data"

### For Live Mode Demos:
1. **Real Data**: "This is live market data from professional sources"
2. **AI Analysis**: Show real AI responses based on actual portfolio data
3. **Market Intelligence**: Display live news sentiment and market conditions
4. **System Health**: Show actual service connections and status
5. **Business Value**: "This system is managing real money in paper trading mode"

---

## 🔧 Troubleshooting

### Mock Mode Issues:
- **Port in use**: Change port with `python local_main.py --mode mock --port 8001`
- **Import errors**: Make sure you're in the `local-deployment` directory

### Live Mode Issues:
- **API errors**: Check your `.env.local` file for correct API keys
- **IBKR connection**: Ensure TWS is running and configured for API access
- **Slow responses**: Live API calls can take time - this is normal

---

## 💡 Key Advantages

### Over Separate Demo Code:
✅ **Authentic**: Investors see the actual product  
✅ **Credible**: No "demo vs. reality" concerns  
✅ **Maintainable**: Single codebase to maintain  
✅ **Accurate**: True representation of capabilities  

### Over Full Cloud Deployment:
✅ **Cost-effective**: $0-600/month vs. $1,500+/month  
✅ **Quick setup**: 10 minutes vs. hours  
✅ **Local control**: No cloud dependencies  
✅ **Easy debugging**: Direct access to logs and data  

---

## 🌟 Conclusion

This enhanced local deployment gives you the best of both worlds:
- **Mock mode** for quick, reliable demonstrations
- **Live mode** for credible, real-data presentations
- **Production code** ensuring authenticity
- **Easy switching** between modes as needed

Perfect for building your team and raising funds while keeping costs minimal!


