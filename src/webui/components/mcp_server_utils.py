import json
import logging
import gradio as gr
from typing import Dict, Any, Optional, Tuple

from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)

def get_server_config_json(server_name: str, webui_manager: WebuiManager) -> str:
    """
    Get the JSON configuration for a specific MCP server.

    Args:
        server_name: Name of the MCP server
        webui_manager: The WebUI manager

    Returns:
        str: JSON string of the server configuration
    """
    try:
        mcp_servers = webui_manager.get_mcp_servers()
        if server_name not in mcp_servers:
            return json.dumps({"error": f"Server '{server_name}' not found"})

        server_config = mcp_servers[server_name]
        config_json = {
            "mcpServers": {
                server_name: server_config
            }
        }
        return json.dumps(config_json, indent=2)
    except Exception as e:
        logger.error(f"Error getting server config JSON: {e}", exc_info=True)
        return json.dumps({"error": str(e)})

def edit_server_modal(server_name: str, webui_manager: WebuiManager) -> Tuple[Any, Any, str, str, Any]:
    """
    Prepare the edit server modal with the current server configuration.

    Args:
        server_name: Name of the MCP server
        webui_manager: The WebUI manager

    Returns:
        Tuple containing updates for the modal components
    """
    try:
        mcp_servers = webui_manager.get_mcp_servers()
        if server_name not in mcp_servers:
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                "",
                f"Server '{server_name}' not found",
                gr.update()
            )

        server_config = mcp_servers[server_name]
        command = server_config.get("command", "")
        args = server_config.get("args", [])

        # Format the command with arguments
        command_str = command
        if args:
            args_str = " ".join(args)
            command_str = f"{command} {args_str}"

        # Get environment variables
        env = server_config.get("env", {})
        env_vars = [[k, v] for k, v in env.items()] if env else []

        # Show the edit modal
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            server_name,
            command_str,
            env_vars
        )
    except Exception as e:
        logger.error(f"Error preparing edit server modal: {e}", exc_info=True)
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            f"Error: {str(e)}",
            gr.update()
        )
