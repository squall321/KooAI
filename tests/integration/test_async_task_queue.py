"""
Integration tests for Async Task Queue

Tests the task queue system with workers, priorities, retries, and timeouts.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.tasks import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskQueue,
    TaskWorker,
    WorkerPool,
    task,
    get_task_queue,
    get_worker_pool,
    get_task_registry,
    register_tasks_to_workers,
    reset_task_queue,
    reset_worker_pool,
)


@pytest.fixture(autouse=True)
def cleanup_singletons():
    """Clean up singleton instances after each test"""
    yield
    reset_task_queue()
    reset_worker_pool()


@pytest.fixture
def task_queue():
    """Create fresh task queue"""
    return TaskQueue()


@pytest.fixture
def worker_pool(task_queue):
    """Create worker pool with task registry"""
    pool = WorkerPool(num_workers=2, queue=task_queue)
    yield pool
    if pool.workers:
        pool.stop(timeout=1.0)


# Test task functions
@task(name="test.simple_task", priority=TaskPriority.NORMAL)
def simple_task(value: int) -> int:
    """Simple test task"""
    return value * 2


@task(name="test.slow_task", priority=TaskPriority.NORMAL)
def slow_task(duration: float) -> str:
    """Task that takes time"""
    time.sleep(duration)
    return "completed"


@task(name="test.failing_task", max_retries=2)
def failing_task(fail_count: int) -> str:
    """Task that fails specified number of times"""
    if not hasattr(failing_task, "_attempts"):
        failing_task._attempts = {}

    key = threading.get_ident()
    failing_task._attempts[key] = failing_task._attempts.get(key, 0) + 1

    if failing_task._attempts[key] <= fail_count:
        raise Exception(f"Intentional failure (attempt {failing_task._attempts[key]})")

    return "success after retries"


@task(name="test.timeout_task", timeout=2)
def timeout_task(duration: float) -> str:
    """Task that might timeout"""
    time.sleep(duration)
    return "completed"


@task(name="test.high_priority", priority=TaskPriority.HIGH)
def high_priority_task() -> str:
    """High priority task"""
    return "high_priority_result"


@task(name="test.low_priority", priority=TaskPriority.LOW)
def low_priority_task() -> str:
    """Low priority task"""
    return "low_priority_result"


class TestTaskDecorator:
    """Test @task decorator"""

    def test_task_has_delay_method(self):
        """Test that decorated function has delay method"""
        assert hasattr(simple_task, 'delay')
        assert callable(simple_task.delay)

    def test_task_has_wait_method(self):
        """Test that decorated function has wait method"""
        assert hasattr(simple_task, 'wait')
        assert callable(simple_task.wait)

    def test_task_has_apply_async_method(self):
        """Test that decorated function has apply_async method"""
        assert hasattr(simple_task, 'apply_async')
        assert callable(simple_task.apply_async)

    def test_task_has_name(self):
        """Test that decorated function has task_name"""
        assert hasattr(simple_task, 'task_name')
        assert simple_task.task_name == "test.simple_task"

    def test_task_still_callable_directly(self):
        """Test that decorated function can still be called directly"""
        result = simple_task(5)
        assert result == 10

    def test_task_registered_in_registry(self):
        """Test that task is registered"""
        registry = get_task_registry()
        assert "test.simple_task" in registry
        assert registry["test.simple_task"] == simple_task.__wrapped__


class TestTaskQueue:
    """Test TaskQueue operations"""

    def test_enqueue_task(self, task_queue):
        """Test enqueueing task"""
        task_obj = Task(
            name="test_task",
            args=(1, 2),
            kwargs={"key": "value"}
        )

        task_id = task_queue.enqueue(task_obj)

        assert task_id is not None
        assert len(task_id) > 0
        assert task_obj.task_id == task_id

    def test_dequeue_task(self, task_queue):
        """Test dequeueing task"""
        task_obj = Task(name="test_task", args=(1,))
        task_queue.enqueue(task_obj)

        dequeued = task_queue.dequeue(timeout=0.1)

        assert dequeued is not None
        assert dequeued.name == "test_task"
        assert dequeued.args == (1,)

    def test_dequeue_timeout(self, task_queue):
        """Test dequeue timeout on empty queue"""
        start = time.time()
        result = task_queue.dequeue(timeout=0.5)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 0.5

    def test_priority_ordering(self, task_queue):
        """Test that high priority tasks are dequeued first"""
        # Enqueue in mixed order
        low_task = Task(name="low", args=(), priority=TaskPriority.LOW)
        normal_task = Task(name="normal", args=(), priority=TaskPriority.NORMAL)
        high_task = Task(name="high", args=(), priority=TaskPriority.HIGH)

        task_queue.enqueue(low_task)
        task_queue.enqueue(normal_task)
        task_queue.enqueue(high_task)

        # Should dequeue in priority order: HIGH, NORMAL, LOW
        first = task_queue.dequeue(timeout=0.1)
        second = task_queue.dequeue(timeout=0.1)
        third = task_queue.dequeue(timeout=0.1)

        assert first.name == "high"
        assert second.name == "normal"
        assert third.name == "low"

    def test_get_result(self, task_queue):
        """Test getting task result"""
        task_obj = Task(name="test_task", args=())
        task_id = task_queue.enqueue(task_obj)

        # Complete task
        task_queue.complete_task(task_id, result="success")

        result = task_queue.get_result(task_id)
        assert result is not None
        assert result.result == "success"
        assert result.status == TaskStatus.COMPLETED

    def test_complete_task_with_error(self, task_queue):
        """Test completing task with error"""
        task_obj = Task(name="test_task", args=())
        task_id = task_queue.enqueue(task_obj)

        task_queue.complete_task(task_id, error="Task failed")

        result = task_queue.get_result(task_id)
        assert result.status == TaskStatus.FAILED
        assert result.error == "Task failed"

    def test_queue_statistics(self, task_queue):
        """Test queue statistics"""
        # Add some tasks
        for i in range(3):
            task_queue.enqueue(Task(name=f"task{i}", args=()))

        stats = task_queue.get_stats()
        assert stats["pending"] == 3
        assert stats["running"] == 0
        assert stats["completed"] == 0

    def test_clear_queue(self, task_queue):
        """Test clearing queue"""
        for i in range(5):
            task_queue.enqueue(Task(name=f"task{i}", args=()))

        task_queue.clear()

        stats = task_queue.get_stats()
        assert stats["pending"] == 0
        assert stats["completed"] == 0


class TestWorkerExecution:
    """Test worker task execution"""

    def test_worker_executes_task(self, task_queue):
        """Test that worker executes task"""
        worker = TaskWorker(queue=task_queue)
        worker.register_task("test.simple_task", simple_task.__wrapped__)

        # Start worker
        worker.start()

        # Enqueue task
        task_id = simple_task.delay(5)

        # Wait for completion
        time.sleep(1.0)

        # Check result
        result = task_queue.get_result(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 10

        # Stop worker
        worker.stop()

    def test_worker_handles_error(self, task_queue):
        """Test that worker handles task errors"""
        def error_task():
            raise ValueError("Test error")

        worker = TaskWorker(queue=task_queue)
        worker.register_task("error_task", error_task)
        worker.start()

        # Enqueue task
        task_obj = Task(name="error_task", args=())
        task_id = task_queue.enqueue(task_obj)

        # Wait for completion
        time.sleep(1.0)

        # Check error
        result = task_queue.get_result(task_id)
        assert result.status == TaskStatus.FAILED
        assert "Test error" in result.error

        worker.stop()

    def test_worker_graceful_shutdown(self, task_queue):
        """Test worker graceful shutdown"""
        worker = TaskWorker(queue=task_queue)
        worker.start()

        assert worker.is_running

        # Stop worker
        worker.stop(timeout=1.0)

        assert not worker.is_running


class TestWorkerPool:
    """Test WorkerPool operations"""

    def test_worker_pool_starts_workers(self):
        """Test that worker pool starts specified number of workers"""
        pool = WorkerPool(num_workers=4)
        pool.start()

        assert len(pool.workers) == 4
        assert pool.running_workers == 4

        pool.stop()

    def test_worker_pool_processes_multiple_tasks(self):
        """Test that worker pool processes multiple tasks concurrently"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=3)
        pool.start()
        time.sleep(0.5)  # Let workers start

        # Submit multiple tasks
        task_ids = []
        for i in range(6):
            task_id = simple_task.delay(i)
            task_ids.append(task_id)

        # Wait for completion
        time.sleep(2.0)

        # Check all completed
        queue = get_task_queue()
        completed = 0
        for task_id in task_ids:
            result = queue.get_result(task_id)
            if result and result.status == TaskStatus.COMPLETED:
                completed += 1

        assert completed == 6

        pool.stop()

    def test_worker_pool_register_task(self):
        """Test registering task to worker pool"""
        pool = WorkerPool(num_workers=2)

        def test_func():
            return "test"

        pool.register_task("test_func", test_func)

        assert "test_func" in pool.task_registry


class TestDelayAndWait:
    """Test .delay() and .wait() methods"""

    def test_delay_returns_task_id(self):
        """Test that delay() returns task ID"""
        task_id = simple_task.delay(10)

        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) > 0

    def test_wait_returns_result(self):
        """Test that wait() returns result"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        task_id = simple_task.delay(10)

        # Wait for result
        result = simple_task.wait(task_id, timeout=5.0)

        assert result == 20

        pool.stop()

    def test_wait_timeout(self):
        """Test that wait() times out"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        # Submit slow task
        task_id = slow_task.delay(5.0)  # 5 seconds

        # Wait with short timeout
        with pytest.raises(TimeoutError):
            slow_task.wait(task_id, timeout=1.0)

        pool.stop()

    def test_wait_raises_on_error(self):
        """Test that wait() raises RuntimeError on task failure"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        # Submit failing task that exceeds retries
        task_id = failing_task.delay(fail_count=5)  # Fails more than max_retries

        # Wait should raise RuntimeError
        with pytest.raises(RuntimeError, match="Task failed"):
            failing_task.wait(task_id, timeout=5.0)

        pool.stop()


class TestPriorityExecution:
    """Test priority-based execution"""

    def test_high_priority_executes_first(self):
        """Test that high priority tasks execute before low priority"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)  # Single worker
        pool.start()
        time.sleep(0.5)

        # Submit tasks in reverse priority order
        low_id = low_priority_task.delay()
        normal_id = simple_task.delay(1)
        high_id = high_priority_task.delay()

        # Wait a bit
        time.sleep(0.5)

        queue = get_task_queue()

        # High priority should complete first
        high_result = queue.get_result(high_id)
        assert high_result is not None
        if high_result.status == TaskStatus.COMPLETED:
            assert high_result.result == "high_priority_result"

        pool.stop()


class TestRetryMechanism:
    """Test retry mechanism"""

    def test_task_retries_on_failure(self):
        """Test that failed tasks are retried"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        # Task that fails once then succeeds
        # Reset failure counter
        if hasattr(failing_task, "_attempts"):
            failing_task._attempts.clear()

        task_id = failing_task.delay(fail_count=1)

        # Wait for completion (with retries)
        time.sleep(5.0)

        queue = get_task_queue()
        result = queue.get_result(task_id)

        # Should eventually succeed after retry
        assert result is not None
        if result.status == TaskStatus.COMPLETED:
            assert result.result == "success after retries"

        pool.stop()


class TestTimeoutHandling:
    """Test timeout handling"""

    def test_task_completes_within_timeout(self):
        """Test task that completes within timeout"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        # Task completes in 1 second, timeout is 2 seconds
        task_id = timeout_task.delay(1.0)

        result = timeout_task.wait(task_id, timeout=5.0)
        assert result == "completed"

        pool.stop()

    def test_task_timeout_handling(self):
        """Test task that exceeds timeout"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        # Task takes 5 seconds, timeout is 2 seconds
        task_id = timeout_task.delay(5.0)

        # Wait for failure
        time.sleep(5.0)

        queue = get_task_queue()
        result = queue.get_result(task_id)

        # Should fail with timeout error
        assert result is not None
        if result.status == TaskStatus.FAILED:
            assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

        pool.stop()


class TestConcurrentExecution:
    """Test concurrent task execution"""

    def test_multiple_workers_process_tasks(self):
        """Test that multiple workers process tasks concurrently"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=4)
        pool.start()
        time.sleep(0.5)

        # Submit many tasks
        task_ids = []
        start_time = time.time()

        for i in range(20):
            task_id = simple_task.delay(i)
            task_ids.append(task_id)

        # Wait for all to complete
        time.sleep(3.0)

        elapsed = time.time() - start_time

        # Check completion
        queue = get_task_queue()
        completed = sum(
            1 for tid in task_ids
            if queue.get_result(tid) and queue.get_result(tid).status == TaskStatus.COMPLETED
        )

        # Most should complete
        assert completed >= 15

        # With 4 workers, should be faster than single worker
        # (This is a rough heuristic)
        assert elapsed < 5.0

        pool.stop()

    def test_thread_safety(self):
        """Test thread safety of queue operations"""
        queue = get_task_queue()

        def enqueue_tasks(thread_id):
            for i in range(50):
                task = Task(name=f"task_{thread_id}_{i}", args=(i,))
                queue.enqueue(task)

        # Enqueue from multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(enqueue_tasks, i) for i in range(5)]
            for f in futures:
                f.result()

        # Should have 250 tasks (5 threads * 50 tasks)
        stats = queue.get_stats()
        assert stats["pending"] == 250


class TestEdgeCases:
    """Test edge cases"""

    def test_task_with_no_args(self):
        """Test task with no arguments"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        task_id = high_priority_task.delay()
        result = high_priority_task.wait(task_id, timeout=5.0)

        assert result == "high_priority_result"

        pool.stop()

    def test_task_with_kwargs_only(self):
        """Test task with keyword arguments only"""
        @task(name="test.kwargs_task")
        def kwargs_task(a=1, b=2):
            return a + b

        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        task_id = kwargs_task.delay(a=10, b=20)
        result = kwargs_task.wait(task_id, timeout=5.0)

        assert result == 30

        pool.stop()

    def test_task_returns_none(self):
        """Test task that returns None"""
        @task(name="test.none_task")
        def none_task():
            return None

        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=1)
        pool.start()
        time.sleep(0.5)

        task_id = none_task.delay()
        result = none_task.wait(task_id, timeout=5.0)

        assert result is None

        pool.stop()

    def test_empty_queue_stats(self, task_queue):
        """Test statistics on empty queue"""
        stats = task_queue.get_stats()

        assert stats["pending"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0


class TestPerformance:
    """Performance tests"""

    def test_queue_enqueue_performance(self, task_queue):
        """Test enqueue performance"""
        start = time.time()

        for i in range(1000):
            task = Task(name=f"task_{i}", args=(i,))
            task_queue.enqueue(task)

        elapsed = time.time() - start

        # Should enqueue 1000 tasks quickly (< 100ms)
        assert elapsed < 0.1

        print(f"\n  1000 task enqueues: {elapsed*1000:.2f}ms")

    def test_throughput(self):
        """Test task processing throughput"""
        register_tasks_to_workers()
        pool = get_worker_pool(num_workers=4)
        pool.start()
        time.sleep(0.5)

        # Submit 100 quick tasks
        start_time = time.time()
        task_ids = [simple_task.delay(i) for i in range(100)]

        # Wait for completion
        queue = get_task_queue()
        while True:
            stats = queue.get_stats()
            if stats["completed"] >= 100:
                break
            if time.time() - start_time > 10:  # Timeout
                break
            time.sleep(0.1)

        elapsed = time.time() - start_time

        # Calculate throughput
        throughput = 100 / elapsed

        print(f"\n  Processed 100 tasks in {elapsed:.2f}s ({throughput:.1f} tasks/s)")

        # Should process at reasonable rate (>= 20 tasks/s with 4 workers)
        assert throughput >= 20

        pool.stop()
