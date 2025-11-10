"""
Repository 통합 테스트

실제 데이터베이스(SQLite in-memory)를 사용한 Repository 테스트입니다.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities import (
    SimulationResult,
    Dataset,
    Analysis,
    AIModel,
    SimulationStatus,
    AnalysisStatus,
)
from src.infrastructure.database.connection import InMemoryDatabaseConnection
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.sql_repository import (
    SimulationRepository,
    DatasetRepository,
    AnalysisRepository,
    AIModelRepository,
)


@pytest.fixture(scope="function")
async def db_connection() -> AsyncGenerator[InMemoryDatabaseConnection, None]:
    """테스트용 데이터베이스 연결"""
    conn = InMemoryDatabaseConnection()
    await conn.create_tables()
    yield conn
    await conn.close()


@pytest.fixture
async def session(db_connection: InMemoryDatabaseConnection) -> AsyncGenerator[AsyncSession, None]:
    """테스트용 세션"""
    async with db_connection.get_session() as sess:
        yield sess
        # 롤백하여 테스트 간 격리 보장
        await sess.rollback()


@pytest.mark.asyncio
class TestSimulationRepository:
    """SimulationRepository 통합 테스트"""

    async def test_save_and_find_by_id(self, session: AsyncSession) -> None:
        """저장 및 ID 조회 테스트"""
        repo = SimulationRepository(session)

        simulation = SimulationResult(
            name="Test Simulation",
            type="CFD",
            description="Test description",
            parameters={"param1": "value1"},
            metadata={"key": "value"},
            tags=["test", "cfd"],
        )

        # 저장
        simulation_id = await repo.save(simulation)
        await session.commit()

        # 조회
        found = await repo.find_by_id(simulation_id)

        assert found is not None
        assert found.name == "Test Simulation"
        assert found.type == "CFD"
        assert found.metadata == {"key": "value"}
        assert found.tags == ["test", "cfd"]

    async def test_update(self, session: AsyncSession) -> None:
        """업데이트 테스트"""
        repo = SimulationRepository(session)

        simulation = SimulationResult(
            name="Original Name",
            type="CFD",
            metadata={"version": "1.0"},
        )

        simulation_id = await repo.save(simulation)
        await session.commit()

        # 업데이트
        simulation.name = "Updated Name"
        simulation.metadata = {"version": "2.0"}
        await repo.update(simulation)
        await session.commit()

        # 확인
        found = await repo.find_by_id(simulation_id)
        assert found is not None
        assert found.name == "Updated Name"
        assert found.metadata == {"version": "2.0"}

    async def test_delete(self, session: AsyncSession) -> None:
        """삭제 테스트"""
        repo = SimulationRepository(session)

        simulation = SimulationResult(
            name="To Delete",
            type="CFD",
        )

        simulation_id = await repo.save(simulation)
        await session.commit()

        # 삭제
        await repo.delete(simulation_id)
        await session.commit()

        # 확인
        found = await repo.find_by_id(simulation_id)
        assert found is None

    async def test_exists(self, session: AsyncSession) -> None:
        """존재 여부 확인 테스트"""
        repo = SimulationRepository(session)

        simulation = SimulationResult(
            name="Test",
            type="CFD",
        )

        simulation_id = await repo.save(simulation)
        await session.commit()

        assert await repo.exists(simulation_id) is True
        assert await repo.exists(uuid4()) is False

    async def test_find_by_name(self, session: AsyncSession) -> None:
        """이름으로 조회 테스트"""
        repo = SimulationRepository(session)

        sim1 = SimulationResult(name="Same Name", type="CFD")
        sim2 = SimulationResult(name="Same Name", type="FEA")
        sim3 = SimulationResult(name="Different", type="CFD")

        await repo.save(sim1)
        await repo.save(sim2)
        await repo.save(sim3)
        await session.commit()

        results = await repo.find_by_name("Same Name")
        assert len(results) == 2

    async def test_find_by_status(self, session: AsyncSession) -> None:
        """상태로 조회 테스트"""
        repo = SimulationRepository(session)

        sim1 = SimulationResult(name="Sim1", type="CFD", status=SimulationStatus.PENDING)
        sim2 = SimulationResult(name="Sim2", type="CFD", status=SimulationStatus.COMPLETED)
        sim3 = SimulationResult(name="Sim3", type="CFD", status=SimulationStatus.PENDING)

        await repo.save(sim1)
        await repo.save(sim2)
        await repo.save(sim3)
        await session.commit()

        pending = await repo.find_by_status(SimulationStatus.PENDING)
        assert len(pending) == 2

    async def test_find_by_type(self, session: AsyncSession) -> None:
        """타입으로 조회 테스트"""
        repo = SimulationRepository(session)

        sim1 = SimulationResult(name="Sim1", type="CFD")
        sim2 = SimulationResult(name="Sim2", type="FEA")
        sim3 = SimulationResult(name="Sim3", type="CFD")

        await repo.save(sim1)
        await repo.save(sim2)
        await repo.save(sim3)
        await session.commit()

        cfd_sims = await repo.find_by_type("CFD")
        assert len(cfd_sims) == 2

    async def test_find_by_criteria_with_tags(self, session: AsyncSession) -> None:
        """태그를 포함한 복합 조건 조회 테스트"""
        repo = SimulationRepository(session)

        sim1 = SimulationResult(name="CFD Test", type="CFD", tags=["production", "validated"])
        sim2 = SimulationResult(name="FEA Test", type="FEA", tags=["test"])
        sim3 = SimulationResult(name="CFD Prod", type="CFD", tags=["production"])

        await repo.save(sim1)
        await repo.save(sim2)
        await repo.save(sim3)
        await session.commit()

        # 타입과 태그로 검색
        results = await repo.find_by_criteria({"type": "CFD", "tags": ["production"]}, limit=10)

        assert len(results) == 2

    async def test_count(self, session: AsyncSession) -> None:
        """카운트 테스트"""
        repo = SimulationRepository(session)

        sim1 = SimulationResult(name="Sim1", type="CFD", status=SimulationStatus.PENDING)
        sim2 = SimulationResult(name="Sim2", type="CFD", status=SimulationStatus.COMPLETED)
        sim3 = SimulationResult(name="Sim3", type="FEA", status=SimulationStatus.PENDING)

        await repo.save(sim1)
        await repo.save(sim2)
        await repo.save(sim3)
        await session.commit()

        total = await repo.count()
        assert total == 3

        cfd_count = await repo.count({"type": "CFD"})
        assert cfd_count == 2

        pending_count = await repo.count({"status": SimulationStatus.PENDING.value})
        assert pending_count == 2


@pytest.mark.asyncio
class TestDatasetRepository:
    """DatasetRepository 통합 테스트"""

    async def test_save_and_find_by_id(self, session: AsyncSession) -> None:
        """저장 및 ID 조회 테스트"""
        sim_repo = SimulationRepository(session)
        ds_repo = DatasetRepository(session)

        # 먼저 시뮬레이션 생성
        simulation = SimulationResult(name="Test Sim", type="CFD")
        sim_id = await sim_repo.save(simulation)
        await session.commit()

        # 데이터셋 생성
        dataset = Dataset(
            simulation_id=sim_id,
            data_type="mesh",
            data_format="vtk",
            storage_path="/path/to/data.vtk",
            size_bytes=1024,
            checksum="abc123",
            metadata={"version": "1.0"},
        )

        ds_id = await ds_repo.save(dataset)
        await session.commit()

        # 조회
        found = await ds_repo.find_by_id(ds_id)

        assert found is not None
        assert found.simulation_id == sim_id
        assert found.data_type == "mesh"
        assert found.metadata == {"version": "1.0"}

    async def test_update_metadata(self, session: AsyncSession) -> None:
        """메타데이터 업데이트 테스트"""
        sim_repo = SimulationRepository(session)
        ds_repo = DatasetRepository(session)

        simulation = SimulationResult(name="Test", type="CFD")
        sim_id = await sim_repo.save(simulation)

        dataset = Dataset(
            simulation_id=sim_id,
            data_type="mesh",
            data_format="vtk",
            storage_path="/path/to/data.vtk",
            size_bytes=1024,
            metadata={"version": "1.0"},
        )

        ds_id = await ds_repo.save(dataset)
        await session.commit()

        # 메타데이터 업데이트
        dataset.metadata = {"version": "2.0", "updated": True}
        await ds_repo.update(dataset)
        await session.commit()

        # 확인
        found = await ds_repo.find_by_id(ds_id)
        assert found is not None
        assert found.metadata == {"version": "2.0", "updated": True}

    async def test_find_by_simulation_id(self, session: AsyncSession) -> None:
        """시뮬레이션 ID로 데이터셋 조회 테스트"""
        sim_repo = SimulationRepository(session)
        ds_repo = DatasetRepository(session)

        simulation = SimulationResult(name="Test", type="CFD")
        sim_id = await sim_repo.save(simulation)

        # 여러 데이터셋 생성
        ds1 = Dataset(
            simulation_id=sim_id,
            data_type="mesh",
            data_format="vtk",
            storage_path="/path1",
            size_bytes=1024,
        )
        ds2 = Dataset(
            simulation_id=sim_id,
            data_type="contour",
            data_format="json",
            storage_path="/path2",
            size_bytes=2048,
        )

        await ds_repo.save(ds1)
        await ds_repo.save(ds2)
        await session.commit()

        # 조회
        datasets = await ds_repo.find_by_simulation_id(sim_id)
        assert len(datasets) == 2

    async def test_find_by_data_type(self, session: AsyncSession) -> None:
        """데이터 타입으로 조회 테스트"""
        sim_repo = SimulationRepository(session)
        ds_repo = DatasetRepository(session)

        sim1 = SimulationResult(name="Sim1", type="CFD")
        sim2 = SimulationResult(name="Sim2", type="FEA")
        sim1_id = await sim_repo.save(sim1)
        sim2_id = await sim_repo.save(sim2)

        ds1 = Dataset(
            simulation_id=sim1_id,
            data_type="mesh",
            data_format="vtk",
            storage_path="/path1",
            size_bytes=1024,
        )
        ds2 = Dataset(
            simulation_id=sim2_id,
            data_type="mesh",
            data_format="stl",
            storage_path="/path2",
            size_bytes=2048,
        )
        ds3 = Dataset(
            simulation_id=sim1_id,
            data_type="contour",
            data_format="json",
            storage_path="/path3",
            size_bytes=512,
        )

        await ds_repo.save(ds1)
        await ds_repo.save(ds2)
        await ds_repo.save(ds3)
        await session.commit()

        mesh_datasets = await ds_repo.find_by_data_type("mesh")
        assert len(mesh_datasets) == 2


@pytest.mark.asyncio
class TestAnalysisRepository:
    """AnalysisRepository 통합 테스트"""

    async def test_save_and_find_by_id(self, session: AsyncSession) -> None:
        """저장 및 ID 조회 테스트"""
        sim_repo = SimulationRepository(session)
        analysis_repo = AnalysisRepository(session)

        simulation = SimulationResult(name="Test", type="CFD")
        sim_id = await sim_repo.save(simulation)
        await session.commit()

        analysis = Analysis(
            simulation_id=sim_id,
            analysis_type="statistical",
            status=AnalysisStatus.PENDING,
            input_parameters={"method": "mean"},
            results={},
        )

        analysis_id = await analysis_repo.save(analysis)
        await session.commit()

        found = await analysis_repo.find_by_id(analysis_id)

        assert found is not None
        assert found.simulation_id == sim_id
        assert found.analysis_type == "statistical"
        assert found.status == AnalysisStatus.PENDING

    async def test_update_status(self, session: AsyncSession) -> None:
        """상태 업데이트 테스트"""
        sim_repo = SimulationRepository(session)
        analysis_repo = AnalysisRepository(session)

        simulation = SimulationResult(name="Test", type="CFD")
        sim_id = await sim_repo.save(simulation)

        analysis = Analysis(
            simulation_id=sim_id,
            analysis_type="statistical",
            status=AnalysisStatus.PENDING,
            input_parameters={},
            results={},
        )

        analysis_id = await analysis_repo.save(analysis)
        await session.commit()

        # 상태 업데이트
        analysis.start()
        await analysis_repo.update(analysis)
        await session.commit()

        found = await analysis_repo.find_by_id(analysis_id)
        assert found is not None
        assert found.status == AnalysisStatus.RUNNING

        # 완료
        analysis.complete({"mean": 10.5})
        await analysis_repo.update(analysis)
        await session.commit()

        found = await analysis_repo.find_by_id(analysis_id)
        assert found is not None
        assert found.status == AnalysisStatus.COMPLETED
        assert found.results == {"mean": 10.5}

    async def test_find_by_status(self, session: AsyncSession) -> None:
        """상태로 조회 테스트"""
        sim_repo = SimulationRepository(session)
        analysis_repo = AnalysisRepository(session)

        simulation = SimulationResult(name="Test", type="CFD")
        sim_id = await sim_repo.save(simulation)

        a1 = Analysis(
            simulation_id=sim_id,
            analysis_type="t1",
            status=AnalysisStatus.PENDING,
            input_parameters={},
            results={},
        )
        a2 = Analysis(
            simulation_id=sim_id,
            analysis_type="t2",
            status=AnalysisStatus.RUNNING,
            input_parameters={},
            results={},
        )
        a3 = Analysis(
            simulation_id=sim_id,
            analysis_type="t3",
            status=AnalysisStatus.PENDING,
            input_parameters={},
            results={},
        )

        await analysis_repo.save(a1)
        await analysis_repo.save(a2)
        await analysis_repo.save(a3)
        await session.commit()

        pending = await analysis_repo.find_by_status(AnalysisStatus.PENDING)
        assert len(pending) == 2

    async def test_find_pending(self, session: AsyncSession) -> None:
        """대기 중 분석 조회 테스트"""
        sim_repo = SimulationRepository(session)
        analysis_repo = AnalysisRepository(session)

        simulation = SimulationResult(name="Test", type="CFD")
        sim_id = await sim_repo.save(simulation)

        # 생성 시간을 다르게 하기 위해 순차적으로 생성
        for i in range(5):
            analysis = Analysis(
                simulation_id=sim_id,
                analysis_type=f"type{i}",
                status=AnalysisStatus.PENDING,
                input_parameters={},
                results={},
            )
            await analysis_repo.save(analysis)

        await session.commit()

        # 최대 3개만 조회
        pending = await analysis_repo.find_pending(limit=3)
        assert len(pending) == 3


@pytest.mark.asyncio
class TestAIModelRepository:
    """AIModelRepository 통합 테스트"""

    async def test_save_and_find_by_id(self, session: AsyncSession) -> None:
        """저장 및 ID 조회 테스트"""
        repo = AIModelRepository(session)

        model = AIModel(
            name="TestVAE",
            version="1.0.0",
            model_type="VAE",
            description="Test VAE model",
            architecture={"encoder": "CNN", "decoder": "CNN"},
            performance_metrics={"loss": 0.05},
            training_config={"epochs": 100},
            storage_path="/models/vae_v1.pth",
        )

        model_id = await repo.save(model)
        await session.commit()

        found = await repo.find_by_id(model_id)

        assert found is not None
        assert found.name == "TestVAE"
        assert found.version == "1.0.0"
        assert found.architecture == {"encoder": "CNN", "decoder": "CNN"}

    async def test_find_by_name(self, session: AsyncSession) -> None:
        """이름으로 조회 테스트 (여러 버전)"""
        repo = AIModelRepository(session)

        model_v1 = AIModel(
            name="TestModel",
            version="1.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )
        model_v2 = AIModel(
            name="TestModel",
            version="2.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )

        await repo.save(model_v1)
        await repo.save(model_v2)
        await session.commit()

        models = await repo.find_by_name("TestModel")
        assert len(models) == 2

    async def test_find_by_name_and_version(self, session: AsyncSession) -> None:
        """이름과 버전으로 조회 테스트"""
        repo = AIModelRepository(session)

        model = AIModel(
            name="TestModel",
            version="1.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )

        await repo.save(model)
        await session.commit()

        found = await repo.find_by_name_and_version("TestModel", "1.0.0")

        assert found is not None
        assert found.version == "1.0.0"

    async def test_find_by_type(self, session: AsyncSession) -> None:
        """타입으로 조회 테스트"""
        repo = AIModelRepository(session)

        vae1 = AIModel(
            name="VAE1",
            version="1.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )
        vae2 = AIModel(
            name="VAE2",
            version="1.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )
        llm = AIModel(
            name="LLM1",
            version="1.0.0",
            model_type="LLM",
            architecture={},
            performance_metrics={},
            training_config={},
        )

        await repo.save(vae1)
        await repo.save(vae2)
        await repo.save(llm)
        await session.commit()

        vae_models = await repo.find_by_type("VAE")
        assert len(vae_models) == 2

    async def test_find_latest_by_name(self, session: AsyncSession) -> None:
        """최신 버전 조회 테스트"""
        repo = AIModelRepository(session)

        # 순서대로 생성 (created_at이 다름)
        v1 = AIModel(
            name="Model",
            version="1.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )
        await repo.save(v1)
        await session.commit()

        v2 = AIModel(
            name="Model",
            version="2.0.0",
            model_type="VAE",
            architecture={},
            performance_metrics={},
            training_config={},
        )
        await repo.save(v2)
        await session.commit()

        latest = await repo.find_latest_by_name("Model")

        assert latest is not None
        assert latest.version == "2.0.0"
