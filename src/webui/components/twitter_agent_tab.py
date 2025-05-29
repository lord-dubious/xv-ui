import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import gradio as gr
from langchain_core.language_models.chat_models import BaseChatModel

from src.agent.xagent.xagent import XAgent
from src.utils import llm_provider

logger = logging.getLogger(__name__)


class TwitterAgentTab:
    """Twitter agent tab component for the web UI."""

    def __init__(
        self,
        xagent: Optional[XAgent] = None,
        llm: Optional[BaseChatModel] = None,
        browser_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Twitter agent tab.

        Args:
            xagent: Existing XAgent instance (if available)
            llm: Language model instance (can be None, will be initialized from settings)
            browser_config: Browser configuration dictionary
        """
        self.xagent = xagent
        self.llm = llm
        self.browser_config = browser_config or {
            "headless": False,
            "window_width": 1280,
            "window_height": 1100,
            "disable_security": False,
        }
        self.chat_history = []
        self.personas = []
        self.twitter_initialized = False

    def create_tab(self):
        """Create the Twitter agent tab UI components."""
        with gr.Column():
            gr.Markdown("# 🐦 Twitter Agent - Automated Twitter Interactions")
            gr.Markdown(
                """
                Twitter Agent provides browser-based Twitter automation with stealth capabilities.

                **Features:**
                - Tweet creation and replies
                - Following users and managing lists
                - Persona-based content generation
                - Cookie-based authentication
                - Enhanced anti-detection measures
                """
            )

            with gr.Row():
                with gr.Column(scale=2):
                    # Twitter authentication section
                    gr.Markdown("### 🔑 Twitter Authentication")
                    
                    cookies_path = gr.Textbox(
                        label="Cookies File Path",
                        placeholder="Path to cookies.json file",
                        value="./cookies.json",
                        elem_id="twitter_cookies_path",
                    )
                    
                    persona_path = gr.Textbox(
                        label="Personas Directory",
                        placeholder="Path to personas directory",
                        value="./personas",
                        elem_id="twitter_personas_path",
                    )
                    
                    config_path = gr.Textbox(
                        label="Config File Path",
                        placeholder="Path to config.json file",
                        value="./config.json",
                        elem_id="twitter_config_path",
                    )
                    
                    initialize_button = gr.Button(
                        "🚀 Initialize Twitter Agent",
                        variant="primary",
                        elem_id="twitter_initialize_button",
                    )

                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ Settings")
                    
                    headless_mode = gr.Checkbox(
                        label="Headless Mode",
                        value=False,
                        elem_id="twitter_headless_mode",
                    )
                    
                    save_results = gr.Checkbox(
                        label="Save Results",
                        value=True,
                        elem_id="twitter_save_results",
                    )

            # Status indicator
            status_text = gr.Textbox(
                label="Status",
                value="Not initialized",
                interactive=False,
                elem_id="twitter_status",
            )

            # Twitter action tabs
            with gr.Tabs():
                # Tweet creation tab
                with gr.TabItem("📝 Create Tweet"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            tweet_content = gr.Textbox(
                                label="Tweet Content",
                                placeholder="Enter your tweet here...",
                                lines=3,
                                elem_id="twitter_tweet_content",
                            )
                            
                            tweet_media = gr.File(
                                label="Attach Media (Optional)",
                                file_count="multiple",
                                elem_id="twitter_tweet_media",
                            )
                            
                            tweet_persona = gr.Dropdown(
                                label="Use Persona (Optional)",
                                choices=[],
                                elem_id="twitter_tweet_persona",
                            )
                            
                            tweet_button = gr.Button(
                                "🐦 Post Tweet",
                                variant="primary",
                                elem_id="twitter_tweet_button",
                            )
                
                # Reply to tweet tab
                with gr.TabItem("💬 Reply to Tweet"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            tweet_url = gr.Textbox(
                                label="Tweet URL",
                                placeholder="https://twitter.com/username/status/123456789",
                                elem_id="twitter_reply_url",
                            )
                            
                            reply_content = gr.Textbox(
                                label="Reply Content",
                                placeholder="Enter your reply here...",
                                lines=3,
                                elem_id="twitter_reply_content",
                            )
                            
                            reply_media = gr.File(
                                label="Attach Media (Optional)",
                                file_count="multiple",
                                elem_id="twitter_reply_media",
                            )
                            
                            reply_persona = gr.Dropdown(
                                label="Use Persona (Optional)",
                                choices=[],
                                elem_id="twitter_reply_persona",
                            )
                            
                            reply_button = gr.Button(
                                "💬 Post Reply",
                                variant="primary",
                                elem_id="twitter_reply_button",
                            )
                
                # Follow users tab
                with gr.TabItem("👥 Follow Users"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            follow_username = gr.Textbox(
                                label="Username to Follow",
                                placeholder="username (without @)",
                                elem_id="twitter_follow_username",
                            )
                            
                            follow_button = gr.Button(
                                "➕ Follow User",
                                variant="primary",
                                elem_id="twitter_follow_button",
                            )
                    
                    gr.Markdown("### 📋 Bulk Follow")
                    
                    with gr.Row():
                        with gr.Column(scale=3):
                            bulk_follow_usernames = gr.Textbox(
                                label="Usernames to Follow (one per line)",
                                placeholder="username1\nusername2\nusername3",
                                lines=5,
                                elem_id="twitter_bulk_follow_usernames",
                            )
                            
                            bulk_follow_button = gr.Button(
                                "➕ Follow All Users",
                                variant="primary",
                                elem_id="twitter_bulk_follow_button",
                            )

            # Results and logs
            gr.Markdown("### 📊 Results and Logs")
            
            result_json = gr.JSON(
                label="Operation Result",
                elem_id="twitter_result_json",
            )
            
            chatbot = gr.Chatbot(
                label="Twitter Agent Log",
                height=300,
                elem_id="twitter_chatbot",
            )

            # Event handlers
            initialize_button.click(
                fn=self._initialize_twitter_agent,
                inputs=[cookies_path, persona_path, config_path, headless_mode],
                outputs=[status_text, tweet_persona, reply_persona, chatbot],
            )
            
            tweet_button.click(
                fn=self._create_tweet,
                inputs=[tweet_content, tweet_media, tweet_persona],
                outputs=[result_json, chatbot, status_text],
            )
            
            reply_button.click(
                fn=self._reply_to_tweet,
                inputs=[tweet_url, reply_content, reply_media, reply_persona],
                outputs=[result_json, chatbot, status_text],
            )
            
            follow_button.click(
                fn=self._follow_user,
                inputs=[follow_username],
                outputs=[result_json, chatbot, status_text],
            )
            
            bulk_follow_button.click(
                fn=self._bulk_follow,
                inputs=[bulk_follow_usernames],
                outputs=[result_json, chatbot, status_text],
            )

    async def _initialize_llm_from_settings(self) -> Optional[BaseChatModel]:
        """Initialize LLM from current settings if not already provided."""
        if self.llm:
            return self.llm

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

    def _initialize_twitter_agent(self, cookies_path, persona_path, config_path, headless_mode):
        """Initialize the Twitter agent with the provided configuration."""
        try:
            # Update browser config
            self.browser_config["headless"] = headless_mode
            
            # Initialize LLM
            llm = asyncio.run(self._initialize_llm_from_settings())
            if not llm:
                error_msg = "Failed to initialize LLM. Please check your settings."
                self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
                return "Error: LLM initialization failed", [], [], self.chat_history
            
            # Create Twitter config
            twitter_config = {
                "cookies_path": cookies_path,
                "persona_path": persona_path,
                "config_path": config_path,
            }
            
            # Initialize XAgent if not already available
            if not self.xagent:
                self.xagent = XAgent(
                    llm=llm,
                    browser_config=self.browser_config,
                    mode="stealth",
                    twitter_config=twitter_config,
                )
                
                self.chat_history.append({"role": "assistant", "content": "🚀 Initializing Twitter agent..."})
            else:
                # Update existing XAgent with Twitter config
                self.xagent.twitter_config = twitter_config
                self.xagent.twitter_agent = None  # Force re-initialization
                
                self.chat_history.append({"role": "assistant", "content": "🔄 Updating Twitter agent configuration..."})
            
            # Initialize Twitter agent
            result = asyncio.run(self._init_and_get_personas())
            
            if result["status"] == "success":
                self.twitter_initialized = True
                self.personas = result["personas"]
                persona_choices = [p["name"] for p in self.personas] if self.personas else []
                
                self.chat_history.append({"role": "assistant", "content": "✅ Twitter agent initialized successfully!"})
                if persona_choices:
                    self.chat_history.append({"role": "assistant", "content": f"📋 Found {len(persona_choices)} personas: {', '.join(persona_choices)}"})
                
                return "Ready", gr.update(choices=persona_choices), gr.update(choices=persona_choices), self.chat_history
            else:
                error_msg = result.get("error", "Unknown error")
                self.chat_history.append({"role": "assistant", "content": f"❌ Failed to initialize Twitter agent: {error_msg}"})
                return f"Error: {error_msg}", [], [], self.chat_history
                
        except Exception as e:
            logger.error(f"Error initializing Twitter agent: {e}")
            self.chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            return f"Error: {str(e)}", [], [], self.chat_history

    async def _init_and_get_personas(self):
        """Initialize Twitter agent and get available personas."""
        if not self.xagent or not self.xagent.twitter_agent:
            return {"status": "error", "error": "Twitter agent not available"}
            
        # Initialize Twitter agent
        init_success = await self.xagent.twitter_agent.initialize()
        if not init_success:
            return {"status": "error", "error": self.xagent.twitter_agent.last_error or "Failed to initialize Twitter agent"}
            
        # Get available personas
        personas_result = await self.xagent.get_available_personas()
        if personas_result["status"] == "success":
            return {"status": "success", "personas": personas_result.get("personas", [])}
        else:
            # Initialization succeeded but no personas found
            return {"status": "success", "personas": []}

    def _create_tweet(self, content, media_files, persona_name):
        """Create a new tweet."""
        if not self.twitter_initialized or not self.xagent or not self.xagent.twitter_agent:
            error_msg = "Twitter agent not initialized. Please initialize first."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Not initialized"
        
        if not content.strip():
            error_msg = "Tweet content cannot be empty."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Empty content"
        
        try:
            # Process media files if provided
            media_paths = []
            if media_files:
                for file in media_files:
                    media_paths.append(file.name)
            
            self.chat_history.append({"role": "user", "content": f"Create tweet: {content}"})
            self.chat_history.append({"role": "assistant", "content": "🔄 Creating tweet..."})
            
            # Create the tweet
            result = asyncio.run(self.xagent.create_tweet(
                content=content,
                media_paths=media_paths if media_paths else None,
                persona_name=persona_name if persona_name else None,
            ))
            
            if result["status"] == "success":
                success_msg = f"✅ Tweet created successfully!"
                if "tweet_url" in result:
                    success_msg += f"\n🔗 Tweet URL: {result['tweet_url']}"
                
                self.chat_history.append({"role": "assistant", "content": success_msg})
                return result, self.chat_history, "Tweet created"
            else:
                error_msg = result.get("error", "Unknown error")
                self.chat_history.append({"role": "assistant", "content": f"❌ Failed to create tweet: {error_msg}"})
                return result, self.chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating tweet: {e}")
            self.chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            return {"status": "error", "error": str(e)}, self.chat_history, f"Error: {str(e)}"

    def _reply_to_tweet(self, tweet_url, content, media_files, persona_name):
        """Reply to an existing tweet."""
        if not self.twitter_initialized or not self.xagent or not self.xagent.twitter_agent:
            error_msg = "Twitter agent not initialized. Please initialize first."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Not initialized"
        
        if not tweet_url.strip():
            error_msg = "Tweet URL cannot be empty."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Empty URL"
            
        if not content.strip():
            error_msg = "Reply content cannot be empty."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Empty content"
        
        try:
            # Process media files if provided
            media_paths = []
            if media_files:
                for file in media_files:
                    media_paths.append(file.name)
            
            self.chat_history.append({"role": "user", "content": f"Reply to tweet {tweet_url}: {content}"})
            self.chat_history.append({"role": "assistant", "content": "🔄 Creating reply..."})
            
            # Create the reply
            result = asyncio.run(self.xagent.reply_to_tweet(
                tweet_url=tweet_url,
                content=content,
                media_paths=media_paths if media_paths else None,
                persona_name=persona_name if persona_name else None,
            ))
            
            if result["status"] == "success":
                success_msg = f"✅ Reply created successfully!"
                if "reply_url" in result:
                    success_msg += f"\n🔗 Reply URL: {result['reply_url']}"
                
                self.chat_history.append({"role": "assistant", "content": success_msg})
                return result, self.chat_history, "Reply created"
            else:
                error_msg = result.get("error", "Unknown error")
                self.chat_history.append({"role": "assistant", "content": f"❌ Failed to create reply: {error_msg}"})
                return result, self.chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating reply: {e}")
            self.chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            return {"status": "error", "error": str(e)}, self.chat_history, f"Error: {str(e)}"

    def _follow_user(self, username):
        """Follow a Twitter user."""
        if not self.twitter_initialized or not self.xagent or not self.xagent.twitter_agent:
            error_msg = "Twitter agent not initialized. Please initialize first."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Not initialized"
        
        if not username.strip():
            error_msg = "Username cannot be empty."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Empty username"
        
        try:
            # Clean username (remove @ if present)
            clean_username = username.strip()
            if clean_username.startswith('@'):
                clean_username = clean_username[1:]
            
            self.chat_history.append({"role": "user", "content": f"Follow user: @{clean_username}"})
            self.chat_history.append({"role": "assistant", "content": f"🔄 Following @{clean_username}..."})
            
            # Follow the user
            result = asyncio.run(self.xagent.follow_user(clean_username))
            
            if result["status"] == "success":
                success_msg = f"✅ Successfully followed @{clean_username}!"
                self.chat_history.append({"role": "assistant", "content": success_msg})
                return result, self.chat_history, "User followed"
            else:
                error_msg = result.get("error", "Unknown error")
                self.chat_history.append({"role": "assistant", "content": f"❌ Failed to follow user: {error_msg}"})
                return result, self.chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error following user: {e}")
            self.chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            return {"status": "error", "error": str(e)}, self.chat_history, f"Error: {str(e)}"

    def _bulk_follow(self, usernames_text):
        """Follow multiple Twitter users."""
        if not self.twitter_initialized or not self.xagent or not self.xagent.twitter_agent:
            error_msg = "Twitter agent not initialized. Please initialize first."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Not initialized"
        
        if not usernames_text.strip():
            error_msg = "Usernames list cannot be empty."
            self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return {"status": "error", "error": error_msg}, self.chat_history, "Error: Empty usernames"
        
        try:
            # Process usernames (one per line, remove @ if present)
            usernames = []
            for line in usernames_text.strip().split('\n'):
                username = line.strip()
                if username:
                    if username.startswith('@'):
                        username = username[1:]
                    usernames.append(username)
            
            if not usernames:
                error_msg = "No valid usernames found."
                self.chat_history.append({"role": "assistant", "content": f"❌ {error_msg}"})
                return {"status": "error", "error": error_msg}, self.chat_history, "Error: No valid usernames"
            
            self.chat_history.append({"role": "user", "content": f"Bulk follow {len(usernames)} users"})
            self.chat_history.append({"role": "assistant", "content": f"🔄 Following {len(usernames)} users..."})
            
            # Follow the users
            result = asyncio.run(self.xagent.bulk_follow(usernames))
            
            if result["status"] == "success":
                success_msg = f"✅ Bulk follow completed!\n"
                success_msg += f"📊 Total: {result.get('total', 0)}, "
                success_msg += f"Followed: {result.get('followed', 0)}, "
                success_msg += f"Failed: {result.get('failed', 0)}"
                
                self.chat_history.append({"role": "assistant", "content": success_msg})
                return result, self.chat_history, "Bulk follow completed"
            else:
                error_msg = result.get("error", "Unknown error")
                self.chat_history.append({"role": "assistant", "content": f"❌ Failed to bulk follow: {error_msg}"})
                return result, self.chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error in bulk follow: {e}")
            self.chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            return {"status": "error", "error": str(e)}, self.chat_history, f"Error: {str(e)}"

