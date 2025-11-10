"""
Tests for JSON Parser

Tests JSONParser, HierarchicalExtractor, and related functionality.
"""

import json
from pathlib import Path
from typing import Any
import pytest


class TestJSONParser:
    """Test JSONParser basic functionality"""

    def test_json_parser_creation(self) -> None:
        """Test creating JSONParser"""
        from src.core.json_processing.parser import JSONParser

        parser = JSONParser()

        assert parser is not None
        assert parser.validate is True

    def test_json_parser_creation_without_validation(self) -> None:
        """Test creating JSONParser without validation"""
        from src.core.json_processing.parser import JSONParser

        parser = JSONParser(validate=False)

        assert parser.validate is False

    def test_parse_file(self, tmp_path: Path) -> None:
        """Test parsing JSON file"""
        from src.core.json_processing.parser import JSONParser

        # Create test JSON file
        json_file = tmp_path / "test.json"
        test_data = {"name": "Test", "value": 42}
        json_file.write_text(json.dumps(test_data))

        parser = JSONParser(validate=False)
        result = parser.parse_file(json_file)

        assert result == test_data
        assert result["name"] == "Test"
        assert result["value"] == 42

    def test_parse_file_raises_error_for_missing_file(self) -> None:
        """Test parse_file raises FileNotFoundError for missing file"""
        from src.core.json_processing.parser import JSONParser

        parser = JSONParser(validate=False)

        with pytest.raises(FileNotFoundError, match="not found"):
            parser.parse_file("/nonexistent/file.json")

    def test_parse_file_raises_error_for_invalid_json(self, tmp_path: Path) -> None:
        """Test parse_file raises JSONDecodeError for invalid JSON"""
        from src.core.json_processing.parser import JSONParser

        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json")

        parser = JSONParser(validate=False)

        with pytest.raises(json.JSONDecodeError):
            parser.parse_file(json_file)

    def test_parse_string(self) -> None:
        """Test parsing JSON string"""
        from src.core.json_processing.parser import JSONParser

        parser = JSONParser(validate=False)
        json_str = '{"name": "Test", "value": 42}'

        result = parser.parse_string(json_str)

        assert result["name"] == "Test"
        assert result["value"] == 42

    def test_parse_string_invalid_json_raises_error(self) -> None:
        """Test parse_string raises JSONDecodeError for invalid JSON"""
        from src.core.json_processing.parser import JSONParser

        parser = JSONParser(validate=False)
        invalid_json = "{invalid}"

        with pytest.raises(json.JSONDecodeError):
            parser.parse_string(invalid_json)

    def test_parse_nested_json(self) -> None:
        """Test parsing nested JSON structure"""
        from src.core.json_processing.parser import JSONParser

        parser = JSONParser(validate=False)
        json_str = '{"metadata": {"name": "Sim", "version": "1.0"}, "data": [1, 2, 3]}'

        result = parser.parse_string(json_str)

        assert result["metadata"]["name"] == "Sim"
        assert result["metadata"]["version"] == "1.0"
        assert result["data"] == [1, 2, 3]


class TestHierarchicalExtractor:
    """Test HierarchicalExtractor"""

    def test_extract_by_path_simple(self) -> None:
        """Test extracting value by simple path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"name": "Test", "value": 42}
        result = HierarchicalExtractor.extract_by_path(data, "name")

        assert result == "Test"

    def test_extract_by_path_nested(self) -> None:
        """Test extracting value by nested path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"metadata": {"name": "CFD Sim", "version": "1.0"}}
        result = HierarchicalExtractor.extract_by_path(data, "metadata.name")

        assert result == "CFD Sim"

    def test_extract_by_path_deeply_nested(self) -> None:
        """Test extracting value by deeply nested path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"a": {"b": {"c": {"d": "deep value"}}}}
        result = HierarchicalExtractor.extract_by_path(data, "a.b.c.d")

        assert result == "deep value"

    def test_extract_by_path_returns_none_for_missing(self) -> None:
        """Test extract_by_path returns None for missing path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"name": "Test"}
        result = HierarchicalExtractor.extract_by_path(data, "nonexistent.path")

        assert result is None

    def test_extract_by_path_from_list(self) -> None:
        """Test extracting value from list by index"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"items": [{"name": "first"}, {"name": "second"}, {"name": "third"}]}
        result = HierarchicalExtractor.extract_by_path(data, "items.1.name")

        assert result == "second"

    def test_extract_by_path_from_list_out_of_bounds(self) -> None:
        """Test extract_by_path returns None for out of bounds list index"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"items": [1, 2, 3]}
        result = HierarchicalExtractor.extract_by_path(data, "items.10")

        assert result is None

    def test_extract_by_path_custom_separator(self) -> None:
        """Test extract_by_path with custom separator"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"metadata": {"name": "Test"}}
        result = HierarchicalExtractor.extract_by_path(data, "metadata/name", separator="/")

        assert result == "Test"

    def test_extract_multiple(self) -> None:
        """Test extracting multiple paths at once"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"metadata": {"name": "Sim", "version": "1.0"}, "status": "complete"}

        paths = ["metadata.name", "metadata.version", "status"]
        result = HierarchicalExtractor.extract_multiple(data, paths)

        assert result["metadata.name"] == "Sim"
        assert result["metadata.version"] == "1.0"
        assert result["status"] == "complete"

    def test_extract_multiple_with_missing_paths(self) -> None:
        """Test extract_multiple includes None for missing paths"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"name": "Test"}
        paths = ["name", "missing.path"]

        result = HierarchicalExtractor.extract_multiple(data, paths)

        assert result["name"] == "Test"
        assert result["missing.path"] is None

    def test_set_by_path_simple(self) -> None:
        """Test setting value by simple path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"name": "Old"}
        HierarchicalExtractor.set_by_path(data, "name", "New")

        assert data["name"] == "New"

    def test_set_by_path_nested(self) -> None:
        """Test setting value by nested path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"metadata": {"name": "Old"}}
        HierarchicalExtractor.set_by_path(data, "metadata.name", "New")

        assert data["metadata"]["name"] == "New"

    def test_set_by_path_creates_missing_keys(self) -> None:
        """Test set_by_path creates missing intermediate keys"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data: dict[str, Any] = {}
        HierarchicalExtractor.set_by_path(data, "metadata.name", "Test")

        assert data["metadata"]["name"] == "Test"

    def test_set_by_path_deeply_nested(self) -> None:
        """Test set_by_path with deeply nested path"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data: dict[str, Any] = {}
        HierarchicalExtractor.set_by_path(data, "a.b.c.d", "value")

        assert data["a"]["b"]["c"]["d"] == "value"

    def test_set_by_path_custom_separator(self) -> None:
        """Test set_by_path with custom separator"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data: dict[str, Any] = {}
        HierarchicalExtractor.set_by_path(data, "metadata/name", "Test", separator="/")

        assert data["metadata"]["name"] == "Test"

    def test_flatten_simple(self) -> None:
        """Test flattening simple nested dictionary"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"a": {"b": 1}, "c": 2}
        result = HierarchicalExtractor.flatten(data)

        assert result == {"a.b": 1, "c": 2}

    def test_flatten_deeply_nested(self) -> None:
        """Test flattening deeply nested dictionary"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"a": {"b": {"c": 1}}, "d": 2}
        result = HierarchicalExtractor.flatten(data)

        assert result == {"a.b.c": 1, "d": 2}

    def test_flatten_with_custom_separator(self) -> None:
        """Test flatten with custom separator"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data = {"a": {"b": 1}}
        result = HierarchicalExtractor.flatten(data, separator="/")

        assert result == {"a/b": 1}

    def test_flatten_empty_dict(self) -> None:
        """Test flattening empty dictionary"""
        from src.core.json_processing.parser import HierarchicalExtractor

        data: dict[str, Any] = {}
        result = HierarchicalExtractor.flatten(data)

        assert result == {}

    def test_unflatten_simple(self) -> None:
        """Test unflattening simple flat dictionary"""
        from src.core.json_processing.parser import HierarchicalExtractor

        flat = {"a.b": 1, "c": 2}
        result = HierarchicalExtractor.unflatten(flat)

        assert result == {"a": {"b": 1}, "c": 2}

    def test_unflatten_deeply_nested(self) -> None:
        """Test unflattening deeply nested paths"""
        from src.core.json_processing.parser import HierarchicalExtractor

        flat = {"a.b.c": 1, "d": 2}
        result = HierarchicalExtractor.unflatten(flat)

        assert result == {"a": {"b": {"c": 1}}, "d": 2}

    def test_unflatten_with_custom_separator(self) -> None:
        """Test unflatten with custom separator"""
        from src.core.json_processing.parser import HierarchicalExtractor

        flat = {"a/b": 1}
        result = HierarchicalExtractor.unflatten(flat, separator="/")

        assert result == {"a": {"b": 1}}

    def test_flatten_unflatten_roundtrip(self) -> None:
        """Test flatten and unflatten preserve data"""
        from src.core.json_processing.parser import HierarchicalExtractor

        original = {"a": {"b": {"c": 1}}, "d": 2, "e": {"f": 3}}

        flattened = HierarchicalExtractor.flatten(original)
        restored = HierarchicalExtractor.unflatten(flattened)

        assert restored == original


class TestChunkedJSONWriter:
    """Test ChunkedJSONWriter"""

    def test_chunked_writer_context_manager(self, tmp_path: Path) -> None:
        """Test ChunkedJSONWriter as context manager"""
        from src.core.json_processing.parser import ChunkedJSONWriter

        output_file = tmp_path / "output.json"

        with ChunkedJSONWriter(output_file, indent=None) as writer:
            assert writer is not None

        # File should be created
        assert output_file.exists()

    def test_write_simple_object(self, tmp_path: Path) -> None:
        """Test writing simple JSON object"""
        from src.core.json_processing.parser import ChunkedJSONWriter

        output_file = tmp_path / "output.json"

        with ChunkedJSONWriter(output_file, indent=None) as writer:
            writer.start_object()
            writer.write_field("name", "Test")
            writer.write_field("value", 42)
            writer.end_object()

        # Read and verify
        with open(output_file) as f:
            data = json.load(f)

        assert data["name"] == "Test"
        assert data["value"] == 42

    def test_write_array(self, tmp_path: Path) -> None:
        """Test writing JSON array"""
        from src.core.json_processing.parser import ChunkedJSONWriter

        output_file = tmp_path / "output.json"

        with ChunkedJSONWriter(output_file, indent=None) as writer:
            writer.start_object()
            writer.start_array("items")
            writer.write_item(1)
            writer.write_item(2)
            writer.write_item(3)
            writer.end_array()
            writer.end_object()

        # Read and verify
        with open(output_file) as f:
            data = json.load(f)

        assert data["items"] == [1, 2, 3]

    def test_write_nested_objects(self, tmp_path: Path) -> None:
        """Test writing nested JSON objects"""
        from src.core.json_processing.parser import ChunkedJSONWriter

        output_file = tmp_path / "output.json"

        with ChunkedJSONWriter(output_file, indent=2) as writer:
            writer.start_object()
            writer.write_field("metadata", {"name": "Test", "version": "1.0"})
            writer.end_object()

        # Read and verify
        with open(output_file) as f:
            data = json.load(f)

        assert data["metadata"]["name"] == "Test"
        assert data["metadata"]["version"] == "1.0"

    def test_write_multiple_fields(self, tmp_path: Path) -> None:
        """Test writing multiple fields"""
        from src.core.json_processing.parser import ChunkedJSONWriter

        output_file = tmp_path / "output.json"

        with ChunkedJSONWriter(output_file, indent=None) as writer:
            writer.start_object()
            writer.write_field("field1", "value1")
            writer.write_field("field2", "value2")
            writer.write_field("field3", "value3")
            writer.end_object()

        with open(output_file) as f:
            data = json.load(f)

        assert len(data) == 3
        assert data["field1"] == "value1"
        assert data["field2"] == "value2"
        assert data["field3"] == "value3"


class TestJSONParserIntegration:
    """Integration tests for JSON parsing"""

    def test_parse_and_extract(self, tmp_path: Path) -> None:
        """Test parsing file and extracting nested data"""
        from src.core.json_processing.parser import JSONParser, HierarchicalExtractor

        # Create test file
        json_file = tmp_path / "test.json"
        test_data = {
            "metadata": {
                "name": "CFD Simulation",
                "version": "1.0"
            },
            "results": {
                "temperature": {
                    "min": 273.15,
                    "max": 373.15
                }
            }
        }
        json_file.write_text(json.dumps(test_data))

        # Parse and extract
        parser = JSONParser(validate=False)
        data = parser.parse_file(json_file)

        name = HierarchicalExtractor.extract_by_path(data, "metadata.name")
        max_temp = HierarchicalExtractor.extract_by_path(data, "results.temperature.max")

        assert name == "CFD Simulation"
        assert max_temp == 373.15

    def test_modify_and_write(self, tmp_path: Path) -> None:
        """Test modifying JSON data and writing back"""
        from src.core.json_processing.parser import (
            JSONParser, HierarchicalExtractor, ChunkedJSONWriter
        )

        # Parse original file
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"value": 10}))

        parser = JSONParser(validate=False)
        data = parser.parse_file(input_file)

        # Modify
        HierarchicalExtractor.set_by_path(data, "value", 20)
        HierarchicalExtractor.set_by_path(data, "new_field", "added")

        # Write to new file
        output_file = tmp_path / "output.json"
        with ChunkedJSONWriter(output_file, indent=None) as writer:
            writer.start_object()
            for key, value in data.items():
                writer.write_field(key, value)
            writer.end_object()

        # Verify
        result = parser.parse_file(output_file)
        assert result["value"] == 20
        assert result["new_field"] == "added"
