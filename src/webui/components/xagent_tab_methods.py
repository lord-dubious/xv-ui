"""
XAgent Tab Methods - Core functionality methods for XAgent UI.

This module contains the core methods for XAgent functionality,
separated for better code organization and maintainability.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

# Import gradio with fallback
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    logging.warning("Gradio not available. UI functionality will be limited.")

logger = logging.getLogger(__name__)


class XAgentTabMethods:
    """Methods for XAgent tab functionality."""
    
    def __init__(self, tab_instance):
        """Initialize with reference to the tab instance."""
        self.tab = tab_instance
        
    async def _initialize_llm_from_settings(self):
        """Initialize LLM from current settings if not already provided."""
        if self.tab.llm:
            return self.tab.llm

        try:
            # Import here to avoid circular imports
            import os
            from src.utils import llm_provider
            
            # Get settings from environment or defaults
            provider = os.getenv("LLM_PROVIDER", "openai")
            model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.6"))
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            base_url = os.getenv(f"{provider.upper()}_ENDPOINT")

            if not provider or not model_name:
                logger.warning("LLM provider or model not configured")
                return None

            llm = llm_provider.get_llm_model(
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                base_url=base_url,
                api_key=api_key,
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None

    def _run_xagent_task(self, task: str, max_steps: int, save_results: bool):
        """Run XAgent task."""
        if not GRADIO_AVAILABLE:
            return "Gradio not available"
            
        if not task.strip():
            return "Error: No task provided"

        try:
            # Import here to avoid circular imports
            import uuid
            from src.agent.xagent.xagent import XAgent
            
            # Initialize LLM
            llm = asyncio.run(self._initialize_llm_from_settings())
            if not llm:
                return "Error: LLM initialization failed"

            # Initialize XAgent with current profile
            self.tab.xagent = XAgent(
                llm=llm,
                browser_config=self.tab.browser_config,
                mode="stealth",
                profile_name=getattr(self.tab, 'current_profile', 'default'),
            )

            # Generate task ID
            self.tab.current_task_id = str(uuid.uuid4())[:8]

            # Run the task
            result = asyncio.run(
                self.tab.xagent.run(
                    task=task,
                    task_id=self.tab.current_task_id,
                    max_steps=max_steps,
                    save_dir="./tmp/xagent" if save_results else None,
                )
            )

            # Process results
            if result["status"] == "completed":
                return f"✅ Task completed successfully!\n\nResult: {result.get('result', 'No result available')}"
            else:
                return f"❌ Task failed: {result.get('error', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Error running XAgent task: {e}")
            return f"❌ Error: {str(e)}"

    def _stop_xagent_task(self):
        """Stop the current XAgent task."""
        if hasattr(self.tab, 'xagent') and self.tab.xagent:
            asyncio.run(self.tab.xagent.stop())
            logger.info("Stopping XAgent task")
        return "Stopped"

    def _clear_chat(self):
        """Clear the chat history."""
        if hasattr(self.tab, 'chat_history'):
            self.tab.chat_history = []
        if hasattr(self.tab, 'current_task_id'):
            self.tab.current_task_id = None
        return "Ready"
