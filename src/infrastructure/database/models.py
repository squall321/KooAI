"""
SQLAlchemy 데이터베이스 모델

도메인 엔티티를 데이터베이스 테이블로 매핑합니다.
"""

from datetime import datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    BigInteger,
    ForeignKey,
    Enum as SQLEnum,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from src.core.domain.entities import SimulationStatus, AnalysisStatus


class Base(DeclarativeBase):
    """SQLAlchemy Base 클래스"""
    pass


class SimulationModel(Base):
    """
    시뮬레이션 테이블 모델

    도메인 엔티티 SimulationResult를 데이터베이스 테이블로 매핑합니다.
    """

    __tablename__ = "simulations"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # 기본 정보
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 상태
    status: Mapped[str] = mapped_column(
        SQLEnum(SimulationStatus, native_enum=False),
        nullable=False,
        default=SimulationStatus.PENDING,
        index=True,
    )

    # JSON 데이터
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    meta_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    # 태그
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 외래 키
    created_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # 관계
    datasets: Mapped[list["DatasetModel"]] = relationship(
        "DatasetModel", back_populates="simulation", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AnalysisModel"]] = relationship(
        "AnalysisModel", back_populates="simulation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SimulationModel(id={self.id}, name='{self.name}', status={self.status})>"


class DatasetModel(Base):
    """
    데이터셋 테이블 모델

    도메인 엔티티 Dataset을 데이터베이스 테이블로 매핑합니다.
    """

    __tablename__ = "datasets"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # 외래 키
    simulation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True
    )

    # 데이터 정보
    data_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    data_format: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    # 크기 및 체크섬
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # JSON 메타데이터
    meta_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # 관계
    simulation: Mapped["SimulationModel"] = relationship(
        "SimulationModel", back_populates="datasets"
    )

    def __repr__(self) -> str:
        return f"<DatasetModel(id={self.id}, type='{self.data_type}', simulation_id={self.simulation_id})>"


class AnalysisModel(Base):
    """
    분석 테이블 모델

    도메인 엔티티 Analysis를 데이터베이스 테이블로 매핑합니다.
    """

    __tablename__ = "analyses"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # 외래 키
    simulation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True
    )
    model_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_models.id"), nullable=True
    )

    # 분석 정보
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(AnalysisStatus, native_enum=False),
        nullable=False,
        default=AnalysisStatus.PENDING,
        index=True,
    )

    # JSON 데이터
    input_parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    results: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 외래 키
    created_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # 관계
    simulation: Mapped["SimulationModel"] = relationship(
        "SimulationModel", back_populates="analyses"
    )
    model: Mapped[Optional["AIModelModel"]] = relationship("AIModelModel")

    def __repr__(self) -> str:
        return f"<AnalysisModel(id={self.id}, type='{self.analysis_type}', status={self.status})>"


class AIModelModel(Base):
    """
    AI 모델 테이블 모델

    도메인 엔티티 AIModel을 데이터베이스 테이블로 매핑합니다.
    """

    __tablename__ = "ai_models"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # 모델 정보
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON 데이터
    architecture: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    performance_metrics: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    training_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 저장 경로
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # 외래 키
    trained_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # 유니크 제약
    __table_args__ = (
        # 이름과 버전의 조합은 유니크해야 함
        # UniqueConstraint('name', 'version', name='uix_model_name_version'),
    )

    def __repr__(self) -> str:
        return f"<AIModelModel(id={self.id}, name='{self.name}', version='{self.version}')>"
