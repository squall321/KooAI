"""
Tests for Streaming Parser Base Classes
"""

import pytest
from pathlib import Path
from typing import Iterator, AsyncIterator

from src.core.simulation.parsers.streaming_base import (
    ProgressCallback,
    StreamingParser,
    AsyncStreamingParser,
)
from src.core.simulation.models import SimulationResult


class TestProgressCallback:
    """Test ProgressCallback functionality."""

    def test_init(self):
        """Test ProgressCallback initialization."""
        callback = ProgressCallback(total_bytes=1000)

        assert callback.total_bytes == 1000
        assert callback.processed_bytes == 0
        assert callback.callback is None

    def test_init_with_callback(self):
        """Test ProgressCallback with callback function."""
        called_args = []

        def progress_fn(processed, total, percent):
            called_args.append((processed, total, percent))

        callback = ProgressCallback(total_bytes=1000, callback=progress_fn)

        assert callback.callback is not None

    def test_update(self):
        """Test progress update."""
        callback = ProgressCallback(total_bytes=1000)

        callback.update(100)
        assert callback.processed_bytes == 100

        callback.update(200)
        assert callback.processed_bytes == 300

    def test_update_with_callback(self):
        """Test progress update triggers callback."""
        called_args = []

        def progress_fn(processed, total, percent):
            called_args.append((processed, total, percent))

        callback = ProgressCallback(total_bytes=1000, callback=progress_fn)

        callback.update(250)

        assert len(called_args) == 1
        assert called_args[0] == (250, 1000, 25.0)

        callback.update(500)

        assert len(called_args) == 2
        assert called_args[1] == (750, 1000, 75.0)

    def test_percentage_property(self):
        """Test percentage calculation."""
        callback = ProgressCallback(total_bytes=1000)

        assert callback.percentage == 0.0

        callback.update(250)
        assert callback.percentage == 25.0

        callback.update(500)
        assert callback.percentage == 75.0

        callback.update(250)
        assert callback.percentage == 100.0

    def test_percentage_zero_total(self):
        """Test percentage with zero total bytes."""
        callback = ProgressCallback(total_bytes=0)

        assert callback.percentage == 100.0

    def test_update_no_callback(self):
        """Test update without callback doesn't raise error."""
        callback = ProgressCallback(total_bytes=1000)

        callback.update(500)  # Should not raise

        assert callback.processed_bytes == 500


class ConcreteStreamingParser(StreamingParser[str]):
    """Concrete implementation for testing."""

    def parse_stream(self, file_path: Path, **options) -> SimulationResult:
        """Dummy implementation."""
        raise NotImplementedError("Test implementation")

    def read_chunks(self, file_path: Path, **options) -> Iterator[str]:
        """Dummy implementation."""
        yield "chunk1"
        yield "chunk2"


class TestStreamingParser:
    """Test StreamingParser base class."""

    def test_init(self):
        """Test StreamingParser initialization."""
        parser = ConcreteStreamingParser()

        assert parser.chunk_size == 1024 * 1024  # 1MB default
        assert parser.progress_callback is None

    def test_init_with_custom_chunk_size(self):
        """Test initialization with custom chunk size."""
        parser = ConcreteStreamingParser(chunk_size=2048)

        assert parser.chunk_size == 2048

    def test_init_with_callback(self):
        """Test initialization with progress callback."""
        def progress_fn(processed, total, percent):
            pass

        parser = ConcreteStreamingParser(progress_callback=progress_fn)

        assert parser.progress_callback is progress_fn

    def test_create_progress_tracker(self, tmp_path):
        """Test progress tracker creation."""
        parser = ConcreteStreamingParser()

        # Create test file
        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"x" * 1000)

        tracker = parser._create_progress_tracker(test_file)

        assert tracker.total_bytes == 1000
        assert tracker.processed_bytes == 0

    def test_create_progress_tracker_with_callback(self, tmp_path):
        """Test progress tracker with callback."""
        called_args = []

        def progress_fn(processed, total, percent):
            called_args.append((processed, total, percent))

        parser = ConcreteStreamingParser(progress_callback=progress_fn)

        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"x" * 1000)

        tracker = parser._create_progress_tracker(test_file)

        assert tracker.callback is progress_fn


class ConcreteAsyncStreamingParser(AsyncStreamingParser[str]):
    """Concrete async implementation for testing."""

    async def parse_stream(self, file_path: Path, **options) -> SimulationResult:
        """Dummy implementation."""
        raise NotImplementedError("Test implementation")

    async def read_chunks(self, file_path: Path, **options) -> AsyncIterator[str]:
        """Dummy implementation."""
        yield "async_chunk1"
        yield "async_chunk2"


class TestAsyncStreamingParser:
    """Test AsyncStreamingParser base class."""

    def test_init(self):
        """Test AsyncStreamingParser initialization."""
        parser = ConcreteAsyncStreamingParser()

        assert parser.chunk_size == 1024 * 1024  # 1MB default
        assert parser.progress_callback is None

    def test_init_with_custom_chunk_size(self):
        """Test initialization with custom chunk size."""
        parser = ConcreteAsyncStreamingParser(chunk_size=4096)

        assert parser.chunk_size == 4096

    def test_init_with_callback(self):
        """Test initialization with progress callback."""
        def progress_fn(processed, total, percent):
            pass

        parser = ConcreteAsyncStreamingParser(progress_callback=progress_fn)

        assert parser.progress_callback is progress_fn

    def test_create_progress_tracker(self, tmp_path):
        """Test async progress tracker creation."""
        parser = ConcreteAsyncStreamingParser()

        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"x" * 2000)

        tracker = parser._create_progress_tracker(test_file)

        assert tracker.total_bytes == 2000
        assert tracker.processed_bytes == 0

    @pytest.mark.asyncio
    async def test_read_chunks_async(self):
        """Test async chunk reading."""
        parser = ConcreteAsyncStreamingParser()

        chunks = []
        async for chunk in parser.read_chunks(Path("dummy.dat")):
            chunks.append(chunk)

        assert chunks == ["async_chunk1", "async_chunk2"]
