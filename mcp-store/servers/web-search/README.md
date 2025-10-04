# Web Search MCP Server

**Standardized MCP server** following the [official Python SDK](https://github.com/modelcontextprotocol/python-sdk) patterns.

## ✨ What Changed

This server has been refactored to follow **official MCP standards**:

### Before (Custom Pattern)
```python
class WebSearchMCP:
    def list_tools(self):
        return [{"name": "search", ...}]
    
    def execute_tool(self, tool_name, parameters):
        if tool_name == "search":
            return self.search(...)
```

### After (Official SDK Pattern)
```python
from mcp.server import Server
from mcp.types import Tool, CallToolResult, TextContent

app = Server("web-search")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="search", ...)]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> CallToolResult:
    return CallToolResult(content=[TextContent(...)])
```

## 🎯 Benefits of Standardization

1. **Official SDK Compliance** - Uses `mcp` package types and patterns
2. **Async/Await** - Proper async handling for I/O operations
3. **Type Safety** - Proper typing with SDK types
4. **Error Handling** - Standard `CallToolResult` with `isError` flag
5. **Interoperability** - Works with any MCP client
6. **Future-Proof** - Updates with SDK versions

## 🚀 Tools Available

### 1. `search` - DuckDuckGo Web Search
```python
# Execute via MCP client
result = await session.call_tool(
    "search",
    {
        "query": "Python async programming",
        "num_results": 5  # Optional, default 10
    }
)
```

**Parameters:**
- `query` (string, required): Search query
- `num_results` (integer, optional): Results count (1-50, default 10)

**Returns:**
- Formatted text with titles, URLs, and snippets
- `isError: false` on success

### 2. `scrape_url` - Web Page Content Extraction
```python
# Execute via MCP client
result = await session.call_tool(
    "scrape_url",
    {
        "url": "https://example.com/article"
    }
)
```

**Parameters:**
- `url` (string, required): URL to scrape

**Returns:**
- Page title, URL, and clean text content (max 5000 chars)
- `isError: false` on success
- `isError: true` on timeout/HTTP errors

## 📦 Installation

### Option 1: Direct Install
```bash
cd mcp-store/servers/web-search
pip install -r requirements.txt
python web.py
```

### Option 2: Via MCP Manager (Mobile App)
```python
from mcp.server_manager import MCPServerManager

manager = MCPServerManager(storage_dir, store_url)
await manager.install_server("web-search")
```

## 🔌 Usage with Official MCP Clients

### Python Client (Stdio Transport)
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["web.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()
        
        # List tools
        tools = await session.list_tools()
        print([tool.name for tool in tools.tools])
        
        # Call search tool
        result = await session.call_tool(
            "search",
            {"query": "Python tutorials", "num_results": 3}
        )
        
        for content in result.content:
            print(content.text)
```

### Node.js/TypeScript Client
```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "python",
  args: ["web.py"],
});

const client = new Client({ name: "my-client" }, { capabilities: {} });
await client.connect(transport);

// Call tools
const result = await client.callTool({
  name: "search",
  arguments: { query: "Python tutorials", num_results: 3 }
});
```

## 🔧 Configuration

Server configuration is in `web.json`:
```json
{
  "configuration": {
    "search_engine": {
      "type": "string",
      "default": "duckduckgo"
    },
    "max_results": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

## 📱 Mobile Compatibility

- ✅ **Android**: Chaquopy compatible
- ✅ **Async I/O**: Non-blocking operations
- ✅ **Thread Pool**: Blocking calls executed in executor
- ⚠️ **Network Required**: Internet access needed
- ⚠️ **Battery Impact**: Low-medium depending on usage

## 🛠️ Development

### Run Tests (if available)
```bash
pytest tests/
```

### Run Server Standalone
```bash
python web.py
```

### Debug Mode
```bash
MCP_DEBUG=1 python web.py
```

## 📚 References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://modelcontextprotocol.io)
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Official Examples](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples)

## 📝 License

MIT License - see main repo LICENSE file

---

**Note**: This server follows the official MCP Python SDK patterns and is maintained to stay compatible with SDK updates. Any changes should preserve compliance with the [official specification](https://modelcontextprotocol.io).

