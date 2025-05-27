import json
import logging
import os
import uuid
from datetime import datetime

import gradio as gr

from src.webui.utils.env_utils import get_env_value, load_env_settings_with_cache

logger = logging.getLogger(__name__)


def create_xagent_tab(webui_manager):
    """Create the XAgent tab with profile system, parallel execution, and MCP servers."""

    # Load environment settings
    env_settings = load_env_settings_with_cache(webui_manager)

    # Profile management state
    profiles_state = gr.State({})
    active_agents_state = gr.State({})  # For parallel execution

    with gr.Column():
        # Header Section
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("# 🎭 XAgent - Advanced Browser Automation")
                gr.Markdown(
                    "**Stealth browser automation powered by Patchright** • Anti-detection • Chrome-optimized • Profile management"
                )
            with gr.Column(scale=1):
                gr.Markdown(
                    """
                    **🛡️ Built-in Stealth Features:**
                    • Runtime leak protection
                    • Fingerprint resistance
                    • Bot detection bypass
                    • Persistent browser sessions
                    """
                )

        # Main Configuration Section
        with gr.Row():
            # Left Column - Task & Execution
            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### 🎯 Task Configuration")

                    task_input = gr.Textbox(
                        label="Task Description",
                        placeholder="Describe what you want XAgent to do...",
                        lines=4,
                        elem_id="xagent_task_input",
                    )

                    with gr.Row():
                        max_steps = gr.Slider(
                            minimum=1,
                            maximum=200,
                            value=get_env_value(
                                env_settings, "XAGENT_MAX_STEPS", 50, int
                            ),
                            step=1,
                            label="Max Steps",
                            elem_id="xagent_max_steps",
                        )

                        parallel_agents = gr.Slider(
                            minimum=1,
                            maximum=5,
                            value=get_env_value(
                                env_settings, "XAGENT_PARALLEL_AGENTS", 1, int
                            ),
                            step=1,
                            label="Parallel Agents",
                        )

                with gr.Group():
                    gr.Markdown("### 🚀 Execution Controls")

                    with gr.Row():
                        run_button = gr.Button(
                            "🚀 Start XAgent",
                            variant="primary",
                            elem_id="xagent_run_button",
                            scale=2,
                        )
                        stop_button = gr.Button(
                            "⏹️ Stop All",
                            variant="stop",
                            interactive=False,
                            elem_id="xagent_stop_button",
                            scale=1,
                        )
                        clear_button = gr.Button(
                            "🗑️ Clear", elem_id="xagent_clear_button", scale=1
                        )

            # Right Column - Settings & Profiles
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### ⚙️ Settings")

                    save_results = gr.Checkbox(
                        label="💾 Save Results",
                        value=get_env_value(
                            env_settings, "XAGENT_SAVE_RESULTS", True, bool
                        ),
                        elem_id="xagent_save_results",
                        info="Save execution logs and results to files",
                    )

                    custom_save_dir = gr.Textbox(
                        label="Save Directory",
                        placeholder="./tmp/xagent",
                        value=get_env_value(
                            env_settings, "XAGENT_SAVE_DIR", "./tmp/xagent"
                        ),
                        info="Directory for results and logs",
                    )

                    browser_user_data_dir = gr.Textbox(
                        label="Browser Profile Directory",
                        placeholder="./tmp/xagent_browser_data",
                        value=get_env_value(
                            env_settings,
                            "XAGENT_BROWSER_USER_DATA",
                            "./tmp/xagent_browser_data",
                        ),
                        info="Browser user data for persistent sessions",
                    )

                with gr.Group():
                    gr.Markdown("### 📁 Profile Management")

                    profile_list = gr.Dropdown(
                        label="Saved Profiles",
                        choices=[],
                        interactive=True,
                        allow_custom_value=False,
                        info="Load saved configurations",
                    )

                    profile_name = gr.Textbox(
                        label="Profile Name",
                        placeholder="Enter name to save current config...",
                    )

                    with gr.Row():
                        save_profile_btn = gr.Button(
                            "💾 Save", variant="secondary", scale=1
                        )
                        load_profile_btn = gr.Button(
                            "📂 Load", variant="secondary", scale=1
                        )
                        delete_profile_btn = gr.Button(
                            "🗑️ Delete", variant="stop", scale=1
                        )

        # MCP Servers Section (Collapsible)
        with gr.Group():
            with gr.Accordion("🔧 MCP Servers (Optional)", open=False):
                gr.Markdown("Configure dedicated MCP servers for XAgent capabilities")

                xagent_mcp_servers = gr.State({})

                with gr.Row():
                    mcp_server_name = gr.Textbox(
                        label="Server Name",
                        placeholder="e.g., xagent-browser-tools",
                        scale=2,
                    )
                    mcp_server_command = gr.Textbox(
                        label="Command",
                        placeholder="e.g., npx @modelcontextprotocol/server-browser",
                        scale=3,
                    )
                    add_mcp_btn = gr.Button("➕ Add", variant="secondary", scale=1)

                xagent_mcp_list = gr.HTML(
                    value="<p><em>No MCP servers configured</em></p>",
                    label="Configured Servers",
                )

        # Results & Status Section
        with gr.Group():
            gr.Markdown("### 📊 Execution Status & Results")

            # Status bar
            with gr.Row():
                status_text = gr.Textbox(
                    label="Status",
                    value="Ready",
                    interactive=False,
                    elem_id="xagent_status",
                    scale=2,
                )

                task_id_text = gr.Textbox(
                    label="Task ID",
                    value="",
                    interactive=False,
                    elem_id="xagent_task_id",
                    scale=1,
                )

            # Active Agents Display
            active_agents_display = gr.HTML(
                value="<p><em>No active agents</em></p>",
                label="Active Agents",
            )

            # Execution Log
            with gr.Accordion("📋 Execution Log", open=True):
                chatbot = gr.Chatbot(
                    label="XAgent Log",
                    height=300,
                    elem_id="xagent_chatbot",
                    type="messages",
                    show_label=False,
                )

            # Results download
            results_file = gr.File(
                label="📁 Download Results",
                visible=False,
                elem_id="xagent_results_file",
            )

    # Component references for webui_manager
    tab_components = {
        "xagent_task_input": task_input,
        "xagent_custom_save_dir": custom_save_dir,
        "xagent_browser_user_data_dir": browser_user_data_dir,
        "xagent_max_steps": max_steps,
        "xagent_parallel_agents": parallel_agents,
        "xagent_save_results": save_results,
        "xagent_profile_name": profile_name,
        "xagent_profile_list": profile_list,
        "xagent_mcp_servers": xagent_mcp_servers,
        "xagent_chatbot": chatbot,
        "xagent_status": status_text,
        "xagent_task_id": task_id_text,
        "xagent_results_file": results_file,
        "xagent_active_agents": active_agents_state,
    }

    webui_manager.add_components("xagent", tab_components)

    # Profile Management Functions
    def save_profile(
        profile_name_val,
        task_val,
        save_dir_val,
        browser_user_data_val,
        max_steps_val,
        parallel_agents_val,
        save_results_val,
        mcp_servers_val,
        profiles_val,
    ):
        """Save current configuration as a profile."""
        if not profile_name_val.strip():
            gr.Warning("Please enter a profile name")
            return profiles_val, gr.update()

        profile_data = {
            "task": task_val,
            "save_dir": save_dir_val,
            "browser_user_data": browser_user_data_val,
            "max_steps": max_steps_val,
            "parallel_agents": parallel_agents_val,
            "save_results": save_results_val,
            "mcp_servers": mcp_servers_val,
            "created_at": datetime.now().isoformat(),
        }

        profiles_val[profile_name_val] = profile_data

        # Save to file
        profiles_dir = "./tmp/xagent_profiles"
        try:
            os.makedirs(profiles_dir, exist_ok=True)
            with open(os.path.join(profiles_dir, "profiles.json"), "w") as f:
                json.dump(profiles_val, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            gr.Warning(f"Failed to save profile: {str(e)}")
            return profiles_val, gr.update()

        gr.Info(f"Profile '{profile_name_val}' saved successfully!")
        return profiles_val, gr.update(choices=list(profiles_val.keys()))

    def load_profile(selected_profile, profiles_val):
        """Load a saved profile."""
        if not selected_profile or selected_profile not in profiles_val:
            gr.Warning("Please select a valid profile")
            return [gr.update() for _ in range(7)]

        profile_data = profiles_val[selected_profile]
        gr.Info(f"Profile '{selected_profile}' loaded successfully!")

        return [
            gr.update(value=profile_data.get("task", "")),
            gr.update(value=profile_data.get("save_dir", "./tmp/xagent")),
            gr.update(
                value=profile_data.get("browser_user_data", "./tmp/xagent_browser_data")
            ),
            gr.update(value=profile_data.get("max_steps", 50)),
            gr.update(value=profile_data.get("parallel_agents", 1)),
            gr.update(value=profile_data.get("save_results", True)),
            profile_data.get("mcp_servers", {}),
        ]

    def delete_profile(selected_profile, profiles_val):
        """Delete a saved profile."""
        if not selected_profile or selected_profile not in profiles_val:
            gr.Warning("Please select a valid profile to delete")
            return profiles_val, gr.update()

        del profiles_val[selected_profile]

        # Save to file
        profiles_dir = "./tmp/xagent_profiles"
        try:
            os.makedirs(profiles_dir, exist_ok=True)
            with open(os.path.join(profiles_dir, "profiles.json"), "w") as f:
                json.dump(profiles_val, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to delete profile: {e}")
            gr.Warning(f"Failed to delete profile: {str(e)}")
            return profiles_val, gr.update()

        gr.Info(f"Profile '{selected_profile}' deleted successfully!")
        return profiles_val, gr.update(choices=list(profiles_val.keys()), value="")

    # Load existing profiles on startup
    def load_existing_profiles():
        """Load existing profiles from file."""
        profiles_dir = "./tmp/xagent_profiles"
        profiles_file = os.path.join(profiles_dir, "profiles.json")

        if os.path.exists(profiles_file):
            try:
                with open(profiles_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load profiles: {e}")

        return {}

    # MCP Server Management Functions
    def add_mcp_server(server_name_val, server_command_val, mcp_servers_val):
        """Add a new MCP server for XAgent."""
        if not server_name_val.strip() or not server_command_val.strip():
            gr.Warning("Please enter both server name and command")
            return mcp_servers_val, gr.update()

        mcp_servers_val[server_name_val] = {
            "command": server_command_val,
            "enabled": True,
            "added_at": datetime.now().isoformat(),
        }

        gr.Info(f"MCP server '{server_name_val}' added successfully!")
        return mcp_servers_val, render_mcp_servers_list(mcp_servers_val)

    def render_mcp_servers_list(mcp_servers_val):
        """Render the MCP servers list as HTML."""
        if not mcp_servers_val:
            return "<p><em>No MCP servers configured for XAgent</em></p>"

        html = "<div style='font-family: monospace;'>"
        for name, config in mcp_servers_val.items():
            status = "🟢 Enabled" if config.get("enabled", True) else "🔴 Disabled"
            html += f"""
            <div style='border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px;'>
                <strong>{name}</strong> {status}<br>
                <code>{config["command"]}</code><br>
                <small>Added: {config.get("added_at", "Unknown")}</small>
            </div>
            """
        html += "</div>"
        return html

    # Parallel Execution Functions
    def run_xagent_task(
        task_val,
        save_dir_val,
        browser_user_data_val,
        max_steps_val,
        parallel_agents_val,
        save_results_val,
        mcp_servers_val,
        active_agents_val,
        chatbot_val,
    ):
        """Run XAgent task with parallel execution support."""
        if not task_val.strip():
            gr.Warning("Please enter a task description")
            return [gr.update() for _ in range(6)]

        try:
            # Generate task ID
            task_id = str(uuid.uuid4())[:8]

            # Update chat
            chatbot_val.append(
                {"role": "user", "content": f"🎭 Starting XAgent task: {task_val}"}
            )
            chatbot_val.append(
                {
                    "role": "assistant",
                    "content": f"🚀 Initializing {parallel_agents_val} XAgent instance(s) with stealth capabilities...",
                }
            )

            # Create agent instances for parallel execution
            for i in range(parallel_agents_val):
                agent_id = f"{task_id}-{i + 1}"
                # Create unique browser user data directory for each agent instance
                agent_browser_data = f"{browser_user_data_val}_{agent_id}"

                active_agents_val[agent_id] = {
                    "task": task_val,
                    "status": "initializing",
                    "progress": 0,
                    "max_steps": max_steps_val,
                    "save_dir": save_dir_val,
                    "browser_user_data": agent_browser_data,
                    "save_results": save_results_val,
                    "mcp_servers": mcp_servers_val,
                    "started_at": datetime.now().isoformat(),
                }

            # Update UI
            return [
                chatbot_val,
                f"Running {parallel_agents_val} agent(s)",
                task_id,
                gr.update(interactive=False),  # run button
                gr.update(interactive=True),  # stop button
                render_active_agents(active_agents_val),
            ]

        except Exception as e:
            logger.error(f"Error starting XAgent task: {e}")
            chatbot_val.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            return [
                chatbot_val,
                f"Error: {str(e)}",
                "",
                gr.update(interactive=True),
                gr.update(interactive=False),
                render_active_agents(active_agents_val),
            ]

    def render_active_agents(active_agents_val):
        """Render active agents display."""
        if not active_agents_val:
            return "<p><em>No active agents</em></p>"

        html = "<div style='font-family: monospace;'>"
        for agent_id, agent_info in active_agents_val.items():
            status_color = {
                "initializing": "🟡",
                "running": "🟢",
                "completed": "✅",
                "failed": "❌",
                "stopped": "⏹️",
            }.get(agent_info["status"], "⚪")

            html += f"""
            <div style='border: 1px solid #ddd; padding: 8px; margin: 3px 0; border-radius: 3px;'>
                <strong>Agent {agent_id}</strong> {status_color} {agent_info["status"]}<br>
                <small>Progress: {agent_info["progress"]}/{agent_info["max_steps"]} steps</small><br>
                <small>Started: {agent_info.get("started_at", "Unknown")}</small>
            </div>
            """
        html += "</div>"
        return html

    def stop_all_agents(active_agents_val, chatbot_val):
        """Stop all active XAgent instances."""
        if not active_agents_val:
            gr.Warning("No active agents to stop")
            return [gr.update() for _ in range(4)]

        # Mark all agents as stopped
        for agent_id in active_agents_val:
            active_agents_val[agent_id]["status"] = "stopped"

        chatbot_val.append(
            {
                "role": "assistant",
                "content": f"⏹️ Stopped {len(active_agents_val)} XAgent instance(s)",
            }
        )

        # Clear active agents after a delay (in real implementation)
        active_agents_val.clear()

        return [
            chatbot_val,
            "Stopped",
            gr.update(interactive=True),  # run button
            gr.update(interactive=False),  # stop button
        ]

    def clear_chat(chatbot_val, active_agents_val):
        """Clear chat and reset state."""
        # Clear chat history and active agents
        active_agents_val.clear()
        return [
            [],  # empty chatbot
            "Ready",
            "",
            render_active_agents(active_agents_val),
            gr.update(visible=False),  # results file
        ]

    # Event Handlers

    # Profile Management Events
    save_profile_btn.click(
        fn=save_profile,
        inputs=[
            profile_name,
            task_input,
            custom_save_dir,
            browser_user_data_dir,
            max_steps,
            parallel_agents,
            save_results,
            xagent_mcp_servers,
            profiles_state,
        ],
        outputs=[profiles_state, profile_list],
    )

    load_profile_btn.click(
        fn=load_profile,
        inputs=[profile_list, profiles_state],
        outputs=[
            task_input,
            custom_save_dir,
            browser_user_data_dir,
            max_steps,
            parallel_agents,
            save_results,
            xagent_mcp_servers,
        ],
    )

    delete_profile_btn.click(
        fn=delete_profile,
        inputs=[profile_list, profiles_state],
        outputs=[profiles_state, profile_list],
    )

    # MCP Server Events
    add_mcp_btn.click(
        fn=add_mcp_server,
        inputs=[mcp_server_name, mcp_server_command, xagent_mcp_servers],
        outputs=[xagent_mcp_servers, xagent_mcp_list],
    )

    # Execution Events
    run_button.click(
        fn=run_xagent_task,
        inputs=[
            task_input,
            custom_save_dir,
            browser_user_data_dir,
            max_steps,
            parallel_agents,
            save_results,
            xagent_mcp_servers,
            active_agents_state,
            chatbot,
        ],
        outputs=[
            chatbot,
            status_text,
            task_id_text,
            run_button,
            stop_button,
            active_agents_display,
        ],
        show_progress=True,
    )

    stop_button.click(
        fn=stop_all_agents,
        inputs=[active_agents_state, chatbot],
        outputs=[chatbot, status_text, run_button, stop_button],
    )

    clear_button.click(
        fn=clear_chat,
        inputs=[chatbot, active_agents_state],
        outputs=[
            chatbot,
            status_text,
            task_id_text,
            active_agents_display,
            results_file,
        ],
    )

    # Auto-save settings to environment
    def save_xagent_setting(setting_name, value):
        """Save XAgent setting to environment."""
        if not hasattr(webui_manager, "load_env_settings") or not hasattr(
            webui_manager, "save_env_settings"
        ):
            logger.warning("WebUI manager missing required methods for saving settings")
            return
        env_vars = webui_manager.load_env_settings()
        env_vars[f"XAGENT_{setting_name.upper()}"] = str(value)
        webui_manager.save_env_settings(env_vars)

    # Connect auto-save events
    custom_save_dir.change(
        fn=lambda val: save_xagent_setting("save_dir", val), inputs=[custom_save_dir]
    )

    browser_user_data_dir.change(
        fn=lambda val: save_xagent_setting("browser_user_data", val),
        inputs=[browser_user_data_dir],
    )

    max_steps.change(
        fn=lambda val: save_xagent_setting("max_steps", val), inputs=[max_steps]
    )

    parallel_agents.change(
        fn=lambda val: save_xagent_setting("parallel_agents", val),
        inputs=[parallel_agents],
    )

    save_results.change(
        fn=lambda val: save_xagent_setting("save_results", val), inputs=[save_results]
    )

    # Initialize profiles
    initial_profiles = load_existing_profiles()
    profiles_state.value = initial_profiles
    profile_list.choices = list(initial_profiles.keys())

    return list(tab_components.values())
