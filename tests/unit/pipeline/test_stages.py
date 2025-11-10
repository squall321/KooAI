"""파이프라인 스테이지 테스트"""

from typing import Any
import pytest
import tempfile
from pathlib import Path

from src.core.pipeline import PipelineContext
from src.core.pipeline.stages.extraction import (
    FileExtractionStage,
    JSONExtractionStage,
)
from src.core.pipeline.stages.transformation import (
    FilterStage,
    MapStage,
    AggregateStage,
    ValidationStage,
)
from src.core.pipeline.stages.loading import (
    FileLoadingStage,
    JSONLoadingStage,
)


class TestExtractionStages:
    """Extraction 단계 테스트"""

    @pytest.mark.asyncio
    async def test_file_extraction(self) -> None:
        """파일 추출 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            stage = FileExtractionStage(file_path=temp_path)
            context = PipelineContext()

            content = await stage.process(None, context)

            assert content == "Test content"
            assert str(temp_path) in str(context.metadata[f"{stage.name}_file_path"])

        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_json_extraction_from_string(self) -> None:
        """JSON 문자열 추출 테스트"""
        json_str = '{"key": "value", "number": 42}'

        stage = JSONExtractionStage()
        context = PipelineContext()

        data = await stage.process(json_str, context)

        assert data["key"] == "value"
        assert data["number"] == 42

    @pytest.mark.asyncio
    async def test_json_extraction_with_path(self) -> None:
        """JSON 경로 추출 테스트"""
        json_str = '{"data": {"results": [1, 2, 3]}}'

        stage = JSONExtractionStage(extract_path="data.results")
        context = PipelineContext()

        results = await stage.process(json_str, context)

        assert results == [1, 2, 3]


class TestTransformationStages:
    """Transformation 단계 테스트"""

    @pytest.mark.asyncio
    async def test_filter_stage_list(self) -> None:
        """필터 단계 (리스트) 테스트"""
        data = [1, 2, 3, 4, 5, 6]

        stage = FilterStage(lambda x: x % 2 == 0)  # 짝수만
        context = PipelineContext()

        filtered = await stage.process(data, context)

        assert filtered == [2, 4, 6]
        assert context.metadata[f"{stage.name}_filtered_count"] == 3

    @pytest.mark.asyncio
    async def test_filter_stage_single(self) -> None:
        """필터 단계 (단일) 테스트"""
        stage = FilterStage(lambda x: x > 5)
        context = PipelineContext()

        # 통과하는 경우
        result = await stage.process(10, context)
        assert result == 10

        # 필터링되는 경우
        with pytest.raises(ValueError):
            await stage.process(3, context)

    @pytest.mark.asyncio
    async def test_map_stage(self) -> None:
        """매핑 단계 테스트"""
        data = [1, 2, 3]

        stage = MapStage(lambda x: x * 2)
        context = PipelineContext()

        mapped = await stage.process(data, context)

        assert mapped == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_map_stage_single(self) -> None:
        """매핑 단계 (단일) 테스트"""
        stage = MapStage(lambda x: x.upper())
        context = PipelineContext()

        result = await stage.process("hello", context)

        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_aggregate_stage(self) -> None:
        """집계 단계 테스트"""
        data = [1, 2, 3, 4, 5]

        stage = AggregateStage(sum)
        context = PipelineContext()

        total = await stage.process(data, context)

        assert total == 15
        assert context.metadata[f"{stage.name}_input_count"] == 5

    @pytest.mark.asyncio
    async def test_validation_stage_pass(self) -> None:
        """검증 단계 (통과) 테스트"""
        stage = ValidationStage(lambda x: x > 0, error_message="Must be positive")
        context = PipelineContext()

        result = await stage.process(5, context)

        assert result == 5

    @pytest.mark.asyncio
    async def test_validation_stage_fail(self) -> None:
        """검증 단계 (실패) 테스트"""
        stage = ValidationStage(lambda x: x > 0, error_message="Must be positive")
        context = PipelineContext()

        with pytest.raises(ValueError, match="Must be positive"):
            await stage.process(-5, context)


class TestLoadingStages:
    """Loading 단계 테스트"""

    @pytest.mark.asyncio
    async def test_file_loading(self) -> None:
        """파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "output.txt"

            stage = FileLoadingStage(file_path)
            context = PipelineContext()

            data = "Test output content"
            result = await stage.process(data, context)

            assert result == data  # 데이터 통과
            assert file_path.exists()
            assert file_path.read_text() == data

    @pytest.mark.asyncio
    async def test_json_loading(self) -> None:
        """JSON 저장 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "output.json"

            stage = JSONLoadingStage(file_path)
            context = PipelineContext()

            data = {"key": "value", "numbers": [1, 2, 3]}
            result = await stage.process(data, context)

            assert result == data
            assert file_path.exists()

            # 파일 내용 확인
            import json

            with open(file_path) as f:
                loaded = json.load(f)

            assert loaded == data
