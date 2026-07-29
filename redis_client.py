import os
import logging
import redis

logger = logging.getLogger(__name__)

redis_url = os.getenv("REDIS_URL")

class SafeRedisClient:
    def __init__(self, url):
        self._client = None
        if url:
            try:
                self._client = redis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")

    def get(self, name):
        if not self._client:
            return None
        try:
            return self._client.get(name)
        except Exception as e:
            logger.warning(f"Redis get('{name}') error: {e}")
            return None

    def set(self, name, value, ex=None):
        if not self._client:
            return False
        try:
            return self._client.set(name, value, ex=ex)
        except Exception as e:
            logger.warning(f"Redis set('{name}') error: {e}")
            return False

    def delete(self, *names):
        if not self._client or not names:
            return 0
        try:
            return self._client.delete(*names)
        except Exception as e:
            logger.warning(f"Redis delete({names}) error: {e}")
            return 0

    def incr(self, name, amount=1):
        if not self._client:
            return 1
        try:
            return self._client.incr(name, amount)
        except Exception as e:
            logger.warning(f"Redis incr('{name}') error: {e}")
            return 1

    def expire(self, name, time):
        if not self._client:
            return False
        try:
            return self._client.expire(name, time)
        except Exception as e:
            logger.warning(f"Redis expire('{name}') error: {e}")
            return False

    def scan_iter(self, match=None, count=None):
        if not self._client:
            return []
        try:
            return self._client.scan_iter(match=match, count=count)
        except Exception as e:
            logger.warning(f"Redis scan_iter('{match}') error: {e}")
            return []

    def lpush(self, name, *values):
        if not self._client or not values:
            return 0
        try:
            return self._client.lpush(name, *values)
        except Exception as e:
            logger.warning(f"Redis lpush('{name}') error: {e}")
            return 0

    def lrem(self, name, count, value):
        if not self._client:
            return 0
        try:
            return self._client.lrem(name, count, value)
        except Exception as e:
            logger.warning(f"Redis lrem('{name}') error: {e}")
            return 0

    def ltrim(self, name, start, end):
        if not self._client:
            return False
        try:
            return self._client.ltrim(name, start, end)
        except Exception as e:
            logger.warning(f"Redis ltrim('{name}') error: {e}")
            return False

    def lrange(self, name, start, end):
        if not self._client:
            return []
        try:
            return self._client.lrange(name, start, end)
        except Exception as e:
            logger.warning(f"Redis lrange('{name}') error: {e}")
            return []

redis_client = SafeRedisClient(redis_url)