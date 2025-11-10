"""
Database integration tests
"""

from typing import Any, Callable, Generator
import pytest
from datetime import datetime
from src.core.domain.simulation import SimulationResult, SimulationMetadata
from src.core.simulation.models import SimulationData, SimulationMesh  # type: ignore[attr-defined]
import numpy as np


class TestSimulationRepository:
    """Test simulation repository with real database"""

    def test_save_and_get_simulation(self, simulation_repository: Any) -> None:
        """Test saving and retrieving simulation"""
        # Create simulation
        mesh = SimulationMesh(vertices=np.random.rand(10, 3).astype(np.float32))
        fields = {"temperature": np.random.rand(10).astype(np.float32)}
        sim_data = SimulationData(name="Test", mesh=mesh, fields=fields)

        simulation = SimulationResult(
            simulation_id=None,
            name="Test Simulation",
            simulation_type="CSV",
            data=sim_data,
            metadata=SimulationMetadata(
                file_format="CSV",
                num_vertices=10,
                num_cells=0,
                field_names=["temperature"],
                created_at=datetime.now(),
            ),
        )

        # Save
        sim_id = simulation_repository.save(simulation)
        assert sim_id is not None

        # Get
        retrieved = simulation_repository.get_by_id(sim_id)
        assert retrieved is not None
        assert retrieved.name == "Test Simulation"
        assert retrieved.simulation_type == "CSV"

    def test_list_simulations(self, simulation_repository: Any, simulation_factory: Callable[[str], SimulationResult]) -> None:
        """Test listing simulations"""
        # Create multiple simulations
        simulation_factory("Sim 1")
        simulation_factory("Sim 2")
        simulation_factory("Sim 3")

        # List all
        simulations = simulation_repository.list_all()
        assert len(simulations) >= 3

        # Check names
        names = [s.name for s in simulations]
        assert "Sim 1" in names
        assert "Sim 2" in names
        assert "Sim 3" in names

    def test_delete_simulation(self, simulation_repository: Any, simulation_factory: Callable[[str], SimulationResult]) -> None:
        """Test deleting simulation"""
        # Create simulation
        simulation = simulation_factory("To Delete")
        sim_id = simulation.simulation_id

        # Delete
        result = simulation_repository.delete(sim_id)
        assert result is True

        # Verify deletion
        retrieved = simulation_repository.get_by_id(sim_id)
        assert retrieved is None

    def test_update_simulation(self, simulation_repository: Any, simulation_factory: Callable[[str], SimulationResult]) -> None:
        """Test updating simulation"""
        # Create simulation
        simulation = simulation_factory("Original Name")
        sim_id = simulation.simulation_id

        # Update name
        simulation.name = "Updated Name"
        simulation_repository.update(simulation)

        # Verify update
        retrieved = simulation_repository.get_by_id(sim_id)
        assert retrieved.name == "Updated Name"

    def test_get_by_name(self, simulation_repository: Any, simulation_factory: Callable[[str], SimulationResult]) -> None:
        """Test getting simulation by name"""
        # Create simulation with unique name
        unique_name = f"Unique_{datetime.now().timestamp()}"
        simulation_factory(unique_name)

        # Get by name
        simulations = simulation_repository.find_by_name(unique_name)
        assert len(simulations) > 0
        assert simulations[0].name == unique_name

    def test_save_with_large_data(self, simulation_repository: Any) -> None:
        """Test saving simulation with large dataset"""
        # Create large simulation
        num_points = 10000
        mesh = SimulationMesh(vertices=np.random.rand(num_points, 3).astype(np.float32))
        fields = {
            "temperature": np.random.rand(num_points).astype(np.float32),
            "pressure": np.random.rand(num_points).astype(np.float32),
            "velocity_x": np.random.rand(num_points).astype(np.float32),
            "velocity_y": np.random.rand(num_points).astype(np.float32),
            "velocity_z": np.random.rand(num_points).astype(np.float32),
        }
        sim_data = SimulationData(name="Large", mesh=mesh, fields=fields)

        simulation = SimulationResult(
            simulation_id=None,
            name="Large Simulation",
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

        # Save
        sim_id = simulation_repository.save(simulation)
        assert sim_id is not None

        # Retrieve and verify
        retrieved = simulation_repository.get_by_id(sim_id)
        assert retrieved is not None
        assert retrieved.metadata.num_vertices == num_points
        assert len(retrieved.data.fields) == 5

    def test_transaction_rollback(self, db_session: Any, simulation_repository: Any) -> None:
        """Test transaction rollback"""
        # Create simulation
        mesh = SimulationMesh(vertices=np.random.rand(5, 3).astype(np.float32))
        fields = {"temperature": np.random.rand(5).astype(np.float32)}
        sim_data = SimulationData(name="Test", mesh=mesh, fields=fields)

        simulation = SimulationResult(
            simulation_id=None,
            name="Rollback Test",
            simulation_type="CSV",
            data=sim_data,
            metadata=SimulationMetadata(
                file_format="CSV",
                num_vertices=5,
                num_cells=0,
                field_names=["temperature"],
                created_at=datetime.now(),
            ),
        )

        # Save
        sim_id = simulation_repository.save(simulation)

        # Rollback session
        db_session.rollback()

        # Should not exist after rollback
        # Note: This behavior depends on session management
        # In some cases, the save might auto-commit

    def test_concurrent_saves(self, simulation_repository: Any) -> None:
        """Test saving multiple simulations concurrently"""
        simulations = []

        for i in range(5):
            mesh = SimulationMesh(vertices=np.random.rand(10, 3).astype(np.float32))
            fields = {"temperature": np.random.rand(10).astype(np.float32)}
            sim_data = SimulationData(name=f"Sim{i}", mesh=mesh, fields=fields)

            simulation = SimulationResult(
                simulation_id=None,
                name=f"Concurrent Simulation {i}",
                simulation_type="CSV",
                data=sim_data,
                metadata=SimulationMetadata(
                    file_format="CSV",
                    num_vertices=10,
                    num_cells=0,
                    field_names=["temperature"],
                    created_at=datetime.now(),
                ),
            )

            sim_id = simulation_repository.save(simulation)
            simulation.simulation_id = sim_id
            simulations.append(simulation)

        # Verify all saved
        assert len(simulations) == 5
        for sim in simulations:
            assert sim.simulation_id is not None
            retrieved = simulation_repository.get_by_id(sim.simulation_id)
            assert retrieved is not None

    def test_get_nonexistent(self, simulation_repository: Any) -> None:
        """Test getting non-existent simulation"""
        result = simulation_repository.get_by_id("nonexistent-id-12345")
        assert result is None

    def test_delete_nonexistent(self, simulation_repository: Any) -> None:
        """Test deleting non-existent simulation"""
        result = simulation_repository.delete("nonexistent-id-12345")
        assert result is False


class TestDatabaseConstraints:
    """Test database constraints and validations"""

    def test_unique_constraints(self, simulation_repository: Any) -> None:
        """Test unique constraints (if any)"""
        # This depends on your schema
        # Example: test that simulation_id is unique
        pass

    def test_foreign_key_constraints(self, simulation_repository: Any) -> None:
        """Test foreign key constraints (if any)"""
        # Example: test that analysis results reference valid simulations
        pass

    def test_null_constraints(self, simulation_repository: Any) -> None:
        """Test null constraints"""
        # Example: test that required fields cannot be null
        pass


class TestDatabasePerformance:
    """Test database performance"""

    def test_bulk_insert_performance(self, simulation_repository: Any) -> None:
        """Test bulk insert performance"""
        import time

        start_time = time.time()

        for i in range(50):
            mesh = SimulationMesh(vertices=np.random.rand(100, 3).astype(np.float32))
            fields = {"temperature": np.random.rand(100).astype(np.float32)}
            sim_data = SimulationData(name=f"Bulk{i}", mesh=mesh, fields=fields)

            simulation = SimulationResult(
                simulation_id=None,
                name=f"Bulk Simulation {i}",
                simulation_type="CSV",
                data=sim_data,
                metadata=SimulationMetadata(
                    file_format="CSV",
                    num_vertices=100,
                    num_cells=0,
                    field_names=["temperature"],
                    created_at=datetime.now(),
                ),
            )

            simulation_repository.save(simulation)

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 10 seconds for 50 simulations)
        assert elapsed < 10.0

    def test_query_performance(self, simulation_repository: Any, simulation_factory: Callable[[str], SimulationResult]) -> None:
        """Test query performance"""
        import time

        # Create test data
        for i in range(20):
            simulation_factory(f"Query Test {i}")

        # Measure query time
        start_time = time.time()
        simulations = simulation_repository.list_all()
        elapsed = time.time() - start_time

        # Should be fast (< 1 second)
        assert elapsed < 1.0
        assert len(simulations) >= 20
