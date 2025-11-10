"""시뮬레이션 API 테스트"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.main import app

client = TestClient(app)


@pytest.fixture
def sample_csv_content() -> str:
    """테스트용 CSV 내용"""
    return """x,y,z,temperature
0.0,0.0,0.0,300.0
1.0,0.0,0.0,310.0
0.0,1.0,0.0,320.0
"""


class TestHealthCheck:
    """헬스 체크 테스트"""

    def test_health_check(self) -> None:
        """헬스 체크 엔드포인트"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self) -> None:
        """루트 엔드포인트"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()


class TestSimulationAPI:
    """시뮬레이션 API 테스트"""

    def test_upload_simulation(self, sample_csv_content: str) -> None:
        """시뮬레이션 업로드"""
        # 임시 CSV 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            # 파일 업로드
            with open(csv_path, "rb") as f:
                response = client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                    data={"name": "Test Simulation"},
                )

            assert response.status_code == 201
            data = response.json()
            assert "simulation_id" in data
            assert data["name"] == "Test Simulation"
            assert data["num_vertices"] == 3
            assert "temperature" in data["fields"]

        finally:
            csv_path.unlink()

    def test_get_simulation(self, sample_csv_content: str) -> None:
        """시뮬레이션 조회"""
        # 먼저 업로드
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            with open(csv_path, "rb") as f:
                upload_response = client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            simulation_id = upload_response.json()["simulation_id"]

            # 조회
            response = client.get(f"/api/v1/simulations/{simulation_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["simulation_id"] == simulation_id
            assert data["num_vertices"] == 3

        finally:
            csv_path.unlink()

    def test_get_nonexistent_simulation(self) -> None:
        """존재하지 않는 시뮬레이션 조회"""
        response = client.get("/api/v1/simulations/nonexistent")
        assert response.status_code == 404
        assert "error" in response.json()

    def test_list_simulations(self, sample_csv_content: str) -> None:
        """시뮬레이션 목록 조회"""
        # 업로드
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            with open(csv_path, "rb") as f:
                client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            # 목록 조회
            response = client.get("/api/v1/simulations/")
            assert response.status_code == 200
            data = response.json()
            assert "simulations" in data
            assert "total" in data
            assert len(data["simulations"]) > 0

        finally:
            csv_path.unlink()

    def test_analyze_field(self, sample_csv_content: str) -> None:
        """필드 분석"""
        # 업로드
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            with open(csv_path, "rb") as f:
                upload_response = client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            simulation_id = upload_response.json()["simulation_id"]

            # 필드 분석
            response = client.post(
                f"/api/v1/simulations/{simulation_id}/analyze",
                json={
                    "timestep": 0,
                    "field_name": "temperature",
                    "compute_extremes": True,
                    "detect_outliers": False,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["field_name"] == "temperature"
            assert "statistics" in data
            assert "min" in data["statistics"]
            assert data["statistics"]["min"] == 300.0
            assert data["statistics"]["max"] == 320.0

        finally:
            csv_path.unlink()

    def test_delete_simulation(self, sample_csv_content: str) -> None:
        """시뮬레이션 삭제"""
        # 업로드
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            with open(csv_path, "rb") as f:
                upload_response = client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            simulation_id = upload_response.json()["simulation_id"]

            # 삭제
            response = client.delete(f"/api/v1/simulations/{simulation_id}")
            assert response.status_code == 200
            assert response.json()["success"] is True

            # 삭제 확인
            get_response = client.get(f"/api/v1/simulations/{simulation_id}")
            assert get_response.status_code == 404

        finally:
            csv_path.unlink()


class TestConvergenceAPI:
    """수렴성 분석 API 테스트"""

    def test_compute_convergence_single_timestep(self, sample_csv_content: str) -> None:
        """단일 타임스텝 - 수렴성 계산 불가"""
        # 업로드
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            with open(csv_path, "rb") as f:
                upload_response = client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            simulation_id = upload_response.json()["simulation_id"]

            # 수렴성 계산 (단일 타임스텝이므로 결과 없음)
            response = client.post(
                f"/api/v1/simulations/{simulation_id}/convergence",
                params={"field_name": "temperature"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["field_name"] == "temperature"
            assert len(data["convergence_data"]) == 0  # 단일 타임스텝

        finally:
            csv_path.unlink()


class TestSpatialAnalysisAPI:
    """공간 분석 API 테스트"""

    def test_spatial_analysis(self, sample_csv_content: str) -> None:
        """공간 영역 분석"""
        # 업로드
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(sample_csv_content)
            csv_path = Path(f.name)

        try:
            with open(csv_path, "rb") as f:
                upload_response = client.post(
                    "/api/v1/simulations/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            simulation_id = upload_response.json()["simulation_id"]

            # 공간 분석 (temperature >= 310)
            response = client.post(
                f"/api/v1/simulations/{simulation_id}/spatial",
                json={
                    "timestep": 0,
                    "field_name": "temperature",
                    "min_value": 310.0,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["field_name"] == "temperature"
            assert data["region_size"] == 2  # 310, 320
            assert data["region_statistics"]["min"] == 310.0

        finally:
            csv_path.unlink()
