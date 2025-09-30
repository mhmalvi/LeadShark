#!/usr/bin/env python3
"""
API Rate Limiter and Quota Manager
Manages rate limits and quotas for external APIs with caching
"""

import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable
from pathlib import Path
import logging


class APIRateLimiter:
    """
    Rate limiter with quota tracking and caching for external APIs

    Supported APIs:
    - Genderize.io: 500 requests/month
    - EVA Email: Unlimited
    - GitHub: 60/hour (unauth), 5000/hour (auth)
    - Google Search: 100/day
    - LinkedIn Scraping: 1 per 3 seconds
    """

    def __init__(self, cache_dir: str = ".api_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # Rate limit configurations
        self.rate_limits = {
            'genderize': {
                'requests_per_period': 500,
                'period_seconds': 30 * 24 * 3600,  # 30 days (monthly)
                'min_delay': 0.1,
                'cache_ttl': 30 * 24 * 3600,  # Cache for 30 days (names don't change)
            },
            'eva_email': {
                'requests_per_period': None,  # Unlimited
                'period_seconds': None,
                'min_delay': 0.5,
                'cache_ttl': 24 * 3600,  # Cache for 24 hours
            },
            'github': {
                'requests_per_period': 60,  # Unauthenticated
                'period_seconds': 3600,  # 1 hour
                'min_delay': 1.0,
                'cache_ttl': 24 * 3600,  # Cache for 24 hours
            },
            'github_auth': {
                'requests_per_period': 5000,  # Authenticated
                'period_seconds': 3600,  # 1 hour
                'min_delay': 0.1,
                'cache_ttl': 24 * 3600,  # Cache for 24 hours
            },
            'google_search': {
                'requests_per_period': 100,
                'period_seconds': 24 * 3600,  # 1 day
                'min_delay': 2.0,
                'cache_ttl': 7 * 24 * 3600,  # Cache for 7 days
            },
            'linkedin_scrape': {
                'requests_per_period': None,  # No hard limit, just delays
                'period_seconds': None,
                'min_delay': 3.0,  # 3 seconds between requests
                'cache_ttl': 7 * 24 * 3600,  # Cache for 7 days
            }
        }

        # Request tracking
        self.request_history: Dict[str, list] = {}
        self.last_request_time: Dict[str, float] = {}

        # Load request history from disk
        self._load_request_history()

    def can_make_request(self, api_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if we can make a request to the API
        Returns: (can_request, reason_if_not)
        """
        if api_name not in self.rate_limits:
            return True, None

        config = self.rate_limits[api_name]

        # Check quota (if limited)
        if config['requests_per_period'] is not None:
            # Clean old requests
            self._clean_old_requests(api_name, config['period_seconds'])

            # Count recent requests
            recent_requests = len(self.request_history.get(api_name, []))

            if recent_requests >= config['requests_per_period']:
                return False, f"Quota exceeded: {recent_requests}/{config['requests_per_period']}"

        # Check minimum delay
        last_time = self.last_request_time.get(api_name, 0)
        time_since_last = time.time() - last_time

        if time_since_last < config['min_delay']:
            wait_time = config['min_delay'] - time_since_last
            return False, f"Rate limit: wait {wait_time:.1f}s"

        return True, None

    def wait_if_needed(self, api_name: str, max_wait: float = 10.0) -> bool:
        """
        Wait if needed to respect rate limits
        Returns: True if request can proceed, False if max_wait exceeded
        """
        can_request, reason = self.can_make_request(api_name)

        if can_request:
            return True

        if reason and "wait" in reason.lower():
            # Extract wait time
            try:
                wait_time = float(reason.split("wait ")[1].split("s")[0])
                if wait_time <= max_wait:
                    self.logger.info(f"Rate limiting {api_name}: waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    return True
            except:
                pass

        self.logger.warning(f"Cannot make request to {api_name}: {reason}")
        return False

    def record_request(self, api_name: str):
        """Record that a request was made"""
        now = time.time()

        if api_name not in self.request_history:
            self.request_history[api_name] = []

        self.request_history[api_name].append(now)
        self.last_request_time[api_name] = now

        # Save to disk periodically
        self._save_request_history()

    def get_quota_status(self, api_name: str) -> Dict[str, Any]:
        """Get current quota status for an API"""
        if api_name not in self.rate_limits:
            return {'error': 'Unknown API'}

        config = self.rate_limits[api_name]

        if config['requests_per_period'] is None:
            return {
                'api': api_name,
                'quota': 'unlimited',
                'remaining': 'unlimited',
                'min_delay': config['min_delay']
            }

        # Clean and count
        self._clean_old_requests(api_name, config['period_seconds'])
        recent_requests = len(self.request_history.get(api_name, []))

        return {
            'api': api_name,
            'quota': config['requests_per_period'],
            'used': recent_requests,
            'remaining': config['requests_per_period'] - recent_requests,
            'period': f"{config['period_seconds'] / 3600:.0f}h",
            'min_delay': config['min_delay']
        }

    def get_cached_response(self, api_name: str, cache_key: str) -> Optional[Dict]:
        """Get cached API response if available and fresh"""
        cache_file = self._get_cache_file(api_name, cache_key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)

            # Check TTL
            config = self.rate_limits.get(api_name, {})
            ttl = config.get('cache_ttl', 24 * 3600)

            cached_time = cached_data.get('timestamp', 0)
            age = time.time() - cached_time

            if age < ttl:
                self.logger.info(f"Cache hit for {api_name}:{cache_key} (age: {age/3600:.1f}h)")
                return cached_data.get('response')
            else:
                self.logger.info(f"Cache expired for {api_name}:{cache_key} (age: {age/3600:.1f}h)")
                cache_file.unlink()
                return None

        except Exception as e:
            self.logger.error(f"Cache read error: {e}")
            return None

    def cache_response(self, api_name: str, cache_key: str, response: Dict):
        """Cache an API response"""
        cache_file = self._get_cache_file(api_name, cache_key)

        try:
            cache_data = {
                'timestamp': time.time(),
                'api': api_name,
                'cache_key': cache_key,
                'response': response
            }

            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            self.logger.debug(f"Cached response for {api_name}:{cache_key}")

        except Exception as e:
            self.logger.error(f"Cache write error: {e}")

    def make_cached_request(
        self,
        api_name: str,
        cache_key: str,
        request_func: Callable,
        *args,
        **kwargs
    ) -> Optional[Dict]:
        """
        Make a request with automatic caching and rate limiting

        Args:
            api_name: Name of the API
            cache_key: Unique key for caching this request
            request_func: Function to call to make the request
            *args, **kwargs: Arguments to pass to request_func

        Returns:
            API response or None if failed
        """
        # Check cache first
        cached = self.get_cached_response(api_name, cache_key)
        if cached:
            return cached

        # Wait if needed
        if not self.wait_if_needed(api_name):
            return None

        # Make request
        try:
            response = request_func(*args, **kwargs)

            # Record request
            self.record_request(api_name)

            # Cache response
            if response:
                self.cache_response(api_name, cache_key, response)

            return response

        except Exception as e:
            self.logger.error(f"Request failed for {api_name}: {e}")
            return None

    def _clean_old_requests(self, api_name: str, period_seconds: float):
        """Remove requests older than the period"""
        if api_name not in self.request_history:
            return

        cutoff = time.time() - period_seconds
        self.request_history[api_name] = [
            t for t in self.request_history[api_name]
            if t > cutoff
        ]

    def _get_cache_file(self, api_name: str, cache_key: str) -> Path:
        """Get cache file path for a request"""
        # Create subdirectory for API
        api_dir = self.cache_dir / api_name
        api_dir.mkdir(exist_ok=True)

        # Hash the cache key for filename
        key_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return api_dir / f"{key_hash}.json"

    def _load_request_history(self):
        """Load request history from disk"""
        history_file = self.cache_dir / "request_history.json"

        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.request_history = data.get('history', {})
                    self.last_request_time = data.get('last_times', {})

                self.logger.info("Loaded request history from disk")
            except Exception as e:
                self.logger.error(f"Failed to load request history: {e}")

    def _save_request_history(self):
        """Save request history to disk"""
        history_file = self.cache_dir / "request_history.json"

        try:
            data = {
                'history': self.request_history,
                'last_times': self.last_request_time,
                'saved_at': time.time()
            }

            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save request history: {e}")

    def get_all_quota_status(self) -> Dict[str, Dict]:
        """Get quota status for all APIs"""
        return {
            api_name: self.get_quota_status(api_name)
            for api_name in self.rate_limits.keys()
        }

    def clear_cache(self, api_name: Optional[str] = None):
        """Clear cache for specific API or all APIs"""
        if api_name:
            api_dir = self.cache_dir / api_name
            if api_dir.exists():
                for cache_file in api_dir.glob("*.json"):
                    cache_file.unlink()
                self.logger.info(f"Cleared cache for {api_name}")
        else:
            for api_dir in self.cache_dir.iterdir():
                if api_dir.is_dir():
                    for cache_file in api_dir.glob("*.json"):
                        cache_file.unlink()
            self.logger.info("Cleared all caches")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    limiter = APIRateLimiter()

    print("API Rate Limiter Test\n")
    print("=" * 60)

    # Get quota status
    print("\nQuota Status:")
    for api, status in limiter.get_all_quota_status().items():
        print(f"\n{api}:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    # Test caching
    print("\n" + "=" * 60)
    print("Testing cache...")

    def mock_api_call():
        return {'result': 'test data', 'timestamp': time.time()}

    # First call - should hit API
    result1 = limiter.make_cached_request(
        'genderize',
        'test_john',
        mock_api_call
    )
    print(f"First call result: {result1}")

    # Second call - should hit cache
    result2 = limiter.make_cached_request(
        'genderize',
        'test_john',
        mock_api_call
    )
    print(f"Second call result (cached): {result2}")

    # Test rate limiting
    print("\n" + "=" * 60)
    print("Testing rate limiting...")

    for i in range(3):
        can_request, reason = limiter.can_make_request('linkedin_scrape')
        print(f"Request {i+1}: {can_request} - {reason if not can_request else 'OK'}")

        if can_request:
            limiter.record_request('linkedin_scrape')
            print("  Request made")

        time.sleep(1)