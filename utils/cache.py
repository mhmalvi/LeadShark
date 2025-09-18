"""
Simple on-disk cache with TTL support.

Provides caching functionality for API responses and scraped data
to reduce redundant requests and improve performance.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional, Dict

from .logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: str = "./.cache", default_ttl: int = 86400):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default TTL in seconds (24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for organization
        for subdir in ['handlers', 'api', 'robots']:
            (self.cache_dir / subdir).mkdir(exist_ok=True)

    def _get_cache_path(self, key: str, category: str = 'handlers') -> Path:
        """Get cache file path for key.

        Args:
            key: Cache key
            category: Cache category (handlers, api, robots)

        Returns:
            Path to cache file
        """
        # Hash the key to avoid filesystem issues
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        filename = f"{key_hash}.json"
        return self.cache_dir / category / filename

    async def get(self, key: str, category: str = 'handlers') -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key
            category: Cache category

        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_path = self._get_cache_path(key, category)

            if not cache_path.exists():
                return None

            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check TTL
            if cache_data.get('expires_at', 0) < time.time():
                # Cache expired, remove file
                cache_path.unlink(missing_ok=True)
                return None

            return cache_data.get('value')

        except Exception as e:
            logger.debug(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = 'handlers'
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
            category: Cache category
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            cache_path = self._get_cache_path(key, category)
            expires_at = time.time() + ttl

            cache_data = {
                'key': key,
                'value': value,
                'created_at': time.time(),
                'expires_at': expires_at
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.debug(f"Cache set error for key {key}: {e}")

    async def delete(self, key: str, category: str = 'handlers') -> None:
        """Delete value from cache.

        Args:
            key: Cache key
            category: Cache category
        """
        try:
            cache_path = self._get_cache_path(key, category)
            cache_path.unlink(missing_ok=True)
        except Exception as e:
            logger.debug(f"Cache delete error for key {key}: {e}")

    async def clear(self, category: Optional[str] = None) -> None:
        """Clear cache.

        Args:
            category: Optional category to clear (clears all if None)
        """
        try:
            if category:
                # Clear specific category
                category_dir = self.cache_dir / category
                if category_dir.exists():
                    for cache_file in category_dir.glob('*.json'):
                        cache_file.unlink(missing_ok=True)
            else:
                # Clear all categories
                for subdir in ['handlers', 'api', 'robots']:
                    category_dir = self.cache_dir / subdir
                    if category_dir.exists():
                        for cache_file in category_dir.glob('*.json'):
                            cache_file.unlink(missing_ok=True)

            logger.info(f"Cache cleared: {category or 'all categories'}")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of expired entries removed
        """
        removed_count = 0
        current_time = time.time()

        try:
            for category in ['handlers', 'api', 'robots']:
                category_dir = self.cache_dir / category
                if not category_dir.exists():
                    continue

                for cache_file in category_dir.glob('*.json'):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)

                        if cache_data.get('expires_at', 0) < current_time:
                            cache_file.unlink(missing_ok=True)
                            removed_count += 1

                    except Exception as e:
                        logger.debug(f"Error checking cache file {cache_file}: {e}")
                        # Remove corrupted cache files
                        cache_file.unlink(missing_ok=True)
                        removed_count += 1

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired cache entries")

        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'categories': {},
            'total_files': 0,
            'total_size_mb': 0,
            'cache_dir': str(self.cache_dir)
        }

        try:
            for category in ['handlers', 'api', 'robots']:
                category_dir = self.cache_dir / category
                if not category_dir.exists():
                    stats['categories'][category] = {'files': 0, 'size_mb': 0}
                    continue

                files = list(category_dir.glob('*.json'))
                file_count = len(files)
                total_size = sum(f.stat().st_size for f in files if f.exists())

                stats['categories'][category] = {
                    'files': file_count,
                    'size_mb': round(total_size / (1024 * 1024), 2)
                }

                stats['total_files'] += file_count
                stats['total_size_mb'] += stats['categories'][category]['size_mb']

            stats['total_size_mb'] = round(stats['total_size_mb'], 2)

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")

        return stats