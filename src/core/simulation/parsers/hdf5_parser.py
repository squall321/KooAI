"""
HDF5 파서

HDF5 형식의 시뮬레이션 데이터를 파싱합니다.
대용량 데이터에 적합한 형식입니다.
"""

from pathlib import Path
from typing import Dict, List, Any
import numpy as np

try:
    import h5py

    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False
    h5py = None  # type: ignore

from .base import BaseParser
from ..models import (
    SimulationResult,
    MeshData,
    TimeStepData,
    FieldData,
    FieldType,
    DataLocation,
)


class HDF5Parser(BaseParser):
    """
    HDF5 파서

    HDF5 형식의 시뮬레이션 데이터를 파싱합니다.

    예상 HDF5 구조:
    /mesh/
        vertices: (N, 3) array
        cells: (M, K) array (선택)
    /fields/
        timestep_0/
            field_name: (N,) or (N, 3) array
        timestep_1/
            ...
    /metadata/
        simulation_type: str
        time_values: (T,) array
    """

    def __init__(self):
        if not HDF5_AVAILABLE:
            raise ImportError(
                "h5py is required for HDF5 parsing. " "Install it with: pip install h5py"
            )

    def can_parse(self, file_path: Path) -> bool:
        """HDF5 파일 여부 확인"""
        if file_path.suffix.lower() not in [".h5", ".hdf5"]:
            return False

        try:
            # HDF5 파일 열기 시도
            with h5py.File(file_path, "r") as f:
                # 기본 구조 확인
                return "mesh" in f or "fields" in f
        except Exception:
            return False

    def get_supported_extensions(self) -> List[str]:
        """지원 확장자: .h5, .hdf5"""
        return [".h5", ".hdf5"]

    def parse(self, file_path: Path, **options) -> SimulationResult:
        """
        HDF5 파일 파싱

        Args:
            file_path: HDF5 파일 경로
            **options: 파싱 옵션
                - name: 시뮬레이션 이름

        Returns:
            SimulationResult
        """
        self.validate_file(file_path)

        with h5py.File(file_path, "r") as f:
            # 메시 데이터 파싱
            mesh = self._parse_mesh(f)

            # 메타데이터 파싱
            metadata = self._parse_metadata(f)
            simulation_type = metadata.get("simulation_type", "HDF5")

            # 필드 데이터 파싱 (타임스텝별)
            timesteps = self._parse_timesteps(f, metadata)

            # SimulationResult 생성
            name = options.get("name", file_path.stem)
            result = SimulationResult(
                name=name,
                simulation_type=simulation_type,
                mesh=mesh,
                timesteps=timesteps,
                metadata=metadata,
                source_file=file_path,
            )

            return result

    def _parse_mesh(self, f: Any) -> MeshData:
        """메시 데이터 파싱"""
        if "mesh" not in f:
            raise ValueError("No mesh data found in HDF5 file")

        mesh_group = f["mesh"]

        # Vertices
        if "vertices" not in mesh_group:
            raise ValueError("No vertices found in mesh data")

        vertices = np.array(mesh_group["vertices"])

        # Cells (선택사항)
        cells = None
        if "cells" in mesh_group:
            cells = np.array(mesh_group["cells"])

        # Faces (선택사항)
        faces = None
        if "faces" in mesh_group:
            faces = np.array(mesh_group["faces"])

        return MeshData(vertices=vertices, cells=cells, faces=faces)

    def _parse_metadata(self, f: Any) -> Dict:
        """메타데이터 파싱"""
        metadata = {}

        if "metadata" in f:
            meta_group = f["metadata"]

            for key in meta_group.keys():
                try:
                    value = meta_group[key][()]
                    # bytes를 str로 변환
                    if isinstance(value, bytes):
                        value = value.decode("utf-8")
                    metadata[key] = value
                except Exception:
                    pass

        return metadata

    def _parse_timesteps(self, f: Any, metadata: Dict) -> List[TimeStepData]:
        """타임스텝 데이터 파싱"""
        timesteps = []

        if "fields" not in f:
            # 필드 데이터가 없으면 빈 타임스텝 반환
            return [TimeStepData(time=0.0, step=0, fields={})]

        fields_group = f["fields"]

        # 타임스텝 목록 찾기
        timestep_names = sorted(
            [name for name in fields_group.keys() if name.startswith("timestep_")]
        )

        # 시간 값 가져오기 (메타데이터에서)
        time_values = metadata.get("time_values", None)
        if time_values is not None and not isinstance(time_values, np.ndarray):
            time_values = np.array(time_values)

        for i, ts_name in enumerate(timestep_names):
            ts_group = fields_group[ts_name]

            # 타임스텝 번호 추출
            step = int(ts_name.replace("timestep_", ""))

            # 시간 값
            if time_values is not None and i < len(time_values):
                time = float(time_values[i])
            else:
                time = float(step)

            # 필드 데이터 파싱
            fields = {}
            for field_name in ts_group.keys():
                field = self._parse_field(ts_group[field_name], field_name)
                if field:
                    fields[field_name] = field

            timesteps.append(TimeStepData(time=time, step=step, fields=fields))

        # 타임스텝이 없으면 기본 타임스텝 생성
        if not timesteps:
            timesteps.append(TimeStepData(time=0.0, step=0, fields={}))

        return timesteps

    def _parse_field(self, dataset: Any, field_name: str) -> FieldData:
        """필드 데이터 파싱"""
        data = np.array(dataset)

        # 데이터 형태로 필드 타입 결정
        if data.ndim == 1:
            field_type = FieldType.SCALAR
        elif data.ndim == 2:
            if data.shape[1] == 3:
                field_type = FieldType.VECTOR
            elif data.shape[1] == 9:
                field_type = FieldType.TENSOR
            else:
                field_type = FieldType.SCALAR
        else:
            field_type = FieldType.SCALAR

        # 데이터 위치 (기본: NODE)
        # HDF5 속성에서 가져올 수 있음
        location = DataLocation.NODE
        if "location" in dataset.attrs:
            location_str = dataset.attrs["location"]
            if isinstance(location_str, bytes):
                location_str = location_str.decode("utf-8")
            if location_str.upper() == "CELL":
                location = DataLocation.CELL

        # 단위
        unit = None
        if "unit" in dataset.attrs:
            unit = dataset.attrs["unit"]
            if isinstance(unit, bytes):
                unit = unit.decode("utf-8")

        return FieldData(
            name=field_name,
            field_type=field_type,
            location=location,
            data=data,
            unit=unit,
        )
