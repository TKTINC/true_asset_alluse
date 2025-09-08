# ALL-USE Implementation Product Requirements Document (PRD)

**Version:** 2.0  
**Date:** September 2025  
**Alignment:** Constitution v1.3, System Story v1.2, Architecture v1.0  
**Implementation Type:** Rules-Based Deterministic System  

---

## 1. Document Control & Governance

### 1.1 Document Hierarchy
1. **Constitution v1.3** - Immutable law and single source of truth
2. **System Overview v1.2** - Vision, philosophy, and high-level architecture
3. **Implementation PRD v2.0** - Detailed functional and technical requirements
4. **System Architecture v1.0** - Technical design and implementation approach

### 1.2 Change Management
- All changes must align with Constitution v1.3
- Changes require: proposal → simulation/backtest → human approval → version increment
- No self-modifying code in production
- Changelog maintained for all versions

### 1.3 Stakeholders
- **Product Owner**: Vision, philosophy, business requirements
- **Engineering Lead**: Technical implementation, architecture decisions
- **Compliance Officer**: Regulatory adherence, audit requirements
- **QA Lead**: Testing, validation, acceptance criteria

---

## 2. Product Vision & Scope

### 2.1 Mission Statement
Build the world's first TRUE ASSET - a deterministic, rules-based autonomous trading system that delivers:
- **Income**: Weekly assurance from option premiums
- **Growth**: Compounding through forks, reinvestment, and scaling
- **Autonomy**: Discipline enforced by deterministic rules and automated execution

### 2.2 Core Principles
1. **100% Rules-Based**: No AI wealth management decisions, only rule execution
2. **Deterministic**: Same inputs always produce same outputs
3. **Transparent**: Every decision traceable to Constitution rules
4. **Resumable**: System can restart and continue from any point
5. **Auditable**: Complete audit trail for regulatory compliance

### 2.3 Scope Definition

#### 2.3.1 In Scope (PoC Phase)
- Single broker integration (IBKR only)
- 1x $200-300K primary account
- Up to 10x $100K accounts in Year 2
- Three-tiered account architecture (Gen/Rev/Com)
- LLMS (Leap Ladder Management System)
- Protocol Engine with ATR-based risk management
- SAFE→ACTIVE state machine
- Week typing and classification
- Natural language reporting (AI-powered)
- Anomaly detection (advisory only)

#### 2.3.2 Out of Scope (PoC Phase)
- Multi-broker integration
- Scaling beyond $5M AUM
- AI autonomous wealth management decisions
- Real-time algorithmic trading
- High-frequency trading capabilities
- Options market making
- Cryptocurrency trading
- International markets

### 2.4 Success Criteria
- **Technical**: 99.5% uptime during market hours
- **Performance**: 20-30% CAGR over 2-year PoC
- **Compliance**: Zero regulatory violations
- **Operational**: <1% manual intervention required
- **User Experience**: Weekly reports generated automatically

---

## 3. Functional Requirements

### 3.1 Account Management System

#### 3.1.1 Three-Tiered Architecture
```
Primary Account ($300K Example)
├── Gen-Acc (40% = $120K)
├── Rev-Acc (30% = $90K)  
└── Com-Acc (30% = $90K)
```

**Requirements:**
- **FR-AM-001**: System MUST enforce 40/30/30 split for new accounts
- **FR-AM-002**: System MUST support dynamic rebalancing quarterly
- **FR-AM-003**: Each account type MUST operate independently with distinct rules
- **FR-AM-004**: System MUST track performance metrics separately per account type
- **FR-AM-005**: Account balances MUST be updated real-time after each transaction

#### 3.1.2 Account Forking Logic

**Gen-Acc Forking:**
- **FR-AM-006**: System MUST fork Gen-Acc every +$100K over base capital
- **FR-AM-007**: Forked accounts MUST run as Mini ALL-USE with 50% Gen-style + 50% Com-style
- **FR-AM-008**: Mini ALL-USE MUST auto-merge to Com-Acc after 3 years OR 3x multiple
- **FR-AM-009**: Gen-Acc MUST NOT participate in quarterly reinvestment

**Rev-Acc Forking:**
- **FR-AM-010**: System MUST fork Rev-Acc every +$500K over base capital
- **FR-AM-011**: Forked Rev-Acc MUST create new full 40/30/30 ALL-USE account
- **FR-AM-012**: New ALL-USE accounts MUST have independent sub-accounts

#### 3.1.3 Position Sizing Rules
- **FR-AM-013**: System MUST deploy 95-100% of sleeve capital (NOT 2% position sizing)
- **FR-AM-014**: Per-symbol exposure MUST NOT exceed 25% of sleeve notional
- **FR-AM-015**: Order granularity MUST be auto-calculated by sleeve size
- **FR-AM-016**: Orders >50 contracts MUST be sliced automatically

### 3.2 Trading Rules Engine

#### 3.2.1 Gen-Acc Trading Rules
- **FR-TR-001**: Gen-Acc MUST trade CSPs only, 0-1DTE, 40-45Δ
- **FR-TR-002**: Entry window MUST be Thursday 9:45-11:00 ET
- **FR-TR-003**: Permitted instruments: AAPL, MSFT, AMZN, GOOG, SPY, QQQ, IWM
- **FR-TR-004**: System MUST skip CSPs on tickers with earnings that week
- **FR-TR-005**: Alternative stress-test mode: 1-3DTE (configurable)
- **FR-TR-006**: Upon assignment, MUST switch to CC-only until recovery

#### 3.2.2 Rev-Acc Trading Rules
- **FR-TR-007**: Rev-Acc MUST trade CSPs only, 3-5DTE, 30-35Δ
- **FR-TR-008**: Entry window MUST be Wednesday 9:45-11:00 ET
- **FR-TR-009**: Permitted instruments: NVDA, TSLA only
- **FR-TR-010**: Roll trigger: spot ≤ strike - 1.5× ATR(5)
- **FR-TR-011**: Upon assignment, MUST switch to CC 20-25Δ, 5DTE until recovery

#### 3.2.3 Com-Acc Trading Rules
- **FR-TR-012**: Com-Acc MUST trade CCs only, 20-25Δ, 5DTE
- **FR-TR-013**: Entry window MUST be Monday 9:45-11:00 ET
- **FR-TR-014**: Permitted instruments: Mag-7 (AAPL, MSFT, AMZN, GOOGL, NVDA, TSLA, META)
- **FR-TR-015**: Profit target: close at ≥65% premium decay
- **FR-TR-016**: Earnings week: reduce coverage to ≤50%
- **FR-TR-017**: Early assignment risk >80%: close at 30% profit

#### 3.2.4 Order Management Rules
- **FR-TR-018**: Orders MUST be placed at mid price
- **FR-TR-019**: Accept fills ≤5% worse than mid, else cancel/retry
- **FR-TR-020**: Cancel-replace timeout: 3 seconds
- **FR-TR-021**: Use idempotent clientOrderId with version suffix
- **FR-TR-022**: Slippage cap: 5% maximum

### 3.3 Protocol Engine (Risk Management)

#### 3.3.1 ATR-Based Escalation System
- **FR-PE-001**: System MUST calculate ATR(5) daily at 9:30 ET
- **FR-PE-002**: Fallback ATR = last valid × 1.1 if calculation fails
- **FR-PE-003**: Level 0 (Normal): within 1× ATR, monitor every 5 minutes
- **FR-PE-004**: Level 1 (Enhanced): breach 1× ATR, monitor every 1 minute
- **FR-PE-005**: Level 2 (Recovery): breach 2× ATR, execute roll + hedge
- **FR-PE-006**: Level 3 (Preservation): breach 3× ATR, stop-loss exit

#### 3.3.2 Roll Economics
- **FR-PE-007**: Do NOT roll if cost >50% of original credit
- **FR-PE-008**: Escalate to Level 3 instead of uneconomical rolls
- **FR-PE-009**: Roll to maintain delta band per account type
- **FR-PE-010**: Freeze new entries during Level 2+ escalations

#### 3.3.3 Hedging Rules
- **FR-PE-011**: Hedge budget: max(5-10% quarterly gains, 1% sleeve equity)
- **FR-PE-012**: Hedge instruments: SPX puts (6-12M, 10-20% OTM), VIX calls (6M)
- **FR-PE-013**: Hedge triggers: VIX >30 for 5 days, SPX drawdown ≥20%
- **FR-PE-014**: Release hedge if profit ≥200% or triggers revert

#### 3.3.4 Circuit Breakers
- **FR-PE-015**: VIX >50: Hedged Week mode (deployment halved)
- **FR-PE-016**: VIX >65: SAFE mode (no new entries)
- **FR-PE-017**: VIX >80: Full system halt (kill switch)
- **FR-PE-018**: User kill switch: per-account pause button

### 3.4 SAFE→ACTIVE State Machine

#### 3.4.1 State Definitions
- **FR-SM-001**: System MUST operate in defined states: SAFE, SCANNING, ANALYZING, ORDERING, MONITORING, CLOSING, RECONCILING
- **FR-SM-002**: Emergency states: EMERGENCY, MAINTENANCE, AUDIT
- **FR-SM-003**: All state transitions MUST be logged with timestamps
- **FR-SM-004**: System MUST be resumable from any interruption point

#### 3.4.2 State Transition Rules
- **FR-SM-005**: SAFE → SCANNING: Market hours begin, system health OK
- **FR-SM-006**: SCANNING → ANALYZING: Market data available, no circuit breakers
- **FR-SM-007**: ANALYZING → ORDERING: Trade opportunities identified, rules satisfied
- **FR-SM-008**: ORDERING → MONITORING: Orders placed successfully
- **FR-SM-009**: MONITORING → CLOSING: Profit targets hit or risk levels breached
- **FR-SM-010**: CLOSING → RECONCILING: Positions closed, orders canceled
- **FR-SM-011**: RECONCILING → SAFE: Ledger updated, reports generated

#### 3.4.3 Resume Flow
- **FR-SM-012**: Resume MUST follow: load snapshot → fetch broker state → reconcile → rebuild schedule → risk check → ACTIVE
- **FR-SM-013**: System MUST handle orphan orders during resume
- **FR-SM-014**: Ledger MUST remain consistent with broker state

### 3.5 LLMS (Leap Ladder Management System)

#### 3.5.1 LEAP Creation Rules
- **FR-LL-001**: Growth LEAPs: 0.25-0.35Δ calls, 12-18M expiry
- **FR-LL-002**: Hedge LEAPs: 10-20% OTM puts, 6-12M expiry
- **FR-LL-003**: Stagger expiries to avoid concentration
- **FR-LL-004**: Source: 25% of Rev-Acc and Com-Acc quarterly reinvestment

#### 3.5.2 Lifecycle Management
- **FR-LL-005**: Roll forward when TTE ≤3 months
- **FR-LL-006**: Roll when delta drifts outside 0.2-0.5 band
- **FR-LL-007**: Close hedge puts early if VIX <20 or triggers normalize
- **FR-LL-008**: Reinvest matured LEAPs into next ladder rung

#### 3.5.3 Optimization & Reporting
- **FR-LL-009**: AI MAY suggest optimization (requires human approval)
- **FR-LL-010**: Track hedge vs compounding LEAPs separately
- **FR-LL-011**: Generate quarterly ladder state reports
- **FR-LL-012**: Maintain dedicated LEAP ledger

### 3.6 Week Typing System

#### 3.6.1 Classification Rules
- **FR-WT-001**: System MUST classify each week deterministically
- **FR-WT-002**: Week types: Calm-Income, Roll, Assignment, Preservation, Hedged, Earnings-Filter
- **FR-WT-003**: Classification based on events: Protocol levels triggered, assignments, earnings filters
- **FR-WT-004**: Store classification in ledger with supporting events

#### 3.6.2 Prediction System (Optional)
- **FR-WT-005**: ML overlay MAY predict week-type probabilities after 50+ weeks
- **FR-WT-006**: Predictions are ADVISORY ONLY, never override rules
- **FR-WT-007**: Prediction accuracy MUST be tracked and reported

### 3.7 Quarterly Reinvestment System

#### 3.7.1 Reinvestment Rules
- **FR-QR-001**: Rev-Acc and Com-Acc MUST reinvest quarterly
- **FR-QR-002**: Reserve 30% for taxes before reinvestment
- **FR-QR-003**: Allocate 75% to additional contracts, 25% to LEAPs (via LLMS)
- **FR-QR-004**: Gen-Acc does NOT reinvest (profits accumulate until fork)

#### 3.7.2 Tax Management
- **FR-QR-005**: Calculate tax liability on realized gains
- **FR-QR-006**: Maintain separate tax reserve accounts
- **FR-QR-007**: Generate quarterly tax reports
- **FR-QR-008**: Track realized vs unrealized PnL separately

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements
- **NFR-P-001**: System MUST achieve 99.5% uptime during market hours
- **NFR-P-002**: Order placement latency MUST be <1 second end-to-end
- **NFR-P-003**: Market data processing MUST be <100ms
- **NFR-P-004**: Database queries MUST complete <500ms
- **NFR-P-005**: System MUST handle 1000+ concurrent positions

### 4.2 Scalability Requirements
- **NFR-S-001**: System MUST support up to 10 accounts in PoC phase
- **NFR-S-002**: Database MUST handle 100K+ transactions per year
- **NFR-S-003**: System MUST scale to $5M AUM without architecture changes
- **NFR-S-004**: LLMS MUST handle 500+ LEAP positions

### 4.3 Security Requirements
- **NFR-SEC-001**: All communications MUST use TLS 1.3+
- **NFR-SEC-002**: Secrets MUST be stored in encrypted vault
- **NFR-SEC-003**: Database MUST be encrypted at rest
- **NFR-SEC-004**: Multi-factor authentication REQUIRED for admin access
- **NFR-SEC-005**: API keys MUST rotate automatically every 90 days

### 4.4 Compliance Requirements
- **NFR-C-001**: Maintain immutable audit trail for 7 years
- **NFR-C-002**: Generate FINRA/SEC compliant reports
- **NFR-C-003**: All wealth management decisions MUST be traceable to Constitution rules
- **NFR-C-004**: Support regulatory examination requests
- **NFR-C-005**: Implement proper record retention policies

### 4.5 Data Requirements
- **NFR-D-001**: Market data MUST be real-time during trading hours
- **NFR-D-002**: Data retention: 7 years for compliance
- **NFR-D-003**: Backup MUST be performed daily
- **NFR-D-004**: Disaster recovery RTO: 4 hours, RPO: 1 hour
- **NFR-D-005**: Data validation MUST catch stale/corrupt data

---

## 5. Integration Requirements

### 5.1 IBKR Integration
- **IR-IB-001**: Connect via IBKR TWS API or IB Gateway
- **IR-IB-002**: Support paper trading and live trading modes
- **IR-IB-003**: Handle connection failures gracefully
- **IR-IB-004**: Implement order status tracking
- **IR-IB-005**: Support account summary and position queries

### 5.2 Market Data Integration
- **IR-MD-001**: Real-time quotes for stocks and options
- **IR-MD-002**: Historical data for ATR calculations
- **IR-MD-003**: Option chain data with Greeks
- **IR-MD-004**: Earnings calendar integration
- **IR-MD-005**: VIX data for circuit breakers

### 5.3 External Services
- **IR-ES-001**: Time synchronization with market hours
- **IR-ES-002**: Holiday calendar integration
- **IR-ES-003**: News feed for anomaly detection (optional)
- **IR-ES-004**: Economic calendar for earnings filter

---

## 6. AI Augmentation Requirements

### 6.1 Natural Language Reporting
- **AI-NL-001**: Generate human-readable explanations of system actions
- **AI-NL-002**: Answer user queries about wealth management decisions
- **AI-NL-003**: Explain Protocol Engine escalations
- **AI-NL-004**: Provide weekly/monthly narrative summaries

### 6.2 Anomaly Detection
- **AI-AD-001**: Monitor volatility spikes (advisory only)
- **AI-AD-002**: Detect correlation breakdowns (advisory only)
- **AI-AD-003**: Sentiment analysis alerts (advisory only)
- **AI-AD-004**: Regime shift detection (advisory only)

### 6.3 LLMS Optimization
- **AI-LO-001**: Analyze historical LEAP performance
- **AI-LO-002**: Suggest strike spacing optimizations
- **AI-LO-003**: Recommend expiry adjustments
- **AI-LO-004**: ALL suggestions REQUIRE human approval

### 6.4 AI Constraints
- **AI-C-001**: AI MUST NOT make autonomous wealth management decisions
- **AI-C-002**: AI MUST NOT override Constitution rules
- **AI-C-003**: All AI outputs MUST be logged and auditable
- **AI-C-004**: AI suggestions MUST require explicit human approval

---

## 7. User Interface Requirements

### 7.1 Dashboard Requirements
- **UI-D-001**: Real-time account balances and positions
- **UI-D-002**: Current system state display
- **UI-D-003**: Recent transactions and P&L
- **UI-D-004**: Protocol Engine status indicators
- **UI-D-005**: Week type classification display

### 7.2 Reporting Interface
- **UI-R-001**: Weekly automated reports
- **UI-R-002**: Monthly performance summaries
- **UI-R-003**: Quarterly tax and reinvestment reports
- **UI-R-004**: LEAP ladder status reports
- **UI-R-005**: Natural language query interface

### 7.3 Control Interface
- **UI-C-001**: User kill switch (per-account pause)
- **UI-C-002**: System status monitoring
- **UI-C-003**: Manual state transitions (emergency only)
- **UI-C-004**: Configuration management
- **UI-C-005**: Audit log viewer

---

## 8. Testing Requirements

### 8.1 Unit Testing
- **T-U-001**: 95%+ code coverage for all components
- **T-U-002**: Test all Constitution rule implementations
- **T-U-003**: Test Protocol Engine escalation logic
- **T-U-004**: Test state machine transitions
- **T-U-005**: Test LLMS lifecycle management

### 8.2 Integration Testing
- **T-I-001**: End-to-end trading workflow tests
- **T-I-002**: IBKR API integration tests
- **T-I-003**: Database integration tests
- **T-I-004**: Market data integration tests
- **T-I-005**: Backup and recovery tests

### 8.3 System Testing
- **T-S-001**: Full system operation for 2 paper trading cycles
- **T-S-002**: One complete live trading cycle
- **T-S-003**: State machine interruption and resume tests
- **T-S-004**: Circuit breaker activation tests
- **T-S-005**: Account forking and merging tests

### 8.4 Performance Testing
- **T-P-001**: Load testing with maximum positions
- **T-P-002**: Latency testing for order placement
- **T-P-003**: Database performance under load
- **T-P-004**: Memory usage optimization
- **T-P-005**: Concurrent user testing

---

## 9. Deployment Requirements

### 9.1 Environment Requirements
- **D-E-001**: Separate development, staging, and production environments
- **D-E-002**: Production environment MUST be isolated and secure
- **D-E-003**: Staging MUST mirror production configuration
- **D-E-004**: Development environment for testing and debugging

### 9.2 Infrastructure Requirements
- **D-I-001**: Container-based deployment (Docker)
- **D-I-002**: Orchestration with Docker Compose or Kubernetes
- **D-I-003**: Load balancing for high availability
- **D-I-004**: Automated backup and monitoring
- **D-I-005**: SSL certificates and security hardening

### 9.3 Monitoring Requirements
- **D-M-001**: Application performance monitoring
- **D-M-002**: System resource monitoring
- **D-M-003**: Trading performance monitoring
- **D-M-004**: Error tracking and alerting
- **D-M-005**: Audit log monitoring

---

## 10. Acceptance Criteria

### 10.1 Technical Acceptance
- **AC-T-001**: Two complete paper trading cycles executed successfully
- **AC-T-002**: One complete live trading cycle with real money
- **AC-T-003**: Weekly reports generated automatically and accurately
- **AC-T-004**: SAFE→ACTIVE state machine tested with interruptions
- **AC-T-005**: Account forking executed at least once in simulation
- **AC-T-006**: LLMS ladder created and managed successfully

### 10.2 Business Acceptance
- **AC-B-001**: System operates autonomously for 30 consecutive days
- **AC-B-002**: All trades comply with Constitution rules
- **AC-B-003**: Performance tracking shows expected returns
- **AC-B-004**: Risk management prevents major losses
- **AC-B-005**: Reporting provides clear insights to users

### 10.3 Compliance Acceptance
- **AC-C-001**: Audit trail passes regulatory review
- **AC-C-002**: All required reports generated correctly
- **AC-C-003**: Security measures meet industry standards
- **AC-C-004**: Data retention policies implemented
- **AC-C-005**: Disaster recovery procedures tested

---

## 11. Risk Management

### 11.1 Technical Risks
- **Risk**: IBKR API failures
- **Mitigation**: Graceful degradation, connection retry logic, manual override capability

- **Risk**: Market data feed interruptions
- **Mitigation**: Multiple data sources, fallback to last valid data with buffers

- **Risk**: System crashes during trading
- **Mitigation**: State machine resume capability, transaction logging, position reconciliation

### 11.2 Business Risks
- **Risk**: Regulatory changes affecting options trading
- **Mitigation**: Compliance monitoring, rule flexibility, legal review process

- **Risk**: Market conditions exceeding historical norms
- **Mitigation**: Circuit breakers, conservative position sizing, hedge mechanisms

- **Risk**: Performance below expectations
- **Mitigation**: Backtesting validation, gradual capital deployment, performance monitoring

### 11.3 Operational Risks
- **Risk**: Human error in system configuration
- **Mitigation**: Configuration validation, change approval process, rollback capability

- **Risk**: Security breaches
- **Mitigation**: Multi-layer security, regular audits, incident response plan

---

## 12. Success Metrics

### 12.1 Performance Metrics
- **Target CAGR**: 20-30% over 2-year PoC period
- **Maximum Drawdown**: <15% per Constitution
- **Sharpe Ratio**: >1.5 target
- **Win Rate**: >65% for CSP strategies
- **Profit Factor**: >1.8 target

### 12.2 Operational Metrics
- **System Uptime**: 99.5% during market hours
- **Order Fill Rate**: >98% within slippage tolerance
- **Manual Intervention**: <1% of wealth management decisions
- **Report Generation**: 100% automated and on-time
- **Error Rate**: <0.1% of transactions

### 12.3 User Experience Metrics
- **Report Clarity**: User satisfaction >90%
- **Query Response Time**: <5 seconds for natural language queries
- **Dashboard Load Time**: <2 seconds
- **Mobile Responsiveness**: Support for all major devices

---

This comprehensive PRD provides the detailed requirements needed to implement the TRUE ALL-USE system exactly as specified in your Constitution and System Overview documents.

