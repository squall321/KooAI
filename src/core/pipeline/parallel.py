"""
병렬 처리 파이프라인

여러 데이터를 병렬로 처리합니다.
"""

import asyncio
from typing import Any, Callable, List, Optional, Union

from .base import (
    Pipeline,
    PipelineContext,
    PipelineResult,
    ProcessingStage,
)


class ParallelPipeline:
    """
    병렬 파이프라인

    여러 데이터 항목을 병렬로 처리합니다.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        max_concurrency: int = 10,
        name: str = "ParallelPipeline",
    ):
        """
        Args:
            pipeline: 실행할 파이프라인
            max_concurrency: 최대 동시 실행 개수
            name: 파이프라인 이름
        """
        self.pipeline = pipeline
        self.max_concurrency = max_concurrency
        self.name = name

    async def execute(
        self, data_list: List[Any], context: Optional[PipelineContext] = None
    ) -> List[PipelineResult]:
        """
        병렬 실행

        Args:
            data_list: 처리할 데이터 리스트
            context: 공유 컨텍스트 (각 파이프라인은 독립적인 컨텍스트 사용)

        Returns:
            List[PipelineResult]: 각 데이터의 실행 결과
        """
        # 세마포어로 동시 실행 개수 제한
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def process_item(item: Any) -> PipelineResult:
            """단일 항목 처리"""
            async with semaphore:
                # 각 항목은 독립적인 컨텍스트 사용
                item_context = PipelineContext()
                if context:
                    # 공유 메타데이터 복사
                    item_context.metadata.update(context.metadata)

                return await self.pipeline.execute(item, item_context)

        # 병렬 실행
        results = await asyncio.gather(
            *[process_item(item) for item in data_list], return_exceptions=False
        )

        return results


class ParallelStage(ProcessingStage):
    """
    병렬 처리 단계

    리스트의 각 항목을 병렬로 처리합니다.
    """

    def __init__(
        self,
        process_func: Callable,
        max_concurrency: int = 10,
        name: str = "ParallelStage",
    ):
        """
        Args:
            process_func: 각 항목에 적용할 비동기 함수
            max_concurrency: 최대 동시 실행 개수
            name: 단계 이름
        """
        super().__init__(name)
        self.process_func = process_func
        self.max_concurrency = max_concurrency

    async def process(self, data: Any, context: PipelineContext) -> List[Any]:
        """
        병렬 처리

        Args:
            data: 입력 데이터 (리스트)
            context: 컨텍스트

        Returns:
            List[Any]: 처리된 결과 리스트
        """
        if not isinstance(data, list):
            raise TypeError(f"ParallelStage expects list, got {type(data)}")

        # 세마포어
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def process_item(item: Any) -> Any:
            """단일 항목 처리"""
            async with semaphore:
                return await self.process_func(item)

        # 병렬 실행
        results = await asyncio.gather(*[process_item(item) for item in data])

        context.metadata[f"{self.name}_processed_count"] = len(results)

        return results


class BatchStage(ProcessingStage):
    """
    배치 처리 단계

    데이터를 배치로 나누어 처리합니다.
    """

    def __init__(
        self,
        batch_func: Callable,
        batch_size: int = 100,
        name: str = "BatchStage",
    ):
        """
        Args:
            batch_func: 배치 처리 함수 (비동기)
            batch_size: 배치 크기
            name: 단계 이름
        """
        super().__init__(name)
        self.batch_func = batch_func
        self.batch_size = batch_size

    async def process(self, data: Any, context: PipelineContext) -> List[Any]:
        """
        배치 처리

        Args:
            data: 입력 데이터 (리스트)
            context: 컨텍스트

        Returns:
            List[Any]: 처리된 결과 리스트
        """
        if not isinstance(data, list):
            raise TypeError(f"BatchStage expects list, got {type(data)}")

        results = []
        batch_count = 0

        # 배치로 나누어 처리
        for i in range(0, len(data), self.batch_size):
            batch = data[i : i + self.batch_size]
            batch_result = await self.batch_func(batch)

            # 결과가 리스트면 확장, 아니면 추가
            if isinstance(batch_result, list):
                results.extend(batch_result)
            else:
                results.append(batch_result)

            batch_count += 1

        context.metadata[f"{self.name}_batch_count"] = batch_count
        context.metadata[f"{self.name}_batch_size"] = self.batch_size

        return results


class ConditionalStage(ProcessingStage):
    """
    조건부 실행 단계

    조건에 따라 다른 처리를 수행합니다.
    """

    def __init__(
        self,
        condition_func: Callable,
        true_stage: Union[ProcessingStage, Pipeline],
        false_stage: Optional[Union[ProcessingStage, Pipeline]] = None,
        name: str = "ConditionalStage",
    ):
        """
        Args:
            condition_func: 조건 함수 (data를 받아 bool 반환)
            true_stage: 조건이 True일 때 실행할 단계
            false_stage: 조건이 False일 때 실행할 단계 (optional)
            name: 단계 이름
        """
        super().__init__(name)
        self.condition_func = condition_func
        self.true_stage = true_stage
        self.false_stage = false_stage

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        조건부 실행

        Args:
            data: 입력 데이터
            context: 컨텍스트

        Returns:
            Any: 처리된 데이터
        """
        # 조건 평가
        condition_result = self.condition_func(data)

        if condition_result:
            # True 경로
            context.metadata[f"{self.name}_branch"] = "true"
            result = await self.true_stage.execute(data, context)
            # PipelineResult는 final_data, StageResult는 data 사용
            return result.final_data if isinstance(result, PipelineResult) else result.data
        else:
            # False 경로
            context.metadata[f"{self.name}_branch"] = "false"
            if self.false_stage:
                result = await self.false_stage.execute(data, context)
                # PipelineResult는 final_data, StageResult는 data 사용
                return result.final_data if isinstance(result, PipelineResult) else result.data
            else:
                # false_stage가 없으면 데이터 그대로 반환
                return data
