import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

import gradio as gr
from langchain_core.language_models.chat_models import BaseChatModel

from src.agent.xagent.xagent import XAgent
from src.utils import llm_provider
from src.webui.components.xagent_tab_methods import XAgentTabMethods
from src.webui.components.xagent_twitter_methods import XAgentTwitterMethods
from src.webui.components.xagent_loop_methods import XAgentLoopMethods

logger = logging.getLogger(__name__)


class XAgentTab:
    """XAgent tab component for the web UI."""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
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

            # Event handlers for task execution
            run_button.click(
                fn=self.methods._run_xagent_task,
                inputs=[task_input, max_steps, save_results],
                outputs=[
                    chatbot,
                    status_text,
                    task_id_text,
                    run_button,
                    stop_button,
                    results_file,
                ],
                show_progress=True,
            )

            stop_button.click(
                fn=self.methods._stop_xagent_task,
                outputs=[status_text, run_button, stop_button],
            )

            clear_button.click(
                fn=self.methods._clear_chat,
                outputs=[chatbot, status_text, task_id_text, results_file],
            )
            
            # Event handlers for profile management
            profile_dropdown.change(
                fn=self.methods._change_profile,
                inputs=[profile_dropdown],
                outputs=[
                    twitter_username,
                    twitter_email,
                    twitter_password,
                    twitter_totp_secret,
                    cookies_path,
                    twitter_status,
                    action_loops_json,
                ],
            )
            
            refresh_profiles_button.click(
                fn=self.methods._refresh_profiles,
                outputs=[profile_dropdown],
            )
            
            create_profile_button.click(
                fn=self.methods._create_profile_dialog,
                outputs=[profile_dropdown],
            )
            
            # Event handlers for Twitter functionality
            save_credentials_button.click(
                fn=self.methods._save_twitter_credentials,
                inputs=[
                    profile_dropdown,
                    twitter_username,
                    twitter_email,
                    twitter_password,
                    twitter_totp_secret,
                    cookies_path,
                ],
                outputs=[twitter_status, current_totp_code],
            )
            
            refresh_totp_button.click(
                fn=self.methods._refresh_totp_code,
                outputs=[current_totp_code],
            )
            
            initialize_twitter_button.click(
                fn=self.methods._initialize_twitter,
                outputs=[
                    twitter_status,
                    tweet_persona,
                    reply_persona,
                    twitter_chatbot,
                ],
            )
            
            # Event handlers for Twitter actions
            tweet_button.click(
                fn=self.twitter_methods._create_tweet,
                inputs=[tweet_content, tweet_media, tweet_persona],
                outputs=[twitter_result_json, twitter_chatbot, twitter_status],
            )
            
            reply_button.click(
                fn=self.twitter_methods._reply_to_tweet,
                inputs=[tweet_url, reply_content, reply_media, reply_persona],
                outputs=[twitter_result_json, twitter_chatbot, twitter_status],
            )
            
            follow_button.click(
                fn=self.twitter_methods._follow_user,
                inputs=[follow_username],
                outputs=[twitter_result_json, twitter_chatbot, twitter_status],
            )
            
            bulk_follow_button.click(
                fn=self.twitter_methods._bulk_follow,
                inputs=[bulk_follow_usernames],
                outputs=[twitter_result_json, twitter_chatbot, twitter_status],
            )
            
            # Event handlers for behavioral loops
            save_loops_button.click(
                fn=self.loop_methods._save_action_loops,
                inputs=[profile_dropdown, action_loops_json],
                outputs=[loop_status],
            )
            
            start_loop_button.click(
                fn=self.loop_methods._start_action_loop,
                outputs=[loop_status],
            )
            
            stop_loop_button.click(
                fn=self.loop_methods._stop_action_loop,
                outputs=[loop_status],
