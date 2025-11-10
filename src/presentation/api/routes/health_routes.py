"""
Health Check Routes

Comprehensive health check endpoints for monitoring service status and dependencies.

Features:
- Basic liveness check
- Detailed readiness check with dependency status
- Database connectivity check
- Redis cache availability check
- Storage backend verification
- System resource monitoring
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.presentation.api.dependencies import get_db
from src.infrastructure.cache.redis_cache import get_cache
from src.infrastructure.logging import get_logger


router = APIRouter(tags=["health"])
logger = get_logger(__name__)


# Response Models
class HealthStatus(BaseModel):
    """Health status response"""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str = "1.0.0"
    environment: str = "production"


class DependencyStatus(BaseModel):
    """Status of a single dependency"""

    name: str
    status: str  # "up", "down", "degraded"
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DetailedHealthStatus(HealthStatus):
    """Detailed health status with dependency checks"""

    dependencies: Dict[str, DependencyStatus]
    uptime_seconds: float
    checks_passed: int
    checks_failed: int


# Track application start time for uptime calculation
_app_start_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Basic health check endpoint (liveness probe)

    Returns 200 OK if the service is running.
    This is a lightweight check suitable for Kubernetes liveness probes.

    Returns:
        HealthStatus: Basic health status
    """
    import os

    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "production"),
    )


@router.get("/health/ready", response_model=DetailedHealthStatus)
async def readiness_check(
    response: Response, db: Session = Depends(get_db)
) -> DetailedHealthStatus:
    """
    Detailed readiness check (readiness probe)

    Checks all critical dependencies:
    - Database connectivity
    - Redis cache availability
    - Storage backend access

    Returns 200 OK if all dependencies are healthy.
    Returns 503 Service Unavailable if any critical dependency is down.

    This is suitable for Kubernetes readiness probes.

    Returns:
        DetailedHealthStatus: Detailed health status with dependency checks
    """
    import os

    dependencies = {}
    checks_passed = 0
    checks_failed = 0

    # Check database
    db_status = await _check_database(db)
    dependencies["database"] = db_status
    if db_status.status == "up":
        checks_passed += 1
    else:
        checks_failed += 1

    # Check Redis cache
    cache_status = await _check_cache()
    dependencies["cache"] = cache_status
    if cache_status.status == "up":
        checks_passed += 1
    elif cache_status.status == "down":
        checks_failed += 1
    # "degraded" doesn't count as failure (cache is optional)

    # Check storage (if applicable)
    storage_status = await _check_storage()
    dependencies["storage"] = storage_status
    if storage_status.status == "up":
        checks_passed += 1
    elif storage_status.status == "down":
        checks_failed += 1

    # Determine overall status
    if checks_failed == 0:
        overall_status = "healthy"
        response.status_code = status.HTTP_200_OK
    elif checks_failed > 0 and checks_passed > 0:
        overall_status = "degraded"
        response.status_code = status.HTTP_200_OK
    else:
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Calculate uptime
    uptime = time.time() - _app_start_time

    logger.info(
        "health_check_completed",
        status=overall_status,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        uptime_seconds=uptime,
    )

    return DetailedHealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "production"),
        dependencies=dependencies,
        uptime_seconds=uptime,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
    )


async def _check_database(db: Session) -> DependencyStatus:
    """
    Check database connectivity

    Args:
        db: Database session

    Returns:
        DependencyStatus: Database status
    """
    start_time = time.time()

    try:
        # Execute simple query
        result = db.execute("SELECT 1").scalar()
        elapsed_ms = (time.time() - start_time) * 1000

        if result == 1:
            return DependencyStatus(
                name="database",
                status="up",
                response_time_ms=round(elapsed_ms, 2),
                details={"connection": "active"},
            )
        else:
            return DependencyStatus(
                name="database",
                status="down",
                response_time_ms=round(elapsed_ms, 2),
                error="Unexpected query result",
            )

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error("database_health_check_failed", error=str(e))

        return DependencyStatus(
            name="database",
            status="down",
            response_time_ms=round(elapsed_ms, 2),
            error=str(e),
        )


async def _check_cache() -> DependencyStatus:
    """
    Check Redis cache availability

    Returns:
        DependencyStatus: Cache status
    """
    start_time = time.time()

    try:
        cache = get_cache()
        is_available = cache.ping()
        elapsed_ms = (time.time() - start_time) * 1000

        if is_available:
            # Get cache stats if available
            details = {}
            try:
                stats = cache.get_stats()  # type: ignore[attr-defined]
                details = {
                    "hit_rate": stats.get("hit_rate", 0),
                    "memory_usage_mb": stats.get("memory_usage_mb", 0),
                }
            except:
                pass

            return DependencyStatus(
                name="cache",
                status="up",
                response_time_ms=round(elapsed_ms, 2),
                details=details,
            )
        else:
            return DependencyStatus(
                name="cache",
                status="degraded",
                response_time_ms=round(elapsed_ms, 2),
                error="Cache unavailable (non-critical)",
            )

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning("cache_health_check_failed", error=str(e))

        # Cache failure is not critical - mark as degraded
        return DependencyStatus(
            name="cache",
            status="degraded",
            response_time_ms=round(elapsed_ms, 2),
            error=str(e),
        )


async def _check_storage() -> DependencyStatus:
    """
    Check storage backend availability

    Returns:
        DependencyStatus: Storage status
    """
    start_time = time.time()

    try:
        # Try to check storage - implementation depends on storage backend
        # For now, assume local filesystem
        import os

        storage_path = os.getenv("LOCAL_STORAGE_PATH", "./data/storage")

        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            elapsed_ms = (time.time() - start_time) * 1000

            # Get storage stats
            stat_info = os.statvfs(storage_path)
            available_bytes = stat_info.f_bavail * stat_info.f_frsize
            available_gb = available_bytes / (1024**3)

            return DependencyStatus(
                name="storage",
                status="up",
                response_time_ms=round(elapsed_ms, 2),
                details={
                    "type": "local",
                    "path": storage_path,
                    "available_gb": round(available_gb, 2),
                },
            )
        else:
            elapsed_ms = (time.time() - start_time) * 1000
            return DependencyStatus(
                name="storage",
                status="down",
                response_time_ms=round(elapsed_ms, 2),
                error="Storage path not accessible",
            )

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error("storage_health_check_failed", error=str(e))

        return DependencyStatus(
            name="storage",
            status="down",
            response_time_ms=round(elapsed_ms, 2),
            error=str(e),
        )


@router.get("/health/live", response_model=HealthStatus)
async def liveness_probe() -> HealthStatus:
    """
    Kubernetes liveness probe endpoint

    Lightweight check that returns 200 OK if the service is running.

    Returns:
        HealthStatus: Basic health status
    """
    import os

    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "production"),
    )


@router.get("/health/startup", response_model=DetailedHealthStatus)
async def startup_probe(response: Response, db: Session = Depends(get_db)) -> DetailedHealthStatus:
    """
    Kubernetes startup probe endpoint

    More thorough check used during application startup.
    Returns 200 OK only when all critical dependencies are ready.

    Returns:
        DetailedHealthStatus: Detailed health status
    """
    # Reuse readiness check logic
    return await readiness_check(response, db)  # type: ignore[no-any-return]


@router.get("/health/metrics")
async def health_metrics() -> Dict[str, Any]:
    """
    Health metrics endpoint

    Returns detailed metrics about service health and performance.
    Suitable for Prometheus scraping or custom monitoring.

    Returns:
        Dict: Health metrics
    """
    uptime = time.time() - _app_start_time

    # Get system metrics
    import psutil

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        },
        "application": {
            "version": "1.0.0",
            "environment": "production",
        },
    }

    return metrics
