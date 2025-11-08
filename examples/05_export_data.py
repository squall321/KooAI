"""
Data Export Example - KooAI Platform

시뮬레이션 데이터를 다양한 형식으로 내보내는 예제
"""

from pathlib import Path
from src.core.simulation.parsers.csv_parser import CSVParser
from src.application.export.exporter import MultiFormatExporter, ExportFormat

def main():
    # 1. 시뮬레이션 로드
    print("📁 시뮬레이션 로드 중...")
    parser = CSVParser()
    simulation = parser.parse(Path("data/sample_simulation.csv"))
    print(f"✅ {simulation.name} 로드 완료")

    # 2. Exporter 생성
    exporter = MultiFormatExporter()
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)

    # 3. JSON 형식으로 내보내기
    print("\n💾 JSON 형식으로 내보내기...")
    exporter.export_simulation_data(
        simulation_data=simulation,
        output_path=output_dir / "simulation.json",
        format=ExportFormat.JSON,
        include_metadata=True
    )
    print("✅ exports/simulation.json 생성 완료")

    # 4. CSV 형식으로 내보내기 (필드 플래팅)
    print("\n💾 CSV 형식으로 내보내기...")
    exporter.export_simulation_data(
        simulation_data=simulation,
        output_path=output_dir / "simulation.csv",
        format=ExportFormat.CSV
    )
    print("✅ exports/simulation.csv 생성 완료")

    # 5. NumPy 형식으로 내보내기
    print("\n💾 NumPy 형식으로 내보내기...")
    exporter.export_simulation_data(
        simulation_data=simulation,
        output_path=output_dir / "simulation.npz",
        format=ExportFormat.NUMPY
    )
    print("✅ exports/simulation.npz 생성 완료")

    # 6. Text 요약 리포트
    print("\n💾 Text 요약 리포트 생성...")
    exporter.export_simulation_data(
        simulation_data=simulation,
        output_path=output_dir / "simulation_summary.txt",
        format=ExportFormat.TEXT
    )
    print("✅ exports/simulation_summary.txt 생성 완료")

    # 7. 분석 결과 내보내기
    print("\n💾 분석 결과 JSON으로 내보내기...")
    analysis_results = {
        "simulation_name": simulation.name,
        "fields_analyzed": list(simulation.timesteps[0].fields.keys()) if simulation.timesteps else [],
        "analysis_date": "2025-11-06",
        "statistics": {
            "temperature": {
                "mean": 273.15,
                "std": 10.5,
                "min": 250.0,
                "max": 300.0
            }
        }
    }

    exporter.export_analysis_results(
        analysis_results=analysis_results,
        output_path=output_dir / "analysis_results.json"
    )
    print("✅ exports/analysis_results.json 생성 완료")

    # 8. NumPy 파일 로드 예제
    print("\n📂 NumPy 파일 다시 로드...")
    import numpy as np
    loaded_data = np.load(output_dir / "simulation.npz")
    print(f"✅ 로드된 필드: {list(loaded_data.keys())}")
    for field_name in loaded_data.keys():
        field_data = loaded_data[field_name]
        print(f"   - {field_name}: shape={field_data.shape}, dtype={field_data.dtype}")

    print("\n" + "="*70)
    print("🎉 모든 내보내기 작업 완료!")
    print(f"📁 출력 디렉토리: {output_dir.absolute()}")
    print("="*70)

if __name__ == "__main__":
    main()
