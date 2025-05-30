"""
StealthBrowser - Patchright-based browser for enhanced stealth capabilities.

This module provides a Patchright-based browser implementation that offers
enhanced anti-detection capabilities compared to standard Playwright.
"""

import logging
import socket
from typing import TYPE_CHECKING, Optional

from browser_use.browser.browser import IN_DOCKER, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from browser_use.utils import time_execution_async

# Import Patchright instead of Playwright
from patchright.async_api import Browser as PatchrightBrowser
from patchright.async_api import Playwright as PatchrightPlaywright
from patchright.async_api import async_playwright

# Import proxy manager (commented out for this branch)
# from src.proxy.proxy_manager import ProxyManager

if TYPE_CHECKING:
    from .stealth_context import StealthBrowserContext

logger = logging.getLogger(__name__)


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

        # Initialize Patchright-specific attributes with proper types
        self.playwright: Optional[PatchrightPlaywright] = None
        self.browser: Optional[PatchrightBrowser] = None

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

        # Patchright Best Practice: no_viewport=True handles window sizing automatically
        # No need for manual screen size or window positioning with persistent context

        # Patchright Best Practice: Minimal args, let Patchright handle stealth automatically
        chrome_args = [
            "--disable-dev-shm-usage",  # Memory optimization (safe)
            "--no-first-run",  # Skip first run setup (safe)
            "--no-default-browser-check",  # Skip default browser check (safe)
        ]

        # Add remote debugging port if needed (check if port is available)
        if (
            hasattr(self.config, "chrome_remote_debugging_port")
            and self.config.chrome_remote_debugging_port
        ):
            chrome_args.append(
                f"--remote-debugging-port={self.config.chrome_remote_debugging_port}"
            )

        # Add Docker args only if in Docker (minimal necessary)
        if IN_DOCKER:
            chrome_args.extend(
                [
                    "--no-sandbox",  # Required for Docker
                    "--disable-setuid-sandbox",  # Required for Docker
                ]
            )

        # Add user's extra args (use with caution - may interfere with stealth)
        if (
            hasattr(self.config, "extra_browser_args")
            and self.config.extra_browser_args
        ):
            chrome_args.extend(self.config.extra_browser_args)

        # Check if chrome remote debugging port is already taken
        if (
            hasattr(self.config, "chrome_remote_debugging_port")
            and self.config.chrome_remote_debugging_port
        ):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if (
                    s.connect_ex(
                        ("localhost", self.config.chrome_remote_debugging_port)
                    )
                    == 0
                ):
                    chrome_args = [
                        arg
                        for arg in chrome_args
                        if not arg.startswith("--remote-debugging-port=")
                    ]

        browser_class = getattr(playwright, self.config.browser_class)
        args = {
            "chromium": list(chrome_args),
            "firefox": ["-no-remote"] + list(self.config.extra_browser_args or []),
            "webkit": ["--no-startup-window"]
            + list(self.config.extra_browser_args or []),
        }

        logger.info(
            f"🎭 Launching Patchright browser with {len(chrome_args)} stealth arguments"
        )

        # Patchright Best Practice: Use launch_persistent_context for maximum stealth
        launch_options = {
            "channel": "chrome",  # Use Google Chrome (not chromium) for best stealth
            "headless": self.config.headless,
            "no_viewport": True,  # Critical for stealth
            "args": args[self.config.browser_class],
            "handle_sigterm": False,
            "handle_sigint": False,
            "user_data_dir": "./tmp/xagent/chrome_profile",  # Persistent context for stealth
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

        # Use launch_persistent_context for maximum stealth (Patchright best practice)
        browser = await browser_class.launch_persistent_context(**launch_options)

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

        # Start Patchright playwright instance
        patchright_playwright = await async_playwright().start()
        self.playwright = patchright_playwright

        if self.config.browser_binary_path or (
            not self.config.wss_url and not self.config.cdp_url
        ):
            # Use builtin browser
            self.browser = await self._setup_builtin_browser(patchright_playwright)
        else:
            # Connect to external browser
            self.browser = await self._setup_external_browser(patchright_playwright)

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
        try:
            import patchright

            version = getattr(patchright, "__version__", "unknown")
        except Exception:
            version = "unknown"

        return {
            "engine": "Patchright",
            "version": version,
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
