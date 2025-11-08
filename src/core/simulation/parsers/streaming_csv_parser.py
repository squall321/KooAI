"""
스트리밍 CSV 파서

대용량 CSV 파일을 메모리 효율적으로 처리합니다.
"""

import csv
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional

import numpy as np

from ..models import (
    DataLocation,
    FieldData,
    FieldType,
    MeshData,
    SimulationResult,
    TimeStepData,
)
from .base import BaseParser
from .streaming_base import StreamingParser


class CSVChunk:
    """CSV 청크 데이터"""

    def __init__(self, rows: List[Dict[str, str]], row_offset: int):
        """
        Args:
            rows: CSV 행 데이터
            row_offset: 청크 시작 행 번호
        """
        self.rows = rows
        self.row_offset = row_offset


class StreamingCSVParser(BaseParser, StreamingParser[CSVChunk]):
    """
    스트리밍 CSV 파서

    대용량 CSV 파일을 청크 단위로 읽어서 메모리 사용량을 최소화합니다.

    주요 기능:
    - 청크 단위 읽기 (기본 10000 행)
    - 진행률 추적
    - 메모리 효율적 처리
    - 다중 타임스텝 지원

    사용 예:
        parser = StreamingCSVParser(
            chunk_size=10000,
            progress_callback=lambda p, t, pct: print(f"Progress: {pct:.1f}%")
        )
        result = parser.parse_stream(Path("large_data.csv"))
    """

    def __init__(
        self,
        chunk_rows: int = 10000,  # 청크당 행 수
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ):
        """
        Args:
            chunk_rows: 청크당 행 수 (기본: 10000)
            progress_callback: 진행률 콜백 함수
        """
        # BaseParser는 인자가 필요 없음
        BaseParser.__init__(self)
        # StreamingParser는 chunk_size를 바이트로 받지만,
        # CSV는 행 단위로 처리하므로 chunk_rows를 따로 저장
        StreamingParser.__init__(
            self,
            chunk_size=chunk_rows,  # 여기서는 행 수를 의미
            progress_callback=progress_callback,
        )
        self.chunk_rows = chunk_rows

    def can_parse(self, file_path: Path) -> bool:
        """CSV 파일 여부 확인"""
        return file_path.suffix.lower() == ".csv"

    def get_supported_extensions(self) -> List[str]:
        """지원 확장자"""
        return [".csv"]

    def parse(
        self,
        file_path: Path,
        delimiter: str = ",",
        has_time: bool = False,
        default_time: float = 0.0,
        default_step: int = 0,
    ) -> SimulationResult:
        """
        CSV 파일 파싱 (호환성 메서드)

        스트리밍 방식을 사용합니다.

        Args:
            file_path: CSV 파일 경로
            delimiter: 구분자
            has_time: 시간 컬럼 포함 여부
            default_time: 기본 시간
            default_step: 기본 스텝

        Returns:
            SimulationResult
        """
        return self.parse_stream(
            file_path,
            delimiter=delimiter,
            has_time=has_time,
            default_time=default_time,
            default_step=default_step,
        )

    def parse_stream(
        self,
        file_path: Path,
        delimiter: str = ",",
        has_time: bool = False,
        default_time: float = 0.0,
        default_step: int = 0,
    ) -> SimulationResult:
        """
        스트리밍 방식으로 CSV 파일 파싱

        Args:
            file_path: CSV 파일 경로
            delimiter: 구분자
            has_time: 시간 컬럼 포함 여부
            default_time: 기본 시간
            default_step: 기본 스텝

        Returns:
            SimulationResult
        """
        self.validate_file(file_path)

        # 진행률 추적기 생성
        progress = self._create_progress_tracker(file_path)

        # 누적 데이터
        all_vertices = []
        all_fields_data: Dict[str, List[np.ndarray]] = {}
        headers: Optional[List[str]] = None
        total_rows = 0

        # 청크 단위로 읽기
        for chunk in self.read_chunks(file_path, delimiter=delimiter, progress_tracker=progress):
            if headers is None:
                # 첫 청크에서 헤더 추출
                if chunk.rows:
                    headers = list(chunk.rows[0].keys())

            # 청크 데이터 파싱
            chunk_data = self._parse_chunk_rows(chunk.rows)

            # 좌표 추출
            chunk_vertices = self._extract_vertices(chunk_data)
            all_vertices.append(chunk_vertices)

            # 필드 데이터 추출
            if headers:
                chunk_fields = self._extract_chunk_fields(chunk_data, headers)

                for field_name, field_array in chunk_fields.items():
                    if field_name not in all_fields_data:
                        all_fields_data[field_name] = []
                    all_fields_data[field_name].append(field_array)

            total_rows += len(chunk.rows)

        # 모든 청크 데이터 병합
        if not all_vertices:
            raise ValueError(f"Empty CSV file: {file_path}")

        vertices = np.vstack(all_vertices)

        # 메시 생성
        mesh = MeshData(vertices=vertices)

        # 필드 생성
        fields = []
        for field_name, arrays in all_fields_data.items():
            combined_data = np.vstack(arrays) if len(arrays) > 1 else arrays[0]

            # 스칼라 vs 벡터 판단
            if combined_data.ndim == 2 and combined_data.shape[1] == 3:
                field_type = FieldType.VECTOR
            else:
                field_type = FieldType.SCALAR
                if combined_data.ndim == 2:
                    combined_data = combined_data.flatten()

            field = FieldData(
                name=field_name,
                field_type=field_type,
                location=DataLocation.POINT,
                data=combined_data,
            )
            fields.append(field)

        # 타임스텝 생성
        timestep = TimeStepData(time=default_time, step=default_step)
        for field in fields:
            timestep.add_field(field)

        # SimulationResult 생성
        result = SimulationResult(
            name=file_path.stem,
            simulation_type="CSV",
            mesh=mesh,
            source_file=file_path,
        )

        result.add_timestep(timestep)

        return result

    def read_chunks(
        self,
        file_path: Path,
        delimiter: str = ",",
        progress_tracker: Optional[object] = None,
    ) -> Iterator[CSVChunk]:
        """
        청크 단위로 CSV 파일 읽기

        Args:
            file_path: CSV 파일 경로
            delimiter: 구분자
            progress_tracker: 진행률 추적기

        Yields:
            CSVChunk 인스턴스
        """
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            chunk_rows = []
            row_offset = 0
            bytes_read = 0

            for row in reader:
                chunk_rows.append(row)

                # 진행률 업데이트 (대략적인 바이트 수 계산)
                if progress_tracker:
                    # 각 행의 대략적인 바이트 수
                    row_bytes = sum(len(str(v)) for v in row.values()) + len(row)
                    bytes_read += row_bytes
                    progress_tracker.update(row_bytes)

                # 청크 크기에 도달하면 yield
                if len(chunk_rows) >= self.chunk_rows:
                    yield CSVChunk(chunk_rows, row_offset)
                    row_offset += len(chunk_rows)
                    chunk_rows = []

            # 남은 행 처리
            if chunk_rows:
                yield CSVChunk(chunk_rows, row_offset)

    def _parse_chunk_rows(self, rows: List[Dict[str, str]]) -> Dict[str, List[float]]:
        """청크 행 데이터 파싱"""
        data: Dict[str, List[float]] = {}

        for row in rows:
            for key, value in row.items():
                if key not in data:
                    data[key] = []

                try:
                    data[key].append(float(value))
                except ValueError:
                    # 숫자가 아닌 값은 0.0으로
                    data[key].append(0.0)

        return data

    def _extract_vertices(self, data: Dict[str, List[float]]) -> np.ndarray:
        """좌표 추출"""
        x_key = self._find_column(data.keys(), ["x", "X", "coord_x"])
        y_key = self._find_column(data.keys(), ["y", "Y", "coord_y"])
        z_key = self._find_column(data.keys(), ["z", "Z", "coord_z"])

        if not x_key or not y_key:
            raise ValueError("CSV must have x, y columns")

        x = np.array(data[x_key])
        y = np.array(data[y_key])

        if z_key:
            z = np.array(data[z_key])
        else:
            z = np.zeros_like(x)

        return np.column_stack([x, y, z])

    def _extract_chunk_fields(
        self,
        data: Dict[str, List[float]],
        columns: List[str],
    ) -> Dict[str, np.ndarray]:
        """청크 필드 데이터 추출 (딕셔너리 반환)"""
        fields_data = {}

        # 제외할 컬럼
        exclude_columns = {
            "x",
            "X",
            "coord_x",
            "y",
            "Y",
            "coord_y",
            "z",
            "Z",
            "coord_z",
            "time",
            "Time",
            "step",
            "Step",
        }

        # 벡터 필드 찾기
        vector_fields = self._find_vector_fields(columns, exclude_columns)

        # 벡터 필드 생성
        for field_name, components in vector_fields.items():
            x_data = np.array(data[components["x"]])
            y_data = np.array(data[components["y"]])
            z_data = np.array(data[components["z"]])

            vector_data = np.column_stack([x_data, y_data, z_data])
            fields_data[field_name] = vector_data

        # 스칼라 필드 생성
        used_columns = set()
        for components in vector_fields.values():
            used_columns.update(components.values())

        for column in columns:
            if column in exclude_columns or column in used_columns:
                continue

            scalar_data = np.array(data[column]).reshape(-1, 1)  # 2D로 유지
            fields_data[column] = scalar_data

        return fields_data

    def _find_column(self, columns: List[str], candidates: List[str]) -> Optional[str]:
        """컬럼 이름 찾기"""
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    def _find_vector_fields(self, columns: List[str], exclude: set) -> Dict[str, Dict[str, str]]:
        """벡터 필드 찾기 (name_x, name_y, name_z 패턴)"""
        vector_fields = {}

        for column in columns:
            if column in exclude:
                continue

            # _x, _y, _z 패턴 확인
            if column.endswith("_x") or column.endswith("_X"):
                base_name = column[:-2]

                y_column = f"{base_name}_y"
                z_column = f"{base_name}_z"

                # Y 대문자 버전도 확인
                if y_column not in columns:
                    y_column = f"{base_name}_Y"

                if z_column not in columns:
                    z_column = f"{base_name}_Z"

                if y_column in columns and z_column in columns:
                    vector_fields[base_name] = {
                        "x": column,
                        "y": y_column,
                        "z": z_column,
                    }

        return vector_fields
