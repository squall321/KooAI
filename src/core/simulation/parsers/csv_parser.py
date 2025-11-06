"""
CSV 시뮬레이션 결과 파서

CSV 형식의 시뮬레이션 결과 파싱.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

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


class CSVParser(BaseParser):
    """
    CSV 결과 파서

    CSV 형식의 시뮬레이션 결과 파싱.

    파일 형식:
    - 첫 행: 헤더 (컬럼 이름)
    - 이후 행: 데이터

    컬럼 형식:
    - x, y, z: 좌표
    - field_name: 필드 값 (스칼라)
    - field_name_x, field_name_y, field_name_z: 벡터 필드
    - time: 시간 (옵션)
    - step: 타임스텝 (옵션)
    """

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
        CSV 파일 파싱

        Args:
            file_path: CSV 파일 경로
            delimiter: 구분자 (기본: ",")
            has_time: 시간 컬럼 포함 여부
            default_time: 기본 시간
            default_step: 기본 스텝

        Returns:
            SimulationResult
        """
        self.validate_file(file_path)

        # CSV 읽기
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)

        if not rows:
            raise ValueError(f"Empty CSV file: {file_path}")

        # 데이터 파싱
        data = self._parse_rows(rows)

        # 좌표 추출
        vertices = self._extract_vertices(data)

        # 메시 생성
        mesh = MeshData(vertices=vertices)

        # 필드 추출
        fields = self._extract_fields(data, rows[0].keys())

        # 시간 정보
        time = default_time
        step = default_step

        if has_time and "time" in data:
            times = data["time"]
            if len(set(times)) == 1:
                time = times[0]
            else:
                # 다중 타임스텝은 별도 처리 필요
                pass

        if "step" in data:
            steps = data["step"]
            if len(set(steps)) == 1:
                step = int(steps[0])

        # 타임스텝 생성
        timestep = TimeStepData(time=time, step=step)

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

    def _parse_rows(self, rows: List[Dict[str, str]]) -> Dict[str, List[float]]:
        """행 데이터 파싱"""
        data: Dict[str, List[float]] = {}

        for row in rows:
            for key, value in row.items():
                if key not in data:
                    data[key] = []

                try:
                    data[key].append(float(value))
                except ValueError:
                    # 숫자가 아닌 값은 건너뜀
                    data[key].append(0.0)

        return data

    def _extract_vertices(self, data: Dict[str, List[float]]) -> np.ndarray:
        """좌표 추출"""
        # x, y, z 컬럼 찾기
        x_key = self._find_column(data.keys(), ["x", "X", "coord_x"])
        y_key = self._find_column(data.keys(), ["y", "Y", "coord_y"])
        z_key = self._find_column(data.keys(), ["z", "Z", "coord_z"])

        if not x_key or not y_key:
            raise ValueError("CSV must have x, y columns")

        x = np.array(data[x_key])
        y = np.array(data[y_key])

        # z가 없으면 0으로 채움
        if z_key:
            z = np.array(data[z_key])
        else:
            z = np.zeros_like(x)

        return np.column_stack([x, y, z])

    def _extract_fields(
        self,
        data: Dict[str, List[float]],
        columns: List[str],
    ) -> List[FieldData]:
        """필드 데이터 추출"""
        fields = []

        # 좌표 및 시간 컬럼 제외
        exclude_columns = {
            "x", "X", "coord_x",
            "y", "Y", "coord_y",
            "z", "Z", "coord_z",
            "time", "Time", "step", "Step",
        }

        # 벡터 필드 찾기 (name_x, name_y, name_z 패턴)
        vector_fields = self._find_vector_fields(columns, exclude_columns)

        # 벡터 필드 생성
        for field_name, components in vector_fields.items():
            x_data = np.array(data[components["x"]])
            y_data = np.array(data[components["y"]])
            z_data = np.array(data[components["z"]])

            vector_data = np.column_stack([x_data, y_data, z_data])

            field = FieldData(
                name=field_name,
                field_type=FieldType.VECTOR,
                location=DataLocation.POINT,
                data=vector_data,
            )

            fields.append(field)

        # 스칼라 필드 생성
        used_columns = set()
        for components in vector_fields.values():
            used_columns.update(components.values())

        for column in columns:
            if column in exclude_columns or column in used_columns:
                continue

            scalar_data = np.array(data[column])

            field = FieldData(
                name=column,
                field_type=FieldType.SCALAR,
                location=DataLocation.POINT,
                data=scalar_data,
            )

            fields.append(field)

        return fields

    def _find_column(
        self,
        columns: List[str],
        candidates: List[str],
    ) -> Optional[str]:
        """컬럼 이름 찾기"""
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    def _find_vector_fields(
        self,
        columns: List[str],
        exclude: set,
    ) -> Dict[str, Dict[str, str]]:
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
