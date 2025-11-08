"""
Integration test fixtures and configuration
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from src.infrastructure.database.models import Base
from src.presentation.api.main import app as fastapi_app
from src.infrastructure.repositories.sql_repository import SimulationRepository
from src.infrastructure.storage.local import LocalStorageBackend
from src.infrastructure.storage.config import StorageConfig
from src.infrastructure.cache.redis_cache import RedisCache, get_cache
from src.infrastructure.cache.config import CacheConfig


@pytest.fixture(scope="session")
def test_db_url():
    """Get test database URL"""
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def db_engine(test_db_url):
    """Create test database engine"""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False} if "sqlite" in test_db_url else {},
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def simulation_repository(db_session):
    """Create simulation repository with test session"""
    return SimulationRepository(db_session)


@pytest.fixture(scope="function")
def temp_storage_dir():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def storage_backend(temp_storage_dir):
    """Create local storage backend for testing"""
    config = StorageConfig(
        storage_backend="local",
        local_storage_path=str(temp_storage_dir),
    )
    return LocalStorageBackend(config)


@pytest.fixture(scope="function")
def test_cache():
    """Create test cache (mock or real Redis)"""
    # Use mock cache for testing
    from unittest.mock import MagicMock

    cache = MagicMock(spec=RedisCache)
    cache.config = CacheConfig(cache_enabled=False)  # Disable for tests
    return cache


@pytest.fixture(scope="function")
def api_client(db_session, storage_backend, test_cache):
    """Create FastAPI test client with dependencies"""
    app = fastapi_app

    # Override dependencies
    def get_test_db():
        try:
            yield db_session
        finally:
            pass

    def get_test_storage():
        return storage_backend

    def get_test_cache_instance():
        return test_cache

    # Override dependency injections
    from src.presentation.api.dependencies import get_db, get_storage

    app.dependency_overrides[get_db] = get_test_db
    # app.dependency_overrides[get_storage] = get_test_storage
    # app.dependency_overrides[get_cache] = get_test_cache_instance

    with TestClient(app) as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_file(temp_storage_dir):
    """Create sample CSV simulation file"""
    csv_content = """x,y,z,temperature,pressure
0.0,0.0,0.0,300.0,101325.0
1.0,0.0,0.0,350.0,101330.0
0.0,1.0,0.0,400.0,101340.0
1.0,1.0,0.0,450.0,101350.0
"""
    csv_file = temp_storage_dir / "sample.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def sample_vtk_file(temp_storage_dir):
    """Create sample VTK simulation file"""
    vtk_content = """# vtk DataFile Version 2.0
Test VTK file
ASCII
DATASET POLYDATA
POINTS 4 float
0.0 0.0 0.0
1.0 0.0 0.0
0.0 1.0 0.0
1.0 1.0 0.0
POINT_DATA 4
SCALARS temperature float 1
LOOKUP_TABLE default
300.0
350.0
400.0
450.0
SCALARS pressure float 1
LOOKUP_TABLE default
101325.0
101330.0
101340.0
101350.0
"""
    vtk_file = temp_storage_dir / "sample.vtk"
    vtk_file.write_text(vtk_content)
    return vtk_file


@pytest.fixture
def simulation_factory(simulation_repository):
    """Factory for creating test simulations"""
    from src.core.domain.simulation import SimulationResult, SimulationMetadata
    from src.core.simulation.models import SimulationData, SimulationMesh
    import numpy as np
    from datetime import datetime

    def create_simulation(name: str = "Test Simulation", num_points: int = 100):
        """Create a test simulation"""
        # Create mesh
        vertices = np.random.rand(num_points, 3).astype(np.float32)
        mesh = SimulationMesh(vertices=vertices)

        # Create fields
        fields = {
            "temperature": np.random.uniform(300, 500, num_points).astype(np.float32),
            "pressure": np.random.uniform(100000, 102000, num_points).astype(np.float32),
        }

        # Create simulation data
        sim_data = SimulationData(
            name=name,
            mesh=mesh,
            fields=fields,
            metadata={"source": "test", "created_at": datetime.now().isoformat()},
        )

        # Create simulation result
        result = SimulationResult(
            simulation_id=None,  # Will be assigned by repository
            name=name,
            simulation_type="CSV",
            data=sim_data,
            metadata=SimulationMetadata(
                file_format="CSV",
                num_vertices=num_points,
                num_cells=0,
                field_names=list(fields.keys()),
                created_at=datetime.now(),
            ),
        )

        # Save to repository
        saved_id = simulation_repository.save(result)
        result.simulation_id = saved_id

        return result

    return create_simulation
