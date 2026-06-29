# Decyphertek-AI Architecture Plans

> Authoritative planning doc for the restructure. Read this first when resuming work on decyphertek-ai.

## Goal

Simplify decyphertek-ai by removing the external store dependencies (App store, MCP store) and collapsing everything into a single self-contained app. Keep it focused on: web browsing, MCP compatibility layer for Docker/Podman, RAG chat via sqlite-vec + LlamaIndex + LangChain, and an optional Flet UI layer. The single installer ships both the CLI and the GUI; the user picks whichever they want (CLI only, GUI only, or both).

## What is being removed

- **agent-store** (GitHub) — no longer pulled in at runtime
- **mcp-store** (GitHub) — no longer pulled in at runtime
- **app-store** (GitHub) — no longer pulled in at runtime
- **ChromaDB** — replaced by sqlite-vec ( Undecided )

All three external stores are dead in the new design. Agents, skills, and apps are bundled into the single repo / single install rather than downloaded on demand.

## What stays

- **decyphertek-ai** core (the app itself)
- LangGraph agent orchestration
- LangChain framework
- FastMCP / MCP compatibility layer
- Password protection + credential encryption/decryption
- OpenRouter (and similar) AI provider integration
- **LLM wiki** — the `wiki/` memory system (`soul.md`, `directory.md`, `memory/`, `projects/`, `research/`). This is the agent's memory layer (Memento principle) and stays in the new design. See `wiki/soul.md` for the contract. Only the store references in `directory.md` (agent-store / mcp-store / app-store / chromadb.app) get cleaned up, not the wiki system itself.

## New Tech Stack

- **LangGraph** — agent orchestration and workflow management
- **LangChain** — agent framework and tool integrations
- **FastMCP** — MCP compatibility layer
- **sqlite-vec** — vector database for RAG (replaces ChromaDB). Chosen over ChromaDB for this design: pure-Python install via wheel, single-file DB that travels with the install, no separate server/native service to run, and bundles cleanly under PyInstaller. ChromaDB is richer (server mode, embeddings API) but heavier and better suited as a standalone service — which contradicts the single-bundle simplification goal.
- **LlamaIndex** — RAG ingestion / indexing layer over sqlite-vec
- **Flet** — optional cross-platform GUI layer (UI + CLI share one codebase/install)
- **uv** — Python version and dependency management
- **PyInstaller** — executable packaging (ships both CLI and GUI in one binary)

## New Architecture

```
User
  ↓
Single install (decyphertek.ai) — ships CLI + Flet GUI together
  ↓
  ├─> CLI entrypoint (terminal use)
  └─> Flet GUI entrypoint (desktop use)
  ↓ Password protection
  ↓ Credential encryption/decryption
  ↓
Adminotaur Agent (LangGraph supervisor — baked-in, not downloaded)
  ↓ Routes queries and slash commands
  ↓ Spawns sub-agents for automated tasks
  ↓ Generates custom MCP servers (FastMCP) on demand
  ↓
Sub-agents (created at runtime by Adminotaur)
  ↓ Run automated tasks, report back to Adminotaur
  ↓
Built-in tools / skills (bundled, no external stores):
  ├─> Web browsing
  ├─> MCP compatibility layer
  │     ├─> Docker MCP server
  │     └─> Podman MCP server
  ├─> Custom MCP servers (generated via FastMCP, can interface with Docker/Podman MCP servers)
  └─> RAG chat
        └─> LlamaIndex ingestion
        └─> sqlite-vec vector store
  ↓
AI Provider (OpenRouter, etc.)
```

## Component Details

### Web Browsing
- Kept as a bundled skill/tool. No external mcp-store download.
- Used for live web search / page fetch during agent runs.

### Adminotaur Agent (baked-in supervisor + sub-agents)
- Adminotaur is the core LangGraph supervisor agent, **baked into the install** (no agent-store download).
- **Sub-agent creation**: Adminotaur can launch sub-agents to perform automated tasks. Sub-agents are spawned at runtime, run their task, and report results back to Adminotaur. This replaces the old agent-store / agent-builder model — agent creation now lives inside the app.
- **Custom MCP server generation**: Adminotaur can create custom MCP servers on demand using FastMCP. Generated servers are usable as tools immediately and can themselves interface with the Docker and Podman MCP servers.
- Sub-agents and generated MCP servers share the same credential store, configs, and vector DB as the core agent.

### MCP Compatibility Layer (Docker / Podman)
- FastMCP-based layer that can interface with Docker MCP servers and Podman MCP servers.
- Lets the agent manage containers/images/compose as tools.
- Credentials still flow through the existing encrypted credential store.
- This same FastMCP layer is what Adminotaur uses when generating custom MCP servers — generated servers speak the same protocol and can connect to Docker/Podman MCP servers.

### RAG Chat — sqlite-vec + LlamaIndex + LangChain
- **sqlite-vec** replaces ChromaDB as the vector store. Pure-Python wheel, single local file, no separate DB service to run.
- **LlamaIndex** handles document ingestion, chunking, and indexing into sqlite-vec.
- **LangChain** wires the retriever into the agent as a RAG tool.
- Result: a single-file vector DB that travels with the install and needs no extra app-store app.
- This RAG layer is distinct from the **LLM wiki** (`wiki/`): the wiki is the agent's hand-written durable memory (Memento principle), RAG is the indexed document retrieval. Both stay.

### Flet UI Layer
- The Flet UI work saved at `/home/adminotaur/Documents/git/flet/decyphertek-ai` is the basis for the GUI.
- One install ships both CLI and GUI. Use cases:
  - Terminal only → run the CLI, ignore the GUI.
  - GUI only → run the Flet UI, ignore the CLI.
  - Both → run either as needed; they share the same core, config, credentials, and vector store.

## Install Behavior (new)

- Single installer (`install.sh`) installs both the CLI binary and the Flet GUI.
- Installs to `~/.decyphertek.ai/` as before.
- No runtime downloads from agent-store / mcp-store / app-store — everything is bundled.
- User chooses CLI, GUI, or both at run time, not install time.

## Migration Notes

- Drop the `agent-store`, `mcp-store`, `app-store` runtime fetch paths from `cli/cli-ai.py`.
- Bake Adminotaur into the core as the LangGraph supervisor; add sub-agent spawning (runtime creation for automated tasks) and FastMCP custom MCP-server generation to the supervisor's capabilities. Both must share the credential store, configs, and sqlite-vec vector DB.
- Replace ChromaDB wiring with sqlite-vec + LlamaIndex.
- Add a Flet entrypoint that reuses the same core agent / credential / vector store as the CLI.
- Update `install.sh` so the single binary / install includes the GUI.
- Update `README.md` Architecture section to match this doc (remove the three stores and ChromaDB).
- Update `wiki/directory.md`: remove the agent-store / mcp-store / app-store / chromadb.app rows and the `Related source repos` block; keep the `wiki/` memory system rows (soul, directory, memory, projects, research). The LLM wiki system itself is NOT removed.

## References

- sqlite-vec: https://github.com/asg017/sqlite-vec
- LlamaIndex: https://www.llamaindex.ai/
- LangChain: https://python.langchain.com/
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- FastMCP: https://github.com/jlowin/fastmcp
- Flet: https://flet.dev/
- Saved Flet UI source: `/home/adminotaur/Documents/git/flet/decyphertek-ai`
- uv: https://docs.astral.sh/uv/
- PyInstaller: https://pyinstaller.org/
