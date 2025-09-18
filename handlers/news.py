"""
News handler for news articles and press releases.

Extracts article title, publish date, content summary, and key takeaways
from news websites and blog posts.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .base import BaseHandler
from utils.logging import get_logger

logger = get_logger(__name__)


class NewsHandler(BaseHandler):
    """Handler for news articles and blog posts."""

    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize news handler.

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        super().__init__(config, cache_manager)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Common news domains and URL patterns
        self.news_indicators = {
            'domains': {
                'techcrunch.com', 'venturebeat.com', 'techradar.com', 'engadget.com',
                'theverge.com', 'wired.com', 'arstechnica.com', 'reuters.com',
                'bloomberg.com', 'wsj.com', 'nytimes.com', 'washingtonpost.com',
                'forbes.com', 'businessinsider.com', 'cnbc.com', 'cnn.com',
                'bbc.com', 'guardian.co.uk', 'independent.co.uk'
            },
            'url_patterns': [
                r'/news/', r'/article/', r'/story/', r'/blog/', r'/post/',
                r'/press-release/', r'/announcement/', r'/update/'
            ],
            'path_keywords': [
                'news', 'article', 'story', 'blog', 'post', 'press',
                'announcement', 'update', 'release'
            ]
        }

    @property
    def handler_name(self) -> str:
        """Return handler name."""
        return "news"

    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL.

        Args:
            url: URL to check

        Returns:
            True for news articles and blog posts
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()

            # Check known news domains
            if any(news_domain in domain for news_domain in self.news_indicators['domains']):
                return True

            # Check URL patterns
            if any(re.search(pattern, url, re.IGNORECASE) for pattern in self.news_indicators['url_patterns']):
                return True

            # Check path keywords
            if any(keyword in path for keyword in self.news_indicators['path_keywords']):
                return True

            return False

        except Exception:
            return False

    async def process(self, url: str) -> Dict[str, Any]:
        """Process news article URL.

        Args:
            url: News article URL to process

        Returns:
            Dictionary with article information
        """
        # Check cache first
        cached = await self.get_cached_result(url)
        if cached:
            logger.debug(f"Using cached result for {url}")
            return cached

        try:
            # Fetch the article
            response = await self._fetch_article(url)
            if not response:
                result = self.create_error_result(url, "Failed to fetch article")
                await self.cache_result(url, result)
                return result

            soup = BeautifulSoup(response.text, 'html.parser')
            article_data = await self._extract_article_data(url, soup)

            # Cache and return result
            await self.cache_result(url, article_data)
            return article_data

        except Exception as e:
            logger.error(f"Error processing news article {url}: {e}")
            result = self.create_error_result(url, str(e))
            await self.cache_result(url, result)
            return result

    async def _fetch_article(self, url: str) -> Optional[requests.Response]:
        """Fetch article content.

        Args:
            url: URL to fetch

        Returns:
            Response object or None if failed
        """
        try:
            response = requests.get(
                url,
                headers=self.session.headers,
                timeout=self.timeout_seconds,
                allow_redirects=True
            )

            if response.status_code == 200:
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None

        except Exception as e:
            logger.error(f"Error fetching article {url}: {e}")
            return None

    async def _extract_article_data(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured data from article.

        Args:
            url: Original URL
            soup: BeautifulSoup parsed content

        Returns:
            Structured article data
        """
        domain = self.extract_domain(url)

        # Extract article components
        title = self._extract_article_title(soup)
        publish_date = self._extract_publish_date(soup)
        author = self._extract_author(soup)
        content_summary = self._extract_content_summary(soup)
        takeaways = self._extract_key_takeaways(soup)

        key_points = []
        signals = []

        # Add title
        if title:
            key_points.append(f"Title: {self.truncate_text(title, 100)}")

        # Add publish date and author
        if publish_date:
            key_points.append(f"Published: {publish_date}")
            # Check if recent (within 90 days)
            if self._is_recent_article(publish_date):
                signals.append("Recent publication (within 90 days)")

        if author:
            key_points.append(f"Author: {author}")

        # Add content summary
        if content_summary:
            key_points.append(f"Summary: {self.truncate_text(content_summary, 150)}")

        # Add key takeaways
        for takeaway in takeaways[:3]:  # Top 3 takeaways
            key_points.append(f"• {self.truncate_text(takeaway, 80)}")

        # Business signals from content
        business_signals = self._find_business_signals_in_content(soup)
        signals.extend(business_signals[:3])

        # Publication signals
        if self._is_business_publication(domain):
            signals.append("Business/tech publication")

        return {
            'source': domain,
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    def _extract_article_title(self, soup: BeautifulSoup) -> str:
        """Extract article title.

        Args:
            soup: BeautifulSoup object

        Returns:
            Article title
        """
        # Try various title selectors
        title_selectors = [
            'h1[class*="title"]',
            'h1[class*="headline"]',
            '.article-title',
            '.post-title',
            '.entry-title',
            'h1',
            'title'
        ]

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                return title_elem.get_text().strip()

        return ""

    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date.

        Args:
            soup: BeautifulSoup object

        Returns:
            Publication date string
        """
        # Try JSON-LD structured data
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, list):
                    data = data[0]
                date_published = data.get('datePublished') or data.get('dateCreated')
                if date_published:
                    return self._format_date(date_published)
            except Exception:
                pass

        # Try meta tags
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publishdate"]',
            'meta[name="date"]',
            'meta[property="og:updated_time"]'
        ]

        for selector in meta_selectors:
            meta = soup.select_one(selector)
            if meta and meta.get('content'):
                return self._format_date(meta['content'])

        # Try time elements
        time_elem = soup.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                return self._format_date(datetime_attr)

        return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author.

        Args:
            soup: BeautifulSoup object

        Returns:
            Author name
        """
        # Try various author selectors
        author_selectors = [
            '.author-name',
            '.byline-author',
            '[rel="author"]',
            '.post-author',
            '.article-author'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem and author_elem.get_text().strip():
                return author_elem.get_text().strip()

        # Try meta tag
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            return author_meta['content'].strip()

        return ""

    def _extract_content_summary(self, soup: BeautifulSoup) -> str:
        """Extract content summary.

        Args:
            soup: BeautifulSoup object

        Returns:
            Content summary
        """
        # Try article excerpt/summary
        summary_selectors = [
            '.article-summary',
            '.post-excerpt',
            '.entry-summary',
            '.article-lead',
            '.intro-text'
        ]

        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem and summary_elem.get_text().strip():
                return summary_elem.get_text().strip()

        # Try first paragraph of article content
        content_selectors = [
            '.article-content p:first-of-type',
            '.post-content p:first-of-type',
            '.entry-content p:first-of-type',
            'article p:first-of-type'
        ]

        for selector in content_selectors:
            para = soup.select_one(selector)
            if para and para.get_text().strip():
                text = para.get_text().strip()
                if len(text) > 50:  # Ensure it's substantial
                    return text

        return ""

    def _extract_key_takeaways(self, soup: BeautifulSoup) -> List[str]:
        """Extract key takeaways from article.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of key takeaways
        """
        takeaways = []

        # Look for bullet points or numbered lists
        list_items = soup.select('article li, .article-content li, .post-content li')
        for item in list_items[:5]:  # Max 5 items
            text = item.get_text().strip()
            if len(text) > 20 and len(text) < 200:  # Reasonable length
                takeaways.append(text)

        # Look for subheadings as takeaways
        if len(takeaways) < 3:
            headings = soup.select('article h2, article h3, .article-content h2, .article-content h3')
            for heading in headings[:3]:
                text = heading.get_text().strip()
                if len(text) > 10 and len(text) < 100:
                    takeaways.append(text)

        return takeaways

    def _find_business_signals_in_content(self, soup: BeautifulSoup) -> List[str]:
        """Find business signals in article content.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of business signals
        """
        signals = []
        text_content = soup.get_text().lower()

        # Business event signals
        business_events = [
            ('funding', 'Mentions funding/investment'),
            ('acquisition', 'Mentions acquisition/merger'),
            ('ipo', 'Mentions IPO/public offering'),
            ('partnership', 'Mentions partnerships'),
            ('launch', 'Product/service launch'),
            ('expansion', 'Business expansion'),
            ('hiring', 'Hiring/team growth')
        ]

        for keyword, signal in business_events:
            if keyword in text_content:
                signals.append(signal)

        # Industry focus
        tech_terms = ['ai', 'artificial intelligence', 'machine learning', 'blockchain', 'cloud', 'saas']
        tech_count = sum(1 for term in tech_terms if term in text_content)
        if tech_count >= 2:
            signals.append('Technology-focused content')

        return signals

    def _format_date(self, date_str: str) -> str:
        """Format date string.

        Args:
            date_str: Raw date string

        Returns:
            Formatted date string
        """
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    dt = datetime.strptime(date_str[:len(fmt)], fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            # If we can't parse, return first 10 characters (likely YYYY-MM-DD)
            return date_str[:10]

        except Exception:
            return date_str

    def _is_recent_article(self, date_str: str) -> bool:
        """Check if article is recent (within 90 days).

        Args:
            date_str: Date string

        Returns:
            True if recent
        """
        try:
            article_date = datetime.strptime(date_str, '%Y-%m-%d')
            days_ago = (datetime.now() - article_date).days
            return days_ago <= 90
        except Exception:
            return False

    def _is_business_publication(self, domain: str) -> bool:
        """Check if domain is a business publication.

        Args:
            domain: Domain name

        Returns:
            True if business publication
        """
        business_domains = {
            'techcrunch.com', 'venturebeat.com', 'bloomberg.com',
            'wsj.com', 'forbes.com', 'businessinsider.com',
            'cnbc.com', 'reuters.com'
        }

        return any(biz_domain in domain for biz_domain in business_domains)