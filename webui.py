import argparse
import json
import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from src.utils.env_utils import ensure_env_file_exists, get_mcp_servers
from src.webui.interface import theme_map, create_ui
from src.webui.components.mcp_server_utils import get_server_config_json
from dotenv import load_dotenv

# Ensure .env file exists before loading it
ensure_env_file_exists()
load_dotenv()

# Create FastAPI app for custom routes
app = FastAPI()

# Create a mock WebUI manager for API routes
class MockWebuiManager:
    def get_mcp_servers(self):
        return get_mcp_servers()

mock_webui_manager = MockWebuiManager()

# API route to get server configuration JSON
@app.get("/api/mcp/server/{server_name}/json")
def get_mcp_server_json_api(server_name: str):
    try:
        # Get the JSON string directly from the utility function
        json_string = get_server_config_json(server_name, mock_webui_manager)
        # Return it as a Response with the correct content type
        return Response(content=json_string, media_type="application/json")
    except Exception as e:
        # Return a proper HTTP error status code
        raise HTTPException(status_code=404, detail=str(e))

def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)

    # Mount Gradio app to FastAPI
    gr.mount_gradio_app(app, demo, path="/")

    # Launch the FastAPI app
    import uvicorn
    uvicorn.run(app, host=args.ip, port=args.port)


if __name__ == '__main__':
    main()
