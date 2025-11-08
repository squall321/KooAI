"""
Simulation Comparison Example - KooAI Platform

두 시뮬레이션을 비교하고 차이를 분석하는 예제
"""

from pathlib import Path
from src.core.simulation.parsers.csv_parser import CSVParser
from src.application.comparison.comparator import SimulationComparator
from src.application.comparison.diff_analyzer import DifferenceAnalyzer

def main():
    # 1. 두 시뮬레이션 로드
    print("📁 시뮬레이션 로드 중...")
    parser = CSVParser()

    sim1 = parser.parse(Path("data/simulation_v1.csv"))
    sim2 = parser.parse(Path("data/simulation_v2.csv"))

    print(f"✅ Simulation 1: {sim1.name}")
    print(f"✅ Simulation 2: {sim2.name}")

    # 2. 시뮬레이션 비교
    print("\n🔍 온도 필드 비교 중...")
    comparator = SimulationComparator()

    comparison = comparator.compare_fields(
        sim1=sim1,
        sim2=sim2,
        field_name="temperature",
        timestep=0
    )

    # 3. 기본 통계 출력
    print("\n📊 비교 결과:")
    print(f"   - RMSE (Root Mean Square Error): {comparison.rmse:.6f}")
    print(f"   - 상관계수: {comparison.correlation:.4f}")
    print(f"   - 평균 차이: {comparison.mean_difference:.6f}")
    print(f"   - 최대 차이: {comparison.max_difference:.6f}")
    print(f"   - 최소 차이: {comparison.min_difference:.6f}")

    # 4. 차이 분석
    print("\n🔬 상세 차이 분석...")
    analyzer = DifferenceAnalyzer()

    field1 = sim1.timesteps[0].get_field("temperature")
    field2 = sim2.timesteps[0].get_field("temperature")

    diff_analysis = analyzer.analyze_field_difference(
        field1.data,
        field2.data,
        "temperature"
    )

    print(f"\n차이 유형: {diff_analysis.difference_type.value}")
    print(f"평균 절대 차이: {diff_analysis.mean_absolute_difference:.6f}")
    print(f"상대 오차: {diff_analysis.relative_error:.2f}%")

    # 5. 이상치 영역 식별
    outlier_regions = analyzer.identify_outlier_regions(
        field1.data,
        field2.data,
        threshold_std=3.0
    )

    if outlier_regions['count'] > 0:
        print(f"\n⚠️ 이상치 영역: {outlier_regions['count']}개 발견")
        print(f"   - 위치: {outlier_regions['indices'][:10]}...")  # 처음 10개

    # 6. 유의미한 차이 식별
    print("\n🎯 유의미한 차이 식별 (임계값: 10%)...")
    significant_diffs = comparator.identify_differences(
        sim1=sim1,
        sim2=sim2,
        field_name="temperature",
        threshold=0.1,  # 10%
        timestep=0
    )

    print(f"유의미한 차이가 있는 점: {significant_diffs['count']}개")
    print(f"비율: {significant_diffs['percentage']:.2f}%")

    # 7. 다중 시뮬레이션 비교 (3개 이상)
    print("\n📈 다중 시뮬레이션 비교...")
    simulations = [sim1, sim2]  # 실제로는 더 많은 시뮬레이션 추가 가능

    multi_comparison = comparator.compare_multiple(
        simulations=simulations,
        field_name="temperature",
        timestep=0
    )

    print(f"비교 시뮬레이션 수: {len(multi_comparison['simulations'])}")
    print(f"평균 RMSE: {multi_comparison['mean_rmse']:.6f}")
    print(f"최대 RMSE: {multi_comparison['max_rmse']:.6f}")

if __name__ == "__main__":
    main()
