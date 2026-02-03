# Decyphertek-AI 

* CURRENTLY IN DEV

## Tech Stack
- **LangGraph**: Agent orchestration and workflow management
- **FastMCP**: MCP server implementation for skills/tools
- **ChromaDB**: Vector database for RAG functionality
- **uv**: Python version and dependency management
- **PyInstaller**: Executable packaging

## Quick Start

Pyinstaller is a self contained python executable that is cross platform for x86 architecture. Linux , Mac, & Windows. Currenlty on being tested on Linux. 

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

### Experimental

```bash
# Install on Android Termux. Recompiles to work on ARM Archtiecture. Very Experimental. ( Untested on Mobian.)
curl -fsSL https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/experimental.sh | bash
```

## Architecture

```
User
  ↓
CLI (cli-ai.py)
  ↓ Password protection
  ↓ Credential encryption/decryption
  ↓
  ├─> agent-store (GitHub) → Downloads Adminotaur + workers
  ├─> mcp-store (GitHub) → Downloads MCP skills
  └─> app-store (GitHub) → Downloads apps (ChromaDB, etc.)
  ↓
Adminotaur Agent (LangGraph supervisor)
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
- CLI downloads agents from agent-store, skills from mcp-store, apps from app-store
- Adminotaur routes user input to workers or MCP skills
- MCP Gateway manages skills and retrieves encrypted credentials
- Skills call AI providers with decrypted credentials

## References

### Repositories
- **[agent-store](https://github.com/decyphertek-io/agent-store)** - LangChain agents (Adminotaur + workers)
- **[mcp-store](https://github.com/decyphertek-io/mcp-store)** - MCP skills (web-search, rag-chat, etc.)
- **[app-store](https://github.com/decyphertek-io/app-store)** - Standalone apps (ChromaDB, etc.)

### Tech Stack
- **[LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)** - Agent orchestration framework
- **[FastMCP](https://github.com/jlowin/fastmcp)** - MCP server implementation
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for RAG
- **[uv](https://docs.astral.sh/uv/)** - Python package and project manager
- **[PyInstaller](https://pyinstaller.org/)** - Python executable packager

