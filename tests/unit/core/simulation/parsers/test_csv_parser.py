"""
Tests for CSV Parser

Tests CSVParser functionality including file validation, data extraction, and field parsing.
"""

from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
import numpy as np


class TestCSVParserBasics:
    """Test CSVParser basic functionality"""

    def test_csv_parser_creation(self) -> None:
        """Test CSVParser can be created"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()

        assert parser is not None

    def test_csv_parser_can_parse_csv_files(self) -> None:
        """Test can_parse returns True for CSV files"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        csv_file = Path("test_data.csv")

        result = parser.can_parse(csv_file)

        assert result is True

    def test_csv_parser_cannot_parse_non_csv_files(self) -> None:
        """Test can_parse returns False for non-CSV files"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        vtk_file = Path("test_data.vtk")

        result = parser.can_parse(vtk_file)

        assert result is False

    def test_get_supported_extensions(self) -> None:
        """Test get_supported_extensions returns correct list"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()

        extensions = parser.get_supported_extensions()

        assert ".csv" in extensions
        assert isinstance(extensions, list)


class TestCSVParserValidation:
    """Test CSV file validation"""

    def test_validate_file_raises_error_for_missing_file(self) -> None:
        """Test validate_file raises FileNotFoundError for missing file"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        missing_file = Path("/nonexistent/file.csv")

        with pytest.raises(FileNotFoundError, match="File not found"):
            parser.validate_file(missing_file)

    def test_validate_file_raises_error_for_directory(self, tmp_path: Path) -> None:
        """Test validate_file raises ValueError for directory"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        directory = tmp_path / "test_dir"
        directory.mkdir()

        with pytest.raises(ValueError, match="Not a file"):
            parser.validate_file(directory)

    def test_validate_file_raises_error_for_wrong_extension(self, tmp_path: Path) -> None:
        """Test validate_file raises ValueError for wrong extension"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        wrong_file = tmp_path / "test.txt"
        wrong_file.write_text("test")

        with pytest.raises(ValueError, match="Unsupported file extension"):
            parser.validate_file(wrong_file)


class TestCSVParserParsing:
    """Test CSV parsing functionality"""

    def test_parse_simple_csv(self, tmp_path: Path) -> None:
        """Test parsing simple CSV file"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        # Create test CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,temperature\n"
            "0.0,0.0,0.0,300.0\n"
            "1.0,0.0,0.0,310.0\n"
            "0.0,1.0,0.0,305.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        assert result is not None
        assert result.name == "test"
        assert result.simulation_type == "CSV"
        assert result.num_timesteps == 1

    def test_parse_csv_extracts_correct_vertices(self, tmp_path: Path) -> None:
        """Test CSV parsing extracts correct vertex coordinates"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,pressure\n"
            "1.0,2.0,3.0,100.0\n"
            "4.0,5.0,6.0,200.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        vertices = result.mesh.vertices

        assert vertices.shape == (2, 3)
        assert np.allclose(vertices[0], [1.0, 2.0, 3.0])
        assert np.allclose(vertices[1], [4.0, 5.0, 6.0])

    def test_parse_csv_without_z_column(self, tmp_path: Path) -> None:
        """Test parsing CSV without z column (2D data)"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test_2d.csv"
        csv_file.write_text(
            "x,y,value\n"
            "0.0,0.0,10.0\n"
            "1.0,1.0,20.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        vertices = result.mesh.vertices

        # z should be filled with zeros
        assert vertices.shape == (2, 3)
        assert vertices[0][2] == 0.0
        assert vertices[1][2] == 0.0

    def test_parse_csv_extracts_scalar_fields(self, tmp_path: Path) -> None:
        """Test CSV parsing extracts scalar fields"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,temperature,pressure\n"
            "0.0,0.0,0.0,300.0,101325.0\n"
            "1.0,0.0,0.0,310.0,101330.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        timestep = result.timesteps[0]
        fields = timestep.fields

        field_names = list(fields.keys())

        assert "temperature" in field_names
        assert "pressure" in field_names

    def test_parse_csv_extracts_vector_fields(self, tmp_path: Path) -> None:
        """Test CSV parsing extracts vector fields (name_x, name_y, name_z pattern)"""
        from src.core.simulation.parsers.csv_parser import CSVParser
        from src.core.simulation.models import FieldType

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,velocity_x,velocity_y,velocity_z\n"
            "0.0,0.0,0.0,10.0,20.0,30.0\n"
            "1.0,0.0,0.0,15.0,25.0,35.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        timestep = result.timesteps[0]
        fields = timestep.fields

        # Should have one vector field "velocity"
        velocity_field = fields.get("velocity")

        assert velocity_field is not None
        assert velocity_field.field_type == FieldType.VECTOR
        assert velocity_field.data.shape == (2, 3)
        assert np.allclose(velocity_field.data[0], [10.0, 20.0, 30.0])

    def test_parse_empty_csv_raises_error(self, tmp_path: Path) -> None:
        """Test parsing empty CSV raises ValueError"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("x,y,z\n")  # Only header

        parser = CSVParser()

        with pytest.raises(ValueError, match="Empty CSV file"):
            parser.parse(csv_file)

    def test_parse_csv_with_time_column(self, tmp_path: Path) -> None:
        """Test parsing CSV with time column"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,time,temperature\n"
            "0.0,0.0,0.0,1.5,300.0\n"
            "1.0,0.0,0.0,1.5,310.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file, has_time=True)

        timestep = result.timesteps[0]

        assert timestep.time == 1.5

    def test_parse_csv_with_step_column(self, tmp_path: Path) -> None:
        """Test parsing CSV with step column"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,step,value\n"
            "0.0,0.0,0.0,5,100.0\n"
            "1.0,0.0,0.0,5,200.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        timestep = result.timesteps[0]

        assert timestep.step == 5

    def test_parse_csv_custom_delimiter(self, tmp_path: Path) -> None:
        """Test parsing CSV with custom delimiter"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x;y;z;temperature\n"
            "0.0;0.0;0.0;300.0\n"
            "1.0;0.0;0.0;310.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file, delimiter=";")

        assert result.num_timesteps == 1
        vertices = result.mesh.vertices
        assert vertices.shape == (2, 3)


class TestCSVParserHelperMethods:
    """Test CSV parser helper methods"""

    def test_find_column_finds_exact_match(self) -> None:
        """Test _find_column finds exact match"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        columns = ["x", "y", "z", "temperature"]

        result = parser._find_column(columns, ["x"])

        assert result == "x"

    def test_find_column_finds_first_candidate(self) -> None:
        """Test _find_column finds first matching candidate"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        columns = ["X", "y", "z"]

        result = parser._find_column(columns, ["x", "X", "coord_x"])

        assert result == "X"

    def test_find_column_returns_none_if_not_found(self) -> None:
        """Test _find_column returns None if not found"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        columns = ["a", "b", "c"]

        result = parser._find_column(columns, ["x", "y", "z"])

        assert result is None

    def test_find_vector_fields_detects_vector_pattern(self) -> None:
        """Test _find_vector_fields detects name_x/y/z pattern"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        columns = ["x", "y", "z", "velocity_x", "velocity_y", "velocity_z"]
        exclude = {"x", "y", "z"}

        vector_fields = parser._find_vector_fields(columns, exclude)

        assert "velocity" in vector_fields
        assert vector_fields["velocity"]["x"] == "velocity_x"
        assert vector_fields["velocity"]["y"] == "velocity_y"
        assert vector_fields["velocity"]["z"] == "velocity_z"

    def test_find_vector_fields_handles_uppercase(self) -> None:
        """Test _find_vector_fields handles uppercase suffixes"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        columns = ["x", "y", "z", "Force_X", "Force_Y", "Force_Z"]
        exclude = {"x", "y", "z"}

        vector_fields = parser._find_vector_fields(columns, exclude)

        assert "Force" in vector_fields


class TestCSVParserEdgeCases:
    """Test CSV parser edge cases"""

    def test_parse_csv_missing_x_column_raises_error(self, tmp_path: Path) -> None:
        """Test parsing CSV without x column raises ValueError"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "a,b,c\n"
            "1,2,3\n"
        )

        parser = CSVParser()

        with pytest.raises(ValueError, match="CSV must have x, y columns"):
            parser.parse(csv_file)

    def test_parse_csv_missing_y_column_raises_error(self, tmp_path: Path) -> None:
        """Test parsing CSV without y column raises ValueError"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,a,b\n"
            "1,2,3\n"
        )

        parser = CSVParser()

        with pytest.raises(ValueError, match="CSV must have x, y columns"):
            parser.parse(csv_file)

    def test_parse_csv_with_non_numeric_values(self, tmp_path: Path) -> None:
        """Test parsing CSV with non-numeric values (should convert to 0.0)"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,value\n"
            "0.0,0.0,0.0,100.0\n"
            "1.0,1.0,1.0,invalid\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        # Should not raise error, invalid value converted to 0.0
        assert result is not None

    def test_parse_csv_case_insensitive_columns(self, tmp_path: Path) -> None:
        """Test CSV parser handles case-insensitive column names"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "X,Y,Z,Temperature\n"
            "0.0,0.0,0.0,300.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file)

        # Should successfully parse uppercase X, Y, Z
        assert result.mesh.num_vertices == 1

    def test_parse_csv_default_time_and_step(self, tmp_path: Path) -> None:
        """Test CSV parser uses default time and step when not specified"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,value\n"
            "0.0,0.0,0.0,100.0\n"
        )

        parser = CSVParser()
        result = parser.parse(csv_file, default_time=5.0, default_step=10)

        timestep = result.timesteps[0]

        assert timestep.time == 5.0
        assert timestep.step == 10
