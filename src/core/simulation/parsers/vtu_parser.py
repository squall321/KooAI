"""
VTU (VTK XML Unstructured Grid) 파서

VTK XML Unstructured Grid 형식 파일을 파싱합니다.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

from .base import BaseParser
from ..models import (
    SimulationResult,
    MeshData,
    TimeStepData,
    FieldData,
    FieldType,
    DataLocation,
)


class VTUParser(BaseParser):
    """
    VTU (VTK XML Unstructured Grid) 파서

    VTK XML Unstructured Grid 형식의 파일을 파싱합니다.
    """

    def can_parse(self, file_path: Path) -> bool:
        """VTU 파일 여부 확인"""
        if file_path.suffix.lower() != ".vtu":
            return False

        try:
            # XML 헤더 확인
            with open(file_path, "r", encoding="utf-8") as f:
                first_lines = "".join([f.readline() for _ in range(5)])
                return "VTKFile" in first_lines and 'type="UnstructuredGrid"' in first_lines
        except Exception:
            return False

    def get_supported_extensions(self) -> List[str]:
        """지원 확장자: .vtu"""
        return [".vtu"]

    def parse(self, file_path: Path, **options: Any) -> SimulationResult:
        """
        VTU 파일 파싱

        Args:
            file_path: VTU 파일 경로
            **options: 파싱 옵션
                - name: 시뮬레이션 이름 (기본: 파일명)

        Returns:
            SimulationResult
        """
        self.validate_file(file_path)

        # XML 파싱
        tree = ET.parse(file_path)
        root = tree.getroot()

        # VTK 파일 검증
        if root.tag != "VTKFile" or root.get("type") != "UnstructuredGrid":
            raise ValueError("Not a valid VTU file")

        # UnstructuredGrid 요소 찾기
        unstructured_grid = root.find("UnstructuredGrid")
        if unstructured_grid is None:
            raise ValueError("UnstructuredGrid element not found")

        # Piece 요소 찾기 (첫 번째 piece만 처리)
        piece = unstructured_grid.find("Piece")
        if piece is None:
            raise ValueError("Piece element not found")

        # 메시 데이터 파싱
        mesh = self._parse_mesh(piece)

        # 필드 데이터 파싱
        fields = self._parse_fields(piece)

        # TimeStepData 생성 (VTU는 단일 타임스텝)
        timestep = TimeStepData(time=0.0, step=0, fields=fields)

        # SimulationResult 생성
        name = options.get("name", file_path.stem)
        result = SimulationResult(
            name=name,
            simulation_type="VTU",
            mesh=mesh,
            timesteps=[timestep],
            source_file=file_path,
        )

        return result

    def _parse_mesh(self, piece: ET.Element) -> MeshData:
        """메시 데이터 파싱"""
        # Points 파싱
        points_elem = piece.find("Points")
        if points_elem is None:
            raise ValueError("Points element not found")

        points_array = points_elem.find("DataArray")
        if points_array is None:
            raise ValueError("Points DataArray not found")

        vertices = self._parse_data_array(points_array)
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            vertices = vertices.reshape(-1, 3)

        # Cells 파싱
        cells_elem = piece.find("Cells")
        cells = None
        if cells_elem is not None:
            connectivity = None
            offsets = None

            for data_array in cells_elem.findall("DataArray"):
                name = data_array.get("Name", "")
                if name == "connectivity":
                    connectivity = self._parse_data_array(data_array).astype(np.int32)
                elif name == "offsets":
                    offsets = self._parse_data_array(data_array).astype(np.int32)

            if connectivity is not None and offsets is not None:
                # offsets를 사용하여 cells 재구성
                cells = self._reconstruct_cells(connectivity, offsets)

        return MeshData(vertices=vertices, cells=cells)

    def _parse_fields(self, piece: ET.Element) -> Dict[str, FieldData]:
        """필드 데이터 파싱"""
        fields = {}

        # PointData 파싱
        point_data = piece.find("PointData")
        if point_data is not None:
            for data_array in point_data.findall("DataArray"):
                field_name = data_array.get("Name", "unnamed")
                field = self._parse_field_data_array(data_array, DataLocation.NODE)
                if field:
                    fields[field_name] = field

        # CellData 파싱
        cell_data = piece.find("CellData")
        if cell_data is not None:
            for data_array in cell_data.findall("DataArray"):
                field_name = data_array.get("Name", "unnamed")
                field = self._parse_field_data_array(data_array, DataLocation.CELL)
                if field:
                    fields[field_name] = field

        return fields

    def _parse_data_array(self, data_array: ET.Element) -> np.ndarray:
        """DataArray 요소 파싱"""
        data_format = data_array.get("format", "ascii")
        data_type = data_array.get("type", "Float32")
        num_components = int(data_array.get("NumberOfComponents", "1"))

        if data_format == "ascii":
            # ASCII 형식 데이터
            text = data_array.text
            if not text:
                return np.array([])

            # NumPy dtype 매핑
            dtype_map = {
                "Float32": np.float32,
                "Float64": np.float64,
                "Int32": np.int32,
                "Int64": np.int64,
                "UInt8": np.uint8,
                "UInt32": np.uint32,
            }
            dtype = dtype_map.get(data_type, np.float32)

            # 데이터 파싱
            values = np.fromstring(text, dtype=dtype, sep=" ")

            # 컴포넌트가 여러 개면 reshape
            if num_components > 1 and len(values) > 0:
                values = values.reshape(-1, num_components)

            return values
        else:
            # binary, appended 형식은 지원하지 않음
            raise ValueError(f"Unsupported data format: {data_format}")

    def _parse_field_data_array(self, data_array: ET.Element, location: DataLocation) -> FieldData:
        """필드 DataArray 파싱"""
        field_name = data_array.get("Name", "unnamed")
        num_components = int(data_array.get("NumberOfComponents", "1"))

        # 데이터 파싱
        data = self._parse_data_array(data_array)

        # 필드 타입 결정
        if num_components == 1:
            field_type = FieldType.SCALAR
        elif num_components == 3:
            field_type = FieldType.VECTOR
        elif num_components == 9:
            field_type = FieldType.TENSOR
        else:
            # 기타 컴포넌트 수는 스칼라로 처리
            field_type = FieldType.SCALAR

        return FieldData(
            name=field_name,
            field_type=field_type,
            location=location,
            data=data,
        )

    def _reconstruct_cells(self, connectivity: np.ndarray, offsets: np.ndarray) -> np.ndarray:
        """connectivity와 offsets로부터 cells 재구성"""
        num_cells = len(offsets)
        cells = []

        prev_offset = 0
        for offset in offsets:
            cell = connectivity[prev_offset:offset]
            cells.append(cell)
            prev_offset = offset

        # 가변 길이 배열을 리스트로 반환
        # (모든 셀이 같은 크기면 2D 배열로 변환 가능)
        if len(cells) > 0:
            cell_sizes = [len(cell) for cell in cells]
            if len(set(cell_sizes)) == 1:
                # 모든 셀이 같은 크기
                return np.array(cells)
            else:
                # 가변 길이 - object array로 반환
                return np.array(cells, dtype=object)

        return np.array([])
