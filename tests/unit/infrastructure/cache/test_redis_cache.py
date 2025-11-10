"""
Tests for Redis cache implementation
"""

import time
from typing import Any
from unittest.mock import Mock, patch, MagicMock
import pytest
import json
import pickle
import zlib

from src.infrastructure.cache.config import CacheConfig
from src.infrastructure.cache.redis_cache import RedisCache


@pytest.fixture
def cache_config() -> CacheConfig:
    """Create cache config for testing"""
    return CacheConfig(
        cache_enabled=True,
        redis_url="redis://localhost:6379/0",
        key_prefix="test:",
        default_ttl=300,
        cache_serialization="json",
        cache_compression=False,
    )


@pytest.fixture
def mock_redis() -> MagicMock:
    """Create mock Redis client"""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    return mock_client


@pytest.fixture
def cache(cache_config: CacheConfig, mock_redis: MagicMock) -> RedisCache:
    """Create RedisCache instance with mock client"""
    with patch("redis.from_url", return_value=mock_redis):
        cache = RedisCache(cache_config)
        cache._client = mock_redis  # Replace with mock
        return cache


def test_cache_initialization(cache_config: CacheConfig) -> None:
    """Test cache initialization"""
    with patch("redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache(cache_config)
        assert cache.config == cache_config
        assert cache._client is None  # Lazy initialization

        # Access client to trigger initialization
        _ = cache.client
        assert cache._client is not None
        mock_from_url.assert_called_once()


def test_cache_disabled(mock_redis: MagicMock) -> None:
    """Test cache operations when cache is disabled"""
    config = CacheConfig(cache_enabled=False)
    cache = RedisCache(config)
    cache._client = mock_redis

    # All operations should return None or do nothing
    assert cache.get("key") is None
    assert cache.set("key", "value") is False
    assert cache.delete("key") is False


def test_set_and_get_json(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test set and get with JSON serialization"""
    test_data = {"field": "value", "number": 42}
    cache.set("test_key", test_data)

    # Verify set was called
    expected_value = json.dumps(test_data).encode("utf-8")
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == "test:test_key"
    assert call_args[0][1] == expected_value

    # Mock get response
    mock_redis.get.return_value = expected_value
    result = cache.get("test_key")
    assert result == test_data


def test_set_and_get_pickle(cache_config: CacheConfig, mock_redis: MagicMock) -> None:
    """Test set and get with pickle serialization"""
    cache_config.cache_serialization = "pickle"
    cache = RedisCache(cache_config)
    cache._client = mock_redis

    test_data = {"field": "value", "complex": [1, 2, 3]}
    cache.set("test_key", test_data)

    # Verify set was called
    expected_value = pickle.dumps(test_data)
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][1] == expected_value

    # Mock get response
    mock_redis.get.return_value = expected_value
    result = cache.get("test_key")
    assert result == test_data


def test_compression(cache_config: CacheConfig, mock_redis: MagicMock) -> None:
    """Test data compression"""
    cache_config.cache_compression = True
    cache = RedisCache(cache_config)
    cache._client = mock_redis

    test_data = {"field": "value" * 100}  # Repeating data for compression
    cache.set("test_key", test_data)

    # Verify compressed data was set
    expected_value = zlib.compress(json.dumps(test_data).encode("utf-8"))
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][1] == expected_value

    # Mock get response
    mock_redis.get.return_value = expected_value
    result = cache.get("test_key")
    assert result == test_data


def test_set_with_ttl(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test set with custom TTL"""
    cache.set("test_key", "value", ttl=60)

    # Verify ex (expiration) parameter was passed
    call_args = mock_redis.set.call_args
    assert call_args[1]["ex"] == 60


def test_set_with_prefix(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test set with custom prefix"""
    cache.set("test_key", "value", prefix="custom:")

    # Verify custom prefix was used
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == "custom:test_key"


def test_get_nonexistent_key(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test get with nonexistent key"""
    mock_redis.get.return_value = None
    result = cache.get("nonexistent")
    assert result is None


def test_delete(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test delete operation"""
    mock_redis.delete.return_value = 1
    result = cache.delete("test_key")
    assert result is True
    mock_redis.delete.assert_called_once_with("test:test_key")


def test_exists(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test exists operation"""
    mock_redis.exists.return_value = 1
    assert cache.exists("test_key") is True

    mock_redis.exists.return_value = 0
    assert cache.exists("other_key") is False


def test_get_many(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test batch get operation"""
    keys = ["key1", "key2", "key3"]
    values = [
        json.dumps("value1").encode("utf-8"),
        json.dumps("value2").encode("utf-8"),
        None,
    ]
    mock_redis.mget.return_value = values

    result = cache.get_many(keys)
    assert result == {"key1": "value1", "key2": "value2"}
    assert "key3" not in result


def test_set_many(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test batch set operation"""
    data = {"key1": "value1", "key2": "value2"}
    cache.set_many(data, ttl=60)

    # Verify pipeline was used
    mock_redis.pipeline.assert_called_once()
    pipeline = mock_redis.pipeline.return_value.__enter__.return_value

    # Verify set calls
    assert pipeline.set.call_count == 2


def test_delete_many(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test batch delete operation"""
    keys = ["key1", "key2", "key3"]
    mock_redis.delete.return_value = 3

    result = cache.delete_many(keys)
    assert result == 3

    # Verify all keys were passed to delete
    call_args = mock_redis.delete.call_args
    assert set(call_args[0]) == {
        "test:key1",
        "test:key2",
        "test:key3",
    }


def test_clear_prefix(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test clear by prefix"""
    mock_redis.scan_iter.return_value = [
        "test:user:1",
        "test:user:2",
        "test:user:3",
    ]
    mock_redis.delete.return_value = 3

    result = cache.clear_prefix("user:")
    assert result == 3

    # Verify scan_iter was called with correct pattern
    mock_redis.scan_iter.assert_called_once_with(match="test:user:*", count=1000)


def test_increment(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test increment operation"""
    mock_redis.incr.return_value = 5
    result = cache.increment("counter", amount=2)
    assert result == 5
    mock_redis.incr.assert_called_once_with("test:counter", 2)


def test_expire(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test expire operation"""
    cache.expire("test_key", 120)
    mock_redis.expire.assert_called_once_with("test:test_key", 120)


def test_ttl(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test TTL check"""
    mock_redis.ttl.return_value = 300
    result = cache.ttl("test_key")
    assert result == 300


def test_ping(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test ping operation"""
    mock_redis.ping.return_value = True
    assert cache.ping() is True


def test_error_handling_get(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test error handling in get"""
    from redis.exceptions import RedisError

    mock_redis.get.side_effect = RedisError("Connection failed")

    # Should return None on error, not raise
    result = cache.get("test_key")
    assert result is None


def test_error_handling_set(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test error handling in set"""
    from redis.exceptions import RedisError

    mock_redis.set.side_effect = RedisError("Connection failed")

    # Should return False on error, not raise
    result = cache.set("test_key", "value")
    assert result is False


def test_singleton_pattern() -> None:
    """Test singleton get_cache()"""
    from src.infrastructure.cache.redis_cache import get_cache, _cache_instance

    # Clear singleton
    import src.infrastructure.cache.redis_cache as cache_module

    cache_module._cache_instance = None

    with patch("redis.from_url"):
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2


def test_make_key(cache: RedisCache) -> None:
    """Test key generation"""
    key = cache._make_key("test", prefix="custom:")
    assert key == "custom:test"

    key = cache._make_key("test")
    assert key == "test:test"


def test_serialize_deserialize_roundtrip(cache: RedisCache) -> None:
    """Test serialization round trip"""
    test_data = {"field": "value", "number": 42, "list": [1, 2, 3]}

    serialized = cache._serialize(test_data)
    assert isinstance(serialized, bytes)

    deserialized = cache._deserialize(serialized)
    assert deserialized == test_data


def test_compression_roundtrip(cache_config: CacheConfig, mock_redis: MagicMock) -> None:
    """Test compression/decompression round trip"""
    cache_config.cache_compression = True
    cache = RedisCache(cache_config)
    cache._client = mock_redis

    test_data = {"field": "value" * 100}

    serialized = cache._serialize(test_data)
    assert isinstance(serialized, bytes)

    deserialized = cache._deserialize(serialized)
    assert deserialized == test_data


def test_large_data_handling(cache: RedisCache, mock_redis: MagicMock) -> None:
    """Test handling of large data"""
    large_data = {"data": "x" * 1000000}  # 1MB of data
    cache.set("large_key", large_data)

    # Verify set was called
    assert mock_redis.set.called

    # Mock get response
    serialized = json.dumps(large_data).encode("utf-8")
    mock_redis.get.return_value = serialized
    result = cache.get("large_key")
    assert result == large_data
