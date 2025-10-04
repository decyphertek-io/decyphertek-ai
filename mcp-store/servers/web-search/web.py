
"""
Web Search MCP Server with Redundant Backup Methods
Handles YouTube videos, images, GIFs, and regular web content
Multiple search engines for reliability and rate limit handling
"""

import asyncio
import requests
import re
import json
from typing import Any, List, Dict, Optional
from urllib.parse import urlparse, parse_qs, quote_plus
from bs4 import BeautifulSoup

# Official MCP Python SDK imports (optional for standalone use)
try:
    from mcp.server import Server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        CallToolResult,
        ErrorData,
    )
    MCP_AVAILABLE = True
    # Initialize MCP server
    app = Server("web-search")
except ImportError:
    MCP_AVAILABLE = False
    print("[Web Search] MCP server not available - running in standalone mode")

# Initialize search engines with fallbacks
try:
    from duckduckgo_search import DDGS
    ddgs_available = True
    ddgs = DDGS()
except ImportError:
    ddgs_available = False
    ddgs = None

# Rate limiting tracking
search_timestamps = []
rate_limit = {'max_requests': 15, 'window_seconds': 60}  # More generous limits
failed_engines = {}  # Track which engines are currently failing


def check_rate_limit() -> bool:
    """Check if we're within rate limits"""
    import time
    current_time = time.time()
    
    # Remove old timestamps
    global search_timestamps
    search_timestamps = [ts for ts in search_timestamps if current_time - ts < rate_limit['window_seconds']]
    
    # Check if we're under the limit
    if len(search_timestamps) >= rate_limit['max_requests']:
        print(f"[Rate Limit] Hit limit: {len(search_timestamps)} requests in {rate_limit['window_seconds']}s")
        return False
    
    # Add current timestamp
    search_timestamps.append(current_time)
    return True


def is_engine_failing(engine_name: str) -> bool:
    """Check if an engine is currently marked as failing"""
    import time
    current_time = time.time()
    
    if engine_name in failed_engines:
        # If failure was more than 5 minutes ago, try again
        if current_time - failed_engines[engine_name] > 300:
            del failed_engines[engine_name]
            return False
        return True
    return False


def mark_engine_failed(engine_name: str):
    """Mark an engine as currently failing"""
    import time
    failed_engines[engine_name] = time.time()
    print(f"[Engine Status] Marked {engine_name} as failing")


def retry_with_delay(engine_name: str, max_retries: int = 2) -> bool:
    """Check if we should retry a failed engine"""
    import time
    import random
    
    if engine_name not in failed_engines:
        return True
    
    # Add random delay to avoid thundering herd
    delay = random.uniform(1, 3)
    time.sleep(delay)
    
    # Check if enough time has passed
    current_time = time.time()
    if current_time - failed_engines[engine_name] > 30:  # 30 second cooldown
        del failed_engines[engine_name]
        return True
    
    return False


def search_google_fallback(query: str, num_results: int = 5) -> List[Dict]:
    """Fallback search using Google (web scraping)"""
    if is_engine_failing("google"):
        print(f"[Google] Skipping - marked as failing")
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Google search URL
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse Google search results
        for result in soup.find_all('div', class_='g')[:num_results]:
            try:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('span', class_='aCOpRe')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    # Clean up Google's URL format
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"[Google Fallback] Error: {e}")
        mark_engine_failed("google")
        return []


def search_bing_fallback(query: str, num_results: int = 5) -> List[Dict]:
    """Fallback search using Bing (web scraping)"""
    if is_engine_failing("bing"):
        print(f"[Bing] Skipping - marked as failing")
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Bing search URL
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={num_results}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse Bing search results
        for result in soup.find_all('li', class_='b_algo')[:num_results]:
            try:
                title_elem = result.find('h2')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('p')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"[Bing Fallback] Error: {e}")
        mark_engine_failed("bing")
        return []


def search_yandex_fallback(query: str, num_results: int = 5) -> List[Dict]:
    """Fallback search using Yandex (web scraping)"""
    if is_engine_failing("yandex"):
        print(f"[Yandex] Skipping - marked as failing")
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Yandex search URL
        search_url = f"https://yandex.com/search/?text={quote_plus(query)}&numdoc={num_results}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse Yandex search results
        for result in soup.find_all('div', class_='serp-item')[:num_results]:
            try:
                title_elem = result.find('h2')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('div', class_='text-container')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"[Yandex Fallback] Error: {e}")
        mark_engine_failed("yandex")
        return []


def search_duckduckgo_html_fallback(query: str, num_results: int = 5) -> List[Dict]:
    """Fallback search using DuckDuckGo HTML (web scraping)"""
    if is_engine_failing("duckduckgo_html"):
        print(f"[DuckDuckGo HTML] Skipping - marked as failing")
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # DuckDuckGo HTML search URL
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse DuckDuckGo HTML results
        for result in soup.find_all('div', class_='result')[:num_results]:
            try:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text()
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"[DuckDuckGo HTML Fallback] Error: {e}")
        mark_engine_failed("duckduckgo_html")
        return []


def search_startpage_fallback(query: str, num_results: int = 5) -> List[Dict]:
    """Fallback search using Startpage (web scraping)"""
    if is_engine_failing("startpage"):
        print(f"[Startpage] Skipping - marked as failing")
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Startpage search URL
        search_url = f"https://www.startpage.com/sp/search?query={quote_plus(query)}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse Startpage results
        for result in soup.find_all('div', class_='w-gl__result')[:num_results]:
            try:
                title_elem = result.find('h3')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('p', class_='w-gl__description')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"[Startpage Fallback] Error: {e}")
        mark_engine_failed("startpage")
        return []


def search_ecosia_fallback(query: str, num_results: int = 5) -> List[Dict]:
    """Fallback search using Ecosia (web scraping)"""
    if is_engine_failing("ecosia"):
        print(f"[Ecosia] Skipping - marked as failing")
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Ecosia search URL
        search_url = f"https://www.ecosia.org/search?q={quote_plus(query)}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse Ecosia results
        for result in soup.find_all('div', class_='result')[:num_results]:
            try:
                title_elem = result.find('h2')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('p', class_='result-snippet')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"[Ecosia Fallback] Error: {e}")
        mark_engine_failed("ecosia")
        return []


def search_with_fallbacks(query: str, num_results: int = 5) -> List[Dict]:
    """Search with comprehensive fallback methods - should always work!"""
    
    # Method 1: Try DuckDuckGo API (if available and not rate limited)
    if ddgs_available and check_rate_limit():
        try:
            print(f"[Web Search] Method 1: Using DuckDuckGo API for: {query}")
            results = list(ddgs.text(query, max_results=num_results))
            if results:
                print(f"[Web Search] ✅ DuckDuckGo API succeeded with {len(results)} results")
                return results
        except Exception as e:
            print(f"[DuckDuckGo API] Error: {e}")
            mark_engine_failed("duckduckgo_api")
    
    # Method 2: Try DuckDuckGo HTML (web scraping)
    print(f"[Web Search] Method 2: Trying DuckDuckGo HTML for: {query}")
    results = search_duckduckgo_html_fallback(query, num_results)
    if results:
        print(f"[Web Search] ✅ DuckDuckGo HTML succeeded with {len(results)} results")
        return results
    
    # Method 3: Try Google (web scraping)
    print(f"[Web Search] Method 3: Trying Google for: {query}")
    results = search_google_fallback(query, num_results)
    if results:
        print(f"[Web Search] ✅ Google succeeded with {len(results)} results")
        return results
    
    # Method 4: Try Bing (web scraping)
    print(f"[Web Search] Method 4: Trying Bing for: {query}")
    results = search_bing_fallback(query, num_results)
    if results:
        print(f"[Web Search] ✅ Bing succeeded with {len(results)} results")
        return results
    
    # Method 5: Try Yandex (web scraping)
    print(f"[Web Search] Method 5: Trying Yandex for: {query}")
    results = search_yandex_fallback(query, num_results)
    if results:
        print(f"[Web Search] ✅ Yandex succeeded with {len(results)} results")
        return results
    
    # Method 6: Try Startpage (web scraping)
    print(f"[Web Search] Method 6: Trying Startpage for: {query}")
    results = search_startpage_fallback(query, num_results)
    if results:
        print(f"[Web Search] ✅ Startpage succeeded with {len(results)} results")
        return results
    
    # Method 7: Try Ecosia (web scraping)
    print(f"[Web Search] Method 7: Trying Ecosia for: {query}")
    results = search_ecosia_fallback(query, num_results)
    if results:
        print(f"[Web Search] ✅ Ecosia succeeded with {len(results)} results")
        return results
    
    # Method 8: All methods failed - return helpful error
    print(f"[Web Search] ❌ All 7 search methods failed for: {query}")
    return [{
        'title': 'Search Temporarily Unavailable',
        'url': '',
        'snippet': f'All search engines are currently unavailable for query: "{query}". This is very rare - please try again in a few minutes. We tried 7 different search methods including DuckDuckGo, Google, Bing, Yandex, Startpage, and Ecosia.'
    }]


def extract_youtube_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/shorts\/([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_image_url(url: str) -> bool:
    """Check if URL points to an image"""
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')
    return url.lower().endswith(image_extensions)


def is_video_url(url: str) -> bool:
    """Check if URL points to a video"""
    video_extensions = ('.mp4', '.webm', '.ogg', '.mov', '.avi')
    return url.lower().endswith(video_extensions)


# MCP Server functions (only if MCP is available)
if MCP_AVAILABLE:
    @app.list_tools()
    async def list_tools() -> list[Tool]:
        """
        List available tools following MCP specification.
        
        Returns:
            List of Tool objects with proper schema
        """
        return [
            Tool(
                name="search",
                description="Search the web using DuckDuckGo. Returns text results with multimedia content (YouTube videos, images, GIFs)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="search_videos",
                description="Search specifically for YouTube videos",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Video search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of videos to return (default: 3)",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="search_images",
                description="Search for images and GIFs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Image search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of images to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
        ]


# MCP Server functions (only if MCP is available)
if MCP_AVAILABLE:
    @app.call_tool()
    async def call_tool(name: str, arguments: Any) -> CallToolResult:
        """
        Execute tool calls following MCP specification.
        
        Args:
            name: Tool name to execute
            arguments: Tool arguments as dict
            
        Returns:
            CallToolResult with content or error
        """
        try:
            if name == "search":
                return await handle_search(arguments)
            elif name == "search_videos":
                return await handle_video_search(arguments)
            elif name == "search_images":
                return await handle_image_search(arguments)
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Unknown tool: {name}",
                        )
                    ],
                    isError=True,
                )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ],
                isError=True,
            )


async def handle_search(arguments: dict) -> CallToolResult:
    """
    Handle general web search with multimedia detection and fallback methods.
    
    Args:
        arguments: Dict with 'query' and optional 'num_results'
        
    Returns:
        CallToolResult with search results including multimedia
    """
    query = arguments.get("query", "")
    num_results = arguments.get("num_results", 5)
    
    # Use fallback search system
    results = search_with_fallbacks(query, num_results)
    
    content_items = []
    multimedia_found = []
    
    for i, result in enumerate(results, 1):
        url = result.get("href", "")
        title = result.get("title", "No title")
        snippet = result.get("body", "No description")
        
        # Check for YouTube videos
        youtube_id = extract_youtube_id(url)
        if youtube_id:
            multimedia_found.append({
                "type": "youtube",
                "id": youtube_id,
                "title": title,
                "url": url
            })
        
        # Check for images
        elif is_image_url(url):
            multimedia_found.append({
                "type": "image",
                "url": url,
                "title": title
            })
        
        # Check for videos
        elif is_video_url(url):
            multimedia_found.append({
                "type": "video",
                "url": url,
                "title": title
            })
        
        # Add text result
        content_items.append(
            TextContent(
                type="text",
                text=f"{i}. {title}\n{snippet}\n{url}\n"
            )
        )
    
    # Add multimedia summary at the beginning
    if multimedia_found:
        multimedia_text = "\n🎬 MULTIMEDIA CONTENT FOUND:\n"
        for item in multimedia_found:
            if item["type"] == "youtube":
                multimedia_text += f"▶️ YouTube: {item['title']}\n   ID: {item['id']}\n   URL: {item['url']}\n"
            elif item["type"] == "image":
                multimedia_text += f"🖼️ Image: {item['title']}\n   URL: {item['url']}\n"
            elif item["type"] == "video":
                multimedia_text += f"🎥 Video: {item['title']}\n   URL: {item['url']}\n"
        
        content_items.insert(0, TextContent(type="text", text=multimedia_text))
    
    return CallToolResult(content=content_items)


async def handle_video_search(arguments: dict) -> CallToolResult:
    """
    Handle YouTube video search.
    
    Args:
        arguments: Dict with 'query' and optional 'num_results'
        
    Returns:
        CallToolResult with video results
    """
    query = arguments.get("query", "")
    num_results = arguments.get("num_results", 3)
    
    # Add "youtube" to query for better video results
    video_query = f"{query} site:youtube.com OR site:youtu.be"
    results = search_with_fallbacks(video_query, num_results)
    
    content_items = []
    videos_found = []
    
    for result in results:
        url = result.get("href", "")
        youtube_id = extract_youtube_id(url)
        
        if youtube_id:
            title = result.get("title", "No title")
            videos_found.append({
                "id": youtube_id,
                "title": title,
                "url": url
            })
    
    if videos_found:
        text = "🎬 YOUTUBE VIDEOS FOUND:\n\n"
        for i, video in enumerate(videos_found, 1):
            text += f"{i}. {video['title']}\n"
            text += f"   Video ID: {video['id']}\n"
            text += f"   URL: {video['url']}\n"
            text += f"   Embed: https://www.youtube.com/embed/{video['id']}\n\n"
        
        content_items.append(TextContent(type="text", text=text))
    else:
        content_items.append(TextContent(type="text", text="No YouTube videos found."))
    
    return CallToolResult(content=content_items)


async def handle_image_search(arguments: dict) -> CallToolResult:
    """
    Handle image search.
    
    Args:
        arguments: Dict with 'query' and optional 'num_results'
        
    Returns:
        CallToolResult with image results
    """
    query = arguments.get("query", "")
    num_results = arguments.get("num_results", 5)
    
    try:
        # Try DuckDuckGo images first, fallback to general search
        if ddgs_available and check_rate_limit():
            try:
                results = list(ddgs.images(query, max_results=num_results))
            except Exception as e:
                print(f"[DuckDuckGo Images] Error: {e}")
                results = []
        else:
            results = []
        
        # If no image results, try general search with image filter
        if not results:
            image_query = f"{query} filetype:jpg OR filetype:png OR filetype:gif"
            results = search_with_fallbacks(image_query, num_results)
        
        content_items = []
        images_found = []
        
        for result in results:
            image_url = result.get("image", "")
            title = result.get("title", "No title")
            
            if image_url:
                images_found.append({
                    "url": image_url,
                    "title": title
                })
        
        if images_found:
            text = "🖼️ IMAGES FOUND:\n\n"
            for i, img in enumerate(images_found, 1):
                text += f"{i}. {img['title']}\n"
                text += f"   URL: {img['url']}\n\n"
            
            content_items.append(TextContent(type="text", text=text))
        else:
            content_items.append(TextContent(type="text", text="No images found."))
        
        return CallToolResult(content=content_items)
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Image search error: {str(e)}",
                )
            ],
            isError=True,
        )


# Module-level functions for direct import (Chaquopy compatibility)
if MCP_AVAILABLE:
    async def search(query: str, num_results: int = 5) -> CallToolResult:
        """
        Direct search function for Chaquopy
        Can be called without spawning server process
        """
        return await call_tool("search", {"query": query, "num_results": num_results})


    async def search_videos(query: str, num_results: int = 3) -> CallToolResult:
        """
        Direct video search function for Chaquopy
        Can be called without spawning server process
        """
        return await call_tool("search_videos", {"query": query, "num_results": num_results})


    async def search_images(query: str, num_results: int = 5) -> CallToolResult:
        """
        Direct image search function for Chaquopy
        Can be called without spawning server process
        """
        return await call_tool("search_images", {"query": query, "num_results": num_results})


    async def main():
        """
        Main entry point for running the MCP server.
        Standard pattern from official SDK.
        """
        # Import stdio transport
        from mcp.server.stdio import stdio_server
        
        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )


# Entry point
if __name__ == "__main__":
    if MCP_AVAILABLE:
        asyncio.run(main())
    else:
        # Standalone mode - can be imported and used directly
        print("[Web Search] Running in standalone mode - ready for import")
