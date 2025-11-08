"""
도메인 엔티티

비즈니스 핵심 개념을 표현하는 엔티티들.
엔티티는 식별자(ID)를 가지며, 생명주기 동안 상태가 변할 수 있습니다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum


class SimulationStatus(str, Enum):
    """시뮬레이션 상태"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisStatus(str, Enum):
    """분석 상태"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SimulationResult:
    """
    시뮬레이션 결과 엔티티

    시뮬레이션 실행 결과를 나타내는 핵심 도메인 객체.
    시뮬레이션의 메타데이터, 파라미터, 상태를 관리합니다.
    """

    name: str
    type: str  # CFD, FEA, Thermal, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    status: SimulationStatus = field(default=SimulationStatus.PENDING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        self.validate()

    def validate(self) -> None:
        """엔티티 유효성 검증"""
        if not self.name or not self.name.strip():
            raise ValueError("Simulation name cannot be empty")

        if not self.type or not self.type.strip():
            raise ValueError("Simulation type cannot be empty")

        if len(self.name) > 255:
            raise ValueError("Simulation name too long (max 255 characters)")

    def mark_as_processing(self) -> None:
        """시뮬레이션을 처리 중으로 표시"""
        if self.status != SimulationStatus.PENDING:
            raise ValueError(f"Cannot mark as processing: current status is {self.status}")
        self.status = SimulationStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_as_completed(self) -> None:
        """시뮬레이션을 완료로 표시"""
        if self.status != SimulationStatus.PROCESSING:
            raise ValueError(f"Cannot mark as completed: current status is {self.status}")
        self.status = SimulationStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """시뮬레이션을 실패로 표시"""
        self.status = SimulationStatus.FAILED
        self.metadata["error"] = error_message
        self.metadata["failed_at"] = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """시뮬레이션 취소"""
        if self.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]:
            raise ValueError(f"Cannot cancel: simulation is already {self.status}")
        self.status = SimulationStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """태그 추가"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """태그 제거"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: Any) -> None:
        """메타데이터 업데이트"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """완료 여부 확인"""
        return self.status == SimulationStatus.COMPLETED

    def is_failed(self) -> bool:
        """실패 여부 확인"""
        return self.status == SimulationStatus.FAILED

    def can_be_analyzed(self) -> bool:
        """분석 가능 여부 확인"""
        return self.status == SimulationStatus.COMPLETED


@dataclass
class Dataset:
    """
    데이터셋 엔티티

    시뮬레이션 결과 데이터를 나타냅니다.
    다양한 형식(메시, 커브, 컨투어 등)의 데이터를 추상화합니다.
    """

    simulation_id: UUID
    data_type: str  # mesh, contour, curve, structured, etc.
    data_format: str  # json, vtk, csv, binary, etc.
    storage_path: str
    id: UUID = field(default_factory=uuid4)
    size_bytes: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        self.validate()

    def validate(self) -> None:
        """엔티티 유효성 검증"""
        if not self.data_type:
            raise ValueError("Data type cannot be empty")

        if not self.storage_path:
            raise ValueError("Storage path cannot be empty")

        if self.size_bytes < 0:
            raise ValueError("Size cannot be negative")

    def update_checksum(self, checksum: str) -> None:
        """체크섬 업데이트"""
        self.checksum = checksum

    def update_size(self, size_bytes: int) -> None:
        """크기 업데이트"""
        if size_bytes < 0:
            raise ValueError("Size cannot be negative")
        self.size_bytes = size_bytes


@dataclass
class Analysis:
    """
    분석 작업 엔티티

    시뮬레이션 결과에 대한 분석 작업을 나타냅니다.
    """

    simulation_id: UUID
    analysis_type: str  # statistical, comparison, anomaly_detection, etc.
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    status: AnalysisStatus = field(default=AnalysisStatus.PENDING)
    results: Dict[str, Any] = field(default_factory=dict)
    model_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        self.validate()

    def validate(self) -> None:
        """엔티티 유효성 검증"""
        if not self.analysis_type:
            raise ValueError("Analysis type cannot be empty")

    def start(self) -> None:
        """분석 시작"""
        if self.status != AnalysisStatus.PENDING:
            raise ValueError(f"Cannot start: current status is {self.status}")

        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, results: Dict[str, Any]) -> None:
        """분석 완료"""
        if self.status != AnalysisStatus.RUNNING:
            raise ValueError(f"Cannot complete: current status is {self.status}")

        self.status = AnalysisStatus.COMPLETED
        self.results = results
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """분석 실패"""
        self.status = AnalysisStatus.FAILED
        self.results = {"error": error_message}
        self.completed_at = datetime.utcnow()

    def get_duration_seconds(self) -> Optional[float]:
        """분석 소요 시간 (초) 반환"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None


@dataclass
class AIModel:
    """
    AI 모델 엔티티

    학습된 AI/ML 모델의 메타데이터를 관리합니다.
    """

    name: str
    version: str
    model_type: str  # vae, transformer, cnn, etc.
    id: UUID = field(default_factory=uuid4)
    architecture: Dict[str, Any] = field(default_factory=dict)
    storage_path: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    trained_by: Optional[UUID] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        self.validate()

    def validate(self) -> None:
        """엔티티 유효성 검증"""
        if not self.name or not self.name.strip():
            raise ValueError("Model name cannot be empty")

        if not self.version or not self.version.strip():
            raise ValueError("Model version cannot be empty")

        if not self.model_type:
            raise ValueError("Model type cannot be empty")

    def update_performance_metrics(self, metrics: Dict[str, float]) -> None:
        """성능 메트릭 업데이트"""
        self.performance_metrics.update(metrics)

    def get_metric(self, metric_name: str) -> Optional[float]:
        """특정 메트릭 조회"""
        return self.performance_metrics.get(metric_name)

    def get_full_name(self) -> str:
        """전체 모델 이름 (이름:버전)"""
        return f"{self.name}:{self.version}"
