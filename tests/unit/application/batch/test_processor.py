"""
Tests for BatchProcessor
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import time

from src.application.batch.processor import (
    BatchProcessor,
    BatchJob,
    BatchResult,
    JobStatus,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory with test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        (tmpdir / "file1.txt").write_text("content1")
        (tmpdir / "file2.txt").write_text("content2")
        (tmpdir / "file3.txt").write_text("content3")
        (tmpdir / "subdir").mkdir()
        (tmpdir / "subdir" / "file4.txt").write_text("content4")

        yield tmpdir


def test_batch_job_creation():
    """Test BatchJob creation"""
    job = BatchJob(
        job_id="job1",
        file_path=Path("/test/file.txt"),
    )

    assert job.job_id == "job1"
    assert job.status == JobStatus.PENDING
    assert job.started_at is None
    assert job.completed_at is None
    assert job.error is None
    assert job.result is None


def test_batch_job_mark_running():
    """Test marking job as running"""
    job = BatchJob(job_id="job1", file_path=Path("/test/file.txt"))

    job.mark_running()

    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None


def test_batch_job_mark_completed():
    """Test marking job as completed"""
    job = BatchJob(job_id="job1", file_path=Path("/test/file.txt"))
    job.mark_running()

    result = {"data": "test"}
    job.mark_completed(result)

    assert job.status == JobStatus.COMPLETED
    assert job.completed_at is not None
    assert job.result == result


def test_batch_job_mark_failed():
    """Test marking job as failed"""
    job = BatchJob(job_id="job1", file_path=Path("/test/file.txt"))
    job.mark_running()

    job.mark_failed("Test error")

    assert job.status == JobStatus.FAILED
    assert job.completed_at is not None
    assert job.error == "Test error"


def test_batch_job_duration():
    """Test job duration calculation"""
    job = BatchJob(job_id="job1", file_path=Path("/test/file.txt"))

    # Not started yet
    assert job.duration() is None

    # Start job
    job.mark_running()
    time.sleep(0.1)
    job.mark_completed()

    duration = job.duration()
    assert duration is not None
    assert duration > 0


def test_batch_result_success_rate():
    """Test BatchResult success rate calculation"""
    jobs = [
        BatchJob(job_id="job1", file_path=Path("/test/file1.txt"), status=JobStatus.COMPLETED),
        BatchJob(job_id="job2", file_path=Path("/test/file2.txt"), status=JobStatus.COMPLETED),
        BatchJob(job_id="job3", file_path=Path("/test/file3.txt"), status=JobStatus.FAILED),
    ]

    result = BatchResult(
        total_jobs=3,
        completed=2,
        failed=1,
        skipped=0,
        total_duration=10.0,
        avg_duration=3.33,
        jobs=jobs,
    )

    assert result.success_rate() == pytest.approx(66.67, abs=0.1)


def test_batch_result_to_dict():
    """Test BatchResult to_dict conversion"""
    jobs = [
        BatchJob(job_id="job1", file_path=Path("/test/file1.txt"), status=JobStatus.COMPLETED),
        BatchJob(job_id="job2", file_path=Path("/test/file2.txt"), status=JobStatus.FAILED, error="Test error"),
    ]

    result = BatchResult(
        total_jobs=2,
        completed=1,
        failed=1,
        skipped=0,
        total_duration=5.0,
        avg_duration=2.5,
        jobs=jobs,
    )

    result_dict = result.to_dict()

    assert result_dict["total_jobs"] == 2
    assert result_dict["completed"] == 1
    assert result_dict["failed"] == 1
    assert "success_rate" in result_dict
    assert len(result_dict["failed_jobs"]) == 1
    assert result_dict["failed_jobs"][0]["error"] == "Test error"


def test_batch_processor_initialization():
    """Test BatchProcessor initialization"""
    processor = BatchProcessor(max_workers=8, stop_on_error=True, skip_existing=False)

    assert processor.max_workers == 8
    assert processor.stop_on_error is True
    assert processor.skip_existing is False
    assert len(processor.jobs) == 0


def test_batch_processor_add_files(temp_dir):
    """Test adding files to batch"""
    processor = BatchProcessor()

    files = [
        temp_dir / "file1.txt",
        temp_dir / "file2.txt",
    ]

    processor.add_files(files)

    assert len(processor.jobs) == 2
    assert processor.jobs[0].status == JobStatus.PENDING


def test_batch_processor_add_directory(temp_dir):
    """Test adding directory to batch"""
    processor = BatchProcessor()

    processor.add_files([temp_dir], pattern="*.txt")

    # Should find file1.txt, file2.txt, file3.txt (not recursive)
    assert len(processor.jobs) == 3


def test_batch_processor_process(temp_dir):
    """Test sequential processing"""
    processor = BatchProcessor(max_workers=1)

    # Create test files
    files = []
    for i in range(3):
        file_path = temp_dir / f"process_file{i}.txt"
        file_path.write_text(f"content{i}")
        files.append(file_path)

    processor.add_files(files)

    call_count = 0

    def processor_func(file_path):
        nonlocal call_count
        call_count += 1
        return f"processed_{file_path.name}"

    result = processor.process(processor_func)

    assert call_count == 3
    assert result.total_jobs == 3
    assert result.completed == 3
    assert result.failed == 0


def test_batch_processor_process_with_error(temp_dir):
    """Test processing with errors"""
    processor = BatchProcessor(stop_on_error=False)

    # Create test files
    files = []
    for i in range(3):
        file_path = temp_dir / f"error_file{i}.txt"
        file_path.write_text(f"content{i}")
        files.append(file_path)

    processor.add_files(files)

    def processor_func(file_path):
        if "error_file1" in str(file_path):
            raise ValueError("Test error")
        return f"processed_{file_path.name}"

    result = processor.process(processor_func)

    assert result.total_jobs == 3
    assert result.completed == 2
    assert result.failed == 1


def test_batch_processor_stop_on_error(temp_dir):
    """Test stop_on_error behavior"""
    processor = BatchProcessor(stop_on_error=True)

    # Create test files
    files = []
    for i in range(3):
        file_path = temp_dir / f"stop_file{i}.txt"
        file_path.write_text(f"content{i}")
        files.append(file_path)

    processor.add_files(files)

    def processor_func(file_path):
        if "stop_file1" in str(file_path):
            raise ValueError("Test error")
        return f"processed_{file_path.name}"

    result = processor.process(processor_func)

    # Should stop after first error
    assert result.failed > 0


def test_batch_processor_parallel(temp_dir):
    """Test parallel processing"""
    processor = BatchProcessor(max_workers=2)

    # Create test files
    files = []
    for i in range(5):
        file_path = temp_dir / f"parallel_file{i}.txt"
        file_path.write_text(f"content{i}")
        files.append(file_path)

    processor.add_files(files)

    def processor_func(file_path):
        time.sleep(0.01)  # Simulate work
        return f"processed_{file_path.name}"

    result = processor.process_parallel(processor_func)

    # Check all jobs completed
    assert result.total_jobs == 5
    assert result.completed == 5
    assert result.failed == 0


def test_batch_processor_progress_callback(temp_dir):
    """Test progress callback"""
    processor = BatchProcessor()

    # Create test files
    files = []
    for i in range(3):
        file_path = temp_dir / f"callback_file{i}.txt"
        file_path.write_text(f"content{i}")
        files.append(file_path)

    processor.add_files(files)

    progress_updates = []

    def progress_callback(current, total):
        progress_updates.append((current, total))

    def processor_func(file_path):
        return f"processed_{file_path.name}"

    processor.process_parallel(processor_func, progress_callback=progress_callback)

    # Should have received progress updates
    assert len(progress_updates) > 0
    assert progress_updates[-1] == (3, 3)  # Final update


def test_batch_processor_empty_batch():
    """Test processing empty batch"""
    processor = BatchProcessor()

    def processor_func(file_path):
        return "processed"

    result = processor.process(processor_func)

    assert result.total_jobs == 0
    assert result.completed == 0
    assert result.failed == 0


def test_batch_processor_metadata():
    """Test job metadata"""
    processor = BatchProcessor()

    job = BatchJob(
        job_id="job1",
        file_path=Path("/test/file.txt"),
        metadata={"priority": "high", "user": "test_user"}
    )

    assert job.metadata["priority"] == "high"
    assert job.metadata["user"] == "test_user"
