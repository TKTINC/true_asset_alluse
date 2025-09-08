"""
Earnings Filter - Constitution v1.3 Compliance

This module implements earnings avoidance logic to skip CSPs on symbols 
with earnings that week, as specified in GPT-5 feedback.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class EarningsFilter:
    """Earnings filter to avoid CSPs during earnings weeks."""
    
    def __init__(self):
        """Initialize earnings filter."""
        self.earnings_calendar: Dict[str, List[datetime]] = {}
        self.last_update: Optional[datetime] = None
        self.update_frequency_hours = 24  # Update daily
    
    def update_earnings_calendar(self, earnings_data: Dict[str, List[str]]) -> None:
        """
        Update earnings calendar with new data.
        
        Args:
            earnings_data: Dict mapping symbols to list of earnings dates (YYYY-MM-DD format)
        """
        try:
            self.earnings_calendar = {}
            
            for symbol, date_strings in earnings_data.items():
                dates = []
                for date_str in date_strings:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        dates.append(date_obj)
                    except ValueError:
                        logger.warning(f"Invalid date format for {symbol}: {date_str}")
                        continue
                
                if dates:
                    self.earnings_calendar[symbol] = sorted(dates)
            
            self.last_update = datetime.now()
            logger.info(f"Updated earnings calendar for {len(self.earnings_calendar)} symbols")
            
        except Exception as e:
            logger.error(f"Error updating earnings calendar: {e}")
            raise
    
    def is_earnings_week(self, symbol: str, target_date: datetime) -> bool:
        """
        Check if target date falls within an earnings week for the symbol.
        
        Args:
            symbol: Stock symbol to check
            target_date: Date to check against earnings calendar
            
        Returns:
            True if target date is in an earnings week
        """
        if symbol not in self.earnings_calendar:
            # If no earnings data, assume safe (no earnings)
            return False
        
        # Get week boundaries (Monday to Friday)
        target_monday = target_date - timedelta(days=target_date.weekday())
        target_friday = target_monday + timedelta(days=4)
        
        # Check if any earnings date falls within this week
        for earnings_date in self.earnings_calendar[symbol]:
            if target_monday <= earnings_date <= target_friday:
                logger.info(f"Earnings week detected for {symbol}: {earnings_date.strftime('%Y-%m-%d')}")
                return True
        
        return False
    
    def filter_symbols_for_csp(self, symbols: List[str], target_date: datetime) -> List[str]:
        """
        Filter symbols to exclude those with earnings in the target week.
        
        Args:
            symbols: List of symbols to filter
            target_date: Target trading date
            
        Returns:
            Filtered list of symbols (earnings weeks excluded)
        """
        if not self._is_calendar_current():
            logger.warning("Earnings calendar may be stale - proceeding with available data")
        
        filtered_symbols = []
        excluded_symbols = []
        
        for symbol in symbols:
            if self.is_earnings_week(symbol, target_date):
                excluded_symbols.append(symbol)
                logger.info(f"Excluding {symbol} from CSPs due to earnings week")
            else:
                filtered_symbols.append(symbol)
        
        if excluded_symbols:
            logger.info(f"Earnings filter excluded {len(excluded_symbols)} symbols: {excluded_symbols}")
        
        return filtered_symbols
    
    def get_next_earnings_date(self, symbol: str) -> Optional[datetime]:
        """
        Get the next earnings date for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Next earnings date or None if not found
        """
        if symbol not in self.earnings_calendar:
            return None
        
        now = datetime.now()
        future_earnings = [date for date in self.earnings_calendar[symbol] if date > now]
        
        return min(future_earnings) if future_earnings else None
    
    def get_earnings_summary(self) -> Dict[str, any]:
        """
        Get summary of earnings calendar status.
        
        Returns:
            Summary dict with calendar statistics
        """
        total_symbols = len(self.earnings_calendar)
        total_dates = sum(len(dates) for dates in self.earnings_calendar.values())
        
        # Count upcoming earnings (next 30 days)
        now = datetime.now()
        upcoming_cutoff = now + timedelta(days=30)
        upcoming_count = 0
        
        for dates in self.earnings_calendar.values():
            upcoming_count += len([d for d in dates if now <= d <= upcoming_cutoff])
        
        return {
            "total_symbols": total_symbols,
            "total_earnings_dates": total_dates,
            "upcoming_earnings_30d": upcoming_count,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "calendar_current": self._is_calendar_current()
        }
    
    def _is_calendar_current(self) -> bool:
        """Check if earnings calendar is current (updated within frequency window)."""
        if not self.last_update:
            return False
        
        hours_since_update = (datetime.now() - self.last_update).total_seconds() / 3600
        return hours_since_update < self.update_frequency_hours
    
    def validate_earnings_compliance(self, symbol: str, strategy: str, target_date: datetime) -> Dict[str, any]:
        """
        Validate earnings compliance for a trading decision.
        
        Args:
            symbol: Stock symbol
            strategy: Trading strategy (csp, cc, etc.)
            target_date: Target trading date
            
        Returns:
            Validation result
        """
        violations = []
        
        # Only apply earnings filter to CSPs
        if strategy.lower() == "csp":
            if self.is_earnings_week(symbol, target_date):
                violations.append(f"CSP on {symbol} blocked due to earnings week")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "symbol": symbol,
            "strategy": strategy,
            "target_date": target_date.isoformat(),
            "rule": "Skip CSPs on symbols with earnings that week"
        }


# Global earnings filter instance
earnings_filter = EarningsFilter()

