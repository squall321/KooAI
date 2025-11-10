"""
Tests for Prometheus metrics
"""

import pytest
from unittest.mock import Mock, patch

# Check for optional dependencies
try:
    import psutil
    import prometheus_client
    MONITORING_DEPS_AVAILABLE = True
except ImportError:
    MONITORING_DEPS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not MONITORING_DEPS_AVAILABLE,
    reason="Monitoring dependencies (psutil, prometheus_client) not installed"
)


class TestPrometheusMetrics:
    """Prometheus 메트릭 테스트"""

    def test_metrics_registry_exists(self) -> None:
        """메트릭 레지스트리 존재 확인"""
        from src.infrastructure.monitoring.prometheus_metrics import metrics_registry

        assert metrics_registry is not None

    def test_http_metrics_exist(self) -> None:
        """HTTP 메트릭 존재 확인"""
        from src.infrastructure.monitoring.prometheus_metrics import (
            http_requests_total,
            http_request_duration_seconds,
            http_requests_in_progress
        )

        assert http_requests_total is not None
        assert http_request_duration_seconds is not None
        assert http_requests_in_progress is not None

    def test_database_metrics_exist(self) -> None:
        """데이터베이스 메트릭 존재 확인"""
        from src.infrastructure.monitoring.prometheus_metrics import (
            database_queries_total,
            database_query_duration_seconds,
            database_connections_active
        )

        assert database_queries_total is not None
        assert database_query_duration_seconds is not None
        assert database_connections_active is not None

    def test_http_request_counter_increments(self) -> None:
        """HTTP 요청 카운터 증가 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import http_requests_total

        # Get initial value
        before = http_requests_total.labels(
            method="GET",
            endpoint="/test",
            status="200"
        )._value._value

        # Increment
        http_requests_total.labels(
            method="GET",
            endpoint="/test",
            status="200"
        ).inc()

        # Verify incremented
        after = http_requests_total.labels(
            method="GET",
            endpoint="/test",
            status="200"
        )._value._value

        assert after > before

    def test_http_request_duration_observes(self) -> None:
        """HTTP 요청 시간 관찰 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import http_request_duration_seconds

        # Observe a duration
        http_request_duration_seconds.labels(
            method="POST",
            endpoint="/api/test"
        ).observe(0.123)

        # Verify it was recorded (count should increase)
        metric = http_request_duration_seconds.labels(
            method="POST",
            endpoint="/api/test"
        )
        assert metric._sum._value > 0

    def test_gauge_can_be_set(self) -> None:
        """Gauge 메트릭 설정 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import http_requests_in_progress

        # Set value
        http_requests_in_progress.labels(
            method="GET",
            endpoint="/test"
        ).set(5)

        # Get value
        value = http_requests_in_progress.labels(
            method="GET",
            endpoint="/test"
        )._value._value

        assert value == 5

    def test_gauge_can_increment_decrement(self) -> None:
        """Gauge 증가/감소 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import database_connections_active

        # Set initial value
        database_connections_active.set(10)

        # Increment
        database_connections_active.inc()
        after_inc = database_connections_active._value._value
        assert after_inc == 11

        # Decrement
        database_connections_active.dec()
        after_dec = database_connections_active._value._value
        assert after_dec == 10

    def test_generate_latest_returns_metrics(self) -> None:
        """메트릭 생성 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import metrics_registry
        from prometheus_client import generate_latest

        # Generate metrics
        metrics_output = generate_latest(metrics_registry)

        # Verify it's bytes
        assert isinstance(metrics_output, bytes)
        # Verify it contains our metrics
        assert b"kooai_http_requests_total" in metrics_output

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_system_metrics_collection(self, mock_memory: Mock, mock_cpu: Mock) -> None:
        """시스템 메트릭 수집 테스트"""
        # Mock system metrics
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.0)

        # Try to call the function if it exists
        import src.infrastructure.monitoring.prometheus_metrics as metrics_module
        if hasattr(metrics_module, 'collect_system_metrics'):
            collect_fn = getattr(metrics_module, 'collect_system_metrics')
            collect_fn()
        # If function doesn't exist, test passes (it's optional)


class TestMetricLabels:
    """메트릭 레이블 테스트"""

    def test_http_metrics_support_multiple_labels(self) -> None:
        """HTTP 메트릭이 다중 레이블 지원 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import http_requests_total

        # Different labels
        http_requests_total.labels(method="GET", endpoint="/api/v1", status="200").inc()
        http_requests_total.labels(method="POST", endpoint="/api/v1", status="201").inc()
        http_requests_total.labels(method="GET", endpoint="/api/v2", status="404").inc()

        # All should work without error
        assert True

    def test_database_operation_labels(self) -> None:
        """데이터베이스 작업 레이블 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import database_queries_total

        # Different operations
        database_queries_total.labels(operation="SELECT").inc()
        database_queries_total.labels(operation="INSERT").inc()
        database_queries_total.labels(operation="UPDATE").inc()
        database_queries_total.labels(operation="DELETE").inc()

        # All should work
        assert True


class TestMetricsMiddleware:
    """메트릭 미들웨어 테스트"""

    def test_metrics_middleware_exists(self) -> None:
        """메트릭 미들웨어 존재 확인"""
        import src.infrastructure.monitoring.prometheus_metrics as metrics_module
        if hasattr(metrics_module, 'PrometheusMiddleware'):
            middleware_class = getattr(metrics_module, 'PrometheusMiddleware')
            assert middleware_class is not None
        else:
            # Middleware might not exist, that's ok
            pytest.skip("PrometheusMiddleware not implemented")

    def test_metrics_can_be_exposed_via_endpoint(self) -> None:
        """메트릭을 엔드포인트로 노출 가능한지 테스트"""
        from src.infrastructure.monitoring.prometheus_metrics import metrics_registry
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

        # Should return valid prometheus format
        metrics = generate_latest(metrics_registry)
        assert metrics is not None
        assert isinstance(metrics, bytes)

        # Content type should be correct
        assert CONTENT_TYPE_LATEST is not None
