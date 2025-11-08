"""
스트리밍 파서 기본 인터페이스

대용량 파일을 메모리 효율적으로 처리하기 위한 스트리밍 파서.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator, Callable, Generic, Iterator, Optional, TypeVar

from ..models import SimulationResult

T = TypeVar("T")  # 청크 데이터 타입


class ProgressCallback:
    """
    진행률 콜백

    파싱 진행 상황을 추적하고 보고합니다.
    """

    def __init__(
        self,
        total_bytes: int,
        callback: Optional[Callable[[int, int, float], None]] = None,
    ):
        """
        Args:
            total_bytes: 전체 파일 크기 (바이트)
            callback: 진행률 콜백 함수 (processed_bytes, total_bytes, percentage)
        """
        self.total_bytes = total_bytes
        self.processed_bytes = 0
        self.callback = callback

    def update(self, bytes_processed: int) -> None:
        """
        진행률 업데이트

        Args:
            bytes_processed: 처리된 바이트 수
        """
        self.processed_bytes += bytes_processed
        if self.callback:
            percentage = (self.processed_bytes / self.total_bytes) * 100
            self.callback(self.processed_bytes, self.total_bytes, percentage)

    @property
    def percentage(self) -> float:
        """현재 진행률 (0-100)"""
        if self.total_bytes == 0:
            return 100.0
        return (self.processed_bytes / self.total_bytes) * 100


class StreamingParser(ABC, Generic[T]):
    """
    스트리밍 파서 기본 클래스

    대용량 파일을 청크 단위로 읽어서 메모리 사용량을 최소화합니다.
    """

    def __init__(
        self,
        chunk_size: int = 1024 * 1024,  # 1MB 기본 청크 크기
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ):
        """
        Args:
            chunk_size: 청크 크기 (바이트)
            progress_callback: 진행률 콜백 함수
        """
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback

    @abstractmethod
    def parse_stream(
        self,
        file_path: Path,
        **options,
    ) -> SimulationResult:
        """
        스트리밍 방식으로 파일 파싱

        Args:
            file_path: 파일 경로
            **options: 파서별 옵션

        Returns:
            SimulationResult

        Raises:
            ValueError: 파싱 실패
            FileNotFoundError: 파일 없음
        """
        pass

    @abstractmethod
    def read_chunks(self, file_path: Path, **options) -> Iterator[T]:
        """
        청크 단위로 파일 읽기

        Args:
            file_path: 파일 경로
            **options: 파서별 옵션

        Yields:
            청크 데이터

        Raises:
            ValueError: 읽기 실패
            FileNotFoundError: 파일 없음
        """
        pass

    def _create_progress_tracker(self, file_path: Path) -> ProgressCallback:
        """
        진행률 추적기 생성

        Args:
            file_path: 파일 경로

        Returns:
            ProgressCallback 인스턴스
        """
        total_bytes = file_path.stat().st_size
        return ProgressCallback(total_bytes, self.progress_callback)


class AsyncStreamingParser(ABC, Generic[T]):
    """
    비동기 스트리밍 파서

    비동기 I/O를 사용하여 대용량 파일을 처리합니다.
    """

    def __init__(
        self,
        chunk_size: int = 1024 * 1024,  # 1MB 기본 청크 크기
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ):
        """
        Args:
            chunk_size: 청크 크기 (바이트)
            progress_callback: 진행률 콜백 함수
        """
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback

    @abstractmethod
    async def parse_stream(
        self,
        file_path: Path,
        **options,
    ) -> SimulationResult:
        """
        비동기 스트리밍 방식으로 파일 파싱

        Args:
            file_path: 파일 경로
            **options: 파서별 옵션

        Returns:
            SimulationResult
        """
        pass

    @abstractmethod
    async def read_chunks(self, file_path: Path, **options) -> AsyncIterator[T]:
        """
        청크 단위로 비동기 파일 읽기

        Args:
            file_path: 파일 경로
            **options: 파서별 옵션

        Yields:
            청크 데이터
        """
        pass

    def _create_progress_tracker(self, file_path: Path) -> ProgressCallback:
        """
        진행률 추적기 생성

        Args:
            file_path: 파일 경로

        Returns:
            ProgressCallback 인스턴스
        """
        total_bytes = file_path.stat().st_size
        return ProgressCallback(total_bytes, self.progress_callback)
