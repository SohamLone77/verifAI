"""Response caching for VerifAI SDK"""

import time
import hashlib
import json
from typing import Dict, Any, Optional
from collections import OrderedDict
import threading


class ResponseCache:
    """
    Simple in-memory cache for API responses

    Features:
    - LRU eviction policy
    - TTL support
    - Thread-safe
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize cache

        Args:
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]

            if time.time() - timestamp > self.ttl:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any):
        """Set cached value"""
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (value, time.time())

    def clear(self):
        """Clear all cached values"""
        with self._lock:
            self._cache.clear()

    def remove(self, key: str):
        """Remove specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
            }


class CacheKeyGenerator:
    """Generate cache keys from requests"""

    @staticmethod
    def from_request(endpoint: str, data: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and data"""
        key_data = {
            "endpoint": endpoint,
            "data": data,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    @staticmethod
    def from_content(content: str, **params) -> str:
        """Generate cache key from content and parameters"""
        key_data = {
            "content": content,
            "params": params,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
