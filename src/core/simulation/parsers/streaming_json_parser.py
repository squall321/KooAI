"""
스트리밍 JSON 파서

ijson을 사용하여 대용량 JSON 파일을 메모리 효율적으로 처리합니다.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

import ijson
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


class JSONChunk:
    """JSON 청크 데이터"""

    def __init__(self, items: List[Dict[str, Any]], item_offset: int):
        """
        Args:
            items: JSON 아이템 리스트
            item_offset: 청크 시작 아이템 번호
        """
        self.items = items
        self.item_offset = item_offset


class StreamingJSONParser(BaseParser, StreamingParser[JSONChunk]):
    """
    스트리밍 JSON 파서

    ijson을 사용하여 대용량 JSON 파일을 청크 단위로 읽습니다.

    지원 형식:
    1. 배열 형식:
       [
         {"x": 0.0, "y": 0.0, "z": 0.0, "temperature": 300.0},
         {"x": 1.0, "y": 0.0, "z": 0.0, "temperature": 310.0},
         ...
       ]

    2. 객체 형식:
       {
         "vertices": [[0,0,0], [1,0,0], ...],
         "fields": {
           "temperature": [300, 310, ...],
           "pressure": [101325, 101330, ...]
         }
       }

    사용 예:
        parser = StreamingJSONParser(
            chunk_size=1000,
            progress_callback=lambda p, t, pct: print(f"Progress: {pct:.1f}%")
        )
        result = parser.parse_stream(Path("large_data.json"))
    """

    def __init__(
        self,
        chunk_size: int = 1000,  # 청크당 아이템 수
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ):
        """
        Args:
            chunk_size: 청크당 아이템 수 (기본: 1000)
            progress_callback: 진행률 콜백 함수
        """
        BaseParser.__init__(self)
        StreamingParser.__init__(
            self,
            chunk_size=chunk_size,
            progress_callback=progress_callback,
        )

    def can_parse(self, file_path: Path) -> bool:
        """JSON 파일 여부 확인"""
        return file_path.suffix.lower() == ".json"

    def get_supported_extensions(self) -> List[str]:
        """지원 확장자"""
        return [".json"]

    def parse(self, file_path: Path, **options) -> SimulationResult:
        """
        JSON 파일 파싱 (호환성 메서드)

        Args:
            file_path: JSON 파일 경로
            **options: 파서 옵션

        Returns:
            SimulationResult
        """
        return self.parse_stream(file_path, **options)

    def parse_stream(
        self,
        file_path: Path,
        json_path: str = "item",  # ijson path (예: "data.item" for {"data": [...]}
        **options,
    ) -> SimulationResult:
        """
        스트리밍 방식으로 JSON 파일 파싱

        Args:
            file_path: JSON 파일 경로
            json_path: ijson path (기본: "item" - 루트 배열)
            **options: 추가 옵션

        Returns:
            SimulationResult
        """
        self.validate_file(file_path)

        # 진행률 추적기 생성
        progress = self._create_progress_tracker(file_path)

        # 누적 데이터
        all_vertices = []
        all_fields_data: Dict[str, List[np.ndarray]] = {}
        total_items = 0

        # 청크 단위로 읽기
        for chunk in self.read_chunks(
            file_path, json_path=json_path, progress_tracker=progress
        ):
            # 청크 데이터 파싱
            chunk_vertices, chunk_fields = self._parse_chunk_items(chunk.items)

            all_vertices.append(chunk_vertices)

            # 필드 데이터 누적
            for field_name, field_array in chunk_fields.items():
                if field_name not in all_fields_data:
                    all_fields_data[field_name] = []
                all_fields_data[field_name].append(field_array)

            total_items += len(chunk.items)

        # 모든 청크 데이터 병합
        if not all_vertices:
            raise ValueError(f"Empty JSON file: {file_path}")

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
        timestep = TimeStepData(time=0.0, step=0)
        for field in fields:
            timestep.add_field(field)

        # SimulationResult 생성
        result = SimulationResult(
            name=file_path.stem,
            simulation_type="JSON",
            mesh=mesh,
            source_file=file_path,
        )

        result.add_timestep(timestep)

        return result

    def read_chunks(
        self,
        file_path: Path,
        json_path: str = "item",
        progress_tracker: Optional[object] = None,
    ) -> Iterator[JSONChunk]:
        """
        청크 단위로 JSON 파일 읽기

        ijson을 사용하여 스트리밍 방식으로 JSON을 파싱합니다.

        Args:
            file_path: JSON 파일 경로
            json_path: ijson path (예: "item", "data.item")
            progress_tracker: 진행률 추적기

        Yields:
            JSONChunk 인스턴스
        """
        with open(file_path, "rb") as f:
            # ijson을 사용한 스트리밍 파싱
            parser = ijson.items(f, json_path)

            chunk_items = []
            item_offset = 0
            bytes_read = 0
            last_position = 0

            for item in parser:
                chunk_items.append(item)

                # 진행률 업데이트
                if progress_tracker:
                    current_position = f.tell()
                    bytes_delta = current_position - last_position
                    if bytes_delta > 0:
                        progress_tracker.update(bytes_delta)
                        last_position = current_position

                # 청크 크기에 도달하면 yield
                if len(chunk_items) >= self.chunk_size:
                    yield JSONChunk(chunk_items, item_offset)
                    item_offset += len(chunk_items)
                    chunk_items = []

            # 남은 아이템 처리
            if chunk_items:
                yield JSONChunk(chunk_items, item_offset)

            # 마지막 바이트까지 진행률 업데이트
            if progress_tracker:
                final_position = f.tell()
                if final_position > last_position:
                    progress_tracker.update(final_position - last_position)

    def _parse_chunk_items(
        self, items: List[Dict[str, Any]]
    ) -> tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        청크 아이템 파싱

        Args:
            items: JSON 아이템 리스트

        Returns:
            (vertices, fields_data) 튜플
        """
        if not items:
            raise ValueError("Empty chunk")

        # 좌표 추출
        vertices = []
        fields_data: Dict[str, List[Any]] = {}

        for item in items:
            # 좌표 추출
            x = self._get_value(item, ["x", "X", "coord_x"], 0.0)
            y = self._get_value(item, ["y", "Y", "coord_y"], 0.0)
            z = self._get_value(item, ["z", "Z", "coord_z"], 0.0)

            vertices.append([x, y, z])

            # 필드 데이터 추출
            for key, value in item.items():
                if key.lower() in ["x", "y", "z", "coord_x", "coord_y", "coord_z"]:
                    continue

                if key not in fields_data:
                    fields_data[key] = []

                # 숫자 또는 리스트 (벡터)
                if isinstance(value, (int, float)):
                    fields_data[key].append(value)
                elif isinstance(value, (list, tuple)) and len(value) in [2, 3]:
                    # 벡터 필드
                    if len(value) == 2:
                        fields_data[key].append([value[0], value[1], 0.0])
                    else:
                        fields_data[key].append(value)
                else:
                    # 기타 타입은 0.0으로
                    fields_data[key].append(0.0)

        vertices_array = np.array(vertices)

        # 필드 데이터를 numpy 배열로 변환
        fields_arrays = {}
        for field_name, values in fields_data.items():
            fields_arrays[field_name] = np.array(values)

        return vertices_array, fields_arrays

    def _get_value(
        self, item: Dict[str, Any], keys: List[str], default: Any
    ) -> Any:
        """딕셔너리에서 값 추출 (여러 키 후보)"""
        for key in keys:
            if key in item:
                value = item[key]
                # 숫자 변환 시도
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
        return default
