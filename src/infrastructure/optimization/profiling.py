"""
Performance profiling utilities
"""

import time
import functools
from contextlib import contextmanager
from typing import Any, Callable, Optional
import structlog

logger = structlog.get_logger(__name__)


class Profiler:
    """
    Performance profiler

    Provides utilities for measuring and analyzing performance.
    """

    def __init__(self):
        self.timings = {}

    @contextmanager
    def measure(self, name: str):
        """
        Context manager to measure execution time

        Args:
            name: Measurement name

        Example:
            profiler = Profiler()
            with profiler.measure("database_query"):
                result = expensive_query()
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.record(name, elapsed)

    def record(self, name: str, duration: float):
        """
        Record timing

        Args:
            name: Measurement name
            duration: Duration in seconds
        """
        if name not in self.timings:
            self.timings[name] = []

        self.timings[name].append(duration)

        logger.debug(
            "performance_measurement",
            name=name,
            duration=duration,
        )

    def get_stats(self, name: str) -> Optional[dict]:
        """
        Get statistics for a measurement

        Args:
            name: Measurement name

        Returns:
            Statistics dictionary
        """
        if name not in self.timings or not self.timings[name]:
            return None

        timings = self.timings[name]

        return {
            "name": name,
            "count": len(timings),
            "total": sum(timings),
            "mean": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }

    def get_all_stats(self) -> dict:
        """
        Get statistics for all measurements

        Returns:
            Dictionary of all statistics
        """
        return {name: self.get_stats(name) for name in self.timings}

    def reset(self):
        """Reset all timings"""
        self.timings.clear()


def profile_function(name: Optional[str] = None, log_args: bool = False):
    """
    Decorator to profile function execution time

    Args:
        name: Custom name for measurement (defaults to function name)
        log_args: Whether to log function arguments

    Example:
        @profile_function(name="expensive_computation")
        def compute(x, y):
            return x ** y
    """

    def decorator(func: Callable) -> Callable:
        measurement_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            log_data = {
                "function": func.__name__,
                "measurement": measurement_name,
            }

            if log_args:
                log_data["args"] = args
                log_data["kwargs"] = kwargs

            logger.debug("function_start", **log_data)

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                logger.info(
                    "function_complete",
                    function=func.__name__,
                    duration=elapsed,
                    **log_data,
                )

                return result

            except Exception as e:
                elapsed = time.time() - start_time

                logger.error(
                    "function_failed",
                    function=func.__name__,
                    duration=elapsed,
                    error=str(e),
                    **log_data,
                )

                raise

        return wrapper

    return decorator


@contextmanager
def measure_time(name: str, log_result: bool = True):
    """
    Context manager to measure time

    Args:
        name: Measurement name
        log_result: Whether to log the result

    Example:
        with measure_time("database_query"):
            result = session.query(User).all()
    """
    start_time = time.time()

    try:
        yield
    finally:
        elapsed = time.time() - start_time

        if log_result:
            logger.info(
                "time_measured",
                name=name,
                duration=elapsed,
            )


class PerformanceMonitor:
    """
    Performance monitoring for requests/operations

    Tracks metrics like:
    - Request count
    - Response times
    - Error rates
    """

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_time = 0.0
        self.response_times = []

    def record_request(self, duration: float, success: bool = True):
        """
        Record request metrics

        Args:
            duration: Request duration in seconds
            success: Whether request was successful
        """
        self.request_count += 1
        self.total_time += duration
        self.response_times.append(duration)

        if not success:
            self.error_count += 1

    def get_metrics(self) -> dict:
        """
        Get performance metrics

        Returns:
            Metrics dictionary
        """
        if self.request_count == 0:
            return {
                "request_count": 0,
                "error_count": 0,
                "error_rate": 0.0,
                "avg_response_time": 0.0,
            }

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count,
            "total_time": self.total_time,
            "avg_response_time": self.total_time / self.request_count,
            "min_response_time": min(self.response_times) if self.response_times else 0,
            "max_response_time": max(self.response_times) if self.response_times else 0,
        }

    def reset(self):
        """Reset all metrics"""
        self.request_count = 0
        self.error_count = 0
        self.total_time = 0.0
        self.response_times.clear()


# Global performance monitor instance
_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _monitor
