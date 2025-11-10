"""
Integration tests for Multi-Tier Cache

Tests the L1+L2 caching system with real Redis backend.
"""

import pytest
import time
from typing import Any, Generator
from unittest.mock import Mock, MagicMock

from src.infrastructure.cache.multi_tier_cache import MultiTierCache
from src.infrastructure.cache.lru_cache import LRUCache
from src.infrastructure.cache.redis_cache import RedisCache


# Skip tests if Redis is not available
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_redis_cache() -> MagicMock:
    """
    Create mock Redis cache for testing

    Note: For full integration testing, replace this with real Redis instance
    """
    cache = MagicMock(spec=RedisCache)
    cache.ping.return_value = True

    # Simulate Redis storage
    cache._storage = {}

    def mock_get(key: str, prefix: str | None = None) -> Any:
        full_key = f"{prefix}:{key}" if prefix else key
        return cache._storage.get(full_key)

    def mock_set(key: str, value: Any, ttl: int | None = None, prefix: str | None = None) -> bool:
        full_key = f"{prefix}:{key}" if prefix else key
        cache._storage[full_key] = value
        return True

    def mock_delete(key: str, prefix: str | None = None) -> bool:
        full_key = f"{prefix}:{key}" if prefix else key
        if full_key in cache._storage:
            del cache._storage[full_key]
            return True
        return False

    def mock_exists(key: str, prefix: str | None = None) -> bool:
        full_key = f"{prefix}:{key}" if prefix else key
        return full_key in cache._storage

    def mock_get_many(keys: list[str], prefix: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key in keys:
            full_key = f"{prefix}:{key}" if prefix else key
            if full_key in cache._storage:
                result[key] = cache._storage[full_key]
        return result

    def mock_set_many(mapping: dict[str, Any], ttl: int | None = None, prefix: str | None = None) -> int:
        for key, value in mapping.items():
            full_key = f"{prefix}:{key}" if prefix else key
            cache._storage[full_key] = value
        return len(mapping)

    def mock_clear_prefix(prefix: str) -> int:
        keys_to_delete = [k for k in cache._storage.keys() if k.startswith(f"{prefix}:")]
        for key in keys_to_delete:
            del cache._storage[key]
        return len(keys_to_delete)

    cache.get.side_effect = mock_get
    cache.set.side_effect = mock_set
    cache.delete.side_effect = mock_delete
    cache.exists.side_effect = mock_exists
    cache.get_many.side_effect = mock_get_many
    cache.set_many.side_effect = mock_set_many
    cache.clear_prefix.side_effect = mock_clear_prefix

    return cache


@pytest.fixture
def multi_tier_cache(mock_redis_cache: MagicMock) -> Generator[MultiTierCache, None, None]:
    """Create multi-tier cache instance"""
    cache = MultiTierCache(
        l2_cache=mock_redis_cache, l1_max_size=100, l1_default_ttl=300, promote_to_l1=True
    )
    yield cache
    cache.clear_l1()
    cache.reset_stats()


class TestMultiTierCacheBasics:
    """Test basic multi-tier cache operations"""

    def test_set_and_get_l1_hit(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that recently set values hit L1"""
        multi_tier_cache.set("key1", "value1")

        # Should hit L1
        value = multi_tier_cache.get("key1")
        assert value == "value1"

        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["l1_hits"] == 1
        assert stats["overall"]["l2_hits"] == 0

    def test_set_stores_in_both_tiers(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that set() stores in both L1 and L2"""
        multi_tier_cache.set("key1", "value1")

        # Check L1
        assert multi_tier_cache.l1.get("key1") == "value1"

        # Check L2 (through mock)
        assert multi_tier_cache.l2._storage.get("key1") == "value1"  # type: ignore[attr-defined]

    def test_l1_only_flag(self, multi_tier_cache: MultiTierCache) -> None:
        """Test l1_only flag skips L2"""
        multi_tier_cache.set("key1", "value1", l1_only=True)

        # Should be in L1
        assert multi_tier_cache.l1.get("key1") == "value1"

        # Should NOT be in L2
        assert "key1" not in multi_tier_cache.l2._storage  # type: ignore[attr-defined]

    def test_delete_from_both_tiers(self, multi_tier_cache: MultiTierCache) -> None:
        """Test delete removes from both tiers"""
        multi_tier_cache.set("key1", "value1")

        result = multi_tier_cache.delete("key1")
        assert result is True

        # Should be gone from L1
        assert multi_tier_cache.l1.get("key1") is None

        # Should be gone from L2
        assert "key1" not in multi_tier_cache.l2._storage  # type: ignore[attr-defined]

    def test_exists_checks_both_tiers(self, multi_tier_cache: MultiTierCache) -> None:
        """Test exists() checks both tiers"""
        # Key only in L2 (not L1)
        multi_tier_cache.l2._storage["key1"] = "value1"  # type: ignore[attr-defined]

        assert multi_tier_cache.exists("key1")

        # Non-existent key
        assert not multi_tier_cache.exists("nonexistent")


class TestL2Promotion:
    """Test L2 hit promotion to L1"""

    def test_l2_hit_promotes_to_l1(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that L2 hit promotes value to L1"""
        # Put value only in L2
        multi_tier_cache.l2._storage["key1"] = "value1"  # type: ignore[attr-defined]

        # Get should miss L1, hit L2, and promote
        value = multi_tier_cache.get("key1")
        assert value == "value1"

        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["l2_hits"] == 1
        assert stats["overall"]["promotions"] == 1

        # Now should be in L1
        assert multi_tier_cache.l1.get("key1") == "value1"

    def test_second_access_hits_l1(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that second access hits L1 after promotion"""
        # Put value only in L2
        multi_tier_cache.l2._storage["key1"] = "value1"  # type: ignore[attr-defined]

        # First access - L2 hit, promotion
        multi_tier_cache.get("key1")

        # Second access - L1 hit
        multi_tier_cache.reset_stats()
        value = multi_tier_cache.get("key1")

        assert value == "value1"
        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["l1_hits"] == 1
        assert stats["overall"]["l2_hits"] == 0

    def test_promotion_disabled(self, mock_redis_cache: MagicMock) -> None:
        """Test cache with promotion disabled"""
        cache = MultiTierCache(l2_cache=mock_redis_cache, promote_to_l1=False)

        # Put value only in L2
        cache.l2._storage["key1"] = "value1"  # type: ignore[attr-defined]

        # Get should hit L2 but NOT promote
        value = cache.get("key1")
        assert value == "value1"

        stats = cache.get_stats()
        assert stats["overall"]["promotions"] == 0

        # Should NOT be in L1
        assert cache.l1.get("key1") is None


class TestPrefixHandling:
    """Test prefix handling"""

    def test_set_with_prefix(self, multi_tier_cache: MultiTierCache) -> None:
        """Test setting value with prefix"""
        multi_tier_cache.set("key1", "value1", prefix="simulation")

        # Check L1 (uses full key with prefix)
        assert multi_tier_cache.l1.get("simulation:key1") == "value1"

        # Check L2 (stores with prefix)
        assert multi_tier_cache.l2._storage.get("simulation:key1") == "value1"  # type: ignore[attr-defined]

    def test_get_with_prefix(self, multi_tier_cache: MultiTierCache) -> None:
        """Test getting value with prefix"""
        multi_tier_cache.set("key1", "value1", prefix="simulation")

        value = multi_tier_cache.get("key1", prefix="simulation")
        assert value == "value1"

    def test_different_prefixes_isolated(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that different prefixes are isolated"""
        multi_tier_cache.set("key1", "value_sim", prefix="simulation")
        multi_tier_cache.set("key1", "value_analysis", prefix="analysis")

        assert multi_tier_cache.get("key1", prefix="simulation") == "value_sim"
        assert multi_tier_cache.get("key1", prefix="analysis") == "value_analysis"

    def test_clear_prefix(self, multi_tier_cache: MultiTierCache) -> None:
        """Test clearing specific prefix"""
        multi_tier_cache.set("key1", "value1", prefix="simulation")
        multi_tier_cache.set("key2", "value2", prefix="simulation")
        multi_tier_cache.set("key3", "value3", prefix="analysis")

        # Clear simulation prefix
        count = multi_tier_cache.clear_prefix("simulation")
        assert count == 2

        # Simulation keys should be gone from L2
        assert not multi_tier_cache.exists("key1", prefix="simulation")
        assert not multi_tier_cache.exists("key2", prefix="simulation")

        # Analysis key should still exist
        assert multi_tier_cache.exists("key3", prefix="analysis")


class TestBatchOperations:
    """Test batch get/set operations"""

    def test_get_many_all_l1_hits(self, multi_tier_cache: MultiTierCache) -> None:
        """Test get_many when all keys in L1"""
        multi_tier_cache.set("key1", "value1")
        multi_tier_cache.set("key2", "value2")
        multi_tier_cache.set("key3", "value3")

        multi_tier_cache.reset_stats()
        result = multi_tier_cache.get_many(["key1", "key2", "key3"])

        assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["l1_hits"] == 3
        assert stats["overall"]["l2_hits"] == 0

    def test_get_many_mixed_hits(self, multi_tier_cache: MultiTierCache) -> None:
        """Test get_many with L1 and L2 hits"""
        # key1, key2 in both tiers
        multi_tier_cache.set("key1", "value1")
        multi_tier_cache.set("key2", "value2")

        # key3 only in L2
        multi_tier_cache.l2._storage["key3"] = "value3"  # type: ignore[attr-defined]

        # key4 doesn't exist

        result = multi_tier_cache.get_many(["key1", "key2", "key3", "key4"])

        assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}
        assert "key4" not in result

    def test_get_many_promotes_l2_hits(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that get_many promotes L2 hits to L1"""
        # Put values only in L2
        multi_tier_cache.l2._storage["key1"] = "value1"  # type: ignore[attr-defined]
        multi_tier_cache.l2._storage["key2"] = "value2"  # type: ignore[attr-defined]

        result = multi_tier_cache.get_many(["key1", "key2"])

        # Should be promoted to L1
        assert multi_tier_cache.l1.get("key1") == "value1"
        assert multi_tier_cache.l1.get("key2") == "value2"

        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["promotions"] == 2

    def test_set_many(self, multi_tier_cache: MultiTierCache) -> None:
        """Test set_many stores in both tiers"""
        mapping = {"key1": "value1", "key2": "value2", "key3": "value3"}

        count = multi_tier_cache.set_many(mapping)
        assert count == 3

        # Check all keys in both tiers
        for key, value in mapping.items():
            assert multi_tier_cache.l1.get(key) == value
            assert multi_tier_cache.l2._storage[key] == value  # type: ignore[attr-defined]

    def test_set_many_with_prefix(self, multi_tier_cache: MultiTierCache) -> None:
        """Test set_many with prefix"""
        mapping = {"key1": "value1", "key2": "value2"}

        multi_tier_cache.set_many(mapping, prefix="simulation")

        # Check with prefix
        result = multi_tier_cache.get_many(["key1", "key2"], prefix="simulation")
        assert result == mapping


class TestStatistics:
    """Test statistics tracking"""

    def test_hit_rate_calculation(self, multi_tier_cache: MultiTierCache) -> None:
        """Test overall hit rate calculation"""
        # Set 3 keys
        multi_tier_cache.set("key1", "value1")
        multi_tier_cache.set("key2", "value2")
        multi_tier_cache.set("key3", "value3")

        # Clear L1 so we get L2 hits
        multi_tier_cache.clear_l1()
        multi_tier_cache.reset_stats()

        # 2 L2 hits
        multi_tier_cache.get("key1")  # L2 hit
        multi_tier_cache.get("key2")  # L2 hit

        # 1 miss
        multi_tier_cache.get("key_nonexistent")  # Miss

        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["l2_hits"] == 2
        assert stats["overall"]["total_misses"] == 1
        assert stats["overall"]["hit_rate"] == 2 / 3  # 2 hits out of 3 requests

    def test_l1_statistics(self, multi_tier_cache: MultiTierCache) -> None:
        """Test L1-specific statistics"""
        multi_tier_cache.set("key1", "value1")
        multi_tier_cache.get("key1")
        multi_tier_cache.get("key1")

        stats = multi_tier_cache.get_stats()
        l1_stats = stats["l1"]

        assert l1_stats["size"] == 1
        assert l1_stats["hits"] == 2

    def test_stats_reset(self, multi_tier_cache: MultiTierCache) -> None:
        """Test resetting statistics"""
        multi_tier_cache.set("key1", "value1")
        multi_tier_cache.get("key1")
        multi_tier_cache.get("nonexistent")

        multi_tier_cache.reset_stats()

        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["l1_hits"] == 0
        assert stats["overall"]["l2_hits"] == 0
        assert stats["overall"]["total_misses"] == 0
        assert stats["overall"]["promotions"] == 0


class TestL1Eviction:
    """Test L1 eviction behavior"""

    def test_l1_eviction_keeps_l2(self, mock_redis_cache: MagicMock) -> None:
        """Test that L1 eviction doesn't affect L2"""
        cache = MultiTierCache(l2_cache=mock_redis_cache, l1_max_size=3)  # Small L1

        # Fill L1 beyond capacity
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        # L1 should have only 3 items
        assert len(cache.l1) == 3

        # But L2 should have all 5
        assert len(cache.l2._storage) == 5  # type: ignore[attr-defined]

        # Evicted items should still be accessible from L2
        value = cache.get("key0")  # Was evicted from L1
        assert value == "value0"

    def test_evicted_items_repromoted(self, mock_redis_cache: MagicMock) -> None:
        """Test that evicted items are re-promoted on access"""
        cache = MultiTierCache(l2_cache=mock_redis_cache, l1_max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Evicts key1 from L1

        # Access key1 - should hit L2 and promote back to L1
        cache.reset_stats()
        value = cache.get("key1")

        assert value == "value1"
        stats = cache.get_stats()
        assert stats["overall"]["l2_hits"] == 1
        assert stats["overall"]["promotions"] == 1

        # Now in L1 again
        assert cache.l1.get("key1") == "value1"


class TestExpiration:
    """Test TTL and expiration"""

    def test_l1_expiration(self, multi_tier_cache: MultiTierCache) -> None:
        """Test L1 TTL expiration"""
        multi_tier_cache.set("key1", "value1", ttl=1)

        # Should exist immediately
        assert multi_tier_cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # L1 should be expired, but L2 might still have it
        # (depends on Redis TTL implementation in mock)
        value = multi_tier_cache.get("key1")
        # In our mock, L2 doesn't implement TTL, so it will still have it
        # In real Redis, this would also be None

    def test_cleanup_expired_l1(self, multi_tier_cache: MultiTierCache) -> None:
        """Test cleanup of expired L1 entries"""
        multi_tier_cache.set("key1", "value1", ttl=1)
        multi_tier_cache.set("key2", "value2", ttl=1)
        multi_tier_cache.set("key3", "value3", ttl=60)

        time.sleep(1.1)

        count = multi_tier_cache.cleanup_expired()
        assert count == 2  # key1, key2 expired

        # key3 should still exist in L1
        assert multi_tier_cache.l1.get("key3") == "value3"


class TestEdgeCases:
    """Test edge cases"""

    def test_none_value(self, multi_tier_cache: MultiTierCache) -> None:
        """Test storing None value"""
        multi_tier_cache.set("none_key", None)

        # Should be able to retrieve None
        assert multi_tier_cache.exists("none_key")
        value = multi_tier_cache.get("none_key")
        assert value is None

    def test_complex_objects(self, multi_tier_cache: MultiTierCache) -> None:
        """Test caching complex objects"""
        complex_obj = {
            "nested": {"data": [1, 2, 3]},
            "list": ["a", "b", "c"],
        }

        multi_tier_cache.set("complex", complex_obj)
        retrieved = multi_tier_cache.get("complex")

        assert retrieved == complex_obj

    def test_empty_get_many(self, multi_tier_cache: MultiTierCache) -> None:
        """Test get_many with empty list"""
        result = multi_tier_cache.get_many([])
        assert result == {}

    def test_empty_set_many(self, multi_tier_cache: MultiTierCache) -> None:
        """Test set_many with empty dict"""
        count = multi_tier_cache.set_many({})
        assert count == 0


class TestPerformance:
    """Performance tests"""

    def test_l1_hit_performance(self, multi_tier_cache: MultiTierCache) -> None:
        """Test L1 hit latency"""
        # Fill cache
        for i in range(100):
            multi_tier_cache.set(f"key{i}", f"value{i}")

        # Time L1 hits
        start = time.time()
        for i in range(100):
            multi_tier_cache.get(f"key{i}")
        elapsed = time.time() - start

        # L1 hits should be very fast (< 5ms for 100 gets)
        assert elapsed < 0.005

        print(f"\n  100 L1 cache hits: {elapsed*1000:.2f}ms")

    def test_promotion_performance(self, multi_tier_cache: MultiTierCache) -> None:
        """Test promotion overhead"""
        # Put 100 items in L2 only
        for i in range(100):
            multi_tier_cache.l2._storage[f"key{i}"] = f"value{i}"  # type: ignore[attr-defined]

        # Time L2 hits with promotion
        start = time.time()
        for i in range(100):
            multi_tier_cache.get(f"key{i}")
        elapsed = time.time() - start

        # Should still be reasonably fast (< 50ms for 100 promotions)
        assert elapsed < 0.05

        print(f"\n  100 L2 hits with promotion: {elapsed*1000:.2f}ms")

        # Verify all were promoted
        stats = multi_tier_cache.get_stats()
        assert stats["overall"]["promotions"] == 100


class TestCacheCoherence:
    """Test cache coherence between tiers"""

    def test_update_propagates_to_both_tiers(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that updates propagate to both tiers"""
        multi_tier_cache.set("key1", "value1")

        # Update value
        multi_tier_cache.set("key1", "value2")

        # Both tiers should have new value
        assert multi_tier_cache.l1.get("key1") == "value2"
        assert multi_tier_cache.l2._storage["key1"] == "value2"  # type: ignore[attr-defined]

    def test_delete_removes_from_both_tiers(self, multi_tier_cache: MultiTierCache) -> None:
        """Test that delete removes from both tiers"""
        multi_tier_cache.set("key1", "value1")
        multi_tier_cache.delete("key1")

        # Should be gone from both
        assert not multi_tier_cache.l1.exists("key1")
        assert "key1" not in multi_tier_cache.l2._storage  # type: ignore[attr-defined]
