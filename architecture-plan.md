# Decyphertek-AI Architecture Plan

## Overview
A modular Sysadmin AI CLI application built with a supervisor-worker agent architecture.

## Tech Stack
- **LangChain**: Agent orchestration and workflow management
- **FastMCP**: MCP server implementation for skills/tools
- **ChromaDB**: Vector database for RAG functionality
- **uv**: Python version and dependency management
- **PyInstaller**: Executable packaging

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

## Implementation Architecture (3-Tier Design)

### Layer 1: CLI Layer
**File**: `cli-ai.py`, `secret_manager.py`

**Responsibilities**:
- User interface and interaction
- Secret management with SSH key-based encryption
- Configuration file management
- Decrypt credentials and pass to MCP Gateway
- Display responses to user

**Components**:
- `DecyphertekCLI` - Main CLI interface class
- `SecretManager` - SSH key encryption/decryption for credentials
- `config/secrets.json` - Encrypted API keys and credentials
- `config/mcp_servers.json` - MCP server configurations

### Layer 2: MCP Gateway (FastMCP)
**File**: `mcp_gateway.py`

**Responsibilities**:
- Connect to configured MCP servers
- Load and expose MCP skills/tools
- Handle MCP protocol communication
- Provide tool interface for Adminotaur and worker agents
- Manage MCP server lifecycle

**Components**:
- `MCPGateway` class using FastMCP client
- MCP server connection pool
- Tool registry and exposure
- Skill discovery and loading

### Layer 3: Adminotaur (LangChain Supervisor Agent)
**File**: `adminotaur.py`

**Responsibilities**:
- Coordinate worker agents
- Route tasks to appropriate agents
- Monitor agent execution and health
- Handle errors and implement retry logic
- Ensure tasks complete successfully
- Act as system administrator/orchestrator

**Components**:
- `Adminotaur` class - LangChain supervisor agent
- Task routing logic
- Agent registry and lifecycle management
- Error handling and recovery
- Status monitoring and reporting

### Layer 4: Worker Agents (Future)
**Files**: `agents/*.py`

**Responsibilities**:
- Execute specialized tasks
- Use MCP tools from gateway
- Report status to Adminotaur
- Domain-specific operations (network, security, monitoring, etc.)

### Data Flow
```
User Input 
  ↓
CLI Layer (decrypt secrets, manage config)
  ↓
MCP Gateway (connect to MCP servers, load skills)
  ↓
Adminotaur (analyze task, route to workers)
  ↓
Worker Agents (execute with MCP tools)
  ↓
Response back through layers to CLI
```

### File Structure
```
cli/
├── cli-ai.py              # Main CLI + user interface
├── secret_manager.py      # SSH key encryption/decryption
├── mcp_gateway.py         # FastMCP gateway implementation
├── adminotaur.py          # LangChain supervisor agent
├── agents/                # Future worker agents
│   └── (specialized agents)
├── config/
│   ├── mcp_servers.json   # MCP server configurations
│   └── secrets.json       # Encrypted credentials
├── build.sh               # Build script
└── pyproject.toml         # Dependencies
```

### Security Model
- **Secrets at Rest**: Encrypted with SSH public key
- **Secrets in Use**: Decrypted by CLI using SSH private key
- **Secret Passing**: Decrypted secrets passed to MCP Gateway in memory only
- **No Disk Writes**: Decrypted secrets never written to disk
- **SSH Key Protection**: Can use password-protected SSH keys for additional security
