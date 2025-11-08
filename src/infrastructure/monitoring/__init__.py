"""
Monitoring Infrastructure

Prometheus metrics collection and monitoring utilities.

Usage:
    from src.infrastructure.monitoring import (
        track_http_request,
        track_database_query,
        track_cache_operation,
        collect_all_metrics,
    )

    # Track HTTP request
    track_http_request("GET", "/api/simulations", 200, 0.123)

    # Track database query
    track_database_query("SELECT", 0.045)

    # Collect all metrics for Prometheus
    metrics_data = collect_all_metrics()
"""

from .prometheus_metrics import (
    # Metric collection
    collect_all_metrics,
    get_metrics_content_type,
    update_system_metrics,
    update_cache_metrics,
    update_task_queue_metrics,
    # Tracking functions
    track_http_request,
    track_database_query,
    track_cache_operation,
    track_task_execution,
    track_simulation_processing,
    # Registry
    metrics_registry,
)

__all__ = [
    # Collection
    "collect_all_metrics",
    "get_metrics_content_type",
    "update_system_metrics",
    "update_cache_metrics",
    "update_task_queue_metrics",
    # Tracking
    "track_http_request",
    "track_database_query",
    "track_cache_operation",
    "track_task_execution",
    "track_simulation_processing",
    # Registry
    "metrics_registry",
]
