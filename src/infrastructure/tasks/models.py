"""
Task models and status

비동기 작업 모델 정의.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(str, Enum):
    """작업 상태"""

    PENDING = "pending"  # 대기 중
    RUNNING = "running"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소됨
    RETRY = "retry"  # 재시도 대기


class TaskPriority(int, Enum):
    """작업 우선순위"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """
    비동기 작업

    Attributes:
        task_id: 작업 ID (UUID)
        name: 작업 이름 (함수명)
        args: 위치 인자
        kwargs: 키워드 인자
        status: 작업 상태
        priority: 작업 우선순위
        created_at: 생성 시간
        started_at: 시작 시간
        completed_at: 완료 시간
        result: 작업 결과
        error: 에러 메시지
        retry_count: 재시도 횟수
        max_retries: 최대 재시도 횟수
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None  # 타임아웃 (초)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error": self.error,
        }

    @property
    def is_finished(self) -> bool:
        """완료 여부 (성공 또는 실패)"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]

    @property
    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return (
            self.status == TaskStatus.FAILED
            and self.retry_count < self.max_retries
        )

    def duration_seconds(self) -> Optional[float]:
        """실행 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class TaskResult:
    """
    작업 결과

    Attributes:
        task_id: 작업 ID
        status: 작업 상태
        result: 작업 결과
        error: 에러 메시지
        duration_seconds: 실행 시간
    """

    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None

    @classmethod
    def from_task(cls, task: Task) -> "TaskResult":
        """Task에서 TaskResult 생성"""
        return cls(
            task_id=task.task_id,
            status=task.status,
            result=task.result,
            error=task.error,
            duration_seconds=task.duration_seconds(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }
