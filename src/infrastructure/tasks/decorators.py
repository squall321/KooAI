"""
Task decorators

작업 등록 및 실행을 위한 데코레이터.
"""

import functools
from typing import Callable, Optional, Any

import structlog

from .models import Task, TaskPriority
from .queue import get_task_queue
from .worker import get_worker_pool

logger = structlog.get_logger(__name__)

# 전역 작업 레지스트리
_task_registry: dict[str, Callable] = {}


def task(
    name: Optional[str] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    timeout: Optional[int] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    작업 데코레이터

    함수를 비동기 작업으로 등록합니다.

    Args:
        name: 작업 이름 (None이면 함수명 사용)
        priority: 작업 우선순위
        max_retries: 최대 재시도 횟수
        timeout: 타임아웃 (초)

    Example:
        @task(name="process_data", priority=TaskPriority.HIGH)
        def process_data(file_path: str):
            # 시간이 오래 걸리는 작업
            return result

        # 비동기 실행
        task_id = process_data.delay("/path/to/file.csv")

        # 결과 대기
        result = process_data.wait(task_id, timeout=60)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        task_name = name or f"{func.__module__}.{func.__name__}"

        # 레지스트리에 등록
        _task_registry[task_name] = func

        # delay() 메서드 추가
        def delay(*args: Any, **kwargs: Any) -> str:
            """
            작업을 큐에 추가하고 즉시 반환

            Returns:
                task_id
            """
            queue = get_task_queue()

            task_obj = Task(
                name=task_name,
                args=args,
                kwargs=kwargs,
                priority=priority,
                max_retries=max_retries,
                timeout=timeout,
            )

            task_id = queue.enqueue(task_obj)

            logger.info(
                "task_delayed",
                task_id=task_id,
                name=task_name,
            )

            return task_id

        # wait() 메서드 추가
        def wait(task_id: str, timeout: Optional[float] = None) -> Any:
            """
            작업 완료 대기

            Args:
                task_id: 작업 ID
                timeout: 타임아웃 (초)

            Returns:
                작업 결과

            Raises:
                TimeoutError: 타임아웃 발생
                RuntimeError: 작업 실패
            """
            import time

            queue = get_task_queue()
            start_time = time.time()

            while True:
                result = queue.get_result(task_id)

                if result is not None:
                    if result.error:
                        raise RuntimeError(f"Task failed: {result.error}")
                    return result.result

                # 타임아웃 확인
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(f"Task did not complete within {timeout} seconds")

                time.sleep(0.1)

        # apply_async() 메서드 추가 (Celery 호환)
        def apply_async(*args: Any, **kwargs: Any) -> str:
            """Celery 스타일 비동기 실행"""
            return delay(*args, **kwargs)

        # 원본 함수 유지
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # 메서드 첨부
        wrapper.delay = delay  # type: ignore[attr-defined]
        wrapper.wait = wait  # type: ignore[attr-defined]
        wrapper.apply_async = apply_async  # type: ignore[attr-defined]
        wrapper.task_name = task_name  # type: ignore[attr-defined]

        return wrapper

    return decorator


def get_task_registry() -> dict[str, Callable]:
    """작업 레지스트리 반환"""
    return _task_registry


def register_tasks_to_workers() -> None:
    """
    등록된 모든 작업을 워커 풀에 등록

    워커 시작 전에 호출해야 합니다.
    """
    worker_pool = get_worker_pool()

    for task_name, func in _task_registry.items():
        worker_pool.register_task(task_name, func)

    logger.info("tasks_registered_to_workers", count=len(_task_registry))
