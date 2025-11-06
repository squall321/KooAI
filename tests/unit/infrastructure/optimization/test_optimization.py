"""
Tests for optimization utilities
"""

import time
import gzip
import zlib
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.infrastructure.optimization.query_optimizer import (
    QueryOptimizer,
    optimize_query,
    batch_query,
    ConnectionPoolManager,
    IndexManager,
)
from src.infrastructure.optimization.profiling import (
    Profiler,
    profile_function,
    measure_time,
    PerformanceMonitor,
)
from src.infrastructure.optimization.compression import (
    compress_response,
    decompress_response,
    should_compress,
    CompressionMiddleware,
)


# ===== Query Optimizer Tests =====


def test_batch_process():
    """Test batch processing"""
    optimizer = QueryOptimizer()

    items = list(range(100))

    def processor(batch):
        return [x * 2 for x in batch]

    results = optimizer.batch_process(items, processor, batch_size=10)

    assert len(results) == 100
    assert results[0] == 0
    assert results[50] == 100
    assert results[99] == 198


def test_chunk_list():
    """Test list chunking"""
    optimizer = QueryOptimizer()

    items = list(range(10))
    chunks = list(optimizer.chunk_list(items, chunk_size=3))

    assert len(chunks) == 4
    assert chunks[0] == [0, 1, 2]
    assert chunks[1] == [3, 4, 5]
    assert chunks[2] == [6, 7, 8]
    assert chunks[3] == [9]


def test_optimize_query_decorator():
    """Test optimize_query decorator"""
    call_count = 0

    @optimize_query(timeout=1.0)
    def sample_query(value):
        nonlocal call_count
        call_count += 1
        return value * 2

    result = sample_query(5)
    assert result == 10
    assert call_count == 1


def test_batch_query_decorator():
    """Test batch_query decorator"""

    @batch_query(batch_size=3, key_param="ids")
    def fetch_items(ids):
        return [{"id": id, "value": id * 2} for id in ids]

    # Test with small list (no batching)
    result = fetch_items(ids=[1, 2])
    assert len(result) == 2
    assert result[0]["id"] == 1

    # Test with large list (batching required)
    result = fetch_items(ids=list(range(10)))
    assert len(result) == 10
    assert result[9]["id"] == 9


def test_connection_pool_manager():
    """Test connection pool manager"""
    pool_manager = ConnectionPoolManager(
        pool_size=5, max_overflow=2, pool_timeout=30.0, pool_recycle=3600
    )

    config = pool_manager.get_pool_config()
    assert config["pool_size"] == 5
    assert config["max_overflow"] == 2
    assert config["pool_timeout"] == 30.0
    assert config["pool_recycle"] == 3600

    stats = pool_manager.get_pool_stats()
    assert "pool_size" in stats
    assert "max_overflow" in stats


def test_index_manager():
    """Test index manager"""
    index_manager = IndexManager()

    # Test index suggestion
    suggestions = index_manager.suggest_indexes(
        table_name="simulations",
        columns=["status", "created_at"],
        query_pattern="WHERE status = ? ORDER BY created_at",
    )

    assert len(suggestions) > 0
    assert "CREATE INDEX" in suggestions[0]
    assert "simulations" in suggestions[0]


# ===== Profiling Tests =====


def test_profiler_measure():
    """Test profiler measure context manager"""
    profiler = Profiler()

    with profiler.measure("test_operation"):
        time.sleep(0.1)

    metrics = profiler.get_metrics()
    assert "test_operation" in metrics
    assert metrics["test_operation"]["count"] == 1
    assert metrics["test_operation"]["total_time"] >= 0.1
    assert metrics["test_operation"]["avg_time"] >= 0.1


def test_profiler_multiple_measurements():
    """Test profiler with multiple measurements"""
    profiler = Profiler()

    for _ in range(3):
        with profiler.measure("repeated_operation"):
            time.sleep(0.05)

    metrics = profiler.get_metrics()
    assert metrics["repeated_operation"]["count"] == 3
    assert metrics["repeated_operation"]["total_time"] >= 0.15
    assert metrics["repeated_operation"]["min_time"] >= 0.05
    assert metrics["repeated_operation"]["max_time"] >= 0.05


def test_profile_function_decorator():
    """Test profile_function decorator"""

    @profile_function()
    def slow_function(n):
        time.sleep(0.05)
        return n * 2

    result = slow_function(5)
    assert result == 10

    # Function should complete without errors


def test_measure_time_context():
    """Test measure_time context manager"""
    with measure_time("test_operation") as timer:
        time.sleep(0.05)

    # Timer should have recorded time
    assert timer is not None


def test_performance_monitor():
    """Test performance monitor"""
    monitor = PerformanceMonitor()

    # Record some metrics
    monitor.record_metric("query_time", 0.1)
    monitor.record_metric("query_time", 0.2)
    monitor.record_metric("parse_time", 0.3)

    metrics = monitor.get_metrics()
    assert "query_time" in metrics
    assert "parse_time" in metrics
    assert len(metrics["query_time"]) == 2
    assert len(metrics["parse_time"]) == 1

    stats = monitor.get_statistics()
    assert "query_time" in stats
    assert stats["query_time"]["count"] == 2
    assert stats["query_time"]["mean"] == 0.15


def test_performance_monitor_percentiles():
    """Test performance monitor percentile calculations"""
    monitor = PerformanceMonitor()

    # Record metrics
    for i in range(100):
        monitor.record_metric("test", i / 100.0)

    stats = monitor.get_statistics()
    assert "test" in stats
    assert "p50" in stats["test"]
    assert "p95" in stats["test"]
    assert "p99" in stats["test"]


def test_profiler_clear():
    """Test profiler clear functionality"""
    profiler = Profiler()

    with profiler.measure("operation1"):
        time.sleep(0.01)

    profiler.clear()
    metrics = profiler.get_metrics()
    assert len(metrics) == 0


# ===== Compression Tests =====


def test_compress_response_gzip():
    """Test gzip compression"""
    data = "Hello World" * 100
    compressed = compress_response(data, method="gzip")

    assert isinstance(compressed, bytes)
    assert len(compressed) < len(data.encode("utf-8"))

    # Verify can be decompressed
    decompressed = gzip.decompress(compressed)
    assert decompressed.decode("utf-8") == data


def test_compress_response_zlib():
    """Test zlib compression"""
    data = "Hello World" * 100
    compressed = compress_response(data, method="zlib")

    assert isinstance(compressed, bytes)
    assert len(compressed) < len(data.encode("utf-8"))

    # Verify can be decompressed
    decompressed = zlib.decompress(compressed)
    assert decompressed.decode("utf-8") == data


def test_compress_response_bytes():
    """Test compression with bytes input"""
    data = b"Hello World" * 100
    compressed = compress_response(data, method="gzip")

    assert isinstance(compressed, bytes)
    assert len(compressed) < len(data)


def test_compress_response_compression_levels():
    """Test different compression levels"""
    data = "x" * 10000

    compressed_low = compress_response(data, method="gzip", level=1)
    compressed_high = compress_response(data, method="gzip", level=9)

    # Higher compression should produce smaller output
    assert len(compressed_high) <= len(compressed_low)


def test_compress_response_invalid_method():
    """Test compression with invalid method"""
    data = "Hello World"

    with pytest.raises(ValueError, match="Unknown compression method"):
        compress_response(data, method="invalid")


def test_decompress_response_gzip():
    """Test gzip decompression"""
    original = "Hello World" * 100
    compressed = gzip.compress(original.encode("utf-8"))

    decompressed = decompress_response(compressed, method="gzip")
    assert decompressed.decode("utf-8") == original


def test_decompress_response_zlib():
    """Test zlib decompression"""
    original = "Hello World" * 100
    compressed = zlib.compress(original.encode("utf-8"))

    decompressed = decompress_response(compressed, method="zlib")
    assert decompressed.decode("utf-8") == original


def test_compression_roundtrip():
    """Test compression and decompression roundtrip"""
    original = "The quick brown fox jumps over the lazy dog" * 100

    # Gzip roundtrip
    compressed_gzip = compress_response(original, method="gzip")
    decompressed_gzip = decompress_response(compressed_gzip, method="gzip")
    assert decompressed_gzip.decode("utf-8") == original

    # Zlib roundtrip
    compressed_zlib = compress_response(original, method="zlib")
    decompressed_zlib = decompress_response(compressed_zlib, method="zlib")
    assert decompressed_zlib.decode("utf-8") == original


def test_should_compress_size_threshold():
    """Test compression decision based on size"""
    small_data = "x" * 500
    large_data = "x" * 2000

    # Small data should not be compressed
    assert should_compress(small_data, min_size=1024) is False

    # Large data should be compressed
    assert should_compress(large_data, min_size=1024) is True


def test_should_compress_content_type():
    """Test compression decision based on content type"""
    data = "x" * 2000

    # Compressible types
    assert should_compress(data, content_type="application/json") is True
    assert should_compress(data, content_type="text/html") is True
    assert should_compress(data, content_type="text/plain") is True
    assert should_compress(data, content_type="application/javascript") is True

    # Non-compressible types
    assert should_compress(data, content_type="image/png") is False
    assert should_compress(data, content_type="video/mp4") is False


def test_compress_response_error_handling():
    """Test error handling in compression"""
    # Create an object that can't be compressed properly
    # by passing invalid level
    data = "Hello World"

    # This should log warning and return original data
    with patch("gzip.compress", side_effect=Exception("Compression failed")):
        result = compress_response(data, method="gzip")
        # On error, should return original data as bytes
        assert result == data.encode("utf-8")


def test_decompress_response_error_handling():
    """Test error handling in decompression"""
    invalid_data = b"not compressed data"

    # Should log warning and return original data
    result = decompress_response(invalid_data, method="gzip")
    assert result == invalid_data


@pytest.mark.asyncio
async def test_compression_middleware():
    """Test compression middleware"""

    # Create a simple ASGI app
    async def simple_app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"x" * 2000,  # Large enough to compress
                "more_body": False,
            }
        )

    # Wrap with compression middleware
    middleware = CompressionMiddleware(simple_app, min_size=1024)

    # Mock scope with gzip support
    scope = {
        "type": "http",
        "headers": [[b"accept-encoding", b"gzip"]],
    }

    # Mock receive
    async def receive():
        return {"type": "http.request"}

    # Capture sent messages
    sent_messages = []

    async def send(message):
        sent_messages.append(message)

    # Call middleware
    await middleware(scope, receive, send)

    # Verify compression headers were added
    assert len(sent_messages) == 2
    start_message = sent_messages[0]
    headers = dict(start_message["headers"])
    assert headers[b"content-encoding"] == b"gzip"


@pytest.mark.asyncio
async def test_compression_middleware_no_gzip_support():
    """Test compression middleware when client doesn't support gzip"""

    async def simple_app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"x" * 2000,
                "more_body": False,
            }
        )

    middleware = CompressionMiddleware(simple_app)

    # Scope without gzip support
    scope = {
        "type": "http",
        "headers": [],
    }

    async def receive():
        return {"type": "http.request"}

    sent_messages = []

    async def send(message):
        sent_messages.append(message)

    await middleware(scope, receive, send)

    # Should not compress
    if len(sent_messages) >= 2:
        start_message = sent_messages[0]
        headers = dict(start_message.get("headers", []))
        assert b"content-encoding" not in headers


def test_batch_query_with_empty_list():
    """Test batch_query with empty list"""

    @batch_query(batch_size=3, key_param="ids")
    def fetch_items(ids):
        return [{"id": id} for id in ids]

    result = fetch_items(ids=[])
    assert len(result) == 0


def test_profiler_nested_measurements():
    """Test profiler with nested measurements"""
    profiler = Profiler()

    with profiler.measure("outer"):
        time.sleep(0.05)
        with profiler.measure("inner"):
            time.sleep(0.05)

    metrics = profiler.get_metrics()
    assert "outer" in metrics
    assert "inner" in metrics
    assert metrics["outer"]["total_time"] >= metrics["inner"]["total_time"]


def test_index_manager_composite_index():
    """Test index manager suggesting composite index"""
    index_manager = IndexManager()

    suggestions = index_manager.suggest_indexes(
        table_name="simulations",
        columns=["user_id", "status", "created_at"],
        query_pattern="WHERE user_id = ? AND status = ? ORDER BY created_at",
    )

    # Should suggest composite index
    assert len(suggestions) > 0
    # Check if suggestion contains multiple columns
    assert any("user_id" in s and "status" in s for s in suggestions)


def test_performance_monitor_clear():
    """Test performance monitor clear"""
    monitor = PerformanceMonitor()

    monitor.record_metric("test", 1.0)
    monitor.record_metric("test", 2.0)

    monitor.clear()
    metrics = monitor.get_metrics()
    assert len(metrics) == 0
