"""
Local filesystem storage adapter
"""

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncIterator, BinaryIO, Optional
import aiofiles
import aiofiles.os

from .base import (
    StorageBackend,
    FileMetadata,
    UploadResult,
    PresignedUrl,
)


class LocalStorageBackend(StorageBackend):
    """
    로컬 파일 시스템 storage adapter

    개발 및 테스트용으로 사용하거나, 로컬 파일 시스템을 사용하는 경우 사용합니다.
    """

    def __init__(self, base_path: str = "./data/storage"):
        """
        Args:
            base_path: 파일을 저장할 기본 경로
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get full path from key"""
        return self.base_path / key

    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadResult:
        """파일 업로드"""
        full_path = self._get_full_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        async with aiofiles.open(full_path, "wb") as f:
            content = file.read()
            await f.write(content)
            size = len(content)

        # Save metadata if provided
        if metadata:
            metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
            async with aiofiles.open(metadata_path, "w") as f:
                import json

                await f.write(json.dumps(metadata))

        return UploadResult(
            key=key,
            size=size,
            url=str(full_path),
        )

    async def upload_multipart(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        part_size: int = 5 * 1024 * 1024,
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadResult:
        """
        멀티파트 업로드

        로컬 파일 시스템에서는 일반 업로드와 동일하게 처리하지만,
        대용량 파일을 청크 단위로 읽어서 메모리 효율을 높입니다.
        """
        full_path = self._get_full_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        async with aiofiles.open(full_path, "wb") as f:
            while True:
                chunk = file.read(part_size)
                if not chunk:
                    break
                await f.write(chunk)
                total_size += len(chunk)

        # Save metadata if provided
        if metadata:
            metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
            async with aiofiles.open(metadata_path, "w") as f:
                import json

                await f.write(json.dumps(metadata))

        return UploadResult(
            key=key,
            size=total_size,
            url=str(full_path),
        )

    async def download(self, key: str) -> bytes:
        """파일 다운로드"""
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()  # type: ignore[no-any-return]

    async def download_to_file(self, key: str, destination: Path) -> None:
        """파일을 로컬 파일로 다운로드"""
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        await aiofiles.os.link(str(full_path), str(destination))

    async def download_stream(self, key: str, chunk_size: int = 8192) -> AsyncIterator[bytes]:  # type: ignore[override,misc]
        """파일을 스트림으로 다운로드"""
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        async with aiofiles.open(full_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    async def delete(self, key: str) -> None:
        """파일 삭제"""
        full_path = self._get_full_path(key)
        if full_path.exists():
            await aiofiles.os.remove(str(full_path))

        # Delete metadata if exists
        metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
        if metadata_path.exists():
            await aiofiles.os.remove(str(metadata_path))

    async def delete_many(self, keys: list[str]) -> None:
        """여러 파일 삭제"""
        for key in keys:
            await self.delete(key)

    async def exists(self, key: str) -> bool:
        """파일 존재 여부 확인"""
        full_path = self._get_full_path(key)
        return full_path.exists()

    async def get_metadata(self, key: str) -> FileMetadata:
        """파일 메타데이터 조회"""
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        stat = full_path.stat()

        # Load custom metadata if exists
        custom_metadata = None
        metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
        if metadata_path.exists():
            async with aiofiles.open(metadata_path, "r") as f:
                import json

                custom_metadata = json.loads(await f.read())

        # Guess content type
        import mimetypes

        content_type, _ = mimetypes.guess_type(str(full_path))
        if content_type is None:
            content_type = "application/octet-stream"

        return FileMetadata(
            key=key,
            size=stat.st_size,
            content_type=content_type,
            last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            custom_metadata=custom_metadata,
        )

    async def list_files(self, prefix: str = "", max_results: int = 1000) -> list[FileMetadata]:
        """파일 목록 조회"""
        search_path = self.base_path / prefix if prefix else self.base_path

        files = []
        for path in search_path.rglob("*"):
            if path.is_file() and not path.suffix == ".meta":
                key = str(path.relative_to(self.base_path))
                try:
                    metadata = await self.get_metadata(key)
                    files.append(metadata)
                    if len(files) >= max_results:
                        break
                except Exception:
                    continue

        return files

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> PresignedUrl:
        """
        Presigned URL 생성

        로컬 파일 시스템에서는 file:// URL을 반환합니다.
        """
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        return PresignedUrl(
            url=f"file://{full_path.absolute()}",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            method=method,
        )

    async def copy(self, source_key: str, destination_key: str) -> None:
        """파일 복사"""
        source_path = self._get_full_path(source_key)
        dest_path = self._get_full_path(destination_key)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_key}")

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)

        # Copy metadata if exists
        source_meta = source_path.with_suffix(source_path.suffix + ".meta")
        if source_meta.exists():
            dest_meta = dest_path.with_suffix(dest_path.suffix + ".meta")
            shutil.copy2(source_meta, dest_meta)

    async def move(self, source_key: str, destination_key: str) -> None:
        """파일 이동"""
        await self.copy(source_key, destination_key)
        await self.delete(source_key)

    async def get_size(self, key: str) -> int:
        """파일 크기 조회"""
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        return full_path.stat().st_size

    async def cleanup_old_files(self, prefix: str, days: int) -> int:
        """오래된 파일 정리"""
        search_path = self.base_path / prefix if prefix else self.base_path
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        deleted_count = 0
        for path in search_path.rglob("*"):
            if path.is_file() and not path.suffix == ".meta":
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff_time:
                    key = str(path.relative_to(self.base_path))
                    await self.delete(key)
                    deleted_count += 1

        return deleted_count
