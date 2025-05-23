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

    input_components = set(webui_manager.get_components())
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
            save_recording_path = gr.Textbox(
                label="Recording Path",
                value=get_env_value(env_settings, "SAVE_RECORDING_PATH", ""),
                placeholder="e.g. ./tmp/record_videos",
                info="Path to save browser recordings",
                interactive=True,
            )

            save_trace_path = gr.Textbox(
                label="Trace Path",
                value=get_env_value(env_settings, "SAVE_TRACE_PATH", ""),
                placeholder="e.g. ./tmp/traces",
                info="Path to save Agent traces",
                interactive=True,
            )

        with gr.Row():
            save_agent_history_path = gr.Textbox(
                label="Agent History Save Path",
                value=get_env_value(
                    env_settings, "SAVE_AGENT_HISTORY_PATH", "./tmp/agent_history"
                ),
                info="Specify the directory where agent history should be saved.",
                interactive=True,
            )
            save_download_path = gr.Textbox(
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
            "save_recording_path": save_recording_path,
            "save_trace_path": save_trace_path,
            "save_agent_history_path": save_agent_history_path,
            "save_download_path": save_download_path,
            "cdp_url": cdp_url,
            "wss_url": wss_url,
            "window_h": window_h,
            "window_w": window_w,
        }
    )
    webui_manager.add_components("browser_settings", tab_components)

    async def close_wrapper():
        """Wrapper for handle_clear."""
        await close_browser(webui_manager)

    headless.change(close_wrapper)
    keep_browser_open.change(close_wrapper)
    disable_security.change(close_wrapper)
    use_own_browser.change(close_wrapper)

    # Function to save a single browser setting to .env
    def save_browser_setting(setting_name, setting_value):
        webui_manager.save_browser_settings_to_env(
            setting_name=setting_name, setting_value=setting_value
        )

    # Connect change events to auto-save function
    browser_binary_path.change(
        fn=lambda value: save_browser_setting("browser_binary_path", value),
        inputs=[browser_binary_path],
    )

    browser_user_data_dir.change(
        fn=lambda value: save_browser_setting("browser_user_data_dir", value),
        inputs=[browser_user_data_dir],
    )

    use_own_browser.change(
        fn=lambda value: save_browser_setting("use_own_browser", value),
        inputs=[use_own_browser],
    )

    keep_browser_open.change(
        fn=lambda value: save_browser_setting("keep_browser_open", value),
        inputs=[keep_browser_open],
    )

    cdp_url.change(
        fn=lambda value: save_browser_setting("cdp_url", value),
        inputs=[cdp_url],
    )

    window_w.change(
        fn=lambda value: save_browser_setting("window_w", value),
        inputs=[window_w],
    )

    window_h.change(
        fn=lambda value: save_browser_setting("window_h", value),
        inputs=[window_h],
    )

    headless.change(
        fn=lambda value: save_browser_setting("headless", value),
        inputs=[headless],
    )

    disable_security.change(
        fn=lambda value: save_browser_setting("disable_security", value),
        inputs=[disable_security],
    )

    save_recording_path.change(
        fn=lambda value: save_browser_setting("save_recording_path", value),
        inputs=[save_recording_path],
    )

    save_trace_path.change(
        fn=lambda value: save_browser_setting("save_trace_path", value),
        inputs=[save_trace_path],
    )

    save_agent_history_path.change(
        fn=lambda value: save_browser_setting("save_agent_history_path", value),
        inputs=[save_agent_history_path],
    )

    save_download_path.change(
        fn=lambda value: save_browser_setting("save_download_path", value),
        inputs=[save_download_path],
    )

    wss_url.change(
        fn=lambda value: save_browser_setting("wss_url", value),
        inputs=[wss_url],
    )
