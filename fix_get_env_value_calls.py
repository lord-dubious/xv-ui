#!/usr/bin/env python3
"""
Script to fix get_env_value function calls in agent_settings_tab.py
Changes from: get_env_value("KEY", default, type_cast)
To: get_env_value(env_settings, "KEY", default, type_cast)
"""

import re

def fix_get_env_value_calls(file_path):
    """Fix all get_env_value calls to use the correct parameter order"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match get_env_value calls
    # Matches: get_env_value("KEY", default) or get_env_value("KEY", default, type_cast)
    pattern = r'get_env_value\(\s*"([^"]+)"\s*,\s*([^,)]+)(?:\s*,\s*([^)]+))?\s*\)'
    
    def replace_call(match):
        key = match.group(1)
        default = match.group(2)
        type_cast = match.group(3)
        
        if type_cast:
            return f'get_env_value(env_settings, "{key}", {default}, {type_cast})'
        else:
            return f'get_env_value(env_settings, "{key}", {default})'
    
    # Replace all occurrences
    fixed_content = re.sub(pattern, replace_call, content)
    
    # Also fix f-string cases
    f_string_pattern = r'get_env_value\(\s*f"([^"]+)"\s*,\s*([^,)]+)(?:\s*,\s*([^)]+))?\s*\)'
    
    def replace_f_string_call(match):
        key = match.group(1)
        default = match.group(2)
        type_cast = match.group(3)
        
        if type_cast:
            return f'get_env_value(env_settings, f"{key}", {default}, {type_cast})'
        else:
            return f'get_env_value(env_settings, f"{key}", {default})'
    
    fixed_content = re.sub(f_string_pattern, replace_f_string_call, fixed_content)
    
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed get_env_value calls in {file_path}")

if __name__ == "__main__":
    fix_get_env_value_calls("src/webui/components/agent_settings_tab.py")
