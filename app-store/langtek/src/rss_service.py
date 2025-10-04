import aiohttp
import asyncio
import feedparser

class RssService:
    async def get_rss_feed(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        return feed
                    else:
                        print(f'Failed to load RSS feed from {url}: {response.status}')
                        return None
        except Exception as e:
            print(f'Error fetching RSS feed from {url}: {str(e)}')
            return None
