"""
Tests for Celery tasks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.tasks import celery_app, create_celery_app
from src.infrastructure.tasks.config import CeleryConfig


@pytest.fixture
def mock_celery_config():
    """Create mock Celery configuration"""
    return CeleryConfig(
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/0",
    )


def test_create_celery_app():
    """Test Celery app creation"""
    app = create_celery_app()

    assert app is not None
    assert app.conf.broker_url is not None
    assert app.conf.result_backend is not None


def test_celery_app_configuration():
    """Test Celery app has correct configuration"""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.enable_utc is True


def test_celery_beat_schedule():
    """Test beat schedule is configured"""
    beat_schedule = celery_app.conf.beat_schedule

    assert "cleanup-old-files" in beat_schedule
    assert "cleanup-expired-results" in beat_schedule
    assert "health-check" in beat_schedule


def test_task_routes():
    """Test task routes are configured"""
    routes = celery_app.conf.task_routes

    assert "src.infrastructure.tasks.simulation.*" in routes
    assert routes["src.infrastructure.tasks.simulation.*"]["queue"] == "simulation"

    assert "src.infrastructure.tasks.analysis.*" in routes
    assert routes["src.infrastructure.tasks.analysis.*"]["queue"] == "analysis"

    assert "src.infrastructure.tasks.cleanup.*" in routes
    assert routes["src.infrastructure.tasks.cleanup.*"]["queue"] == "cleanup"


def test_debug_task():
    """Test debug task execution"""
    from src.infrastructure.tasks.celery_app import debug_task

    # Mock the task execution
    result = debug_task()

    assert result == "Debug task completed"


@pytest.mark.parametrize(
    "task_name,expected_queue",
    [
        ("src.infrastructure.tasks.simulation.parse_simulation_file", "simulation"),
        ("src.infrastructure.tasks.analysis.analyze_field", "analysis"),
        ("src.infrastructure.tasks.cleanup.cleanup_old_files", "cleanup"),
    ],
)
def test_task_queues(task_name, expected_queue):
    """Test tasks are routed to correct queues"""
    routes = celery_app.conf.task_routes

    # Find matching route
    matched_queue = None
    for pattern, config in routes.items():
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if task_name.startswith(prefix):
                matched_queue = config["queue"]
                break

    assert matched_queue == expected_queue


def test_base_task_retry_config():
    """Test base task has retry configuration"""
    from src.infrastructure.tasks.base import BaseTask

    assert BaseTask.retry_backoff is True
    assert BaseTask.retry_backoff_max == 600
    assert BaseTask.retry_jitter is True
    assert BaseTask.retry_kwargs["max_retries"] == 3


def test_long_running_task_limits():
    """Test long running task has appropriate time limits"""
    from src.infrastructure.tasks.base import LongRunningTask

    assert LongRunningTask.time_limit == 3600
    assert LongRunningTask.soft_time_limit == 3000


@pytest.mark.asyncio
async def test_simulation_task_decorator():
    """Test simulation task decorator"""
    from src.infrastructure.tasks.base import simulation_task

    @simulation_task(name="test.simulation.task")
    def test_task(self):
        return "test"

    assert test_task.queue == "simulation"


@pytest.mark.asyncio
async def test_analysis_task_decorator():
    """Test analysis task decorator"""
    from src.infrastructure.tasks.base import analysis_task

    @analysis_task(name="test.analysis.task")
    def test_task(self):
        return "test"

    assert test_task.queue == "analysis"


@pytest.mark.asyncio
async def test_cleanup_task_decorator():
    """Test cleanup task decorator"""
    from src.infrastructure.tasks.base import cleanup_task

    @cleanup_task(name="test.cleanup.task")
    def test_task(self):
        return "test"

    assert test_task.queue == "cleanup"
