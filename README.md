# Decyphertek-AI 

* CURRENTLY IN DEV ; This is a side project to understand AI agents and how they work. Many things are not working yet. 

## Tech Stack
- **LangGraph**: Agent orchestration and workflow management
- **LangChain**: Agent framework and tool integrations
- **Agent Skills SDK**: Skill/tool management for LangChain agents
- **FastMCP**: MCP server implementation for skills/tools
- **ChromaDB**: Vector database for RAG functionality
- **uv**: Python version and dependency management
- **PyInstaller**: Executable packaging

## Quick Start

Pyinstaller is a self contained python executable that is cross platform for x86 architecture. Linux , Mac, & Windows. Currenlty being tested on Linux. 

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

> In progress restructure. See [`wiki/decyphertek-ai-architecture.md`](wiki/decyphertek-ai-architecture.md) for the full plan.

The three external stores (agent-store, mcp-store, app-store) are being removed. Everything is bundled into a single install that ships both a CLI and an optional Flet GUI. ChromaDB is replaced by sqlite-vec + LlamaIndex for RAG.

```
User
  ↓
Single install (decyphertek.ai) — ships CLI + Flet GUI together
  ↓ Password protection
  ↓ Credential encryption/decryption
  ↓
  ├─> CLI entrypoint (terminal)
  └─> Flet GUI entrypoint (desktop)
  ↓
Core Agent (LangGraph supervisor)
  ↓ Routes queries and slash commands
  ↓
Built-in tools (bundled, no external stores):
  ├─> Web browsing
  ├─> MCP compatibility layer → Docker / Podman MCP servers
  └─> RAG chat → LlamaIndex → sqlite-vec vector store
  ↓
AI Provider (OpenRouter, etc.)
```

**Flow:**
- Single install ships CLI and GUI; user picks CLI, GUI, or both at run time.
- Core agent routes input to bundled tools (web browsing, MCP layer, RAG chat).
- MCP compatibility layer interfaces with Docker / Podman MCP servers using encrypted credentials.
- RAG chat uses LlamaIndex for ingestion and sqlite-vec as the local vector store.

## References

### Tech Stack
- **[LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)** - Agent orchestration framework
- **[LangChain](https://python.langchain.com/)** - Agent framework and tool integrations
- **[FastMCP](https://github.com/jlowin/fastmcp)** - MCP compatibility layer
- **[sqlite-vec](https://github.com/asg017/sqlite-vec)** - Vector database for RAG (replaces ChromaDB)
- **[LlamaIndex](https://www.llamaindex.ai/)** - RAG ingestion / indexing
- **[Flet](https://flet.dev/)** - Optional cross-platform GUI layer
- **[uv](https://docs.astral.sh/uv/)** - Python package and project manager
- **[PyInstaller](https://pyinstaller.org/)** - Python executable packager

