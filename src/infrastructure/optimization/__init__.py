"""
Performance optimization utilities

Provides tools for:
- Database query optimization
- Connection pooling
- Batch processing
- Response compression
- Profiling
"""

from .query_optimizer import QueryOptimizer, optimize_query, batch_query
from .profiling import Profiler, profile_function, measure_time
from .compression import compress_response, decompress_response

__all__ = [
    # Query optimization
    "QueryOptimizer",
    "optimize_query",
    "batch_query",
    # Profiling
    "Profiler",
    "profile_function",
    "measure_time",
    # Compression
    "compress_response",
    "decompress_response",
]
