"""
Integration test fixtures and configuration
"""

import os
import tempfile
from pathlib import Path
from typing import Generator, Callable, Any
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from fastapi.testclient import TestClient

from src.infrastructure.database.models import Base
from src.presentation.api.main import app as fastapi_app
from src.infrastructure.repositories.sql_repository import SimulationRepository
from src.infrastructure.storage.local import LocalStorageBackend
from src.infrastructure.storage.config import StorageConfig
from src.infrastructure.cache.redis_cache import RedisCache, get_cache
from src.infrastructure.cache.config import CacheConfig


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get test database URL"""
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def db_engine(test_db_url: str) -> Generator[Engine, None, None]:
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
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def simulation_repository(db_session: Session) -> SimulationRepository:
    """Create simulation repository with test session"""
    return SimulationRepository(db_session)


@pytest.fixture(scope="function")
def temp_storage_dir() -> Generator[Path, None, None]:
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def storage_backend(temp_storage_dir: Path) -> LocalStorageBackend:
    """Create local storage backend for testing"""
    return LocalStorageBackend(str(temp_storage_dir))


@pytest.fixture(scope="function")
def test_cache() -> MagicMock:
    """Create test cache (mock or real Redis)"""
    # Use mock cache for testing
    cache = MagicMock(spec=RedisCache)
    cache.config = CacheConfig(cache_enabled=False)  # Disable for tests
    return cache


@pytest.fixture(scope="function")
def api_client(db_session: Session, storage_backend: LocalStorageBackend, test_cache: MagicMock) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with dependencies"""
    app = fastapi_app

    # Override dependencies
    def get_test_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    def get_test_storage() -> LocalStorageBackend:
        return storage_backend

    def get_test_cache_instance() -> MagicMock:
        return test_cache

    # Override dependency injections
    from src.presentation.api.dependencies import get_db

    app.dependency_overrides[get_db] = get_test_db
    # Note: get_storage and get_cache are not defined in dependencies.py
    # app.dependency_overrides[get_storage] = get_test_storage
    # app.dependency_overrides[get_cache] = get_test_cache_instance

    with TestClient(app) as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_file(temp_storage_dir: Path) -> Path:
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
def sample_vtk_file(temp_storage_dir: Path) -> Path:
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
def simulation_factory(simulation_repository: SimulationRepository) -> Callable[[str, int], Any]:
    """Factory for creating test simulations"""
    from src.core.domain.entities import SimulationResult
    from src.core.simulation.models import MeshData, FieldData, FieldType, DataLocation
    import numpy as np
    from datetime import datetime
    from typing import Any

    def create_simulation(name: str = "Test Simulation", num_points: int = 100) -> SimulationResult:
        """Create a test simulation"""
        # Create mesh
        vertices = np.random.rand(num_points, 3).astype(np.float32)
        mesh = MeshData(vertices=vertices)

        # Create fields
        temperature_field = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=np.random.uniform(300, 500, num_points).astype(np.float32),
            unit="K",
        )

        pressure_field = FieldData(
            name="pressure",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=np.random.uniform(100000, 102000, num_points).astype(np.float32),
            unit="Pa",
        )

        # Create simulation result
        result = SimulationResult(
            name=name,
            type="CSV",
            description="Test simulation",
            parameters={"num_points": num_points},
            metadata={"source": "test", "created_at": datetime.now().isoformat()},
        )

        # Save to repository (async repository needs to be called differently in real scenarios)
        # For now, just return the result
        return result

    return create_simulation
