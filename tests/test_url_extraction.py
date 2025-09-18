"""
Tests for URL extraction and normalization functionality.

Tests URL discovery from cells, multi-URL handling, deduplication,
and normalization according to specifications.
"""

import pytest
from utils.normalize import URLExtractor


class TestURLExtraction:
    """Test URL extraction and normalization."""

    def setup_method(self):
        """Setup for each test."""
        self.extractor = URLExtractor()

    def test_single_url_extraction(self):
        """Test extracting single URL from cell."""
        headers = ['name', 'website', 'email']
        row = ['John Doe', 'https://example.com', 'john@example.com']

        urls = self.extractor._extract_urls_from_cell('https://example.com')
        assert len(urls) == 1
        assert urls[0] == 'https://example.com'

    def test_multi_url_extraction_comma_separated(self):
        """Test extracting multiple URLs separated by commas."""
        cell_value = 'https://example.com, https://twitter.com/john, https://github.com/john'
        urls = self.extractor._extract_urls_from_cell(cell_value)

        assert len(urls) == 3
        assert 'https://example.com' in urls
        assert 'https://twitter.com/john' in urls
        assert 'https://github.com/john' in urls

    def test_multi_url_extraction_various_separators(self):
        """Test extracting URLs with different separators."""
        test_cases = [
            'https://example.com | https://twitter.com/john',
            'https://example.com\nhttps://github.com/john',
            'https://example.com; https://youtube.com/channel/123',
            'https://example.com https://linkedin.com/in/john'
        ]

        for cell_value in test_cases:
            urls = self.extractor._extract_urls_from_cell(cell_value)
            assert len(urls) >= 2, f"Failed for: {cell_value}"

    def test_url_normalization(self):
        """Test URL normalization functionality."""
        test_cases = [
            ('example.com', 'https://example.com'),
            ('www.example.com', 'https://www.example.com'),
            ('http://example.com', 'http://example.com'),
            ('https://example.com/', 'https://example.com/'),
            ('Example.Com', 'https://example.com'),
        ]

        for input_url, expected in test_cases:
            normalized = self.extractor._normalize_url(input_url)
            assert normalized == expected, f"Failed for {input_url}: got {normalized}, expected {expected}"

    def test_url_deduplication(self):
        """Test URL deduplication by (scheme, host, path)."""
        urls = [
            'https://example.com',
            'https://example.com/',
            'https://example.com?utm_source=test',
            'http://example.com',  # Different scheme
            'https://www.example.com'  # Different host
        ]

        # First normalize
        normalized_urls = []
        for url in urls:
            normalized = self.extractor._normalize_url(url)
            if normalized:
                normalized_urls.append(normalized)

        # Then deduplicate
        unique_urls = self.extractor._deduplicate_urls(normalized_urls)

        # Should have 4 unique URLs (different scheme, host combinations)
        assert len(unique_urls) == 4

    def test_query_parameter_cleaning(self):
        """Test removal of tracking parameters."""
        url_with_tracking = 'https://example.com/page?utm_source=twitter&utm_campaign=test&id=123'
        normalized = self.extractor._normalize_url(url_with_tracking)

        # Should remove utm parameters but keep id
        assert 'utm_source' not in normalized
        assert 'utm_campaign' not in normalized
        assert 'id=123' in normalized

    def test_url_column_identification(self):
        """Test automatic identification of URL columns."""
        headers = ['name', 'website_url', 'twitter_profile', 'email', 'company_site']
        row = ['John', 'https://example.com', 'https://twitter.com/john', 'john@example.com', 'corp.com']

        url_columns = self.extractor._identify_url_columns(headers, row)

        # Should identify columns 1, 2, 4 (0-based: website_url, twitter_profile, company_site)
        expected_columns = [1, 2, 4]
        assert set(url_columns) == set(expected_columns)

    @pytest.mark.asyncio
    async def test_row_url_extraction_integration(self):
        """Test complete row URL extraction workflow."""
        headers = ['name', 'website', 'social_links', 'email']
        row = [
            'John Doe',
            'https://johndoe.com',
            'https://twitter.com/john, https://github.com/john',
            'john@johndoe.com'
        ]

        urls = await self.extractor.extract_urls_from_row(headers, row)

        # Should extract 3 URLs and deduplicate
        assert len(urls) == 3
        assert 'https://johndoe.com' in urls
        assert any('twitter.com' in url for url in urls)
        assert any('github.com' in url for url in urls)

    def test_domain_without_protocol(self):
        """Test handling domains without protocol."""
        test_cases = [
            'example.com',
            'www.github.com',
            'subdomain.example.org',
            'company.co.uk'
        ]

        for domain in test_cases:
            normalized = self.extractor._normalize_url(domain)
            assert normalized.startswith('https://'), f"Failed for {domain}: {normalized}"
            assert domain.lower() in normalized.lower()

    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        invalid_urls = [
            '',
            'not-a-url',
            'ftp://example.com',  # Unsupported scheme
            'javascript:alert(1)',  # Dangerous scheme
            'http://',  # Incomplete
            'https://.'  # Invalid domain
        ]

        for invalid_url in invalid_urls:
            normalized = self.extractor._normalize_url(invalid_url)
            # Should either normalize to valid URL or return None
            if normalized:
                assert normalized.startswith(('http://', 'https://'))

    def test_url_classification(self):
        """Test URL platform classification."""
        test_cases = [
            ('https://twitter.com/john', 'twitter'),
            ('https://x.com/john', 'twitter'),
            ('https://github.com/john/repo', 'github'),
            ('https://youtube.com/channel/123', 'youtube'),
            ('https://linkedin.com/in/john', 'linkedin'),
            ('https://example.com', 'website'),
            ('https://techcrunch.com/article/123', 'news')
        ]

        for url, expected_handler in test_cases:
            classification = self.extractor.classify_url(url)
            assert classification['handler'] == expected_handler, f"Failed for {url}"

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty and whitespace
        assert self.extractor._extract_urls_from_cell('') == []
        assert self.extractor._extract_urls_from_cell('   ') == []

        # Very long URLs
        long_url = 'https://example.com/' + 'a' * 1000
        urls = self.extractor._extract_urls_from_cell(long_url)
        assert len(urls) == 1

        # Mixed content
        mixed_content = 'Check out my website https://example.com and follow me on Twitter!'
        urls = self.extractor._extract_urls_from_cell(mixed_content)
        assert len(urls) == 1
        assert 'https://example.com' in urls

    def test_international_domains(self):
        """Test handling of international domain names."""
        international_domains = [
            'münchen.de',
            'пример.рф',
            'example.中国'
        ]

        for domain in international_domains:
            # Should handle gracefully (may not normalize perfectly but shouldn't crash)
            try:
                normalized = self.extractor._normalize_url(domain)
                if normalized:
                    assert isinstance(normalized, str)
            except Exception as e:
                pytest.fail(f"Failed to handle international domain {domain}: {e}")

    def test_subdomain_extraction(self):
        """Test extraction of domain information including subdomains."""
        test_cases = [
            ('https://www.example.com', 'www', 'example', 'com'),
            ('https://blog.company.co.uk', 'blog', 'company', 'co.uk'),
            ('https://api.v2.service.io', 'api.v2', 'service', 'io')
        ]

        for url, expected_subdomain, expected_domain, expected_suffix in test_cases:
            domain_info = self.extractor.extract_domain_info(url)
            assert domain_info['subdomain'] == expected_subdomain
            assert domain_info['domain'] == expected_domain
            assert domain_info['suffix'] == expected_suffix