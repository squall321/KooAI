"""
Redis cache implementation
"""

import json
import pickle
import zlib
from typing import Any, Optional, List, Dict
import structlog
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError

from .config import CacheConfig, get_cache_config


logger = structlog.get_logger(__name__)


class RedisCache:
    """
    Redis cache client

    Provides high-level caching operations with:
    - Automatic serialization/deserialization
    - Compression support
    - TTL management
    - Batch operations
    - Pipeline support
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize Redis cache

        Args:
            config: Cache configuration (uses default if None)
        """
        if config is None:
            config = get_cache_config()

        self.config = config
        self._client: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None

    @property
    def client(self) -> Redis:
        """Get Redis client (lazy initialization)"""
        if self._client is None:
            self._pool = ConnectionPool(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                max_connections=self.config.redis_max_connections,
                socket_timeout=self.config.redis_socket_timeout,
                socket_connect_timeout=self.config.redis_socket_connect_timeout,
                decode_responses=False,  # We handle encoding/decoding
            )
            self._client = Redis(connection_pool=self._pool)

        return self._client

    def _make_key(self, key: str, prefix: Optional[str] = None) -> str:
        """Create full cache key with prefix"""
        parts = [self.config.key_prefix]
        if prefix:
            parts.append(prefix)
        parts.append(key)
        return "".join(parts)

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if self.config.cache_serialization == "json":
            serialized = json.dumps(value).encode("utf-8")
        elif self.config.cache_serialization == "pickle":
            serialized = pickle.dumps(value)
        else:
            # Fallback to JSON
            serialized = json.dumps(value).encode("utf-8")

        # Compress if enabled
        if self.config.cache_compression:
            serialized = zlib.compress(serialized)

        return serialized

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        # Decompress if needed
        if self.config.cache_compression:
            try:
                data = zlib.decompress(data)
            except zlib.error:
                # Not compressed, use as-is
                pass

        # Deserialize
        if self.config.cache_serialization == "json":
            return json.loads(data.decode("utf-8"))
        elif self.config.cache_serialization == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode("utf-8"))

    def get(self, key: str, prefix: Optional[str] = None) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            prefix: Optional key prefix

        Returns:
            Cached value or None if not found
        """
        if not self.config.cache_enabled:
            return None

        try:
            full_key = self._make_key(key, prefix)
            data = self.client.get(full_key)

            if data is None:
                return None

            return self._deserialize(data)

        except RedisError as e:
            logger.warning("cache_get_failed", key=key, error=str(e))
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: Optional[str] = None,
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = use default)
            prefix: Optional key prefix

        Returns:
            True if successful
        """
        if not self.config.cache_enabled:
            return False

        try:
            full_key = self._make_key(key, prefix)
            data = self._serialize(value)

            if ttl is None:
                ttl = self.config.default_ttl

            self.client.setex(full_key, ttl, data)
            return True

        except RedisError as e:
            logger.warning("cache_set_failed", key=key, error=str(e))
            return False

    def delete(self, key: str, prefix: Optional[str] = None) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key
            prefix: Optional key prefix

        Returns:
            True if key was deleted
        """
        try:
            full_key = self._make_key(key, prefix)
            result = self.client.delete(full_key)
            return result > 0

        except RedisError as e:
            logger.warning("cache_delete_failed", key=key, error=str(e))
            return False

    def exists(self, key: str, prefix: Optional[str] = None) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key
            prefix: Optional key prefix

        Returns:
            True if key exists
        """
        try:
            full_key = self._make_key(key, prefix)
            return self.client.exists(full_key) > 0

        except RedisError as e:
            logger.warning("cache_exists_failed", key=key, error=str(e))
            return False

    def get_many(self, keys: List[str], prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get multiple values from cache

        Args:
            keys: List of cache keys
            prefix: Optional key prefix

        Returns:
            Dictionary of key-value pairs
        """
        if not self.config.cache_enabled or not keys:
            return {}

        try:
            full_keys = [self._make_key(key, prefix) for key in keys]
            values = self.client.mget(full_keys)

            result = {}
            for key, data in zip(keys, values):
                if data is not None:
                    try:
                        result[key] = self._deserialize(data)
                    except Exception as e:
                        logger.warning("cache_deserialize_failed", key=key, error=str(e))

            return result

        except RedisError as e:
            logger.warning("cache_get_many_failed", error=str(e))
            return {}

    def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        prefix: Optional[str] = None,
    ) -> int:
        """
        Set multiple values in cache

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            prefix: Optional key prefix

        Returns:
            Number of keys successfully set
        """
        if not self.config.cache_enabled or not mapping:
            return 0

        try:
            if ttl is None:
                ttl = self.config.default_ttl

            # Use pipeline for efficiency
            pipe = self.client.pipeline()

            for key, value in mapping.items():
                full_key = self._make_key(key, prefix)
                data = self._serialize(value)
                pipe.setex(full_key, ttl, data)

            pipe.execute()
            return len(mapping)

        except RedisError as e:
            logger.warning("cache_set_many_failed", error=str(e))
            return 0

    def delete_many(self, keys: List[str], prefix: Optional[str] = None) -> int:
        """
        Delete multiple keys from cache

        Args:
            keys: List of cache keys
            prefix: Optional key prefix

        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0

        try:
            full_keys = [self._make_key(key, prefix) for key in keys]
            return self.client.delete(*full_keys)

        except RedisError as e:
            logger.warning("cache_delete_many_failed", error=str(e))
            return 0

    def clear_prefix(self, prefix: str) -> int:
        """
        Clear all keys with given prefix

        Args:
            prefix: Key prefix to clear

        Returns:
            Number of keys deleted
        """
        try:
            pattern = self._make_key("*", prefix)
            keys = list(self.client.scan_iter(match=pattern, count=1000))

            if keys:
                return self.client.delete(*keys)

            return 0

        except RedisError as e:
            logger.warning("cache_clear_prefix_failed", prefix=prefix, error=str(e))
            return 0

    def increment(self, key: str, amount: int = 1, prefix: Optional[str] = None) -> int:
        """
        Increment counter

        Args:
            key: Cache key
            amount: Increment amount
            prefix: Optional key prefix

        Returns:
            New value after increment
        """
        try:
            full_key = self._make_key(key, prefix)
            return self.client.incrby(full_key, amount)

        except RedisError as e:
            logger.warning("cache_increment_failed", key=key, error=str(e))
            return 0

    def expire(self, key: str, ttl: int, prefix: Optional[str] = None) -> bool:
        """
        Set expiration on existing key

        Args:
            key: Cache key
            ttl: Time to live in seconds
            prefix: Optional key prefix

        Returns:
            True if successful
        """
        try:
            full_key = self._make_key(key, prefix)
            return self.client.expire(full_key, ttl)

        except RedisError as e:
            logger.warning("cache_expire_failed", key=key, error=str(e))
            return False

    def ttl(self, key: str, prefix: Optional[str] = None) -> int:
        """
        Get remaining TTL for key

        Args:
            key: Cache key
            prefix: Optional key prefix

        Returns:
            Remaining TTL in seconds (-1 if no TTL, -2 if key doesn't exist)
        """
        try:
            full_key = self._make_key(key, prefix)
            return self.client.ttl(full_key)

        except RedisError as e:
            logger.warning("cache_ttl_failed", key=key, error=str(e))
            return -2

    def ping(self) -> bool:
        """
        Check if Redis is accessible

        Returns:
            True if Redis is accessible
        """
        try:
            return self.client.ping()
        except RedisError:
            return False


# Singleton instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get cache singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def reset_cache() -> None:
    """Reset cache singleton (useful for testing)"""
    global _cache_instance
    _cache_instance = None
