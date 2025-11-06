"""
시뮬레이션 결과 파서 기본 인터페이스

모든 파서가 구현해야 하는 기본 인터페이스.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..models import SimulationResult


class BaseParser(ABC):
    """
    시뮬레이션 결과 파서 기본 클래스

    모든 파서는 이 클래스를 상속하여 구현.
    """

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        파일 파싱 가능 여부 확인

        Args:
            file_path: 파일 경로

        Returns:
            파싱 가능 여부
        """
        pass

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        **options
    ) -> SimulationResult:
        """
        파일 파싱

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
    def get_supported_extensions(self) -> List[str]:
        """
        지원 파일 확장자 목록

        Returns:
            확장자 리스트 (예: [".vtk", ".vtu"])
        """
        pass

    def validate_file(self, file_path: Path) -> None:
        """
        파일 검증

        Args:
            file_path: 파일 경로

        Raises:
            FileNotFoundError: 파일 없음
            ValueError: 지원하지 않는 파일
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        extension = file_path.suffix.lower()
        supported = self.get_supported_extensions()

        if extension not in supported:
            raise ValueError(
                f"Unsupported file extension: {extension}. "
                f"Supported: {', '.join(supported)}"
            )


class ParserRegistry:
    """
    파서 레지스트리

    파일 타입에 따라 적절한 파서 자동 선택.
    """

    def __init__(self):
        self._parsers: List[BaseParser] = []

    def register(self, parser: BaseParser) -> None:
        """파서 등록"""
        self._parsers.append(parser)

    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """
        파일에 적합한 파서 찾기

        Args:
            file_path: 파일 경로

        Returns:
            적합한 파서 또는 None
        """
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def parse(self, file_path: Path, **options) -> SimulationResult:
        """
        파일 자동 파싱

        Args:
            file_path: 파일 경로
            **options: 파서 옵션

        Returns:
            SimulationResult

        Raises:
            ValueError: 적합한 파서를 찾을 수 없음
        """
        parser = self.get_parser(file_path)

        if not parser:
            raise ValueError(
                f"No suitable parser found for file: {file_path}"
            )

        return parser.parse(file_path, **options)

    def list_parsers(self) -> List[BaseParser]:
        """등록된 파서 목록"""
        return self._parsers.copy()
