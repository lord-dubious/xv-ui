import json
import logging
import os
from typing import Dict, Tuple

import gradio as gr

from src.utils import config
from src.webui.utils.env_utils import get_env_value, load_env_settings_with_cache
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def update_model_dropdown(
    llm_provider: str, webui_manager=None, is_planner=False
) -> gr.Dropdown:
    """
    Update the model name dropdown with predefined models for the selected provider.
    Preserves the currently saved model name if it's valid for the new provider.

    Args:
        llm_provider: The LLM provider name
        webui_manager: WebUI manager instance for loading saved settings
        is_planner: Whether this is for the planner LLM (affects which env var to check)

    Returns:
        Updated Gradio Dropdown component
    """
    # Use predefined models for the selected provider
    if llm_provider in config.model_names:
        choices = config.model_names[llm_provider]

        # Try to preserve the currently saved model name if it's valid for this provider
        saved_model = None
        if webui_manager:
            try:
                env_settings = webui_manager.load_env_settings()
                # Use different env var for planner vs main LLM
                env_var = "PLANNER_LLM_MODEL_NAME" if is_planner else "LLM_MODEL_NAME"
                saved_model = env_settings.get(env_var)
            except Exception:
                pass

        # Use saved model if it's in the choices, otherwise use first choice
        if saved_model and saved_model in choices:
            default_value = saved_model
        else:
            default_value = choices[0] if choices else ""

        return gr.Dropdown(
            choices=choices,
            value=default_value,
            interactive=True,
        )
    else:
        return gr.Dropdown(
            choices=[], value="", interactive=True, allow_custom_value=True
        )


async def update_mcp_server(mcp_file: str, webui_manager: WebuiManager):
    """
    Update the MCP server.
    """
    if hasattr(webui_manager, "bu_controller") and webui_manager.bu_controller:
        logger.warning("⚠️ Close controller because mcp file has changed!")
        await webui_manager.bu_controller.close_mcp_client()
        webui_manager.bu_controller = None

    if not mcp_file or not os.path.exists(mcp_file) or not mcp_file.endswith(".json"):
        logger.warning(f"{mcp_file} is not a valid MCP file.")
        return None, gr.update(visible=False)

    with open(mcp_file, "r") as f:
        mcp_server = json.load(f)

    return json.dumps(mcp_server, indent=2), gr.update(visible=True)


def setup_synchronized_delay_setting(
    slider_component, number_input_component, setting_key_name, save_function
):
    """
    Sets up two-way synchronization and save-on-change for a slider and a number input.

    Args:
        slider_component: The Gradio Slider component.
        number_input_component: The Gradio Number component.
        setting_key_name (str): The key name for the setting (e.g., 'step_delay_minutes').
        save_function (callable): The function to call to save the setting.
                                  It's expected to take a keyword argument,
                                  e.g., save_function(step_delay_minutes=value).
    """

    def on_slider_change(value):
        save_function(**{setting_key_name: value})
        return gr.update(value=value)

    def on_number_input_change(value):
        save_function(**{setting_key_name: value})
        return gr.update(value=value)

    slider_component.change(
        fn=on_slider_change,
        inputs=[slider_component],
        outputs=[number_input_component],
    )
    number_input_component.change(
        fn=on_number_input_change,
        inputs=[number_input_component],
        outputs=[slider_component],
    )


def _create_system_prompt_components(
    env_settings: Dict[str, str],
) -> Tuple[gr.Textbox, gr.Textbox]:
    """Create system prompt components.

    Args:
        env_settings: Environment settings dictionary

    Returns:
        Tuple of (override_system_prompt, extend_system_prompt) components
    """
    with gr.Group(), gr.Column():
        override_system_prompt = gr.Textbox(
            label="Override system prompt",
            lines=4,
            interactive=True,
            value=get_env_value(env_settings, "OVERRIDE_SYSTEM_PROMPT", ""),
        )
        extend_system_prompt = gr.Textbox(
            label="Extend system prompt",
            lines=4,
            interactive=True,
            value=get_env_value(env_settings, "EXTEND_SYSTEM_PROMPT", ""),
        )
    return override_system_prompt, extend_system_prompt


def _create_mcp_components() -> Tuple[gr.File, gr.Textbox]:
    """Create MCP server components.

    Returns:
        Tuple of (mcp_json_file, mcp_server_config) components
    """
    with gr.Group():
        mcp_json_file = gr.File(
            label="MCP server json", interactive=True, file_types=[".json"]
        )
        mcp_server_config = gr.Textbox(
            label="MCP server", lines=6, interactive=True, visible=False
        )
    return mcp_json_file, mcp_server_config


def _create_llm_components(env_settings):
    """Create main LLM configuration components."""
    with gr.Group():
        with gr.Row():
            initial_llm_provider = get_env_value(env_settings, "LLM_PROVIDER", "openai")
            llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="LLM Provider",
                value=initial_llm_provider,
                info="Select LLM provider for LLM",
                interactive=True,
            )

            initial_llm_model_choices = config.model_names.get(initial_llm_provider, [])
            initial_llm_model_name = get_env_value(
                env_settings,
                "LLM_MODEL_NAME",
                initial_llm_model_choices[0] if initial_llm_model_choices else "gpt-4o",
            )

            llm_model_name = gr.Dropdown(
                label="LLM Model Name",
                choices=initial_llm_model_choices,
                value=initial_llm_model_name,
                interactive=True,
                allow_custom_value=True,
                info="Select a model in the dropdown options or directly type a custom model name",
            )
        with gr.Row():
            llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=get_env_value(env_settings, "LLM_TEMPERATURE", 0.6, float),
                step=0.1,
                label="LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True,
            )

            use_vision = gr.Checkbox(
                label="Use Vision",
                value=get_env_value(env_settings, "USE_VISION", True, bool),
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True,
            )

            ollama_num_ctx = gr.Number(
                label="Ollama Context Length",
                value=get_env_value(env_settings, "OLLAMA_NUM_CTX", 128000, int),
                precision=0,
                interactive=True,
                visible=initial_llm_provider == "ollama",
            )

        with gr.Row():
            llm_base_url = gr.Textbox(
                label="LLM Base URL",
                value=get_env_value(env_settings, "LLM_BASE_URL", ""),
                interactive=True,
                visible=initial_llm_provider in ["openai", "anthropic", "ollama"],
            )
            llm_api_key = gr.Textbox(
                label="LLM API Key",
                value=get_env_value(env_settings, "LLM_API_KEY", ""),
                type="password",
                interactive=True,
                visible=initial_llm_provider in ["openai", "anthropic", "ollama"],
            )

    return (
        llm_provider,
        llm_model_name,
        llm_temperature,
        use_vision,
        ollama_num_ctx,
        llm_base_url,
        llm_api_key,
    )


def _create_planner_components(env_settings):
    """Create planner LLM configuration components."""
    with gr.Group():
        with gr.Row():
            initial_planner_llm_provider = get_env_value(
                env_settings, "PLANNER_LLM_PROVIDER", None
            )
            planner_llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="Planner LLM Provider",
                info="Select LLM provider for LLM",
                value=initial_planner_llm_provider,
                interactive=True,
            )

            initial_planner_model_choices = (
                config.model_names.get(initial_planner_llm_provider, [])
                if initial_planner_llm_provider
                else []
            )
            initial_planner_model_name = get_env_value(
                env_settings,
                "PLANNER_LLM_MODEL_NAME",
                initial_planner_model_choices[0]
                if initial_planner_model_choices
                else None,
            )

            planner_llm_model_name = gr.Dropdown(
                label="Planner LLM Model Name",
                choices=initial_planner_model_choices,
                value=initial_planner_model_name,
                interactive=True,
                allow_custom_value=True,
                info="Select a model in the dropdown options or directly type a custom model name",
            )
        with gr.Row():
            planner_llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=get_env_value(
                    env_settings, "PLANNER_LLM_TEMPERATURE", 0.6, float
                ),
                step=0.1,
                label="Planner LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True,
            )

            planner_use_vision = gr.Checkbox(
                label="Use Vision(Planner LLM)",
                value=get_env_value(env_settings, "PLANNER_USE_VISION", False, bool),
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True,
            )

            planner_ollama_num_ctx = gr.Slider(
                minimum=2**8,
                maximum=2**16,
                value=get_env_value(env_settings, "PLANNER_OLLAMA_NUM_CTX", 16000, int),
                step=1,
                label="Ollama Context Length",
                info="Controls max context length model needs to handle (less = faster)",
                visible=initial_planner_llm_provider == "ollama",
                interactive=True,
            )

        with gr.Row():
            planner_llm_base_url = gr.Textbox(
                label="Base URL",
                value=(
                    get_env_value(
                        env_settings,
                        f"{initial_planner_llm_provider.upper()}_ENDPOINT",
                        "",
                    )
                    if initial_planner_llm_provider
                    else ""
                ),
                info="API endpoint URL (if required)",
            )
            planner_llm_api_key = gr.Textbox(
                label="API Key",
                type="password",
                value=(
                    get_env_value(
                        env_settings,
                        f"{initial_planner_llm_provider.upper()}_API_KEY",
                        "",
                    )
                    if initial_planner_llm_provider
                    else ""
                ),
                info="Your API key (auto-saved to .env)",
            )

    return (
        planner_llm_provider,
        planner_llm_model_name,
        planner_llm_temperature,
        planner_use_vision,
        planner_ollama_num_ctx,
        planner_llm_base_url,
        planner_llm_api_key,
    )


def _create_agent_config_components(env_settings):
    """Create agent configuration components (max steps, actions, etc.)."""
    with gr.Row():
        max_steps = gr.Slider(
            minimum=1,
            maximum=1000,
            value=get_env_value(env_settings, "MAX_STEPS", 100, int),
            step=1,
            label="Max Run Steps",
            info="Maximum number of steps the agent will take",
            interactive=True,
        )
        max_actions = gr.Slider(
            minimum=1,
            maximum=100,
            value=get_env_value(env_settings, "MAX_ACTIONS", 10, int),
            step=1,
            label="Max Number of Actions",
            info="Maximum number of actions the agent will take per step",
            interactive=True,
        )

    with gr.Row():
        max_input_tokens = gr.Number(
            label="Max Input Tokens",
            value=get_env_value(env_settings, "MAX_INPUT_TOKENS", 128000, int),
            precision=0,
            interactive=True,
        )
        tool_calling_method = gr.Dropdown(
            label="Tool Calling Method",
            value=get_env_value(env_settings, "TOOL_CALLING_METHOD", "auto"),
            interactive=True,
            allow_custom_value=True,
            choices=["function_calling", "json_mode", "raw", "auto", "tools", "None"],
            visible=True,
        )

    return max_steps, max_actions, max_input_tokens, tool_calling_method


def create_agent_settings_tab(webui_manager: WebuiManager):
    """
    Creates an agent settings tab.
    """
    env_settings = load_env_settings_with_cache(webui_manager)

    input_components = set(webui_manager.get_components())  # noqa: F841
    tab_components = {}

    # Create system prompt components
    override_system_prompt, extend_system_prompt = _create_system_prompt_components(
        env_settings
    )

    # Create MCP components
    mcp_json_file, mcp_server_config = _create_mcp_components()

    # Create main LLM components
    (
        llm_provider,
        llm_model_name,
        llm_temperature,
        use_vision,
        ollama_num_ctx,
        llm_base_url,
        llm_api_key,
    ) = _create_llm_components(env_settings)

    # Create planner components
    (
        planner_llm_provider,
        planner_llm_model_name,
        planner_llm_temperature,
        planner_use_vision,
        planner_ollama_num_ctx,
        planner_llm_base_url,
        planner_llm_api_key,
    ) = _create_planner_components(env_settings)

    # Create agent configuration components
    max_steps, max_actions, max_input_tokens, tool_calling_method = (
        _create_agent_config_components(env_settings)
    )

    # Improved Delay Settings UI
    with gr.Group():
        gr.Markdown("## ⏱️ Agent Timing & Delays")
        gr.Markdown(
            "Configure delays between agent operations to control execution speed and avoid rate limits."
        )

        with gr.Tabs():
            # Step Delays Tab
            with gr.Tab("🚶 Step Delays"):
                gr.Markdown(
                    "**Step delays** occur before each agent reasoning step (between thinking phases)"
                )

                with gr.Row():
                    step_delay_preset = gr.Dropdown(
                        label="Quick Presets",
                        choices=[
                            ("No delay", "0"),
                            ("Fast (30s)", "0.5"),
                            ("Normal (2min)", "2"),
                            ("Slow (5min)", "5"),
                            ("Very slow (10min)", "10"),
                            ("Custom", "custom"),
                        ],
                        value="0",
                        interactive=True,
                        info="Choose a preset or select 'Custom' for manual configuration",
                    )

                with gr.Row():
                    step_enable_random_interval_switch = gr.Checkbox(
                        label="🎲 Enable Random Intervals",
                        value=get_env_value(
                            env_settings, "STEP_ENABLE_RANDOM_INTERVAL", False, bool
                        ),
                        interactive=True,
                        info="Use random delays instead of fixed delays",
                    )

                with gr.Group() as step_fixed_group, gr.Row():
                    step_delay_value = gr.Number(
                        label="Step Delay",
                        value=get_env_value(
                            env_settings, "STEP_DELAY_MINUTES", 0.0, float
                        ),
                        minimum=0,
                        maximum=1440,
                        interactive=True,
                        precision=2,
                    )
                    step_delay_unit = gr.Dropdown(
                        label="Unit",
                        choices=[
                            ("Seconds", "seconds"),
                            ("Minutes", "minutes"),
                            ("Hours", "hours"),
                        ],
                        value="minutes",
                        interactive=True,
                    )

                with gr.Group(
                    visible=get_env_value(
                        env_settings, "STEP_ENABLE_RANDOM_INTERVAL", False, bool
                    )
                ) as step_random_group:
                    gr.Markdown("**Random Interval Range:**")
                    with gr.Row():
                        step_min_delay = gr.Number(
                            label="Minimum Delay",
                            value=get_env_value(
                                env_settings, "STEP_MIN_DELAY_MINUTES", 0.0, float
                            ),
                            minimum=0,
                            maximum=1440,
                            interactive=True,
                            precision=2,
                        )
                        step_max_delay = gr.Number(
                            label="Maximum Delay",
                            value=get_env_value(
                                env_settings, "STEP_MAX_DELAY_MINUTES", 0.0, float
                            ),
                            minimum=0,
                            maximum=1440,
                            interactive=True,
                            precision=2,
                        )
                        step_random_unit = gr.Dropdown(
                            label="Unit",
                            choices=[
                                ("Seconds", "seconds"),
                                ("Minutes", "minutes"),
                                ("Hours", "hours"),
                            ],
                            value="minutes",
                            interactive=True,
                        )

            # Action Delays Tab
            with gr.Tab("⚡ Action Delays"):
                gr.Markdown(
                    "**Action delays** occur between individual browser actions within a single step"
                )

                with gr.Row():
                    action_delay_preset = gr.Dropdown(
                        label="Quick Presets",
                        choices=[
                            ("No delay", "0"),
                            ("Fast (5s)", "0.083"),
                            ("Normal (30s)", "0.5"),
                            ("Slow (1min)", "1"),
                            ("Very slow (2min)", "2"),
                            ("Custom", "custom"),
                        ],
                        value="0",
                        interactive=True,
                        info="Choose a preset or select 'Custom' for manual configuration",
                    )

                with gr.Row():
                    action_enable_random_interval_switch = gr.Checkbox(
                        label="🎲 Enable Random Intervals",
                        value=get_env_value(
                            env_settings, "ACTION_ENABLE_RANDOM_INTERVAL", False, bool
                        ),
                        interactive=True,
                        info="Use random delays instead of fixed delays",
                    )

                with gr.Group() as action_fixed_group, gr.Row():
                    action_delay_value = gr.Number(
                        label="Action Delay",
                        value=get_env_value(
                            env_settings, "ACTION_DELAY_MINUTES", 0.0, float
                        ),
                        minimum=0,
                        maximum=1440,
                        interactive=True,
                        precision=2,
                    )
                    action_delay_unit = gr.Dropdown(
                        label="Unit",
                        choices=[
                            ("Seconds", "seconds"),
                            ("Minutes", "minutes"),
                            ("Hours", "hours"),
                        ],
                        value="minutes",
                        interactive=True,
                    )

                with gr.Group(
                    visible=get_env_value(
                        env_settings, "ACTION_ENABLE_RANDOM_INTERVAL", False, bool
                    )
                ) as action_random_group:
                    gr.Markdown("**Random Interval Range:**")
                    with gr.Row():
                        action_min_delay = gr.Number(
                            label="Minimum Delay",
                            value=get_env_value(
                                env_settings, "ACTION_MIN_DELAY_MINUTES", 0.0, float
                            ),
                            minimum=0,
                            maximum=1440,
                            interactive=True,
                            precision=2,
                        )
                        action_max_delay = gr.Number(
                            label="Maximum Delay",
                            value=get_env_value(
                                env_settings, "ACTION_MAX_DELAY_MINUTES", 0.0, float
                            ),
                            minimum=0,
                            maximum=1440,
                            interactive=True,
                            precision=2,
                        )
                        action_random_unit = gr.Dropdown(
                            label="Unit",
                            choices=[
                                ("Seconds", "seconds"),
                                ("Minutes", "minutes"),
                                ("Hours", "hours"),
                            ],
                            value="minutes",
                            interactive=True,
                        )

            # Task Delays Tab
            with gr.Tab("📋 Task Delays"):
                gr.Markdown(
                    "**Task delays** occur at the beginning of each new task/run"
                )

                with gr.Row():
                    task_delay_preset = gr.Dropdown(
                        label="Quick Presets",
                        choices=[
                            ("No delay", "0"),
                            ("Fast (1min)", "1"),
                            ("Normal (5min)", "5"),
                            ("Slow (15min)", "15"),
                            ("Very slow (30min)", "30"),
                            ("Custom", "custom"),
                        ],
                        value="0",
                        interactive=True,
                        info="Choose a preset or select 'Custom' for manual configuration",
                    )

                with gr.Row():
                    task_enable_random_interval_switch = gr.Checkbox(
                        label="🎲 Enable Random Intervals",
                        value=get_env_value(
                            env_settings, "TASK_ENABLE_RANDOM_INTERVAL", False, bool
                        ),
                        interactive=True,
                        info="Use random delays instead of fixed delays",
                    )

                with gr.Group() as task_fixed_group, gr.Row():
                    task_delay_value = gr.Number(
                        label="Task Delay",
                        value=get_env_value(
                            env_settings, "TASK_DELAY_MINUTES", 0.0, float
                        ),
                        minimum=0,
                        maximum=1440,
                        interactive=True,
                        precision=2,
                    )
                    task_delay_unit = gr.Dropdown(
                        label="Unit",
                        choices=[
                            ("Seconds", "seconds"),
                            ("Minutes", "minutes"),
                            ("Hours", "hours"),
                        ],
                        value="minutes",
                        interactive=True,
                    )

                with gr.Group(
                    visible=get_env_value(
                        env_settings, "TASK_ENABLE_RANDOM_INTERVAL", False, bool
                    )
                ) as task_random_group:
                    gr.Markdown("**Random Interval Range:**")
                    with gr.Row():
                        task_min_delay = gr.Number(
                            label="Minimum Delay",
                            value=get_env_value(
                                env_settings, "TASK_MIN_DELAY_MINUTES", 0.0, float
                            ),
                            minimum=0,
                            maximum=1440,
                            interactive=True,
                            precision=2,
                        )
                        task_max_delay = gr.Number(
                            label="Maximum Delay",
                            value=get_env_value(
                                env_settings, "TASK_MAX_DELAY_MINUTES", 0.0, float
                            ),
                            minimum=0,
                            maximum=1440,
                            interactive=True,
                            precision=2,
                        )
                        task_random_unit = gr.Dropdown(
                            label="Unit",
                            choices=[
                                ("Seconds", "seconds"),
                                ("Minutes", "minutes"),
                                ("Hours", "hours"),
                            ],
                            value="minutes",
                            interactive=True,
                        )

    tab_components.update(
        {
            "override_system_prompt": override_system_prompt,
            "extend_system_prompt": extend_system_prompt,
            "llm_provider": llm_provider,
            "llm_model_name": llm_model_name,
            "llm_temperature": llm_temperature,
            "use_vision": use_vision,
            "ollama_num_ctx": ollama_num_ctx,
            "llm_base_url": llm_base_url,
            "llm_api_key": llm_api_key,
            "planner_llm_provider": planner_llm_provider,
            "planner_llm_model_name": planner_llm_model_name,
            "planner_llm_temperature": planner_llm_temperature,
            "planner_use_vision": planner_use_vision,
            "planner_ollama_num_ctx": planner_ollama_num_ctx,
            "planner_llm_base_url": planner_llm_base_url,
            "planner_llm_api_key": planner_llm_api_key,
            "max_steps": max_steps,
            "max_actions": max_actions,
            "max_input_tokens": max_input_tokens,
            "tool_calling_method": tool_calling_method,
            "mcp_json_file": mcp_json_file,
            "mcp_server_config": mcp_server_config,
            # New delay components
            "step_delay_preset": step_delay_preset,
            "step_delay_value": step_delay_value,
            "step_delay_unit": step_delay_unit,
            "step_enable_random_interval": step_enable_random_interval_switch,
            "step_min_delay": step_min_delay,
            "step_max_delay": step_max_delay,
            "step_random_unit": step_random_unit,
            "action_delay_preset": action_delay_preset,
            "action_delay_value": action_delay_value,
            "action_delay_unit": action_delay_unit,
            "action_enable_random_interval": action_enable_random_interval_switch,
            "action_min_delay": action_min_delay,
            "action_max_delay": action_max_delay,
            "action_random_unit": action_random_unit,
            "task_delay_preset": task_delay_preset,
            "task_delay_value": task_delay_value,
            "task_delay_unit": task_delay_unit,
            "task_enable_random_interval": task_enable_random_interval_switch,
            "task_min_delay": task_min_delay,
            "task_max_delay": task_max_delay,
            "task_random_unit": task_random_unit,
        }
    )
    webui_manager.add_components("agent_settings", tab_components)

    llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=llm_provider,
        outputs=ollama_num_ctx,
    )
    llm_provider.change(
        lambda provider: update_model_dropdown(provider, webui_manager),
        inputs=[llm_provider],
        outputs=[llm_model_name],
    )
    planner_llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=[planner_llm_provider],
        outputs=[planner_ollama_num_ctx],
    )
    planner_llm_provider.change(
        lambda provider: update_model_dropdown(
            provider, webui_manager, is_planner=True
        ),
        inputs=[planner_llm_provider],
        outputs=[planner_llm_model_name],
    )

    async def update_wrapper(mcp_file):
        """Wrapper for handle_pause_resume."""
        update_dict = await update_mcp_server(mcp_file, webui_manager)
        yield update_dict

    mcp_json_file.change(
        update_wrapper,
        inputs=[mcp_json_file],
        outputs=[mcp_server_config, mcp_server_config],
    )

    # Auto-save LLM API settings when they change
    def save_llm_api_setting(provider=None, api_key=None, base_url=None):
        if provider is None:
            provider = llm_provider.value

        if provider:
            webui_manager.save_api_keys_to_env(provider, api_key, base_url)

    # Auto-save Planner LLM API settings when they change
    def save_planner_api_setting(provider=None, api_key=None, base_url=None):
        if provider is None:
            provider = planner_llm_provider.value

        if provider:
            webui_manager.save_api_keys_to_env(provider, api_key, base_url)

    # Add a new function to save additional planner settings
    def save_planner_settings(
        model_name=None, temperature=None, use_vision=None, ollama_num_ctx=None
    ):
        env_vars = webui_manager.load_env_settings()
        if model_name is not None:
            env_vars["PLANNER_LLM_MODEL_NAME"] = str(model_name)
        if temperature is not None:
            env_vars["PLANNER_LLM_TEMPERATURE"] = str(temperature)
        if use_vision is not None:
            env_vars["PLANNER_USE_VISION"] = str(use_vision).lower()
        if ollama_num_ctx is not None:
            env_vars["PLANNER_OLLAMA_NUM_CTX"] = str(ollama_num_ctx)
        webui_manager.save_env_settings(env_vars)

    # Add a new function to save time interval settings
    def save_time_interval_settings(
        step_delay_minutes=None,
        action_delay_minutes=None,
        task_delay_minutes=None,
        step_enable_random_interval=None,
        min_step_delay_minutes=None,
        max_step_delay_minutes=None,
        action_enable_random_interval=None,
        min_action_delay_minutes=None,
        max_action_delay_minutes=None,
        task_enable_random_interval=None,
        min_task_delay_minutes=None,
        max_task_delay_minutes=None,
    ):
        env_vars = webui_manager.load_env_settings()
        # Fixed delays
        if step_delay_minutes is not None:
            env_vars["STEP_DELAY_MINUTES"] = str(step_delay_minutes)
        if action_delay_minutes is not None:
            env_vars["ACTION_DELAY_MINUTES"] = str(action_delay_minutes)
        if task_delay_minutes is not None:
            env_vars["TASK_DELAY_MINUTES"] = str(task_delay_minutes)

        # Step random interval settings
        if step_enable_random_interval is not None:
            env_vars["STEP_ENABLE_RANDOM_INTERVAL"] = str(
                step_enable_random_interval
            ).lower()
        if min_step_delay_minutes is not None:
            env_vars["STEP_MIN_DELAY_MINUTES"] = str(min_step_delay_minutes)
        if max_step_delay_minutes is not None:
            env_vars["STEP_MAX_DELAY_MINUTES"] = str(max_step_delay_minutes)

        # Action random interval settings
        if action_enable_random_interval is not None:
            env_vars["ACTION_ENABLE_RANDOM_INTERVAL"] = str(
                action_enable_random_interval
            ).lower()
        if min_action_delay_minutes is not None:
            env_vars["ACTION_MIN_DELAY_MINUTES"] = str(min_action_delay_minutes)
        if max_action_delay_minutes is not None:
            env_vars["ACTION_MAX_DELAY_MINUTES"] = str(max_action_delay_minutes)

        # Task random interval settings
        if task_enable_random_interval is not None:
            env_vars["TASK_ENABLE_RANDOM_INTERVAL"] = str(
                task_enable_random_interval
            ).lower()
        if min_task_delay_minutes is not None:
            env_vars["TASK_MIN_DELAY_MINUTES"] = str(min_task_delay_minutes)
        if max_task_delay_minutes is not None:
            env_vars["TASK_MAX_DELAY_MINUTES"] = str(max_task_delay_minutes)

        webui_manager.save_env_settings(env_vars)

    # Add a new function to save main LLM settings
    def save_main_llm_settings(
        model_name=None,
        temperature=None,
        use_vision=None,
        ollama_num_ctx=None,
        max_steps=None,
        max_actions=None,
        max_input_tokens=None,
        tool_calling_method=None,
        override_system_prompt=None,
        extend_system_prompt=None,
    ):
        env_vars = webui_manager.load_env_settings()
        if model_name is not None:
            env_vars["LLM_MODEL_NAME"] = str(model_name)
        if temperature is not None:
            env_vars["LLM_TEMPERATURE"] = str(temperature)
        if use_vision is not None:
            env_vars["USE_VISION"] = str(use_vision).lower()
        if ollama_num_ctx is not None:
            env_vars["OLLAMA_NUM_CTX"] = str(ollama_num_ctx)
        if max_steps is not None:
            env_vars["MAX_STEPS"] = str(max_steps)
        if max_actions is not None:
            env_vars["MAX_ACTIONS"] = str(max_actions)
        if max_input_tokens is not None:
            env_vars["MAX_INPUT_TOKENS"] = str(max_input_tokens)
        if tool_calling_method is not None:
            env_vars["TOOL_CALLING_METHOD"] = str(tool_calling_method)
        if override_system_prompt is not None:
            env_vars["OVERRIDE_SYSTEM_PROMPT"] = str(override_system_prompt)
        if extend_system_prompt is not None:
            env_vars["EXTEND_SYSTEM_PROMPT"] = str(extend_system_prompt)
        webui_manager.save_env_settings(env_vars)

    # Connect change events to auto-save functions
    def save_llm_provider(provider):
        """Save LLM provider to environment variables"""
        env_vars = webui_manager.load_env_settings()
        env_vars["LLM_PROVIDER"] = str(provider)
        webui_manager.save_env_settings(env_vars)
        # Also save API settings
        save_llm_api_setting(provider=provider)

    llm_provider.change(
        fn=save_llm_provider,
        inputs=[llm_provider],
    )

    llm_model_name.change(
        fn=lambda model_name: save_main_llm_settings(model_name=model_name),
        inputs=[llm_model_name],
    )

    llm_temperature.change(
        fn=lambda temperature: save_main_llm_settings(temperature=temperature),
        inputs=[llm_temperature],
    )

    use_vision.change(
        fn=lambda use_vision: save_main_llm_settings(use_vision=use_vision),
        inputs=[use_vision],
    )

    ollama_num_ctx.change(
        fn=lambda ollama_num_ctx: save_main_llm_settings(ollama_num_ctx=ollama_num_ctx),
        inputs=[ollama_num_ctx],
    )

    max_steps.change(
        fn=lambda max_steps: save_main_llm_settings(max_steps=max_steps),
        inputs=[max_steps],
    )

    max_actions.change(
        fn=lambda max_actions: save_main_llm_settings(max_actions=max_actions),
        inputs=[max_actions],
    )

    max_input_tokens.change(
        fn=lambda max_input_tokens: save_main_llm_settings(
            max_input_tokens=max_input_tokens
        ),
        inputs=[max_input_tokens],
    )

    tool_calling_method.change(
        fn=lambda tool_calling_method: save_main_llm_settings(
            tool_calling_method=tool_calling_method
        ),
        inputs=[tool_calling_method],
    )

    override_system_prompt.change(
        fn=lambda override_system_prompt: save_main_llm_settings(
            override_system_prompt=override_system_prompt
        ),
        inputs=[override_system_prompt],
    )

    extend_system_prompt.change(
        fn=lambda extend_system_prompt: save_main_llm_settings(
            extend_system_prompt=extend_system_prompt
        ),
        inputs=[extend_system_prompt],
    )

    llm_api_key.change(
        fn=lambda api_key: save_llm_api_setting(api_key=api_key),
        inputs=[llm_api_key],
    )

    llm_base_url.change(
        fn=lambda base_url: save_llm_api_setting(base_url=base_url),
        inputs=[llm_base_url],
    )

    def save_planner_llm_provider(provider):
        """Save Planner LLM provider to environment variables"""
        env_vars = webui_manager.load_env_settings()
        env_vars["PLANNER_LLM_PROVIDER"] = str(provider)
        webui_manager.save_env_settings(env_vars)
        # Also save API settings
        save_planner_api_setting(provider=provider)

    planner_llm_provider.change(
        fn=save_planner_llm_provider,
        inputs=[planner_llm_provider],
    )

    planner_llm_api_key.change(
        fn=lambda api_key: save_planner_api_setting(api_key=api_key),
        inputs=[planner_llm_api_key],
    )

    planner_llm_base_url.change(
        fn=lambda base_url: save_planner_api_setting(base_url=base_url),
        inputs=[planner_llm_base_url],
    )

    # Connect change events for additional planner settings to the new save function
    planner_llm_model_name.change(
        fn=lambda model_name: save_planner_settings(model_name=model_name),
        inputs=[planner_llm_model_name],
    )

    planner_llm_temperature.change(
        fn=lambda temperature: save_planner_settings(temperature=temperature),
        inputs=[planner_llm_temperature],
    )

    planner_use_vision.change(
        fn=lambda use_vision: save_planner_settings(use_vision=use_vision),
        inputs=[planner_use_vision],
    )

    planner_ollama_num_ctx.change(
        fn=lambda ollama_num_ctx: save_planner_settings(ollama_num_ctx=ollama_num_ctx),
        inputs=[planner_ollama_num_ctx],
    )

    # Helper functions for the new delay UI
    def convert_to_minutes(value, unit):
        """Convert delay value to minutes based on unit"""
        if unit == "seconds":
            return value / 60
        elif unit == "hours":
            return value * 60
        else:  # minutes
            return value

    def apply_preset(preset_value, delay_type):
        """Apply preset delay value"""
        if preset_value == "custom":
            return gr.update(), gr.update(interactive=True)
        else:
            minutes = float(preset_value)
            return gr.update(value=minutes), gr.update(interactive=False)

    def toggle_random_mode(enable_random, delay_type):
        """Toggle between fixed and random delay modes"""
        return [
            gr.update(visible=not enable_random),  # fixed group
            gr.update(visible=enable_random),  # random group
        ]

    def save_delay_setting(
        delay_type,
        value=None,
        unit=None,
        enable_random=None,
        min_delay=None,
        max_delay=None,
        random_unit=None,
    ):
        """Save delay settings to environment and invalidate agent cache"""
        env_vars = webui_manager.load_env_settings()

        if enable_random is not None:
            env_vars[f"{delay_type.upper()}_ENABLE_RANDOM_INTERVAL"] = str(
                enable_random
            ).lower()

        if value is not None and unit is not None:
            minutes = convert_to_minutes(value, unit)
            env_vars[f"{delay_type.upper()}_DELAY_MINUTES"] = str(minutes)

        if min_delay is not None and random_unit is not None:
            min_minutes = convert_to_minutes(min_delay, random_unit)
            env_vars[f"{delay_type.upper()}_MIN_DELAY_MINUTES"] = str(min_minutes)

        if max_delay is not None and random_unit is not None:
            max_minutes = convert_to_minutes(max_delay, random_unit)
            env_vars[f"{delay_type.upper()}_MAX_DELAY_MINUTES"] = str(max_minutes)

        webui_manager.save_env_settings(env_vars)

        # Invalidate delay cache in active agent if it exists
        if hasattr(webui_manager, "bu_agent") and webui_manager.bu_agent:
            try:
                webui_manager.bu_agent.invalidate_delay_cache()
                logger.debug(f"Invalidated delay cache for {delay_type} settings")
            except AttributeError:
                # Agent might not have the cache method (older version)
                logger.debug("Agent does not support delay cache invalidation")

    # Connect preset dropdowns
    step_delay_preset.change(
        fn=lambda preset: apply_preset(preset, "step"),
        inputs=[step_delay_preset],
        outputs=[step_delay_value, step_delay_value],
    )
    action_delay_preset.change(
        fn=lambda preset: apply_preset(preset, "action"),
        inputs=[action_delay_preset],
        outputs=[action_delay_value, action_delay_value],
    )
    task_delay_preset.change(
        fn=lambda preset: apply_preset(preset, "task"),
        inputs=[task_delay_preset],
        outputs=[task_delay_value, task_delay_value],
    )

    # Connect random mode toggles
    step_enable_random_interval_switch.change(
        fn=lambda enable: toggle_random_mode(enable, "step"),
        inputs=[step_enable_random_interval_switch],
        outputs=[step_fixed_group, step_random_group],
    )
    action_enable_random_interval_switch.change(
        fn=lambda enable: toggle_random_mode(enable, "action"),
        inputs=[action_enable_random_interval_switch],
        outputs=[action_fixed_group, action_random_group],
    )
    task_enable_random_interval_switch.change(
        fn=lambda enable: toggle_random_mode(enable, "task"),
        inputs=[task_enable_random_interval_switch],
        outputs=[task_fixed_group, task_random_group],
    )

    # Connect auto-save for all delay settings
    # Step delays
    step_delay_value.change(
        fn=lambda value, unit: save_delay_setting("step", value=value, unit=unit),
        inputs=[step_delay_value, step_delay_unit],
        outputs=[],
    )
    step_delay_unit.change(
        fn=lambda unit, value: save_delay_setting("step", value=value, unit=unit),
        inputs=[step_delay_unit, step_delay_value],
        outputs=[],
    )
    step_enable_random_interval_switch.change(
        fn=lambda enable: save_delay_setting("step", enable_random=enable),
        inputs=[step_enable_random_interval_switch],
        outputs=[],
    )
    step_min_delay.change(
        fn=lambda min_val, unit: save_delay_setting(
            "step", min_delay=min_val, random_unit=unit
        ),
        inputs=[step_min_delay, step_random_unit],
        outputs=[],
    )
    step_max_delay.change(
        fn=lambda max_val, unit: save_delay_setting(
            "step", max_delay=max_val, random_unit=unit
        ),
        inputs=[step_max_delay, step_random_unit],
        outputs=[],
    )
    step_random_unit.change(
        fn=lambda unit, min_val, max_val: (
            save_delay_setting("step", min_delay=min_val, random_unit=unit),
            save_delay_setting("step", max_delay=max_val, random_unit=unit),
        ),
        inputs=[step_random_unit, step_min_delay, step_max_delay],
        outputs=[],
    )

    # Action delays
    action_delay_value.change(
        fn=lambda value, unit: save_delay_setting("action", value=value, unit=unit),
        inputs=[action_delay_value, action_delay_unit],
        outputs=[],
    )
    action_delay_unit.change(
        fn=lambda unit, value: save_delay_setting("action", value=value, unit=unit),
        inputs=[action_delay_unit, action_delay_value],
        outputs=[],
    )
    action_enable_random_interval_switch.change(
        fn=lambda enable: save_delay_setting("action", enable_random=enable),
        inputs=[action_enable_random_interval_switch],
        outputs=[],
    )
    action_min_delay.change(
        fn=lambda min_val, unit: save_delay_setting(
            "action", min_delay=min_val, random_unit=unit
        ),
        inputs=[action_min_delay, action_random_unit],
        outputs=[],
    )
    action_max_delay.change(
        fn=lambda max_val, unit: save_delay_setting(
            "action", max_delay=max_val, random_unit=unit
        ),
        inputs=[action_max_delay, action_random_unit],
        outputs=[],
    )
    action_random_unit.change(
        fn=lambda unit, min_val, max_val: (
            save_delay_setting("action", min_delay=min_val, random_unit=unit),
            save_delay_setting("action", max_delay=max_val, random_unit=unit),
        ),
        inputs=[action_random_unit, action_min_delay, action_max_delay],
        outputs=[],
    )

    # Task delays
    task_delay_value.change(
        fn=lambda value, unit: save_delay_setting("task", value=value, unit=unit),
        inputs=[task_delay_value, task_delay_unit],
        outputs=[],
    )
    task_delay_unit.change(
        fn=lambda unit, value: save_delay_setting("task", value=value, unit=unit),
        inputs=[task_delay_unit, task_delay_value],
        outputs=[],
    )
    task_enable_random_interval_switch.change(
        fn=lambda enable: save_delay_setting("task", enable_random=enable),
        inputs=[task_enable_random_interval_switch],
        outputs=[],
    )
    task_min_delay.change(
        fn=lambda min_val, unit: save_delay_setting(
            "task", min_delay=min_val, random_unit=unit
        ),
        inputs=[task_min_delay, task_random_unit],
        outputs=[],
    )
    task_max_delay.change(
        fn=lambda max_val, unit: save_delay_setting(
            "task", max_delay=max_val, random_unit=unit
        ),
        inputs=[task_max_delay, task_random_unit],
        outputs=[],
    )
    task_random_unit.change(
        fn=lambda unit, min_val, max_val: (
            save_delay_setting("task", min_delay=min_val, random_unit=unit),
            save_delay_setting("task", max_delay=max_val, random_unit=unit),
        ),
        inputs=[task_random_unit, task_min_delay, task_max_delay],
        outputs=[],
    )

    return list(tab_components.values())
