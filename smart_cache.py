#!/usr/bin/env python3
"""
💾 Smart Cache System for API Cost Optimization

Provides intelligent caching with TTL for different data types:
- AI analysis: 30 days (company data is stable)
- Email verification: 30 days
- Google/GitHub: 7 days
- Personalization: 14 days

Expected savings: 60-80% reduction in API costs
"""

import os
import json
import time
import hashlib
import logging
from typing import Any, Optional, Dict
from pathlib import Path


class SmartCache:
    """
    Intelligent caching system with configurable TTL per cache type

    Cache Types:
    - ai_analysis: Claude/GPT business analysis (30 day TTL)
    - email_verification: Email validation results (30 day TTL)
    - google_search: Company info from Google (7 day TTL)
    - github: GitHub profile data (7 day TTL)
    - personalization: Cold outreach hooks (14 day TTL)
    - email_sequences: AI-generated email sequences (14 day TTL)
    """

    def __init__(self, cache_dir: str = '.api_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache TTL in seconds
        self.ttl = {
            'ai_analysis': 30 * 24 * 3600,      # 30 days - company data stable
            'email_verification': 30 * 24 * 3600,  # 30 days
            'google_search': 7 * 24 * 3600,     # 7 days
            'github': 7 * 24 * 3600,            # 7 days
            'personalization': 14 * 24 * 3600, # 14 days
            'email_sequences': 14 * 24 * 3600, # 14 days
            'genderize': 90 * 24 * 3600,       # 90 days - very stable
            'eva_email': 30 * 24 * 3600,       # 30 days
        }

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'errors': 0
        }

        self.logger = logging.getLogger(__name__)

    def _get_cache_key(self, key: str, cache_type: str) -> str:
        """
        Generate cache key hash from input

        Args:
            key: Unique identifier (e.g., company domain, email address)
            cache_type: Type of cache (ai_analysis, email_verification, etc.)

        Returns:
            MD5 hash of the key
        """
        key_str = f"{cache_type}:{str(key)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str, cache_type: str) -> Path:
        """Get file path for cache entry"""
        type_dir = self.cache_dir / cache_type
        type_dir.mkdir(exist_ok=True)
        return type_dir / f"{cache_key}.json"

    def get(self, key: str, cache_type: str) -> Optional[Any]:
        """
        Retrieve cached result if valid

        Args:
            key: Cache lookup key (e.g., 'example.com', 'john@example.com')
            cache_type: Type of cache to check

        Returns:
            Cached data if valid, None if expired or not found
        """
        try:
            cache_key = self._get_cache_key(key, cache_type)
            cache_file = self._get_cache_path(cache_key, cache_type)

            if not cache_file.exists():
                self.stats['misses'] += 1
                return None

            # Read cache file
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check TTL
            age = time.time() - cached['timestamp']
            ttl = self.ttl.get(cache_type, 7 * 24 * 3600)  # Default 7 days

            if age > ttl:
                self.stats['expired'] += 1
                self.logger.debug(f"Cache expired for {cache_type}:{key} (age: {age/3600:.1f}h, TTL: {ttl/3600:.1f}h)")
                return None

            self.stats['hits'] += 1
            self.logger.debug(f"Cache HIT for {cache_type}:{key} (age: {age/3600:.1f}h)")
            return cached['data']

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.warning(f"Cache read error for {cache_type}:{key}: {e}")
            return None

    def set(self, key: str, value: Any, cache_type: str) -> bool:
        """
        Store data in cache

        Args:
            key: Cache key (e.g., 'example.com', 'john@example.com')
            value: Data to cache (must be JSON-serializable)
            cache_type: Type of cache

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._get_cache_key(key, cache_type)
            cache_file = self._get_cache_path(cache_key, cache_type)

            # Prepare cache entry
            cache_entry = {
                'timestamp': time.time(),
                'cache_type': cache_type,
                'key': str(key),
                'data': value
            }

            # Write to file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Cache WRITE for {cache_type}:{key}")
            return True

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.warning(f"Cache write error for {cache_type}:{key}: {e}")
            return False

    def delete(self, key: str, cache_type: str) -> bool:
        """
        Delete a cache entry

        Args:
            key: Cache key to delete
            cache_type: Type of cache

        Returns:
            True if deleted, False if not found or error
        """
        try:
            cache_key = self._get_cache_key(key, cache_type)
            cache_file = self._get_cache_path(cache_key, cache_type)

            if cache_file.exists():
                cache_file.unlink()
                self.logger.debug(f"Cache DELETED for {cache_type}:{key}")
                return True
            return False

        except Exception as e:
            self.logger.warning(f"Cache delete error for {cache_type}:{key}: {e}")
            return False

    def clear_type(self, cache_type: str) -> int:
        """
        Clear all cache entries of a specific type

        Args:
            cache_type: Type of cache to clear

        Returns:
            Number of entries deleted
        """
        try:
            type_dir = self.cache_dir / cache_type
            if not type_dir.exists():
                return 0

            count = 0
            for cache_file in type_dir.glob('*.json'):
                cache_file.unlink()
                count += 1

            self.logger.info(f"Cleared {count} entries from {cache_type} cache")
            return count

        except Exception as e:
            self.logger.warning(f"Error clearing {cache_type} cache: {e}")
            return 0

    def clear_expired(self) -> int:
        """
        Delete all expired cache entries across all types

        Returns:
            Number of expired entries deleted
        """
        count = 0
        try:
            for cache_type in self.ttl.keys():
                type_dir = self.cache_dir / cache_type
                if not type_dir.exists():
                    continue

                ttl = self.ttl[cache_type]
                current_time = time.time()

                for cache_file in type_dir.glob('*.json'):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached = json.load(f)

                        age = current_time - cached['timestamp']
                        if age > ttl:
                            cache_file.unlink()
                            count += 1
                    except:
                        pass  # Skip invalid files

            self.logger.info(f"Cleared {count} expired cache entries")
            return count

        except Exception as e:
            self.logger.warning(f"Error clearing expired cache: {e}")
            return count

    def get_stats(self) -> Dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache performance metrics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'expired': self.stats['expired'],
            'errors': self.stats['errors'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 1),
            'estimated_api_calls_saved': self.stats['hits']
        }

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'errors': 0
        }

    def get_cache_size(self) -> Dict:
        """
        Get size of cache by type

        Returns:
            Dictionary with entry counts per cache type
        """
        sizes = {}
        try:
            for cache_type in self.ttl.keys():
                type_dir = self.cache_dir / cache_type
                if type_dir.exists():
                    sizes[cache_type] = len(list(type_dir.glob('*.json')))
                else:
                    sizes[cache_type] = 0

            sizes['total'] = sum(sizes.values())
            return sizes

        except Exception as e:
            self.logger.warning(f"Error getting cache size: {e}")
            return {'error': str(e)}


# Convenience functions for common cache operations

def get_cached_ai_analysis(company_domain: str, cache: SmartCache) -> Optional[Dict]:
    """Get cached AI analysis for a company"""
    return cache.get(company_domain, 'ai_analysis')


def cache_ai_analysis(company_domain: str, analysis: Dict, cache: SmartCache) -> bool:
    """Cache AI analysis result"""
    return cache.set(company_domain, analysis, 'ai_analysis')


def get_cached_email_verification(email: str, cache: SmartCache) -> Optional[Dict]:
    """Get cached email verification result"""
    return cache.get(email, 'email_verification')


def cache_email_verification(email: str, result: Dict, cache: SmartCache) -> bool:
    """Cache email verification result"""
    return cache.set(email, result, 'email_verification')


def get_cached_company_info(domain: str, cache: SmartCache) -> Optional[Dict]:
    """Get cached Google Search company info"""
    return cache.get(domain, 'google_search')


def cache_company_info(domain: str, info: Dict, cache: SmartCache) -> bool:
    """Cache Google Search company info"""
    return cache.set(domain, info, 'google_search')


if __name__ == '__main__':
    """Test the smart cache system"""
    import logging
    import sys

    # Fix Windows encoding
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    logging.basicConfig(level=logging.DEBUG)

    print("=" * 80)
    print("SMART CACHE SYSTEM TEST")
    print("=" * 80)

    # Initialize cache
    cache = SmartCache()

    # Test AI analysis caching
    print("\n1. Testing AI Analysis Cache (30 day TTL)")
    test_domain = "example.com"
    test_analysis = {
        'category': 'SaaS',
        'value_proposition': 'Cloud storage for teams',
        'score': 85
    }

    print(f"   Caching analysis for {test_domain}...")
    cache.set(test_domain, test_analysis, 'ai_analysis')

    print(f"   Retrieving cached analysis...")
    cached = cache.get(test_domain, 'ai_analysis')
    print(f"   ✅ Retrieved: {cached}")

    # Test email verification caching
    print("\n2. Testing Email Verification Cache (30 day TTL)")
    test_email = "john@example.com"
    test_verification = {
        'deliverable': True,
        'confidence': 95,
        'source': 'EVA'
    }

    print(f"   Caching verification for {test_email}...")
    cache.set(test_email, test_verification, 'email_verification')

    print(f"   Retrieving cached verification...")
    cached = cache.get(test_email, 'email_verification')
    print(f"   ✅ Retrieved: {cached}")

    # Test cache miss
    print("\n3. Testing Cache Miss")
    cached = cache.get('nonexistent.com', 'ai_analysis')
    print(f"   Cache miss result: {cached}")

    # Get statistics
    print("\n4. Cache Statistics")
    stats = cache.get_stats()
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate_percent']}%")
    print(f"   API Calls Saved: {stats['estimated_api_calls_saved']}")

    # Get cache size
    print("\n5. Cache Size")
    sizes = cache.get_cache_size()
    for cache_type, count in sizes.items():
        print(f"   {cache_type}: {count} entries")

    print("\n" + "=" * 80)
    print("✅ SMART CACHE TEST COMPLETE")
    print("=" * 80)
