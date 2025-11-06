"""
데이터베이스 통합 테스트

실제 데이터베이스 (SQLite in-memory)를 사용한 리포지토리 통합 테스트입니다.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from src.infrastructure.database.connection import InMemoryDatabaseConnection
from src.infrastructure.database.models import (
    SimulationModel,
    DatasetModel,
    AnalysisModel,
    AIModelModel,
)
from src.infrastructure.repositories.sql_repository import (
    SimulationRepository,
    DatasetRepository,
    AnalysisRepository,
    AIModelRepository,
)
from src.core.domain.entities import (
    SimulationResult,
    Dataset,
    Analysis,
    AIModel,
    SimulationStatus,
    AnalysisStatus,
)


@pytest.fixture
async def db_connection():
    """인메모리 데이터베이스 연결"""
    conn = InMemoryDatabaseConnection()
    
    # 테이블 생성
    await conn.create_tables()
    
    yield conn
    
    # 정리
    await conn.close()


@pytest.fixture
async def db_session(db_connection):
    """데이터베이스 세션"""
    async with db_connection.get_session() as session:
        yield session
        await session.rollback()


# SimulationRepository 테스트


@pytest.mark.asyncio
async def test_simulation_repository_save_and_find(db_session):
    """시뮬레이션 저장 및 조회 테스트"""
    repo = SimulationRepository(db_session)
    
    # Given: 시뮬레이션 생성
    simulation = SimulationResult(
        name="Test CFD Simulation",
        type="CFD",
        description="Test simulation",
        parameters={"reynolds": 1000, "mach": 0.3},
        tags=["test", "cfd"],
    )
    
    # When: 저장
    saved_id = await repo.save(simulation)
    await db_session.commit()
    
    # Then: 조회 성공
    assert saved_id == simulation.id
    
    found = await repo.find_by_id(simulation.id)
    assert found is not None
    assert found.name == "Test CFD Simulation"
    assert found.type == "CFD"
    assert found.status == SimulationStatus.PENDING
    assert found.parameters["reynolds"] == 1000
    assert "cfd" in found.tags


@pytest.mark.asyncio
async def test_simulation_repository_find_by_name(db_session):
    """이름으로 시뮬레이션 조회 테스트"""
    repo = SimulationRepository(db_session)
    
    # Given: 여러 시뮬레이션 저장
    sim1 = SimulationResult(name="CFD Test", type="CFD")
    sim2 = SimulationResult(name="CFD Test", type="CFD")
    sim3 = SimulationResult(name="FEA Test", type="FEA")
    
    await repo.save(sim1)
    await repo.save(sim2)
    await repo.save(sim3)
    await db_session.commit()
    
    # When: 이름으로 조회
    results = await repo.find_by_name("CFD Test")
    
    # Then: 2개 조회됨
    assert len(results) == 2
    assert all(r.name == "CFD Test" for r in results)


@pytest.mark.asyncio
async def test_simulation_repository_find_by_status(db_session):
    """상태로 시뮬레이션 조회 테스트"""
    repo = SimulationRepository(db_session)
    
    # Given
    sim1 = SimulationResult(name="Sim1", type="CFD", status=SimulationStatus.PENDING)
    sim2 = SimulationResult(name="Sim2", type="CFD", status=SimulationStatus.PENDING)
    sim3 = SimulationResult(name="Sim3", type="CFD", status=SimulationStatus.COMPLETED)
    
    sim3.status = SimulationStatus.COMPLETED
    
    await repo.save(sim1)
    await repo.save(sim2)
    await repo.save(sim3)
    await db_session.commit()
    
    # When
    pending = await repo.find_by_status(SimulationStatus.PENDING)
    completed = await repo.find_by_status(SimulationStatus.COMPLETED)
    
    # Then
    assert len(pending) == 2
    assert len(completed) == 1


@pytest.mark.asyncio
async def test_simulation_repository_update(db_session):
    """시뮬레이션 업데이트 테스트"""
    repo = SimulationRepository(db_session)
    
    # Given
    simulation = SimulationResult(name="Original", type="CFD")
    await repo.save(simulation)
    await db_session.commit()
    
    # When: 상태 변경
    simulation.mark_as_processing()
    simulation.name = "Updated"
    await repo.update(simulation)
    await db_session.commit()
    
    # Then
    found = await repo.find_by_id(simulation.id)
    assert found.name == "Updated"
    assert found.status == SimulationStatus.PROCESSING


@pytest.mark.asyncio
async def test_simulation_repository_delete(db_session):
    """시뮬레이션 삭제 테스트"""
    repo = SimulationRepository(db_session)
    
    # Given
    simulation = SimulationResult(name="To Delete", type="CFD")
    await repo.save(simulation)
    await db_session.commit()
    
    # When
    await repo.delete(simulation.id)
    await db_session.commit()
    
    # Then
    found = await repo.find_by_id(simulation.id)
    assert found is None
    
    exists = await repo.exists(simulation.id)
    assert not exists


@pytest.mark.asyncio
async def test_simulation_repository_count(db_session):
    """시뮬레이션 개수 조회 테스트"""
    repo = SimulationRepository(db_session)
    
    # Given
    for i in range(5):
        sim = SimulationResult(name=f"Sim{i}", type="CFD")
        await repo.save(sim)
    await db_session.commit()
    
    # When
    count = await repo.count()
    
    # Then
    assert count == 5


# DatasetRepository 테스트


@pytest.mark.asyncio
async def test_dataset_repository_save_and_find(db_session):
    """데이터셋 저장 및 조회 테스트"""
    sim_repo = SimulationRepository(db_session)
    ds_repo = DatasetRepository(db_session)
    
    # Given: 시뮬레이션 먼저 생성
    simulation = SimulationResult(name="Test", type="CFD")
    await sim_repo.save(simulation)
    
    # 데이터셋 생성
    dataset = Dataset(
        simulation_id=simulation.id,
        data_type="mesh",
        data_format="vtk",
        storage_path="/data/mesh.vtk",
        size_bytes=1024,
        metadata={"vertices": 1000},
    )
    
    # When: 저장
    saved_id = await ds_repo.save(dataset)
    await db_session.commit()
    
    # Then
    assert saved_id == dataset.id
    
    found = await ds_repo.find_by_id(dataset.id)
    assert found is not None
    assert found.data_type == "mesh"
    assert found.size_bytes == 1024


@pytest.mark.asyncio
async def test_dataset_repository_find_by_simulation_id(db_session):
    """시뮬레이션 ID로 데이터셋 조회 테스트"""
    sim_repo = SimulationRepository(db_session)
    ds_repo = DatasetRepository(db_session)
    
    # Given
    simulation = SimulationResult(name="Test", type="CFD")
    await sim_repo.save(simulation)
    
    ds1 = Dataset(
        simulation_id=simulation.id,
        data_type="mesh",
        data_format="vtk",
        storage_path="/data/mesh.vtk",
    )
    ds2 = Dataset(
        simulation_id=simulation.id,
        data_type="contour",
        data_format="csv",
        storage_path="/data/contour.csv",
    )
    
    await ds_repo.save(ds1)
    await ds_repo.save(ds2)
    await db_session.commit()
    
    # When
    datasets = await ds_repo.find_by_simulation_id(simulation.id)
    
    # Then
    assert len(datasets) == 2


# AnalysisRepository 테스트


@pytest.mark.asyncio
async def test_analysis_repository_save_and_find(db_session):
    """분석 저장 및 조회 테스트"""
    sim_repo = SimulationRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)
    
    # Given
    simulation = SimulationResult(name="Test", type="CFD")
    await sim_repo.save(simulation)
    
    analysis = Analysis(
        simulation_id=simulation.id,
        analysis_type="statistical",
        input_parameters={"field": "pressure"},
        results={"mean": 101325.0},
    )
    
    # When
    saved_id = await analysis_repo.save(analysis)
    await db_session.commit()
    
    # Then
    found = await analysis_repo.find_by_id(analysis.id)
    assert found is not None
    assert found.analysis_type == "statistical"
    assert found.status == AnalysisStatus.PENDING


@pytest.mark.asyncio
async def test_analysis_repository_find_pending(db_session):
    """대기 중인 분석 조회 테스트"""
    sim_repo = SimulationRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)
    
    # Given
    simulation = SimulationResult(name="Test", type="CFD")
    await sim_repo.save(simulation)
    
    # 3개의 분석 생성 (2개 pending, 1개 running)
    a1 = Analysis(simulation_id=simulation.id, analysis_type="type1")
    a2 = Analysis(simulation_id=simulation.id, analysis_type="type2")
    a3 = Analysis(simulation_id=simulation.id, analysis_type="type3")
    a3.start()
    
    await analysis_repo.save(a1)
    await analysis_repo.save(a2)
    await analysis_repo.save(a3)
    await db_session.commit()
    
    # When
    pending = await analysis_repo.find_pending(limit=10)
    
    # Then
    assert len(pending) == 2
    assert all(a.status == AnalysisStatus.PENDING for a in pending)


# AIModelRepository 테스트


@pytest.mark.asyncio
async def test_ai_model_repository_save_and_find(db_session):
    """AI 모델 저장 및 조회 테스트"""
    repo = AIModelRepository(db_session)
    
    # Given
    model = AIModel(
        name="VAE-v1",
        version="1.0.0",
        model_type="vae",
        description="Test VAE model",
        architecture={"layers": 10},
        performance_metrics={"loss": 0.01},
    )
    
    # When
    saved_id = await repo.save(model)
    await db_session.commit()
    
    # Then
    found = await repo.find_by_id(model.id)
    assert found is not None
    assert found.name == "VAE-v1"
    assert found.version == "1.0.0"


@pytest.mark.asyncio
async def test_ai_model_repository_find_by_name_and_version(db_session):
    """이름과 버전으로 AI 모델 조회 테스트"""
    repo = AIModelRepository(db_session)
    
    # Given
    model1 = AIModel(name="VAE", version="1.0.0", model_type="vae")
    model2 = AIModel(name="VAE", version="2.0.0", model_type="vae")
    
    await repo.save(model1)
    await repo.save(model2)
    await db_session.commit()
    
    # When
    found = await repo.find_by_name_and_version("VAE", "2.0.0")
    
    # Then
    assert found is not None
    assert found.version == "2.0.0"


@pytest.mark.asyncio
async def test_ai_model_repository_find_latest_by_name(db_session):
    """이름으로 최신 AI 모델 조회 테스트"""
    repo = AIModelRepository(db_session)
    
    # Given: 시간 차이를 두고 저장
    model1 = AIModel(name="VAE", version="1.0.0", model_type="vae")
    await repo.save(model1)
    await db_session.commit()
    
    # 약간의 지연 후 두 번째 모델 저장
    model2 = AIModel(name="VAE", version="2.0.0", model_type="vae")
    await repo.save(model2)
    await db_session.commit()
    
    # When
    latest = await repo.find_latest_by_name("VAE")
    
    # Then: 최신 모델이 조회됨
    assert latest is not None
    assert latest.version == "2.0.0"
