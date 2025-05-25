import asyncio
import json
import logging
import os
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

import gradio as gr
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from langchain_core.language_models.chat_models import BaseChatModel

from src.agent.xagent.xagent import XAgent
from src.utils import llm_provider
from src.webui.utils.env_utils import get_env_value, load_env_settings_with_cache
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


class XAgentTab:
    """XAgent tab component for the web UI."""

    def __init__(self, llm: Optional[BaseChatModel] = None, browser_config: Optional[Dict[str, Any]] = None):
        """Initialize XAgent tab.
        
        Args:
            llm: Language model instance (can be None, will be initialized from settings)
            browser_config: Browser configuration dictionary
        """
        self.llm = llm
        self.browser_config = browser_config or {
            "headless": False,
            "window_width": 1280,
            "window_height": 1100,
            "disable_security": False,
        }
        self.xagent = None
        self.chat_history = []
        self.current_task_id = None

    def create_tab(self):
        """Create the XAgent tab UI components."""
        with gr.Column():
            gr.Markdown("# 🎭 XAgent - Stealth Browser Automation")
            gr.Markdown(
                """
                XAgent provides advanced stealth browser automation using Patchright technology.
                
                **Features:**
                - Enhanced anti-detection capabilities
                - Patchright stealth browser (Chrome-optimized)
                - Advanced fingerprint resistance
                - Bypasses major bot detection systems
                """
            )

            with gr.Row():
                with gr.Column(scale=3):
                    task_input = gr.Textbox(
                        label="Task Description",
                        placeholder="Enter your automation task here...",
                        lines=3,
                        elem_id="xagent_task_input"
                    )
                    
                    with gr.Row():
                        run_button = gr.Button("🚀 Run XAgent", variant="primary", elem_id="xagent_run_button")
                        stop_button = gr.Button("⏹️ Stop", variant="stop", interactive=False, elem_id="xagent_stop_button")
                        clear_button = gr.Button("🗑️ Clear", elem_id="xagent_clear_button")

                with gr.Column(scale=1):
                    gr.Markdown("### Settings")
                    max_steps = gr.Slider(
                        minimum=1,
                        maximum=200,
                        value=50,
                        step=1,
                        label="Max Steps",
                        elem_id="xagent_max_steps"
                    )
                    
                    save_results = gr.Checkbox(
                        label="Save Results",
                        value=True,
                        elem_id="xagent_save_results"
                    )

            # Chat interface
            chatbot = gr.Chatbot(
                label="XAgent Execution Log",
                height=400,
                elem_id="xagent_chatbot"
            )

            # Status and results
            with gr.Row():
                status_text = gr.Textbox(
                    label="Status",
                    value="Ready",
                    interactive=False,
                    elem_id="xagent_status"
                )
                
                task_id_text = gr.Textbox(
                    label="Task ID",
                    value="",
                    interactive=False,
                    elem_id="xagent_task_id"
                )

            # Results download
            results_file = gr.File(
                label="Download Results",
                visible=False,
                elem_id="xagent_results_file"
            )

            # Event handlers
            run_button.click(
                fn=self._run_xagent_task,
                inputs=[task_input, max_steps, save_results],
                outputs=[chatbot, status_text, task_id_text, run_button, stop_button, results_file],
                show_progress=True
            )

            stop_button.click(
                fn=self._stop_xagent_task,
                outputs=[status_text, run_button, stop_button]
            )

            clear_button.click(
                fn=self._clear_chat,
                outputs=[chatbot, status_text, task_id_text, results_file]
            )

    async def _initialize_llm_from_settings(self) -> Optional[BaseChatModel]:
        """Initialize LLM from current settings if not already provided."""
        if self.llm:
            return self.llm
            
        try:
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

    async def _run_xagent_task(self, task: str, max_steps: int, save_results: bool):
        """Run XAgent task."""
        if not task.strip():
            gr.Warning("Please enter a task description")
            return (
                self.chat_history,
                "Error: No task provided",
                "",
                gr.update(interactive=True),
                gr.update(interactive=False),
                gr.update(visible=False)
            )

        try:
            # Initialize LLM
            llm = await self._initialize_llm_from_settings()
            if not llm:
                gr.Warning("Failed to initialize LLM. Please check your settings.")
                return (
                    self.chat_history,
                    "Error: LLM initialization failed",
                    "",
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                    gr.update(visible=False)
                )

            # Initialize XAgent
            self.xagent = XAgent(
                llm=llm,
                browser_config=self.browser_config,
                mode="stealth"  # Stealth mode only for this branch
            )

            # Generate task ID
            self.current_task_id = str(uuid.uuid4())[:8]
            
            # Update UI
            self.chat_history.append({"role": "user", "content": task})
            self.chat_history.append({"role": "assistant", "content": "🎭 Starting XAgent with stealth capabilities..."})

            # Run the task
            result = await self.xagent.run(
                task=task,
                task_id=self.current_task_id,
                max_steps=max_steps,
                save_dir="./tmp/xagent" if save_results else None
            )

            # Process results
            if result["status"] == "completed":
                self.chat_history.append({
                    "role": "assistant", 
                    "content": f"✅ Task completed successfully!\n\nResult: {result.get('result', 'No result available')}"
                })
                status = "Completed"
                results_file_update = gr.update(visible=save_results)
            else:
                self.chat_history.append({
                    "role": "assistant", 
                    "content": f"❌ Task failed: {result.get('error', 'Unknown error')}"
                })
                status = f"Failed: {result.get('error', 'Unknown error')}"
                results_file_update = gr.update(visible=False)

            return (
                self.chat_history,
                status,
                self.current_task_id,
                gr.update(interactive=True),
                gr.update(interactive=False),
                results_file_update
            )

        except Exception as e:
            logger.error(f"Error running XAgent task: {e}")
            self.chat_history.append({
                "role": "assistant", 
                "content": f"❌ Error: {str(e)}"
            })
            return (
                self.chat_history,
                f"Error: {str(e)}",
                "",
                gr.update(interactive=True),
                gr.update(interactive=False),
                gr.update(visible=False)
            )

    def _stop_xagent_task(self):
        """Stop the current XAgent task."""
        if self.xagent:
            # Note: XAgent.stop() method would need to be implemented
            logger.info("Stopping XAgent task")
            
        return (
            "Stopped",
            gr.update(interactive=True),
            gr.update(interactive=False)
        )

    def _clear_chat(self):
        """Clear the chat history."""
        self.chat_history = []
        self.current_task_id = None
        return (
            [],
            "Ready",
            "",
            gr.update(visible=False)
        )
