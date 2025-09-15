"""
Protocol Levels and States

This module defines the protocol levels and states for the escalation system
as specified in Constitution v1.3 §6.Protocol-Engine.
"""

from enum import Enum, IntEnum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProtocolLevel(IntEnum):
    """
    Protocol escalation levels per Constitution v1.3 - GPT-5 Corrected.
    
    L0 (normal), L1 (prep), L2 (roll + hedge), L3 (stop-loss + SAFE)
    """
    LEVEL_0 = 0         # L0: Normal operations (5-minute monitoring)
    LEVEL_1 = 1         # L1: Prep mode (1-minute monitoring, roll preparation)
    LEVEL_2 = 2         # L2: Roll + Hedge (30-second monitoring, hedge deployment)
    LEVEL_3 = 3         # L3: Stop-loss + SAFE (real-time monitoring, emergency exit)


class ProtocolState(Enum):
    """Protocol state machine states."""
    ACTIVE = "active"               # Normal active trading
    MONITORING = "monitoring"       # Enhanced monitoring active
    RECOVERY = "recovery"          # Recovery procedures active
    PRESERVATION = "preservation"   # Preservation mode active
    SAFE = "safe"                  # SAFE mode (trading halted)
    ERROR = "error"                # Error state


@dataclass
class ProtocolLevelConfig:
    """Configuration for a protocol level."""
    level: ProtocolLevel
    name: str
    description: str
    monitoring_frequency: int  # seconds
    atr_breach_threshold: float
    max_position_loss_pct: float
    stop_loss_multiplier: float
    roll_trigger_multiplier: float
    alert_priority: str
    auto_actions: Dict[str, bool]
    escalation_delay: int  # seconds before escalation
    de_escalation_delay: int  # seconds before de-escalation


class ProtocolLevelManager:
    """Manager for protocol level configurations and transitions."""
    
    def __init__(self):
        """Initialize protocol level manager."""
        self.levels = self._initialize_levels()
        self.current_level = ProtocolLevel.NORMAL
        self.last_escalation_time = None
        self.last_de_escalation_time = None
        
    def _initialize_levels(self) -> Dict[ProtocolLevel, ProtocolLevelConfig]:
        """Initialize protocol level configurations per Constitution v1.3."""
        return {
            ProtocolLevel.NORMAL: ProtocolLevelConfig(
                level=ProtocolLevel.NORMAL,
                name="Normal Operations",
                description="Standard trading operations with routine monitoring",
                monitoring_frequency=300,  # 5 minutes
                atr_breach_threshold=0.0,  # No breach threshold
                max_position_loss_pct=5.0,  # 5% max position loss
                stop_loss_multiplier=3.0,  # 3× ATR stop loss
                roll_trigger_multiplier=1.0,  # Roll at 1× ATR
                alert_priority="info",
                auto_actions={
                    "position_monitoring": True,
                    "auto_roll": True,
                    "stop_loss": True,
                    "hedge_deployment": False
                },
                escalation_delay=60,  # 1 minute
                de_escalation_delay=300  # 5 minutes
            ),
            
            ProtocolLevel.ENHANCED: ProtocolLevelConfig(
                level=ProtocolLevel.ENHANCED,
                name="Enhanced Monitoring",
                description="Increased monitoring frequency due to 1× ATR breach",
                monitoring_frequency=60,  # 1 minute
                atr_breach_threshold=1.0,  # 1× ATR breach
                max_position_loss_pct=3.0,  # 3% max position loss
                stop_loss_multiplier=2.5,  # 2.5× ATR stop loss
                roll_trigger_multiplier=0.8,  # Roll at 0.8× ATR
                alert_priority="warning",
                auto_actions={
                    "position_monitoring": True,
                    "auto_roll": True,
                    "stop_loss": True,
                    "hedge_deployment": False,
                    "position_size_reduction": True
                },
                escalation_delay=30,  # 30 seconds
                de_escalation_delay=180  # 3 minutes
            ),
            
            ProtocolLevel.RECOVERY: ProtocolLevelConfig(
                level=ProtocolLevel.RECOVERY,
                name="Recovery Mode",
                description="Recovery procedures active due to 2× ATR breach",
                monitoring_frequency=30,  # 30 seconds
                atr_breach_threshold=2.0,  # 2× ATR breach
                max_position_loss_pct=2.0,  # 2% max position loss
                stop_loss_multiplier=2.0,  # 2× ATR stop loss
                roll_trigger_multiplier=0.6,  # Roll at 0.6× ATR
                alert_priority="critical",
                auto_actions={
                    "position_monitoring": True,
                    "auto_roll": True,
                    "stop_loss": True,
                    "hedge_deployment": True,
                    "position_size_reduction": True,
                    "new_position_halt": True
                },
                escalation_delay=15,  # 15 seconds
                de_escalation_delay=120  # 2 minutes
            ),
            
            ProtocolLevel.PRESERVATION: ProtocolLevelConfig(
                level=ProtocolLevel.PRESERVATION,
                name="Preservation Mode",
                description="Capital preservation mode due to 3× ATR breach",
                monitoring_frequency=1,  # Real-time (1 second)
                atr_breach_threshold=3.0,  # 3× ATR breach
                max_position_loss_pct=1.0,  # 1% max position loss
                stop_loss_multiplier=1.5,  # 1.5× ATR stop loss
                roll_trigger_multiplier=0.4,  # Roll at 0.4× ATR
                alert_priority="emergency",
                auto_actions={
                    "position_monitoring": True,
                    "auto_roll": True,
                    "stop_loss": True,
                    "hedge_deployment": True,
                    "position_size_reduction": True,
                    "new_position_halt": True,
                    "emergency_exit": True
                },
                escalation_delay=5,  # 5 seconds
                de_escalation_delay=60  # 1 minute
            )
        }
    
    def get_level_config(self, level: ProtocolLevel) -> ProtocolLevelConfig:
        """Get configuration for a protocol level."""
        return self.levels.get(level)
    
    def get_current_level_config(self) -> ProtocolLevelConfig:
        """Get current protocol level configuration."""
        return self.levels[self.current_level]
    
    def should_escalate(self, 
                       atr_breach_multiple: float, 
                       position_loss_pct: float,
                       time_in_breach: int) -> Optional[ProtocolLevel]:
        """
        Determine if escalation is needed based on breach conditions.
        
        Args:
            atr_breach_multiple: Current ATR breach multiple
            position_loss_pct: Current position loss percentage
            time_in_breach: Time in seconds since breach started
            
        Returns:
            Target protocol level if escalation needed, None otherwise
        """
        current_config = self.get_current_level_config()
        
        # Check if escalation delay has passed
        if (self.last_escalation_time and 
            (datetime.now() - self.last_escalation_time).total_seconds() < current_config.escalation_delay):
            return None
        
        # Determine target level based on breach severity
        target_level = self.current_level
        
        if atr_breach_multiple >= 3.0 or position_loss_pct >= 5.0:
            target_level = ProtocolLevel.PRESERVATION
        elif atr_breach_multiple >= 2.0 or position_loss_pct >= 3.0:
            target_level = ProtocolLevel.RECOVERY
        elif atr_breach_multiple >= 1.0 or position_loss_pct >= 2.0:
            target_level = ProtocolLevel.ENHANCED
        
        # Only escalate if target level is higher than current
        if target_level > self.current_level:
            # Additional check: ensure breach has persisted long enough
            min_breach_time = current_config.escalation_delay
            if time_in_breach >= min_breach_time:
                return target_level
        
        return None
    
    def should_de_escalate(self, 
                          atr_breach_multiple: float, 
                          position_loss_pct: float,
                          time_since_breach_resolved: int) -> Optional[ProtocolLevel]:
        """
        Determine if de-escalation is appropriate.
        
        Args:
            atr_breach_multiple: Current ATR breach multiple
            position_loss_pct: Current position loss percentage
            time_since_breach_resolved: Time since breach was resolved
            
        Returns:
            Target protocol level if de-escalation appropriate, None otherwise
        """
        if self.current_level == ProtocolLevel.NORMAL:
            return None
        
        current_config = self.get_current_level_config()
        
        # Check if de-escalation delay has passed
        if (self.last_de_escalation_time and 
            (datetime.now() - self.last_de_escalation_time).total_seconds() < current_config.de_escalation_delay):
            return None
        
        # Ensure conditions have improved sufficiently
        if time_since_breach_resolved < current_config.de_escalation_delay:
            return None
        
        # Determine appropriate de-escalation level
        if atr_breach_multiple < 1.0 and position_loss_pct < 1.0:
            # Conditions are good, can de-escalate to normal
            return ProtocolLevel.NORMAL
        elif atr_breach_multiple < 2.0 and position_loss_pct < 2.0:
            # Moderate conditions, de-escalate one level
            target_level = ProtocolLevel(max(0, self.current_level - 1))
            return target_level if target_level < self.current_level else None
        
        return None
    
    def escalate_to_level(self, target_level: ProtocolLevel) -> bool:
        """
        Escalate to target protocol level.
        
        Args:
            target_level: Target protocol level
            
        Returns:
            True if escalation successful
        """
        if target_level <= self.current_level:
            logger.warning(f"Cannot escalate from {self.current_level} to {target_level}")
            return False
        
        previous_level = self.current_level
        self.current_level = target_level
        self.last_escalation_time = datetime.now()
        
        logger.warning(f"Protocol escalated from {previous_level.name} to {target_level.name}")
        return True
    
    def de_escalate_to_level(self, target_level: ProtocolLevel) -> bool:
        """
        De-escalate to target protocol level.
        
        Args:
            target_level: Target protocol level
            
        Returns:
            True if de-escalation successful
        """
        if target_level >= self.current_level:
            logger.warning(f"Cannot de-escalate from {self.current_level} to {target_level}")
            return False
        
        previous_level = self.current_level
        self.current_level = target_level
        self.last_de_escalation_time = datetime.now()
        
        logger.info(f"Protocol de-escalated from {previous_level.name} to {target_level.name}")
        return True
    
    def get_escalation_history(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get escalation history for specified time period.
        
        Args:
            hours: Number of hours of history to retrieve
            
        Returns:
            Escalation history summary
        """
        # This would typically query a database or log files
        # For now, return current state information
        return {
            "current_level": self.current_level.name,
            "current_level_value": self.current_level.value,
            "last_escalation_time": self.last_escalation_time.isoformat() if self.last_escalation_time else None,
            "last_de_escalation_time": self.last_de_escalation_time.isoformat() if self.last_de_escalation_time else None,
            "time_in_current_level": (datetime.now() - (self.last_escalation_time or self.last_de_escalation_time or datetime.now())).total_seconds() if (self.last_escalation_time or self.last_de_escalation_time) else 0
        }
    
    def get_level_summary(self) -> Dict[str, Any]:
        """Get summary of all protocol levels."""
        return {
            level.name: {
                "level": level.value,
                "name": config.name,
                "description": config.description,
                "monitoring_frequency": config.monitoring_frequency,
                "atr_breach_threshold": config.atr_breach_threshold,
                "alert_priority": config.alert_priority,
                "auto_actions": config.auto_actions
            }
            for level, config in self.levels.items()
        }

