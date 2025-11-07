"""
Integration tests for streaming parsers

Tests the streaming CSV and JSON parsers with real files.
"""

import pytest
import tempfile
import json
from pathlib import Path
from io import StringIO

from src.core.simulation.parsers.streaming_csv_parser import StreamingCSVParser
from src.core.simulation.parsers.streaming_json_parser import StreamingJSONParser
from src.core.exceptions import ParsingError


class TestStreamingCSVParser:
    """Test streaming CSV parser with real files"""

    @pytest.fixture
    def csv_parser(self):
        """Create CSV parser instance"""
        return StreamingCSVParser(chunk_size=100)

    @pytest.fixture
    def small_csv_file(self, tmp_path):
        """Create small CSV file (< 1 chunk)"""
        csv_file = tmp_path / "small.csv"
        content = "x,y,z,temperature\n"
        for i in range(50):
            content += f"{i},{i*2},{i*3},{300+i}\n"
        csv_file.write_text(content)
        return csv_file

    @pytest.fixture
    def large_csv_file(self, tmp_path):
        """Create large CSV file (multiple chunks)"""
        csv_file = tmp_path / "large.csv"
        content = "x,y,z,temperature,pressure\n"
        # Create 10,000 rows
        for i in range(10000):
            content += f"{i*0.1},{i*0.2},{i*0.3},{300+i%500},{101325+i%1000}\n"
        csv_file.write_text(content)
        return csv_file

    @pytest.fixture
    def malformed_csv_file(self, tmp_path):
        """Create CSV with inconsistent columns"""
        csv_file = tmp_path / "malformed.csv"
        content = "x,y,z\n"
        content += "1,2,3\n"
        content += "4,5\n"  # Missing column
        content += "6,7,8,9\n"  # Extra column
        csv_file.write_text(content)
        return csv_file

    def test_parse_small_file(self, csv_parser, small_csv_file):
        """Test parsing small CSV file"""
        chunks = list(csv_parser.parse(small_csv_file))

        assert len(chunks) > 0

        # Verify first chunk
        first_chunk = chunks[0]
        assert "x" in first_chunk.columns
        assert "y" in first_chunk.columns
        assert "temperature" in first_chunk.columns

        # Verify data
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 50

    def test_parse_large_file_chunks(self, csv_parser, large_csv_file):
        """Test parsing large file yields multiple chunks"""
        chunks = []
        for chunk in csv_parser.parse(large_csv_file):
            chunks.append(chunk)
            # Verify chunk size constraint
            assert len(chunk) <= 100

        # Should have multiple chunks
        assert len(chunks) > 1

        # Verify total rows
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 10000

    def test_memory_efficiency(self, csv_parser, large_csv_file):
        """Test that streaming doesn't load entire file at once"""
        import sys

        # Process one chunk at a time
        max_chunk_memory = 0
        for chunk in csv_parser.parse(large_csv_file):
            chunk_memory = sys.getsizeof(chunk)
            max_chunk_memory = max(max_chunk_memory, chunk_memory)

        # Each chunk should be much smaller than full file
        file_size = large_csv_file.stat().st_size
        # Chunk memory should be < 10% of file size (rough estimate)
        assert max_chunk_memory < file_size * 0.1

    def test_parse_with_different_chunk_sizes(self, small_csv_file):
        """Test parsing with different chunk sizes"""
        for chunk_size in [10, 50, 100]:
            parser = StreamingCSVParser(chunk_size=chunk_size)
            chunks = list(parser.parse(small_csv_file))

            # Verify all chunks respect size limit
            for chunk in chunks[:-1]:  # All but last
                assert len(chunk) <= chunk_size

            # Verify total rows
            total_rows = sum(len(chunk) for chunk in chunks)
            assert total_rows == 50

    def test_column_detection(self, csv_parser, large_csv_file):
        """Test automatic column detection"""
        chunks = csv_parser.parse(large_csv_file)
        first_chunk = next(chunks)

        assert "x" in first_chunk.columns
        assert "y" in first_chunk.columns
        assert "z" in first_chunk.columns
        assert "temperature" in first_chunk.columns
        assert "pressure" in first_chunk.columns

    def test_numeric_conversion(self, csv_parser, small_csv_file):
        """Test automatic numeric type conversion"""
        chunks = csv_parser.parse(small_csv_file)
        first_chunk = next(chunks)

        # All columns should be numeric
        for col in first_chunk.columns:
            assert first_chunk[col].dtype.kind in ['i', 'f']  # int or float

    def test_parse_with_missing_values(self, tmp_path, csv_parser):
        """Test parsing CSV with missing values"""
        csv_file = tmp_path / "missing.csv"
        content = "x,y,z\n"
        content += "1,2,3\n"
        content += "4,,6\n"  # Missing value
        content += "7,8,\n"  # Missing value
        csv_file.write_text(content)

        chunks = list(csv_parser.parse(csv_file))
        assert len(chunks) > 0

        # Missing values should be handled (NaN or similar)
        first_chunk = chunks[0]
        assert len(first_chunk) == 3

    def test_parse_empty_file(self, tmp_path, csv_parser):
        """Test parsing empty CSV file"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        with pytest.raises(ParsingError):
            list(csv_parser.parse(csv_file))

    def test_parse_header_only(self, tmp_path, csv_parser):
        """Test parsing CSV with only header"""
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("x,y,z\n")

        chunks = list(csv_parser.parse(csv_file))
        # Should return empty chunks or no chunks
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 0

    def test_parse_nonexistent_file(self, csv_parser):
        """Test parsing non-existent file"""
        with pytest.raises((FileNotFoundError, ParsingError)):
            list(csv_parser.parse(Path("/nonexistent/file.csv")))


class TestStreamingJSONParser:
    """Test streaming JSON parser with real files"""

    @pytest.fixture
    def json_parser(self):
        """Create JSON parser instance"""
        return StreamingJSONParser(batch_size=100)

    @pytest.fixture
    def small_json_file(self, tmp_path):
        """Create small JSON file"""
        json_file = tmp_path / "small.json"
        data = {
            "metadata": {"name": "test", "version": "1.0"},
            "points": [
                {"x": i, "y": i*2, "z": i*3, "temperature": 300+i}
                for i in range(50)
            ]
        }
        json_file.write_text(json.dumps(data))
        return json_file

    @pytest.fixture
    def large_json_array_file(self, tmp_path):
        """Create large JSON array file"""
        json_file = tmp_path / "large_array.json"
        # Create array of objects
        data = [
            {
                "id": i,
                "x": i*0.1,
                "y": i*0.2,
                "z": i*0.3,
                "temperature": 300 + (i % 500),
                "pressure": 101325 + (i % 1000)
            }
            for i in range(5000)
        ]
        json_file.write_text(json.dumps(data))
        return json_file

    @pytest.fixture
    def nested_json_file(self, tmp_path):
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
                                "temperature": [300+j for j in range(100)],
                                "pressure": [101325+j for j in range(100)]
                            }
                        }
                        for i in range(10)
                    ]
                }
            }
        }
        json_file.write_text(json.dumps(data))
        return json_file

    def test_parse_small_json(self, json_parser, small_json_file):
        """Test parsing small JSON file"""
        result = json_parser.parse(small_json_file)

        assert "metadata" in result
        assert "points" in result
        assert len(result["points"]) == 50

    def test_parse_array_streaming(self, json_parser, large_json_array_file):
        """Test streaming array parsing"""
        import time

        start_time = time.time()
        items = list(json_parser.parse_array_stream(large_json_array_file))
        elapsed = time.time() - start_time

        assert len(items) == 5000

        # Verify item structure
        first_item = items[0]
        assert "x" in first_item
        assert "y" in first_item
        assert "temperature" in first_item

    def test_memory_efficiency_streaming(self, json_parser, large_json_array_file):
        """Test memory efficiency of streaming"""
        import sys

        max_batch_memory = 0
        batch_count = 0

        for batch in json_parser.parse_array_stream(large_json_array_file):
            batch_memory = sys.getsizeof(batch)
            max_batch_memory = max(max_batch_memory, batch_memory)
            batch_count += 1

        # Should have multiple batches
        assert batch_count > 1

        # Each batch should be smaller than full file
        file_size = large_json_array_file.stat().st_size
        assert max_batch_memory < file_size * 0.5

    def test_parse_nested_structure(self, json_parser, nested_json_file):
        """Test parsing nested JSON structure"""
        result = json_parser.parse(nested_json_file)

        assert "simulation" in result
        assert "metadata" in result["simulation"]
        assert "results" in result["simulation"]
        assert "timesteps" in result["simulation"]["results"]
        assert len(result["simulation"]["results"]["timesteps"]) == 10

    def test_parse_with_path_extraction(self, json_parser, nested_json_file):
        """Test extracting specific JSON path"""
        # Parse and extract specific path
        result = json_parser.parse(nested_json_file)
        timesteps = result["simulation"]["results"]["timesteps"]

        assert len(timesteps) == 10
        assert "time" in timesteps[0]
        assert "fields" in timesteps[0]

    def test_parse_invalid_json(self, tmp_path, json_parser):
        """Test parsing invalid JSON"""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json content")

        with pytest.raises((json.JSONDecodeError, ParsingError)):
            json_parser.parse(json_file)

    def test_parse_empty_json(self, tmp_path, json_parser):
        """Test parsing empty JSON file"""
        json_file = tmp_path / "empty.json"
        json_file.write_text("")

        with pytest.raises((json.JSONDecodeError, ParsingError)):
            json_parser.parse(json_file)

    def test_parse_empty_array(self, tmp_path, json_parser):
        """Test parsing empty JSON array"""
        json_file = tmp_path / "empty_array.json"
        json_file.write_text("[]")

        items = list(json_parser.parse_array_stream(json_file))
        assert len(items) == 0

    def test_parse_array_with_different_batch_sizes(self, large_json_array_file):
        """Test parsing with different batch sizes"""
        for batch_size in [50, 100, 500]:
            parser = StreamingJSONParser(batch_size=batch_size)
            batches = list(parser.parse_array_stream(large_json_array_file))

            # Verify batch sizes
            for batch in batches[:-1]:  # All but last
                assert len(batch) <= batch_size

            # Verify total items
            total_items = sum(len(batch) for batch in batches)
            assert total_items == 5000

    def test_unicode_handling(self, tmp_path, json_parser):
        """Test handling Unicode characters"""
        json_file = tmp_path / "unicode.json"
        data = {
            "name": "테스트",
            "description": "한글 설명",
            "values": [1, 2, 3]
        }
        json_file.write_text(json.dumps(data, ensure_ascii=False))

        result = json_parser.parse(json_file)
        assert result["name"] == "테스트"
        assert result["description"] == "한글 설명"


class TestParserPerformance:
    """Performance comparison tests"""

    @pytest.fixture
    def very_large_csv_file(self, tmp_path):
        """Create very large CSV file (50,000 rows)"""
        csv_file = tmp_path / "very_large.csv"
        with open(csv_file, 'w') as f:
            f.write("x,y,z,temperature,pressure\n")
            for i in range(50000):
                f.write(f"{i*0.1},{i*0.2},{i*0.3},{300+i%500},{101325+i%1000}\n")
        return csv_file

    def test_csv_streaming_performance(self, very_large_csv_file):
        """Test CSV streaming performance"""
        import time

        parser = StreamingCSVParser(chunk_size=1000)

        start_time = time.time()
        total_rows = 0
        for chunk in parser.parse(very_large_csv_file):
            total_rows += len(chunk)
        elapsed = time.time() - start_time

        assert total_rows == 50000
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

        print(f"\n  CSV Streaming: {total_rows} rows in {elapsed:.2f}s ({total_rows/elapsed:.0f} rows/s)")

    def test_chunk_size_impact(self, very_large_csv_file):
        """Test impact of different chunk sizes on performance"""
        import time

        results = {}
        for chunk_size in [100, 500, 1000, 5000]:
            parser = StreamingCSVParser(chunk_size=chunk_size)

            start_time = time.time()
            total_rows = sum(len(chunk) for chunk in parser.parse(very_large_csv_file))
            elapsed = time.time() - start_time

            results[chunk_size] = {
                'elapsed': elapsed,
                'rows': total_rows
            }

        print("\n  Chunk Size Performance:")
        for size, data in results.items():
            print(f"    {size:5d}: {data['elapsed']:.3f}s ({data['rows']/data['elapsed']:.0f} rows/s)")

        # All should process same number of rows
        assert all(r['rows'] == 50000 for r in results.values())


class TestParserEdgeCases:
    """Test edge cases and error handling"""

    def test_csv_with_quoted_fields(self, tmp_path):
        """Test CSV with quoted fields containing commas"""
        parser = StreamingCSVParser()
        csv_file = tmp_path / "quoted.csv"
        content = 'name,description,value\n'
        content += '"John Doe","A description, with commas",100\n'
        content += '"Jane Smith","Another, description",200\n'
        csv_file.write_text(content)

        chunks = list(parser.parse(csv_file))
        assert len(chunks) > 0

    def test_csv_with_different_delimiters(self, tmp_path):
        """Test CSV with different delimiters"""
        # Tab-separated
        csv_file = tmp_path / "tab_separated.csv"
        content = "x\ty\tz\n"
        content += "1\t2\t3\n"
        csv_file.write_text(content)

        parser = StreamingCSVParser()
        chunks = list(parser.parse(csv_file))
        assert len(chunks) > 0

    def test_json_with_large_nested_arrays(self, tmp_path):
        """Test JSON with large nested arrays"""
        parser = StreamingJSONParser()
        json_file = tmp_path / "large_nested.json"
        data = {
            "results": [
                {"values": list(range(1000))}
                for _ in range(100)
            ]
        }
        json_file.write_text(json.dumps(data))

        result = parser.parse(json_file)
        assert "results" in result
        assert len(result["results"]) == 100
