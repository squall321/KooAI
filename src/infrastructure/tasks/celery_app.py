"""
Celery application instance
"""

from typing import Optional
from celery import Celery
from celery.schedules import crontab

from .config import CeleryConfig, get_celery_config


def create_celery_app(config: Optional[CeleryConfig] = None) -> Celery:
    """
    Create and configure Celery application

    Args:
        config: Celery configuration (uses default if None)

    Returns:
        Configured Celery application
    """
    if config is None:
        config = get_celery_config()

    app = Celery("kooai")

    # Configure Celery
    app.conf.update(
        broker_url=config.broker_url,
        result_backend=config.result_backend,
        task_serializer=config.task_serializer,
        result_serializer=config.result_serializer,
        accept_content=config.accept_content,
        timezone=config.timezone,
        enable_utc=config.enable_utc,
        task_track_started=config.task_track_started,
        task_time_limit=config.task_time_limit,
        task_soft_time_limit=config.task_soft_time_limit,
        worker_prefetch_multiplier=config.worker_prefetch_multiplier,
        worker_max_tasks_per_child=config.worker_max_tasks_per_child,
        worker_disable_rate_limits=config.worker_disable_rate_limits,
        result_expires=config.result_expires,
        result_persistent=config.result_persistent,
        task_send_sent_event=config.task_send_sent_event,
        worker_send_task_events=config.worker_send_task_events,
        task_default_queue=config.task_default_queue,
        task_routes=config.task_routes,
    )

    # Beat schedule for periodic tasks
    app.conf.beat_schedule = {
        # Cleanup old simulation files every day at 2 AM
        "cleanup-old-files": {
            "task": "src.infrastructure.tasks.cleanup.cleanup_old_files",
            "schedule": crontab(hour=2, minute=0),
            "kwargs": {"days": 30},
        },
        # Cleanup expired results every 6 hours
        "cleanup-expired-results": {
            "task": "src.infrastructure.tasks.cleanup.cleanup_expired_results",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Health check every 5 minutes
        "health-check": {
            "task": "src.infrastructure.tasks.monitoring.health_check",
            "schedule": 300.0,  # 5 minutes in seconds
        },
    }

    # Auto-discover tasks in the tasks package
    app.autodiscover_tasks(
        [
            "src.infrastructure.tasks.simulation",
            "src.infrastructure.tasks.analysis",
            "src.infrastructure.tasks.cleanup",
            "src.infrastructure.tasks.monitoring",
        ],
        force=True,
    )

    return app


# Global Celery app instance
celery_app = create_celery_app()


# Optional: Celery signal handlers
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    print(f"Request: {self.request!r}")
    return "Debug task completed"
