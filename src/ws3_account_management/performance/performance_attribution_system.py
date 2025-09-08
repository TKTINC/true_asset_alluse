"""
Performance Attribution System

This module implements comprehensive performance tracking and attribution
across the three-tiered account structure with support for forked account
hierarchies, cross-account analysis, and performance-based decision making.
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, date, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict
import uuid
import statistics

from src.ws3_account_management.accounts import AccountType, Account
from src.ws1_rules_engine.audit import AuditTrailManager

# Set decimal precision for financial calculations
getcontext().prec = 10

logger = logging.getLogger(__name__)


class PerformancePeriod(Enum):
    """Performance measurement periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    INCEPTION = "inception"


class PerformanceMetric(Enum):
    """Performance metrics."""
    TOTAL_RETURN = "total_return"
    ANNUALIZED_RETURN = "annualized_return"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for a specific time period."""
    snapshot_id: str
    account_id: str
    account_type: AccountType
    period: PerformancePeriod
    start_date: date
    end_date: date
    start_value: Decimal
    end_value: Decimal
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Optional[Decimal]
    win_rate: Decimal
    profit_factor: Decimal
    trade_count: int
    winning_trades: int
    losing_trades: int
    largest_win: Decimal
    largest_loss: Decimal
    average_win: Decimal
    average_loss: Decimal
    benchmark_return: Optional[Decimal]
    alpha: Optional[Decimal]
    beta: Optional[Decimal]
    information_ratio: Optional[Decimal]
    tracking_error: Optional[Decimal]
    timestamp: datetime


@dataclass
class HierarchyPerformance:
    """Performance analysis across account hierarchy."""
    hierarchy_id: str
    root_account_id: str
    total_accounts: int
    total_value: Decimal
    weighted_return: Decimal
    best_performer: str
    worst_performer: str
    performance_spread: Decimal
    correlation_matrix: Dict[str, Dict[str, Decimal]]
    attribution_analysis: Dict[str, Decimal]
    risk_contribution: Dict[str, Decimal]
    timestamp: datetime


@dataclass
class PerformanceComparison:
    """Performance comparison between accounts or periods."""
    comparison_id: str
    comparison_type: str
    accounts: List[str]
    period: PerformancePeriod
    metrics: Dict[str, Dict[str, Any]]
    rankings: Dict[str, int]
    statistical_significance: Dict[str, bool]
    insights: List[str]
    recommendations: List[str]
    timestamp: datetime


class PerformanceAttributionSystem:
    """
    Comprehensive performance attribution system.
    
    Tracks performance across the three-tiered account structure,
    provides attribution analysis for forked accounts, and enables
    performance-based decision making for forking and merging.
    """
    
    def __init__(self, 
                 audit_manager: AuditTrailManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance attribution system.
        
        Args:
            audit_manager: Audit trail manager
            config: Optional configuration
        """
        self.audit_manager = audit_manager
        self.config = config or {}
        
        # Configuration parameters
        self.risk_free_rate = Decimal(str(self.config.get("risk_free_rate", 0.02)))  # 2% annual
        self.benchmark_return = Decimal(str(self.config.get("benchmark_return", 0.10)))  # 10% annual
        self.min_tracking_period_days = self.config.get("min_tracking_period_days", 30)
        
        # Performance data storage
        self.performance_snapshots = {}  # snapshot_id -> PerformanceSnapshot
        self.hierarchy_performance = {}  # hierarchy_id -> HierarchyPerformance
        self.performance_comparisons = {}  # comparison_id -> PerformanceComparison
        self.daily_values = {}  # account_id -> List[Tuple[date, Decimal]]
        
        # Benchmark data (simplified - would integrate with market data)
        self.benchmark_data = {}  # date -> benchmark_value
        
        logger.info("Performance Attribution System initialized")
    
    def track_account_performance(self, 
                                account_id: str,
                                account_value: Decimal,
                                date_recorded: Optional[date] = None) -> Dict[str, Any]:
        """
        Track daily account performance.
        
        Args:
            account_id: Account ID
            account_value: Current account value
            date_recorded: Date of recording (defaults to today)
            
        Returns:
            Tracking result
        """
        try:
            if date_recorded is None:
                date_recorded = date.today()
            
            # Initialize account tracking if needed
            if account_id not in self.daily_values:
                self.daily_values[account_id] = []
            
            # Add daily value
            self.daily_values[account_id].append((date_recorded, account_value))
            
            # Sort by date and remove duplicates
            self.daily_values[account_id] = sorted(list(set(self.daily_values[account_id])))
            
            # Trim old data (keep last 2 years)
            cutoff_date = date_recorded - timedelta(days=730)
            self.daily_values[account_id] = [
                (d, v) for d, v in self.daily_values[account_id]
                if d >= cutoff_date
            ]
            
            # Calculate recent performance metrics
            recent_performance = self._calculate_recent_performance(account_id)
            
            return {
                "success": True,
                "account_id": account_id,
                "date_recorded": date_recorded.isoformat(),
                "account_value": float(account_value),
                "data_points": len(self.daily_values[account_id]),
                "recent_performance": recent_performance,
                "tracking_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error tracking account performance for {account_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id
            }
    
    def generate_performance_snapshot(self, 
                                    account_id: str,
                                    account_type: AccountType,
                                    period: PerformancePeriod,
                                    end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance snapshot.
        
        Args:
            account_id: Account ID
            account_type: Account type
            period: Performance period
            end_date: End date (defaults to today)
            
        Returns:
            Performance snapshot
        """
        try:
            if end_date is None:
                end_date = date.today()
            
            # Calculate period start date
            start_date = self._calculate_period_start_date(period, end_date)
            
            # Get account values for period
            period_values = self._get_period_values(account_id, start_date, end_date)
            
            if len(period_values) < 2:
                return {
                    "success": False,
                    "error": "Insufficient data for performance calculation",
                    "account_id": account_id,
                    "period": period.value
                }
            
            # Calculate performance metrics
            start_value = period_values[0][1]
            end_value = period_values[-1][1]
            
            # Calculate returns
            total_return = (end_value - start_value) / start_value
            period_days = (end_date - start_date).days
            annualized_return = self._annualize_return(total_return, period_days)
            
            # Calculate volatility
            returns = self._calculate_daily_returns(period_values)
            volatility = self._calculate_volatility(returns)
            
            # Calculate drawdown
            max_drawdown = self._calculate_max_drawdown(period_values)
            
            # Calculate risk-adjusted metrics
            sharpe_ratio = self._calculate_sharpe_ratio(annualized_return, volatility)
            
            # Calculate trade-based metrics (simplified)
            trade_metrics = self._calculate_trade_metrics(account_id, start_date, end_date)
            
            # Calculate benchmark comparison
            benchmark_metrics = self._calculate_benchmark_comparison(
                account_id, start_date, end_date, annualized_return
            )
            
            # Create performance snapshot
            snapshot = PerformanceSnapshot(
                snapshot_id=f"perf_{account_id}_{period.value}_{end_date.strftime('%Y%m%d')}",
                account_id=account_id,
                account_type=account_type,
                period=period,
                start_date=start_date,
                end_date=end_date,
                start_value=start_value,
                end_value=end_value,
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=trade_metrics["win_rate"],
                profit_factor=trade_metrics["profit_factor"],
                trade_count=trade_metrics["trade_count"],
                winning_trades=trade_metrics["winning_trades"],
                losing_trades=trade_metrics["losing_trades"],
                largest_win=trade_metrics["largest_win"],
                largest_loss=trade_metrics["largest_loss"],
                average_win=trade_metrics["average_win"],
                average_loss=trade_metrics["average_loss"],
                benchmark_return=benchmark_metrics["benchmark_return"],
                alpha=benchmark_metrics["alpha"],
                beta=benchmark_metrics["beta"],
                information_ratio=benchmark_metrics["information_ratio"],
                tracking_error=benchmark_metrics["tracking_error"],
                timestamp=datetime.now()
            )
            
            # Store snapshot
            self.performance_snapshots[snapshot.snapshot_id] = snapshot
            
            # Log performance snapshot
            self.audit_manager.log_system_event(
                event_type="performance_snapshot_generated",
                event_data={
                    "account_id": account_id,
                    "period": period.value,
                    "total_return": float(total_return),
                    "annualized_return": float(annualized_return),
                    "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio else None
                },
                severity="info"
            )
            
            return {
                "success": True,
                "snapshot": asdict(snapshot),
                "generation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance snapshot for {account_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_id": account_id,
                "period": period.value if period else "unknown"
            }
    
    def analyze_hierarchy_performance(self, 
                                    root_account_id: str,
                                    child_accounts: List[Account]) -> Dict[str, Any]:
        """
        Analyze performance across account hierarchy.
        
        Args:
            root_account_id: Root account ID
            child_accounts: List of child accounts
            
        Returns:
            Hierarchy performance analysis
        """
        try:
            all_accounts = [root_account_id] + [acc.account_id for acc in child_accounts]
            
            # Generate performance snapshots for all accounts
            account_performances = {}
            total_value = Decimal("0")
            
            for account_id in all_accounts:
                # Get account type (simplified)
                account_type = AccountType.GEN_ACC  # Would get from account data
                
                snapshot_result = self.generate_performance_snapshot(
                    account_id, account_type, PerformancePeriod.MONTHLY
                )
                
                if snapshot_result["success"]:
                    snapshot = snapshot_result["snapshot"]
                    account_performances[account_id] = snapshot
                    total_value += Decimal(str(snapshot["end_value"]))
            
            if not account_performances:
                return {
                    "success": False,
                    "error": "No performance data available for hierarchy analysis"
                }
            
            # Calculate weighted return
            weighted_return = Decimal("0")
            for account_id, perf in account_performances.items():
                weight = Decimal(str(perf["end_value"])) / total_value
                weighted_return += weight * Decimal(str(perf["annualized_return"]))
            
            # Find best and worst performers
            returns = {aid: Decimal(str(perf["annualized_return"])) for aid, perf in account_performances.items()}
            best_performer = max(returns.keys(), key=lambda k: returns[k])
            worst_performer = min(returns.keys(), key=lambda k: returns[k])
            performance_spread = returns[best_performer] - returns[worst_performer]
            
            # Calculate correlation matrix
            correlation_matrix = self._calculate_correlation_matrix(all_accounts)
            
            # Calculate attribution analysis
            attribution_analysis = self._calculate_attribution_analysis(account_performances, total_value)
            
            # Calculate risk contribution
            risk_contribution = self._calculate_risk_contribution(account_performances, total_value)
            
            # Create hierarchy performance
            hierarchy_perf = HierarchyPerformance(
                hierarchy_id=f"hier_{root_account_id}_{datetime.now().strftime('%Y%m%d')}",
                root_account_id=root_account_id,
                total_accounts=len(all_accounts),
                total_value=total_value,
                weighted_return=weighted_return,
                best_performer=best_performer,
                worst_performer=worst_performer,
                performance_spread=performance_spread,
                correlation_matrix=correlation_matrix,
                attribution_analysis=attribution_analysis,
                risk_contribution=risk_contribution,
                timestamp=datetime.now()
            )
            
            # Store hierarchy performance
            self.hierarchy_performance[hierarchy_perf.hierarchy_id] = hierarchy_perf
            
            return {
                "success": True,
                "hierarchy_performance": asdict(hierarchy_perf),
                "account_performances": {aid: perf for aid, perf in account_performances.items()},
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing hierarchy performance: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "root_account_id": root_account_id
            }
    
    def compare_account_performance(self, 
                                  account_ids: List[str],
                                  period: PerformancePeriod,
                                  metrics: Optional[List[PerformanceMetric]] = None) -> Dict[str, Any]:
        """
        Compare performance across multiple accounts.
        
        Args:
            account_ids: List of account IDs to compare
            period: Performance period
            metrics: Optional list of metrics to compare
            
        Returns:
            Performance comparison
        """
        try:
            if metrics is None:
                metrics = [
                    PerformanceMetric.TOTAL_RETURN,
                    PerformanceMetric.ANNUALIZED_RETURN,
                    PerformanceMetric.SHARPE_RATIO,
                    PerformanceMetric.MAX_DRAWDOWN,
                    PerformanceMetric.VOLATILITY
                ]
            
            # Generate snapshots for all accounts
            account_snapshots = {}
            for account_id in account_ids:
                # Get account type (simplified)
                account_type = AccountType.GEN_ACC  # Would get from account data
                
                snapshot_result = self.generate_performance_snapshot(account_id, account_type, period)
                if snapshot_result["success"]:
                    account_snapshots[account_id] = snapshot_result["snapshot"]
            
            if len(account_snapshots) < 2:
                return {
                    "success": False,
                    "error": "Insufficient accounts with performance data for comparison"
                }
            
            # Extract metrics for comparison
            comparison_metrics = {}
            for metric in metrics:
                comparison_metrics[metric.value] = {}
                
                for account_id, snapshot in account_snapshots.items():
                    metric_value = self._extract_metric_value(snapshot, metric)
                    comparison_metrics[metric.value][account_id] = metric_value
            
            # Calculate rankings
            rankings = {}
            for metric_name, metric_data in comparison_metrics.items():
                # Higher is better for most metrics (except max_drawdown and volatility)
                reverse = metric_name not in ["max_drawdown", "volatility"]
                sorted_accounts = sorted(metric_data.keys(), key=lambda k: metric_data[k], reverse=reverse)
                rankings[metric_name] = {account_id: idx + 1 for idx, account_id in enumerate(sorted_accounts)}
            
            # Calculate statistical significance (simplified)
            statistical_significance = {}
            for metric_name in comparison_metrics.keys():
                statistical_significance[metric_name] = True  # Simplified - would do proper statistical tests
            
            # Generate insights and recommendations
            insights = self._generate_performance_insights(comparison_metrics, rankings)
            recommendations = self._generate_performance_recommendations(comparison_metrics, rankings)
            
            # Create performance comparison
            comparison = PerformanceComparison(
                comparison_id=f"comp_{uuid.uuid4().hex[:8]}",
                comparison_type="account_comparison",
                accounts=account_ids,
                period=period,
                metrics=comparison_metrics,
                rankings=rankings,
                statistical_significance=statistical_significance,
                insights=insights,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
            # Store comparison
            self.performance_comparisons[comparison.comparison_id] = comparison
            
            return {
                "success": True,
                "comparison": asdict(comparison),
                "comparison_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing account performance: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "account_ids": account_ids
            }
    
    def _calculate_recent_performance(self, account_id: str) -> Dict[str, Any]:
        """Calculate recent performance metrics."""
        try:
            if account_id not in self.daily_values or len(self.daily_values[account_id]) < 2:
                return {"insufficient_data": True}
            
            values = self.daily_values[account_id]
            
            # Last 30 days performance
            if len(values) >= 30:
                current_value = values[-1][1]
                month_ago_value = values[-30][1]
                monthly_return = (current_value - month_ago_value) / month_ago_value
            else:
                monthly_return = Decimal("0")
            
            # Last 7 days performance
            if len(values) >= 7:
                current_value = values[-1][1]
                week_ago_value = values[-7][1]
                weekly_return = (current_value - week_ago_value) / week_ago_value
            else:
                weekly_return = Decimal("0")
            
            # Daily return
            if len(values) >= 2:
                current_value = values[-1][1]
                yesterday_value = values[-2][1]
                daily_return = (current_value - yesterday_value) / yesterday_value
            else:
                daily_return = Decimal("0")
            
            return {
                "daily_return": float(daily_return),
                "weekly_return": float(weekly_return),
                "monthly_return": float(monthly_return),
                "current_value": float(values[-1][1]),
                "data_points": len(values)
            }
            
        except Exception as e:
            logger.error(f"Error calculating recent performance: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_period_start_date(self, period: PerformancePeriod, end_date: date) -> date:
        """Calculate start date for performance period."""
        if period == PerformancePeriod.DAILY:
            return end_date - timedelta(days=1)
        elif period == PerformancePeriod.WEEKLY:
            return end_date - timedelta(days=7)
        elif period == PerformancePeriod.MONTHLY:
            return end_date - timedelta(days=30)
        elif period == PerformancePeriod.QUARTERLY:
            return end_date - timedelta(days=90)
        elif period == PerformancePeriod.YEARLY:
            return end_date - timedelta(days=365)
        else:  # INCEPTION
            return date(2020, 1, 1)  # Default inception date
    
    def _get_period_values(self, account_id: str, start_date: date, end_date: date) -> List[Tuple[date, Decimal]]:
        """Get account values for specific period."""
        if account_id not in self.daily_values:
            return []
        
        return [
            (d, v) for d, v in self.daily_values[account_id]
            if start_date <= d <= end_date
        ]
    
    def _calculate_daily_returns(self, values: List[Tuple[date, Decimal]]) -> List[Decimal]:
        """Calculate daily returns from values."""
        if len(values) < 2:
            return []
        
        returns = []
        for i in range(1, len(values)):
            prev_value = values[i-1][1]
            curr_value = values[i][1]
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)
        
        return returns
    
    def _annualize_return(self, total_return: Decimal, period_days: int) -> Decimal:
        """Annualize return based on period."""
        if period_days <= 0:
            return Decimal("0")
        
        return total_return * Decimal("365") / Decimal(str(period_days))
    
    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate annualized volatility."""
        if len(returns) < 2:
            return Decimal("0")
        
        # Convert to float for statistics calculation
        float_returns = [float(r) for r in returns]
        daily_vol = Decimal(str(statistics.stdev(float_returns)))
        
        # Annualize volatility
        return daily_vol * Decimal("365").sqrt()
    
    def _calculate_max_drawdown(self, values: List[Tuple[date, Decimal]]) -> Decimal:
        """Calculate maximum drawdown."""
        if len(values) < 2:
            return Decimal("0")
        
        peak = values[0][1]
        max_dd = Decimal("0")
        
        for _, value in values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, annualized_return: Decimal, volatility: Decimal) -> Optional[Decimal]:
        """Calculate Sharpe ratio."""
        if volatility == 0:
            return None
        
        excess_return = annualized_return - self.risk_free_rate
        return excess_return / volatility
    
    def _calculate_trade_metrics(self, account_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate trade-based metrics (simplified)."""
        # Simplified implementation - would integrate with actual trade data
        return {
            "trade_count": 50,
            "winning_trades": 30,
            "losing_trades": 20,
            "win_rate": Decimal("0.60"),
            "profit_factor": Decimal("1.5"),
            "largest_win": Decimal("500"),
            "largest_loss": Decimal("300"),
            "average_win": Decimal("200"),
            "average_loss": Decimal("150")
        }
    
    def _calculate_benchmark_comparison(self, 
                                      account_id: str,
                                      start_date: date,
                                      end_date: date,
                                      account_return: Decimal) -> Dict[str, Any]:
        """Calculate benchmark comparison metrics."""
        # Simplified implementation - would use actual benchmark data
        benchmark_return = self.benchmark_return * Decimal(str((end_date - start_date).days)) / Decimal("365")
        
        alpha = account_return - benchmark_return
        beta = Decimal("1.0")  # Simplified
        tracking_error = Decimal("0.05")  # Simplified
        
        information_ratio = alpha / tracking_error if tracking_error > 0 else None
        
        return {
            "benchmark_return": benchmark_return,
            "alpha": alpha,
            "beta": beta,
            "information_ratio": information_ratio,
            "tracking_error": tracking_error
        }
    
    def _calculate_correlation_matrix(self, account_ids: List[str]) -> Dict[str, Dict[str, Decimal]]:
        """Calculate correlation matrix between accounts."""
        # Simplified implementation
        correlation_matrix = {}
        
        for account1 in account_ids:
            correlation_matrix[account1] = {}
            for account2 in account_ids:
                if account1 == account2:
                    correlation_matrix[account1][account2] = Decimal("1.0")
                else:
                    # Simplified correlation calculation
                    correlation_matrix[account1][account2] = Decimal("0.7")
        
        return correlation_matrix
    
    def _calculate_attribution_analysis(self, 
                                      account_performances: Dict[str, Any],
                                      total_value: Decimal) -> Dict[str, Decimal]:
        """Calculate performance attribution analysis."""
        attribution = {}
        
        for account_id, perf in account_performances.items():
            weight = Decimal(str(perf["end_value"])) / total_value
            contribution = weight * Decimal(str(perf["annualized_return"]))
            attribution[account_id] = contribution
        
        return attribution
    
    def _calculate_risk_contribution(self, 
                                   account_performances: Dict[str, Any],
                                   total_value: Decimal) -> Dict[str, Decimal]:
        """Calculate risk contribution analysis."""
        risk_contribution = {}
        
        for account_id, perf in account_performances.items():
            weight = Decimal(str(perf["end_value"])) / total_value
            volatility = Decimal(str(perf["volatility"]))
            risk_contrib = weight * volatility
            risk_contribution[account_id] = risk_contrib
        
        return risk_contribution
    
    def _extract_metric_value(self, snapshot: Dict[str, Any], metric: PerformanceMetric) -> float:
        """Extract metric value from performance snapshot."""
        metric_map = {
            PerformanceMetric.TOTAL_RETURN: "total_return",
            PerformanceMetric.ANNUALIZED_RETURN: "annualized_return",
            PerformanceMetric.SHARPE_RATIO: "sharpe_ratio",
            PerformanceMetric.MAX_DRAWDOWN: "max_drawdown",
            PerformanceMetric.VOLATILITY: "volatility",
            PerformanceMetric.WIN_RATE: "win_rate",
            PerformanceMetric.PROFIT_FACTOR: "profit_factor"
        }
        
        field_name = metric_map.get(metric, "total_return")
        value = snapshot.get(field_name, 0)
        
        return float(value) if value is not None else 0.0
    
    def _generate_performance_insights(self, 
                                     metrics: Dict[str, Dict[str, float]],
                                     rankings: Dict[str, Dict[str, int]]) -> List[str]:
        """Generate performance insights."""
        insights = []
        
        # Find consistent top performers
        account_scores = {}
        for metric_name, metric_rankings in rankings.items():
            for account_id, rank in metric_rankings.items():
                if account_id not in account_scores:
                    account_scores[account_id] = []
                account_scores[account_id].append(rank)
        
        # Calculate average rankings
        avg_rankings = {
            account_id: sum(ranks) / len(ranks)
            for account_id, ranks in account_scores.items()
        }
        
        best_overall = min(avg_rankings.keys(), key=lambda k: avg_rankings[k])
        worst_overall = max(avg_rankings.keys(), key=lambda k: avg_rankings[k])
        
        insights.append(f"Account {best_overall} shows the most consistent performance across metrics")
        insights.append(f"Account {worst_overall} may need attention for performance improvement")
        
        # Risk-return analysis
        if "annualized_return" in metrics and "volatility" in metrics:
            for account_id in metrics["annualized_return"].keys():
                ret = metrics["annualized_return"][account_id]
                vol = metrics["volatility"][account_id]
                
                if ret > 0.15 and vol < 0.20:
                    insights.append(f"Account {account_id} shows excellent risk-adjusted performance")
                elif ret < 0.05 and vol > 0.25:
                    insights.append(f"Account {account_id} shows poor risk-adjusted performance")
        
        return insights
    
    def _generate_performance_recommendations(self, 
                                            metrics: Dict[str, Dict[str, float]],
                                            rankings: Dict[str, Dict[str, int]]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Identify underperformers for potential consolidation
        if "annualized_return" in metrics:
            poor_performers = [
                account_id for account_id, ret in metrics["annualized_return"].items()
                if ret < 0.05  # Less than 5% annual return
            ]
            
            if poor_performers:
                recommendations.append(f"Consider consolidating underperforming accounts: {', '.join(poor_performers)}")
        
        # Identify high performers for potential forking
        if "annualized_return" in metrics:
            high_performers = [
                account_id for account_id, ret in metrics["annualized_return"].items()
                if ret > 0.20  # Greater than 20% annual return
            ]
            
            if high_performers:
                recommendations.append(f"Consider forking high-performing accounts: {', '.join(high_performers)}")
        
        # Risk management recommendations
        if "max_drawdown" in metrics:
            high_risk_accounts = [
                account_id for account_id, dd in metrics["max_drawdown"].items()
                if dd > 0.15  # Greater than 15% drawdown
            ]
            
            if high_risk_accounts:
                recommendations.append(f"Review risk management for accounts with high drawdown: {', '.join(high_risk_accounts)}")
        
        return recommendations
    
    def get_performance_dashboard(self, account_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive performance dashboard."""
        try:
            if account_ids is None:
                account_ids = list(self.daily_values.keys())
            
            dashboard_data = {
                "summary": {
                    "total_accounts_tracked": len(account_ids),
                    "total_snapshots": len(self.performance_snapshots),
                    "total_comparisons": len(self.performance_comparisons),
                    "last_update": datetime.now().isoformat()
                },
                "recent_performance": {},
                "top_performers": [],
                "performance_alerts": []
            }
            
            # Get recent performance for each account
            for account_id in account_ids[:10]:  # Limit to top 10 for dashboard
                recent_perf = self._calculate_recent_performance(account_id)
                dashboard_data["recent_performance"][account_id] = recent_perf
            
            # Identify top performers
            monthly_returns = {}
            for account_id in account_ids:
                recent_perf = self._calculate_recent_performance(account_id)
                if "monthly_return" in recent_perf:
                    monthly_returns[account_id] = recent_perf["monthly_return"]
            
            if monthly_returns:
                top_performers = sorted(monthly_returns.keys(), key=lambda k: monthly_returns[k], reverse=True)
                dashboard_data["top_performers"] = top_performers[:5]
            
            # Generate performance alerts
            alerts = []
            for account_id, recent_perf in dashboard_data["recent_performance"].items():
                if "monthly_return" in recent_perf and recent_perf["monthly_return"] < -0.10:
                    alerts.append(f"Account {account_id} down {recent_perf['monthly_return']*100:.1f}% this month")
                
                if "weekly_return" in recent_perf and recent_perf["weekly_return"] < -0.05:
                    alerts.append(f"Account {account_id} down {recent_perf['weekly_return']*100:.1f}% this week")
            
            dashboard_data["performance_alerts"] = alerts
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating performance dashboard: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "dashboard_timestamp": datetime.now().isoformat()
            }

