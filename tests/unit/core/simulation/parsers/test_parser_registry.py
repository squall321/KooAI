"""
Tests for Parser Registry

Tests ParserRegistry functionality including parser registration and automatic selection.
"""

from pathlib import Path
from unittest.mock import Mock
import pytest


class TestParserRegistryBasics:
    """Test ParserRegistry basic functionality"""

    def test_parser_registry_creation(self):
        """Test ParserRegistry can be created"""
        from src.core.simulation.parsers.base import ParserRegistry

        registry = ParserRegistry()

        assert registry is not None

    def test_parser_registry_starts_empty(self):
        """Test ParserRegistry starts with no parsers"""
        from src.core.simulation.parsers.base import ParserRegistry

        registry = ParserRegistry()

        parsers = registry.list_parsers()

        assert len(parsers) == 0
        assert isinstance(parsers, list)


class TestParserRegistration:
    """Test parser registration"""

    def test_register_parser(self):
        """Test registering a parser"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()
        mock_parser = Mock(spec=BaseParser)

        registry.register(mock_parser)

        parsers = registry.list_parsers()

        assert len(parsers) == 1
        assert parsers[0] == mock_parser

    def test_register_multiple_parsers(self):
        """Test registering multiple parsers"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()
        parser1 = Mock(spec=BaseParser)
        parser2 = Mock(spec=BaseParser)
        parser3 = Mock(spec=BaseParser)

        registry.register(parser1)
        registry.register(parser2)
        registry.register(parser3)

        parsers = registry.list_parsers()

        assert len(parsers) == 3

    def test_list_parsers_returns_copy(self):
        """Test list_parsers returns a copy (not original list)"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()
        parser = Mock(spec=BaseParser)
        registry.register(parser)

        parsers1 = registry.list_parsers()
        parsers2 = registry.list_parsers()

        # Should be different list objects
        assert parsers1 is not parsers2
        # But contain same parsers
        assert parsers1[0] is parsers2[0]


class TestGetParser:
    """Test get_parser functionality"""

    def test_get_parser_finds_matching_parser(self):
        """Test get_parser returns matching parser"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        csv_parser = Mock(spec=BaseParser)
        csv_parser.can_parse.return_value = True

        vtk_parser = Mock(spec=BaseParser)
        vtk_parser.can_parse.return_value = False

        registry.register(csv_parser)
        registry.register(vtk_parser)

        file_path = Path("test.csv")
        parser = registry.get_parser(file_path)

        assert parser == csv_parser
        csv_parser.can_parse.assert_called_once_with(file_path)

    def test_get_parser_returns_none_if_no_match(self):
        """Test get_parser returns None if no parser can parse file"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        parser1 = Mock(spec=BaseParser)
        parser1.can_parse.return_value = False

        parser2 = Mock(spec=BaseParser)
        parser2.can_parse.return_value = False

        registry.register(parser1)
        registry.register(parser2)

        file_path = Path("unknown.xyz")
        parser = registry.get_parser(file_path)

        assert parser is None

    def test_get_parser_returns_first_matching_parser(self):
        """Test get_parser returns first parser that can parse file"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        parser1 = Mock(spec=BaseParser, name="parser1")
        parser1.can_parse.return_value = True

        parser2 = Mock(spec=BaseParser, name="parser2")
        parser2.can_parse.return_value = True

        registry.register(parser1)
        registry.register(parser2)

        file_path = Path("test.csv")
        parser = registry.get_parser(file_path)

        # Should return first matching parser
        assert parser == parser1

    def test_get_parser_checks_parsers_in_order(self):
        """Test get_parser checks parsers in registration order"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        parser1 = Mock(spec=BaseParser)
        parser1.can_parse.return_value = False

        parser2 = Mock(spec=BaseParser)
        parser2.can_parse.return_value = True

        parser3 = Mock(spec=BaseParser)
        parser3.can_parse.return_value = True

        registry.register(parser1)
        registry.register(parser2)
        registry.register(parser3)

        file_path = Path("test.csv")
        parser = registry.get_parser(file_path)

        # Should return parser2 (first match)
        assert parser == parser2
        # parser3 should not be checked
        parser3.can_parse.assert_not_called()


class TestParse:
    """Test parse functionality"""

    def test_parse_calls_parser_parse_method(self):
        """Test parse calls the appropriate parser's parse method"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        mock_parser = Mock(spec=BaseParser)
        mock_parser.can_parse.return_value = True
        mock_result = Mock()
        mock_parser.parse.return_value = mock_result

        registry.register(mock_parser)

        file_path = Path("test.csv")
        result = registry.parse(file_path)

        assert result == mock_result
        mock_parser.parse.assert_called_once_with(file_path)

    def test_parse_passes_options_to_parser(self):
        """Test parse passes kwargs to parser"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        mock_parser = Mock(spec=BaseParser)
        mock_parser.can_parse.return_value = True
        mock_parser.parse.return_value = Mock()

        registry.register(mock_parser)

        file_path = Path("test.csv")
        registry.parse(file_path, delimiter=";", has_time=True)

        mock_parser.parse.assert_called_once_with(
            file_path,
            delimiter=";",
            has_time=True
        )

    def test_parse_raises_error_if_no_parser_found(self):
        """Test parse raises ValueError if no suitable parser found"""
        from src.core.simulation.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        parser = Mock(spec=BaseParser)
        parser.can_parse.return_value = False
        registry.register(parser)

        file_path = Path("unknown.xyz")

        with pytest.raises(ValueError, match="No suitable parser found"):
            registry.parse(file_path)

    def test_parse_with_empty_registry_raises_error(self):
        """Test parse raises ValueError with empty registry"""
        from src.core.simulation.parsers.base import ParserRegistry

        registry = ParserRegistry()
        file_path = Path("test.csv")

        with pytest.raises(ValueError, match="No suitable parser found"):
            registry.parse(file_path)


class TestParserRegistryIntegration:
    """Test ParserRegistry with real parsers"""

    def test_register_csv_and_vtk_parsers(self):
        """Test registering CSV and VTK parsers"""
        from src.core.simulation.parsers.base import ParserRegistry
        from src.core.simulation.parsers.csv_parser import CSVParser
        from src.core.simulation.parsers.vtk_parser import VTKParser

        registry = ParserRegistry()

        csv_parser = CSVParser()
        vtk_parser = VTKParser()

        registry.register(csv_parser)
        registry.register(vtk_parser)

        parsers = registry.list_parsers()

        assert len(parsers) == 2

    def test_get_parser_selects_correct_parser_for_csv(self):
        """Test get_parser selects CSV parser for .csv files"""
        from src.core.simulation.parsers.base import ParserRegistry
        from src.core.simulation.parsers.csv_parser import CSVParser
        from src.core.simulation.parsers.vtk_parser import VTKParser

        registry = ParserRegistry()
        csv_parser = CSVParser()
        vtk_parser = VTKParser()

        registry.register(csv_parser)
        registry.register(vtk_parser)

        csv_file = Path("test.csv")
        parser = registry.get_parser(csv_file)

        assert isinstance(parser, CSVParser)

    def test_get_parser_selects_correct_parser_for_vtk(self, tmp_path):
        """Test get_parser selects VTK parser for .vtk files"""
        from src.core.simulation.parsers.base import ParserRegistry
        from src.core.simulation.parsers.csv_parser import CSVParser
        from src.core.simulation.parsers.vtk_parser import VTKParser

        # Create a valid VTK file for testing
        vtk_file = tmp_path / "test.vtk"
        vtk_file.write_text("# vtk DataFile Version 3.0\nTest\nASCII\n")

        registry = ParserRegistry()
        csv_parser = CSVParser()
        vtk_parser = VTKParser()

        registry.register(csv_parser)
        registry.register(vtk_parser)

        parser = registry.get_parser(vtk_file)

        assert isinstance(parser, VTKParser)

    def test_parse_with_real_csv_file(self, tmp_path):
        """Test parse with actual CSV file"""
        from src.core.simulation.parsers.base import ParserRegistry
        from src.core.simulation.parsers.csv_parser import CSVParser

        registry = ParserRegistry()
        registry.register(CSVParser())

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "x,y,z,temperature\n"
            "0.0,0.0,0.0,300.0\n"
            "1.0,0.0,0.0,310.0\n"
        )

        result = registry.parse(csv_file)

        assert result is not None
        assert result.simulation_type == "CSV"
        assert result.mesh.num_vertices == 2


class TestBaseParserInterface:
    """Test BaseParser abstract interface"""

    def test_base_parser_cannot_be_instantiated(self):
        """Test BaseParser cannot be instantiated directly"""
        from src.core.simulation.parsers.base import BaseParser

        with pytest.raises(TypeError):
            BaseParser()

    def test_base_parser_validate_file_checks_existence(self, tmp_path):
        """Test validate_file checks file existence"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        missing_file = Path("/nonexistent/file.csv")

        with pytest.raises(FileNotFoundError):
            parser.validate_file(missing_file)

    def test_base_parser_validate_file_checks_is_file(self, tmp_path):
        """Test validate_file checks if path is a file"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        directory = tmp_path / "test_dir"
        directory.mkdir()

        with pytest.raises(ValueError, match="Not a file"):
            parser.validate_file(directory)

    def test_base_parser_validate_file_checks_extension(self, tmp_path):
        """Test validate_file checks file extension"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        wrong_ext = tmp_path / "test.txt"
        wrong_ext.write_text("test")

        with pytest.raises(ValueError, match="Unsupported file extension"):
            parser.validate_file(wrong_ext)

    def test_base_parser_validate_file_succeeds_for_valid_file(self, tmp_path):
        """Test validate_file succeeds for valid file"""
        from src.core.simulation.parsers.csv_parser import CSVParser

        parser = CSVParser()
        valid_file = tmp_path / "test.csv"
        valid_file.write_text("x,y,z\n")

        # Should not raise any exception
        parser.validate_file(valid_file)
