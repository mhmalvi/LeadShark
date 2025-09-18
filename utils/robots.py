"""
Robots.txt checker for ToS compliance.

Checks robots.txt files to ensure we respect website scraping policies
and maintain ethical scraping practices.
"""

import asyncio
from typing import Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

from .cache import CacheManager
from .logging import get_logger

logger = get_logger(__name__)


class RobotsChecker:
    """Robots.txt compliance checker."""

    def __init__(self, user_agent: str = "ProspectResearchBot/1.0", cache_manager: Optional[CacheManager] = None):
        """Initialize robots checker.

        Args:
            user_agent: User agent string to check against
            cache_manager: Optional cache manager for robots.txt caching
        """
        self.user_agent = user_agent
        self.cache_manager = cache_manager
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.forbidden_domains: Set[str] = {
            # Explicitly forbidden domains (ToS violations)
            'linkedin.com',
            'www.linkedin.com',
            # Add other domains that explicitly forbid scraping
        }

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if fetching is allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check forbidden domains first
            if domain in self.forbidden_domains:
                logger.debug(f"Domain {domain} is explicitly forbidden")
                return False

            # Get robots.txt for domain
            robots_parser = await self._get_robots_parser(domain)
            if not robots_parser:
                # If we can't get robots.txt, allow by default
                logger.debug(f"No robots.txt found for {domain}, allowing by default")
                return True

            # Check if URL is allowed
            can_fetch = robots_parser.can_fetch(self.user_agent, url)
            logger.debug(f"Robots.txt check for {url}: {'allowed' if can_fetch else 'forbidden'}")
            return can_fetch

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If there's an error, err on the side of caution but allow
            return True

    async def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """Get robots.txt parser for domain.

        Args:
            domain: Domain to get robots.txt for

        Returns:
            RobotFileParser instance or None if not available
        """
        # Check memory cache first
        if domain in self.robots_cache:
            return self.robots_cache[domain]

        # Check persistent cache
        if self.cache_manager:
            cached_robots = await self.cache_manager.get(f"robots:{domain}", "robots")
            if cached_robots:
                try:
                    parser = RobotFileParser()
                    parser.set_url(f"https://{domain}/robots.txt")
                    # Parse from cached content
                    if cached_robots.get('content'):
                        lines = cached_robots['content'].split('\n')
                        for line in lines:
                            parser.add_line(line)
                    parser.parse()
                    self.robots_cache[domain] = parser
                    return parser
                except Exception as e:
                    logger.debug(f"Error parsing cached robots.txt for {domain}: {e}")

        # Fetch robots.txt
        robots_url = f"https://{domain}/robots.txt"
        try:
            # Use asyncio to avoid blocking
            robots_content = await asyncio.get_event_loop().run_in_executor(
                None,
                self._fetch_robots_content,
                robots_url
            )

            if robots_content is None:
                # Try HTTP fallback
                robots_url = f"http://{domain}/robots.txt"
                robots_content = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._fetch_robots_content,
                    robots_url
                )

            parser = RobotFileParser()
            parser.set_url(robots_url)

            if robots_content:
                # Parse content
                lines = robots_content.split('\n')
                for line in lines:
                    parser.add_line(line)
                parser.parse()

                # Cache the result
                if self.cache_manager:
                    await self.cache_manager.set(
                        f"robots:{domain}",
                        {
                            'url': robots_url,
                            'content': robots_content,
                            'domain': domain
                        },
                        ttl=86400,  # Cache for 24 hours
                        category="robots"
                    )
            else:
                # Empty robots.txt (allow everything)
                parser.parse()

            # Cache in memory
            self.robots_cache[domain] = parser
            return parser

        except Exception as e:
            logger.debug(f"Error fetching robots.txt for {domain}: {e}")
            return None

    def _fetch_robots_content(self, robots_url: str) -> Optional[str]:
        """Fetch robots.txt content synchronously.

        Args:
            robots_url: URL to robots.txt file

        Returns:
            Robots.txt content or None if not available
        """
        try:
            response = requests.get(
                robots_url,
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'text/plain, text/html, */*'
                },
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                # No robots.txt file (allow everything)
                return ""
            else:
                logger.debug(f"HTTP {response.status_code} for {robots_url}")
                return None

        except requests.exceptions.RequestException as e:
            logger.debug(f"Request error for {robots_url}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error fetching {robots_url}: {e}")
            return None

    def add_forbidden_domain(self, domain: str) -> None:
        """Add domain to forbidden list.

        Args:
            domain: Domain to forbid
        """
        self.forbidden_domains.add(domain.lower())
        logger.info(f"Added {domain} to forbidden domains list")

    def remove_forbidden_domain(self, domain: str) -> None:
        """Remove domain from forbidden list.

        Args:
            domain: Domain to remove from forbidden list
        """
        self.forbidden_domains.discard(domain.lower())
        logger.info(f"Removed {domain} from forbidden domains list")

    def is_domain_forbidden(self, domain: str) -> bool:
        """Check if domain is explicitly forbidden.

        Args:
            domain: Domain to check

        Returns:
            True if domain is forbidden
        """
        return domain.lower() in self.forbidden_domains

    async def get_crawl_delay(self, domain: str) -> float:
        """Get crawl delay for domain from robots.txt.

        Args:
            domain: Domain to check

        Returns:
            Crawl delay in seconds (0 if not specified)
        """
        try:
            parser = await self._get_robots_parser(domain)
            if parser:
                delay = parser.crawl_delay(self.user_agent)
                return float(delay) if delay else 0.0
            return 0.0

        except Exception as e:
            logger.debug(f"Error getting crawl delay for {domain}: {e}")
            return 0.0

    def clear_cache(self) -> None:
        """Clear robots.txt cache."""
        self.robots_cache.clear()
        logger.info("Cleared robots.txt cache")