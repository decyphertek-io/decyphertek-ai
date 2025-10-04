# Web Search MCP Server - AI Instructions

## Overview
This MCP server provides web search and scraping capabilities for AI assistants running in the DecypherTek AI mobile app environment (Android with Chaquopy).

## Mobile Environment Context
- **Runtime**: Python via Chaquopy on Android
- **Execution**: Server runs in the mobile app's Python environment
- **Access**: AI can execute this server's tools through the MCP manager

## Available Tools

### 1. `search` - Web Search
**Purpose**: Search the web using DuckDuckGo and return relevant results.

**When to Use**:
- User asks for current information not in your knowledge base
- User requests to "search for", "look up", or "find information about" something
- Questions about recent events, news, or data

**How to Execute**:
```python
# Through MCP Manager in mobile app
from mcp.server_manager import MCPServerManager

# Initialize
manager = MCPServerManager(data_dir, store_url)

# Execute search
result = await manager.execute_server(
    server_id="web-search",
    method="search",
    params={
        "query": "Python tutorials 2024",
        "num_results": 5  # Optional, defaults to 10
    }
)
```

**Parameters**:
- `query` (string, **required**): The search query
- `num_results` (integer, optional): Number of results to return (default: 10)

**Returns**:
```json
[
    {
        "title": "Result title",
        "url": "https://example.com",
        "snippet": "Brief description of the page..."
    }
]
```

**Example Interaction**:
```
User: "Search for the latest Python best practices"

AI Action:
1. Recognize search intent
2. Call search tool with query="latest Python best practices"
3. Parse results
4. Present summarized findings to user with sources
```

### 2. `scrape_url` - Web Page Scraping
**Purpose**: Extract full text content from a specific URL.

**When to Use**:
- User provides a URL and asks for its content
- Need to read article text from search results
- Extract information from a specific webpage
- User asks "what does this page say" or "summarize this article"

**How to Execute**:
```python
# Through MCP Manager
result = await manager.execute_server(
    server_id="web-search",
    method="scrape_url",
    params={
        "url": "https://example.com/article"
    }
)
```

**Parameters**:
- `url` (string, **required**): The URL to scrape

**Returns**:
```json
{
    "url": "https://example.com/article",
    "title": "Article Title",
    "content": "Full text content (up to 5000 chars)..."
}
```

**On Error**:
```json
{
    "url": "https://example.com/article",
    "error": "Error message"
}
```

**Example Interaction**:
```
User: "Summarize this article: https://example.com/ai-trends"

AI Action:
1. Call scrape_url with the provided URL
2. Extract the content from the response
3. Summarize the content
4. Present summary to user
```

## AI Guidelines for Using This Server

### When to Search
✅ **DO use search for**:
- Current events or recent information
- Specific facts you don't know
- User explicitly requests search
- Verifying or updating information
- Finding resources, tutorials, or documentation

❌ **DON'T use search for**:
- General knowledge questions you can answer
- Every user question (only when needed)
- Information that's already in the conversation context

### Search Best Practices

1. **Formulate Clear Queries**
   - Use specific, targeted search terms
   - Include relevant keywords
   - Example: Instead of "Python", use "Python async/await tutorial 2024"

2. **Handle Results Appropriately**
   - Check if results are returned (may be empty)
   - Parse and summarize findings
   - Always cite sources with URLs
   - Don't just dump raw results

3. **Combine Search with Scraping**
   ```
   Workflow:
   1. Search for relevant pages
   2. Identify most relevant URL from results
   3. Scrape that URL for full content
   4. Analyze and present information
   ```

4. **Error Handling**
   - Network may fail on mobile
   - Handle empty results gracefully
   - Inform user if search fails
   - Offer to try alternative approach

### Response Format

**Good Response**:
```
I searched for "Python FastAPI tutorial" and found several resources:

1. **FastAPI Official Tutorial** (fastapi.tiangolo.com)
   - Comprehensive guide for beginners
   - Covers async/await and type hints

2. **Real Python: FastAPI Guide** (realpython.com)
   - Step-by-step walkthrough
   - Includes database integration

Would you like me to get the full content from any of these?
```

**Bad Response**:
```
Here are the search results:
[dumps raw JSON]
```

## Mobile-Specific Considerations

### Performance
- **Search**: ~2-5 seconds typical
- **Scraping**: ~3-10 seconds depending on page size
- **Inform user**: "Searching..." or "Fetching page content..."

### Network
- Mobile may have limited connectivity
- Timeout: 10 seconds for scraping
- Handle network errors gracefully

### Battery
- Don't make excessive requests
- Batch related searches if possible
- Cache results in conversation context

### Data Usage
- Be mindful of mobile data
- Scraping downloads full pages
- Inform user if fetching large content

## Integration with ChromaDB RAG

After searching or scraping, consider storing valuable information:

```python
# Store search results in RAG for context
from rag.chroma_engine import ChromaRAGEngine

rag = ChromaRAGEngine(storage_dir)

# Store important findings
rag.add_message(
    text=f"Search results for '{query}': {formatted_results}",
    user_id=user_id,
    conversation_id=conversation_id,
    message_type="system",
    metadata={"source": "web_search", "query": query}
)
```

This allows future queries to reference past searches without re-searching.

## Example Complete Workflow

```
User: "Find and summarize articles about Python async programming"

AI Process:
1. Execute search:
   - Query: "Python async programming best practices 2024"
   - Get top 5 results

2. Select best result (e.g., Real Python article)

3. Execute scrape_url on that article

4. Read and summarize content

5. Present to user:
   "I found this comprehensive guide on Python async programming...
   [summary]
   
   Source: [title] ([url])"

6. Store in RAG:
   - Search query and results
   - Scraped content summary
   - For future reference in conversation
```

## Configuration

Server configuration is set via `web.json`:
- `search_engine`: "duckduckgo" (only option currently)
- `max_results`: Default number of search results (1-50)

## Dependencies Required
- `duckduckgo-search>=4.0.0`
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`

These are installed automatically by the MCP manager when the server is installed.

## Troubleshooting

### "Server not installed"
- Check if web-search server is installed in MCP manager
- Install from GitHub store if needed

### "Network error"
- Mobile device may not have internet
- Try again when connected
- Inform user of connectivity issue

### "No results found"
- Query may be too specific
- Try broader search terms
- Inform user to rephrase query

### "Rate limited"
- DuckDuckGo may rate limit
- Wait a few seconds and retry
- Consider caching results

---

**Remember**: This server enhances AI capabilities but should be used judiciously. Always prioritize user privacy and be transparent when fetching external data.

