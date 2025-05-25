import gradio as gr

from src.webui.components.agent_settings_tab import create_agent_settings_tab
from src.webui.components.browser_settings_tab import create_browser_settings_tab
from src.webui.components.browser_use_agent_tab import create_browser_use_agent_tab
from src.webui.components.deep_research_agent_tab import create_deep_research_agent_tab
from src.webui.components.load_save_config_tab import create_load_save_config_tab
from src.webui.components.xagent_tab import XAgentTab
from src.webui.webui_manager import WebuiManager

theme_map = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base(),
}


def create_ui(theme_name="Ocean"):
    """
    Builds and returns the main Gradio-based web UI for browser control with AI assistance.
    
    The interface includes custom styling, dark mode enforcement, and a tabbed layout for agent settings, browser settings, agent execution, agent marketplace (with XAgent and Deep Research tabs), and configuration management.
    
    Args:
        theme_name: The name of the Gradio theme to apply to the UI. Defaults to "Ocean".
    
    Returns:
        A Gradio Blocks object representing the complete web UI.
    """
    css = """
    .gradio-container {
        width: 70vw !important;
        max-width: 70% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 20px;
    }
    .tab-header-text {
        text-align: center;
    }
    .theme-section {
        margin-bottom: 10px;
        padding: 15px;
        border-radius: 10px;
    }
    """

    # dark mode in default
    js_func = """
    function refresh() {
        const url = new URL(window.location);

        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
        title="Browser Use WebUI",
        theme=theme_map[theme_name],
        css=css,
        js=js_func,
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 🌐 Browser Use WebUI
                ### Control your browser with AI assistance
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs():
            with gr.TabItem("⚙️ Agent Settings"):
                create_agent_settings_tab(ui_manager)

            with gr.TabItem("🌐 Browser Settings"):
                create_browser_settings_tab(ui_manager)

            with gr.TabItem("🤖 Run Agent"):
                create_browser_use_agent_tab(ui_manager)

            with gr.TabItem("🎁 Agent Marketplace"):
                gr.Markdown(
                    """
                    ### Agents built on Browser-Use
                    """,
                    elem_classes=["tab-header-text"],
                )
                with gr.Tabs():
                    with gr.TabItem("🎭 XAgent (Stealth + Proxy)"):
                        # Create XAgent tab with browser config
                        browser_config = {
                            "headless": False,
                            "window_width": 1280,
                            "window_height": 1100,
                            "disable_security": False,
                        }
                        xagent_tab = XAgentTab(llm=None, browser_config=browser_config)
                        xagent_tab.create_tab()

                    with gr.TabItem("🔍 Deep Research"):
                        create_deep_research_agent_tab(ui_manager)

            with gr.TabItem("📁 Load & Save Config"):
                create_load_save_config_tab(ui_manager)

    return demo
