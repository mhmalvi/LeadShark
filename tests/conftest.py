"""
Pytest configuration and shared fixtures for testing.

Provides common test utilities, mock objects, and configuration
for the Google Sheets Prospect Enrichment test suite.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List

from utils.sheets import GoogleSheetsManager
from utils.normalize import URLExtractor
from utils.scoring import LeadScorer
from utils.cache import CacheManager
from handlers.orchestrator import EnrichmentOrchestrator


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        'HEADER_NAMESPACE': 'ENRICH_',
        'MAX_LINK_SUMMARIES': 5,
        'MAX_CELL_CHARS': 4000,
        'MAX_COMBINED_CHARS': 5000,
        'PER_DOMAIN_RPS': 0.2,
        'TIMEOUT_SECONDS': 20,
        'USER_AGENT': 'TestBot/1.0',
        'TWITTER_BEARER': 'test_bearer_token',
        'YOUTUBE_API_KEY': 'test_youtube_key',
        'GITHUB_TOKEN': 'test_github_token'
    }


@pytest.fixture
def mock_sheets_manager():
    """Mock Google Sheets manager."""
    mock = MagicMock(spec=GoogleSheetsManager)
    mock.get_headers = AsyncMock()
    mock.update_headers = AsyncMock()
    mock.get_all_data = AsyncMock()
    mock.update_cells = AsyncMock()
    mock.authenticate = AsyncMock()
    return mock


@pytest.fixture
def url_extractor():
    """Real URL extractor instance for testing."""
    return URLExtractor()


@pytest.fixture
def lead_scorer():
    """Real lead scorer instance for testing."""
    return LeadScorer()


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager."""
    mock = MagicMock(spec=CacheManager)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.clear = AsyncMock()
    return mock


@pytest.fixture
def orchestrator(mock_sheets_manager, url_extractor, lead_scorer, sample_config):
    """Orchestrator instance with mocked dependencies."""
    return EnrichmentOrchestrator(
        sheets_manager=mock_sheets_manager,
        url_extractor=url_extractor,
        lead_scorer=lead_scorer,
        config=sample_config
    )


@pytest.fixture
def sample_sheet_headers() -> List[str]:
    """Sample sheet headers for testing."""
    return [
        'name', 'email', 'company', 'title', 'website',
        'linkedin_url', 'twitter_url', 'github_url'
    ]


@pytest.fixture
def sample_sheet_row() -> List[str]:
    """Sample sheet row data for testing."""
    return [
        'John Doe',
        'john@techcorp.com',
        'TechCorp Solutions',
        'VP Engineering',
        'https://techcorp.com',
        'https://linkedin.com/in/johndoe',
        'https://twitter.com/johndoe',
        'https://github.com/johndoe'
    ]


@pytest.fixture
def sample_managed_columns() -> Dict[str, int]:
    """Sample managed columns mapping for testing."""
    return {
        'ENRICH_LINK_1_SUMMARY': 9,
        'ENRICH_LINK_2_SUMMARY': 10,
        'ENRICH_LINK_3_SUMMARY': 11,
        'ENRICH_LINK_4_SUMMARY': 12,
        'ENRICH_LINK_5_SUMMARY': 13,
        'ENRICH_COMBINED_REPORT': 14,
        'ENRICH_LEAD_SCORE': 15,
        'ENRICH_LEAD_SCORE_NOTES': 16,
        'ENRICH_STATUS': 17,
        'ENRICH_LAST_RUN': 18
    }


@pytest.fixture
def sample_url_results() -> List[Dict[str, Any]]:
    """Sample URL processing results for testing."""
    return [
        {
            'source': 'techcorp.com',
            'url': 'https://techcorp.com',
            'key_points': [
                'Title: TechCorp - Enterprise Solutions',
                'Description: Cloud-based business platform',
                'Features: API integration, automation tools',
                'Recent: Product update announcement'
            ],
            'signals': [
                'Technology-focused company',
                'Has pricing content',
                'Recent activity detected',
                'Enterprise solutions'
            ],
            'status': 'OK',
            'error': None,
            'last_checked': '2024-01-01T12:00:00Z'
        },
        {
            'source': 'Twitter/X',
            'url': 'https://twitter.com/johndoe',
            'key_points': [
                'Name: John Doe (@johndoe)',
                'Bio: VP Engineering at TechCorp',
                'Location: San Francisco',
                'Metrics: 2,500 followers, 850 tweets'
            ],
            'signals': [
                'Good follower count (1k+)',
                'Active on Twitter',
                'Tech industry professional'
            ],
            'status': 'OK',
            'error': None,
            'last_checked': '2024-01-01T12:00:00Z'
        }
    ]


@pytest.fixture
def sample_website_result() -> Dict[str, Any]:
    """Sample website processing result."""
    return {
        'source': 'example.com',
        'url': 'https://example.com',
        'key_points': [
            'Title: Example Corp - Software Solutions',
            'Description: Enterprise software development',
            'Section: About Our Platform',
            'Section: Pricing and Plans'
        ],
        'signals': [
            'Technology-focused company',
            'Has pricing content',
            'Enterprise solutions',
            'Software development'
        ],
        'status': 'OK',
        'error': None,
        'last_checked': '2024-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_twitter_result() -> Dict[str, Any]:
    """Sample Twitter processing result."""
    return {
        'source': 'Twitter/X',
        'url': 'https://twitter.com/testuser',
        'key_points': [
            'Name: Test User (@testuser)',
            'Bio: Software Engineer, AI enthusiast',
            'Metrics: 1,200 followers, 500 tweets',
            'Recent tweet 1: Working on new ML project',
            'Recent tweet 2: Excited about latest AI developments'
        ],
        'signals': [
            'Good follower count (1k+)',
            'Tech industry professional',
            'Recent tweets mention AI'
        ],
        'status': 'OK',
        'error': None,
        'last_checked': '2024-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_skipped_result() -> Dict[str, Any]:
    """Sample skipped processing result (e.g., LinkedIn)."""
    return {
        'source': 'linkedin.com',
        'url': 'https://linkedin.com/in/testuser',
        'key_points': ['Skipped: No LinkedIn API token (ToS compliance)'],
        'signals': [],
        'status': 'SKIPPED_TOS',
        'error': None,
        'last_checked': '2024-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_error_result() -> Dict[str, Any]:
    """Sample error processing result."""
    return {
        'source': 'broken.com',
        'url': 'https://broken.com',
        'key_points': ['Processing failed: Connection timeout'],
        'signals': [],
        'status': 'ERROR',
        'error': 'Connection timeout',
        'last_checked': '2024-01-01T12:00:00Z'
    }


# Test data generators
def create_test_row(name: str, urls: Dict[str, str]) -> List[str]:
    """Create a test row with specific URLs.

    Args:
        name: Person/company name
        urls: Dictionary mapping column types to URLs

    Returns:
        List representing a sheet row
    """
    row = [name, 'test@example.com', 'Test Corp', 'Test Title']
    row.extend([
        urls.get('website', ''),
        urls.get('linkedin', ''),
        urls.get('twitter', ''),
        urls.get('github', ''),
        urls.get('youtube', '')
    ])
    return row


def create_mock_handler_result(
    source: str,
    url: str,
    status: str = 'OK',
    key_points: List[str] = None,
    signals: List[str] = None,
    error: str = None
) -> Dict[str, Any]:
    """Create a mock handler result.

    Args:
        source: Source domain/platform
        url: Original URL
        status: Processing status
        key_points: List of key findings
        signals: List of business signals
        error: Error message if any

    Returns:
        Handler result dictionary
    """
    return {
        'source': source,
        'url': url,
        'key_points': key_points or [],
        'signals': signals or [],
        'status': status,
        'error': error,
        'last_checked': '2024-01-01T12:00:00Z'
    }


# Async test utilities
async def async_noop(*args, **kwargs):
    """Async no-op function for mocking."""
    pass


async def async_return(value):
    """Async function that returns a value."""
    return value


# Test markers
pytest_mark_slow = pytest.mark.slow
pytest_mark_integration = pytest.mark.integration
pytest_mark_unit = pytest.mark.unit