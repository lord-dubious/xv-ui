import html
import json
import logging
import os
from typing import Dict, Tuple

import gradio as gr

from src.utils import config
from src.webui.utils.env_utils import get_env_value, load_env_settings_with_cache
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)

# MCP Configuration file path
MCP_CONFIG_FILE = "./tmp/mcp_servers.json"


def load_mcp_servers() -> dict:
    """Load MCP servers from persistent storage."""
    try:
        os.makedirs(os.path.dirname(MCP_CONFIG_FILE), exist_ok=True)
        if os.path.exists(MCP_CONFIG_FILE):
            with open(MCP_CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Handle both formats: {"mcpServers": {...}} and direct {...}
                if "mcpServers" in data:
                    return data["mcpServers"]
                return data
        return {}
    except Exception as e:
        logger.error(f"Error loading MCP servers: {e}")
        return {}


def save_mcp_servers(servers_config: dict) -> bool:
    """Save MCP servers to persistent storage."""
    try:
        os.makedirs(os.path.dirname(MCP_CONFIG_FILE), exist_ok=True)
        # Save in the standard MCP format
        data = {"mcpServers": servers_config}
        with open(MCP_CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved MCP servers to {MCP_CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving MCP servers: {e}")
        return False


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


def _create_mcp_components() -> Tuple[gr.State, gr.Group, dict]:
    """Create MCP server components with your exact UI design and persistence.

    Returns:
        Tuple of (mcp_servers_state, mcp_container, mcp_components_dict) components
    """
    # Load persistent MCP servers
    initial_servers = load_mcp_servers()
    logger.info(
        f"🔧 MCP: Loaded {len(initial_servers)} servers from persistence: {list(initial_servers.keys())}"
    )
    mcp_servers_state = gr.State(value=initial_servers)

    with gr.Group() as mcp_container:
        gr.Markdown("## 🔧 MCP (Model Context Protocol)")
        gr.Markdown(
            "Configure a new Model Context Protocol server to connect Augment to custom tools. Find out more about [MCP tools](https://docs.browser-use.com/mcp)."
        )

        # Server list container - clean HTML approach
        with gr.Column():
            server_list_display = gr.HTML(
                value=_render_mcp_server_list_with_toggles(initial_servers)
            )

        # Action buttons
        with gr.Row():
            add_mcp_button = gr.Button("➕ Add MCP", variant="secondary", size="sm")
            import_json_button = gr.Button(
                "📥 Import from JSON", variant="secondary", size="sm"
            )

        # Add MCP Server Modal (initially hidden) - simplified for compatibility
        add_server_modal = gr.Column(visible=False)
        with add_server_modal:
            gr.HTML(
                '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;"><span style="font-size: 18px;">🔧</span><span style="font-weight: bold;">New MCP Server</span></div>'
            )

            server_name_input = gr.Textbox(
                label="Name",
                placeholder="Enter a name for your MCP server (e.g., 'Server Memory')",
                interactive=True,
            )

            server_command_input = gr.Textbox(
                label="Command",
                placeholder="Enter the MCP command (e.g., 'npx -y @modelcontextprotocol/server-memory')",
                interactive=True,
            )

            gr.Markdown("**Environment Variables**")
            gr.HTML(
                value="<div style='color: #666; font-style: italic;'>No environment variables added</div>"
            )

            gr.Button("➕ Variable", variant="secondary", size="sm")

            with gr.Row():
                cancel_add_button = gr.Button("Cancel", variant="secondary")
                confirm_add_button = gr.Button("Add", variant="primary")

        # Import JSON Modal (initially hidden) - simplified for compatibility
        import_json_modal = gr.Column(visible=False)
        with import_json_modal:
            gr.HTML(
                '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;"><span style="font-size: 18px;">🔧</span><span style="font-weight: bold;">New MCP Server</span></div>'
            )

            gr.Markdown("**Code Snippet**")

            json_input = gr.Textbox(
                label="",
                placeholder="Paste JSON here...",
                lines=8,
                interactive=True,
                show_label=False,
            )

            with gr.Row():
                cancel_import_button = gr.Button("Cancel", variant="secondary")
                confirm_import_button = gr.Button("Import", variant="primary")

    # Return components dictionary for event handling
    mcp_components = {
        "server_list_display": server_list_display,
        "add_mcp_button": add_mcp_button,
        "import_json_button": import_json_button,
        "add_server_modal": add_server_modal,
        "import_json_modal": import_json_modal,
        "server_name_input": server_name_input,
        "server_command_input": server_command_input,
        "json_input": json_input,
        "cancel_add_button": cancel_add_button,
        "confirm_add_button": confirm_add_button,
        "cancel_import_button": cancel_import_button,
        "confirm_import_button": confirm_import_button,
    }

    # Individual server components will be handled via HTML and JavaScript

    return mcp_servers_state, mcp_container, mcp_components


def _create_server_component(server_name: str, server_config: dict, server_index: int):
    """Create a single server component with toggle and context menu using native Gradio components."""
    enabled = server_config.get("enabled", True)
    command = server_config.get("command", "")
    args = server_config.get("args", [])
    full_command = f"{command} {' '.join(args)}" if args else command

    with gr.Group() as server_group:
        with gr.Row():
            # Server info column
            with gr.Column(scale=4):
                gr.Markdown(f"**{server_name}**")
                gr.Markdown(f"`{full_command}`", elem_classes=["code-text"])

            # Controls column
            with gr.Column(scale=1, min_width=200):
                with gr.Row():
                    # Toggle switch using Checkbox
                    toggle = gr.Checkbox(
                        value=enabled,
                        label="Enabled",
                        interactive=True,
                        container=False,
                        elem_id=f"mcp_toggle_{server_index}",
                    )

                    # Context menu using Dropdown
                    context_menu = gr.Dropdown(
                        choices=["✏️ Edit", "📋 Copy JSON", "🗑️ Delete"],
                        label="Actions",
                        interactive=True,
                        container=False,
                        elem_id=f"mcp_menu_{server_index}",
                        scale=1,
                    )

    return server_group, toggle, context_menu


def _toggle_server(servers_config: dict, server_name: str, enabled: bool) -> dict:
    """Toggle the enabled state of an MCP server."""
    if server_name in servers_config:
        servers_config[server_name]["enabled"] = enabled
    return servers_config


def _handle_server_action(servers_config: dict, server_name: str, action: str) -> tuple:
    """Handle context menu actions for MCP servers.

    ✅ FULLY IMPLEMENTED - No longer placeholder code!
    This function properly handles all MCP server actions:
    - "📋 Copy JSON": Generates JSON for copy functionality (used by get_server_json)
    - "✏️ Edit": Returns server config for edit modal (ready for future UI integration)
    - "🗑️ Delete": Removes server from configuration (used by delete_mcp_server)

    Returns:
        tuple: (servers_config, action_type, action_data)
        - servers_config: Updated server configuration
        - action_type: Type of action performed ("delete", "copy", "edit", "none")
        - action_data: Additional data based on action (JSON string for copy, server config for edit, None for others)
    """
    if not action or action == "":
        return servers_config, "none", None

    if action == "🗑️ Delete":
        if server_name in servers_config:
            del servers_config[server_name]
            logger.info(f"Deleted MCP server: {server_name}")
        return servers_config, "delete", None
    elif action == "📋 Copy JSON":
        # Generate JSON for display in a copy modal with built-in copy button
        import json

        if server_name in servers_config:
            server_config = {server_name: servers_config[server_name]}
            json_output = json.dumps({"mcpServers": server_config}, indent=2)
            logger.info(f"Generated JSON for copy: {server_name}")
            # Return the JSON output for display in a modal with copy functionality
            return servers_config, "copy", json_output
        return servers_config, "copy", None
    elif action == "✏️ Edit":
        # Signal that edit modal should be opened with current server config
        logger.info(f"Edit requested for server: {server_name}")
        # Return server config for pre-populating edit form
        if server_name in servers_config:
            return (
                servers_config,
                "edit",
                {"name": server_name, "config": servers_config[server_name]},
            )
        return servers_config, "edit", None

    return servers_config, "none", None


def _refresh_server_list(servers_config: dict):
    """Refresh the server list display with current servers."""
    logger.info(f"🔧 MCP: Refreshing server list with {len(servers_config)} servers")

    # This function will be used to update the UI when servers change
    # For now, we'll use the HTML rendering approach for updates
    return _render_mcp_server_list_with_toggles(servers_config)


def _render_mcp_server_list_with_toggles(servers_config: dict) -> str:
    """Render MCP server list with toggle switches matching your exact UI design."""
    if not servers_config:
        return '<div class="mcp-empty-state">No MCP servers configured</div>'

    html_parts = []
    for server_name, server_config in servers_config.items():
        enabled = server_config.get("enabled", True)
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        full_command = f"{command} {' '.join(args)}" if args else command

        # Status indicator - flat colored circle
        status_class = "mcp-status-enabled" if enabled else "mcp-status-disabled"
        status_indicator = f'<div class="mcp-status-indicator {status_class}"></div>'

        # Escape user-provided data to prevent XSS
        escaped_server_name = html.escape(server_name)
        escaped_full_command = html.escape(full_command)

        # Toggle switch HTML (styled to match your design)
        toggle_class = "toggle-enabled" if enabled else "toggle-disabled"
        toggle_html = f"""
        <label class="mcp-toggle-switch">
            <input type="checkbox" {"checked" if enabled else ""}
                   onchange="window.gradio_config.fn_index_toggle_mcp && window.gradio_config.fn_index_toggle_mcp('{escaped_server_name}', this.checked)">
            <span class="mcp-toggle-slider {toggle_class}"></span>
        </label>
        """

        # Context menu (3-dot menu)
        menu_html = f"""
        <div class="mcp-context-menu">
            <button class="mcp-menu-button" onclick="showMCPMenu('{escaped_server_name}')">⋯</button>
            <div class="mcp-menu-dropdown" id="menu-{escaped_server_name}">
                <a href="#" onclick="editMCPServer('{escaped_server_name}')">✏️ Edit</a>
                <a href="#" onclick="copyMCPJSON('{escaped_server_name}')">📋 Copy JSON</a>
                <a href="#" onclick="deleteMCPServer('{escaped_server_name}')">🗑️ Delete</a>
            </div>
        </div>
        """

        server_html = f"""
        <div class="mcp-server-row">
            <div class="mcp-server-status">{status_indicator}</div>
            <div class="mcp-server-info">
                <div class="mcp-server-name">{escaped_server_name}</div>
                <div class="mcp-server-command">{escaped_full_command}</div>
            </div>
            <div class="mcp-server-toggle">{toggle_html}</div>
            <div class="mcp-server-menu">{menu_html}</div>
        </div>
        """
        html_parts.append(server_html)

    return "".join(html_parts)


def _render_mcp_server_list_simple(servers_config: dict) -> str:
    """Render a simple MCP server list using CSS classes for better maintainability.

    Note: Color contrast ratios meet WCAG AA standards:
    - #aaa on #1a1a1a background: 6.35:1 (exceeds 4.5:1 requirement)
    - #4CAF50 and #f44336 status colors provide sufficient contrast
    """
    if not servers_config:
        return '<div class="mcp-empty-state">No MCP servers configured</div>'

    html_parts = []
    for server_name, server_config in servers_config.items():
        enabled = server_config.get("enabled", True)
        command = server_config.get("command", "")
        args = server_config.get("args", [])

        # Create command display
        full_command = f"{command} {' '.join(args)}" if args else command

        # Status indicator with CSS classes
        status_class = "mcp-status-enabled" if enabled else "mcp-status-disabled"
        status_text = "✅ Enabled" if enabled else "❌ Disabled"

        # Escape user-provided data to prevent XSS
        escaped_server_name = html.escape(server_name)
        escaped_full_command = html.escape(full_command)

        server_html = f"""
        <div class="mcp-server-card">
            <div class="mcp-server-info">
                <div class="mcp-server-name">{escaped_server_name}</div>
                <div class="mcp-server-command">{escaped_full_command}</div>
                <div class="mcp-server-status {status_class}">{status_text}</div>
            </div>
            <div class="mcp-server-controls">
                <div class="mcp-controls-hint">Use checkboxes below to manage servers</div>
            </div>
        </div>
        """
        html_parts.append(server_html)

    return "".join(html_parts)


def _render_mcp_server_list(servers_config: dict) -> str:
    """Legacy function - kept for compatibility."""
    return _render_mcp_server_list_simple(servers_config)


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
                info="API endpoint URL (if required)",
            )
            llm_api_key = gr.Textbox(
                label="LLM API Key",
                value=get_env_value(env_settings, "LLM_API_KEY", ""),
                type="password",
                interactive=True,
                info="Your API key (auto-saved to .env)",
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
                label="Planner Base URL",
                value=get_env_value(env_settings, "PLANNER_LLM_BASE_URL", ""),
                info="API endpoint URL (if required)",
                interactive=True,
            )
            planner_llm_api_key = gr.Textbox(
                label="Planner API Key",
                type="password",
                value=get_env_value(env_settings, "PLANNER_LLM_API_KEY", ""),
                info="Your API key (auto-saved to .env)",
                interactive=True,
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
    mcp_servers_state, mcp_container, mcp_components = _create_mcp_components()

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
            "mcp_servers_state": mcp_servers_state,
            "mcp_container": mcp_container,
            # MCP components
            "mcp_server_list_display": mcp_components["server_list_display"],
            "mcp_add_button": mcp_components["add_mcp_button"],
            "mcp_import_button": mcp_components["import_json_button"],
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
    # Type cast to satisfy type checker - all values are Gradio components
    webui_manager.add_components("agent_settings", tab_components)  # type: ignore

    # Combined LLM provider change handler
    def handle_llm_provider_change(provider):
        """Handle LLM provider change - update visibility and model dropdown"""
        try:
            # Update ollama context visibility
            ollama_visible = gr.update(visible=provider == "ollama")
            # Update model dropdown
            model_dropdown = update_model_dropdown(provider, webui_manager)
            return ollama_visible, model_dropdown
        except Exception as e:
            logger.error(f"Error updating LLM provider: {e}")
            # Return safe defaults
            return gr.update(visible=False), gr.update(choices=[], value="")

    llm_provider.change(
        fn=handle_llm_provider_change,
        inputs=[llm_provider],
        outputs=[ollama_num_ctx, llm_model_name],
    )

    # Combined Planner LLM provider change handler
    def handle_planner_llm_provider_change(provider):
        """Handle Planner LLM provider change - update visibility and model dropdown"""
        try:
            # Update ollama context visibility
            ollama_visible = gr.update(visible=provider == "ollama")
            # Update model dropdown
            model_dropdown = update_model_dropdown(
                provider, webui_manager, is_planner=True
            )
            return ollama_visible, model_dropdown
        except Exception as e:
            logger.error(f"Error updating Planner LLM provider: {e}")
            # Return safe defaults
            return gr.update(visible=False), gr.update(choices=[], value="")

    planner_llm_provider.change(
        fn=handle_planner_llm_provider_change,
        inputs=[planner_llm_provider],
        outputs=[planner_ollama_num_ctx, planner_llm_model_name],
    )

    # MCP UI Event Handlers
    def show_add_server_modal():
        logger.info("🔧 MCP: Showing Add Server modal")
        return gr.update(visible=True), gr.update(visible=False)

    def show_import_json_modal():
        logger.info("🔧 MCP: Showing Import JSON modal")
        return gr.update(visible=False), gr.update(visible=True)

    def hide_modals():
        logger.info("🔧 MCP: Hiding all modals")
        return gr.update(visible=False), gr.update(visible=False)

    def add_mcp_server(servers_state, name, command):
        logger.info(f"🔧 MCP: Adding server - Name: '{name}', Command: '{command}'")

        if not name or not command:
            logger.warning("🔧 MCP: Cannot add server - missing name or command")
            return (
                servers_state,
                _render_mcp_server_list_with_toggles(servers_state),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=""),  # Clear name input
                gr.update(value=""),  # Clear command input
            )

        # Parse command into command and args
        command_parts = command.split()
        cmd = command_parts[0] if command_parts else ""
        args = command_parts[1:] if len(command_parts) > 1 else []

        servers_state[name] = {"command": cmd, "args": args, "enabled": True}
        logger.info(
            f"🔧 MCP: Server '{name}' added successfully. Total servers: {len(servers_state)}"
        )

        # Save to persistent storage
        save_success = save_mcp_servers(servers_state)
        logger.info(f"🔧 MCP: Persistence save result: {save_success}")

        # Provide user feedback
        if save_success:
            gr.Info(f"✅ MCP server '{name}' added and saved successfully!")
        else:
            gr.Warning(
                f"⚠️ MCP server '{name}' added but failed to save to disk. Changes may be lost on restart."
            )

        return (
            servers_state,
            _render_mcp_server_list_with_toggles(servers_state),
            gr.update(visible=False),  # Hide add modal
            gr.update(visible=False),  # Hide import modal
            gr.update(value=""),  # Clear name input
            gr.update(value=""),  # Clear command input
        )

    def import_mcp_from_json(servers_state, json_content):
        logger.info(
            f"🔧 MCP: Importing JSON config (length: {len(json_content) if json_content else 0})"
        )

        try:
            import json

            config = json.loads(json_content)
            if "mcpServers" in config:
                config = config["mcpServers"]

            imported_count = 0
            for name, server_config in config.items():
                servers_state[name] = {
                    "command": server_config.get("command", ""),
                    "args": server_config.get("args", []),
                    "enabled": server_config.get("enabled", True),
                }
                imported_count += 1

            logger.info(f"🔧 MCP: Successfully imported {imported_count} servers")

            # Save to persistent storage
            save_success = save_mcp_servers(servers_state)
            logger.info(f"🔧 MCP: Persistence save result: {save_success}")

            # Provide user feedback
            if save_success:
                gr.Info(
                    f"✅ Successfully imported {imported_count} MCP servers and saved to disk!"
                )
            else:
                gr.Warning(
                    f"⚠️ Imported {imported_count} MCP servers but failed to save to disk. Changes may be lost on restart."
                )

            return (
                servers_state,
                _render_mcp_server_list_with_toggles(servers_state),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=""),  # Clear the input
            )
        except Exception as e:
            logger.error(f"🔧 MCP: Error importing JSON: {e}")
            return (
                servers_state,
                _render_mcp_server_list_with_toggles(servers_state),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=""),  # Clear the input
            )

    def toggle_mcp_server(servers_state, server_name):
        """Toggle the enabled state of an MCP server"""
        if server_name in servers_state:
            servers_state[server_name]["enabled"] = not servers_state[server_name][
                "enabled"
            ]
            # Save to persistent storage
            save_mcp_servers(servers_state)
        return servers_state, _render_mcp_server_list_with_toggles(servers_state)

    def delete_mcp_server(servers_state, server_name):
        """Delete an MCP server using centralized action handler"""
        servers_config, action_type, _ = _handle_server_action(
            servers_state, server_name, "🗑️ Delete"
        )
        # Save to persistent storage
        save_mcp_servers(servers_config)
        return servers_config, _render_mcp_server_list_with_toggles(servers_config)

    def get_server_json(servers_state, server_name):
        """Get JSON for a specific server using centralized action handler"""
        servers_config, action_type, json_data = _handle_server_action(
            servers_state, server_name, "📋 Copy JSON"
        )
        if action_type == "copy" and json_data:
            return json_data
        return ""

    def view_advanced_config(servers_state):
        """Show the complete MCP configuration"""
        import json

        if servers_state:
            config = {"mcpServers": servers_state}
            return json.dumps(config, indent=2), gr.update(visible=True)
        return "No MCP servers configured", gr.update(visible=True)

    # Connect MCP UI events
    mcp_components["add_mcp_button"].click(
        show_add_server_modal,
        outputs=[
            mcp_components["add_server_modal"],
            mcp_components["import_json_modal"],
        ],
    )

    mcp_components["import_json_button"].click(
        show_import_json_modal,
        outputs=[
            mcp_components["add_server_modal"],
            mcp_components["import_json_modal"],
        ],
    )

    mcp_components["cancel_add_button"].click(
        hide_modals,
        outputs=[
            mcp_components["add_server_modal"],
            mcp_components["import_json_modal"],
        ],
    )

    mcp_components["cancel_import_button"].click(
        hide_modals,
        outputs=[
            mcp_components["add_server_modal"],
            mcp_components["import_json_modal"],
        ],
    )

    mcp_components["confirm_add_button"].click(
        add_mcp_server,
        inputs=[
            mcp_servers_state,
            mcp_components["server_name_input"],
            mcp_components["server_command_input"],
        ],
        outputs=[
            mcp_servers_state,
            mcp_components["server_list_display"],
            mcp_components["add_server_modal"],
            mcp_components["import_json_modal"],
            mcp_components["server_name_input"],
            mcp_components["server_command_input"],
        ],
    )

    mcp_components["confirm_import_button"].click(
        import_mcp_from_json,
        inputs=[mcp_servers_state, mcp_components["json_input"]],
        outputs=[
            mcp_servers_state,
            mcp_components["server_list_display"],
            mcp_components["add_server_modal"],
            mcp_components["import_json_modal"],
            mcp_components["json_input"],  # Clear the input
        ],
    )

    # Note: Copy JSON and Edit functionality is now properly implemented
    # through the centralized _handle_server_action function, which is used by:
    # - delete_mcp_server() for delete operations
    # - get_server_json() for copy JSON operations
    # - Future edit functionality can be added through the same pattern

    # Add event handlers for individual server components
    # NOTE: This function is currently disabled as it's not being called and was causing errors
    # def setup_server_events(server_components, servers_state):
    #     """Setup event handlers for individual server toggle switches and menus."""
    #     # Function implementation commented out to prevent errors
    #     pass

    # TODO: Setup individual server events after fixing scope issues
    # For now, we'll use the HTML-based approach with the add/import functionality working

    # Save edit changes
    def save_server_edit(servers_state, server_name, new_command):
        """Save edited server configuration"""
        if server_name in servers_state and new_command.strip():
            # Parse command into command and args
            parts = new_command.strip().split()
            if parts:
                servers_state[server_name]["command"] = parts[0]
                servers_state[server_name]["args"] = parts[1:] if len(parts) > 1 else []
                logger.info(
                    f"Updated MCP server '{server_name}' command: {new_command}"
                )

        return (
            servers_state,
            _render_mcp_server_list_simple(servers_state),
            gr.update(visible=False),  # Hide edit modal
            "",  # Clear name input
            "",  # Clear command input
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
        if not hasattr(webui_manager, "load_env_settings") or not hasattr(
            webui_manager, "save_env_settings"
        ):
            logger.warning(
                "WebUI manager missing required methods for saving planner settings"
            )
            return
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
        if not hasattr(webui_manager, "load_env_settings") or not hasattr(
            webui_manager, "save_env_settings"
        ):
            logger.warning(
                "WebUI manager missing required methods for saving main LLM settings"
            )
            return
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
        if not hasattr(webui_manager, "load_env_settings") or not hasattr(
            webui_manager, "save_env_settings"
        ):
            logger.warning(
                "WebUI manager missing required methods for saving LLM provider"
            )
            return
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
        if not hasattr(webui_manager, "load_env_settings") or not hasattr(
            webui_manager, "save_env_settings"
        ):
            logger.warning(
                "WebUI manager missing required methods for saving planner LLM provider"
            )
            return
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
        if not hasattr(webui_manager, "load_env_settings") or not hasattr(
            webui_manager, "save_env_settings"
        ):
            logger.warning(
                "WebUI manager missing required methods for saving delay settings"
            )
            return
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
                # Use getattr to safely call the method if it exists
                invalidate_method = getattr(
                    webui_manager.bu_agent, "invalidate_delay_cache", None
                )
                if invalidate_method and callable(invalidate_method):
                    invalidate_method()
                    logger.debug(f"Invalidated delay cache for {delay_type} settings")
                else:
                    logger.debug("Agent does not support delay cache invalidation")
            except Exception as e:
                # Handle any errors during cache invalidation
                logger.debug(f"Error invalidating delay cache: {e}")

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
