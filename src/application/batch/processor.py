"""
Batch processor

Process multiple simulation files in batch
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Batch job status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchJob:
    """Single job in a batch"""

    job_id: str
    file_path: Path
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_running(self) -> None:
        """Mark job as running"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, result: Any = None) -> None:
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def mark_failed(self, error: str) -> None:
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class BatchResult:
    """Result of batch processing"""

    total_jobs: int
    completed: int
    failed: int
    skipped: int

    total_duration: float
    avg_duration: float

    jobs: List[BatchJob]

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed / self.total_jobs) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_jobs": self.total_jobs,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": self.success_rate(),
            "total_duration": self.total_duration,
            "avg_duration": self.avg_duration,
            "failed_jobs": [
                {"job_id": job.job_id, "file_path": str(job.file_path), "error": job.error}
                for job in self.jobs
                if job.status == JobStatus.FAILED
            ],
        }


class BatchProcessor:
    """
    Process multiple files in batch

    Features:
    - Parallel processing
    - Error handling
    - Progress tracking
    - Resume capability
    """

    def __init__(
        self,
        max_workers: int = 4,
        stop_on_error: bool = False,
        skip_existing: bool = True,
    ):
        """
        Initialize batch processor

        Args:
            max_workers: Maximum parallel workers
            stop_on_error: Whether to stop on first error
            skip_existing: Skip already processed files
        """
        self.max_workers = max_workers
        self.stop_on_error = stop_on_error
        self.skip_existing = skip_existing
        self.jobs: List[BatchJob] = []

    def add_files(
        self,
        file_paths: List[Path],
        pattern: Optional[str] = None,
    ) -> None:
        """
        Add files to batch

        Args:
            file_paths: List of file paths
            pattern: Optional glob pattern to filter files
        """
        for path in file_paths:
            if path.is_dir():
                # Add all files in directory
                if pattern:
                    files = list(path.glob(pattern))
                else:
                    files = list(path.glob("*"))
                for file in files:
                    if file.is_file():
                        self._add_job(file)
            elif path.is_file():
                self._add_job(path)

    def add_directory(
        self,
        directory: Path,
        pattern: str = "*.csv",
        recursive: bool = False,
    ) -> None:
        """
        Add all files from a directory

        Args:
            directory: Directory path
            pattern: Glob pattern (default: *.csv)
            recursive: Search recursively
        """
        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)

        for file in files:
            if file.is_file():
                self._add_job(file)

    def process(
        self,
        processor_func: Callable[[Path], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """
        Process all jobs

        Args:
            processor_func: Function to process each file
            progress_callback: Optional callback for progress updates

        Returns:
            BatchResult with processing results
        """
        start_time = datetime.now()
        total = len(self.jobs)
        completed_count = 0
        failed_count = 0
        skipped_count = 0

        logger.info(f"Starting batch processing of {total} jobs")

        for i, job in enumerate(self.jobs):
            # Skip if already processed
            if self.skip_existing and job.status == JobStatus.COMPLETED:
                job.status = JobStatus.SKIPPED
                skipped_count += 1
                continue

            # Process job
            job.mark_running()

            try:
                logger.info(f"Processing {job.file_path} ({i+1}/{total})")
                result = processor_func(job.file_path)
                job.mark_completed(result)
                completed_count += 1

                logger.info(f"Completed {job.file_path}")

            except Exception as e:
                logger.error(f"Failed {job.file_path}: {e}")
                job.mark_failed(str(e))
                failed_count += 1

                if self.stop_on_error:
                    logger.error("Stopping batch processing due to error")
                    break

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total)

        # Calculate statistics
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        completed_jobs = [j for j in self.jobs if j.status == JobStatus.COMPLETED]
        durations: list[float] = [d for j in completed_jobs if (d := j.duration()) is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return BatchResult(
            total_jobs=total,
            completed=completed_count,
            failed=failed_count,
            skipped=skipped_count,
            total_duration=total_duration,
            avg_duration=avg_duration,
            jobs=self.jobs,
        )

    def process_parallel(
        self,
        processor_func: Callable[[Path], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """
        Process jobs in parallel

        Args:
            processor_func: Function to process each file
            progress_callback: Optional callback for progress updates

        Returns:
            BatchResult with processing results
        """
        import concurrent.futures

        start_time = datetime.now()
        total = len(self.jobs)
        completed_count = 0
        failed_count = 0

        logger.info(
            f"Starting parallel batch processing of {total} jobs with {self.max_workers} workers"
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(self._process_job, job, processor_func): job for job in self.jobs
            }

            # Collect results
            for i, future in enumerate(concurrent.futures.as_completed(future_to_job)):
                job = future_to_job[future]

                try:
                    future.result()  # This will raise if job failed
                    if job.status == JobStatus.COMPLETED:
                        completed_count += 1
                    elif job.status == JobStatus.FAILED:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Unexpected error processing {job.file_path}: {e}")
                    job.mark_failed(str(e))
                    failed_count += 1

                # Progress callback
                if progress_callback:
                    progress_callback(i + 1, total)

        # Calculate statistics
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        completed_jobs = [j for j in self.jobs if j.status == JobStatus.COMPLETED]
        durations: list[float] = [d for j in completed_jobs if (d := j.duration()) is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return BatchResult(
            total_jobs=total,
            completed=completed_count,
            failed=failed_count,
            skipped=0,
            total_duration=total_duration,
            avg_duration=avg_duration,
            jobs=self.jobs,
        )

    def _add_job(self, file_path: Path) -> None:
        """Add a job to the batch"""
        job_id = f"job_{len(self.jobs) + 1}"
        job = BatchJob(job_id=job_id, file_path=file_path)
        self.jobs.append(job)

    def _process_job(self, job: BatchJob, processor_func: Callable) -> None:
        """Process a single job"""
        job.mark_running()

        try:
            result = processor_func(job.file_path)
            job.mark_completed(result)
        except Exception as e:
            job.mark_failed(str(e))
            raise

    def get_statistics(self) -> Dict:
        """Get current processing statistics"""
        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = sum(1 for job in self.jobs if job.status == status)

        return {
            "total_jobs": len(self.jobs),
            "status_counts": status_counts,
            "completion_rate": (
                status_counts[JobStatus.COMPLETED.value] / len(self.jobs) * 100 if self.jobs else 0
            ),
        }

    def reset(self) -> None:
        """Reset all jobs to pending"""
        for job in self.jobs:
            if job.status != JobStatus.COMPLETED or not self.skip_existing:
                job.status = JobStatus.PENDING
                job.started_at = None
                job.completed_at = None
                job.error = None
                job.result = None
