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
