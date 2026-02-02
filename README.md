# Decyphertek-AI 

## Overview
CURRENTLY IN DEV
A modular Sysadmin AI CLI application built with a supervisor-worker agent architecture.

## Tech Stack
- **LangChain**: Agent orchestration and workflow management
- **FastMCP**: MCP server implementation for skills/tools
- **ChromaDB**: Vector database for RAG functionality
- **uv**: Python version and dependency management
- **PyInstaller**: Executable packaging

## Quick Start

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/install.sh | bash
```

Installs to `~/.decyphertek.ai/bin/` and adds to PATH. No sudo required.

### Run

```bash
decyphertek.ai
```

On first run, the app will:
1. Ask you to set a master password
2. Generate SSH keys for credential encryption
3. Detect if OpenRouter AI is enabled
4. **Automatically prompt you for your API key if missing**


### Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/uninstall.sh | bash
```

Removes `~/.decyphertek.ai/` 

## Architecture

```
User
  ↓
CLI (cli-ai.py)
  ↓ Password protection
  ↓ Credential encryption/decryption
  ↓ Downloads agents/skills from GitHub
  ↓
Adminotaur Agent (LangChain supervisor)
  ↓ Routes queries and slash commands
  ↓ Coordinates worker agents
  ↓
MCP Gateway
  ↓ Manages MCP skills
  ↓ Retrieves encrypted credentials
  ↓
MCP Skills (web-search, rag-chat, etc.)
  ↓
AI Provider (OpenRouter, etc.)
```

**Flow:**
- CLI handles auth, credential storage, and downloads
- Adminotaur routes user input to workers or MCP skills
- MCP Gateway proxies skill requests and manages credentials
- Skills call external APIs with decrypted credentials

