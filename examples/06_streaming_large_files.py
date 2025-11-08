"""
스트리밍 파서로 대용량 파일 처리

이 예제는 StreamingCSVParser와 StreamingJSONParser를 사용하여
메모리 효율적으로 대용량 시뮬레이션 결과를 처리하는 방법을 보여줍니다.
"""

from pathlib import Path

from src.core.simulation.parsers import (
    ProgressCallback,
    StreamingCSVParser,
    StreamingJSONParser,
)


def progress_handler(processed: int, total: int, percentage: float):
    """진행률 콜백 함수"""
    bar_length = 40
    filled = int(bar_length * percentage / 100)
    bar = "=" * filled + "-" * (bar_length - filled)
    print(f"\rProgress: [{bar}] {percentage:.1f}% ({processed}/{total} bytes)", end="")


def example_streaming_csv():
    """스트리밍 CSV 파서 예제"""
    print("=" * 60)
    print("Example 1: Streaming CSV Parser")
    print("=" * 60)

    # 대용량 CSV 파일 경로
    csv_file = Path("sample_data/large_simulation.csv")

    if not csv_file.exists():
        print(f"⚠️  파일이 없습니다: {csv_file}")
        print("   sample_data/flow_simulation.csv를 사용합니다.")
        csv_file = Path("sample_data/flow_simulation.csv")

    if not csv_file.exists():
        print(f"⚠️  샘플 데이터가 없습니다. scripts/generate_sample_data.py를 실행하세요.")
        return

    # 스트리밍 파서 생성 (청크당 5000행)
    parser = StreamingCSVParser(
        chunk_rows=5000, progress_callback=progress_handler
    )

    print(f"\n📂 파일: {csv_file}")
    print(f"📊 청크 크기: {parser.chunk_rows} 행")
    print()

    # 파싱 시작
    result = parser.parse_stream(csv_file)

    print()  # 진행률 바 다음 줄
    print(f"✅ 파싱 완료!")
    print(f"   이름: {result.name}")
    print(f"   포인트 수: {len(result.mesh.vertices)}")
    print(f"   타임스텝: {len(result.timesteps)}")
    print(f"   필드: {', '.join([f.name for f in result.timesteps[0].fields])}")
    print()


def example_streaming_json():
    """스트리밍 JSON 파서 예제"""
    print("=" * 60)
    print("Example 2: Streaming JSON Parser")
    print("=" * 60)

    # 대용량 JSON 파일 경로
    json_file = Path("sample_data/large_simulation.json")

    if not json_file.exists():
        print(f"⚠️  JSON 샘플 파일이 없습니다.")
        print("   샘플 JSON 파일을 생성합니다...")

        # 간단한 샘플 JSON 생성
        import json
        import numpy as np

        json_file.parent.mkdir(parents=True, exist_ok=True)

        # 10000개 포인트 생성
        n_points = 10000
        data = []

        for i in range(n_points):
            x = i % 100
            y = i // 100
            temperature = 300 + 10 * np.sin(x / 10) * np.cos(y / 10)
            pressure = 101325 + 100 * np.random.randn()

            data.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "z": 0.0,
                    "temperature": float(temperature),
                    "pressure": float(pressure),
                }
            )

        with open(json_file, "w") as f:
            json.dump(data, f)

        print(f"   ✅ 생성 완료: {json_file}")
        print()

    # 스트리밍 파서 생성 (청크당 1000 아이템)
    parser = StreamingJSONParser(chunk_size=1000, progress_callback=progress_handler)

    print(f"📂 파일: {json_file}")
    print(f"📊 청크 크기: {parser.chunk_size} 아이템")
    print()

    # 파싱 시작
    result = parser.parse_stream(json_file, json_path="item")

    print()  # 진행률 바 다음 줄
    print(f"✅ 파싱 완료!")
    print(f"   이름: {result.name}")
    print(f"   포인트 수: {len(result.mesh.vertices)}")
    print(f"   타임스텝: {len(result.timesteps)}")
    print(f"   필드: {', '.join([f.name for f in result.timesteps[0].fields])}")
    print()


def example_memory_comparison():
    """메모리 사용량 비교 예제"""
    print("=" * 60)
    print("Example 3: Memory Usage Comparison")
    print("=" * 60)

    import tracemalloc

    csv_file = Path("sample_data/flow_simulation.csv")

    if not csv_file.exists():
        print(f"⚠️  샘플 데이터가 없습니다.")
        return

    # 1. 기본 CSV 파서 (전체 메모리 로드)
    print("\n1️⃣  기본 CSVParser (전체 로드):")
    from src.core.simulation.parsers import CSVParser

    tracemalloc.start()
    parser1 = CSVParser()
    result1 = parser1.parse(csv_file)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"   현재 메모리: {current / 1024 / 1024:.2f} MB")
    print(f"   최대 메모리: {peak / 1024 / 1024:.2f} MB")

    # 2. 스트리밍 CSV 파서 (청크 단위)
    print("\n2️⃣  StreamingCSVParser (청크 단위):")

    tracemalloc.start()
    parser2 = StreamingCSVParser(chunk_rows=1000)
    result2 = parser2.parse_stream(csv_file)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"   현재 메모리: {current / 1024 / 1024:.2f} MB")
    print(f"   최대 메모리: {peak / 1024 / 1024:.2f} MB")

    print(
        f"\n💡 스트리밍 파서는 대용량 파일(100MB+)에서 더 큰 차이를 보입니다."
    )
    print()


def example_custom_progress():
    """커스텀 진행률 추적 예제"""
    print("=" * 60)
    print("Example 4: Custom Progress Tracking")
    print("=" * 60)

    csv_file = Path("sample_data/flow_simulation.csv")

    if not csv_file.exists():
        print(f"⚠️  샘플 데이터가 없습니다.")
        return

    # 커스텀 진행률 핸들러
    class ProgressTracker:
        def __init__(self):
            self.start_time = None
            self.last_percentage = 0

        def __call__(self, processed: int, total: int, percentage: float):
            import time

            if self.start_time is None:
                self.start_time = time.time()

            # 10% 단위로만 출력
            if int(percentage / 10) > int(self.last_percentage / 10):
                elapsed = time.time() - self.start_time
                rate = processed / elapsed / 1024 / 1024  # MB/s

                print(
                    f"   {percentage:.0f}% 완료 | "
                    f"속도: {rate:.2f} MB/s | "
                    f"경과: {elapsed:.1f}초"
                )

                self.last_percentage = percentage

    tracker = ProgressTracker()
    parser = StreamingCSVParser(chunk_rows=5000, progress_callback=tracker)

    print(f"📂 파일: {csv_file}")
    print("📊 진행 상황:\n")

    result = parser.parse_stream(csv_file)

    print(f"\n✅ 완료! 총 {len(result.mesh.vertices)} 포인트 파싱됨")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         스트리밍 파서 - 대용량 파일 처리 예제                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    try:
        # Example 1: CSV 스트리밍
        example_streaming_csv()

        # Example 2: JSON 스트리밍
        example_streaming_json()

        # Example 3: 메모리 비교
        example_memory_comparison()

        # Example 4: 커스텀 진행률
        example_custom_progress()

        print("=" * 60)
        print("✅ 모든 예제 완료!")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()
