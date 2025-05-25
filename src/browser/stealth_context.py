"""
StealthBrowserContext - Patchright-based browser context for enhanced stealth.

This module provides a Patchright-based browser context implementation
with enhanced anti-detection capabilities using Patchright's Chrome-only optimizations.
"""

import logging
from typing import Optional

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
            # Patchright-optimized stealth script (minimal since Patchright handles most)
            # Note: Console is disabled in Patchright, so we avoid console.log
            await context.add_init_script("""
                // Minimal stealth enhancements (Patchright handles the heavy lifting)

                // Enhanced navigator properties (Chrome-specific)
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });

                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });

                // Enhanced screen properties for Chrome
                Object.defineProperty(screen, 'colorDepth', {
                    get: () => 24,
                });

                // Chrome-specific WebGL fingerprint resistance
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel(R) Iris(TM) Graphics 6100';
                    }
                    return getParameter.call(this, parameter);
                };

                // Enhanced Chrome runtime spoofing
                if (!window.chrome) {
                    window.chrome = {};
                }
                window.chrome.runtime = {
                    onConnect: null,
                    onMessage: null,
                };
            """)

            # Chrome-optimized headers for maximum stealth
            await context.set_extra_http_headers(
                {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-User": "?1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                }
            )

            logger.info(
                "✅ Patchright Chrome stealth configurations applied successfully"
            )

        except Exception as e:
            logger.warning(f"⚠️ Some Patchright stealth configurations failed: {e}")

    async def _create_context(self, browser) -> PatchrightBrowserContext:
        """Create a new Patchright browser context with Chrome-optimized stealth."""
        logger.info(
            "🎭 Creating StealthBrowserContext with Patchright Chrome optimizations..."
        )

        # Chrome-optimized viewport
        viewport = {
            "width": self.config.window_width,
            "height": self.config.window_height,
        }

        # Chrome-realistic user agent (Patchright optimized)
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Create the Patchright context with minimal options for compatibility
        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            java_script_enabled=True,
            accept_downloads=True,
            ignore_https_errors=True,
            bypass_csp=True,
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
                "Runtime.enable leak patched",
                "Console.enable leak patched",
                "Command flags optimized",
                "webdriver property hidden",
                "chrome runtime spoofed",
                "plugins spoofed",
                "enhanced headers",
                "fingerprint resistance",
                "closed shadow root support",
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
                "Chrome/Chromium only",
                "Console API disabled for stealth",
                "Init scripts use Routes (minimal timing attack risk)",
            ],
        }
