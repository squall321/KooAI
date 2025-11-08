"""
Basic Usage Example - KooAI Platform

시뮬레이션 파일을 로드하고 기본 분석을 수행하는 간단한 예제
"""

from pathlib import Path
from src.core.simulation.parsers.csv_parser import CSVParser
from src.core.simulation.analysis import FieldAnalyzer

def main():
    # 1. CSV 파일 파싱
    print("📁 시뮬레이션 파일 로드 중...")
    parser = CSVParser()
    simulation = parser.parse(Path("data/sample_simulation.csv"))

    print(f"✅ 로드 완료!")
    print(f"   - 이름: {simulation.name}")
    print(f"   - 타임스텝: {len(simulation.timesteps)}개")
    print(f"   - 필드: {', '.join(simulation.timesteps[0].fields.keys())}")

    # 2. 필드 분석
    print("\n📊 필드 분석 중...")
    analyzer = FieldAnalyzer()

    # 온도 필드 통계
    if simulation.timesteps and "temperature" in simulation.timesteps[0].fields:
        temp_field = simulation.timesteps[0].get_field("temperature")
        stats = analyzer.calculate_statistics(temp_field.data)

        print("\n🌡️ 온도 통계:")
        print(f"   - 평균: {stats.mean:.2f}")
        print(f"   - 최소: {stats.min:.2f}")
        print(f"   - 최대: {stats.max:.2f}")
        print(f"   - 표준편차: {stats.std:.2f}")

        # 극값 찾기
        extremes = analyzer.find_extremes(temp_field.data)
        print(f"\n🔍 극값:")
        print(f"   - 최댓값 위치: {extremes['max_location']}")
        print(f"   - 최솟값 위치: {extremes['min_location']}")

    # 3. 이상치 탐지
    if simulation.timesteps and "pressure" in simulation.timesteps[0].fields:
        pressure_field = simulation.timesteps[0].get_field("pressure")
        outliers = analyzer.detect_outliers(pressure_field.data, threshold=3.0)

        print(f"\n⚠️ 압력 이상치: {len(outliers['indices'])}개 발견")
        if outliers['indices']:
            print(f"   - 위치: {outliers['indices'][:5]}...")  # 처음 5개만

if __name__ == "__main__":
    main()
