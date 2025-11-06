"""
Transformation stages

데이터 변환을 위한 처리 단계들.
"""

from typing import Any, Callable, Dict, List, Optional

from ..base import ProcessingStage, PipelineContext


class FilterStage(ProcessingStage):
    """
    필터 단계

    조건에 맞는 데이터만 필터링합니다.
    """

    def __init__(
        self,
        filter_func: Callable[[Any], bool],
        name: str = "Filter",
    ):
        """
        Args:
            filter_func: 필터 함수 (True를 반환하면 유지)
            name: 단계 이름
        """
        super().__init__(name)
        self.filter_func = filter_func

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 필터링

        Args:
            data: 입력 데이터 (리스트 또는 단일 항목)
            context: 컨텍스트

        Returns:
            Any: 필터링된 데이터
        """
        if isinstance(data, list):
            filtered = [item for item in data if self.filter_func(item)]
            context.metadata[f"{self.name}_filtered_count"] = len(data) - len(
                filtered
            )
            return filtered
        else:
            # 단일 항목
            if self.filter_func(data):
                return data
            else:
                raise ValueError(f"Data filtered out by {self.name}")


class MapStage(ProcessingStage):
    """
    매핑 단계

    각 데이터 항목에 함수를 적용합니다.
    """

    def __init__(
        self,
        map_func: Callable[[Any], Any],
        name: str = "Map",
    ):
        """
        Args:
            map_func: 매핑 함수
            name: 단계 이름
        """
        super().__init__(name)
        self.map_func = map_func

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 매핑

        Args:
            data: 입력 데이터
            context: 컨텍스트

        Returns:
            Any: 변환된 데이터
        """
        if isinstance(data, list):
            return [self.map_func(item) for item in data]
        else:
            return self.map_func(data)


class AggregateStage(ProcessingStage):
    """
    집계 단계

    데이터를 집계합니다.
    """

    def __init__(
        self,
        aggregate_func: Callable[[List[Any]], Any],
        name: str = "Aggregate",
    ):
        """
        Args:
            aggregate_func: 집계 함수
            name: 단계 이름
        """
        super().__init__(name)
        self.aggregate_func = aggregate_func

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 집계

        Args:
            data: 입력 데이터 (리스트)
            context: 컨텍스트

        Returns:
            Any: 집계된 결과
        """
        if not isinstance(data, list):
            raise TypeError(f"AggregateStage expects list, got {type(data)}")

        result = self.aggregate_func(data)

        context.metadata[f"{self.name}_input_count"] = len(data)

        return result


class ValidationStage(ProcessingStage):
    """
    검증 단계

    데이터 유효성을 검증합니다.
    """

    def __init__(
        self,
        validation_func: Callable[[Any], bool],
        error_message: str = "Validation failed",
        name: str = "Validation",
    ):
        """
        Args:
            validation_func: 검증 함수 (True를 반환하면 통과)
            error_message: 실패 시 에러 메시지
            name: 단계 이름
        """
        super().__init__(name)
        self.validation_func = validation_func
        self.error_message = error_message

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 검증

        Args:
            data: 입력 데이터
            context: 컨텍스트

        Returns:
            Any: 입력 데이터 (검증 통과 시)

        Raises:
            ValueError: 검증 실패 시
        """
        if not self.validation_func(data):
            raise ValueError(self.error_message)

        return data


class TransformStage(ProcessingStage):
    """
    변환 단계

    데이터 구조를 변환합니다.
    """

    def __init__(
        self,
        transform_func: Callable[[Any, PipelineContext], Any],
        name: str = "Transform",
    ):
        """
        Args:
            transform_func: 변환 함수 (data, context를 받음)
            name: 단계 이름
        """
        super().__init__(name)
        self.transform_func = transform_func

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 변환

        Args:
            data: 입력 데이터
            context: 컨텍스트

        Returns:
            Any: 변환된 데이터
        """
        return self.transform_func(data, context)


class NormalizeStage(ProcessingStage):
    """
    정규화 단계

    데이터를 정규화합니다.
    """

    def __init__(
        self,
        normalizer: Optional[Any] = None,
        method: str = "min_max",
        name: str = "Normalize",
    ):
        """
        Args:
            normalizer: 정규화 객체 (normalize 메서드 필요)
            method: 정규화 방법
            name: 단계 이름
        """
        super().__init__(name)
        self.normalizer = normalizer
        self.method = method

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 정규화

        Args:
            data: 입력 데이터
            context: 컨텍스트

        Returns:
            Any: 정규화된 데이터
        """
        if self.normalizer:
            normalized, params = self.normalizer.normalize(data, method=self.method)
            context.metadata[f"{self.name}_params"] = params
            return normalized
        else:
            # 기본 min-max 정규화 (numpy array 가정)
            import numpy as np

            data_array = np.array(data)
            min_val = data_array.min()
            max_val = data_array.max()

            if max_val - min_val == 0:
                return data_array

            normalized = (data_array - min_val) / (max_val - min_val)

            context.metadata[f"{self.name}_min"] = float(min_val)
            context.metadata[f"{self.name}_max"] = float(max_val)

            return normalized.tolist() if isinstance(data, list) else normalized
