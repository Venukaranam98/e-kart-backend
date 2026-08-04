"""Safe Redis client wrapper with fallback error handling."""

import logging
import os
from collections.abc import Iterable
from typing import Any

import redis

logger = logging.getLogger(__name__)

redis_url = os.getenv("REDIS_URL")


class SafeRedisClient:
    """Redis client wrapper that swallows connection errors safely to prevent app crashes."""

    def __init__(self, url: str | None) -> None:
        self._client: redis.Redis | None = None
        if url:
            try:
                self._client = redis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")

    def get(self, name: str) -> Any | None:
        """Fetch value from Redis by key."""
        if not self._client:
            return None
        try:
            return self._client.get(name)
        except Exception as e:
            logger.warning(f"Redis get('{name}') error: {e}")
            return None

    def set(self, name: str, value: Any, ex: int | None = None) -> bool:
        """Set key-value pair in Redis with optional TTL in seconds."""
        if not self._client:
            return False
        try:
            return bool(self._client.set(name, value, ex=ex))
        except Exception as e:
            logger.warning(f"Redis set('{name}') error: {e}")
            return False

    def delete(self, *names: str) -> int:
        """Delete one or more keys from Redis."""
        if not self._client or not names:
            return 0
        try:
            return int(self._client.delete(*names))
        except Exception as e:
            logger.warning(f"Redis delete({names}) error: {e}")
            return 0

    def incr(self, name: str, amount: int = 1) -> int:
        """Increment value of a Redis key."""
        if not self._client:
            return 1
        try:
            return int(self._client.incr(name, amount))
        except Exception as e:
            logger.warning(f"Redis incr('{name}') error: {e}")
            return 1

    def expire(self, name: str, time: int) -> bool:
        """Set TTL on a Redis key."""
        if not self._client:
            return False
        try:
            return bool(self._client.expire(name, time))
        except Exception as e:
            logger.warning(f"Redis expire('{name}') error: {e}")
            return False

    def scan_iter(
        self, match: str | None = None, count: int | None = None
    ) -> Iterable[str]:
        """Iterate over matching keys in Redis."""
        if not self._client:
            return []
        try:
            return self._client.scan_iter(match=match, count=count)
        except Exception as e:
            logger.warning(f"Redis scan_iter('{match}') error: {e}")
            return []

    def lpush(self, name: str, *values: Any) -> int:
        """Push values onto head of Redis list."""
        if not self._client or not values:
            return 0
        try:
            return int(self._client.lpush(name, *values))
        except Exception as e:
            logger.warning(f"Redis lpush('{name}') error: {e}")
            return 0

    def lrem(self, name: str, count: int, value: Any) -> int:
        """Remove matching elements from Redis list."""
        if not self._client:
            return 0
        try:
            return int(self._client.lrem(name, count, value))
        except Exception as e:
            logger.warning(f"Redis lrem('{name}') error: {e}")
            return 0

    def ltrim(self, name: str, start: int, end: int) -> bool:
        """Trim Redis list to specified index range."""
        if not self._client:
            return False
        try:
            return bool(self._client.ltrim(name, start, end))
        except Exception as e:
            logger.warning(f"Redis ltrim('{name}') error: {e}")
            return False

    def lrange(self, name: str, start: int, end: int) -> list[Any]:
        """Fetch slice of elements from Redis list."""
        if not self._client:
            return []
        try:
            return list(self._client.lrange(name, start, end))
        except Exception as e:
            logger.warning(f"Redis lrange('{name}') error: {e}")
            return []


redis_client = SafeRedisClient(redis_url)
