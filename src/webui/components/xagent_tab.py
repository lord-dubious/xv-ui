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
            with gr.Accordion("⏱️ Behavioral Loops & Scheduling", open=False):
                self._create_loops_section()

            # Module control section
            with gr.Accordion("🔧 Module Controls", open=False):
                gr.Markdown("#### Enable/Disable System Modules")
                
                with gr.Row():
                    with gr.Column():
                        rate_limiting_enabled = gr.Checkbox(
                            label="Rate Limiting",
                            value=True,
                            elem_id="rate_limiting_enabled",
                        )
                        
                        caching_enabled = gr.Checkbox(
                            label="Action Caching",
                            value=True,
                            elem_id="caching_enabled",
                        )
                        
                        performance_monitoring_enabled = gr.Checkbox(
                            label="Performance Monitoring",
                            value=True,
                            elem_id="performance_monitoring_enabled",
                        )
                    
                    with gr.Column():
                        adaptive_delays_enabled = gr.Checkbox(
                            label="Adaptive Delays",
                            value=True,
                            elem_id="adaptive_delays_enabled",
                        )
                        
                        burst_protection_enabled = gr.Checkbox(
                            label="Burst Protection",
                            value=True,
                            elem_id="burst_protection_enabled",
                        )
                        
                        update_modules_button = gr.Button(
                            "🔧 Update Module Settings",
                            elem_id="update_modules_button",
                        )
                
                module_status = gr.Code(
                    label="Module Status",
                    language="json",
                    lines=8,
                    value="{}",
                    elem_id="module_status",
                )

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
            
        gr.Markdown("### Behavioral Loops & Scheduling")
        gr.Markdown("Configure automated action sequences with advanced scheduling and rate limiting.")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Profile selection
                profile_dropdown = gr.Dropdown(
                    choices=self.profiles,
                    value=self.current_profile,
                    label="Profile",
                    elem_id="loop_profile_dropdown",
                )
                
                # Loop templates
                template_dropdown = gr.Dropdown(
                    choices=["daily_engagement", "content_sharing", "growth_strategy", "weekend_casual"],
                    label="Load Template",
                    elem_id="loop_template_dropdown",
                )
                
                load_template_button = gr.Button(
                    "📋 Load Template",
                    elem_id="load_template_button",
                )
                
                # Action loops configuration
                action_loops_json = gr.Code(
                    label="Action Loops Configuration (JSON)",
                    language="json",
                    lines=20,
                    value='[\n  {\n    "id": "example_loop",\n    "description": "Example automation loop",\n    "interval_seconds": 3600,\n    "rate_limit": {\n      "tweets_per_hour": 5,\n      "follows_per_hour": 10,\n      "min_delay_seconds": 300\n    },\n    "conditions": {\n      "time_range": {"start": "09:00", "end": "18:00"},\n      "days_of_week": [1, 2, 3, 4, 5]\n    },\n    "actions": [\n      {\n        "type": "tweet",\n        "params": {\n          "content": "Good morning! Ready for a productive day! 🌅",\n          "persona": "tech_enthusiast"\n        },\n        "conditions": {\n          "time_range": {"start": "08:00", "end": "10:00"}\n        }\n      },\n      {\n        "type": "delay",\n        "params": {"seconds": 1800}\n      }\n    ]\n  }\n]',
                    elem_id="action_loops_json",
                )
                
                # Validation and save
                with gr.Row():
                    validate_button = gr.Button(
                        "✅ Validate Config",
                        elem_id="validate_loops_button",
                    )
                    save_loops_button = gr.Button(
                        "💾 Save Loops",
                        variant="primary",
                        elem_id="save_loops_button",
                    )
                
                validation_result = gr.Textbox(
                    label="Validation Result",
                    interactive=False,
                    elem_id="validation_result",
                )
            
            with gr.Column(scale=1):
                # Loop control
                gr.Markdown("#### Loop Control")
                
                with gr.Row():
                    start_loop_button = gr.Button(
                        "▶️ Start Loops",
                        variant="primary",
                        elem_id="start_loop_button",
                    )
                    stop_loop_button = gr.Button(
                        "⏹️ Stop Loops",
                        variant="stop",
                        elem_id="stop_loop_button",
                    )
                
                loop_status = gr.Textbox(
                    label="Loop Status",
                    value="⏸️ Stopped",
                    interactive=False,
                    elem_id="loop_status",
                )
                
                # Performance monitoring
                gr.Markdown("#### Performance Monitor")
                
                refresh_stats_button = gr.Button(
                    "🔄 Refresh Stats",
                    elem_id="refresh_stats_button",
                )
                
                performance_stats = gr.Code(
                    label="Performance Statistics",
                    language="json",
                    lines=10,
                    value="{}",
                    elem_id="performance_stats",
                )
                
                # Rate limiting controls
                gr.Markdown("#### Rate Limiting")
                
                with gr.Row():
                    tweets_per_hour = gr.Slider(
                        minimum=1,
                        maximum=50,
                        value=5,
                        step=1,
                        label="Tweets/Hour",
                        elem_id="tweets_per_hour",
                    )
                    
                    follows_per_hour = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=20,
                        step=1,
                        label="Follows/Hour",
                        elem_id="follows_per_hour",
                    )
                
                min_delay_seconds = gr.Slider(
                    minimum=30,
                    maximum=1800,
                    value=300,
                    step=30,
                    label="Min Delay (seconds)",
                    elem_id="min_delay_seconds",
                )
                
                update_limits_button = gr.Button(
                    "⚙️ Update Limits",
                    elem_id="update_limits_button",
                )
        
        # Advanced scheduling section
        with gr.Accordion("⏰ Advanced Scheduling", open=False):
            gr.Markdown("#### Time-based Triggers & Conditional Logic")
            
            with gr.Row():
                with gr.Column():
                    # Time mode selection
                    time_mode = gr.Radio(
                        choices=["Time Ranges", "Fixed Intervals"],
                        value="Time Ranges",
                        label="Timing Mode",
                        elem_id="time_mode",
                    )
                    
                    # Time range settings (for time range mode)
                    with gr.Group(visible=True) as time_range_group:
                        start_time = gr.Textbox(
                            label="Start Time (HH:MM)",
                            value="09:00",
                            elem_id="schedule_start_time",
                        )
                        
                        end_time = gr.Textbox(
                            label="End Time (HH:MM)",
                            value="18:00",
                            elem_id="schedule_end_time",
                        )
                    
                    # Fixed interval settings (for interval mode)
                    with gr.Group(visible=False) as interval_group:
                        interval_minutes = gr.Slider(
                            minimum=5,
                            maximum=480,  # 8 hours
                            value=60,
                            step=5,
                            label="Interval (minutes)",
                            elem_id="interval_minutes",
                        )
                        
                        randomize_intervals = gr.Checkbox(
                            label="Randomize Intervals",
                            value=True,
                            elem_id="randomize_intervals",
                        )
                        
                        randomization_factor = gr.Slider(
                            minimum=0.0,
                            maximum=0.5,
                            value=0.2,
                            step=0.05,
                            label="Randomization Factor (±%)",
                            elem_id="randomization_factor",
                        )
                    
                    # Days of week
                    days_of_week = gr.CheckboxGroup(
                        choices=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                        value=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                        label="Active Days",
                        elem_id="schedule_days",
                    )
                
                with gr.Column():
                    # Conditional logic
                    max_actions_per_day = gr.Slider(
                        minimum=1,
                        maximum=200,
                        value=50,
                        step=1,
                        label="Max Actions/Day",
                        elem_id="max_actions_per_day",
                    )
                    
                    follower_count_condition = gr.Slider(
                        minimum=0,
                        maximum=10000,
                        value=5000,
                        step=100,
                        label="Max Follower Count",
                        elem_id="follower_count_condition",
                    )
                    
                    # Update time settings button
                    update_time_settings_button = gr.Button(
                        "⏰ Update Time Settings",
                        elem_id="update_time_settings_button",
                    )
        
        # Event handlers for loops functionality
        if GRADIO_AVAILABLE:
            # Template loading
            load_template_button.click(
                fn=self.loop_methods._load_loop_template,
                inputs=[template_dropdown],
                outputs=[action_loops_json],
            )
            
            # Validation
            validate_button.click(
                fn=self.loop_methods._validate_loop_config,
                inputs=[action_loops_json],
                outputs=[validation_result],
            )
            
            # Loop management
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
            )
            
            # Performance monitoring
            refresh_stats_button.click(
                fn=self.loop_methods._get_performance_stats,
                outputs=[performance_stats],
            )
            
            # Rate limiting controls
            update_limits_button.click(
                fn=self.loop_methods._update_rate_limits,
                inputs=[tweets_per_hour, follows_per_hour, min_delay_seconds],
                outputs=[loop_status],
            )
            
            # Module controls
            update_modules_button.click(
                fn=self.loop_methods._update_module_settings,
                inputs=[
                    rate_limiting_enabled, 
                    caching_enabled, 
                    performance_monitoring_enabled, 
                    adaptive_delays_enabled, 
                    burst_protection_enabled
                ],
                outputs=[module_status],
            )
            
            # Time interval controls
            time_mode.change(
                fn=self.loop_methods._toggle_time_mode_visibility,
                inputs=[time_mode],
                outputs=[time_range_group, interval_group],
            )
            
            update_time_settings_button.click(
                fn=self.loop_methods._update_time_interval_settings,
                inputs=[time_mode, interval_minutes, randomize_intervals, randomization_factor],
                outputs=[loop_status],
            )
            
            # Load module status on page load
            self.interface.load(
                fn=self.loop_methods._get_module_status,
                outputs=[module_status],
            )
