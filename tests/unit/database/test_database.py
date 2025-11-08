"""
Database Module Tests

데이터베이스 설정 및 모델 테스트
"""

import pytest
from sqlalchemy import create_engine, inspect

from src.infrastructure.database.config import DatabaseConfig
from src.infrastructure.database.models import Base, SimulationModel
from src.core.domain.entities import SimulationStatus


def test_database_config_creation():
    """Test DatabaseConfig creation"""
    config = DatabaseConfig(
        host="testhost",
        port=5433,
        database="testdb",
        user="testuser",
        password="testpass",
        echo=True,
        pool_size=10,
        max_overflow=20,
    )

    assert config.host == "testhost"
    assert config.port == 5433
    assert config.database == "testdb"
    assert config.user == "testuser"
    assert config.password == "testpass"
    assert config.echo is True
    assert config.pool_size == 10
    assert config.max_overflow == 20


def test_database_config_defaults():
    """Test DatabaseConfig default values"""
    config = DatabaseConfig()

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "kooai"
    assert config.user == "kooai"
    assert config.echo is False
    assert config.pool_size == 20
    assert config.max_overflow == 10


def test_database_config_test_mode():
    """Test DatabaseConfig in test mode"""
    config = DatabaseConfig(use_test_db=True)

    assert "sqlite" in config.database_url
    assert ":memory:" in config.database_url


def test_database_config_postgresql_url():
    """Test DatabaseConfig PostgreSQL URL"""
    config = DatabaseConfig(
        host="myhost",
        port=5432,
        database="mydb",
        user="myuser",
        password="mypass",
        use_test_db=False,
    )

    url = config.database_url
    assert "postgresql" in url
    assert "myhost" in url
    assert "mydb" in url
    assert "myuser" in url


def test_simulation_model_creation():
    """Test SimulationModel creation"""
    model = SimulationModel(
        name="Test Simulation",
        type="CFD",
        description="A test simulation",
        status=SimulationStatus.PENDING,
        parameters={"timestep": 0.01},
        meta_data={"vertices": 1000},
    )

    assert model.name == "Test Simulation"
    assert model.type == "CFD"
    assert model.description == "A test simulation"
    assert model.parameters["timestep"] == 0.01
    assert model.meta_data["vertices"] == 1000


def test_simulation_model_in_memory():
    """Test SimulationModel with in-memory SQLite"""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # Check table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "simulations" in tables


def test_simulation_model_repr():
    """Test SimulationModel string representation"""
    model = SimulationModel(name="Test", type="FEA", status=SimulationStatus.PENDING)

    repr_str = repr(model)
    # repr should contain SimulationModel and the name
    assert "SimulationModel" in repr_str
    assert "Test" in repr_str
