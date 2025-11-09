"""
Prometheus Metrics

Exposes application metrics in Prometheus format.

Metrics Categories:
1. HTTP Metrics - Request count, duration, status codes
2. Database Metrics - Query count, connection pool, transaction time
3. Cache Metrics - Hit rate, evictions, memory usage
4. Task Queue Metrics - Queue size, processing time, success/failure
5. System Metrics - CPU, memory, disk usage
6. Application Metrics - Uptime, version info, active users
"""

from typing import Optional, cast
import time
import psutil
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Create custom registry to avoid conflicts
metrics_registry = CollectorRegistry()

# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    "kooai_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=metrics_registry,
)

http_request_duration_seconds = Histogram(
    "kooai_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=metrics_registry,
)

http_requests_in_progress = Gauge(
    "kooai_http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
    registry=metrics_registry,
)

# ============================================================================
# Database Metrics
# ============================================================================

database_queries_total = Counter(
    "kooai_database_queries_total",
    "Total database queries",
    ["operation"],  # SELECT, INSERT, UPDATE, DELETE
    registry=metrics_registry,
)

database_query_duration_seconds = Histogram(
    "kooai_database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    registry=metrics_registry,
)

database_connections_active = Gauge(
    "kooai_database_connections_active",
    "Number of active database connections",
    registry=metrics_registry,
)

database_connection_pool_size = Gauge(
    "kooai_database_connection_pool_size",
    "Database connection pool size",
    registry=metrics_registry,
)

database_errors_total = Counter(
    "kooai_database_errors_total",
    "Total database errors",
    ["error_type"],
    registry=metrics_registry,
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    "kooai_cache_hits_total",
    "Total cache hits",
    ["cache_tier"],  # L1, L2
    registry=metrics_registry,
)

cache_misses_total = Counter(
    "kooai_cache_misses_total",
    "Total cache misses",
    ["cache_tier"],
    registry=metrics_registry,
)

cache_evictions_total = Counter(
    "kooai_cache_evictions_total",
    "Total cache evictions",
    ["cache_tier"],
    registry=metrics_registry,
)

cache_memory_bytes = Gauge(
    "kooai_cache_memory_bytes",
    "Cache memory usage in bytes",
    ["cache_tier"],
    registry=metrics_registry,
)

cache_entries_total = Gauge(
    "kooai_cache_entries_total",
    "Total number of cache entries",
    ["cache_tier"],
    registry=metrics_registry,
)

cache_operation_duration_seconds = Histogram(
    "kooai_cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation", "cache_tier"],  # get, set, delete
    registry=metrics_registry,
)

# ============================================================================
# Task Queue Metrics
# ============================================================================

task_queue_size = Gauge(
    "kooai_task_queue_size",
    "Number of tasks in queue",
    ["status"],  # pending, running, completed, failed
    registry=metrics_registry,
)

task_processing_duration_seconds = Histogram(
    "kooai_task_processing_duration_seconds",
    "Task processing duration in seconds",
    ["task_name", "priority"],
    registry=metrics_registry,
)

tasks_total = Counter(
    "kooai_tasks_total",
    "Total number of tasks",
    ["task_name", "status"],  # completed, failed
    registry=metrics_registry,
)

task_retries_total = Counter(
    "kooai_task_retries_total",
    "Total number of task retries",
    ["task_name"],
    registry=metrics_registry,
)

active_workers = Gauge(
    "kooai_active_workers",
    "Number of active task workers",
    registry=metrics_registry,
)

# ============================================================================
# Simulation Metrics
# ============================================================================

simulations_processed_total = Counter(
    "kooai_simulations_processed_total",
    "Total simulations processed",
    ["file_format", "status"],  # CSV, VTU, HDF5, etc.
    registry=metrics_registry,
)

simulation_file_size_bytes = Histogram(
    "kooai_simulation_file_size_bytes",
    "Simulation file size in bytes",
    ["file_format"],
    registry=metrics_registry,
)

simulation_processing_duration_seconds = Histogram(
    "kooai_simulation_processing_duration_seconds",
    "Simulation processing duration in seconds",
    ["file_format"],
    registry=metrics_registry,
)

simulation_vertices_total = Histogram(
    "kooai_simulation_vertices_total",
    "Number of vertices in simulation mesh",
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
    registry=metrics_registry,
)

# ============================================================================
# System Metrics
# ============================================================================

system_cpu_usage_percent = Gauge(
    "kooai_system_cpu_usage_percent",
    "System CPU usage percentage",
    registry=metrics_registry,
)

system_memory_usage_bytes = Gauge(
    "kooai_system_memory_usage_bytes",
    "System memory usage in bytes",
    registry=metrics_registry,
)

system_memory_available_bytes = Gauge(
    "kooai_system_memory_available_bytes",
    "System available memory in bytes",
    registry=metrics_registry,
)

system_disk_usage_bytes = Gauge(
    "kooai_system_disk_usage_bytes",
    "System disk usage in bytes",
    ["mountpoint"],
    registry=metrics_registry,
)

system_disk_available_bytes = Gauge(
    "kooai_system_disk_available_bytes",
    "System disk available in bytes",
    ["mountpoint"],
    registry=metrics_registry,
)

system_network_sent_bytes_total = Counter(
    "kooai_system_network_sent_bytes_total",
    "Total bytes sent over network",
    registry=metrics_registry,
)

system_network_received_bytes_total = Counter(
    "kooai_system_network_received_bytes_total",
    "Total bytes received over network",
    registry=metrics_registry,
)

# ============================================================================
# Application Metrics
# ============================================================================

app_info = Info(
    "kooai_app",
    "Application information",
    registry=metrics_registry,
)

app_uptime_seconds = Gauge(
    "kooai_app_uptime_seconds",
    "Application uptime in seconds",
    registry=metrics_registry,
)

app_start_time = Gauge(
    "kooai_app_start_time_seconds",
    "Application start time in Unix epoch seconds",
    registry=metrics_registry,
)

# Set application info
app_info.info(
    {
        "version": "1.0.0",
        "environment": "production",
        "python_version": "3.11",
    }
)

# Track start time
_app_start_time = time.time()
app_start_time.set(_app_start_time)


# ============================================================================
# Metric Collection Functions
# ============================================================================


def update_system_metrics() -> None:
    """Update system resource metrics"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage_percent.set(cpu_percent)

        # Memory
        memory = psutil.virtual_memory()
        system_memory_usage_bytes.set(memory.used)
        system_memory_available_bytes.set(memory.available)

        # Disk
        disk = psutil.disk_usage("/")
        system_disk_usage_bytes.labels(mountpoint="/").set(disk.used)
        system_disk_available_bytes.labels(mountpoint="/").set(disk.free)

        # Network
        net_io = psutil.net_io_counters()
        system_network_sent_bytes_total.inc(net_io.bytes_sent)
        system_network_received_bytes_total.inc(net_io.bytes_recv)

        # Uptime
        uptime = time.time() - _app_start_time
        app_uptime_seconds.set(uptime)

    except Exception as e:
        logger.error("failed_to_update_system_metrics", error=str(e))


def update_cache_metrics() -> None:
    """Update cache metrics from cache system"""
    try:
        from src.infrastructure.cache.multi_tier_cache import get_multi_tier_cache

        cache = get_multi_tier_cache()
        stats = cache.get_stats()

        # L1 metrics
        l1_stats = stats.get("l1", {})
        cache_hits_total.labels(cache_tier="L1").inc(l1_stats.get("hits", 0))
        cache_misses_total.labels(cache_tier="L1").inc(l1_stats.get("misses", 0))
        cache_evictions_total.labels(cache_tier="L1").inc(l1_stats.get("evictions", 0))
        cache_entries_total.labels(cache_tier="L1").set(l1_stats.get("size", 0))

        # L2 metrics
        overall_stats = stats.get("overall", {})
        cache_hits_total.labels(cache_tier="L2").inc(overall_stats.get("l2_hits", 0))

    except Exception as e:
        logger.warning("failed_to_update_cache_metrics", error=str(e))


def update_task_queue_metrics() -> None:
    """Update task queue metrics"""
    try:
        from src.infrastructure.tasks import get_task_queue, get_worker_pool

        queue = get_task_queue()
        stats = queue.get_stats()

        # Queue sizes
        task_queue_size.labels(status="pending").set(stats.get("pending", 0))
        task_queue_size.labels(status="running").set(stats.get("running", 0))
        task_queue_size.labels(status="completed").set(stats.get("completed", 0))
        task_queue_size.labels(status="failed").set(stats.get("failed", 0))

        # Workers
        try:
            pool = get_worker_pool()
            active_workers.set(pool.running_workers)
        except:
            pass

    except Exception as e:
        logger.warning("failed_to_update_task_queue_metrics", error=str(e))


def collect_all_metrics() -> bytes:
    """
    Collect all metrics and return in Prometheus format

    Returns:
        bytes: Metrics in Prometheus text format
    """
    # Update dynamic metrics
    update_system_metrics()
    update_cache_metrics()
    update_task_queue_metrics()

    # Generate Prometheus format
    return cast(bytes, generate_latest(metrics_registry))


def get_metrics_content_type() -> str:
    """Get content type for Prometheus metrics"""
    return cast(str, CONTENT_TYPE_LATEST)


# ============================================================================
# Metric Helpers (for use in application code)
# ============================================================================


def track_http_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Track HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_database_query(operation: str, duration: float, error: Optional[str] = None) -> None:
    """Track database query metrics"""
    database_queries_total.labels(operation=operation).inc()
    database_query_duration_seconds.labels(operation=operation).observe(duration)

    if error:
        database_errors_total.labels(error_type=error).inc()


def track_cache_operation(
    operation: str, cache_tier: str, duration: float, hit: bool = False
) -> None:
    """Track cache operation metrics"""
    if hit:
        cache_hits_total.labels(cache_tier=cache_tier).inc()
    else:
        cache_misses_total.labels(cache_tier=cache_tier).inc()

    cache_operation_duration_seconds.labels(operation=operation, cache_tier=cache_tier).observe(
        duration
    )


def track_task_execution(
    task_name: str, priority: str, duration: float, status: str, retries: int = 0
) -> None:
    """Track task execution metrics"""
    tasks_total.labels(task_name=task_name, status=status).inc()
    task_processing_duration_seconds.labels(task_name=task_name, priority=priority).observe(
        duration
    )

    if retries > 0:
        task_retries_total.labels(task_name=task_name).inc(retries)


def track_simulation_processing(
    file_format: str, file_size: int, vertices: int, duration: float, status: str
) -> None:
    """Track simulation processing metrics"""
    simulations_processed_total.labels(file_format=file_format, status=status).inc()
    simulation_file_size_bytes.labels(file_format=file_format).observe(file_size)
    simulation_processing_duration_seconds.labels(file_format=file_format).observe(duration)
    simulation_vertices_total.observe(vertices)
