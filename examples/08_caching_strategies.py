"""
캐싱 전략 및 모니터링

이 예제는 다층 캐싱(Multi-tier caching)과 캐시 모니터링을 시연합니다.
"""

import time
from pathlib import Path

from src.infrastructure.cache import (
    CacheMonitor,
    LRUCache,
    MultiTierCache,
    get_cache_monitor,
    get_multi_tier_cache,
)


def example_lru_cache():
    """LRU 캐시 기본 사용"""
    print("=" * 60)
    print("Example 1: LRU Cache (L1 - In-Memory)")
    print("=" * 60)

    # LRU 캐시 생성 (최대 5개 엔트리)
    cache = LRUCache(max_size=5, default_ttl=10)

    print("\n1️⃣  Adding 5 items:")
    for i in range(5):
        key = f"item_{i}"
        value = f"value_{i}"
        cache.set(key, value)
        print(f"   Set: {key} = {value}")

    print(f"\n   Cache size: {len(cache)}")
    print(f"   Stats: {cache.get_stats()}")

    print("\n2️⃣  Adding 6th item (triggers LRU eviction):")
    cache.set("item_5", "value_5")
    print(f"   Set: item_5 = value_5")
    print(f"   Cache size: {len(cache)}")

    # item_0 should be evicted (least recently used)
    print(f"\n   item_0 exists: {cache.exists('item_0')} (evicted)")
    print(f"   item_1 exists: {cache.exists('item_1')} (still in cache)")

    print("\n3️⃣  Access pattern (updating LRU order):")
    cache.get("item_1")  # Access item_1
    print("   Accessed: item_1")

    # Add new item, item_2 should be evicted (not item_1)
    cache.set("item_6", "value_6")
    print("   Set: item_6 = value_6")
    print(f"   item_1 exists: {cache.exists('item_1')} (still in cache - recently used)")
    print(f"   item_2 exists: {cache.exists('item_2')} (evicted - least recently used)")

    print(f"\n   Final stats: {cache.get_stats()}")
    print()


def example_multi_tier_cache():
    """Multi-tier 캐시 사용"""
    print("=" * 60)
    print("Example 2: Multi-Tier Cache (L1 + L2)")
    print("=" * 60)

    # Multi-tier 캐시는 싱글톤으로 사용
    cache = get_multi_tier_cache()

    # L1 캐시 클리어 (데모용)
    cache.clear_l1()

    print("\n1️⃣  First access (cold cache):")
    start = time.time()
    value = cache.get("demo_key", prefix="test")
    elapsed_ms = (time.time() - start) * 1000
    print(f"   GET demo_key: {value}")
    print(f"   Time: {elapsed_ms:.2f} ms (MISS)")

    print("\n2️⃣  Set value:")
    cache.set("demo_key", {"data": "Hello, World!"}, ttl=60, prefix="test")
    print(f"   SET demo_key = {{'data': 'Hello, World!'}}")

    print("\n3️⃣  Second access (L1 cache hit):")
    start = time.time()
    value = cache.get("demo_key", prefix="test")
    elapsed_ms = (time.time() - start) * 1000
    print(f"   GET demo_key: {value}")
    print(f"   Time: {elapsed_ms:.2f} ms (L1 HIT - very fast!)")

    print("\n4️⃣  Clear L1, access again (L2 cache hit):")
    cache.clear_l1()
    print("   L1 cleared")

    start = time.time()
    value = cache.get("demo_key", prefix="test")
    elapsed_ms = (time.time() - start) * 1000
    print(f"   GET demo_key: {value}")
    print(f"   Time: {elapsed_ms:.2f} ms (L2 HIT - promoted to L1)")

    print("\n5️⃣  Third access (L1 cache hit again):")
    start = time.time()
    value = cache.get("demo_key", prefix="test")
    elapsed_ms = (time.time() - start) * 1000
    print(f"   GET demo_key: {value}")
    print(f"   Time: {elapsed_ms:.2f} ms (L1 HIT)")

    print("\n6️⃣  Cache statistics:")
    stats = cache.get_stats()
    print(f"   L1 hits: {stats['overall']['l1_hits']}")
    print(f"   L2 hits: {stats['overall']['l2_hits']}")
    print(f"   Total misses: {stats['overall']['total_misses']}")
    print(f"   Overall hit rate: {stats['overall']['hit_rate']:.1%}")
    print(f"   Promotions (L2→L1): {stats['overall']['promotions']}")
    print()


def example_cache_monitoring():
    """캐시 모니터링"""
    print("=" * 60)
    print("Example 3: Cache Monitoring & Metrics")
    print("=" * 60)

    monitor = get_cache_monitor()
    monitor.reset()  # Reset for demo

    print("\n1️⃣  Simulating cache operations:")

    # Simulate 100 cache operations
    for i in range(100):
        key = f"key_{i % 10}"  # 10 unique keys (hot keys)

        if i % 3 == 0:  # 33% hit rate
            # Simulate L1 hit (fast)
            monitor.record_get(key, hit=True, duration_ms=0.5, tier="l1")
        elif i % 3 == 1:  # 33% L2 hit
            # Simulate L2 hit (slower)
            monitor.record_get(key, hit=True, duration_ms=2.0, tier="l2")
        else:  # 33% miss
            # Simulate miss (slowest)
            monitor.record_get(key, hit=False, duration_ms=50.0)
            # Simulate set after miss
            monitor.record_set(key, duration_ms=1.5)

    print(f"   Simulated 100 operations")

    print("\n2️⃣  Cache statistics:")
    stats = monitor.get_stats()
    print(f"   Total requests: {stats.total_requests}")
    print(f"   Hits: {stats.hits}")
    print(f"   Misses: {stats.misses}")
    print(f"   Hit rate: {stats.hit_rate:.1%}")
    print(f"   Avg response time: {stats.avg_response_time_ms:.2f} ms")
    print(f"   P95 response time: {stats.p95_response_time_ms:.2f} ms")
    print(f"   P99 response time: {stats.p99_response_time_ms:.2f} ms")

    print("\n3️⃣  Tier distribution:")
    tier_stats = monitor.get_tier_stats()
    for tier, count in sorted(tier_stats.items()):
        percentage = count / stats.total_requests * 100
        print(f"   {tier.upper()}: {count} ({percentage:.1f}%)")

    print("\n4️⃣  Hot keys (top 5):")
    hot_keys = monitor.get_hot_keys(top_n=5)
    for key, access_count in hot_keys:
        print(f"   {key}: {access_count} accesses")

    print("\n5️⃣  Full report:")
    print()
    print(monitor.get_report())


def example_cache_decorator():
    """캐시 데코레이터 사용"""
    print("=" * 60)
    print("Example 4: Cache Decorator with Monitoring")
    print("=" * 60)

    from src.infrastructure.cache import cache_result

    # 캐시 데코레이터 적용
    @cache_result(ttl=60, prefix="fib", use_multi_tier=True, monitor=True)
    def fibonacci(n: int) -> int:
        """피보나치 수열 (expensive computation)"""
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    print("\n1️⃣  First call (cache miss, slow):")
    start = time.time()
    result = fibonacci(30)
    elapsed = time.time() - start
    print(f"   fibonacci(30) = {result}")
    print(f"   Time: {elapsed:.3f} seconds")

    print("\n2️⃣  Second call (cache hit, fast):")
    start = time.time()
    result = fibonacci(30)
    elapsed = time.time() - start
    print(f"   fibonacci(30) = {result}")
    print(f"   Time: {elapsed:.6f} seconds (from cache!)")

    print("\n3️⃣  Cache monitor stats:")
    monitor = get_cache_monitor()
    stats = monitor.get_stats(time_window_seconds=60)
    print(f"   Recent hit rate: {stats.hit_rate:.1%}")
    print()


def example_batch_operations():
    """배치 캐시 작업"""
    print("=" * 60)
    print("Example 5: Batch Cache Operations")
    print("=" * 60)

    cache = get_multi_tier_cache()

    print("\n1️⃣  Batch set (10 items):")
    data = {f"batch_key_{i}": f"batch_value_{i}" for i in range(10)}

    start = time.time()
    count = cache.set_many(data, ttl=60, prefix="batch")
    elapsed_ms = (time.time() - start) * 1000

    print(f"   Set {count} items in {elapsed_ms:.2f} ms")

    print("\n2️⃣  Batch get:")
    keys = [f"batch_key_{i}" for i in range(10)]

    start = time.time()
    results = cache.get_many(keys, prefix="batch")
    elapsed_ms = (time.time() - start) * 1000

    print(f"   Retrieved {len(results)} items in {elapsed_ms:.2f} ms")
    print(f"   First 3 items: {list(results.items())[:3]}")

    print("\n3️⃣  Partial batch get (some in L1, some in L2):")
    # Clear L1 for half the keys
    cache.clear_l1()
    print("   L1 cleared")

    # Access half the keys (promote to L1)
    for i in range(5):
        cache.get(f"batch_key_{i}", prefix="batch")

    # Now get all keys
    start = time.time()
    results = cache.get_many(keys, prefix="batch")
    elapsed_ms = (time.time() - start) * 1000

    print(f"   Retrieved {len(results)} items in {elapsed_ms:.2f} ms")
    print(f"   (5 from L1, 5 from L2)")

    stats = cache.get_stats()
    print(f"\n   L1 hits: {stats['overall']['l1_hits']}")
    print(f"   L2 hits: {stats['overall']['l2_hits']}")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         캐싱 전략 및 모니터링 예제                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    try:
        # Example 1: LRU 캐시
        example_lru_cache()

        # Example 2: Multi-tier 캐시
        example_multi_tier_cache()

        # Example 3: 캐시 모니터링
        example_cache_monitoring()

        # Example 4: 캐시 데코레이터
        example_cache_decorator()

        # Example 5: 배치 작업
        example_batch_operations()

        print("=" * 60)
        print("✅ 모든 예제 완료!")
        print("=" * 60)
        print()

        print("💡 주요 기능:")
        print("   1. LRU 캐시 (로컬 인메모리, 빠른 접근)")
        print("   2. Multi-tier 캐싱 (L1 + L2 전략)")
        print("   3. 자동 L2→L1 프로모션")
        print("   4. 실시간 캐시 모니터링")
        print("   5. 핫 키 감지")
        print("   6. 응답 시간 분석 (P95, P99)")
        print()

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()
