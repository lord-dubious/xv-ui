"""
Interaction Scheduler for XAgent

Automatically schedules and executes user interactions:
- Follow/unfollow cycles
- Engagement scheduling
- Rate limiting and delays
- Safety checks and monitoring
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class InteractionScheduler:
	"""Automatic interaction scheduling and execution system."""
	
	def __init__(self, profile_name: str):
		"""Initialize interaction scheduler."""
		self.profile_name = profile_name
		self.profile_dir = Path(f"profiles/{profile_name}")
		self.scheduler_config_file = self.profile_dir / "scheduler_config.json"
		self.schedule_file = self.profile_dir / "interaction_schedule.json"
		self.execution_log_file = self.profile_dir / "execution_log.json"
		
		# Scheduler configuration
		self.scheduler_config = {
			"enabled": True,
			"rate_limits": {
				"follows_per_hour": 10,
				"unfollows_per_hour": 15,
				"likes_per_hour": 30,
				"replies_per_hour": 5,
				"retweets_per_hour": 8
			},
			"timing": {
				"min_delay_seconds": 180,  # 3 minutes
				"max_delay_seconds": 900,  # 15 minutes
				"active_hours": {"start": "08:00", "end": "22:00"},
				"active_days": [1, 2, 3, 4, 5, 6, 7],  # Monday to Sunday
				"burst_protection": True,
				"randomize_timing": True
			},
			"safety": {
				"max_daily_follows": 50,
				"max_daily_unfollows": 75,
				"follow_unfollow_ratio": 0.8,  # Unfollow 80% of follows
				"cooldown_after_limit": 3600,  # 1 hour cooldown
				"respect_rate_limits": True
			},
			"interaction_patterns": {
				"follow_then_engage": True,
				"engagement_delay_hours": 2,
				"unfollow_delay_days": 7,
				"like_probability_after_follow": 0.6,
				"reply_probability_after_follow": 0.1
			}
		}
		
		# Load existing data
		self.scheduled_interactions = []
		self.execution_log = []
		self._load_data()
		
		# Runtime state
		self.is_running = False
		self.last_execution_times = {}
		self.daily_counts = {}
		
		logger.info(f"Interaction scheduler initialized for profile: {profile_name}")
	
	def _load_data(self):
		"""Load scheduler configuration and data."""
		try:
			# Load scheduler config
			if self.scheduler_config_file.exists():
				with open(self.scheduler_config_file, 'r') as f:
					loaded_config = json.load(f)
					self.scheduler_config.update(loaded_config)
			
			# Load scheduled interactions
			if self.schedule_file.exists():
				with open(self.schedule_file, 'r') as f:
					self.scheduled_interactions = json.load(f)
			
			# Load execution log
			if self.execution_log_file.exists():
				with open(self.execution_log_file, 'r') as f:
					self.execution_log = json.load(f)
			
			logger.info(f"Loaded {len(self.scheduled_interactions)} scheduled interactions and {len(self.execution_log)} log entries")
		
		except Exception as e:
			logger.error(f"Error loading scheduler data: {e}")
	
	def _save_data(self):
		"""Save scheduler data to files."""
		try:
			self.profile_dir.mkdir(parents=True, exist_ok=True)
			
			# Save scheduler config
			with open(self.scheduler_config_file, 'w') as f:
				json.dump(self.scheduler_config, f, indent=2)
			
			# Save scheduled interactions
			with open(self.schedule_file, 'w') as f:
				json.dump(self.scheduled_interactions, f, indent=2)
			
			# Save execution log (keep last 1000 entries)
			with open(self.execution_log_file, 'w') as f:
				json.dump(self.execution_log[-1000:], f, indent=2)
		
		except Exception as e:
			logger.error(f"Error saving scheduler data: {e}")
	
	def update_scheduler_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
		"""Update scheduler configuration."""
		try:
			self.scheduler_config.update(config)
			self._save_data()
			
			return {
				"status": "success",
				"message": "Scheduler configuration updated",
				"config": self.scheduler_config
			}
		
		except Exception as e:
			logger.error(f"Error updating scheduler config: {e}")
			return {"status": "error", "message": str(e)}
	
	def schedule_interaction(self, interaction_type: str, username: str, 
						   delay_minutes: Optional[int] = None, 
						   priority: float = 0.5) -> Dict[str, Any]:
		"""Schedule a single interaction."""
		try:
			# Calculate execution time
			if delay_minutes is None:
				min_delay = self.scheduler_config["timing"]["min_delay_seconds"]
				max_delay = self.scheduler_config["timing"]["max_delay_seconds"]
				delay_seconds = random.randint(min_delay, max_delay)
			else:
				delay_seconds = delay_minutes * 60
			
			execution_time = datetime.now() + timedelta(seconds=delay_seconds)
			
			# Create interaction
			interaction = {
				"id": f"{interaction_type}_{username}_{int(datetime.now().timestamp())}",
				"type": interaction_type,
				"username": username,
				"scheduled_time": execution_time.isoformat(),
				"priority": priority,
				"status": "scheduled",
				"created_at": datetime.now().isoformat(),
				"attempts": 0,
				"max_attempts": 3
			}
			
			# Add to schedule
			self.scheduled_interactions.append(interaction)
			self._sort_schedule()
			self._save_data()
			
			logger.info(f"Scheduled {interaction_type} for {username} at {execution_time}")
			
			return {
				"status": "success",
				"interaction_id": interaction["id"],
				"execution_time": execution_time.isoformat()
			}
		
		except Exception as e:
			logger.error(f"Error scheduling interaction: {e}")
			return {"status": "error", "message": str(e)}
	
	def schedule_bulk_interactions(self, users: List[Dict[str, Any]], interaction_type: str) -> Dict[str, Any]:
		"""Schedule bulk interactions with proper spacing."""
		try:
			scheduled_count = 0
			failed_count = 0
			
			for i, user in enumerate(users):
				username = user.get("username")
				if not username:
					failed_count += 1
					continue
				
				# Calculate staggered delay
				base_delay = i * random.randint(3, 8)  # 3-8 minutes between each
				
				result = self.schedule_interaction(interaction_type, username, delay_minutes=base_delay)
				
				if result["status"] == "success":
					scheduled_count += 1
				else:
					failed_count += 1
			
			logger.info(f"Bulk scheduled {scheduled_count} {interaction_type} interactions, {failed_count} failed")
			
			return {
				"status": "success",
				"scheduled_count": scheduled_count,
				"failed_count": failed_count,
				"total_scheduled": len(self.scheduled_interactions)
			}
		
		except Exception as e:
			logger.error(f"Error scheduling bulk interactions: {e}")
			return {"status": "error", "message": str(e)}
	
	def _sort_schedule(self):
		"""Sort scheduled interactions by execution time and priority."""
		self.scheduled_interactions.sort(key=lambda x: (x["scheduled_time"], -x["priority"]))
	
	def get_ready_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
		"""Get interactions ready for execution."""
		if not self.scheduler_config["enabled"]:
			return []
		
		ready_interactions = []
		now = datetime.now()
		
		for interaction in self.scheduled_interactions[:limit * 2]:  # Check more than limit
			if len(ready_interactions) >= limit:
				break
			
			# Check if it's time to execute
			scheduled_time = datetime.fromisoformat(interaction["scheduled_time"])
			if scheduled_time > now:
				continue
			
			ready_interactions.append(interaction)
		
		return ready_interactions
	
	def mark_interaction_executed(self, interaction_id: str, status: str, result: Dict[str, Any] = None) -> Dict[str, Any]:
		"""Mark an interaction as executed."""
		try:
			# Find and update interaction
			interaction = None
			for i, scheduled in enumerate(self.scheduled_interactions):
				if scheduled["id"] == interaction_id:
					interaction = scheduled
					break
			
			if not interaction:
				return {"status": "error", "message": "Interaction not found"}
			
			# Update interaction status
			interaction["status"] = status
			interaction["executed_at"] = datetime.now().isoformat()
			interaction["attempts"] += 1
			
			# Add to execution log
			log_entry = {
				"id": interaction_id,
				"type": interaction["type"],
				"username": interaction["username"],
				"status": status,
				"timestamp": datetime.now().isoformat(),
				"result": result or {}
			}
			self.execution_log.append(log_entry)
			
			# Remove from schedule if completed or max attempts reached
			if status in ["completed", "failed"] or interaction["attempts"] >= interaction["max_attempts"]:
				self.scheduled_interactions = [s for s in self.scheduled_interactions if s["id"] != interaction_id]
			
			self._save_data()
			
			return {"status": "success", "message": f"Interaction {interaction_id} marked as {status}"}
		
		except Exception as e:
			logger.error(f"Error marking interaction executed: {e}")
			return {"status": "error", "message": str(e)}
	
	def get_scheduler_stats(self) -> Dict[str, Any]:
		"""Get scheduler statistics."""
		try:
			now = datetime.now()
			today = now.date()
			hour_ago = now - timedelta(hours=1)
			
			# Count scheduled interactions by type
			scheduled_counts = {}
			for interaction in self.scheduled_interactions:
				itype = interaction["type"]
				scheduled_counts[itype] = scheduled_counts.get(itype, 0) + 1
			
			# Count executions in last hour
			recent_executions = {}
			for log_entry in self.execution_log:
				if datetime.fromisoformat(log_entry.get("timestamp", "")) > hour_ago:
					itype = log_entry["type"]
					recent_executions[itype] = recent_executions.get(itype, 0) + 1
			
			# Count executions today
			today_executions = {}
			for log_entry in self.execution_log:
				if datetime.fromisoformat(log_entry.get("timestamp", "")).date() == today:
					itype = log_entry["type"]
					today_executions[itype] = today_executions.get(itype, 0) + 1
			
			return {
				"scheduler_enabled": self.scheduler_config["enabled"],
				"total_scheduled": len(self.scheduled_interactions),
				"scheduled_by_type": scheduled_counts,
				"executions_last_hour": recent_executions,
				"executions_today": today_executions,
				"total_execution_log": len(self.execution_log),
				"config": self.scheduler_config
			}
		
		except Exception as e:
			logger.error(f"Error getting scheduler stats: {e}")
			return {"status": "error", "message": str(e)}

