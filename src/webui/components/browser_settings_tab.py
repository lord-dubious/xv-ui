import logging

import gradio as gr

from src.webui.utils.env_utils import get_env_value, load_env_settings_with_cache
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def close_browser(webui_manager: WebuiManager):
    """
    Close browser
    """
    if webui_manager.bu_current_task and not webui_manager.bu_current_task.done():
        webui_manager.bu_current_task.cancel()
        webui_manager.bu_current_task = None

    if webui_manager.bu_browser_context:
        logger.info("⚠️ Closing browser context when changing browser config.")
        await webui_manager.bu_browser_context.close()
        webui_manager.bu_browser_context = None

    if webui_manager.bu_browser:
        logger.info("⚠️ Closing browser when changing browser config.")
        await webui_manager.bu_browser.close()
        webui_manager.bu_browser = None


def create_browser_settings_tab(webui_manager: WebuiManager):
    """
    Creates a browser settings tab.
    """
    # Load persistent settings from environment
    env_settings = load_env_settings_with_cache(webui_manager)

    tab_components = {}

    with gr.Group():
        with gr.Row():
            browser_binary_path = gr.Textbox(
                label="Browser Binary Path",
                lines=1,
                interactive=True,
                value=get_env_value(env_settings, "BROWSER_PATH", ""),
                placeholder="e.g. '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome'",
            )
            browser_user_data_dir = gr.Textbox(
                label="Browser User Data Dir",
                lines=1,
                interactive=True,
                value=get_env_value(env_settings, "BROWSER_USER_DATA", ""),
                placeholder="Leave it empty if you use your default user data",
            )
    with gr.Group():
        with gr.Row():
            use_own_browser = gr.Checkbox(
                label="Use Own Browser",
                value=get_env_value(env_settings, "USE_OWN_BROWSER", False, bool),
                info="Use your existing browser instance",
                interactive=True,
            )
            keep_browser_open = gr.Checkbox(
                label="Keep Browser Open",
                value=get_env_value(env_settings, "KEEP_BROWSER_OPEN", True, bool),
                info="Keep Browser Open between Tasks",
                interactive=True,
            )
            headless = gr.Checkbox(
                label="Headless Mode",
                value=get_env_value(env_settings, "HEADLESS", False, bool),
                info="Run browser without GUI",
                interactive=True,
            )
            disable_security = gr.Checkbox(
                label="Disable Security",
                value=get_env_value(env_settings, "DISABLE_SECURITY", False, bool),
                info="Disable browser security",
                interactive=True,
            )

    with gr.Group():
        with gr.Row():
            window_w = gr.Number(
                label="Window Width",
                value=get_env_value(env_settings, "RESOLUTION_WIDTH", 1280, int),
                info="Browser window width",
                interactive=True,
            )
            window_h = gr.Number(
                label="Window Height",
                value=get_env_value(env_settings, "RESOLUTION_HEIGHT", 1100, int),
                info="Browser window height",
                interactive=True,
            )
    with gr.Group():
        with gr.Row():
            cdp_url = gr.Textbox(
                label="CDP URL",
                value=get_env_value(env_settings, "BROWSER_CDP", ""),
                info="CDP URL for browser remote debugging",
                interactive=True,
            )
            wss_url = gr.Textbox(
                label="WSS URL",
                value=get_env_value(env_settings, "WSS_URL", ""),
                info="WSS URL for browser remote debugging",
                interactive=True,
            )
    with gr.Group():
        with gr.Row():
            recording_path_input = gr.Textbox(
                label="Recording Path",
                value=get_env_value(env_settings, "SAVE_RECORDING_PATH", ""),
                placeholder="e.g. ./tmp/record_videos",
                info="Path to save browser recordings",
                interactive=True,
            )

            trace_path_input = gr.Textbox(
                label="Trace Path",
                value=get_env_value(env_settings, "SAVE_TRACE_PATH", ""),
                placeholder="e.g. ./tmp/traces",
                info="Path to save Agent traces",
                interactive=True,
            )

        with gr.Row():
            agent_history_path_input = gr.Textbox(
                label="Agent History Save Path",
                value=get_env_value(
                    env_settings, "SAVE_AGENT_HISTORY_PATH", "./tmp/agent_history"
                ),
                info="Specify the directory where agent history should be saved.",
                interactive=True,
            )
            download_path_input = gr.Textbox(
                label="Save Directory for browser downloads",
                value=get_env_value(
                    env_settings, "SAVE_DOWNLOAD_PATH", "./tmp/downloads"
                ),
                info="Specify the directory where downloaded files should be saved.",
                interactive=True,
            )

    # Add a note about auto-saving
    with gr.Group():
        gr.Markdown("*Settings are automatically saved to .env file*")
    tab_components.update(
        {
            "browser_binary_path": browser_binary_path,
            "browser_user_data_dir": browser_user_data_dir,
            "use_own_browser": use_own_browser,
            "keep_browser_open": keep_browser_open,
            "headless": headless,
            "disable_security": disable_security,
            "save_recording_path": recording_path_input,
            "save_trace_path": trace_path_input,
            "save_agent_history_path": agent_history_path_input,
            "save_download_path": download_path_input,
            "cdp_url": cdp_url,
            "wss_url": wss_url,
            "window_h": window_h,
            "window_w": window_w,
        }
    )
    webui_manager.add_components("browser_settings", tab_components)

    def close_wrapper():
        """Wrapper for handle_clear."""
        import asyncio

        asyncio.create_task(close_browser(webui_manager))

    headless.change(fn=close_wrapper)
    keep_browser_open.change(fn=close_wrapper)
    disable_security.change(fn=close_wrapper)
    use_own_browser.change(fn=close_wrapper)

    # Function to save a single browser setting to .env
    def save_browser_setting(setting_name, setting_value):
        webui_manager.save_browser_settings_to_env(
            setting_name=setting_name, setting_value=setting_value
        )

    # Individual handler functions for each setting
    def save_browser_binary_path(value):
        """Save browser binary path setting"""
        save_browser_setting("browser_binary_path", value)

    def save_browser_user_data_dir(value):
        """Save browser user data directory setting"""
        save_browser_setting("browser_user_data_dir", value)

    def save_use_own_browser(value):
        """Save use own browser setting"""
        save_browser_setting("use_own_browser", value)

    def save_keep_browser_open(value):
        """Save keep browser open setting"""
        save_browser_setting("keep_browser_open", value)

    def save_cdp_url(value):
        """Save CDP URL setting"""
        save_browser_setting("cdp_url", value)

    def save_window_w(value):
        """Save window width setting"""
        save_browser_setting("window_w", value)

    def save_window_h(value):
        """Save window height setting"""
        save_browser_setting("window_h", value)

    def save_headless(value):
        """Save headless setting"""
        save_browser_setting("headless", value)

    def save_disable_security(value):
        """Save disable security setting"""
        save_browser_setting("disable_security", value)

    def save_recording_path(value):
        """Save recording path setting"""
        save_browser_setting("save_recording_path", value)

    def save_trace_path(value):
        """Save trace path setting"""
        save_browser_setting("save_trace_path", value)

    def save_agent_history_path(value):
        """Save agent history path setting"""
        save_browser_setting("save_agent_history_path", value)

    def save_download_path(value):
        """Save download path setting"""
        save_browser_setting("save_download_path", value)

    def save_wss_url(value):
        """Save WSS URL setting"""
        save_browser_setting("wss_url", value)

    # Connect change events to auto-save function
    browser_binary_path.change(
        fn=save_browser_binary_path,
        inputs=[browser_binary_path],
    )

    browser_user_data_dir.change(
        fn=save_browser_user_data_dir,
        inputs=[browser_user_data_dir],
    )

    use_own_browser.change(
        fn=save_use_own_browser,
        inputs=[use_own_browser],
    )

    keep_browser_open.change(
        fn=save_keep_browser_open,
        inputs=[keep_browser_open],
    )

    cdp_url.change(
        fn=save_cdp_url,
        inputs=[cdp_url],
    )

    window_w.change(
        fn=save_window_w,
        inputs=[window_w],
    )

    window_h.change(
        fn=save_window_h,
        inputs=[window_h],
    )

    headless.change(
        fn=save_headless,
        inputs=[headless],
    )

    disable_security.change(
        fn=save_disable_security,
        inputs=[disable_security],
    )

    recording_path_input.change(
        fn=save_recording_path,
        inputs=[recording_path_input],
    )

    trace_path_input.change(
        fn=save_trace_path,
        inputs=[trace_path_input],
    )

    agent_history_path_input.change(
        fn=save_agent_history_path,
        inputs=[agent_history_path_input],
    )

    download_path_input.change(
        fn=save_download_path,
        inputs=[download_path_input],
    )

    wss_url.change(
        fn=save_wss_url,
        inputs=[wss_url],
    )
