"""
Media Manager for XAgent
Minimal version for testing
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class MediaManager:
    """Manages media files for Twitter posts."""
    
    def __init__(self, media_dir: str = "./media"):
        self.media_dir = Path(media_dir)
        self.media_cache = {}
        
        # Create media directory structure
        self._setup_directories()
    
    def _setup_directories(self):
        """Create media directory structure."""
        try:
            self.media_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['images', 'videos', 'gifs', 'processed']
            for subdir in subdirs:
                (self.media_dir / subdir).mkdir(exist_ok=True)
            
            logger.info(f"Media directories set up at: {self.media_dir}")
            
        except Exception as e:
            logger.error(f"Failed to setup media directories: {e}")
    
    def add_media(self, file_path: str, description: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """Add a media file to the manager."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return {"status": "error", "message": f"File not found: {file_path}"}
            
            # Generate media ID
            media_id = f"media_{int(datetime.now().timestamp())}"
            
            # Create media entry
            media_entry = {
                "id": media_id,
                "original_path": str(source_path),
                "description": description or "",
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
            }
            
            # Add to cache
            self.media_cache[media_id] = media_entry
            
            logger.info(f"Added media: {media_id}")
            
            return {
                "status": "success",
                "media_id": media_id,
                "media_entry": media_entry,
                "message": "Media added successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to add media {file_path}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_media(self, media_type: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """List media files with optional filtering."""
        try:
            results = []
            
            for media_id, media_entry in self.media_cache.items():
                # Filter by tags
                if tags:
                    media_tags = media_entry.get("tags", [])
                    if not any(tag in media_tags for tag in tags):
                        continue
                
                results.append(media_entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to list media: {e}")
            return []
    
    def search_media(self, query: str) -> List[Dict[str, Any]]:
        """Search media by description or tags."""
        try:
            results = []
            query_lower = query.lower()
            
            for media_id, media_entry in self.media_cache.items():
                # Search in description
                description = media_entry.get("description", "").lower()
                if query_lower in description:
                    results.append(media_entry)
                    continue
                
                # Search in tags
                tags = media_entry.get("tags", [])
                if any(query_lower in tag.lower() for tag in tags):
                    results.append(media_entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search media: {e}")
            return []
    
    def get_media_stats(self) -> Dict[str, Any]:
        """Get statistics about stored media."""
        try:
            stats = {
                "total_files": len(self.media_cache),
                "by_type": {"image": 0, "video": 0, "gif": 0},
                "total_size": 0,
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get media stats: {e}")
            return {"error": str(e)}

