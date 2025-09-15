"""
Monitoring System

This module implements the automated monitoring system that tracks positions
at different frequencies based on the current protocol level.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .protocol_levels import ProtocolLevel

logger = logging.getLogger(__name__)


class MonitoringTask:
    """Individual monitoring task for a position or system component."""
    
    def __init__(self, 
                 task_id: str,
                 task_type: str,
                 target_id: str,
                 callback: Callable,
                 frequency: int,
                 enabled: bool = True):
        """
        Initialize monitoring task.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of monitoring task
            target_id: ID of the target being monitored
            callback: Callback function to execute
            frequency: Monitoring frequency in seconds
            enabled: Whether task is enabled
        """
        self.task_id = task_id
        self.task_type = task_type
        self.target_id = target_id
        self.callback = callback
        self.frequency = frequency
        self.enabled = enabled
        self.last_execution = None
        self.next_execution = None
        self.execution_count = 0
        self.error_count = 0
        self.last_error = None
        self.created_at = datetime.now()
    
    def should_execute(self) -> bool:
        """Check if task should be executed now."""
        if not self.enabled:
            return False
        
        now = datetime.now()
        
        if self.next_execution is None:
            return True
        
        return now >= self.next_execution
    
    def execute(self) -> Dict[str, Any]:
        """Execute the monitoring task."""
        try:
            now = datetime.now()
            
            # Execute callback
            result = self.callback(self.target_id)
            
            # Update execution tracking
            self.last_execution = now
            self.next_execution = now + timedelta(seconds=self.frequency)
            self.execution_count += 1
            
            return {
                "success": True,
                "task_id": self.task_id,
                "execution_time": now.isoformat(),
                "result": result
            }
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Error executing monitoring task {self.task_id}: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "task_id": self.task_id,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
    
    def update_frequency(self, new_frequency: int):
        """Update monitoring frequency."""
        self.frequency = new_frequency
        
        # Recalculate next execution time
        if self.last_execution:
            self.next_execution = self.last_execution + timedelta(seconds=new_frequency)
        
        logger.info(f"Updated frequency for task {self.task_id} to {new_frequency} seconds")


class MonitoringSystem:
    """
    Automated monitoring system that executes tasks at different frequencies
    based on the current protocol level.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize monitoring system.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        
        # Task management
        self.tasks = {}  # task_id -> MonitoringTask
        self.task_groups = {}  # group_name -> List[task_id]
        
        # Execution management
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 5))
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.start_time = None
        self.total_executions = 0
        self.total_errors = 0
        
        logger.info("Monitoring System initialized")
    
    def add_task(self, 
                task_id: str,
                task_type: str,
                target_id: str,
                callback: Callable,
                frequency: int,
                group: Optional[str] = None,
                enabled: bool = True) -> bool:
        """
        Add monitoring task.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of monitoring task
            target_id: ID of target being monitored
            callback: Callback function
            frequency: Monitoring frequency in seconds
            group: Optional task group name
            enabled: Whether task is enabled
            
        Returns:
            True if task added successfully
        """
        try:
            if task_id in self.tasks:
                logger.warning(f"Task {task_id} already exists, updating")
            
            task = MonitoringTask(
                task_id=task_id,
                task_type=task_type,
                target_id=target_id,
                callback=callback,
                frequency=frequency,
                enabled=enabled
            )
            
            self.tasks[task_id] = task
            
            # Add to group if specified
            if group:
                if group not in self.task_groups:
                    self.task_groups[group] = []
                self.task_groups[group].append(task_id)
            
            logger.info(f"Added monitoring task: {task_id} ({task_type}) - {frequency}s frequency")
            return True
            
        except Exception as e:
            logger.error(f"Error adding monitoring task {task_id}: {str(e)}", exc_info=True)
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove monitoring task."""
        try:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return False
            
            # Remove from task groups
            for group_name, task_list in self.task_groups.items():
                if task_id in task_list:
                    task_list.remove(task_id)
            
            # Remove task
            del self.tasks[task_id]
            
            logger.info(f"Removed monitoring task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing monitoring task {task_id}: {str(e)}", exc_info=True)
            return False
    
    def update_task_frequency(self, task_id: str, new_frequency: int) -> bool:
        """Update task monitoring frequency."""
        try:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return False
            
            self.tasks[task_id].update_frequency(new_frequency)
            return True
            
        except Exception as e:
            logger.error(f"Error updating task frequency for {task_id}: {str(e)}", exc_info=True)
            return False
    
    def update_group_frequency(self, group_name: str, new_frequency: int) -> bool:
        """Update frequency for all tasks in a group."""
        try:
            if group_name not in self.task_groups:
                logger.warning(f"Task group {group_name} not found")
                return False
            
            updated_count = 0
            for task_id in self.task_groups[group_name]:
                if self.update_task_frequency(task_id, new_frequency):
                    updated_count += 1
            
            logger.info(f"Updated frequency for {updated_count} tasks in group {group_name}")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Error updating group frequency for {group_name}: {str(e)}", exc_info=True)
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable monitoring task."""
        try:
            if task_id not in self.tasks:
                return False
            
            self.tasks[task_id].enabled = True
            logger.info(f"Enabled monitoring task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling task {task_id}: {str(e)}")
            return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable monitoring task."""
        try:
            if task_id not in self.tasks:
                return False
            
            self.tasks[task_id].enabled = False
            logger.info(f"Disabled monitoring task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling task {task_id}: {str(e)}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start the monitoring system."""
        try:
            if self.running:
                logger.warning("Monitoring system is already running")
                return False
            
            self.running = True
            self.start_time = datetime.now()
            self.shutdown_event.clear()
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            logger.info("Monitoring system started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitoring system: {str(e)}", exc_info=True)
            self.running = False
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop the monitoring system."""
        try:
            if not self.running:
                logger.warning("Monitoring system is not running")
                return False
            
            self.running = False
            self.shutdown_event.set()
            
            # Wait for monitoring thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            logger.info("Monitoring system stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping monitoring system: {str(e)}", exc_info=True)
            return False
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Monitoring loop started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get tasks that should be executed
                tasks_to_execute = [
                    task for task in self.tasks.values()
                    if task.should_execute()
                ]
                
                if tasks_to_execute:
                    # Execute tasks in parallel
                    futures = []
                    for task in tasks_to_execute:
                        future = self.executor.submit(task.execute)
                        futures.append((task.task_id, future))
                    
                    # Collect results
                    for task_id, future in futures:
                        try:
                            result = future.result(timeout=30)  # 30 second timeout
                            self.total_executions += 1
                            
                            if not result.get("success"):
                                self.total_errors += 1
                                
                        except Exception as e:
                            self.total_errors += 1
                            logger.error(f"Error executing task {task_id}: {str(e)}")
                
                # Sleep for a short interval before next check
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                time.sleep(5)  # Longer sleep on error
        
        logger.info("Monitoring loop stopped")
    
    def update_protocol_level_frequencies(self, protocol_level: ProtocolLevel) -> bool:
        """
        Update monitoring frequencies based on protocol level.
        
        Args:
            protocol_level: Current protocol level
            
        Returns:
            True if frequencies updated successfully
        """
        try:
            # Define frequency mappings based on protocol level
            frequency_map = {
                ProtocolLevel.NORMAL: {
                    "position_monitoring": 300,  # 5 minutes
                    "system_health": 600,        # 10 minutes
                    "risk_assessment": 900       # 15 minutes
                },
                ProtocolLevel.ENHANCED: {
                    "position_monitoring": 60,   # 1 minute
                    "system_health": 300,        # 5 minutes
                    "risk_assessment": 300       # 5 minutes
                },
                ProtocolLevel.RECOVERY: {
                    "position_monitoring": 30,   # 30 seconds
                    "system_health": 60,         # 1 minute
                    "risk_assessment": 120       # 2 minutes
                },
                ProtocolLevel.PRESERVATION: {
                    "position_monitoring": 1,    # Real-time (1 second)
                    "system_health": 30,         # 30 seconds
                    "risk_assessment": 60        # 1 minute
                }
            }
            
            if protocol_level not in frequency_map:
                logger.error(f"Unknown protocol level: {protocol_level}")
                return False
            
            frequencies = frequency_map[protocol_level]
            updated_count = 0
            
            # Update frequencies for each task group
            for group_name, frequency in frequencies.items():
                if self.update_group_frequency(group_name, frequency):
                    updated_count += 1
            
            logger.info(f"Updated monitoring frequencies for protocol level {protocol_level.name}")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Error updating protocol level frequencies: {str(e)}", exc_info=True)
            return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring system status."""
        try:
            # Calculate uptime
            uptime_seconds = 0
            if self.start_time:
                uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            # Task statistics
            total_tasks = len(self.tasks)
            enabled_tasks = sum(1 for task in self.tasks.values() if task.enabled)
            disabled_tasks = total_tasks - enabled_tasks
            
            # Execution statistics
            avg_executions_per_task = self.total_executions / total_tasks if total_tasks > 0 else 0
            error_rate = (self.total_errors / self.total_executions * 100) if self.total_executions > 0 else 0
            
            # Task details
            task_details = {}
            for task_id, task in self.tasks.items():
                task_details[task_id] = {
                    "type": task.task_type,
                    "target_id": task.target_id,
                    "frequency": task.frequency,
                    "enabled": task.enabled,
                    "execution_count": task.execution_count,
                    "error_count": task.error_count,
                    "last_execution": task.last_execution.isoformat() if task.last_execution else None,
                    "next_execution": task.next_execution.isoformat() if task.next_execution else None,
                    "last_error": task.last_error
                }
            
            return {
                "running": self.running,
                "uptime_seconds": uptime_seconds,
                "total_tasks": total_tasks,
                "enabled_tasks": enabled_tasks,
                "disabled_tasks": disabled_tasks,
                "total_executions": self.total_executions,
                "total_errors": self.total_errors,
                "error_rate_pct": error_rate,
                "avg_executions_per_task": avg_executions_per_task,
                "task_groups": {group: len(tasks) for group, tasks in self.task_groups.items()},
                "task_details": task_details,
                "status_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status_timestamp": datetime.now().isoformat()
            }
    
    def get_task_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Get task performance statistics."""
        try:
            # This would typically query historical data
            # For now, return current task statistics
            
            performance_data = {}
            
            for task_id, task in self.tasks.items():
                success_rate = 0
                if task.execution_count > 0:
                    success_rate = ((task.execution_count - task.error_count) / task.execution_count) * 100
                
                performance_data[task_id] = {
                    "execution_count": task.execution_count,
                    "error_count": task.error_count,
                    "success_rate_pct": success_rate,
                    "avg_frequency": task.frequency,
                    "uptime_hours": (datetime.now() - task.created_at).total_seconds() / 3600
                }
            
            return {
                "performance_data": performance_data,
                "analysis_period_hours": hours,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting task performance: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if self.running:
                self.stop_monitoring()
            
            if self.executor:
                self.executor.shutdown(wait=True)
        except Exception:
            pass

