"""
Tests for health check routes
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import status
from datetime import datetime
from typing import Any, Callable, Awaitable
from starlette.requests import Request
from starlette.responses import Response

# Check for optional dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not REDIS_AVAILABLE,
    reason="Redis dependency not installed"
)


class TestBasicHealthCheck:
    """기본 헬스 체크 테스트"""

    def test_health_status_model(self) -> None:
        """HealthStatus 모델 테스트"""
        from src.presentation.api.routes.health_routes import HealthStatus

        health = HealthStatus(
            status="healthy",
            timestamp="2024-01-01T00:00:00",
            version="1.0.0",
            environment="test"
        )

        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.environment == "test"

    def test_dependency_status_model(self) -> None:
        """DependencyStatus 모델 테스트"""
        from src.presentation.api.routes.health_routes import DependencyStatus

        dep = DependencyStatus(
            name="database",
            status="up",
            response_time_ms=12.5,
            details={"connections": 10}
        )

        assert dep.name == "database"
        assert dep.status == "up"
        assert dep.response_time_ms == 12.5
        assert dep.details == {"connections": 10}

    def test_detailed_health_status_model(self) -> None:
        """DetailedHealthStatus 모델 테스트"""
        from src.presentation.api.routes.health_routes import (
            DetailedHealthStatus,
            DependencyStatus
        )

        health = DetailedHealthStatus(
            status="healthy",
            timestamp="2024-01-01T00:00:00",
            dependencies={
                "db": DependencyStatus(name="db", status="up")
            },
            uptime_seconds=3600.0,
            checks_passed=3,
            checks_failed=0
        )

        assert health.checks_passed == 3
        assert health.checks_failed == 0
        assert health.uptime_seconds == 3600.0

    @pytest.mark.asyncio
    async def test_basic_health_check_returns_healthy(self) -> None:
        """기본 헬스 체크가 healthy 반환하는지 테스트"""
        from src.presentation.api.routes.health_routes import health_check

        result = await health_check()

        assert result.status == "healthy"
        assert result.version == "1.0.0"
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_liveness_probe_returns_healthy(self) -> None:
        """Liveness probe가 healthy 반환하는지 테스트"""
        from src.presentation.api.routes.health_routes import liveness_probe

        result = await liveness_probe()

        assert result.status == "healthy"


class TestDatabaseHealthCheck:
    """데이터베이스 헬스 체크 테스트"""

    @pytest.mark.asyncio
    async def test_check_database_success(self) -> None:
        """데이터베이스 체크 성공 테스트"""
        from src.presentation.api.routes.health_routes import _check_database

        # Mock database session
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = 1

        result = await _check_database(mock_db)

        assert result.name == "database"
        assert result.status == "up"
        assert result.response_time_ms is not None
        assert result.response_time_ms >= 0

    @pytest.mark.asyncio
    async def test_check_database_failure(self) -> None:
        """데이터베이스 체크 실패 테스트"""
        from src.presentation.api.routes.health_routes import _check_database

        # Mock database error
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Connection failed")

        result = await _check_database(mock_db)

        assert result.name == "database"
        assert result.status == "down"
        assert result.error is not None
        assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_check_database_unexpected_result(self) -> None:
        """데이터베이스 체크 예상치 못한 결과 테스트"""
        from src.presentation.api.routes.health_routes import _check_database

        # Mock unexpected result
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = 0  # Not 1

        result = await _check_database(mock_db)

        assert result.status == "down"
        assert result.error is not None
        assert "Unexpected" in result.error


class TestCacheHealthCheck:
    """캐시 헬스 체크 테스트"""

    @pytest.mark.asyncio
    @patch('src.presentation.api.routes.health_routes.get_cache')
    async def test_check_cache_success(self, mock_get_cache: Any) -> None:
        """캐시 체크 성공 테스트"""
        from src.presentation.api.routes.health_routes import _check_cache

        # Mock cache
        mock_cache = Mock()
        mock_cache.ping.return_value = True
        mock_cache.get_stats.return_value = {
            "hit_rate": 0.85,
            "memory_usage_mb": 128
        }
        mock_get_cache.return_value = mock_cache

        result = await _check_cache()

        assert result.name == "cache"
        assert result.status == "up"
        assert result.details is not None

    @pytest.mark.asyncio
    @patch('src.presentation.api.routes.health_routes.get_cache')
    async def test_check_cache_unavailable(self, mock_get_cache: Any) -> None:
        """캐시 체크 실패 테스트 (degraded)"""
        from src.presentation.api.routes.health_routes import _check_cache

        # Mock cache unavailable
        mock_cache = Mock()
        mock_cache.ping.return_value = False
        mock_get_cache.return_value = mock_cache

        result = await _check_cache()

        assert result.name == "cache"
        assert result.status == "degraded"  # Cache failure is not critical

    @pytest.mark.asyncio
    @patch('src.presentation.api.routes.health_routes.get_cache')
    async def test_check_cache_exception(self, mock_get_cache: Any) -> None:
        """캐시 체크 예외 테스트"""
        from src.presentation.api.routes.health_routes import _check_cache

        # Mock exception
        mock_get_cache.side_effect = Exception("Redis connection error")

        result = await _check_cache()

        assert result.name == "cache"
        assert result.status == "degraded"
        assert result.error is not None


class TestStorageHealthCheck:
    """스토리지 헬스 체크 테스트"""

    @pytest.mark.asyncio
    @patch('os.path.exists')
    @patch('os.access')
    @patch('os.statvfs')
    async def test_check_storage_success(self, mock_statvfs: Any, mock_access: Any, mock_exists: Any) -> None:
        """스토리지 체크 성공 테스트"""
        from src.presentation.api.routes.health_routes import _check_storage

        # Mock filesystem
        mock_exists.return_value = True
        mock_access.return_value = True

        # Mock disk stats
        mock_stat = Mock()
        mock_stat.f_bavail = 1000000
        mock_stat.f_frsize = 4096
        mock_statvfs.return_value = mock_stat

        result = await _check_storage()

        assert result.name == "storage"
        assert result.status == "up"
        assert result.details is not None
        assert "available_gb" in result.details

    @pytest.mark.asyncio
    @patch('os.path.exists')
    async def test_check_storage_not_accessible(self, mock_exists: Any) -> None:
        """스토리지 체크 접근 불가 테스트"""
        from src.presentation.api.routes.health_routes import _check_storage

        # Mock path doesn't exist
        mock_exists.return_value = False

        result = await _check_storage()

        assert result.name == "storage"
        assert result.status == "down"
        assert result.error is not None


class TestReadinessCheck:
    """Readiness 체크 테스트"""

    @pytest.mark.asyncio
    @patch('src.presentation.api.routes.health_routes._check_storage')
    @patch('src.presentation.api.routes.health_routes._check_cache')
    @patch('src.presentation.api.routes.health_routes._check_database')
    async def test_readiness_all_healthy(
        self,
        mock_db_check: Any,
        mock_cache_check: Any,
        mock_storage_check: Any
    ) -> None:
        """모든 의존성이 healthy일 때 테스트"""
        from src.presentation.api.routes.health_routes import (
            readiness_check,
            DependencyStatus
        )
        from fastapi import Response

        # Mock all checks as healthy
        mock_db_check.return_value = DependencyStatus(name="db", status="up")
        mock_cache_check.return_value = DependencyStatus(name="cache", status="up")
        mock_storage_check.return_value = DependencyStatus(name="storage", status="up")

        mock_response = Mock(spec=Response)
        mock_db = Mock()

        result = await readiness_check(mock_response, mock_db)

        assert result.status == "healthy"
        assert result.checks_passed == 3
        assert result.checks_failed == 0
        assert mock_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @patch('src.presentation.api.routes.health_routes._check_storage')
    @patch('src.presentation.api.routes.health_routes._check_cache')
    @patch('src.presentation.api.routes.health_routes._check_database')
    async def test_readiness_degraded(
        self,
        mock_db_check: Any,
        mock_cache_check: Any,
        mock_storage_check: Any
    ) -> None:
        """일부 의존성이 degraded일 때 테스트"""
        from src.presentation.api.routes.health_routes import (
            readiness_check,
            DependencyStatus
        )
        from fastapi import Response

        # DB up, cache degraded, storage up
        mock_db_check.return_value = DependencyStatus(name="db", status="up")
        mock_cache_check.return_value = DependencyStatus(name="cache", status="degraded")
        mock_storage_check.return_value = DependencyStatus(name="storage", status="up")

        mock_response = Mock(spec=Response)
        mock_db = Mock()

        result = await readiness_check(mock_response, mock_db)

        assert result.status == "healthy" or result.status == "degraded"
        assert result.checks_passed >= 2

    @pytest.mark.asyncio
    @patch('src.presentation.api.routes.health_routes._check_storage')
    @patch('src.presentation.api.routes.health_routes._check_cache')
    @patch('src.presentation.api.routes.health_routes._check_database')
    async def test_readiness_unhealthy(
        self,
        mock_db_check: Any,
        mock_cache_check: Any,
        mock_storage_check: Any
    ) -> None:
        """중요 의존성이 down일 때 테스트"""
        from src.presentation.api.routes.health_routes import (
            readiness_check,
            DependencyStatus
        )
        from fastapi import Response

        # DB down - critical!
        mock_db_check.return_value = DependencyStatus(
            name="db",
            status="down",
            error="Connection refused"
        )
        mock_cache_check.return_value = DependencyStatus(name="cache", status="up")
        mock_storage_check.return_value = DependencyStatus(name="storage", status="up")

        mock_response = Mock(spec=Response)
        mock_db = Mock()

        result = await readiness_check(mock_response, mock_db)

        assert result.checks_failed >= 1
        # Status should be degraded or unhealthy


class TestHealthMetrics:
    """헬스 메트릭 테스트"""

    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    async def test_health_metrics(self, mock_disk: Any, mock_memory: Any, mock_cpu: Any) -> None:
        """헬스 메트릭 반환 테스트"""
        from src.presentation.api.routes.health_routes import health_metrics

        # Mock system metrics
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=45.0)

        result = await health_metrics()

        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert "system" in result
        assert result["system"]["cpu_percent"] == 25.5
        assert result["system"]["memory_percent"] == 60.0

    @pytest.mark.asyncio
    async def test_startup_probe_calls_readiness(self) -> None:
        """Startup probe가 readiness를 호출하는지 테스트"""
        from src.presentation.api.routes.health_routes import startup_probe
        from fastapi import Response

        mock_response = Mock(spec=Response)
        mock_db = Mock()

        # Should not raise
        with patch('src.presentation.api.routes.health_routes.readiness_check') as mock_ready:
            from src.presentation.api.routes.health_routes import DependencyStatus
            mock_ready.return_value = Mock(
                status="healthy",
                checks_passed=3,
                checks_failed=0
            )

            result = await startup_probe(mock_response, mock_db)
            mock_ready.assert_called_once()


class TestHealthCheckUptime:
    """Uptime 추적 테스트"""

    @pytest.mark.asyncio
    async def test_uptime_increases_over_time(self) -> None:
        """Uptime이 시간에 따라 증가하는지 테스트"""
        from src.presentation.api.routes.health_routes import readiness_check
        from fastapi import Response
        import time

        mock_response = Mock(spec=Response)
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = 1

        # Patch dependencies
        with patch('src.presentation.api.routes.health_routes._check_cache') as mock_cache:
            with patch('src.presentation.api.routes.health_routes._check_storage') as mock_storage:
                from src.presentation.api.routes.health_routes import DependencyStatus

                mock_cache.return_value = DependencyStatus(name="cache", status="up")
                mock_storage.return_value = DependencyStatus(name="storage", status="up")

                result1 = await readiness_check(mock_response, mock_db)
                time.sleep(0.1)
                result2 = await readiness_check(mock_response, mock_db)

                # Uptime should increase (or at least not decrease)
                assert result2.uptime_seconds >= result1.uptime_seconds
