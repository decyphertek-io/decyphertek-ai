# MCP Server Instructions for AI

## 📋 Overview

This document explains how MCP (Model Context Protocol) servers work in DecypherTek AI, so you (the AI assistant) can understand and use them effectively.

## 🗂️ Registry Structure

All MCP servers are registered in `mcp-registry.json`. This JSON file tells you:
- Which servers are **available**
- Which servers are **enabled**
- What **tools** each server provides
- How to **invoke** them

## 📖 How to Read the Registry

### Server Status
```json
{
  "enabled": true,    // Can you use this server?
  "auto_start": true, // Does it start automatically?
  "status": "running" // Current state: "running", "stopped", or "error"
}
```

### Available Tools
```json
{
  "tools": [
    {
      "name": "search",
      "description": "Search the web",
      "required_params": ["query"],
      "optional_params": ["num_results"]
    }
  ]
}
```

## 🚀 How to Use MCP Servers

### Step 1: Check if Enabled
```python
# Before using a server, check mcp-registry.json
servers = load_json("mcp-registry.json")
if servers["servers"]["web-search"]["enabled"]:
    # You can use this server!
```

### Step 2: Invoke a Tool
```python
# Example: Web search
result = await mcp_manager.execute_tool(
    server_id="web-search",
    tool_name="search",
    params={
        "query": "Python async programming",
        "num_results": 5
    }
)
```

### Step 3: Handle Response
```python
# The server returns structured data
for item in result:
    print(f"Title: {item['title']}")
    print(f"URL: {item['url']}")
    print(f"Snippet: {item['snippet']}")
```

## 🔧 Available Servers

### 1. Web Search (`web-search`)
**Purpose**: Search the web and scrape content

**Tools**:
- `search` - Search DuckDuckGo
  - Params: `query` (required), `num_results` (optional, default 10)
  - Returns: List of {title, url, snippet}

- `scrape_url` - Extract text from URL
  - Params: `url` (required)
  - Returns: {title, content}

**When to Use**:
- User asks to search for information
- User provides a URL to read
- User wants current information not in your knowledge base

**Example**:
```
User: "Search for Python async tutorials"

AI Action:
1. Check if web-search is enabled
2. Call search tool with query="Python async tutorials"
3. Present results to user with URLs
```

### 2. Nextcloud (`nextcloud`)
**Purpose**: Access Nextcloud files

**Status**: Coming soon

### 3. Google Drive (`google-drive`)
**Purpose**: Access Google Drive files

**Status**: Coming soon

### 4. WhatsApp (`whatsapp`)
**Purpose**: Send/receive WhatsApp messages

**Status**: Coming soon

### 5. Google Voice (`google-voice`)
**Purpose**: Send/receive SMS via Google Voice

**Status**: Coming soon

## ⚙️ Server Lifecycle

### Enabling a Server
1. User clicks "Enable" in MCP tab
2. App updates `mcp-registry.json`: `"enabled": true`
3. If `auto_start: true`, app starts the Python script
4. Status changes to `"running"`
5. AI can now use the server's tools

### Disabling a Server
1. User clicks "Disable" in MCP tab
2. App stops the Python script (if running)
3. App updates `mcp-registry.json`: `"enabled": false`
4. Status changes to `"stopped"`
5. AI can no longer use the server's tools

### Auto-Start
- If `auto_start: true`, server starts when app launches
- If `auto_start: false`, server starts only when explicitly needed

## 🤖 AI Guidelines

### When to Use MCP Servers

✅ **DO use MCP servers for**:
- Real-time web searches (user asks for current info)
- Fetching content from URLs (user provides link)
- Accessing user's cloud files (when implemented)
- Sending messages (when implemented)

❌ **DON'T use MCP servers for**:
- Questions you can answer from your knowledge
- Information already in the conversation context
- Every single query (use judiciously)

### Error Handling

```python
try:
    result = await mcp_manager.execute_tool(...)
except ServerNotEnabledError:
    tell_user("The web-search server is not enabled. Please enable it in Settings > MCP Servers.")
except ServerNotRunningError:
    tell_user("The server is enabled but not running. Trying to start it...")
    # App will attempt to restart
except ToolNotFoundError:
    tell_user("That tool doesn't exist on this server.")
```

### Best Practices

1. **Check Before Using**
   - Always verify `enabled: true` before invoking
   - Handle cases where server is disabled

2. **Inform the User**
   - Tell user when you're searching or fetching data
   - "Searching the web for..."
   - "Fetching content from URL..."

3. **Cache Results**
   - Store search results in conversation context
   - Avoid repeated searches for same query

4. **Cite Sources**
   - Always include URLs when presenting web search results
   - Give credit to scraped content

## 📊 Registry Format Reference

```json
{
  "servers": {
    "server-id": {
      "id": "unique-server-id",
      "name": "Human-readable name",
      "enabled": boolean,        // Can AI use this?
      "auto_start": boolean,     // Start on app launch?
      "status": "running|stopped|error",
      "description": "What this server does",
      "python_script": "path/to/script.py",
      "host": "localhost",
      "port": null,
      "transport": "stdio",
      "capabilities": ["list", "of", "capabilities"],
      "tools": [
        {
          "name": "tool_name",
          "description": "What it does",
          "required_params": ["param1"],
          "optional_params": ["param2"]
        }
      ],
      "requirements": ["python-package>=version"],
      "platforms": ["linux", "android", "macos", "windows"],
      "config_required": {
        "key": "description"
      }
    }
  }
}
```

## 🔄 Dynamic Updates

The registry is **live** - it updates when:
- User enables/disables a server
- Server status changes
- New servers are installed

**Always read the latest state** before making decisions.

## 🎯 Example Workflows

### Workflow 1: User Asks to Search
```
User: "Find me tutorials on Rust programming"

AI Process:
1. Check mcp-registry.json
2. Is web-search enabled? → Yes
3. Is status running? → Yes
4. Invoke: search(query="Rust programming tutorials", num_results=5)
5. Get results
6. Format and present to user with URLs
7. Ask if they want to read any specific page (scrape_url)
```

### Workflow 2: User Provides URL
```
User: "Summarize this article: https://example.com/article"

AI Process:
1. Check mcp-registry.json
2. Is web-search enabled? → Yes
3. Invoke: scrape_url(url="https://example.com/article")
4. Get content
5. Read and summarize
6. Present summary to user
```

### Workflow 3: Server Not Enabled
```
User: "Search for Python news"

AI Process:
1. Check mcp-registry.json
2. Is web-search enabled? → No
3. Tell user: "The web search server is not enabled. Would you like me to guide you through enabling it?"
4. If yes, explain: "Go to Settings → MCP Servers → Enable 'Web Search'"
```

## 🆘 Troubleshooting

### Server Won't Start
- Check if dependencies are installed
- Check if port is already in use
- Check logs for errors

### Server Enabled But Not Running
- App will attempt to restart
- If fails, status becomes "error"
- User needs to check server logs

### Tool Returns Error
- Check if required params are provided
- Check if values are in correct format
- Server may return error message - show to user

---

**Remember**: MCP servers extend your capabilities! Use them wisely to help users with real-time data and external integrations. 🚀

