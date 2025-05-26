import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController

logger = logging.getLogger(__name__)


class SocialMediaAgent:
    """
    Social Media Agent for automated social media management tasks.

    Features:
    - Post content across multiple platforms
    - Monitor mentions and engagement
    - Schedule posts
    - Analyze social media metrics
    """

    def __init__(
        self,
        llm,
        browser_config: Dict[str, Any],
        mcp_server_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Social Media Agent.

        Args:
            llm: Language model instance
            browser_config: Browser configuration dictionary
            mcp_server_config: MCP server configuration
        """
        self.llm = llm
        self.browser_config = browser_config
        self.mcp_server_config = mcp_server_config or {}

        # Agent state
        self.current_task_id = None
        self.runner = None
        self.stopped = False
        self.stop_event = None

        logger.info("SocialMediaAgent initialized")

    async def run(
        self,
        task: str,
        platforms: list = None,
        task_id: Optional[str] = None,
        save_dir: str = "./tmp/social_media",
        max_steps: int = 50,
    ) -> Dict[str, Any]:
        """
        Run a social media task.

        Args:
            task: The social media task to perform
            platforms: List of platforms to target (e.g., ['twitter', 'linkedin'])
            task_id: Optional task ID for resuming
            save_dir: Directory to save results
            max_steps: Maximum steps for browser agent

        Returns:
            Dict with task results
        """
        if self.runner and not self.runner.done():
            logger.warning(
                "Agent is already running. Please stop the current task first."
            )
            return {
                "status": "error",
                "message": "Agent already running.",
                "task_id": self.current_task_id,
            }

        # Generate task ID
        self.current_task_id = task_id or str(uuid.uuid4())
        self.stop_event = asyncio.Event()
        self.stopped = False

        logger.info(f"Starting social media task: {task}")
        logger.info(f"Target platforms: {platforms or ['all']}")
        logger.info(f"Task ID: {self.current_task_id}")

        # Initialize browser variable for cleanup
        browser = None

        try:
            # Create browser instance
            browser = await self._create_browser()
            context = await self._create_context(browser)
            controller = CustomController()

            # Create specialized system prompt for social media tasks
            social_media_prompt = self._create_social_media_prompt(task, platforms)

            # Create browser agent with social media specialization
            browser_agent = BrowserUseAgent(
                task=social_media_prompt,
                llm=self.llm,
                browser=browser,
                browser_context=context,
                controller=controller,
                source="social_media_agent",
            )

            # Run the browser agent
            logger.info("Executing social media task...")
            result = await browser_agent.run(max_steps=max_steps)

            # Process results
            final_result = result.final_result()

            # Save results
            await self._save_results(final_result, save_dir)

            logger.info(f"Social media task completed: {self.current_task_id}")

            return {
                "status": "completed",
                "task_id": self.current_task_id,
                "result": final_result,
                "platforms": platforms,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in social media task: {e}")
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

    def _create_social_media_prompt(self, task: str, platforms: list) -> str:
        """Create a specialized prompt for social media tasks."""
        platform_instructions = ""
        if platforms:
            platform_instructions = (
                f"\nFocus specifically on these platforms: {', '.join(platforms)}"
            )

        return f"""
        Social Media Task: {task}
        {platform_instructions}

        You are a social media management specialist. Your capabilities include:
        - Creating and posting content
        - Monitoring engagement and mentions
        - Analyzing social media metrics
        - Managing multiple social media accounts
        - Scheduling posts for optimal timing

        Guidelines:
        1. Always respect platform terms of service
        2. Use appropriate hashtags and mentions
        3. Maintain brand voice and consistency
        4. Monitor for engagement opportunities
        5. Take screenshots of important metrics or posts

        Execute the task step by step, providing detailed feedback on each action.
        """

    async def _create_browser(self) -> CustomBrowser:
        """Create browser instance with social media optimizations."""
        extra_args = []

        # Add social media specific browser args
        extra_args.extend(
            [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
            ]
        )

        browser = CustomBrowser(
            config=BrowserConfig(
                headless=self.browser_config.get("headless", False),
                disable_security=self.browser_config.get("disable_security", False),
                browser_binary_path=self.browser_config.get("browser_binary_path"),
                extra_browser_args=extra_args,
                new_context_config=BrowserContextConfig(
                    window_width=self.browser_config.get("window_width", 1280),
                    window_height=self.browser_config.get("window_height", 1100),
                ),
            )
        )
        return browser

    async def _create_context(self, browser):
        """Create browser context for social media tasks."""
        context_config = BrowserContextConfig(
            save_downloads_path="./tmp/social_media/downloads",
            window_height=self.browser_config.get("window_height", 1100),
            window_width=self.browser_config.get("window_width", 1280),
            force_new_context=True,
        )
        return await browser.new_context(config=context_config)

    async def _save_results(self, result: str, save_dir: str):
        """Save social media task results."""

        os.makedirs(save_dir, exist_ok=True)

        result_file = os.path.join(save_dir, f"{self.current_task_id}_result.json")

        result_data = {
            "task_id": self.current_task_id,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "status": "completed",
        }

        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"Results saved to: {result_file}")

    async def stop(self):
        """Stop the currently running social media task."""
        if not self.current_task_id or not self.stop_event:
            logger.info("No social media task is currently running.")
            return

        logger.info(f"Stop requested for social media task: {self.current_task_id}")
        self.stop_event.set()
        self.stopped = True

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "current_task_id": self.current_task_id,
            "is_running": bool(self.runner and not self.runner.done()),
            "stopped": self.stopped,
        }
