"""Safe Redis client wrapper with graceful database fallback and detailed logging."""

import logging
import os
from collections.abc import Iterable
from typing import Any

import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

redis_url = os.getenv("REDIS_URL")


class SafeRedisClient:
    """Redis client wrapper that swallows connection errors safely to prevent app crashes."""

    def __init__(self, url: str | None) -> None:
        self._client: redis.Redis | None = None
        self.url = url
        if url:
            try:
                self._client = redis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                pong, connected = self.ping()
                if connected:
                    logger.info("[REDIS] Connected successfully to Redis server (PONG)")
                else:
                    logger.warning(
                        f"[REDIS WARNING] Unable to ping Redis ({pong}). Application running in Database Fallback mode."
                    )
            except Exception as e:
                logger.warning(
                    f"[REDIS WARNING] Failed to initialize Redis client: {e}. Application running in Database Fallback mode."
                )

    def ping(self) -> tuple[str, bool]:
        """Check Redis server connection and ping response."""
        if not self._client:
            return ("Redis client disabled or URL missing", False)
        try:
            res = self._client.ping()
            if res:
                return ("PONG", True)
            return ("No PONG response from Redis", False)
        except Exception as e:
            return (str(e), False)

    def get(self, name: str) -> Any | None:
        """Fetch value from Redis by key with cache logging."""
        if not self._client:
            logger.info(f"[CACHE MISS] Key: {name} (Redis Disabled)")
            return None
        try:
            val = self._client.get(name)
            if val is not None:
                logger.info(f"[CACHE HIT] Key: {name}")
                return val
            logger.info(f"[CACHE MISS] Key: {name}")
            return None
        except Exception as e:
            logger.warning(f"[CACHE ERROR] Key: {name} - {e}. Falling back to Database.")
            return None

    def set(self, name: str, value: Any, ex: int | None = None) -> bool:
        """Set key-value pair in Redis with optional TTL in seconds."""
        if not self._client:
            return False
        try:
            res = bool(self._client.set(name, value, ex=ex))
            if res:
                logger.info(f"[CACHE SET] Key: {name} (TTL: {ex}s)")
            return res
        except Exception as e:
            logger.warning(f"[CACHE ERROR] Key: {name} - {e}")
            return False

    def delete(self, *names: str) -> int:
        """Delete one or more keys from Redis."""
        if not self._client or not names:
            return 0
        try:
            count = int(self._client.delete(*names))
            logger.info(f"[CACHE DELETE] Keys: {names} (Deleted: {count})")
            return count
        except Exception as e:
            logger.warning(f"[CACHE ERROR] Keys: {names} - {e}")
            return 0

    def incr(self, name: str, amount: int = 1) -> int:
        """Increment value of a Redis key."""
        if not self._client:
            return 1
        try:
            val = int(self._client.incr(name, amount))
            logger.info(f"[CACHE INCR] Key: {name} -> {val}")
            return val
        except Exception as e:
            logger.warning(f"[CACHE ERROR] Key: {name} - {e}")
            return 1

    def expire(self, name: str, time: int) -> bool:
        """Set TTL on a Redis key."""
        if not self._client:
            return False
        try:
            return bool(self._client.expire(name, time))
        except Exception as e:
            logger.warning(f"[CACHE ERROR] Key: {name} - {e}")
            return False

    def scan_iter(
        self, match: str | None = None, count: int | None = None
    ) -> Iterable[str]:
        """Iterate over matching keys in Redis."""
        if not self._client:
            return []
        try:
            keys = list(self._client.scan_iter(match=match, count=count))
            if keys:
                logger.info(f"[CACHE DELETE] Found matching keys for pattern '{match}': {keys}")
            return keys
        except Exception as e:
            logger.warning(f"[CACHE ERROR] scan_iter('{match}') - {e}")
            return []

    def lpush(self, name: str, *values: Any) -> int:
        """Push values onto head of Redis list."""
        if not self._client or not values:
            return 0
        try:
            res = int(self._client.lpush(name, *values))
            logger.info(f"[CACHE SET] List Key: {name} (Pushed: {values})")
            return res
        except Exception as e:
            logger.warning(f"[CACHE ERROR] List Key: {name} - {e}")
            return 0

    def lrem(self, name: str, count: int, value: Any) -> int:
        """Remove matching elements from Redis list."""
        if not self._client:
            return 0
        try:
            res = int(self._client.lrem(name, count, value))
            if res:
                logger.info(f"[CACHE DELETE] List Key: {name} (Removed: {value})")
            return res
        except Exception as e:
            logger.warning(f"[CACHE ERROR] List Key: {name} - {e}")
            return 0

    def ltrim(self, name: str, start: int, end: int) -> bool:
        """Trim Redis list to specified index range."""
        if not self._client:
            return False
        try:
            return bool(self._client.ltrim(name, start, end))
        except Exception as e:
            logger.warning(f"[CACHE ERROR] List Key: {name} - {e}")
            return False

    def lrange(self, name: str, start: int, end: int) -> list[Any]:
        """Fetch slice of elements from Redis list."""
        if not self._client:
            logger.info(f"[CACHE MISS] List Key: {name} (Redis Disabled)")
            return []
        try:
            val = list(self._client.lrange(name, start, end))
            if val:
                logger.info(f"[CACHE HIT] List Key: {name} (Items: {len(val)})")
            else:
                logger.info(f"[CACHE MISS] List Key: {name}")
            return val
        except Exception as e:
            logger.warning(f"[CACHE ERROR] List Key: {name} - {e}")
            return []


redis_client = SafeRedisClient(redis_url)
