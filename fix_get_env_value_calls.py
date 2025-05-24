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


if __name__ == "__main__":
    fix_agent_settings_tab("src/webui/components/agent_settings_tab.py")
