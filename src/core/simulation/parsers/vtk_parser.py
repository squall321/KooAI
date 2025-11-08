"""
VTK 시뮬레이션 결과 파서

VTK ASCII 형식의 시뮬레이션 결과 파싱.
"""

from pathlib import Path
from typing import Dict, List, Tuple

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


class VTKParser(BaseParser):
    """
    VTK ASCII 파서

    VTK Legacy ASCII 형식 파싱.

    지원 데이터셋:
    - STRUCTURED_POINTS
    - STRUCTURED_GRID
    - UNSTRUCTURED_GRID
    - POLYDATA
    """

    def can_parse(self, file_path: Path) -> bool:
        """VTK 파일 여부 확인"""
        extension = file_path.suffix.lower()
        if extension not in [".vtk"]:
            return False

        # 파일 헤더 확인
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                return first_line.startswith("# vtk DataFile Version")
        except Exception:
            return False

    def get_supported_extensions(self) -> List[str]:
        """지원 확장자"""
        return [".vtk"]

    def parse(
        self,
        file_path: Path,
        time: float = 0.0,
        step: int = 0,
    ) -> SimulationResult:
        """
        VTK 파일 파싱

        Args:
            file_path: VTK 파일 경로
            time: 타임스텝 시간
            step: 타임스텝 번호

        Returns:
            SimulationResult
        """
        self.validate_file(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        # 헤더 파싱
        header = self._parse_header(lines)

        # 데이터셋 파싱
        mesh, line_idx = self._parse_dataset(lines, header["format"])

        # 필드 데이터 파싱
        fields = self._parse_fields(lines, line_idx, mesh.num_vertices)

        # 타임스텝 생성
        timestep = TimeStepData(time=time, step=step)
        for field in fields:
            timestep.add_field(field)

        # SimulationResult 생성
        result = SimulationResult(
            name=file_path.stem,
            simulation_type="VTK",
            mesh=mesh,
            source_file=file_path,
            metadata={
                "vtk_version": header.get("version", ""),
                "description": header.get("description", ""),
            },
        )

        result.add_timestep(timestep)

        return result

    def _parse_header(self, lines: List[str]) -> Dict[str, str]:
        """VTK 헤더 파싱"""
        if len(lines) < 4:
            raise ValueError("Invalid VTK file: too few lines")

        # 라인 1: 버전
        version_line = lines[0]
        if not version_line.startswith("# vtk DataFile Version"):
            raise ValueError("Invalid VTK file: missing version header")

        version = version_line.replace("# vtk DataFile Version", "").strip()

        # 라인 2: 설명
        description = lines[1]

        # 라인 3: 형식 (ASCII/BINARY)
        format_line = lines[2].upper()
        if format_line not in ["ASCII", "BINARY"]:
            raise ValueError(f"Invalid VTK format: {format_line}")

        if format_line == "BINARY":
            raise NotImplementedError("Binary VTK not supported yet")

        return {
            "version": version,
            "description": description,
            "format": format_line,
        }

    def _parse_dataset(
        self,
        lines: List[str],
        format_type: str,
    ) -> Tuple[MeshData, int]:
        """데이터셋 파싱"""
        # 라인 4: DATASET 타입
        dataset_line_idx = 3

        if not lines[dataset_line_idx].startswith("DATASET"):
            raise ValueError("Missing DATASET keyword")

        dataset_type = lines[dataset_line_idx].split()[1]

        if dataset_type == "POLYDATA":
            return self._parse_polydata(lines, dataset_line_idx + 1)
        elif dataset_type == "UNSTRUCTURED_GRID":
            return self._parse_unstructured_grid(lines, dataset_line_idx + 1)
        else:
            raise NotImplementedError(f"Dataset type {dataset_type} not supported yet")

    def _parse_polydata(
        self,
        lines: List[str],
        start_idx: int,
    ) -> Tuple[MeshData, int]:
        """POLYDATA 파싱"""
        idx = start_idx

        # POINTS
        if not lines[idx].startswith("POINTS"):
            raise ValueError("Missing POINTS in POLYDATA")

        parts = lines[idx].split()
        num_points = int(parts[1])
        idx += 1

        # 꼭짓점 읽기
        vertices = []
        while len(vertices) < num_points * 3:
            idx += 1
            values = lines[idx - 1].split()
            vertices.extend([float(v) for v in values])

        vertices = np.array(vertices).reshape(-1, 3)

        # POLYGONS 또는 TRIANGLE_STRIPS (옵션)
        faces = None

        while idx < len(lines):
            line = lines[idx]

            if line.startswith("POLYGONS"):
                parts = line.split()
                num_polygons = int(parts[1])
                idx += 1

                # 면 읽기
                face_data = []
                while len(face_data) < num_polygons:
                    parts = lines[idx].split()
                    idx += 1

                    # 첫 숫자는 꼭짓점 개수
                    n_vertices = int(parts[0])
                    face_indices = [int(parts[i + 1]) for i in range(n_vertices)]

                    # 삼각형만 지원
                    if n_vertices == 3:
                        face_data.append(face_indices)
                    elif n_vertices == 4:
                        # 사각형 -> 2개 삼각형
                        face_data.append([face_indices[0], face_indices[1], face_indices[2]])
                        face_data.append([face_indices[0], face_indices[2], face_indices[3]])
                    else:
                        # 다각형은 건너뜀
                        pass

                faces = np.array(face_data) if face_data else None
                break

            elif line.startswith("POINT_DATA") or line.startswith("CELL_DATA"):
                break

            idx += 1

        mesh = MeshData(vertices=vertices, faces=faces)
        return mesh, idx

    def _parse_unstructured_grid(
        self,
        lines: List[str],
        start_idx: int,
    ) -> Tuple[MeshData, int]:
        """UNSTRUCTURED_GRID 파싱"""
        idx = start_idx

        # POINTS
        if not lines[idx].startswith("POINTS"):
            raise ValueError("Missing POINTS in UNSTRUCTURED_GRID")

        parts = lines[idx].split()
        num_points = int(parts[1])
        idx += 1

        # 꼭짓점 읽기
        vertices = []
        while len(vertices) < num_points * 3:
            values = lines[idx].split()
            idx += 1
            vertices.extend([float(v) for v in values])

        vertices = np.array(vertices).reshape(-1, 3)

        # CELLS
        cells = None
        if idx < len(lines) and lines[idx].startswith("CELLS"):
            parts = lines[idx].split()
            num_cells = int(parts[1])
            idx += 1

            # 셀 읽기 (간단히 건너뜀)
            cell_data = []
            while len(cell_data) < num_cells:
                parts = lines[idx].split()
                idx += 1
                cell_data.append([int(p) for p in parts])

            # CELL_TYPES (건너뜀)
            if idx < len(lines) and lines[idx].startswith("CELL_TYPES"):
                idx += 1
                idx += num_cells  # 셀 타입 라인 건너뜀

        mesh = MeshData(vertices=vertices, cells=cells)
        return mesh, idx

    def _parse_fields(
        self,
        lines: List[str],
        start_idx: int,
        num_points: int,
    ) -> List[FieldData]:
        """필드 데이터 파싱"""
        fields = []
        idx = start_idx

        location = DataLocation.POINT

        while idx < len(lines):
            line = lines[idx]

            if line.startswith("POINT_DATA"):
                location = DataLocation.POINT
                parts = line.split()
                num_data = int(parts[1])
                idx += 1

            elif line.startswith("CELL_DATA"):
                location = DataLocation.CELL
                parts = line.split()
                num_data = int(parts[1])
                idx += 1

            elif line.startswith("SCALARS"):
                # SCALARS name data_type num_comp
                parts = line.split()
                field_name = parts[1]
                idx += 1

                # LOOKUP_TABLE (건너뜀)
                if idx < len(lines) and lines[idx].startswith("LOOKUP_TABLE"):
                    idx += 1

                # 데이터 읽기
                values = []
                while len(values) < num_points:
                    if idx >= len(lines):
                        break
                    parts = lines[idx].split()
                    idx += 1

                    # 필드 데이터 종료 확인
                    if parts and parts[0] in ["SCALARS", "VECTORS", "POINT_DATA", "CELL_DATA"]:
                        idx -= 1
                        break

                    values.extend([float(v) for v in parts])

                if values:
                    data = np.array(values[:num_points])
                    field = FieldData(
                        name=field_name,
                        field_type=FieldType.SCALAR,
                        location=location,
                        data=data,
                    )
                    fields.append(field)

            elif line.startswith("VECTORS"):
                # VECTORS name data_type
                parts = line.split()
                field_name = parts[1]
                idx += 1

                # 데이터 읽기
                values = []
                while len(values) < num_points * 3:
                    if idx >= len(lines):
                        break
                    parts = lines[idx].split()
                    idx += 1

                    # 필드 데이터 종료 확인
                    if parts and parts[0] in ["SCALARS", "VECTORS", "POINT_DATA", "CELL_DATA"]:
                        idx -= 1
                        break

                    values.extend([float(v) for v in parts])

                if values:
                    data = np.array(values[: num_points * 3]).reshape(-1, 3)
                    field = FieldData(
                        name=field_name,
                        field_type=FieldType.VECTOR,
                        location=location,
                        data=data,
                    )
                    fields.append(field)

            else:
                idx += 1

        return fields
