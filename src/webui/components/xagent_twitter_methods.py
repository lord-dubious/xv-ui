"""
XAgent Twitter Methods - Twitter-specific functionality for XAgent tab.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

logger = logging.getLogger(__name__)


class XAgentTwitterMethods:
    """Twitter-specific methods for XAgent tab."""
    
    def __init__(self, tab_instance):
        """Initialize with reference to the tab instance."""
        self.tab = tab_instance
        
    def _create_tweet(self, content: str, media_files, persona_name: Optional[str]):
        """Create a new tweet."""
        if not self.tab.twitter_initialized or not self.tab.xagent:
            error_msg = "Twitter not initialized. Please initialize Twitter first."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Not initialized"
        
        if not content.strip():
            error_msg = "Tweet content cannot be empty."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Empty content"
        
        try:
            # Process media files if provided
            media_paths = []
            if media_files:
                for file in media_files:
                    media_paths.append(file.name)
            
            chat_history = [
                {"role": "user", "content": f"Create tweet: {content}"},
                {"role": "assistant", "content": "🔄 Creating tweet..."}
            ]
            
            # Create the tweet
            result = asyncio.run(self.tab.xagent.create_tweet(
                content=content,
                media_paths=media_paths if media_paths else None,
                persona_name=persona_name if persona_name else None,
            ))
            
            if result["status"] == "success":
                success_msg = "✅ Tweet created successfully!"
                if "tweet_url" in result:
                    success_msg += f"\n🔗 Tweet URL: {result['tweet_url']}"
                
                chat_history.append({"role": "assistant", "content": success_msg})
                return result, chat_history, "Tweet created"
            else:
                error_msg = result.get("error", "Unknown error")
                chat_history.append({"role": "assistant", "content": f"❌ Failed to create tweet: {error_msg}"})
                return result, chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating tweet: {e}")
            chat_history = [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
            return {"status": "error", "error": str(e)}, chat_history, f"Error: {str(e)}"

    def _reply_to_tweet(self, tweet_url: str, content: str, media_files, persona_name: Optional[str]):
        """Reply to an existing tweet."""
        if not self.tab.twitter_initialized or not self.tab.xagent:
            error_msg = "Twitter not initialized. Please initialize Twitter first."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Not initialized"
        
        if not tweet_url.strip():
            error_msg = "Tweet URL cannot be empty."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Empty URL"
            
        if not content.strip():
            error_msg = "Reply content cannot be empty."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Empty content"
        
        try:
            # Process media files if provided
            media_paths = []
            if media_files:
                for file in media_files:
                    media_paths.append(file.name)
            
            chat_history = [
                {"role": "user", "content": f"Reply to tweet {tweet_url}: {content}"},
                {"role": "assistant", "content": "🔄 Creating reply..."}
            ]
            
            # Create the reply
            result = asyncio.run(self.tab.xagent.reply_to_tweet(
                tweet_url=tweet_url,
                content=content,
                media_paths=media_paths if media_paths else None,
                persona_name=persona_name if persona_name else None,
            ))
            
            if result["status"] == "success":
                success_msg = "✅ Reply created successfully!"
                if "reply_url" in result:
                    success_msg += f"\n🔗 Reply URL: {result['reply_url']}"
                
                chat_history.append({"role": "assistant", "content": success_msg})
                return result, chat_history, "Reply created"
            else:
                error_msg = result.get("error", "Unknown error")
                chat_history.append({"role": "assistant", "content": f"❌ Failed to create reply: {error_msg}"})
                return result, chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating reply: {e}")
            chat_history = [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
            return {"status": "error", "error": str(e)}, chat_history, f"Error: {str(e)}"

    def _follow_user(self, username: str):
        """Follow a Twitter user."""
        if not self.tab.twitter_initialized or not self.tab.xagent:
            error_msg = "Twitter not initialized. Please initialize Twitter first."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Not initialized"
        
        if not username.strip():
            error_msg = "Username cannot be empty."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Empty username"
        
        try:
            # Clean username (remove @ if present)
            clean_username = username.strip()
            if clean_username.startswith('@'):
                clean_username = clean_username[1:]
            
            chat_history = [
                {"role": "user", "content": f"Follow user: @{clean_username}"},
                {"role": "assistant", "content": f"🔄 Following @{clean_username}..."}
            ]
            
            # Follow the user
            result = asyncio.run(self.tab.xagent.follow_user(clean_username))
            
            if result["status"] == "success":
                success_msg = f"✅ Successfully followed @{clean_username}!"
                chat_history.append({"role": "assistant", "content": success_msg})
                return result, chat_history, "User followed"
            else:
                error_msg = result.get("error", "Unknown error")
                chat_history.append({"role": "assistant", "content": f"❌ Failed to follow user: {error_msg}"})
                return result, chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error following user: {e}")
            chat_history = [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
            return {"status": "error", "error": str(e)}, chat_history, f"Error: {str(e)}"

    def _bulk_follow(self, usernames_text: str):
        """Follow multiple Twitter users."""
        if not self.tab.twitter_initialized or not self.tab.xagent:
            error_msg = "Twitter not initialized. Please initialize Twitter first."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Not initialized"
        
        if not usernames_text.strip():
            error_msg = "Usernames list cannot be empty."
            chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
            return {"status": "error", "error": error_msg}, chat_history, "Error: Empty usernames"
        
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
                chat_history = [{"role": "assistant", "content": f"❌ {error_msg}"}]
                return {"status": "error", "error": error_msg}, chat_history, "Error: No valid usernames"
            
            chat_history = [
                {"role": "user", "content": f"Bulk follow {len(usernames)} users"},
                {"role": "assistant", "content": f"🔄 Following {len(usernames)} users..."}
            ]
            
            # Follow the users
            result = asyncio.run(self.tab.xagent.bulk_follow(usernames))
            
            if result["status"] == "success":
                success_msg = "✅ Bulk follow completed!\n"
                success_msg += f"📊 Total: {result.get('total', 0)}, "
                success_msg += f"Followed: {result.get('followed', 0)}, "
                success_msg += f"Failed: {result.get('failed', 0)}"
                
                chat_history.append({"role": "assistant", "content": success_msg})
                return result, chat_history, "Bulk follow completed"
            else:
                error_msg = result.get("error", "Unknown error")
                chat_history.append({"role": "assistant", "content": f"❌ Failed to bulk follow: {error_msg}"})
                return result, chat_history, f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error in bulk follow: {e}")
            chat_history = [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
            return {"status": "error", "error": str(e)}, chat_history, f"Error: {str(e)}"

