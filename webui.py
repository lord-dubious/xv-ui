import argparse
import atexit
import logging
import signal
import sys

from dotenv import load_dotenv

from src.utils.env_utils import ensure_env_file_exists
from src.webui.interface import create_ui, theme_map

# Ensure .env file exists before loading it
ensure_env_file_exists()
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the demo instance
demo_instance = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    signal_name = signal.Signals(signum).name
    logger.info(f"\n🛑 Received {signal_name} signal. Shutting down gracefully...")

    # Close the Gradio demo if it exists
    if demo_instance:
        try:
            logger.info("📱 Closing Gradio interface...")
            demo_instance.close()
        except Exception as e:
            logger.error(f"Error closing Gradio interface: {e}")

    logger.info("✅ Shutdown complete. Goodbye!")
    sys.exit(0)


def cleanup_on_exit():
    """Cleanup function called on normal exit"""
    logger.info("🧹 Performing cleanup on exit...")
    if demo_instance:
        try:
            demo_instance.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    global demo_instance

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    # Register cleanup function for normal exit
    atexit.register(cleanup_on_exit)

    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument(
        "--ip", type=str, default="127.0.0.1", help="IP address to bind to"
    )
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument(
        "--theme",
        type=str,
        default="Ocean",
        choices=theme_map.keys(),
        help="Theme to use for the UI",
    )
    args = parser.parse_args()

    try:
        logger.info(f"🚀 Starting Gradio WebUI on {args.ip}:{args.port}")
        logger.info(f"🎨 Using theme: {args.theme}")
        logger.info("💡 Press Ctrl+C to shutdown gracefully")

        demo_instance = create_ui(theme_name=args.theme)
        demo_instance.queue().launch(
            server_name=args.ip, server_port=args.port, show_error=True, quiet=False
        )

    except KeyboardInterrupt:
        logger.info("\n🛑 Keyboard interrupt received. Shutting down...")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"❌ Error starting WebUI: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
