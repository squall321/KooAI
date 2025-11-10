"""
Base task classes with common functionality
"""

import time
from typing import Any, Optional, Dict, Callable
from celery import Task
import structlog

from .celery_app import celery_app


logger = structlog.get_logger(__name__)


class BaseTask(Task):
    """
    Base task class with common functionality

    Features:
    - Automatic retry with exponential backoff
    - Structured logging
    - Error handling
    - Execution time tracking
    """

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute task with timing and logging"""
        start_time = time.time()
        task_id = self.request.id
        task_name = self.name

        logger.info(
            "task_started",
            task_id=task_id,
            task_name=task_name,
            args=args,
            kwargs=kwargs,
        )

        try:
            result = super().__call__(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                "task_completed",
                task_id=task_id,
                task_name=task_name,
                execution_time=execution_time,
            )

            return result

        except Exception as exc:
            execution_time = time.time() - start_time

            logger.error(
                "task_failed",
                task_id=task_id,
                task_name=task_name,
                execution_time=execution_time,
                error=str(exc),
                exc_info=True,
            )

            raise

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Called when task is retried"""
        logger.warning(
            "task_retry",
            task_id=task_id,
            task_name=self.name,
            retry_count=self.request.retries,
            max_retries=self.max_retries,
            error=str(exc),
        )

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        """Called when task fails after all retries"""
        logger.error(
            "task_failed_permanently",
            task_id=task_id,
            task_name=self.name,
            retry_count=self.request.retries,
            error=str(exc),
            exc_info=True,
        )


class LongRunningTask(BaseTask):
    """
    Base class for long-running tasks

    Features:
    - Extended time limits
    - Progress tracking
    - Cancellation support
    """

    time_limit = 3600  # 1 hour
    soft_time_limit = 3000  # 50 minutes

    def update_progress(self, current: int, total: int, status: Optional[str] = None) -> None:
        """
        Update task progress

        Args:
            current: Current progress value
            total: Total expected value
            status: Optional status message
        """
        meta: Dict[str, Any] = {
            "current": current,
            "total": total,
            "percent": int((current / total) * 100) if total > 0 else 0,
        }

        if status:
            meta["status"] = status

        self.update_state(state="PROGRESS", meta=meta)

        logger.debug(
            "task_progress",
            task_id=self.request.id,
            task_name=self.name,
            **meta,
        )


class HighPriorityTask(BaseTask):
    """High priority task"""

    queue = "high"
    priority = 10


class LowPriorityTask(BaseTask):
    """Low priority task"""

    queue = "low"
    priority = 1


# Task decorators for common use cases
def simulation_task(*args: Any, **kwargs: Any) -> Callable[..., Any]:
    """Decorator for simulation-related tasks"""
    kwargs.setdefault("base", LongRunningTask)
    kwargs.setdefault("bind", True)
    kwargs.setdefault("queue", "simulation")
    return celery_app.task(*args, **kwargs)


def analysis_task(*args: Any, **kwargs: Any) -> Callable[..., Any]:
    """Decorator for analysis tasks"""
    kwargs.setdefault("base", LongRunningTask)
    kwargs.setdefault("bind", True)
    kwargs.setdefault("queue", "analysis")
    return celery_app.task(*args, **kwargs)


def cleanup_task(*args: Any, **kwargs: Any) -> Callable[..., Any]:
    """Decorator for cleanup tasks"""
    kwargs.setdefault("base", BaseTask)
    kwargs.setdefault("bind", True)
    kwargs.setdefault("queue", "cleanup")
    return celery_app.task(*args, **kwargs)


def high_priority_task(*args: Any, **kwargs: Any) -> Callable[..., Any]:
    """Decorator for high priority tasks"""
    kwargs.setdefault("base", HighPriorityTask)
    kwargs.setdefault("bind", True)
    return celery_app.task(*args, **kwargs)
