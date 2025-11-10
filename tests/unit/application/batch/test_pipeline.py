"""
Tests for Pipeline
"""

from typing import Any
import pytest
from src.application.batch.pipeline import (
    Pipeline,
    PipelineStage,
    ParseStage,
    AnalyzeStage,
    ExportStage,
)


class TestStage(PipelineStage):
    """Test pipeline stage"""

    def __init__(self, name: str, operation: str = "append"):
        super().__init__(name)
        self.operation = operation

    def process(self, data: Any) -> Any:
        """Add stage name to data"""
        if isinstance(data, list):
            return data + [self.name]
        else:
            return f"{data}_{self.name}"


class MultiplyStage(PipelineStage):
    """Stage that multiplies numbers"""

    def __init__(self, multiplier: int):
        super().__init__(f"multiply_by_{multiplier}")
        self.multiplier = multiplier

    def process(self, data: Any) -> Any:
        """Multiply data"""
        if isinstance(data, (int, float)):
            return data * self.multiplier
        return data


class ErrorStage(PipelineStage):
    """Stage that raises an error"""

    def __init__(self) -> None:
        super().__init__("error_stage")

    def process(self, data: Any) -> Any:
        """Raise error"""
        raise ValueError("Test error from stage")


def test_pipeline_creation() -> None:
    """Test pipeline creation"""
    pipeline = Pipeline(name="test_pipeline")

    assert pipeline.name == "test_pipeline"
    assert len(pipeline.stages) == 0


def test_pipeline_add_stage() -> None:
    """Test adding stages to pipeline"""
    pipeline = Pipeline()

    stage1 = TestStage("stage1")
    stage2 = TestStage("stage2")

    pipeline.add_stage(stage1).add_stage(stage2)

    assert len(pipeline.stages) == 2
    assert pipeline.stages[0].name == "stage1"
    assert pipeline.stages[1].name == "stage2"


def test_pipeline_process() -> None:
    """Test pipeline processing"""
    pipeline = Pipeline()

    pipeline.add_stage(TestStage("stage1"))
    pipeline.add_stage(TestStage("stage2"))
    pipeline.add_stage(TestStage("stage3"))

    result = pipeline.process([])

    assert result == ["stage1", "stage2", "stage3"]


def test_pipeline_callable() -> None:
    """Test pipeline is callable"""
    pipeline = Pipeline()
    pipeline.add_stage(TestStage("stage1"))

    result = pipeline([])

    assert result == ["stage1"]


def test_pipeline_data_transformation() -> None:
    """Test data transformation through pipeline"""
    pipeline = Pipeline()

    pipeline.add_stage(MultiplyStage(2))
    pipeline.add_stage(MultiplyStage(3))
    pipeline.add_stage(MultiplyStage(4))

    result = pipeline.process(1)

    assert result == 24  # 1 * 2 * 3 * 4


def test_pipeline_error_handling() -> None:
    """Test pipeline error handling"""
    pipeline = Pipeline()

    pipeline.add_stage(TestStage("stage1"))
    pipeline.add_stage(ErrorStage())
    pipeline.add_stage(TestStage("stage3"))  # Should not be reached

    with pytest.raises(ValueError, match="Test error from stage"):
        pipeline.process([])


def test_parse_stage() -> None:
    """Test ParseStage"""

    def mock_parser(file_path: Any) -> Any:
        return {"data": f"parsed_{file_path}"}

    stage = ParseStage(mock_parser)
    result = stage.process("/test/file.txt")

    assert result["data"] == "parsed_/test/file.txt"


def test_analyze_stage() -> None:
    """Test AnalyzeStage"""

    def mock_analyzer(sim_data: Any, field: Any) -> Any:
        return {"field": field, "mean": 42.0}

    stage = AnalyzeStage(mock_analyzer, "temperature")

    sim_data = {"fields": {"temperature": [1, 2, 3]}}
    result = stage.process(sim_data)

    # AnalyzeStage should return the simulation data with analysis results added
    assert "analysis_results" in result
    assert "temperature" in result["analysis_results"]
    assert result["analysis_results"]["temperature"]["field"] == "temperature"
    assert result["analysis_results"]["temperature"]["mean"] == 42.0


def test_export_stage() -> None:
    """Test ExportStage"""
    export_calls = []

    def mock_exporter(data: Any, path: Any) -> Any:
        export_calls.append((data, path))
        return data

    stage = ExportStage(mock_exporter, "/output/result.json")

    data = {"test": "data"}
    result = stage.process(data)

    assert len(export_calls) == 1
    assert export_calls[0][0] == data
    assert export_calls[0][1] == "/output/result.json"


def test_pipeline_complex_workflow() -> None:
    """Test complex pipeline workflow"""
    # Simulate: parse -> multiply -> transform -> export

    parsed_data = []
    exported_data = []

    def parse_func(path: Any) -> Any:
        parsed_data.append(path)
        return 10

    def export_func(data: Any, path: Any) -> Any:
        exported_data.append((data, path))
        return data

    pipeline = Pipeline(name="complex_workflow")
    pipeline.add_stage(ParseStage(parse_func))
    pipeline.add_stage(MultiplyStage(5))
    pipeline.add_stage(ExportStage(export_func, "/output/result.txt"))

    result = pipeline.process("/input/file.txt")

    # Check each stage worked
    assert len(parsed_data) == 1
    assert result == 50  # 10 * 5
    assert len(exported_data) == 1
    assert exported_data[0][0] == 50


def test_pipeline_empty() -> None:
    """Test empty pipeline"""
    pipeline = Pipeline()

    result = pipeline.process("test_data")

    # Should return data unchanged
    assert result == "test_data"


def test_stage_callable() -> None:
    """Test that stages are callable"""
    stage = TestStage("test")

    result = stage(["initial"])

    assert result == ["initial", "test"]


def test_pipeline_method_chaining() -> None:
    """Test method chaining for adding stages"""
    pipeline = Pipeline()

    # Should be able to chain add_stage calls
    result = (
        pipeline.add_stage(TestStage("s1")).add_stage(TestStage("s2")).add_stage(TestStage("s3"))
    )

    assert result is pipeline
    assert len(pipeline.stages) == 3


def test_pipeline_with_different_data_types() -> None:
    """Test pipeline with different data types"""

    class StringAppendStage(PipelineStage):
        def __init__(self, suffix: Any) -> None:
            super().__init__(f"append_{suffix}")
            self.suffix = suffix

        def process(self, data: Any) -> Any:
            return f"{data}_{self.suffix}"

    pipeline = Pipeline()
    pipeline.add_stage(StringAppendStage("foo"))
    pipeline.add_stage(StringAppendStage("bar"))
    pipeline.add_stage(StringAppendStage("baz"))

    result = pipeline.process("start")

    assert result == "start_foo_bar_baz"


def test_pipeline_state_isolation() -> None:
    """Test that pipeline stages don't share state between calls"""

    class CounterStage(PipelineStage):
        def __init__(self) -> None:
            super().__init__("counter")
            self.count = 0

        def process(self, data: Any) -> Any:
            self.count += 1
            return self.count

    stage = CounterStage()
    pipeline = Pipeline()
    pipeline.add_stage(stage)

    result1 = pipeline.process(None)
    result2 = pipeline.process(None)
    result3 = pipeline.process(None)

    # Count should increase across calls
    assert result1 == 1
    assert result2 == 2
    assert result3 == 3
