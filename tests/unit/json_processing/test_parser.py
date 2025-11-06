"""
JSON 파서 테스트
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.core.json_processing.parser import (
    JSONParser,
    HierarchicalExtractor,
    ChunkedJSONWriter,
)
from src.core.json_processing.schema import SimulationMetadata


class TestJSONParser:
    """JSONParser 테스트"""

    def test_parse_string(self):
        """JSON 문자열 파싱 테스트"""
        parser = JSONParser(validate=False)
        json_str = '{"name": "test", "value": 123}'

        result = parser.parse_string(json_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_file(self, tmp_path):
        """JSON 파일 파싱 테스트"""
        # 임시 JSON 파일 생성
        json_file = tmp_path / "test.json"
        data = {"name": "CFD Sim", "solver": "OpenFOAM", "version": "8.0"}

        with open(json_file, "w") as f:
            json.dump(data, f)

        # 파싱
        parser = JSONParser(validate=False)
        result = parser.parse_file(json_file)

        assert result["name"] == "CFD Sim"
        assert result["solver"] == "OpenFOAM"

    def test_parse_with_validation(self, tmp_path):
        """스키마 검증과 함께 파싱"""
        json_file = tmp_path / "metadata.json"
        data = {
            "name": "Test Simulation",
            "solver": "ANSYS",
            "solver_version": "2023",
        }

        with open(json_file, "w") as f:
            json.dump(data, f)

        parser = JSONParser(validate=True)
        result = parser.parse_file(json_file, schema_name="simulation_metadata")

        assert isinstance(result, SimulationMetadata)
        assert result.name == "Test Simulation"

    def test_parse_invalid_file(self):
        """존재하지 않는 파일 파싱 시 에러"""
        parser = JSONParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.json")

    def test_parse_invalid_json(self):
        """잘못된 JSON 파싱 시 에러"""
        parser = JSONParser()

        with pytest.raises(json.JSONDecodeError):
            parser.parse_string("{invalid json}")


class TestHierarchicalExtractor:
    """HierarchicalExtractor 테스트"""

    def test_extract_by_path(self):
        """경로로 데이터 추출 테스트"""
        data = {"metadata": {"name": "CFD", "version": "1.0"}, "solver": "OpenFOAM"}

        result = HierarchicalExtractor.extract_by_path(data, "metadata.name")
        assert result == "CFD"

        result = HierarchicalExtractor.extract_by_path(data, "solver")
        assert result == "OpenFOAM"

    def test_extract_nested_path(self):
        """깊이 중첩된 경로 추출"""
        data = {"a": {"b": {"c": {"d": 42}}}}

        result = HierarchicalExtractor.extract_by_path(data, "a.b.c.d")
        assert result == 42

    def test_extract_nonexistent_path(self):
        """존재하지 않는 경로 추출 (None 반환)"""
        data = {"a": {"b": 1}}

        result = HierarchicalExtractor.extract_by_path(data, "a.c")
        assert result is None

    def test_extract_array_index(self):
        """배열 인덱스 추출"""
        data = {"items": [10, 20, 30, 40]}

        result = HierarchicalExtractor.extract_by_path(data, "items.0")
        assert result == 10

        result = HierarchicalExtractor.extract_by_path(data, "items.2")
        assert result == 30

    def test_extract_multiple(self):
        """여러 경로 한 번에 추출"""
        data = {
            "metadata": {"name": "Sim1", "version": "1.0"},
            "mesh": {"num_vertices": 1000},
        }

        paths = ["metadata.name", "metadata.version", "mesh.num_vertices"]
        result = HierarchicalExtractor.extract_multiple(data, paths)

        assert result["metadata.name"] == "Sim1"
        assert result["metadata.version"] == "1.0"
        assert result["mesh.num_vertices"] == 1000

    def test_set_by_path(self):
        """경로로 값 설정 테스트"""
        data = {"metadata": {"name": "Old"}}

        HierarchicalExtractor.set_by_path(data, "metadata.name", "New")
        assert data["metadata"]["name"] == "New"

    def test_set_create_path(self):
        """존재하지 않는 경로 생성 및 설정"""
        data = {}

        HierarchicalExtractor.set_by_path(data, "a.b.c", 123)
        assert data["a"]["b"]["c"] == 123

    def test_flatten(self):
        """딕셔너리 평탄화 테스트"""
        data = {"a": {"b": {"c": 1}}, "d": 2, "e": {"f": 3}}

        flat = HierarchicalExtractor.flatten(data)

        assert flat["a.b.c"] == 1
        assert flat["d"] == 2
        assert flat["e.f"] == 3

    def test_unflatten(self):
        """평탄화 역변환 테스트"""
        flat = {"a.b.c": 1, "d": 2, "e.f": 3}

        nested = HierarchicalExtractor.unflatten(flat)

        assert nested["a"]["b"]["c"] == 1
        assert nested["d"] == 2
        assert nested["e"]["f"] == 3

    def test_flatten_unflatten_roundtrip(self):
        """평탄화 → 역변환 왕복 테스트"""
        original = {"metadata": {"name": "Test", "version": "1.0"}, "value": 42}

        flat = HierarchicalExtractor.flatten(original)
        restored = HierarchicalExtractor.unflatten(flat)

        assert restored == original


class TestChunkedJSONWriter:
    """ChunkedJSONWriter 테스트"""

    def test_write_simple_object(self, tmp_path):
        """단순 객체 작성 테스트"""
        output_file = tmp_path / "output.json"

        with ChunkedJSONWriter(output_file) as writer:
            writer.start_object()
            writer.write_field("name", "Test")
            writer.write_field("value", 123)
            writer.end_object()

        # 파일 읽어서 확인
        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["name"] == "Test"
        assert data["value"] == 123

    def test_write_array(self, tmp_path):
        """배열 작성 테스트"""
        output_file = tmp_path / "array.json"

        with ChunkedJSONWriter(output_file) as writer:
            writer.start_object()
            writer.start_array("items")
            writer.write_item(10)
            writer.write_item(20)
            writer.write_item(30)
            writer.end_array()
            writer.end_object()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["items"] == [10, 20, 30]

    def test_write_complex_structure(self, tmp_path):
        """복잡한 구조 작성 테스트"""
        output_file = tmp_path / "complex.json"

        with ChunkedJSONWriter(output_file) as writer:
            writer.start_object()

            writer.write_field("metadata", {"name": "CFD", "version": "1.0"})

            writer.start_array("time_steps")
            writer.write_item({"step": 0, "time": 0.0})
            writer.write_item({"step": 1, "time": 0.01})
            writer.end_array()

            writer.end_object()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["metadata"]["name"] == "CFD"
        assert len(data["time_steps"]) == 2
        assert data["time_steps"][0]["step"] == 0


# 스트리밍 파서 테스트는 ijson이 설치되어 있어야 하므로 선택적으로 실행
pytest_plugins = []

try:
    import ijson

    IJSON_AVAILABLE = True
except ImportError:
    IJSON_AVAILABLE = False


@pytest.mark.skipif(not IJSON_AVAILABLE, reason="ijson not installed")
class TestStreamingJSONParser:
    """StreamingJSONParser 테스트 (ijson 필요)"""

    def test_stream_array_items(self, tmp_path):
        """배열 아이템 스트리밍 테스트"""
        from src.core.json_processing.parser import StreamingJSONParser

        json_file = tmp_path / "array.json"
        data = {"items": [1, 2, 3, 4, 5]}

        with open(json_file, "w") as f:
            json.dump(data, f)

        parser = StreamingJSONParser()
        items = list(parser.stream_array_items(json_file, "items.item"))

        assert items == [1, 2, 3, 4, 5]

    def test_extract_field(self, tmp_path):
        """필드 추출 테스트"""
        from src.core.json_processing.parser import StreamingJSONParser

        json_file = tmp_path / "data.json"
        data = {"metadata": {"name": "CFD Sim", "version": "1.0"}}

        with open(json_file, "w") as f:
            json.dump(data, f)

        parser = StreamingJSONParser()
        name = parser.extract_field(json_file, "metadata.name")

        assert name == "CFD Sim"

    def test_stream_large_array_batches(self, tmp_path):
        """대용량 배열 배치 스트리밍 테스트"""
        from src.core.json_processing.parser import StreamingJSONParser

        json_file = tmp_path / "large.json"
        data = {"values": list(range(100))}

        with open(json_file, "w") as f:
            json.dump(data, f)

        parser = StreamingJSONParser()
        batches = list(parser.stream_large_array(json_file, "values.item", batch_size=25))

        assert len(batches) == 4
        assert len(batches[0]) == 25
        assert batches[0][0] == 0
        assert batches[3][-1] == 99
