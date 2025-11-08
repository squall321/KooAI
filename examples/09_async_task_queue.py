"""
비동기 작업 큐

이 예제는 백그라운드 작업 큐 시스템을 시연합니다.
"""

import time

from src.infrastructure.tasks import (
    TaskPriority,
    get_task_queue,
    get_worker_pool,
    register_tasks_to_workers,
    task,
)


# 작업 함수 정의
@task(name="process_data", priority=TaskPriority.NORMAL, max_retries=3)
def process_data(file_path: str, chunk_size: int = 1000) -> dict:
    """데이터 처리 작업 (시뮬레이션)"""
    print(f"   📊 Processing: {file_path} (chunk_size={chunk_size})")
    time.sleep(2)  # 실제 작업 시뮬레이션
    return {
        "file": file_path,
        "chunks_processed": 10,
        "status": "success",
    }


@task(name="send_email", priority=TaskPriority.HIGH)
def send_email(to: str, subject: str, body: str) -> dict:
    """이메일 전송 작업 (시뮬레이션)"""
    print(f"   📧 Sending email to: {to}")
    print(f"      Subject: {subject}")
    time.sleep(1)
    return {"to": to, "sent_at": time.time(), "status": "delivered"}


@task(name="generate_report", priority=TaskPriority.LOW, timeout=10)
def generate_report(report_type: str) -> dict:
    """리포트 생성 작업 (시뮬레이션)"""
    print(f"   📄 Generating report: {report_type}")
    time.sleep(3)
    return {
        "report_type": report_type,
        "page_count": 25,
        "generated_at": time.time(),
    }


@task(name="failing_task", max_retries=2)
def failing_task(fail_times: int) -> str:
    """실패하는 작업 (재시도 테스트용)"""
    # 전역 카운터 사용 (간단한 예제용)
    global _fail_counter
    if not hasattr(failing_task, "_fail_counter"):
        failing_task._fail_counter = {}

    task_key = f"fail_{fail_times}"
    if task_key not in failing_task._fail_counter:
        failing_task._fail_counter[task_key] = 0

    failing_task._fail_counter[task_key] += 1

    print(f"   ❌ Failing task attempt {failing_task._fail_counter[task_key]}")

    if failing_task._fail_counter[task_key] <= fail_times:
        raise Exception(
            f"Intentional failure (attempt {failing_task._fail_counter[task_key]})"
        )

    print(f"   ✅ Failing task finally succeeded!")
    return "Success after retries"


def example_basic_async():
    """기본 비동기 작업"""
    print("=" * 60)
    print("Example 1: Basic Async Tasks")
    print("=" * 60)

    # 워커 풀 시작
    print("\n1️⃣  Starting worker pool (4 workers)...")
    register_tasks_to_workers()
    worker_pool = get_worker_pool(num_workers=4)
    worker_pool.start()
    time.sleep(0.5)  # 워커 시작 대기

    print(f"   ✅ {worker_pool.running_workers} workers started")

    print("\n2️⃣  Submitting tasks:")

    # 작업 제출
    task_id1 = process_data.delay("/data/file1.csv", chunk_size=500)
    print(f"   Task 1: {task_id1[:8]}... (process_data)")

    task_id2 = send_email.delay(
        "user@example.com", "Report Ready", "Your report is ready!"
    )
    print(f"   Task 2: {task_id2[:8]}... (send_email)")

    task_id3 = generate_report.delay("monthly_sales")
    print(f"   Task 3: {task_id3[:8]}... (generate_report)")

    print("\n3️⃣  Tasks are running in background...")
    print("   (Workers will process these tasks)")
    time.sleep(1)

    print("\n4️⃣  Queue statistics:")
    queue = get_task_queue()
    stats = queue.get_stats()
    print(f"   Pending: {stats['pending']}")
    print(f"   Running: {stats['running']}")
    print(f"   Completed: {stats['completed']}")

    print("\n5️⃣  Waiting for tasks to complete...")
    time.sleep(5)  # 작업 완료 대기

    # 결과 확인
    print("\n6️⃣  Task results:")
    result1 = queue.get_result(task_id1)
    if result1:
        print(f"   Task 1: {result1.status.value} - {result1.result}")

    result2 = queue.get_result(task_id2)
    if result2:
        print(f"   Task 2: {result2.status.value} - {result2.result}")

    result3 = queue.get_result(task_id3)
    if result3:
        print(f"   Task 3: {result3.status.value} - {result3.result}")

    # 워커 정리
    worker_pool.stop()
    queue.clear()
    print()


def example_priority_queue():
    """우선순위 큐"""
    print("=" * 60)
    print("Example 2: Priority Queue")
    print("=" * 60)

    # 워커 풀 시작
    register_tasks_to_workers()
    worker_pool = get_worker_pool(num_workers=2)  # 2개 워커만 사용
    worker_pool.start()
    time.sleep(0.5)

    print("\n1️⃣  Submitting tasks with different priorities:")

    # 낮은 우선순위 작업 3개
    for i in range(3):
        task_id = generate_report.delay(f"report_{i}")
        print(f"   LOW priority: {task_id[:8]}... (generate_report)")

    # 높은 우선순위 작업 1개
    task_id_high = send_email.delay(
        "urgent@example.com", "URGENT", "High priority email"
    )
    print(f"   HIGH priority: {task_id_high[:8]}... (send_email)")

    print(
        "\n2️⃣  High priority task will be processed first, even though it was submitted last"
    )
    time.sleep(8)

    # 워커 정리
    worker_pool.stop()
    get_task_queue().clear()
    print()


def example_wait_for_result():
    """결과 대기"""
    print("=" * 60)
    print("Example 3: Wait for Result (Blocking)")
    print("=" * 60)

    register_tasks_to_workers()
    worker_pool = get_worker_pool(num_workers=2)
    worker_pool.start()
    time.sleep(0.5)

    print("\n1️⃣  Submit task and wait for result:")

    # 작업 제출
    task_id = process_data.delay("/data/important.csv")
    print(f"   Task submitted: {task_id[:8]}...")

    print("\n2️⃣  Waiting for result (blocking)...")

    try:
        # 결과 대기 (최대 10초)
        result = process_data.wait(task_id, timeout=10)
        print(f"   ✅ Result: {result}")
    except TimeoutError:
        print("   ❌ Timeout waiting for result")

    # 워커 정리
    worker_pool.stop()
    get_task_queue().clear()
    print()


def example_retry_mechanism():
    """재시도 메커니즘"""
    print("=" * 60)
    print("Example 4: Retry Mechanism")
    print("=" * 60)

    register_tasks_to_workers()
    worker_pool = get_worker_pool(num_workers=1)
    worker_pool.start()
    time.sleep(0.5)

    print("\n1️⃣  Submit task that will fail twice, then succeed:")

    # 2번 실패 후 성공하는 작업
    task_id = failing_task.delay(fail_times=2)
    print(f"   Task submitted: {task_id[:8]}...")
    print(f"   (max_retries=2)")

    print("\n2️⃣  Watching task execution:")
    time.sleep(8)  # 재시도 대기

    # 결과 확인
    result = get_task_queue().get_result(task_id)
    if result:
        print(f"\n3️⃣  Final result:")
        print(f"   Status: {result.status.value}")
        if result.error:
            print(f"   Error: {result.error}")
        else:
            print(f"   Result: {result.result}")

    # 워커 정리
    worker_pool.stop()
    get_task_queue().clear()
    print()


def example_batch_processing():
    """배치 작업 처리"""
    print("=" * 60)
    print("Example 5: Batch Processing")
    print("=" * 60)

    register_tasks_to_workers()
    worker_pool = get_worker_pool(num_workers=4)
    worker_pool.start()
    time.sleep(0.5)

    print("\n1️⃣  Submitting 10 data processing tasks:")

    task_ids = []
    for i in range(10):
        task_id = process_data.delay(f"/data/batch/file_{i}.csv")
        task_ids.append(task_id)

    print(f"   Submitted {len(task_ids)} tasks")

    print("\n2️⃣  Monitoring progress:")

    start_time = time.time()
    completed = 0

    while completed < len(task_ids):
        queue = get_task_queue()
        stats = queue.get_stats()

        completed = stats["completed"]
        running = stats["running"]
        pending = stats["pending"]

        elapsed = time.time() - start_time

        print(
            f"\r   Completed: {completed}/{len(task_ids)} | "
            f"Running: {running} | "
            f"Pending: {pending} | "
            f"Time: {elapsed:.1f}s",
            end="",
        )

        time.sleep(0.5)

        if elapsed > 30:  # 타임아웃
            break

    print(f"\n\n3️⃣  All tasks completed in {elapsed:.1f} seconds!")

    # 워커 정리
    worker_pool.stop()
    get_task_queue().clear()
    print()


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           비동기 작업 큐 시스템 예제                          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    try:
        # Example 1: 기본 비동기 작업
        example_basic_async()

        # Example 2: 우선순위 큐
        example_priority_queue()

        # Example 3: 결과 대기
        example_wait_for_result()

        # Example 4: 재시도 메커니즘
        example_retry_mechanism()

        # Example 5: 배치 처리
        example_batch_processing()

        print("=" * 60)
        print("✅ 모든 예제 완료!")
        print("=" * 60)
        print()

        print("💡 주요 기능:")
        print("   1. @task 데코레이터로 간편한 작업 등록")
        print("   2. 우선순위 기반 작업 처리")
        print("   3. 백그라운드 워커 풀")
        print("   4. 자동 재시도 메커니즘")
        print("   5. 작업 상태 추적")
        print("   6. .delay() - 비동기 실행")
        print("   7. .wait() - 결과 대기")
        print()

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 정리
        worker_pool = get_worker_pool()
        if worker_pool.running_workers > 0:
            worker_pool.stop()
