"""
XAgent Tab - GUI interface for XAgent with Patchright stealth and proxy support.

This module provides the Gradio interface for configuring and running XAgent
with SOCKS5 proxy rotation and enhanced stealth capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import gradio as gr

from src.agent.xagent.xagent import XAgent
from src.proxy.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class XAgentTab:
    """XAgent tab with stealth and proxy configuration."""

    def __init__(self, llm, browser_config: Dict[str, Any]):
        """Initialize XAgent tab."""
        self.llm = llm
        self.browser_config = browser_config
        self.xagent: Optional[XAgent] = None
        self.proxy_manager: Optional[ProxyManager] = None
        
        logger.info("🎭 XAgent tab initialized")

    def create_tab(self) -> gr.Tab:
        """Create the XAgent tab interface."""
        with gr.Tab("🎭 XAgent (Stealth + Proxy)", id="xagent_tab") as tab:
            gr.Markdown("""
            # 🎭 XAgent - Advanced Stealth Agent
            
            **Enhanced stealth capabilities with Patchright and SOCKS5 proxy rotation**
            
            ✨ **Features:**
            - 🎭 **Patchright Stealth**: Runtime.enable patched, Console.enable patched
            - 🌐 **SOCKS5 Proxies**: Rotating IP addresses with automatic failover
            - 🛡️ **Anti-Detection**: Bypasses Cloudflare, Kasada, Datadome, and more
            - 🔒 **Connection Isolation**: All traffic routed through proxy
            - 🎯 **Chrome Optimized**: Patchright works best with Chrome/Chromium
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Task Configuration
                    with gr.Group():
                        gr.Markdown("### 📋 Task Configuration")
                        
                        task_input = gr.Textbox(
                            label="Task Description",
                            placeholder="Enter your stealth automation task...",
                            lines=3,
                            info="Describe what you want XAgent to do with maximum stealth"
                        )
                        
                        with gr.Row():
                            max_steps = gr.Number(
                                label="Max Steps",
                                value=50,
                                minimum=1,
                                maximum=200,
                                info="Maximum number of automation steps"
                            )
                            
                            test_proxies_checkbox = gr.Checkbox(
                                label="Test Proxies Before Start",
                                value=True,
                                info="Validate proxy connectivity before running task"
                            )
                    
                    # Proxy Configuration
                    with gr.Group():
                        gr.Markdown("### 🌐 SOCKS5 Proxy Configuration")
                        
                        proxy_list_input = gr.Textbox(
                            label="Proxy List",
                            placeholder="socks5://user:pass@host:port\nsocks5://user2:pass2@host2:port2",
                            lines=5,
                            info="One proxy per line. Format: socks5://username:password@host:port"
                        )
                        
                        with gr.Row():
                            rotation_mode = gr.Dropdown(
                                label="Rotation Mode",
                                choices=["round_robin", "random"],
                                value="round_robin",
                                info="How to rotate between proxies"
                            )
                            
                            proxy_test_btn = gr.Button(
                                "🧪 Test Proxies",
                                variant="secondary",
                                size="sm"
                            )
                    
                    # Control Buttons
                    with gr.Row():
                        start_btn = gr.Button(
                            "🚀 Start XAgent",
                            variant="primary",
                            size="lg"
                        )
                        
                        stop_btn = gr.Button(
                            "🛑 Stop XAgent",
                            variant="stop",
                            size="lg"
                        )
                        
                        rotate_proxy_btn = gr.Button(
                            "🔄 Rotate Proxy",
                            variant="secondary",
                            size="sm"
                        )

                with gr.Column(scale=1):
                    # Status and Results
                    with gr.Group():
                        gr.Markdown("### 📊 Status")
                        
                        status_display = gr.JSON(
                            label="XAgent Status",
                            value={"status": "idle", "stealth_engine": "Patchright"},
                        )
                        
                        proxy_status_display = gr.JSON(
                            label="Proxy Status",
                            value={"proxy_enabled": False},
                        )
                    
                    # Results
                    with gr.Group():
                        gr.Markdown("### 📋 Results")
                        
                        results_display = gr.Textbox(
                            label="Task Results",
                            lines=10,
                            max_lines=20,
                            interactive=False,
                            show_copy_button=True
                        )
            
            # Proxy Test Results
            with gr.Row():
                proxy_test_results = gr.JSON(
                    label="🧪 Proxy Test Results",
                    visible=False
                )

            # Event handlers
            start_btn.click(
                fn=self._start_xagent,
                inputs=[task_input, proxy_list_input, rotation_mode, max_steps, test_proxies_checkbox],
                outputs=[results_display, status_display, proxy_status_display],
                show_progress=True
            )
            
            stop_btn.click(
                fn=self._stop_xagent,
                outputs=[results_display, status_display],
                show_progress=True
            )
            
            proxy_test_btn.click(
                fn=self._test_proxies,
                inputs=[proxy_list_input, rotation_mode],
                outputs=[proxy_test_results],
                show_progress=True
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[proxy_test_results]
            )
            
            rotate_proxy_btn.click(
                fn=self._rotate_proxy,
                outputs=[proxy_status_display, results_display],
                show_progress=True
            )
            
            # Auto-refresh status every 5 seconds
            def refresh_status():
                if self.xagent:
                    return self.xagent.get_status()
                return {"status": "idle", "stealth_engine": "Patchright"}
            
            # Set up periodic status updates
            status_timer = gr.Timer(5.0)  # 5 second intervals
            status_timer.tick(
                fn=refresh_status,
                outputs=[status_display]
            )

        return tab

    async def _start_xagent(
        self,
        task: str,
        proxy_list_str: str,
        rotation_mode: str,
        max_steps: int,
        test_proxies: bool
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """Start XAgent with the given configuration."""
        try:
            if not task.strip():
                return "❌ Error: Task description is required", {}, {}
            
            # Parse proxy list
            proxy_list = []
            if proxy_list_str.strip():
                proxy_list = [
                    line.strip() 
                    for line in proxy_list_str.strip().split('\n') 
                    if line.strip()
                ]
            
            # Create XAgent
            self.xagent = XAgent(
                llm=self.llm,
                browser_config=self.browser_config,
                proxy_list=proxy_list if proxy_list else None,
                proxy_rotation_mode=rotation_mode,
            )
            
            # Run task
            result = await self.xagent.run(
                task=task,
                max_steps=int(max_steps),
                test_proxies=test_proxies
            )
            
            # Format results
            if result["status"] == "completed":
                results_text = f"✅ Task completed successfully!\n\n{result['result']}"
            else:
                results_text = f"❌ Task failed: {result.get('error', 'Unknown error')}"
            
            status = self.xagent.get_status()
            proxy_status = status.get("proxy_status", {})
            
            return results_text, status, proxy_status
            
        except Exception as e:
            logger.error(f"Error starting XAgent: {e}")
            return f"❌ Error starting XAgent: {str(e)}", {}, {}

    async def _stop_xagent(self) -> Tuple[str, Dict[str, Any]]:
        """Stop the running XAgent."""
        try:
            if self.xagent:
                await self.xagent.stop()
                return "🛑 XAgent stopped", {"status": "stopped", "stealth_engine": "Patchright"}
            else:
                return "ℹ️ No XAgent running", {"status": "idle", "stealth_engine": "Patchright"}
        except Exception as e:
            logger.error(f"Error stopping XAgent: {e}")
            return f"❌ Error stopping XAgent: {str(e)}", {}

    async def _test_proxies(
        self, 
        proxy_list_str: str, 
        rotation_mode: str
    ) -> Dict[str, Any]:
        """Test the provided proxy list."""
        try:
            if not proxy_list_str.strip():
                return {"error": "No proxies provided"}
            
            # Parse proxy list
            proxy_list = [
                line.strip() 
                for line in proxy_list_str.strip().split('\n') 
                if line.strip()
            ]
            
            if not proxy_list:
                return {"error": "No valid proxies found"}
            
            # Create temporary proxy manager
            temp_proxy_manager = ProxyManager(proxy_list, rotation_mode)
            
            # Test all proxies
            report = await temp_proxy_manager.test_all_proxies()
            
            return {
                "status": "completed",
                "total_proxies": report["total_proxies"],
                "working_proxies": report["working_proxies"],
                "success_rate": f"{report['success_rate']:.1f}%",
                "proxies": report["proxies"]
            }
            
        except Exception as e:
            logger.error(f"Error testing proxies: {e}")
            return {"error": str(e)}

    async def _rotate_proxy(self) -> Tuple[Dict[str, Any], str]:
        """Rotate to the next proxy."""
        try:
            if not self.xagent:
                return {}, "ℹ️ No XAgent running"
            
            result = await self.xagent.rotate_proxy()
            
            if result["status"] == "success":
                message = f"🔄 Rotated proxy: {result['old_proxy']} → {result['new_proxy']}"
                status = self.xagent.get_status()
                return status.get("proxy_status", {}), message
            else:
                return {}, f"❌ {result['message']}"
                
        except Exception as e:
            logger.error(f"Error rotating proxy: {e}")
            return {}, f"❌ Error rotating proxy: {str(e)}"
