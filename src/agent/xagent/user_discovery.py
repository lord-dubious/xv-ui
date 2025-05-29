"""
User Discovery System for XAgent

Automatically discovers and selects users for interaction based on:
- Interest matching
- Activity patterns
- Engagement potential
- Follower network analysis
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class UserDiscovery:
	"""Automatic user discovery and targeting system."""
	
	def __init__(self, profile_name: str):
		"""Initialize user discovery system."""
		self.profile_name = profile_name
		self.profile_dir = Path(f"profiles/{profile_name}")
		self.discovery_config_file = self.profile_dir / "discovery_config.json"
		self.discovered_users_file = self.profile_dir / "discovered_users.json"
		self.interaction_queue_file = self.profile_dir / "interaction_queue.json"
		
		# Discovery configuration
		self.discovery_config = {
			"target_keywords": ["AI", "tech", "startup", "coding", "python"],
			"target_hashtags": ["#AI", "#tech", "#startup", "#coding", "#python"],
			"target_accounts": ["@elonmusk", "@sama", "@karpathy"],
			"min_followers": 100,
			"max_followers": 100000,
			"min_activity_score": 0.3,
			"discovery_methods": ["hashtag_search", "follower_analysis", "engagement_tracking"],
			"daily_discovery_limit": 200,
			"interaction_preferences": {
				"follow_probability": 0.7,
				"like_probability": 0.8,
				"reply_probability": 0.2,
				"retweet_probability": 0.3
			}
		}
		
		# Load existing data
		self.discovered_users = []
		self.interaction_queue = []
		self._load_data()
		
		logger.info(f"User discovery system initialized for profile: {profile_name}")
	
	def _load_data(self):
		"""Load discovery configuration and user data."""
		try:
			# Load discovery config
			if self.discovery_config_file.exists():
				with open(self.discovery_config_file, 'r') as f:
					loaded_config = json.load(f)
					self.discovery_config.update(loaded_config)
			
			# Load discovered users
			if self.discovered_users_file.exists():
				with open(self.discovered_users_file, 'r') as f:
					self.discovered_users = json.load(f)
			
			# Load interaction queue
			if self.interaction_queue_file.exists():
				with open(self.interaction_queue_file, 'r') as f:
					self.interaction_queue = json.load(f)
			
			logger.info(f"Loaded {len(self.discovered_users)} discovered users and {len(self.interaction_queue)} queued interactions")
		
		except Exception as e:
			logger.error(f"Error loading discovery data: {e}")
	
	def _save_data(self):
		"""Save discovery data to files."""
		try:
			self.profile_dir.mkdir(parents=True, exist_ok=True)
			
			# Save discovery config
			with open(self.discovery_config_file, 'w') as f:
				json.dump(self.discovery_config, f, indent=2)
			
			# Save discovered users
			with open(self.discovered_users_file, 'w') as f:
				json.dump(self.discovered_users, f, indent=2)
			
			# Save interaction queue
			with open(self.interaction_queue_file, 'w') as f:
				json.dump(self.interaction_queue, f, indent=2)
		
		except Exception as e:
			logger.error(f"Error saving discovery data: {e}")
	
	def update_discovery_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
		"""Update discovery configuration."""
		try:
			self.discovery_config.update(config)
			self._save_data()
			
			return {
				"status": "success",
				"message": "Discovery configuration updated",
				"config": self.discovery_config
			}
		
		except Exception as e:
			logger.error(f"Error updating discovery config: {e}")
			return {"status": "error", "message": str(e)}
	
	async def discover_users_by_hashtag(self, hashtag: str, limit: int = 50) -> List[Dict[str, Any]]:
		"""Discover users by hashtag search."""
		try:
			# Simulate hashtag search (in real implementation, this would use Twitter API)
			discovered = []
			
			for i in range(min(limit, 20)):  # Simulate finding users
				user = {
					"username": f"user_{hashtag.replace('#', '')}_{i}",
					"display_name": f"User {i}",
					"followers_count": random.randint(100, 50000),
					"following_count": random.randint(50, 5000),
					"tweet_count": random.randint(100, 10000),
					"bio": f"Interested in {hashtag} and technology",
					"verified": random.choice([True, False]),
					"discovery_method": "hashtag_search",
					"discovery_source": hashtag,
					"discovery_timestamp": datetime.now().isoformat(),
					"activity_score": random.uniform(0.1, 1.0),
					"relevance_score": random.uniform(0.3, 0.9),
					"interaction_potential": random.uniform(0.2, 0.8)
				}
				
				# Filter by criteria
				if (user["followers_count"] >= self.discovery_config["min_followers"] and
					user["followers_count"] <= self.discovery_config["max_followers"] and
					user["activity_score"] >= self.discovery_config["min_activity_score"]):
					discovered.append(user)
			
			logger.info(f"Discovered {len(discovered)} users from hashtag {hashtag}")
			return discovered
		
		except Exception as e:
			logger.error(f"Error discovering users by hashtag {hashtag}: {e}")
			return []
	
	async def auto_discover_users(self, limit: int = 100) -> Dict[str, Any]:
		"""Automatically discover users using all configured methods."""
		try:
			all_discovered = []
			
			# Hashtag discovery
			if "hashtag_search" in self.discovery_config["discovery_methods"]:
				for hashtag in self.discovery_config["target_hashtags"][:3]:
					users = await self.discover_users_by_hashtag(hashtag, limit // 4)
					all_discovered.extend(users)
			
			# Remove duplicates and sort by relevance
			unique_users = {}
			for user in all_discovered:
				username = user["username"]
				if username not in unique_users or user["relevance_score"] > unique_users[username]["relevance_score"]:
					unique_users[username] = user
			
			discovered_list = list(unique_users.values())
			discovered_list.sort(key=lambda x: x["relevance_score"], reverse=True)
			
			# Limit to daily discovery limit
			daily_limit = self.discovery_config["daily_discovery_limit"]
			discovered_list = discovered_list[:daily_limit]
			
			# Add to discovered users
			self.discovered_users.extend(discovered_list)
			self._save_data()
			
			logger.info(f"Auto-discovered {len(discovered_list)} users")
			
			return {
				"status": "success",
				"discovered_count": len(discovered_list),
				"total_discovered": len(self.discovered_users),
				"users": discovered_list[:10]  # Return first 10 for preview
			}
		
		except Exception as e:
			logger.error(f"Error in auto user discovery: {e}")
			return {"status": "error", "message": str(e)}
	
	def select_users_for_interaction(self, interaction_type: str, count: int = 20) -> List[Dict[str, Any]]:
		"""Select users for specific interaction types."""
		try:
			# Filter users based on interaction type and probability
			suitable_users = []
			
			for user in self.discovered_users:
				# Skip if already interacted recently
				if self._recently_interacted(user["username"], interaction_type):
					continue
				
				# Check interaction probability
				prob_key = f"{interaction_type}_probability"
				if prob_key in self.discovery_config["interaction_preferences"]:
					probability = self.discovery_config["interaction_preferences"][prob_key]
					if random.random() > probability:
						continue
				
				# Score user for this interaction type
				score = self._calculate_interaction_score(user, interaction_type)
				user["interaction_score"] = score
				suitable_users.append(user)
			
			# Sort by interaction score and select top users
			suitable_users.sort(key=lambda x: x["interaction_score"], reverse=True)
			selected = suitable_users[:count]
			
			logger.info(f"Selected {len(selected)} users for {interaction_type}")
			return selected
		
		except Exception as e:
			logger.error(f"Error selecting users for {interaction_type}: {e}")
			return []
	
	def _recently_interacted(self, username: str, interaction_type: str) -> bool:
		"""Check if we recently interacted with this user."""
		# Check interaction queue for recent interactions
		cutoff_time = datetime.now() - timedelta(hours=24)
		
		for interaction in self.interaction_queue:
			if (interaction.get("username") == username and
				interaction.get("type") == interaction_type and
				datetime.fromisoformat(interaction.get("timestamp", "")) > cutoff_time):
				return True
		
		return False
	
	def _calculate_interaction_score(self, user: Dict[str, Any], interaction_type: str) -> float:
		"""Calculate interaction score for a user and interaction type."""
		base_score = user.get("relevance_score", 0.5)
		activity_score = user.get("activity_score", 0.5)
		potential_score = user.get("interaction_potential", 0.5)
		
		# Adjust score based on interaction type
		if interaction_type == "follow":
			# Prefer users with good follower ratio and activity
			follower_ratio = min(user.get("followers_count", 0) / max(user.get("following_count", 1), 1), 5.0) / 5.0
			score = (base_score * 0.4 + activity_score * 0.3 + potential_score * 0.2 + follower_ratio * 0.1)
		
		elif interaction_type == "like":
			# Prefer highly active users
			score = (base_score * 0.3 + activity_score * 0.5 + potential_score * 0.2)
		
		elif interaction_type == "reply":
			# Prefer users with high engagement potential
			score = (base_score * 0.3 + activity_score * 0.2 + potential_score * 0.5)
		
		else:
			# Default scoring
			score = (base_score * 0.4 + activity_score * 0.3 + potential_score * 0.3)
		
		return min(score, 1.0)
	
	def queue_interactions(self, users: List[Dict[str, Any]], interaction_type: str) -> Dict[str, Any]:
		"""Queue users for automatic interactions."""
		try:
			queued_count = 0
			
			for user in users:
				interaction = {
					"id": f"{interaction_type}_{user['username']}_{int(datetime.now().timestamp())}",
					"username": user["username"],
					"type": interaction_type,
					"user_data": user,
					"timestamp": datetime.now().isoformat(),
					"status": "queued",
					"priority": user.get("interaction_score", 0.5)
				}
				
				self.interaction_queue.append(interaction)
				queued_count += 1
			
			# Sort queue by priority
			self.interaction_queue.sort(key=lambda x: x["priority"], reverse=True)
			self._save_data()
			
			logger.info(f"Queued {queued_count} {interaction_type} interactions")
			
			return {
				"status": "success",
				"queued_count": queued_count,
				"total_queue_size": len(self.interaction_queue)
			}
		
		except Exception as e:
			logger.error(f"Error queueing interactions: {e}")
			return {"status": "error", "message": str(e)}
	
	def get_discovery_stats(self) -> Dict[str, Any]:
		"""Get discovery system statistics."""
		try:
			# Calculate stats
			total_discovered = len(self.discovered_users)
			queued_interactions = len(self.interaction_queue)
			
			# Discovery method breakdown
			method_counts = {}
			for user in self.discovered_users:
				method = user.get("discovery_method", "unknown")
				method_counts[method] = method_counts.get(method, 0) + 1
			
			# Interaction type breakdown
			interaction_counts = {}
			for interaction in self.interaction_queue:
				itype = interaction.get("type", "unknown")
				interaction_counts[itype] = interaction_counts.get(itype, 0) + 1
			
			return {
				"total_discovered_users": total_discovered,
				"queued_interactions": queued_interactions,
				"discovery_methods": method_counts,
				"interaction_types": interaction_counts,
				"discovery_config": self.discovery_config
			}
		
		except Exception as e:
			logger.error(f"Error getting discovery stats: {e}")
			return {"status": "error", "message": str(e)}

