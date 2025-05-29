"""
Tweet Generator for XAgent
Minimal version for testing
"""

import json
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TweetGenerator:
    """Generates tweets with various styles and templates."""
    
    def __init__(self, templates_dir: str = "./tweet_templates"):
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        
        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default templates
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default tweet templates."""
        default_templates = {
            "announcement": {
                "name": "Announcement",
                "patterns": [
                    "🚀 Exciting news! {content}",
                    "📢 Announcement: {content}",
                    "🎉 We're thrilled to share: {content}"
                ],
                "variables": ["content"]
            },
            "question": {
                "name": "Question",
                "patterns": [
                    "🤔 What do you think about {topic}?",
                    "💭 Quick question: {question}?",
                    "🗣️ I'm curious - {question}?"
                ],
                "variables": ["topic", "question"]
            }
        }
        
        self.templates = default_templates
        logger.info(f"Created {len(default_templates)} default templates")
    
    def generate_tweet(self, 
                      content: str = None, 
                      template: str = None, 
                      persona: Dict[str, Any] = None,
                      variables: Dict[str, str] = None,
                      max_length: int = 280) -> str:
        """Generate a tweet."""
        try:
            if template and template in self.templates:
                return self._generate_from_template(template, variables, persona, max_length)
            
            if content:
                return self._enhance_content(content, persona, max_length)
            
            return "Generated tweet content"
            
        except Exception as e:
            logger.error(f"Error generating tweet: {e}")
            return content or "Generated tweet content"
    
    def _generate_from_template(self, 
                               template_name: str, 
                               variables: Dict[str, str] = None,
                               persona: Dict[str, Any] = None,
                               max_length: int = 280) -> str:
        """Generate tweet from a template."""
        template = self.templates.get(template_name)
        if not template:
            return "Template not found"
        
        variables = variables or {}
        patterns = template.get("patterns", [])
        
        if not patterns:
            return "No patterns in template"
        
        # Select random pattern
        pattern = random.choice(patterns)
        
        # Fill in variables
        try:
            for var_name in template.get("variables", []):
                placeholder = f"{{{var_name}}}"
                if placeholder in pattern:
                    value = variables.get(var_name, f"[{var_name}]")
                    pattern = pattern.replace(placeholder, value)
            
            # Ensure length limit
            if len(pattern) > max_length:
                pattern = pattern[:max_length-3] + "..."
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error filling template: {e}")
            return pattern
    
    def _enhance_content(self, 
                        content: str, 
                        persona: Dict[str, Any] = None,
                        max_length: int = 280) -> str:
        """Enhance existing content."""
        enhanced = content
        
        try:
            # Ensure length limit
            if len(enhanced) > max_length:
                enhanced = enhanced[:max_length-3] + "..."
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing content: {e}")
            return content
    
    def generate_thread(self, topic: str, points: List[str], persona: Dict[str, Any] = None) -> List[str]:
        """Generate a Twitter thread."""
        try:
            thread = []
            
            # Generate starter tweet
            starter = f"🧵 Thread: {topic} (1/n)"
            thread.append(starter)
            
            # Generate tweets for each point
            for i, point in enumerate(points, 2):
                tweet_content = f"{point} ({i}/n)"
                thread.append(tweet_content)
            
            # Update thread numbering
            total_tweets = len(thread)
            for i, tweet in enumerate(thread):
                thread[i] = tweet.replace("(n)", f"({total_tweets})")
                thread[i] = thread[i].replace("n)", f"{total_tweets})")
            
            return thread
            
        except Exception as e:
            logger.error(f"Error generating thread: {e}")
            return [f"Thread about {topic}"]
    
    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name."""
        return self.templates.get(template_name)
    
    def save_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Save a tweet template."""
        try:
            self.templates[template_name] = template_data
            logger.info(f"Saved template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save template {template_name}: {e}")
            return False

