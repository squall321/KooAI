"""
시뮬레이션 결과 도메인 모델

시뮬레이션 결과 데이터 구조와 모델.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


class FieldType(Enum):
    """필드 데이터 타입"""

    SCALAR = "scalar"  # 스칼라 (온도, 압력 등)
    VECTOR = "vector"  # 벡터 (속도, 힘 등)
    TENSOR = "tensor"  # 텐서 (응력, 변형률 등)


class DataLocation(Enum):
    """데이터 위치"""

    NODE = "node"  # 노드/꼭짓점 데이터
    CELL = "cell"  # 셀/요소 데이터
    POINT = "point"  # 포인트 데이터


@dataclass
class FieldData:
    """
    필드 데이터

    시뮬레이션 결과의 필드 데이터 (스칼라, 벡터, 텐서).
    """

    name: str
    field_type: FieldType
    location: DataLocation
    data: np.ndarray
    unit: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """데이터 검증"""
        # 데이터 타입 검증
        if self.field_type == FieldType.SCALAR:
            if self.data.ndim != 1:
                raise ValueError(f"Scalar field must be 1D, got {self.data.ndim}D")
        elif self.field_type == FieldType.VECTOR:
            if self.data.ndim != 2 or self.data.shape[1] != 3:
                raise ValueError(
                    f"Vector field must be Nx3, got shape {self.data.shape}"
                )
        elif self.field_type == FieldType.TENSOR:
            if self.data.ndim != 3:
                raise ValueError(f"Tensor field must be 3D, got {self.data.ndim}D")

    @property
    def size(self) -> int:
        """데이터 개수"""
        return len(self.data)

    def get_min(self) -> float:
        """최솟값"""
        return float(np.min(self.data))

    def get_max(self) -> float:
        """최댓값"""
        return float(np.max(self.data))

    def get_mean(self) -> float:
        """평균값"""
        return float(np.mean(self.data))

    def get_std(self) -> float:
        """표준편차"""
        return float(np.std(self.data))


@dataclass
class MeshData:
    """
    메시 데이터

    시뮬레이션 메시/격자 정보.
    """

    vertices: np.ndarray  # 꼭짓점 (N x 3)
    cells: Optional[np.ndarray] = None  # 셀/요소 (M x K)
    faces: Optional[np.ndarray] = None  # 면 (surface mesh용)
    cell_types: Optional[np.ndarray] = None  # 셀 타입

    def __post_init__(self):
        """데이터 검증"""
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError(
                f"Vertices must be Nx3, got shape {self.vertices.shape}"
            )

    @property
    def num_vertices(self) -> int:
        """꼭짓점 개수"""
        return len(self.vertices)

    @property
    def num_cells(self) -> int:
        """셀 개수"""
        return len(self.cells) if self.cells is not None else 0

    @property
    def num_faces(self) -> int:
        """면 개수"""
        return len(self.faces) if self.faces is not None else 0

    def get_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """바운딩 박스"""
        min_point = np.min(self.vertices, axis=0)
        max_point = np.max(self.vertices, axis=0)
        return min_point, max_point


@dataclass
class TimeStepData:
    """
    타임스텝 데이터

    특정 시간 단계의 시뮬레이션 결과.
    """

    time: float
    step: int
    fields: Dict[str, FieldData] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_field(self, field: FieldData) -> None:
        """필드 추가"""
        self.fields[field.name] = field

    def get_field(self, name: str) -> Optional[FieldData]:
        """필드 조회"""
        return self.fields.get(name)

    def has_field(self, name: str) -> bool:
        """필드 존재 확인"""
        return name in self.fields

    def list_fields(self) -> List[str]:
        """필드 목록"""
        return list(self.fields.keys())


@dataclass
class SimulationResult:
    """
    시뮬레이션 결과

    전체 시뮬레이션 결과 데이터 컨테이너.
    """

    name: str
    simulation_type: str  # "CFD", "FEA", "Particle" 등
    mesh: MeshData
    timesteps: List[TimeStepData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_file: Optional[Path] = None

    def add_timestep(self, timestep: TimeStepData) -> None:
        """타임스텝 추가"""
        self.timesteps.append(timestep)

    def get_timestep(self, step: int) -> Optional[TimeStepData]:
        """타임스텝 조회 (step index)"""
        for ts in self.timesteps:
            if ts.step == step:
                return ts
        return None

    def get_timestep_by_time(self, time: float, tolerance: float = 1e-6) -> Optional[TimeStepData]:
        """타임스텝 조회 (time value)"""
        for ts in self.timesteps:
            if abs(ts.time - time) < tolerance:
                return ts
        return None

    @property
    def num_timesteps(self) -> int:
        """타임스텝 개수"""
        return len(self.timesteps)

    @property
    def time_range(self) -> tuple[float, float]:
        """시간 범위"""
        if not self.timesteps:
            return (0.0, 0.0)
        times = [ts.time for ts in self.timesteps]
        return (min(times), max(times))

    def list_all_fields(self) -> List[str]:
        """모든 타임스텝의 필드 목록 (중복 제거)"""
        all_fields = set()
        for ts in self.timesteps:
            all_fields.update(ts.list_fields())
        return sorted(all_fields)

    def get_field_over_time(self, field_name: str) -> List[tuple[float, FieldData]]:
        """시간에 따른 필드 데이터"""
        result = []
        for ts in self.timesteps:
            field = ts.get_field(field_name)
            if field:
                result.append((ts.time, field))
        return result


@dataclass
class SimulationMetrics:
    """
    시뮬레이션 메트릭

    시뮬레이션 결과의 주요 메트릭 및 통계.
    """

    result_name: str
    timestep: int
    time: float
    field_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    computed_at: datetime = field(default_factory=datetime.utcnow)

    def add_field_stats(
        self,
        field_name: str,
        min_val: float,
        max_val: float,
        mean_val: float,
        std_val: float,
    ) -> None:
        """필드 통계 추가"""
        self.field_statistics[field_name] = {
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "std": std_val,
        }

    def get_field_stats(self, field_name: str) -> Optional[Dict[str, float]]:
        """필드 통계 조회"""
        return self.field_statistics.get(field_name)
