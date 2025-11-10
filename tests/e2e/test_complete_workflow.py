"""
End-to-End Workflow Tests

Tests complete user workflows from simulation upload to analysis.
"""

import pytest
from pathlib import Path
import tempfile
import csv

from src.application.services import SimulationService
from src.infrastructure.repositories.memory_simulation_repository import (
    InMemorySimulationResultRepository,
)


@pytest.fixture
def service():
    """Create simulation service for testing."""
    repository = InMemorySimulationResultRepository()
    return SimulationService(repository)


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV simulation file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["x", "y", "z", "temperature", "pressure", "velocity_x"])
        # Data
        for i in range(10):
            writer.writerow(
                [
                    float(i),
                    float(i * 2),
                    float(i * 3),
                    300.0 + i,
                    101325.0 + i * 100,
                    1.0 + i * 0.1,
                ]
            )
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        path.unlink()


class TestCompleteSimulationWorkflow:
    """
    Test the complete simulation workflow.

    Workflow:
    1. Upload simulation file
    2. Retrieve simulation info
    3. Analyze field
    4. Check for extremes
    5. Detect outliers
    6. Analyze convergence (if multiple timesteps)
    7. Find critical regions
    8. Delete simulation
    """

    def test_complete_workflow(self, service, sample_csv_file):
        """Test complete simulation workflow from upload to deletion."""

        # Step 1: Upload and analyze simulation
        result = service.upload_and_analyze(
            file_path=sample_csv_file, name="E2E Test Simulation", analyze_all_fields=True
        )

        simulation_id = result.simulation_info.simulation_id

        # Verify upload
        assert simulation_id is not None
        assert result.simulation_info.name == "E2E Test Simulation"
        assert result.simulation_info.simulation_type == "CSV"
        assert len(result.simulation_info.fields) > 0

        # Verify all fields were analyzed
        assert "temperature" in result.field_analyses
        assert "pressure" in result.field_analyses

        # Step 2: Retrieve simulation
        simulation = service.get_simulation(simulation_id)
        assert simulation is not None
        assert simulation.name == "E2E Test Simulation"

        # Step 3: Analyze specific field
        field_analysis = service.analyze_field(
            simulation_id=simulation_id,
            timestep=0,
            field_name="temperature",
            compute_extremes=True,
            n_extremes=5,
            detect_outliers=True,
        )

        # Verify analysis results
        assert field_analysis.field_name == "temperature"
        assert "min" in field_analysis.statistics
        assert "max" in field_analysis.statistics
        assert "mean" in field_analysis.statistics

        # Step 4: Check extremes
        if field_analysis.extremes:
            assert "max" in field_analysis.extremes
            assert "min" in field_analysis.extremes

        # Step 5: Find critical regions
        high_temp_region, low_temp_region = service.find_critical_regions(
            simulation_id=simulation_id,
            timestep=0,
            field_name="temperature",
            percentile=90.0,
        )

        # Verify critical regions
        assert high_temp_region.region_size > 0
        assert low_temp_region.region_size > 0
        assert high_temp_region.region_statistics["mean"] > low_temp_region.region_statistics["mean"]

        # Step 6: Delete simulation
        service.delete_simulation(simulation_id)

        # Verify deletion
        with pytest.raises(Exception):  # Should raise KeyError or similar
            service.get_simulation(simulation_id)


class TestMultipleSimulationsWorkflow:
    """Test workflows involving multiple simulations."""

    def test_upload_and_compare_simulations(self, service, sample_csv_file):
        """Test uploading and comparing multiple simulations."""

        # Upload first simulation
        result1 = service.upload_and_analyze(
            file_path=sample_csv_file, name="Simulation 1", analyze_all_fields=False
        )
        sim_id_1 = result1.simulation_info.simulation_id

        # Upload second simulation
        result2 = service.upload_and_analyze(
            file_path=sample_csv_file, name="Simulation 2", analyze_all_fields=False
        )
        sim_id_2 = result2.simulation_info.simulation_id

        # Verify both simulations exist
        assert service.get_simulation(sim_id_1) is not None
        assert service.get_simulation(sim_id_2) is not None

        # List simulations
        simulations = service.list_simulations()
        assert len(simulations.simulations) >= 2

        # Cleanup
        service.delete_simulation(sim_id_1)
        service.delete_simulation(sim_id_2)


class TestAnalysisWorkflows:
    """Test various analysis workflows."""

    def test_progressive_analysis_workflow(self, service, sample_csv_file):
        """Test progressive analysis from basic to advanced."""

        # Upload
        result = service.upload_and_analyze(
            file_path=sample_csv_file, name="Progressive Analysis", analyze_all_fields=False
        )
        sim_id = result.simulation_info.simulation_id

        # Step 1: Basic statistics
        basic_analysis = service.analyze_field(
            simulation_id=sim_id, timestep=0, field_name="temperature", compute_extremes=False
        )
        assert "mean" in basic_analysis.statistics

        # Step 2: Add extremes
        extremes_analysis = service.analyze_field(
            simulation_id=sim_id,
            timestep=0,
            field_name="temperature",
            compute_extremes=True,
            n_extremes=3,
        )
        assert extremes_analysis.extremes is not None

        # Step 3: Add outlier detection
        outliers_analysis = service.analyze_field(
            simulation_id=sim_id, timestep=0, field_name="temperature", detect_outliers=True
        )
        assert outliers_analysis.outliers is not None

        # Step 4: Spatial analysis (critical regions)
        high_region, low_region = service.find_critical_regions(
            simulation_id=sim_id, timestep=0, field_name="temperature"
        )
        assert high_region.region_size > 0
        assert low_region.region_size > 0

        # Cleanup
        service.delete_simulation(sim_id)


class TestErrorHandling:
    """Test error handling in workflows."""

    def test_invalid_simulation_id(self, service):
        """Test handling of invalid simulation ID."""
        with pytest.raises(Exception):
            service.get_simulation("invalid-id")

    def test_invalid_field_name(self, service, sample_csv_file):
        """Test handling of invalid field name."""
        result = service.upload_and_analyze(
            file_path=sample_csv_file, name="Invalid Field Test"
        )
        sim_id = result.simulation_info.simulation_id

        with pytest.raises(Exception):
            service.analyze_field(
                simulation_id=sim_id, timestep=0, field_name="nonexistent_field"
            )

        # Cleanup
        service.delete_simulation(sim_id)

    def test_invalid_timestep(self, service, sample_csv_file):
        """Test handling of invalid timestep."""
        result = service.upload_and_analyze(
            file_path=sample_csv_file, name="Invalid Timestep Test"
        )
        sim_id = result.simulation_info.simulation_id

        with pytest.raises(Exception):
            service.analyze_field(simulation_id=sim_id, timestep=999, field_name="temperature")

        # Cleanup
        service.delete_simulation(sim_id)


@pytest.mark.asyncio
class TestConcurrentWorkflows:
    """Test concurrent operations (async workflows)."""

    async def test_concurrent_uploads(self, service, sample_csv_file):
        """Test concurrent simulation uploads."""
        # Note: This is a placeholder for future async support
        # Current implementation is synchronous

        # Upload simulations sequentially
        sim_ids = []
        for i in range(3):
            result = service.upload_and_analyze(
                file_path=sample_csv_file, name=f"Concurrent Test {i}"
            )
            sim_ids.append(result.simulation_info.simulation_id)

        # Verify all uploaded
        assert len(sim_ids) == 3

        # Cleanup
        for sim_id in sim_ids:
            service.delete_simulation(sim_id)
