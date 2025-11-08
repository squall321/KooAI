"""
Unit tests for LRU Cache

Tests the in-memory LRU cache implementation.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.cache.lru_cache import LRUCache, CacheEntry


class TestCacheEntry:
    """Test CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test creating cache entry"""
        entry = CacheEntry(value="test", expires_at=time.time() + 60)

        assert entry.value == "test"
        assert entry.access_count == 0
        assert entry.created_at <= time.time()
        assert entry.last_access <= time.time()

    def test_is_expired(self):
        """Test expiration check"""
        # Not expired
        entry = CacheEntry(value="test", expires_at=time.time() + 60)
        assert not entry.is_expired()

        # Expired
        entry_expired = CacheEntry(value="test", expires_at=time.time() - 1)
        assert entry_expired.is_expired()

    def test_access_tracking(self):
        """Test access counting"""
        entry = CacheEntry(value="test", expires_at=time.time() + 60)

        initial_count = entry.access_count
        initial_time = entry.last_access

        time.sleep(0.01)
        entry.access()

        assert entry.access_count == initial_count + 1
        assert entry.last_access > initial_time


class TestLRUCacheBasicOperations:
    """Test basic cache operations"""

    @pytest.fixture
    def cache(self):
        """Create cache instance"""
        return LRUCache(max_size=10, default_ttl=60)

    def test_cache_initialization(self):
        """Test cache initialization"""
        cache = LRUCache(max_size=100, default_ttl=300)

        assert cache.max_size == 100
        assert cache.default_ttl == 300
        assert len(cache) == 0

    def test_set_and_get(self, cache):
        """Test basic set and get"""
        cache.set("key1", "value1")

        value = cache.get("key1")
        assert value == "value1"

    def test_get_nonexistent_key(self, cache):
        """Test getting non-existent key"""
        value = cache.get("nonexistent")
        assert value is None

    def test_set_overwrites_existing(self, cache):
        """Test that set overwrites existing value"""
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        value = cache.get("key1")
        assert value == "value2"
        assert len(cache) == 1

    def test_delete_key(self, cache):
        """Test deleting key"""
        cache.set("key1", "value1")
        assert cache.exists("key1")

        result = cache.delete("key1")
        assert result is True
        assert not cache.exists("key1")

    def test_delete_nonexistent_key(self, cache):
        """Test deleting non-existent key"""
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear_cache(self, cache):
        """Test clearing all cache"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        count = cache.clear()
        assert count == 3
        assert len(cache) == 0

    def test_exists(self, cache):
        """Test exists check"""
        cache.set("key1", "value1")

        assert cache.exists("key1")
        assert not cache.exists("key2")

    def test_contains_operator(self, cache):
        """Test 'in' operator"""
        cache.set("key1", "value1")

        assert "key1" in cache
        assert "key2" not in cache


class TestLRUEviction:
    """Test LRU eviction policy"""

    def test_eviction_when_full(self):
        """Test that least recently used item is evicted when cache is full"""
        cache = LRUCache(max_size=3, default_ttl=60)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new item - should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still exists
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # Still exists
        assert cache.get("key4") == "value4"  # New item

    def test_eviction_order(self):
        """Test eviction happens in correct LRU order"""
        cache = LRUCache(max_size=3, default_ttl=60)

        # Add items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access in specific order
        cache.get("key1")  # key1 is most recent
        cache.get("key2")  # key2 is most recent
        # key3 is least recent

        # Add new item - should evict key3
        cache.set("key4", "value4")

        assert "key1" in cache
        assert "key2" in cache
        assert "key3" not in cache
        assert "key4" in cache

    def test_update_moves_to_end(self):
        """Test that updating a key moves it to end (most recent)"""
        cache = LRUCache(max_size=3, default_ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Update key1 (makes it most recent)
        cache.set("key1", "updated")

        # Add new item - should evict key2 (now least recent)
        cache.set("key4", "value4")

        assert cache.get("key1") == "updated"
        assert cache.get("key2") is None  # Evicted
        assert "key3" in cache
        assert "key4" in cache

    def test_eviction_statistics(self):
        """Test eviction statistics tracking"""
        cache = LRUCache(max_size=2, default_ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Evicts key1
        cache.set("key4", "value4")  # Evicts key2

        stats = cache.get_stats()
        assert stats["evictions"] == 2


class TestTTLAndExpiration:
    """Test TTL and expiration"""

    def test_custom_ttl(self):
        """Test custom TTL per key"""
        cache = LRUCache(default_ttl=60)

        cache.set("key1", "value1", ttl=1)  # 1 second TTL

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_default_ttl(self):
        """Test default TTL is used when not specified"""
        cache = LRUCache(default_ttl=1)

        cache.set("key1", "value1")  # Uses default TTL

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_expired_key_returns_none(self):
        """Test that expired keys return None"""
        cache = LRUCache(default_ttl=60)

        cache.set("key1", "value1", ttl=1)
        time.sleep(1.1)

        value = cache.get("key1")
        assert value is None

    def test_exists_checks_expiration(self):
        """Test that exists() checks expiration"""
        cache = LRUCache(default_ttl=60)

        cache.set("key1", "value1", ttl=1)
        assert cache.exists("key1")

        time.sleep(1.1)
        assert not cache.exists("key1")

    def test_cleanup_expired(self):
        """Test manual cleanup of expired entries"""
        cache = LRUCache(default_ttl=60)

        # Add items with short TTL
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=1)
        cache.set("key3", "value3", ttl=60)  # Long TTL

        # Wait for expiration
        time.sleep(1.1)

        # Run cleanup
        cleaned = cache.cleanup_expired()

        assert cleaned == 2
        assert cache.get("key3") == "value3"
        assert len(cache) == 1

    def test_expiration_statistics(self):
        """Test expiration statistics tracking"""
        cache = LRUCache(default_ttl=60)

        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=1)

        time.sleep(1.1)

        # Trigger expirations via get
        cache.get("key1")
        cache.get("key2")

        stats = cache.get_stats()
        assert stats["expirations"] == 2


class TestCacheStatistics:
    """Test cache statistics"""

    @pytest.fixture
    def cache(self):
        """Create cache instance"""
        return LRUCache(max_size=10, default_ttl=60)

    def test_hit_statistics(self, cache):
        """Test hit statistics"""
        cache.set("key1", "value1")

        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_hit_rate_calculation(self, cache):
        """Test hit rate calculation"""
        cache.set("key1", "value1")

        # 3 hits, 1 miss
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.75  # 3/4

    def test_hit_rate_with_no_requests(self, cache):
        """Test hit rate when no requests made"""
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.0

    def test_reset_statistics(self, cache):
        """Test resetting statistics"""
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2")

        cache.reset_stats()

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["expirations"] == 0

    def test_size_statistics(self, cache):
        """Test size statistics"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 10


class TestThreadSafety:
    """Test thread safety"""

    def test_concurrent_reads_writes(self):
        """Test concurrent reads and writes"""
        cache = LRUCache(max_size=100, default_ttl=60)

        def writer(thread_id):
            for i in range(100):
                cache.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")

        def reader(thread_id):
            results = []
            for i in range(100):
                value = cache.get(f"key_{thread_id}_{i}")
                results.append(value)
            return results

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Start writers
            write_futures = [executor.submit(writer, i) for i in range(5)]
            # Start readers
            read_futures = [executor.submit(reader, i) for i in range(5)]

            # Wait for completion
            for future in write_futures + read_futures:
                future.result()

        # Cache should be in consistent state
        stats = cache.get_stats()
        assert stats["size"] <= 100

    def test_concurrent_evictions(self):
        """Test concurrent evictions don't cause issues"""
        cache = LRUCache(max_size=10, default_ttl=60)

        def fill_cache(thread_id):
            for i in range(50):
                cache.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fill_cache, i) for i in range(5)]
            for future in futures:
                future.result()

        # Cache should respect max_size
        assert len(cache) <= 10

    def test_concurrent_cleanup(self):
        """Test concurrent cleanup operations"""
        cache = LRUCache(max_size=100, default_ttl=60)

        # Add items with short TTL
        for i in range(50):
            cache.set(f"key_{i}", f"value_{i}", ttl=1)

        time.sleep(1.1)

        # Run cleanup from multiple threads
        def cleanup():
            return cache.cleanup_expired()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(cleanup) for _ in range(5)]
            results = [f.result() for f in futures]

        # Total cleaned should be 50 (across all threads)
        total_cleaned = sum(results)
        assert total_cleaned == 50
        assert len(cache) == 0


class TestEdgeCases:
    """Test edge cases"""

    def test_zero_size_cache(self):
        """Test cache with size 0"""
        cache = LRUCache(max_size=0, default_ttl=60)

        # Can't store anything
        cache.set("key1", "value1")
        assert cache.get("key1") is None

    def test_very_short_ttl(self):
        """Test very short TTL"""
        cache = LRUCache(default_ttl=60)

        cache.set("key1", "value1", ttl=0.1)
        time.sleep(0.15)

        assert cache.get("key1") is None

    def test_large_values(self):
        """Test caching large values"""
        cache = LRUCache(max_size=10, default_ttl=60)

        large_value = "x" * 1_000_000  # 1MB string
        cache.set("large", large_value)

        retrieved = cache.get("large")
        assert retrieved == large_value

    def test_none_value(self):
        """Test storing None value"""
        cache = LRUCache(max_size=10, default_ttl=60)

        cache.set("none_key", None)

        # Should be able to distinguish between cached None and missing key
        assert cache.exists("none_key")
        assert cache.get("none_key") is None

    def test_complex_objects(self):
        """Test caching complex objects"""
        cache = LRUCache(max_size=10, default_ttl=60)

        complex_obj = {"list": [1, 2, 3], "dict": {"nested": "value"}, "set": {1, 2, 3}}

        cache.set("complex", complex_obj)
        retrieved = cache.get("complex")

        assert retrieved == complex_obj

    def test_many_keys(self):
        """Test cache with many keys"""
        cache = LRUCache(max_size=1000, default_ttl=60)

        # Add 1000 keys
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")

        assert len(cache) == 1000

        # Add one more - should evict first
        cache.set("key_1000", "value_1000")

        assert len(cache) == 1000
        assert "key_0" not in cache  # First one evicted
        assert "key_1000" in cache


class TestLRUCachePerformance:
    """Performance tests"""

    def test_get_performance(self):
        """Test get operation performance"""
        cache = LRUCache(max_size=10000, default_ttl=60)

        # Fill cache
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")

        # Time get operations
        start = time.time()
        for i in range(1000):
            cache.get(f"key_{i}")
        elapsed = time.time() - start

        # Should be very fast (< 10ms for 1000 gets)
        assert elapsed < 0.01

        print(f"\n  1000 cache gets: {elapsed*1000:.2f}ms")

    def test_set_performance(self):
        """Test set operation performance"""
        cache = LRUCache(max_size=10000, default_ttl=60)

        start = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        elapsed = time.time() - start

        # Should be fast (< 20ms for 1000 sets)
        assert elapsed < 0.02

        print(f"\n  1000 cache sets: {elapsed*1000:.2f}ms")
