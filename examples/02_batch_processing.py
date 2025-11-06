"""
Batch Processing Example - KooAI Platform

여러 시뮬레이션 파일을 병렬로 처리하는 예제
"""

from pathlib import Path
from src.application.batch.processor import BatchProcessor
from src.core.simulation.parsers.csv_parser import CSVParser

def process_simulation(file_path: Path):
    """단일 시뮬레이션 파일 처리"""
    parser = CSVParser()
    try:
        simulation = parser.parse(file_path)
        print(f"✅ {file_path.name} 처리 완료")
        return {
            "file": str(file_path),
            "timesteps": len(simulation.timesteps),
            "fields": list(simulation.timesteps[0].fields.keys()) if simulation.timesteps else []
        }
    except Exception as e:
        print(f"❌ {file_path.name} 처리 실패: {e}")
        raise

def main():
    # 1. BatchProcessor 생성
    processor = BatchProcessor(
        max_workers=4,        # 4개 병렬 워커
        stop_on_error=False,  # 에러 발생 시 계속 진행
        skip_existing=True    # 이미 처리된 파일 스킵
    )

    # 2. 처리할 파일 추가
    data_dir = Path("data/simulations")
    processor.add_directory(
        directory=data_dir,
        pattern="*.csv",
        recursive=True
    )

    print(f"📁 {len(processor.jobs)}개 파일 발견")

    # 3. 진행률 콜백 정의
    def progress_callback(current, total):
        percentage = (current / total) * 100
        print(f"⏳ 진행률: {current}/{total} ({percentage:.1f}%)")

    # 4. 병렬 처리 시작
    print("\n🚀 병렬 처리 시작...")
    result = processor.process_parallel(
        processor_func=process_simulation,
        progress_callback=progress_callback
    )

    # 5. 결과 출력
    print("\n" + "="*50)
    print("📊 배치 처리 결과")
    print("="*50)
    print(f"총 작업: {result.total_jobs}개")
    print(f"✅ 완료: {result.completed}개")
    print(f"❌ 실패: {result.failed}개")
    print(f"성공률: {result.success_rate():.1f}%")
    print(f"총 소요 시간: {result.total_duration:.2f}초")
    print(f"평균 처리 시간: {result.avg_duration:.2f}초")

    # 실패한 작업 출력
    if result.failed > 0:
        print("\n⚠️ 실패한 작업:")
        result_dict = result.to_dict()
        for failed_job in result_dict['failed_jobs']:
            print(f"   - {failed_job['file_path']}: {failed_job['error']}")

if __name__ == "__main__":
    main()
