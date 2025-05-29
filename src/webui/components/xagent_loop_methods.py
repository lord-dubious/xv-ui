"""
XAgent Loop Methods - Behavioral loop functionality for XAgent UI.

This module contains behavioral loop and scheduling methods for the XAgent interface,
separated for better code organization and maintainability.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import gradio with fallback
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    logging.warning("Gradio not available. UI functionality will be limited.")

logger = logging.getLogger(__name__)


class XAgentLoopMethods:
    """Methods for XAgent behavioral loops and scheduling functionality."""
    
    def __init__(self, tab_instance):
        """Initialize with reference to the tab instance."""
        self.tab = tab_instance
        
    def _save_action_loops(self, profile_name: str, loops_json: str):
        """Save action loops configuration."""
        if not GRADIO_AVAILABLE:
            return "Gradio not available"
            
        try:
            # Import here to avoid circular imports
            from src.agent.xagent.xagent import XAgent
            
            # Initialize XAgent if needed
            if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
                llm = asyncio.run(self.tab.methods._initialize_llm_from_settings())
                if llm:
                    self.tab.xagent = XAgent(
                        llm=llm,
                        browser_config=self.tab.browser_config,
                        profile_name=profile_name,
                    )
            
            if self.tab.xagent:
                result = self.tab.xagent.save_action_loops(loops_json)
                if result["status"] == "success":
                    return f"✅ {result['message']} ({result['loops_count']} loops)"
                else:
                    return f"❌ {result['error']}"
            else:
                return "❌ XAgent not initialized"
                
        except Exception as e:
            logger.error(f"Error saving action loops: {e}")
            return f"❌ Error: {str(e)}"

    def _start_action_loop(self):
        """Start behavioral action loops."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            result = asyncio.run(self.tab.xagent.start_action_loop())
            if result["status"] == "success":
                return f"✅ {result['message']} ({result['loops_count']} loops)"
            else:
                return f"❌ {result['error']}"
                
        except Exception as e:
            logger.error(f"Error starting action loops: {e}")
            return f"❌ Error: {str(e)}"

    def _stop_action_loop(self):
        """Stop behavioral action loops."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            result = asyncio.run(self.tab.xagent.stop_action_loop())
            if result["status"] == "success":
                return f"✅ {result['message']}"
            else:
                return f"❌ {result['error']}"
                
        except Exception as e:
            logger.error(f"Error stopping action loops: {e}")
            return f"❌ Error: {str(e)}"

    def _get_loop_status(self):
        """Get current loop status."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            status = self.tab.xagent.get_action_loops_status()
            if status["loop_running"]:
                return f"🔄 Running ({status['loops_count']} loops active)"
            else:
                return f"⏸️ Stopped ({status['loops_count']} loops configured)"
                
        except Exception as e:
            logger.error(f"Error getting loop status: {e}")
            return f"❌ Error: {str(e)}"

    def _load_loop_template(self, template_name: str):
        """Load a predefined loop template."""
        templates = {
            "daily_engagement": {
                "id": "daily_engagement",
                "description": "Daily Twitter engagement routine",
                "interval_seconds": 3600,
                "rate_limit": {
                    "tweets_per_hour": 5,
                    "follows_per_hour": 10,
                    "min_delay_seconds": 300
                },
                "conditions": {
                    "time_range": {"start": "09:00", "end": "18:00"},
                    "days_of_week": [1, 2, 3, 4, 5]
                },
                "actions": [
                    {
                        "type": "tweet",
                        "params": {
                            "content": "Good morning Twitter! 🌅 Ready for another productive day!",
                            "persona": "tech_enthusiast"
                        },
                        "conditions": {
                            "time_range": {"start": "08:00", "end": "10:00"}
                        }
                    },
                    {
                        "type": "delay",
                        "params": {"seconds": 1800}
                    },
                    {
                        "type": "follow",
                        "params": {"username": "openai"},
                        "conditions": {
                            "max_follows_today": 20
                        }
                    }
                ]
            },
            "content_sharing": {
                "id": "content_sharing",
                "description": "Automated content sharing with engagement",
                "interval_seconds": 7200,
                "rate_limit": {
                    "tweets_per_hour": 3,
                    "replies_per_hour": 5,
                    "min_delay_seconds": 600
                },
                "actions": [
                    {
                        "type": "tweet",
                        "params": {
                            "content": "Sharing some interesting insights about {topic}! 🧠 #AI #Technology",
                            "persona": "tech_enthusiast"
                        }
                    },
                    {
                        "type": "delay",
                        "params": {"seconds": 3600}
                    },
                    {
                        "type": "reply",
                        "params": {
                            "tweet_url": "https://twitter.com/user/status/123",
                            "content": "Great point! This aligns with what we're seeing in the industry.",
                            "persona": "tech_enthusiast"
                        }
                    }
                ]
            },
            "growth_strategy": {
                "id": "growth_strategy",
                "description": "Strategic growth through targeted following and engagement",
                "interval_seconds": 14400,
                "rate_limit": {
                    "follows_per_hour": 15,
                    "tweets_per_hour": 2,
                    "min_delay_seconds": 900
                },
                "conditions": {
                    "follower_count_max": 5000
                },
                "actions": [
                    {
                        "type": "bulk_follow",
                        "params": {
                            "usernames": ["elonmusk", "sundarpichai", "satyanadella"]
                        },
                        "conditions": {
                            "max_follows_today": 50
                        }
                    },
                    {
                        "type": "delay",
                        "params": {"seconds": 2400}
                    },
                    {
                        "type": "tweet",
                        "params": {
                            "content": "Building connections in the tech community! 🤝 #Networking #TechCommunity",
                            "persona": "tech_enthusiast"
                        }
                    }
                ]
            },
            "weekend_casual": {
                "id": "weekend_casual",
                "description": "Casual weekend posting schedule",
                "interval_seconds": 10800,
                "rate_limit": {
                    "tweets_per_hour": 2,
                    "min_delay_seconds": 1800
                },
                "conditions": {
                    "days_of_week": [6, 7]
                },
                "actions": [
                    {
                        "type": "tweet",
                        "params": {
                            "content": "Weekend vibes! 🌟 Taking some time to explore new technologies and ideas.",
                            "persona": "tech_enthusiast"
                        }
                    },
                    {
                        "type": "delay",
                        "params": {"seconds": 5400}
                    }
                ]
            }
        }
        
        template = templates.get(template_name, {})
        return json.dumps(template, indent=2) if template else "{}"

    def _validate_loop_config(self, loops_json: str):
        """Validate loop configuration JSON."""
        try:
            loops = json.loads(loops_json)
            
            if not isinstance(loops, list):
                return "❌ Configuration must be a list of loops"
            
            for i, loop in enumerate(loops):
                if not isinstance(loop, dict):
                    return f"❌ Loop {i+1} must be an object"
                
                required_fields = ["id", "description", "interval_seconds", "actions"]
                for field in required_fields:
                    if field not in loop:
                        return f"�� Loop {i+1} missing required field: {field}"
                
                if not isinstance(loop["actions"], list):
                    return f"❌ Loop {i+1} actions must be a list"
                
                for j, action in enumerate(loop["actions"]):
                    if not isinstance(action, dict):
                        return f"❌ Loop {i+1}, Action {j+1} must be an object"
                    
                    if "type" not in action:
                        return f"❌ Loop {i+1}, Action {j+1} missing type"
                    
                    valid_types = ["tweet", "reply", "follow", "bulk_follow", "delay", "create_list"]
                    if action["type"] not in valid_types:
                        return f"❌ Loop {i+1}, Action {j+1} invalid type: {action['type']}"
            
            return "✅ Configuration is valid"
            
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {str(e)}"
        except Exception as e:
            return f"❌ Validation error: {str(e)}"

    def _get_loop_statistics(self):
        """Get loop execution statistics."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            # This would be expanded with actual statistics tracking
            status = self.tab.xagent.get_action_loops_status()
            
            stats = {
                "total_loops": status["loops_count"],
                "running": status["loop_running"],
                "last_execution": "Not available",
                "total_actions_executed": "Not tracked yet",
                "success_rate": "Not tracked yet"
            }
            
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting loop statistics: {e}")
            return f"❌ Error: {str(e)}"

    def _update_rate_limits(self, tweets_per_hour: int, follows_per_hour: int, min_delay_seconds: int):
        """Update rate limiting settings."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            if self.tab.xagent.rate_limiter:
                # Update custom limits
                custom_limits = {
                    "tweets": tweets_per_hour,
                    "follows": follows_per_hour,
                }
                self.tab.xagent.rate_limiter.set_custom_limits(custom_limits)
                
                # Update minimum delays
                min_delays = {
                    "tweets": min_delay_seconds,
                    "follows": min_delay_seconds // 2,  # Follows can be faster
                    "replies": min_delay_seconds,
                }
                self.tab.xagent.rate_limiter.set_min_delays(min_delays)
                
                return f"✅ Updated rate limits: {tweets_per_hour} tweets/hour, {follows_per_hour} follows/hour, {min_delay_seconds}s min delay"
            else:
                return "❌ Rate limiter not available"
                
        except Exception as e:
            logger.error(f"Error updating rate limits: {e}")
            return f"❌ Error: {str(e)}"

    def _get_performance_stats(self):
        """Get comprehensive performance statistics."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            stats = {}
            
            # Rate limiting stats
            if self.tab.xagent.rate_limiter:
                stats["rate_limiting"] = self.tab.xagent.rate_limiter.get_statistics()
            
            # Performance monitoring stats
            if self.tab.xagent.performance_monitor:
                stats["performance"] = self.tab.xagent.performance_monitor.export_performance_data()
            
            # Cache stats
            if self.tab.xagent.action_cache:
                stats["cache"] = self.tab.xagent.action_cache.get_statistics()
            
            # Loop status
            loop_status = self.tab.xagent.get_action_loops_status()
            stats["loops"] = {
                "running": loop_status["loop_running"],
                "total_loops": loop_status["loops_count"],
                "timestamp": loop_status["timestamp"],
            }
            
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return f"❌ Error: {str(e)}"

    def _optimize_performance(self):
        """Analyze and optimize performance."""
        if not hasattr(self.tab, 'xagent') or not self.tab.xagent:
            return "❌ XAgent not initialized"
            
        try:
            optimizations = []
            
            # Get performance analysis
            if self.tab.xagent.performance_monitor:
                analysis = self.tab.xagent.performance_monitor.optimize_performance()
                optimizations.extend(analysis.get("optimizations", []))
            
            # Check rate limiting efficiency
            if self.tab.xagent.rate_limiter:
                rate_stats = self.tab.xagent.rate_limiter.get_statistics()
                
                # Suggest optimizations based on rate limiting
                for action_type, stats in rate_stats.items():
                    if isinstance(stats, dict) and stats.get("wait_time", 0) > 300:  # 5 minutes
                        optimizations.append({
                            "type": "rate_limiting",
                            "operation": action_type,
                            "issue": f"Long wait times: {stats['wait_time']:.1f}s",
                            "suggestion": "Consider reducing action frequency or increasing limits",
                        })
            
            # Check cache efficiency
            if self.tab.xagent.action_cache:
                cache_stats = self.tab.xagent.action_cache.get_statistics()
                hit_rate = cache_stats.get("hit_rate", 0)
                
                if hit_rate < 20:  # Low cache hit rate
                    optimizations.append({
                        "type": "caching",
                        "operation": "cache",
                        "issue": f"Low cache hit rate: {hit_rate}%",
                        "suggestion": "Review caching strategy or increase cache TTL",
                    })
            
            result = {
                "optimizations": optimizations,
                "total_issues": len(optimizations),
                "recommendations": [
                    "Monitor performance regularly",
                    "Adjust rate limits based on Twitter API responses",
                    "Use caching for repeated operations",
                    "Enable adaptive delays for error recovery",
                ],
                "timestamp": datetime.now().isoformat(),
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error optimizing performance: {e}")
            return f"❌ Error: {str(e)}"
