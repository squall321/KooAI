"""
Tests for Core Domain Entities

Tests SimulationResult, AnalysisStatus, and other domain entities.
"""

from datetime import datetime
from uuid import UUID
import pytest


class TestSimulationStatus:
    """Test SimulationStatus enum"""

    def test_simulation_status_values(self) -> None:
        """Test SimulationStatus enum values"""
        from src.core.domain.entities import SimulationStatus

        assert SimulationStatus.PENDING.value == "pending"
        assert SimulationStatus.PROCESSING.value == "processing"
        assert SimulationStatus.COMPLETED.value == "completed"
        assert SimulationStatus.FAILED.value == "failed"
        assert SimulationStatus.CANCELLED.value == "cancelled"


class TestAnalysisStatus:
    """Test AnalysisStatus enum"""

    def test_analysis_status_values(self) -> None:
        """Test AnalysisStatus enum values"""
        from src.core.domain.entities import AnalysisStatus

        assert AnalysisStatus.PENDING.value == "pending"
        assert AnalysisStatus.RUNNING.value == "running"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"


class TestSimulationResult:
    """Test SimulationResult entity"""

    def test_simulation_result_creation(self) -> None:
        """Test creating SimulationResult entity"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test Simulation", type="CFD")

        assert sim.name == "Test Simulation"
        assert sim.type == "CFD"
        assert sim.status == SimulationStatus.PENDING
        assert isinstance(sim.id, UUID)
        assert isinstance(sim.created_at, datetime)

    def test_simulation_result_with_parameters(self) -> None:
        """Test SimulationResult with parameters"""
        from src.core.domain.entities import SimulationResult

        params = {"reynolds": 1000, "mach": 0.3}
        sim = SimulationResult(
            name="Test Sim", type="CFD", parameters=params
        )

        assert sim.parameters == params

    def test_simulation_result_with_metadata(self) -> None:
        """Test SimulationResult with metadata"""
        from src.core.domain.entities import SimulationResult

        metadata = {"solver": "OpenFOAM", "version": "8.0"}
        sim = SimulationResult(
            name="Test Sim", type="CFD", metadata=metadata
        )

        assert sim.metadata == metadata

    def test_simulation_result_with_tags(self) -> None:
        """Test SimulationResult with tags"""
        from src.core.domain.entities import SimulationResult

        tags = ["turbulent", "high-speed"]
        sim = SimulationResult(
            name="Test Sim", type="CFD", tags=tags
        )

        assert sim.tags == tags

    def test_simulation_result_empty_name_raises_error(self) -> None:
        """Test empty name raises ValueError"""
        from src.core.domain.entities import SimulationResult

        with pytest.raises(ValueError, match="name cannot be empty"):
            SimulationResult(name="", type="CFD")

    def test_simulation_result_empty_type_raises_error(self) -> None:
        """Test empty type raises ValueError"""
        from src.core.domain.entities import SimulationResult

        with pytest.raises(ValueError, match="type cannot be empty"):
            SimulationResult(name="Test", type="")

    def test_simulation_result_long_name_raises_error(self) -> None:
        """Test name too long raises ValueError"""
        from src.core.domain.entities import SimulationResult

        long_name = "x" * 256

        with pytest.raises(ValueError, match="name too long"):
            SimulationResult(name=long_name, type="CFD")

    def test_mark_as_processing(self) -> None:
        """Test marking simulation as processing"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test", type="CFD")
        original_updated_at = sim.updated_at

        sim.mark_as_processing()

        assert sim.status == SimulationStatus.PROCESSING
        assert sim.updated_at >= original_updated_at

    def test_mark_as_processing_from_wrong_status_raises_error(self) -> None:
        """Test marking as processing from wrong status raises error"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test", type="CFD")
        sim.status = SimulationStatus.COMPLETED

        with pytest.raises(ValueError, match="Cannot mark as processing"):
            sim.mark_as_processing()

    def test_mark_as_completed(self) -> None:
        """Test marking simulation as completed"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test", type="CFD")
        sim.mark_as_processing()

        sim.mark_as_completed()

        assert sim.status == SimulationStatus.COMPLETED

    def test_mark_as_completed_from_wrong_status_raises_error(self) -> None:
        """Test marking as completed from wrong status raises error"""
        from src.core.domain.entities import SimulationResult

        sim = SimulationResult(name="Test", type="CFD")

        with pytest.raises(ValueError, match="Cannot mark as completed"):
            sim.mark_as_completed()

    def test_mark_as_failed(self) -> None:
        """Test marking simulation as failed"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test", type="CFD")

        sim.mark_as_failed("Out of memory")

        assert sim.status == SimulationStatus.FAILED
        assert sim.metadata["error"] == "Out of memory"
        assert "failed_at" in sim.metadata

    def test_cancel_simulation(self) -> None:
        """Test cancelling simulation"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test", type="CFD")
        sim.mark_as_processing()

        sim.cancel()

        assert sim.status == SimulationStatus.CANCELLED

    def test_cancel_completed_simulation_raises_error(self) -> None:
        """Test cancelling completed simulation raises error"""
        from src.core.domain.entities import SimulationResult

        sim = SimulationResult(name="Test", type="CFD")
        sim.mark_as_processing()
        sim.mark_as_completed()

        with pytest.raises(ValueError, match="Cannot cancel"):
            sim.cancel()

    def test_add_tag(self) -> None:
        """Test adding tag to simulation"""
        from src.core.domain.entities import SimulationResult

        sim = SimulationResult(name="Test", type="CFD")

        sim.add_tag("turbulent")

        assert "turbulent" in sim.tags

    def test_add_duplicate_tag(self) -> None:
        """Test adding duplicate tag doesn't duplicate"""
        from src.core.domain.entities import SimulationResult

        sim = SimulationResult(name="Test", type="CFD", tags=["turbulent"])

        sim.add_tag("turbulent")

        assert sim.tags.count("turbulent") == 1

    def test_simulation_result_default_values(self) -> None:
        """Test SimulationResult default values"""
        from src.core.domain.entities import SimulationResult, SimulationStatus

        sim = SimulationResult(name="Test", type="CFD")

        assert sim.parameters == {}
        assert sim.metadata == {}
        assert sim.tags == []
        assert sim.status == SimulationStatus.PENDING
        assert sim.created_by is None
        assert sim.description is None
