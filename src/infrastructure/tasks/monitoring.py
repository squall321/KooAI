"""
Monitoring and health check tasks
"""

from datetime import datetime, timezone
from typing import Any, Dict
import structlog

from .base import BaseTask
from .celery_app import celery_app as app


logger = structlog.get_logger(__name__)


@app.task(bind=True, base=BaseTask, name="src.infrastructure.tasks.monitoring.health_check")
def health_check(self: BaseTask) -> dict:
    """
    Perform system health check

    Returns:
        dict: Health check results
    """
    logger.debug("performing_health_check", task_id=self.request.id)

    try:
        health_status: Dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "celery": {
                "active_workers": 0,
                "active_tasks": 0,
            },
            "broker": {
                "status": "connected",
            },
            "backend": {
                "status": "connected",
            },
        }

        # Check Celery workers
        try:
            inspect = app.control.inspect()
            stats = inspect.stats()

            if stats:
                health_status["celery"]["active_workers"] = len(stats)

            active = inspect.active()
            if active:
                task_count = sum(len(tasks) for tasks in active.values())
                health_status["celery"]["active_tasks"] = task_count

        except Exception as e:
            logger.warning("health_check_celery_failed", error=str(e))
            health_status["celery"]["error"] = str(e)
            health_status["status"] = "degraded"

        # Check broker connection
        try:
            app.broker_connection().ensure_connection(max_retries=1)
        except Exception as e:
            logger.warning("health_check_broker_failed", error=str(e))
            health_status["broker"]["status"] = "disconnected"
            health_status["broker"]["error"] = str(e)
            health_status["status"] = "unhealthy"

        # Check backend connection
        try:
            app.backend.client.ping()
        except Exception as e:
            logger.warning("health_check_backend_failed", error=str(e))
            health_status["backend"]["status"] = "disconnected"
            health_status["backend"]["error"] = str(e)
            health_status["status"] = "degraded"

        logger.debug(
            "health_check_completed",
            status=health_status["status"],
            task_id=self.request.id,
        )

        return health_status

    except Exception as e:
        logger.error(
            "health_check_failed",
            error=str(e),
            exc_info=True,
        )
        raise


@app.task(bind=True, base=BaseTask, name="src.infrastructure.tasks.monitoring.get_task_stats")
def get_task_stats(self: BaseTask, limit: int = 100) -> dict:
    """
    Get task execution statistics

    Args:
        limit: Maximum number of tasks to include

    Returns:
        dict: Task statistics
    """
    logger.debug("getting_task_stats", task_id=self.request.id)

    try:
        inspect = app.control.inspect()

        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active": {},
            "scheduled": {},
            "reserved": {},
            "stats": {},
        }

        # Active tasks
        active = inspect.active()
        if active:
            stats["active"] = {worker: tasks[:limit] for worker, tasks in active.items()}

        # Scheduled tasks
        scheduled = inspect.scheduled()
        if scheduled:
            stats["scheduled"] = {worker: tasks[:limit] for worker, tasks in scheduled.items()}

        # Reserved tasks
        reserved = inspect.reserved()
        if reserved:
            stats["reserved"] = {worker: tasks[:limit] for worker, tasks in reserved.items()}

        # Worker stats
        worker_stats = inspect.stats()
        if worker_stats:
            stats["stats"] = worker_stats

        logger.debug("task_stats_retrieved", task_id=self.request.id)

        return stats

    except Exception as e:
        logger.error(
            "get_task_stats_failed",
            error=str(e),
            exc_info=True,
        )
        raise


@app.task(bind=True, base=BaseTask, name="src.infrastructure.tasks.monitoring.get_queue_lengths")
def get_queue_lengths(self: BaseTask) -> dict:
    """
    Get queue lengths for all queues

    Returns:
        dict: Queue lengths
    """
    logger.debug("getting_queue_lengths", task_id=self.request.id)

    try:
        # This would integrate with broker to get queue lengths
        # For Redis:
        queue_lengths = {
            "default": 0,
            "simulation": 0,
            "analysis": 0,
            "cleanup": 0,
            "high": 0,
            "low": 0,
        }

        try:
            # If using Redis backend
            if hasattr(app.backend, "client"):
                redis_client = app.backend.client

                for queue_name in queue_lengths.keys():
                    key = f"celery:queue:{queue_name}"
                    length = redis_client.llen(key)
                    queue_lengths[queue_name] = length

        except Exception as e:
            logger.warning("failed_to_get_queue_lengths_from_redis", error=str(e))

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queues": queue_lengths,
            "total": sum(queue_lengths.values()),
        }

        logger.debug("queue_lengths_retrieved", task_id=self.request.id)

        return result

    except Exception as e:
        logger.error(
            "get_queue_lengths_failed",
            error=str(e),
            exc_info=True,
        )
        raise


@app.task(bind=True, base=BaseTask, name="src.infrastructure.tasks.monitoring.purge_queue")
def purge_queue(self: BaseTask, queue_name: str) -> dict:
    """
    Purge all tasks from a queue

    Args:
        queue_name: Name of queue to purge

    Returns:
        dict: Purge results
    """
    logger.warning(
        "purging_queue",
        queue_name=queue_name,
        task_id=self.request.id,
    )

    try:
        app.control.purge()

        result = {
            "queue_name": queue_name,
            "status": "purged",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.warning(
            "queue_purged",
            queue_name=queue_name,
            task_id=self.request.id,
        )

        return result

    except Exception as e:
        logger.error(
            "purge_queue_failed",
            queue_name=queue_name,
            error=str(e),
            exc_info=True,
        )
        raise


@app.task(bind=True, base=BaseTask, name="src.infrastructure.tasks.monitoring.revoke_task")
def revoke_task(
    self: BaseTask,
    task_id: str,
    terminate: bool = False,
    signal: str = "SIGTERM",
) -> dict:
    """
    Revoke a running task

    Args:
        task_id: Task ID to revoke
        terminate: Whether to terminate the task
        signal: Signal to send if terminating

    Returns:
        dict: Revoke results
    """
    logger.warning(
        "revoking_task",
        revoked_task_id=task_id,
        terminate=terminate,
        task_id=self.request.id,
    )

    try:
        app.control.revoke(task_id, terminate=terminate, signal=signal)

        result = {
            "task_id": task_id,
            "status": "revoked",
            "terminated": terminate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.warning(
            "task_revoked",
            revoked_task_id=task_id,
            task_id=self.request.id,
        )

        return result

    except Exception as e:
        logger.error(
            "revoke_task_failed",
            revoked_task_id=task_id,
            error=str(e),
            exc_info=True,
        )
        raise
