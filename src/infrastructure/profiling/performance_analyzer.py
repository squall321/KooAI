"""
Performance Analysis Tools

Analyze application performance and generate reports.
"""

import time
import tracemalloc
from typing import Callable, Any, Optional
from functools import wraps
from pathlib import Path
import json
from datetime import datetime
import statistics

try:
    import line_profiler
except ImportError:
    line_profiler = None

try:
    import memory_profiler
except ImportError:
    memory_profiler = None


class FunctionProfiler:
    """
    Profile individual functions for performance analysis.

    Tracks execution time and call frequency.
    """

    def __init__(self):
        """Initialize function profiler."""
        self.calls: dict = {}

    def profile(self, func: Callable) -> Callable:
        """
        Decorator to profile function execution.

        Args:
            func: Function to profile

        Returns:
            Wrapped function

        Example:
            ```python
            profiler = FunctionProfiler()

            @profiler.profile
            def slow_function():
                time.sleep(1)

            slow_function()
            stats = profiler.get_stats()
            print(stats)
            ```
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                raise
            finally:
                duration = time.perf_counter() - start_time

                # Record call
                func_name = f"{func.__module__}.{func.__name__}"
                if func_name not in self.calls:
                    self.calls[func_name] = {
                        "count": 0,
                        "total_time": 0.0,
                        "min_time": float("inf"),
                        "max_time": 0.0,
                        "times": [],
                        "errors": 0,
                    }

                record = self.calls[func_name]
                record["count"] += 1
                record["total_time"] += duration
                record["min_time"] = min(record["min_time"], duration)
                record["max_time"] = max(record["max_time"], duration)
                record["times"].append(duration)
                if not success:
                    record["errors"] += 1

            return result

        return wrapper

    def get_stats(self) -> dict:
        """
        Get profiling statistics.

        Returns:
            Dictionary with function statistics
        """
        stats = {}

        for func_name, record in self.calls.items():
            times = record["times"]
            stats[func_name] = {
                "calls": record["count"],
                "total_time_seconds": record["total_time"],
                "avg_time_seconds": record["total_time"] / record["count"],
                "min_time_seconds": record["min_time"],
                "max_time_seconds": record["max_time"],
                "median_time_seconds": statistics.median(times) if times else 0,
                "errors": record["errors"],
                "error_rate": (
                    record["errors"] / record["count"] if record["count"] > 0 else 0
                ),
            }

        # Sort by total time
        sorted_stats = dict(
            sorted(stats.items(), key=lambda x: x[1]["total_time_seconds"], reverse=True)
        )

        return sorted_stats

    def reset(self):
        """Reset profiling data."""
        self.calls = {}


class MemoryProfiler:
    """
    Profile memory usage of functions.

    Tracks memory allocation and deallocation.
    """

    def __init__(self):
        """Initialize memory profiler."""
        self.snapshots: list = []

    def profile_memory(self, func: Callable) -> Callable:
        """
        Decorator to profile memory usage.

        Args:
            func: Function to profile

        Returns:
            Wrapped function

        Example:
            ```python
            mem_profiler = MemoryProfiler()

            @mem_profiler.profile_memory
            def memory_intensive_function():
                data = [i for i in range(1000000)]
                return data

            result = memory_intensive_function()
            stats = mem_profiler.get_stats()
            ```
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            tracemalloc.start()

            try:
                result = func(*args, **kwargs)
            finally:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                self.snapshots.append(
                    {
                        "function": f"{func.__module__}.{func.__name__}",
                        "current_bytes": current,
                        "peak_bytes": peak,
                        "current_mb": current / 1024 / 1024,
                        "peak_mb": peak / 1024 / 1024,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            return result

        return wrapper

    def get_stats(self) -> dict:
        """
        Get memory profiling statistics.

        Returns:
            Memory usage statistics
        """
        if not self.snapshots:
            return {"total_snapshots": 0}

        total_current = sum(s["current_bytes"] for s in self.snapshots)
        total_peak = sum(s["peak_bytes"] for s in self.snapshots)

        return {
            "total_snapshots": len(self.snapshots),
            "total_current_mb": total_current / 1024 / 1024,
            "total_peak_mb": total_peak / 1024 / 1024,
            "avg_current_mb": (total_current / len(self.snapshots)) / 1024 / 1024,
            "avg_peak_mb": (total_peak / len(self.snapshots)) / 1024 / 1024,
            "snapshots": self.snapshots[-10:],  # Last 10 snapshots
        }

    def reset(self):
        """Reset memory snapshots."""
        self.snapshots = []


class PerformanceReport:
    """
    Generate comprehensive performance reports.

    Combines profiling data into detailed reports.
    """

    def __init__(
        self,
        function_profiler: Optional[FunctionProfiler] = None,
        memory_profiler: Optional[MemoryProfiler] = None,
    ):
        """
        Initialize performance report generator.

        Args:
            function_profiler: Function profiler instance
            memory_profiler: Memory profiler instance
        """
        self.function_profiler = function_profiler
        self.memory_profiler = memory_profiler

    def generate_report(self) -> dict:
        """
        Generate comprehensive performance report.

        Returns:
            Performance report dictionary

        Example:
            ```python
            report_gen = PerformanceReport(func_profiler, mem_profiler)
            report = report_gen.generate_report()

            print(json.dumps(report, indent=2))
            ```
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "performance_analysis",
        }

        # Function profiling
        if self.function_profiler:
            func_stats = self.function_profiler.get_stats()
            report["function_profiling"] = {
                "total_functions": len(func_stats),
                "top_by_total_time": dict(list(func_stats.items())[:10]),
                "summary": {
                    "total_calls": sum(
                        s["calls"] for s in func_stats.values()
                    ),
                    "total_time_seconds": sum(
                        s["total_time_seconds"] for s in func_stats.values()
                    ),
                    "total_errors": sum(
                        s["errors"] for s in func_stats.values()
                    ),
                },
            }

        # Memory profiling
        if self.memory_profiler:
            mem_stats = self.memory_profiler.get_stats()
            report["memory_profiling"] = mem_stats

        return report

    def save_report(self, output_path: Path):
        """
        Save report to JSON file.

        Args:
            output_path: Output file path

        Example:
            ```python
            report_gen.save_report(Path("performance_report.json"))
            ```
        """
        report = self.generate_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Performance report saved to {output_path}")

    def print_summary(self):
        """Print performance report summary to console."""
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("  Performance Report")
        print("=" * 60)
        print(f"Generated: {report['generated_at']}")

        if "function_profiling" in report:
            func_prof = report["function_profiling"]
            summary = func_prof["summary"]

            print("\n--- Function Profiling ---")
            print(f"Total Functions: {func_prof['total_functions']}")
            print(f"Total Calls: {summary['total_calls']}")
            print(f"Total Time: {summary['total_time_seconds']:.2f} seconds")
            print(f"Total Errors: {summary['total_errors']}")

            print("\nTop 5 Functions by Total Time:")
            for i, (func, stats) in enumerate(
                list(func_prof["top_by_total_time"].items())[:5], 1
            ):
                print(f"\n  {i}. {func}")
                print(f"     Calls: {stats['calls']}")
                print(f"     Total Time: {stats['total_time_seconds']:.4f}s")
                print(f"     Avg Time: {stats['avg_time_seconds']:.4f}s")
                print(f"     Errors: {stats['errors']}")

        if "memory_profiling" in report:
            mem_prof = report["memory_profiling"]

            print("\n--- Memory Profiling ---")
            print(f"Total Snapshots: {mem_prof['total_snapshots']}")
            print(f"Total Current: {mem_prof.get('total_current_mb', 0):.2f} MB")
            print(f"Total Peak: {mem_prof.get('total_peak_mb', 0):.2f} MB")
            print(f"Avg Current: {mem_prof.get('avg_current_mb', 0):.2f} MB")
            print(f"Avg Peak: {mem_prof.get('avg_peak_mb', 0):.2f} MB")

        print("\n" + "=" * 60 + "\n")


# Global profiler instances
_function_profiler: Optional[FunctionProfiler] = None
_memory_profiler: Optional[MemoryProfiler] = None


def get_function_profiler() -> FunctionProfiler:
    """Get global function profiler instance."""
    global _function_profiler
    if _function_profiler is None:
        _function_profiler = FunctionProfiler()
    return _function_profiler


def get_memory_profiler() -> MemoryProfiler:
    """Get global memory profiler instance."""
    global _memory_profiler
    if _memory_profiler is None:
        _memory_profiler = MemoryProfiler()
    return _memory_profiler


def profile(func: Callable) -> Callable:
    """
    Convenience decorator for profiling functions.

    Profiles both execution time and memory.

    Example:
        ```python
        from src.infrastructure.profiling import profile

        @profile
        def my_function():
            # Function code
            pass
        ```
    """
    func_profiler = get_function_profiler()
    mem_profiler = get_memory_profiler()

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Apply both profilers
        profiled_func = func_profiler.profile(func)
        memory_profiled = mem_profiler.profile_memory(profiled_func)
        return memory_profiled(*args, **kwargs)

    return wrapper
