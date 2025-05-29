"""
XAgent Loop Methods - Behavioral loop functionality for XAgent UI.

This module contains behavioral loop and scheduling methods for the XAgent interface,
separated for better code organization and maintainability.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

# Import gradio with fallback
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    logging.warning("Gradio not available. UI functionality will be limited.")

logger = logging.getLogger(__name__)


class XAgentLoopMethods:
    """Behavioral loop methods for XAgent tab."""
    
    def __init__(self, tab_instance):
        """Initialize with reference to the tab instance."""
        self.tab = tab_instance
        
    def _save_action_loops(self, profile_name: str, loops_json: str):
        """Save action loops configuration."""
        try:
            # Parse the JSON
            loops_data = json.loads(loops_json)
            
            if not isinstance(loops_data, list):
                return "❌ Error: Action loops must be a JSON array"
            
            # Validate loop structure
            for loop in loops_data:
                if not isinstance(loop, dict):
                    return "❌ Error: Each loop must be a JSON object"
                    
                required_fields = ["id", "actions"]
                for field in required_fields:
                    if field not in loop:
                        return f"❌ Error: Loop missing required field: {field}"
                        
                if not isinstance(loop["actions"], list):
                    return "❌ Error: Loop actions must be an array"
            
            # Initialize XAgent if needed
            if not self.tab.xagent:
                llm = asyncio.run(self.tab.methods._initialize_llm_from_settings())
                if llm:
                    from src.agent.xagent.xagent import XAgent
                    self.tab.xagent = XAgent(
                        llm=llm,
                        browser_config=self.tab.browser_config,
                        profile_name=profile_name,
                    )
            
            if self.tab.xagent:
                # Clear existing loops and add new ones
                self.tab.xagent.action_loops = []
                
                for loop_data in loops_data:
                    success = self.tab.xagent.add_action_loop(
                        loop_id=loop_data["id"],
                        actions=loop_data["actions"],
                        interval_seconds=loop_data.get("interval_seconds", 3600),
                        description=loop_data.get("description", ""),
                    )
                    
                    if not success:
                        return f"❌ Error: Failed to add loop {loop_data['id']}"
                
                return f"✅ Saved {len(loops_data)} action loop(s) successfully"
            else:
                return "❌ Error: Failed to initialize XAgent"
                
        except json.JSONDecodeError as e:
            return f"❌ Error: Invalid JSON format - {str(e)}"
        except Exception as e:
            logger.error(f"Error saving action loops: {e}")
            return f"❌ Error: {str(e)}"

    def _start_action_loop(self):
        """Start the action loops."""
        if not self.tab.xagent:
            return "❌ Error: XAgent not initialized"
            
        try:
            result = asyncio.run(self.tab.xagent.start_action_loop())
            
            if result["status"] == "success":
                loops = result.get("loops", [])
                return f"✅ Started {len(loops)} action loop(s): {', '.join(loops)}"
            else:
                error_msg = result.get("error", "Unknown error")
                return f"❌ Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error starting action loop: {e}")
            return f"❌ Error: {str(e)}"

    def _stop_action_loop(self):
        """Stop the action loops."""
        if not self.tab.xagent:
            return "❌ Error: XAgent not initialized"
            
        try:
            result = asyncio.run(self.tab.xagent.stop_action_loop())
            
            if result["status"] == "success":
                return "✅ Action loops stopped"
            else:
                error_msg = result.get("error", "Unknown error")
                return f"❌ Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error stopping action loop: {e}")
            return f"❌ Error: {str(e)}"

    def get_loop_status(self):
        """Get the current status of action loops."""
        if not self.tab.xagent:
            return "XAgent not initialized"
            
        try:
            status = self.tab.xagent.get_status()
            
            if status.get("is_running", False):
                return "🔄 Loops running"
            else:
                loop_count = len(self.tab.xagent.get_action_loops())
                return f"⏹️ Stopped ({loop_count} loops configured)"
                
        except Exception as e:
            logger.error(f"Error getting loop status: {e}")
            return f"❌ Error: {str(e)}"
