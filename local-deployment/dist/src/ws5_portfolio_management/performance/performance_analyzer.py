"""
Performance Analyzer

This module implements the comprehensive performance analysis system that
provides performance attribution, risk-adjusted metrics, and benchmarking
for the True-Asset-ALLUSE system.
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


class AttributionModel(Enum):
    """Performance attribution models."""
    BRINSON_FACHLER = "brinson_fachler"
    BRINSON_HOOD_BEBOWER = "brinson_hood_bebower"
    CUSTOM = "custom"


class RiskAdjustedMetric(Enum):
    """Risk-adjusted return metrics."""
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    TREYNOR_RATIO = "treynor_ratio"
    CALMAR_RATIO = "calmar_ratio"
    INFORMATION_RATIO = "information_ratio"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    portfolio_id: str
    start_date: date
    end_date: date
    total_return: Decimal
    annualized_return: Decimal
    annualized_volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    treynor_ratio: Decimal
    calmar_ratio: Decimal
    information_ratio: Decimal
    beta: Decimal
    alpha: Decimal
    correlation: Decimal
    tracking_error: Decimal
    skewness: Decimal
    kurtosis: Decimal
    value_at_risk: Decimal
    conditional_value_at_risk: Decimal
    calculation_timestamp: datetime


@dataclass
class AttributionResult:
    """Performance attribution result."""
    portfolio_id: str
    benchmark_id: str
    model: AttributionModel
    allocation_effect: Decimal
    selection_effect: Decimal
    interaction_effect: Decimal
    total_excess_return: Decimal
    calculation_timestamp: datetime


class PerformanceAnalyzer:
    """
    Comprehensive Performance Analyzer.
    
    Provides performance attribution, risk-adjusted metrics, benchmarking,
    and comprehensive performance analysis for the True-Asset-ALLUSE system.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 market_data_manager: MarketDataManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance analyzer.
        
        Args:
            audit_manager: Audit trail manager
            market_data_manager: Market data manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.market_data_manager = market_data_manager
        self.config = config or {}
        
        # Configuration parameters
        self.default_attribution_model = AttributionModel(self.config.get("default_attribution_model", "brinson_fachler"))
        self.risk_free_rate = Decimal(str(self.config.get("risk_free_rate", 0.02)))
        self.downside_risk_threshold = Decimal(str(self.config.get("downside_risk_threshold", 0.0)))
        
        # Performance data storage
        self.performance_history = {}  # portfolio_id -> pd.DataFrame
        self.attribution_history = {}  # portfolio_id -> List[AttributionResult]
        
        # Threading and processing
        self.analyzer_lock = threading.RLock()
        self.analyzer_thread = None
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_analysis_time": 0,
            "last_analysis": None
        }
        
        logger.info("Performance Analyzer initialized")
    
    def start(self) -> Dict[str, Any]:
        """Start performance analyzer."""
        try:
            if self.running:
                return {"success": False, "error": "Performance analyzer already running"}
            
            self.running = True
            
            # Start analysis processing thread
            self.analyzer_thread = threading.Thread(target=self._analysis_loop, daemon=True)
            self.analyzer_thread.start()
            
            logger.info("Performance Analyzer started")
            
            return {
                "success": True,
                "default_attribution_model": self.default_attribution_model.value,
                "risk_free_rate": float(self.risk_free_rate),
                "start_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting performance analyzer: {str(e)}", exc_info=True)
            self.running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop performance analyzer."""
        try:
            if not self.running:
                return {"success": False, "error": "Performance analyzer not running"}
            
            self.running = False
            
            # Wait for analysis thread to finish
            if self.analyzer_thread and self.analyzer_thread.is_alive():
                self.analyzer_thread.join(timeout=10)
            
            logger.info("Performance Analyzer stopped")
            
            return {
                "success": True,
                "total_analyses": self.metrics["total_analyses"],
                "stop_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping performance analyzer: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_performance_metrics(self, 
                                      portfolio_id: str,
                                      portfolio_returns: pd.Series,
                                      benchmark_returns: pd.Series) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            portfolio_id: ID of the portfolio
            portfolio_returns: Series of portfolio daily returns
            benchmark_returns: Series of benchmark daily returns
            
        Returns:
            Performance metrics result
        """
        try:
            start_time = time.time()
            
            # Calculate metrics
            total_return = self._calculate_total_return(portfolio_returns)
            annualized_return = self._calculate_annualized_return(portfolio_returns)
            annualized_volatility = self._calculate_annualized_volatility(portfolio_returns)
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)
            sharpe_ratio = self._calculate_sharpe_ratio(annualized_return, annualized_volatility)
            sortino_ratio = self._calculate_sortino_ratio(annualized_return, portfolio_returns)
            beta = self._calculate_beta(portfolio_returns, benchmark_returns)
            treynor_ratio = self._calculate_treynor_ratio(annualized_return, beta)
            calmar_ratio = self._calculate_calmar_ratio(annualized_return, max_drawdown)
            alpha = self._calculate_alpha(annualized_return, beta, benchmark_returns)
            information_ratio = self._calculate_information_ratio(annualized_return, benchmark_returns)
            correlation = self._calculate_correlation(portfolio_returns, benchmark_returns)
            tracking_error = self._calculate_tracking_error(portfolio_returns, benchmark_returns)
            skewness = self._calculate_skewness(portfolio_returns)
            kurtosis = self._calculate_kurtosis(portfolio_returns)
            value_at_risk = self._calculate_value_at_risk(portfolio_returns)
            conditional_value_at_risk = self._calculate_conditional_value_at_risk(portfolio_returns)
            
            performance_metrics = PerformanceMetrics(
                portfolio_id=portfolio_id,
                start_date=portfolio_returns.index.min().date(),
                end_date=portfolio_returns.index.max().date(),
                total_return=total_return,
                annualized_return=annualized_return,
                annualized_volatility=annualized_volatility,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                treynor_ratio=treynor_ratio,
                calmar_ratio=calmar_ratio,
                information_ratio=information_ratio,
                beta=beta,
                alpha=alpha,
                correlation=correlation,
                tracking_error=tracking_error,
                skewness=skewness,
                kurtosis=kurtosis,
                value_at_risk=value_at_risk,
                conditional_value_at_risk=conditional_value_at_risk,
                calculation_timestamp=datetime.now()
            )
            
            # Log analysis
            self.audit_manager.log_system_event(
                event_type="performance_analysis_completed",
                event_data={
                    "portfolio_id": portfolio_id,
                    "total_return": float(total_return),
                    "sharpe_ratio": float(sharpe_ratio),
                    "max_drawdown": float(max_drawdown)
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
                "performance_metrics": asdict(performance_metrics),
                "analysis_time_seconds": analysis_time
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics for {portfolio_id}: {str(e)}", exc_info=True)
            self.metrics["failed_analyses"] += 1
            return {
                "success": False,
                "error": str(e),
                "portfolio_id": portfolio_id
            }
    
    def perform_attribution_analysis(self, 
                                     portfolio_id: str,
                                     portfolio_weights: pd.DataFrame,
                                     portfolio_returns: pd.Series,
                                     benchmark_weights: pd.DataFrame,
                                     benchmark_returns: pd.Series,
                                     model: AttributionModel) -> Dict[str, Any]:
        """
        Perform performance attribution analysis.
        
        Args:
            portfolio_id: ID of the portfolio
            portfolio_weights: DataFrame of portfolio asset weights
            portfolio_returns: Series of portfolio daily returns
            benchmark_weights: DataFrame of benchmark asset weights
            benchmark_returns: Series of benchmark daily returns
            model: Attribution model to use
            
        Returns:
            Attribution analysis result
        """
        try:
            if model == AttributionModel.BRINSON_FACHLER:
                attribution_result = self._brinson_fachler_attribution(
                    portfolio_weights, portfolio_returns, benchmark_weights, benchmark_returns
                )
            else:
                return {"success": False, "error": "Attribution model not supported"}
            
            result = AttributionResult(
                portfolio_id=portfolio_id,
                benchmark_id="benchmark",  # Placeholder
                model=model,
                allocation_effect=Decimal(str(attribution_result["allocation"])),
                selection_effect=Decimal(str(attribution_result["selection"])),
                interaction_effect=Decimal(str(attribution_result["interaction"])),
                total_excess_return=Decimal(str(attribution_result["total_excess"])),
                calculation_timestamp=datetime.now()
            )
            
            with self.analyzer_lock:
                if portfolio_id not in self.attribution_history:
                    self.attribution_history[portfolio_id] = []
                self.attribution_history[portfolio_id].append(result)
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "attribution_result": asdict(result)
            }
            
        except Exception as e:
            logger.error(f"Error performing attribution analysis for {portfolio_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "portfolio_id": portfolio_id
            }
    
    def _calculate_total_return(self, returns: pd.Series) -> Decimal:
        return Decimal(str((1 + returns).prod() - 1))
    
    def _calculate_annualized_return(self, returns: pd.Series) -> Decimal:
        return Decimal(str(returns.mean() * 252))
    
    def _calculate_annualized_volatility(self, returns: pd.Series) -> Decimal:
        return Decimal(str(returns.std() * np.sqrt(252)))
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> Decimal:
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        return Decimal(str(drawdown.min()))
    
    def _calculate_sharpe_ratio(self, annualized_return: Decimal, annualized_volatility: Decimal) -> Decimal:
        if annualized_volatility == 0:
            return Decimal("0")
        return (annualized_return - self.risk_free_rate) / annualized_volatility
    
    def _calculate_sortino_ratio(self, annualized_return: Decimal, returns: pd.Series) -> Decimal:
        downside_returns = returns[returns < float(self.downside_risk_threshold)]
        downside_volatility = downside_returns.std() * np.sqrt(252)
        if downside_volatility == 0:
            return Decimal("0")
        return (annualized_return - self.risk_free_rate) / Decimal(str(downside_volatility))
    
    def _calculate_beta(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> Decimal:
        covariance = portfolio_returns.cov(benchmark_returns)
        variance = benchmark_returns.var()
        if variance == 0:
            return Decimal("0")
        return Decimal(str(covariance / variance))
    
    def _calculate_treynor_ratio(self, annualized_return: Decimal, beta: Decimal) -> Decimal:
        if beta == 0:
            return Decimal("0")
        return (annualized_return - self.risk_free_rate) / beta
    
    def _calculate_calmar_ratio(self, annualized_return: Decimal, max_drawdown: Decimal) -> Decimal:
        if max_drawdown == 0:
            return Decimal("0")
        return annualized_return / abs(max_drawdown)
    
    def _calculate_alpha(self, annualized_return: Decimal, beta: Decimal, benchmark_returns: pd.Series) -> Decimal:
        benchmark_annualized_return = self._calculate_annualized_return(benchmark_returns)
        expected_return = self.risk_free_rate + beta * (benchmark_annualized_return - self.risk_free_rate)
        return annualized_return - expected_return
    
    def _calculate_information_ratio(self, annualized_return: Decimal, benchmark_returns: pd.Series) -> Decimal:
        benchmark_annualized_return = self._calculate_annualized_return(benchmark_returns)
        excess_return = annualized_return - benchmark_annualized_return
        tracking_error = self._calculate_tracking_error(annualized_return, benchmark_returns)
        if tracking_error == 0:
            return Decimal("0")
        return excess_return / tracking_error
    
    def _calculate_correlation(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> Decimal:
        return Decimal(str(portfolio_returns.corr(benchmark_returns)))
    
    def _calculate_tracking_error(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> Decimal:
        excess_returns = portfolio_returns - benchmark_returns
        return Decimal(str(excess_returns.std() * np.sqrt(252)))
    
    def _calculate_skewness(self, returns: pd.Series) -> Decimal:
        return Decimal(str(returns.skew()))
    
    def _calculate_kurtosis(self, returns: pd.Series) -> Decimal:
        return Decimal(str(returns.kurtosis()))
    
    def _calculate_value_at_risk(self, returns: pd.Series, confidence_level: float = 0.95) -> Decimal:
        return Decimal(str(returns.quantile(1 - confidence_level)))
    
    def _calculate_conditional_value_at_risk(self, returns: pd.Series, confidence_level: float = 0.95) -> Decimal:
        var = self._calculate_value_at_risk(returns, confidence_level)
        return Decimal(str(returns[returns <= float(var)].mean()))
    
    def _brinson_fachler_attribution(self, 
                                     portfolio_weights: pd.DataFrame,
                                     portfolio_returns: pd.Series,
                                     benchmark_weights: pd.DataFrame,
                                     benchmark_returns: pd.Series) -> Dict[str, float]:
        """Brinson-Fachler attribution model."""
        # This is a simplified implementation
        # Assumes weights and returns are aligned by date and assets
        
        # Calculate sector returns for benchmark
        sector_returns = (benchmark_weights * benchmark_returns).sum(axis=1)
        
        # Calculate allocation effect
        allocation_effect = ((portfolio_weights.mean() - benchmark_weights.mean()) * (sector_returns.mean() - benchmark_returns.mean().mean())).sum()
        
        # Calculate selection effect
        selection_effect = (benchmark_weights.mean() * (portfolio_returns.mean() - sector_returns.mean())).sum()
        
        # Calculate interaction effect
        interaction_effect = ((portfolio_weights.mean() - benchmark_weights.mean()) * (portfolio_returns.mean() - sector_returns.mean())).sum()
        
        total_excess = allocation_effect + selection_effect + interaction_effect
        
        return {
            "allocation": allocation_effect,
            "selection": selection_effect,
            "interaction": interaction_effect,
            "total_excess": total_excess
        }
    
    def _analysis_loop(self):
        """Main analysis processing loop."""
        logger.info("Performance analysis loop started")
        
        while self.running:
            try:
                # This loop can be used for periodic performance calculations
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {str(e)}", exc_info=True)
                time.sleep(600)  # Longer sleep on error
        
        logger.info("Performance analysis loop stopped")
    
    def get_analyzer_status(self) -> Dict[str, Any]:
        """Get performance analyzer status."""
        try:
            return {
                "success": True,
                "running": self.running,
                "total_analyses": self.metrics["total_analyses"],
                "metrics": self.metrics.copy(),
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting analyzer status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

