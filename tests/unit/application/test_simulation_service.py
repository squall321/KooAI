"""시뮬레이션 서비스 테스트"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.application.services import SimulationService
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
def service(repository: InMemorySimulationResultRepository) -> SimulationService:
    """테스트용 서비스"""
    return SimulationService(repository)


@pytest.fixture
def sample_csv_file() -> Generator[Path, None, None]:
    """테스트용 CSV 파일"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("x,y,z,temperature\n")
        f.write("0.0,0.0,0.0,300.0\n")
        f.write("1.0,0.0,0.0,310.0\n")
        f.write("0.0,1.0,0.0,320.0\n")
        csv_path = Path(f.name)

    yield csv_path

    csv_path.unlink()


class TestSimulationService:
    """시뮬레이션 서비스 테스트"""

    def test_upload_and_analyze(self, service: SimulationService, sample_csv_file: Path) -> None:
        """업로드 및 자동 분석"""
        result = service.upload_and_analyze(
            file_path=sample_csv_file,
            name="test_simulation",
            analyze_all_fields=True,
        )

        assert result.simulation_info.name == "test_simulation"
        assert "temperature" in result.field_analyses
        assert result.field_analyses["temperature"].field_type == "scalar"

    def test_list_simulations(self, service: SimulationService, sample_csv_file: Path) -> None:
        """시뮬레이션 목록 조회"""
        # 2개 업로드
        service.upload_and_analyze(sample_csv_file, name="sim1", analyze_all_fields=False)
        service.upload_and_analyze(sample_csv_file, name="sim2", analyze_all_fields=False)

        # 목록 조회
        list_response = service.list_simulations(page=1, page_size=10)

        assert list_response.total == 2
        assert len(list_response.simulations) == 2

    def test_get_simulation_summary(self, service: SimulationService, sample_csv_file: Path) -> None:
        """시뮬레이션 요약 조회"""
        # 업로드
        upload_result = service.upload_and_analyze(
            sample_csv_file, name="test", analyze_all_fields=False
        )

        # 요약 조회
        summary = service.get_simulation_summary(upload_result.simulation_info.simulation_id)

        assert summary["name"] == "test"
        assert summary["num_vertices"] == 3
        assert "temperature" in summary["fields"]
