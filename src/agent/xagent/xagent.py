"""
XAgent - Advanced stealth agent using Patchright with SOCKS5 proxy support.

This agent combines Patchright's enhanced stealth capabilities with rotating
SOCKS5 proxies for maximum anonymity and bot detection evasion.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.stealth_browser import StealthBrowser
from src.controller.custom_controller import CustomController

# Optional proxy support (commented out for this branch)
# try:
#     from src.proxy.proxy_manager import ProxyManager
#     PROXY_AVAILABLE = True
# except ImportError:
#     ProxyManager = None
#     PROXY_AVAILABLE = False

# Import TwitterAgent integration
try:
    from src.agent.xagent.twitter_agent import TwitterAgent
    TWITTER_AGENT_AVAILABLE = True
except ImportError:
    TwitterAgent = None
    TWITTER_AGENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class XAgent:
    """
    XAgent - Advanced stealth agent with Patchright and proxy rotation.

    Features:
    - Patchright stealth browser (Chrome-only optimized)
    - SOCKS5 proxy rotation with proxystr
    - Enhanced anti-detection capabilities
    - Automatic proxy failover
    - Connection isolation (all traffic through proxy)
    - Twitter automation capabilities (via twagent)
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
    ):
        """
        Initialize XAgent with stealth and proxy capabilities.

        Args:
            llm: Language model instance
            browser_config: Browser configuration dictionary
            proxy_list: List of SOCKS5 proxy URLs (socks5://user:pass@host:port)
            proxy_rotation_mode: "round_robin" or "random"
            mcp_server_config: MCP server configuration
            mode: "stealth" (Patchright only), "proxy" (browser+proxy), "hybrid" (both)
            twitter_config: Optional Twitter configuration with cookies_path, persona_path, etc.
        """
        self.llm = llm
        self.browser_config = browser_config
        self.mcp_server_config = mcp_server_config or {}
        self.mode = mode
        self.twitter_config = twitter_config or {}

        # Initialize proxy manager if proxies provided (commented out for this branch)
        self.proxy_manager = None
        # if proxy_list and PROXY_AVAILABLE and ProxyManager:
        #     self.proxy_manager = ProxyManager(proxy_list, proxy_rotation_mode)
        #     logger.info(f"🌐 XAgent initialized with {len(proxy_list)} proxies")
        # elif proxy_list and not PROXY_AVAILABLE:
        #     logger.warning(
        #         "⚠️ Proxy list provided but proxy dependencies not available. Install 'proxystr' for proxy support."
        #     )

        # Initialize Twitter agent if configured
        self.twitter_agent = None
        if TWITTER_AGENT_AVAILABLE and self.twitter_config:
            logger.info("🐦 Initializing Twitter agent integration")
            self.twitter_agent = TwitterAgent(
                xagent=self,
                cookies_path=self.twitter_config.get("cookies_path"),
                persona_path=self.twitter_config.get("persona_path"),
                config_path=self.twitter_config.get("config_path"),
            )

        # Agent state
        self.current_task_id = None
        self.runner = None
        self.stopped = False
        self.stop_event = None
        self.browser = None
        self.context = None

        logger.info("🎭 XAgent initialized with Patchright stealth capabilities")

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
            # Test proxies if enabled (commented out for this branch)
            # if self.proxy_manager and test_proxies:
            #     logger.info("🧪 Testing proxies before starting...")
            #     proxy_report = await self.proxy_manager.test_all_proxies()
            #
            #     if proxy_report["working_proxies"] == 0:
            #         return {
            #             "status": "error",
            #             "message": "No working proxies available",
            #             "task_id": self.current_task_id,
            #             "proxy_report": proxy_report,
            #         }
            #
            #     logger.info(
            #         f"✅ {proxy_report['working_proxies']}/{proxy_report['total_proxies']} proxies working"
            #     )

            # Create stealth browser with proxy support
            self.browser = await self._create_stealth_browser()
            self.context = await self._create_stealth_context(self.browser)
            controller = CustomController()

            # Initialize Twitter agent if available but not initialized
            if self.twitter_agent and not self.twitter_agent.initialized:
                logger.info("🐦 Initializing Twitter agent for task")
                await self.twitter_agent.initialize()

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
        if self.twitter_agent and self.twitter_agent.initialized:
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

    async def _create_stealth_browser(self) -> StealthBrowser:
        """Create StealthBrowser with proxy support."""
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

    async def _create_stealth_context(self, browser: StealthBrowser):
        """Create stealth browser context."""
        context_config = BrowserContextConfig(
            save_downloads_path="./tmp/xagent/downloads",
            window_height=self.browser_config.get("window_height", 1100),
            window_width=self.browser_config.get("window_width", 1280),
            force_new_context=True,
        )
        return await browser.new_context(context_config)

    async def _save_results(self, result: str, save_dir: str):
        """Save XAgent task results."""
        import json
        import os

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
        }

        # if self.proxy_manager:
        #     status["proxy_status"] = self.proxy_manager.get_status()
        #     status["current_proxy"] = self._get_current_proxy_info()
        
        # Add Twitter agent status if available
        if self.twitter_agent:
            status["twitter_agent"] = {
                "initialized": self.twitter_agent.initialized,
                "last_error": self.twitter_agent.last_error,
            }

        return status

    async def create_tweet(self, content: str, media_paths: Optional[List[str]] = None, persona_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new tweet using the Twitter agent.
        
        Args:
            content: Tweet text content
            media_paths: Optional list of paths to media files to attach
            persona_name: Optional persona to use for tweet generation
            
        Returns:
            Dict with tweet result information
        """
        if not self.twitter_agent:
            return {
                "status": "error",
                "error": "Twitter agent not available",
                "timestamp": datetime.now().isoformat(),
            }
            
        return await self.twitter_agent.create_tweet(content, media_paths, persona_name)
    
    async def reply_to_tweet(self, tweet_url: str, content: str, media_paths: Optional[List[str]] = None, persona_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Reply to an existing tweet using the Twitter agent.
        
        Args:
            tweet_url: URL of the tweet to reply to
            content: Reply text content
            media_paths: Optional list of paths to media files to attach
            persona_name: Optional persona to use for reply generation
            
        Returns:
            Dict with reply result information
        """
        if not self.twitter_agent:
            return {
                "status": "error",
                "error": "Twitter agent not available",
                "timestamp": datetime.now().isoformat(),
            }
            
        return await self.twitter_agent.reply_to_tweet(tweet_url, content, media_paths, persona_name)
    
    async def follow_user(self, username: str) -> Dict[str, Any]:
        """
        Follow a Twitter user using the Twitter agent.
        
        Args:
            username: Twitter username to follow (without @)
            
        Returns:
            Dict with follow result information
        """
        if not self.twitter_agent:
            return {
                "status": "error",
                "error": "Twitter agent not available",
                "timestamp": datetime.now().isoformat(),
            }
            
        return await self.twitter_agent.follow_user(username)
    
    async def bulk_follow(self, usernames: List[str]) -> Dict[str, Any]:
        """
        Follow multiple Twitter users using the Twitter agent.
        
        Args:
            usernames: List of Twitter usernames to follow
            
        Returns:
            Dict with bulk follow result information
        """
        if not self.twitter_agent:
            return {
                "status": "error",
                "error": "Twitter agent not available",
                "timestamp": datetime.now().isoformat(),
            }
            
        return await self.twitter_agent.bulk_follow(usernames)
    
    async def get_available_personas(self) -> Dict[str, Any]:
        """
        Get list of available Twitter personas.
        
        Returns:
            Dict with persona information
        """
        if not self.twitter_agent:
            return {
                "status": "error",
                "error": "Twitter agent not available",
                "timestamp": datetime.now().isoformat(),
            }
            
        return await self.twitter_agent.get_available_personas()

    # async def rotate_proxy(self) -> Dict[str, Any]:
    #     """Manually rotate to next proxy."""
    #     if not self.proxy_manager:
    #         return {"status": "error", "message": "No proxy manager configured"}
    #
    #     old_proxy = self.proxy_manager.get_current_proxy()
    #     new_proxy = self.proxy_manager.force_rotate()
    #
    #     return {
    #         "status": "success",
    #         "old_proxy": f"{old_proxy.host}:{old_proxy.port}" if old_proxy else None,
    #         "new_proxy": f"{new_proxy.host}:{new_proxy.port}" if new_proxy else None,
    #     }
    #
    # async def test_current_proxy(self) -> Dict[str, Any]:
    #     """Test the current proxy."""
    #     if not self.proxy_manager:
    #         return {"status": "error", "message": "No proxy manager configured"}
    #
    #     current_proxy = self.proxy_manager.get_current_proxy()
    #     if not current_proxy:
    #         return {"status": "error", "message": "No current proxy available"}
    #
    #     is_working = await self.proxy_manager.test_proxy(current_proxy)
    #
    #     return {
    #         "status": "success",
    #         "proxy": f"{current_proxy.host}:{current_proxy.port}",
    #         "is_working": is_working,
    #         "response_time": current_proxy.response_time,
    #     }
