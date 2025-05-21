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

    return list(tab_components.values())
