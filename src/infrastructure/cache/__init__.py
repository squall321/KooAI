"""
Caching infrastructure

Provides multi-tier caching with various strategies:
- Multi-tier caching (L1: LRU in-memory + L2: Redis)
- Result caching (analysis results, query results)
- Cache monitoring and metrics
- Session caching
- Memoization decorators
- Cache invalidation strategies
"""

from .cache_monitor import CacheMonitor, CacheStats, get_cache_monitor
from .config import CacheConfig, get_cache_config
from .decorators import cache_analysis, cache_result, invalidate_cache
from .lru_cache import LRUCache
from .multi_tier_cache import MultiTierCache, get_multi_tier_cache
from .redis_cache import RedisCache, get_cache

__all__ = [
    # Core caches
    "RedisCache",
    "get_cache",
    "LRUCache",
    "MultiTierCache",
    "get_multi_tier_cache",
    # Monitoring
    "CacheMonitor",
    "CacheStats",
    "get_cache_monitor",
    # Decorators
    "cache_result",
    "cache_analysis",
    "invalidate_cache",
    # Config
    "CacheConfig",
    "get_cache_config",
]
