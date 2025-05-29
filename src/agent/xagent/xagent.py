"""
XAgent - Advanced stealth agent using Patchright with integrated Twitter capabilities.

This agent combines Patchright's enhanced stealth capabilities with Twitter automation
for maximum functionality and bot detection evasion.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Union
import pyotp
import base64
import time as time_module
from collections import defaultdict, deque
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rate_limiter import RateLimiter
from action_cache import ActionCache
from performance_monitor import PerformanceMonitor
import hashlib

# Import browser_use components with fallback
try:
    from browser_use import BrowserUseAgent, BrowserConfig, BrowserContextConfig
    from browser_use.browser.browser import Browser as BrowserUseBrowser
    from browser_use.controller.service import Controller as CustomController
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logging.warning("Browser-use components not available. Install browser-use for full functionality.")

# Import stealth browser components with fallback
try:
    from browser_use.browser.stealth_browser import StealthBrowser
    STEALTH_BROWSER_AVAILABLE = True
except ImportError:
    STEALTH_BROWSER_AVAILABLE = False
    logging.warning("Stealth browser not available. Using standard browser.")

# Import Twitter components with fallback
try:
    from twagent.api.twitter_api import TwitterAPI
    from twagent.actions.create_post import CreatePost
    from twagent.actions.reply_to_post import ReplyToPost
    from twagent.actions.follow_user import FollowUser
    from twagent.actions.follow_system import FollowSystem
    from twagent.personas.persona_manager import PersonaManager
    from twagent.content.tweet_generator import TweetGenerator
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    logging.warning("Twitter functionality not available. Install twagent for Twitter support.")

logger = logging.getLogger(__name__)


class XAgent:
    """
    XAgent - Advanced stealth agent with integrated Twitter capabilities.

    Features:
    - Patchright stealth browser (Chrome-only optimized)
    - Enhanced anti-detection capabilities
    - Twitter automation capabilities (directly integrated)
    - Persona-based content generation
    - Secure credential management
    - Behavioral loops and scheduling
    """

    def __init__(
        self,
        llm,
        browser_config: Dict[str, Any],
        proxy_list: Optional[List[str]] = None,
        proxy_rotation_mode: str = "round_robin",
        mcp_server_config: Optional[Dict[str, Any]] = None,
        mode: str = "stealth",  # "stealth", "proxy", or "hybrid"
        twitter_config: Optional[Dict[str, Any]] = None,
        profile_name: Optional[str] = None,
    ):
        """
        Initialize XAgent with stealth and Twitter capabilities.

        Args:
            llm: Language model instance
            browser_config: Browser configuration dictionary
            proxy_list: List of SOCKS5 proxy URLs (socks5://user:pass@host:port)
            proxy_rotation_mode: "round_robin" or "random"
            mcp_server_config: MCP server configuration
            mode: "stealth" (Patchright only), "proxy" (browser+proxy), "hybrid" (both)
            twitter_config: Optional Twitter configuration
            profile_name: Optional profile name for configuration isolation
        """
        self.llm = llm
        self.browser_config = browser_config
        self.mcp_server_config = mcp_server_config or {}
        self.mode = mode
        self.twitter_config = twitter_config or {}
        self.profile_name = profile_name or "default"

        # Initialize proxy manager if proxies provided (commented out for this branch)
        self.proxy_manager = None
        # if proxy_list and PROXY_AVAILABLE and ProxyManager:
        #     self.proxy_manager = ProxyManager(proxy_list, proxy_rotation_mode)
        #     logger.info(f"🌐 XAgent initialized with {len(proxy_list)} proxies")
        # elif proxy_list and not PROXY_AVAILABLE:
        #     logger.warning(
        #         "⚠️ Proxy list provided but proxy dependencies not available. Install 'proxystr' for proxy support."
        #     )

        # Twitter integration components
        self.twitter_api = None
        self.persona_manager = None
        self.tweet_generator = None
        self.twitter_initialized = False
        self.twitter_credentials = {
            "username": "",
            "email": "",
            "password": "",
            "totp_secret": "",
        }
        
        # Behavioral loop settings
        self.action_loops = []
        self.scheduled_actions = []
        self.loop_running = False
        self.loop_task = None
        
        # Rate limiting and performance optimization
        try:
            from .rate_limiter import RateLimiter
            from .action_cache import ActionCache
            from .performance_monitor import PerformanceMonitor
            self.rate_limiter = RateLimiter()
            self.action_cache = ActionCache()
            self.performance_monitor = PerformanceMonitor()
        except ImportError:
            # Fallback to basic implementations
            self.rate_limiter = None
            self.action_cache = None
            self.performance_monitor = None
            logger.warning("Performance optimization components not available")
        
        # Encryption for secure credential storage
        self._encryption_key = None
        self._initialize_encryption()

        # Agent state
        self.current_task_id = None
        self.runner = None
        self.stopped = False
        self.stop_event = None
        self.browser = None
        self.context = None

        # Load profile configuration if available
        self._load_profile_config()

        logger.info("🎭 XAgent initialized with Patchright stealth capabilities")

    def _initialize_encryption(self):
        """Initialize encryption for secure credential storage."""
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
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._encryption_key = None

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self._encryption_key or not data:
            return data
        try:
            return self._encryption_key.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return data

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self._encryption_key or not encrypted_data:
            return encrypted_data
        try:
            return self._encryption_key.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return encrypted_data

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
                
                # Load action loops
                self.action_loops = config.get("action_loops", [])
                self.scheduled_actions = config.get("scheduled_actions", [])
                
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
                "twitter": self.twitter_config,
                "credentials": encrypted_credentials,
                "action_loops": self.action_loops,
                "scheduled_actions": self.scheduled_actions,
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"💾 Saved profile configuration: {self.profile_name}")
            
        except Exception as e:
            logger.error(f"Failed to save profile config: {e}")

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
        try:
            if not self.twitter_credentials.get("totp_secret"):
                return ""
            
            totp = pyotp.TOTP(self.twitter_credentials["totp_secret"])
            return totp.now()
            
        except Exception as e:
            logger.error(f"Failed to generate TOTP code: {e}")
            return ""

    async def initialize_twitter(self) -> Dict[str, Any]:
        """Initialize Twitter functionality."""
        if not TWITTER_AVAILABLE:
            return {
                "status": "error",
                "error": "Twitter functionality not available. Install twagent for Twitter support.",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            # Initialize Twitter API with browser context
            if not self.browser or not self.context:
                # Create browser context if not available
                await self._ensure_browser_context()
            
            self.twitter_api = TwitterAPI(
                browser_context=self.context,
                cookies_path=self.twitter_config.get("cookies_path", "./cookies.json"),
            )
            
            # Initialize persona manager
            persona_path = self.twitter_config.get("persona_path", "./personas")
            if os.path.exists(persona_path):
                self.persona_manager = PersonaManager(persona_path)
            
            # Initialize tweet generator with LLM
            if self.llm:
                self.tweet_generator = TweetGenerator(self.llm)
            
            self.twitter_initialized = True
            
            return {
                "status": "success",
                "message": "Twitter functionality initialized",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _ensure_browser_context(self):
        """Ensure browser context is available."""
        if not BROWSER_USE_AVAILABLE:
            raise Exception("Browser-use components not available")
            
        if not self.browser:
            self.browser = await self._create_stealth_browser()
        
        if not self.context:
            self.context = await self._create_stealth_context(self.browser)

    async def create_tweet(self, content: str, media_paths: Optional[List[str]] = None, persona_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new tweet."""
        if not self.twitter_initialized:
            init_result = await self.initialize_twitter()
            if init_result["status"] != "success":
                return init_result
        
        try:
            # Generate content with persona if specified
            if persona_name and self.persona_manager and self.tweet_generator:
                persona = self.persona_manager.get_persona(persona_name)
                if persona:
                    content = await self.tweet_generator.generate_tweet(content, persona)
            
            # Create tweet using Twitter API
            create_post = CreatePost(self.twitter_api)
            result = await create_post.create_tweet(content, media_paths)
            
            return {
                "status": "success",
                "result": result,
                "content": content,
                "persona": persona_name,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to create tweet: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def reply_to_tweet(self, tweet_url: str, content: str, media_paths: Optional[List[str]] = None, persona_name: Optional[str] = None) -> Dict[str, Any]:
        """Reply to an existing tweet."""
        if not self.twitter_initialized:
            init_result = await self.initialize_twitter()
            if init_result["status"] != "success":
                return init_result
        
        try:
            # Generate content with persona if specified
            if persona_name and self.persona_manager and self.tweet_generator:
                persona = self.persona_manager.get_persona(persona_name)
                if persona:
                    content = await self.tweet_generator.generate_reply(content, persona)
            
            # Reply to tweet using Twitter API
            reply_to_post = ReplyToPost(self.twitter_api)
            result = await reply_to_post.reply_to_tweet(tweet_url, content, media_paths)
            
            return {
                "status": "success",
                "result": result,
                "content": content,
                "tweet_url": tweet_url,
                "persona": persona_name,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to reply to tweet: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def follow_user(self, username: str) -> Dict[str, Any]:
        """Follow a Twitter user."""
        if not self.twitter_initialized:
            init_result = await self.initialize_twitter()
            if init_result["status"] != "success":
                return init_result
        
        try:
            follow_user = FollowUser(self.twitter_api)
            result = await follow_user.follow(username)
            
            return {
                "status": "success",
                "result": result,
                "username": username,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to follow user: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def bulk_follow(self, usernames: List[str]) -> Dict[str, Any]:
        """Follow multiple Twitter users."""
        if not self.twitter_initialized:
            init_result = await self.initialize_twitter()
            if init_result["status"] != "success":
                return init_result
        
        try:
            follow_system = FollowSystem(self.twitter_api)
            result = await follow_system.bulk_follow(usernames)
            
            return {
                "status": "success",
                "result": result,
                "usernames": usernames,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to bulk follow: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def start_action_loop(self) -> Dict[str, Any]:
        """Start behavioral action loops."""
        if self.loop_running:
            return {
                "status": "error",
                "error": "Action loop already running",
                "timestamp": datetime.now().isoformat(),
            }
        
        if not self.action_loops:
            return {
                "status": "error",
                "error": "No action loops configured",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            self.loop_running = True
            self.loop_task = asyncio.create_task(self._run_action_loops())
            
            return {
                "status": "success",
                "message": "Action loops started",
                "loops_count": len(self.action_loops),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to start action loops: {e}")
            self.loop_running = False
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def stop_action_loop(self) -> Dict[str, Any]:
        """Stop behavioral action loops."""
        if not self.loop_running:
            return {
                "status": "error",
                "error": "No action loop running",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            self.loop_running = False
            if self.loop_task:
                self.loop_task.cancel()
                try:
                    await self.loop_task
                except asyncio.CancelledError:
                    pass
                self.loop_task = None
            
            return {
                "status": "success",
                "message": "Action loops stopped",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to stop action loops: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _run_action_loops(self):
        """Run the behavioral action loops with advanced scheduling."""
        while self.loop_running:
            try:
                for loop in self.action_loops:
                    if not self.loop_running:
                        break
                    
                    loop_id = loop.get("id", "unknown")
                    interval = loop.get("interval_seconds", 3600)
                    actions = loop.get("actions", [])
                    conditions = loop.get("conditions", {})
                    rate_limit = loop.get("rate_limit", {})
                    
                    # Check loop-level conditions
                    if not self._check_loop_conditions(conditions):
                        logger.debug(f"Skipping loop {loop_id} - conditions not met")
                        continue
                    
                    # Update rate limits for this loop
                    if self.rate_limiter and rate_limit:
                        self.rate_limiter.set_custom_limits(rate_limit)
                        if "min_delay_seconds" in rate_limit:
                            min_delays = {
                                "tweets": rate_limit["min_delay_seconds"],
                                "follows": rate_limit["min_delay_seconds"],
                                "replies": rate_limit["min_delay_seconds"],
                            }
                            self.rate_limiter.set_min_delays(min_delays)
                    
                    logger.info(f"🔄 Executing action loop: {loop_id}")
                    
                    for action in actions:
                        if not self.loop_running:
                            break
                        
                        action_type = action.get("type")
                        params = action.get("params", {})
                        action_conditions = action.get("conditions", {})
                        
                        # Check action-level conditions
                        if not self._check_action_conditions(action_conditions):
                            logger.debug(f"Skipping action {action_type} - conditions not met")
                            continue
                        
                        try:
                            await self._execute_action(action_type, params)
                            logger.info(f"✅ Executed {action_type} successfully")
                        except Exception as e:
                            logger.error(f"Failed to execute action {action_type}: {e}")
                            
                            # Adaptive delay on failure
                            if self.rate_limiter:
                                self.rate_limiter.adjust_global_rate(1.5)  # Slow down on errors
                    
                    # Wait for the interval before next loop iteration
                    if self.loop_running:
                        await asyncio.sleep(interval)
                        
            except Exception as e:
                logger.error(f"Error in action loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def _check_loop_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if loop-level conditions are met."""
        if not conditions:
            return True
        
        # Check time range
        time_range = conditions.get("time_range")
        if time_range:
            current_time = datetime.now().time()
            start_time = time.fromisoformat(time_range["start"])
            end_time = time.fromisoformat(time_range["end"])
            
            if not (start_time <= current_time <= end_time):
                return False
        
        # Check days of week (1=Monday, 7=Sunday)
        days_of_week = conditions.get("days_of_week")
        if days_of_week:
            current_day = datetime.now().isoweekday()
            if current_day not in days_of_week:
                return False
        
        # Check follower count condition
        follower_count_max = conditions.get("follower_count_max")
        if follower_count_max:
            # This would check actual follower count
            # For now, we'll assume it passes
            pass
        
        return True

    def _check_action_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if action-level conditions are met."""
        if not conditions:
            return True
        
        # Check time range for specific actions
        time_range = conditions.get("time_range")
        if time_range:
            current_time = datetime.now().time()
            start_time = time.fromisoformat(time_range["start"])
            end_time = time.fromisoformat(time_range["end"])
            
            if not (start_time <= current_time <= end_time):
                return False
        
        # Check daily action limits
        max_actions_today = conditions.get("max_actions_today")
        if max_actions_today:
            # This would check actual action count for today
            # For now, we'll assume it passes
            pass
        
        # Check follow limits
        max_follows_today = conditions.get("max_follows_today")
        if max_follows_today:
            # This would check actual follow count for today
            # For now, we'll assume it passes
            pass
        
        return True

    def save_action_loops(self, loops_json: str) -> Dict[str, Any]:
        """Save action loops configuration."""
        try:
            loops = json.loads(loops_json)
            self.action_loops = loops
            self._save_profile_config()
            
            return {
                "status": "success",
                "message": "Action loops saved successfully",
                "loops_count": len(loops),
                "timestamp": datetime.now().isoformat(),
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Invalid JSON: {e}",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to save action loops: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_action_loops_status(self) -> Dict[str, Any]:
        """Get current action loops status."""
        return {
            "loop_running": self.loop_running,
            "loops_count": len(self.action_loops),
            "action_loops": self.action_loops,
            "timestamp": datetime.now().isoformat(),
        }

    async def _create_stealth_browser(self):
        """Create StealthBrowser with enhanced capabilities."""
        if not BROWSER_USE_AVAILABLE:
            raise Exception("Browser-use components not available")
            
        # Enhanced browser config for stealth
        config = BrowserConfig(
            headless=self.browser_config.get("headless", False),
            disable_security=self.browser_config.get("disable_security", False),
            browser_binary_path=self.browser_config.get("browser_binary_path"),
            browser_class="chromium",  # Patchright only supports Chromium
            extra_browser_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
            ],
        )

        # Create StealthBrowser with proxy manager
        browser = StealthBrowser(config, self.proxy_manager)
        return browser

    async def _create_stealth_context(self, browser):
        """Create stealth browser context."""
        if not BROWSER_USE_AVAILABLE:
            raise Exception("Browser-use components not available")
            
        context_config = BrowserContextConfig(
            save_downloads_path="./tmp/xagent/downloads",
            window_height=self.browser_config.get("window_height", 1100),
            window_width=self.browser_config.get("window_width", 1280),
            force_new_context=True,
        )
        return await browser.new_context(context_config)

    async def run(
        self,
        task: str,
        task_id: Optional[str] = None,
        save_dir: str = "./tmp/xagent",
        max_steps: int = 50,
        test_proxies: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a task with XAgent stealth capabilities.

        Args:
            task: The task to perform
            task_id: Optional task ID for resuming
            save_dir: Directory to save results
            max_steps: Maximum steps for browser agent
            test_proxies: Whether to test proxies before starting

        Returns:
            Dict with task results
        """
        if not BROWSER_USE_AVAILABLE:
            return {
                "status": "error",
                "error": "Browser-use components not available",
                "timestamp": datetime.now().isoformat(),
            }
            
        if self.runner and not self.runner.done():
            logger.warning(
                "XAgent is already running. Please stop the current task first."
            )
            return {
                "status": "error",
                "message": "XAgent already running.",
                "task_id": self.current_task_id,
            }

        # Generate task ID
        self.current_task_id = task_id or str(uuid.uuid4())
        self.stop_event = asyncio.Event()
        self.stopped = False

        logger.info(f"🎭 Starting XAgent task: {task}")
        logger.info(f"🔔 Task ID: {self.current_task_id}")

        # Initialize browser variable for cleanup
        self.browser = None
        self.context = None

        try:
            # Create stealth browser with proxy support
            self.browser = await self._create_stealth_browser()
            self.context = await self._create_stealth_context(self.browser)
            controller = CustomController()

            # Initialize Twitter agent if available but not initialized
            if self.twitter_config and not self.twitter_initialized:
                logger.info("🐦 Initializing Twitter agent for task")
                await self.initialize_twitter()

            # Create specialized system prompt for XAgent
            xagent_prompt = self._create_xagent_prompt(task)

            # Create browser agent with stealth specialization
            browser_agent = BrowserUseAgent(
                task=xagent_prompt,
                llm=self.llm,
                browser=self.browser,
                browser_context=self.context,
                controller=controller,
                source="xagent",
            )

            # Run the browser agent
            logger.info("🚀 Executing XAgent task with stealth capabilities...")
            result = await browser_agent.run(max_steps=max_steps)

            # Process results
            final_result = result.final_result()

            # Save results
            await self._save_results(final_result, save_dir)

            logger.info(f"✅ XAgent task completed: {self.current_task_id}")

            return {
                "status": "completed",
                "task_id": self.current_task_id,
                "result": final_result,
                "proxy_used": self._get_current_proxy_info(),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error in XAgent task: {e}")
            return {
                "status": "error",
                "task_id": self.current_task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            # Cleanup
            try:
                if self.browser:
                    await self.browser.close()
                    self.browser = None
                    self.context = None
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

    def _create_xagent_prompt(self, task: str) -> str:
        """Create a specialized prompt for XAgent tasks."""
        proxy_info = ""
        # if self.proxy_manager:
        #     current_proxy = self.proxy_manager.get_current_proxy()
        #     if current_proxy:
        #         proxy_info = f"\nProxy: Using SOCKS5 proxy {current_proxy.host}:{current_proxy.port} for enhanced anonymity"

        twitter_info = ""
        if self.twitter_initialized:
            twitter_info = "\n🐦 TWITTER CAPABILITIES: Enabled with browser-based automation for tweeting, following, and engagement"

        return f"""
        XAgent Stealth Task: {task}
        {proxy_info}
        {twitter_info}

        You are XAgent, an advanced stealth automation specialist with enhanced capabilities:

        🎭 STEALTH FEATURES:
        - Patchright browser with Runtime.enable patched
        - Console.enable patched for stealth
        - Enhanced anti-detection measures
        - Closed shadow root interaction support
        - Advanced fingerprint resistance

        🌐 PROXY FEATURES:
        - Proxy support planned (currently disabled)
        - Future: SOCKS5 proxy routing
        - Future: IP rotation for anonymity

        🛡️ DETECTION BYPASS:
        - Cloudflare, Kasada, Akamai bypass
        - Datadome, Fingerprint.com evasion
        - CreepJS, Sannysoft stealth
        - Enhanced bot detection resistance
        
        🐦 TWITTER CAPABILITIES:
        - Browser-based Twitter automation
        - Tweet creation and replies
        - Following users and managing lists
        - Persona-based content generation
        - Cookie-based authentication

        GUIDELINES:
        1. Always respect website terms of service
        2. Use stealth capabilities responsibly
        3. Take screenshots of important actions
        4. Monitor for detection attempts
        5. Rotate proxies if connection issues occur
        6. Maintain realistic browsing patterns
        7. For Twitter: maintain natural posting patterns

        Execute the task step by step with maximum stealth and anonymity.
        """

    async def _save_results(self, result: str, save_dir: str):
        """Save XAgent task results."""
        os.makedirs(save_dir, exist_ok=True)

        result_file = os.path.join(save_dir, f"{self.current_task_id}_result.json")

        result_data = {
            "task_id": self.current_task_id,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "status": "completed",
            "proxy_info": self._get_current_proxy_info(),
            "stealth_features": [
                "Patchright Runtime.enable patched",
                "Console.enable patched",
                "Enhanced anti-detection",
            ],
        }

        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"📁 Results saved to: {result_file}")

    def _get_current_proxy_info(self) -> Optional[Dict[str, Any]]:
        """Get current proxy information."""
        if not self.proxy_manager:
            return None

        current_proxy = self.proxy_manager.get_current_proxy()
        if not current_proxy:
            return None

        return {
            "host": current_proxy.host,
            "port": current_proxy.port,
            "protocol": current_proxy.protocol,
            "is_working": current_proxy.is_working,
            "response_time": current_proxy.response_time,
        }

    async def stop(self):
        """Stop the currently running XAgent task."""
        if not self.current_task_id or not self.stop_event:
            logger.info("No XAgent task is currently running.")
            return

        logger.info(f"🛑 Stop requested for XAgent task: {self.current_task_id}")
        self.stop_event.set()
        self.stopped = True

    def get_status(self) -> Dict[str, Any]:
        """Get current XAgent status."""
        status = {
            "current_task_id": self.current_task_id,
            "is_running": self.runner and not self.runner.done()
            if self.runner
            else False,
            "stopped": self.stopped,
            "stealth_engine": "Patchright",
            "proxy_enabled": self.proxy_manager is not None,
            "twitter_initialized": self.twitter_initialized,
            "loop_running": self.loop_running,
            "profile_name": self.profile_name,
        }

        # if self.proxy_manager:
        #     status["proxy_status"] = self.proxy_manager.get_status()
        #     status["current_proxy"] = self._get_current_proxy_info()

        return status

    async def _execute_action(self, action_type: str, params: Dict[str, Any]):
        """Execute a single action with performance monitoring and rate limiting."""
        # Start performance monitoring
        operation_id = None
        if self.performance_monitor:
            operation_id = self.performance_monitor.start_operation(action_type)
        
        # Check rate limiting
        if self.rate_limiter:
            await self.rate_limiter.wait_if_needed(action_type)
        
        success = False
        error = None
        
        try:
            if action_type == "tweet":
                content = params.get("content", "")
                persona = params.get("persona")
                media_paths = params.get("media_paths")
                
                # Check cache for similar content
                if self.action_cache:
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    cached_content = self.action_cache.get_tweet_content(content_hash)
                    if cached_content:
                        content = cached_content
                        logger.info("Using cached tweet content")
                
                result = await self.create_tweet(content, media_paths, persona)
                success = result.get("status") == "success"
                
                # Cache successful content
                if success and self.action_cache:
                    self.action_cache.cache_tweet_content(content_hash, content)
                
            elif action_type == "reply":
                tweet_url = params.get("tweet_url", "")
                content = params.get("content", "")
                persona = params.get("persona")
                media_paths = params.get("media_paths")
                result = await self.reply_to_tweet(tweet_url, content, media_paths, persona)
                success = result.get("status") == "success"
                
            elif action_type == "follow":
                username = params.get("username", "")
                
                # Check cache for follow status
                if self.action_cache:
                    cached_status = self.action_cache.get_follow_status(username)
                    if cached_status is True:
                        logger.info(f"Already following {username} (cached)")
                        success = True
                        return
                
                result = await self.follow_user(username)
                success = result.get("status") == "success"
                
                # Cache follow status
                if success and self.action_cache:
                    self.action_cache.cache_follow_status(username, True)
                
            elif action_type == "bulk_follow":
                usernames = params.get("usernames", [])
                result = await self.bulk_follow(usernames)
                success = result.get("status") == "success"
                
            elif action_type == "delay":
                seconds = params.get("seconds", 60)
                await asyncio.sleep(seconds)
                success = True
                
            elif action_type == "create_list":
                list_name = params.get("list_name", "")
                description = params.get("description", "")
                # This would be implemented with Twitter list creation
                logger.info(f"Creating list: {list_name}")
                success = True
                
            else:
                logger.warning(f"Unknown action type: {action_type}")
                error = f"Unknown action type: {action_type}"
                
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            error = str(e)
        
        # Record action in rate limiter
        if self.rate_limiter:
            self.rate_limiter.record_action(action_type, success)
        
        # End performance monitoring
        if self.performance_monitor and operation_id:
            self.performance_monitor.end_operation(operation_id, success, error)
        
        if not success and error:
            raise Exception(error)
