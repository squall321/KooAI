"""
파이프라인 기본 아키텍처

데이터 처리 파이프라인의 핵심 추상화.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID, uuid4


class StageStatus(str, Enum):
    """처리 단계 상태"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """처리 단계 결과"""

    stage_name: str
    status: StageStatus
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def get_duration_seconds(self) -> Optional[float]:
        """처리 시간 (초) 반환"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def is_success(self) -> bool:
        """성공 여부"""
        return self.status == StageStatus.COMPLETED

    def is_failed(self) -> bool:
        """실패 여부"""
        return self.status == StageStatus.FAILED


@dataclass
class PipelineContext:
    """
    파이프라인 컨텍스트

    파이프라인 실행 중 공유되는 컨텍스트.
    """

    pipeline_id: UUID = field(default_factory=uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage_results: List[StageResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_stage_result(self, result: StageResult) -> None:
        """단계 결과 추가"""
        self.stage_results.append(result)

    def get_last_result(self) -> Optional[StageResult]:
        """마지막 단계 결과 반환"""
        return self.stage_results[-1] if self.stage_results else None

    def get_stage_result(self, stage_name: str) -> Optional[StageResult]:
        """특정 단계의 결과 조회"""
        for result in self.stage_results:
            if result.stage_name == stage_name:
                return result
        return None

    def has_failures(self) -> bool:
        """실패한 단계가 있는지 확인"""
        return any(r.is_failed() for r in self.stage_results)


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""

    pipeline_id: UUID
    final_data: Any
    context: PipelineContext
    success: bool
    total_duration_seconds: float
    stage_count: int

    def get_stage_results(self) -> List[StageResult]:
        """모든 단계 결과 반환"""
        return self.context.stage_results

    def get_failed_stages(self) -> List[StageResult]:
        """실패한 단계들 반환"""
        return [r for r in self.context.stage_results if r.is_failed()]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "pipeline_id": str(self.pipeline_id),
            "success": self.success,
            "total_duration_seconds": self.total_duration_seconds,
            "stage_count": self.stage_count,
            "stages": [
                {
                    "name": r.stage_name,
                    "status": r.status.value,
                    "duration_seconds": r.get_duration_seconds(),
                    "error": r.error,
                }
                for r in self.context.stage_results
            ],
        }


class ProcessingStage(ABC):
    """
    처리 단계 기본 클래스

    파이프라인의 각 단계를 나타냅니다.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Args:
            name: 단계 이름 (없으면 클래스 이름 사용)
        """
        self.name = name or self.__class__.__name__
        self.skip_on_failure = False

    @abstractmethod
    async def process(self, data: Any, context: PipelineContext) -> Any:
        """
        데이터 처리

        Args:
            data: 입력 데이터
            context: 파이프라인 컨텍스트

        Returns:
            Any: 처리된 데이터

        Raises:
            Exception: 처리 실패 시
        """
        pass

    async def execute(self, data: Any, context: PipelineContext) -> StageResult:
        """
        단계 실행

        Args:
            data: 입력 데이터
            context: 파이프라인 컨텍스트

        Returns:
            StageResult: 단계 실행 결과
        """
        started_at = datetime.utcnow()

        try:
            # 처리 수행
            processed_data = await self.process(data, context)

            # 성공 결과
            result = StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=processed_data,
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        except Exception as e:
            # 실패 결과
            result = StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                data=data,  # 원본 데이터 유지
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        return result

    def should_skip(self, context: PipelineContext) -> bool:
        """
        단계를 건너뛸지 결정

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            bool: 건너뛰기 여부
        """
        # 이전 단계 실패 시 skip_on_failure 확인
        if self.skip_on_failure and context.has_failures():
            return True
        return False


class Pipeline:
    """
    데이터 처리 파이프라인

    여러 처리 단계를 순차적으로 실행합니다.
    """

    def __init__(
        self,
        stages: Optional[List[ProcessingStage]] = None,
        name: str = "Pipeline",
        stop_on_failure: bool = True,
    ):
        """
        Args:
            stages: 처리 단계 리스트
            name: 파이프라인 이름
            stop_on_failure: 실패 시 중단 여부
        """
        self.name = name
        self.stages: List[ProcessingStage] = stages or []
        self.stop_on_failure = stop_on_failure
        self._hooks: Dict[str, List[Callable]] = {
            "before_stage": [],
            "after_stage": [],
            "on_error": [],
        }

    def add_stage(self, stage: ProcessingStage) -> "Pipeline":
        """
        처리 단계 추가

        Args:
            stage: 처리 단계

        Returns:
            Pipeline: 체이닝을 위한 자신 반환
        """
        self.stages.append(stage)
        return self

    def add_hook(self, event: str, callback: Callable) -> None:
        """
        훅 추가

        Args:
            event: 이벤트 이름 (before_stage, after_stage, on_error)
            callback: 콜백 함수
        """
        if event in self._hooks:
            self._hooks[event].append(callback)

    async def execute(
        self, initial_data: Any, context: Optional[PipelineContext] = None
    ) -> PipelineResult:
        """
        파이프라인 실행

        Args:
            initial_data: 초기 입력 데이터
            context: 파이프라인 컨텍스트 (없으면 새로 생성)

        Returns:
            PipelineResult: 실행 결과
        """
        # 컨텍스트 생성 또는 사용
        if context is None:
            context = PipelineContext()

        context.metadata["pipeline_name"] = self.name
        context.metadata["stage_count"] = len(self.stages)

        start_time = datetime.utcnow()
        current_data = initial_data
        success = True

        # 각 단계 실행
        for stage in self.stages:
            # 건너뛰기 확인
            if stage.should_skip(context):
                skip_result = StageResult(
                    stage_name=stage.name,
                    status=StageStatus.SKIPPED,
                    data=current_data,
                )
                context.add_stage_result(skip_result)
                continue

            # Before hook
            for hook in self._hooks["before_stage"]:
                await hook(stage, current_data, context)

            # 단계 실행
            stage_result = await stage.execute(current_data, context)
            context.add_stage_result(stage_result)

            # After hook
            for hook in self._hooks["after_stage"]:
                await hook(stage, stage_result, context)

            # 실패 처리
            if stage_result.is_failed():
                success = False

                # Error hook
                for hook in self._hooks["on_error"]:
                    await hook(stage, stage_result, context)

                # 중단 여부 확인
                if self.stop_on_failure:
                    break
            else:
                # 성공 시 데이터 업데이트
                current_data = stage_result.data

        # 최종 결과
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()

        return PipelineResult(
            pipeline_id=context.pipeline_id,
            final_data=current_data,
            context=context,
            success=success and not context.has_failures(),
            total_duration_seconds=total_duration,
            stage_count=len(self.stages),
        )

    def __len__(self) -> int:
        """파이프라인의 단계 개수"""
        return len(self.stages)

    def __repr__(self) -> str:
        return f"<Pipeline '{self.name}' with {len(self.stages)} stages>"
