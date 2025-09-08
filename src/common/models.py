"""
Database Models for True-Asset-ALLUSE

SQLAlchemy models implementing the core database schema as specified
in the Constitution v1.3 and Architecture documents.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Date, Boolean, 
    Text, JSON, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# Enums for database constraints
class AccountType(str, Enum):
    """Account types per Constitution."""
    GEN_ACC = "gen_acc"
    REV_ACC = "rev_acc"
    COM_ACC = "com_acc"
    MINI_ALLUSE = "mini_alluse"


class AccountStatus(str, Enum):
    """Account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FORKED = "forked"
    MERGED = "merged"
    SUSPENDED = "suspended"


class PositionType(str, Enum):
    """Position types."""
    CSP = "csp"  # Cash-Secured Put
    CC = "cc"    # Covered Call
    LEAP_CALL = "leap_call"
    LEAP_PUT = "leap_put"
    STOCK = "stock"


class PositionStatus(str, Enum):
    """Position status."""
    OPEN = "open"
    CLOSED = "closed"
    ASSIGNED = "assigned"
    EXPIRED = "expired"
    ROLLED = "rolled"


class ProtocolLevel(str, Enum):
    """Protocol escalation levels per Constitution §6."""
    LEVEL_0 = "level_0"  # Normal
    LEVEL_1 = "level_1"  # Enhanced
    LEVEL_2 = "level_2"  # Recovery
    LEVEL_3 = "level_3"  # Preservation


class SystemState(str, Enum):
    """System states per Constitution §9."""
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


class WeekType(str, Enum):
    """Week types per Constitution §12."""
    CALM_INCOME = "calm_income"
    ROLL = "roll"
    ASSIGNMENT = "assignment"
    PRESERVATION = "preservation"
    HEDGED = "hedged"
    EARNINGS_FILTER = "earnings_filter"


# Core Models
class Account(Base):
    """Account model implementing three-tiered architecture."""
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_type = Column(ENUM(AccountType), nullable=False)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    # Account details
    initial_capital = Column(Numeric(15, 2), nullable=False)
    current_balance = Column(Numeric(15, 2), nullable=False)
    available_capital = Column(Numeric(15, 2), nullable=False)
    
    # Status and metadata
    status = Column(ENUM(AccountStatus), default=AccountStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constitution compliance tracking
    constitution_version = Column(String(10), default="1.3")
    last_fork_check = Column(DateTime(timezone=True))
    fork_count = Column(Integer, default=0)
    
    # Relationships
    parent_account = relationship("Account", remote_side=[id], backref="child_accounts")
    positions = relationship("Position", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")
    performance_metrics = relationship("PerformanceMetric", back_populates="account")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("initial_capital >= 100000", name="min_capital_check"),
        CheckConstraint("current_balance >= 0", name="positive_balance_check"),
        CheckConstraint("available_capital >= 0", name="positive_available_check"),
        Index("idx_account_type_status", "account_type", "status"),
        Index("idx_parent_account", "parent_account_id"),
    )


class Position(Base):
    """Position model for tracking all trading positions."""
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Position details
    symbol = Column(String(10), nullable=False)
    position_type = Column(ENUM(PositionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    # Options-specific fields
    strike_price = Column(Numeric(10, 2), nullable=True)
    expiry_date = Column(Date, nullable=True)
    option_type = Column(String(4), nullable=True)  # 'call' or 'put'
    
    # Pricing and P&L
    entry_price = Column(Numeric(10, 4), nullable=False)
    current_price = Column(Numeric(10, 4), nullable=True)
    unrealized_pnl = Column(Numeric(12, 2), default=0)
    realized_pnl = Column(Numeric(12, 2), default=0)
    
    # Status and timing
    status = Column(ENUM(PositionStatus), default=PositionStatus.OPEN)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Protocol Engine tracking
    current_protocol_level = Column(ENUM(ProtocolLevel), default=ProtocolLevel.LEVEL_0)
    atr_at_entry = Column(Numeric(10, 4), nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    orders = relationship("Order", back_populates="position")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity != 0", name="non_zero_quantity"),
        CheckConstraint(
            "(position_type IN ('csp', 'cc', 'leap_call', 'leap_put') AND strike_price IS NOT NULL AND expiry_date IS NOT NULL) OR "
            "(position_type = 'stock' AND strike_price IS NULL AND expiry_date IS NULL)",
            name="options_fields_check"
        ),
        Index("idx_position_symbol_status", "symbol", "status"),
        Index("idx_position_account_type", "account_id", "position_type"),
        Index("idx_position_expiry", "expiry_date"),
    )


class Order(Base):
    """Order model for tracking all trading orders."""
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Order identification
    client_order_id = Column(String(50), nullable=False, unique=True)
    broker_order_id = Column(String(50), nullable=True)
    
    # Order details
    symbol = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # LMT, MKT, etc.
    quantity = Column(Integer, nullable=False)
    limit_price = Column(Numeric(10, 4), nullable=True)
    
    # Options-specific
    strike_price = Column(Numeric(10, 2), nullable=True)
    expiry_date = Column(Date, nullable=True)
    option_type = Column(String(4), nullable=True)
    
    # Order status and execution
    status = Column(String(20), default="PENDING")
    filled_quantity = Column(Integer, default=0)
    avg_fill_price = Column(Numeric(10, 4), nullable=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Constitution compliance
    rule_reference = Column(String(50), nullable=True)  # e.g., "§2.Gen-Acc.Entry"
    
    # Relationships
    position = relationship("Position", back_populates="orders")
    account = relationship("Account")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("filled_quantity >= 0", name="non_negative_filled"),
        CheckConstraint("filled_quantity <= quantity", name="filled_not_exceed_quantity"),
        Index("idx_order_status_created", "status", "created_at"),
        Index("idx_order_symbol_expiry", "symbol", "expiry_date"),
    )


class Transaction(Base):
    """Transaction model for financial ledger."""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # TRADE, DIVIDEND, FEE, etc.
    symbol = Column(String(10), nullable=True)
    quantity = Column(Integer, nullable=True)
    price = Column(Numeric(10, 4), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    
    # Categorization
    realized_pnl = Column(Numeric(12, 2), default=0)
    commission = Column(Numeric(8, 2), default=0)
    fees = Column(Numeric(8, 2), default=0)
    
    # Timing and reference
    transaction_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # External references
    broker_transaction_id = Column(String(50), nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    order = relationship("Order")
    
    # Constraints
    __table_args__ = (
        Index("idx_transaction_account_date", "account_id", "transaction_date"),
        Index("idx_transaction_type_date", "transaction_type", "transaction_date"),
    )


class RuleExecution(Base):
    """Rule execution audit trail per Constitution requirements."""
    __tablename__ = "rule_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_section = Column(String(50), nullable=False)  # e.g., "§2.Gen-Acc.Entry"
    rule_description = Column(Text, nullable=False)
    constitution_version = Column(String(10), default="1.3")
    
    # Execution context
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"), nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    
    # Execution details
    execution_context = Column(JSON, nullable=False)
    execution_result = Column(JSON, nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timing
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index("idx_rule_section_date", "rule_section", "executed_at"),
        Index("idx_rule_success_date", "success", "executed_at"),
    )


class PerformanceMetric(Base):
    """Performance metrics per account."""
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Time period
    metric_date = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY, QUARTERLY
    
    # Performance metrics
    total_return = Column(Numeric(10, 4), nullable=False)
    realized_pnl = Column(Numeric(12, 2), default=0)
    unrealized_pnl = Column(Numeric(12, 2), default=0)
    total_pnl = Column(Numeric(12, 2), default=0)
    
    # Risk metrics
    max_drawdown = Column(Numeric(8, 4), default=0)
    volatility = Column(Numeric(8, 4), nullable=True)
    sharpe_ratio = Column(Numeric(6, 4), nullable=True)
    sortino_ratio = Column(Numeric(6, 4), nullable=True)
    
    # Activity metrics
    trades_count = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4), nullable=True)
    avg_trade_pnl = Column(Numeric(10, 2), nullable=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="performance_metrics")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "metric_date", "period_type", name="unique_metric_period"),
        Index("idx_performance_account_date", "account_id", "metric_date"),
    )


class SystemState(Base):
    """System state tracking for SAFE→ACTIVE state machine."""
    __tablename__ = "system_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # State information
    current_state = Column(ENUM(SystemState), nullable=False)
    previous_state = Column(ENUM(SystemState), nullable=True)
    
    # Context and metadata
    state_context = Column(JSON, nullable=True)
    transition_reason = Column(Text, nullable=True)
    
    # Timing
    entered_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_seconds = Column(Integer, nullable=True)
    
    # Constraints
    __table_args__ = (
        Index("idx_state_entered", "current_state", "entered_at"),
    )


class WeekClassification(Base):
    """Week typing per Constitution §12."""
    __tablename__ = "week_classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Week identification
    week_start_date = Column(Date, nullable=False, unique=True)
    week_end_date = Column(Date, nullable=False)
    
    # Classification
    week_type = Column(ENUM(WeekType), nullable=False)
    classification_reason = Column(Text, nullable=True)
    
    # Market conditions
    market_conditions = Column(JSON, nullable=True)
    vix_level = Column(Numeric(6, 2), nullable=True)
    
    # AI predictions (advisory only)
    ai_predicted_type = Column(ENUM(WeekType), nullable=True)
    ai_confidence = Column(Numeric(4, 3), nullable=True)
    
    # Timing
    classified_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index("idx_week_type_date", "week_type", "week_start_date"),
    )


class LEAPLadder(Base):
    """LLMS (Leap Ladder Management System) tracking."""
    __tablename__ = "leap_ladders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Ladder details
    ladder_type = Column(String(20), nullable=False)  # GROWTH, HEDGE
    symbol = Column(String(10), nullable=False)
    
    # LEAP positions in this ladder
    positions = Column(JSON, nullable=False)  # Array of position IDs
    
    # Ladder metrics
    total_investment = Column(Numeric(12, 2), nullable=False)
    current_value = Column(Numeric(12, 2), nullable=False)
    unrealized_pnl = Column(Numeric(12, 2), default=0)
    
    # Management dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_rebalanced = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(Date, nullable=True)
    
    # AI optimization (advisory only)
    ai_suggestions = Column(JSON, nullable=True)
    last_ai_review = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    account = relationship("Account")
    
    # Constraints
    __table_args__ = (
        Index("idx_ladder_account_type", "account_id", "ladder_type"),
        Index("idx_ladder_symbol", "symbol"),
    )

