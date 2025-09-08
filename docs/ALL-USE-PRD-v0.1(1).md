# ALL-USE Product Requirements Document (PRD v0.1)

---

## 1. Document Control
- **Product:** ALL-USE (Autonomous Lumpsum Leveraged US Equities)  
- **Version:** PRD v0.1  
- **Alignment:** Constitution v1.3, System Story v1.2  
- **Owners:** Product (vision & philosophy), Engineering (execution), Compliance (regulatory & audit)  
- **Change Process:** PRD changes must follow Constitution governance (proposal → simulation/backtest → approval → version increment).  

---

## 2. Purpose & Scope
- **Purpose:** Define all functional and non-functional requirements for the ALL-USE Proof-of-Concept (PoC).  
- **Scope:**  
  - 2-year PoC.  
  - 1x 200–300K account + up to 10x 100K accounts in Year 2.  
  - Broker: IBKR only for PoC.  
- **Non-Goals:**  
  - Scaling beyond $5M AUM.  
  - Multi-broker integration.  
  - AI models trading autonomously (AI is explain/alert/suggest only).  

---

## 3. Product Overview
- **Core Mission:** Deliver a true asset with income + growth + autonomy.  
- **Architecture:**  
  - **Gen-Acc (Generator):** 40–45Δ CSP/CC, 0–1DTE (alt 1–3DTE stress-test).  
  - **Rev-Acc (Revenue):** 30–35Δ CSP/CC, 3–5DTE (NVDA/TSLA).  
  - **Com-Acc (Compounding):** 20–25Δ CCs, 5DTE (Mag-7).  
  - **LLMS (Leap Ladder Management System):** manages lifecycle of LEAPs (growth & hedge).  
- **Risk Controls:** Protocol Engine, SAFE→ACTIVE state machine, tiered circuit breakers.  
- **AI Augmentation:** Natural language reports, anomaly alerts, LLMS optimization.  

---

## 4. Functional Requirements

### 4.1 Trading Rules Engine

#### Gen-Acc
- **Entry:** CSPs, 0–1DTE, 40–45Δ, Thursdays 9:45–11:00.  
- **Stress-Test Mode:** optional 1–3DTE for validation.  
- **Roll Trigger:** ATR(5) breach → Level 1 (prep), Level 2 (roll).  
- **Assignment:** switch to CC-only until break-even or within 5% equity recovery.  
- **Forks:** +100K increments → mini ALL-USE. Run ≤3 years or until 3×, then merge to Com.  

#### Rev-Acc
- **Entry:** CSPs, 3–5DTE, 30–35Δ, Wednesdays 9:45–11:00.  
- **Roll Trigger:** ATR(5) breach 1.5× → prep/roll.  
- **Assignment:** switch to CC-only until recovery.  
- **Quarterly Reinvest:** 30% tax reserve, 70% reinvest (75% contracts, 25% LEAPs managed by LLMS).  
- **Forks:** +500K increments → new 40/30/30 ALL-USE with own subs.  

#### Com-Acc
- **Entry:** CCs, 20–25Δ, 5DTE, Mondays 9:45–11:00.  
- **Profit-Take:** ≥65% decay.  
- **Earnings Weeks:** coverage ≤50%.  
- **Quarterly Reinvest:** 30% tax reserve, 70% reinvest (75% contracts, 25% LEAPs managed by LLMS).  

#### LLMS
- **Purpose:** manage LEAPs lifecycle (growth + hedge).  
- **Entry:** Calls: 0.25–0.35Δ, 12–18M expiry. Hedge puts: 10–20% OTM, 6–12M expiry.  
- **Laddering:** stagger expiries, roll when TTE ≤3M or delta drifts outside 0.2–0.5.  
- **Close Rules:** hedge puts closed early if VIX <20 or hedge triggers normalize.  
- **Reporting:** quarterly ladder summary, separate hedge vs compounding LEAPs.  

**Acceptance Criteria:**  
- Orders at mid; accept ≤5% worse.  
- Cancel-replace if no ack in 3s.  
- Trades rejected if: OI <500, vol <100/day, spread >5% mid, or order >10% ADV.  

---

### 4.2 Risk Management (Protocol Engine)
- **Levels:**  
  - L0: normal monitoring.  
  - L1: enhanced monitoring.  
  - L2: recovery (roll + hedge).  
  - L3: preservation (stop-loss exit, SAFE).  
- **Covered Calls Protocol:** profit-take, early assignment close, reduced coverage on earnings, re-entry CSP.  
- **Hedging:** triggered at L2. SPX puts 1% sleeve, VIX calls 0.5% sleeve, ≥1% equity floor.  
- **Circuit Breakers:** tiered (VIX 50 → Hedged Week; VIX 65 → SAFE; VIX 80 → Kill).  

**Acceptance Criteria:**  
- Escalation deterministic (no skips).  
- Hedge applied automatically at L2.  
- Preservation halts new entries.  
- Circuit breaker response logged in ledger.  

---

### 4.3 SAFE→ACTIVE State Machine
- **States:** SAFE → SCANNING → ANALYZING → ORDERING → MONITORING → CLOSING → RECONCILING → SAFE.  
- **Extensions:** EMERGENCY, MAINTENANCE, AUDIT.  
- **Resume Flow:** load snapshot → fetch broker → reconcile → risk check → ACTIVE.  

**Acceptance Criteria:**  
- Restart yields consistent ledger vs broker.  
- Orphan orders canceled, no duplicates.  
- State transitions logged.  

---

### 4.4 Reporting
- **Weekly:** trades, forks, income, week type.  
- **Monthly:** CAGR YTD, DD, Sharpe/Sortino.  
- **Quarterly:** tax ledger, reinvests, hedge summary, LEAP ladder state.  
- **Natural Language Reports:** user queries answered by AI from ledger.  

**Acceptance Criteria:**  
- CSV + PDF + API delivery.  
- Realized vs unrealized PnL separated.  
- Week type labeled.  
- LEAP ledger included in quarterly reports.  

---

### 4.5 Week Typing Protocol
- **Types:** Calm-Income, Roll, Assignment, Preservation, Hedged, Earnings-Filter.  
- **Triggers:**  
  - Roll Week = Protocol 2 executed.  
  - Assignment Week = CC pivot triggered.  
  - Preservation Week = Protocol 3 executed.  
  - Hedged Week = hedge deployed.  
  - Earnings-Filter Week = CSPs skipped.  
  - Calm-Income Week = no escalations.  
- **Output:** ledger entry + report tag.  

**Acceptance Criteria:**  
- Every week labeled deterministically.  
- ML overlay allowed for predictions (advisory only).  

---

### 4.6 AI Augmentation
- **Natural Language Reports:** explain trades, pivots, protocol actions.  
- **Anomaly Detection:** advisory alerts on vol, correlations, sentiment.  
- **LLMS Optimization:** AI suggestions for LEAP ladder adjustments.  

**Acceptance Criteria:**  
- AI cannot auto-trade or override rules.  
- All AI outputs logged.  

---

## 5. Non-Functional Requirements
- **Availability:** 99.5% uptime market hours.  
- **Latency:** Orders <1s end-to-end.  
- **Security:** TLS, secrets vault, MFA.  
- **Compliance:** immutable ledger, audit-ready logs, changelog versioning.  
- **Data Retention:** 7 years (FINRA/SEC standard).  

---

## 6. Governance
- Constitution = single source of truth.  
- PRD changes must align with Constitution.  
- Changelog required for each version.  

---

## 7. Engineering Acceptance (for PoC)
- Two paper cycles + one live cycle executed cleanly.  
- Weekly reports generated error-free.  
- SAFE→ACTIVE tested with outage.  
- Fork executed once in sim.  
- LLMS ladder created + reported once.  

---
