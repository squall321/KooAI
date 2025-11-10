"""
Tests for SimulationComparator
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Iterator

import pytest
import numpy as np
from datetime import datetime

from src.application.comparison.comparator import (
    SimulationComparator,
    ComparisonResult,
)
from src.core.simulation.models import (
    SimulationResult,
    MeshData,
    TimeStepData,
    FieldData,
    FieldType,
    DataLocation,
)


@pytest.fixture
def sample_mesh() -> MeshData:
    """Create sample mesh"""
    vertices = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [1, 1, 0],
        ],
        dtype=np.float32,
    )
    return MeshData(vertices=vertices)


@pytest.fixture
def simulation1(sample_mesh: MeshData) -> SimulationResult:
    """Create first simulation"""
    # Create fields
    temperature = FieldData(
        name="temperature",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([300.0, 310.0, 320.0, 330.0], dtype=np.float32),
        unit="K",
    )
    pressure = FieldData(
        name="pressure",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([101000.0, 101100.0, 101200.0, 101300.0], dtype=np.float32),
        unit="Pa",
    )

    # Create timestep
    timestep = TimeStepData(time=0.0, step=0)
    timestep.add_field(temperature)
    timestep.add_field(pressure)

    # Create simulation
    sim = SimulationResult(
        name="Simulation 1",
        simulation_type="CFD",
        mesh=sample_mesh,
    )
    sim.add_timestep(timestep)
    sim.id = "sim1"

    return sim


@pytest.fixture
def simulation2(sample_mesh: MeshData) -> SimulationResult:
    """Create second simulation with slight differences"""
    # Create fields
    temperature = FieldData(
        name="temperature",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([305.0, 315.0, 325.0, 335.0], dtype=np.float32),
        unit="K",
    )
    pressure = FieldData(
        name="pressure",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([101050.0, 101150.0, 101250.0, 101350.0], dtype=np.float32),
        unit="Pa",
    )

    # Create timestep
    timestep = TimeStepData(time=0.0, step=0)
    timestep.add_field(temperature)
    timestep.add_field(pressure)

    # Create simulation
    sim = SimulationResult(
        name="Simulation 2",
        simulation_type="CFD",
        mesh=sample_mesh,
    )
    sim.add_timestep(timestep)
    sim.id = "sim2"

    return sim


@pytest.fixture
def simulation3(sample_mesh: MeshData) -> SimulationResult:
    """Create third simulation"""
    # Create fields
    temperature = FieldData(
        name="temperature",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([302.0, 312.0, 322.0, 332.0], dtype=np.float32),
        unit="K",
    )
    pressure = FieldData(
        name="pressure",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([101020.0, 101120.0, 101220.0, 101320.0], dtype=np.float32),
        unit="Pa",
    )

    # Create timestep
    timestep = TimeStepData(time=0.0, step=0)
    timestep.add_field(temperature)
    timestep.add_field(pressure)

    # Create simulation
    sim = SimulationResult(
        name="Simulation 3",
        simulation_type="CFD",
        mesh=sample_mesh,
    )
    sim.add_timestep(timestep)
    sim.id = "sim3"

    return sim


@pytest.fixture
def comparator() -> SimulationComparator:
    """Create comparator instance"""
    return SimulationComparator()


def test_comparison_result_to_dict() -> None:
    """Test ComparisonResult.to_dict()"""
    result = ComparisonResult(
        simulation_ids=["sim1", "sim2"],
        field_name="temperature",
        comparison_type="field_comparison",
        mean_difference=5.0,
        max_difference=10.0,
        min_difference=2.0,
        rmse=6.0,
        correlation=0.98,
        difference_histogram={"counts": [1, 2, 3], "bin_edges": [0, 1, 2, 3]},
    )

    result_dict = result.to_dict()

    assert result_dict["simulation_ids"] == ["sim1", "sim2"]
    assert result_dict["field_name"] == "temperature"
    assert result_dict["mean_difference"] == 5.0
    assert result_dict["rmse"] == 6.0
    assert "compared_at" in result_dict


def test_compare_fields_basic(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult) -> None:
    """Test basic field comparison"""
    result = comparator.compare_fields(simulation1, simulation2, "temperature")

    assert result.simulation_ids == ["sim1", "sim2"]
    assert result.field_name == "temperature"
    assert result.comparison_type == "field_comparison"

    # Check that differences were calculated
    assert result.mean_difference == pytest.approx(5.0, abs=0.01)
    assert result.max_difference == pytest.approx(5.0, abs=0.01)
    assert result.min_difference == pytest.approx(5.0, abs=0.01)
    assert result.rmse == pytest.approx(5.0, abs=0.01)

    # Correlation should be high (values are highly correlated)
    assert result.correlation > 0.99

    # Check histogram
    assert result.difference_histogram is not None
    assert "counts" in result.difference_histogram
    assert "bin_edges" in result.difference_histogram


def test_compare_fields_identical(comparator: SimulationComparator, simulation1: SimulationResult) -> None:
    """Test comparing identical fields"""
    result = comparator.compare_fields(simulation1, simulation1, "temperature")

    assert result.mean_difference == pytest.approx(0.0, abs=1e-6)
    assert result.max_difference == pytest.approx(0.0, abs=1e-6)
    assert result.rmse == pytest.approx(0.0, abs=1e-6)
    assert result.correlation == pytest.approx(1.0, abs=1e-6)


def test_compare_fields_nonexistent_field(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult) -> None:
    """Test comparing nonexistent field"""
    with pytest.raises(ValueError, match="Field 'nonexistent' not found"):
        comparator.compare_fields(simulation1, simulation2, "nonexistent")


def test_compare_all_fields(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult) -> None:
    """Test comparing all fields"""
    results = comparator.compare_all_fields(simulation1, simulation2)

    # Should have all common fields
    assert "temperature" in results
    assert "pressure" in results

    # Each result should be a ComparisonResult
    for field_name, result in results.items():
        assert isinstance(result, ComparisonResult)
        assert result.field_name == field_name
        assert result.simulation_ids == ["sim1", "sim2"]


def test_compare_multiple(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult, simulation3: SimulationResult) -> None:
    """Test comparing multiple simulations"""
    simulations = [simulation1, simulation2, simulation3]

    result = comparator.compare_multiple(simulations, "temperature")

    assert result["simulation_ids"] == ["sim1", "sim2", "sim3"]
    assert result["field_name"] == "temperature"
    assert result["num_simulations"] == 3

    # Check statistics
    assert "mean_of_means" in result
    assert "mean_of_stds" in result
    assert "mean_range" in result
    assert "max_range" in result
    assert "correlation_matrix" in result

    # Correlation matrix should be 3x3
    corr_matrix = result["correlation_matrix"]
    assert len(corr_matrix) == 3
    assert len(corr_matrix[0]) == 3

    # Diagonal should be 1.0
    assert corr_matrix[0][0] == pytest.approx(1.0)
    assert corr_matrix[1][1] == pytest.approx(1.0)
    assert corr_matrix[2][2] == pytest.approx(1.0)


def test_compare_multiple_insufficient_simulations(comparator: SimulationComparator, simulation1: SimulationResult) -> None:
    """Test compare_multiple with less than 2 simulations"""
    with pytest.raises(ValueError, match="Need at least 2 simulations"):
        comparator.compare_multiple([simulation1], "temperature")


def test_calculate_convergence(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult, simulation3: SimulationResult) -> None:
    """Test convergence calculation"""
    simulations = [simulation1, simulation2, simulation3]

    result = comparator.calculate_convergence(simulations, "temperature")

    assert result["reference_simulation_id"] == "sim3"  # Last one by default
    assert result["field_name"] == "temperature"
    assert "metrics" in result

    # Should have metrics for all except the reference
    metrics = result["metrics"]
    assert len(metrics) == 2

    for metric in metrics:
        assert "simulation_id" in metric
        assert "l2_error" in metric
        assert "l_inf_error" in metric
        assert "relative_l2_error" in metric
        assert metric["l2_error"] >= 0
        assert metric["l_inf_error"] >= 0


def test_calculate_convergence_custom_reference(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult, simulation3: SimulationResult) -> None:
    """Test convergence calculation with custom reference"""
    simulations = [simulation1, simulation2, simulation3]

    result = comparator.calculate_convergence(simulations, "temperature", reference_idx=0)

    assert result["reference_simulation_id"] == "sim1"


def test_identify_differences(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult) -> None:
    """Test identifying significant differences"""
    result = comparator.identify_differences(
        simulation1, simulation2, "temperature", threshold=0.01
    )

    assert result["simulation_ids"] == ["sim1", "sim2"]
    assert result["field_name"] == "temperature"
    assert result["threshold"] == 0.01
    assert "num_significant_differences" in result
    assert "percentage_significant" in result
    assert "max_relative_difference" in result
    assert "mean_relative_difference" in result
    assert "difference_mask" in result


def test_identify_differences_high_threshold(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult) -> None:
    """Test identifying differences with high threshold"""
    # With high threshold, should find no significant differences
    result = comparator.identify_differences(simulation1, simulation2, "temperature", threshold=0.5)

    # Temperature difference is about 1.6%, so no points should exceed 50%
    assert result["num_significant_differences"] == 0
    assert result["percentage_significant"] == 0.0
    assert result["max_relative_difference"] == 0.0


def test_spatial_diff_map(comparator: SimulationComparator, simulation1: SimulationResult, simulation2: SimulationResult) -> None:
    """Test spatial difference map generation"""
    result = comparator.compare_fields(simulation1, simulation2, "temperature")

    assert result.spatial_diff_map is not None
    assert isinstance(result.spatial_diff_map, np.ndarray)
    # Check shape matches the field data shape
    assert result.spatial_diff_map.shape == (4,)


def test_no_timesteps_error(comparator: SimulationComparator, sample_mesh: MeshData) -> None:
    """Test error when simulation has no timesteps"""
    sim = SimulationResult(
        name="Empty",
        simulation_type="CFD",
        mesh=sample_mesh,
    )
    sim.id = "empty"

    with pytest.raises(ValueError, match="Timestep 0 not found"):
        comparator.compare_fields(sim, sim, "temperature")


def test_timestep_index(comparator: SimulationComparator, sample_mesh: MeshData) -> None:
    """Test comparing specific timestep"""
    # Create simulation with multiple timesteps
    sim1 = SimulationResult(name="Multi", simulation_type="CFD", mesh=sample_mesh)

    # Timestep 0
    ts0 = TimeStepData(time=0.0, step=0)
    temp0 = FieldData(
        name="temperature",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([300.0, 310.0, 320.0, 330.0], dtype=np.float32),
    )
    ts0.add_field(temp0)
    sim1.add_timestep(ts0)

    # Timestep 1
    ts1 = TimeStepData(time=1.0, step=1)
    temp1 = FieldData(
        name="temperature",
        field_type=FieldType.SCALAR,
        location=DataLocation.NODE,
        data=np.array([305.0, 315.0, 325.0, 335.0], dtype=np.float32),
    )
    ts1.add_field(temp1)
    sim1.add_timestep(ts1)
    sim1.id = "multi"

    # Compare timestep 0 with timestep 1 (using same simulation)
    # This should work since they're different timesteps
    result = comparator.compare_fields(sim1, sim1, "temperature", timestep=1)

    # Should compare timestep 1 with itself (zero difference)
    assert result.rmse == pytest.approx(0.0, abs=1e-6)
