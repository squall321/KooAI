"""시뮬레이션 결과 처리 시스템 통합 테스트"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.core.simulation import (
    CSVParser,
    DataLocation,
    FieldData,
    FieldType,
    MeshData,
    ParserRegistry,
    ResultAnalyzer,
    SimulationResult,
    SpatialAnalyzer,
    TimeStepData,
    VTKParser,
)


class TestFieldData:
    """필드 데이터 테스트"""

    def test_scalar_field(self):
        """스칼라 필드 생성 및 통계"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        field = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=data,
            unit="K",
        )

        assert field.name == "temperature"
        assert field.size == 5
        assert field.get_min() == 1.0
        assert field.get_max() == 5.0
        assert field.get_mean() == 3.0

    def test_vector_field(self):
        """벡터 필드 생성 및 통계"""
        data = np.array([[1, 0, 0], [0, 2, 0], [0, 0, 3]], dtype=float)

        field = FieldData(
            name="velocity",
            field_type=FieldType.VECTOR,
            location=DataLocation.NODE,
            data=data,
            unit="m/s",
        )

        assert field.name == "velocity"
        assert field.size == 3
        assert field.data.shape == (3, 3)

    def test_invalid_scalar_field(self):
        """잘못된 스칼라 필드"""
        data = np.array([[1, 2], [3, 4]])  # 2D는 스칼라에 적합하지 않음

        with pytest.raises(ValueError):
            FieldData(
                name="test",
                field_type=FieldType.SCALAR,
                location=DataLocation.NODE,
                data=data,
            )

    def test_invalid_vector_field(self):
        """잘못된 벡터 필드"""
        data = np.array([1, 2, 3])  # 1D는 벡터에 적합하지 않음

        with pytest.raises(ValueError):
            FieldData(
                name="test",
                field_type=FieldType.VECTOR,
                location=DataLocation.NODE,
                data=data,
            )


class TestMeshData:
    """메시 데이터 테스트"""

    def test_mesh_creation(self):
        """메시 생성"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)

        mesh = MeshData(vertices=vertices)

        assert mesh.num_vertices == 3
        assert mesh.num_cells == 0
        assert mesh.num_faces == 0

    def test_mesh_with_faces(self):
        """면이 있는 메시"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)

        faces = np.array([[0, 1, 2]])

        mesh = MeshData(vertices=vertices, faces=faces)

        assert mesh.num_vertices == 3
        assert mesh.num_faces == 1

    def test_bounding_box(self):
        """바운딩 박스"""
        vertices = np.array([[0, 0, 0], [2, 3, 4], [-1, -2, -3]], dtype=float)

        mesh = MeshData(vertices=vertices)

        min_point, max_point = mesh.get_bounds()

        assert np.allclose(min_point, [-1, -2, -3])
        assert np.allclose(max_point, [2, 3, 4])


class TestSimulationResult:
    """시뮬레이션 결과 테스트"""

    def test_result_creation(self):
        """결과 생성"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
        mesh = MeshData(vertices=vertices)

        result = SimulationResult(
            name="test_simulation",
            simulation_type="CFD",
            mesh=mesh,
        )

        assert result.name == "test_simulation"
        assert result.simulation_type == "CFD"
        assert result.num_timesteps == 0

    def test_add_timestep(self):
        """타임스텝 추가"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
        mesh = MeshData(vertices=vertices)

        result = SimulationResult(
            name="test",
            simulation_type="CFD",
            mesh=mesh,
        )

        # 타임스텝 추가
        ts1 = TimeStepData(time=0.0, step=0)
        ts2 = TimeStepData(time=1.0, step=1)

        result.add_timestep(ts1)
        result.add_timestep(ts2)

        assert result.num_timesteps == 2
        assert result.time_range == (0.0, 1.0)

    def test_timestep_with_fields(self):
        """필드가 있는 타임스텝"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
        mesh = MeshData(vertices=vertices)

        result = SimulationResult(
            name="test",
            simulation_type="CFD",
            mesh=mesh,
        )

        # 필드 생성
        temperature = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=np.array([300.0, 310.0, 320.0]),
        )

        # 타임스텝에 필드 추가
        ts = TimeStepData(time=0.0, step=0)
        ts.add_field(temperature)

        result.add_timestep(ts)

        # 필드 조회
        assert result.list_all_fields() == ["temperature"]

        retrieved_ts = result.get_timestep(0)
        assert retrieved_ts is not None
        assert retrieved_ts.has_field("temperature")


class TestCSVParser:
    """CSV 파서 테스트"""

    def test_can_parse(self):
        """CSV 파일 인식"""
        parser = CSVParser()

        csv_file = Path("test.csv")
        txt_file = Path("test.txt")

        assert parser.can_parse(csv_file)
        assert not parser.can_parse(txt_file)

    def test_parse_simple_csv(self):
        """간단한 CSV 파싱"""
        parser = CSVParser()

        # 테스트 CSV 파일 생성
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("x,y,z,temperature\n")
            f.write("0.0,0.0,0.0,300.0\n")
            f.write("1.0,0.0,0.0,310.0\n")
            f.write("0.0,1.0,0.0,320.0\n")
            csv_path = Path(f.name)

        try:
            result = parser.parse(csv_path)

            assert result.name == csv_path.stem
            assert result.simulation_type == "CSV"
            assert result.mesh.num_vertices == 3
            assert result.num_timesteps == 1

            # 필드 확인
            ts = result.timesteps[0]
            assert ts.has_field("temperature")

            temp_field = ts.get_field("temperature")
            assert temp_field.field_type == FieldType.SCALAR
            assert len(temp_field.data) == 3

        finally:
            csv_path.unlink()

    def test_parse_vector_field_csv(self):
        """벡터 필드가 있는 CSV 파싱"""
        parser = CSVParser()

        # 벡터 필드가 있는 CSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("x,y,z,velocity_x,velocity_y,velocity_z\n")
            f.write("0.0,0.0,0.0,1.0,0.0,0.0\n")
            f.write("1.0,0.0,0.0,2.0,1.0,0.0\n")
            csv_path = Path(f.name)

        try:
            result = parser.parse(csv_path)

            # 벡터 필드 확인
            ts = result.timesteps[0]
            assert ts.has_field("velocity")

            vel_field = ts.get_field("velocity")
            assert vel_field.field_type == FieldType.VECTOR
            assert vel_field.data.shape == (2, 3)

        finally:
            csv_path.unlink()


class TestVTKParser:
    """VTK 파서 테스트"""

    def test_can_parse(self):
        """VTK 파일 인식"""
        parser = VTKParser()

        # VTK 파일 생성
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vtk", delete=False
        ) as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Test VTK\n")
            f.write("ASCII\n")
            vtk_path = Path(f.name)

        try:
            assert parser.can_parse(vtk_path)
        finally:
            vtk_path.unlink()

    def test_parse_polydata(self):
        """POLYDATA 파싱"""
        parser = VTKParser()

        # POLYDATA VTK 파일
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vtk", delete=False
        ) as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Test Polydata\n")
            f.write("ASCII\n")
            f.write("DATASET POLYDATA\n")
            f.write("POINTS 3 float\n")
            f.write("0.0 0.0 0.0\n")
            f.write("1.0 0.0 0.0\n")
            f.write("0.0 1.0 0.0\n")
            f.write("POLYGONS 1 4\n")
            f.write("3 0 1 2\n")
            f.write("POINT_DATA 3\n")
            f.write("SCALARS temperature float 1\n")
            f.write("LOOKUP_TABLE default\n")
            f.write("300.0\n310.0\n320.0\n")
            vtk_path = Path(f.name)

        try:
            result = parser.parse(vtk_path)

            assert result.simulation_type == "VTK"
            assert result.mesh.num_vertices == 3
            assert result.mesh.num_faces == 1

            # 필드 확인
            ts = result.timesteps[0]
            assert ts.has_field("temperature")

            temp_field = ts.get_field("temperature")
            assert temp_field.field_type == FieldType.SCALAR
            assert len(temp_field.data) == 3

        finally:
            vtk_path.unlink()


class TestParserRegistry:
    """파서 레지스트리 테스트"""

    def test_register_and_get_parser(self):
        """파서 등록 및 조회"""
        registry = ParserRegistry()

        csv_parser = CSVParser()
        vtk_parser = VTKParser()

        registry.register(csv_parser)
        registry.register(vtk_parser)

        # CSV 파일용 파서
        csv_file = Path("test.csv")
        parser = registry.get_parser(csv_file)
        assert isinstance(parser, CSVParser)

        # VTK 파일용 파서 (헤더 확인이 필요하므로 실제 파일 필요)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vtk", delete=False
        ) as f:
            f.write("# vtk DataFile Version 3.0\n")
            vtk_path = Path(f.name)

        try:
            parser = registry.get_parser(vtk_path)
            assert isinstance(parser, VTKParser)
        finally:
            vtk_path.unlink()


class TestResultAnalyzer:
    """결과 분석기 테스트"""

    def test_field_statistics(self):
        """필드 통계 계산"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=data,
        )

        stats = ResultAnalyzer.compute_field_statistics(field)

        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0

    def test_vector_field_statistics(self):
        """벡터 필드 통계 (크기 기준)"""
        data = np.array([[3, 0, 0], [0, 4, 0], [0, 0, 5]], dtype=float)

        field = FieldData(
            name="velocity",
            field_type=FieldType.VECTOR,
            location=DataLocation.NODE,
            data=data,
        )

        stats = ResultAnalyzer.compute_field_statistics(field)

        # 벡터 크기: [3, 4, 5]
        assert stats["min"] == 3.0
        assert stats["max"] == 5.0
        assert stats["mean"] == 4.0

    def test_find_extreme_values(self):
        """극값 찾기"""
        data = np.array([1, 5, 2, 8, 3, 9, 4, 7, 6], dtype=float)

        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=data,
        )

        max_indices, min_indices = ResultAnalyzer.find_extreme_values(field, n_extremes=3)

        # 최댓값: 9(idx=5), 8(idx=3), 7(idx=7)
        assert 5 in max_indices
        assert 3 in max_indices
        assert 7 in max_indices

        # 최솟값: 1(idx=0), 2(idx=2), 3(idx=4)
        assert 0 in min_indices
        assert 2 in min_indices
        assert 4 in min_indices

    def test_detect_outliers(self):
        """이상치 탐지"""
        # 정규 분포 + 이상치
        data = np.array([1, 2, 3, 4, 5, 100], dtype=float)  # 100은 이상치

        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=data,
        )

        outliers = ResultAnalyzer.detect_outliers(field, threshold=2.0)

        # 100이 이상치로 감지됨
        assert 5 in outliers

    def test_compute_timestep_metrics(self):
        """타임스텝 메트릭 계산"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
        mesh = MeshData(vertices=vertices)

        result = SimulationResult(
            name="test",
            simulation_type="CFD",
            mesh=mesh,
        )

        # 필드 생성
        temperature = FieldData(
            name="temperature",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=np.array([300.0, 310.0, 320.0]),
        )

        # 타임스텝
        ts = TimeStepData(time=0.0, step=0)
        ts.add_field(temperature)

        metrics = ResultAnalyzer.compute_timestep_metrics(result, ts)

        assert metrics.result_name == "test"
        assert metrics.timestep == 0

        temp_stats = metrics.get_field_stats("temperature")
        assert temp_stats["min"] == 300.0
        assert temp_stats["max"] == 320.0
        assert temp_stats["mean"] == 310.0


class TestSpatialAnalyzer:
    """공간 분석기 테스트"""

    def test_region_statistics(self):
        """영역 통계"""
        data = np.array([1, 2, 3, 4, 5], dtype=float)

        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=data,
        )

        vertices = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0], [4, 0, 0]], dtype=float)

        # 영역: 처음 3개
        region_mask = np.array([True, True, True, False, False])

        stats = SpatialAnalyzer.compute_region_statistics(field, vertices, region_mask)

        assert stats["count"] == 3
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0
        assert stats["mean"] == 2.0

    def test_find_region_by_value(self):
        """값 범위로 영역 찾기"""
        data = np.array([1, 5, 10, 15, 20], dtype=float)

        field = FieldData(
            name="test",
            field_type=FieldType.SCALAR,
            location=DataLocation.NODE,
            data=data,
        )

        # 5~15 범위
        mask = SpatialAnalyzer.find_region_by_value(field, min_value=5, max_value=15)

        # 5, 10, 15가 포함
        assert mask[1]  # 5
        assert mask[2]  # 10
        assert mask[3]  # 15
        assert not mask[0]  # 1
        assert not mask[4]  # 20
