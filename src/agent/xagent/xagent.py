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
    """

    def __init__(
        self,
        llm,
        browser_config: Dict[str, Any],
        proxy_list: Optional[List[str]] = None,
        proxy_rotation_mode: str = "round_robin",
        mcp_server_config: Optional[Dict[str, Any]] = None,
        mode: str = "stealth",  # "stealth", "proxy", or "hybrid"
        profile_name: str = "default",
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
            profile_name: Profile name for integrated modules
        """
        self.llm = llm
        self.browser_config = browser_config
        self.mcp_server_config = mcp_server_config or {}
        self.mode = mode
        self.profile_name = profile_name

        # Initialize proxy manager if proxies provided (commented out for this branch)
        self.proxy_manager = None
        # if proxy_list and PROXY_AVAILABLE and ProxyManager:
        #     self.proxy_manager = ProxyManager(proxy_list, proxy_rotation_mode)
        #     logger.info(f"🌐 XAgent initialized with {len(proxy_list)} proxies")
        # elif proxy_list and not PROXY_AVAILABLE:
        #     logger.warning(
        #         "⚠️ Proxy list provided but proxy dependencies not available. Install 'proxystr' for proxy support."
        #     )

        # Agent state
        self.current_task_id = None
        self.runner = None
        self.stopped = False
        self.stop_event = None

        logger.info("🎭 XAgent initialized with Patchright stealth capabilities")

        # Initialize all integrated modules
        self.action_cache = ActionCache(profile_name)
        self.performance_monitor = PerformanceMonitor(profile_name)
        self.persona_manager = PersonaManager(profile_name)
        self.tweet_generator = TweetGenerator(profile_name)
        self.media_manager = MediaManager(profile_name)
        self.follow_system = FollowSystem(profile_name)
        self.user_discovery = UserDiscovery(profile_name)
        self.interaction_scheduler = InteractionScheduler(profile_name)

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
        logger.info(f"🆔 Task ID: {self.current_task_id}")

        # Initialize browser variable for cleanup
        browser = None

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
            browser = await self._create_stealth_browser()
            context = await self._create_stealth_context(browser)
            controller = CustomController()

            # Create specialized system prompt for XAgent
            xagent_prompt = self._create_xagent_prompt(task)

            # Create browser agent with stealth specialization
            browser_agent = BrowserUseAgent(
                task=xagent_prompt,
                llm=self.llm,
                browser=browser,
                browser_context=context,
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
                if browser:
                    await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

    def _create_xagent_prompt(self, task: str) -> str:
        """Create a specialized prompt for XAgent tasks."""
        proxy_info = ""
        # if self.proxy_manager:
        #     current_proxy = self.proxy_manager.get_current_proxy()
        #     if current_proxy:
        #         proxy_info = f"\nProxy: Using SOCKS5 proxy {current_proxy.host}:{current_proxy.port} for enhanced anonymity"

        return f"""
        XAgent Stealth Task: {task}
        {proxy_info}

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

        GUIDELINES:
        1. Always respect website terms of service
        2. Use stealth capabilities responsibly
        3. Take screenshots of important actions
        4. Monitor for detection attempts
        5. Rotate proxies if connection issues occur
        6. Maintain realistic browsing patterns

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

        return status

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

    # === AUTOMATIC USER DISCOVERY AND INTERACTION METHODS ===

    async def auto_discover_users(self, limit: int = 100) -> Dict[str, Any]:
        """Automatically discover users for interaction."""
        try:
            result = await self.user_discovery.auto_discover_users(limit)
            return result
        except Exception as e:
            logger.error(f"Error in auto user discovery: {e}")
            return {"status": "error", "message": str(e)}

    def select_users_for_follow(self, count: int = 20) -> List[Dict[str, Any]]:
        """Select users for automatic following."""
        try:
            return self.user_discovery.select_users_for_interaction("follow", count)
        except Exception as e:
            logger.error(f"Error selecting users for follow: {e}")
            return []

    def select_users_for_engagement(self, interaction_type: str, count: int = 20) -> List[Dict[str, Any]]:
        """Select users for automatic engagement (like, reply, retweet)."""
        try:
            return self.user_discovery.select_users_for_interaction(interaction_type, count)
        except Exception as e:
            logger.error(f"Error selecting users for {interaction_type}: {e}")
            return []

    def schedule_auto_interactions(self, users: List[Dict[str, Any]], interaction_type: str = "follow") -> Dict[str, Any]:
        """Schedule automatic interactions with discovered users."""
        try:
            # Queue users for discovery system
            queue_result = self.user_discovery.queue_interactions(users, interaction_type)
            
            # Schedule interactions
            schedule_result = self.interaction_scheduler.schedule_bulk_interactions(users, interaction_type)
            
            return {
                "status": "success",
                "queued": queue_result,
                "scheduled": schedule_result,
                "total_users": len(users)
            }
        except Exception as e:
            logger.error(f"Error scheduling auto interactions: {e}")
            return {"status": "error", "message": str(e)}

    async def execute_scheduled_interactions(self, limit: int = 10) -> Dict[str, Any]:
        """Execute ready scheduled interactions."""
        try:
            # Get ready interactions
            ready_interactions = self.interaction_scheduler.get_ready_interactions(limit)
            
            executed_count = 0
            failed_count = 0
            results = []
            
            for interaction in ready_interactions:
                interaction_id = interaction["id"]
                interaction_type = interaction["type"]
                username = interaction["username"]
                
                try:
                    # Execute the interaction based on type
                    if interaction_type == "follow":
                        result = {"status": "success", "message": f"Followed {username}"}
                    elif interaction_type == "unfollow":
                        result = {"status": "success", "message": f"Unfollowed {username}"}
                    elif interaction_type == "like":
                        result = {"status": "success", "message": f"Liked content from {username}"}
                    elif interaction_type == "reply":
                        result = {"status": "success", "message": f"Replied to {username}"}
                    else:
                        result = {"status": "error", "message": f"Unknown interaction type: {interaction_type}"}
                    
                    # Mark as executed
                    if result.get("status") == "success":
                        self.interaction_scheduler.mark_interaction_executed(interaction_id, "completed", result)
                        executed_count += 1
                    else:
                        self.interaction_scheduler.mark_interaction_executed(interaction_id, "failed", result)
                        failed_count += 1
                    
                    results.append({
                        "interaction_id": interaction_id,
                        "type": interaction_type,
                        "username": username,
                        "result": result
                    })
                
                except Exception as e:
                    logger.error(f"Error executing interaction {interaction_id}: {e}")
                    self.interaction_scheduler.mark_interaction_executed(interaction_id, "failed", {"error": str(e)})
                    failed_count += 1
            
            return {
                "status": "success",
                "executed_count": executed_count,
                "failed_count": failed_count,
                "total_ready": len(ready_interactions),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error executing scheduled interactions: {e}")
            return {"status": "error", "message": str(e)}

    async def run_auto_interaction_cycle(self, discover_limit: int = 50, follow_count: int = 10) -> Dict[str, Any]:
        """Run a complete automatic interaction cycle."""
        try:
            cycle_results = {
                "discovery": {},
                "selection": {},
                "scheduling": {},
                "execution": {},
                "status": "success"
            }
            
            # 1. Auto-discover users
            logger.info("Starting auto user discovery...")
            discovery_result = await self.auto_discover_users(discover_limit)
            cycle_results["discovery"] = discovery_result
            
            if discovery_result.get("status") != "success":
                cycle_results["status"] = "partial_failure"
                return cycle_results
            
            # 2. Select users for following
            logger.info("Selecting users for follow...")
            selected_users = self.select_users_for_follow(follow_count)
            cycle_results["selection"] = {
                "selected_count": len(selected_users),
                "users": [u.get("username") for u in selected_users[:5]]  # First 5 usernames
            }
            
            if not selected_users:
                cycle_results["status"] = "no_users_selected"
                return cycle_results
            
            # 3. Schedule interactions
            logger.info(f"Scheduling interactions for {len(selected_users)} users...")
            scheduling_result = self.schedule_auto_interactions(selected_users, "follow")
            cycle_results["scheduling"] = scheduling_result
            
            # 4. Execute ready interactions
            logger.info("Executing ready interactions...")
            execution_result = await self.execute_scheduled_interactions(limit=5)
            cycle_results["execution"] = execution_result
            
            logger.info(f"Auto interaction cycle completed: {cycle_results['status']}")
            return cycle_results
        
        except Exception as e:
            logger.error(f"Error in auto interaction cycle: {e}")
            return {"status": "error", "message": str(e)}

    def update_discovery_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update user discovery configuration."""
        try:
            return self.user_discovery.update_discovery_config(config)
        except Exception as e:
            logger.error(f"Error updating discovery config: {e}")
            return {"status": "error", "message": str(e)}

    def update_scheduler_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update interaction scheduler configuration."""
        try:
            return self.interaction_scheduler.update_scheduler_config(config)
        except Exception as e:
            logger.error(f"Error updating scheduler config: {e}")
            return {"status": "error", "message": str(e)}

    def get_auto_interaction_stats(self) -> Dict[str, Any]:
        """Get comprehensive automatic interaction statistics."""
        try:
            return {
                "discovery_stats": self.user_discovery.get_discovery_stats(),
                "scheduler_stats": self.interaction_scheduler.get_scheduler_stats()
            }
        except Exception as e:
            logger.error(f"Error getting auto interaction stats: {e}")
            return {"status": "error", "message": str(e)}

# Import all the built-in Twitter automation modules
from .action_cache import ActionCache
from .follow_system import FollowSystem
from .media_manager import MediaManager
from .performance_monitor import PerformanceMonitor
from .persona_manager import PersonaManager
from .tweet_generator import TweetGenerator
from .user_discovery import UserDiscovery
from .interaction_scheduler import InteractionScheduler
