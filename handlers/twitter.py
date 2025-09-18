"""
Twitter/X handler for profile and post analysis.

Uses Twitter API v2 to get profile information and recent posts
while respecting ToS. Falls back to skipping if no API token available.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import requests

from .base import BaseHandler
from utils.logging import get_logger

logger = get_logger(__name__)


class TwitterHandler(BaseHandler):
    """Handler for Twitter/X URLs."""

    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize Twitter handler.

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        super().__init__(config, cache_manager)
        self.bearer_token = config.get('TWITTER_BEARER', '')
        self.base_url = "https://api.twitter.com/2"

    @property
    def handler_name(self) -> str:
        """Return handler name."""
        return "twitter"

    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL.

        Args:
            url: URL to check

        Returns:
            True for Twitter/X URLs
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain in [
                'twitter.com', 'www.twitter.com',
                'x.com', 'www.x.com'
            ]
        except Exception:
            return False

    async def process(self, url: str) -> Dict[str, Any]:
        """Process Twitter URL.

        Args:
            url: Twitter URL to process

        Returns:
            Dictionary with profile and post information
        """
        # Check cache first
        cached = await self.get_cached_result(url)
        if cached:
            logger.debug(f"Using cached result for {url}")
            return cached

        # Check if we have API token
        if not self.bearer_token:
            result = self.create_skipped_result(
                url,
                "No Twitter API token (ToS compliance - scraping not allowed)"
            )
            await self.cache_result(url, result)
            return result

        try:
            # Extract username from URL
            username = self._extract_username(url)
            if not username:
                result = self.create_error_result(url, "Could not extract username")
                await self.cache_result(url, result)
                return result

            # Get user data
            user_data = await self._get_user_data(username)
            if not user_data:
                result = self.create_error_result(url, "User not found or API error")
                await self.cache_result(url, result)
                return result

            # Get recent tweets
            tweets = await self._get_recent_tweets(user_data['id'])

            # Process data
            processed_data = self._process_twitter_data(url, user_data, tweets)

            # Cache and return
            await self.cache_result(url, processed_data)
            return processed_data

        except Exception as e:
            logger.error(f"Error processing Twitter URL {url}: {e}")
            result = self.create_error_result(url, str(e))
            await self.cache_result(url, result)
            return result

    def _extract_username(self, url: str) -> Optional[str]:
        """Extract username from Twitter URL.

        Args:
            url: Twitter URL

        Returns:
            Username or None if not found
        """
        # Pattern to match Twitter usernames
        patterns = [
            r'(?:twitter\.com|x\.com)/([^/\?#]+)',
            r'(?:twitter\.com|x\.com)/intent/user\?screen_name=([^&]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                username = match.group(1)
                # Skip non-username paths
                if username.lower() not in [
                    'home', 'explore', 'notifications', 'messages',
                    'bookmarks', 'lists', 'profile', 'more', 'compose',
                    'settings', 'help', 'login', 'signup', 'i', 'search'
                ]:
                    return username.replace('@', '')

        return None

    async def _get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile data from Twitter API.

        Args:
            username: Twitter username

        Returns:
            User data dictionary or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': self.user_agent
            }

            # User fields we want
            user_fields = [
                'id', 'username', 'name', 'description', 'location',
                'public_metrics', 'created_at', 'verified', 'url'
            ]

            params = {
                'user.fields': ','.join(user_fields)
            }

            url = f"{self.base_url}/users/by/username/{username}"

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data')
            else:
                logger.warning(f"Twitter API error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error fetching Twitter user data: {e}")
            return None

    async def _get_recent_tweets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent tweets from user.

        Args:
            user_id: Twitter user ID

        Returns:
            List of recent tweets
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': self.user_agent
            }

            # Tweet fields we want
            tweet_fields = [
                'id', 'text', 'created_at', 'public_metrics',
                'context_annotations', 'lang'
            ]

            params = {
                'tweet.fields': ','.join(tweet_fields),
                'max_results': '10',  # Get 10 most recent tweets
                'exclude': 'retweets'  # Exclude retweets
            }

            url = f"{self.base_url}/users/{user_id}/tweets"

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                logger.warning(f"Twitter API error for tweets {response.status_code}: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching Twitter tweets: {e}")
            return []

    def _process_twitter_data(
        self,
        url: str,
        user_data: Dict[str, Any],
        tweets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process Twitter user and tweet data.

        Args:
            url: Original URL
            user_data: User profile data
            tweets: Recent tweets

        Returns:
            Processed data dictionary
        """
        key_points = []
        signals = []

        # Profile information
        name = user_data.get('name', '')
        username = user_data.get('username', '')
        bio = user_data.get('description', '')
        location = user_data.get('location', '')

        if name:
            key_points.append(f"Name: {name} (@{username})")

        if bio:
            key_points.append(f"Bio: {self.truncate_text(bio, 120)}")

        if location:
            key_points.append(f"Location: {location}")

        # Metrics
        metrics = user_data.get('public_metrics', {})
        followers = metrics.get('followers_count', 0)
        following = metrics.get('following_count', 0)
        tweet_count = metrics.get('tweet_count', 0)

        key_points.append(f"Metrics: {followers:,} followers, {tweet_count:,} tweets")

        # Account signals
        if user_data.get('verified'):
            signals.append("Verified account")

        if followers > 10000:
            signals.append("High follower count (10k+)")
        elif followers > 1000:
            signals.append("Good follower count (1k+)")

        # Analyze recent tweets
        recent_tweet_texts = []
        for tweet in tweets[:3]:  # Top 3 tweets
            text = tweet.get('text', '').strip()
            if text and not text.startswith('RT @'):  # Skip retweets
                # Clean up tweet text
                text = re.sub(r'http[s]?://\S+', '[URL]', text)  # Replace URLs
                text = re.sub(r'@\w+', '[USER]', text)  # Replace mentions
                recent_tweet_texts.append(self.truncate_text(text, 80))

        if recent_tweet_texts:
            for i, tweet_text in enumerate(recent_tweet_texts, 1):
                key_points.append(f"Recent tweet {i}: {tweet_text}")

            # Look for business signals in tweets
            all_tweet_text = ' '.join([t.get('text', '') for t in tweets]).lower()

            business_keywords = [
                'hiring', 'job', 'position', 'team', 'launch', 'product',
                'announcement', 'partnership', 'funding', 'growth'
            ]

            for keyword in business_keywords:
                if keyword in all_tweet_text:
                    signals.append(f"Recent tweets mention {keyword}")

            # Activity level
            if len(tweets) >= 5:
                signals.append("Active on Twitter (5+ recent tweets)")

        return {
            'source': 'Twitter/X',
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }