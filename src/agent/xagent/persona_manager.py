"""
Persona Manager for XAgent
Minimal version for testing
"""

import json
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PersonaManager:
    """Manages Twitter personas for content generation and styling."""
    
    def __init__(self, personas_dir: str = "./personas"):
        self.personas_dir = Path(personas_dir)
        self.personas = {}
        self.current_persona = None
        
        # Create personas directory if it doesn't exist
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default personas
        self._create_default_personas()
    
    def _create_default_personas(self):
        """Create default personas."""
        default_personas = {
            "tech_enthusiast": {
                "name": "Tech Enthusiast",
                "description": "Passionate about technology, AI, and innovation",
                "hashtags": ["#TechLife", "#Innovation", "#AI"],
                "emojis": ["🚀", "💡", "🔥", "⚡", "🌟"],
                "writing_style": {
                    "emoji_frequency": 0.4,
                    "hashtag_count": 2,
                }
            },
            "casual_friendly": {
                "name": "Casual & Friendly",
                "description": "Relaxed, approachable, and conversational tone",
                "hashtags": ["#JustSaying", "#Thoughts", "#Life"],
                "emojis": ["😊", "😄", "🤔", "👍", "❤️"],
                "writing_style": {
                    "emoji_frequency": 0.3,
                    "hashtag_count": 1,
                }
            }
        }
        
        self.personas = default_personas
        logger.info(f"Created {len(default_personas)} default personas")
    
    def get_persona(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """Get a persona by name."""
        return self.personas.get(persona_name)
    
    def list_personas(self) -> List[str]:
        """Get list of available persona names."""
        return list(self.personas.keys())
    
    def set_current_persona(self, persona_name: str) -> bool:
        """Set the current active persona."""
        if persona_name in self.personas:
            self.current_persona = persona_name
            logger.info(f"Set current persona to: {persona_name}")
            return True
        else:
            logger.error(f"Persona not found: {persona_name}")
            return False
    
    def get_current_persona(self) -> Optional[Dict[str, Any]]:
        """Get the current active persona."""
        if self.current_persona:
            return self.personas.get(self.current_persona)
        return None
    
    def apply_persona_style(self, content: str, persona_name: str = None) -> str:
        """Apply persona styling to content."""
        persona = self.get_persona(persona_name) if persona_name else self.get_current_persona()
        
        if not persona:
            return content
        
        try:
            styled_content = content
            writing_style = persona.get("writing_style", {})
            
            # Add emojis based on frequency
            emoji_freq = writing_style.get("emoji_frequency", 0.2)
            if random.random() < emoji_freq:
                emojis = persona.get("emojis", [])
                if emojis:
                    emoji = random.choice(emojis)
                    styled_content = f"{styled_content} {emoji}"
            
            # Add hashtags
            hashtag_count = writing_style.get("hashtag_count", 1)
            hashtags = persona.get("hashtags", [])
            if hashtags and hashtag_count > 0:
                selected_hashtags = random.sample(hashtags, min(hashtag_count, len(hashtags)))
                hashtag_string = " ".join(selected_hashtags)
                styled_content = f"{styled_content} {hashtag_string}"
            
            return styled_content.strip()
            
        except Exception as e:
            logger.error(f"Error applying persona style: {e}")
            return content
    
    def generate_persona_content(self, theme: str, persona_name: str = None) -> str:
        """Generate content based on persona and theme."""
        persona = self.get_persona(persona_name) if persona_name else self.get_current_persona()
        
        if not persona:
            return f"Content about {theme}"
        
        try:
            # Generate base content
            content = f"Here's something interesting about {theme}"
            
            # Apply persona styling
            return self.apply_persona_style(content, persona_name)
            
        except Exception as e:
            logger.error(f"Error generating persona content: {e}")
            return f"Content about {theme}"
    
    def save_persona(self, persona_name: str, persona_data: Dict[str, Any]) -> bool:
        """Save a persona."""
        try:
            self.personas[persona_name] = persona_data
            logger.info(f"Saved persona: {persona_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save persona {persona_name}: {e}")
            return False

