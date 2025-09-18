"""
Handlers package for different URL types and platforms.

This package contains specialized handlers for:
- Website scraping (generic)
- Twitter/X API integration
- YouTube API integration
- GitHub API integration
- News article processing
"""

from .website import WebsiteHandler
from .twitter import TwitterHandler
from .youtube import YouTubeHandler
from .github import GitHubHandler
from .news import NewsHandler
from .orchestrator import EnrichmentOrchestrator

__all__ = [
    'WebsiteHandler',
    'TwitterHandler',
    'YouTubeHandler',
    'GitHubHandler',
    'NewsHandler',
    'EnrichmentOrchestrator'
]