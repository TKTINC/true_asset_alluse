# ALL-USE Technical Specifications & Development Guide

**Version:** 1.0  
**Date:** September 2025  
**Alignment:** Constitution v1.3, PRD v2.0, Architecture v1.0  
**Implementation Type:** Rules-Based Deterministic System  

---

## 1. Development Overview

### 1.1 Project Structure
```
all-use-rules-based/
├── src/
│   ├── rules_engine/           # Constitution rule enforcement
│   ├── protocol_engine/        # Risk management and escalation
│   ├── state_machine/          # SAFE→ACTIVE state management
│   ├── account_management/     # Account types and forking logic
│   ├── llms/                   # Leap Ladder Management System
│   ├── trading/                # Order management and execution
│   ├── market_data/            # Data feeds and validation
│   ├── reporting/              # Report generation and AI
│   ├── integrations/           # IBKR and external APIs
│   └── utils/                  # Common utilities
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── system/                 # End-to-end tests
├── config/
│   ├── development.yaml        # Dev environment config
│   ├── staging.yaml           # Staging environment config
│   └── production.yaml        # Production environment config
├── docs/
│   ├── api/                   # API documentation
│   ├── deployment/            # Deployment guides
│   └── operations/            # Operations runbooks
├── scripts/
│   ├── setup/                 # Environment setup scripts
│   ├── deployment/            # Deployment automation
│   └── maintenance/           # Maintenance scripts
├── docker/
│   ├── Dockerfile             # Application container
│   ├── docker-compose.yml     # Local development
│   └── docker-compose.prod.yml # Production deployment
└── requirements/
    ├── base.txt               # Core dependencies
    ├── development.txt        # Dev dependencies
    └── production.txt         # Production dependencies
```

### 1.2 Technology Stack

#### 1.2.1 Core Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI for REST APIs
- **Database**: PostgreSQL 13+ for primary data
- **Cache**: Redis 6+ for session and market data
- **Message Queue**: RabbitMQ for async processing
- **Container**: Docker with Docker Compose

#### 1.2.2 Key Libraries
```python
# Core Dependencies
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
pydantic==2.5.0

# Trading & Market Data
ib-insync==0.9.86
pandas==2.1.3
numpy==1.25.2
ta-lib==0.4.28

# AI & ML
openai==1.3.7
langchain==0.0.340
scikit-learn==1.3.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Monitoring
prometheus-client==0.19.0
structlog==23.2.0
```

### 1.3 Development Principles
1. **Constitution First**: Every feature must align with Constitution v1.3
2. **Test-Driven Development**: Write tests before implementation
3. **Immutable Audit Trail**: All decisions and actions logged
4. **Fail-Safe Design**: System defaults to SAFE state on errors
5. **Deterministic Behavior**: Same inputs always produce same outputs

---

## 2. Core Component Specifications

### 2.1 Rules Engine Implementation

#### 2.1.1 Constitution Parser
```python
# src/rules_engine/constitution.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class AccountType(Enum):
    GEN_ACC = "gen_acc"
    REV_ACC = "rev_acc"
    COM_ACC = "com_acc"
    MINI_ALLUSE = "mini_alluse"

@dataclass
class TradingRule:
    account_type: AccountType
    strategy: str  # CSP, CC
    delta_min: float
    delta_max: float
    dte_min: int
    dte_max: int
    entry_day: str  # Monday, Tuesday, etc.
    entry_time_start: str  # "09:45"
    entry_time_end: str  # "11:00"
    permitted_symbols: List[str]
    position_size_pct: float  # 0.95-1.0 for 95-100%
    max_symbol_exposure_pct: float  # 0.25 for 25%

class ConstitutionV13:
    def __init__(self):
        self.global_params = self._load_global_params()
        self.trading_rules = self._load_trading_rules()
        self.protocol_rules = self._load_protocol_rules()
        self.hedging_rules = self._load_hedging_rules()
    
    def _load_trading_rules(self) -> Dict[AccountType, TradingRule]:
        return {
            AccountType.GEN_ACC: TradingRule(
                account_type=AccountType.GEN_ACC,
                strategy="CSP",
                delta_min=0.40,
                delta_max=0.45,
                dte_min=0,
                dte_max=1,
                entry_day="Thursday",
                entry_time_start="09:45",
                entry_time_end="11:00",
                permitted_symbols=["AAPL", "MSFT", "AMZN", "GOOG", "SPY", "QQQ", "IWM"],
                position_size_pct=0.975,  # 97.5% average of 95-100%
                max_symbol_exposure_pct=0.25
            ),
            AccountType.REV_ACC: TradingRule(
                account_type=AccountType.REV_ACC,
                strategy="CSP",
                delta_min=0.30,
                delta_max=0.35,
                dte_min=3,
                dte_max=5,
                entry_day="Wednesday",
                entry_time_start="09:45",
                entry_time_end="11:00",
                permitted_symbols=["NVDA", "TSLA"],
                position_size_pct=0.975,
                max_symbol_exposure_pct=0.25
            ),
            AccountType.COM_ACC: TradingRule(
                account_type=AccountType.COM_ACC,
                strategy="CC",
                delta_min=0.20,
                delta_max=0.25,
                dte_min=5,
                dte_max=5,
                entry_day="Monday",
                entry_time_start="09:45",
                entry_time_end="11:00",
                permitted_symbols=["AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "TSLA", "META"],
                position_size_pct=0.975,
                max_symbol_exposure_pct=0.25
            )
        }
    
    def get_trading_rule(self, account_type: AccountType) -> TradingRule:
        return self.trading_rules[account_type]
    
    def validate_trade_eligibility(self, account_type: AccountType, symbol: str, 
                                 delta: float, dte: int, current_time: str) -> bool:
        rule = self.get_trading_rule(account_type)
        
        # Symbol validation
        if symbol not in rule.permitted_symbols:
            return False
        
        # Delta validation
        if not (rule.delta_min <= delta <= rule.delta_max):
            return False
        
        # DTE validation
        if not (rule.dte_min <= dte <= rule.dte_max):
            return False
        
        # Time validation
        if not self._is_valid_entry_time(rule, current_time):
            return False
        
        return True
    
    def _is_valid_entry_time(self, rule: TradingRule, current_time: str) -> bool:
        # Implementation for time validation
        pass
```

#### 2.1.2 Position Sizing Calculator
```python
# src/rules_engine/position_sizing.py
from typing import Dict, List
from decimal import Decimal

class PositionSizingCalculator:
    def __init__(self, constitution: ConstitutionV13):
        self.constitution = constitution
    
    def calculate_position_size(self, account_type: AccountType, 
                              available_capital: Decimal,
                              symbol: str,
                              option_price: Decimal,
                              strike_price: Decimal) -> int:
        """Calculate position size based on Constitution rules"""
        rule = self.constitution.get_trading_rule(account_type)
        
        # Calculate maximum capital to deploy
        max_capital = available_capital * Decimal(str(rule.position_size_pct))
        
        # Calculate maximum per-symbol exposure
        max_symbol_capital = available_capital * Decimal(str(rule.max_symbol_exposure_pct))
        
        # For CSPs, capital requirement is strike_price * 100 per contract
        if rule.strategy == "CSP":
            capital_per_contract = strike_price * 100
        else:  # CC
            capital_per_contract = option_price * 100  # Premium received
        
        # Calculate maximum contracts based on capital constraints
        max_contracts_total = int(max_capital / capital_per_contract)
        max_contracts_symbol = int(max_symbol_capital / capital_per_contract)
        
        # Return the more restrictive limit
        return min(max_contracts_total, max_contracts_symbol)
    
    def validate_position_size(self, account_type: AccountType,
                             current_positions: List[Dict],
                             new_position: Dict) -> bool:
        """Validate new position doesn't violate sizing rules"""
        # Implementation for position size validation
        pass
```

### 2.2 Protocol Engine Implementation

#### 2.2.1 ATR Calculator
```python
# src/protocol_engine/atr_calculator.py
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

class ATRCalculator:
    def __init__(self, market_data_service):
        self.market_data_service = market_data_service
        self.atr_cache = {}
    
    def calculate_atr(self, symbol: str, period: int = 5) -> Optional[float]:
        """Calculate ATR(5) daily at 9:30 ET per Constitution §6"""
        try:
            # Get historical data for ATR calculation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period * 2)  # Extra buffer
            
            historical_data = self.market_data_service.get_historical_data(
                symbol, start_date, end_date, "1d"
            )
            
            if len(historical_data) < period:
                return self._get_fallback_atr(symbol)
            
            # Calculate True Range
            historical_data['high_low'] = historical_data['high'] - historical_data['low']
            historical_data['high_close'] = abs(historical_data['high'] - historical_data['close'].shift(1))
            historical_data['low_close'] = abs(historical_data['low'] - historical_data['close'].shift(1))
            
            historical_data['true_range'] = historical_data[['high_low', 'high_close', 'low_close']].max(axis=1)
            
            # Calculate ATR as simple moving average of True Range
            atr = historical_data['true_range'].rolling(window=period).mean().iloc[-1]
            
            # Cache the result
            self.atr_cache[symbol] = {
                'value': atr,
                'timestamp': datetime.now()
            }
            
            return atr
            
        except Exception as e:
            logger.error(f"ATR calculation failed for {symbol}: {e}")
            return self._get_fallback_atr(symbol)
    
    def _get_fallback_atr(self, symbol: str) -> Optional[float]:
        """Fallback ATR = last valid × 1.1 per Constitution §6"""
        if symbol in self.atr_cache:
            last_atr = self.atr_cache[symbol]['value']
            return last_atr * 1.1
        
        # Ultimate fallback: 2% of current price
        current_price = self.market_data_service.get_current_price(symbol)
        if current_price:
            return current_price * 0.02
        
        return None
```

#### 2.2.2 Protocol Engine Core
```python
# src/protocol_engine/protocol_engine.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class ProtocolLevel(Enum):
    LEVEL_0 = 0  # Normal
    LEVEL_1 = 1  # Enhanced monitoring
    LEVEL_2 = 2  # Recovery
    LEVEL_3 = 3  # Preservation

@dataclass
class ProtocolThresholds:
    level_1_threshold: float  # strike - 1.0 * ATR
    level_2_threshold: float  # strike - 2.0 * ATR
    level_3_threshold: float  # strike - 3.0 * ATR

class ProtocolEngine:
    def __init__(self, atr_calculator: ATRCalculator, 
                 hedge_manager, order_manager):
        self.atr_calculator = atr_calculator
        self.hedge_manager = hedge_manager
        self.order_manager = order_manager
        self.monitoring_frequencies = {
            ProtocolLevel.LEVEL_0: 300,  # 5 minutes
            ProtocolLevel.LEVEL_1: 60,   # 1 minute
            ProtocolLevel.LEVEL_2: 30,   # 30 seconds
            ProtocolLevel.LEVEL_3: 1     # real-time
        }
    
    def evaluate_position_risk(self, position: Dict) -> ProtocolLevel:
        """Evaluate current risk level for position"""
        symbol = position['symbol']
        strike_price = position['strike_price']
        current_price = self.market_data_service.get_current_price(symbol)
        
        if not current_price:
            return ProtocolLevel.LEVEL_0
        
        atr = self.atr_calculator.calculate_atr(symbol)
        if not atr:
            return ProtocolLevel.LEVEL_0
        
        thresholds = self._calculate_thresholds(strike_price, atr)
        
        if current_price <= thresholds.level_3_threshold:
            return ProtocolLevel.LEVEL_3
        elif current_price <= thresholds.level_2_threshold:
            return ProtocolLevel.LEVEL_2
        elif current_price <= thresholds.level_1_threshold:
            return ProtocolLevel.LEVEL_1
        else:
            return ProtocolLevel.LEVEL_0
    
    def _calculate_thresholds(self, strike_price: float, atr: float) -> ProtocolThresholds:
        """Calculate Protocol Engine thresholds per Constitution §6"""
        return ProtocolThresholds(
            level_1_threshold=strike_price - (1.0 * atr),
            level_2_threshold=strike_price - (2.0 * atr),
            level_3_threshold=strike_price - (3.0 * atr)
        )
    
    def execute_protocol_action(self, position: Dict, level: ProtocolLevel):
        """Execute appropriate action based on protocol level"""
        if level == ProtocolLevel.LEVEL_1:
            self._execute_level_1_actions(position)
        elif level == ProtocolLevel.LEVEL_2:
            self._execute_level_2_actions(position)
        elif level == ProtocolLevel.LEVEL_3:
            self._execute_level_3_actions(position)
    
    def _execute_level_1_actions(self, position: Dict):
        """Enhanced monitoring, pre-compute roll candidates"""
        # Increase monitoring frequency
        # Pre-compute roll options
        # Log escalation event
        pass
    
    def _execute_level_2_actions(self, position: Dict):
        """Execute roll, add hedge, freeze new entries"""
        # Attempt to roll position
        # Deploy hedge if roll fails
        # Freeze new entries for this account
        # Log recovery actions
        pass
    
    def _execute_level_3_actions(self, position: Dict):
        """Stop-loss exit, SAFE mode until reset"""
        # Execute stop-loss exit
        # Enter SAFE mode
        # Log preservation actions
        pass
```

### 2.3 State Machine Implementation

#### 2.3.1 State Machine Core
```python
# src/state_machine/state_machine.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Callable
import asyncio
from datetime import datetime

class SystemState(Enum):
    SAFE = "safe"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    ORDERING = "ordering"
    MONITORING = "monitoring"
    CLOSING = "closing"
    RECONCILING = "reconciling"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"
    AUDIT = "audit"

@dataclass
class StateTransition:
    from_state: SystemState
    to_state: SystemState
    condition: Callable[[], bool]
    action: Optional[Callable[[], None]] = None

class StateMachine:
    def __init__(self, logger, market_data_service, broker_service):
        self.current_state = SystemState.SAFE
        self.previous_state = None
        self.state_history = []
        self.logger = logger
        self.market_data_service = market_data_service
        self.broker_service = broker_service
        self.transitions = self._define_transitions()
        self.state_handlers = self._define_state_handlers()
    
    def _define_transitions(self) -> List[StateTransition]:
        """Define valid state transitions per Constitution §9"""
        return [
            StateTransition(
                from_state=SystemState.SAFE,
                to_state=SystemState.SCANNING,
                condition=self._market_hours_active,
                action=self._initialize_scanning
            ),
            StateTransition(
                from_state=SystemState.SCANNING,
                to_state=SystemState.ANALYZING,
                condition=self._market_data_available,
                action=self._start_analysis
            ),
            StateTransition(
                from_state=SystemState.ANALYZING,
                to_state=SystemState.ORDERING,
                condition=self._trade_opportunities_found,
                action=self._prepare_orders
            ),
            StateTransition(
                from_state=SystemState.ORDERING,
                to_state=SystemState.MONITORING,
                condition=self._orders_placed_successfully,
                action=self._start_monitoring
            ),
            StateTransition(
                from_state=SystemState.MONITORING,
                to_state=SystemState.CLOSING,
                condition=self._closing_conditions_met,
                action=self._prepare_closing
            ),
            StateTransition(
                from_state=SystemState.CLOSING,
                to_state=SystemState.RECONCILING,
                condition=self._positions_closed,
                action=self._start_reconciliation
            ),
            StateTransition(
                from_state=SystemState.RECONCILING,
                to_state=SystemState.SAFE,
                condition=self._reconciliation_complete,
                action=self._finalize_cycle
            ),
            # Emergency transitions from any state
            StateTransition(
                from_state=None,  # Any state
                to_state=SystemState.EMERGENCY,
                condition=self._emergency_conditions,
                action=self._handle_emergency
            )
        ]
    
    async def run(self):
        """Main state machine loop"""
        while True:
            try:
                # Execute current state handler
                if self.current_state in self.state_handlers:
                    await self.state_handlers[self.current_state]()
                
                # Check for valid transitions
                await self._check_transitions()
                
                # Sleep based on current state requirements
                await asyncio.sleep(self._get_sleep_duration())
                
            except Exception as e:
                self.logger.error(f"State machine error: {e}")
                await self.transition_to(SystemState.EMERGENCY, f"Unhandled error: {e}")
    
    async def transition_to(self, new_state: SystemState, reason: str = ""):
        """Execute state transition with logging"""
        if new_state == self.current_state:
            return
        
        self.logger.info(f"State transition: {self.current_state.value} → {new_state.value}, Reason: {reason}")
        
        # Record transition
        self.state_history.append({
            'from_state': self.current_state,
            'to_state': new_state,
            'timestamp': datetime.now(),
            'reason': reason
        })
        
        # Update states
        self.previous_state = self.current_state
        self.current_state = new_state
        
        # Execute transition action if defined
        transition = self._find_transition(self.previous_state, new_state)
        if transition and transition.action:
            await transition.action()
    
    async def resume_from_interruption(self):
        """Resume flow per Constitution §9"""
        self.logger.info("Resuming from interruption")
        
        # Load snapshot
        snapshot = await self._load_system_snapshot()
        
        # Fetch broker state
        broker_state = await self.broker_service.get_account_state()
        
        # Reconcile positions
        await self._reconcile_positions(snapshot, broker_state)
        
        # Rebuild schedule
        await self._rebuild_trading_schedule()
        
        # Risk check
        if await self._risk_check_passed():
            await self.transition_to(SystemState.SCANNING, "Resume from interruption")
        else:
            await self.transition_to(SystemState.SAFE, "Risk check failed during resume")
```

### 2.4 Account Management Implementation

#### 2.4.1 Account Structure
```python
# src/account_management/account.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime

@dataclass
class Account:
    id: str
    account_type: AccountType
    parent_account_id: Optional[str]
    initial_capital: Decimal
    current_balance: Decimal
    available_capital: Decimal
    positions: List[Dict]
    transaction_history: List[Dict]
    performance_metrics: Dict
    status: str  # active, paused, closed
    created_at: datetime
    updated_at: datetime

class AccountManager:
    def __init__(self, database, constitution, logger):
        self.database = database
        self.constitution = constitution
        self.logger = logger
        self.fork_tracker = ForkTracker(database, logger)
        self.reinvestment_scheduler = ReinvestmentScheduler(database, logger)
    
    def create_primary_account(self, initial_capital: Decimal) -> Dict[str, Account]:
        """Create primary account with 40/30/30 split"""
        gen_capital = initial_capital * Decimal('0.40')
        rev_capital = initial_capital * Decimal('0.30')
        com_capital = initial_capital * Decimal('0.30')
        
        accounts = {
            'gen_acc': Account(
                id=self._generate_account_id(),
                account_type=AccountType.GEN_ACC,
                parent_account_id=None,
                initial_capital=gen_capital,
                current_balance=gen_capital,
                available_capital=gen_capital,
                positions=[],
                transaction_history=[],
                performance_metrics={},
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            'rev_acc': Account(
                id=self._generate_account_id(),
                account_type=AccountType.REV_ACC,
                parent_account_id=None,
                initial_capital=rev_capital,
                current_balance=rev_capital,
                available_capital=rev_capital,
                positions=[],
                transaction_history=[],
                performance_metrics={},
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            'com_acc': Account(
                id=self._generate_account_id(),
                account_type=AccountType.COM_ACC,
                parent_account_id=None,
                initial_capital=com_capital,
                current_balance=com_capital,
                available_capital=com_capital,
                positions=[],
                transaction_history=[],
                performance_metrics={},
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        }
        
        # Save to database
        for account in accounts.values():
            self.database.save_account(account)
        
        return accounts
    
    def check_fork_eligibility(self, account: Account) -> int:
        """Check if account meets forking thresholds"""
        if account.account_type == AccountType.GEN_ACC:
            return self.fork_tracker.check_gen_acc_fork(account)
        elif account.account_type == AccountType.REV_ACC:
            return self.fork_tracker.check_rev_acc_fork(account)
        return 0
    
    def execute_fork(self, parent_account: Account) -> Optional[Account]:
        """Execute account forking per Constitution rules"""
        if parent_account.account_type == AccountType.GEN_ACC:
            return self.fork_tracker.create_mini_alluse(parent_account)
        elif parent_account.account_type == AccountType.REV_ACC:
            return self.fork_tracker.create_new_alluse_account(parent_account)
        return None
```

#### 2.4.2 Fork Tracker Implementation
```python
# src/account_management/fork_tracker.py
class ForkTracker:
    def __init__(self, database, logger):
        self.database = database
        self.logger = logger
    
    def check_gen_acc_fork(self, gen_acc: Account) -> int:
        """Check for +$100K increments over base per Constitution §2"""
        base_capital = gen_acc.initial_capital
        current_capital = gen_acc.current_balance
        fork_threshold = Decimal('100000')
        
        if current_capital <= base_capital:
            return 0
        
        excess_capital = current_capital - base_capital
        eligible_forks = int(excess_capital / fork_threshold)
        
        # Check how many forks already created
        existing_forks = self.database.count_child_accounts(gen_acc.id)
        
        return max(0, eligible_forks - existing_forks)
    
    def check_rev_acc_fork(self, rev_acc: Account) -> int:
        """Check for +$500K increments over base per Constitution §3"""
        base_capital = rev_acc.initial_capital
        current_capital = rev_acc.current_balance
        fork_threshold = Decimal('500000')
        
        if current_capital <= base_capital:
            return 0
        
        excess_capital = current_capital - base_capital
        eligible_forks = int(excess_capital / fork_threshold)
        
        # Check how many forks already created
        existing_forks = self.database.count_child_accounts(rev_acc.id)
        
        return max(0, eligible_forks - existing_forks)
    
    def create_mini_alluse(self, parent_gen_acc: Account) -> Account:
        """Create mini ALL-USE per Constitution §2"""
        fork_amount = Decimal('100000')
        
        mini_account = Account(
            id=self._generate_account_id(),
            account_type=AccountType.MINI_ALLUSE,
            parent_account_id=parent_gen_acc.id,
            initial_capital=fork_amount,
            current_balance=fork_amount,
            available_capital=fork_amount,
            positions=[],
            transaction_history=[],
            performance_metrics={
                'max_duration_years': 3,
                'max_multiple': 3.0,
                'strategy_mix': {'gen_style': 0.5, 'com_style': 0.5},
                'merge_target': 'com_acc'
            },
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Deduct from parent account
        parent_gen_acc.current_balance -= fork_amount
        parent_gen_acc.available_capital -= fork_amount
        
        # Save both accounts
        self.database.save_account(mini_account)
        self.database.update_account(parent_gen_acc)
        
        self.logger.info(f"Created Mini ALL-USE {mini_account.id} from Gen-Acc {parent_gen_acc.id}")
        
        return mini_account
    
    def check_merge_eligibility(self, mini_account: Account) -> bool:
        """Check if Mini ALL-USE should merge to Com-Acc"""
        if mini_account.account_type != AccountType.MINI_ALLUSE:
            return False
        
        # Check 3-year limit
        age_years = (datetime.now() - mini_account.created_at).days / 365.25
        if age_years >= 3:
            return True
        
        # Check 3x multiple
        multiple = mini_account.current_balance / mini_account.initial_capital
        if multiple >= 3.0:
            return True
        
        # Check if balance reached $500K
        if mini_account.current_balance >= Decimal('500000'):
            return True
        
        return False
```

### 2.5 LLMS Implementation

#### 2.5.1 LLMS Core
```python
# src/llms/llms_core.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

@dataclass
class LEAPContract:
    id: str
    account_id: str
    symbol: str
    option_type: str  # call, put
    strike_price: Decimal
    expiry_date: datetime
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    delta: float
    category: str  # growth, hedge
    status: str  # active, closed, rolled
    created_at: datetime
    updated_at: datetime

class LLMS:
    def __init__(self, database, market_data_service, broker_service, logger):
        self.database = database
        self.market_data_service = market_data_service
        self.broker_service = broker_service
        self.logger = logger
        self.leap_portfolio = LEAPPortfolio(database)
        self.hedge_manager = HedgeManager(database, market_data_service)
        self.optimization_engine = OptimizationEngine(database, logger)
    
    def create_growth_leaps(self, account_id: str, capital_allocation: Decimal) -> List[LEAPContract]:
        """Create growth LEAPs from reinvestment per Constitution §17"""
        # Calls: 0.25-0.35Δ, 12-18M expiry
        target_symbols = self._get_mag7_symbols()
        leaps_created = []
        
        capital_per_symbol = capital_allocation / len(target_symbols)
        
        for symbol in target_symbols:
            leap = self._create_growth_leap_for_symbol(
                account_id, symbol, capital_per_symbol
            )
            if leap:
                leaps_created.append(leap)
        
        return leaps_created
    
    def create_hedge_leaps(self, account_id: str, hedge_allocation: Decimal) -> List[LEAPContract]:
        """Create hedge LEAPs per Constitution §17"""
        # Puts: 10-20% OTM, 6-12M expiry
        hedge_symbols = ["SPX"]  # SPX puts for hedging
        leaps_created = []
        
        for symbol in hedge_symbols:
            leap = self._create_hedge_leap_for_symbol(
                account_id, symbol, hedge_allocation
            )
            if leap:
                leaps_created.append(leap)
        
        return leaps_created
    
    def manage_ladder_lifecycle(self) -> List[Dict]:
        """Manage LEAP ladder lifecycle per Constitution §17"""
        active_leaps = self.database.get_active_leaps()
        actions_taken = []
        
        for leap in active_leaps:
            action = self._check_leap_action_needed(leap)
            if action:
                result = self._execute_leap_action(leap, action)
                actions_taken.append(result)
        
        return actions_taken
    
    def _check_leap_action_needed(self, leap: LEAPContract) -> Optional[str]:
        """Check if LEAP needs action per Constitution §17"""
        # Check TTE ≤3M
        tte_months = (leap.expiry_date - datetime.now()).days / 30.44
        if tte_months <= 3:
            return "roll_forward"
        
        # Check delta drift outside 0.2-0.5 band
        current_delta = self.market_data_service.get_option_delta(
            leap.symbol, leap.strike_price, leap.expiry_date, leap.option_type
        )
        
        if current_delta and (current_delta < 0.2 or current_delta > 0.5):
            return "roll_delta"
        
        # Check hedge put early close conditions
        if leap.category == "hedge" and leap.option_type == "put":
            vix = self.market_data_service.get_vix()
            if vix and vix < 20:
                return "close_early"
        
        return None
    
    def _execute_leap_action(self, leap: LEAPContract, action: str) -> Dict:
        """Execute LEAP action"""
        if action == "roll_forward":
            return self._roll_leap_forward(leap)
        elif action == "roll_delta":
            return self._roll_leap_delta(leap)
        elif action == "close_early":
            return self._close_leap_early(leap)
        
        return {"action": "none", "leap_id": leap.id}
    
    def generate_optimization_suggestions(self) -> List[Dict]:
        """Generate AI-powered optimization suggestions per Constitution §17"""
        return self.optimization_engine.analyze_and_suggest()

class OptimizationEngine:
    def __init__(self, database, logger):
        self.database = database
        self.logger = logger
    
    def analyze_and_suggest(self) -> List[Dict]:
        """Analyze historical LEAP performance and suggest optimizations"""
        suggestions = []
        
        # Analyze strike spacing
        strike_analysis = self._analyze_strike_spacing()
        if strike_analysis['suggestion']:
            suggestions.append({
                'type': 'strike_spacing',
                'analysis': strike_analysis,
                'requires_approval': True
            })
        
        # Analyze expiry patterns
        expiry_analysis = self._analyze_expiry_patterns()
        if expiry_analysis['suggestion']:
            suggestions.append({
                'type': 'expiry_optimization',
                'analysis': expiry_analysis,
                'requires_approval': True
            })
        
        # Analyze delta band performance
        delta_analysis = self._analyze_delta_performance()
        if delta_analysis['suggestion']:
            suggestions.append({
                'type': 'delta_band_refinement',
                'analysis': delta_analysis,
                'requires_approval': True
            })
        
        return suggestions
    
    def _analyze_strike_spacing(self) -> Dict:
        """Analyze optimal strike spacing for LEAP ladders"""
        # Implementation for strike spacing analysis
        pass
    
    def _analyze_expiry_patterns(self) -> Dict:
        """Analyze optimal expiry patterns"""
        # Implementation for expiry analysis
        pass
    
    def _analyze_delta_performance(self) -> Dict:
        """Analyze delta band performance"""
        # Implementation for delta analysis
        pass
```

### 2.6 Trading System Implementation

#### 2.6.1 Order Manager
```python
# src/trading/order_manager.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from decimal import Decimal
import uuid

@dataclass
class Order:
    id: str
    account_id: str
    symbol: str
    option_type: str  # call, put
    strike_price: Decimal
    expiry_date: datetime
    quantity: int
    order_type: str  # CSP, CC, BTO, STC
    limit_price: Decimal
    status: str  # pending, filled, cancelled, rejected
    broker_order_id: Optional[str]
    created_at: datetime
    filled_at: Optional[datetime]
    commission: Decimal

class OrderManager:
    def __init__(self, broker_service, constitution, logger):
        self.broker_service = broker_service
        self.constitution = constitution
        self.logger = logger
        self.order_validator = OrderValidator(constitution)
        self.execution_tracker = ExecutionTracker(logger)
    
    def create_csp_order(self, account_id: str, symbol: str, 
                        strike_price: Decimal, expiry_date: datetime,
                        quantity: int, limit_price: Decimal) -> Order:
        """Create cash-secured put order per Constitution rules"""
        order = Order(
            id=str(uuid.uuid4()),
            account_id=account_id,
            symbol=symbol,
            option_type="put",
            strike_price=strike_price,
            expiry_date=expiry_date,
            quantity=quantity,
            order_type="CSP",
            limit_price=limit_price,
            status="pending",
            broker_order_id=None,
            created_at=datetime.now(),
            filled_at=None,
            commission=Decimal('0')
        )
        
        # Validate order
        if not self.order_validator.validate_order(order):
            raise ValueError("Order validation failed")
        
        return order
    
    def create_cc_order(self, account_id: str, symbol: str,
                       strike_price: Decimal, expiry_date: datetime,
                       quantity: int, limit_price: Decimal) -> Order:
        """Create covered call order per Constitution rules"""
        order = Order(
            id=str(uuid.uuid4()),
            account_id=account_id,
            symbol=symbol,
            option_type="call",
            strike_price=strike_price,
            expiry_date=expiry_date,
            quantity=quantity,
            order_type="CC",
            limit_price=limit_price,
            status="pending",
            broker_order_id=None,
            created_at=datetime.now(),
            filled_at=None,
            commission=Decimal('0')
        )
        
        # Validate order
        if not self.order_validator.validate_order(order):
            raise ValueError("Order validation failed")
        
        return order
    
    def place_order(self, order: Order) -> bool:
        """Place order with broker per Constitution §0"""
        try:
            # Place at mid price, accept ≤5% worse
            mid_price = self.broker_service.get_option_mid_price(
                order.symbol, order.strike_price, order.expiry_date, order.option_type
            )
            
            if not mid_price:
                self.logger.error(f"Could not get mid price for {order.symbol}")
                return False
            
            # Check slippage tolerance
            slippage = abs(order.limit_price - mid_price) / mid_price
            if slippage > 0.05:  # 5% slippage cap
                self.logger.warning(f"Order {order.id} exceeds slippage tolerance")
                return False
            
            # Submit to broker
            broker_order_id = self.broker_service.submit_order(order)
            if broker_order_id:
                order.broker_order_id = broker_order_id
                order.status = "submitted"
                self.execution_tracker.track_order(order)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Order placement failed: {e}")
            order.status = "rejected"
            return False
    
    def monitor_orders(self) -> List[Dict]:
        """Monitor pending orders per Constitution timeout rules"""
        pending_orders = self.execution_tracker.get_pending_orders()
        actions_taken = []
        
        for order in pending_orders:
            # Check 3-second timeout for cancel-replace
            if self._order_timeout_exceeded(order):
                action = self._handle_order_timeout(order)
                actions_taken.append(action)
        
        return actions_taken
    
    def _order_timeout_exceeded(self, order: Order) -> bool:
        """Check if order has exceeded 3-second timeout"""
        elapsed = (datetime.now() - order.created_at).total_seconds()
        return elapsed > 3 and order.status == "submitted"
    
    def _handle_order_timeout(self, order: Order) -> Dict:
        """Handle order timeout with cancel-replace logic"""
        # Cancel existing order
        cancel_success = self.broker_service.cancel_order(order.broker_order_id)
        
        if cancel_success:
            # Create new order with adjusted price or smaller size
            new_order = self._create_retry_order(order)
            if new_order and self.place_order(new_order):
                return {"action": "cancel_replace", "old_order": order.id, "new_order": new_order.id}
        
        return {"action": "cancel_failed", "order": order.id}
```

This comprehensive technical specification provides the detailed implementation guidance needed to build the TRUE ALL-USE system exactly as specified in your Constitution and System Overview documents.

