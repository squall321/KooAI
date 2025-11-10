"""
Performance Profiling Middleware

FastAPI middleware for profiling request performance.
"""

import time
import tracemalloc
from typing import Callable, Optional, Any
from datetime import datetime
import psutil
import os

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    import cProfile
    import pstats
    from io import StringIO
except ImportError:
    cProfile = None  # type: ignore[assignment]


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for profiling request performance.

    Tracks request duration, memory usage, and optionally CPU profiling.
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_profiling: bool = False,
        enable_memory_tracking: bool = True,
        slow_request_threshold_ms: float = 1000.0,
    ):
        """
        Initialize performance middleware.

        Args:
            app: FastAPI application
            enable_profiling: Enable CPU profiling with cProfile
            enable_memory_tracking: Track memory usage
            slow_request_threshold_ms: Log warning for slow requests

        Example:
            ```python
            from fastapi import FastAPI
            from src.infrastructure.profiling import PerformanceMiddleware

            app = FastAPI()
            app.add_middleware(
                PerformanceMiddleware,
                enable_profiling=True,
                slow_request_threshold_ms=500.0
            )
            ```
        """
        super().__init__(app)
        self.enable_profiling = enable_profiling and cProfile is not None
        self.enable_memory_tracking = enable_memory_tracking
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.process = psutil.Process(os.getpid())

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with performance profiling.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with performance headers
        """
        # Start timing
        start_time = time.perf_counter()

        # Memory tracking
        if self.enable_memory_tracking:
            tracemalloc.start()
            memory_before = self.process.memory_info().rss

        # CPU profiling
        profiler = None
        if self.enable_profiling:
            profiler = cProfile.Profile()
            profiler.enable()

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Memory metrics
            if self.enable_memory_tracking:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                memory_after = self.process.memory_info().rss
                memory_delta_mb = (memory_after - memory_before) / 1024 / 1024

                response.headers["X-Memory-Used-MB"] = f"{memory_delta_mb:.2f}"
                response.headers["X-Memory-Peak-KB"] = f"{peak / 1024:.2f}"

            # Add performance headers
            response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"

            # Log slow requests
            if duration_ms > self.slow_request_threshold_ms:
                print(
                    f"SLOW REQUEST: {request.method} {request.url.path} "
                    f"took {duration_ms:.2f}ms"
                )

            # CPU profiling results
            if profiler:
                profiler.disable()
                stats_stream = StringIO()
                stats = pstats.Stats(profiler, stream=stats_stream)
                stats.sort_stats("cumulative")
                stats.print_stats(10)  # Top 10 functions

                # Store profile in request state for debugging
                if hasattr(request.state, "profile_stats"):
                    request.state.profile_stats = stats_stream.getvalue()

            return response

        except Exception as e:
            if self.enable_memory_tracking:
                tracemalloc.stop()
            if profiler:
                profiler.disable()
            raise


class ResourceMonitor:
    """
    Monitor system resources during request processing.

    Tracks CPU, memory, and disk I/O.
    """

    def __init__(self) -> None:
        """Initialize resource monitor."""
        self.process = psutil.Process(os.getpid())

    def get_current_usage(self) -> dict:
        """
        Get current resource usage.

        Returns:
            Dictionary with resource metrics

        Example:
            ```python
            monitor = ResourceMonitor()
            usage = monitor.get_current_usage()
            print(f"CPU: {usage['cpu_percent']}%")
            print(f"Memory: {usage['memory_mb']:.2f} MB")
            ```
        """
        memory_info = self.process.memory_info()

        return {
            "cpu_percent": self.process.cpu_percent(interval=0.1),
            "memory_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "num_threads": self.process.num_threads(),
            "open_files": len(self.process.open_files()),
            "connections": len(self.process.connections()),
        }

    def get_system_usage(self) -> dict:
        """
        Get system-wide resource usage.

        Returns:
            Dictionary with system metrics
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": memory.total / 1024 / 1024 / 1024,
            "memory_available_gb": memory.available / 1024 / 1024 / 1024,
            "memory_percent": memory.percent,
            "disk_total_gb": disk.total / 1024 / 1024 / 1024,
            "disk_used_gb": disk.used / 1024 / 1024 / 1024,
            "disk_percent": disk.percent,
        }


class QueryProfiler:
    """
    Profile database queries for performance analysis.

    Tracks slow queries and query patterns.
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        """
        Initialize query profiler.

        Args:
            slow_query_threshold_ms: Threshold for slow query logging
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.queries: list = []

    def profile_query(self, query: str, params: Optional[dict] = None) -> "QueryContext":
        """
        Context manager for profiling queries.

        Args:
            query: SQL query
            params: Query parameters

        Example:
            ```python
            profiler = QueryProfiler()

            with profiler.profile_query("SELECT * FROM users WHERE id = %s", {"id": 123}):
                result = db.execute(query, params)
            ```
        """
        return QueryContext(self, query, params)

    def add_query(
        self, query: str, duration_ms: float, params: Optional[dict] = None
    ) -> None:
        """Record query execution."""
        query_record = {
            "query": query,
            "duration_ms": duration_ms,
            "params": params,
            "timestamp": datetime.utcnow().isoformat(),
            "is_slow": duration_ms > self.slow_query_threshold_ms,
        }

        self.queries.append(query_record)

        if query_record["is_slow"]:
            print(
                f"SLOW QUERY ({duration_ms:.2f}ms): {query[:100]}..."
            )

    def get_stats(self) -> dict:
        """
        Get query statistics.

        Returns:
            Query performance statistics
        """
        if not self.queries:
            return {"total_queries": 0}

        durations = [q["duration_ms"] for q in self.queries]
        slow_queries = [q for q in self.queries if q["is_slow"]]

        return {
            "total_queries": len(self.queries),
            "slow_queries": len(slow_queries),
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "total_time_ms": sum(durations),
        }

    def clear(self) -> None:
        """Clear query history."""
        self.queries = []


class QueryContext:
    """Context manager for query profiling."""

    def __init__(
        self, profiler: QueryProfiler, query: str, params: Optional[dict] = None
    ):
        """Initialize query context."""
        self.profiler = profiler
        self.query = query
        self.params = params
        self.start_time: Optional[float] = None

    def __enter__(self) -> "QueryContext":
        """Start profiling."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop profiling and record."""
        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.profiler.add_query(self.query, duration_ms, self.params)
