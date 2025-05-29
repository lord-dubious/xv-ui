"""
XAgent - Advanced Twitter automation agent with behavioral loops
Now includes all twagent functionality as built-in modules
Plus complete TOTP, encryption, and configuration management
"""

import asyncio
import json
import logging
import os
import uuid
import random
import base64
import time as time_module
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Union
import hashlib

# Security and encryption imports
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logging.warning("pyotp not available. Install pyotp for TOTP support.")

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography not available. Install cryptography for secure credential storage.")

# Import all the integrated twagent modules
import sys
import os
sys.path.append(os.path.dirname(__file__))

from twitter_api import TwitterAPI
from persona_manager import PersonaManager
from tweet_generator import TweetGenerator
from media_manager import MediaManager
from follow_system import FollowSystem

# Set up logging
logger = logging.getLogger(__name__)

class XAgent:
    """Advanced Twitter automation agent with all twagent functionality built-in plus complete TOTP and security."""
    
    def __init__(self, profile_name: str = "default", llm=None, browser_config: Dict[str, Any] = None):
        """Initialize XAgent with a specific profile and optional LLM."""
        self.profile_name = profile_name
        self.current_task_id = None
        self.llm = llm
        self.browser_config = browser_config or {}
        
        # Twitter credentials with encryption support
        self.twitter_credentials = {
            "username": "",
            "email": "",
            "password": "",
            "totp_secret": "",
        }
        
        # Initialize encryption for secure credential storage
        self._encryption_key = None
        self._initialize_encryption()
        
        # Initialize all integrated modules
        self.twitter_api = TwitterAPI()
        self.persona_manager = PersonaManager(f"./profiles/{profile_name}/personas")
        self.tweet_generator = TweetGenerator(f"./profiles/{profile_name}/tweet_templates")
        self.media_manager = MediaManager(f"./profiles/{profile_name}/media")
        self.follow_system = FollowSystem(f"./profiles/{profile_name}/follow_data")
        
        # Behavioral loops and scheduling
        self.action_loops = []
        self.scheduled_actions = []
        self.loop_states = {}
        self.is_running = False
        self.loop_task = None
        
        # Configuration settings
        self.module_settings = {
            "rate_limiting_enabled": True,
            "caching_enabled": True,
            "performance_monitoring_enabled": True,
            "adaptive_delays_enabled": True,
            "burst_protection_enabled": True,
            "follow_system_enabled": True,
            "unfollow_system_enabled": True,
            "twitter_api_enabled": True,
            "persona_manager_enabled": True,
            "tweet_generator_enabled": True,
            "media_manager_enabled": True,
        }
        
        self.time_interval_settings = {
            "use_fixed_intervals": False,
            "interval_minutes": 60,
            "randomize_intervals": True,
            "randomization_factor": 0.2,
        }
        
        # Twitter configuration
        self.twitter_config = {
            "cookies_path": f"./profiles/{profile_name}/cookies.json",
            "config_path": f"./profiles/{profile_name}/config.json",
            "headless": True,
            "stealth_mode": True,
            "user_agent": None,
            "viewport": {"width": 1280, "height": 720},
            "timeout": 30,
        }
        
        # Performance tracking
        self.performance_stats = {
            "actions_executed": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "start_time": datetime.now().timestamp(),
        }
        
        # Load profile configuration
        self._load_profile_config()
        
        logger.info(f"XAgent initialized with profile: {profile_name}")
        logger.info("All twagent functionality integrated as built-in modules!")
        logger.info(f"TOTP support: {'✅' if PYOTP_AVAILABLE else '❌'}")
        logger.info(f"Encryption support: {'✅' if CRYPTO_AVAILABLE else '❌'}")
    
    def _initialize_encryption(self):
        """Initialize encryption for secure credential storage."""
        if not CRYPTO_AVAILABLE:
            logger.warning("Cryptography not available - credentials will not be encrypted")
            return
            
        try:
            salt = b'xagent_salt_for_credentials'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.profile_name.encode()))
            self._encryption_key = Fernet(key)
            logger.info("Encryption initialized for secure credential storage")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._encryption_key = None

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self._encryption_key or not data or not CRYPTO_AVAILABLE:
            return data
        try:
            return self._encryption_key.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return data

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self._encryption_key or not encrypted_data or not CRYPTO_AVAILABLE:
            return encrypted_data
        try:
            return self._encryption_key.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return encrypted_data
    
    def save_twitter_credentials(self, username: str, email: str, password: str, totp_secret: str) -> Dict[str, Any]:
        """Save Twitter credentials securely."""
        try:
            self.twitter_credentials = {
                "username": username,
                "email": email,
                "password": password,
                "totp_secret": totp_secret,
            }
            
            self._save_profile_config()
            
            return {
                "status": "success",
                "message": "Credentials saved successfully",
                "encrypted": CRYPTO_AVAILABLE,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_current_totp_code(self) -> str:
        """Get current TOTP code for 2FA."""
        if not PYOTP_AVAILABLE:
            logger.warning("pyotp not available - cannot generate TOTP codes")
            return ""
            
        try:
            if not self.twitter_credentials.get("totp_secret"):
                return ""
            
            totp = pyotp.TOTP(self.twitter_credentials["totp_secret"])
            return totp.now()
            
        except Exception as e:
            logger.error(f"Failed to generate TOTP code: {e}")
            return ""
    
    def get_totp_qr_code_url(self, service_name: str = "Twitter") -> str:
        """Get QR code URL for TOTP setup."""
        if not PYOTP_AVAILABLE:
            return ""
            
        try:
            if not self.twitter_credentials.get("totp_secret"):
                return ""
            
            totp = pyotp.TOTP(self.twitter_credentials["totp_secret"])
            username = self.twitter_credentials.get("username", "user")
            return totp.provisioning_uri(
                name=username,
                issuer_name=service_name
            )
            
        except Exception as e:
            logger.error(f"Failed to generate QR code URL: {e}")
            return ""
    
    def generate_new_totp_secret(self) -> str:
        """Generate a new TOTP secret."""
        if not PYOTP_AVAILABLE:
            logger.warning("pyotp not available - cannot generate TOTP secret")
            return ""
            
        try:
            return pyotp.random_base32()
        except Exception as e:
            logger.error(f"Failed to generate TOTP secret: {e}")
            return ""
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the agent and all modules."""
        try:
            # Initialize Twitter API
            result = await self.twitter_api.initialize_session()
            if result["status"] != "success":
                logger.warning(f"Twitter API initialization warning: {result.get('message', '')}")
            
            logger.info("XAgent fully initialized with all integrated modules")
            return {"status": "success", "message": "XAgent initialized successfully"}
        except Exception as e:
            logger.error(f"Failed to initialize XAgent: {e}")
            return {"status": "error", "message": str(e)}
    
    # Core Twitter functionality using integrated modules
    async def create_tweet(self, content: str, media_paths: List[str] = None, persona: str = None) -> Dict[str, Any]:
        """Create a tweet with optional persona and media."""
        try:
            # Apply persona styling if specified
            if persona:
                persona_data = self.persona_manager.get_persona(persona)
                if persona_data:
                    content = self.persona_manager.apply_persona_style(content, persona)
                else:
                    logger.warning(f"Persona not found: {persona}")
            
            # Create tweet using integrated Twitter API
            result = await self.twitter_api.create_tweet(content, media_paths)
            
            # Update performance stats
            self._update_performance_stats(result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating tweet: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    async def reply_to_tweet(self, tweet_url: str, content: str, media_paths: List[str] = None, persona: str = None) -> Dict[str, Any]:
        """Reply to a tweet with optional persona and media."""
        try:
            # Apply persona styling if specified
            if persona:
                persona_data = self.persona_manager.get_persona(persona)
                if persona_data:
                    content = self.persona_manager.apply_persona_style(content, persona)
            
            # Create reply using integrated Twitter API
            result = await self.twitter_api.reply_to_tweet(tweet_url, content, media_paths)
            
            # Update performance stats
            self._update_performance_stats(result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    async def follow_user(self, username: str) -> Dict[str, Any]:
        """Follow a user using the integrated follow system."""
        try:
            # Check if follow system is enabled
            if not self.module_settings.get("follow_system_enabled", True):
                return {
                    "status": "disabled",
                    "message": "Follow system is disabled in module settings",
                    "timestamp": datetime.now().isoformat()
                }
            
            result = await self.follow_system.follow_user(username, "manual")
            
            # Update performance stats
            self._update_performance_stats(result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error following user {username}: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    async def bulk_follow(self, usernames: List[str]) -> Dict[str, Any]:
        """Follow multiple users using the integrated follow system."""
        try:
            # Check if follow system is enabled
            if not self.module_settings.get("follow_system_enabled", True):
                return {
                    "status": "disabled",
                    "message": "Follow system is disabled in module settings",
                    "timestamp": datetime.now().isoformat()
                }
            
            result = await self.follow_system.bulk_follow(usernames, "bulk")
            
            # Update performance stats for each successful follow
            successful = result.get("successful", 0)
            failed = result.get("failed", 0)
            for _ in range(successful):
                self._update_performance_stats(True)
            for _ in range(failed):
                self._update_performance_stats(False)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk follow: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    async def unfollow_user(self, username: str, reason: str = "cleanup") -> Dict[str, Any]:
        """Unfollow a user using the integrated follow system."""
        try:
            # Check if unfollow system is enabled
            if not self.module_settings.get("unfollow_system_enabled", True):
                return {
                    "status": "disabled",
                    "message": "Unfollow system is disabled in module settings",
                    "timestamp": datetime.now().isoformat()
                }
            
            result = await self.follow_system.unfollow_user(username, reason)
            
            # Update performance stats
            self._update_performance_stats(result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error unfollowing user {username}: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    async def like_tweet(self, tweet_url: str) -> Dict[str, Any]:
        """Like a tweet."""
        try:
            result = await self.twitter_api.like_tweet(tweet_url)
            
            # Update performance stats
            self._update_performance_stats(result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error liking tweet: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    async def retweet(self, tweet_url: str, comment: str = None) -> Dict[str, Any]:
        """Retweet a tweet with optional comment."""
        try:
            result = await self.twitter_api.retweet(tweet_url, comment)
            
            # Update performance stats
            self._update_performance_stats(result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error retweeting: {e}")
            self._update_performance_stats(False)
            return {"status": "error", "message": str(e)}
    
    # Advanced content generation methods
    def generate_tweet_content(self, theme: str, persona: str = None, template: str = None) -> str:
        """Generate tweet content using integrated tweet generator."""
        try:
            persona_data = None
            if persona:
                persona_data = self.persona_manager.get_persona(persona)
            
            if template:
                # Use template-based generation
                content = self.tweet_generator.generate_tweet(
                    template=template,
                    persona=persona_data,
                    variables={"topic": theme, "content": theme}
                )
            else:
                # Use persona-based generation
                content = self.persona_manager.generate_persona_content(theme, persona)
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating tweet content: {e}")
            return f"Content about {theme}"
    
    def generate_thread(self, topic: str, points: List[str], persona: str = None) -> List[str]:
        """Generate a Twitter thread using integrated tweet generator."""
        try:
            persona_data = None
            if persona:
                persona_data = self.persona_manager.get_persona(persona)
            
            thread = self.tweet_generator.generate_thread(topic, points, persona_data)
            return thread
            
        except Exception as e:
            logger.error(f"Error generating thread: {e}")
            return [f"Thread about {topic}"]
    
    # Media management methods
    def add_media(self, file_path: str, description: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """Add media file using integrated media manager."""
        return self.media_manager.add_media(file_path, description, tags)
    
    def list_media(self, media_type: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """List media files using integrated media manager."""
        return self.media_manager.list_media(media_type, tags)
    
    def search_media(self, query: str) -> List[Dict[str, Any]]:
        """Search media files using integrated media manager."""
        return self.media_manager.search_media(query)
    
    # Persona management methods
    def list_personas(self) -> List[str]:
        """List available personas."""
        return self.persona_manager.list_personas()
    
    def get_persona(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """Get persona data."""
        return self.persona_manager.get_persona(persona_name)
    
    def set_current_persona(self, persona_name: str) -> bool:
        """Set the current active persona."""
        return self.persona_manager.set_current_persona(persona_name)
    
    def create_persona(self, persona_name: str, persona_data: Dict[str, Any]) -> bool:
        """Create a new persona."""
        return self.persona_manager.save_persona(persona_name, persona_data)
    
    # Follow system methods
    def add_follow_targets(self, targets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add follow targets to the system."""
        return self.follow_system.add_follow_targets(targets)
    
    async def process_follow_targets(self, max_follows: int = 50) -> Dict[str, Any]:
        """Process follow targets automatically."""
        return await self.follow_system.process_follow_targets(max_follows)
    
    async def cleanup_non_followers(self, max_unfollows: int = 100) -> Dict[str, Any]:
        """Cleanup users who haven't followed back."""
        return await self.follow_system.cleanup_non_followers(max_unfollows)
    
    def get_follow_stats(self) -> Dict[str, Any]:
        """Get follow system statistics."""
        return self.follow_system.get_follow_stats()
    
    # Template management methods
    def list_templates(self) -> List[str]:
        """List available tweet templates."""
        return self.tweet_generator.list_templates()
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get template data."""
        return self.tweet_generator.get_template(template_name)
    
    def create_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Create a new tweet template."""
        return self.tweet_generator.save_template(template_name, template_data)
    
    # Configuration and utility methods
    def update_module_settings(self, settings: Dict[str, bool]) -> Dict[str, Any]:
        """Update module enable/disable settings."""
        try:
            for key, value in settings.items():
                if key in self.module_settings:
                    self.module_settings[key] = value
                    logger.info(f"Updated module setting: {key} = {value}")
            
            self._save_profile_config()
            
            return {
                "status": "success",
                "message": "Module settings updated successfully",
                "current_settings": self.module_settings.copy()
            }
        except Exception as e:
            logger.error(f"Error updating module settings: {e}")
            return {"status": "error", "message": str(e)}
    
    def update_time_interval_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update time interval settings."""
        try:
            for key, value in settings.items():
                if key in self.time_interval_settings:
                    self.time_interval_settings[key] = value
                    logger.info(f"Updated time interval setting: {key} = {value}")
            
            self._save_profile_config()
            
            return {
                "status": "success",
                "message": "Time interval settings updated successfully",
                "current_settings": self.time_interval_settings.copy()
            }
        except Exception as e:
            logger.error(f"Error updating time interval settings: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get current status of all modules and settings."""
        return {
            "profile_name": self.profile_name,
            "module_settings": self.module_settings.copy(),
            "time_interval_settings": self.time_interval_settings.copy(),
            "twitter_config": self.twitter_config.copy(),
            "available_modules": {
                "twitter_api": True,
                "persona_manager": True,
                "tweet_generator": True,
                "media_manager": True,
                "follow_system": True,
            },
            "security_features": {
                "totp_support": PYOTP_AVAILABLE,
                "encryption_support": CRYPTO_AVAILABLE,
            },
            "personas": len(self.persona_manager.list_personas()),
            "templates": len(self.tweet_generator.list_templates()),
            "media_files": len(self.media_manager.list_media()),
            "follow_targets": len(self.follow_system.follow_targets),
            "performance_stats": self.get_performance_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        runtime = datetime.now().timestamp() - self.performance_stats["start_time"]
        total_actions = self.performance_stats["actions_executed"]
        
        return {
            "runtime_seconds": runtime,
            "total_actions": total_actions,
            "successful_actions": self.performance_stats["successful_actions"],
            "failed_actions": self.performance_stats["failed_actions"],
            "success_rate": (self.performance_stats["successful_actions"] / max(total_actions, 1)) * 100,
            "actions_per_hour": (total_actions / max(runtime / 3600, 1/3600)) if runtime > 0 else 0,
        }
    
    def _update_performance_stats(self, success: bool):
        """Update performance statistics."""
        self.performance_stats["actions_executed"] += 1
        if success:
            self.performance_stats["successful_actions"] += 1
        else:
            self.performance_stats["failed_actions"] += 1
    
    # Profile and configuration management
    def _load_profile_config(self):
        """Load profile configuration from file."""
        try:
            profile_dir = os.path.join("./profiles", self.profile_name)
            config_file = os.path.join(profile_dir, "config.json")
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Load encrypted credentials
                credentials = config.get("credentials", {})
                for key, value in credentials.items():
                    if value:
                        self.twitter_credentials[key] = self._decrypt_data(value)
                
                # Load Twitter configuration
                self.twitter_config.update(config.get("twitter_config", {}))
                
                # Load action loops
                self.action_loops = config.get("action_loops", [])
                self.scheduled_actions = config.get("scheduled_actions", [])
                
                # Load module settings
                self.module_settings.update(config.get("module_settings", {}))
                
                # Load time interval settings
                self.time_interval_settings.update(config.get("time_interval_settings", {}))
                
                logger.info(f"📁 Loaded profile configuration: {self.profile_name}")
            else:
                logger.info(f"📁 No profile configuration found for: {self.profile_name}")
                
        except Exception as e:
            logger.error(f"Failed to load profile config: {e}")

    def _save_profile_config(self):
        """Save profile configuration to file."""
        try:
            profile_dir = os.path.join("./profiles", self.profile_name)
            os.makedirs(profile_dir, exist_ok=True)
            config_file = os.path.join(profile_dir, "config.json")
            
            # Encrypt credentials before saving
            encrypted_credentials = {}
            for key, value in self.twitter_credentials.items():
                if value:
                    encrypted_credentials[key] = self._encrypt_data(value)
                else:
                    encrypted_credentials[key] = ""
            
            config = {
                "credentials": encrypted_credentials,
                "twitter_config": self.twitter_config,
                "action_loops": self.action_loops,
                "scheduled_actions": self.scheduled_actions,
                "module_settings": self.module_settings,
                "time_interval_settings": self.time_interval_settings,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"💾 Saved profile configuration: {self.profile_name}")
            
        except Exception as e:
            logger.error(f"Failed to save profile config: {e}")
    
    # Behavioral loops functionality
    def load_action_loops(self, loops_json: str) -> Dict[str, Any]:
        """Load action loops from JSON configuration."""
        try:
            loops = json.loads(loops_json)
            if not isinstance(loops, list):
                return {"status": "error", "message": "Configuration must be a list of loops"}
            
            # Validate loop structure
            for loop in loops:
                if not isinstance(loop, dict):
                    return {"status": "error", "message": "Each loop must be a dictionary"}
                
                required_fields = ["id", "actions"]
                for field in required_fields:
                    if field not in loop:
                        return {"status": "error", "message": f"Missing required field: {field}"}
            
            self.action_loops = loops
            self._save_profile_config()
            
            return {
                "status": "success",
                "message": f"Loaded {len(loops)} action loops",
                "loops": loops
            }
            
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            logger.error(f"Error loading action loops: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_action_loops(self) -> List[Dict[str, Any]]:
        """Get current action loops configuration."""
        return self.action_loops.copy()
    
    async def start_behavioral_loops(self) -> Dict[str, Any]:
        """Start behavioral action loops."""
        if self.is_running:
            return {"status": "error", "message": "Loops already running"}
        
        if not self.action_loops:
            return {"status": "error", "message": "No action loops configured"}
        
        try:
            self.is_running = True
            # Start the loop execution in the background
            self.loop_task = asyncio.create_task(self._run_behavioral_loops())
            
            return {
                "status": "success",
                "message": f"Started {len(self.action_loops)} behavioral loops",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start behavioral loops: {e}")
            self.is_running = False
            return {"status": "error", "message": str(e)}
    
    async def stop_behavioral_loops(self) -> Dict[str, Any]:
        """Stop behavioral action loops."""
        if not self.is_running:
            return {"status": "error", "message": "No loops running"}
        
        try:
            self.is_running = False
            if self.loop_task:
                self.loop_task.cancel()
                try:
                    await self.loop_task
                except asyncio.CancelledError:
                    pass
                self.loop_task = None
            
            return {
                "status": "success",
                "message": "Stopped behavioral loops",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop behavioral loops: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _run_behavioral_loops(self):
        """Run the behavioral action loops."""
        while self.is_running:
            try:
                for loop in self.action_loops:
                    if not self.is_running:
                        break
                    
                    loop_id = loop.get("id", "unknown")
                    actions = loop.get("actions", [])
                    interval = loop.get("interval_seconds", 3600)
                    
                    logger.info(f"🔄 Executing loop: {loop_id}")
                    
                    for action in actions:
                        if not self.is_running:
                            break
                        
                        action_type = action.get("type")
                        params = action.get("params", {})
                        
                        try:
                            await self._execute_loop_action(action_type, params)
                            logger.info(f"✅ Executed {action_type}")
                        except Exception as e:
                            logger.error(f"Failed to execute {action_type}: {e}")
                    
                    # Wait for interval
                    if self.is_running:
                        await asyncio.sleep(interval)
                        
            except Exception as e:
                logger.error(f"Error in behavioral loops: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _execute_loop_action(self, action_type: str, params: Dict[str, Any]):
        """Execute a single loop action."""
        if action_type == "tweet":
            content = params.get("content", "")
            persona = params.get("persona")
            media_paths = params.get("media_paths")
            await self.create_tweet(content, media_paths, persona)
            
        elif action_type == "reply":
            tweet_url = params.get("tweet_url", "")
            content = params.get("content", "")
            persona = params.get("persona")
            media_paths = params.get("media_paths")
            await self.reply_to_tweet(tweet_url, content, media_paths, persona)
            
        elif action_type == "follow":
            username = params.get("username", "")
            await self.follow_user(username)
            
        elif action_type == "bulk_follow":
            usernames = params.get("usernames", [])
            await self.bulk_follow(usernames)
            
        elif action_type == "like":
            tweet_url = params.get("tweet_url", "")
            await self.like_tweet(tweet_url)
            
        elif action_type == "retweet":
            tweet_url = params.get("tweet_url", "")
            comment = params.get("comment")
            await self.retweet(tweet_url, comment)
            
        elif action_type == "delay":
            seconds = params.get("seconds", 60)
            await asyncio.sleep(seconds)
            
        else:
            logger.warning(f"Unknown action type: {action_type}")
    
    # Task execution methods for UI compatibility
    async def run_task(self, task: str, max_steps: int = 10, save_results: bool = True) -> Dict[str, Any]:
        """Run a general task (for UI compatibility)."""
        try:
            self.current_task_id = str(uuid.uuid4())
            
            # Parse task and execute appropriate actions
            if "tweet" in task.lower():
                result = await self.create_tweet(task)
            elif "follow" in task.lower():
                # Extract username from task
                words = task.split()
                username = next((word for word in words if word.startswith("@")), "example_user")
                username = username.lstrip("@")
                result = await self.follow_user(username)
            else:
                # Generic task execution
                result = {
                    "status": "success",
                    "message": f"Task executed: {task}",
                    "task_id": self.current_task_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Save results if requested
            if save_results:
                await self._save_task_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running task: {e}")
            return {
                "status": "error",
                "message": str(e),
                "task_id": self.current_task_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _save_task_results(self, result: Dict[str, Any]):
        """Save task results to file."""
        try:
            if not self.current_task_id:
                return
            
            save_dir = f"./profiles/{self.profile_name}/results"
            os.makedirs(save_dir, exist_ok=True)
            
            result_file = os.path.join(save_dir, f"{self.current_task_id}_result.json")
            
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"💾 Saved task results: {result_file}")
            
        except Exception as e:
            logger.error(f"Failed to save task results: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "profile_name": self.profile_name,
            "current_task_id": self.current_task_id,
            "is_running": self.is_running,
            "action_loops_count": len(self.action_loops),
            "module_status": self.get_module_status(),
            "performance_stats": self.get_performance_stats(),
            "security_status": {
                "totp_configured": bool(self.twitter_credentials.get("totp_secret")),
                "credentials_encrypted": CRYPTO_AVAILABLE and bool(self._encryption_key),
                "totp_available": PYOTP_AVAILABLE,
                "encryption_available": CRYPTO_AVAILABLE,
            },
            "timestamp": datetime.now().isoformat()
        }
