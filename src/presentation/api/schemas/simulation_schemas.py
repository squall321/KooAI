"""
시뮬레이션 API 스키마

FastAPI Pydantic 스키마 정의.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Upload Simulation
# ============================================================================


class UploadSimulationRequest(BaseModel):
    """시뮬레이션 업로드 요청"""

    name: Optional[str] = Field(None, description="시뮬레이션 이름")
    simulation_type: Optional[str] = Field(None, description="시뮬레이션 타입")
    metadata: Optional[Dict] = Field(default_factory=dict, description="메타데이터")


class UploadSimulationResponse(BaseModel):
    """시뮬레이션 업로드 응답"""

    simulation_id: str = Field(..., description="시뮬레이션 ID")
    name: str = Field(..., description="시뮬레이션 이름")
    simulation_type: str = Field(..., description="시뮬레이션 타입")
    num_vertices: int = Field(..., description="꼭짓점 개수")
    num_timesteps: int = Field(..., description="타임스텝 개수")
    fields: List[str] = Field(..., description="필드 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "CFD Simulation 1",
                "simulation_type": "CFD",
                "num_vertices": 1000,
                "num_timesteps": 10,
                "fields": ["temperature", "pressure", "velocity"],
            }
        }


# ============================================================================
# Get Simulation
# ============================================================================


class SimulationInfoResponse(BaseModel):
    """시뮬레이션 정보 응답"""

    simulation_id: str = Field(..., description="시뮬레이션 ID")
    name: str = Field(..., description="시뮬레이션 이름")
    simulation_type: str = Field(..., description="시뮬레이션 타입")
    num_vertices: int = Field(..., description="꼭짓점 개수")
    num_timesteps: int = Field(..., description="타임스텝 개수")
    time_range: tuple = Field(..., description="시간 범위 (시작, 종료)")
    fields: List[str] = Field(..., description="필드 목록")
    metadata: Dict = Field(default_factory=dict, description="메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "CFD Simulation 1",
                "simulation_type": "CFD",
                "num_vertices": 1000,
                "num_timesteps": 10,
                "time_range": [0.0, 1.0],
                "fields": ["temperature", "pressure"],
                "metadata": {"solver": "OpenFOAM"},
            }
        }


# ============================================================================
# Analyze Field
# ============================================================================


class AnalyzeFieldRequest(BaseModel):
    """필드 분석 요청"""

    timestep: int = Field(..., description="타임스텝 번호", ge=0)
    field_name: str = Field(..., description="필드 이름")
    compute_extremes: bool = Field(False, description="극값 계산 여부")
    n_extremes: int = Field(10, description="극값 개수", ge=1, le=100)
    detect_outliers: bool = Field(False, description="이상치 탐지 여부")
    outlier_threshold: float = Field(3.0, description="이상치 임계값", gt=0.0)
    compute_histogram: bool = Field(False, description="히스토그램 계산 여부")
    histogram_bins: int = Field(50, description="히스토그램 빈 개수", ge=10, le=200)

    class Config:
        json_schema_extra = {
            "example": {
                "timestep": 0,
                "field_name": "temperature",
                "compute_extremes": True,
                "n_extremes": 10,
                "detect_outliers": True,
                "outlier_threshold": 3.0,
            }
        }


class AnalyzeFieldResponse(BaseModel):
    """필드 분석 응답"""

    field_name: str = Field(..., description="필드 이름")
    field_type: str = Field(..., description="필드 타입 (scalar/vector/tensor)")
    statistics: Dict[str, float] = Field(..., description="통계 정보")
    extremes: Optional[Dict] = Field(None, description="극값 정보")
    outliers: Optional[List[int]] = Field(None, description="이상치 인덱스")
    histogram: Optional[Dict] = Field(None, description="히스토그램 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "temperature",
                "field_type": "scalar",
                "statistics": {
                    "min": 300.0,
                    "max": 500.0,
                    "mean": 400.0,
                    "std": 50.0,
                },
                "extremes": {
                    "max": [[0, 500.0], [10, 499.0]],
                    "min": [[5, 300.0], [15, 301.0]],
                },
            }
        }


# ============================================================================
# Compare Timesteps
# ============================================================================


class CompareTimestepsRequest(BaseModel):
    """타임스텝 비교 요청"""

    timestep1: int = Field(..., description="첫 번째 타임스텝", ge=0)
    timestep2: int = Field(..., description="두 번째 타임스텝", ge=0)
    field_name: str = Field(..., description="필드 이름")


class CompareTimestepsResponse(BaseModel):
    """타임스텝 비교 응답"""

    field_name: str = Field(..., description="필드 이름")
    timestep1: int = Field(..., description="첫 번째 타임스텝")
    timestep2: int = Field(..., description="두 번째 타임스텝")
    time1: float = Field(..., description="첫 번째 시간")
    time2: float = Field(..., description="두 번째 시간")
    comparison_metrics: Dict[str, float] = Field(..., description="비교 메트릭")

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "temperature",
                "timestep1": 0,
                "timestep2": 1,
                "time1": 0.0,
                "time2": 0.1,
                "comparison_metrics": {
                    "max_diff": 10.0,
                    "mean_diff": 2.0,
                    "rms_diff": 3.5,
                    "relative_change": 0.05,
                },
            }
        }


# ============================================================================
# Convergence Analysis
# ============================================================================


class ComputeConvergenceRequest(BaseModel):
    """수렴성 분석 요청"""

    field_name: str = Field(..., description="필드 이름")


class ConvergenceDataPoint(BaseModel):
    """수렴성 데이터 포인트"""

    timestep: int = Field(..., description="타임스텝")
    time: float = Field(..., description="시간")
    rms_change: float = Field(..., description="RMS 변화율")
    relative_change: float = Field(..., description="상대 변화율")


class ComputeConvergenceResponse(BaseModel):
    """수렴성 분석 응답"""

    field_name: str = Field(..., description="필드 이름")
    convergence_data: List[ConvergenceDataPoint] = Field(
        ..., description="수렴성 데이터"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "temperature",
                "convergence_data": [
                    {
                        "timestep": 1,
                        "time": 0.1,
                        "rms_change": 5.0,
                        "relative_change": 0.1,
                    },
                    {
                        "timestep": 2,
                        "time": 0.2,
                        "rms_change": 2.0,
                        "relative_change": 0.04,
                    },
                ],
            }
        }


# ============================================================================
# Spatial Analysis
# ============================================================================


class SpatialAnalysisRequest(BaseModel):
    """공간 분석 요청"""

    timestep: int = Field(..., description="타임스텝", ge=0)
    field_name: str = Field(..., description="필드 이름")
    min_value: Optional[float] = Field(None, description="최솟값 (범위)")
    max_value: Optional[float] = Field(None, description="최댓값 (범위)")


class SpatialAnalysisResponse(BaseModel):
    """공간 분석 응답"""

    field_name: str = Field(..., description="필드 이름")
    region_size: int = Field(..., description="영역 크기 (포인트 개수)")
    region_statistics: Dict[str, float] = Field(..., description="영역 통계")

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "temperature",
                "region_size": 150,
                "region_statistics": {
                    "min": 450.0,
                    "max": 500.0,
                    "mean": 475.0,
                    "std": 15.0,
                    "count": 150,
                },
            }
        }


# ============================================================================
# List Simulations
# ============================================================================


class ListSimulationsRequest(BaseModel):
    """시뮬레이션 목록 요청"""

    page: int = Field(1, description="페이지 번호", ge=1)
    page_size: int = Field(20, description="페이지 크기", ge=1, le=100)


class SimulationSummary(BaseModel):
    """시뮬레이션 요약"""

    simulation_id: str = Field(..., description="시뮬레이션 ID")
    name: str = Field(..., description="시뮬레이션 이름")
    simulation_type: str = Field(..., description="시뮬레이션 타입")
    num_timesteps: int = Field(..., description="타임스텝 개수")
    created_at: str = Field(..., description="생성 시간 (ISO 형식)")


class ListSimulationsResponse(BaseModel):
    """시뮬레이션 목록 응답"""

    simulations: List[SimulationSummary] = Field(..., description="시뮬레이션 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="전체 페이지 수")

    class Config:
        json_schema_extra = {
            "example": {
                "simulations": [
                    {
                        "simulation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "CFD Simulation 1",
                        "simulation_type": "CFD",
                        "num_timesteps": 10,
                        "created_at": "2025-11-06T12:00:00Z",
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "total_pages": 3,
            }
        }


# ============================================================================
# Error Responses
# ============================================================================


class ErrorResponse(BaseModel):
    """에러 응답"""

    error: str = Field(..., description="에러 타입")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[Dict] = Field(None, description="상세 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "NotFoundError",
                "message": "Simulation not found: abc123",
                "detail": None,
            }
        }


# ============================================================================
# Success Response
# ============================================================================


class SuccessResponse(BaseModel):
    """성공 응답"""

    success: bool = Field(True, description="성공 여부")
    message: str = Field(..., description="메시지")

    class Config:
        json_schema_extra = {"example": {"success": True, "message": "Operation completed successfully"}}
