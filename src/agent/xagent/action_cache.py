"""
Action Cache for XAgent Performance Optimization.

This module provides caching functionality to improve performance
and reduce redundant operations in Twitter automation.
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ActionCache:
    """Advanced caching system for Twitter actions and data."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize the action cache.
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
        }
        
        # Cache categories with different TTLs
        self.category_ttls = {
            "user_info": 1800,      # 30 minutes
            "tweet_content": 300,    # 5 minutes
            "follow_status": 600,    # 10 minutes
            "rate_limits": 60,       # 1 minute
            "search_results": 900,   # 15 minutes
            "media_upload": 3600,    # 1 hour
        }
    
    def _generate_key(self, category: str, identifier: Union[str, Dict]) -> str:
        """Generate a cache key from category and identifier."""
        if isinstance(identifier, dict):
            # Sort dict for consistent hashing
            identifier_str = json.dumps(identifier, sort_keys=True)
        else:
            identifier_str = str(identifier)
        
        # Create hash for long identifiers
        if len(identifier_str) > 100:
            identifier_str = hashlib.md5(identifier_str.encode()).hexdigest()
        
        return f"{category}:{identifier_str}"
    
    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry is expired."""
        if key not in self.cache:
            return True
        
        entry = self.cache[key]
        expiry_time = entry.get("expiry", 0)
        return time.time() > expiry_time
    
    def _evict_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry.get("expiry", 0)
        ]
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def _evict_lru(self):
        """Evict least recently used items if cache is full."""
        while len(self.cache) >= self.max_size:
            # Find least recently used key
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            
            del self.cache[lru_key]
            del self.access_times[lru_key]
            self.stats["evictions"] += 1
    
    def get(self, category: str, identifier: Union[str, Dict]) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            category: Cache category
            identifier: Unique identifier for the item
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(category, identifier)
        
        # Clean expired entries periodically
        if len(self.cache) % 100 == 0:
            self._evict_expired()
        
        if key in self.cache and not self._is_expired(key):
            self.access_times[key] = time.time()
            self.stats["hits"] += 1
            return self.cache[key]["value"]
        
        self.stats["misses"] += 1
        return None
    
    def set(
        self, 
        category: str, 
        identifier: Union[str, Dict], 
        value: Any, 
        ttl: Optional[int] = None
    ):
        """
        Set an item in the cache.
        
        Args:
            category: Cache category
            identifier: Unique identifier for the item
            value: Value to cache
            ttl: Time-to-live in seconds (uses category default if None)
        """
        key = self._generate_key(category, identifier)
        
        # Determine TTL
        if ttl is None:
            ttl = self.category_ttls.get(category, self.default_ttl)
        
        # Evict if necessary
        self._evict_lru()
        
        # Store the entry
        expiry_time = time.time() + ttl
        self.cache[key] = {
            "value": value,
            "expiry": expiry_time,
            "category": category,
            "created": time.time(),
        }
        
        self.access_times[key] = time.time()
        self.stats["sets"] += 1
    
    def delete(self, category: str, identifier: Union[str, Dict]):
        """Delete an item from the cache."""
        key = self._generate_key(category, identifier)
        
        if key in self.cache:
            del self.cache[key]
        
        if key in self.access_times:
            del self.access_times[key]
    
    def clear_category(self, category: str):
        """Clear all items in a specific category."""
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if entry.get("category") == category
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
        
        logger.info(f"Cleared {len(keys_to_delete)} items from category '{category}'")
    
    def clear_all(self):
        """Clear all cached items."""
        count = len(self.cache)
        self.cache.clear()
        self.access_times.clear()
        logger.info(f"Cleared all {count} cached items")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._evict_expired()
        
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Category breakdown
        category_counts = {}
        for entry in self.cache.values():
            category = entry.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_items": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 2),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "evictions": self.stats["evictions"],
            "categories": category_counts,
        }
    
    def cache_user_info(self, username: str, user_data: Dict[str, Any]):
        """Cache user information."""
        self.set("user_info", username, user_data)
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get cached user information."""
        return self.get("user_info", username)
    
    def cache_tweet_content(self, content_hash: str, generated_content: str):
        """Cache generated tweet content."""
        self.set("tweet_content", content_hash, generated_content)
    
    def get_tweet_content(self, content_hash: str) -> Optional[str]:
        """Get cached tweet content."""
        return self.get("tweet_content", content_hash)
    
    def cache_follow_status(self, username: str, is_following: bool):
        """Cache follow status for a user."""
        self.set("follow_status", username, is_following)
    
    def get_follow_status(self, username: str) -> Optional[bool]:
        """Get cached follow status."""
        return self.get("follow_status", username)
    
    def cache_search_results(self, query: str, results: List[Dict[str, Any]]):
        """Cache search results."""
        self.set("search_results", query, results)
    
    def get_search_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        return self.get("search_results", query)
    
    def cache_media_upload(self, media_path: str, upload_result: Dict[str, Any]):
        """Cache media upload result."""
        self.set("media_upload", media_path, upload_result)
    
    def get_media_upload(self, media_path: str) -> Optional[Dict[str, Any]]:
        """Get cached media upload result."""
        return self.get("media_upload", media_path)
    
    def invalidate_user_cache(self, username: str):
        """Invalidate all cached data for a specific user."""
        self.delete("user_info", username)
        self.delete("follow_status", username)
        logger.info(f"Invalidated cache for user: {username}")
    
    def warm_cache(self, data: Dict[str, Any]):
        """Pre-populate cache with known data."""
        for category, items in data.items():
            if isinstance(items, dict):
                for identifier, value in items.items():
                    self.set(category, identifier, value)
        
        logger.info(f"Warmed cache with {sum(len(items) for items in data.values())} items")

