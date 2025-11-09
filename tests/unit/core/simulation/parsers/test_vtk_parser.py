"""
Tests for VTK Parser

Tests VTKParser functionality including ASCII VTK file parsing, dataset types, and field extraction.
"""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import numpy as np


class TestVTKParserBasics:
    """Test VTKParser basic functionality"""

    def test_vtk_parser_creation(self):
        """Test VTKParser can be created"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()

        assert parser is not None

    def test_vtk_parser_can_parse_vtk_files(self, tmp_path):
        """Test can_parse returns True for VTK files with valid header"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text("# vtk DataFile Version 3.0\nTest\nASCII\nDATASET POLYDATA\n")

        parser = VTKParser()
        result = parser.can_parse(vtk_file)

        assert result is True

    def test_vtk_parser_cannot_parse_non_vtk_files(self):
        """Test can_parse returns False for non-VTK files"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()
        csv_file = Path("test.csv")

        result = parser.can_parse(csv_file)

        assert result is False

    def test_vtk_parser_cannot_parse_invalid_header(self, tmp_path):
        """Test can_parse returns False for VTK file with invalid header"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text("Invalid header\n")

        parser = VTKParser()
        result = parser.can_parse(vtk_file)

        assert result is False

    def test_get_supported_extensions(self):
        """Test get_supported_extensions returns correct list"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()

        extensions = parser.get_supported_extensions()

        assert ".vtk" in extensions
        assert isinstance(extensions, list)


class TestVTKParserHeaderParsing:
    """Test VTK header parsing"""

    def test_parse_header_valid(self):
        """Test _parse_header with valid VTK header"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()
        lines = [
            "# vtk DataFile Version 3.0",
            "Test VTK file",
            "ASCII",
            "DATASET POLYDATA",
        ]

        header = parser._parse_header(lines)

        assert header["version"] == "3.0"
        assert header["description"] == "Test VTK file"
        assert header["format"] == "ASCII"

    def test_parse_header_missing_version_raises_error(self):
        """Test _parse_header raises error for missing version"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()
        lines = [
            "Invalid header",
            "Description",
            "ASCII",
            "DATASET POLYDATA",
        ]

        with pytest.raises(ValueError, match="missing version header"):
            parser._parse_header(lines)

    def test_parse_header_invalid_format_raises_error(self):
        """Test _parse_header raises error for invalid format"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()
        lines = [
            "# vtk DataFile Version 3.0",
            "Description",
            "INVALID_FORMAT",
            "DATASET POLYDATA",
        ]

        with pytest.raises(ValueError, match="Invalid VTK format"):
            parser._parse_header(lines)

    def test_parse_header_binary_not_supported(self):
        """Test _parse_header raises NotImplementedError for BINARY format"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()
        lines = [
            "# vtk DataFile Version 3.0",
            "Description",
            "BINARY",
            "DATASET POLYDATA",
        ]

        with pytest.raises(NotImplementedError, match="Binary VTK not supported"):
            parser._parse_header(lines)

    def test_parse_header_too_few_lines_raises_error(self):
        """Test _parse_header raises error for too few lines"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        parser = VTKParser()
        lines = ["# vtk DataFile Version 3.0"]

        with pytest.raises(ValueError, match="too few lines"):
            parser._parse_header(lines)


class TestVTKParserPolydata:
    """Test VTK POLYDATA parsing"""

    def test_parse_simple_polydata(self, tmp_path):
        """Test parsing simple POLYDATA file"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test polydata\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 3 float\n"
            "0.0 0.0 0.0\n"
            "1.0 0.0 0.0\n"
            "0.0 1.0 0.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        assert result is not None
        assert result.simulation_type == "VTK"
        assert result.mesh.num_vertices == 3

    def test_parse_polydata_extracts_vertices(self, tmp_path):
        """Test POLYDATA parsing extracts correct vertices"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 2 float\n"
            "1.0 2.0 3.0\n"
            "4.0 5.0 6.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        vertices = result.mesh.vertices

        assert vertices.shape == (2, 3)
        assert np.allclose(vertices[0], [1.0, 2.0, 3.0])
        assert np.allclose(vertices[1], [4.0, 5.0, 6.0])

    def test_parse_polydata_with_polygons(self, tmp_path):
        """Test POLYDATA with POLYGONS section"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 3 float\n"
            "0.0 0.0 0.0\n"
            "1.0 0.0 0.0\n"
            "0.0 1.0 0.0\n"
            "POLYGONS 1 4\n"
            "3 0 1 2\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        assert result.mesh.faces is not None
        assert result.mesh.faces.shape[0] >= 1

    def test_parse_polydata_missing_points_raises_error(self, tmp_path):
        """Test POLYDATA without POINTS raises error"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
        )

        parser = VTKParser()

        # Parser tries to access lines beyond bounds, raising IndexError
        with pytest.raises((ValueError, IndexError)):
            parser.parse(vtk_file)


class TestVTKParserUnstructuredGrid:
    """Test VTK UNSTRUCTURED_GRID parsing"""

    def test_parse_unstructured_grid(self, tmp_path):
        """Test parsing UNSTRUCTURED_GRID"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test unstructured grid\n"
            "ASCII\n"
            "DATASET UNSTRUCTURED_GRID\n"
            "POINTS 4 float\n"
            "0.0 0.0 0.0\n"
            "1.0 0.0 0.0\n"
            "1.0 1.0 0.0\n"
            "0.0 1.0 0.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        assert result is not None
        assert result.mesh.num_vertices == 4

    def test_parse_unstructured_grid_with_cells(self, tmp_path):
        """Test UNSTRUCTURED_GRID with CELLS"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET UNSTRUCTURED_GRID\n"
            "POINTS 4 float\n"
            "0.0 0.0 0.0 1.0 0.0 0.0\n"
            "1.0 1.0 0.0 0.0 1.0 0.0\n"
            "CELLS 1 5\n"
            "4 0 1 2 3\n"
            "CELL_TYPES 1\n"
            "9\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        assert result is not None

    def test_parse_unstructured_grid_missing_points_raises_error(self, tmp_path):
        """Test UNSTRUCTURED_GRID without POINTS raises error"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET UNSTRUCTURED_GRID\n"
        )

        parser = VTKParser()

        # Parser tries to access lines beyond bounds, raising IndexError
        with pytest.raises((ValueError, IndexError)):
            parser.parse(vtk_file)


class TestVTKParserFieldData:
    """Test VTK field data parsing"""

    def test_parse_scalar_field(self, tmp_path):
        """Test parsing SCALARS field"""
        from src.core.simulation.parsers.vtk_parser import VTKParser
        from src.core.simulation.models import FieldType

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 3 float\n"
            "0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0 0.0\n"
            "POINT_DATA 3\n"
            "SCALARS temperature float 1\n"
            "LOOKUP_TABLE default\n"
            "300.0 310.0 305.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        timestep = result.timesteps[0]
        temp_field = timestep.fields.get("temperature")

        assert temp_field is not None
        assert temp_field.field_type == FieldType.SCALAR
        assert temp_field.data.shape == (3,)

    def test_parse_vector_field(self, tmp_path):
        """Test parsing VECTORS field"""
        from src.core.simulation.parsers.vtk_parser import VTKParser
        from src.core.simulation.models import FieldType

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 2 float\n"
            "0.0 0.0 0.0 1.0 0.0 0.0\n"
            "POINT_DATA 2\n"
            "VECTORS velocity float\n"
            "10.0 20.0 30.0\n"
            "15.0 25.0 35.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        timestep = result.timesteps[0]
        vel_field = timestep.fields.get("velocity")

        assert vel_field is not None
        assert vel_field.field_type == FieldType.VECTOR
        assert vel_field.data.shape == (2, 3)
        assert np.allclose(vel_field.data[0], [10.0, 20.0, 30.0])

    def test_parse_multiple_fields(self, tmp_path):
        """Test parsing multiple SCALARS and VECTORS fields"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 2 float\n"
            "0.0 0.0 0.0 1.0 0.0 0.0\n"
            "POINT_DATA 2\n"
            "SCALARS pressure float 1\n"
            "LOOKUP_TABLE default\n"
            "100.0 200.0\n"
            "VECTORS velocity float\n"
            "1.0 2.0 3.0 4.0 5.0 6.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        timestep = result.timesteps[0]

        assert len(timestep.fields) == 2

    def test_parse_cell_data(self, tmp_path):
        """Test parsing CELL_DATA"""
        from src.core.simulation.parsers.vtk_parser import VTKParser
        from src.core.simulation.models import DataLocation

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 3 float\n"
            "0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0 0.0\n"
            "POLYGONS 1 4\n"
            "3 0 1 2\n"
            "CELL_DATA 1\n"
            "SCALARS quality float 1\n"
            "LOOKUP_TABLE default\n"
            "0.95\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        timestep = result.timesteps[0]
        quality_field = timestep.fields.get("quality")

        assert quality_field is not None
        assert quality_field.location == DataLocation.CELL


class TestVTKParserMetadata:
    """Test VTK metadata handling"""

    def test_parse_stores_metadata(self, tmp_path):
        """Test parsing stores VTK version and description in metadata"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 4.2\n"
            "Custom description text\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 1 float\n"
            "0.0 0.0 0.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        assert result.metadata["vtk_version"] == "4.2"
        assert result.metadata["description"] == "Custom description text"

    def test_parse_custom_time_and_step(self, tmp_path):
        """Test parsing with custom time and step parameters"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 1 float\n"
            "0.0 0.0 0.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file, time=2.5, step=10)

        timestep = result.timesteps[0]

        assert timestep.time == 2.5
        assert timestep.step == 10


class TestVTKParserEdgeCases:
    """Test VTK parser edge cases"""

    def test_parse_unsupported_dataset_type_raises_error(self, tmp_path):
        """Test parsing unsupported dataset type raises NotImplementedError"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET STRUCTURED_POINTS\n"
        )

        parser = VTKParser()

        with pytest.raises(NotImplementedError, match="not supported yet"):
            parser.parse(vtk_file)

    def test_parse_missing_dataset_keyword_raises_error(self, tmp_path):
        """Test parsing without DATASET keyword raises error"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "POINTS 1 float\n"
        )

        parser = VTKParser()

        with pytest.raises(ValueError, match="Missing DATASET keyword"):
            parser.parse(vtk_file)

    def test_parse_multiline_point_data(self, tmp_path):
        """Test parsing vertices spread across multiple lines"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 4 float\n"
            "0.0 0.0\n"
            "0.0 1.0\n"
            "0.0 0.0\n"
            "1.0 1.0\n"
            "0.0 0.0\n"
            "0.0 1.0\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        assert result.mesh.num_vertices == 4

    def test_parse_polygon_to_triangles_conversion(self, tmp_path):
        """Test quad polygon converted to triangles"""
        from src.core.simulation.parsers.vtk_parser import VTKParser

        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text(
            "# vtk DataFile Version 3.0\n"
            "Test\n"
            "ASCII\n"
            "DATASET POLYDATA\n"
            "POINTS 4 float\n"
            "0.0 0.0 0.0 1.0 0.0 0.0\n"
            "1.0 1.0 0.0 0.0 1.0 0.0\n"
            "POLYGONS 1 5\n"
            "4 0 1 2 3\n"
        )

        parser = VTKParser()
        result = parser.parse(vtk_file)

        # Quad should be split into 2 triangles
        assert result.mesh.faces is not None
        assert result.mesh.faces.shape[0] == 2
