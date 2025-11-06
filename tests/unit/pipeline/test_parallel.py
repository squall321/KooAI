"""병렬 처리 파이프라인 테스트"""

import pytest
import asyncio
from typing import Any

from src.core.pipeline import (
    Pipeline,
    ProcessingStage,
    PipelineContext,
)
from src.core.pipeline.parallel import (
    ParallelPipeline,
    ParallelStage,
    BatchStage,
    ConditionalStage,
)


class DoubleStage(ProcessingStage):
    """테스트용 단계: 값을 2배로"""

    async def process(self, data: Any, context: PipelineContext) -> Any:
        return data * 2


class AsyncDoubleFunc:
    """비동기 함수 래퍼"""

    async def __call__(self, x):
        await asyncio.sleep(0.01)  # 비동기 작업 시뮬레이션
        return x * 2


class TestParallelPipeline:
    """ParallelPipeline 테스트"""

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """병렬 실행 테스트"""
        pipeline = Pipeline().add_stage(DoubleStage())
        parallel_pipeline = ParallelPipeline(pipeline, max_concurrency=3)

        data_list = [1, 2, 3, 4, 5]
        results = await parallel_pipeline.execute(data_list)

        assert len(results) == 5
        # 모든 결과가 성공적
        for i, result in enumerate(results):
            assert result.success is True
            assert result.final_data == (i + 1) * 2

    @pytest.mark.asyncio
    async def test_parallel_with_max_concurrency(self):
        """동시 실행 제한 테스트"""
        pipeline = Pipeline().add_stage(DoubleStage())
        parallel_pipeline = ParallelPipeline(pipeline, max_concurrency=2)

        data_list = list(range(10))
        results = await parallel_pipeline.execute(data_list)

        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.final_data == i * 2

    @pytest.mark.asyncio
    async def test_parallel_with_shared_context(self):
        """공유 컨텍스트 테스트"""
        pipeline = Pipeline().add_stage(DoubleStage())

        shared_context = PipelineContext()
        shared_context.metadata["shared_key"] = "shared_value"

        parallel_pipeline = ParallelPipeline(pipeline)

        results = await parallel_pipeline.execute([1, 2, 3], shared_context)

        assert len(results) == 3
        # 각 결과는 독립적인 컨텍스트를 가지지만 공유 메타데이터는 복사됨
        for result in results:
            assert result.success is True


class TestParallelStage:
    """ParallelStage 테스트"""

    @pytest.mark.asyncio
    async def test_parallel_stage(self):
        """병렬 스테이지 테스트"""
        async def double_async(x):
            await asyncio.sleep(0.01)
            return x * 2

        stage = ParallelStage(double_async, max_concurrency=3)
        context = PipelineContext()

        data = [1, 2, 3, 4, 5]
        results = await stage.process(data, context)

        assert results == [2, 4, 6, 8, 10]
        assert context.metadata["ParallelStage_processed_count"] == 5

    @pytest.mark.asyncio
    async def test_parallel_stage_with_single_concurrency(self):
        """단일 동시 실행 테스트"""
        async def square_async(x):
            return x ** 2

        stage = ParallelStage(square_async, max_concurrency=1)
        context = PipelineContext()

        data = [2, 3, 4]
        results = await stage.process(data, context)

        assert results == [4, 9, 16]

    @pytest.mark.asyncio
    async def test_parallel_stage_with_non_list_raises_error(self):
        """리스트가 아닌 입력 시 에러 테스트"""
        async def dummy(x):
            return x

        stage = ParallelStage(dummy)
        context = PipelineContext()

        with pytest.raises(TypeError, match="expects list"):
            await stage.process(42, context)


class TestBatchStage:
    """BatchStage 테스트"""

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """배치 처리 테스트"""
        async def sum_batch(batch):
            """배치를 합산"""
            return sum(batch)

        stage = BatchStage(sum_batch, batch_size=3)
        context = PipelineContext()

        data = [1, 2, 3, 4, 5, 6, 7, 8]
        results = await stage.process(data, context)

        # [1,2,3] -> 6, [4,5,6] -> 15, [7,8] -> 15
        assert results == [6, 15, 15]
        assert context.metadata["BatchStage_batch_count"] == 3
        assert context.metadata["BatchStage_batch_size"] == 3

    @pytest.mark.asyncio
    async def test_batch_with_list_results(self):
        """배치 결과가 리스트인 경우 테스트"""
        async def double_batch(batch):
            """배치의 각 항목을 2배로"""
            return [x * 2 for x in batch]

        stage = BatchStage(double_batch, batch_size=2)
        context = PipelineContext()

        data = [1, 2, 3, 4, 5]
        results = await stage.process(data, context)

        # [1,2] -> [2,4], [3,4] -> [6,8], [5] -> [10]
        # extend로 합쳐짐
        assert results == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_batch_with_single_batch(self):
        """단일 배치 테스트"""
        async def process_batch(batch):
            return len(batch)

        stage = BatchStage(process_batch, batch_size=100)
        context = PipelineContext()

        data = [1, 2, 3]
        results = await stage.process(data, context)

        assert results == [3]
        assert context.metadata["BatchStage_batch_count"] == 1

    @pytest.mark.asyncio
    async def test_batch_with_non_list_raises_error(self):
        """리스트가 아닌 입력 시 에러 테스트"""
        async def dummy(batch):
            return batch

        stage = BatchStage(dummy, batch_size=5)
        context = PipelineContext()

        with pytest.raises(TypeError, match="expects list"):
            await stage.process("not a list", context)


class TestConditionalStage:
    """ConditionalStage 테스트"""

    @pytest.mark.asyncio
    async def test_conditional_true_path(self):
        """True 경로 테스트"""
        def is_positive(x):
            return x > 0

        true_stage = Pipeline().add_stage(DoubleStage())

        stage = ConditionalStage(
            condition_func=is_positive,
            true_stage=true_stage,
        )
        context = PipelineContext()

        result = await stage.process(5, context)

        assert result == 10  # 5 * 2
        assert context.metadata["ConditionalStage_branch"] == "true"

    @pytest.mark.asyncio
    async def test_conditional_false_path_with_stage(self):
        """False 경로 (단계 있음) 테스트"""
        def is_even(x):
            return x % 2 == 0

        true_stage = Pipeline().add_stage(DoubleStage())

        class TripleStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return data * 3

        false_stage = Pipeline().add_stage(TripleStage())

        stage = ConditionalStage(
            condition_func=is_even,
            true_stage=true_stage,
            false_stage=false_stage,
        )
        context = PipelineContext()

        # 짝수 경로
        result_even = await stage.process(4, context)
        assert result_even == 8  # 4 * 2
        assert context.metadata["ConditionalStage_branch"] == "true"

        # 홀수 경로
        context2 = PipelineContext()
        result_odd = await stage.process(5, context2)
        assert result_odd == 15  # 5 * 3
        assert context2.metadata["ConditionalStage_branch"] == "false"

    @pytest.mark.asyncio
    async def test_conditional_false_path_without_stage(self):
        """False 경로 (단계 없음) 테스트"""
        def is_large(x):
            return x > 100

        true_stage = Pipeline().add_stage(DoubleStage())

        stage = ConditionalStage(
            condition_func=is_large,
            true_stage=true_stage,
            false_stage=None,  # False 경로 없음
        )
        context = PipelineContext()

        # 작은 값: 데이터 그대로 반환
        result = await stage.process(10, context)

        assert result == 10  # 변경 없음
        assert context.metadata["ConditionalStage_branch"] == "false"

    @pytest.mark.asyncio
    async def test_conditional_with_lambda(self):
        """람다 조건 함수 테스트"""
        true_stage = Pipeline().add_stage(DoubleStage())

        stage = ConditionalStage(
            condition_func=lambda x: x < 0,  # 음수 체크
            true_stage=true_stage,
        )

        context1 = PipelineContext()
        result_negative = await stage.process(-5, context1)
        assert result_negative == -10  # -5 * 2
        assert context1.metadata["ConditionalStage_branch"] == "true"

        context2 = PipelineContext()
        result_positive = await stage.process(5, context2)
        assert result_positive == 5  # 변경 없음
        assert context2.metadata["ConditionalStage_branch"] == "false"
