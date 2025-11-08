"""
Report Generation Example - KooAI Platform

분석 결과를 다양한 형식의 리포트로 생성하는 예제
"""

from pathlib import Path
from src.application.reporting.generator import ReportGenerator
from src.core.simulation.parsers.csv_parser import CSVParser
from src.core.simulation.analysis import FieldAnalyzer

def main():
    # 1. 시뮬레이션 로드 및 분석
    print("📁 시뮬레이션 분석 중...")
    parser = CSVParser()
    simulation = parser.parse(Path("data/sample_simulation.csv"))

    analyzer = FieldAnalyzer()
    temp_field = simulation.timesteps[0].get_field("temperature")
    temp_stats = analyzer.calculate_statistics(temp_field.data)

    # 2. 리포트 생성기 초기화
    report = ReportGenerator(title="시뮬레이션 분석 리포트")

    # 3. 시뮬레이션 요약 섹션 추가
    report.add_summary(
        simulation_name=simulation.name,
        simulation_id=simulation.id or "N/A",
        num_vertices=len(temp_field.data),
        num_fields=len(simulation.timesteps[0].fields),
        field_names=list(simulation.timesteps[0].fields.keys())
    )

    # 4. 통계 테이블 추가
    stats_dict = {
        "mean": temp_stats.mean,
        "min": temp_stats.min,
        "max": temp_stats.max,
        "std": temp_stats.std,
        "median": temp_stats.percentiles.get(50, 0),
    }

    report.add_statistics_table("temperature", stats_dict)

    # 5. 배치 처리 결과 추가 (예시)
    batch_results = {
        "total_jobs": 10,
        "completed": 9,
        "failed": 1,
        "success_rate": 90.0,
        "total_duration": 45.5,
        "avg_duration": 4.55,
        "failed_jobs": [
            {"file_path": "data/failed_sim.csv", "error": "Parse error"}
        ]
    }

    report.add_batch_results(batch_results)

    # 6. 커스텀 섹션 추가
    custom_data = {
        "analysis_date": "2025-11-06",
        "analyst": "KooAI System",
        "notes": "자동 생성된 리포트입니다."
    }

    def format_custom(data):
        return f"""
**분석 일자**: {data['analysis_date']}
**분석자**: {data['analyst']}

*{data['notes']}*
"""

    report.add_custom_section(
        "분석 메타데이터",
        custom_data,
        format_func=format_custom
    )

    # 7. 다양한 형식으로 저장
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    print("\n💾 리포트 저장 중...")

    # Markdown
    report.save(output_dir / "report.md", format="markdown")
    print("✅ Markdown 리포트: reports/report.md")

    # HTML
    report.save(output_dir / "report.html", format="html")
    print("✅ HTML 리포트: reports/report.html")

    # Plain Text
    report.save(output_dir / "report.txt", format="text")
    print("✅ Text 리포트: reports/report.txt")

    # 8. 리포트 내용 미리보기
    print("\n" + "="*70)
    print("📄 리포트 미리보기 (Markdown)")
    print("="*70)
    preview = report.generate_markdown()
    print(preview[:500] + "...\n")  # 처음 500자만 출력

if __name__ == "__main__":
    main()
