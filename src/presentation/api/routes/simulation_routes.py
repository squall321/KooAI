"""
시뮬레이션 API 라우트

시뮬레이션 결과 처리 REST API 엔드포인트.
"""

import math
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from src.application.services import SimulationService
from src.application.use_cases import (
    AnalyzeFieldRequest as UseCaseAnalyzeFieldRequest,
)
from src.application.use_cases import (
    CompareTimestepsRequest as UseCaseCompareTimestepsRequest,
)
from src.application.use_cases import (
    ComputeConvergenceRequest as UseCaseComputeConvergenceRequest,
)
from src.application.use_cases import (
    SpatialAnalysisRequest as UseCaseSpatialAnalysisRequest,
)

from ..dependencies import get_simulation_service
from ..schemas.simulation_schemas import (
    AnalyzeFieldRequest,
    AnalyzeFieldResponse,
    CompareTimestepsRequest,
    CompareTimestepsResponse,
    ComputeConvergenceResponse,
    ConvergenceDataPoint,
    ListSimulationsResponse,
    SimulationInfoResponse,
    SimulationSummary,
    SpatialAnalysisRequest,
    SpatialAnalysisResponse,
    SuccessResponse,
    UploadSimulationResponse,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


# ============================================================================
# Upload Simulation
# ============================================================================


@router.post(
    "/upload",
    response_model=UploadSimulationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="시뮬레이션 업로드",
    description="시뮬레이션 파일을 업로드하고 파싱합니다.",
)
async def upload_simulation(
    file: UploadFile = File(..., description="시뮬레이션 파일 (CSV, VTK)"),
    name: Optional[str] = Form(None, description="시뮬레이션 이름"),
    simulation_type: Optional[str] = Form(None, description="시뮬레이션 타입"),
    service: SimulationService = Depends(get_simulation_service),
):
    """
    시뮬레이션 파일 업로드

    지원 포맷:
    - CSV (.csv)
    - VTK Legacy ASCII (.vtk)
    """
    # 임시 파일로 저장
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = Path(tmp_file.name)

    try:
        # 업로드 및 분석
        result = service.upload_and_analyze(
            file_path=tmp_file_path,
            name=name or file.filename,
            analyze_all_fields=False,  # 빠른 업로드를 위해 분석 건너뜀
        )

        return UploadSimulationResponse(
            simulation_id=result.simulation_info.simulation_id,
            name=result.simulation_info.name,
            simulation_type=result.simulation_info.simulation_type,
            num_vertices=result.simulation_info.num_vertices,
            num_timesteps=result.simulation_info.num_timesteps,
            fields=result.simulation_info.fields,
        )
    finally:
        # 임시 파일 삭제
        tmp_file_path.unlink()


# ============================================================================
# Get Simulation
# ============================================================================


@router.get(
    "/{simulation_id}",
    response_model=SimulationInfoResponse,
    summary="시뮬레이션 조회",
    description="시뮬레이션 정보를 조회합니다.",
)
async def get_simulation(
    simulation_id: str,
    service: SimulationService = Depends(get_simulation_service),
):
    """시뮬레이션 정보 조회"""
    from src.application.use_cases import GetSimulationRequest

    result = service.get_use_case.execute(GetSimulationRequest(simulation_id=simulation_id))

    return SimulationInfoResponse(
        simulation_id=result.simulation_id,
        name=result.name,
        simulation_type=result.simulation_type,
        num_vertices=result.num_vertices,
        num_timesteps=result.num_timesteps,
        time_range=result.time_range,
        fields=result.fields,
        metadata=result.metadata,
    )


# ============================================================================
# Delete Simulation
# ============================================================================


@router.delete(
    "/{simulation_id}",
    response_model=SuccessResponse,
    summary="시뮬레이션 삭제",
    description="시뮬레이션을 삭제합니다.",
)
async def delete_simulation(
    simulation_id: str,
    service: SimulationService = Depends(get_simulation_service),
):
    """시뮬레이션 삭제"""
    deleted = service.repository.delete(simulation_id)

    if not deleted:
        from src.application.use_cases import NotFoundError

        raise NotFoundError(f"Simulation not found: {simulation_id}")

    return SuccessResponse(success=True, message=f"Simulation {simulation_id} deleted successfully")


# ============================================================================
# List Simulations
# ============================================================================


@router.get(
    "/",
    response_model=ListSimulationsResponse,
    summary="시뮬레이션 목록",
    description="저장된 시뮬레이션 목록을 조회합니다.",
)
async def list_simulations(
    page: int = 1,
    page_size: int = 20,
    service: SimulationService = Depends(get_simulation_service),
):
    """시뮬레이션 목록 조회 (페이지네이션)"""
    result = service.list_simulations(page=page, page_size=page_size)

    # 전체 페이지 수 계산
    total_pages = math.ceil(result.total / page_size) if result.total > 0 else 1

    return ListSimulationsResponse(
        simulations=[
            SimulationSummary(
                simulation_id=sim.simulation_id,
                name=sim.name,
                simulation_type=sim.simulation_type,
                num_timesteps=sim.num_timesteps,
                created_at=sim.created_at,
            )
            for sim in result.simulations
        ],
        total=result.total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ============================================================================
# Analyze Field
# ============================================================================


@router.post(
    "/{simulation_id}/analyze",
    response_model=AnalyzeFieldResponse,
    summary="필드 분석",
    description="시뮬레이션 필드를 분석합니다 (통계, 극값, 이상치, 히스토그램).",
)
async def analyze_field(
    simulation_id: str,
    request: AnalyzeFieldRequest,
    service: SimulationService = Depends(get_simulation_service),
):
    """필드 데이터 분석"""
    result = service.analyze_field_use_case.execute(
        UseCaseAnalyzeFieldRequest(
            simulation_id=simulation_id,
            timestep=request.timestep,
            field_name=request.field_name,
            compute_extremes=request.compute_extremes,
            n_extremes=request.n_extremes,
            detect_outliers=request.detect_outliers,
            outlier_threshold=request.outlier_threshold,
            compute_histogram=request.compute_histogram,
            histogram_bins=request.histogram_bins,
        )
    )

    return AnalyzeFieldResponse(
        field_name=result.field_name,
        field_type=result.field_type,
        statistics=result.statistics,
        extremes=result.extremes,
        outliers=result.outliers,
        histogram=result.histogram,
    )


# ============================================================================
# Compare Timesteps
# ============================================================================


@router.post(
    "/{simulation_id}/compare",
    response_model=CompareTimestepsResponse,
    summary="타임스텝 비교",
    description="두 타임스텝 간의 필드 변화를 비교합니다.",
)
async def compare_timesteps(
    simulation_id: str,
    request: CompareTimestepsRequest,
    service: SimulationService = Depends(get_simulation_service),
):
    """타임스텝 간 비교"""
    result = service.compare_timesteps_use_case.execute(
        UseCaseCompareTimestepsRequest(
            simulation_id=simulation_id,
            timestep1=request.timestep1,
            timestep2=request.timestep2,
            field_name=request.field_name,
        )
    )

    return CompareTimestepsResponse(
        field_name=result.field_name,
        timestep1=result.timestep1,
        timestep2=result.timestep2,
        time1=result.time1,
        time2=result.time2,
        comparison_metrics=result.comparison_metrics,
    )


# ============================================================================
# Compute Convergence
# ============================================================================


@router.post(
    "/{simulation_id}/convergence",
    response_model=ComputeConvergenceResponse,
    summary="수렴성 분석",
    description="시간에 따른 필드 변화율을 계산하여 수렴성을 분석합니다.",
)
async def compute_convergence(
    simulation_id: str,
    field_name: str,
    service: SimulationService = Depends(get_simulation_service),
):
    """수렴성 분석"""
    result = service.compute_convergence_use_case.execute(
        UseCaseComputeConvergenceRequest(simulation_id=simulation_id, field_name=field_name)
    )

    return ComputeConvergenceResponse(
        field_name=result.field_name,
        convergence_data=[
            ConvergenceDataPoint(
                timestep=point["timestep"],
                time=point["time"],
                rms_change=point["rms_change"],
                relative_change=point["relative_change"],
            )
            for point in result.convergence_data
        ],
    )


# ============================================================================
# Spatial Analysis
# ============================================================================


@router.post(
    "/{simulation_id}/spatial",
    response_model=SpatialAnalysisResponse,
    summary="공간 분석",
    description="특정 값 범위의 공간 영역을 분석합니다.",
)
async def spatial_analysis(
    simulation_id: str,
    request: SpatialAnalysisRequest,
    service: SimulationService = Depends(get_simulation_service),
):
    """공간 영역 분석"""
    result = service.spatial_analysis_use_case.execute(
        UseCaseSpatialAnalysisRequest(
            simulation_id=simulation_id,
            timestep=request.timestep,
            field_name=request.field_name,
            min_value=request.min_value,
            max_value=request.max_value,
        )
    )

    return SpatialAnalysisResponse(
        field_name=result.field_name,
        region_size=result.region_size,
        region_statistics=result.region_statistics,
    )
