# ALL-USE System Overview & Story (v1.2)

---

## 1. Origin & Mission
ALL-USE (Autonomous Lumpsum Leveraged US Equities) began with a simple observation:  
Most “assets” don’t feel like assets anymore.  

- Equities swing violently.  
- Bonds stagnate.  
- Real estate locks up liquidity.  
- Commodities speculate.  
- Crypto whipsaws.  

True assets should be **safe, assuring, and growing**. ALL-USE’s mission is to restore that definition — delivering income + growth + autonomy in one product.

---

## 2. Core Philosophy
- **Income:** Weekly assurance from option premiums.  
- **Growth:** Compounding through forks, reinvestment, and scaling.  
- **Autonomy:** Discipline enforced by deterministic rules and automated execution.  

---

## 3. Architecture at a Glance
Capital is divided into three sleeves:

- **Gen-Acc (Generator):** 40–45Δ CSP/CC, 0–1DTE (alt: 1–3DTE stress-test), diversified across AAPL, MSFT, AMZN, GOOG, SPY, QQQ, IWM.  
- **Rev-Acc (Revenue):** 30–35Δ CSP/CC, 3–5DTE, on NVDA and TSLA.  
- **Com-Acc (Compounding):** 20–25Δ CCs, 5DTE, on Mag-7; quarterly reinvest into contracts and LEAPs (managed by LLMS).  

**Forks:**  
- Gen forks +100K → spin mini-ALL-USEs (run ≤3 years or 3×, then merge to Com).  
- Rev forks +500K → new full 40/30/30 ALL-USE accounts.  

**LLMS (Leap Ladder Management System/Service):**  
- Manages lifecycle of LEAPs (growth + hedge).  
- Handles entry, laddering, lifecycle, rolls, reporting.  
- AI-assisted optimization over time.  

---

## 4. Risk & Protocol Engine
The **Protocol Engine** governs every position using ATR-based escalation:

- **Level 0:** Normal → hold, monitor every 5m.  
- **Level 1:** Enhanced monitoring → prep roll candidates.  
- **Level 2:** Recovery → execute roll, add hedge, freeze new entries.  
- **Level 3:** Preservation → stop-loss exit, SAFE mode until reset.  

**Covered Calls Protocol:**  
- 65% profit or 1DTE = close.  
- Earnings week = reduce coverage to 50%.  
- Early assignment risk >80% = close early.  
- If called away = re-enter CSP next cycle.  

---

## 5. SAFE→ACTIVE State Machine
ALL-USE never operates ad hoc. Every cycle flows through a state machine:

SAFE → SCANNING → ANALYZING → ORDERING → MONITORING → CLOSING → RECONCILING → SAFE  

- **EMERGENCY:** triggered on black swan events (e.g., VIX >80).  
- **MAINTENANCE:** for system upgrades.  
- **AUDIT:** periodic reconciliation with broker + ledger.  

This design ensures deterministic, resumable autonomy.  

---

## 6. Week Typing Protocol
Each week is classified by type, stored in the ledger, and reported:

- Calm-Income  
- Roll Week  
- Assignment Week  
- Preservation Week  
- Hedged Week  
- Earnings-Filter Week  

Over time, AI analyzes week types to detect regimes and **predict probabilities** of upcoming conditions (advisory only, never overrides rules).

---

## 7. AI Augmentation
AI enhances the user and ops experience:

- **Natural Language Reports:** Users ask, *“Why did Gen-Acc pivot last week?”* → AI narrates market conditions + Protocol Engine actions.  
- **Anomaly Detection:** AI scans volatility, correlations, sentiment. Flags regime shifts early, advisory only.  
- **LLMS Optimization:** AI reviews historical LEAP ladder performance and suggests refinements. Requires human approval.  

---

## 8. Practical Scaling
- **Gen-Acc:** Feasible up to ~$1M diversified across 6–7 tickers.  
- **Rev-Acc:** $2–3M via pods and order slicing.  
- **Com-Acc:** $20–50M easily.  
- **Forks:** Expect ≤8 sub-accounts in 10 years per user.  

**Liquidity Rules:** OI ≥500, vol ≥100/day, spread ≤5%, reject if order >10% ADV.  

---

## 9. Safety & Kill Switches
- **User Kill Switch:** Per-account “pause button.” Cancels orders, SAFE mode.  
- **System Kill Switch:** Global halt with tiered triggers:  
  - VIX >50 → Hedged Week.  
  - VIX >65 → SAFE mode.  
  - VIX >80 → Full halt.  

---

## 10. User Flow
1. User links IBKR account.  
2. ALL-USE provisions sub-accounts (Gen, Rev, Com, forks).  
3. Protocol Engine + cadence rules execute autonomously.  
4. System logs trades, week types, tax ledgers, LEAP ladders (via LLMS).  
5. Reports delivered weekly/monthly/quarterly, in numbers + natural language.  
6. User input not required; oversight optional.  

---

## 11. Differentiation
- **Hedge Funds:** opaque, people-driven, inconsistent discipline.  
- **Robo-Advisors:** passive, low-return, generic ETFs.  
- **ALL-USE:** deterministic, autonomous, compounding engine. Income every week, growth every year, assurance always.  

---

## 12. Vision Forward
- **2-Year Proof:** $200–300K PoC account, audited 20–30% CAGR.  
- **Scaling:** 10×100K accounts in Year 2, prove repeatability.  
- **Expansion:** WLTH integration — Wealth as anchor, with Legacy, Travel, Health agents.  

---

## 13. Bottom Line
ALL-USE is the **first true Asset** — because it doesn’t just compound wealth, it compounds trust.  

- Income each week (assurance).  
- Growth each year (compounding).  
- Autonomy forever (discipline).  

---
