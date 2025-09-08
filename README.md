# True-Asset-ALLUSE

**Rules-Based Autonomous Trading System**

A revolutionary rules-based autonomous trading system that represents the first TRUE ASSET in financial technology. Built using the proven ALL-USE methodology across 6 workstreams, implementing Constitution v1.3 with 100% deterministic rule execution.

## 🎯 Mission

Deliver the world's first TRUE ASSET with:
- **Income**: Weekly assurance from option premiums
- **Growth**: Compounding through forks, reinvestment, and scaling  
- **Autonomy**: Discipline enforced by deterministic rules and automated execution

## 🏗️ Architecture

### Three-Tiered Account System
- **Gen-Acc (40%)**: 40-45Δ CSP/CC, 0-1DTE, diversified across AAPL, MSFT, AMZN, GOOG, SPY, QQQ, IWM
- **Rev-Acc (30%)**: 30-35Δ CSP/CC, 3-5DTE, NVDA/TSLA focused
- **Com-Acc (30%)**: 20-25Δ CC, 5DTE, Mag-7 holdings with LLMS integration

### Key Components
- **Rules Engine**: Constitution v1.3 enforcement with zero AI trading decisions
- **Protocol Engine**: ATR-based risk management with 4-level escalation
- **State Machine**: SAFE→ACTIVE deterministic state management
- **LLMS**: Leap Ladder Management System for growth and hedging
- **Account Forking**: Automatic scaling at $100K (Gen) and $500K (Rev) thresholds

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/TKTINC/true_asset_alluse.git
   cd true_asset_alluse
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements/development.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Start PostgreSQL and Redis (or use Docker Compose)
   docker-compose up -d postgres redis
   
   # Run migrations
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   uvicorn src.main:app --reload
   ```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Run tests
docker-compose exec app pytest
```

## 📊 Constitution Compliance

This system implements **Constitution v1.3** with 100% rule-based decisions:

- **§0**: Global parameters (40/30/30 split, 95-100% capital deployment)
- **§1**: Weekly cadence (Thu/Wed/Mon schedule per account type)
- **§2-4**: Account-specific rules (Gen/Rev/Com strategies)
- **§5**: Hedging rules (5-10% budget, SPX puts + VIX calls)
- **§6**: Protocol Engine (ATR-based 4-level escalation)
- **§7**: Assignment protocol (automatic CC pivot)
- **§8**: Liquidity & data validation
- **§9**: SAFE→ACTIVE state machine
- **§10-17**: Tax, reporting, week typing, AI augmentation, LLMS

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

## 📈 Performance Targets

- **Returns**: 20-30% CAGR (2-year PoC target)
- **Uptime**: 99.5% during market hours
- **Compliance**: Zero regulatory violations
- **Automation**: <1% manual intervention required

## 🔧 Development

### Project Structure
```
src/
├── ws1_rules_engine/      # Constitution rule enforcement
├── ws2_protocol_engine/   # Risk management and escalation
├── ws3_account_management/# Account types and forking logic
├── ws4_trading_engine/    # Order management and execution
├── ws5_llms/             # Leap Ladder Management System
├── ws6_state_machine/    # SAFE→ACTIVE state management
├── common/               # Shared utilities and models
└── api/                  # REST API endpoints
```

### Development Workflow
1. **Constitution First**: Every feature must align with Constitution v1.3
2. **Test-Driven Development**: Write tests before implementation
3. **Immutable Audit Trail**: All decisions and actions logged
4. **Fail-Safe Design**: System defaults to SAFE state on errors

## 📋 Acceptance Criteria

### PoC Must Pass
- [x] Gen-Acc entry (Thu): CSPs 40-45Δ, 0-1DTE, liquidity filters
- [ ] Rev-Acc roll at Protocol-2: breach 2×ATR → roll within delta band
- [ ] Protocol Level-3 exit: stop-loss market exit, SAFE mode
- [ ] Assignment → CC pivot: assigned shares → CCs 20-25Δ, 5DTE
- [ ] Tiered VIX triggers: 52→Hedged Week, 66→SAFE, 81→Kill
- [ ] SAFE→ACTIVE resume: reconcile orphans, no duplicate orders
- [ ] Fork lifecycle: Gen +100K → MINI account → merge to Com
- [ ] LLMS ladder: LEAP calls 12-18M, puts 6-12M, quarterly reports
- [ ] Reporting: Weekly/Monthly/Quarterly outputs with natural language
- [ ] Liquidity rejection: order >10% ADV → trade skipped

## 🔐 Security & Compliance

- Non-custodial, software-only PoC
- Company capital only (no client funds)
- Encrypted data at rest and in transit
- Complete audit trail for regulatory compliance
- No self-modifying code in production

## 📚 Documentation

- [Constitution v1.3](docs/ALL-USE-Constitution-v1.3(1).md) - Immutable system law
- [System Overview](docs/ALL-USE-System-Overview-&-Story-v1.2(1).md) - Vision and philosophy
- [Architecture](docs/architecture/ALL-USERules-BasedSystemArchitecture&DesignDocument.md) - Technical design
- [PRD](docs/ALL-USEImplementationProductRequirementsDocument(PRD).md) - Product requirements
- [Technical Specs](docs/ALL-USETechnicalSpecifications&DevelopmentGuide.md) - Implementation guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Ensure Constitution v1.3 compliance
4. Write tests and ensure 95%+ coverage
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

Proprietary - All rights reserved. This software is proprietary and confidential.

## 🆘 Support

For technical support or questions:
- Create an issue in this repository
- Contact the development team
- Review the documentation in the `docs/` directory

---

**True-Asset-ALLUSE**: The first TRUE ASSET - because it doesn't just compound wealth, it compounds trust.

*Income each week (assurance). Growth each year (compounding). Autonomy forever (discipline).*

