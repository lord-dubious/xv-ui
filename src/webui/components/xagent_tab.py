"""
XAgent Tab - Enhanced stealth agent with integrated Twitter capabilities.

This module provides the main UI interface for XAgent, combining
stealth browser automation with Twitter functionality.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

# Import gradio with fallback
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    logging.warning("Gradio not available. UI functionality will be limited.")

from src.webui.components.xagent_tab_methods import XAgentTabMethods
from src.webui.components.xagent_twitter_methods import XAgentTwitterMethods
from src.webui.components.xagent_loop_methods import XAgentLoopMethods

logger = logging.getLogger(__name__)


class XAgentTab:
    """XAgent tab component for the web UI."""

    def __init__(
        self,
        llm: Optional[Any] = None,
        browser_config: Optional[Dict[str, Any]] = None,
    ):
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
        self.profiles = self._load_available_profiles()
        self.current_profile = "default"
        self.personas = []
        self.twitter_initialized = False
        
        # Initialize method handlers
        self.methods = XAgentTabMethods(self)
        self.twitter_methods = XAgentTwitterMethods(self)
        self.loop_methods = XAgentLoopMethods(self)

    def _load_available_profiles(self) -> List[str]:
        """Load available XAgent profiles."""
        profiles = ["default"]
        profiles_dir = "./profiles"
        
        if os.path.exists(profiles_dir):
            for item in os.listdir(profiles_dir):
                if os.path.isdir(os.path.join(profiles_dir, item)) and item != "default":
                    profiles.append(item)
                    
        return profiles

    def create_tab(self):
        """Create the XAgent tab UI components."""
        if not GRADIO_AVAILABLE:
            logger.error("Cannot create XAgent tab: Gradio not available")
            return
            
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
                - Integrated Twitter automation capabilities
                """
            )

            with gr.Row():
                with gr.Column(scale=3):
                    task_input = gr.Textbox(
                        label="Task Description",
                        placeholder="Enter your automation task here...",
                        lines=3,
                        elem_id="xagent_task_input",
                    )

                    with gr.Row():
                        run_button = gr.Button(
                            "🚀 Run XAgent",
                            variant="primary",
                            elem_id="xagent_run_button",
                        )
                        stop_button = gr.Button(
                            "⏹️ Stop",
                            variant="stop",
                            interactive=False,
                            elem_id="xagent_stop_button",
                        )
                        clear_button = gr.Button(
                            "🗑️ Clear", elem_id="xagent_clear_button"
                        )

                with gr.Column(scale=1):
                    gr.Markdown("### Settings")
                    max_steps = gr.Slider(
                        minimum=1,
                        maximum=200,
                        value=50,
                        step=1,
                        label="Max Steps",
                        elem_id="xagent_max_steps",
                    )

                    save_results = gr.Checkbox(
                        label="Save Results", value=True, elem_id="xagent_save_results"
                    )

            # Chat interface
            chatbot = gr.Chatbot(
                label="XAgent Execution Log", height=400, elem_id="xagent_chatbot"
            )

            # Status and results
            with gr.Row():
                status_text = gr.Textbox(
                    label="Status",
                    value="Ready",
                    interactive=False,
                    elem_id="xagent_status",
                )

                task_id_text = gr.Textbox(
                    label="Task ID",
                    value="",
                    interactive=False,
                    elem_id="xagent_task_id",
                )

            # Results download
            results_file = gr.File(
                label="Download Results", visible=False, elem_id="xagent_results_file"
            )

            # Twitter functionality section
            with gr.Accordion("🐦 Twitter Actions", open=False):
                self._create_twitter_section()

            # Behavioral loops section
            with gr.Accordion("⏱️ Behavioral Loops", open=False):
                self._create_loops_section()

            # Event handlers for task execution
            run_button.click(
                fn=self.methods._run_xagent_task,
                inputs=[task_input, max_steps, save_results],
                outputs=[chatbot, status_text, task_id_text],
                show_progress=True,
            )

            stop_button.click(
                fn=self.methods._stop_xagent_task,
                outputs=[status_text],
            )

            clear_button.click(
                fn=self.methods._clear_chat,
                outputs=[chatbot, status_text, task_id_text],
            )

    def _create_twitter_section(self):
        """Create Twitter functionality section."""
        if not GRADIO_AVAILABLE:
            return
            
        gr.Markdown("### Twitter Automation")
        gr.Markdown("Configure and use Twitter automation capabilities.")
        
        # Placeholder for Twitter UI components
        # This would be expanded with actual Twitter functionality
        gr.Markdown("*Twitter functionality will be available when dependencies are installed.*")

    def _create_loops_section(self):
        """Create behavioral loops section."""
        if not GRADIO_AVAILABLE:
            return
            
        gr.Markdown("### Behavioral Loops")
        gr.Markdown("Configure automated action sequences and scheduling.")
        
        # Placeholder for loops UI components
        # This would be expanded with actual loop functionality
        gr.Markdown("*Behavioral loops functionality will be available when dependencies are installed.*")

