# DecypherTek MCP Store

**Standardized MCP servers** following the [official Python SDK](https://github.com/modelcontextprotocol/python-sdk) patterns.

## 📦 Available Servers

All servers in this store follow the **official MCP specification** and use the standard Python SDK patterns.

### ✅ Standardized Servers

- **[web-search](servers/web-search/)** - DuckDuckGo search + web scraping (Official SDK ✓)
- **nextcloud** - Nextcloud file integration (Coming soon)
- **google-drive** - Google Drive integration (Coming soon)
- **google-voice** - Google Voice messaging (Coming soon)
- **whatsapp** - WhatsApp integration (Coming soon)

## 🎯 Standardization Benefits

1. **Official SDK Compliance** - Uses `mcp` package types
2. **Interoperability** - Works with any MCP client
3. **Type Safety** - Proper Python typing
4. **Async/Await** - Non-blocking I/O
5. **Error Handling** - Standard error responses
6. **Future-Proof** - Compatible with SDK updates

## 🚀 Quick Start

### Install a Server
```bash
cd servers/web-search
pip install -r requirements.txt
python web.py
```

### Use with Official MCP Client
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["servers/web-search/web.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

## 📚 Resources

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://modelcontextprotocol.io)
- [Official Examples](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples)
  
