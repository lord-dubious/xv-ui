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
        """
        Initializes a StealthBrowserContext with Patchright Chrome-specific stealth features.
        
        Creates a browser context optimized for anti-detection on Chrome/Chromium browsers using Patchright, with optional configuration and state.
        """
        super().__init__(browser=browser, config=config, state=state)
        logger.info(
            "🎭 StealthBrowserContext initialized with Patchright Chrome-only stealth features"
        )

    async def _setup_context_stealth(self, context: PatchrightBrowserContext) -> None:
        """
        Applies additional stealth configurations to a Patchright Chrome browser context.
        
        Injects a minimal initialization script to patch navigator properties and define a basic `window.chrome` object, enhancing anti-detection measures. Relies on Patchright's built-in stealth features and avoids custom HTTP header or user agent modifications.
        """
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

    async def _create_context(self, browser: Any) -> PatchrightBrowserContext:  # type: ignore[override]
        """
        Asynchronously applies Patchright Chrome-specific stealth measures to an existing persistent browser context and returns it.
        
        The provided `browser` parameter is assumed to be a persistent context (as per Patchright's requirements), so no new context is created. Stealth features are applied to enhance anti-detection capabilities for Chrome/Chromium browsers.
        
        Returns:
            The Patchright browser context with stealth optimizations applied.
        """
        logger.info(
            "🎭 Creating StealthBrowserContext with Patchright Chrome optimizations..."
        )

        # Patchright Best Practice: Use no_viewport=True and no custom user_agent
        # The browser should already be launched with launch_persistent_context

        # For persistent context, we don't create a new context - it's already created
        # Just return the existing context from the browser
        context = browser  # With launch_persistent_context, browser IS the context

        # Apply Patchright-specific stealth measures
        await self._setup_context_stealth(context)

        logger.info(
            "✅ StealthBrowserContext created with Patchright Chrome stealth capabilities"
        )
        return context

    def get_context_info(self) -> dict:
        """
        Returns a dictionary describing the characteristics and configuration of the Patchright-based StealthBrowserContext.
        
        The returned information includes context type, engine, supported browsers, stealth features, detection bypass targets, configuration parameters, and known limitations.
        """
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