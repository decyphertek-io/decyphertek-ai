# DecypherTek AI

Linux based decyphertek.ai chat. Modular stores: mcp ; agent ; app , to customize AI . 

## Features

- **AI Chat** - Generalized / Specialized AI chat.
- **Rag Chat** - Upload docs and inquire about them. 
- **App Store** - Python apps.
 **Agent Store** - Manage the AI personality.
- **MCP Servers** - Modular AI Skills.

## Quick Start
```
curl -fsSL https://github.com/decyphertek-io/decyphertek-ai/install.sh | sudo bash

* Setup > Create creds > add settings > AI Admin Chat . 

# Decyphertek AI working directory:
cd ~/.decyphertek-ai/

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

# Debugging:
/opt/decyphertak.ai 
* This will run the app and show terminal output for debugging issues.
* Run this from chat to help debug.
sudo systemctl status mcp
sudo systemctl status agent
sudo systemctl status app
healthcheck-agent
```
