"""
Proxy Manager for SOCKS5 proxy rotation with proxystr.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional

from proxystr import Proxy, check_proxies

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages SOCKS5 proxy rotation using proxystr."""

    def __init__(self, proxy_list: List[str], rotation_mode: str = "round_robin"):
        """Initialize ProxyManager with proxystr."""
        self.proxy_list = proxy_list
        self.rotation_mode = rotation_mode
        self.proxies: List[Proxy] = []
        self.working_proxies: List[Proxy] = []
        self.current_index = 0
        self.last_rotation = 0.0
        self.rotation_interval = 300.0  # 5 minutes
        
        # Parse and create Proxy objects
        self._parse_proxies()
        
        logger.info(f"🔄 ProxyManager initialized with {len(self.proxies)} proxies")

    def _parse_proxies(self) -> None:
        """Parse proxy URLs into proxystr Proxy objects."""
        for proxy_url in self.proxy_list:
            try:
                # Create Proxy object using proxystr
                proxy = Proxy(proxy_url)
                self.proxies.append(proxy)
                self.working_proxies.append(proxy)  # Assume working initially
                
                logger.info(f"✅ Added proxy: {proxy.host}:{proxy.port} ({proxy.protocol})")
                
            except Exception as e:
                logger.error(f"❌ Failed to parse proxy URL {proxy_url}: {e}")

    def get_current_proxy(self) -> Optional[Proxy]:
        """Get the current active proxy."""
        if not self.working_proxies:
            logger.error("❌ No working proxies available!")
            return None
        
        # Check if rotation is needed
        if (time.time() - self.last_rotation) > self.rotation_interval:
            self._rotate_proxy()
        
        if self.rotation_mode == "random":
            return random.choice(self.working_proxies)
        else:
            # Round robin
            if self.current_index >= len(self.working_proxies):
                self.current_index = 0
            return self.working_proxies[self.current_index]

    def _rotate_proxy(self) -> None:
        """Rotate to the next proxy."""
        if len(self.working_proxies) <= 1:
            return
        
        if self.rotation_mode == "round_robin":
            self.current_index = (self.current_index + 1) % len(self.working_proxies)
        
        self.last_rotation = time.time()
        current = self.get_current_proxy()
        if current:
            logger.info(f"🔄 Rotated to proxy: {current.host}:{current.port}")

    def force_rotate(self) -> Optional[Proxy]:
        """Force rotation to next proxy."""
        self._rotate_proxy()
        return self.get_current_proxy()

    async def test_proxy(self, proxy: Proxy) -> bool:
        """Test if a proxy is working using proxystr's built-in check."""
        try:
            logger.info(f"🧪 Testing proxy: {proxy.host}:{proxy.port}")
            
            # Use proxystr's built-in async check method
            is_working = await proxy.acheck()
            
            if is_working:
                logger.info(f"✅ Proxy {proxy.host}:{proxy.port} is working")
                return True
            else:
                logger.error(f"❌ Proxy {proxy.host}:{proxy.port} is not working")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing proxy {proxy.host}:{proxy.port}: {e}")
            return False

    async def test_all_proxies(self) -> Dict[str, Any]:
        """Test all proxies and return status report using proxystr."""
        logger.info("🧪 Testing all proxies with proxystr...")
        
        try:
            # Use proxystr's check_proxies function for efficient batch testing
            good_proxies, bad_proxies = check_proxies(self.proxies)
            
            # Update working proxies list
            self.working_proxies = good_proxies
            
            working_count = len(good_proxies)
            total_count = len(self.proxies)
            
            report = {
                "total_proxies": total_count,
                "working_proxies": working_count,
                "failed_proxies": len(bad_proxies),
                "success_rate": (working_count / total_count * 100) if total_count > 0 else 0,
                "working_proxy_list": [
                    {
                        "host": p.host,
                        "port": p.port,
                        "protocol": p.protocol,
                        "url": p.url,
                    }
                    for p in good_proxies
                ],
                "failed_proxy_list": [
                    {
                        "host": p.host,
                        "port": p.port,
                        "protocol": p.protocol,
                        "url": p.url,
                    }
                    for p in bad_proxies
                ]
            }
            
            logger.info(f"📊 Proxy test complete: {working_count}/{total_count} working ({report['success_rate']:.1f}%)")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error testing proxies: {e}")
            return {
                "total_proxies": len(self.proxies),
                "working_proxies": 0,
                "failed_proxies": len(self.proxies),
                "success_rate": 0,
                "error": str(e)
            }

    def get_proxy_for_browser(self) -> Optional[Dict[str, Any]]:
        """Get proxy configuration for Playwright/Patchright browser use."""
        proxy = self.get_current_proxy()
        if not proxy:
            return None
        
        # Use proxystr's playwright property for browser integration
        proxy_config = proxy.playwright
        
        logger.info(f"🌐 Using proxy for browser: {proxy.host}:{proxy.port} ({proxy.protocol})")
        return proxy_config

    def get_status(self) -> Dict[str, Any]:
        """Get current proxy manager status."""
        current = self.get_current_proxy()
        
        return {
            "total_proxies": len(self.proxies),
            "working_proxies": len(self.working_proxies),
            "current_proxy": f"{current.host}:{current.port}" if current else None,
            "current_proxy_protocol": current.protocol if current else None,
            "rotation_mode": self.rotation_mode,
            "last_rotation": self.last_rotation,
            "next_rotation": self.last_rotation + self.rotation_interval,
        }

    def mark_proxy_failed(self, host: str, port: int) -> None:
        """Mark a specific proxy as failed and remove from working list."""
        for proxy in self.working_proxies[:]:  # Create a copy to iterate
            if proxy.host == host and proxy.port == port:
                self.working_proxies.remove(proxy)
                logger.warning(f"⚠️ Marked proxy {host}:{port} as failed and removed from working list")
                break

    def reset_proxy_errors(self) -> None:
        """Reset working proxies list to include all proxies."""
        self.working_proxies = self.proxies.copy()
        logger.info("🔄 Reset proxy errors - all proxies marked as working")
