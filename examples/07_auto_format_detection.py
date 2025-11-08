"""
자동 파일 형식 감지

이 예제는 FormatDetector와 AutoFormatParser를 사용하여
파일 확장자에 의존하지 않고 자동으로 형식을 감지하는 방법을 보여줍니다.
"""

from pathlib import Path

from src.core.simulation.parsers import (
    AutoFormatParser,
    FileFormat,
    FormatDetector,
)


def example_format_detection():
    """형식 감지 예제"""
    print("=" * 60)
    print("Example 1: Format Detection")
    print("=" * 60)

    detector = FormatDetector()

    # 샘플 데이터 디렉토리의 파일들 테스트
    sample_dir = Path("sample_data")

    if not sample_dir.exists():
        print(f"⚠️  샘플 데이터 디렉토리가 없습니다: {sample_dir}")
        print("   scripts/generate_sample_data.py를 실행하세요.")
        return

    print(f"\n📂 디렉토리: {sample_dir}\n")

    # 모든 파일 검사
    for file_path in sample_dir.iterdir():
        if not file_path.is_file():
            continue

        print(f"파일: {file_path.name}")

        # 형식 감지
        result = detector.detect(file_path)

        # 결과 출력
        confidence_emoji = "✅" if result.confidence >= 0.8 else "⚠️"
        print(f"  {confidence_emoji} 형식: {result.format.value}")
        print(f"     신뢰도: {result.confidence:.1%}")
        if result.mime_type:
            print(f"     MIME: {result.mime_type}")
        if result.details:
            print(f"     상세: {result.details}")
        print()


def example_wrong_extension():
    """잘못된 확장자 테스트"""
    print("=" * 60)
    print("Example 2: Handling Wrong File Extensions")
    print("=" * 60)

    import shutil

    # CSV 파일을 .txt로 복사
    csv_file = Path("sample_data/simple_temperature.csv")
    wrong_ext_file = Path("sample_data/temperature.txt")

    if not csv_file.exists():
        print(f"⚠️  샘플 파일이 없습니다: {csv_file}")
        return

    # 파일 복사 (잘못된 확장자)
    shutil.copy(csv_file, wrong_ext_file)

    print(f"\n파일: {csv_file.name} → {wrong_ext_file.name} (확장자 변경)\n")

    # FormatDetector는 내용 기반으로 감지
    detector = FormatDetector()

    print("1️⃣  확장자 기반 추측:")
    print(f"   {wrong_ext_file.suffix} → Unknown (TXT는 지원하지 않음)")

    print("\n2️⃣  내용 기반 자동 감지:")
    result = detector.detect(wrong_ext_file)
    print(f"   ✅ 형식: {result.format.value}")
    print(f"   신뢰도: {result.confidence:.1%}")
    print(f"   상세: {result.details}")

    # 파일 삭제
    wrong_ext_file.unlink()
    print(f"\n🗑️  테스트 파일 삭제: {wrong_ext_file.name}")
    print()


def example_auto_parse():
    """AutoFormatParser 사용 예제"""
    print("=" * 60)
    print("Example 3: AutoFormatParser")
    print("=" * 60)

    # 자동 형식 감지 파서
    auto_parser = AutoFormatParser(min_confidence=0.6)

    csv_file = Path("sample_data/simple_temperature.csv")

    if not csv_file.exists():
        print(f"⚠️  샘플 파일이 없습니다: {csv_file}")
        return

    print(f"\n📂 파일: {csv_file}\n")

    # 자동 감지 및 파싱
    print("자동 형식 감지 및 파싱 중...\n")

    result = auto_parser.parse(csv_file)

    print(f"\n✅ 파싱 완료!")
    print(f"   시뮬레이션: {result.name}")
    print(f"   포인트 수: {len(result.mesh.vertices)}")
    print(f"   필드 수: {len(result.timesteps[0].fields)}")
    print(f"   필드: {', '.join([f.name for f in result.timesteps[0].fields])}")
    print()


def example_confidence_threshold():
    """신뢰도 임계값 테스트"""
    print("=" * 60)
    print("Example 4: Confidence Threshold")
    print("=" * 60)

    # 신뢰도 임계값이 높은 파서
    strict_parser = AutoFormatParser(min_confidence=0.9)

    # 신뢰도 임계값이 낮은 파서
    lenient_parser = AutoFormatParser(min_confidence=0.5)

    csv_file = Path("sample_data/simple_temperature.csv")

    if not csv_file.exists():
        print(f"⚠️  샘플 파일이 없습니다.")
        return

    print(f"\n파일: {csv_file}\n")

    # 1. 엄격한 파서 (신뢰도 >= 90%)
    print("1️⃣  Strict parser (min_confidence=0.9):")
    try:
        result1 = strict_parser.parse(csv_file)
        print(f"   ✅ 파싱 성공")
    except ValueError as e:
        print(f"   ❌ 파싱 실패: {e}")

    print()

    # 2. 관대한 파서 (신뢰도 >= 50%)
    print("2️⃣  Lenient parser (min_confidence=0.5):")
    try:
        result2 = lenient_parser.parse(csv_file)
        print(f"   ✅ 파싱 성공")
    except ValueError as e:
        print(f"   ❌ 파싱 실패: {e}")

    print()


def example_batch_detection():
    """배치 파일 형식 감지"""
    print("=" * 60)
    print("Example 5: Batch Format Detection")
    print("=" * 60)

    detector = FormatDetector()
    sample_dir = Path("sample_data")

    if not sample_dir.exists():
        print(f"⚠️  샘플 데이터 디렉토리가 없습니다.")
        return

    # 형식별로 분류
    by_format = {}

    print(f"\n📂 디렉토리: {sample_dir}\n")
    print("파일 검사 중...\n")

    for file_path in sample_dir.iterdir():
        if not file_path.is_file():
            continue

        result = detector.detect(file_path)

        if result.format not in by_format:
            by_format[result.format] = []

        by_format[result.format].append(
            {
                "file": file_path.name,
                "confidence": result.confidence,
            }
        )

    # 결과 출력
    print("형식별 분류 결과:\n")

    for file_format, files in sorted(by_format.items(), key=lambda x: x[0].value):
        print(f"📁 {file_format.value.upper()}:")

        for file_info in files:
            confidence_bar = "█" * int(file_info["confidence"] * 10)
            print(
                f"   • {file_info['file']:<30} "
                f"[{confidence_bar:<10}] {file_info['confidence']:.1%}"
            )

        print()


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           자동 파일 형식 감지 예제                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    try:
        # Example 1: 기본 형식 감지
        example_format_detection()

        # Example 2: 잘못된 확장자 처리
        example_wrong_extension()

        # Example 3: 자동 파서
        example_auto_parse()

        # Example 4: 신뢰도 임계값
        example_confidence_threshold()

        # Example 5: 배치 감지
        example_batch_detection()

        print("=" * 60)
        print("✅ 모든 예제 완료!")
        print("=" * 60)
        print()

        print("💡 주요 기능:")
        print("   1. Magic bytes 기반 형식 감지 (신뢰도 95%)")
        print("   2. 파일 헤더 분석 (신뢰도 70-90%)")
        print("   3. MIME 타입 추론 (신뢰도 60%)")
        print("   4. 확장자 기반 추측 (신뢰도 50%)")
        print("   5. 다중 감지 방법 조합으로 최적 결과 선택")
        print()

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()
