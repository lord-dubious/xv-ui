"""
Shared utilities for environment variable handling in WebUI components.
"""

from typing import Any, Dict


def get_env_value(env_settings: Dict[str, str], key: str, default: Any, type_cast=None) -> Any:
    """
    Get environment variable value with type casting and error handling.
    
    Args:
        env_settings: Dictionary of environment settings
        key: Environment variable key
        default: Default value if key not found or conversion fails
        type_cast: Type to cast the value to (bool, int, float, etc.)
        
    Returns:
        The environment value cast to the specified type, or default value
    """
    val = env_settings.get(key, default)
    if type_cast:
        try:
            if type_cast is bool:
                return str(val).lower() == "true"
            return type_cast(val)
        except (ValueError, TypeError):
            return default
    return val


def load_env_settings_with_cache(webui_manager, force_reload: bool = False) -> Dict[str, str]:
    """
    Load environment settings with caching to avoid repeated file reads.
    
    Args:
        webui_manager: WebUI manager instance
        force_reload: Force reload from file even if cached
        
    Returns:
        Dictionary of environment settings
    """
    # Check if we have cached settings and don't need to reload
    if not force_reload and hasattr(webui_manager, '_cached_env_settings'):
        return webui_manager._cached_env_settings
    
    # Load fresh settings and cache them
    env_settings = webui_manager.load_env_settings()
    webui_manager._cached_env_settings = env_settings
    return env_settings


def invalidate_env_cache(webui_manager):
    """
    Invalidate the cached environment settings to force reload on next access.
    
    Args:
        webui_manager: WebUI manager instance
    """
    if hasattr(webui_manager, '_cached_env_settings'):
        delattr(webui_manager, '_cached_env_settings')
