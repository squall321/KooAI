"""
Cache decorators

Provides convenient decorators for caching function results.
"""

import functools
import hashlib
import json
import time
from typing import Any, Callable, Optional

import structlog

from .cache_monitor import get_cache_monitor
from .config import get_cache_config
from .multi_tier_cache import get_multi_tier_cache
from .redis_cache import get_cache


logger = structlog.get_logger(__name__)


def _make_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """
    Generate cache key from function and arguments

    Args:
        func: Function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Create key from function name and arguments
    func_name = f"{func.__module__}.{func.__name__}"

    # Serialize arguments
    try:
        args_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    except TypeError:
        # Fallback to string representation
        args_str = str((args, kwargs))

    # Hash for consistent key length
    args_hash = hashlib.md5(args_str.encode()).hexdigest()

    return f"{func_name}:{args_hash}"


def cache_result(
    ttl: Optional[int] = None,
    prefix: Optional[str] = None,
    key_func: Optional[Callable] = None,
    use_multi_tier: bool = True,
    monitor: bool = True,
):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds (None = use default)
        prefix: Cache key prefix
        key_func: Custom function to generate cache key
        use_multi_tier: Use multi-tier cache (L1+L2) instead of L2 only
        monitor: Record metrics for monitoring

    Example:
        @cache_result(ttl=3600, prefix="query:", use_multi_tier=True)
        def expensive_query(user_id: int):
            return database.query(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = get_cache_config()

            if not config.cache_enabled:
                return func(*args, **kwargs)

            # 캐시 선택 (multi-tier 또는 Redis만)
            if use_multi_tier:
                cache = get_multi_tier_cache()
            else:
                cache = get_cache()

            # 모니터
            cache_monitor = get_cache_monitor() if monitor else None

            # Generate cache key
            if key_func is not None:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _make_cache_key(func, args, kwargs)

            # Try to get from cache
            start_time = time.time()
            cached_value = cache.get(cache_key, prefix=prefix)
            duration_ms = (time.time() - start_time) * 1000

            if cached_value is not None:
                logger.debug(
                    "cache_hit",
                    function=func.__name__,
                    key=cache_key,
                )

                # Record metric
                if cache_monitor:
                    cache_monitor.record_get(
                        key=cache_key, hit=True, duration_ms=duration_ms
                    )

                return cached_value

            # Cache miss - execute function
            logger.debug(
                "cache_miss",
                function=func.__name__,
                key=cache_key,
            )

            # Record miss metric
            if cache_monitor:
                cache_monitor.record_get(
                    key=cache_key, hit=False, duration_ms=duration_ms
                )

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            set_start = time.time()
            cache.set(cache_key, result, ttl=ttl, prefix=prefix)
            set_duration_ms = (time.time() - set_start) * 1000

            # Record set metric
            if cache_monitor:
                cache_monitor.record_set(key=cache_key, duration_ms=set_duration_ms)

            return result

        return wrapper

    return decorator


def cache_analysis(
    ttl: Optional[int] = None,
    simulation_id_arg: str = "simulation_id",
    field_name_arg: str = "field_name",
):
    """
    Decorator specifically for caching analysis results

    Args:
        ttl: Time to live (None = use analysis_ttl from config)
        simulation_id_arg: Name of simulation ID argument
        field_name_arg: Name of field name argument

    Example:
        @cache_analysis()
        def analyze_field(simulation_id: str, field_name: str):
            # Expensive analysis
            return results
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            config = get_cache_config()

            if not config.cache_enabled:
                return func(*args, **kwargs)

            # Extract simulation_id and field_name
            # Try to get from kwargs first
            simulation_id = kwargs.get(simulation_id_arg)
            field_name = kwargs.get(field_name_arg)

            # If not in kwargs, try to get from args based on function signature
            if simulation_id is None or field_name is None:
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if simulation_id is None and simulation_id_arg in param_names:
                    idx = param_names.index(simulation_id_arg)
                    if idx < len(args):
                        simulation_id = args[idx]

                if field_name is None and field_name_arg in param_names:
                    idx = param_names.index(field_name_arg)
                    if idx < len(args):
                        field_name = args[idx]

            # Generate cache key
            cache_key = f"{func.__name__}:{simulation_id}:{field_name}"

            # Try to get from cache
            cached_value = cache.get(cache_key, prefix=config.analysis_prefix)
            if cached_value is not None:
                logger.debug(
                    "analysis_cache_hit",
                    function=func.__name__,
                    simulation_id=simulation_id,
                    field_name=field_name,
                )
                return cached_value

            # Cache miss - execute function
            logger.debug(
                "analysis_cache_miss",
                function=func.__name__,
                simulation_id=simulation_id,
                field_name=field_name,
            )

            result = func(*args, **kwargs)

            # Store in cache with analysis TTL
            actual_ttl = ttl if ttl is not None else config.analysis_ttl
            cache.set(cache_key, result, ttl=actual_ttl, prefix=config.analysis_prefix)

            return result

        return wrapper

    return decorator


def invalidate_cache(
    patterns: Optional[list[str]] = None,
    prefix: Optional[str] = None,
):
    """
    Decorator to invalidate cache after function execution

    Args:
        patterns: List of key patterns to invalidate
        prefix: Prefix to clear

    Example:
        @invalidate_cache(prefix="query:")
        def update_user(user_id: int, data: dict):
            database.update(user_id, data)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function first
            result = func(*args, **kwargs)

            # Then invalidate cache
            cache = get_cache()

            if prefix is not None:
                deleted = cache.clear_prefix(prefix)
                logger.info(
                    "cache_invalidated",
                    function=func.__name__,
                    prefix=prefix,
                    deleted_keys=deleted,
                )

            if patterns is not None:
                for pattern in patterns:
                    cache.delete(pattern)
                logger.info(
                    "cache_invalidated",
                    function=func.__name__,
                    patterns=patterns,
                )

            return result

        return wrapper

    return decorator


def cache_async_result(
    ttl: Optional[int] = None,
    prefix: Optional[str] = None,
):
    """
    Decorator for caching async function results

    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix

    Example:
        @cache_async_result(ttl=3600)
        async def fetch_data(user_id: int):
            return await api.get(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            config = get_cache_config()

            if not config.cache_enabled:
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = _make_cache_key(func, args, kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key, prefix=prefix)
            if cached_value is not None:
                logger.debug(
                    "async_cache_hit",
                    function=func.__name__,
                    key=cache_key,
                )
                return cached_value

            # Cache miss - execute function
            logger.debug(
                "async_cache_miss",
                function=func.__name__,
                key=cache_key,
            )

            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl, prefix=prefix)

            return result

        return wrapper

    return decorator
