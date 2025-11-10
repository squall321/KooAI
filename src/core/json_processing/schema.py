"""
JSON 스키마 정의

시뮬레이션 결과 JSON 파일의 스키마를 Pydantic 모델로 정의합니다.
"""

from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class CoordinateSystem(str, Enum):
    """좌표계 타입"""

    CARTESIAN = "cartesian"
    CYLINDRICAL = "cylindrical"
    SPHERICAL = "spherical"


class UnitSystem(str, Enum):
    """단위계 타입"""

    SI = "si"
    CGS = "cgs"
    IMPERIAL = "imperial"
    CUSTOM = "custom"


class DataType(str, Enum):
    """데이터 타입"""

    SCALAR = "scalar"
    VECTOR = "vector"
    TENSOR = "tensor"


class MeshType(str, Enum):
    """메시 타입"""

    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"
    HYBRID = "hybrid"


# ============================================================================
# 메타데이터 스키마
# ============================================================================


class SimulationMetadata(BaseModel):
    """시뮬레이션 메타데이터"""

    model_config = ConfigDict(frozen=False, extra="allow")

    name: str = Field(..., description="시뮬레이션 이름")
    version: str = Field("1.0.0", description="스키마 버전")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="생성 시각")
    solver: str = Field(..., description="솔버 이름 (예: OpenFOAM, ANSYS)")
    solver_version: Optional[str] = Field(None, description="솔버 버전")
    description: Optional[str] = Field(None, description="설명")
    tags: List[str] = Field(default_factory=list, description="태그")

    coordinate_system: CoordinateSystem = Field(CoordinateSystem.CARTESIAN, description="좌표계")
    unit_system: UnitSystem = Field(UnitSystem.SI, description="단위계")

    # 사용자 정의 메타데이터
    custom_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="사용자 정의 메타데이터"
    )


# ============================================================================
# 메시 스키마
# ============================================================================


class MeshInfo(BaseModel):
    """메시 정보"""

    model_config = ConfigDict(frozen=False)

    mesh_type: MeshType = Field(..., description="메시 타입")
    num_vertices: int = Field(..., ge=0, description="정점 개수")
    num_cells: int = Field(..., ge=0, description="셀 개수")
    num_faces: Optional[int] = Field(None, ge=0, description="면 개수")

    dimensions: int = Field(..., ge=2, le=3, description="차원 (2D or 3D)")

    # 경계 조건
    boundary_conditions: Dict[str, Any] = Field(default_factory=dict, description="경계 조건")

    @field_validator("num_vertices", "num_cells")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Mesh counts must be non-negative")
        return v


class MeshData(BaseModel):
    """메시 데이터"""

    model_config = ConfigDict(frozen=False)

    info: MeshInfo = Field(..., description="메시 정보")

    # 정점 좌표 (flatten array or nested)
    vertices: Union[List[float], List[List[float]]] = Field(..., description="정점 좌표 배열")

    # 셀 연결성 (각 셀의 정점 인덱스)
    cells: Union[List[int], List[List[int]]] = Field(..., description="셀 연결성")

    # 면 정보 (선택적)
    faces: Optional[Union[List[int], List[List[int]]]] = Field(None, description="면 정보")


# ============================================================================
# 필드 데이터 스키마
# ============================================================================


class FieldMetadata(BaseModel):
    """필드 메타데이터"""

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., description="필드 이름 (예: temperature, pressure)")
    data_type: DataType = Field(..., description="데이터 타입")
    unit: str = Field(..., description="단위 (예: K, Pa, m/s)")

    components: Optional[int] = Field(None, ge=1, description="벡터/텐서 컴포넌트 개수")
    component_names: Optional[List[str]] = Field(None, description="컴포넌트 이름")

    min_value: Optional[float] = Field(None, description="최소값")
    max_value: Optional[float] = Field(None, description="최대값")
    mean_value: Optional[float] = Field(None, description="평균값")

    location: Literal["vertex", "cell", "face"] = Field("vertex", description="데이터 위치")


class FieldData(BaseModel):
    """필드 데이터"""

    model_config = ConfigDict(frozen=False)

    metadata: FieldMetadata = Field(..., description="필드 메타데이터")
    values: Union[List[float], List[List[float]]] = Field(..., description="필드 값")

    # 데이터 압축 정보 (VAE로 압축된 경우)
    compressed: bool = Field(False, description="압축 여부")
    compression_method: Optional[str] = Field(None, description="압축 방법")
    compression_params: Optional[Dict[str, Any]] = Field(None, description="압축 파라미터")


# ============================================================================
# 컨투어 데이터 스키마
# ============================================================================


class ContourLevel(BaseModel):
    """컨투어 레벨"""

    model_config = ConfigDict(frozen=False)

    value: float = Field(..., description="컨투어 값")
    num_points: int = Field(..., ge=0, description="포인트 개수")
    points: Union[List[float], List[List[float]]] = Field(..., description="포인트 좌표")
    is_closed: bool = Field(True, description="닫힌 컨투어 여부")


class ContourData(BaseModel):
    """컨투어 데이터"""

    model_config = ConfigDict(frozen=False)

    field_name: str = Field(..., description="필드 이름")
    unit: str = Field(..., description="단위")
    levels: List[ContourLevel] = Field(..., description="컨투어 레벨 목록")

    # VAE 압축 정보
    compressed: bool = Field(False, description="압축 여부")
    latent_representation: Optional[List[float]] = Field(None, description="VAE 잠재 벡터")


# ============================================================================
# 시간 단계 데이터 스키마
# ============================================================================


class TimeStep(BaseModel):
    """시간 단계 데이터"""

    model_config = ConfigDict(frozen=False)

    step: int = Field(..., ge=0, description="시간 단계 번호")
    time: float = Field(..., description="물리적 시간")
    time_unit: str = Field("s", description="시간 단위")

    fields: Dict[str, FieldData] = Field(
        default_factory=dict, description="시간 단계별 필드 데이터"
    )
    contours: Dict[str, ContourData] = Field(
        default_factory=dict, description="시간 단계별 컨투어 데이터"
    )


# ============================================================================
# 전체 시뮬레이션 결과 스키마
# ============================================================================


class SimulationResult(BaseModel):
    """전체 시뮬레이션 결과"""

    model_config = ConfigDict(frozen=False, extra="allow")

    # 메타데이터
    metadata: SimulationMetadata = Field(..., description="시뮬레이션 메타데이터")

    # 메시 데이터 (정적 - 시간 불변)
    mesh: MeshData = Field(..., description="메시 데이터")

    # 정상 상태 시뮬레이션의 경우
    steady_state: bool = Field(False, description="정상 상태 여부")

    # 정상 상태인 경우 단일 필드/컨투어 데이터
    fields: Optional[Dict[str, FieldData]] = Field(None, description="필드 데이터")
    contours: Optional[Dict[str, ContourData]] = Field(None, description="컨투어 데이터")

    # 비정상 상태인 경우 시간 단계별 데이터
    time_steps: Optional[List[TimeStep]] = Field(None, description="시간 단계 데이터")

    @field_validator("time_steps")
    @classmethod
    def validate_time_steps(cls, v: Optional[List[TimeStep]], info: Any) -> Optional[List[TimeStep]]:
        """비정상 상태의 경우 time_steps 필수"""
        steady_state = info.data.get("steady_state", False)
        if not steady_state and not v:
            raise ValueError(
                "time_steps is required for transient simulations (steady_state=False)"
            )
        return v


# ============================================================================
# 스키마 레지스트리
# ============================================================================


class SchemaRegistry:
    """JSON 스키마 레지스트리

    동적으로 스키마를 등록하고 검증할 수 있습니다.
    """

    def __init__(self) -> None:
        self._schemas: Dict[str, type[BaseModel]] = {
            "simulation_result": SimulationResult,
            "simulation_metadata": SimulationMetadata,
            "mesh_data": MeshData,
            "field_data": FieldData,
            "contour_data": ContourData,
            "time_step": TimeStep,
        }

    def register_schema(self, name: str, schema: type[BaseModel]) -> None:
        """
        새로운 스키마 등록

        Args:
            name: 스키마 이름
            schema: Pydantic 모델 클래스
        """
        if not issubclass(schema, BaseModel):
            raise TypeError("Schema must be a Pydantic BaseModel subclass")
        self._schemas[name] = schema

    def get_schema(self, name: str) -> type[BaseModel]:
        """
        스키마 조회

        Args:
            name: 스키마 이름

        Returns:
            Pydantic 모델 클래스

        Raises:
            KeyError: 스키마가 등록되지 않은 경우
        """
        if name not in self._schemas:
            raise KeyError(f"Schema '{name}' not found in registry")
        return self._schemas[name]

    def list_schemas(self) -> List[str]:
        """등록된 스키마 목록 반환"""
        return list(self._schemas.keys())

    def validate(self, name: str, data: Dict[str, Any]) -> BaseModel:
        """
        데이터 검증

        Args:
            name: 스키마 이름
            data: 검증할 데이터

        Returns:
            검증된 Pydantic 모델 인스턴스

        Raises:
            KeyError: 스키마가 등록되지 않은 경우
            ValidationError: 데이터가 스키마에 맞지 않는 경우
        """
        schema = self.get_schema(name)
        return schema.model_validate(data)

    def unregister_schema(self, name: str) -> None:
        """
        스키마 등록 해제

        Args:
            name: 스키마 이름
        """
        if name in self._schemas:
            del self._schemas[name]


# 전역 스키마 레지스트리 인스턴스
schema_registry = SchemaRegistry()
