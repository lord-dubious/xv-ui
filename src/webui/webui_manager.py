import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import gradio as gr
from browser_use.agent.service import Agent
from gradio.components import Component

from src.agent.deep_research.deep_research_agent import DeepResearchAgent
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext
from src.controller.custom_controller import CustomController
from src.utils.env_utils import read_env_file, write_env_file


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.id_to_component: dict[str, Component] = {}
        self.component_to_id: dict[Component, str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

    def init_browser_use_agent(self) -> None:
        """
        init browser use agent
        """
        self.bu_agent: Optional[Agent] = None
        self.bu_browser: Optional[CustomBrowser] = None
        self.bu_browser_context: Optional[CustomBrowserContext] = None
        self.bu_controller: Optional[CustomController] = None
        self.bu_chat_history: List[Dict[str, Optional[str]]] = []
        self.bu_response_event: Optional[asyncio.Event] = None
        self.bu_user_help_response: Optional[str] = None
        self.bu_current_task: Optional[asyncio.Task] = None
        self.bu_agent_task_id: Optional[str] = None

    def init_deep_research_agent(self) -> None:
        """
        init deep research agent
        """
        self.dr_agent: Optional[DeepResearchAgent] = None
        self.dr_current_task = None
        self.dr_agent_task_id: Optional[str] = None
        self.dr_save_dir: Optional[str] = None

    def add_components(
        self, tab_name: str, components_dict: dict[str, "Component"]
    ) -> None:
        """
        Add tab components
        """
        for comp_name, component in components_dict.items():
            comp_id = f"{tab_name}.{comp_name}"
            self.id_to_component[comp_id] = component
            self.component_to_id[component] = comp_id

    def get_components(self) -> list["Component"]:
        """
        Get all components
        """
        return list(self.id_to_component.values())

    def get_component_by_id(self, comp_id: str) -> "Component":
        """
        Get component by id
        """
        return self.id_to_component[comp_id]

    def get_id_by_component(self, comp: "Component") -> str:
        """
        Get id by component
        """
        return self.component_to_id[comp]

    def save_config(self, components: Dict["Component", str]) -> None:
        """
        Save config
        """
        cur_settings = {}
        for comp in components:
            if (
                not isinstance(comp, gr.Button)
                and not isinstance(comp, gr.File)
                and str(getattr(comp, "interactive", True)).lower() != "false"
            ):
                comp_id = self.get_id_by_component(comp)
                cur_settings[comp_id] = components[comp]

        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(
            os.path.join(self.settings_save_dir, f"{config_name}.json"), "w"
        ) as fw:
            json.dump(cur_settings, fw, indent=4)

        return os.path.join(self.settings_save_dir, f"{config_name}.json")

    def load_config(self, config_path: str):
        """
        Load config
        """
        with open(config_path, "r") as fr:
            ui_settings = json.load(fr)

        update_components = {}
        for comp_id, comp_val in ui_settings.items():
            if comp_id in self.id_to_component:
                comp = self.id_to_component[comp_id]
                if comp.__class__.__name__ == "Chatbot":
                    update_components[comp] = comp.__class__(
                        value=comp_val, type="messages"
                    )
                else:
                    update_components[comp] = comp.__class__(value=comp_val)

        config_status = self.id_to_component["load_save_config.config_status"]
        update_components.update(
            {
                config_status: config_status.__class__(
                    value=f"Successfully loaded config: {config_path}"
                )
            }
        )
        yield update_components

    def load_env_settings(self, env_path: str = ".env") -> Dict[str, str]:
        """
        Load environment settings from .env file

        Args:
            env_path: Path to the .env file

        Returns:
            Dict[str, str]: Dictionary of environment variables
        """
        return read_env_file(env_path)

    def save_env_settings(
        self, env_vars: Dict[str, str], env_path: str = ".env"
    ) -> bool:
        """
        Save environment settings to .env file

        Args:
            env_vars: Dictionary of environment variables
            env_path: Path to the .env file

        Returns:
            bool: True if successful, False otherwise
        """
        return write_env_file(env_vars, env_path)

    def save_api_keys_to_env(
        self, provider: str, api_key: str = None, base_url: str = None
    ) -> bool:
        """
        Save API keys to .env file

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            api_key: API key value (optional)
            base_url: Base URL for the API (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        # Load current env vars
        env_vars = self.load_env_settings()

        # Update with new values
        if api_key is not None:
            env_vars[f"{provider.upper()}_API_KEY"] = api_key

        if base_url is not None:
            env_vars[f"{provider.upper()}_ENDPOINT"] = base_url

        # Save back to .env file
        return self.save_env_settings(env_vars)

    def save_browser_settings_to_env(
        self,
        settings: Dict[str, str] = None,
        setting_name: str = None,
        setting_value=None,
    ) -> bool:
        """
        Save browser settings to .env file

        Args:
            settings: Dictionary of browser settings (optional)
            setting_name: Name of a single setting to update (optional)
            setting_value: Value for the single setting (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        # Load current env vars
        env_vars = self.load_env_settings()

        # Map of UI component names to .env variable names
        mapping = {
            "browser_binary_path": "BROWSER_PATH",
            "browser_user_data_dir": "BROWSER_USER_DATA",
            "cdp_url": "BROWSER_CDP",
            "keep_browser_open": "KEEP_BROWSER_OPEN",
            "window_w": "RESOLUTION_WIDTH",
            "window_h": "RESOLUTION_HEIGHT",
            "headless": "HEADLESS",
            "disable_security": "DISABLE_SECURITY",
            "save_recording_path": "SAVE_RECORDING_PATH",
            "save_trace_path": "SAVE_TRACE_PATH",
            "save_agent_history_path": "SAVE_AGENT_HISTORY_PATH",
            "save_download_path": "SAVE_DOWNLOAD_PATH",
            "wss_url": "WSS_URL",
        }

        # Handle single setting update
        if setting_name and setting_name in mapping:
            # Convert boolean values to string
            if isinstance(setting_value, bool):
                env_vars[mapping[setting_name]] = str(setting_value).lower()
            elif setting_value is not None:
                env_vars[mapping[setting_name]] = str(setting_value)

            # Special case for window dimensions
            if setting_name in ["window_w", "window_h"]:
                # Get current resolution
                width = env_vars.get("RESOLUTION_WIDTH", "1920")
                height = env_vars.get("RESOLUTION_HEIGHT", "1080")
                depth = 24  # Default depth

                # Update the dimension that changed
                if setting_name == "window_w":
                    width = setting_value
                else:
                    height = setting_value

                # Update resolution string
                if width and height:
                    env_vars["RESOLUTION"] = f"{width}x{height}x{depth}"

        # Handle dictionary of settings
        elif settings:
            # Update env vars with new values
            for ui_name, env_name in mapping.items():
                if ui_name in settings and settings[ui_name] is not None:
                    # Convert boolean values to string
                    if isinstance(settings[ui_name], bool):
                        env_vars[env_name] = str(settings[ui_name]).lower()
                    else:
                        env_vars[env_name] = str(settings[ui_name])

            # Update resolution string (WxHxD)
            if "window_w" in settings and "window_h" in settings:
                width = settings["window_w"]
                height = settings["window_h"]
                depth = 24  # Default depth
                if width and height:
                    env_vars["RESOLUTION"] = f"{width}x{height}x{depth}"

        # Save back to .env file
        return self.save_env_settings(env_vars)
