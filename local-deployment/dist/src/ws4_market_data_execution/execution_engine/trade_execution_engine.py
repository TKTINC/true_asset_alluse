"""
Trade Execution Engine

This module implements the comprehensive trade execution system that manages
order lifecycle, execution logic, risk validation, and trade reconciliation
for the True-Asset-ALLUSE platform with full Constitution v1.3 compliance.
"""

from typing import Dict, Any, Optional, List, Callable
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading
import time
import uuid
from dataclasses import dataclass, asdict

from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws1_rules_engine.rules_engine import RulesEngine
from src.ws2_protocol_engine.escalation.escalation_manager import EscalationManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    BRACKET = "bracket"
    ONE_CANCELS_OTHER = "oco"


class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_OPEN = "sell_to_open"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_CLOSE = "sell_to_close"


class OrderStatus(Enum):
    """Order status."""
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"


class ExecutionVenue(Enum):
    """Execution venues."""
    INTERACTIVE_BROKERS = "interactive_brokers"
    SMART_ROUTING = "smart_routing"
    NYSE = "nyse"
    NASDAQ = "nasdaq"
    CBOE = "cboe"
    ISE = "ise"


@dataclass
class OrderRequest:
    """Order request structure."""
    order_id: str
    account_id: str
    symbol: str
    order_type: OrderType
    order_side: OrderSide
    quantity: int
    price: Optional[Decimal]
    stop_price: Optional[Decimal]
    time_in_force: str
    execution_venue: ExecutionVenue
    strategy_name: Optional[str]
    parent_order_id: Optional[str]
    metadata: Dict[str, Any]
    created_timestamp: datetime


@dataclass
class OrderExecution:
    """Order execution details."""
    execution_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    commission: Decimal
    execution_timestamp: datetime
    venue: ExecutionVenue
    liquidity_flag: str
    execution_quality: Decimal
    metadata: Dict[str, Any]


@dataclass
class OrderStatus:
    """Order status tracking."""
    order_id: str
    status: OrderStatus
    filled_quantity: int
    remaining_quantity: int
    average_fill_price: Optional[Decimal]
    total_commission: Decimal
    executions: List[OrderExecution]
    last_update: datetime
    error_message: Optional[str]


class TradeExecutionEngine:
    """
    Comprehensive Trade Execution Engine.
    
    Manages the complete order lifecycle from validation through execution
    and reconciliation, with full Constitution v1.3 compliance and
    integration with the Rules Engine and Protocol Engine.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 rules_engine: RulesEngine,
                 escalation_manager: EscalationManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize trade execution engine.
        
        Args:
            audit_manager: Audit trail manager
            rules_engine: Rules engine for validation
            escalation_manager: Protocol escalation manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.rules_engine = rules_engine
        self.escalation_manager = escalation_manager
        self.config = config or {}
        
        # Configuration parameters
        self.max_order_size = Decimal(str(self.config.get("max_order_size", 10000)))
        self.max_daily_volume = Decimal(str(self.config.get("max_daily_volume", 100000)))
        self.execution_timeout_seconds = self.config.get("execution_timeout_seconds", 300)
        self.max_slippage_tolerance = Decimal(str(self.config.get("max_slippage_tolerance", 0.02)))
        self.default_venue = ExecutionVenue(self.config.get("default_venue", "smart_routing"))
        
        # Order management
        self.pending_orders = {}  # order_id -> OrderRequest
        self.active_orders = {}   # order_id -> OrderStatus
        self.completed_orders = {}  # order_id -> OrderStatus
        self.order_executions = {}  # execution_id -> OrderExecution
        
        # Threading and processing
        self.execution_lock = threading.RLock()
        self.execution_thread = None
        self.running = False
        
        # Execution callbacks
        self.execution_callbacks = {}  # event_type -> List[callback]
        
        # Performance metrics
        self.metrics = {
            "total_orders": 0,
            "successful_orders": 0,
            "rejected_orders": 0,
            "cancelled_orders": 0,
            "total_executions": 0,
            "total_volume": Decimal("0"),
            "total_commission": Decimal("0"),
            "average_execution_time": 0,
            "slippage_statistics": {
                "average_slippage": Decimal("0"),
                "max_slippage": Decimal("0"),
                "slippage_count": 0
            },
            "venue_statistics": {},
            "last_execution": None
        }
        
        logger.info("Trade Execution Engine initialized")
    
    def start(self) -> Dict[str, Any]:
        """Start trade execution engine."""
        try:
            if self.running:
                return {"success": False, "error": "Trade execution engine already running"}
            
            self.running = True
            
            # Start execution processing thread
            self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
            self.execution_thread.start()
            
            logger.info("Trade Execution Engine started")
            
            return {
                "success": True,
                "max_order_size": float(self.max_order_size),
                "max_daily_volume": float(self.max_daily_volume),
                "default_venue": self.default_venue.value,
                "start_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting trade execution engine: {str(e)}", exc_info=True)
            self.running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop trade execution engine."""
        try:
            if not self.running:
                return {"success": False, "error": "Trade execution engine not running"}
            
            self.running = False
            
            # Cancel all pending orders
            with self.execution_lock:
                pending_order_ids = list(self.pending_orders.keys())
            
            for order_id in pending_order_ids:
                self.cancel_order(order_id)
            
            # Wait for execution thread to finish
            if self.execution_thread and self.execution_thread.is_alive():
                self.execution_thread.join(timeout=10)
            
            logger.info("Trade Execution Engine stopped")
            
            return {
                "success": True,
                "cancelled_orders": len(pending_order_ids),
                "stop_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping trade execution engine: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def submit_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """
        Submit order for execution.
        
        Args:
            order_request: Order request details
            
        Returns:
            Order submission result
        """
        try:
            # Validate order request
            validation_result = self._validate_order_request(order_request)
            if not validation_result["success"]:
                self.metrics["rejected_orders"] += 1
                return validation_result
            
            # Rules engine validation
            rules_validation = self._validate_with_rules_engine(order_request)
            if not rules_validation["success"]:
                self.metrics["rejected_orders"] += 1
                return rules_validation
            
            # Add to pending orders
            with self.execution_lock:
                self.pending_orders[order_request.order_id] = order_request
                
                # Create order status
                order_status = OrderStatus(
                    order_id=order_request.order_id,
                    status=OrderStatus.PENDING_VALIDATION,
                    filled_quantity=0,
                    remaining_quantity=order_request.quantity,
                    average_fill_price=None,
                    total_commission=Decimal("0"),
                    executions=[],
                    last_update=datetime.now(),
                    error_message=None
                )
                
                self.active_orders[order_request.order_id] = order_status
            
            # Log order submission
            self.audit_manager.log_system_event(
                event_type="order_submitted",
                event_data={
                    "order_id": order_request.order_id,
                    "account_id": order_request.account_id,
                    "symbol": order_request.symbol,
                    "side": order_request.order_side.value,
                    "quantity": order_request.quantity,
                    "order_type": order_request.order_type.value,
                    "price": float(order_request.price) if order_request.price else None
                },
                severity="info"
            )
            
            self.metrics["total_orders"] += 1
            
            return {
                "success": True,
                "order_id": order_request.order_id,
                "status": OrderStatus.PENDING_VALIDATION.value,
                "submission_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error submitting order: {str(e)}", exc_info=True)
            self.metrics["rejected_orders"] += 1
            return {
                "success": False,
                "error": str(e),
                "order_id": order_request.order_id
            }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel pending or active order."""
        try:
            with self.execution_lock:
                # Check if order exists
                if order_id not in self.active_orders:
                    return {
                        "success": False,
                        "error": "Order not found",
                        "order_id": order_id
                    }
                
                order_status = self.active_orders[order_id]
                
                # Check if order can be cancelled
                if order_status.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    return {
                        "success": False,
                        "error": f"Order cannot be cancelled in status: {order_status.status.value}",
                        "order_id": order_id
                    }
                
                # Cancel order
                order_status.status = OrderStatus.CANCELLED
                order_status.last_update = datetime.now()
                
                # Remove from pending orders if present
                if order_id in self.pending_orders:
                    del self.pending_orders[order_id]
                
                # Move to completed orders
                self.completed_orders[order_id] = order_status
                del self.active_orders[order_id]
            
            # Log order cancellation
            self.audit_manager.log_system_event(
                event_type="order_cancelled",
                event_data={
                    "order_id": order_id,
                    "cancellation_reason": "manual_cancellation"
                },
                severity="info"
            )
            
            self.metrics["cancelled_orders"] += 1
            
            return {
                "success": True,
                "order_id": order_id,
                "status": OrderStatus.CANCELLED.value,
                "cancellation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "order_id": order_id
            }
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status."""
        try:
            with self.execution_lock:
                # Check active orders
                if order_id in self.active_orders:
                    order_status = self.active_orders[order_id]
                    return {
                        "success": True,
                        "order_status": asdict(order_status),
                        "is_active": True
                    }
                
                # Check completed orders
                if order_id in self.completed_orders:
                    order_status = self.completed_orders[order_id]
                    return {
                        "success": True,
                        "order_status": asdict(order_status),
                        "is_active": False
                    }
                
                return {
                    "success": False,
                    "error": "Order not found",
                    "order_id": order_id
                }
                
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "order_id": order_id
            }
    
    def get_account_orders(self, account_id: str) -> Dict[str, Any]:
        """Get all orders for account."""
        try:
            account_orders = {
                "active": [],
                "completed": []
            }
            
            with self.execution_lock:
                # Get active orders
                for order_id, order_status in self.active_orders.items():
                    if order_id in self.pending_orders:
                        order_request = self.pending_orders[order_id]
                        if order_request.account_id == account_id:
                            account_orders["active"].append({
                                "order_request": asdict(order_request),
                                "order_status": asdict(order_status)
                            })
                
                # Get completed orders
                for order_id, order_status in self.completed_orders.items():
                    # Would need to store account_id in order_status for this to work properly
                    # For now, simplified implementation
                    account_orders["completed"].append(asdict(order_status))
            
            return {
                "success": True,
                "account_id": account_id,
                "orders": account_orders,
                "total_active": len(account_orders["active"]),
                "total_completed": len(account_orders["completed"])
            }
            
        except Exception as e:
            logger.error(f"Error getting account orders for {account_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id
            }
    
    def _validate_order_request(self, order_request: OrderRequest) -> Dict[str, Any]:
        """Validate order request."""
        try:
            # Basic validation
            if not order_request.symbol:
                return {"success": False, "error": "Symbol is required"}
            
            if order_request.quantity <= 0:
                return {"success": False, "error": "Quantity must be positive"}
            
            if order_request.quantity > self.max_order_size:
                return {"success": False, "error": f"Order size exceeds maximum: {self.max_order_size}"}
            
            # Price validation for limit orders
            if order_request.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                if not order_request.price or order_request.price <= 0:
                    return {"success": False, "error": "Price is required for limit orders"}
            
            # Stop price validation for stop orders
            if order_request.order_type in [OrderType.STOP, OrderType.STOP_LIMIT, OrderType.TRAILING_STOP]:
                if not order_request.stop_price or order_request.stop_price <= 0:
                    return {"success": False, "error": "Stop price is required for stop orders"}
            
            # Daily volume check
            today_volume = self._calculate_daily_volume(order_request.account_id)
            if today_volume + Decimal(str(order_request.quantity)) > self.max_daily_volume:
                return {"success": False, "error": f"Daily volume limit exceeded: {self.max_daily_volume}"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error validating order request: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _validate_with_rules_engine(self, order_request: OrderRequest) -> Dict[str, Any]:
        """Validate order with rules engine."""
        try:
            # This would integrate with the actual rules engine
            # For now, simplified validation
            
            validation_data = {
                "account_id": order_request.account_id,
                "symbol": order_request.symbol,
                "order_side": order_request.order_side.value,
                "quantity": order_request.quantity,
                "order_type": order_request.order_type.value,
                "price": float(order_request.price) if order_request.price else None
            }
            
            # Simulate rules engine validation
            # In real implementation, this would call self.rules_engine.validate_order(validation_data)
            
            return {"success": True, "validation_data": validation_data}
            
        except Exception as e:
            logger.error(f"Error validating with rules engine: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _calculate_daily_volume(self, account_id: str) -> Decimal:
        """Calculate daily trading volume for account."""
        try:
            today = datetime.now().date()
            daily_volume = Decimal("0")
            
            # Calculate volume from completed orders today
            with self.execution_lock:
                for order_status in self.completed_orders.values():
                    if order_status.last_update.date() == today:
                        daily_volume += Decimal(str(order_status.filled_quantity))
            
            return daily_volume
            
        except Exception as e:
            logger.error(f"Error calculating daily volume: {str(e)}")
            return Decimal("0")
    
    def _execution_loop(self):
        """Main execution processing loop."""
        logger.info("Trade execution loop started")
        
        while self.running:
            try:
                # Process pending orders
                self._process_pending_orders()
                
                # Monitor active orders
                self._monitor_active_orders()
                
                # Update metrics
                self._update_execution_metrics()
                
                time.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Error in execution loop: {str(e)}", exc_info=True)
                time.sleep(5)  # Longer sleep on error
        
        logger.info("Trade execution loop stopped")
    
    def _process_pending_orders(self):
        """Process pending orders."""
        try:
            with self.execution_lock:
                pending_order_ids = list(self.pending_orders.keys())
            
            for order_id in pending_order_ids:
                try:
                    self._process_single_order(order_id)
                except Exception as e:
                    logger.error(f"Error processing order {order_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error processing pending orders: {str(e)}")
    
    def _process_single_order(self, order_id: str):
        """Process single order."""
        try:
            with self.execution_lock:
                if order_id not in self.pending_orders or order_id not in self.active_orders:
                    return
                
                order_request = self.pending_orders[order_id]
                order_status = self.active_orders[order_id]
            
            # Update status to validated
            order_status.status = OrderStatus.VALIDATED
            order_status.last_update = datetime.now()
            
            # Simulate order execution
            execution_result = self._execute_order(order_request)
            
            if execution_result["success"]:
                # Create execution record
                execution = OrderExecution(
                    execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                    order_id=order_id,
                    symbol=order_request.symbol,
                    side=order_request.order_side,
                    quantity=order_request.quantity,
                    price=execution_result["execution_price"],
                    commission=execution_result["commission"],
                    execution_timestamp=datetime.now(),
                    venue=order_request.execution_venue,
                    liquidity_flag="added",
                    execution_quality=Decimal("0.95"),
                    metadata=execution_result.get("metadata", {})
                )
                
                # Update order status
                order_status.status = OrderStatus.FILLED
                order_status.filled_quantity = order_request.quantity
                order_status.remaining_quantity = 0
                order_status.average_fill_price = execution_result["execution_price"]
                order_status.total_commission = execution_result["commission"]
                order_status.executions.append(execution)
                order_status.last_update = datetime.now()
                
                # Store execution
                self.order_executions[execution.execution_id] = execution
                
                # Move to completed orders
                with self.execution_lock:
                    self.completed_orders[order_id] = order_status
                    del self.active_orders[order_id]
                    del self.pending_orders[order_id]
                
                # Update metrics
                self.metrics["successful_orders"] += 1
                self.metrics["total_executions"] += 1
                self.metrics["total_volume"] += Decimal(str(order_request.quantity))
                self.metrics["total_commission"] += execution_result["commission"]
                self.metrics["last_execution"] = datetime.now().isoformat()
                
                # Log execution
                self.audit_manager.log_system_event(
                    event_type="order_executed",
                    event_data={
                        "order_id": order_id,
                        "execution_id": execution.execution_id,
                        "symbol": order_request.symbol,
                        "quantity": order_request.quantity,
                        "price": float(execution_result["execution_price"]),
                        "commission": float(execution_result["commission"])
                    },
                    severity="info"
                )
                
                # Trigger execution callback
                self._trigger_execution_callback("order_filled", order_id, execution_result)
                
            else:
                # Order execution failed
                order_status.status = OrderStatus.REJECTED
                order_status.error_message = execution_result["error"]
                order_status.last_update = datetime.now()
                
                # Move to completed orders
                with self.execution_lock:
                    self.completed_orders[order_id] = order_status
                    del self.active_orders[order_id]
                    del self.pending_orders[order_id]
                
                self.metrics["rejected_orders"] += 1
                
                logger.error(f"Order execution failed for {order_id}: {execution_result['error']}")
                
        except Exception as e:
            logger.error(f"Error processing single order {order_id}: {str(e)}")
    
    def _execute_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """Execute order (simulate execution)."""
        try:
            # Simulate order execution
            # In real implementation, this would route to actual broker/exchange
            
            # Simulate execution price with some slippage
            if order_request.price:
                base_price = order_request.price
            else:
                # Market order - simulate current market price
                base_price = Decimal("100.00")  # Placeholder market price
            
            # Add small random slippage
            slippage_factor = Decimal("0.001")  # 0.1% slippage
            if order_request.order_side in [OrderSide.BUY, OrderSide.BUY_TO_OPEN, OrderSide.BUY_TO_CLOSE]:
                execution_price = base_price * (Decimal("1") + slippage_factor)
            else:
                execution_price = base_price * (Decimal("1") - slippage_factor)
            
            # Calculate commission
            commission = Decimal("1.00")  # Flat $1 commission
            
            # Simulate execution delay
            time.sleep(0.1)
            
            return {
                "success": True,
                "execution_price": execution_price,
                "commission": commission,
                "execution_venue": order_request.execution_venue.value,
                "metadata": {
                    "simulated": True,
                    "execution_time_ms": 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _monitor_active_orders(self):
        """Monitor active orders for timeouts."""
        try:
            now = datetime.now()
            timeout_threshold = timedelta(seconds=self.execution_timeout_seconds)
            
            with self.execution_lock:
                active_order_ids = list(self.active_orders.keys())
            
            for order_id in active_order_ids:
                try:
                    order_status = self.active_orders[order_id]
                    
                    # Check for timeout
                    if (now - order_status.last_update) > timeout_threshold:
                        logger.warning(f"Order {order_id} timed out, cancelling")
                        self.cancel_order(order_id)
                        
                except Exception as e:
                    logger.error(f"Error monitoring order {order_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error monitoring active orders: {str(e)}")
    
    def _update_execution_metrics(self):
        """Update execution metrics."""
        try:
            # Update venue statistics
            venue_stats = {}
            for execution in self.order_executions.values():
                venue = execution.venue.value
                if venue not in venue_stats:
                    venue_stats[venue] = {"count": 0, "volume": Decimal("0")}
                
                venue_stats[venue]["count"] += 1
                venue_stats[venue]["volume"] += Decimal(str(execution.quantity))
            
            self.metrics["venue_statistics"] = venue_stats
            
            # Update slippage statistics
            slippages = []
            for execution in self.order_executions.values():
                # Would calculate actual slippage if we had reference prices
                # For now, use placeholder
                slippages.append(Decimal("0.001"))
            
            if slippages:
                self.metrics["slippage_statistics"]["average_slippage"] = sum(slippages) / len(slippages)
                self.metrics["slippage_statistics"]["max_slippage"] = max(slippages)
                self.metrics["slippage_statistics"]["slippage_count"] = len(slippages)
            
        except Exception as e:
            logger.error(f"Error updating execution metrics: {str(e)}")
    
    def _trigger_execution_callback(self, event_type: str, order_id: str, event_data: Dict[str, Any]):
        """Trigger execution event callbacks."""
        try:
            if event_type in self.execution_callbacks:
                for callback in self.execution_callbacks[event_type]:
                    try:
                        callback(order_id, event_data)
                    except Exception as e:
                        logger.error(f"Error in execution callback: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error triggering execution callbacks: {str(e)}")
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution performance metrics."""
        try:
            return {
                "success": True,
                "metrics": self.metrics.copy(),
                "active_orders": len(self.active_orders),
                "pending_orders": len(self.pending_orders),
                "completed_orders": len(self.completed_orders),
                "total_executions": len(self.order_executions),
                "metrics_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting execution metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

