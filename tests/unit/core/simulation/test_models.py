"""
Tests for Core Simulation Models

Tests FieldData, MeshData, TimeStepData, and SimulationResult models.
"""

from datetime import datetime
from pathlib import Path
import pytest
import numpy as np


class TestFieldType:
    """Test FieldType enum"""

    def test_field_type_values(self):
        """Test FieldType enum values"""
        from src.core.simulation.models import FieldType

        assert FieldType.SCALAR.value == "scalar"
        assert FieldType.VECTOR.value == "vector"
        assert FieldType.TENSOR.value == "tensor"


class TestDataLocation:
    """Test DataLocation enum"""

    def test_data_location_values(self):
        """Test DataLocation enum values"""
        from src.core.simulation.models import DataLocation

        assert DataLocation.NODE.value == "node"
        assert DataLocation.CELL.value == "cell"
        assert DataLocation.POINT.value == "point"


class TestFieldData:
    """Test FieldData model"""

    def test_field_data_creation_scalar(self):
        """Test creating scalar FieldData"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([1.0, 2.0, 3.0, 4.0])
        field = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data
        )

        assert field.name == "temperature"
        assert field.field_type == FieldType.SCALAR
        assert field.location == DataLocation.POINT
        assert field.size == 4

    def test_field_data_creation_vector(self):
        """Test creating vector FieldData"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        field = FieldData(
            name="velocity",
            field_type=FieldType.VECTOR,
            location=DataLocation.POINT,
            data=data
        )

        assert field.name == "velocity"
        assert field.field_type == FieldType.VECTOR
        assert field.data.shape == (2, 3)

    def test_field_data_with_unit(self):
        """Test FieldData with unit"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([300.0, 310.0])
        field = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data,
            unit="K"
        )

        assert field.unit == "K"

    def test_field_data_with_description(self):
        """Test FieldData with description"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([1.0, 2.0])
        field = FieldData(
            name="pressure",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data,
            description="Static pressure"
        )

        assert field.description == "Static pressure"

    def test_field_data_scalar_validation_fails_for_2d(self):
        """Test scalar field validation fails for 2D data"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([[1.0, 2.0], [3.0, 4.0]])

        with pytest.raises(ValueError, match="Scalar field must be 1D"):
            FieldData(
                name="test",
                field_type=FieldType.SCALAR,
                location=DataLocation.POINT,
                data=data
            )

    def test_field_data_vector_validation_fails_for_1d(self):
        """Test vector field validation fails for 1D data"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Vector field must be Nx3"):
            FieldData(
                name="test",
                field_type=FieldType.VECTOR,
                location=DataLocation.POINT,
                data=data
            )

    def test_field_data_vector_validation_fails_for_wrong_shape(self):
        """Test vector field validation fails for wrong shape"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([[1.0, 2.0], [3.0, 4.0]])  # Nx2 instead of Nx3

        with pytest.raises(ValueError, match="Vector field must be Nx3"):
            FieldData(
                name="test",
                field_type=FieldType.VECTOR,
                location=DataLocation.POINT,
                data=data
            )

    def test_field_data_get_min(self):
        """Test get_min method"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([10.0, 5.0, 20.0, 3.0])
        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data
        )

        assert field.get_min() == 3.0

    def test_field_data_get_max(self):
        """Test get_max method"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([10.0, 5.0, 20.0, 3.0])
        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data
        )

        assert field.get_max() == 20.0

    def test_field_data_get_mean(self):
        """Test get_mean method"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([10.0, 20.0, 30.0])
        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data
        )

        assert field.get_mean() == 20.0

    def test_field_data_get_std(self):
        """Test get_std method"""
        from src.core.simulation.models import FieldData, FieldType, DataLocation

        data = np.array([10.0, 20.0, 30.0])
        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=data
        )

        std = field.get_std()
        assert std > 0  # Standard deviation should be positive


class TestMeshData:
    """Test MeshData model"""

    def test_mesh_data_creation(self):
        """Test creating MeshData"""
        from src.core.simulation.models import MeshData

        vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        mesh = MeshData(vertices=vertices)

        assert mesh.num_vertices == 3
        assert mesh.vertices.shape == (3, 3)

    def test_mesh_data_with_cells(self):
        """Test MeshData with cells"""
        from src.core.simulation.models import MeshData

        vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        cells = np.array([[0, 1]])
        mesh = MeshData(vertices=vertices, cells=cells)

        assert mesh.num_cells == 1

    def test_mesh_data_with_faces(self):
        """Test MeshData with faces"""
        from src.core.simulation.models import MeshData

        vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        faces = np.array([[0, 1, 2]])
        mesh = MeshData(vertices=vertices, faces=faces)

        assert mesh.num_faces == 1

    def test_mesh_data_validation_fails_for_wrong_shape(self):
        """Test MeshData validation fails for wrong vertex shape"""
        from src.core.simulation.models import MeshData

        vertices = np.array([[0.0, 0.0], [1.0, 1.0]])  # Nx2 instead of Nx3

        with pytest.raises(ValueError, match="Vertices must be Nx3"):
            MeshData(vertices=vertices)

    def test_mesh_data_get_bounds(self):
        """Test get_bounds method"""
        from src.core.simulation.models import MeshData

        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 2.0, 3.0],
            [-1.0, -2.0, -3.0]
        ])
        mesh = MeshData(vertices=vertices)

        min_point, max_point = mesh.get_bounds()

        assert np.allclose(min_point, [-1.0, -2.0, -3.0])
        assert np.allclose(max_point, [1.0, 2.0, 3.0])

    def test_mesh_data_num_cells_zero_when_none(self):
        """Test num_cells returns 0 when cells is None"""
        from src.core.simulation.models import MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)

        assert mesh.num_cells == 0

    def test_mesh_data_num_faces_zero_when_none(self):
        """Test num_faces returns 0 when faces is None"""
        from src.core.simulation.models import MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)

        assert mesh.num_faces == 0


class TestTimeStepData:
    """Test TimeStepData model"""

    def test_timestep_data_creation(self):
        """Test creating TimeStepData"""
        from src.core.simulation.models import TimeStepData

        timestep = TimeStepData(time=1.5, step=10)

        assert timestep.time == 1.5
        assert timestep.step == 10
        assert len(timestep.fields) == 0

    def test_timestep_add_field(self):
        """Test adding field to timestep"""
        from src.core.simulation.models import (
            TimeStepData, FieldData, FieldType, DataLocation
        )

        timestep = TimeStepData(time=0.0, step=0)
        field = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=np.array([300.0])
        )

        timestep.add_field(field)

        assert len(timestep.fields) == 1
        assert "temperature" in timestep.fields

    def test_timestep_get_field(self):
        """Test getting field from timestep"""
        from src.core.simulation.models import (
            TimeStepData, FieldData, FieldType, DataLocation
        )

        timestep = TimeStepData(time=0.0, step=0)
        field = FieldData(
            name="pressure",
            field_type=FieldType.SCALAR,
            location=DataLocation.POINT,
            data=np.array([101325.0])
        )
        timestep.add_field(field)

        retrieved = timestep.get_field("pressure")

        assert retrieved is not None
        assert retrieved.name == "pressure"

    def test_timestep_get_field_returns_none_if_not_found(self):
        """Test get_field returns None for non-existent field"""
        from src.core.simulation.models import TimeStepData

        timestep = TimeStepData(time=0.0, step=0)

        result = timestep.get_field("nonexistent")

        assert result is None

    def test_timestep_has_field(self):
        """Test has_field method"""
        from src.core.simulation.models import (
            TimeStepData, FieldData, FieldType, DataLocation
        )

        timestep = TimeStepData(time=0.0, step=0)
        field = FieldData(
            name="velocity",
            field_type=FieldType.VECTOR,
            location=DataLocation.POINT,
            data=np.array([[1.0, 2.0, 3.0]])
        )
        timestep.add_field(field)

        assert timestep.has_field("velocity") is True
        assert timestep.has_field("nonexistent") is False

    def test_timestep_list_fields(self):
        """Test list_fields method"""
        from src.core.simulation.models import (
            TimeStepData, FieldData, FieldType, DataLocation
        )

        timestep = TimeStepData(time=0.0, step=0)

        field1 = FieldData("temp", FieldType.SCALAR, DataLocation.POINT, np.array([1.0]))
        field2 = FieldData("pressure", FieldType.SCALAR, DataLocation.POINT, np.array([2.0]))

        timestep.add_field(field1)
        timestep.add_field(field2)

        fields = timestep.list_fields()

        assert len(fields) == 2
        assert "temp" in fields
        assert "pressure" in fields

    def test_timestep_metadata(self):
        """Test timestep metadata"""
        from src.core.simulation.models import TimeStepData

        timestep = TimeStepData(
            time=0.0,
            step=0,
            metadata={"solver": "OpenFOAM", "iterations": 100}
        )

        assert timestep.metadata["solver"] == "OpenFOAM"
        assert timestep.metadata["iterations"] == 100


class TestSimulationResult:
    """Test SimulationResult model"""

    def test_simulation_result_creation(self):
        """Test creating SimulationResult"""
        from src.core.simulation.models import SimulationResult, MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)

        result = SimulationResult(
            name="Test Simulation",
            simulation_type="CFD",
            mesh=mesh
        )

        assert result.name == "Test Simulation"
        assert result.simulation_type == "CFD"
        assert result.num_timesteps == 0

    def test_simulation_result_add_timestep(self):
        """Test adding timestep to simulation"""
        from src.core.simulation.models import SimulationResult, MeshData, TimeStepData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        timestep = TimeStepData(time=0.0, step=0)
        result.add_timestep(timestep)

        assert result.num_timesteps == 1

    def test_simulation_result_get_timestep_by_step(self):
        """Test getting timestep by step number"""
        from src.core.simulation.models import SimulationResult, MeshData, TimeStepData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        ts1 = TimeStepData(time=0.0, step=0)
        ts2 = TimeStepData(time=0.5, step=1)
        result.add_timestep(ts1)
        result.add_timestep(ts2)

        retrieved = result.get_timestep(1)

        assert retrieved is not None
        assert retrieved.step == 1
        assert retrieved.time == 0.5

    def test_simulation_result_get_timestep_returns_none_if_not_found(self):
        """Test get_timestep returns None for non-existent step"""
        from src.core.simulation.models import SimulationResult, MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        retrieved = result.get_timestep(999)

        assert retrieved is None

    def test_simulation_result_get_timestep_by_time(self):
        """Test getting timestep by time value"""
        from src.core.simulation.models import SimulationResult, MeshData, TimeStepData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        ts = TimeStepData(time=1.5, step=0)
        result.add_timestep(ts)

        retrieved = result.get_timestep_by_time(1.5)

        assert retrieved is not None
        assert retrieved.time == 1.5

    def test_simulation_result_get_timestep_by_time_with_tolerance(self):
        """Test getting timestep by time with tolerance"""
        from src.core.simulation.models import SimulationResult, MeshData, TimeStepData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        ts = TimeStepData(time=1.5, step=0)
        result.add_timestep(ts)

        # Should find timestep within tolerance
        retrieved = result.get_timestep_by_time(1.5000001, tolerance=1e-5)

        assert retrieved is not None

    def test_simulation_result_time_range(self):
        """Test time_range property"""
        from src.core.simulation.models import SimulationResult, MeshData, TimeStepData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        result.add_timestep(TimeStepData(time=0.0, step=0))
        result.add_timestep(TimeStepData(time=0.5, step=1))
        result.add_timestep(TimeStepData(time=1.0, step=2))

        min_time, max_time = result.time_range

        assert min_time == 0.0
        assert max_time == 1.0

    def test_simulation_result_time_range_empty(self):
        """Test time_range with no timesteps"""
        from src.core.simulation.models import SimulationResult, MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        min_time, max_time = result.time_range

        assert min_time == 0.0
        assert max_time == 0.0

    def test_simulation_result_with_metadata(self):
        """Test SimulationResult with metadata"""
        from src.core.simulation.models import SimulationResult, MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)

        metadata = {"solver": "OpenFOAM", "version": "8.0"}
        result = SimulationResult(
            name="Test",
            simulation_type="CFD",
            mesh=mesh,
            metadata=metadata
        )

        assert result.metadata["solver"] == "OpenFOAM"
        assert result.metadata["version"] == "8.0"

    def test_simulation_result_with_source_file(self):
        """Test SimulationResult with source file"""
        from src.core.simulation.models import SimulationResult, MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)

        source = Path("/path/to/simulation.csv")
        result = SimulationResult(
            name="Test",
            simulation_type="CFD",
            mesh=mesh,
            source_file=source
        )

        assert result.source_file == source

    def test_simulation_result_created_at_is_datetime(self):
        """Test created_at is datetime"""
        from src.core.simulation.models import SimulationResult, MeshData

        vertices = np.array([[0.0, 0.0, 0.0]])
        mesh = MeshData(vertices=vertices)
        result = SimulationResult(name="Test", simulation_type="CFD", mesh=mesh)

        assert isinstance(result.created_at, datetime)
