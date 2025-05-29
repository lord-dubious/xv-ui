"""
Rate Limiter for XAgent Twitter Operations.

This module provides comprehensive rate limiting functionality to ensure
Twitter operations respect API limits and avoid restrictions.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Advanced rate limiter for Twitter operations."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Action counters per hour
        self.action_counts = defaultdict(deque)
        
        # Default rate limits (per hour)
        self.default_limits = {
            "tweets": 50,
            "follows": 400,
            "unfollows": 400,
            "likes": 1000,
            "replies": 300,
            "retweets": 300,
            "dm": 1000,
        }
        
        # Custom rate limits (can be overridden)
        self.custom_limits = {}
        
        # Minimum delays between actions (seconds)
        self.min_delays = {
            "tweets": 60,
            "follows": 30,
            "unfollows": 30,
            "likes": 10,
            "replies": 45,
            "retweets": 20,
            "dm": 30,
        }
        
        # Last action timestamps
        self.last_action_time = defaultdict(float)
        
        # Burst protection
        self.burst_limits = {
            "tweets": 5,  # Max 5 tweets in 10 minutes
            "follows": 20,  # Max 20 follows in 10 minutes
        }
        self.burst_windows = defaultdict(deque)
        
        # Adaptive delays
        self.adaptive_delays = defaultdict(float)
        self.base_delay_multiplier = 1.0
        
    def set_custom_limits(self, limits: Dict[str, int]):
        """Set custom rate limits for actions."""
        self.custom_limits.update(limits)
        logger.info(f"Updated custom rate limits: {limits}")
    
    def set_min_delays(self, delays: Dict[str, int]):
        """Set minimum delays between actions."""
        self.min_delays.update(delays)
        logger.info(f"Updated minimum delays: {delays}")
    
    def _get_effective_limit(self, action_type: str) -> int:
        """Get the effective rate limit for an action type."""
        return self.custom_limits.get(action_type, self.default_limits.get(action_type, 100))
    
    def _clean_old_entries(self, action_type: str):
        """Remove entries older than 1 hour."""
        now = time.time()
        hour_ago = now - 3600
        
        # Clean hourly counters
        while self.action_counts[action_type] and self.action_counts[action_type][0] < hour_ago:
            self.action_counts[action_type].popleft()
        
        # Clean burst windows (10 minutes)
        ten_minutes_ago = now - 600
        while self.burst_windows[action_type] and self.burst_windows[action_type][0] < ten_minutes_ago:
            self.burst_windows[action_type].popleft()
    
    def can_perform_action(self, action_type: str) -> bool:
        """Check if an action can be performed without violating rate limits."""
        self._clean_old_entries(action_type)
        
        # Check hourly limit
        hourly_limit = self._get_effective_limit(action_type)
        if len(self.action_counts[action_type]) >= hourly_limit:
            return False
        
        # Check burst limit
        burst_limit = self.burst_limits.get(action_type)
        if burst_limit and len(self.burst_windows[action_type]) >= burst_limit:
            return False
        
        # Check minimum delay
        min_delay = self.min_delays.get(action_type, 30)
        adaptive_delay = self.adaptive_delays.get(action_type, 0)
        total_delay = (min_delay + adaptive_delay) * self.base_delay_multiplier
        
        last_time = self.last_action_time.get(action_type, 0)
        if time.time() - last_time < total_delay:
            return False
        
        return True
    
    def get_wait_time(self, action_type: str) -> float:
        """Get the time to wait before performing an action."""
        self._clean_old_entries(action_type)
        
        wait_times = []
        
        # Check hourly limit
        hourly_limit = self._get_effective_limit(action_type)
        if len(self.action_counts[action_type]) >= hourly_limit:
            if self.action_counts[action_type]:
                oldest_action = self.action_counts[action_type][0]
                wait_times.append(oldest_action + 3600 - time.time())
        
        # Check burst limit
        burst_limit = self.burst_limits.get(action_type)
        if burst_limit and len(self.burst_windows[action_type]) >= burst_limit:
            if self.burst_windows[action_type]:
                oldest_burst = self.burst_windows[action_type][0]
                wait_times.append(oldest_burst + 600 - time.time())
        
        # Check minimum delay
        min_delay = self.min_delays.get(action_type, 30)
        adaptive_delay = self.adaptive_delays.get(action_type, 0)
        total_delay = (min_delay + adaptive_delay) * self.base_delay_multiplier
        
        last_time = self.last_action_time.get(action_type, 0)
        delay_wait = last_time + total_delay - time.time()
        if delay_wait > 0:
            wait_times.append(delay_wait)
        
        return max(wait_times) if wait_times else 0
    
    async def wait_if_needed(self, action_type: str):
        """Wait if necessary before performing an action."""
        wait_time = self.get_wait_time(action_type)
        if wait_time > 0:
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s before {action_type}")
            await asyncio.sleep(wait_time)
    
    def record_action(self, action_type: str, success: bool = True):
        """Record that an action was performed."""
        now = time.time()
        
        # Record in hourly counter
        self.action_counts[action_type].append(now)
        
        # Record in burst window
        if action_type in self.burst_limits:
            self.burst_windows[action_type].append(now)
        
        # Update last action time
        self.last_action_time[action_type] = now
        
        # Adjust adaptive delays based on success
        if not success:
            # Increase delay on failure
            self.adaptive_delays[action_type] = min(
                self.adaptive_delays.get(action_type, 0) + 30,
                300  # Max 5 minutes additional delay
            )
            logger.warning(f"Action {action_type} failed, increased adaptive delay to {self.adaptive_delays[action_type]}s")
        else:
            # Gradually reduce delay on success
            current_delay = self.adaptive_delays.get(action_type, 0)
            if current_delay > 0:
                self.adaptive_delays[action_type] = max(current_delay - 5, 0)
        
        self._clean_old_entries(action_type)
    
    def adjust_global_rate(self, multiplier: float):
        """Adjust global rate limiting multiplier."""
        self.base_delay_multiplier = max(0.1, min(multiplier, 10.0))
        logger.info(f"Adjusted global rate multiplier to {self.base_delay_multiplier}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        stats = {}
        
        for action_type in self.default_limits.keys():
            self._clean_old_entries(action_type)
            
            hourly_count = len(self.action_counts[action_type])
            hourly_limit = self._get_effective_limit(action_type)
            
            burst_count = len(self.burst_windows.get(action_type, []))
            burst_limit = self.burst_limits.get(action_type, 0)
            
            wait_time = self.get_wait_time(action_type)
            
            stats[action_type] = {
                "hourly_count": hourly_count,
                "hourly_limit": hourly_limit,
                "hourly_remaining": max(0, hourly_limit - hourly_count),
                "burst_count": burst_count,
                "burst_limit": burst_limit,
                "wait_time": wait_time,
                "adaptive_delay": self.adaptive_delays.get(action_type, 0),
                "can_perform": self.can_perform_action(action_type),
            }
        
        stats["global_multiplier"] = self.base_delay_multiplier
        
        return stats
    
    def reset_action_type(self, action_type: str):
        """Reset counters for a specific action type."""
        self.action_counts[action_type].clear()
        self.burst_windows[action_type].clear()
        self.adaptive_delays[action_type] = 0
        self.last_action_time[action_type] = 0
        logger.info(f"Reset rate limiting for {action_type}")
    
    def reset_all(self):
        """Reset all rate limiting counters."""
        self.action_counts.clear()
        self.burst_windows.clear()
        self.adaptive_delays.clear()
        self.last_action_time.clear()
        self.base_delay_multiplier = 1.0
        logger.info("Reset all rate limiting counters")

