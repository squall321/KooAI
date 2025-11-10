"""시뮬레이션 Use Cases 테스트"""

import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

from src.application.use_cases import (
    AnalyzeFieldRequest,
    AnalyzeFieldUseCase,
    CompareTimestepsRequest,
    CompareTimestepsUseCase,
    ComputeConvergenceRequest,
    ComputeConvergenceUseCase,
    GetSimulationRequest,
    GetSimulationUseCase,
    ListSimulationsRequest,
    ListSimulationsUseCase,
    NotFoundError,
    SpatialAnalysisRequest,
    SpatialAnalysisUseCase,
    UploadSimulationRequest,
    UploadSimulationUseCase,
)
from src.core.simulation import CSVParser, ParserRegistry, VTKParser
from src.infrastructure.repositories.memory_simulation_repository import (
    InMemorySimulationResultRepository,
)


@pytest.fixture
def repository() -> Generator[InMemorySimulationResultRepository, None, None]:
    """테스트용 리포지토리"""
    repo = InMemorySimulationResultRepository()
    yield repo
    repo.clear()


@pytest.fixture
def parser_registry() -> ParserRegistry:
    """테스트용 파서 레지스트리"""
    registry = ParserRegistry()
    registry.register(CSVParser())
    registry.register(VTKParser())
    return registry


@pytest.fixture
def sample_csv_file() -> Generator[Path, None, None]:
    """테스트용 CSV 파일"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("x,y,z,temperature,velocity_x,velocity_y,velocity_z\n")
        f.write("0.0,0.0,0.0,300.0,1.0,0.0,0.0\n")
        f.write("1.0,0.0,0.0,310.0,2.0,0.5,0.0\n")
        f.write("0.0,1.0,0.0,320.0,1.5,1.0,0.0\n")
        csv_path = Path(f.name)

    yield csv_path

    csv_path.unlink()


class TestUploadSimulationUseCase:
    """시뮬레이션 업로드 Use Case 테스트"""

    def test_upload_csv_simulation(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """CSV 시뮬레이션 업로드"""
        use_case = UploadSimulationUseCase(parser_registry, repository)

        request = UploadSimulationRequest(file_path=sample_csv_file, name="test_simulation")

        response = use_case.execute(request)

        assert response.simulation_id is not None
        assert response.name == "test_simulation"
        assert response.simulation_type == "CSV"
        assert response.num_vertices == 3
        assert response.num_timesteps == 1
        assert "temperature" in response.fields
        assert "velocity" in response.fields

    def test_upload_nonexistent_file(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry) -> None:
        """존재하지 않는 파일 업로드 시 에러"""
        use_case = UploadSimulationUseCase(parser_registry, repository)

        request = UploadSimulationRequest(file_path=Path("nonexistent.csv"))

        with pytest.raises(Exception):  # ValidationError
            use_case.execute(request)


class TestGetSimulationUseCase:
    """시뮬레이션 조회 Use Case 테스트"""

    def test_get_existing_simulation(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """존재하는 시뮬레이션 조회"""
        # 먼저 업로드
        upload_use_case = UploadSimulationUseCase(parser_registry, repository)
        upload_response = upload_use_case.execute(
            UploadSimulationRequest(file_path=sample_csv_file)
        )

        # 조회
        get_use_case = GetSimulationUseCase(repository)
        get_response = get_use_case.execute(
            GetSimulationRequest(simulation_id=upload_response.simulation_id)
        )

        assert get_response.simulation_id == upload_response.simulation_id
        assert get_response.num_vertices == 3
        assert get_response.num_timesteps == 1

    def test_get_nonexistent_simulation(self, repository: InMemorySimulationResultRepository) -> None:
        """존재하지 않는 시뮬레이션 조회 시 에러"""
        use_case = GetSimulationUseCase(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(GetSimulationRequest(simulation_id="nonexistent"))


class TestAnalyzeFieldUseCase:
    """필드 분석 Use Case 테스트"""

    def test_analyze_scalar_field(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """스칼라 필드 분석"""
        # 업로드
        upload_use_case = UploadSimulationUseCase(parser_registry, repository)
        upload_response = upload_use_case.execute(
            UploadSimulationRequest(file_path=sample_csv_file)
        )

        # 분석
        analyze_use_case = AnalyzeFieldUseCase(repository)
        analyze_response = analyze_use_case.execute(
            AnalyzeFieldRequest(
                simulation_id=upload_response.simulation_id,
                timestep=0,
                field_name="temperature",
                compute_extremes=True,
                detect_outliers=True,
                compute_histogram=True,
            )
        )

        assert analyze_response.field_name == "temperature"
        assert analyze_response.field_type == "scalar"
        assert "min" in analyze_response.statistics
        assert "max" in analyze_response.statistics
        assert analyze_response.extremes is not None
        assert analyze_response.histogram is not None

    def test_analyze_vector_field(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """벡터 필드 분석"""
        # 업로드
        upload_use_case = UploadSimulationUseCase(parser_registry, repository)
        upload_response = upload_use_case.execute(
            UploadSimulationRequest(file_path=sample_csv_file)
        )

        # 분석
        analyze_use_case = AnalyzeFieldUseCase(repository)
        analyze_response = analyze_use_case.execute(
            AnalyzeFieldRequest(
                simulation_id=upload_response.simulation_id,
                timestep=0,
                field_name="velocity",
            )
        )

        assert analyze_response.field_name == "velocity"
        assert analyze_response.field_type == "vector"


class TestListSimulationsUseCase:
    """시뮬레이션 목록 조회 Use Case 테스트"""

    def test_list_simulations(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """시뮬레이션 목록 조회"""
        # 여러 시뮬레이션 업로드
        upload_use_case = UploadSimulationUseCase(parser_registry, repository)

        upload_use_case.execute(
            UploadSimulationRequest(file_path=sample_csv_file, name="simulation1")
        )
        upload_use_case.execute(
            UploadSimulationRequest(file_path=sample_csv_file, name="simulation2")
        )

        # 목록 조회
        list_use_case = ListSimulationsUseCase(repository)
        list_response = list_use_case.execute(ListSimulationsRequest(skip=0, limit=10))

        assert list_response.total == 2
        assert len(list_response.simulations) == 2

    def test_list_simulations_pagination(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """페이지네이션"""
        # 3개 업로드
        upload_use_case = UploadSimulationUseCase(parser_registry, repository)

        for i in range(3):
            upload_use_case.execute(
                UploadSimulationRequest(file_path=sample_csv_file, name=f"simulation{i}")
            )

        # 첫 페이지 (2개씩)
        list_use_case = ListSimulationsUseCase(repository)
        page1 = list_use_case.execute(ListSimulationsRequest(skip=0, limit=2))

        assert page1.total == 3
        assert len(page1.simulations) == 2

        # 두 번째 페이지
        page2 = list_use_case.execute(ListSimulationsRequest(skip=2, limit=2))

        assert page2.total == 3
        assert len(page2.simulations) == 1


class TestSpatialAnalysisUseCase:
    """공간 분석 Use Case 테스트"""

    def test_spatial_analysis(self, repository: InMemorySimulationResultRepository, parser_registry: ParserRegistry, sample_csv_file: Path) -> None:
        """공간 영역 분석"""
        # 업로드
        upload_use_case = UploadSimulationUseCase(parser_registry, repository)
        upload_response = upload_use_case.execute(
            UploadSimulationRequest(file_path=sample_csv_file)
        )

        # 공간 분석 (온도 >= 310)
        spatial_use_case = SpatialAnalysisUseCase(repository)
        spatial_response = spatial_use_case.execute(
            SpatialAnalysisRequest(
                simulation_id=upload_response.simulation_id,
                timestep=0,
                field_name="temperature",
                min_value=310.0,
            )
        )

        assert spatial_response.field_name == "temperature"
        assert spatial_response.region_size == 2  # 310, 320
        assert "min" in spatial_response.region_statistics
        assert spatial_response.region_statistics["min"] == 310.0
