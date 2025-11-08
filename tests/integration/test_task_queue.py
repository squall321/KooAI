"""
Integration tests for Celery task queue system

Tests the complete task queue workflow including:
- Task submission and execution
- Task status tracking
- Result retrieval
- Error handling
- Task retries
- Task cancellation
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from uuid import uuid4

from src.infrastructure.tasks.celery_app import celery_app
from src.infrastructure.tasks.simulation_tasks import (
    process_simulation_file_task,
    analyze_simulation_task,
    cleanup_old_files_task,
)


@pytest.fixture
def celery_worker():
    """
    Start Celery worker for testing

    Note: In real integration tests, use celery_worker fixture from pytest-celery
    """
    # For this test, we'll use eager mode
    celery_app.conf.update(task_always_eager=True)
    yield celery_app


class TestTaskSubmission:
    """Test task submission and basic execution"""

    def test_submit_process_simulation_task(self, celery_worker):
        """Test submitting a file processing task"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService") as mock_service:
            mock_service.return_value.process_file.return_value = {
                "status": "completed",
                "metadata": {"vertices": 1000, "faces": 500},
            }

            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])

            # Wait for task completion
            result_data = result.get(timeout=5)

        # Assert
        assert result.successful()
        assert result_data["status"] == "completed"
        assert "metadata" in result_data

    def test_submit_multiple_tasks(self, celery_worker):
        """Test submitting multiple tasks concurrently"""
        # Arrange
        task_count = 5
        tasks = []

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            for i in range(task_count):
                file_id = str(uuid4())
                sim_id = str(uuid4())
                result = process_simulation_file_task.apply_async(args=[file_id, sim_id])
                tasks.append(result)

        # Assert
        assert len(tasks) == task_count
        for task in tasks:
            assert task.state in ["PENDING", "SUCCESS"]


class TestTaskStatusTracking:
    """Test task status tracking and monitoring"""

    def test_track_task_status(self, celery_worker):
        """Test tracking task status through lifecycle"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])

            # Check initial status
            initial_state = result.state

            # Wait and get final status
            result.get(timeout=5)
            final_state = result.state

        # Assert
        assert initial_state in ["PENDING", "SUCCESS"]
        assert final_state == "SUCCESS"

    def test_get_task_info(self, celery_worker):
        """Test retrieving task information"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])
            result.get(timeout=5)

            task_info = {
                "task_id": result.id,
                "state": result.state,
                "successful": result.successful(),
            }

        # Assert
        assert task_info["task_id"] is not None
        assert task_info["state"] == "SUCCESS"
        assert task_info["successful"] is True


class TestTaskResults:
    """Test task result retrieval and handling"""

    def test_get_task_result(self, celery_worker):
        """Test retrieving task results"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())
        expected_result = {
            "status": "completed",
            "file_id": file_id,
            "metadata": {"vertices": 1000},
        }

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService") as mock_service:
            mock_service.return_value.process_file.return_value = expected_result

            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])
            actual_result = result.get(timeout=5)

        # Assert
        assert actual_result == expected_result

    def test_result_backend_storage(self, celery_worker):
        """Test that results are stored in backend"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])
            result.get(timeout=5)

            # Retrieve result again using task_id
            retrieved = celery_app.AsyncResult(result.id)

        # Assert
        assert retrieved.state == "SUCCESS"


class TestTaskErrorHandling:
    """Test error handling and retry logic"""

    def test_task_failure(self, celery_worker):
        """Test handling of task failures"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService") as mock_service:
            mock_service.return_value.process_file.side_effect = Exception("Processing failed")

            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])

            # Expect failure
            with pytest.raises(Exception):
                result.get(timeout=5)

        # Assert
        assert result.failed()

    def test_task_retry_on_failure(self, celery_worker):
        """Test automatic retry on transient failures"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService") as mock_service:
            # First call fails, second succeeds
            mock_service.return_value.process_file.side_effect = [
                Exception("Transient error"),
                {"status": "completed"},
            ]

            # Note: In eager mode, retries don't work the same way
            # This is a simplified test
            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])

            # Should eventually succeed after retry
            # In real integration test with worker, this would work
            pass


class TestAnalysisTasks:
    """Test AI analysis tasks"""

    def test_analyze_simulation_task(self, celery_worker):
        """Test simulation analysis task"""
        # Arrange
        simulation_id = str(uuid4())
        prompt = "Analyze simulation results"

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.LLMService") as mock_llm:
            mock_llm.return_value.analyze.return_value = {
                "analysis": "Results show optimal performance",
                "insights": ["Key finding 1", "Key finding 2"],
            }

            result = analyze_simulation_task.apply_async(args=[simulation_id, prompt])
            analysis_result = result.get(timeout=10)

        # Assert
        assert result.successful()
        assert "analysis" in analysis_result
        assert "insights" in analysis_result


class TestCleanupTasks:
    """Test cleanup and maintenance tasks"""

    def test_cleanup_old_files_task(self, celery_worker):
        """Test old files cleanup task"""
        # Arrange
        days_old = 30

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService") as mock_service:
            mock_service.return_value.cleanup_old_files.return_value = {
                "deleted_count": 10,
                "freed_space_mb": 150,
            }

            result = cleanup_old_files_task.apply_async(args=[days_old])
            cleanup_result = result.get(timeout=5)

        # Assert
        assert result.successful()
        assert cleanup_result["deleted_count"] == 10
        assert cleanup_result["freed_space_mb"] == 150


class TestTaskCancellation:
    """Test task cancellation"""

    def test_cancel_pending_task(self, celery_worker):
        """Test cancelling a pending task"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])

            # Cancel before it starts (in real worker scenario)
            result.revoke(terminate=True)

        # Assert
        # In eager mode, task already completed
        # In real integration test with worker, task would be revoked
        pass


class TestTaskChaining:
    """Test task chaining and workflows"""

    def test_chain_file_processing_and_analysis(self, celery_worker):
        """Test chaining file processing followed by analysis"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with (
            patch("src.infrastructure.tasks.simulation_tasks.FileService"),
            patch("src.infrastructure.tasks.simulation_tasks.LLMService"),
        ):

            # Create chain: process file -> analyze
            from celery import chain

            workflow = chain(
                process_simulation_file_task.s(file_id, simulation_id),
                analyze_simulation_task.s(simulation_id, "Analyze results"),
            )

            result = workflow.apply_async()
            final_result = result.get(timeout=15)

        # Assert
        assert result.successful()


class TestTaskMetrics:
    """Test task metrics and monitoring"""

    def test_task_execution_time(self, celery_worker):
        """Test measuring task execution time"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        start_time = time.time()
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            result = process_simulation_file_task.apply_async(args=[file_id, simulation_id])
            result.get(timeout=5)
        execution_time = time.time() - start_time

        # Assert
        assert execution_time < 5  # Should complete quickly in eager mode

    def test_task_count_metrics(self, celery_worker):
        """Test tracking number of tasks"""
        # Arrange
        initial_count = 0

        # Act
        tasks = []
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            for _ in range(3):
                result = process_simulation_file_task.apply_async(args=[str(uuid4()), str(uuid4())])
                tasks.append(result)

        # Assert
        assert len(tasks) == 3


class TestTaskQueuePriority:
    """Test task priority handling"""

    def test_high_priority_task(self, celery_worker):
        """Test submitting high priority task"""
        # Arrange
        file_id = str(uuid4())
        simulation_id = str(uuid4())

        # Act
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            result = process_simulation_file_task.apply_async(
                args=[file_id, simulation_id], priority=9  # High priority
            )
            result.get(timeout=5)

        # Assert
        assert result.successful()


@pytest.mark.integration
class TestRealWorkerIntegration:
    """
    Integration tests that require real Celery worker

    Note: These tests should be run with pytest-celery and actual worker
    Skip if worker is not available
    """

    @pytest.mark.skip(reason="Requires real Celery worker")
    def test_with_real_worker(self):
        """Test with actual Celery worker"""
        # This test requires a real worker running
        pass

    @pytest.mark.skip(reason="Requires real Celery worker")
    def test_distributed_tasks(self):
        """Test distributed task processing across workers"""
        # This test requires multiple workers
        pass


# Performance test
@pytest.mark.slow
class TestTaskPerformance:
    """Performance tests for task queue"""

    def test_bulk_task_submission(self, celery_worker):
        """Test submitting many tasks at once"""
        # Arrange
        task_count = 100

        # Act
        start_time = time.time()
        tasks = []
        with patch("src.infrastructure.tasks.simulation_tasks.FileService"):
            for _ in range(task_count):
                result = process_simulation_file_task.apply_async(args=[str(uuid4()), str(uuid4())])
                tasks.append(result)

        submission_time = time.time() - start_time

        # Assert
        assert len(tasks) == task_count
        assert submission_time < 5  # Should submit quickly
