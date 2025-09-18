"""
Website handler for generic web scraping.

Extracts title, meta description, headers, and other key information
from websites while respecting robots.txt and implementing rate limiting.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .base import BaseHandler
from utils.robots import RobotsChecker
from utils.logging import get_logger

logger = get_logger(__name__)


class WebsiteHandler(BaseHandler):
    """Handler for generic website scraping."""

    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize website handler.

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        super().__init__(config, cache_manager)
        self.robots_checker = RobotsChecker(user_agent=self.user_agent)
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

    @property
    def handler_name(self) -> str:
        """Return handler name."""
        return "website"

    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL.

        Args:
            url: URL to check

        Returns:
            True for any HTTP/HTTPS URL not handled by specialized handlers
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False

            domain = parsed.netloc.lower()

            # Skip if handled by specialized handlers
            specialized_domains = {
                'linkedin.com', 'www.linkedin.com',
                'twitter.com', 'www.twitter.com', 'x.com', 'www.x.com',
                'youtube.com', 'www.youtube.com',
                'github.com', 'www.github.com'
            }

            return domain not in specialized_domains
        except Exception:
            return False

    async def process(self, url: str) -> Dict[str, Any]:
        """Process website URL and extract information.

        Args:
            url: Website URL to process

        Returns:
            Dictionary with extracted information
        """
        # Check cache first
        cached = await self.get_cached_result(url)
        if cached:
            logger.debug(f"Using cached result for {url}")
            return cached

        try:
            # Check robots.txt
            if not await self._check_robots_allowed(url):
                result = self.create_skipped_result(url, "Blocked by robots.txt")
                await self.cache_result(url, result)
                return result

            # Fetch and parse the webpage
            response = await self._fetch_page(url)
            if not response:
                result = self.create_error_result(url, "Failed to fetch page")
                await self.cache_result(url, result)
                return result

            soup = BeautifulSoup(response.text, 'html.parser')
            extracted_data = await self._extract_website_data(url, soup)

            # Cache and return result
            await self.cache_result(url, extracted_data)
            return extracted_data

        except Exception as e:
            logger.error(f"Error processing website {url}: {e}")
            result = self.create_error_result(url, str(e))
            await self.cache_result(url, result)
            return result

    async def _check_robots_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        try:
            return await self.robots_checker.can_fetch(url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If we can't check robots.txt, err on the side of caution but allow
            return True

    async def _fetch_page(self, url: str) -> Optional[requests.Response]:
        """Fetch webpage content.

        Args:
            url: URL to fetch

        Returns:
            Response object or None if failed
        """
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(
                    url,
                    timeout=self.timeout_seconds,
                    allow_redirects=True
                )
            )

            if response.status_code == 200:
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def _extract_website_data(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured data from webpage.

        Args:
            url: Original URL
            soup: BeautifulSoup parsed content

        Returns:
            Structured data dictionary
        """
        domain = self.extract_domain(url)

        # Extract basic information
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        headers = self._extract_headers(soup)

        # Extract business signals
        key_points = []
        signals = []

        # Add title and description
        if title:
            key_points.append(f"Title: {self.truncate_text(title, 100)}")
        if description:
            key_points.append(f"Description: {self.truncate_text(description, 150)}")

        # Add headers
        for header in headers[:3]:  # Top 3 headers
            key_points.append(f"Section: {self.truncate_text(header, 80)}")

        # Look for business signals
        business_signals = self._find_business_signals(soup)
        signals.extend(business_signals[:4])  # Top 4 signals

        # Look for recent content
        recent_content = self._find_recent_content(soup)
        if recent_content:
            key_points.extend(recent_content[:2])  # Top 2 recent items

        return {
            'source': domain,
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title or empty string
        """
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description.

        Args:
            soup: BeautifulSoup object

        Returns:
            Meta description or empty string
        """
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            return desc_tag['content'].strip()

        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()

        return ""

    def _extract_headers(self, soup: BeautifulSoup) -> List[str]:
        """Extract H1, H2 headers.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of header texts
        """
        headers = []
        for tag in soup.find_all(['h1', 'h2'], limit=6):
            if tag.string:
                text = tag.get_text().strip()
                if text and len(text) > 3:
                    headers.append(text)
        return headers

    def _find_business_signals(self, soup: BeautifulSoup) -> List[str]:
        """Find business/outreach signals on the page.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of business signals
        """
        signals = []
        text_content = soup.get_text().lower()

        # Pricing/sales signals
        pricing_keywords = [
            'pricing', 'plans', 'subscribe', 'contact sales', 'get started',
            'free trial', 'demo', 'quote', 'buy now', 'purchase'
        ]

        for keyword in pricing_keywords:
            if keyword in text_content:
                signals.append(f"Has {keyword.title()} content")
                break

        # Hiring signals
        hiring_keywords = [
            'we\'re hiring', 'join our team', 'careers', 'job openings',
            'open positions', 'work with us'
        ]

        for keyword in hiring_keywords:
            if keyword in text_content:
                signals.append("Currently hiring")
                break

        # Technology signals
        tech_keywords = [
            'api', 'integration', 'developer', 'technical', 'saas', 'platform',
            'software', 'solution', 'automation'
        ]

        tech_mentions = sum(1 for keyword in tech_keywords if keyword in text_content)
        if tech_mentions >= 3:
            signals.append("Technology-focused company")

        # Contact information signals
        if any(word in text_content for word in ['contact', 'get in touch', 'reach out']):
            signals.append("Easy to contact")

        return signals

    def _find_recent_content(self, soup: BeautifulSoup) -> List[str]:
        """Find recent blog posts, news, or updates.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of recent content items
        """
        recent_items = []

        # Look for blog posts, news, articles
        content_selectors = [
            'article h2', 'article h3',
            '.blog-post h2', '.blog-post h3',
            '.news h2', '.news h3',
            '.post-title', '.article-title'
        ]

        for selector in content_selectors:
            items = soup.select(selector)
            for item in items[:3]:  # Max 3 items per selector
                text = item.get_text().strip()
                if text and len(text) > 10:
                    recent_items.append(f"Recent: {self.truncate_text(text, 60)}")

        return recent_items[:3]  # Return max 3 items total