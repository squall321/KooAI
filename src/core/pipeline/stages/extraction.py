"""
Extraction stages

데이터 추출을 위한 처리 단계들.
"""

import json
from pathlib import Path
from typing import Any, List, Optional

from ..base import ProcessingStage, PipelineContext


class FileExtractionStage(ProcessingStage):
    """
    파일 추출 단계

    파일에서 데이터를 읽어옵니다.
    """

    def __init__(
        self,
        file_path: Optional[Path] = None,
        encoding: str = "utf-8",
        name: str = "FileExtraction",
    ):
        """
        Args:
            file_path: 파일 경로 (None이면 data에서 경로 받음)
            encoding: 파일 인코딩
            name: 단계 이름
        """
        super().__init__(name)
        self.file_path = file_path
        self.encoding = encoding

    async def process(self, data: Any, context: PipelineContext) -> str:
        """
        파일 읽기

        Args:
            data: 파일 경로 (file_path가 None인 경우) 또는 무시됨
            context: 컨텍스트

        Returns:
            str: 파일 내용
        """
        # 경로 결정
        path = self.file_path if self.file_path else Path(data)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # 파일 읽기
        with open(path, "r", encoding=self.encoding) as f:
            content = f.read()

        # 메타데이터 저장
        context.metadata[f"{self.name}_file_path"] = str(path)
        context.metadata[f"{self.name}_file_size"] = path.stat().st_size

        return content


class JSONExtractionStage(ProcessingStage):
    """
    JSON 추출 단계

    JSON 파일 또는 문자열에서 데이터를 추출합니다.
    """

    def __init__(
        self,
        file_path: Optional[Path] = None,
        extract_path: Optional[str] = None,
        name: str = "JSONExtraction",
    ):
        """
        Args:
            file_path: JSON 파일 경로 (None이면 data가 JSON 문자열)
            extract_path: 추출할 경로 (예: "data.results") (None이면 전체)
            name: 단계 이름
        """
        super().__init__(name)
        self.file_path = file_path
        self.extract_path = extract_path

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        JSON 파싱

        Args:
            data: JSON 문자열 또는 파일 경로
            context: 컨텍스트

        Returns:
            Any: 파싱된 데이터
        """
        # JSON 로드
        if self.file_path:
            with open(self.file_path, "r") as f:
                json_data = json.load(f)
        elif isinstance(data, str):
            json_data = json.loads(data)
        else:
            json_data = data

        # 경로 추출
        if self.extract_path:
            keys = self.extract_path.split(".")
            for key in keys:
                json_data = json_data[key]

        return json_data


class DatabaseExtractionStage(ProcessingStage):
    """
    데이터베이스 추출 단계

    데이터베이스에서 데이터를 조회합니다.
    """

    def __init__(
        self,
        query: str,
        repository: Optional[Any] = None,
        name: str = "DatabaseExtraction",
    ):
        """
        Args:
            query: SQL 쿼리 또는 조회 조건
            repository: 리포지토리 인스턴스
            name: 단계 이름
        """
        super().__init__(name)
        self.query = query
        self.repository = repository

    async def process(self, data: Any, context: PipelineContext) -> List[Any]:
        """
        DB 조회

        Args:
            data: 쿼리 파라미터 (dict)
            context: 컨텍스트

        Returns:
            List[Any]: 조회 결과
        """
        if not self.repository:
            raise ValueError("Repository not provided")

        # 쿼리 파라미터
        params = data if isinstance(data, dict) else {}

        # 조회 실행
        results: List[Any] = await self.repository.query(self.query, **params)

        # 메타데이터
        context.metadata[f"{self.name}_result_count"] = len(results)

        return results
