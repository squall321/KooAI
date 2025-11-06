"""
Base storage abstraction interfaces
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, AsyncIterator


@dataclass
class FileMetadata:
    """파일 메타데이터"""

    key: str  # Storage key/path
    size: int  # File size in bytes
    content_type: str  # MIME type
    etag: Optional[str] = None  # ETag (for S3, etc.)
    last_modified: Optional[datetime] = None
    custom_metadata: Optional[dict[str, str]] = None


@dataclass
class UploadResult:
    """파일 업로드 결과"""

    key: str
    size: int
    etag: Optional[str] = None
    url: Optional[str] = None  # Public URL if available


@dataclass
class PresignedUrl:
    """Presigned URL 정보"""

    url: str
    expires_at: datetime
    method: str = "GET"  # HTTP method (GET, PUT, etc.)


class StorageBackend(ABC):
    """
    Storage backend 추상 인터페이스

    모든 storage 구현체가 따라야 하는 인터페이스를 정의합니다.
    """

    @abstractmethod
    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadResult:
        """
        파일 업로드

        Args:
            file: 업로드할 파일 객체
            key: Storage key (경로)
            content_type: MIME type
            metadata: 커스텀 메타데이터

        Returns:
            UploadResult
        """
        pass

    @abstractmethod
    async def upload_multipart(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        part_size: int = 5 * 1024 * 1024,  # 5MB default
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadResult:
        """
        멀티파트 업로드 (대용량 파일)

        Args:
            file: 업로드할 파일 객체
            key: Storage key
            content_type: MIME type
            part_size: 파트 크기 (bytes)
            metadata: 커스텀 메타데이터

        Returns:
            UploadResult
        """
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """
        파일 다운로드

        Args:
            key: Storage key

        Returns:
            파일 내용 (bytes)
        """
        pass

    @abstractmethod
    async def download_to_file(self, key: str, destination: Path) -> None:
        """
        파일을 로컬 파일로 다운로드

        Args:
            key: Storage key
            destination: 저장할 로컬 파일 경로
        """
        pass

    @abstractmethod
    async def download_stream(self, key: str, chunk_size: int = 8192) -> AsyncIterator[bytes]:
        """
        파일을 스트림으로 다운로드

        Args:
            key: Storage key
            chunk_size: 청크 크기

        Yields:
            파일 청크 (bytes)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        파일 삭제

        Args:
            key: Storage key
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: list[str]) -> None:
        """
        여러 파일 삭제

        Args:
            keys: Storage keys 리스트
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        파일 존재 여부 확인

        Args:
            key: Storage key

        Returns:
            존재 여부
        """
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> FileMetadata:
        """
        파일 메타데이터 조회

        Args:
            key: Storage key

        Returns:
            FileMetadata
        """
        pass

    @abstractmethod
    async def list_files(
        self, prefix: str = "", max_results: int = 1000
    ) -> list[FileMetadata]:
        """
        파일 목록 조회

        Args:
            prefix: Key prefix (디렉토리 경로)
            max_results: 최대 결과 수

        Returns:
            FileMetadata 리스트
        """
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> PresignedUrl:
        """
        Presigned URL 생성

        Args:
            key: Storage key
            expires_in: 만료 시간 (초)
            method: HTTP method

        Returns:
            PresignedUrl
        """
        pass

    @abstractmethod
    async def copy(self, source_key: str, destination_key: str) -> None:
        """
        파일 복사

        Args:
            source_key: 원본 key
            destination_key: 대상 key
        """
        pass

    @abstractmethod
    async def move(self, source_key: str, destination_key: str) -> None:
        """
        파일 이동

        Args:
            source_key: 원본 key
            destination_key: 대상 key
        """
        pass

    @abstractmethod
    async def get_size(self, key: str) -> int:
        """
        파일 크기 조회

        Args:
            key: Storage key

        Returns:
            파일 크기 (bytes)
        """
        pass

    @abstractmethod
    async def cleanup_old_files(self, prefix: str, days: int) -> int:
        """
        오래된 파일 정리

        Args:
            prefix: Key prefix
            days: 보관 기간 (일)

        Returns:
            삭제된 파일 수
        """
        pass
