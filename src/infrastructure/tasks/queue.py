"""
Task queue implementation

Thread-safe 작업 큐 구현.
"""

import heapq
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog

from .models import Task, TaskResult, TaskStatus

logger = structlog.get_logger(__name__)


class TaskQueue:
    """
    우선순위 기반 작업 큐

    주요 기능:
    - 우선순위 큐 (heapq 사용)
    - Thread-safe operations
    - 작업 상태 추적
    - 작업 결과 저장
    - 통계 수집

    사용 예:
        queue = TaskQueue()
        task = Task(name="process_data", args=(data,), priority=TaskPriority.HIGH)
        queue.enqueue(task)

        task = queue.dequeue()  # 가장 높은 우선순위 작업 반환
    """

    def __init__(self) -> None:
        """작업 큐 초기화"""
        # 우선순위 큐 (heapq): (priority, timestamp, task)
        self._queue: List[Tuple[int, float, Task]] = []
        self._lock = threading.RLock()

        # 작업 저장소 (task_id -> Task)
        self._tasks: Dict[str, Task] = {}

        # 작업 결과 저장소
        self._results: Dict[str, TaskResult] = {}

        # 통계
        self._stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
        }

    def enqueue(self, task: Task) -> str:
        """
        작업을 큐에 추가

        Args:
            task: 작업 인스턴스

        Returns:
            task_id
        """
        with self._lock:
            # 우선순위가 높을수록 먼저 처리 (음수 사용)
            priority = -task.priority.value
            timestamp = time.time()

            heapq.heappush(self._queue, (priority, timestamp, task))
            self._tasks[task.task_id] = task

            self._stats["total_enqueued"] += 1

            logger.info(
                "task_enqueued",
                task_id=task.task_id,
                name=task.name,
                priority=task.priority.value,
            )

            return task.task_id

    def dequeue(self, timeout: Optional[float] = None) -> Optional[Task]:
        """
        큐에서 작업 꺼내기 (가장 높은 우선순위)

        Args:
            timeout: 타임아웃 (초), None이면 무한 대기

        Returns:
            Task 또는 None
        """
        start_time = time.time()

        while True:
            with self._lock:
                if self._queue:
                    _, _, task = heapq.heappop(self._queue)

                    # 상태 업데이트
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.utcnow()

                    logger.debug(
                        "task_dequeued",
                        task_id=task.task_id,
                        name=task.name,
                    )

                    return task

            # 타임아웃 확인
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None

            # 짧은 대기 후 재시도
            time.sleep(0.1)

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        작업 조회

        Args:
            task_id: 작업 ID

        Returns:
            Task 또는 None
        """
        with self._lock:
            return self._tasks.get(task_id)

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """
        작업 결과 조회

        Args:
            task_id: 작업 ID

        Returns:
            TaskResult 또는 None
        """
        with self._lock:
            return self._results.get(task_id)

    def complete_task(self, task_id: str, result: Any = None, error: Optional[str] = None) -> None:
        """
        작업 완료 처리

        Args:
            task_id: 작업 ID
            result: 작업 결과
            error: 에러 메시지 (실패 시)
        """
        with self._lock:
            task = self._tasks.get(task_id)

            if not task:
                logger.warning("task_not_found", task_id=task_id)
                return

            task.completed_at = datetime.utcnow()
            task.result = result
            task.error = error

            if error:
                task.status = TaskStatus.FAILED
                self._stats["total_failed"] += 1

                # 재시도 가능한 경우
                if task.can_retry:
                    task.status = TaskStatus.RETRY
                    task.retry_count += 1
                    # 재시도 큐에 추가
                    self.enqueue(task)
                    logger.info(
                        "task_retry",
                        task_id=task_id,
                        retry_count=task.retry_count,
                    )
                    return
            else:
                task.status = TaskStatus.COMPLETED
                self._stats["total_completed"] += 1

            # 결과 저장
            self._results[task_id] = TaskResult.from_task(task)

            logger.info(
                "task_completed",
                task_id=task_id,
                status=task.status.value,
                duration=task.duration_seconds(),
            )

    def cancel_task(self, task_id: str) -> bool:
        """
        작업 취소

        Args:
            task_id: 작업 ID

        Returns:
            취소 성공 여부
        """
        with self._lock:
            task = self._tasks.get(task_id)

            if not task:
                return False

            # 실행 중인 작업은 취소 불가
            if task.status == TaskStatus.RUNNING:
                return False

            # 대기 중인 작업만 취소 가능
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self._stats["total_cancelled"] += 1

                # 큐에서 제거 (재구성)
                self._queue = [(p, t, tk) for p, t, tk in self._queue if tk.task_id != task_id]
                heapq.heapify(self._queue)

                logger.info("task_cancelled", task_id=task_id)
                return True

            return False

    def get_pending_tasks(self) -> List[Task]:
        """대기 중인 작업 목록"""
        with self._lock:
            return [task for _, _, task in self._queue]

    def get_running_tasks(self) -> List[Task]:
        """실행 중인 작업 목록"""
        with self._lock:
            return [task for task in self._tasks.values() if task.status == TaskStatus.RUNNING]

    def get_stats(self) -> Dict[str, Any]:
        """큐 통계"""
        with self._lock:
            pending_count = len(self._queue)
            running_count = len(self.get_running_tasks())

            return {
                "pending": pending_count,
                "running": running_count,
                "total_enqueued": self._stats["total_enqueued"],
                "total_completed": self._stats["total_completed"],
                "total_failed": self._stats["total_failed"],
                "total_cancelled": self._stats["total_cancelled"],
            }

    def clear(self) -> None:
        """큐 초기화"""
        with self._lock:
            self._queue.clear()
            self._tasks.clear()
            self._results.clear()

    def __len__(self) -> int:
        """큐 크기"""
        with self._lock:
            return len(self._queue)


# Singleton instance
_queue_instance: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """작업 큐 싱글톤"""
    global _queue_instance

    if _queue_instance is None:
        _queue_instance = TaskQueue()

    return _queue_instance


def reset_task_queue() -> None:
    """싱글톤 초기화 (테스트용)"""
    global _queue_instance
    _queue_instance = None
