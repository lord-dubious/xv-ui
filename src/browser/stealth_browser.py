"""
StealthBrowser - Patchright-based browser for enhanced stealth capabilities.

This module provides a Patchright-based browser implementation that offers
enhanced anti-detection capabilities compared to standard Playwright.
"""

import logging
import socket
from typing import Optional

from browser_use.browser.browser import IN_DOCKER, Browser, BrowserConfig
from browser_use.browser.chrome import (
    CHROME_ARGS,
    CHROME_DETERMINISTIC_RENDERING_ARGS,
    CHROME_DISABLE_SECURITY_ARGS,
    CHROME_DOCKER_ARGS,
    CHROME_HEADLESS_ARGS,
)
from browser_use.browser.context import BrowserContextConfig
from browser_use.browser.utils.screen_resolution import (
    get_screen_resolution,
    get_window_adjustments,
)
from browser_use.utils import time_execution_async

# Import Patchright instead of Playwright
from patchright.async_api import Browser as PatchrightBrowser
from patchright.async_api import Playwright as PatchrightPlaywright
from patchright.async_api import async_playwright

# Import proxy manager (commented out for this branch)
# from src.proxy.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

# Import StealthBrowserContext (avoid circular import)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .stealth_context import StealthBrowserContext


class StealthBrowser(Browser):
    """
    StealthBrowser - Enhanced browser using Patchright for stealth capabilities.

    Features:
    - Anti-detection patches
    - Enhanced stealth mode
    - Closed shadow root interaction
    - Bypasses common bot detection systems
    """

    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        proxy_manager: Optional[object] = None,  # Commented out for this branch
    ):
        """Initialize StealthBrowser with Patchright stealth capabilities."""
        super().__init__(config)
        self.proxy_manager = None  # Commented out for this branch

        logger.info(
            "🎭 StealthBrowser initialized with Patchright stealth capabilities"
        )

    async def new_context(
        self, config: BrowserContextConfig | None = None
    ) -> "StealthBrowserContext":
        """Create a browser context using StealthBrowserContext."""
        from .stealth_context import StealthBrowserContext

        browser_config = self.config.model_dump() if self.config else {}
        context_config = config.model_dump() if config else {}
        merged_config = {**browser_config, **context_config}
        return StealthBrowserContext(
            config=BrowserContextConfig(**merged_config), browser=self
        )

    async def _setup_builtin_browser(
        self, playwright: PatchrightPlaywright
    ) -> PatchrightBrowser:
        """Sets up and returns a Patchright Browser instance with enhanced stealth measures."""
        # Note: For Patchright, we can use browser_binary_path to specify Chrome location

        # Use the configured window size from new_context_config if available
        if (
            not self.config.headless
            and hasattr(self.config, "new_context_config")
            and hasattr(self.config.new_context_config, "window_width")
            and hasattr(self.config.new_context_config, "window_height")
        ):
            screen_size = {
                "width": self.config.new_context_config.window_width,
                "height": self.config.new_context_config.window_height,
            }
            offset_x, offset_y = get_window_adjustments()
        elif self.config.headless:
            screen_size = {"width": 1920, "height": 1080}
            offset_x, offset_y = 0, 0
        else:
            screen_size = get_screen_resolution()
            offset_x, offset_y = get_window_adjustments()

        # Enhanced Chrome args for Patchright stealth
        chrome_args = {
            f"--remote-debugging-port={self.config.chrome_remote_debugging_port}",
            *CHROME_ARGS,
            *(CHROME_DOCKER_ARGS if IN_DOCKER else []),
            *(CHROME_HEADLESS_ARGS if self.config.headless else []),
            *(CHROME_DISABLE_SECURITY_ARGS if self.config.disable_security else []),
            *(
                CHROME_DETERMINISTIC_RENDERING_ARGS
                if self.config.deterministic_rendering
                else []
            ),
            f"--window-position={offset_x},{offset_y}",
            f"--window-size={screen_size['width']},{screen_size['height']}",
            # Additional args (Patchright already handles most stealth args automatically)
            "--disable-dev-shm-usage",  # Memory optimization
            "--no-first-run",  # Skip first run setup
            "--no-default-browser-check",  # Skip default browser check
            *self.config.extra_browser_args,
        }

        # Check if chrome remote debugging port is already taken
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if (
                s.connect_ex(("localhost", self.config.chrome_remote_debugging_port))
                == 0
            ):
                chrome_args.remove(
                    f"--remote-debugging-port={self.config.chrome_remote_debugging_port}"
                )

        browser_class = getattr(playwright, self.config.browser_class)
        args = {
            "chromium": list(chrome_args),
            "firefox": [
                *{
                    "-no-remote",
                    *self.config.extra_browser_args,
                }
            ],
            "webkit": [
                *{
                    "--no-startup-window",
                    *self.config.extra_browser_args,
                }
            ],
        }

        logger.info(
            f"🎭 Launching Patchright browser with {len(chrome_args)} stealth arguments"
        )

        # Launch with or without custom executable path
        launch_options = {
            "channel": "chromium",
            "headless": self.config.headless,
            "args": args[self.config.browser_class],
            "handle_sigterm": False,
            "handle_sigint": False,
        }

        # Add proxy configuration (commented out for this branch)
        # if self.proxy_manager:
        #     proxy_config = self.proxy_manager.get_proxy_for_browser()
        #     if proxy_config:
        #         launch_options["proxy"] = proxy_config
        #         logger.info(f"🌐 Using proxy from ProxyManager: {proxy_config['server']}")
        # elif self.config.proxy:
        #     launch_options["proxy"] = self.config.proxy.model_dump()
        #     logger.info("🌐 Using proxy from browser config")

        # Add executable path if specified
        if self.config.browser_binary_path:
            launch_options["executable_path"] = self.config.browser_binary_path

        browser = await browser_class.launch(**launch_options)

        logger.info(
            "🎭 Patchright browser launched successfully with stealth capabilities"
        )
        return browser

    async def _setup_external_browser(
        self, playwright: PatchrightPlaywright
    ) -> PatchrightBrowser:
        """Connect to external browser using Patchright."""
        logger.info("🎭 Connecting to external browser via Patchright")

        if self.config.wss_url:
            browser = await playwright.chromium.connect_over_cdp(self.config.wss_url)
        elif self.config.cdp_url:
            browser = await playwright.chromium.connect_over_cdp(self.config.cdp_url)
        else:
            raise ValueError(
                "Either wss_url or cdp_url must be provided for external browser connection"
            )

        logger.info("🎭 Successfully connected to external browser via Patchright")
        return browser

    @time_execution_async("--browser-startup")
    async def start(self) -> None:
        """Start the Patchright browser."""
        logger.info("🎭 Starting XBrowser with Patchright...")

        self.playwright = await async_playwright().start()

        if self.config.browser_binary_path or (
            not self.config.wss_url and not self.config.cdp_url
        ):
            # Use builtin browser
            self.browser = await self._setup_builtin_browser(self.playwright)
        else:
            # Connect to external browser
            self.browser = await self._setup_external_browser(self.playwright)

        logger.info(
            "🎭 XBrowser started successfully with enhanced stealth capabilities"
        )

    async def close(self) -> None:
        """Close the Patchright browser and cleanup."""
        logger.info("🎭 Closing XBrowser...")

        if hasattr(self, "browser") and self.browser:
            await self.browser.close()

        if hasattr(self, "playwright") and self.playwright:
            await self.playwright.stop()

        logger.info("🎭 XBrowser closed successfully")

    def get_stealth_info(self) -> dict:
        """Get information about Patchright stealth capabilities."""
        return {
            "engine": "Patchright",
            "version": "1.52.3",
            "stealth_features": [
                "Runtime.enable leak patched",
                "Console.enable leak patched",
                "Command flags optimized",
                "AutomationControlled disabled",
                "Closed shadow root support",
                "Enhanced anti-detection",
            ],
            "supported_detections": [
                "Cloudflare",
                "Kasada",
                "Akamai",
                "Shape/F5",
                "Bet365",
                "Datadome",
                "Fingerprint.com",
                "CreepJS",
                "Sannysoft",
                "Incolumitas",
            ],
        }
