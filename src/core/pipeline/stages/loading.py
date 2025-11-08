"""
Loading stages

데이터 저장을 위한 처리 단계들.
"""

import json
from pathlib import Path
from typing import Any, Optional

from ..base import ProcessingStage, PipelineContext


class FileLoadingStage(ProcessingStage):
    """
    파일 저장 단계

    데이터를 파일에 저장합니다.
    """

    def __init__(
        self,
        file_path: Path,
        encoding: str = "utf-8",
        mode: str = "w",
        name: str = "FileLoading",
    ):
        """
        Args:
            file_path: 저장할 파일 경로
            encoding: 파일 인코딩
            mode: 쓰기 모드 ('w', 'a')
            name: 단계 이름
        """
        super().__init__(name)
        self.file_path = file_path
        self.encoding = encoding
        self.mode = mode

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        파일 저장

        Args:
            data: 저장할 데이터 (문자열로 변환 가능해야 함)
            context: 컨텍스트

        Returns:
            Any: 입력 데이터 (통과)
        """
        # 디렉토리 생성
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # 데이터를 문자열로 변환
        if isinstance(data, (dict, list)):
            content = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            content = str(data)

        # 파일 쓰기
        with open(self.file_path, self.mode, encoding=self.encoding) as f:
            f.write(content)

        # 메타데이터
        context.metadata[f"{self.name}_file_path"] = str(self.file_path)
        context.metadata[f"{self.name}_bytes_written"] = len(content.encode(self.encoding))

        return data


class JSONLoadingStage(ProcessingStage):
    """
    JSON 저장 단계

    데이터를 JSON 파일로 저장합니다.
    """

    def __init__(
        self,
        file_path: Path,
        indent: int = 2,
        ensure_ascii: bool = False,
        name: str = "JSONLoading",
    ):
        """
        Args:
            file_path: 저장할 JSON 파일 경로
            indent: JSON 들여쓰기
            ensure_ascii: ASCII 강제 여부
            name: 단계 이름
        """
        super().__init__(name)
        self.file_path = file_path
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        JSON 저장

        Args:
            data: 저장할 데이터
            context: 컨텍스트

        Returns:
            Any: 입력 데이터 (통과)
        """
        # 디렉토리 생성
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON 저장
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=self.indent, ensure_ascii=self.ensure_ascii)

        # 메타데이터
        context.metadata[f"{self.name}_file_path"] = str(self.file_path)
        context.metadata[f"{self.name}_file_size"] = self.file_path.stat().st_size

        return data


class DatabaseLoadingStage(ProcessingStage):
    """
    데이터베이스 저장 단계

    데이터를 데이터베이스에 저장합니다.
    """

    def __init__(
        self,
        repository: Optional[Any] = None,
        batch_size: int = 100,
        name: str = "DatabaseLoading",
    ):
        """
        Args:
            repository: 리포지토리 인스턴스
            batch_size: 배치 저장 크기
            name: 단계 이름
        """
        super().__init__(name)
        self.repository = repository
        self.batch_size = batch_size

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        DB 저장

        Args:
            data: 저장할 데이터 (단일 항목 또는 리스트)
            context: 컨텍스트

        Returns:
            Any: 입력 데이터 (통과)
        """
        if not self.repository:
            raise ValueError("Repository not provided")

        # 리스트 확인
        items = data if isinstance(data, list) else [data]

        # 배치 저장
        saved_count = 0
        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            await self.repository.save_batch(batch)
            saved_count += len(batch)

        # 메타데이터
        context.metadata[f"{self.name}_saved_count"] = saved_count

        return data


class CacheLoadingStage(ProcessingStage):
    """
    캐시 저장 단계

    데이터를 캐시에 저장합니다.
    """

    def __init__(
        self,
        cache_key: str,
        cache_client: Optional[Any] = None,
        ttl: Optional[int] = None,
        name: str = "CacheLoading",
    ):
        """
        Args:
            cache_key: 캐시 키
            cache_client: 캐시 클라이언트 (Redis 등)
            ttl: TTL (초)
            name: 단계 이름
        """
        super().__init__(name)
        self.cache_key = cache_key
        self.cache_client = cache_client
        self.ttl = ttl

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        캐시 저장

        Args:
            data: 저장할 데이터
            context: 컨텍스트

        Returns:
            Any: 입력 데이터 (통과)
        """
        if not self.cache_client:
            raise ValueError("Cache client not provided")

        # JSON 직렬화
        serialized = json.dumps(data, ensure_ascii=False)

        # 캐시 저장
        if self.ttl:
            await self.cache_client.setex(self.cache_key, self.ttl, serialized)
        else:
            await self.cache_client.set(self.cache_key, serialized)

        # 메타데이터
        context.metadata[f"{self.name}_cache_key"] = self.cache_key
        context.metadata[f"{self.name}_ttl"] = self.ttl

        return data
