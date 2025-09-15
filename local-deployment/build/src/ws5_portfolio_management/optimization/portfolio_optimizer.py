"""
Portfolio Optimizer

This module implements the comprehensive portfolio optimization engine that
constructs, optimizes, and rebalances portfolios based on various strategies
and risk profiles for the True-Asset-ALLUSE system.
"""

from typing import Dict, Any, Optional, List, Callable, Set
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import threading
import time
from dataclasses import dataclass, asdict
import uuid
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws4_market_data_execution.market_data.market_data_manager import MarketDataManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Portfolio optimization strategies."""
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    EQUAL_WEIGHT = "equal_weight"
    CUSTOM = "custom"


class RebalancingTrigger(Enum):
    """Portfolio rebalancing triggers."""
    PERIODIC = "periodic"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    RISK_BASED = "risk_based"


@dataclass
class PortfolioConstraints:
    """Portfolio optimization constraints."""
    max_position_size: Decimal
    min_position_size: Decimal
    max_asset_class_weight: Dict[str, Decimal]
    min_asset_class_weight: Dict[str, Decimal]
    max_sector_weight: Dict[str, Decimal]
    min_sector_weight: Dict[str, Decimal]
    max_leverage: Decimal
    liquidity_threshold: Decimal
    custom_constraints: List[Dict[str, Any]]


@dataclass
class PortfolioDefinition:
    """Portfolio definition structure."""
    portfolio_id: str
    name: str
    description: str
    strategy: OptimizationStrategy
    constraints: PortfolioConstraints
    target_return: Optional[Decimal]
    target_risk: Optional[Decimal]
    rebalancing_trigger: RebalancingTrigger
    rebalancing_frequency: Optional[str]  # e.g., "monthly", "quarterly"
    rebalancing_threshold: Optional[Decimal]
    created_timestamp: datetime
    last_rebalanced: Optional[datetime]


@dataclass
class OptimizedPortfolio:
    """Optimized portfolio weights and metrics."""
    portfolio_id: str
    weights: Dict[str, Decimal]  # symbol -> weight
    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    diversification_ratio: Decimal
    optimization_timestamp: datetime
    metadata: Dict[str, Any]


class PortfolioOptimizer:
    """
    Comprehensive Portfolio Optimizer.
    
    Constructs, optimizes, and rebalances portfolios based on various
    strategies, risk profiles, and constraints. Integrates with market
    data and risk management systems for data-driven optimization.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 market_data_manager: MarketDataManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize portfolio optimizer.
        
        Args:
            audit_manager: Audit trail manager
            market_data_manager: Market data manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.market_data_manager = market_data_manager
        self.config = config or {}
        
        # Configuration parameters
        self.default_strategy = OptimizationStrategy(self.config.get("default_strategy", "mean_variance"))
        self.risk_free_rate = Decimal(str(self.config.get("risk_free_rate", 0.02)))
        self.max_iterations = self.config.get("max_iterations", 1000)
        self.optimization_timeout_seconds = self.config.get("optimization_timeout_seconds", 300)
        
        # Portfolio management
        self.portfolios = {}  # portfolio_id -> PortfolioDefinition
        self.optimized_portfolios = {}  # portfolio_id -> OptimizedPortfolio
        
        # Threading and processing
        self.optimizer_lock = threading.RLock()
        self.optimizer_thread = None
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "failed_optimizations": 0,
            "average_optimization_time": 0,
            "last_optimization": None
        }
        
        logger.info("Portfolio Optimizer initialized")
    
    def start(self) -> Dict[str, Any]:
        """Start portfolio optimizer."""
        try:
            if self.running:
                return {"success": False, "error": "Portfolio optimizer already running"}
            
            self.running = True
            
            # Start optimization processing thread
            self.optimizer_thread = threading.Thread(target=self._optimization_loop, daemon=True)
            self.optimizer_thread.start()
            
            logger.info("Portfolio Optimizer started")
            
            return {
                "success": True,
                "default_strategy": self.default_strategy.value,
                "risk_free_rate": float(self.risk_free_rate),
                "start_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting portfolio optimizer: {str(e)}", exc_info=True)
            self.running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop portfolio optimizer."""
        try:
            if not self.running:
                return {"success": False, "error": "Portfolio optimizer not running"}
            
            self.running = False
            
            # Wait for optimization thread to finish
            if self.optimizer_thread and self.optimizer_thread.is_alive():
                self.optimizer_thread.join(timeout=10)
            
            logger.info("Portfolio Optimizer stopped")
            
            return {
                "success": True,
                "total_optimizations": self.metrics["total_optimizations"],
                "stop_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping portfolio optimizer: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_portfolio(self, portfolio_def: PortfolioDefinition) -> Dict[str, Any]:
        """Create new portfolio definition."""
        try:
            with self.optimizer_lock:
                self.portfolios[portfolio_def.portfolio_id] = portfolio_def
            
            logger.info(f"Created portfolio definition: {portfolio_def.portfolio_id}")
            
            return {
                "success": True,
                "portfolio_id": portfolio_def.portfolio_id,
                "name": portfolio_def.name,
                "strategy": portfolio_def.strategy.value,
                "created_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating portfolio: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "portfolio_id": portfolio_def.portfolio_id
            }
    
    def optimize_portfolio(self, 
                           portfolio_id: str,
                           asset_universe: List[str],
                           historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Optimize portfolio based on its definition.
        
        Args:
            portfolio_id: ID of portfolio to optimize
            asset_universe: List of asset symbols to consider
            historical_data: DataFrame of historical prices
            
        Returns:
            Optimization result
        """
        try:
            start_time = time.time()
            
            if portfolio_id not in self.portfolios:
                return {"success": False, "error": "Portfolio not found"}
            
            portfolio_def = self.portfolios[portfolio_id]
            
            # Calculate expected returns and covariance matrix
            expected_returns = self._calculate_expected_returns(historical_data)
            covariance_matrix = self._calculate_covariance_matrix(historical_data)
            
            # Perform optimization based on strategy
            optimization_result = self._run_optimization(
                portfolio_def,
                expected_returns,
                covariance_matrix
            )
            
            if not optimization_result["success"]:
                self.metrics["failed_optimizations"] += 1
                return optimization_result
            
            # Create optimized portfolio object
            optimized_portfolio = self._create_optimized_portfolio(
                portfolio_def,
                optimization_result,
                expected_returns,
                covariance_matrix
            )
            
            with self.optimizer_lock:
                self.optimized_portfolios[portfolio_id] = optimized_portfolio
            
            # Log optimization
            self.audit_manager.log_system_event(
                event_type="portfolio_optimized",
                event_data={
                    "portfolio_id": portfolio_id,
                    "strategy": portfolio_def.strategy.value,
                    "expected_return": float(optimized_portfolio.expected_return),
                    "expected_volatility": float(optimized_portfolio.expected_volatility),
                    "sharpe_ratio": float(optimized_portfolio.sharpe_ratio)
                },
                severity="info"
            )
            
            optimization_time = time.time() - start_time
            self.metrics["total_optimizations"] += 1
            self.metrics["successful_optimizations"] += 1
            self.metrics["average_optimization_time"] = (
                (self.metrics["average_optimization_time"] * (self.metrics["successful_optimizations"] - 1) + optimization_time) / 
                self.metrics["successful_optimizations"]
            )
            self.metrics["last_optimization"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "optimized_portfolio": asdict(optimized_portfolio),
                "optimization_time_seconds": optimization_time
            }
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio {portfolio_id}: {str(e)}", exc_info=True)
            self.metrics["failed_optimizations"] += 1
            return {
                "success": False,
                "error": str(e),
                "portfolio_id": portfolio_id
            }
    
    def get_optimized_portfolio(self, portfolio_id: str) -> Optional[OptimizedPortfolio]:
        """Get optimized portfolio."""
        try:
            with self.optimizer_lock:
                return self.optimized_portfolios.get(portfolio_id)
                
        except Exception as e:
            logger.error(f"Error getting optimized portfolio {portfolio_id}: {str(e)}")
            return None
    
    def _calculate_expected_returns(self, historical_data: pd.DataFrame) -> pd.Series:
        """Calculate expected returns from historical data."""
        try:
            # Simple mean of daily returns, annualized
            daily_returns = historical_data.pct_change().dropna()
            expected_returns = daily_returns.mean() * 252  # 252 trading days
            return expected_returns
            
        except Exception as e:
            logger.error(f"Error calculating expected returns: {str(e)}")
            return pd.Series()
    
    def _calculate_covariance_matrix(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate covariance matrix from historical data."""
        try:
            daily_returns = historical_data.pct_change().dropna()
            covariance_matrix = daily_returns.cov() * 252
            return covariance_matrix
            
        except Exception as e:
            logger.error(f"Error calculating covariance matrix: {str(e)}")
            return pd.DataFrame()
    
    def _run_optimization(self, 
                          portfolio_def: PortfolioDefinition,
                          expected_returns: pd.Series,
                          covariance_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Run optimization based on strategy."""
        try:
            num_assets = len(expected_returns)
            
            # Initial guess (equal weights)
            initial_weights = np.array([1 / num_assets] * num_assets)
            
            # Constraints
            constraints = (
                {"type": "eq", "fun": lambda weights: np.sum(weights) - 1}  # Sum of weights = 1
            )
            
            # Bounds (0 <= weight <= 1)
            bounds = tuple((0, 1) for _ in range(num_assets))
            
            # Optimization function based on strategy
            if portfolio_def.strategy == OptimizationStrategy.MAX_SHARPE:
                objective_function = self._sharpe_ratio_objective
                args = (expected_returns.values, covariance_matrix.values, self.risk_free_rate)
            elif portfolio_def.strategy == OptimizationStrategy.MIN_VOLATILITY:
                objective_function = self._portfolio_volatility
                args = (covariance_matrix.values,)
            else:  # Default to Mean-Variance
                objective_function = self._mean_variance_objective
                args = (expected_returns.values, covariance_matrix.values, portfolio_def.target_return)
            
            # Run optimization
            result = minimize(
                objective_function,
                initial_weights,
                args=args,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": self.max_iterations}
            )
            
            if not result.success:
                return {"success": False, "error": result.message}
            
            return {"success": True, "weights": result.x}
            
        except Exception as e:
            logger.error(f"Error running optimization: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_optimized_portfolio(self, 
                                    portfolio_def: PortfolioDefinition,
                                    optimization_result: Dict[str, Any],
                                    expected_returns: pd.Series,
                                    covariance_matrix: pd.DataFrame) -> OptimizedPortfolio:
        """Create optimized portfolio object."""
        try:
            weights = optimization_result["weights"]
            
            # Calculate portfolio metrics
            portfolio_return = np.sum(weights * expected_returns.values)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix.values, weights)))
            sharpe_ratio = (portfolio_return - float(self.risk_free_rate)) / portfolio_volatility
            
            # Diversification ratio (simplified)
            diversification_ratio = 1 / np.sum(weights**2)
            
            # Create optimized portfolio
            optimized_portfolio = OptimizedPortfolio(
                portfolio_id=portfolio_def.portfolio_id,
                weights={symbol: Decimal(str(weight)) for symbol, weight in zip(expected_returns.index, weights)},
                expected_return=Decimal(str(portfolio_return)),
                expected_volatility=Decimal(str(portfolio_volatility)),
                sharpe_ratio=Decimal(str(sharpe_ratio)),
                diversification_ratio=Decimal(str(diversification_ratio)),
                optimization_timestamp=datetime.now(),
                metadata={
                    "strategy": portfolio_def.strategy.value,
                    "num_assets": len(expected_returns)
                }
            )
            
            return optimized_portfolio
            
        except Exception as e:
            logger.error(f"Error creating optimized portfolio: {str(e)}")
            raise
    
    def _sharpe_ratio_objective(self, weights, expected_returns, covariance_matrix, risk_free_rate):
        """Objective function for max Sharpe ratio (negative for minimization)."""
        portfolio_return = np.sum(weights * expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
        sharpe_ratio = (portfolio_return - float(risk_free_rate)) / portfolio_volatility
        return -sharpe_ratio
    
    def _portfolio_volatility(self, weights, covariance_matrix):
        """Objective function for min volatility."""
        return np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
    
    def _mean_variance_objective(self, weights, expected_returns, covariance_matrix, target_return):
        """Objective function for mean-variance optimization."""
        # This is a simplified version, would typically use a risk aversion parameter
        portfolio_return = np.sum(weights * expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
        
        # Penalize deviation from target return
        return portfolio_volatility + abs(portfolio_return - float(target_return))
    
    def _optimization_loop(self):
        """Main optimization processing loop."""
        logger.info("Portfolio optimization loop started")
        
        while self.running:
            try:
                # This loop can be used for periodic rebalancing or other background tasks
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {str(e)}", exc_info=True)
                time.sleep(300)  # Longer sleep on error
        
        logger.info("Portfolio optimization loop stopped")
    
    def get_optimizer_status(self) -> Dict[str, Any]:
        """Get portfolio optimizer status."""
        try:
            return {
                "success": True,
                "running": self.running,
                "total_portfolios": len(self.portfolios),
                "optimized_portfolios": len(self.optimized_portfolios),
                "metrics": self.metrics.copy(),
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimizer status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

