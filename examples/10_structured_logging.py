"""
Structured Logging Examples

Demonstrates how to use the structured logging system with structlog.

Features demonstrated:
1. Basic logging with context
2. Different log levels
3. Error logging with stack traces
4. Request/response logging
5. Performance timing
6. Sensitive data censoring
7. Custom context managers
"""

import time
from contextlib import contextmanager

from src.infrastructure.logging import (
    setup_logging,
    get_logger,
    get_request_logger,
    get_database_logger,
    get_cache_logger,
    get_task_logger,
    LogConfig,
)


@contextmanager
def log_execution_time(logger, operation: str):
    """Context manager to log execution time"""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(
            "operation_completed",
            operation=operation,
            duration_ms=round(elapsed * 1000, 2),
        )


def example_1_basic_logging():
    """Example 1: Basic structured logging"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Structured Logging")
    print("=" * 60 + "\n")

    logger = get_logger(__name__)

    # Simple log messages
    logger.info("application_started", version="1.0.0", port=8000)

    # Log with multiple context fields
    logger.info(
        "user_action",
        user_id=123,
        action="login",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    # Log with nested data
    logger.info(
        "simulation_uploaded",
        simulation_id="sim_001",
        metadata={"file_size": 1024000, "format": "CSV", "fields": ["temp", "pressure"]},
    )


def example_2_log_levels():
    """Example 2: Different log levels"""
    print("\n" + "=" * 60)
    print("Example 2: Different Log Levels")
    print("=" * 60 + "\n")

    logger = get_logger(__name__)

    logger.debug("debug_message", detail="This is for debugging")
    logger.info("info_message", status="normal operation")
    logger.warning("warning_message", reason="resource usage high", cpu_percent=85)
    logger.error("error_message", error_code="E001", description="Failed to process file")


def example_3_error_logging():
    """Example 3: Error logging with stack traces"""
    print("\n" + "=" * 60)
    print("Example 3: Error Logging with Stack Traces")
    print("=" * 60 + "\n")

    logger = get_logger(__name__)

    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.exception(
            "calculation_failed",
            operation="division",
            numerator=1,
            denominator=0,
            exc_info=True,
        )


def example_4_request_logging():
    """Example 4: HTTP request/response logging"""
    print("\n" + "=" * 60)
    print("Example 4: Request/Response Logging")
    print("=" * 60 + "\n")

    request_logger = get_request_logger()

    # Log incoming request
    request_logger.info(
        "request_received",
        method="POST",
        path="/api/simulations",
        client_ip="10.0.1.5",
        user_id=456,
    )

    # Simulate request processing
    time.sleep(0.1)

    # Log response
    request_logger.info(
        "request_completed",
        method="POST",
        path="/api/simulations",
        status_code=201,
        duration_ms=105,
        response_size=1234,
    )


def example_5_database_logging():
    """Example 5: Database operation logging"""
    print("\n" + "=" * 60)
    print("Example 5: Database Operation Logging")
    print("=" * 60 + "\n")

    db_logger = get_database_logger()

    # Log query
    db_logger.info(
        "query_executed",
        operation="SELECT",
        table="simulations",
        filters={"status": "completed"},
        duration_ms=23,
        rows_returned=15,
    )

    # Log transaction
    db_logger.info(
        "transaction_committed",
        operations=["INSERT", "UPDATE"],
        tables=["simulations", "analysis_results"],
        duration_ms=45,
    )


def example_6_cache_logging():
    """Example 6: Cache operation logging"""
    print("\n" + "=" * 60)
    print("Example 6: Cache Operation Logging")
    print("=" * 60 + "\n")

    cache_logger = get_cache_logger()

    # Log cache hit
    cache_logger.info(
        "cache_hit",
        cache_key="simulation:sim_001",
        ttl_remaining=180,
        tier="L1",
    )

    # Log cache miss
    cache_logger.info(
        "cache_miss",
        cache_key="simulation:sim_002",
        tier="L2",
        fallback="database",
    )

    # Log cache stats
    cache_logger.info(
        "cache_stats",
        hit_rate=0.85,
        total_hits=1700,
        total_misses=300,
        evictions=50,
    )


def example_7_task_logging():
    """Example 7: Background task logging"""
    print("\n" + "=" * 60)
    print("Example 7: Background Task Logging")
    print("=" * 60 + "\n")

    task_logger = get_task_logger()

    # Log task enqueued
    task_logger.info(
        "task_enqueued",
        task_id="task_123",
        task_name="process_simulation",
        priority="NORMAL",
        args={"simulation_id": "sim_001"},
    )

    # Log task started
    task_logger.info(
        "task_started",
        task_id="task_123",
        worker_id="worker_01",
    )

    # Simulate task execution
    time.sleep(0.2)

    # Log task completed
    task_logger.info(
        "task_completed",
        task_id="task_123",
        status="success",
        duration_ms=205,
        result={"records_processed": 1000},
    )


def example_8_sensitive_data_censoring():
    """Example 8: Sensitive data censoring"""
    print("\n" + "=" * 60)
    print("Example 8: Sensitive Data Censoring")
    print("=" * 60 + "\n")

    logger = get_logger(__name__)

    # These sensitive fields will be automatically censored
    logger.info(
        "user_authentication",
        username="john.doe",
        password="secret123",  # Will be censored
        api_key="sk-1234567890",  # Will be censored
        email="john@example.com",
    )

    logger.info(
        "external_api_call",
        service="payment_gateway",
        token="bearer_xyz789",  # Will be censored
        amount=99.99,
    )


def example_9_execution_timing():
    """Example 9: Execution timing with context manager"""
    print("\n" + "=" * 60)
    print("Example 9: Execution Timing")
    print("=" * 60 + "\n")

    logger = get_logger(__name__)

    # Time a single operation
    with log_execution_time(logger, "data_processing"):
        time.sleep(0.5)
        # Simulate data processing
        data = [i**2 for i in range(10000)]

    # Time database query
    with log_execution_time(logger, "database_query"):
        time.sleep(0.1)
        # Simulate database query


def example_10_json_format():
    """Example 10: JSON format logging"""
    print("\n" + "=" * 60)
    print("Example 10: JSON Format Logging")
    print("=" * 60 + "\n")
    print("(Reconfigure with LOG_FORMAT=json to see JSON output)")

    # Reconfigure for JSON
    setup_logging(LogConfig(level="INFO", format="json"))

    logger = get_logger(__name__)

    logger.info(
        "json_log_example",
        event_type="simulation_processed",
        simulation_id="sim_123",
        metrics={"processing_time_ms": 1234, "memory_usage_mb": 256},
        tags=["production", "high-priority"],
    )

    # Reconfigure back to console
    setup_logging(LogConfig(level="INFO", format="console"))


def example_11_error_tracking():
    """Example 11: Comprehensive error tracking"""
    print("\n" + "=" * 60)
    print("Example 11: Comprehensive Error Tracking")
    print("=" * 60 + "\n")

    logger = get_logger(__name__)

    # Track different types of errors
    errors = [
        {"type": "ValidationError", "field": "temperature", "value": -999},
        {"type": "FileNotFoundError", "path": "/data/missing.csv"},
        {"type": "TimeoutError", "service": "external_api", "timeout_seconds": 30},
    ]

    for error in errors:
        logger.error(
            "error_occurred",
            error_type=error["type"],
            context=error,
            severity="medium",
        )


def main():
    """Run all examples"""
    # Initialize logging with console format
    setup_logging(LogConfig(level="INFO", format="console"))

    print("=" * 60)
    print("Structured Logging Examples")
    print("=" * 60)

    # Run examples
    example_1_basic_logging()
    example_2_log_levels()
    example_3_error_logging()
    example_4_request_logging()
    example_5_database_logging()
    example_6_cache_logging()
    example_7_task_logging()
    example_8_sensitive_data_censoring()
    example_9_execution_timing()
    example_10_json_format()
    example_11_error_tracking()

    print("\n" + "=" * 60)
    print("✅ All logging examples completed!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Use structured logging with key-value pairs")
    print("2. Sensitive data is automatically censored")
    print("3. Different loggers for different components")
    print("4. JSON format for production environments")
    print("5. Console format for development")
    print("\nTo change log format:")
    print("  export LOG_FORMAT=json")
    print("  export LOG_LEVEL=DEBUG")


if __name__ == "__main__":
    main()
