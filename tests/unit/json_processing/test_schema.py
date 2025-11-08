"""
JSON 스키마 테스트
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.json_processing.schema import (
    SimulationMetadata,
    MeshInfo,
    MeshData,
    FieldMetadata,
    FieldData,
    ContourLevel,
    ContourData,
    TimeStep,
    SimulationResult,
    SchemaRegistry,
    CoordinateSystem,
    UnitSystem,
    DataType,
    MeshType,
    schema_registry,
)


class TestSimulationMetadata:
    """SimulationMetadata 테스트"""

    def test_create_metadata(self):
        """메타데이터 생성 테스트"""
        metadata = SimulationMetadata(
            name="CFD Simulation",
            solver="OpenFOAM",
            solver_version="8.0",
        )

        assert metadata.name == "CFD Simulation"
        assert metadata.solver == "OpenFOAM"
        assert metadata.coordinate_system == CoordinateSystem.CARTESIAN
        assert metadata.unit_system == UnitSystem.SI

    def test_metadata_with_custom_fields(self):
        """사용자 정의 메타데이터 테스트"""
        metadata = SimulationMetadata(
            name="Test",
            solver="ANSYS",
            custom_metadata={"mesh_size": 1e-3, "turbulence_model": "k-epsilon"},
        )

        assert metadata.custom_metadata["mesh_size"] == 1e-3
        assert metadata.custom_metadata["turbulence_model"] == "k-epsilon"


class TestMeshData:
    """MeshData 테스트"""

    def test_create_mesh(self):
        """메시 생성 테스트"""
        mesh_info = MeshInfo(
            mesh_type=MeshType.UNSTRUCTURED,
            num_vertices=100,
            num_cells=50,
            dimensions=3,
        )

        mesh = MeshData(
            info=mesh_info,
            vertices=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            cells=[0, 1, 2],
        )

        assert mesh.info.num_vertices == 100
        assert mesh.info.mesh_type == MeshType.UNSTRUCTURED
        assert len(mesh.vertices) == 9

    def test_mesh_validation(self):
        """메시 검증 테스트"""
        with pytest.raises(ValidationError):
            # 음수 정점 개수는 허용 안됨
            MeshInfo(
                mesh_type=MeshType.STRUCTURED,
                num_vertices=-1,
                num_cells=10,
                dimensions=2,
            )


class TestFieldData:
    """FieldData 테스트"""

    def test_scalar_field(self):
        """스칼라 필드 테스트"""
        metadata = FieldMetadata(
            name="temperature",
            data_type=DataType.SCALAR,
            unit="K",
            min_value=273.0,
            max_value=373.0,
            location="vertex",
        )

        field = FieldData(metadata=metadata, values=[300.0, 310.0, 320.0])

        assert field.metadata.name == "temperature"
        assert field.metadata.data_type == DataType.SCALAR
        assert len(field.values) == 3
        assert not field.compressed

    def test_vector_field(self):
        """벡터 필드 테스트"""
        metadata = FieldMetadata(
            name="velocity",
            data_type=DataType.VECTOR,
            unit="m/s",
            components=3,
            component_names=["vx", "vy", "vz"],
            location="cell",
        )

        field = FieldData(
            metadata=metadata,
            values=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        )

        assert field.metadata.components == 3
        assert len(field.metadata.component_names) == 3
        assert len(field.values) == 3


class TestContourData:
    """ContourData 테스트"""

    def test_contour_levels(self):
        """컨투어 레벨 테스트"""
        level1 = ContourLevel(
            value=300.0, num_points=10, points=[0.0, 0.0, 1.0, 0.0, 1.0, 1.0], is_closed=True
        )

        level2 = ContourLevel(
            value=310.0, num_points=8, points=[0.5, 0.5, 1.5, 0.5], is_closed=False
        )

        contour = ContourData(field_name="temperature", unit="K", levels=[level1, level2])

        assert len(contour.levels) == 2
        assert contour.levels[0].value == 300.0
        assert contour.levels[1].is_closed == False

    def test_compressed_contour(self):
        """압축된 컨투어 테스트"""
        contour = ContourData(
            field_name="pressure",
            unit="Pa",
            levels=[],
            compressed=True,
            latent_representation=[0.1, 0.2, 0.3, 0.4],
        )

        assert contour.compressed
        assert len(contour.latent_representation) == 4


class TestTimeStep:
    """TimeStep 테스트"""

    def test_time_step(self):
        """시간 단계 테스트"""
        field_meta = FieldMetadata(
            name="temperature", data_type=DataType.SCALAR, unit="K", location="vertex"
        )
        field = FieldData(metadata=field_meta, values=[300.0, 310.0])

        timestep = TimeStep(step=0, time=0.0, time_unit="s", fields={"temperature": field})

        assert timestep.step == 0
        assert timestep.time == 0.0
        assert "temperature" in timestep.fields


class TestSimulationResult:
    """SimulationResult 테스트"""

    def test_steady_state_simulation(self):
        """정상 상태 시뮬레이션 테스트"""
        metadata = SimulationMetadata(name="Steady CFD", solver="OpenFOAM")

        mesh_info = MeshInfo(
            mesh_type=MeshType.STRUCTURED, num_vertices=100, num_cells=50, dimensions=2
        )
        mesh = MeshData(info=mesh_info, vertices=[0.0] * 300, cells=[0] * 150)

        field_meta = FieldMetadata(
            name="pressure", data_type=DataType.SCALAR, unit="Pa", location="cell"
        )
        field = FieldData(metadata=field_meta, values=[101325.0] * 50)

        result = SimulationResult(
            metadata=metadata,
            mesh=mesh,
            steady_state=True,
            fields={"pressure": field},
        )

        assert result.steady_state
        assert "pressure" in result.fields
        assert result.time_steps is None

    def test_transient_simulation(self):
        """비정상 상태 시뮬레이션 테스트"""
        metadata = SimulationMetadata(name="Transient CFD", solver="ANSYS")

        mesh_info = MeshInfo(
            mesh_type=MeshType.UNSTRUCTURED, num_vertices=50, num_cells=25, dimensions=3
        )
        mesh = MeshData(info=mesh_info, vertices=[0.0] * 150, cells=[0] * 75)

        timestep1 = TimeStep(step=0, time=0.0, time_unit="s")
        timestep2 = TimeStep(step=1, time=0.001, time_unit="s")

        result = SimulationResult(
            metadata=metadata,
            mesh=mesh,
            steady_state=False,
            time_steps=[timestep1, timestep2],
        )

        assert not result.steady_state
        assert len(result.time_steps) == 2

    def test_transient_without_timesteps_fails(self):
        """비정상 상태인데 time_steps 없으면 실패"""
        metadata = SimulationMetadata(name="Test", solver="Test")
        mesh_info = MeshInfo(
            mesh_type=MeshType.STRUCTURED, num_vertices=10, num_cells=5, dimensions=2
        )
        mesh = MeshData(info=mesh_info, vertices=[0.0] * 30, cells=[0] * 15)

        with pytest.raises(ValidationError):
            SimulationResult(metadata=metadata, mesh=mesh, steady_state=False, time_steps=None)


class TestSchemaRegistry:
    """SchemaRegistry 테스트"""

    def test_registry_initialization(self):
        """레지스트리 초기화 테스트"""
        registry = SchemaRegistry()
        schemas = registry.list_schemas()

        assert "simulation_result" in schemas
        assert "simulation_metadata" in schemas
        assert "field_data" in schemas

    def test_get_schema(self):
        """스키마 조회 테스트"""
        registry = SchemaRegistry()
        schema = registry.get_schema("simulation_metadata")

        assert schema == SimulationMetadata

    def test_get_nonexistent_schema(self):
        """존재하지 않는 스키마 조회"""
        registry = SchemaRegistry()

        with pytest.raises(KeyError):
            registry.get_schema("nonexistent")

    def test_register_custom_schema(self):
        """커스텀 스키마 등록 테스트"""
        from pydantic import BaseModel

        class CustomSchema(BaseModel):
            name: str
            value: int

        registry = SchemaRegistry()
        registry.register_schema("custom", CustomSchema)

        assert "custom" in registry.list_schemas()
        assert registry.get_schema("custom") == CustomSchema

    def test_validate_data(self):
        """데이터 검증 테스트"""
        registry = SchemaRegistry()

        data = {
            "name": "Test Sim",
            "solver": "OpenFOAM",
        }

        validated = registry.validate("simulation_metadata", data)

        assert isinstance(validated, SimulationMetadata)
        assert validated.name == "Test Sim"

    def test_validate_invalid_data(self):
        """잘못된 데이터 검증 실패"""
        registry = SchemaRegistry()

        invalid_data = {
            # name 필드 누락
            "solver": "OpenFOAM",
        }

        with pytest.raises(ValidationError):
            registry.validate("simulation_metadata", invalid_data)

    def test_unregister_schema(self):
        """스키마 등록 해제 테스트"""
        from pydantic import BaseModel

        class TempSchema(BaseModel):
            value: int

        registry = SchemaRegistry()
        registry.register_schema("temp", TempSchema)

        assert "temp" in registry.list_schemas()

        registry.unregister_schema("temp")

        assert "temp" not in registry.list_schemas()


class TestGlobalRegistry:
    """전역 레지스트리 테스트"""

    def test_global_registry_exists(self):
        """전역 레지스트리가 존재하는지 확인"""
        assert schema_registry is not None
        assert isinstance(schema_registry, SchemaRegistry)

    def test_global_registry_has_schemas(self):
        """전역 레지스트리에 기본 스키마가 있는지 확인"""
        schemas = schema_registry.list_schemas()
        assert len(schemas) > 0
        assert "simulation_result" in schemas
