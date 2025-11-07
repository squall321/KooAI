"""
KooAI Logging System - Usage Examples

This module demonstrates 11 different logging scenarios:
1. Basic logging
2. Structured logging with context
3. Sensitive data censoring
4. Request/response logging
5. Database query logging
6. Cache operation logging
7. Task queue logging
8. Security event logging
9. Error logging with stack traces
10. Performance measurement logging
11. File rotation and JSON output

Run this script to see all logging examples in action.
"""

import time
import structlog
from pathlib import Path

# Import logging configuration
from src.infrastructure.logging.config import setup_logging, LogConfig


def example_1_basic_logging():
    """Example 1: Basic logging"""
    print("\n" + "="*60)
    print("Example 1: Basic Logging")
    print("="*60)
    
    logger = structlog.get_logger("example")
    
    logger.debug("This is a debug message")
    logger.info("Application started", version="1.0.0")
    logger.warning("This is a warning")
    logger.error("An error occurred")
    

def example_2_structured_logging():
    """Example 2: Structured logging with context"""
    print("\n" + "="*60)
    print("Example 2: Structured Logging with Context")
    print("="*60)
    
    logger = structlog.get_logger("user_service")
    
    # Bind context that will be included in all subsequent logs
    logger = logger.bind(
        user_id="user_12345",
        session_id="sess_abc",
        ip_address="192.168.1.100"
    )
    
    logger.info("User logged in", action="login", method="oauth")
    logger.info("Profile updated", action="update", fields=["email", "name"])
    logger.info("User logged out", action="logout", duration_seconds=3600)


def example_3_sensitive_data_censoring():
    """Example 3: Automatic sensitive data censoring"""
    print("\n" + "="*60)
    print("Example 3: Sensitive Data Censoring")
    print("="*60)
    
    logger = structlog.get_logger("security")
    
    # These will be automatically censored
    logger.info(
        "User authentication attempt",
        username="john@example.com",
        password="secret123",  # Will be censored
        api_key="sk-1234567890",  # Will be censored
        token="Bearer xyz123"  # Will be censored
    )
    
    # This won't be censored
    logger.info(
        "Public information",
        username="john@example.com",
        email="john@example.com"
    )


def example_4_request_response_logging():
    """Example 4: HTTP request/response logging"""
    print("\n" + "="*60)
    print("Example 4: Request/Response Logging")
    print("="*60)
    
    logger = structlog.get_logger("http")
    
    # Log incoming request
    logger.info(
        "Incoming request",
        method="POST",
        path="/api/simulations",
        remote_addr="192.168.1.50",
        user_agent="Mozilla/5.0"
    )
    
    # Simulate processing
    time.sleep(0.1)
    
    # Log response
    logger.info(
        "Request completed",
        method="POST",
        path="/api/simulations",
        status_code=201,
        response_time_ms=105.3,
        response_size_bytes=1024
    )


def example_5_database_logging():
    """Example 5: Database query logging"""
    print("\n" + "="*60)
    print("Example 5: Database Query Logging")
    print("="*60)
    
    logger = structlog.get_logger("database")
    
    # Log slow query
    logger.warning(
        "Slow database query detected",
        query="SELECT * FROM simulations WHERE status = 'completed'",
        execution_time_ms=1523.4,
        rows_returned=150,
        connection_pool_size=10
    )
    
    # Log connection issue
    logger.error(
        "Database connection failed",
        error="Connection timeout",
        host="db.example.com",
        port=5432,
        retry_attempt=3
    )
    
    # Log successful transaction
    logger.info(
        "Transaction committed",
        transaction_id="txn_abc123",
        tables_affected=["simulations", "files"],
        rows_modified=5
    )


def example_6_cache_logging():
    """Example 6: Cache operation logging"""
    print("\n" + "="*60)
    print("Example 6: Cache Operation Logging")
    print("="*60)
    
    logger = structlog.get_logger("cache")
    
    # Cache hit
    logger.info(
        "Cache hit",
        key="simulation:123:metadata",
        tier="L1",
        ttl_remaining=3500
    )
    
    # Cache miss
    logger.info(
        "Cache miss",
        key="simulation:456:metadata",
        tier="L1",
        fallback_to="L2"
    )
    
    # Cache eviction
    logger.warning(
        "Cache eviction occurred",
        tier="L2",
        evicted_keys_count=10,
        reason="max_size_reached"
    )


def example_7_task_queue_logging():
    """Example 7: Task queue logging"""
    print("\n" + "="*60)
    print("Example 7: Task Queue Logging")
    print("="*60)
    
    logger = structlog.get_logger("tasks")
    
    # Task submitted
    logger.info(
        "Task submitted",
        task_id="task_abc123",
        task_name="process_simulation_file",
        queue="default",
        priority=5
    )
    
    # Task started
    logger.info(
        "Task started",
        task_id="task_abc123",
        worker_id="worker_1",
        started_at="2024-11-07T12:00:00Z"
    )
    
    # Task completed
    logger.info(
        "Task completed",
        task_id="task_abc123",
        status="success",
        execution_time_seconds=45.2,
        result_size_bytes=2048
    )
    
    # Task failed
    logger.error(
        "Task failed",
        task_id="task_xyz789",
        error="Processing timeout",
        retry_count=2,
        will_retry=True
    )


def example_8_security_logging():
    """Example 8: Security event logging"""
    print("\n" + "="*60)
    print("Example 8: Security Event Logging")
    print("="*60)
    
    logger = structlog.get_logger("security")
    
    # Failed login attempt
    logger.warning(
        "Failed login attempt",
        username="admin",
        ip_address="192.168.1.200",
        reason="invalid_password",
        attempt_number=3
    )
    
    # Suspicious activity
    logger.error(
        "Suspicious activity detected",
        user_id="user_999",
        activity="rapid_api_requests",
        request_count=1000,
        time_window_seconds=60
    )
    
    # Permission denied
    logger.warning(
        "Access denied",
        user_id="user_123",
        resource="/api/admin/users",
        required_role="admin",
        user_role="user"
    )


def example_9_error_logging():
    """Example 9: Error logging with stack traces"""
    print("\n" + "="*60)
    print("Example 9: Error Logging with Stack Traces")
    print("="*60)
    
    logger = structlog.get_logger("application")
    
    try:
        # Simulate an error
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.exception(
            "Unexpected error occurred",
            error_type="ZeroDivisionError",
            operation="division",
            exc_info=True
        )
    
    # Log with additional context
    logger.error(
        "File processing failed",
        file_id="file_abc123",
        file_format="vtk",
        file_size_mb=150,
        error="Corrupted file header",
        recovery_action="quarantine_file"
    )


def example_10_performance_logging():
    """Example 10: Performance measurement logging"""
    print("\n" + "="*60)
    print("Example 10: Performance Measurement Logging")
    print("="*60)
    
    logger = structlog.get_logger("performance")
    
    # Measure operation time
    start_time = time.time()
    
    # Simulate operation
    time.sleep(0.2)
    
    elapsed = (time.time() - start_time) * 1000
    
    logger.info(
        "Operation completed",
        operation="file_parsing",
        duration_ms=elapsed,
        file_size_mb=50,
        throughput_mbps=50 / (elapsed / 1000),
        memory_used_mb=125
    )
    
    # Log resource usage
    logger.info(
        "Resource usage snapshot",
        cpu_percent=45.2,
        memory_percent=62.1,
        disk_io_read_mbps=120.5,
        disk_io_write_mbps=45.3,
        network_rx_mbps=10.2,
        network_tx_mbps=5.8
    )


def example_11_json_output():
    """Example 11: JSON format output"""
    print("\n" + "="*60)
    print("Example 11: JSON Format Output")
    print("="*60)
    print("Switching to JSON output format...")
    
    # Reconfigure for JSON output
    config = LogConfig(
        level="INFO",
        format="json",
        environment="production"
    )
    setup_logging(config)
    
    logger = structlog.get_logger("json_example")
    
    # These will be output as JSON
    logger.info(
        "JSON formatted log entry",
        user_id="user_123",
        action="file_upload",
        file_name="simulation.vtk",
        file_size_bytes=1024000,
        metadata={
            "format": "vtk",
            "version": "4.2",
            "compression": "gzip"
        }
    )
    
    logger.error(
        "Error in JSON format",
        error_code="FILE_TOO_LARGE",
        max_size_mb=500,
        actual_size_mb=750,
        user_id="user_456"
    )


def main():
    """Run all logging examples"""
    print("="*60)
    print("KooAI Logging System - Usage Examples")
    print("="*60)
    
    # Setup logging with console output (human-readable)
    config = LogConfig(
        level="DEBUG",
        format="console",
        environment="development"
    )
    setup_logging(config)
    
    # Run all examples
    example_1_basic_logging()
    example_2_structured_logging()
    example_3_sensitive_data_censoring()
    example_4_request_response_logging()
    example_5_database_logging()
    example_6_cache_logging()
    example_7_task_queue_logging()
    example_8_security_logging()
    example_9_error_logging()
    example_10_performance_logging()
    example_11_json_output()
    
    print("\n" + "="*60)
    print("All logging examples completed!")
    print("="*60)
    print("\nKey Features Demonstrated:")
    print("✅ Structured logging with context")
    print("✅ Automatic sensitive data censoring")
    print("✅ Multiple log levels (DEBUG, INFO, WARNING, ERROR)")
    print("✅ Request/response tracking")
    print("✅ Database query logging")
    print("✅ Cache operation logging")
    print("✅ Task queue logging")
    print("✅ Security event logging")
    print("✅ Error logging with stack traces")
    print("✅ Performance measurement")
    print("✅ JSON output format for production")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
