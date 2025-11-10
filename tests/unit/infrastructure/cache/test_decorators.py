"""
Tests for cache decorators
"""

import asyncio
from typing import Any, Optional
from unittest.mock import Mock, patch, MagicMock
import pytest
import time

from src.infrastructure.cache.decorators import (
    cache_result,
    cache_analysis,
    invalidate_cache,
    cache_async_result,
)


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create mock cache"""
    cache = MagicMock()
    cache.config.cache_enabled = True
    cache.config.default_ttl = 300
    cache.config.analysis_ttl = 600
    cache.config.analysis_prefix = "analysis:"
    return cache


def test_cache_result_basic(mock_cache: MagicMock) -> None:
    """Test basic cache_result decorator"""
    call_count = 0

    @cache_result()
    def expensive_function(x: int, y: int) -> int:
        nonlocal call_count
        call_count += 1
        return x + y

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            # First call - cache miss
            mock_cache.get.return_value = None
            result1 = expensive_function(1, 2)
            assert result1 == 3
            assert call_count == 1
            mock_cache.set.assert_called_once()

            # Second call - cache hit
            mock_cache.get.return_value = 3
            result2 = expensive_function(1, 2)
            assert result2 == 3
            assert call_count == 1  # Function not called again


def test_cache_result_with_kwargs(mock_cache: MagicMock) -> None:
    """Test cache_result with keyword arguments"""

    @cache_result()
    def function_with_kwargs(a: int, b: int = 10, c: int = 20) -> int:
        return a + b + c

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = function_with_kwargs(5, b=15, c=25)
            assert result == 45

            # Verify cache.set was called
            assert mock_cache.set.called


def test_cache_result_custom_ttl(mock_cache: MagicMock) -> None:
    """Test cache_result with custom TTL"""

    @cache_result(ttl=120)
    def cached_function(x: int) -> int:
        return x * 2

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = cached_function(5)
            assert result == 10

            # Verify custom TTL was used
            call_args = mock_cache.set.call_args
            assert call_args[1]["ttl"] == 120


def test_cache_result_custom_prefix(mock_cache: MagicMock) -> None:
    """Test cache_result with custom prefix"""

    @cache_result(prefix="custom:")
    def cached_function(x: int) -> int:
        return x * 2

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = cached_function(5)
            assert result == 10

            # Verify custom prefix was used
            call_args = mock_cache.set.call_args
            assert call_args[1]["prefix"] == "custom:"


def test_cache_result_disabled(mock_cache: MagicMock) -> None:
    """Test cache_result when cache is disabled"""
    mock_cache.config.cache_enabled = False
    call_count = 0

    @cache_result()
    def uncached_function(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            result1 = uncached_function(5)
            result2 = uncached_function(5)

            assert result1 == 10
            assert result2 == 10
            assert call_count == 2  # Function called both times

            # Cache should not be used
            mock_cache.get.assert_not_called()
            mock_cache.set.assert_not_called()


def test_cache_analysis_decorator(mock_cache: MagicMock) -> None:
    """Test cache_analysis decorator"""

    @cache_analysis()
    def analyze_field(simulation_id: str, field_name: str, options: Optional[Any] = None) -> str:
        return f"Analysis of {simulation_id}:{field_name}"

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = analyze_field(simulation_id="sim123", field_name="velocity")
            assert result == "Analysis of sim123:velocity"

            # Verify analysis prefix was used
            call_args = mock_cache.set.call_args
            assert call_args[1]["prefix"] == "analysis:"
            assert call_args[1]["ttl"] == 600  # analysis_ttl


def test_cache_analysis_custom_args(mock_cache: MagicMock) -> None:
    """Test cache_analysis with custom argument names"""

    @cache_analysis(simulation_id_arg="sim_id", field_name_arg="field")
    def custom_analysis(sim_id: str, field: str, threshold: float = 0.5) -> str:
        return f"Analysis of {sim_id}:{field}"

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = custom_analysis(sim_id="sim456", field="pressure")
            assert result == "Analysis of sim456:pressure"

            # Verify cache key includes sim_id and field
            call_args = mock_cache.set.call_args
            cache_key = call_args[0][0]
            assert "sim456" in cache_key
            assert "pressure" in cache_key


def test_invalidate_cache_decorator(mock_cache: MagicMock) -> None:
    """Test invalidate_cache decorator"""

    @invalidate_cache(patterns=["key1", "key2"])
    def update_function(value: str) -> str:
        return f"Updated: {value}"

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        result = update_function("test")
        assert result == "Updated: test"

        # Verify cache keys were deleted
        assert mock_cache.delete.call_count == 2


def test_invalidate_cache_with_prefix(mock_cache: MagicMock) -> None:
    """Test invalidate_cache with prefix"""

    @invalidate_cache(prefix="user:")
    def update_user(user_id: int) -> str:
        return f"Updated user {user_id}"

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        result = update_user(123)
        assert result == "Updated user 123"

        # Verify prefix was cleared
        mock_cache.clear_prefix.assert_called_once_with("user:")


def test_invalidate_cache_both_keys_and_prefix(mock_cache: MagicMock) -> None:
    """Test invalidate_cache with both patterns and prefix"""

    @invalidate_cache(patterns=["key1"], prefix="data:")
    def update_data() -> str:
        return "Updated"

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        result = update_data()
        assert result == "Updated"

        # Verify both operations
        mock_cache.delete.assert_called_once_with("key1")
        mock_cache.clear_prefix.assert_called_once_with("data:")


@pytest.mark.asyncio
async def test_cache_async_result(mock_cache: MagicMock) -> None:
    """Test cache_async_result decorator for async functions"""

    @cache_async_result()
    async def async_expensive_function(x: int, y: int) -> int:
        await asyncio.sleep(0.01)  # Simulate async work
        return x + y

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            # First call - cache miss
            mock_cache.get.return_value = None
            result1 = await async_expensive_function(1, 2)
            assert result1 == 3
            mock_cache.set.assert_called_once()

            # Second call - cache hit
            mock_cache.get.return_value = 3
            result2 = await async_expensive_function(1, 2)
            assert result2 == 3


def test_cache_key_generation(mock_cache: MagicMock) -> None:
    """Test cache key generation from function arguments"""

    @cache_result()
    def function_with_many_args(a: int, b: int, c: int = 10, d: int = 20) -> int:
        return a + b + c + d

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            # Call with different argument combinations
            function_with_many_args(1, 2, c=30)
            key1 = mock_cache.set.call_args[0][0]

            mock_cache.reset_mock()
            function_with_many_args(1, 2, c=40)
            key2 = mock_cache.set.call_args[0][0]

            # Keys should be different
            assert key1 != key2


def test_cache_result_with_none_return(mock_cache: MagicMock) -> None:
    """Test caching when function returns None"""

    @cache_result()
    def function_returning_none() -> None:
        return None

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = function_returning_none()
            assert result is None

            # None should still be cached
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            assert call_args[0][1] is None


def test_cache_result_with_exception(mock_cache: MagicMock) -> None:
    """Test cache behavior when function raises exception"""

    @cache_result()
    def function_with_error() -> None:
        raise ValueError("Test error")

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            with pytest.raises(ValueError, match="Test error"):
                function_with_error()

            # Exception should not be cached
            mock_cache.set.assert_not_called()


def test_different_functions_different_keys(mock_cache: MagicMock) -> None:
    """Test that different functions generate different cache keys"""

    @cache_result()
    def function1(x: int) -> int:
        return x * 2

    @cache_result()
    def function2(x: int) -> int:
        return x * 3

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            function1(5)
            key1 = mock_cache.set.call_args[0][0]

            mock_cache.reset_mock()
            function2(5)
            key2 = mock_cache.set.call_args[0][0]

            # Different functions should have different keys
            assert key1 != key2
            assert "function1" in key1
            assert "function2" in key2


def test_cache_result_preserves_function_metadata() -> None:
    """Test that decorator preserves function metadata"""

    @cache_result()
    def documented_function(x: int) -> int:
        """This is a documented function"""
        return x * 2

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This is a documented function"


@pytest.mark.asyncio
async def test_cache_async_preserves_function_metadata() -> None:
    """Test that async decorator preserves function metadata"""

    @cache_async_result()
    async def async_documented_function(x: int) -> int:
        """This is an async documented function"""
        return x * 2

    assert async_documented_function.__name__ == "async_documented_function"
    assert async_documented_function.__doc__ == "This is an async documented function"


def test_complex_data_types(mock_cache: MagicMock) -> None:
    """Test caching with complex data types"""

    @cache_result()
    def function_with_complex_return() -> dict[str, Any]:
        return {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (4, 5, 6),
            "string": "test",
        }

    with patch("src.infrastructure.cache.decorators.get_cache", return_value=mock_cache):
        with patch(
            "src.infrastructure.cache.decorators.get_cache_config",
            return_value=mock_cache.config,
        ):
            mock_cache.get.return_value = None

            result = function_with_complex_return()

            # Verify complex data was passed to cache
            call_args = mock_cache.set.call_args
            cached_value = call_args[0][1]
            assert "list" in cached_value
            assert "dict" in cached_value
