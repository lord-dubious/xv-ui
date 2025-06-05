"""
Performance Monitor for XAgent Operations.

This module provides comprehensive performance monitoring and optimization
for Twitter automation operations.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import psutil
import threading

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Advanced performance monitoring for XAgent operations."""
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize the performance monitor.
        
        Args:
            history_size: Number of operations to keep in history
        """
        self.history_size = history_size
        
        # Operation timing data
        self.operation_times = defaultdict(deque)
        self.operation_counts = defaultdict(int)
        self.operation_errors = defaultdict(int)
        
        # System resource monitoring
        self.resource_history = deque(maxlen=100)
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Performance thresholds
        self.thresholds = {
            "tweet_time": 30.0,      # seconds
            "follow_time": 15.0,     # seconds
            "reply_time": 25.0,      # seconds
            "cpu_usage": 80.0,       # percentage
            "memory_usage": 85.0,    # percentage
        }
        
        # Optimization recommendations
        self.recommendations = []
        
        # Start resource monitoring
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start system resource monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self.monitor_thread.start()
            logger.info("Started performance monitoring")
    
    def stop_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("Stopped performance monitoring")
    
    def _monitor_resources(self):
        """Monitor system resources in background thread."""
        while self.monitoring_active:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Network I/O
                net_io = psutil.net_io_counters()
                
                resource_data = {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "network_bytes_sent": net_io.bytes_sent,
                    "network_bytes_recv": net_io.bytes_recv,
                }
                
                self.resource_history.append(resource_data)
                
                # Check thresholds and generate recommendations
                self._check_thresholds(resource_data)
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
            
            time.sleep(5)  # Monitor every 5 seconds
    
    def _check_thresholds(self, resource_data: Dict[str, Any]):
        """Check if any performance thresholds are exceeded."""
        recommendations = []
        
        if resource_data["cpu_percent"] > self.thresholds["cpu_usage"]:
            recommendations.append({
                "type": "high_cpu",
                "message": f"High CPU usage: {resource_data['cpu_percent']:.1f}%",
                "suggestion": "Consider reducing concurrent operations or increasing delays",
                "timestamp": time.time(),
            })
        
        if resource_data["memory_percent"] > self.thresholds["memory_usage"]:
            recommendations.append({
                "type": "high_memory",
                "message": f"High memory usage: {resource_data['memory_percent']:.1f}%",
                "suggestion": "Consider clearing caches or reducing operation history",
                "timestamp": time.time(),
            })
        
        # Add new recommendations
        for rec in recommendations:
            if not any(r["type"] == rec["type"] for r in self.recommendations[-5:]):
                self.recommendations.append(rec)
                logger.warning(f"Performance warning: {rec['message']} - {rec['suggestion']}")
    
    def start_operation(self, operation_type: str) -> str:
        """
        Start timing an operation.
        
        Args:
            operation_type: Type of operation (e.g., 'tweet', 'follow')
            
        Returns:
            Operation ID for tracking
        """
        operation_id = f"{operation_type}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        # Store start time
        if not hasattr(self, '_active_operations'):
            self._active_operations = {}
        
        self._active_operations[operation_id] = {
            "type": operation_type,
            "start_time": start_time,
        }
        
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, error: Optional[str] = None):
        """
        End timing an operation.
        
        Args:
            operation_id: Operation ID from start_operation
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        if not hasattr(self, '_active_operations') or operation_id not in self._active_operations:
            logger.warning(f"Unknown operation ID: {operation_id}")
            return
        
        operation = self._active_operations.pop(operation_id)
        end_time = time.time()
        duration = end_time - operation["start_time"]
        operation_type = operation["type"]
        
        # Record timing
        self.operation_times[operation_type].append({
            "duration": duration,
            "timestamp": end_time,
            "success": success,
            "error": error,
        })
        
        # Maintain history size
        if len(self.operation_times[operation_type]) > self.history_size:
            self.operation_times[operation_type].popleft()
        
        # Update counters
        self.operation_counts[operation_type] += 1
        if not success:
            self.operation_errors[operation_type] += 1
        
        # Check performance thresholds
        threshold_key = f"{operation_type}_time"
        if threshold_key in self.thresholds and duration > self.thresholds[threshold_key]:
            self.recommendations.append({
                "type": "slow_operation",
                "message": f"Slow {operation_type}: {duration:.1f}s (threshold: {self.thresholds[threshold_key]}s)",
                "suggestion": f"Consider optimizing {operation_type} operations or increasing timeouts",
                "timestamp": time.time(),
            })
        
        logger.debug(f"Operation {operation_type} completed in {duration:.2f}s (success: {success})")
    
    def get_operation_stats(self, operation_type: str) -> Dict[str, Any]:
        """Get statistics for a specific operation type."""
        if operation_type not in self.operation_times:
            return {"error": f"No data for operation type: {operation_type}"}
        
        times = self.operation_times[operation_type]
        if not times:
            return {"error": f"No timing data for operation type: {operation_type}"}
        
        durations = [t["duration"] for t in times]
        successes = [t for t in times if t["success"]]
        failures = [t for t in times if not t["success"]]
        
        # Calculate statistics
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Recent performance (last 10 operations)
        recent_times = list(times)[-10:]
        recent_avg = sum(t["duration"] for t in recent_times) / len(recent_times) if recent_times else 0
        
        return {
            "total_operations": len(times),
            "successful_operations": len(successes),
            "failed_operations": len(failures),
            "success_rate": len(successes) / len(times) * 100 if times else 0,
            "avg_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "recent_avg_duration": recent_avg,
            "threshold": self.thresholds.get(f"{operation_type}_time", "Not set"),
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system resource statistics."""
        if not self.resource_history:
            return {"error": "No resource data available"}
        
        latest = self.resource_history[-1]
        
        # Calculate averages over last 5 minutes
        five_min_ago = time.time() - 300
        recent_data = [r for r in self.resource_history if r["timestamp"] > five_min_ago]
        
        if recent_data:
            avg_cpu = sum(r["cpu_percent"] for r in recent_data) / len(recent_data)
            avg_memory = sum(r["memory_percent"] for r in recent_data) / len(recent_data)
        else:
            avg_cpu = latest["cpu_percent"]
            avg_memory = latest["memory_percent"]
        
        return {
            "current_cpu": latest["cpu_percent"],
            "current_memory": latest["memory_percent"],
            "current_disk": latest["disk_percent"],
            "avg_cpu_5min": avg_cpu,
            "avg_memory_5min": avg_memory,
            "memory_available_gb": latest["memory_available"] / (1024**3),
            "network_sent_mb": latest["network_bytes_sent"] / (1024**2),
            "network_recv_mb": latest["network_bytes_recv"] / (1024**2),
        }
    
    def get_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance recommendations."""
        return list(self.recommendations)[-limit:]
    
    def clear_recommendations(self):
        """Clear all performance recommendations."""
        self.recommendations.clear()
        logger.info("Cleared performance recommendations")
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Analyze performance and suggest optimizations."""
        optimizations = []
        
        # Analyze operation performance
        for op_type in self.operation_times.keys():
            stats = self.get_operation_stats(op_type)
            
            if stats.get("success_rate", 100) < 90:
                optimizations.append({
                    "type": "reliability",
                    "operation": op_type,
                    "issue": f"Low success rate: {stats['success_rate']:.1f}%",
                    "suggestion": "Review error handling and retry logic",
                })
            
            if stats.get("avg_duration", 0) > self.thresholds.get(f"{op_type}_time", float('inf')):
                optimizations.append({
                    "type": "performance",
                    "operation": op_type,
                    "issue": f"Slow average time: {stats['avg_duration']:.1f}s",
                    "suggestion": "Consider optimizing operation or increasing timeouts",
                })
        
        # Analyze system resources
        system_stats = self.get_system_stats()
        if not system_stats.get("error"):
            if system_stats["avg_cpu_5min"] > 70:
                optimizations.append({
                    "type": "system",
                    "operation": "cpu",
                    "issue": f"High CPU usage: {system_stats['avg_cpu_5min']:.1f}%",
                    "suggestion": "Reduce concurrent operations or increase delays",
                })
            
            if system_stats["avg_memory_5min"] > 80:
                optimizations.append({
                    "type": "system",
                    "operation": "memory",
                    "issue": f"High memory usage: {system_stats['avg_memory_5min']:.1f}%",
                    "suggestion": "Clear caches or reduce operation history",
                })
        
        return {
            "optimizations": optimizations,
            "total_issues": len(optimizations),
            "timestamp": datetime.now().isoformat(),
        }
    
    def export_performance_data(self) -> Dict[str, Any]:
        """Export all performance data for analysis."""
        return {
            "operation_stats": {
                op_type: self.get_operation_stats(op_type)
                for op_type in self.operation_times.keys()
            },
            "system_stats": self.get_system_stats(),
            "recommendations": self.get_recommendations(),
            "thresholds": self.thresholds,
            "export_timestamp": datetime.now().isoformat(),
        }
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.operation_times.clear()
        self.operation_counts.clear()
        self.operation_errors.clear()
        self.recommendations.clear()
        self.resource_history.clear()
        logger.info("Reset all performance statistics")
    
    def __del__(self):
        """Cleanup when monitor is destroyed."""
        self.stop_monitoring()

