"""
Integration tests for streaming parsers

Tests the streaming CSV and JSON parsers with real files.
"""

import pytest
import tempfile
import json
from pathlib import Path
from io import StringIO
from typing import Generator, Any, Iterator

from src.core.simulation.parsers.streaming_csv_parser import StreamingCSVParser
from src.core.simulation.parsers.streaming_json_parser import StreamingJSONParser
from src.core.exceptions import ParsingError


class TestStreamingCSVParser:
    """Test streaming CSV parser with real files"""

    @pytest.fixture
    def csv_parser(self) -> StreamingCSVParser:
        """Create CSV parser instance"""
        return StreamingCSVParser(chunk_rows=100)

    @pytest.fixture
    def small_csv_file(self, tmp_path: Path) -> Path:
        """Create small CSV file (< 1 chunk)"""
        csv_file = tmp_path / "small.csv"
        content = "x,y,z,temperature\n"
        for i in range(50):
            content += f"{i},{i*2},{i*3},{300+i}\n"
        csv_file.write_text(content)
        return csv_file

    @pytest.fixture
    def large_csv_file(self, tmp_path: Path) -> Path:
        """Create large CSV file (multiple chunks)"""
        csv_file = tmp_path / "large.csv"
        content = "x,y,z,temperature,pressure\n"
        # Create 10,000 rows
        for i in range(10000):
            content += f"{i*0.1},{i*0.2},{i*0.3},{300+i%500},{101325+i%1000}\n"
        csv_file.write_text(content)
        return csv_file

    @pytest.fixture
    def malformed_csv_file(self, tmp_path: Path) -> Path:
        """Create CSV with inconsistent columns"""
        csv_file = tmp_path / "malformed.csv"
        content = "x,y,z\n"
        content += "1,2,3\n"
        content += "4,5\n"  # Missing column
        content += "6,7,8,9\n"  # Extra column
        csv_file.write_text(content)
        return csv_file

    def test_parse_small_file(self, csv_parser: StreamingCSVParser, small_csv_file: Path) -> None:
        """Test parsing small CSV file"""
        result = csv_parser.parse(small_csv_file)

        assert result is not None
        assert result.mesh is not None
        assert result.mesh.vertices is not None

        # Verify we have 50 rows
        assert len(result.mesh.vertices) == 50

        # Verify fields exist
        assert len(result.timesteps) > 0
        timestep = result.timesteps[0]
        assert len(timestep.fields) > 0

    def test_parse_large_file_chunks(self, csv_parser: StreamingCSVParser, large_csv_file: Path) -> None:
        """Test parsing large file yields multiple chunks"""
        chunks = []
        for chunk in csv_parser.read_chunks(large_csv_file):
            chunks.append(chunk)
            # Verify chunk size constraint
            assert len(chunk.rows) <= 100

        # Should have multiple chunks
        assert len(chunks) > 1

        # Verify total rows
        total_rows = sum(len(chunk.rows) for chunk in chunks)
        assert total_rows == 10000

    def test_memory_efficiency(self, csv_parser: StreamingCSVParser, large_csv_file: Path) -> None:
        """Test that streaming doesn't load entire file at once"""
        import sys

        # Process one chunk at a time
        max_chunk_memory = 0
        for chunk in csv_parser.read_chunks(large_csv_file):
            chunk_memory = sys.getsizeof(chunk.rows)
            max_chunk_memory = max(max_chunk_memory, chunk_memory)

        # Each chunk should be much smaller than full file
        file_size = large_csv_file.stat().st_size
        # Chunk memory should be < 10% of file size (rough estimate)
        assert max_chunk_memory < file_size * 0.1

    def test_parse_with_different_chunk_sizes(self, small_csv_file: Path) -> None:
        """Test parsing with different chunk sizes"""
        for chunk_rows in [10, 50, 100]:
            parser = StreamingCSVParser(chunk_rows=chunk_rows)
            chunks = list(parser.read_chunks(small_csv_file))

            # Verify all chunks respect size limit
            for chunk in chunks[:-1]:  # All but last
                assert len(chunk.rows) <= chunk_rows

            # Verify total rows
            total_rows = sum(len(chunk.rows) for chunk in chunks)
            assert total_rows == 50

    def test_column_detection(self, csv_parser: StreamingCSVParser, large_csv_file: Path) -> None:
        """Test automatic column detection"""
        result = csv_parser.parse(large_csv_file)

        # Verify we have timestep with fields
        assert len(result.timesteps) > 0
        timestep = result.timesteps[0]

        # Get field names from the dictionary
        field_names = set(timestep.fields.keys())

        # temperature and pressure fields should exist
        assert "temperature" in field_names
        assert "pressure" in field_names

    def test_numeric_conversion(self, csv_parser: StreamingCSVParser, small_csv_file: Path) -> None:
        """Test automatic numeric type conversion"""
        result = csv_parser.parse(small_csv_file)

        # Verify mesh vertices are numeric
        assert result.mesh.vertices.dtype.kind == "f"  # float

        # Verify fields are numeric
        timestep = result.timesteps[0]
        for field in timestep.fields.values():
            assert field.data.dtype.kind in ["i", "f"]  # int or float

    def test_parse_with_missing_values(self, tmp_path: Path, csv_parser: StreamingCSVParser) -> None:
        """Test parsing CSV with missing values"""
        csv_file = tmp_path / "missing.csv"
        content = "x,y,z\n"
        content += "1,2,3\n"
        content += "4,,6\n"  # Missing value
        content += "7,8,\n"  # Missing value
        csv_file.write_text(content)

        result = csv_parser.parse(csv_file)
        assert result is not None

        # Missing values should be handled (converted to 0.0)
        assert len(result.mesh.vertices) == 3

    def test_parse_empty_file(self, tmp_path: Path, csv_parser: StreamingCSVParser) -> None:
        """Test parsing empty CSV file"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        with pytest.raises((ParsingError, ValueError)):
            csv_parser.parse(csv_file)

    def test_parse_header_only(self, tmp_path: Path, csv_parser: StreamingCSVParser) -> None:
        """Test parsing CSV with only header"""
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("x,y,z\n")

        # Should raise error or return empty result
        with pytest.raises((ParsingError, ValueError)):
            csv_parser.parse(csv_file)

    def test_parse_nonexistent_file(self, csv_parser: StreamingCSVParser) -> None:
        """Test parsing non-existent file"""
        with pytest.raises((FileNotFoundError, ParsingError)):
            csv_parser.parse(Path("/nonexistent/file.csv"))


class TestStreamingJSONParser:
    """Test streaming JSON parser with real files"""

    @pytest.fixture
    def json_parser(self) -> StreamingJSONParser:
        """Create JSON parser instance"""
        return StreamingJSONParser(chunk_size=100)

    @pytest.fixture
    def small_json_file(self, tmp_path: Path) -> Path:
        """Create small JSON file"""
        json_file = tmp_path / "small.json"
        data = {
            "metadata": {"name": "test", "version": "1.0"},
            "points": [{"x": i, "y": i * 2, "z": i * 3, "temperature": 300 + i} for i in range(50)],
        }
        json_file.write_text(json.dumps(data))
        return json_file

    @pytest.fixture
    def large_json_array_file(self, tmp_path: Path) -> Path:
        """Create large JSON array file"""
        json_file = tmp_path / "large_array.json"
        # Create array of objects
        data = [
            {
                "id": i,
                "x": i * 0.1,
                "y": i * 0.2,
                "z": i * 0.3,
                "temperature": 300 + (i % 500),
                "pressure": 101325 + (i % 1000),
            }
            for i in range(5000)
        ]
        json_file.write_text(json.dumps(data))
        return json_file

    @pytest.fixture
    def nested_json_file(self, tmp_path: Path) -> Path:
        """Create JSON with nested structure"""
        json_file = tmp_path / "nested.json"
        data = {
            "simulation": {
                "metadata": {"name": "test", "type": "CFD"},
                "results": {
                    "timesteps": [
                        {
                            "time": i,
                            "fields": {
                                "temperature": [300 + j for j in range(100)],
                                "pressure": [101325 + j for j in range(100)],
                            },
                        }
                        for i in range(10)
                    ]
                },
            }
        }
        json_file.write_text(json.dumps(data))
        return json_file

    def test_parse_small_json(self, json_parser: StreamingJSONParser, small_json_file: Path) -> None:
        """Test parsing small JSON file"""
        result = json_parser.parse(small_json_file, json_path="points.item")

        assert result is not None
        assert result.mesh is not None
        assert len(result.mesh.vertices) == 50

    def test_parse_array_streaming(self, json_parser: StreamingJSONParser, large_json_array_file: Path) -> None:
        """Test streaming array parsing"""
        import time

        start_time = time.time()
        chunks = list(json_parser.read_chunks(large_json_array_file, json_path="item"))
        elapsed = time.time() - start_time

        # Count total items from all chunks
        total_items = sum(len(chunk.items) for chunk in chunks)
        assert total_items == 5000

        # Verify item structure
        first_chunk = chunks[0]
        assert len(first_chunk.items) > 0
        first_item = first_chunk.items[0]
        assert "x" in first_item
        assert "y" in first_item
        assert "temperature" in first_item

    def test_memory_efficiency_streaming(self, json_parser: StreamingJSONParser, large_json_array_file: Path) -> None:
        """Test memory efficiency of streaming"""
        import sys

        max_batch_memory = 0
        batch_count = 0

        for chunk in json_parser.read_chunks(large_json_array_file, json_path="item"):
            batch_memory = sys.getsizeof(chunk.items)
            max_batch_memory = max(max_batch_memory, batch_memory)
            batch_count += 1

        # Should have multiple batches
        assert batch_count > 1

        # Each batch should be smaller than full file
        file_size = large_json_array_file.stat().st_size
        assert max_batch_memory < file_size * 0.5

    def test_parse_nested_structure(self, json_parser: StreamingJSONParser, nested_json_file: Path) -> None:
        """Test parsing nested JSON structure"""
        # Parse nested structure by extracting timesteps array
        result = json_parser.parse(nested_json_file, json_path="simulation.results.timesteps.item")

        assert result is not None
        assert result.mesh is not None
        # Should have parsed 10 timesteps, each with 100 points
        assert len(result.mesh.vertices) == 1000  # 10 * 100

    def test_parse_with_path_extraction(self, json_parser: StreamingJSONParser, nested_json_file: Path) -> None:
        """Test extracting specific JSON path"""
        # Parse using specific path to extract timesteps
        chunks = list(json_parser.read_chunks(nested_json_file, json_path="simulation.results.timesteps.item"))

        # Should have chunks containing timestep items
        assert len(chunks) > 0
        total_timesteps = sum(len(chunk.items) for chunk in chunks)
        assert total_timesteps == 10

        # Verify structure of first timestep
        first_item = chunks[0].items[0]
        assert "time" in first_item
        assert "fields" in first_item

    def test_parse_invalid_json(self, tmp_path: Path, json_parser: StreamingJSONParser) -> None:
        """Test parsing invalid JSON"""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json content")

        with pytest.raises((json.JSONDecodeError, ParsingError)):
            json_parser.parse(json_file)

    def test_parse_empty_json(self, tmp_path: Path, json_parser: StreamingJSONParser) -> None:
        """Test parsing empty JSON file"""
        json_file = tmp_path / "empty.json"
        json_file.write_text("")

        with pytest.raises((json.JSONDecodeError, ParsingError)):
            json_parser.parse(json_file)

    def test_parse_empty_array(self, tmp_path: Path, json_parser: StreamingJSONParser) -> None:
        """Test parsing empty JSON array"""
        json_file = tmp_path / "empty_array.json"
        json_file.write_text("[]")

        chunks = list(json_parser.read_chunks(json_file, json_path="item"))
        total_items = sum(len(chunk.items) for chunk in chunks)
        assert total_items == 0

    def test_parse_array_with_different_batch_sizes(self, large_json_array_file: Path) -> None:
        """Test parsing with different batch sizes"""
        for chunk_size in [50, 100, 500]:
            parser = StreamingJSONParser(chunk_size=chunk_size)
            chunks = list(parser.read_chunks(large_json_array_file, json_path="item"))

            # Verify chunk sizes
            for chunk in chunks[:-1]:  # All but last
                assert len(chunk.items) <= chunk_size

            # Verify total items
            total_items = sum(len(chunk.items) for chunk in chunks)
            assert total_items == 5000

    def test_unicode_handling(self, tmp_path: Path, json_parser: StreamingJSONParser) -> None:
        """Test handling Unicode characters"""
        json_file = tmp_path / "unicode.json"
        # Create array of items with unicode fields
        data = [
            {"x": 1.0, "y": 2.0, "z": 3.0, "name": "테스트", "description": "한글 설명"},
        ]
        json_file.write_text(json.dumps(data, ensure_ascii=False))

        # Parse successfully with unicode data
        result = json_parser.parse(json_file, json_path="item")
        assert result is not None
        assert len(result.mesh.vertices) == 1


class TestParserPerformance:
    """Performance comparison tests"""

    @pytest.fixture
    def very_large_csv_file(self, tmp_path: Path) -> Path:
        """Create very large CSV file (50,000 rows)"""
        csv_file = tmp_path / "very_large.csv"
        with open(csv_file, "w") as f:
            f.write("x,y,z,temperature,pressure\n")
            for i in range(50000):
                f.write(f"{i*0.1},{i*0.2},{i*0.3},{300+i%500},{101325+i%1000}\n")
        return csv_file

    def test_csv_streaming_performance(self, very_large_csv_file: Path) -> None:
        """Test CSV streaming performance"""
        import time

        parser = StreamingCSVParser(chunk_rows=1000)

        start_time = time.time()
        total_rows = 0
        for chunk in parser.read_chunks(very_large_csv_file):
            total_rows += len(chunk.rows)
        elapsed = time.time() - start_time

        assert total_rows == 50000
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

        print(
            f"\n  CSV Streaming: {total_rows} rows in {elapsed:.2f}s ({total_rows/elapsed:.0f} rows/s)"
        )

    def test_chunk_size_impact(self, very_large_csv_file: Path) -> None:
        """Test impact of different chunk sizes on performance"""
        import time

        results = {}
        for chunk_rows in [100, 500, 1000, 5000]:
            parser = StreamingCSVParser(chunk_rows=chunk_rows)

            start_time = time.time()
            total_rows = sum(len(chunk.rows) for chunk in parser.read_chunks(very_large_csv_file))
            elapsed = time.time() - start_time

            results[chunk_rows] = {"elapsed": elapsed, "rows": total_rows}

        print("\n  Chunk Size Performance:")
        for size, data in results.items():
            print(
                f"    {size:5d}: {data['elapsed']:.3f}s ({data['rows']/data['elapsed']:.0f} rows/s)"
            )

        # All should process same number of rows
        assert all(r["rows"] == 50000 for r in results.values())


class TestParserEdgeCases:
    """Test edge cases and error handling"""

    def test_csv_with_quoted_fields(self, tmp_path: Path) -> None:
        """Test CSV with quoted fields containing commas"""
        parser = StreamingCSVParser()
        csv_file = tmp_path / "quoted.csv"
        content = "x,y,name,description,value\n"
        content += '1,2,"John Doe","A description, with commas",100\n'
        content += '3,4,"Jane Smith","Another, description",200\n'
        csv_file.write_text(content)

        result = parser.parse(csv_file)
        assert result is not None
        assert len(result.mesh.vertices) == 2

    def test_csv_with_different_delimiters(self, tmp_path: Path) -> None:
        """Test CSV with different delimiters"""
        # Tab-separated
        csv_file = tmp_path / "tab_separated.csv"
        content = "x\ty\tz\n"
        content += "1\t2\t3\n"
        csv_file.write_text(content)

        parser = StreamingCSVParser()
        result = parser.parse(csv_file, delimiter="\t")
        assert result is not None
        assert len(result.mesh.vertices) == 1

    def test_json_with_large_nested_arrays(self, tmp_path: Path) -> None:
        """Test JSON with large nested arrays"""
        parser = StreamingJSONParser()
        json_file = tmp_path / "large_nested.json"
        # Create array with x, y, z coordinates
        data = [{"x": i, "y": i * 2, "z": i * 3, "values": list(range(100))} for i in range(100)]
        json_file.write_text(json.dumps(data))

        result = parser.parse(json_file, json_path="item")
        assert result is not None
        assert len(result.mesh.vertices) == 100
