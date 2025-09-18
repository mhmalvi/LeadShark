"""
URL extraction and normalization utilities.

Handles URL discovery from spreadsheet cells, normalization,
deduplication, and classification for proper handler routing.
"""

import re
from typing import List, Set, Dict, Tuple, Optional
from urllib.parse import urlparse, urlunparse, urljoin

import tldextract

from .logging import get_logger

logger = get_logger(__name__)


class URLExtractor:
    """Extracts and normalizes URLs from spreadsheet data."""

    def __init__(self):
        """Initialize URL extractor."""
        # URL detection patterns
        self.url_patterns = [
            # Standard HTTP/HTTPS URLs
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            # URLs without protocol
            r'(?:www\.)?[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.(?:[a-zA-Z]{2,}|xn--[a-zA-Z0-9]+)(?:/[^\s<>"{}|\\^`\[\]]*)?',
        ]

        # Column name patterns that likely contain URLs
        self.url_column_patterns = [
            r'.*link.*', r'.*url.*', r'.*website.*', r'.*site.*',
            r'.*twitter.*', r'.*x\.com.*', r'.*youtube.*', r'.*github.*',
            r'.*social.*', r'.*profile.*', r'.*portfolio.*', r'.*company.*'
        ]

        # URL separators for multi-URL cells
        self.url_separators = [',', '|', '\n', '\r\n', ';', ' ']

    async def extract_urls_from_row(self, headers: List[str], row: List[str]) -> List[str]:
        """Extract and normalize URLs from a spreadsheet row.

        Args:
            headers: Column headers
            row: Row data

        Returns:
            List of normalized, deduplicated URLs
        """
        all_urls = []

        # Find URL candidate columns
        url_columns = self._identify_url_columns(headers, row)

        # Extract URLs from identified columns
        for col_index in url_columns:
            if col_index < len(row):
                cell_value = row[col_index]
                if cell_value and cell_value.strip():
                    cell_urls = self._extract_urls_from_cell(cell_value)
                    all_urls.extend(cell_urls)

        # Normalize and deduplicate
        normalized_urls = []
        for url in all_urls:
            normalized = self._normalize_url(url)
            if normalized:
                normalized_urls.append(normalized)

        # Deduplicate by (scheme, host, path)
        unique_urls = self._deduplicate_urls(normalized_urls)

        logger.debug(f"Extracted {len(unique_urls)} unique URLs from row")
        return unique_urls

    def _identify_url_columns(self, headers: List[str], row: List[str]) -> List[int]:
        """Identify columns that likely contain URLs.

        Args:
            headers: Column headers
            row: Row data

        Returns:
            List of column indices
        """
        url_columns = []

        for i, header in enumerate(headers):
            if not header:
                continue

            header_lower = header.lower().strip()

            # Check header name patterns
            is_url_header = any(
                re.match(pattern, header_lower, re.IGNORECASE)
                for pattern in self.url_column_patterns
            )

            # Check cell content for URLs (if header doesn't match)
            has_url_content = False
            if not is_url_header and i < len(row):
                cell_value = row[i]
                if cell_value and self._contains_url(cell_value):
                    has_url_content = True

            if is_url_header or has_url_content:
                url_columns.append(i)

        return url_columns

    def _contains_url(self, text: str) -> bool:
        """Check if text contains URLs.

        Args:
            text: Text to check

        Returns:
            True if text contains URLs
        """
        if not text or len(text) < 4:
            return False

        # Quick check for common URL indicators
        url_indicators = ['http://', 'https://', 'www.', '.com', '.org', '.net']
        return any(indicator in text.lower() for indicator in url_indicators)

    def _extract_urls_from_cell(self, cell_value: str) -> List[str]:
        """Extract URLs from a single cell.

        Args:
            cell_value: Cell content

        Returns:
            List of URLs found in cell
        """
        if not cell_value or not cell_value.strip():
            return []

        urls = []

        # Split by common separators first
        parts = [cell_value]
        for separator in self.url_separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(separator))
            parts = new_parts

        # Extract URLs from each part
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Try regex patterns
            for pattern in self.url_patterns:
                matches = re.findall(pattern, part, re.IGNORECASE)
                urls.extend(matches)

            # If no regex match but looks like a domain, try to construct URL
            if not any(re.search(pattern, part, re.IGNORECASE) for pattern in self.url_patterns):
                if self._looks_like_domain(part):
                    # Add protocol if missing
                    if not part.startswith(('http://', 'https://')):
                        urls.append(f"https://{part}")
                    else:
                        urls.append(part)

        return urls

    def _looks_like_domain(self, text: str) -> bool:
        """Check if text looks like a domain name.

        Args:
            text: Text to check

        Returns:
            True if text looks like a domain
        """
        if not text or len(text) < 4:
            return False

        # Remove common prefixes
        text = text.lower().strip()
        if text.startswith('www.'):
            text = text[4:]

        # Check for valid domain pattern
        domain_pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.(?:[a-zA-Z]{2,}|xn--[a-zA-Z0-9]+)(?:/.*)?$'
        return bool(re.match(domain_pattern, text))

    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize a URL.

        Args:
            url: Raw URL

        Returns:
            Normalized URL or None if invalid
        """
        if not url or not url.strip():
            return None

        url = url.strip()

        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                if url.startswith('//'):
                    url = 'https:' + url
                else:
                    url = 'https://' + url

            # Parse and validate
            parsed = urlparse(url)

            if not parsed.netloc:
                return None

            # Normalize components
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path

            # Remove common tracking parameters
            query = self._clean_query_params(parsed.query)

            # Remove fragment (anchor)
            fragment = ''

            # Reconstruct URL
            normalized = urlunparse((
                scheme, netloc, path, parsed.params, query, fragment
            ))

            return normalized

        except Exception as e:
            logger.debug(f"Error normalizing URL '{url}': {e}")
            return None

    def _clean_query_params(self, query: str) -> str:
        """Remove tracking and unnecessary query parameters.

        Args:
            query: Query string

        Returns:
            Cleaned query string
        """
        if not query:
            return ''

        # Parameters to remove (tracking, analytics, etc.)
        remove_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'gclid', 'fbclid', 'msclkid', 'ref', 'referrer', 'source',
            '_ga', '_gid', 'mc_cid', 'mc_eid', 'ck_subscriber_id'
        }

        try:
            from urllib.parse import parse_qs, urlencode

            params = parse_qs(query, keep_blank_values=True)
            cleaned_params = {}

            for key, values in params.items():
                if key.lower() not in remove_params:
                    cleaned_params[key] = values

            return urlencode(cleaned_params, doseq=True)

        except Exception:
            # If parsing fails, return original query
            return query

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Deduplicate URLs by (scheme, host, path).

        Args:
            urls: List of URLs

        Returns:
            Deduplicated list of URLs
        """
        seen = set()
        unique_urls = []

        for url in urls:
            try:
                parsed = urlparse(url)
                # Create key from scheme, host, and path
                key = (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path)

                if key not in seen:
                    seen.add(key)
                    unique_urls.append(url)

            except Exception as e:
                logger.debug(f"Error deduplicating URL '{url}': {e}")
                # If parsing fails, just check exact match
                if url not in unique_urls:
                    unique_urls.append(url)

        return unique_urls

    def classify_url(self, url: str) -> Dict[str, str]:
        """Classify URL by platform/type.

        Args:
            url: URL to classify

        Returns:
            Dictionary with classification info
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Platform-specific classifications
            if 'linkedin.com' in domain:
                return {'platform': 'linkedin', 'type': 'social', 'handler': 'forbidden'}

            elif domain in ['twitter.com', 'x.com'] or 'twitter.com' in domain or 'x.com' in domain:
                return {'platform': 'twitter', 'type': 'social', 'handler': 'twitter'}

            elif 'youtube.com' in domain or 'youtu.be' in domain:
                return {'platform': 'youtube', 'type': 'video', 'handler': 'youtube'}

            elif 'github.com' in domain:
                return {'platform': 'github', 'type': 'code', 'handler': 'github'}

            # News/blog detection
            elif self._is_news_site(domain):
                return {'platform': domain, 'type': 'news', 'handler': 'news'}

            else:
                return {'platform': domain, 'type': 'website', 'handler': 'website'}

        except Exception as e:
            logger.debug(f"Error classifying URL '{url}': {e}")
            return {'platform': 'unknown', 'type': 'website', 'handler': 'website'}

    def _is_news_site(self, domain: str) -> bool:
        """Check if domain is a news/blog site.

        Args:
            domain: Domain to check

        Returns:
            True if appears to be a news site
        """
        news_indicators = [
            'news', 'blog', 'post', 'article', 'press', 'media',
            'techcrunch', 'venturebeat', 'wired', 'theverge',
            'reuters', 'bloomberg', 'wsj', 'nytimes', 'forbes'
        ]

        return any(indicator in domain for indicator in news_indicators)

    def extract_domain_info(self, url: str) -> Dict[str, str]:
        """Extract detailed domain information.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with domain info
        """
        try:
            parsed = urlparse(url)
            extracted = tldextract.extract(url)

            return {
                'full_domain': parsed.netloc.lower(),
                'domain': extracted.domain,
                'subdomain': extracted.subdomain,
                'suffix': extracted.suffix,
                'registered_domain': extracted.registered_domain,
                'scheme': parsed.scheme.lower(),
                'path': parsed.path
            }

        except Exception as e:
            logger.debug(f"Error extracting domain info from '{url}': {e}")
            return {
                'full_domain': 'unknown',
                'domain': 'unknown',
                'subdomain': '',
                'suffix': '',
                'registered_domain': 'unknown',
                'scheme': 'https',
                'path': '/'
            }