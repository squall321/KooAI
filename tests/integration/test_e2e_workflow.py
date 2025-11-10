"""
End-to-end workflow integration tests
"""

import pytest
from pathlib import Path
import time
from typing import Any


class TestSimulationWorkflow:
    """Test complete simulation processing workflow"""

    def test_complete_csv_workflow(self, api_client: Any, sample_csv_file: Any) -> None:
        """
        Test complete workflow:
        1. Upload CSV file
        2. Analyze field
        3. Run convergence analysis
        4. Run spatial analysis
        5. Retrieve results
        6. Delete simulation
        """
        # Step 1: Upload simulation
        with open(sample_csv_file, "rb") as f:
            upload_response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("test.csv", f, "text/csv")},
                data={"name": "E2E Test CSV", "auto_analyze": "false"},
            )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        sim_id = upload_data["simulation_id"]

        # Step 2: Analyze temperature field
        analyze_response = api_client.post(
            f"/api/simulations/{sim_id}/analyze",
            json={
                "field_name": "temperature",
                "include_extremes": True,
                "include_outliers": True,
            },
        )

        assert analyze_response.status_code == 200
        analyze_data = analyze_response.json()
        assert "statistics" in analyze_data
        assert analyze_data["statistics"]["mean"] > 0

        # Step 3: Run convergence analysis
        convergence_response = api_client.post(
            f"/api/simulations/{sim_id}/convergence",
            json={"field_name": "temperature"},
        )

        assert convergence_response.status_code == 200
        convergence_data = convergence_response.json()
        assert convergence_data["field_name"] == "temperature"

        # Step 4: Run spatial analysis
        spatial_response = api_client.post(
            f"/api/simulations/{sim_id}/spatial",
            json={
                "field_name": "temperature",
                "min_value": 300.0,
                "max_value": 450.0,
            },
        )

        assert spatial_response.status_code == 200
        spatial_data = spatial_response.json()
        assert "region_count" in spatial_data

        # Step 5: Retrieve simulation details
        get_response = api_client.get(f"/api/simulations/{sim_id}")

        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == "E2E Test CSV"

        # Step 6: Delete simulation
        delete_response = api_client.delete(f"/api/simulations/{sim_id}")

        assert delete_response.status_code == 200

        # Verify deletion
        final_get_response = api_client.get(f"/api/simulations/{sim_id}")
        assert final_get_response.status_code == 404

    def test_complete_vtk_workflow(self, api_client: Any, sample_vtk_file: Any) -> None:
        """
        Test complete workflow with VTK file
        """
        # Upload VTK simulation
        with open(sample_vtk_file, "rb") as f:
            upload_response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("test.vtk", f, "application/octet-stream")},
                data={"name": "E2E Test VTK"},
            )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        sim_id = upload_data["simulation_id"]

        # Analyze pressure field
        analyze_response = api_client.post(
            f"/api/simulations/{sim_id}/analyze",
            json={"field_name": "pressure"},
        )

        assert analyze_response.status_code == 200

        # Clean up
        api_client.delete(f"/api/simulations/{sim_id}")

    def test_multiple_field_analysis_workflow(self, api_client: Any, sample_csv_file: Any) -> None:
        """
        Test analyzing multiple fields in sequence
        """
        # Upload simulation
        with open(sample_csv_file, "rb") as f:
            upload_response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("multi.csv", f, "text/csv")},
                data={"name": "Multi-field Test"},
            )

        sim_id = upload_response.json()["simulation_id"]

        # Analyze all fields
        fields = ["temperature", "pressure"]

        for field in fields:
            response = api_client.post(
                f"/api/simulations/{sim_id}/analyze",
                json={"field_name": field},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["field_name"] == field
            assert "statistics" in data

        # Clean up
        api_client.delete(f"/api/simulations/{sim_id}")

    def test_batch_upload_workflow(self, api_client: Any, sample_csv_file: Any) -> None:
        """
        Test uploading and processing multiple simulations
        """
        simulation_ids = []

        # Upload multiple simulations
        for i in range(3):
            with open(sample_csv_file, "rb") as f:
                response = api_client.post(
                    "/api/simulations/upload",
                    files={"file": (f"batch{i}.csv", f, "text/csv")},
                    data={"name": f"Batch Simulation {i}"},
                )

            assert response.status_code == 200
            simulation_ids.append(response.json()["simulation_id"])

        # List all simulations
        list_response = api_client.get("/api/simulations/")
        assert list_response.status_code == 200
        all_sims = list_response.json()
        assert len(all_sims) >= 3

        # Analyze each
        for sim_id in simulation_ids:
            response = api_client.post(
                f"/api/simulations/{sim_id}/analyze",
                json={"field_name": "temperature"},
            )
            assert response.status_code == 200

        # Clean up all
        for sim_id in simulation_ids:
            api_client.delete(f"/api/simulations/{sim_id}")

    def test_error_recovery_workflow(self, api_client: Any, sample_csv_file: Any) -> None:
        """
        Test error handling and recovery
        """
        # Upload simulation
        with open(sample_csv_file, "rb") as f:
            upload_response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("error_test.csv", f, "text/csv")},
                data={"name": "Error Test"},
            )

        sim_id = upload_response.json()["simulation_id"]

        # Try to analyze non-existent field (should fail gracefully)
        error_response = api_client.post(
            f"/api/simulations/{sim_id}/analyze",
            json={"field_name": "nonexistent_field"},
        )

        assert error_response.status_code in [400, 404]

        # Simulation should still be accessible
        get_response = api_client.get(f"/api/simulations/{sim_id}")
        assert get_response.status_code == 200

        # Can still analyze valid field
        valid_response = api_client.post(
            f"/api/simulations/{sim_id}/analyze",
            json={"field_name": "temperature"},
        )
        assert valid_response.status_code == 200

        # Clean up
        api_client.delete(f"/api/simulations/{sim_id}")


class TestConcurrentWorkflows:
    """Test concurrent workflow execution"""

    def test_concurrent_uploads(self, api_client: Any, sample_csv_file: Any) -> None:
        """Test uploading simulations concurrently"""
        # In a real concurrent test, we would use threading or asyncio
        # For now, we'll just test sequential uploads quickly

        simulation_ids = []

        for i in range(5):
            with open(sample_csv_file, "rb") as f:
                response = api_client.post(
                    "/api/simulations/upload",
                    files={"file": (f"concurrent{i}.csv", f, "text/csv")},
                    data={"name": f"Concurrent {i}"},
                )

            assert response.status_code == 200
            simulation_ids.append(response.json()["simulation_id"])

        # Verify all were created
        assert len(simulation_ids) == 5
        assert len(set(simulation_ids)) == 5  # All unique

        # Clean up
        for sim_id in simulation_ids:
            api_client.delete(f"/api/simulations/{sim_id}")

    def test_concurrent_analysis(self, api_client: Any, simulation_factory: Any) -> None:
        """Test running analysis on multiple simulations concurrently"""
        # Create test simulations
        simulations = [simulation_factory(f"Concurrent Analysis {i}") for i in range(3)]

        # Analyze all
        responses = []
        for sim in simulations:
            response = api_client.post(
                f"/api/simulations/{sim.simulation_id}/analyze",
                json={"field_name": "temperature"},
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200


class TestPerformanceWorkflow:
    """Test workflow performance"""

    def test_upload_performance(self, api_client: Any, sample_csv_file: Any) -> None:
        """Test upload performance"""
        start_time = time.time()

        with open(sample_csv_file, "rb") as f:
            response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("perf.csv", f, "text/csv")},
                data={"name": "Performance Test"},
            )

        elapsed = time.time() - start_time

        assert response.status_code == 200
        # Should complete within 5 seconds
        assert elapsed < 5.0

        # Clean up
        sim_id = response.json()["simulation_id"]
        api_client.delete(f"/api/simulations/{sim_id}")

    def test_analysis_performance(self, api_client: Any, simulation_factory: Any) -> None:
        """Test analysis performance"""
        # Create simulation with reasonable size
        simulation = simulation_factory("Performance Test", num_points=1000)

        start_time = time.time()

        response = api_client.post(
            f"/api/simulations/{simulation.simulation_id}/analyze",
            json={"field_name": "temperature", "include_extremes": True, "include_outliers": True},
        )

        elapsed = time.time() - start_time

        assert response.status_code == 200
        # Analysis should complete within 2 seconds
        assert elapsed < 2.0


class TestDataIntegrity:
    """Test data integrity throughout workflow"""

    def test_data_consistency(self, api_client: Any, sample_csv_file: Any) -> None:
        """Test that data remains consistent through upload and retrieval"""
        # Upload
        with open(sample_csv_file, "rb") as f:
            upload_response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("integrity.csv", f, "text/csv")},
                data={"name": "Integrity Test"},
            )

        sim_id = upload_response.json()["simulation_id"]

        # Get simulation multiple times
        responses = []
        for _ in range(3):
            response = api_client.get(f"/api/simulations/{sim_id}")
            responses.append(response.json())

        # All responses should be identical
        for i in range(1, len(responses)):
            assert responses[i] == responses[0]

        # Clean up
        api_client.delete(f"/api/simulations/{sim_id}")

    def test_field_data_preservation(self, api_client: Any, sample_csv_file: Any) -> None:
        """Test that field data is preserved correctly"""
        # Upload simulation
        with open(sample_csv_file, "rb") as f:
            upload_response = api_client.post(
                "/api/simulations/upload",
                files={"file": ("fields.csv", f, "text/csv")},
                data={"name": "Field Test"},
            )

        sim_id = upload_response.json()["simulation_id"]

        # Analyze temperature
        temp_response = api_client.post(
            f"/api/simulations/{sim_id}/analyze",
            json={"field_name": "temperature"},
        )

        temp_stats = temp_response.json()["statistics"]

        # Analyze pressure
        press_response = api_client.post(
            f"/api/simulations/{sim_id}/analyze",
            json={"field_name": "pressure"},
        )

        press_stats = press_response.json()["statistics"]

        # Stats should be different for different fields
        assert temp_stats["mean"] != press_stats["mean"]

        # Clean up
        api_client.delete(f"/api/simulations/{sim_id}")
