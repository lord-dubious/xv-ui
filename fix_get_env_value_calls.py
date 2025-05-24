#!/usr/bin/env python3
"""
Comprehensive script to fix all issues in agent_settings_tab.py
1. Fix get_env_value function calls parameter order
2. Fix complex multi-line calls
3. Fix type checking issues
"""

import re


def fix_agent_settings_tab(file_path):
    """Fix all issues in agent_settings_tab.py"""

    with open(file_path, "r") as f:
        content = f.read()

    # Fix the remaining planner API key call
    content = re.sub(
        r'value=get_env_value\(\s*f"\{str\(initial_planner_llm_provider\)\.upper\(\)\}_API_KEY"\s*if initial_planner_llm_provider\s*else "",\s*"",\s*\)\s*if initial_planner_llm_provider\s*else "",',
        'value=(\n                    get_env_value(\n                        env_settings,\n                        f"{str(initial_planner_llm_provider).upper()}_API_KEY",\n                        ""\n                    )\n                    if initial_planner_llm_provider\n                    else ""\n                ),',
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Fix the tab_components.update() call - change dict() to regular dict literal
    content = re.sub(
        r"tab_components\.update\(\s*dict\(", "tab_components.update({", content
    )

    # Fix the closing of the dict() call
    content = re.sub(
        r"(\s+)\)\s*\)\s*webui_manager\.add_components",
        r"\1})\n    webui_manager.add_components",
        content,
    )

    with open(file_path, "w") as f:
        f.write(content)

    print(f"Fixed all issues in {file_path}")


def fix_browser_use_agent_tab(file_path):
    """Fix get_env_value calls in browser_use_agent_tab.py"""

    with open(file_path, "r") as f:
        content = f.read()

    # Fix the get_setting function to use correct parameter order
    content = re.sub(
        r"return get_env_value\(env_key, default\)",
        "return get_env_value(env_settings, env_key, default)",
        content,
    )

    # Fix all other get_env_value calls
    # Pattern to match get_env_value calls
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
    f_string_pattern = (
        r'get_env_value\(\s*f"([^"]+)"\s*,\s*([^,)]+)(?:\s*,\s*([^)]+))?\s*\)'
    )

    def replace_f_string_call(match):
        key = match.group(1)
        default = match.group(2)
        type_cast = match.group(3)

        if type_cast:
            return f'get_env_value(env_settings, f"{key}", {default}, {type_cast})'
        else:
            return f'get_env_value(env_settings, f"{key}", {default})'

    fixed_content = re.sub(f_string_pattern, replace_f_string_call, fixed_content)

    with open(file_path, "w") as f:
        f.write(fixed_content)

    print(f"Fixed get_env_value calls in {file_path}")


if __name__ == "__main__":
    fix_agent_settings_tab("src/webui/components/agent_settings_tab.py")
    fix_browser_use_agent_tab("src/webui/components/browser_use_agent_tab.py")
