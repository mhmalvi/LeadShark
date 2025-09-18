"""
YouTube handler for channel analysis.

Uses YouTube Data API v3 to get channel information and recent videos.
Falls back to skipping if no API key available.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

import requests

from .base import BaseHandler
from utils.logging import get_logger

logger = get_logger(__name__)


class YouTubeHandler(BaseHandler):
    """Handler for YouTube URLs."""

    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize YouTube handler.

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        super().__init__(config, cache_manager)
        self.api_key = config.get('YOUTUBE_API_KEY', '')
        self.base_url = "https://www.googleapis.com/youtube/v3"

    @property
    def handler_name(self) -> str:
        """Return handler name."""
        return "youtube"

    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL.

        Args:
            url: URL to check

        Returns:
            True for YouTube URLs
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain in [
                'youtube.com', 'www.youtube.com',
                'youtu.be', 'm.youtube.com'
            ]
        except Exception:
            return False

    async def process(self, url: str) -> Dict[str, Any]:
        """Process YouTube URL.

        Args:
            url: YouTube URL to process

        Returns:
            Dictionary with channel and video information
        """
        # Check cache first
        cached = await self.get_cached_result(url)
        if cached:
            logger.debug(f"Using cached result for {url}")
            return cached

        # Check if we have API key
        if not self.api_key:
            result = self.create_skipped_result(
                url,
                "No YouTube API key available"
            )
            await self.cache_result(url, result)
            return result

        try:
            # Extract channel ID or username
            channel_info = self._extract_channel_info(url)
            if not channel_info:
                result = self.create_error_result(url, "Could not extract channel information")
                await self.cache_result(url, result)
                return result

            # Get channel data
            channel_data = await self._get_channel_data(channel_info)
            if not channel_data:
                result = self.create_error_result(url, "Channel not found or API error")
                await self.cache_result(url, result)
                return result

            # Get recent videos
            videos = await self._get_recent_videos(channel_data['id'])

            # Process data
            processed_data = self._process_youtube_data(url, channel_data, videos)

            # Cache and return
            await self.cache_result(url, processed_data)
            return processed_data

        except Exception as e:
            logger.error(f"Error processing YouTube URL {url}: {e}")
            result = self.create_error_result(url, str(e))
            await self.cache_result(url, result)
            return result

    def _extract_channel_info(self, url: str) -> Optional[Dict[str, str]]:
        """Extract channel ID or username from YouTube URL.

        Args:
            url: YouTube URL

        Returns:
            Dictionary with 'type' and 'value' or None if not found
        """
        # Channel ID pattern
        channel_id_match = re.search(r'/channel/([a-zA-Z0-9_-]+)', url)
        if channel_id_match:
            return {'type': 'id', 'value': channel_id_match.group(1)}

        # Custom username pattern
        user_match = re.search(r'/(?:user/|@)([a-zA-Z0-9_.-]+)', url)
        if user_match:
            username = user_match.group(1)
            return {'type': 'username', 'value': username}

        # Handle /c/ pattern (custom URL)
        c_match = re.search(r'/c/([a-zA-Z0-9_.-]+)', url)
        if c_match:
            return {'type': 'username', 'value': c_match.group(1)}

        # Try to extract from video URL and get channel from there
        video_id = self._extract_video_id(url)
        if video_id:
            return {'type': 'video', 'value': video_id}

        return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.

        Args:
            url: YouTube URL

        Returns:
            Video ID or None if not found
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def _get_channel_data(self, channel_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get channel data from YouTube API.

        Args:
            channel_info: Dictionary with channel type and value

        Returns:
            Channel data dictionary or None if failed
        """
        try:
            params = {
                'part': 'snippet,statistics,brandingSettings',
                'key': self.api_key
            }

            if channel_info['type'] == 'id':
                params['id'] = channel_info['value']
            elif channel_info['type'] == 'username':
                params['forUsername'] = channel_info['value']
            elif channel_info['type'] == 'video':
                # First get channel ID from video
                video_data = await self._get_video_data(channel_info['value'])
                if not video_data:
                    return None
                params['id'] = video_data.get('snippet', {}).get('channelId')
                if not params['id']:
                    return None

            url = f"{self.base_url}/channels"

            response = requests.get(
                url,
                params=params,
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                return items[0] if items else None
            else:
                logger.warning(f"YouTube API error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error fetching YouTube channel data: {e}")
            return None

    async def _get_video_data(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video data to extract channel ID.

        Args:
            video_id: YouTube video ID

        Returns:
            Video data or None if failed
        """
        try:
            params = {
                'part': 'snippet',
                'id': video_id,
                'key': self.api_key
            }

            url = f"{self.base_url}/videos"

            response = requests.get(
                url,
                params=params,
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                return items[0] if items else None

            return None

        except Exception as e:
            logger.error(f"Error fetching YouTube video data: {e}")
            return None

    async def _get_recent_videos(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get recent videos from channel.

        Args:
            channel_id: YouTube channel ID

        Returns:
            List of recent videos
        """
        try:
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'order': 'date',
                'maxResults': '5',  # Get 5 most recent videos
                'type': 'video',
                'key': self.api_key
            }

            url = f"{self.base_url}/search"

            response = requests.get(
                url,
                params=params,
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                logger.warning(f"YouTube API error for videos {response.status_code}: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {e}")
            return []

    def _process_youtube_data(
        self,
        url: str,
        channel_data: Dict[str, Any],
        videos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process YouTube channel and video data.

        Args:
            url: Original URL
            channel_data: Channel data from API
            videos: Recent videos

        Returns:
            Processed data dictionary
        """
        key_points = []
        signals = []

        # Channel information
        snippet = channel_data.get('snippet', {})
        statistics = channel_data.get('statistics', {})

        channel_title = snippet.get('title', '')
        description = snippet.get('description', '')
        custom_url = snippet.get('customUrl', '')

        if channel_title:
            key_points.append(f"Channel: {channel_title}")

        if custom_url:
            key_points.append(f"Handle: {custom_url}")

        if description:
            # Take first sentence or 100 chars
            desc_short = description.split('.')[0][:100]
            key_points.append(f"About: {self.truncate_text(desc_short, 100)}")

        # Statistics
        subscriber_count = int(statistics.get('subscriberCount', 0))
        video_count = int(statistics.get('videoCount', 0))
        view_count = int(statistics.get('viewCount', 0))

        if subscriber_count > 0:
            key_points.append(f"Subscribers: {self._format_number(subscriber_count)}")

        key_points.append(f"Videos: {video_count:,}, Views: {self._format_number(view_count)}")

        # Channel signals
        if subscriber_count > 100000:
            signals.append("Large channel (100k+ subscribers)")
        elif subscriber_count > 10000:
            signals.append("Medium channel (10k+ subscribers)")
        elif subscriber_count > 1000:
            signals.append("Growing channel (1k+ subscribers)")

        if video_count > 50:
            signals.append("Active content creator (50+ videos)")

        # Analyze recent videos
        recent_titles = []
        for video in videos[:3]:  # Top 3 videos
            video_snippet = video.get('snippet', {})
            title = video_snippet.get('title', '').strip()
            if title:
                recent_titles.append(self.truncate_text(title, 60))

        if recent_titles:
            for i, title in enumerate(recent_titles, 1):
                key_points.append(f"Recent video {i}: {title}")

            # Look for business signals in video titles
            all_titles = ' '.join(recent_titles).lower()

            business_keywords = [
                'tutorial', 'how to', 'review', 'tips', 'guide',
                'business', 'marketing', 'strategy', 'course',
                'launch', 'announcement', 'new'
            ]

            found_keywords = [kw for kw in business_keywords if kw in all_titles]
            if found_keywords:
                signals.append(f"Content themes: {', '.join(found_keywords[:3])}")

            # Check video recency
            if videos:
                latest_video = videos[0]
                published = latest_video.get('snippet', {}).get('publishedAt', '')
                if published:
                    try:
                        pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        days_ago = (datetime.now(timezone.utc) - pub_date).days

                        if days_ago <= 7:
                            signals.append("Very recent activity (within 7 days)")
                        elif days_ago <= 30:
                            signals.append("Recent activity (within 30 days)")

                    except Exception:
                        pass

        return {
            'source': 'YouTube',
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    def _format_number(self, num: int) -> str:
        """Format large numbers with K/M suffixes.

        Args:
            num: Number to format

        Returns:
            Formatted number string
        """
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return f"{num:,}"