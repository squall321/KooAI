"""
Celery configuration
"""

from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class CeleryConfig(BaseSettings):
    """
    Celery 설정

    Environment variables나 .env 파일에서 설정을 읽어옵니다.
    """

    # Broker settings
    broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Message broker URL (Redis or RabbitMQ)",
    )
    result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Result backend URL",
    )

    # Task settings
    task_serializer: str = Field(default="json", description="Task serialization format")
    result_serializer: str = Field(default="json", description="Result serialization format")
    accept_content: list[str] = Field(default=["json"], description="Accepted content types")
    timezone: str = Field(default="UTC", description="Timezone for scheduled tasks")
    enable_utc: bool = Field(default=True, description="Enable UTC timezone")

    # Task execution settings
    task_track_started: bool = Field(default=True, description="Track task start events")
    task_time_limit: int = Field(default=3600, description="Hard time limit for tasks (seconds)")
    task_soft_time_limit: int = Field(
        default=3000, description="Soft time limit for tasks (seconds)"
    )
    task_max_retries: int = Field(default=3, description="Maximum task retries")
    task_default_retry_delay: int = Field(default=60, description="Default retry delay (seconds)")

    # Worker settings
    worker_prefetch_multiplier: int = Field(default=4, description="Worker prefetch multiplier")
    worker_max_tasks_per_child: int = Field(default=1000, description="Max tasks per worker child")
    worker_disable_rate_limits: bool = Field(default=False, description="Disable rate limits")

    # Result backend settings
    result_expires: int = Field(
        default=86400, description="Result expiration time (seconds, 24 hours)"
    )
    result_persistent: bool = Field(default=True, description="Persist results to backend")

    # Beat scheduler settings
    beat_schedule_filename: str = Field(
        default="celerybeat-schedule", description="Beat schedule database filename"
    )

    # Monitoring
    task_send_sent_event: bool = Field(default=True, description="Send task-sent events")
    worker_send_task_events: bool = Field(default=True, description="Send task events from workers")

    # Task routes (queue configuration)
    task_default_queue: str = Field(default="default", description="Default queue name")
    task_routes: dict[str, dict[str, str]] = Field(
        default={
            "src.infrastructure.tasks.simulation.*": {"queue": "simulation"},
            "src.infrastructure.tasks.analysis.*": {"queue": "analysis"},
            "src.infrastructure.tasks.cleanup.*": {"queue": "cleanup"},
        },
        description="Task routing configuration",
    )

    # Priority queues
    task_queue_priorities: dict[str, int] = Field(
        default={
            "high": 10,
            "default": 5,
            "low": 1,
        },
        description="Queue priority levels",
    )

    model_config = ConfigDict(
        env_prefix="CELERY_",
        case_sensitive=False,
    )


# Singleton instance
_celery_config: Optional[CeleryConfig] = None


def get_celery_config() -> CeleryConfig:
    """Get Celery configuration singleton"""
    global _celery_config
    if _celery_config is None:
        _celery_config = CeleryConfig()
    return _celery_config
