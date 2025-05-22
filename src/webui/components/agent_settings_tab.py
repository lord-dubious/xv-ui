import json
import logging
import os
from typing import Any

import gradio as gr

from src.utils import config
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def update_model_dropdown(llm_provider):
    """
    Update the model name dropdown with predefined models for the selected provider.
    """
    # Use predefined models for the selected provider
    if llm_provider in config.model_names:
        return gr.Dropdown(
            choices=config.model_names[llm_provider],
            value=config.model_names[llm_provider][0],
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


def create_agent_settings_tab(webui_manager: WebuiManager):
    """
    Creates an agent settings tab.
    """
    env_settings = webui_manager.load_env_settings()

    def get_env_value(key: str, default: Any, type_cast=None):
        val = env_settings.get(key, default)
        if type_cast:
            try:
                if type_cast is bool:
                    return str(val).lower() == "true"
                return type_cast(val)
            except (ValueError, TypeError):
                return default
        return val

    input_components = set(webui_manager.get_components())  # noqa: F841
    tab_components = {}

    with gr.Group():
        with gr.Column():
            override_system_prompt = gr.Textbox(
                label="Override system prompt",
                lines=4,
                interactive=True,
                value=get_env_value("OVERRIDE_SYSTEM_PROMPT", ""),
            )
            extend_system_prompt = gr.Textbox(
                label="Extend system prompt",
                lines=4,
                interactive=True,
                value=get_env_value("EXTEND_SYSTEM_PROMPT", ""),
            )

    with gr.Group():
        mcp_json_file = gr.File(
            label="MCP server json", interactive=True, file_types=[".json"]
        )
        mcp_server_config = gr.Textbox(
            label="MCP server", lines=6, interactive=True, visible=False
        )

    with gr.Group():
        with gr.Row():
            initial_llm_provider = get_env_value("LLM_PROVIDER", "openai")
            llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="LLM Provider",
                value=initial_llm_provider,
                info="Select LLM provider for LLM",
                interactive=True,
            )

            initial_llm_model_choices = config.model_names.get(initial_llm_provider, [])
            initial_llm_model_name = get_env_value(
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
                value=get_env_value("LLM_TEMPERATURE", 0.6, float),
                step=0.1,
                label="LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True,
            )

            use_vision = gr.Checkbox(
                label="Use Vision",
                value=get_env_value("USE_VISION", True, bool),
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True,
            )

            ollama_num_ctx = gr.Slider(
                minimum=2**8,
                maximum=2**16,
                value=get_env_value("OLLAMA_NUM_CTX", 16000, int),
                step=1,
                label="Ollama Context Length",
                info="Controls max context length model needs to handle (less = faster)",
                visible=initial_llm_provider == "ollama",
                interactive=True,
            )

        with gr.Row():
            llm_base_url = gr.Textbox(
                label="Base URL",
                value=get_env_value(f"{initial_llm_provider.upper()}_ENDPOINT", ""),
                info="API endpoint URL (if required)",
            )
            llm_api_key = gr.Textbox(
                label="API Key",
                type="password",
                value=get_env_value(f"{initial_llm_provider.upper()}_API_KEY", ""),
                info="Your API key (auto-saved to .env)",
            )

    with gr.Group():
        with gr.Row():
            initial_planner_llm_provider = get_env_value("PLANNER_LLM_PROVIDER", None)
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
                value=get_env_value("PLANNER_LLM_TEMPERATURE", 0.6, float),
                step=0.1,
                label="Planner LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True,
            )

            planner_use_vision = gr.Checkbox(
                label="Use Vision(Planner LLM)",
                value=get_env_value("PLANNER_USE_VISION", False, bool),
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True,
            )

            planner_ollama_num_ctx = gr.Slider(
                minimum=2**8,
                maximum=2**16,
                value=get_env_value("PLANNER_OLLAMA_NUM_CTX", 16000, int),
                step=1,
                label="Ollama Context Length",
                info="Controls max context length model needs to handle (less = faster)",
                visible=initial_planner_llm_provider == "ollama",
                interactive=True,
            )

        with gr.Row():
            planner_llm_base_url = gr.Textbox(
                label="Base URL",
                value=get_env_value(
                    f"{initial_planner_llm_provider.upper()}_ENDPOINT", ""
                )
                if initial_planner_llm_provider
                else "",
                info="API endpoint URL (if required)",
            )
            planner_llm_api_key = gr.Textbox(
                label="API Key",
                type="password",
                value=get_env_value(
                    f"{initial_planner_llm_provider.upper()}_API_KEY", ""
                )
                if initial_planner_llm_provider
                else "",
                info="Your API key (auto-saved to .env)",
            )

    with gr.Row():
        max_steps = gr.Slider(
            minimum=1,
            maximum=1000,
            value=get_env_value("MAX_STEPS", 100, int),
            step=1,
            label="Max Run Steps",
            info="Maximum number of steps the agent will take",
            interactive=True,
        )
        max_actions = gr.Slider(
            minimum=1,
            maximum=100,
            value=get_env_value("MAX_ACTIONS", 10, int),
            step=1,
            label="Max Number of Actions",
            info="Maximum number of actions the agent will take per step",
            interactive=True,
        )

    with gr.Row():
        max_input_tokens = gr.Number(
            label="Max Input Tokens",
            value=get_env_value("MAX_INPUT_TOKENS", 128000, int),
            precision=0,
            interactive=True,
        )
        tool_calling_method = gr.Dropdown(
            label="Tool Calling Method",
            value=get_env_value("TOOL_CALLING_METHOD", "auto"),
            interactive=True,
            allow_custom_value=True,
            choices=["function_calling", "json_mode", "raw", "auto", "tools", "None"],
            visible=True,
        )

    with gr.Group():
        with gr.Row():
            step_delay_slider_minutes = gr.Slider(
                minimum=0,
                maximum=1440,
                value=get_env_value("STEP_DELAY_MINUTES", 0.0, float),
                step=1,
                label="Delay Between Steps (minutes)",
                info="Time to wait in minutes (0-1440) before executing each agent step.",
                interactive=True,
            )
            custom_step_delay_minutes = gr.Number(
                label="Custom Step Delay (mins)",
                value=get_env_value("STEP_DELAY_MINUTES", 0.0, float),
                minimum=0,
                maximum=1440,
                interactive=True,
            )
            action_delay_slider_minutes = gr.Slider(
                minimum=0,
                maximum=1440,
                value=get_env_value("ACTION_DELAY_MINUTES", 0.0, float),
                step=1,
                label="Delay Between Actions (minutes)",
                info="Time to wait in minutes (0-1440) between individual actions (if applicable; currently may not be supported by all agent bases).",
                interactive=True,
            )
            custom_action_delay_minutes = gr.Number(
                label="Custom Action Delay (mins)",
                value=get_env_value("ACTION_DELAY_MINUTES", 0.0, float),
                minimum=0,
                maximum=1440,
                interactive=True,
            )
            task_delay_slider_minutes = gr.Slider(
                minimum=0,
                maximum=1440,
                value=get_env_value("TASK_DELAY_MINUTES", 0.0, float),
                step=1,
                label="Delay Between Tasks (minutes)",
                info="Time to wait in minutes (0-1440) before starting a new task or run (interpretation may vary based on execution context).",
                interactive=True,
            )
            custom_task_delay_minutes = gr.Number(
                label="Custom Task Delay (mins)",
                value=get_env_value("TASK_DELAY_MINUTES", 0.0, float),
                minimum=0,
                maximum=1440,
                interactive=True,
            )

        # --- Step Delay Settings ---
        with gr.Row():
            step_enable_random_interval = get_env_value("STEP_ENABLE_RANDOM_INTERVAL", False, bool)
            step_enable_random_interval_checkbox = gr.Checkbox(
                label="Enable Random Interval for Step Delay",
                value=step_enable_random_interval,
                interactive=True,
            )
        with gr.Row():
            min_step_delay_slider_minutes = gr.Slider(
                label="Min Step Delay (minutes)",
                minimum=0,
                maximum=1440,
                value=get_env_value("STEP_MIN_DELAY_MINUTES", 0.0, float),
                step=1,
                interactive=step_enable_random_interval,
            )
            max_step_delay_slider_minutes = gr.Slider(
                label="Max Step Delay (minutes)",
                minimum=0,
                maximum=1440,
                value=get_env_value("STEP_MAX_DELAY_MINUTES", 0.0, float),
                step=1,
                interactive=step_enable_random_interval,
            )

        # --- Action Delay Settings ---
        with gr.Row():
            action_enable_random_interval = get_env_value("ACTION_ENABLE_RANDOM_INTERVAL", False, bool)
            action_enable_random_interval_checkbox = gr.Checkbox(
                label="Enable Random Interval for Action Delay",
                value=action_enable_random_interval,
                interactive=True,
            )
        with gr.Row():
            min_action_delay_slider_minutes = gr.Slider(
                label="Min Action Delay (minutes)",
                minimum=0,
                maximum=1440,
                value=get_env_value("ACTION_MIN_DELAY_MINUTES", 0.0, float),
                step=1,
                interactive=action_enable_random_interval,
            )
            max_action_delay_slider_minutes = gr.Slider(
                label="Max Action Delay (minutes)",
                minimum=0,
                maximum=1440,
                value=get_env_value("ACTION_MAX_DELAY_MINUTES", 0.0, float),
                step=1,
                interactive=action_enable_random_interval,
            )

        # --- Task Delay Settings ---
        with gr.Row():
            task_enable_random_interval = get_env_value("TASK_ENABLE_RANDOM_INTERVAL", False, bool)
            task_enable_random_interval_checkbox = gr.Checkbox(
                label="Enable Random Interval for Task Delay",
                value=task_enable_random_interval,
                interactive=True,
            )
        with gr.Row():
            min_task_delay_slider_minutes = gr.Slider(
                label="Min Task Delay (minutes)",
                minimum=0,
                maximum=1440,
                value=get_env_value("TASK_MIN_DELAY_MINUTES", 0.0, float),
                step=1,
                interactive=task_enable_random_interval,
            )
            max_task_delay_slider_minutes = gr.Slider(
                label="Max Task Delay (minutes)",
                minimum=0,
                maximum=1440,
                value=get_env_value("TASK_MAX_DELAY_MINUTES", 0.0, float),
                step=1,
                interactive=task_enable_random_interval,
            )

    tab_components.update(
        dict(
            override_system_prompt=override_system_prompt,
            extend_system_prompt=extend_system_prompt,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_temperature=llm_temperature,
            use_vision=use_vision,
            ollama_num_ctx=ollama_num_ctx,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            planner_llm_provider=planner_llm_provider,
            planner_llm_model_name=planner_llm_model_name,
            planner_llm_temperature=planner_llm_temperature,
            planner_use_vision=planner_use_vision,
            planner_ollama_num_ctx=planner_ollama_num_ctx,
            planner_llm_base_url=planner_llm_base_url,
            planner_llm_api_key=planner_llm_api_key,
            max_steps=max_steps,
            max_actions=max_actions,
            max_input_tokens=max_input_tokens,
            tool_calling_method=tool_calling_method,
            mcp_json_file=mcp_json_file,
            mcp_server_config=mcp_server_config,
            step_delay_minutes=step_delay_slider_minutes,
            custom_step_delay_minutes=custom_step_delay_minutes,
            step_enable_random_interval=step_enable_random_interval_checkbox,
            min_step_delay_minutes=min_step_delay_slider_minutes,
            max_step_delay_minutes=max_step_delay_slider_minutes,
            action_delay_minutes=action_delay_slider_minutes,
            custom_action_delay_minutes=custom_action_delay_minutes,
            action_enable_random_interval=action_enable_random_interval_checkbox,
            min_action_delay_minutes=min_action_delay_slider_minutes,
            max_action_delay_minutes=max_action_delay_slider_minutes,
            task_delay_minutes=task_delay_slider_minutes,
            custom_task_delay_minutes=custom_task_delay_minutes,
            task_enable_random_interval=task_enable_random_interval_checkbox,
            min_task_delay_minutes=min_task_delay_slider_minutes,
            max_task_delay_minutes=max_task_delay_slider_minutes,
        )
    )
    webui_manager.add_components("agent_settings", tab_components)

    llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=llm_provider,
        outputs=ollama_num_ctx,
    )
    llm_provider.change(
        lambda provider: update_model_dropdown(provider),
        inputs=[llm_provider],
        outputs=[llm_model_name],
    )
    planner_llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=[planner_llm_provider],
        outputs=[planner_ollama_num_ctx],
    )
    planner_llm_provider.change(
        lambda provider: update_model_dropdown(provider),
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
        step_delay_minutes=None, action_delay_minutes=None, task_delay_minutes=None,
        step_enable_random_interval=None, min_step_delay_minutes=None, max_step_delay_minutes=None,
        action_enable_random_interval=None, min_action_delay_minutes=None, max_action_delay_minutes=None,
        task_enable_random_interval=None, min_task_delay_minutes=None, max_task_delay_minutes=None
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
            env_vars["STEP_ENABLE_RANDOM_INTERVAL"] = str(step_enable_random_interval).lower()
        if min_step_delay_minutes is not None:
            env_vars["STEP_MIN_DELAY_MINUTES"] = str(min_step_delay_minutes)
        if max_step_delay_minutes is not None:
            env_vars["STEP_MAX_DELAY_MINUTES"] = str(max_step_delay_minutes)

        # Action random interval settings
        if action_enable_random_interval is not None:
            env_vars["ACTION_ENABLE_RANDOM_INTERVAL"] = str(action_enable_random_interval).lower()
        if min_action_delay_minutes is not None:
            env_vars["ACTION_MIN_DELAY_MINUTES"] = str(min_action_delay_minutes)
        if max_action_delay_minutes is not None:
            env_vars["ACTION_MAX_DELAY_MINUTES"] = str(max_action_delay_minutes)

        # Task random interval settings
        if task_enable_random_interval is not None:
            env_vars["TASK_ENABLE_RANDOM_INTERVAL"] = str(task_enable_random_interval).lower()
        if min_task_delay_minutes is not None:
            env_vars["TASK_MIN_DELAY_MINUTES"] = str(min_task_delay_minutes)
        if max_task_delay_minutes is not None:
            env_vars["TASK_MAX_DELAY_MINUTES"] = str(max_task_delay_minutes)

        webui_manager.save_env_settings(env_vars)

    # Connect change events to auto-save functions
    llm_provider.change(
        fn=lambda provider: save_llm_api_setting(provider=provider),
        inputs=[llm_provider],
        outputs=[],
    )

    llm_api_key.change(
        fn=lambda api_key: save_llm_api_setting(api_key=api_key),
        inputs=[llm_api_key],
        outputs=[],
    )

    llm_base_url.change(
        fn=lambda base_url: save_llm_api_setting(base_url=base_url),
        inputs=[llm_base_url],
        outputs=[],
    )

    planner_llm_provider.change(
        fn=lambda provider: save_planner_api_setting(provider=provider),
        inputs=[planner_llm_provider],
        outputs=[],
    )

    planner_llm_api_key.change(
        fn=lambda api_key: save_planner_api_setting(api_key=api_key),
        inputs=[planner_llm_api_key],
        outputs=[],
    )

    planner_llm_base_url.change(
        fn=lambda base_url: save_planner_api_setting(base_url=base_url),
        inputs=[planner_llm_base_url],
        outputs=[],
    )

    # Connect change events for additional planner settings to the new save function
    planner_llm_model_name.change(
        fn=lambda model_name: save_planner_settings(model_name=model_name),
        inputs=[planner_llm_model_name],
        outputs=[],
    )

    planner_llm_temperature.change(
        fn=lambda temperature: save_planner_settings(temperature=temperature),
        inputs=[planner_llm_temperature],
        outputs=[],
    )

    planner_use_vision.change(
        fn=lambda use_vision: save_planner_settings(use_vision=use_vision),
        inputs=[planner_use_vision],
        outputs=[],
    )

    planner_ollama_num_ctx.change(
        fn=lambda ollama_num_ctx: save_planner_settings(ollama_num_ctx=ollama_num_ctx),
        inputs=[planner_ollama_num_ctx],
        outputs=[],
    )

    # Setup synchronized delay settings using the helper function
    setup_synchronized_delay_setting(
        step_delay_slider_minutes,
        custom_step_delay_minutes,
        'step_delay_minutes',
        save_time_interval_settings
    )
    setup_synchronized_delay_setting(
        action_delay_slider_minutes,
        custom_action_delay_minutes,
        'action_delay_minutes',
        save_time_interval_settings
    )
    setup_synchronized_delay_setting(
        task_delay_slider_minutes,
        custom_task_delay_minutes,
        'task_delay_minutes',
        save_time_interval_settings
    )

    # --- Define interactivity update logic ---
    def update_delay_interactivity(checkbox_state):
        # If checkbox is True (random interval enabled):
        # - Min/Max sliders are interactive
        # - Fixed delay inputs are NOT interactive
        # If checkbox is False (random interval disabled):
        # - Min/Max sliders are NOT interactive
        # - Fixed delay inputs are interactive
        return [
            gr.update(interactive=checkbox_state),  # For min_slider
            gr.update(interactive=checkbox_state),  # For max_slider
            gr.update(interactive=not checkbox_state),  # For fixed_delay_number_input
            gr.update(interactive=not checkbox_state),  # For fixed_delay_descriptive_slider
        ]

    # --- Connect interactivity logic for Step Delay ---
    step_enable_random_interval_checkbox.change(
        fn=update_delay_interactivity,
        inputs=[step_enable_random_interval_checkbox],
        outputs=[
            min_step_delay_slider_minutes,
            max_step_delay_slider_minutes,
            custom_step_delay_minutes,
            step_delay_slider_minutes,
        ],
    )

    # --- Connect interactivity logic for Action Delay ---
    action_enable_random_interval_checkbox.change(
        fn=update_delay_interactivity,
        inputs=[action_enable_random_interval_checkbox],
        outputs=[
            min_action_delay_slider_minutes,
            max_action_delay_slider_minutes,
            custom_action_delay_minutes,
            action_delay_slider_minutes,
        ],
    )

    # --- Connect interactivity logic for Task Delay ---
    task_enable_random_interval_checkbox.change(
        fn=update_delay_interactivity,
        inputs=[task_enable_random_interval_checkbox],
        outputs=[
            min_task_delay_slider_minutes,
            max_task_delay_slider_minutes,
            custom_task_delay_minutes,
            task_delay_slider_minutes,
        ],
    )

    # --- Connect save logic for new interval components ---
    # Step delay random interval
    step_enable_random_interval_checkbox.change(
        fn=lambda x: save_time_interval_settings(step_enable_random_interval=x),
        inputs=[step_enable_random_interval_checkbox],
        outputs=[],
    )
    min_step_delay_slider_minutes.change(
        fn=lambda x: save_time_interval_settings(min_step_delay_minutes=x),
        inputs=[min_step_delay_slider_minutes],
        outputs=[],
    )
    max_step_delay_slider_minutes.change(
        fn=lambda x: save_time_interval_settings(max_step_delay_minutes=x),
        inputs=[max_step_delay_slider_minutes],
        outputs=[],
    )

    # Action delay random interval
    action_enable_random_interval_checkbox.change(
        fn=lambda x: save_time_interval_settings(action_enable_random_interval=x),
        inputs=[action_enable_random_interval_checkbox],
        outputs=[],
    )
    min_action_delay_slider_minutes.change(
        fn=lambda x: save_time_interval_settings(min_action_delay_minutes=x),
        inputs=[min_action_delay_slider_minutes],
        outputs=[],
    )
    max_action_delay_slider_minutes.change(
        fn=lambda x: save_time_interval_settings(max_action_delay_minutes=x),
        inputs=[max_action_delay_slider_minutes],
        outputs=[],
    )

    # Task delay random interval
    task_enable_random_interval_checkbox.change(
        fn=lambda x: save_time_interval_settings(task_enable_random_interval=x),
        inputs=[task_enable_random_interval_checkbox],
        outputs=[],
    )
    min_task_delay_slider_minutes.change(
        fn=lambda x: save_time_interval_settings(min_task_delay_minutes=x),
        inputs=[min_task_delay_slider_minutes],
        outputs=[],
    )
    max_task_delay_slider_minutes.change(
        fn=lambda x: save_time_interval_settings(max_task_delay_minutes=x),
        inputs=[max_task_delay_slider_minutes],
        outputs=[],
    )

    return list(tab_components.values())
