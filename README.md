# DecypherTek AI

A modern AI assistant with chat, document management, and app integration capabilities. 
**Note**: This is in dev and the mobile feature doesnt work as of now. Running the launch.sh from linux does work. Many features are in dev as well and do not function correctly. 

## Features

- **AI Chat** - Chat with multiple AI providers (OpenRouter, DuckDuckGo AI, Ollama)
- **Document Management** - Upload and search through your documents with RAG
- **App Store** - Launch and manage Flet applications
- **MCP Servers** - Modular Python servers for web search, file management, and more

## Quick Start
```
curl -fsSL https://github.com/decyphertek-io/decyphertek-ai/install.sh | sudo bash
* Create creds > add settings > AI Admin Chat . 

# After installation, manage the service with:
sudo systemctl start decyphertek.ai
sudo systemctl stop decyphertek.ai
sudo systemctl restart decyphertek.ai
sudo systemctl status decyphertek.ai
sudo systemctl enable decyphertek.ai
sudo systemctl disable decyphertek.ai

# View logs:
sudo journalctl -u decyphertek.ai
sudo journalctl -u decyphertek.ai 

```

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

## Getting Help

- **App won't start?** Make sure you have Python 3.10+ and all dependencies installed
- **Login issues?** Try deleting `~/.decyphertek-ai/` and setting up again
- **API errors?** Check your OpenRouter API key in Settings
- **Still having trouble?** The app is in active development - some features may not work perfectly yet

---

**Note**: This app stores your credentials locally and securely. No data is sent to external servers except for AI API calls.