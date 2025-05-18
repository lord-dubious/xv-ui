import os
import shutil
from typing import Dict, Optional, List, Tuple


def ensure_env_file_exists(env_path: str = '.env', example_env_path: str = '.env.example') -> bool:
    """
    Ensures that the .env file exists. If it doesn't, creates it from the example file or creates an empty one.
    
    Args:
        env_path: Path to the .env file
        example_env_path: Path to the example .env file
        
    Returns:
        bool: True if the file was created, False if it already existed
    """
    if os.path.exists(env_path):
        return False
    
    # If example file exists, copy it
    if os.path.exists(example_env_path):
        shutil.copy2(example_env_path, env_path)
    else:
        # Create an empty .env file
        with open(env_path, 'w') as f:
            f.write("# Environment Variables\n")
    
    return True


def read_env_file(env_path: str = '.env') -> Dict[str, str]:
    """
    Reads the .env file and returns a dictionary of key-value pairs.
    
    Args:
        env_path: Path to the .env file
        
    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    env_vars = {}
    
    if not os.path.exists(env_path):
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Split by the first equals sign
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def write_env_file(env_vars: Dict[str, str], env_path: str = '.env', 
                   preserve_comments: bool = True, 
                   preserve_order: bool = True) -> bool:
    """
    Writes environment variables to the .env file.
    
    Args:
        env_vars: Dictionary of environment variables
        env_path: Path to the .env file
        preserve_comments: Whether to preserve comments in the file
        preserve_order: Whether to preserve the order of variables in the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if preserve_comments and preserve_order and os.path.exists(env_path):
            # Read the existing file to preserve comments and order
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update existing variables and track which ones were updated
            updated_keys = set()
            for i, line in enumerate(lines):
                if not line.strip() or line.strip().startswith('#'):
                    continue
                
                if '=' in line:
                    key = line.split('=', 1)[0].strip()
                    if key in env_vars:
                        lines[i] = f"{key}={env_vars[key]}\n"
                        updated_keys.add(key)
            
            # Add new variables at the end
            for key, value in env_vars.items():
                if key not in updated_keys:
                    lines.append(f"{key}={value}\n")
            
            # Write back to the file
            with open(env_path, 'w') as f:
                f.writelines(lines)
        else:
            # Simple write without preserving comments or order
            with open(env_path, 'w') as f:
                f.write("# Environment Variables\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
        
        return True
    except Exception as e:
        print(f"Error writing to .env file: {e}")
        return False


def is_sensitive_key(key: str) -> bool:
    """
    Determines if an environment variable key is sensitive (e.g., API keys, passwords).
    
    Args:
        key: The environment variable key
        
    Returns:
        bool: True if the key is sensitive, False otherwise
    """
    sensitive_patterns = ['API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'PRIVATE']
    key_upper = key.upper()
    
    return any(pattern in key_upper for pattern in sensitive_patterns)


def get_env_groups() -> List[Tuple[str, List[str]]]:
    """
    Returns a list of environment variable groups for UI organization.
    
    Returns:
        List[Tuple[str, List[str]]]: List of (group_name, [key_patterns]) tuples
    """
    return [
        ("API Keys", ["API_KEY", "KEY"]),
        ("Endpoints", ["ENDPOINT", "URL", "HOST"]),
        ("Browser Settings", ["BROWSER", "RESOLUTION", "CDP"]),
        ("VNC Settings", ["VNC"]),
        ("Other Settings", [])  # Catch-all for variables that don't match other groups
    ]


def categorize_env_var(key: str) -> str:
    """
    Categorizes an environment variable key into a group.
    
    Args:
        key: The environment variable key
        
    Returns:
        str: The group name
    """
    key_upper = key.upper()
    
    for group_name, patterns in get_env_groups():
        if any(pattern in key_upper for pattern in patterns):
            return group_name
    
    return "Other Settings"  # Default group
