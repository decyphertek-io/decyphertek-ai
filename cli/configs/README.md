# Decyphertek AI Configuration

Configuration files for Adminotaur agent routing and AI providers.

## Files

### slash-commands.json
Defines slash command routing for Adminotaur agent.

**Structure:**
- `commands`: Dictionary of slash commands with routing info
- `default_routing`: Default behavior and context files

**Example Commands:**
- `/web <query>`: Search web and answer with context
- `/rag <query>`: Query ChromaDB vector database
- `/help`: Show available commands
- `/status`: Check system health
- `/config`: View configuration

### ai-config.json
AI provider configuration for routing requests.

**Structure:**
- `providers`: Dictionary of AI providers with `credential_service` for MCP Gateway lookup
- `default_provider`: Default AI to use
- `mcp_gateway`: Gateway connection settings with SSH key encryption

**Credential Management:**
All API keys and credentials are encrypted using SSH keys in `~/.decyphertek.ai/keys/` and stored in `~/.decyphertek.ai/creds/`. The MCP Gateway handles encryption/decryption using OpenSSL.

## Usage

Adminotaur loads these configs on startup and uses them to:
1. Route slash commands to appropriate MCP skills
2. Route regular queries to default AI provider
3. Retrieve encrypted credentials from MCP Gateway
4. Load context from JSON/MD files for self-awareness

## Credential Flow

```
Adminotaur → MCP Gateway (get_credential) → Decrypt with SSH key → Return API key
    ↓
Adminotaur → MCP Gateway (invoke_skill) → OpenRouter AI with API key → Response
```

## Modifying

Edit JSON files directly or use `/config` command in Adminotaur CLI.

Changes take effect on next Adminotaur restart.

**Never store credentials in config files - use MCP Gateway credential management.**
