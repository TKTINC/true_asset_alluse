# ALL-USE Constitution v1.3

---

## 🔄 Changelog (v1.2 → v1.3)

1. **LLMS (Leap Ladder Management System/Service) Added:**  
   - Manages lifecycle of LEAPs (growth + hedge).  
   - Defines entry, laddering, lifecycle management, optimization, and reporting.  
2. **Clarified AI Optimization:** “LLMS Optimization” = AI-assisted LEAP ladder analysis, requires human approval.  
3. **Story alignment:** Constitution and System Story both reference LLMS explicitly.  

---

## §0 Global Parameters

- **Base Split:** 40/30/30 → Gen/Rev/Com.  
- **Sizing:** Deploy up to 95–100% of sleeve capital across permitted tickers.  
- **Per-Symbol Exposure:** ≤25% of sleeve notional.  
- **Order Granularity:** auto-calculated by sleeve size; slice if >50 contracts.  
- **Slippage Cap:** place at mid; accept ≤5% worse; else cancel/retry smaller clip.  
- **Cancel-Replace Timeout:** 3s; idempotent clientOrderId with version suffix.  
- **Kill Switch:**  
  - *User-facing:* per-account pause, cancels live orders, SAFE mode.  
  - *System-wide:* tiered circuit breakers (see §6).  
- **Drawdown Pivot:** if sleeve equity ≤ –15% from high *and* VIX <30 → suspend CSPs, CC-only until recovery.  
- **Risk Limits:**  
  - Max margin use: ≤60%.  
  - Portfolio delta: uncapped (bounded by sleeve rules).  
- **Monitoring Frequency:**  
  - Level 0: 5m  
  - Level 1: 1m  
  - Level 2: 30s during rolls  
  - Level 3: real-time until exit.  

---

## §1 Weekly Cadence

| Account | Day/Time | Action |
|---|---|---|
| **Gen-Acc** | Thu 9:45–11:00 | Open 0–1DTE CSPs, 40–45Δ, across AAPL, MSFT, AMZN, GOOG, SPY, QQQ, IWM. (Alt stress-test: 1–3DTE) |
| **Rev-Acc** | Wed 9:45–11:00 | Open 3–5DTE CSPs, 30–35Δ, on NVDA, TSLA. |
| **Com-Acc** | Mon 9:45–11:00 | Write 5DTE CCs, 20–25Δ, on Mag-7 holdings. |
| **All** | Fri 14:30–15:45 | Manage/close to avoid pin risk; weekly report cut 16:30. |

**Earnings Filter:** Skip CSPs on tickers with earnings that week.  
**Early Close:** Shift cadence forward 2h.  

---

## §2 Gen-Acc Rules

- **Sizing:** Deploy up to 95–100% of sleeve across diversified tickers.  
- **Entry:** CSPs, 0–1DTE, 40–45Δ. (Alt: 1–3DTE for stress-testing).  
- **Roll Trigger:** if spot ≤ strike – 1× ATR(5) → prep roll.  
- **Assignment:** if assigned → switch to CCs, 20–25Δ, 5DTE, until break-even or within 5% of pre-drawdown equity.  
- **Pivot:** if drawdown ≥15% → CSPs suspended, CC-only until recovery.  
- **Fork:** each +100K over base → fork mini ALL-USE. Mini runs ≤3 years or until 3×, then merges to Com. No reinvesting.  

---

## §3 Rev-Acc Rules

- **Sizing:** Deploy up to 95–100% of sleeve.  
- **Entry:** CSPs, 3–5DTE, 30–35Δ, NVDA/TSLA.  
- **Roll Trigger:** if spot ≤ strike – 1.5× ATR(5).  
- **Assignment:** switch to CCs 20–25Δ, 5DTE until recovery.  
- **Quarterly Reinvest:** 30% tax reserve; 70% reinvest → 75% to contracts, 25% to LEAPs (managed by LLMS).  
- **Fork:** +500K over base → create new 40/30/30 ALL-USE account with its own subs.  

---

## §4 Com-Acc Rules

- **Entry:** CCs, 20–25Δ, 5DTE, on Mag-7 (AAPL, MSFT, AMZN, GOOGL, NVDA, TSLA, META).  
- **Profit-Take:** close if ≥65% premium decay.  
- **Earnings:** reduce CC coverage to ≤50%.  
- **Quarterly Reinvest:** 30% tax reserve; 70% reinvest (75% to contracts, 25% to LEAPs managed by LLMS).  

---

## §5 Hedging Rules

- **Budget:** greater of (5–10% of quarterly net gains OR 1% of sleeve equity).  
- **Instruments:** SPX puts (6–12M, 10–20% OTM), VIX calls (6M).  
- **Triggers:**  
  - VIX >30 for 5d.  
  - SPX drawdown ≥20%.  
  - Breadth (% S&P >50DMA) <20%.  
- **Management:** release hedge if profit ≥200% or triggers revert.  
- **LLMS Role:** Manages hedge LEAP puts lifecycle.  

---

## §6 Protocol Engine

- **Level 0 (Normal):** within 1× ATR → hold, monitor every 5m.  
- **Level 1 (Enhanced):** breach 1× ATR → monitor 1m, pre-compute roll.  
- **Level 2 (Recovery):** breach 2× ATR → roll to delta band, add hedge, freeze new entries.  
- **Level 3 (Preservation):** breach 3× ATR → stop-loss exit, SAFE mode until reset.  

**Covered Calls (CC Protocol):**  
- Level 0: hold until 65% profit or 1DTE.  
- Level 1: if early assignment risk >80% → close at 30% profit.  
- Level 2: if earnings week → reduce coverage to 50%.  
- Level 3: if called away → re-enter via CSP next cycle.  

**ATR Spec:** ATR(5), daily at 9:30 ET, fallback = last valid ×1.1.  

**Roll Economics:** do not roll if cost >50% of original credit; escalate to Level 3 instead.  

**Hedge Trigger:** any Level 2 breach. Hedge sizing = 1% SPX puts, 0.5% VIX calls, cap 5% of quarterly gains or min 1% sleeve equity.  

**Circuit Breakers (tiered):**  
- VIX >50 → Hedged Week mode (deployment halved, only defensive rolls).  
- VIX >65 → SAFE mode (no new entries).  
- VIX >80 → Kill switch (full system halt).  

---

## §7 Assignment Protocol

- Prep: Friday 3pm if ITM >95% → log, prep for assignment.  
- If assigned: log event, switch to CC 20Δ, 5DTE.  
- Resume CSP eligibility after shares called away.  

---

## §8 Liquidity & Data Validation

- **Liquidity Checks:**  
  - OI ≥500, vol ≥100/day, spread ≤5% of mid.  
  - Reject if order size >10% of average daily option volume.  
- **Data Failures:**  
  - Stale >30s → use last valid + buffer.  
  - No ATR → use 2% of price.  
  - Missing option chain → skip trade.  
  - Broker API down → SAFE mode.  

---

## §9 SAFE→ACTIVE State Machine

**States:** SAFE → SCANNING → ANALYZING → ORDERING → MONITORING → CLOSING → RECONCILING → SAFE.  
- **EMERGENCY:** black swan halt.  
- **MAINTENANCE:** manual patch/upgrade.  
- **AUDIT:** periodic reconciliation checks.  

**Resume Flow:** load snapshot → fetch broker state → reconcile → rebuild schedule → risk check → ACTIVE.  

---

## §10 Tax & Ledger

- **Gen-Acc:** no reinvest; profits accumulate until fork.  
- **Rev-Acc & Com-Acc:** quarterly reinvest after tax reserve.  
- **Ledger:** realized vs unrealized PnL separated; audit-ready CSV.  

---

## §11 Reporting

- **Weekly:** trades, forks, income, week type.  
- **Monthly:** CAGR YTD, DD, Sharpe/Sortino.  
- **Quarterly:** tax ledger, reinvests, hedge summary.  
- **Natural Language Reports:** AI answers user queries (“Why did Gen-Acc pivot last week?”).  

---

## §12 Week Typing Protocol

Each week labeled as one of: Calm-Income, Roll, Assignment, Preservation, Hedged, Earnings-Filter.  
Stored in ledger + reported to user.  
ML overlay may predict week-type probabilities after 50+ weeks. Advisory only.  

---

## §13 AI Augmentation

- **Natural Language Reports:** AI translates ledger into user-facing answers.  
- **Anomaly Detection:** monitors vol/correlation/news; advisory alerts only.  
- **LLMS Optimization:** AI analyzes historical LEAP ladder performance and suggests refinements. Requires human approval.  

---

## §14 Compliance & Ops

- Non-custodial, software-only PoC. Company capital only.  
- No self-modifying code in prod.  
- Secrets managed, CI scans.  
- Ops runbook defines handling of stale data, orphan orders, margin breach.  

---

## §15 Governance & Versioning

- Constitution is immutable law.  
- Any change must follow: proposal → simulation/backtest → human approval → version increment.  
- Changelog maintained at top of document.  

---

## §16 Engineering Acceptance

- Two weekly cycles in paper, one live cycle.  
- Weekly report must generate.  
- Idempotent order flow verified.  
- SAFE→ACTIVE tested.  
- Fork→mini→merge executed at least once in sim.  

---

## §17 Leap Ladder Management System (LLMS)

**Purpose:** Manage lifecycle of LEAPs created via Rev/Com reinvestments and hedge allocations.  

**Responsibilities:**  
1. **Entry Rules:**  
   - Calls: 0.25–0.35Δ, 12–18M expiry.  
   - Hedge puts: 10–20% OTM, 6–12M expiry.  
2. **Laddering:** stagger expiries to avoid concentration; reinvest matured LEAPs into next rung.  
3. **Lifecycle Management:** roll forward when TTE ≤3M or delta drifts outside 0.2–0.5 band. Close hedge puts early if hedge criteria normalize.  
4. **Optimization:** AI suggests adjustments (strike spacing, expiry). Requires human approval.  
5. **Reporting:** dedicated LEAP ledger; quarterly ladder state; hedge vs compounding LEAPs tracked separately.  

---
