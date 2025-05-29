"""
Follow System for XAgent
Minimal version for testing
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FollowSystem:
    """Manages Twitter following and unfollowing operations."""
    
    def __init__(self, data_dir: str = "./follow_data"):
        self.data_dir = Path(data_dir)
        self.follow_targets = []
        self.follow_history = []
        self.following_list = set()
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load follow system data."""
        try:
            # Load follow targets
            targets_file = self.data_dir / "targets.json"
            if targets_file.exists():
                with open(targets_file, 'r') as f:
                    self.follow_targets = json.load(f)
            
            # Load follow history
            history_file = self.data_dir / "history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.follow_history = json.load(f)
            
            logger.info(f"Loaded {len(self.follow_targets)} targets and {len(self.follow_history)} history entries")
            
        except Exception as e:
            logger.error(f"Failed to load follow data: {e}")
    
    def _save_data(self):
        """Save follow system data."""
        try:
            # Save follow targets
            targets_file = self.data_dir / "targets.json"
            with open(targets_file, 'w') as f:
                json.dump(self.follow_targets, f, indent=2)
            
            # Save follow history
            history_file = self.data_dir / "history.json"
            with open(history_file, 'w') as f:
                json.dump(self.follow_history, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save follow data: {e}")
    
    async def follow_user(self, username: str, source: str = "manual") -> Dict[str, Any]:
        """Follow a single user."""
        try:
            if not username:
                return {"status": "error", "message": "Username is required"}
            
            # Simulate follow delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Record follow action
            follow_record = {
                "username": username,
                "action": "follow",
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            self.follow_history.append(follow_record)
            self.following_list.add(username)
            
            # Save data
            self._save_data()
            
            logger.info(f"Successfully followed user: {username}")
            
            return {
                "status": "success",
                "username": username,
                "action": "follow",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to follow user {username}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "username": username,
                "timestamp": datetime.now().isoformat()
            }
    
    async def unfollow_user(self, username: str, reason: str = "cleanup") -> Dict[str, Any]:
        """Unfollow a user."""
        try:
            if not username:
                return {"status": "error", "message": "Username is required"}
            
            # Simulate unfollow delay
            await asyncio.sleep(random.uniform(1, 2))
            
            # Record unfollow action
            unfollow_record = {
                "username": username,
                "action": "unfollow",
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            self.follow_history.append(unfollow_record)
            self.following_list.discard(username)
            
            # Save data
            self._save_data()
            
            logger.info(f"Successfully unfollowed user: {username}")
            
            return {
                "status": "success",
                "username": username,
                "action": "unfollow",
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to unfollow user {username}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "username": username,
                "timestamp": datetime.now().isoformat()
            }
    
    async def bulk_follow(self, usernames: List[str], source: str = "bulk") -> Dict[str, Any]:
        """Follow multiple users."""
        try:
            results = {"successful": 0, "failed": 0, "details": []}
            
            for username in usernames:
                result = await self.follow_user(username, source)
                
                if result["status"] == "success":
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append(result)
                
                # Add delay between follows
                await asyncio.sleep(random.uniform(2, 5))
            
            logger.info(f"Bulk follow completed: {results['successful']} successful, {results['failed']} failed")
            
            return {
                "status": "success",
                "message": f"Bulk follow completed: {results['successful']} successful, {results['failed']} failed",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed bulk follow: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def add_follow_targets(self, targets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add follow targets to the system."""
        try:
            added_count = 0
            
            for target in targets:
                if isinstance(target, dict) and "username" in target:
                    self.follow_targets.append({
                        "username": target["username"],
                        "priority": target.get("priority", 1),
                        "tags": target.get("tags", []),
                        "added_at": datetime.now().isoformat()
                    })
                    added_count += 1
            
            self._save_data()
            
            return {
                "status": "success",
                "message": f"Added {added_count} follow targets",
                "added_count": added_count
            }
            
        except Exception as e:
            logger.error(f"Failed to add follow targets: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_follow_targets(self, max_follows: int = 50) -> Dict[str, Any]:
        """Process follow targets automatically."""
        try:
            processed = 0
            successful = 0
            
            for target in self.follow_targets[:max_follows]:
                username = target.get("username")
                if username and username not in self.following_list:
                    result = await self.follow_user(username, "auto_target")
                    processed += 1
                    
                    if result["status"] == "success":
                        successful += 1
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(3, 7))
            
            return {
                "status": "success",
                "message": f"Processed {processed} targets, {successful} successful follows",
                "processed": processed,
                "successful": successful,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process follow targets: {e}")
            return {"status": "error", "message": str(e)}
    
    async def cleanup_non_followers(self, max_unfollows: int = 100) -> Dict[str, Any]:
        """Cleanup users who haven't followed back."""
        try:
            # Simulate cleanup logic
            cleanup_count = min(max_unfollows, len(self.following_list) // 4)
            
            return {
                "status": "success",
                "message": f"Cleanup would process {cleanup_count} users",
                "cleanup_count": cleanup_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed cleanup: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_follow_stats(self) -> Dict[str, Any]:
        """Get follow system statistics."""
        try:
            recent_follows = [h for h in self.follow_history 
                            if h.get("action") == "follow" 
                            and datetime.fromisoformat(h["timestamp"]) > datetime.now() - timedelta(days=7)]
            
            return {
                "currently_following": len(self.following_list),
                "total_targets": len(self.follow_targets),
                "total_history_entries": len(self.follow_history),
                "recent_follows_7d": len(recent_follows),
                "last_activity": self.follow_history[-1]["timestamp"] if self.follow_history else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get follow stats: {e}")
            return {"error": str(e)}

