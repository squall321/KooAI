"""
Prometheus Metrics Routes

Exposes application metrics in Prometheus format.
"""

from fastapi import APIRouter, Response

from src.infrastructure.monitoring import collect_all_metrics, get_metrics_content_type
from src.infrastructure.logging import get_logger

router = APIRouter(tags=["metrics"])
logger = get_logger(__name__)


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint

    Exposes all application metrics in Prometheus text format.
    This endpoint should be scraped by Prometheus server.

    Metrics include:
    - HTTP requests (count, duration, status)
    - Database queries (count, duration, errors)
    - Cache operations (hits, misses, evictions)
    - Task queue (size, processing time, workers)
    - Simulations (processed count, file sizes, vertices)
    - System resources (CPU, memory, disk, network)
    - Application info (uptime, version)

    Returns:
        Response: Metrics in Prometheus text format

    Example Prometheus scrape config:
        ```yaml
        scrape_configs:
          - job_name: 'kooai'
            scrape_interval: 15s
            static_configs:
              - targets: ['localhost:8000']
            metrics_path: '/api/v1/metrics'
        ```
    """
    try:
        metrics_data = collect_all_metrics()
        return Response(content=metrics_data, media_type=get_metrics_content_type())

    except Exception as e:
        logger.error("failed_to_collect_metrics", error=str(e))
        return Response(
            content=f"# Error collecting metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500,
        )
