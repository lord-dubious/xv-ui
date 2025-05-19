import json
import html
import shlex
import gradio as gr
from src.webui.webui_manager import WebuiManager
from src.utils import config
import logging

logger = logging.getLogger(__name__)


def update_model_dropdown(llm_provider):
    """
    Update the model name dropdown with predefined models for the selected provider.
    """
    # Use predefined models for the selected provider
    if llm_provider in config.model_names:
        return gr.Dropdown(choices=config.model_names[llm_provider], value=config.model_names[llm_provider][0],
                           interactive=True)
    else:
        return gr.Dropdown(choices=[], value="", interactive=True, allow_custom_value=True)


def get_mcp_server_names(webui_manager: WebuiManager):
    """
    Get the list of MCP server names for the dropdown.
    Returns a sorted list for consistent display order.
    """
    mcp_servers = webui_manager.get_mcp_servers()
    server_names = sorted(mcp_servers.keys())
    logger.debug(f"MCP server names: {server_names}")
    return server_names


def get_mcp_server_details(server_name: str, webui_manager: WebuiManager):
    """
    Get the details of an MCP server.
    """
    mcp_servers = webui_manager.get_mcp_servers()
    if not server_name or server_name not in mcp_servers:
        return "", "", "", gr.update(visible=False)

    server_config = mcp_servers[server_name]
    command = server_config.get("command", "")
    args = server_config.get("args", [])
    env = server_config.get("env", {})

    args_str = json.dumps(args, indent=2)
    env_str = json.dumps(env, indent=2) if env else ""

    return command, args_str, env_str, gr.update(visible=True)


def get_full_mcp_config_json(webui_manager: WebuiManager):
    """
    Get the full MCP server configuration as a formatted JSON string.
    """
    mcp_servers = webui_manager.get_mcp_servers()
    full_config = {"mcpServers": mcp_servers}
    return json.dumps(full_config, indent=2)


def get_mcp_servers_list(webui_manager: WebuiManager):
    """
    Get the list of MCP servers for display.
    Returns a list of dictionaries with server details.
    """
    try:
        mcp_servers = webui_manager.get_mcp_servers()
        logger.debug(f"Raw MCP servers data: {json.dumps(mcp_servers, indent=2)}")
        servers_list = []

        # Sort server names for consistent display order
        sorted_names = sorted(mcp_servers.keys())

        for name in sorted_names:
            config = mcp_servers[name]
            command = config.get("command", "")
            args = config.get("args", [])
            env = config.get("env", {})
            enabled = config.get("enabled", True)  # Default to enabled

            # Format the command with arguments for display
            display_command = command
            if args:
                args_str = " ".join(args)
                display_command = f"{command} {args_str}"

            server_entry = {
                "name": name,
                "command": display_command,
                "raw_command": command,
                "args": args,
                "env": env,
                "enabled": enabled
            }
            servers_list.append(server_entry)
            logger.debug(f"Added server to list: {name}")

        logger.debug(f"Processed {len(servers_list)} MCP servers")
        return servers_list
    except Exception as e:
        logger.error(f"Error getting MCP servers list: {e}", exc_info=True)
        return []


def parse_command_string(command_str: str):
    """
    Parse a command string into command and args.
    Uses shlex.split to properly handle quoted arguments with spaces.

    Args:
        command_str: The command string (e.g., 'npx -y @modelcontextprotocol/server-memory')

    Returns:
        tuple: (command, args)
    """
    try:
        parts = shlex.split(command_str.strip())
        if not parts:
            return "", []

        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        return command, args
    except ValueError as e:
        # Handle malformed quoted strings
        logger.warning(f"Error parsing command string: {e}")
        return "", []


def render_mcp_servers_html(webui_manager: WebuiManager):
    """
    Render the MCP servers as HTML for display.

    Args:
        webui_manager: The WebUI manager

    Returns:
        str: HTML representation of the MCP servers
    """
    logger.debug("Rendering MCP servers HTML")
    servers = get_mcp_servers_list(webui_manager)
    logger.debug(f"Found {len(servers)} MCP servers to render")

    if not servers:
        logger.debug("No MCP servers found to render")
        return "<div class='mcp-servers-empty'>No MCP servers configured</div>"

    html = "<div class='mcp-servers-container'>"

    for server in servers:
        name = server["name"]
        command = server["command"]
        enabled = server["enabled"]
        logger.debug(f"Rendering server: {name}, enabled: {enabled}")

        # Escape HTML to prevent XSS
        escaped_name = html.escape(name)
        escaped_command = html.escape(command)

        # Create a unique ID for the dropdown (safe for HTML attributes)
        safe_name = escaped_name.replace(' ', '-').replace('"', '').replace("'", "")
        dropdown_id = f"dropdown-{safe_name}"

        # Create a toggle switch for the enabled status
        toggle_html = f"""
        <label class="switch">
            <input type="checkbox" data-server="{escaped_name}" {'checked' if enabled else ''}>
            <span class="slider round"></span>
        </label>
        """

        # Create the server entry with dropdown menu
        server_html = f"""
        <div class="mcp-server-entry" data-server="{escaped_name}">
            <div class="mcp-server-info">
                <div class="mcp-server-name">{escaped_name}</div>
                <div class="mcp-server-command">{escaped_command}</div>
            </div>
            <div class="mcp-server-actions">
                {toggle_html}
                <div class="dropdown">
                    <button class="mcp-server-more-btn" onclick="toggleDropdown('{dropdown_id}', event)">...</button>
                    <div id="{dropdown_id}" class="dropdown-content">
                        <a href="#" class="edit-server" data-server="{escaped_name}">Edit</a>
                        <a href="#" class="copy-json" data-server="{escaped_name}">Copy JSON</a>
                        <a href="#" class="delete-server" data-server="{escaped_name}">Delete</a>
                    </div>
                </div>
            </div>
        </div>
        """
        html += server_html
        logger.debug(f"Added HTML for server: {name}")

    html += "</div>"

    # Add some CSS to style the servers list
    html += """
    <style>
    .mcp-servers-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 16px;
    }

    .mcp-servers-empty {
        color: #a6adc8;
        font-style: italic;
        padding: 12px;
        text-align: center;
    }

    .mcp-server-entry {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border-radius: 8px;
        background-color: #1e1e2e;
        border: 1px solid #313244;
    }

    .mcp-server-info {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .mcp-server-name {
        font-weight: bold;
        color: #cdd6f4;
    }

    .mcp-server-command {
        color: #a6adc8;
        font-size: 0.9em;
    }

    .mcp-server-actions {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Toggle switch styles */
    .switch {
        position: relative;
        display: inline-block;
        width: 40px;
        height: 20px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #45475a;
        transition: .4s;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 2px;
        bottom: 2px;
        background-color: #cdd6f4;
        transition: .4s;
    }

    input:checked + .slider {
        background-color: #a6e3a1;
    }

    input:checked + .slider:before {
        transform: translateX(20px);
    }

    .slider.round {
        border-radius: 34px;
    }

    .slider.round:before {
        border-radius: 50%;
    }

    .mcp-server-more-btn {
        background: none;
        border: none;
        color: #cdd6f4;
        font-size: 1.2em;
        cursor: pointer;
        padding: 4px 8px;
    }

    /* Dropdown menu styles */
    .dropdown {
        position: relative;
        display: inline-block;
    }

    .dropdown-content {
        display: none;
        position: absolute;
        right: 0;
        background-color: #1e1e2e;
        min-width: 160px;
        max-height: 300px;
        overflow: hidden;
        box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
        z-index: 10;
        border-radius: 4px;
        border: 1px solid #313244;
    }

    .dropdown-content a {
        color: #cdd6f4;
        padding: 12px 16px;
        text-decoration: none;
        display: block;
        text-align: left;
    }

    .dropdown-content a:hover {
        background-color: #313244;
    }

    /* Show dropdown on click instead of hover */
    .dropdown-content.show {
        display: block;
    }

    /* Button styles to match the screenshots */
    #add-mcp-btn, #import-json-btn {
        background-color: #1e1e2e;
        border: 1px solid #313244;
        color: #cdd6f4;
        border-radius: 4px;
        padding: 6px 12px;
    }

    /* Modal styles */
    .modal-content {
        background-color: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 16px;
    }
    </style>

    <script>
    // Function to toggle dropdown visibility
    function toggleDropdown(dropdownId, event) {
        // Get the event object
        event = event || window.event;

        // Close all dropdowns first
        document.querySelectorAll('.dropdown-content').forEach(function(dropdown) {
            dropdown.classList.remove('show');
        });

        // Toggle the clicked dropdown
        const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            dropdown.classList.toggle('show');

            // Stop event propagation
            if (event) {
                event.stopPropagation();
            }
        }
    }

    // Close dropdowns when clicking outside
    window.addEventListener('click', function(event) {
        if (!event.target.matches('.mcp-server-more-btn')) {
            document.querySelectorAll('.dropdown-content').forEach(function(dropdown) {
                dropdown.classList.remove('show');
            });
        }
    });

    // Add event listeners to toggle switches and dropdown menu items
    document.addEventListener('DOMContentLoaded', function() {
        // Function to set up toggle switch event listeners
        function setupToggleSwitches() {
            const toggles = document.querySelectorAll('.switch input[type="checkbox"]');
            toggles.forEach(toggle => {
                toggle.addEventListener('change', function() {
                    const serverName = this.getAttribute('data-server');
                    const enabled = this.checked;

                    // Update the hidden textbox with server name and enabled status
                    const updateData = document.getElementById('server-update-data');
                    if (updateData) {
                        updateData.value = serverName + '|' + enabled;

                        // Trigger the change event
                        const event = new Event('change');
                        updateData.dispatchEvent(event);
                    }
                });
            });
        }

        // Function to set up dropdown menu event listeners
        function setupDropdownMenus() {
            // Edit server action
            document.querySelectorAll('.edit-server').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const serverName = this.getAttribute('data-server');

                    // Close the dropdown
                    document.querySelectorAll('.dropdown-content').forEach(function(dropdown) {
                        dropdown.classList.remove('show');
                    });

                    // Try to fetch the server configuration from the backend
                    fetch(`/api/mcp/server/${serverName}/json`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.error) {
                                console.error('Error fetching server config:', data.error);
                                alert('Error fetching server configuration: ' + data.error);
                                return;
                            }

                            // Get the server configuration
                            const serverConfig = data.mcpServers[serverName];

                            // Show the edit modal
                            // For now, we'll just show the JSON in an alert
                            // In a real implementation, we would populate the edit modal fields
                            const jsonStr = JSON.stringify(serverConfig, null, 2);
                            alert('Server Configuration:\n' + jsonStr + '\n\nEdit feature coming soon!');
                        })
                        .catch(error => {
                            console.error('Error fetching server config:', error);
                            alert('Error fetching server configuration: ' + error.message);
                        });
                });
            });

            // Copy JSON action
            document.querySelectorAll('.copy-json').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const serverName = this.getAttribute('data-server');

                    // Close the dropdown
                    document.querySelectorAll('.dropdown-content').forEach(function(dropdown) {
                        dropdown.classList.remove('show');
                    });

                    // Get the server configuration from the page as a fallback
                    const serverConfig = getMCPServerConfig(serverName);

                    // Try to fetch the actual configuration from the backend
                    fetch(`/api/mcp/server/${serverName}/json`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            // Create a temporary textarea to copy the JSON
                            const textarea = document.createElement('textarea');
                            textarea.value = JSON.stringify(data, null, 2);
                            document.body.appendChild(textarea);
                            textarea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textarea);

                            alert('Server configuration copied to clipboard');
                        })
                        .catch(error => {
                            console.error('Error fetching server config:', error);

                            // Fall back to the client-side configuration
                            const textarea = document.createElement('textarea');
                            textarea.value = JSON.stringify(serverConfig, null, 2);
                            document.body.appendChild(textarea);
                            textarea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textarea);

                            alert('Server configuration copied to clipboard (client-side fallback): ' + error.message);
                        });
                });
            });

            // Delete server action
            document.querySelectorAll('.delete-server').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const serverName = this.getAttribute('data-server');

                    // Close the dropdown
                    document.querySelectorAll('.dropdown-content').forEach(function(dropdown) {
                        dropdown.classList.remove('show');
                    });

                    if (confirm('Are you sure you want to delete the server "' + serverName + '"?')) {
                        // This would typically be handled by a Gradio function
                        // For now, we'll just update the hidden textbox with a special command
                        const updateData = document.getElementById('server-update-data');
                        if (updateData) {
                            updateData.value = 'delete|' + serverName;
                            const event = new Event('change');
                            updateData.dispatchEvent(event);
                        }
                    }
                });
            });
        }

        // Helper function to get server configuration
        function getMCPServerConfig(serverName) {
            // Find the server entry in the DOM
            const serverEntry = document.querySelector(`.mcp-server-entry[data-server="${serverName}"]`);
            if (!serverEntry) {
                return {
                    "mcpServers": {
                        [serverName]: {
                            "command": "unknown",
                            "args": [],
                            "enabled": false
                        }
                    }
                };
            }

            // Get the command text
            const commandText = serverEntry.querySelector('.mcp-server-command').textContent;

            // Check if the server is enabled
            const isEnabled = serverEntry.querySelector('input[type="checkbox"]').checked;

            // Parse the command and args
            let command = "npx";
            let args = [];

            if (commandText) {
                const parts = commandText.trim().split(' ');
                if (parts.length > 0) {
                    command = parts[0];
                    args = parts.slice(1);
                }
            }

            // Return the server configuration
            return {
                "mcpServers": {
                    [serverName]: {
                        "command": command,
                        "args": args,
                        "enabled": isEnabled
                    }
                }
            };
        }

        // Set up toggle switches and dropdown menus initially
        setupToggleSwitches();
        setupDropdownMenus();

        // Set up a MutationObserver to detect when the HTML is updated
        const observer = new MutationObserver(function(mutations) {
            setupToggleSwitches();
            setupDropdownMenus();
        });

        // Start observing the target node for configured mutations
        const targetNode = document.getElementById('mcp-servers-list');
        if (targetNode) {
            observer.observe(targetNode, { childList: true, subtree: true });
        }
    });
    </script>
    """

    return html


# Note: The async functions add_or_update_mcp_server and remove_mcp_server have been removed
# as they were replaced with synchronous versions in the save_json_wrapper and handle_server_update_data functions


def create_agent_settings_tab(webui_manager: WebuiManager):
    """
    Creates an agent settings tab.
    """
    tab_components = {}

    with gr.Group():
        with gr.Column():
            override_system_prompt = gr.Textbox(label="Override system prompt", lines=4, interactive=True)
            extend_system_prompt = gr.Textbox(label="Extend system prompt", lines=4, interactive=True)

    with gr.Group():
        with gr.Row():
            gr.Markdown("## MCP")

        with gr.Row():
            gr.Markdown("Configure a new Model Context Protocol server to connect Augment to custom tools. Find out more about MCP in the [docs](https://modelcontextprotocol.github.io/protocol/).")

        # MCP Server List
        with gr.Row():
            mcp_servers_html = gr.HTML(
                value=lambda: render_mcp_servers_html(webui_manager),
                elem_id="mcp-servers-list"
            )

        # Action buttons
        with gr.Row():
            add_mcp_btn = gr.Button("➕ Add MCP", elem_id="add-mcp-btn", variant="secondary")
            import_json_btn = gr.Button("📥 Import from JSON", elem_id="import-json-btn", variant="secondary")

        # Status message
        with gr.Row():
            mcp_server_status = gr.Textbox(
                label="Status",
                value="",
                interactive=False
            )

        # Add MCP Server Modal (initially hidden)
        with gr.Group(visible=False, elem_id="add-mcp-modal", elem_classes=["modal-content"]) as add_mcp_modal:
            gr.Markdown("### New MCP Server")

            with gr.Row():
                mcp_server_name = gr.Textbox(
                    label="Name",
                    placeholder="Enter a name for your MCP server (e.g., Server Memory)",
                    interactive=True
                )

            with gr.Row():
                mcp_server_command = gr.Textbox(
                    label="Command",
                    placeholder="Enter the MCP command (e.g., 'npx -y @modelcontextprotocol/server-memory')",
                    interactive=True
                )

            with gr.Row():
                gr.Markdown("### Environment Variables")

            with gr.Row():
                # Add button to add a new environment variable
                add_env_var_btn = gr.Button("+ Variable", size="sm", elem_id="add-env-var-btn")

            # Container for environment variables
            with gr.Row():
                mcp_env_vars = gr.Dataframe(
                    headers=["Key", "Value"],
                    datatype=["str", "str"],
                    col_count=(2, "fixed"),
                    row_count=(0, "dynamic"),
                    interactive=True,
                    elem_id="mcp-env-vars",
                    visible=True
                )

            with gr.Row():
                mcp_modal_cancel_btn = gr.Button("Cancel", variant="secondary")
                mcp_modal_add_btn = gr.Button("Add", variant="primary")

        # Import JSON Modal (initially hidden)
        with gr.Group(visible=False, elem_id="import-json-modal", elem_classes=["modal-content"]) as import_json_modal:
            gr.Markdown("### New MCP Server")

            with gr.Row():
                mcp_json_editor = gr.Textbox(
                    label="Code Snippet",
                    placeholder="Paste JSON here...",
                    lines=10,
                    interactive=True
                )

            with gr.Row():
                mcp_json_cancel_btn = gr.Button("Cancel", variant="secondary")
                mcp_json_import_btn = gr.Button("Import", variant="primary")

        # Hidden components for compatibility with existing code
        mcp_server_dropdown = gr.Dropdown(visible=False)
        mcp_json_refresh_btn = gr.Button(visible=False)
        mcp_json_save_btn = gr.Button(visible=False)

    with gr.Group():
        with gr.Row():
            llm_provider = gr.Dropdown(
                choices=list(config.model_names.keys()),
                label="LLM Provider",
                value="openai",
                info="Select LLM provider for LLM",
                interactive=True
            )
            llm_model_name = gr.Dropdown(
                label="LLM Model Name",
                choices=config.model_names['openai'],
                value="gpt-4o",
                interactive=True,
                allow_custom_value=True,
                info="Select a model in the dropdown options or directly type a custom model name"
            )
        with gr.Row():
            llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.6,
                step=0.1,
                label="LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True
            )

            use_vision = gr.Checkbox(
                label="Use Vision",
                value=True,
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True
            )

            ollama_num_ctx = gr.Slider(
                minimum=2 ** 8,
                maximum=2 ** 16,
                value=16000,
                step=1,
                label="Ollama Context Length",
                info="Controls max context length model needs to handle (less = faster)",
                visible=False,
                interactive=True
            )

        with gr.Row():
            llm_base_url = gr.Textbox(
                label="Base URL",
                value="",
                info="API endpoint URL (if required)"
            )
            llm_api_key = gr.Textbox(
                label="API Key",
                type="password",
                value="",
                info="Your API key (auto-saved to .env)"
            )

    with gr.Group():
        with gr.Row():
            planner_llm_provider = gr.Dropdown(
                choices=list(config.model_names.keys()),
                label="Planner LLM Provider",
                info="Select LLM provider for LLM",
                value=None,
                interactive=True
            )
            planner_llm_model_name = gr.Dropdown(
                label="Planner LLM Model Name",
                interactive=True,
                allow_custom_value=True,
                info="Select a model in the dropdown options or directly type a custom model name"
            )
        with gr.Row():
            planner_llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.6,
                step=0.1,
                label="Planner LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True
            )

            planner_use_vision = gr.Checkbox(
                label="Use Vision(Planner LLM)",
                value=False,
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True
            )

            planner_ollama_num_ctx = gr.Slider(
                minimum=2 ** 8,
                maximum=2 ** 16,
                value=16000,
                step=1,
                label="Ollama Context Length",
                info="Controls max context length model needs to handle (less = faster)",
                visible=False,
                interactive=True
            )

        with gr.Row():
            planner_llm_base_url = gr.Textbox(
                label="Base URL",
                value="",
                info="API endpoint URL (if required)"
            )
            planner_llm_api_key = gr.Textbox(
                label="API Key",
                type="password",
                value="",
                info="Your API key (auto-saved to .env)"
            )

    with gr.Row():
        max_steps = gr.Slider(
            minimum=1,
            maximum=1000,
            value=100,
            step=1,
            label="Max Run Steps",
            info="Maximum number of steps the agent will take",
            interactive=True
        )
        max_actions = gr.Slider(
            minimum=1,
            maximum=100,
            value=10,
            step=1,
            label="Max Number of Actions",
            info="Maximum number of actions the agent will take per step",
            interactive=True
        )

    with gr.Row():
        max_input_tokens = gr.Number(
            label="Max Input Tokens",
            value=128000,
            precision=0,
            interactive=True
        )
        tool_calling_method = gr.Dropdown(
            label="Tool Calling Method",
            value="auto",
            interactive=True,
            allow_custom_value=True,
            choices=['function_calling', 'json_mode', 'raw', 'auto', 'tools', "None"],
            visible=True
        )
    tab_components.update(dict(
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
        # MCP components
        mcp_server_dropdown=mcp_server_dropdown,
        mcp_server_status=mcp_server_status,
        mcp_json_editor=mcp_json_editor,
        mcp_json_refresh_btn=mcp_json_refresh_btn,
        mcp_json_save_btn=mcp_json_save_btn,
        # New MCP UI components
        mcp_servers_html=mcp_servers_html,
        add_mcp_btn=add_mcp_btn,
        import_json_btn=import_json_btn,
        add_mcp_modal=add_mcp_modal,
        mcp_server_name=mcp_server_name,
        mcp_server_command=mcp_server_command,
        mcp_env_vars=mcp_env_vars,
        add_env_var_btn=add_env_var_btn,
        mcp_modal_cancel_btn=mcp_modal_cancel_btn,
        mcp_modal_add_btn=mcp_modal_add_btn,
        import_json_modal=import_json_modal,
        mcp_json_cancel_btn=mcp_json_cancel_btn,
        mcp_json_import_btn=mcp_json_import_btn,
    ))
    webui_manager.add_components("agent_settings", tab_components)

    llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=llm_provider,
        outputs=ollama_num_ctx
    )
    llm_provider.change(
        lambda provider: update_model_dropdown(provider),
        inputs=[llm_provider],
        outputs=[llm_model_name]
    )
    planner_llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=[planner_llm_provider],
        outputs=[planner_ollama_num_ctx]
    )
    planner_llm_provider.change(
        lambda provider: update_model_dropdown(provider),
        inputs=[planner_llm_provider],
        outputs=[planner_llm_model_name]
    )

    # We only need the JSON editor functionality now

    # MCP JSON refresh button click event
    mcp_json_refresh_btn.click(
        fn=lambda: get_full_mcp_config_json(webui_manager),
        inputs=[],
        outputs=[mcp_json_editor]
    )

    # MCP JSON save button click event
    def save_json_wrapper(config_json):
        try:
            config_data = json.loads(config_json)

            if not isinstance(config_data, dict):
                return "Configuration must be a JSON object"

            # Extract the mcpServers object
            mcp_servers = config_data.get("mcpServers", {})
            if not isinstance(mcp_servers, dict):
                return "mcpServers must be a JSON object"

            # Validate each server configuration
            for server_name, server_config in mcp_servers.items():
                if not isinstance(server_config, dict):
                    return f"Server configuration for '{server_name}' must be a JSON object"

                if "command" not in server_config:
                    return f"Server '{server_name}' is missing the 'command' field"

                if "args" not in server_config or not isinstance(server_config["args"], list):
                    return f"Server '{server_name}' must have 'args' as a JSON array"

            # Save the configuration
            success = webui_manager.save_mcp_servers(mcp_servers)

            if success:
                return "MCP server configuration saved successfully"
            else:
                return "Failed to save MCP server configuration"

        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    mcp_json_save_btn.click(
        fn=save_json_wrapper,
        inputs=[mcp_json_editor],
        outputs=[mcp_server_status]
    )

    # New UI event handlers

    # Show/hide modals
    def show_add_modal():
        return gr.update(visible=True), gr.update(visible=False)

    def show_import_modal():
        return gr.update(visible=False), gr.update(visible=True)

    def hide_modals():
        return gr.update(visible=False), gr.update(visible=False), gr.update(value="")

    # Add MCP button click event
    add_mcp_btn.click(
        fn=show_add_modal,
        inputs=[],
        outputs=[add_mcp_modal, import_json_modal]
    )

    # Import JSON button click event
    import_json_btn.click(
        fn=show_import_modal,
        inputs=[],
        outputs=[add_mcp_modal, import_json_modal]
    )

    # Cancel buttons click events
    mcp_modal_cancel_btn.click(
        fn=hide_modals,
        inputs=[],
        outputs=[add_mcp_modal, import_json_modal, mcp_server_status]
    )

    mcp_json_cancel_btn.click(
        fn=hide_modals,
        inputs=[],
        outputs=[add_mcp_modal, import_json_modal, mcp_server_status]
    )

    # Add MCP server from modal
    def add_mcp_from_modal(name, command, env_vars):
        if not name or not command:
            return gr.update(visible=True), gr.update(visible=False), "Server name and command are required", gr.update()

        try:
            # Parse command to extract command and args
            cmd, args = parse_command_string(command)

            # Parse environment variables
            env = {}
            if env_vars and len(env_vars) > 0:
                for row in env_vars:
                    if len(row) >= 2 and row[0] and row[1]:
                        env[row[0]] = row[1]

            # Add the server
            success = webui_manager.add_mcp_server(name, cmd, args, env)

            if success:
                # Hide modal and update HTML
                return gr.update(visible=False), gr.update(visible=False), f"Added MCP server: {name}", render_mcp_servers_html(webui_manager)
            else:
                return gr.update(visible=True), gr.update(visible=False), f"Failed to add MCP server: {name}", gr.update()

        except Exception as e:
            return gr.update(visible=True), gr.update(visible=False), f"Error: {str(e)}", gr.update()

    mcp_modal_add_btn.click(
        fn=add_mcp_from_modal,
        inputs=[mcp_server_name, mcp_server_command, mcp_env_vars],
        outputs=[add_mcp_modal, import_json_modal, mcp_server_status, mcp_servers_html]
    )

    # Import MCP servers from JSON
    def import_mcp_from_json(json_text):
        try:
            config_data = json.loads(json_text)

            if not isinstance(config_data, dict):
                return gr.update(visible=False), gr.update(visible=True), "Configuration must be a JSON object", gr.update()

            # Extract the mcpServers object
            mcp_servers = config_data.get("mcpServers", {})
            if not isinstance(mcp_servers, dict):
                return gr.update(visible=False), gr.update(visible=True), "mcpServers must be a JSON object", gr.update()

            # Validate and save the configuration
            success = webui_manager.save_mcp_servers(mcp_servers)

            if success:
                # Hide modal and update HTML
                return gr.update(visible=False), gr.update(visible=False), "MCP servers imported successfully", render_mcp_servers_html(webui_manager)
            else:
                return gr.update(visible=False), gr.update(visible=True), "Failed to import MCP servers", gr.update()

        except json.JSONDecodeError as e:
            return gr.update(visible=False), gr.update(visible=True), f"Invalid JSON: {str(e)}", gr.update()
        except Exception as e:
            return gr.update(visible=False), gr.update(visible=True), f"Error: {str(e)}", gr.update()

    mcp_json_import_btn.click(
        fn=import_mcp_from_json,
        inputs=[mcp_json_editor],
        outputs=[add_mcp_modal, import_json_modal, mcp_server_status, mcp_servers_html]
    )



    # Add a hidden refresh button and server update data textbox
    with gr.Row(visible=False):
        refresh_mcp_servers = gr.Button("Refresh", elem_id="refresh-mcp-servers")
        server_update_data = gr.Textbox(elem_id="server-update-data")

    # Add JavaScript to handle toggle switch clicks
    mcp_servers_html.change(
        fn=lambda: None,  # No-op function
        inputs=[],
        outputs=[]
    )

    # Add a function to refresh the MCP servers list
    def refresh_mcp_servers_list():
        return render_mcp_servers_html(webui_manager)

    # Add a handler for the refresh button
    refresh_mcp_servers.click(
        fn=refresh_mcp_servers_list,
        inputs=[],
        outputs=[mcp_servers_html]
    )

    # Add a handler for updating server status
    def handle_server_status_update(server_name, enabled):
        try:
            if not server_name:
                return "No server specified", render_mcp_servers_html(webui_manager)

            # Convert enabled string to boolean
            enabled_bool = str(enabled).lower() == "true"
            logger.debug(f"Toggling server {server_name} to {enabled} (parsed as {enabled_bool})")

            # Update the server enabled status
            success = webui_manager.toggle_mcp_server(server_name, enabled_bool)

            if success:
                status = f"Server '{server_name}' {'enabled' if enabled_bool else 'disabled'}"
            else:
                status = f"Failed to update server '{server_name}'"

            return status, render_mcp_servers_html(webui_manager)
        except Exception as e:
            logger.error(f"Error updating server status: {e}", exc_info=True)
            return f"Error updating server status: {str(e)}", render_mcp_servers_html(webui_manager)



    # We'll use the hidden textbox to pass server name and enabled status

    # Add a handler for the server update data
    def handle_server_update_data(data):
        if not data or "|" not in data:
            return "Invalid data format", render_mcp_servers_html(webui_manager)

        parts = data.split("|")
        action = parts[0]

        if action == "delete":
            if len(parts) < 2:
                return "Invalid delete command format", render_mcp_servers_html(webui_manager)
            server_name = parts[1]
            success = webui_manager.remove_mcp_server(server_name)
            if success:
                return f"Server '{server_name}' deleted successfully", render_mcp_servers_html(webui_manager)
            else:
                return f"Failed to delete server '{server_name}'", render_mcp_servers_html(webui_manager)
        else:
            # Handle toggle status (original functionality)
            return handle_server_status_update(*parts)

    server_update_data.change(
        fn=handle_server_update_data,
        inputs=[server_update_data],
        outputs=[mcp_server_status, mcp_servers_html]
    )

    # Add environment variable button click event
    def add_env_var_row(env_vars):
        if env_vars is None or len(env_vars) == 0:
            return [[""]]

        # Add a new empty row
        env_vars.append(["", ""])
        return env_vars

    add_env_var_btn.click(
        fn=add_env_var_row,
        inputs=[mcp_env_vars],
        outputs=[mcp_env_vars]
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

    # Connect change events to auto-save functions
    llm_provider.change(
        fn=lambda provider: save_llm_api_setting(provider=provider),
        inputs=[llm_provider],
        outputs=[]
    )

    llm_api_key.change(
        fn=lambda api_key: save_llm_api_setting(api_key=api_key),
        inputs=[llm_api_key],
        outputs=[]
    )

    llm_base_url.change(
        fn=lambda base_url: save_llm_api_setting(base_url=base_url),
        inputs=[llm_base_url],
        outputs=[]
    )

    planner_llm_provider.change(
        fn=lambda provider: save_planner_api_setting(provider=provider),
        inputs=[planner_llm_provider],
        outputs=[]
    )

    planner_llm_api_key.change(
        fn=lambda api_key: save_planner_api_setting(api_key=api_key),
        inputs=[planner_llm_api_key],
        outputs=[]
    )

    planner_llm_base_url.change(
        fn=lambda base_url: save_planner_api_setting(base_url=base_url),
        inputs=[planner_llm_base_url],
        outputs=[]
    )
