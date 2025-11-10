"""파이프라인 기본 기능 테스트"""

import pytest
from typing import Any

from src.core.pipeline import (
    Pipeline,
    ProcessingStage,
    PipelineContext,
    StageStatus,
    StageResult,
)


class DoubleStage(ProcessingStage):
    """테스트용 단계: 값을 2배로"""

    async def process(self, data: Any, context: PipelineContext) -> Any:
        return data * 2


class AddStage(ProcessingStage):
    """테스트용 단계: 값을 더함"""

    def __init__(self, value: int, name: str = "Add"):
        super().__init__(name)
        self.value = value

    async def process(self, data: Any, context: PipelineContext) -> Any:
        return data + self.value


class FailingStage(ProcessingStage):
    """테스트용 단계: 항상 실패"""

    async def process(self, data: Any, context: PipelineContext) -> Any:
        raise ValueError("Intentional failure")


class TestPipeline:
    """Pipeline 테스트"""

    @pytest.mark.asyncio
    async def test_empty_pipeline(self) -> None:
        """빈 파이프라인 테스트"""
        pipeline = Pipeline()

        result = await pipeline.execute(42)

        assert result.success
        assert result.final_data == 42
        assert len(result.get_stage_results()) == 0

    @pytest.mark.asyncio
    async def test_single_stage(self) -> None:
        """단일 단계 파이프라인 테스트"""
        pipeline = Pipeline()
        pipeline.add_stage(DoubleStage())

        result = await pipeline.execute(5)

        assert result.success
        assert result.final_data == 10
        assert len(result.get_stage_results()) == 1

    @pytest.mark.asyncio
    async def test_multiple_stages(self) -> None:
        """다중 단계 파이프라인 테스트"""
        pipeline = Pipeline()
        pipeline.add_stage(DoubleStage())
        pipeline.add_stage(AddStage(3))

        result = await pipeline.execute(5)

        # 5 -> 10 -> 13
        assert result.success
        assert result.final_data == 13
        assert len(result.get_stage_results()) == 2

    @pytest.mark.asyncio
    async def test_chaining_add_stage(self) -> None:
        """add_stage 체이닝 테스트"""
        pipeline = (
            Pipeline().add_stage(DoubleStage()).add_stage(AddStage(3)).add_stage(DoubleStage())
        )

        result = await pipeline.execute(5)

        # 5 -> 10 -> 13 -> 26
        assert result.final_data == 26
        assert len(pipeline) == 3

    @pytest.mark.asyncio
    async def test_stage_failure(self) -> None:
        """단계 실패 테스트"""
        pipeline = Pipeline(stop_on_failure=True)
        pipeline.add_stage(DoubleStage())
        pipeline.add_stage(FailingStage())
        pipeline.add_stage(AddStage(3))

        result = await pipeline.execute(5)

        assert not result.success
        assert result.final_data == 10  # FailingStage 이전까지의 데이터
        assert len(result.get_stage_results()) == 2  # 실패 후 중단

        failed_stages = result.get_failed_stages()
        assert len(failed_stages) == 1
        assert failed_stages[0].stage_name == "FailingStage"

    @pytest.mark.asyncio
    async def test_continue_on_failure(self) -> None:
        """실패 시에도 계속 실행 테스트"""
        pipeline = Pipeline(stop_on_failure=False)
        pipeline.add_stage(DoubleStage())
        pipeline.add_stage(FailingStage())
        pipeline.add_stage(AddStage(3))

        result = await pipeline.execute(5)

        assert not result.success
        # 모든 단계 실행됨
        assert len(result.get_stage_results()) == 3

    @pytest.mark.asyncio
    async def test_pipeline_context(self) -> None:
        """파이프라인 컨텍스트 테스트"""
        context = PipelineContext()
        context.metadata["initial_key"] = "initial_value"

        pipeline = Pipeline()
        pipeline.add_stage(DoubleStage())

        result = await pipeline.execute(5, context=context)

        assert result.context.metadata["initial_key"] == "initial_value"
        assert result.context.metadata["pipeline_name"] == "Pipeline"
        assert result.context.pipeline_id == context.pipeline_id

    @pytest.mark.asyncio
    async def test_stage_results(self) -> None:
        """단계 결과 테스트"""
        pipeline = Pipeline()
        pipeline.add_stage(DoubleStage())
        pipeline.add_stage(AddStage(3))

        result = await pipeline.execute(5)

        stages = result.get_stage_results()
        assert len(stages) == 2

        # 첫 번째 단계
        assert stages[0].stage_name == "DoubleStage"
        assert stages[0].status == StageStatus.COMPLETED
        assert stages[0].data == 10
        assert stages[0].is_success()

        # 두 번째 단계
        assert stages[1].stage_name == "Add"
        assert stages[1].data == 13

    @pytest.mark.asyncio
    async def test_stage_duration(self) -> None:
        """단계 실행 시간 측정 테스트"""
        pipeline = Pipeline()
        pipeline.add_stage(DoubleStage())

        result = await pipeline.execute(5)

        stage_result = result.get_stage_results()[0]
        duration = stage_result.get_duration_seconds()

        assert duration is not None
        assert duration >= 0

    @pytest.mark.asyncio
    async def test_pipeline_to_dict(self) -> None:
        """파이프라인 결과 딕셔너리 변환 테스트"""
        pipeline = Pipeline()
        pipeline.add_stage(DoubleStage())

        result = await pipeline.execute(5)

        data = result.to_dict()

        assert "pipeline_id" in data
        assert data["success"] is True
        assert data["stage_count"] == 1
        assert "stages" in data
        assert len(data["stages"]) == 1


class TestPipelineContext:
    """PipelineContext 테스트"""

    def test_create_context(self) -> None:
        """컨텍스트 생성 테스트"""
        context = PipelineContext()

        assert context.pipeline_id is not None
        assert len(context.stage_results) == 0
        assert len(context.metadata) == 0

    def test_add_stage_result(self) -> None:
        """단계 결과 추가 테스트"""
        context = PipelineContext()

        result1 = StageResult("Stage1", StageStatus.COMPLETED, "data1")
        context.add_stage_result(result1)

        assert len(context.stage_results) == 1
        assert context.get_last_result() == result1

    def test_get_stage_result(self) -> None:
        """특정 단계 결과 조회 테스트"""
        context = PipelineContext()

        result1 = StageResult("Stage1", StageStatus.COMPLETED, "data1")
        result2 = StageResult("Stage2", StageStatus.COMPLETED, "data2")

        context.add_stage_result(result1)
        context.add_stage_result(result2)

        found = context.get_stage_result("Stage1")
        assert found == result1

    def test_has_failures(self) -> None:
        """실패 확인 테스트"""
        context = PipelineContext()

        result1 = StageResult("Stage1", StageStatus.COMPLETED, "data")
        context.add_stage_result(result1)
        assert not context.has_failures()

        result2 = StageResult("Stage2", StageStatus.FAILED, "data", error="Error")
        context.add_stage_result(result2)
        assert context.has_failures()
