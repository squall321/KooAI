"""
시뮬레이션 결과 관련 Use Cases

시뮬레이션 결과 업로드, 조회, 분석 등의 비즈니스 로직.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.core.repositories.interfaces import SimulationResultRepository
from src.core.simulation import (
    FieldData,
    ParserRegistry,
    ResultAnalyzer,
    SimulationResult,
    SpatialAnalyzer,
    TimeStepData,
)

from .base import NotFoundError, UseCase, UseCaseError, ValidationError


# ============================================================================
# Upload Simulation Use Case
# ============================================================================


@dataclass
class UploadSimulationRequest:
    """시뮬레이션 업로드 요청"""

    file_path: Path
    name: Optional[str] = None
    simulation_type: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class UploadSimulationResponse:
    """시뮬레이션 업로드 응답"""

    simulation_id: str
    name: str
    simulation_type: str
    num_vertices: int
    num_timesteps: int
    fields: List[str]


class UploadSimulationUseCase(UseCase[UploadSimulationRequest, UploadSimulationResponse]):
    """
    시뮬레이션 결과 업로드

    파일을 파싱하고 저장소에 저장.
    """

    def __init__(
        self,
        parser_registry: ParserRegistry,
        repository: SimulationResultRepository,
    ):
        self.parser_registry = parser_registry
        self.repository = repository

    def execute(self, request: UploadSimulationRequest) -> UploadSimulationResponse:
        """시뮬레이션 업로드 실행"""
        # 파일 존재 확인
        if not request.file_path.exists():
            raise ValidationError(f"File not found: {request.file_path}")

        # 파일 파싱
        try:
            result = self.parser_registry.parse(request.file_path)
        except Exception as e:
            raise UseCaseError(f"Failed to parse file: {str(e)}")

        # 이름 설정
        if request.name:
            result.name = request.name

        # 시뮬레이션 타입 설정
        if request.simulation_type:
            result.simulation_type = request.simulation_type

        # 메타데이터 추가
        if request.metadata:
            result.metadata.update(request.metadata)

        # 저장
        saved_result = self.repository.add(result)

        return UploadSimulationResponse(
            simulation_id=saved_result.id,
            name=saved_result.name,
            simulation_type=saved_result.simulation_type,
            num_vertices=saved_result.mesh.num_vertices,
            num_timesteps=saved_result.num_timesteps,
            fields=saved_result.list_all_fields(),
        )


# ============================================================================
# Get Simulation Use Case
# ============================================================================


@dataclass
class GetSimulationRequest:
    """시뮬레이션 조회 요청"""

    simulation_id: str


@dataclass
class GetSimulationResponse:
    """시뮬레이션 조회 응답"""

    simulation_id: str
    name: str
    simulation_type: str
    num_vertices: int
    num_timesteps: int
    time_range: tuple
    fields: List[str]
    metadata: Dict


class GetSimulationUseCase(UseCase[GetSimulationRequest, GetSimulationResponse]):
    """
    시뮬레이션 결과 조회

    ID로 시뮬레이션 결과를 조회.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

    def execute(self, request: GetSimulationRequest) -> GetSimulationResponse:
        """시뮬레이션 조회 실행"""
        result = self.repository.get_by_id(request.simulation_id)

        if not result:
            raise NotFoundError(f"Simulation not found: {request.simulation_id}")

        return GetSimulationResponse(
            simulation_id=result.id,
            name=result.name,
            simulation_type=result.simulation_type,
            num_vertices=result.mesh.num_vertices,
            num_timesteps=result.num_timesteps,
            time_range=result.time_range,
            fields=result.list_all_fields(),
            metadata=result.metadata,
        )


# ============================================================================
# Analyze Field Use Case
# ============================================================================


@dataclass
class AnalyzeFieldRequest:
    """필드 분석 요청"""

    simulation_id: str
    timestep: int
    field_name: str
    compute_extremes: bool = False
    n_extremes: int = 10
    detect_outliers: bool = False
    outlier_threshold: float = 3.0
    compute_histogram: bool = False
    histogram_bins: int = 50


@dataclass
class AnalyzeFieldResponse:
    """필드 분석 응답"""

    field_name: str
    field_type: str
    statistics: Dict[str, float]
    extremes: Optional[Dict[str, List[tuple]]] = None
    outliers: Optional[List[int]] = None
    histogram: Optional[Dict] = None


class AnalyzeFieldUseCase(UseCase[AnalyzeFieldRequest, AnalyzeFieldResponse]):
    """
    필드 데이터 분석

    통계, 극값, 이상치, 히스토그램 등 분석.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

    def execute(self, request: AnalyzeFieldRequest) -> AnalyzeFieldResponse:
        """필드 분석 실행"""
        # 시뮬레이션 조회
        result = self.repository.get_by_id(request.simulation_id)
        if not result:
            raise NotFoundError(f"Simulation not found: {request.simulation_id}")

        # 타임스텝 조회
        timestep = result.get_timestep(request.timestep)
        if not timestep:
            raise NotFoundError(
                f"Timestep {request.timestep} not found in simulation {request.simulation_id}"
            )

        # 필드 조회
        field = timestep.get_field(request.field_name)
        if not field:
            raise NotFoundError(
                f"Field {request.field_name} not found in timestep {request.timestep}"
            )

        # 기본 통계
        statistics = ResultAnalyzer.compute_field_statistics(field)

        # 극값
        extremes = None
        if request.compute_extremes:
            max_indices, min_indices = ResultAnalyzer.find_extreme_values(
                field, n_extremes=request.n_extremes
            )

            # 인덱스와 값 반환
            if field.field_type.value == "scalar":
                max_values = [(int(idx), float(field.data[idx])) for idx in max_indices]
                min_values = [(int(idx), float(field.data[idx])) for idx in min_indices]
            else:
                # 벡터/텐서는 크기 반환
                max_values = [
                    (int(idx), float(np.linalg.norm(field.data[idx])))
                    for idx in max_indices
                ]
                min_values = [
                    (int(idx), float(np.linalg.norm(field.data[idx])))
                    for idx in min_indices
                ]

            extremes = {"max": max_values, "min": min_values}

        # 이상치
        outliers = None
        if request.detect_outliers:
            outlier_indices = ResultAnalyzer.detect_outliers(
                field, threshold=request.outlier_threshold
            )
            outliers = [int(idx) for idx in outlier_indices]

        # 히스토그램
        histogram = None
        if request.compute_histogram:
            hist, edges = ResultAnalyzer.compute_field_histogram(
                field, bins=request.histogram_bins
            )
            histogram = {
                "counts": hist.tolist(),
                "edges": edges.tolist(),
            }

        return AnalyzeFieldResponse(
            field_name=field.name,
            field_type=field.field_type.value,
            statistics=statistics,
            extremes=extremes,
            outliers=outliers,
            histogram=histogram,
        )


# ============================================================================
# Compare Timesteps Use Case
# ============================================================================


@dataclass
class CompareTimestepsRequest:
    """타임스텝 비교 요청"""

    simulation_id: str
    timestep1: int
    timestep2: int
    field_name: str


@dataclass
class CompareTimestepsResponse:
    """타임스텝 비교 응답"""

    field_name: str
    timestep1: int
    timestep2: int
    time1: float
    time2: float
    comparison_metrics: Dict[str, float]


class CompareTimestepsUseCase(
    UseCase[CompareTimestepsRequest, CompareTimestepsResponse]
):
    """
    타임스텝 간 비교

    두 타임스텝의 필드를 비교하여 차이 분석.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

    def execute(self, request: CompareTimestepsRequest) -> CompareTimestepsResponse:
        """타임스텝 비교 실행"""
        # 시뮬레이션 조회
        result = self.repository.get_by_id(request.simulation_id)
        if not result:
            raise NotFoundError(f"Simulation not found: {request.simulation_id}")

        # 타임스텝 조회
        ts1 = result.get_timestep(request.timestep1)
        ts2 = result.get_timestep(request.timestep2)

        if not ts1:
            raise NotFoundError(f"Timestep {request.timestep1} not found")
        if not ts2:
            raise NotFoundError(f"Timestep {request.timestep2} not found")

        # 비교
        try:
            metrics = ResultAnalyzer.compare_timesteps(ts1, ts2, request.field_name)
        except ValueError as e:
            raise ValidationError(str(e))

        return CompareTimestepsResponse(
            field_name=request.field_name,
            timestep1=ts1.step,
            timestep2=ts2.step,
            time1=ts1.time,
            time2=ts2.time,
            comparison_metrics=metrics,
        )


# ============================================================================
# Compute Convergence Use Case
# ============================================================================


@dataclass
class ComputeConvergenceRequest:
    """수렴성 계산 요청"""

    simulation_id: str
    field_name: str


@dataclass
class ComputeConvergenceResponse:
    """수렴성 계산 응답"""

    field_name: str
    convergence_data: List[Dict[str, float]]


class ComputeConvergenceUseCase(
    UseCase[ComputeConvergenceRequest, ComputeConvergenceResponse]
):
    """
    수렴성 분석

    시간에 따른 필드 변화율을 계산하여 수렴성 분석.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

    def execute(self, request: ComputeConvergenceRequest) -> ComputeConvergenceResponse:
        """수렴성 계산 실행"""
        # 시뮬레이션 조회
        result = self.repository.get_by_id(request.simulation_id)
        if not result:
            raise NotFoundError(f"Simulation not found: {request.simulation_id}")

        # 수렴성 계산
        convergence = ResultAnalyzer.compute_convergence_metrics(
            result, request.field_name
        )

        return ComputeConvergenceResponse(
            field_name=request.field_name, convergence_data=convergence
        )


# ============================================================================
# Spatial Analysis Use Case
# ============================================================================


@dataclass
class SpatialAnalysisRequest:
    """공간 분석 요청"""

    simulation_id: str
    timestep: int
    field_name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class SpatialAnalysisResponse:
    """공간 분석 응답"""

    field_name: str
    region_size: int
    region_statistics: Dict[str, float]


class SpatialAnalysisUseCase(UseCase[SpatialAnalysisRequest, SpatialAnalysisResponse]):
    """
    공간 영역 분석

    특정 값 범위의 영역을 찾고 통계 계산.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

    def execute(self, request: SpatialAnalysisRequest) -> SpatialAnalysisResponse:
        """공간 분석 실행"""
        # 시뮬레이션 조회
        result = self.repository.get_by_id(request.simulation_id)
        if not result:
            raise NotFoundError(f"Simulation not found: {request.simulation_id}")

        # 타임스텝 조회
        timestep = result.get_timestep(request.timestep)
        if not timestep:
            raise NotFoundError(f"Timestep {request.timestep} not found")

        # 필드 조회
        field = timestep.get_field(request.field_name)
        if not field:
            raise NotFoundError(f"Field {request.field_name} not found")

        # 영역 찾기
        region_mask = SpatialAnalyzer.find_region_by_value(
            field, min_value=request.min_value, max_value=request.max_value
        )

        # 영역 통계
        stats = SpatialAnalyzer.compute_region_statistics(
            field, result.mesh.vertices, region_mask
        )

        return SpatialAnalysisResponse(
            field_name=field.name,
            region_size=int(stats["count"]),
            region_statistics=stats,
        )


# ============================================================================
# List Simulations Use Case
# ============================================================================


@dataclass
class ListSimulationsRequest:
    """시뮬레이션 목록 조회 요청"""

    skip: int = 0
    limit: int = 100


@dataclass
class SimulationSummary:
    """시뮬레이션 요약"""

    simulation_id: str
    name: str
    simulation_type: str
    num_timesteps: int
    created_at: str


@dataclass
class ListSimulationsResponse:
    """시뮬레이션 목록 조회 응답"""

    simulations: List[SimulationSummary]
    total: int


class ListSimulationsUseCase(UseCase[ListSimulationsRequest, ListSimulationsResponse]):
    """
    시뮬레이션 목록 조회

    저장된 모든 시뮬레이션 목록을 페이지네이션으로 조회.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

    def execute(self, request: ListSimulationsRequest) -> ListSimulationsResponse:
        """목록 조회 실행"""
        # 전체 개수
        total = self.repository.count()

        # 페이지네이션
        results = self.repository.list_all(skip=request.skip, limit=request.limit)

        # 요약 생성
        summaries = [
            SimulationSummary(
                simulation_id=r.id,
                name=r.name,
                simulation_type=r.simulation_type,
                num_timesteps=r.num_timesteps,
                created_at=r.created_at.isoformat(),
            )
            for r in results
        ]

        return ListSimulationsResponse(simulations=summaries, total=total)
