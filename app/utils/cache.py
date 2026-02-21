import time
import hashlib
import json
from typing import Optional, Any
from app.core.config import settings
from app.utils.logger import log


class InMemoryCache:
    """Simple TTL-based in-memory cache"""

    def __init__(self):
        self._store: dict = {}
        self._hits = 0
        self._misses = 0

    def _make_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[Any]:
        key = self._make_key(url)
        entry = self._store.get(key)

        if not entry:
            self._misses += 1
            return None

        # TTL check
        if time.time() > entry["expires_at"]:
            del self._store[key]
            self._misses += 1
            log.debug(f"Cache EXPIRED for: {url[:50]}")
            return None

        self._hits += 1
        log.debug(f"Cache HIT for: {url[:50]}")
        return entry["data"]

    def set(self, url: str, data: Any, ttl: int = None):
        key = self._make_key(url)
        ttl = ttl or settings.CACHE_TTL
        self._store[key] = {
            "data": data,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }
        log.debug(f"Cache SET for: {url[:50]} (TTL: {ttl}s)")

    def delete(self, url: str):
        key = self._make_key(url)
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()
        log.info("Cache cleared!")

    def stats(self) -> dict:
        active = sum(
            1 for v in self._store.values()
            if time.time() < v["expires_at"]
        )
        return {
            "total_keys": len(self._store),
            "active_keys": active,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(
                self._hits / max(self._hits + self._misses, 1) * 100, 2
            ),
        }


# Global cache instance
cache = InMemoryCache()
