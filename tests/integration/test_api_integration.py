"""
API integration tests
"""

import pytest
from typing import Any, Callable
from pathlib import Path
from fastapi.testclient import TestClient
from io import BytesIO


class TestSimulationAPI:
    """Test simulation API endpoints"""

    def test_upload_simulation_csv(self, api_client: TestClient, sample_csv_file: Path) -> None:
        """Test uploading CSV simulation file"""
        with open(sample_csv_file, "rb") as f:
            response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("sample.csv", f, "text/csv")},
                data={"name": "Test Upload", "auto_analyze": "false"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "simulation_id" in data
        assert data["name"] == "Test Upload"
        assert data["simulation_type"] == "CSV"

    def test_get_simulation(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test getting simulation by ID"""
        # Create test simulation
        simulation = simulation_factory("Test Simulation")

        # Get simulation
        response = api_client.get(f"/api/simulations/{simulation.simulation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["simulation_id"] == simulation.simulation_id
        assert data["name"] == "Test Simulation"

    def test_list_simulations(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test listing simulations"""
        # Create multiple simulations
        simulation_factory("Sim 1")
        simulation_factory("Sim 2")
        simulation_factory("Sim 3")

        # List simulations
        response = api_client.get("/api/simulations/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_analyze_field(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test field analysis endpoint"""
        # Create test simulation
        simulation = simulation_factory("Test Analysis")

        # Analyze temperature field
        response = api_client.post(
            f"/api/simulations/{simulation.simulation_id}/analyze",
            json={
                "field_name": "temperature",
                "include_extremes": True,
                "include_outliers": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert "min" in data["statistics"]
        assert "max" in data["statistics"]
        assert "mean" in data["statistics"]

    def test_convergence_analysis(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test convergence analysis endpoint"""
        # Create test simulation
        simulation = simulation_factory("Convergence Test")

        # Run convergence analysis
        response = api_client.post(
            f"/api/simulations/{simulation.simulation_id}/convergence",
            json={"field_name": "temperature", "window_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert "field_name" in data

    def test_spatial_analysis(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test spatial analysis endpoint"""
        # Create test simulation
        simulation = simulation_factory("Spatial Test")

        # Run spatial analysis
        response = api_client.post(
            f"/api/simulations/{simulation.simulation_id}/spatial",
            json={
                "field_name": "temperature",
                "min_value": 300.0,
                "max_value": 400.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "field_name" in data
        assert "region_count" in data

    def test_delete_simulation(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test deleting simulation"""
        # Create test simulation
        simulation = simulation_factory("Delete Test")
        sim_id = simulation.simulation_id

        # Delete simulation
        response = api_client.delete(f"/api/simulations/{sim_id}")

        assert response.status_code == 200

        # Verify deletion
        response = api_client.get(f"/api/simulations/{sim_id}")
        assert response.status_code == 404

    def test_upload_invalid_file(self, api_client: TestClient) -> None:
        """Test uploading invalid file"""
        # Create invalid file content
        invalid_content = b"This is not a valid simulation file"

        response = api_client.post(
            "/api/simulations/upload",
            files={"file": ("invalid.txt", BytesIO(invalid_content), "text/plain")},
            data={"name": "Invalid Upload"},
        )

        # Should return error
        assert response.status_code in [400, 422, 500]

    def test_get_nonexistent_simulation(self, api_client: TestClient) -> None:
        """Test getting non-existent simulation"""
        response = api_client.get("/api/simulations/nonexistent-id")

        assert response.status_code == 404

    def test_analyze_nonexistent_field(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test analyzing non-existent field"""
        simulation = simulation_factory("Field Test")

        response = api_client.post(
            f"/api/simulations/{simulation.simulation_id}/analyze",
            json={"field_name": "nonexistent_field"},
        )

        assert response.status_code in [400, 404]


class TestHealthCheck:
    """Test health check endpoints"""

    def test_health_check(self, api_client: TestClient) -> None:
        """Test health check endpoint"""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check(self, api_client: TestClient) -> None:
        """Test readiness check endpoint"""
        response = api_client.get("/ready")

        assert response.status_code == 200


class TestAPIValidation:
    """Test API input validation"""

    def test_upload_without_file(self, api_client: TestClient) -> None:
        """Test upload without file"""
        response = api_client.post(
            "/api/simulations/upload",
            data={"name": "No File"},
        )

        assert response.status_code == 422

    def test_analyze_without_field_name(self, api_client: TestClient, simulation_factory: Callable[..., Any]) -> None:
        """Test analysis without field name"""
        simulation = simulation_factory("Validation Test")

        response = api_client.post(
            f"/api/simulations/{simulation.simulation_id}/analyze",
            json={},
        )

        assert response.status_code == 422

    def test_invalid_simulation_id_format(self, api_client: TestClient) -> None:
        """Test invalid simulation ID format"""
        response = api_client.get("/api/simulations/invalid-id-format-123-456")

        # Should handle gracefully
        assert response.status_code in [400, 404]
