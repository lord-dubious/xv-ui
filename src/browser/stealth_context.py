"""
StealthBrowserContext - Patchright-based browser context for enhanced stealth.

This module provides a Patchright-based browser context implementation
with enhanced anti-detection capabilities using Patchright's Chrome-only optimizations.
"""

import logging
from typing import Any, Optional

from browser_use.browser.browser import Browser
from browser_use.browser.context import (
    BrowserContext,
    BrowserContextConfig,
    BrowserContextState,
)

# Import Patchright types (Chrome/Chromium only)
from patchright.async_api import BrowserContext as PatchrightBrowserContext

logger = logging.getLogger(__name__)


class StealthBrowserContext(BrowserContext):
    """
    StealthBrowserContext - Enhanced browser context using Patchright.

    Features (Chrome/Chromium only):
    - Runtime.enable leak patched (uses isolated ExecutionContexts)
    - Console.enable leak patched (console disabled for stealth)
    - Command flags automatically optimized
    - Closed shadow root interaction support
    - Advanced fingerprint resistance
    - Bypasses major bot detection systems
    """

    def __init__(
        self,
        browser: "Browser",
        config: BrowserContextConfig | None = None,
        state: Optional[BrowserContextState] = None,
    ):
        """Initialize StealthBrowserContext with Patchright Chrome optimizations."""
        super().__init__(browser=browser, config=config, state=state)
        logger.info(
            "🎭 StealthBrowserContext initialized with Patchright Chrome-only stealth features"
        )

    async def _setup_context_stealth(self, context: PatchrightBrowserContext) -> None:
        """Setup additional stealth measures optimized for Patchright Chrome."""
        logger.info("🎭 Applying Patchright Chrome stealth configurations...")

        try:
            # Minimal stealth script (Patchright handles most automatically)
            # Note: Console is disabled in Patchright for stealth
            await context.add_init_script("""
                // Minimal enhancements - Patchright already patches the major leaks

                // Basic navigator enhancements (optional since Patchright handles webdriver)
                if (!navigator.hardwareConcurrency || navigator.hardwareConcurrency < 4) {
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8,
                        configurable: true
                    });
                }

                // Basic chrome object (Patchright may handle this)
                if (!window.chrome) {
                    window.chrome = {
                        runtime: {
                            onConnect: null,
                            onMessage: null
                        }
                    };
                }
            """)

            # Patchright Best Practice: do NOT add custom browser headers or user_agent
            # Patchright handles headers automatically for maximum stealth
            # await context.set_extra_http_headers({...})  # REMOVED per best practices

            logger.info(
                "✅ Patchright Chrome stealth configurations applied successfully"
            )

        except Exception as e:
            logger.warning(f"⚠️ Some Patchright stealth configurations failed: {e}")

    async def _create_context(
        self, browser_or_context: Any
    ) -> PatchrightBrowserContext:  # type: ignore[override]
        """
        Create or configure a Patchright browser context with Chrome-optimized stealth.

        Note: When using launch_persistent_context, the browser object IS the context,
        so this method just applies stealth configurations to the existing context.

        Args:
            browser_or_context: The browser/context object from launch_persistent_context

        Returns:
            The configured context
        """
        logger.info(
            "🎭 Creating StealthBrowserContext with Patchright Chrome optimizations..."
        )

        # Patchright Best Practice: Use no_viewport=True and no custom user_agent
        # The browser should already be launched with launch_persistent_context

        # For persistent context, we don't create a new context - it's already created
        # Just return the existing context from the browser
        context = (
            browser_or_context  # With launch_persistent_context, browser IS the context
        )

        # Apply Patchright-specific stealth measures
        await self._setup_context_stealth(context)

        logger.info(
            "✅ StealthBrowserContext created with Patchright Chrome stealth capabilities"
        )
        return context

    def get_context_info(self) -> dict:
        """Get information about the StealthBrowserContext with Patchright details."""
        return {
            "type": "StealthBrowserContext",
            "engine": "Patchright",
            "browser_support": "Chrome/Chromium only",
            "stealth_features": [
                "Runtime.enable leak patched (isolated ExecutionContexts)",
                "Console.enable leak patched (console disabled)",
                "Command flags optimized (--enable-automation removed)",
                "AutomationControlled disabled",
                "Closed shadow root support",
                "Persistent context with no_viewport",
                "Google Chrome channel (not Chromium)",
                "No custom headers/user_agent (Patchright handles)",
            ],
            "detection_bypass": [
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
                "IPHey",
                "Browserscan",
                "Pixelscan",
            ],
            "config": {
                "window_width": self.config.window_width,
                "window_height": self.config.window_height,
                "recording_enabled": bool(self.config.save_recording_path),
                "trace_enabled": bool(self.config.trace_path),
            },
            "limitations": [
                "Chrome/Chromium only (Firefox/Webkit not supported)",
                "Console API disabled for stealth",
                "Init scripts use Routes (minimal timing attack risk)",
                "Best with Google Chrome channel (not Chromium)",
                "Requires persistent context for maximum stealth",
            ],
        }
