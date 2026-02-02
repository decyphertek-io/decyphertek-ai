# Decyphertek AI CLI

## Overview
Core CLI interface for the Decyphertek AI sysadmin assistant. This modular skeleton allows agents and MCP skills to extend functionality.

## Prerequisites
- uv (auto-installed by build.sh if missing)

## Structure
- `cli-ai.py` - Core CLI application
- `build.sh` - PyInstaller build script
- `pyproject.toml` - uv dependency management

## Usage

### Run from Source
```bash
python3 cli-ai.py
```

### Interactive Mode
```bash
python3 cli-ai.py
# Launches interactive prompt
```

### Command Mode
```bash
python3 cli-ai.py "your command here"
```

## Building Executable

```bash
chmod +x build.sh
./build.sh
```

The executable will be created in the `dist/` directory.

**Why uv?**
- Combines Python version management + dependency locking in one tool
- Automatically manages Python 3.12 (no pyenv needed)
- Faster than Poetry with automatic virtual environments
- Ensures consistent builds across different Linux systems

## Architecture Integration
This CLI serves as the entry point for:
- Adminotaur agent interactions
- Worker agent coordination
- MCP skill execution
- RAG context queries

## Extensibility
The skeleton is designed to be extended by:
- Agent modules
- MCP skill integrations
- RAG system connections
- Custom command handlers
