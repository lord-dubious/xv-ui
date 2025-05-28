"""
Twitter Agent - Integration of twagent functionality into XAgent.

This module provides Twitter automation capabilities within the XAgent framework,
leveraging the twagent library for browser-based Twitter interactions.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.agent.xagent.xagent import XAgent
from src.browser.stealth_browser import StealthBrowser

# Import twagent components
try:
    # These imports will work after the twagent library is installed
    from browser_use.my_twitter_api_v3.follows.follow_system import FollowSystem
    from browser_use.my_twitter_api_v3.follows.follow_user import FollowUser
    from browser_use.my_twitter_api_v3.lists.create_list import CreateList
    from browser_use.my_twitter_api_v3.manage_posts.create_post import CreatePost
    from browser_use.my_twitter_api_v3.manage_posts.reply_to_post import ReplyToPost
    from browser_use.my_twitter_api_v3.persona_manager import PersonaManager
    from browser_use.my_twitter_api_v3.tweet_generator import TweetGenerator
    from browser_use.twitter_api import TwitterAPI
    TWAGENT_AVAILABLE = True
except ImportError:
    TWAGENT_AVAILABLE = False
    logging.warning("Twagent components not available. Twitter functionality will be limited.")

logger = logging.getLogger(__name__)


class TwitterAgent:
    """
    TwitterAgent - Integration of twagent functionality into XAgent.
    
    This class extends XAgent with Twitter-specific capabilities, including:
    - Automated tweeting and replying
    - Following users and managing lists
    - Persona-based content generation
    - Cookie-based authentication
    """

    def __init__(
        self,
        xagent: XAgent,
        cookies_path: Optional[str] = None,
        persona_path: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        """
        Initialize TwitterAgent with XAgent integration.
        
        Args:
            xagent: The parent XAgent instance
            cookies_path: Path to Twitter cookies JSON file
            persona_path: Path to persona configuration directory
            config_path: Path to twagent config JSON file
        """
        self.xagent = xagent
        self.cookies_path = cookies_path
        self.persona_path = persona_path
        self.config_path = config_path
        
        # Twitter API instance
        self.twitter_api = None
        self.persona_manager = None
        self.tweet_generator = None
        
        # Status tracking
        self.initialized = False
        self.last_error = None
        
        logger.info("🐦 TwitterAgent initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize Twitter API and components.
        
        Returns:
            bool: True if initialization was successful
        """
        if not TWAGENT_AVAILABLE:
            self.last_error = "Twagent components not available"
            logger.error(self.last_error)
            return False
            
        try:
            # Load configuration
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Initialize browser if needed
            if not hasattr(self.xagent, 'browser') or not self.xagent.browser:
                logger.info("Creating new browser instance for TwitterAgent")
                self.xagent.browser = await self.xagent._create_stealth_browser()
                self.xagent.context = await self.xagent._create_stealth_context(self.xagent.browser)
            
            # Initialize Twitter API with the XAgent's browser
            self.twitter_api = TwitterAPI(
                browser=self.xagent.browser,
                context=self.xagent.context,
                cookies_file=self.cookies_path,
            )
            
            # Initialize persona manager if persona path provided
            if self.persona_path and os.path.exists(self.persona_path):
                self.persona_manager = PersonaManager(
                    persona_directory=self.persona_path,
                    twitter_api=self.twitter_api,
                )
                
                # Initialize tweet generator
                self.tweet_generator = TweetGenerator(
                    twitter_api=self.twitter_api,
                    persona_manager=self.persona_manager,
                    llm=self.xagent.llm,
                )
            
            self.initialized = True
            logger.info("🐦 TwitterAgent successfully initialized")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to initialize TwitterAgent: {e}")
            return False
    
    async def create_tweet(
        self, 
        content: str, 
        media_paths: Optional[List[str]] = None,
        persona_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new tweet.
        
        Args:
            content: Tweet text content
            media_paths: Optional list of paths to media files to attach
            persona_name: Optional persona to use for tweet generation
            
        Returns:
            Dict with tweet result information
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {
                "status": "error",
                "error": f"TwitterAgent not initialized: {self.last_error}",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            # Use persona-based tweet if persona specified
            if persona_name and self.persona_manager and self.tweet_generator:
                persona = self.persona_manager.get_persona(persona_name)
                if not persona:
                    return {
                        "status": "error",
                        "error": f"Persona '{persona_name}' not found",
                        "timestamp": datetime.now().isoformat(),
                    }
                
                # Generate tweet using persona
                tweet_content = await self.tweet_generator.generate_tweet(
                    persona=persona,
                    base_content=content,
                )
                
                logger.info(f"Generated persona-based tweet: {tweet_content}")
                content = tweet_content
            
            # Create the tweet
            create_post = CreatePost(
                twitter_api=self.twitter_api,
                text=content,
                media_paths=media_paths or [],
            )
            
            result = await create_post.execute()
            
            return {
                "status": "success",
                "tweet_url": result.get("tweet_url"),
                "tweet_id": result.get("tweet_id"),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating tweet: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def reply_to_tweet(
        self,
        tweet_url: str,
        content: str,
        media_paths: Optional[List[str]] = None,
        persona_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reply to an existing tweet.
        
        Args:
            tweet_url: URL of the tweet to reply to
            content: Reply text content
            media_paths: Optional list of paths to media files to attach
            persona_name: Optional persona to use for reply generation
            
        Returns:
            Dict with reply result information
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {
                "status": "error",
                "error": f"TwitterAgent not initialized: {self.last_error}",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            # Use persona-based reply if persona specified
            if persona_name and self.persona_manager and self.tweet_generator:
                persona = self.persona_manager.get_persona(persona_name)
                if not persona:
                    return {
                        "status": "error",
                        "error": f"Persona '{persona_name}' not found",
                        "timestamp": datetime.now().isoformat(),
                    }
                
                # Generate reply using persona
                reply_content = await self.tweet_generator.generate_reply(
                    persona=persona,
                    tweet_url=tweet_url,
                    base_content=content,
                )
                
                logger.info(f"Generated persona-based reply: {reply_content}")
                content = reply_content
            
            # Create the reply
            reply_post = ReplyToPost(
                twitter_api=self.twitter_api,
                tweet_url=tweet_url,
                text=content,
                media_paths=media_paths or [],
            )
            
            result = await reply_post.execute()
            
            return {
                "status": "success",
                "reply_url": result.get("reply_url"),
                "reply_id": result.get("reply_id"),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def follow_user(self, username: str) -> Dict[str, Any]:
        """
        Follow a Twitter user.
        
        Args:
            username: Twitter username to follow (without @)
            
        Returns:
            Dict with follow result information
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {
                "status": "error",
                "error": f"TwitterAgent not initialized: {self.last_error}",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            follow_user = FollowUser(
                twitter_api=self.twitter_api,
                username=username,
            )
            
            result = await follow_user.execute()
            
            return {
                "status": "success",
                "username": username,
                "followed": result.get("followed", False),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error following user: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def bulk_follow(self, usernames: List[str]) -> Dict[str, Any]:
        """
        Follow multiple Twitter users.
        
        Args:
            usernames: List of Twitter usernames to follow
            
        Returns:
            Dict with bulk follow result information
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {
                "status": "error",
                "error": f"TwitterAgent not initialized: {self.last_error}",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            follow_system = FollowSystem(
                twitter_api=self.twitter_api,
                usernames=usernames,
            )
            
            results = await follow_system.execute()
            
            return {
                "status": "success",
                "total": len(usernames),
                "followed": results.get("followed_count", 0),
                "failed": results.get("failed_count", 0),
                "details": results.get("details", []),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error in bulk follow: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def create_list(
        self, 
        name: str, 
        description: str, 
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new Twitter list.
        
        Args:
            name: List name
            description: List description
            is_private: Whether the list should be private
            
        Returns:
            Dict with list creation result information
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {
                "status": "error",
                "error": f"TwitterAgent not initialized: {self.last_error}",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            create_list = CreateList(
                twitter_api=self.twitter_api,
                name=name,
                description=description,
                is_private=is_private,
            )
            
            result = await create_list.execute()
            
            return {
                "status": "success",
                "list_id": result.get("list_id"),
                "list_url": result.get("list_url"),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating list: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def get_available_personas(self) -> Dict[str, Any]:
        """
        Get list of available personas.
        
        Returns:
            Dict with persona information
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.persona_manager:
            return {
                "status": "error",
                "error": "Persona manager not initialized",
                "timestamp": datetime.now().isoformat(),
            }
        
        try:
            personas = self.persona_manager.list_personas()
            
            return {
                "status": "success",
                "personas": personas,
                "count": len(personas),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting personas: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def close(self):
        """Close the TwitterAgent and clean up resources."""
        logger.info("Closing TwitterAgent")
        # No specific cleanup needed as the browser is managed by XAgent
        self.initialized = False

