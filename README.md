# DecypherTek AI

A modern AI assistant with chat, document management, and app integration capabilities. Note: This is in dev and the mobile feature doesnt work as of now. Runiing the launch.sh from linux does work. Many features are in dev as well and do not function correctly. 

## Features

- **AI Chat** - Chat with multiple AI providers (OpenRouter, DuckDuckGo AI, Ollama)
- **Document Management** - Upload and search through your documents with RAG
- **App Store** - Launch and manage Flet applications
- **MCP Servers** - Modular Python servers for web search, file management, and more
- **Mobile Ready** - Works on desktop and mobile platforms

## Quick Start

1. **Install Dependencies**
   ```bash
   # Using Poetry (recommended)
   curl -sSL https://install.python-poetry.org | python3 -
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

2. **Launch the App**
   ```bash
   bash launch.sh
   ```

3. **First Time Setup**
   - Create your account credentials
   - Add your OpenRouter API key in Settings
   - Start chatting!

## Basic Usage

- **Chat**: Type messages to interact with the AI
- **Upload Documents**: Use the paper clip icon to add documents to RAG
- **Launch Apps**: Ask the AI to "run langtek" or other available apps
- **Web Search**: Ask for current information and the AI will search the web

## Configuration

- **API Keys**: Add your OpenRouter API key in Settings → API Keys
- **AI Providers**: Switch between OpenRouter, DuckDuckGo AI, and Ollama
- **Apps**: Enable/disable applications in the Apps tab

## Requirements

- Python 3.10+
- Poetry (recommended) or pip
- OpenRouter API key (for full AI features)

## Support

For issues or questions, please check the logs in the `logs/` directory or create an issue in the repository.

---

**Note**: This app stores your credentials locally and securely. No data is sent to external servers except for AI API calls.