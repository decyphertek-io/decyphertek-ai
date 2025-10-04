import aiohttp
from bs4 import BeautifulSoup
import re

class ArticleExtractor:
    @staticmethod
    async def get_full_content(rss_description, article_url):
        """Extract full article content from RSS description or URL"""
        if rss_description is None:
            return None
        
        # Check if RSS content is truncated or looks like a summary
        if ArticleExtractor._is_content_truncated_or_summary(rss_description):
            if article_url and article_url.strip():
                return await ArticleExtractor._extract_from_url(article_url)
        
        return rss_description
    
    @staticmethod
    def _is_content_truncated_or_summary(content):
        """Check if content appears to be truncated or a summary"""
        # Remove HTML tags and CDATA for analysis
        clean_content = re.sub(r'<!\[CDATA\[', '', content)
        clean_content = re.sub(r'\]\]>', '', clean_content)
        clean_content = re.sub(r'<[^>]*>', '', clean_content)
        clean_content = clean_content.strip()
        
        return (len(clean_content) < 500 or
                clean_content.endswith('...') or
                clean_content.endswith('[...]') or
                'Read more' in clean_content or
                'Continue reading' in clean_content or
                'Ver más' in clean_content or
                'Leer más' in clean_content or
                '* ' in clean_content or
                len(clean_content.split('\n')) <= 5)
    
    @staticmethod
    async def _extract_from_url(url):
        """Extract article content from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return f'Error: Could not fetch article ({response.status})'
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove unwanted elements
                    ArticleExtractor._remove_unwanted_elements(soup)
                    
                    # Try multiple extraction strategies
                    content = (ArticleExtractor._extract_by_selectors(soup) or
                              ArticleExtractor._extract_largest_text_block(soup) or
                              ArticleExtractor._extract_by_readability(soup) or
                              'Content extraction failed')
                    
                    return ArticleExtractor._clean_content(content)
        except Exception as e:
            return f'Error fetching article: {str(e)}'
    
    @staticmethod
    def _remove_unwanted_elements(soup):
        """Remove unwanted elements from the HTML"""
        unwanted_selectors = [
            'nav', 'header', 'footer', '.ad', '.advertisement',
            '.social', '.share', '.comments', '.sidebar',
            '.navigation', '.menu', 'script', 'style',
            '.related', '.tags', '.author-info', '.newsletter',
            '.subscription', '.paywall', '.login-wall'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    @staticmethod
    def _extract_by_selectors(soup):
        """Extract content using common article selectors"""
        selectors = [
            '.body-nota', '.nota-cuerpo', '.article-body',  # Clarin specific
            'article', '.post-content', '.entry-content', '.article-content',
            '.content', '.story-body', '.post-body', '.entry', '.main-content',
            '.article-text', '.news-content', '.texto', '.contenido',
            '[data-module="ArticleBody"]', '.story-content'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if len(text) > 200:
                    return text
        
        return None
    
    @staticmethod
    def _extract_largest_text_block(soup):
        """Extract the largest text block from paragraphs"""
        paragraphs = soup.find_all('p')
        parent_texts = {}
        
        # Find the container with the most paragraph content
        for p in paragraphs:
            parent = p.parent
            if parent:
                existing_text = parent_texts.get(parent, '')
                p_text = p.get_text().strip()
                if p_text:
                    parent_texts[parent] = existing_text + ' ' + p_text
        
        # Find the parent with the most content
        largest_block = ''
        best_parent = None
        
        for parent, text in parent_texts.items():
            if len(text) > len(largest_block):
                largest_block = text
                best_parent = parent
        
        return largest_block.strip() if len(largest_block) > 200 else None
    
    @staticmethod
    def _extract_by_readability(soup):
        """Extract content using readability heuristics"""
        body_elements = soup.select('div, section, main, article')
        best_content = ''
        best_score = 0
        
        for element in body_elements:
            text = element.get_text().strip()
            score = ArticleExtractor._calculate_readability_score(element)
            
            if score > best_score and len(text) > 200:
                best_score = score
                best_content = text
        
        return best_content if best_content else None
    
    @staticmethod
    def _calculate_readability_score(element):
        """Calculate readability score for an element"""
        score = 0
        text = element.get_text()
        
        # More paragraphs = higher score
        score += len(element.select('p')) * 10
        
        # Text length bonus
        score += int(len(text) / 200)
        
        # Bonus for article-like structure
        element_class = element.get('class', [])
        if element_class:
            class_str = ' '.join(element_class)
            if ('article' in class_str or 'content' in class_str or
                'body' in class_str or 'texto' in class_str):
                score += 20
        
        # Penalty for unwanted elements
        score -= len(element.select('a'))
        score -= len(element.select('img'))
        score -= len(element.select('.ad, .advertisement')) * 10
        
        return score
    
    @staticmethod
    def _clean_content(content):
        """Clean up the extracted content"""
        content = re.sub(r'<!\[CDATA\[', '', content)
        content = re.sub(r'\]\]>', '', content)
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n+', '\n', content)
        return content.strip()
