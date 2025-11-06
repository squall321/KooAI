"""
PostgreSQL Repository 구현

SQLAlchemy를 사용한 Repository 패턴 구체 구현입니다.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.domain.entities import (
    SimulationResult,
    Dataset,
    Analysis,
    AIModel,
    SimulationStatus,
    AnalysisStatus,
)
from src.infrastructure.database.models import (
    SimulationModel,
    DatasetModel,
    AnalysisModel,
    AIModelModel,
)


class SimulationRepository:
    """
    PostgreSQL 시뮬레이션 리포지토리

    도메인 엔티티 SimulationResult와 데이터베이스 간 변환을 담당합니다.
    """

    def __init__(self, session: AsyncSession):
        """
        Args:
            session: SQLAlchemy 비동기 세션
        """
        self.session = session

    async def save(self, simulation: SimulationResult) -> UUID:
        """시뮬레이션 저장"""
        db_simulation = SimulationModel(
            id=simulation.id,
            name=simulation.name,
            type=simulation.type,
            description=simulation.description,
            status=simulation.status.value,
            parameters=simulation.parameters,
            meta_data=simulation.metadata,
            tags=simulation.tags,
            created_at=simulation.created_at,
            updated_at=simulation.updated_at,
            created_by=simulation.created_by,
        )

        self.session.add(db_simulation)
        await self.session.flush()

        return db_simulation.id

    async def find_by_id(self, simulation_id: UUID) -> Optional[SimulationResult]:
        """ID로 시뮬레이션 조회"""
        stmt = select(SimulationModel).where(SimulationModel.id == simulation_id)
        result = await self.session.execute(stmt)
        db_simulation = result.scalar_one_or_none()

        if db_simulation is None:
            return None

        return self._to_domain(db_simulation)

    async def find_by_name(self, name: str) -> List[SimulationResult]:
        """이름으로 시뮬레이션 조회"""
        stmt = select(SimulationModel).where(SimulationModel.name == name)
        result = await self.session.execute(stmt)
        db_simulations = result.scalars().all()

        return [self._to_domain(db_sim) for db_sim in db_simulations]

    async def find_by_status(self, status: SimulationStatus) -> List[SimulationResult]:
        """상태로 시뮬레이션 조회"""
        stmt = select(SimulationModel).where(SimulationModel.status == status.value)
        result = await self.session.execute(stmt)
        db_simulations = result.scalars().all()

        return [self._to_domain(db_sim) for db_sim in db_simulations]

    async def find_by_type(self, sim_type: str) -> List[SimulationResult]:
        """타입으로 시뮬레이션 조회"""
        stmt = select(SimulationModel).where(SimulationModel.type == sim_type)
        result = await self.session.execute(stmt)
        db_simulations = result.scalars().all()

        return [self._to_domain(db_sim) for db_sim in db_simulations]

    async def find_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[SimulationResult]:
        """복합 조건으로 시뮬레이션 조회"""
        stmt = select(SimulationModel)

        # 동적 필터 구성
        filters = []

        if "name" in criteria:
            filters.append(SimulationModel.name.ilike(f"%{criteria['name']}%"))

        if "type" in criteria:
            filters.append(SimulationModel.type == criteria["type"])

        if "status" in criteria:
            filters.append(SimulationModel.status == criteria["status"])

        if "date_from" in criteria:
            filters.append(SimulationModel.created_at >= criteria["date_from"])

        if "date_to" in criteria:
            filters.append(SimulationModel.created_at <= criteria["date_to"])

        if "tags" in criteria:
            # 태그 포함 검색 (JSON array에서 검색)
            tags = criteria["tags"]
            if isinstance(tags, list):
                for tag in tags:
                    # JSON 배열에 태그가 포함되어 있는지 확인
                    # PostgreSQL: @>, SQLite: JSON string contains
                    filters.append(SimulationModel.tags.cast(String).contains(f'"{tag}"'))

        if filters:
            stmt = stmt.where(and_(*filters))

        # 정렬
        stmt = stmt.order_by(SimulationModel.created_at.desc())

        # 페이지네이션
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        db_simulations = result.scalars().all()

        return [self._to_domain(db_sim) for db_sim in db_simulations]

    async def update(self, simulation: SimulationResult) -> None:
        """시뮬레이션 업데이트"""
        stmt = select(SimulationModel).where(SimulationModel.id == simulation.id)
        result = await self.session.execute(stmt)
        db_simulation = result.scalar_one_or_none()

        if db_simulation is None:
            raise ValueError(f"Simulation {simulation.id} not found")

        # 필드 업데이트
        db_simulation.name = simulation.name
        db_simulation.type = simulation.type
        db_simulation.description = simulation.description
        db_simulation.status = simulation.status.value
        db_simulation.parameters = simulation.parameters
        db_simulation.meta_data = simulation.metadata
        db_simulation.tags = simulation.tags
        db_simulation.updated_at = simulation.updated_at

        await self.session.flush()

    async def delete(self, simulation_id: UUID) -> None:
        """시뮬레이션 삭제"""
        stmt = select(SimulationModel).where(SimulationModel.id == simulation_id)
        result = await self.session.execute(stmt)
        db_simulation = result.scalar_one_or_none()

        if db_simulation is not None:
            await self.session.delete(db_simulation)
            await self.session.flush()

    async def exists(self, simulation_id: UUID) -> bool:
        """시뮬레이션 존재 여부 확인"""
        stmt = select(func.count()).select_from(SimulationModel).where(
            SimulationModel.id == simulation_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """시뮬레이션 개수 조회"""
        stmt = select(func.count()).select_from(SimulationModel)

        if criteria:
            filters = []
            if "status" in criteria:
                filters.append(SimulationModel.status == criteria["status"])
            if "type" in criteria:
                filters.append(SimulationModel.type == criteria["type"])

            if filters:
                stmt = stmt.where(and_(*filters))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _to_domain(self, db_model: SimulationModel) -> SimulationResult:
        """DB 모델 → 도메인 엔티티 변환"""
        return SimulationResult(
            id=db_model.id,
            name=db_model.name,
            type=db_model.type,
            description=db_model.description,
            status=SimulationStatus(db_model.status),
            parameters=db_model.parameters or {},
            metadata=db_model.meta_data or {},
            tags=db_model.tags or [],
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            created_by=db_model.created_by,
        )


class DatasetRepository:
    """PostgreSQL 데이터셋 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, dataset: Dataset) -> UUID:
        """데이터셋 저장"""
        db_dataset = DatasetModel(
            id=dataset.id,
            simulation_id=dataset.simulation_id,
            data_type=dataset.data_type,
            data_format=dataset.data_format,
            storage_path=dataset.storage_path,
            size_bytes=dataset.size_bytes,
            checksum=dataset.checksum,
            meta_data=dataset.metadata,
            created_at=dataset.created_at,
        )

        self.session.add(db_dataset)
        await self.session.flush()

        return db_dataset.id

    async def find_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """ID로 데이터셋 조회"""
        stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
        result = await self.session.execute(stmt)
        db_dataset = result.scalar_one_or_none()

        if db_dataset is None:
            return None

        return self._to_domain(db_dataset)

    async def find_by_simulation_id(self, simulation_id: UUID) -> List[Dataset]:
        """시뮬레이션 ID로 데이터셋 조회"""
        stmt = select(DatasetModel).where(
            DatasetModel.simulation_id == simulation_id
        )
        result = await self.session.execute(stmt)
        db_datasets = result.scalars().all()

        return [self._to_domain(db_ds) for db_ds in db_datasets]

    async def find_by_data_type(self, data_type: str) -> List[Dataset]:
        """데이터 타입으로 조회"""
        stmt = select(DatasetModel).where(DatasetModel.data_type == data_type)
        result = await self.session.execute(stmt)
        db_datasets = result.scalars().all()

        return [self._to_domain(db_ds) for db_ds in db_datasets]

    async def update(self, dataset: Dataset) -> None:
        """데이터셋 업데이트"""
        stmt = select(DatasetModel).where(DatasetModel.id == dataset.id)
        result = await self.session.execute(stmt)
        db_dataset = result.scalar_one_or_none()

        if db_dataset is None:
            raise ValueError(f"Dataset {dataset.id} not found")

        db_dataset.data_type = dataset.data_type
        db_dataset.data_format = dataset.data_format
        db_dataset.storage_path = dataset.storage_path
        db_dataset.size_bytes = dataset.size_bytes
        db_dataset.checksum = dataset.checksum
        db_dataset.meta_data = dataset.metadata

        await self.session.flush()

    async def delete(self, dataset_id: UUID) -> None:
        """데이터셋 삭제"""
        stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
        result = await self.session.execute(stmt)
        db_dataset = result.scalar_one_or_none()

        if db_dataset is not None:
            await self.session.delete(db_dataset)
            await self.session.flush()

    def _to_domain(self, db_model: DatasetModel) -> Dataset:
        """DB 모델 → 도메인 엔티티 변환"""
        return Dataset(
            id=db_model.id,
            simulation_id=db_model.simulation_id,
            data_type=db_model.data_type,
            data_format=db_model.data_format,
            storage_path=db_model.storage_path,
            size_bytes=db_model.size_bytes,
            checksum=db_model.checksum,
            metadata=db_model.meta_data or {},
            created_at=db_model.created_at,
        )


class AnalysisRepository:
    """PostgreSQL 분석 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, analysis: Analysis) -> UUID:
        """분석 저장"""
        db_analysis = AnalysisModel(
            id=analysis.id,
            simulation_id=analysis.simulation_id,
            model_id=analysis.model_id,
            analysis_type=analysis.analysis_type,
            status=analysis.status.value,
            input_parameters=analysis.input_parameters,
            results=analysis.results,
            created_at=analysis.created_at,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            created_by=analysis.created_by,
        )

        self.session.add(db_analysis)
        await self.session.flush()

        return db_analysis.id

    async def find_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        """ID로 분석 조회"""
        stmt = select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        result = await self.session.execute(stmt)
        db_analysis = result.scalar_one_or_none()

        if db_analysis is None:
            return None

        return self._to_domain(db_analysis)

    async def find_by_simulation_id(self, simulation_id: UUID) -> List[Analysis]:
        """시뮬레이션 ID로 분석 조회"""
        stmt = select(AnalysisModel).where(
            AnalysisModel.simulation_id == simulation_id
        )
        result = await self.session.execute(stmt)
        db_analyses = result.scalars().all()

        return [self._to_domain(db_a) for db_a in db_analyses]

    async def find_by_status(self, status: AnalysisStatus) -> List[Analysis]:
        """상태로 분석 조회"""
        stmt = select(AnalysisModel).where(AnalysisModel.status == status.value)
        result = await self.session.execute(stmt)
        db_analyses = result.scalars().all()

        return [self._to_domain(db_a) for db_a in db_analyses]

    async def find_pending(self, limit: int = 10) -> List[Analysis]:
        """대기 중인 분석 조회"""
        stmt = (
            select(AnalysisModel)
            .where(AnalysisModel.status == AnalysisStatus.PENDING.value)
            .order_by(AnalysisModel.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        db_analyses = result.scalars().all()

        return [self._to_domain(db_a) for db_a in db_analyses]

    async def update(self, analysis: Analysis) -> None:
        """분석 업데이트"""
        stmt = select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        result = await self.session.execute(stmt)
        db_analysis = result.scalar_one_or_none()

        if db_analysis is None:
            raise ValueError(f"Analysis {analysis.id} not found")

        db_analysis.status = analysis.status.value
        db_analysis.input_parameters = analysis.input_parameters
        db_analysis.results = analysis.results
        db_analysis.started_at = analysis.started_at
        db_analysis.completed_at = analysis.completed_at

        await self.session.flush()

    async def delete(self, analysis_id: UUID) -> None:
        """분석 삭제"""
        stmt = select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        result = await self.session.execute(stmt)
        db_analysis = result.scalar_one_or_none()

        if db_analysis is not None:
            await self.session.delete(db_analysis)
            await self.session.flush()

    def _to_domain(self, db_model: AnalysisModel) -> Analysis:
        """DB 모델 → 도메인 엔티티 변환"""
        return Analysis(
            id=db_model.id,
            simulation_id=db_model.simulation_id,
            model_id=db_model.model_id,
            analysis_type=db_model.analysis_type,
            status=AnalysisStatus(db_model.status),
            input_parameters=db_model.input_parameters or {},
            results=db_model.results or {},
            created_at=db_model.created_at,
            started_at=db_model.started_at,
            completed_at=db_model.completed_at,
            created_by=db_model.created_by,
        )


class AIModelRepository:
    """PostgreSQL AI 모델 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, model: AIModel) -> UUID:
        """모델 저장"""
        db_model = AIModelModel(
            id=model.id,
            name=model.name,
            version=model.version,
            model_type=model.model_type,
            description=model.description,
            architecture=model.architecture,
            performance_metrics=model.performance_metrics,
            training_config=model.training_config,
            storage_path=model.storage_path,
            created_at=model.created_at,
            trained_by=model.trained_by,
        )

        self.session.add(db_model)
        await self.session.flush()

        return db_model.id

    async def find_by_id(self, model_id: UUID) -> Optional[AIModel]:
        """ID로 모델 조회"""
        stmt = select(AIModelModel).where(AIModelModel.id == model_id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        return self._to_domain(db_model)

    async def find_by_name(self, name: str) -> List[AIModel]:
        """이름으로 모델 조회"""
        stmt = select(AIModelModel).where(AIModelModel.name == name).order_by(
            AIModelModel.created_at.desc()
        )
        result = await self.session.execute(stmt)
        db_models = result.scalars().all()

        return [self._to_domain(db_m) for db_m in db_models]

    async def find_by_name_and_version(
        self, name: str, version: str
    ) -> Optional[AIModel]:
        """이름과 버전으로 모델 조회"""
        stmt = select(AIModelModel).where(
            and_(AIModelModel.name == name, AIModelModel.version == version)
        )
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        return self._to_domain(db_model)

    async def find_by_type(self, model_type: str) -> List[AIModel]:
        """타입으로 모델 조회"""
        stmt = select(AIModelModel).where(AIModelModel.model_type == model_type)
        result = await self.session.execute(stmt)
        db_models = result.scalars().all()

        return [self._to_domain(db_m) for db_m in db_models]

    async def find_latest_by_name(self, name: str) -> Optional[AIModel]:
        """이름으로 최신 모델 조회"""
        stmt = (
            select(AIModelModel)
            .where(AIModelModel.name == name)
            .order_by(AIModelModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        return self._to_domain(db_model)

    async def update(self, model: AIModel) -> None:
        """모델 업데이트"""
        stmt = select(AIModelModel).where(AIModelModel.id == model.id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            raise ValueError(f"Model {model.id} not found")

        db_model.description = model.description
        db_model.architecture = model.architecture
        db_model.performance_metrics = model.performance_metrics
        db_model.training_config = model.training_config
        db_model.storage_path = model.storage_path

        await self.session.flush()

    async def delete(self, model_id: UUID) -> None:
        """모델 삭제"""
        stmt = select(AIModelModel).where(AIModelModel.id == model_id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model is not None:
            await self.session.delete(db_model)
            await self.session.flush()

    def _to_domain(self, db_model: AIModelModel) -> AIModel:
        """DB 모델 → 도메인 엔티티 변환"""
        return AIModel(
            id=db_model.id,
            name=db_model.name,
            version=db_model.version,
            model_type=db_model.model_type,
            description=db_model.description,
            architecture=db_model.architecture or {},
            performance_metrics=db_model.performance_metrics or {},
            training_config=db_model.training_config or {},
            storage_path=db_model.storage_path,
            created_at=db_model.created_at,
            trained_by=db_model.trained_by,
        )
