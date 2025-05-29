<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>

[![GitHub stars](https://img.shields.io/github/stars/browser-use/web-ui?style=social)](https://github.com/browser-use/web-ui/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![WarmShao](https://img.shields.io/twitter/follow/warmshao?style=social)](https://x.com/warmshao)

This project builds upon the foundation of the [browser-use](https://github.com/browser-use/browser-use), which is designed to make websites accessible for AI agents.

We would like to officially thank [WarmShao](https://github.com/warmshao) for his contribution to this project.

**WebUI:** is built on Gradio and supports most of `browser-use` functionalities. This UI is designed to be user-friendly and enables easy interaction with the browser agent.

**Expanded LLM Support:** We've integrated support for various Large Language Models (LLMs), including: Google, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama etc. And we plan to add support for even more models in the future.

**Custom Browser Support:** You can use your own browser with our tool, eliminating the need to re-login to sites or deal with other authentication challenges. This feature also supports high-definition screen recording.

**Persistent Browser Sessions:** You can choose to keep the browser window open between AI tasks, allowing you to see the complete history and state of AI interactions.

<video src="https://github.com/user-attachments/assets/56bc7080-f2e3-4367-af22-6bf2245ff6cb" controls="controls">Your browser does not support playing this video!</video>

## Features

- 🌐 Browser automation with AI assistance
- 🤖 Multiple specialized agents:
  - 🎭 XAgent: Enhanced stealth capabilities with anti-detection measures
  - 🐦 Twitter Agent: Browser-based Twitter automation (tweeting, following, engagement)
  - 🔍 Deep Research: Advanced web research capabilities
- 🧠 Multiple LLM providers support (OpenAI, Anthropic, etc.)
- 🎮 Interactive browser control
- 📊 Task execution tracking
- 🔒 Secure cookie and session management
- 📱 Mobile-responsive UI

## Installation Guide

### Prerequisites

- Python 3.10 or higher
- Docker (optional, for containerized deployment)

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/lord-dubious/xv-ui.git
cd xv-ui
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

5. (Optional) Set up Twitter Agent integration:
```bash
python src/agent/xagent/setup_twagent.py
```

6. Run the application:
```bash
python webui.py
```

7. Open your browser and navigate to http://localhost:7860

### Option 2: Docker Installation

#### Prerequisites
- Docker and Docker Compose installed
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (For Windows/macOS)
  - [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) (For Linux)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 3: Docker Build and Run
```bash
docker compose up --build
```
For ARM64 systems (e.g., Apple Silicon Macs), please run follow command:
```bash
TARGETPLATFORM=linux/arm64 docker compose up --build
```

#### Step 4: Enjoy the web-ui and vnc
- Web-UI: Open `http://localhost:7788` in your browser
- VNC Viewer (for watching browser interactions): Open `http://localhost:6080/vnc.html`
  - Default VNC password: "youvncpassword"
  - Can be changed by setting `VNC_PASSWORD` in your `.env` file

## Changelog
- [x] **2025/01/26:** Thanks to @vvincent1234. Now browser-use-webui can combine with DeepSeek-r1 to engage in deep thinking!
- [x] **2025/01/10:** Thanks to @casistack. Now we have Docker Setup option and also Support keep browser open between tasks.[Video tutorial demo](https://github.com/browser-use/web-ui/issues/1#issuecomment-2582511750).
- [x] **2025/01/06:** Thanks to @richard-devbot. A New and Well-Designed WebUI is released. [Video tutorial demo](https://github.com/warmshao/browser-use-webui/issues/1#issuecomment-2573393113).

## Agents

### Browser Use Agent
The core agent that provides browser automation capabilities. It can navigate websites, fill forms, click buttons, and perform various browser-based tasks.

### XAgent
XAgent enhances the Browser Use Agent with advanced stealth capabilities:
- Patchright browser with patched Runtime.enable and Console.enable
- Enhanced anti-detection measures
- Closed shadow root interaction support
- Advanced fingerprint resistance
- Bot detection bypass for Cloudflare, Kasada, Akamai, Datadome, and more

### Twitter Agent
Twitter Agent integrates the [twagent](https://github.com/lord-dubious/twagent) library to provide browser-based Twitter automation:
- Tweet creation and replies
- Following users and managing lists
- Persona-based content generation
- Cookie-based authentication
- Stealth capabilities to avoid detection

To use the Twitter Agent:
1. Run the setup script: `python src/agent/xagent/setup_twagent.py`
2. Obtain Twitter cookies (see [twagent documentation](https://github.com/lord-dubious/twagent))
3. Configure personas in the `personas` directory
4. Use the Twitter Agent tab in the UI

### Deep Research Agent
<!-- ... rest of the existing content ... -->
