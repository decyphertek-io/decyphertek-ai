# Decyphertek-AI Architecture Plan

## Overview
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

First run will:
1. Set up password protection
2. Generate SSH key for credential encryption
3. Download Adminotaur supervisor agent

### Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/uninstall.sh | bash
```

Removes `~/.decyphertek.ai/` and `~/.ssh/decyphertek.ai`

## Architecture

### Core Components

#### 1. Agent System (LangChain-based)
- **Adminotaur Agent** (Supervisor)
  - Core orchestration agent
  - Coordinates worker agents
  - Integrates MCP skills
  - Routes tasks to appropriate workers
  - Manages agent lifecycle

- **Worker Agents** (Modular)
  - Specialized task agents
  - Automation agents
  - Scheduled task agents
  - Domain-specific agents (network, security, monitoring, etc.)

#### 2. MCP Skills Layer (FastMCP)
- Modular skill servers
- Add/remove skills dynamically
- Tool exposure to agents
- System interaction capabilities

#### 3. RAG System (ChromaDB)
- **Document Indexing**
  - Configurable directory scanning
  - Support for: PDFs, EPUBs, DOCs, TXT, MD
  - Automatic embedding generation
  - Incremental updates

- **Context Retrieval**
  - Semantic search over indexed documents
  - Permission-based access control
  - Query-relevant context injection

#### 4. CLI Interface
- Command-line interaction
- Agent selection
- Task execution
- Configuration management

## Data Flow

```
User Input → CLI → Adminotaur Agent → [Worker Agents | MCP Skills | RAG Context] → Response
```

## Modularity Benefits
- Add/remove agents without core changes
- Plug-and-play MCP skills
- Configurable RAG directories
- Independent component updates

## Configuration
- Agent registry (enable/disable agents)
- MCP skill manifest
- RAG directory whitelist
- Permissions and access control

## Deployment
- **Build System**: uv + PyInstaller
  - uv manages Python 3.12 environment automatically
  - Locks dependencies for consistent builds across Linux systems
  - PyInstaller creates single portable executable
- **Distribution**:
  - Single executable binary
  - Embedded dependencies
  - Portable configuration files

---

## Implementation Architecture

### Simple Flow
```
Main App (cli-ai.py)
  ↓ Password unlock at startup
  ↓ Manages ~/.decyphertek.ai/creds (SSH key encrypted)
  ↓
Adminotaur (supervisor agent)
  ↓ Coordinates tasks and worker agents
  ↓
MCP Gateway (FastMCP)
  ↓ Requests decrypted creds from main app when needed
  ↓
MCP Skills
```

### Main App (cli-ai.py)
**Responsibilities**:
- Terminal interface with password protection at startup
- Manage `~/.decyphertek.ai/` working directory
- Encrypt/decrypt credentials using SSH keys
- Store encrypted creds in `~/.decyphertek.ai/creds/`
- Provide decrypted credentials to MCP Gateway on request (memory only)
- Initialize and communicate with Adminotaur

**Security**:
- Password-protected app launch
- SSH key-based credential encryption
- Credentials encrypted at rest in `~/.decyphertek.ai/creds/`
- Credentials only decrypted in memory when MCP Gateway needs them
- No plaintext credentials written to disk

### Adminotaur (adminotaur.py)
**Responsibilities**:
- LangChain supervisor agent
- Coordinate worker agents
- Route tasks to appropriate agents/skills
- Monitor execution and handle errors
- Act as system administrator/orchestrator

### MCP Gateway (mcp_gateway.py)
**Responsibilities**:
- FastMCP client implementation
- Connect to MCP servers
- Load and expose MCP skills
- Request credentials from main app when connecting to servers
- Provide tools to Adminotaur and worker agents

### File Structure
```
cli/
├── cli-ai.py              # Main app with password protection & credential management
├── adminotaur.py          # LangChain supervisor agent
├── mcp_gateway.py         # FastMCP gateway
├── build.sh               # Build script
└── pyproject.toml         # Dependencies

~/.decyphertek.ai/         # Working directory (created at runtime)
├── creds/                 # Encrypted credentials (SSH key encrypted)
│   ├── github_token
│   ├── openai_key
│   └── ...
└── config/                # Configuration files
    └── mcp_servers.json   # MCP server configurations
```

### Security Model
- **App Launch**: Password required to unlock main app
- **Creds at Rest**: All credentials in `~/.decyphertek.ai/creds/` encrypted with SSH public key
- **Creds in Use**: Main app decrypts with SSH private key only when MCP Gateway requests
- **Memory Only**: Decrypted credentials passed to MCP Gateway in memory, never written to disk
- **SSH Key**: Can be password-protected for additional security layer
