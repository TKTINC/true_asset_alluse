"""
Portfolio Risk Manager

This module implements the comprehensive portfolio risk management system
that provides risk modeling, analysis, monitoring, and alerting for the
True-Asset-ALLUSE system.
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

from src.ws1_rules_engine.audit import AuditTrailManager
from src.ws4_market_data_execution.market_data.market_data_manager import MarketDataManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class RiskModel(Enum):
    """Portfolio risk models."""
    HISTORICAL_SIMULATION = "historical_simulation"
    MONTE_CARLO = "monte_carlo"
    PARAMETRIC = "parametric"
    CUSTOM = "custom"


class RiskMetric(Enum):
    """Portfolio risk metrics."""
    VALUE_AT_RISK = "value_at_risk"
    CONDITIONAL_VALUE_AT_RISK = "conditional_value_at_risk"
    EXPECTED_SHORTFALL = "expected_shortfall"
    STRESS_TEST = "stress_test"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"


@dataclass
class RiskAnalysisResult:
    """Comprehensive risk analysis result."""
    portfolio_id: str
    model: RiskModel
    value_at_risk_95: Decimal
    value_at_risk_99: Decimal
    conditional_value_at_risk_95: Decimal
    conditional_value_at_risk_99: Decimal
    expected_shortfall: Decimal
    stress_test_results: Dict[str, Decimal]
    sensitivity_analysis_results: Dict[str, Decimal]
    calculation_timestamp: datetime


class PortfolioRiskManager:
    """
    Comprehensive Portfolio Risk Manager.
    
    Provides risk modeling, analysis, monitoring, and alerting for the
    True-Asset-ALLUSE system, integrating with market data and portfolio
    management systems for comprehensive risk oversight.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 market_data_manager: MarketDataManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize portfolio risk manager.
        
        Args:
            audit_manager: Audit trail manager
            market_data_manager: Market data manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.market_data_manager = market_data_manager
        self.config = config or {}
        
        # Configuration parameters
        self.default_risk_model = RiskModel(self.config.get("default_risk_model", "historical_simulation"))
        self.var_confidence_levels = self.config.get("var_confidence_levels", [0.95, 0.99])
        self.monte_carlo_simulations = self.config.get("monte_carlo_simulations", 10000)
        
        # Risk data storage
        self.risk_analysis_history = {}  # portfolio_id -> List[RiskAnalysisResult]
        
        # Threading and processing
        self.risk_manager_lock = threading.RLock()
        self.risk_manager_thread = None
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_analysis_time": 0,
            "last_analysis": None
        }
        
        logger.info("Portfolio Risk Manager initialized")
    
    def start(self) -> Dict[str, Any]:
        """Start portfolio risk manager."""
        try:
            if self.running:
                return {"success": False, "error": "Portfolio risk manager already running"}
            
            self.running = True
            
            # Start risk analysis processing thread
            self.risk_manager_thread = threading.Thread(target=self._risk_analysis_loop, daemon=True)
            self.risk_manager_thread.start()
            
            logger.info("Portfolio Risk Manager started")
            
            return {
                "success": True,
                "default_risk_model": self.default_risk_model.value,
                "start_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting portfolio risk manager: {str(e)}", exc_info=True)
            self.running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop portfolio risk manager."""
        try:
            if not self.running:
                return {"success": False, "error": "Portfolio risk manager not running"}
            
            self.running = False
            
            # Wait for risk analysis thread to finish
            if self.risk_manager_thread and self.risk_manager_thread.is_alive():
                self.risk_manager_thread.join(timeout=10)
            
            logger.info("Portfolio Risk Manager stopped")
            
            return {
                "success": True,
                "total_analyses": self.metrics["total_analyses"],
                "stop_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping portfolio risk manager: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def perform_risk_analysis(self, 
                              portfolio_id: str,
                              portfolio_returns: pd.Series,
                              model: RiskModel) -> Dict[str, Any]:
        """
        Perform comprehensive portfolio risk analysis.
        
        Args:
            portfolio_id: ID of the portfolio
            portfolio_returns: Series of portfolio daily returns
            model: Risk model to use
            
        Returns:
            Risk analysis result
        """
        try:
            start_time = time.time()
            
            if model == RiskModel.HISTORICAL_SIMULATION:
                risk_results = self._historical_simulation_analysis(portfolio_returns)
            elif model == RiskModel.MONTE_CARLO:
                risk_results = self._monte_carlo_analysis(portfolio_returns)
            elif model == RiskModel.PARAMETRIC:
                risk_results = self._parametric_analysis(portfolio_returns)
            else:
                return {"success": False, "error": "Risk model not supported"}
            
            analysis_result = RiskAnalysisResult(
                portfolio_id=portfolio_id,
                model=model,
                value_at_risk_95=Decimal(str(risk_results["var_95"])),
                value_at_risk_99=Decimal(str(risk_results["var_99"])),
                conditional_value_at_risk_95=Decimal(str(risk_results["cvar_95"])),
                conditional_value_at_risk_99=Decimal(str(risk_results["cvar_99"])),
                expected_shortfall=Decimal(str(risk_results["expected_shortfall"])),
                stress_test_results={},
                sensitivity_analysis_results={},
                calculation_timestamp=datetime.now()
            )
            
            with self.risk_manager_lock:
                if portfolio_id not in self.risk_analysis_history:
                    self.risk_analysis_history[portfolio_id] = []
                self.risk_analysis_history[portfolio_id].append(analysis_result)
            
            # Log analysis
            self.audit_manager.log_system_event(
                event_type="risk_analysis_completed",
                event_data={
                    "portfolio_id": portfolio_id,
                    "model": model.value,
                    "var_95": float(analysis_result.value_at_risk_95),
                    "cvar_95": float(analysis_result.conditional_value_at_risk_95)
                },
                severity="info"
            )
            
            analysis_time = time.time() - start_time
            self.metrics["total_analyses"] += 1
            self.metrics["successful_analyses"] += 1
            self.metrics["average_analysis_time"] = (
                (self.metrics["average_analysis_time"] * (self.metrics["successful_analyses"] - 1) + analysis_time) / 
                self.metrics["successful_analyses"]
            )
            self.metrics["last_analysis"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "risk_analysis_result": asdict(analysis_result),
                "analysis_time_seconds": analysis_time
            }
            
        except Exception as e:
            logger.error(f"Error performing risk analysis for {portfolio_id}: {str(e)}", exc_info=True)
            self.metrics["failed_analyses"] += 1
            return {
                "success": False,
                "error": str(e),
                "portfolio_id": portfolio_id
            }
    
    def _historical_simulation_analysis(self, returns: pd.Series) -> Dict[str, float]:
        """Historical simulation risk analysis."""
        var_95 = returns.quantile(0.05)
        var_99 = returns.quantile(0.01)
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()
        expected_shortfall = cvar_95  # Simplified
        
        return {
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "expected_shortfall": expected_shortfall
        }
    
    def _monte_carlo_analysis(self, returns: pd.Series) -> Dict[str, float]:
        """Monte Carlo simulation risk analysis."""
        mean = returns.mean()
        std_dev = returns.std()
        
        simulated_returns = np.random.normal(mean, std_dev, self.monte_carlo_simulations)
        
        var_95 = np.percentile(simulated_returns, 5)
        var_99 = np.percentile(simulated_returns, 1)
        cvar_95 = simulated_returns[simulated_returns <= var_95].mean()
        cvar_99 = simulated_returns[simulated_returns <= var_99].mean()
        expected_shortfall = cvar_95
        
        return {
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "expected_shortfall": expected_shortfall
        }
    
    def _parametric_analysis(self, returns: pd.Series) -> Dict[str, float]:
        """Parametric (Variance-Covariance) risk analysis."""
        from scipy.stats import norm
        
        mean = returns.mean()
        std_dev = returns.std()
        
        var_95 = norm.ppf(0.05, loc=mean, scale=std_dev)
        var_99 = norm.ppf(0.01, loc=mean, scale=std_dev)
        
        # CVaR for normal distribution
        cvar_95 = mean - std_dev * (norm.pdf(norm.ppf(0.05)) / 0.05)
        cvar_99 = mean - std_dev * (norm.pdf(norm.ppf(0.01)) / 0.01)
        expected_shortfall = cvar_95
        
        return {
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "expected_shortfall": expected_shortfall
        }
    
    def _risk_analysis_loop(self):
        """Main risk analysis processing loop."""
        logger.info("Portfolio risk analysis loop started")
        
        while self.running:
            try:
                # This loop can be used for periodic risk calculations
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in risk analysis loop: {str(e)}", exc_info=True)
                time.sleep(600)  # Longer sleep on error
        
        logger.info("Portfolio risk analysis loop stopped")
    
    def get_risk_manager_status(self) -> Dict[str, Any]:
        """Get portfolio risk manager status."""
        try:
            return {
                "success": True,
                "running": self.running,
                "total_analyses": self.metrics["total_analyses"],
                "metrics": self.metrics.copy(),
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting risk manager status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

