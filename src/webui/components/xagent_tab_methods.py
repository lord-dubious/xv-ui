"""
XAgent Tab Methods - Separated methods for better code organization.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from src.agent.xagent.xagent import XAgent
from src.utils import llm_provider

logger = logging.getLogger(__name__)


class XAgentTabMethods:
    """Methods for XAgent tab functionality."""
    
    def __init__(self, tab_instance):
        """Initialize with reference to the tab instance."""
        self.tab = tab_instance
        
    async def _initialize_llm_from_settings(self):
        """Initialize LLM from current settings if not already provided."""
        if self.tab.llm:
            return self.tab.llm

        try:
            # Get settings from environment or defaults
            provider = os.getenv("LLM_PROVIDER", "openai")
            model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.6"))
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            base_url = os.getenv(f"{provider.upper()}_ENDPOINT")

            if not provider or not model_name:
                logger.warning("LLM provider or model not configured")
                return None

            llm = llm_provider.get_llm_model(
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                base_url=base_url,
                api_key=api_key,
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None

    def _run_xagent_task(self, task: str, max_steps: int, save_results: bool):
        """Run XAgent task."""
        if not task.strip():
            gr.Warning("Please enter a task description")
            return (
                self.tab.chat_history,
                "Error: No task provided",
                "",
                gr.update(interactive=True),
                gr.update(interactive=False),
                gr.update(visible=False),
            )

        try:
            # Initialize LLM
            llm = asyncio.run(self._initialize_llm_from_settings())
            if not llm:
                gr.Warning("Failed to initialize LLM. Please check your settings.")
                return (
                    self.tab.chat_history,
                    "Error: LLM initialization failed",
                    "",
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                    gr.update(visible=False),
                )

            # Initialize XAgent with current profile
            self.tab.xagent = XAgent(
                llm=llm,
                browser_config=self.tab.browser_config,
                mode="stealth",
                profile_name=self.tab.current_profile,
            )

            # Generate task ID
            self.tab.current_task_id = str(uuid.uuid4())[:8]

            # Update UI
            self.tab.chat_history.append({"role": "user", "content": task})
            self.tab.chat_history.append(
                {
                    "role": "assistant",
                    "content": "🎭 Starting XAgent with stealth capabilities...",
                }
            )

            # Run the task
            result = asyncio.run(
                self.tab.xagent.run(
                    task=task,
                    task_id=self.tab.current_task_id,
                    max_steps=max_steps,
                    save_dir="./tmp/xagent" if save_results else None,
                )
            )

            # Process results
            if result["status"] == "completed":
                self.tab.chat_history.append(
                    {
                        "role": "assistant",
                        "content": f"✅ Task completed successfully!\n\nResult: {result.get('result', 'No result available')}",
                    }
                )
                status = "Completed"
                results_file_update = gr.update(visible=save_results)
            else:
                self.tab.chat_history.append(
                    {
                        "role": "assistant",
                        "content": f"❌ Task failed: {result.get('error', 'Unknown error')}",
                    }
                )
                status = f"Failed: {result.get('error', 'Unknown error')}"
                results_file_update = gr.update(visible=False)

            return (
                self.tab.chat_history,
                status,
                self.tab.current_task_id,
                gr.update(interactive=True),
                gr.update(interactive=False),
                results_file_update,
            )

        except Exception as e:
            logger.error(f"Error running XAgent task: {e}")
            self.tab.chat_history.append(
                {"role": "assistant", "content": f"❌ Error: {str(e)}"}
            )
            return (
                self.tab.chat_history,
                f"Error: {str(e)}",
                "",
                gr.update(interactive=True),
                gr.update(interactive=False),
                gr.update(visible=False),
            )

    def _stop_xagent_task(self):
        """Stop the current XAgent task."""
        if self.tab.xagent:
            asyncio.run(self.tab.xagent.stop())
            logger.info("Stopping XAgent task")

        return ("Stopped", gr.update(interactive=True), gr.update(interactive=False))

    def _clear_chat(self):
        """Clear the chat history."""
        self.tab.chat_history = []
        self.tab.current_task_id = None
        return ([], "Ready", "", gr.update(visible=False))

    def _change_profile(self, profile_name: str):
        """Change the current profile and load its configuration."""
        self.tab.current_profile = profile_name
        
        # Load profile configuration
        profile_dir = os.path.join("./profiles", profile_name)
        config_file = os.path.join(profile_dir, "config.json")
        
        # Default values
        username = ""
        email = ""
        password = ""
        totp_secret = ""
        cookies_path = "./cookies.json"
        status = "Not initialized"
        action_loops = "[]"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                # Load credentials (they will be decrypted by XAgent)
                if "credentials" in config:
                    creds = config["credentials"]
                    username = creds.get("username", "")
                    email = creds.get("email", "")
                    # Don't load encrypted passwords in UI for security
                    
                # Load Twitter config
                if "twitter" in config:
                    twitter_config = config["twitter"]
                    cookies_path = twitter_config.get("cookies_path", "./cookies.json")
                    
                # Load action loops
                if "action_loops" in config:
                    action_loops = json.dumps(config["action_loops"], indent=2)
                    
                status = f"Profile '{profile_name}' loaded"
                
            except Exception as e:
                logger.error(f"Error loading profile configuration: {e}")
                status = f"Error loading profile: {str(e)}"
        
        return username, email, password, totp_secret, cookies_path, status, action_loops

    def _refresh_profiles(self):
        """Refresh the list of available profiles."""
        self.tab.profiles = self.tab._load_available_profiles()
        return gr.update(choices=self.tab.profiles)

    def _create_profile_dialog(self):
        """Create a new profile (simplified for now)."""
        # For now, just refresh profiles
        # In a full implementation, this would open a dialog
        return self._refresh_profiles()

    def _save_twitter_credentials(
        self, 
        profile_name: str,
        username: str, 
        email: str, 
        password: str, 
        totp_secret: str,
        cookies_path: str
    ):
        """Save Twitter credentials for the current profile."""
        try:
            # Initialize XAgent with current profile to save credentials
            if not self.tab.xagent:
                llm = asyncio.run(self._initialize_llm_from_settings())
                if llm:
                    self.tab.xagent = XAgent(
                        llm=llm,
                        browser_config=self.tab.browser_config,
                        profile_name=profile_name,
                    )
            
            if self.tab.xagent:
                # Set credentials
                success = self.tab.xagent.set_twitter_credentials(
                    username=username,
                    email=email,
                    password=password,
                    totp_secret=totp_secret,
                )
                
                # Update Twitter config
                self.tab.xagent.twitter_config["cookies_path"] = cookies_path
                self.tab.xagent.save_profile_config()
                
                if success:
                    status = "✅ Credentials saved successfully"
                    totp_code = self.tab.xagent.get_current_totp_code() or ""
                else:
                    status = "❌ Failed to save credentials"
                    totp_code = ""
            else:
                status = "❌ Failed to initialize XAgent"
                totp_code = ""
                
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            status = f"❌ Error: {str(e)}"
            totp_code = ""
            
        return status, totp_code

    def _refresh_totp_code(self):
        """Refresh the current TOTP code."""
        if self.tab.xagent:
            totp_code = self.tab.xagent.get_current_totp_code()
            return totp_code or "No TOTP secret configured"
        return "XAgent not initialized"

    def _initialize_twitter(self):
        """Initialize Twitter functionality."""
        if not self.tab.xagent:
            return (
                "❌ XAgent not initialized",
                gr.update(choices=[]),
                gr.update(choices=[]),
                [{"role": "assistant", "content": "❌ XAgent not initialized"}],
            )
            
        try:
            # Initialize Twitter
            success = asyncio.run(self.tab.xagent.initialize_twitter())
            
            if success:
                # Get available personas
                personas_result = asyncio.run(self.tab.xagent.get_available_personas())
                if personas_result["status"] == "success":
                    self.tab.personas = [p["name"] for p in personas_result["personas"]]
                else:
                    self.tab.personas = []
                
                self.tab.twitter_initialized = True
                status = "✅ Twitter initialized successfully"
                chat_history = [{"role": "assistant", "content": "🐦 Twitter functionality initialized"}]
            else:
                status = "❌ Failed to initialize Twitter"
                chat_history = [{"role": "assistant", "content": "❌ Failed to initialize Twitter"}]
                
        except Exception as e:
            logger.error(f"Error initializing Twitter: {e}")
            status = f"❌ Error: {str(e)}"
            chat_history = [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
            
        return (
            status,
            gr.update(choices=self.tab.personas),
            gr.update(choices=self.tab.personas),
            chat_history,
        )

