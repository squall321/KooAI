"""
Tests for MultiFormatExporter
"""

import pytest
import json
import csv
import numpy as np
from pathlib import Path
from unittest.mock import Mock

from src.application.export.exporter import (
    MultiFormatExporter,
    ExportFormat,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test outputs"""
    return tmp_path


@pytest.fixture
def mock_simulation_data():
    """Create mock simulation data"""
    # Create mock simulation data with nested attributes
    sim_data = Mock()
    sim_data.simulation_id = "sim123"
    sim_data.name = "test_simulation"

    # Create mock data object with fields
    sim_data.data = Mock()
    sim_data.data.fields = {
        "temperature": np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
        "pressure": np.array([100.0, 200.0, 300.0, 400.0, 500.0]),
    }

    # Create mock metadata
    sim_data.metadata = Mock()
    sim_data.metadata.file_format = "VTK"
    sim_data.metadata.num_vertices = 5
    sim_data.metadata.num_cells = 4
    sim_data.metadata.field_names = ["temperature", "pressure"]

    return sim_data


@pytest.fixture
def exporter():
    """Create exporter instance"""
    return MultiFormatExporter()


def test_export_json(exporter, mock_simulation_data, temp_dir):
    """Test JSON export"""
    output_path = temp_dir / "output.json"

    exporter.export_simulation_data(
        mock_simulation_data,
        output_path,
        format=ExportFormat.JSON,
        include_metadata=True,
    )

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path) as f:
        data = json.load(f)

    assert data["simulation_id"] == "sim123"
    assert data["name"] == "test_simulation"
    assert "fields" in data
    assert "metadata" in data
    assert data["metadata"]["file_format"] == "VTK"
    assert data["metadata"]["num_vertices"] == 5


def test_export_json_without_metadata(exporter, mock_simulation_data, temp_dir):
    """Test JSON export without metadata"""
    output_path = temp_dir / "output_no_meta.json"

    exporter.export_simulation_data(
        mock_simulation_data,
        output_path,
        format=ExportFormat.JSON,
        include_metadata=False,
    )

    with open(output_path) as f:
        data = json.load(f)

    assert "metadata" not in data


def test_export_csv(exporter, mock_simulation_data, temp_dir):
    """Test CSV export"""
    output_path = temp_dir / "output.csv"

    exporter.export_simulation_data(
        mock_simulation_data,
        output_path,
        format=ExportFormat.CSV,
    )

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check header
    assert "temperature" in rows[0]
    assert "pressure" in rows[0]

    # Check data rows (5 data points + 1 header)
    assert len(rows) == 6


def test_export_numpy(exporter, mock_simulation_data, temp_dir):
    """Test NumPy export"""
    output_path = temp_dir / "output.npz"

    exporter.export_simulation_data(
        mock_simulation_data,
        output_path,
        format=ExportFormat.NUMPY,
    )

    # Verify file was created
    assert output_path.exists()

    # Load and verify content
    loaded = np.load(output_path)

    assert "temperature" in loaded
    assert "pressure" in loaded
    assert np.array_equal(loaded["temperature"], np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    assert np.array_equal(loaded["pressure"], np.array([100.0, 200.0, 300.0, 400.0, 500.0]))


def test_export_text(exporter, mock_simulation_data, temp_dir):
    """Test text export"""
    output_path = temp_dir / "output.txt"

    exporter.export_simulation_data(
        mock_simulation_data,
        output_path,
        format=ExportFormat.TEXT,
    )

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path) as f:
        content = f.read()

    assert "Simulation: test_simulation" in content
    assert "ID: sim123" in content
    assert "File Format: VTK" in content
    assert "Vertices: 5" in content
    assert "temperature:" in content
    assert "pressure:" in content


def test_export_analysis_results(exporter, temp_dir):
    """Test exporting analysis results"""
    output_path = temp_dir / "analysis.json"

    analysis_results = {
        "mean_temperature": 3.0,
        "max_pressure": 500.0,
        "statistics": {
            "variance": np.float64(2.5),
            "std": np.float64(1.58),
        },
    }

    exporter.export_analysis_results(analysis_results, output_path)

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path) as f:
        data = json.load(f)

    assert data["mean_temperature"] == 3.0
    assert data["max_pressure"] == 500.0
    assert data["statistics"]["variance"] == 2.5


def test_export_unsupported_format(exporter, mock_simulation_data, temp_dir):
    """Test unsupported format raises error"""
    output_path = temp_dir / "output.xyz"

    # Create an invalid format enum value
    with pytest.raises(ValueError, match="Unsupported format"):
        exporter.export_simulation_data(
            mock_simulation_data,
            output_path,
            format="INVALID",  # This will fail before reaching the ValueError
        )


def test_export_csv_without_fields(exporter, temp_dir):
    """Test CSV export without fields raises error"""
    output_path = temp_dir / "output.csv"

    # Create simulation data without proper fields
    sim_data = Mock()
    sim_data.simulation_id = "sim123"
    # Explicitly delete data attribute so hasattr returns False
    del sim_data.data

    with pytest.raises(ValueError, match="No fields to export"):
        exporter.export_simulation_data(
            sim_data,
            output_path,
            format=ExportFormat.CSV,
        )


def test_export_numpy_without_fields(exporter, temp_dir):
    """Test NumPy export without fields raises error"""
    output_path = temp_dir / "output.npz"

    # Create simulation data without proper fields
    sim_data = Mock()
    sim_data.simulation_id = "sim123"
    # Explicitly delete data attribute so hasattr returns False
    del sim_data.data

    with pytest.raises(ValueError, match="No fields to export"):
        exporter.export_simulation_data(
            sim_data,
            output_path,
            format=ExportFormat.NUMPY,
        )


def test_json_serialize_numpy_types(exporter):
    """Test JSON serialization of NumPy types"""
    # Test different NumPy types
    assert exporter._json_serialize(np.int64(42)) == 42
    assert exporter._json_serialize(np.float64(3.14)) == 3.14
    assert exporter._json_serialize(np.bool_(True)) is True
    assert exporter._json_serialize(np.array([1, 2, 3])) == [1, 2, 3]

    # Test unsupported type
    with pytest.raises(TypeError):
        exporter._json_serialize(object())


def test_export_with_path_string(exporter, mock_simulation_data, temp_dir):
    """Test export accepts string paths"""
    output_path = str(temp_dir / "output.json")

    exporter.export_simulation_data(
        mock_simulation_data,
        output_path,
        format=ExportFormat.JSON,
    )

    assert Path(output_path).exists()


def test_export_minimal_simulation_data(exporter, temp_dir):
    """Test export with minimal simulation data"""
    output_path = temp_dir / "minimal.json"

    # Create minimal mock data with no fields
    sim_data = Mock()
    sim_data.simulation_id = None
    sim_data.name = None
    # Delete data attribute so JSON export doesn't try to iterate fields
    del sim_data.data
    del sim_data.metadata

    exporter.export_simulation_data(
        sim_data,
        output_path,
        format=ExportFormat.JSON,
        include_metadata=False,
    )

    assert output_path.exists()

    with open(output_path) as f:
        data = json.load(f)

    assert data["simulation_id"] is None
    assert data["name"] is None
    assert "fields" in data


def test_export_large_array(exporter, temp_dir):
    """Test export with large arrays"""
    output_path = temp_dir / "large.npz"

    # Create simulation with large array
    sim_data = Mock()
    sim_data.data = Mock()
    sim_data.data.fields = {
        "large_field": np.random.rand(1000, 100),
    }

    exporter.export_simulation_data(
        sim_data,
        output_path,
        format=ExportFormat.NUMPY,
    )

    assert output_path.exists()

    # Verify
    loaded = np.load(output_path)
    assert loaded["large_field"].shape == (1000, 100)
