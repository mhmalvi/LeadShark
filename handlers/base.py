"""
Base handler class for all URL processors.

Provides common functionality and interface for all handlers.
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from utils.cache import CacheManager
from utils.logging import get_logger

logger = get_logger(__name__)


class BaseHandler(ABC):
    """Base class for all URL handlers."""

    def __init__(self, config: Dict[str, Any], cache_manager: Optional[CacheManager] = None):
        """Initialize base handler.

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager instance
        """
        self.config = config
        self.cache_manager = cache_manager
        self.max_cell_chars = config.get('MAX_CELL_CHARS', 4000)
        self.timeout_seconds = config.get('TIMEOUT_SECONDS', 20)
        self.user_agent = config.get('USER_AGENT', 'ProspectResearchBot/1.0')

    @property
    @abstractmethod
    def handler_name(self) -> str:
        """Return the name of this handler."""
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the given URL.

        Args:
            url: URL to check

        Returns:
            True if this handler can process the URL
        """
        pass

    @abstractmethod
    async def process(self, url: str) -> Dict[str, Any]:
        """Process a URL and return enrichment data.

        Args:
            url: URL to process

        Returns:
            Dictionary containing:
                - source: domain/platform name
                - url: normalized URL
                - key_points: list of key findings
                - signals: list of outreach signals
                - status: processing status
                - error: error message if any
                - last_checked: ISO8601 timestamp
        """
        pass

    def get_cache_key(self, url: str) -> str:
        """Generate cache key for URL.

        Args:
            url: URL to generate key for

        Returns:
            Cache key string
        """
        return hashlib.sha256(f"{self.handler_name}:{url}".encode()).hexdigest()

    async def get_cached_result(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached result for URL.

        Args:
            url: URL to check cache for

        Returns:
            Cached result if available, None otherwise
        """
        if not self.cache_manager:
            return None

        cache_key = self.get_cache_key(url)
        return await self.cache_manager.get(cache_key)

    async def cache_result(self, url: str, result: Dict[str, Any]) -> None:
        """Cache result for URL.

        Args:
            url: URL to cache result for
            result: Result to cache
        """
        if not self.cache_manager:
            return

        cache_key = self.get_cache_key(url)
        await self.cache_manager.set(cache_key, result)

    def format_summary(self, data: Dict[str, Any]) -> str:
        """Format handler result into summary text.

        Args:
            data: Result data from process()

        Returns:
            Formatted markdown summary
        """
        lines = []
        lines.append(f"**Source:** {data.get('source', 'Unknown')}")
        lines.append(f"**URL:** {data.get('url', 'N/A')}")

        # Key points
        key_points = data.get('key_points', [])
        if key_points:
            lines.append("**Key Points:**")
            for point in key_points[:6]:  # Limit to 6 points
                lines.append(f"• {point}")

        # Signals for outreach
        signals = data.get('signals', [])
        if signals:
            lines.append("**Signals for Outreach:**")
            for signal in signals[:4]:  # Limit to 4 signals
                lines.append(f"• {signal}")

        lines.append(f"**Last Checked:** {data.get('last_checked', 'Unknown')}")

        # Join and truncate if needed
        summary = "\n".join(lines)
        if len(summary) > self.max_cell_chars:
            summary = summary[:self.max_cell_chars - 3] + "..."

        return summary

    def create_error_result(self, url: str, error_msg: str) -> Dict[str, Any]:
        """Create error result dictionary.

        Args:
            url: URL that failed
            error_msg: Error message

        Returns:
            Error result dictionary
        """
        parsed = urlparse(url)
        domain = parsed.netloc or 'unknown'

        return {
            'source': domain,
            'url': url,
            'key_points': [f"Processing failed: {error_msg}"],
            'signals': [],
            'status': 'ERROR',
            'error': error_msg,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    def create_skipped_result(self, url: str, reason: str) -> Dict[str, Any]:
        """Create skipped result dictionary.

        Args:
            url: URL that was skipped
            reason: Reason for skipping

        Returns:
            Skipped result dictionary
        """
        parsed = urlparse(url)
        domain = parsed.netloc or 'unknown'

        return {
            'source': domain,
            'url': url,
            'key_points': [f"Skipped: {reason}"],
            'signals': [],
            'status': 'SKIPPED_TOS',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain string
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return 'unknown'

    def truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."