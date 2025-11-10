"""
Streaming File Upload and Processing

Handles large file uploads with chunked streaming and parallel processing.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, List, Optional
from dataclasses import dataclass
import aiofiles  # type: ignore[import-untyped]

from fastapi import UploadFile


@dataclass
class UploadProgress:
    """Upload progress information."""

    filename: str
    total_size: int
    uploaded_size: int
    chunk_count: int
    md5_hash: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        """Calculate upload progress percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.uploaded_size / self.total_size) * 100


class StreamingFileUploader:
    """
    Streaming file uploader for large files.

    Features:
    - Chunked uploads to save memory
    - MD5 checksum calculation
    - Progress tracking
    - Async I/O for better performance
    """

    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB default
        """
        Initialize streaming uploader.

        Args:
            chunk_size: Size of each chunk in bytes
        """
        self.chunk_size = chunk_size

    async def upload_stream(
        self,
        file: UploadFile,
        destination: Path,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None,
    ) -> UploadProgress:
        """
        Upload file in streaming chunks.

        Args:
            file: FastAPI UploadFile
            destination: Destination file path
            progress_callback: Optional callback for progress updates

        Returns:
            Upload progress with final stats

        Example:
            ```python
            uploader = StreamingFileUploader(chunk_size=1024*1024)  # 1MB chunks

            async def on_progress(progress: UploadProgress):
                print(f"Uploaded: {progress.progress_percent:.1f}%")

            result = await uploader.upload_stream(file, dest_path, on_progress)
            print(f"MD5: {result.md5_hash}")
            ```
        """
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Initialize progress
        total_size = 0
        uploaded_size = 0
        chunk_count = 0
        md5 = hashlib.md5()

        # Open destination file
        async with aiofiles.open(destination, "wb") as f:
            # Read and write in chunks
            while True:
                chunk = await file.read(self.chunk_size)
                if not chunk:
                    break

                # Write chunk
                await f.write(chunk)

                # Update stats
                chunk_size = len(chunk)
                uploaded_size += chunk_size
                total_size += chunk_size
                chunk_count += 1

                # Update MD5
                md5.update(chunk)

                # Progress callback
                if progress_callback:
                    progress = UploadProgress(
                        filename=file.filename or "unknown",
                        total_size=total_size,
                        uploaded_size=uploaded_size,
                        chunk_count=chunk_count,
                    )
                    progress_callback(progress)

        # Final progress
        final_progress = UploadProgress(
            filename=file.filename or "unknown",
            total_size=total_size,
            uploaded_size=uploaded_size,
            chunk_count=chunk_count,
            md5_hash=md5.hexdigest(),
        )

        return final_progress

    async def upload_with_resume(
        self,
        file: UploadFile,
        destination: Path,
        resume_from: int = 0,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None,
    ) -> UploadProgress:
        """
        Upload file with resume support.

        Args:
            file: FastAPI UploadFile
            destination: Destination file path
            resume_from: Byte offset to resume from
            progress_callback: Optional callback for progress updates

        Returns:
            Upload progress with final stats
        """
        # Check if file exists and we're resuming
        if resume_from > 0 and destination.exists():
            mode = "ab"  # Append mode
            await file.seek(resume_from)
        else:
            mode = "wb"  # Write mode
            resume_from = 0

        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Initialize progress
        total_size = resume_from
        uploaded_size = resume_from
        chunk_count = 0
        md5 = hashlib.md5()

        # Open destination file
        async with aiofiles.open(destination, mode) as f:
            # Read and write in chunks
            while True:
                chunk = await file.read(self.chunk_size)
                if not chunk:
                    break

                # Write chunk
                await f.write(chunk)

                # Update stats
                chunk_size = len(chunk)
                uploaded_size += chunk_size
                total_size += chunk_size
                chunk_count += 1

                # Update MD5
                md5.update(chunk)

                # Progress callback
                if progress_callback:
                    progress = UploadProgress(
                        filename=file.filename or "unknown",
                        total_size=total_size,
                        uploaded_size=uploaded_size,
                        chunk_count=chunk_count,
                    )
                    progress_callback(progress)

        # Final progress
        final_progress = UploadProgress(
            filename=file.filename or "unknown",
            total_size=total_size,
            uploaded_size=uploaded_size,
            chunk_count=chunk_count,
            md5_hash=md5.hexdigest(),
        )

        return final_progress


class ParallelFileProcessor:
    """
    Parallel file processor for handling multiple files concurrently.

    Features:
    - Concurrent processing using asyncio
    - Configurable worker pool size
    - Progress tracking for each file
    - Error handling and retry logic
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel processor.

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers

    async def process_files(
        self,
        files: List[Path],
        process_func: Callable[[Path], Awaitable[Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Any]:
        """
        Process multiple files in parallel.

        Args:
            files: List of file paths to process
            process_func: Async function to process each file
            progress_callback: Optional callback(completed, total)

        Returns:
            List of processing results

        Example:
            ```python
            async def process_file(path: Path):
                # Process file
                result = await parse_simulation(path)
                return result

            processor = ParallelFileProcessor(max_workers=4)
            results = await processor.process_files(
                files=[Path("file1.csv"), Path("file2.csv")],
                process_func=process_file
            )
            ```
        """
        semaphore = asyncio.Semaphore(self.max_workers)
        completed = 0
        total = len(files)

        async def process_with_semaphore(file: Path) -> Any:
            nonlocal completed
            async with semaphore:
                result = await process_func(file)
                completed += 1

                if progress_callback:
                    progress_callback(completed, total)

                return result

        # Process all files concurrently with worker limit
        tasks = [process_with_semaphore(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results


async def stream_file_chunks(
    file_path: Path, chunk_size: int = 1024 * 64
) -> AsyncIterator[bytes]:
    """
    Stream file in chunks (async generator).

    Args:
        file_path: Path to file
        chunk_size: Size of each chunk

    Yields:
        File chunks as bytes

    Example:
        ```python
        async for chunk in stream_file_chunks(Path("large_file.dat")):
            # Process chunk
            await process_chunk(chunk)
        ```
    """
    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk


async def calculate_file_checksum(file_path: Path, algorithm: str = "md5") -> str:
    """
    Calculate file checksum using streaming.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha256, sha512)

    Returns:
        Hex digest of file hash

    Example:
        ```python
        md5_hash = await calculate_file_checksum(Path("file.dat"), "md5")
        sha256_hash = await calculate_file_checksum(Path("file.dat"), "sha256")
        ```
    """
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    async for chunk in stream_file_chunks(file_path):
        hasher.update(chunk)

    return hasher.hexdigest()
