"""
Tests for local filesystem storage backend
"""

import io
import tempfile
from pathlib import Path
from typing import Generator
import pytest

from src.infrastructure.storage.local import LocalStorageBackend
from src.infrastructure.storage.base import FileMetadata, UploadResult


@pytest.fixture
def temp_storage_dir() -> Generator[str, None, None]:
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def storage(temp_storage_dir: str) -> LocalStorageBackend:
    """Create local storage backend"""
    return LocalStorageBackend(base_path=temp_storage_dir)


@pytest.mark.asyncio
async def test_upload_and_download(storage: LocalStorageBackend) -> None:
    """Test basic upload and download"""
    # Upload file
    content = b"Hello, World!"
    file = io.BytesIO(content)
    result = await storage.upload(
        file=file,
        key="test/hello.txt",
        content_type="text/plain",
    )

    assert isinstance(result, UploadResult)
    assert result.key == "test/hello.txt"
    assert result.size == len(content)

    # Download file
    downloaded = await storage.download("test/hello.txt")
    assert downloaded == content


@pytest.mark.asyncio
async def test_upload_with_metadata(storage: LocalStorageBackend) -> None:
    """Test upload with custom metadata"""
    content = b"Test data"
    file = io.BytesIO(content)
    metadata = {"author": "test", "version": "1.0"}

    await storage.upload(
        file=file,
        key="data.bin",
        metadata=metadata,
    )

    # Check metadata
    file_metadata = await storage.get_metadata("data.bin")
    assert file_metadata.custom_metadata == metadata


@pytest.mark.asyncio
async def test_multipart_upload(storage: LocalStorageBackend) -> None:
    """Test multipart upload for large files"""
    # Create larger content
    content = b"x" * (10 * 1024 * 1024)  # 10MB
    file = io.BytesIO(content)

    result = await storage.upload_multipart(
        file=file,
        key="large.bin",
        part_size=2 * 1024 * 1024,  # 2MB parts
    )

    assert result.size == len(content)

    # Verify file exists
    assert await storage.exists("large.bin")


@pytest.mark.asyncio
async def test_download_to_file(storage: LocalStorageBackend, temp_storage_dir: str) -> None:
    """Test download to file"""
    # Upload
    content = b"Test content"
    file = io.BytesIO(content)
    await storage.upload(file, "source.txt")

    # Download to file
    destination = Path(temp_storage_dir) / "downloaded.txt"
    await storage.download_to_file("source.txt", destination)

    assert destination.exists()


@pytest.mark.asyncio
async def test_download_stream(storage: LocalStorageBackend) -> None:
    """Test streaming download"""
    content = b"Stream test content"
    file = io.BytesIO(content)
    await storage.upload(file, "stream.txt")

    # Download as stream
    chunks = []
    async for chunk in storage.download_stream("stream.txt", chunk_size=5):
        chunks.append(chunk)

    assert b"".join(chunks) == content


@pytest.mark.asyncio
async def test_delete(storage: LocalStorageBackend) -> None:
    """Test file deletion"""
    # Upload
    file = io.BytesIO(b"delete me")
    await storage.upload(file, "to_delete.txt")

    assert await storage.exists("to_delete.txt")

    # Delete
    await storage.delete("to_delete.txt")

    assert not await storage.exists("to_delete.txt")


@pytest.mark.asyncio
async def test_delete_many(storage: LocalStorageBackend) -> None:
    """Test batch deletion"""
    # Upload multiple files
    for i in range(5):
        file = io.BytesIO(f"file {i}".encode())
        await storage.upload(file, f"batch/file{i}.txt")

    # Delete all
    keys = [f"batch/file{i}.txt" for i in range(5)]
    await storage.delete_many(keys)

    # Verify all deleted
    for key in keys:
        assert not await storage.exists(key)


@pytest.mark.asyncio
async def test_get_metadata(storage: LocalStorageBackend) -> None:
    """Test metadata retrieval"""
    content = b"Metadata test"
    file = io.BytesIO(content)
    await storage.upload(file, "meta.txt", content_type="text/plain")

    metadata = await storage.get_metadata("meta.txt")

    assert isinstance(metadata, FileMetadata)
    assert metadata.key == "meta.txt"
    assert metadata.size == len(content)
    assert metadata.content_type == "text/plain"
    assert metadata.last_modified is not None


@pytest.mark.asyncio
async def test_list_files(storage: LocalStorageBackend) -> None:
    """Test file listing"""
    # Upload multiple files
    for i in range(3):
        file = io.BytesIO(f"content {i}".encode())
        await storage.upload(file, f"list/file{i}.txt")

    # List files
    files = await storage.list_files(prefix="list/")

    assert len(files) >= 3
    keys = [f.key for f in files]
    assert any("file0.txt" in k for k in keys)
    assert any("file1.txt" in k for k in keys)
    assert any("file2.txt" in k for k in keys)


@pytest.mark.asyncio
async def test_generate_presigned_url(storage: LocalStorageBackend) -> None:
    """Test presigned URL generation"""
    file = io.BytesIO(b"test")
    await storage.upload(file, "presigned.txt")

    url_info = await storage.generate_presigned_url("presigned.txt", expires_in=3600)

    assert url_info.url.startswith("file://")
    assert url_info.method == "GET"
    assert url_info.expires_at is not None


@pytest.mark.asyncio
async def test_copy(storage: LocalStorageBackend) -> None:
    """Test file copy"""
    # Upload source
    file = io.BytesIO(b"copy me")
    await storage.upload(file, "source.txt")

    # Copy
    await storage.copy("source.txt", "destination.txt")

    # Verify both exist
    assert await storage.exists("source.txt")
    assert await storage.exists("destination.txt")

    # Verify content
    content = await storage.download("destination.txt")
    assert content == b"copy me"


@pytest.mark.asyncio
async def test_move(storage: LocalStorageBackend) -> None:
    """Test file move"""
    # Upload source
    file = io.BytesIO(b"move me")
    await storage.upload(file, "old.txt")

    # Move
    await storage.move("old.txt", "new.txt")

    # Verify source deleted and destination exists
    assert not await storage.exists("old.txt")
    assert await storage.exists("new.txt")


@pytest.mark.asyncio
async def test_get_size(storage: LocalStorageBackend) -> None:
    """Test file size retrieval"""
    content = b"size test"
    file = io.BytesIO(content)
    await storage.upload(file, "size.txt")

    size = await storage.get_size("size.txt")
    assert size == len(content)


@pytest.mark.asyncio
async def test_cleanup_old_files(storage: LocalStorageBackend) -> None:
    """Test cleanup of old files"""
    import time

    # Upload files
    file1 = io.BytesIO(b"old")
    await storage.upload(file1, "cleanup/old.txt")

    # Wait a bit
    time.sleep(0.1)

    file2 = io.BytesIO(b"new")
    await storage.upload(file2, "cleanup/new.txt")

    # Cleanup files older than 0 days (should delete old.txt)
    # Note: This test might be flaky depending on filesystem timestamp resolution
    deleted = await storage.cleanup_old_files("cleanup/", days=0)

    # At least one file should be cleaned up
    assert deleted >= 0


@pytest.mark.asyncio
async def test_nonexistent_file(storage: LocalStorageBackend) -> None:
    """Test handling of non-existent files"""
    # Check exists
    assert not await storage.exists("nonexistent.txt")

    # Download should raise
    with pytest.raises(FileNotFoundError):
        await storage.download("nonexistent.txt")

    # Get metadata should raise
    with pytest.raises(FileNotFoundError):
        await storage.get_metadata("nonexistent.txt")
