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
    ):
        """
        Initializes an XAgent instance with Patchright stealth browser features and optional proxy rotation.
        
        Args:
            llm: The language model to use for agent reasoning and task execution.
            browser_config: Dictionary specifying browser settings such as headless mode and window size.
            proxy_list: Optional list of SOCKS5 proxy URLs for proxy rotation (currently unused).
            proxy_rotation_mode: Proxy selection strategy, either "round_robin" or "random".
            mcp_server_config: Optional configuration for MCP server integration.
            mode: Operation mode, one of "stealth", "proxy", or "hybrid".
        """
        self.llm = llm
        self.browser_config = browser_config
        self.mcp_server_config = mcp_server_config or {}
        self.mode = mode

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

    async def run(
        self,
        task: str,
        task_id: Optional[str] = None,
        save_dir: str = "./tmp/xagent",
        max_steps: int = 50,
        test_proxies: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes a browser automation task using XAgent's stealth capabilities.
        
        Runs the specified task with anti-detection browser features, manages task lifecycle, and saves results to disk. Returns task status, results, proxy information (if applicable), and metadata. If a task is already running, returns an error status.
        
        Args:
            task: Description or instructions for the automation task.
            task_id: Optional identifier to resume or track the task.
            save_dir: Directory path where results will be stored.
            max_steps: Maximum number of steps the browser agent may execute.
            test_proxies: Ignored in this version (proxy testing is disabled).
        
        Returns:
            A dictionary containing the task status, task ID, result, proxy information (if any), and timestamp.
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
                if "browser" in locals():
                    await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

    def _create_xagent_prompt(self, task: str) -> str:
        """
        Generates a detailed system prompt describing XAgent's stealth, proxy, and detection bypass capabilities for a given automation task.
        
        Args:
            task: The description of the automation task to be performed.
        
        Returns:
            A multi-line string prompt tailored for XAgent, outlining its advanced features and operational guidelines.
        """
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
        - All connections routed through SOCKS5 proxy
        - Rotating IP addresses for anonymity
        - Connection isolation and leak prevention

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
        """
        Asynchronously creates and returns a StealthBrowser instance configured for stealth automation.
        
        The browser is set up with enhanced Chromium arguments to minimize automation detection. Proxy support is included if a proxy manager is configured.
        	
        Returns:
        	A StealthBrowser instance with stealth and optional proxy capabilities.
        """
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
        """
        Creates a new stealth browser context with specified window dimensions and download path.
        
        Args:
            browser: The StealthBrowser instance to create the context from.
        
        Returns:
            An asynchronously created browser context configured for stealth automation.
        """
        context_config = BrowserContextConfig(
            save_downloads_path="./tmp/xagent/downloads",
            window_height=self.browser_config.get("window_height", 1100),
            window_width=self.browser_config.get("window_width", 1280),
            force_new_context=True,
        )
        return await browser.new_context(context_config)

    async def _save_results(self, result: str, save_dir: str):
        """
        Saves the results of the current XAgent task to a JSON file in the specified directory.
        
        The saved file includes task metadata, result content, proxy information, and a list of stealth features used.
        """
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
                "SOCKS5 proxy rotation",
                "Connection isolation",
            ],
        }

        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"📁 Results saved to: {result_file}")

    def _get_current_proxy_info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves details about the currently active proxy.
        
        Returns:
            A dictionary containing the current proxy's host, port, protocol, working status, and response time, or None if no proxy is configured or active.
        """
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
        """
        Stops the currently running XAgent task, if any.
        
        If a task is active, signals it to stop and marks the agent as stopped. If no task is running, logs that no action is taken.
        """
        if not self.current_task_id or not self.stop_event:
            logger.info("No XAgent task is currently running.")
            return

        logger.info(f"🛑 Stop requested for XAgent task: {self.current_task_id}")
        self.stop_event.set()
        self.stopped = True

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the XAgent, including task ID, running state, stop flag, stealth engine, and proxy enablement.
        """
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
