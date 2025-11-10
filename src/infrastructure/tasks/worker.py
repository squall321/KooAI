"""
Task worker implementation

백그라운드에서 작업을 실행하는 워커.
"""

import threading
import time
from typing import Any, Callable, Dict, Optional

import structlog

from .models import Task
from .queue import TaskQueue, get_task_queue

logger = structlog.get_logger(__name__)


class TaskWorker:
    """
    작업 워커

    백그라운드 스레드에서 작업을 실행합니다.

    주요 기능:
    - 작업 큐에서 작업 가져오기
    - 작업 실행
    - 결과 또는 에러 처리
    - Graceful shutdown
    - 타임아웃 처리

    사용 예:
        worker = TaskWorker(queue=queue, task_registry=registry)
        worker.start()  # 백그라운드 실행 시작

        # ... 작업 처리 ...

        worker.stop()  # Graceful shutdown
    """

    def __init__(
        self,
        queue: Optional[TaskQueue] = None,
        task_registry: Optional[Dict[str, Callable]] = None,
        worker_id: Optional[str] = None,
    ):
        """
        Args:
            queue: 작업 큐 (None이면 싱글톤 사용)
            task_registry: 작업 함수 레지스트리
            worker_id: 워커 ID (디버깅용)
        """
        self.queue = queue or get_task_queue()
        self.task_registry = task_registry or {}
        self.worker_id = worker_id or f"worker-{id(self)}"

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

    def register_task(self, name: str, func: Callable) -> None:
        """
        작업 함수 등록

        Args:
            name: 작업 이름
            func: 실행할 함수
        """
        self.task_registry[name] = func
        logger.debug("task_registered", name=name, worker_id=self.worker_id)

    def start(self) -> None:
        """워커 시작 (백그라운드 스레드)"""
        if self._running:
            logger.warning("worker_already_running", worker_id=self.worker_id)
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        logger.info("worker_started", worker_id=self.worker_id)

    def stop(self, timeout: float = 5.0) -> None:
        """
        워커 중지 (Graceful shutdown)

        Args:
            timeout: 대기 타임아웃 (초)
        """
        if not self._running:
            return

        logger.info("worker_stopping", worker_id=self.worker_id)
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

        self._running = False
        logger.info("worker_stopped", worker_id=self.worker_id)

    def _run(self) -> None:
        """워커 메인 루프"""
        logger.info("worker_loop_started", worker_id=self.worker_id)

        while not self._stop_event.is_set():
            try:
                # 작업 가져오기 (1초 타임아웃)
                task = self.queue.dequeue(timeout=1.0)

                if task is None:
                    continue

                # 작업 실행
                self._execute_task(task)

            except Exception as e:
                logger.exception(
                    "worker_loop_error",
                    worker_id=self.worker_id,
                    error=str(e),
                )
                time.sleep(1.0)

        logger.info("worker_loop_stopped", worker_id=self.worker_id)

    def _execute_task(self, task: Task) -> None:
        """
        작업 실행

        Args:
            task: 실행할 작업
        """
        logger.info(
            "task_executing",
            worker_id=self.worker_id,
            task_id=task.task_id,
            name=task.name,
        )

        # 작업 함수 찾기
        func = self.task_registry.get(task.name)

        if func is None:
            error_msg = f"Task function not found: {task.name}"
            logger.error(
                "task_function_not_found",
                task_id=task.task_id,
                name=task.name,
            )
            self.queue.complete_task(task.task_id, error=error_msg)
            return

        # 작업 실행
        try:
            # 타임아웃 처리 (선택적)
            if task.timeout:
                result = self._execute_with_timeout(func, task)
            else:
                result = func(*task.args, **task.kwargs)

            # 성공
            self.queue.complete_task(task.task_id, result=result)

            logger.info(
                "task_executed_successfully",
                worker_id=self.worker_id,
                task_id=task.task_id,
                name=task.name,
            )

        except Exception as e:
            # 실패
            error_msg = str(e)
            logger.exception(
                "task_execution_failed",
                worker_id=self.worker_id,
                task_id=task.task_id,
                name=task.name,
                error=error_msg,
            )
            self.queue.complete_task(task.task_id, error=error_msg)

    def _execute_with_timeout(self, func: Callable, task: Task) -> Any:
        """
        타임아웃과 함께 작업 실행

        Args:
            func: 실행할 함수
            task: 작업

        Returns:
            작업 결과

        Raises:
            TimeoutError: 타임아웃 발생 시
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *task.args, **task.kwargs)

            try:
                result = future.result(timeout=task.timeout)
                return result
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Task timed out after {task.timeout} seconds")

    @property
    def is_running(self) -> bool:
        """워커 실행 중 여부"""
        return self._running


class WorkerPool:
    """
    워커 풀

    여러 워커를 관리합니다.

    사용 예:
        pool = WorkerPool(num_workers=4, task_registry=registry)
        pool.start()

        # ... 작업 처리 ...

        pool.stop()
    """

    def __init__(
        self,
        num_workers: int = 4,
        queue: Optional[TaskQueue] = None,
        task_registry: Optional[Dict[str, Callable]] = None,
    ):
        """
        Args:
            num_workers: 워커 수
            queue: 작업 큐
            task_registry: 작업 함수 레지스트리
        """
        self.num_workers = num_workers
        self.queue = queue or get_task_queue()
        self.task_registry = task_registry or {}

        self.workers: list[TaskWorker] = []

    def start(self) -> None:
        """모든 워커 시작"""
        for i in range(self.num_workers):
            worker = TaskWorker(
                queue=self.queue,
                task_registry=self.task_registry,
                worker_id=f"worker-{i}",
            )
            worker.start()
            self.workers.append(worker)

        logger.info("worker_pool_started", num_workers=self.num_workers)

    def stop(self, timeout: float = 5.0) -> None:
        """모든 워커 중지"""
        logger.info("worker_pool_stopping", num_workers=self.num_workers)

        for worker in self.workers:
            worker.stop(timeout=timeout)

        self.workers.clear()
        logger.info("worker_pool_stopped")

    def register_task(self, name: str, func: Callable) -> None:
        """모든 워커에 작업 함수 등록"""
        self.task_registry[name] = func

        for worker in self.workers:
            worker.register_task(name, func)

    @property
    def running_workers(self) -> int:
        """실행 중인 워커 수"""
        return sum(1 for w in self.workers if w.is_running)


# Singleton instance
_worker_pool_instance: Optional[WorkerPool] = None


def get_worker_pool(num_workers: int = 4) -> WorkerPool:
    """워커 풀 싱글톤"""
    global _worker_pool_instance

    if _worker_pool_instance is None:
        _worker_pool_instance = WorkerPool(num_workers=num_workers)

    return _worker_pool_instance


def reset_worker_pool() -> None:
    """싱글톤 초기화 (테스트용)"""
    global _worker_pool_instance

    if _worker_pool_instance:
        _worker_pool_instance.stop()

    _worker_pool_instance = None
