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

            # Complete configuration management
            with gr.Accordion("⚙️ Complete Configuration Manager", open=False):
                gr.Markdown("#### All System Settings in One Place")
                
                with gr.Tabs():
                    # Twitter Configuration Tab
                    with gr.Tab("🐦 Twitter Settings"):
                        with gr.Row():
                            with gr.Column():
                                twitter_cookies_path = gr.Textbox(
                                    label="Cookies File Path",
                                    value="./cookies.json",
                                    elem_id="twitter_cookies_path",
                                )
                                
                                twitter_config_path = gr.Textbox(
                                    label="Config File Path", 
                                    value="./config.json",
                                    elem_id="twitter_config_path",
                                )
                                
                                twitter_headless = gr.Checkbox(
                                    label="Headless Mode",
                                    value=True,
                                    elem_id="twitter_headless",
                                )
                                
                                twitter_stealth_mode = gr.Checkbox(
                                    label="Stealth Mode",
                                    value=True,
                                    elem_id="twitter_stealth_mode",
                                )
                            
                            with gr.Column():
                                twitter_user_agent = gr.Textbox(
                                    label="Custom User Agent",
                                    placeholder="Leave empty for default",
                                    elem_id="twitter_user_agent",
                                )
                                
                                twitter_viewport_width = gr.Slider(
                                    minimum=800,
                                    maximum=1920,
                                    value=1280,
                                    step=10,
                                    label="Viewport Width",
                                    elem_id="twitter_viewport_width",
                                )
                                
                                twitter_viewport_height = gr.Slider(
                                    minimum=600,
                                    maximum=1080,
                                    value=720,
                                    step=10,
                                    label="Viewport Height",
                                    elem_id="twitter_viewport_height",
                                )
                                
                                twitter_timeout = gr.Slider(
                                    minimum=5,
                                    maximum=120,
                                    value=30,
                                    step=5,
                                    label="Page Timeout (seconds)",
                                    elem_id="twitter_timeout",
                                )
                    
                    # Performance Configuration Tab
                    with gr.Tab("⚡ Performance Settings"):
                        with gr.Row():
                            with gr.Column():
                                cache_max_size = gr.Slider(
                                    minimum=100,
                                    maximum=10000,
                                    value=1000,
                                    step=100,
                                    label="Cache Max Size",
                                    elem_id="cache_max_size",
                                )
                                
                                cache_default_ttl = gr.Slider(
                                    minimum=300,
                                    maximum=7200,
                                    value=3600,
                                    step=300,
                                    label="Cache TTL (seconds)",
                                    elem_id="cache_default_ttl",
                                )
                                
                                performance_history_size = gr.Slider(
                                    minimum=100,
                                    maximum=5000,
                                    value=1000,
                                    step=100,
                                    label="Performance History Size",
                                    elem_id="performance_history_size",
                                )
                            
                            with gr.Column():
                                cpu_threshold = gr.Slider(
                                    minimum=50,
                                    maximum=95,
                                    value=80,
                                    step=5,
                                    label="CPU Usage Threshold (%)",
                                    elem_id="cpu_threshold",
                                )
                                
                                memory_threshold = gr.Slider(
                                    minimum=50,
                                    maximum=95,
                                    value=85,
                                    step=5,
                                    label="Memory Usage Threshold (%)",
                                    elem_id="memory_threshold",
                                )
                                
                                monitoring_interval = gr.Slider(
                                    minimum=1,
                                    maximum=30,
                                    value=5,
                                    step=1,
                                    label="Monitoring Interval (seconds)",
                                    elem_id="monitoring_interval",
                                )
                    
                    # Rate Limiting Configuration Tab
                    with gr.Tab("🛡️ Rate Limiting Settings"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("**Default Rate Limits (per hour)**")
                                
                                default_tweets_limit = gr.Slider(
                                    minimum=1,
                                    maximum=100,
                                    value=50,
                                    step=1,
                                    label="Default Tweets Limit",
                                    elem_id="default_tweets_limit",
                                )
                                
                                default_follows_limit = gr.Slider(
                                    minimum=1,
                                    maximum=500,
                                    value=400,
                                    step=10,
                                    label="Default Follows Limit",
                                    elem_id="default_follows_limit",
                                )
                                
                                default_likes_limit = gr.Slider(
                                    minimum=1,
                                    maximum=2000,
                                    value=1000,
                                    step=50,
                                    label="Default Likes Limit",
                                    elem_id="default_likes_limit",
                                )
                            
                            with gr.Column():
                                gr.Markdown("**Minimum Delays (seconds)**")
                                
                                min_tweet_delay = gr.Slider(
                                    minimum=30,
                                    maximum=600,
                                    value=60,
                                    step=10,
                                    label="Min Tweet Delay",
                                    elem_id="min_tweet_delay",
                                )
                                
                                min_follow_delay = gr.Slider(
                                    minimum=10,
                                    maximum=300,
                                    value=30,
                                    step=5,
                                    label="Min Follow Delay",
                                    elem_id="min_follow_delay",
                                )
                                
                                min_like_delay = gr.Slider(
                                    minimum=5,
                                    maximum=60,
                                    value=10,
                                    step=1,
                                    label="Min Like Delay",
                                    elem_id="min_like_delay",
                                )
                    
                    # Advanced Configuration Tab
                    with gr.Tab("🔧 Advanced Settings"):
                        with gr.Row():
                            with gr.Column():
                                encryption_enabled = gr.Checkbox(
                                    label="Enable Credential Encryption",
                                    value=True,
                                    elem_id="encryption_enabled",
                                )
                                
                                auto_save_enabled = gr.Checkbox(
                                    label="Auto-save Configurations",
                                    value=True,
                                    elem_id="auto_save_enabled",
                                )
                                
                                debug_mode = gr.Checkbox(
                                    label="Debug Mode",
                                    value=False,
                                    elem_id="debug_mode",
                                )
                                
                                verbose_logging = gr.Checkbox(
                                    label="Verbose Logging",
                                    value=False,
                                    elem_id="verbose_logging",
                                )
                            
                            with gr.Column():
                                max_retries = gr.Slider(
                                    minimum=1,
                                    maximum=10,
                                    value=3,
                                    step=1,
                                    label="Max Retries",
                                    elem_id="max_retries",
                                )
                                
                                retry_delay = gr.Slider(
                                    minimum=1,
                                    maximum=60,
                                    value=5,
                                    step=1,
                                    label="Retry Delay (seconds)",
                                    elem_id="retry_delay",
                                )
                                
                                session_timeout = gr.Slider(
                                    minimum=300,
                                    maximum=7200,
                                    value=1800,
                                    step=300,
                                    label="Session Timeout (seconds)",
                                    elem_id="session_timeout",
                                )
                
                # Configuration actions
                with gr.Row():
                    save_all_config_button = gr.Button(
                        "💾 Save All Settings",
                        variant="primary",
                        elem_id="save_all_config_button",
                    )
                    
                    load_config_button = gr.Button(
                        "📂 Load Configuration",
                        elem_id="load_config_button",
                    )
                    
                    reset_config_button = gr.Button(
                        "🔄 Reset to Defaults",
                        elem_id="reset_config_button",
                    )
                    
                    export_config_button = gr.Button(
                        "📤 Export Config",
                        elem_id="export_config_button",
                    )
                
                config_status = gr.Textbox(
                    label="Configuration Status",
                    interactive=False,
                    elem_id="config_status",
                )
                
                # Complete configuration viewer
                complete_config_viewer = gr.Code(
                    label="Complete Configuration (Read-Only)",
                    language="json",
                    lines=15,
                    value="{}",
                    elem_id="complete_config_viewer",
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
            
            # Complete configuration management handlers
            save_all_config_button.click(
                fn=self.loop_methods._save_all_configuration,
                inputs=[
                    # Twitter settings
                    twitter_cookies_path, twitter_config_path, twitter_headless, twitter_stealth_mode,
                    twitter_user_agent, twitter_viewport_width, twitter_viewport_height, twitter_timeout,
                    # Performance settings
                    cache_max_size, cache_default_ttl, performance_history_size,
                    cpu_threshold, memory_threshold, monitoring_interval,
                    # Rate limiting settings
                    default_tweets_limit, default_follows_limit, default_likes_limit,
                    min_tweet_delay, min_follow_delay, min_like_delay,
                    # Advanced settings
                    encryption_enabled, auto_save_enabled, debug_mode, verbose_logging,
                    max_retries, retry_delay, session_timeout,
                ],
                outputs=[config_status],
            )
            
            load_config_button.click(
                fn=self.loop_methods._load_complete_configuration,
                outputs=[complete_config_viewer],
            )
            
            reset_config_button.click(
                fn=self.loop_methods._reset_to_defaults,
                outputs=[config_status],
            )
            
            export_config_button.click(
                fn=self.loop_methods._export_configuration,
                outputs=[config_status],
            )
