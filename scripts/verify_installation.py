#!/usr/bin/env python3
"""
KooAI 설치 검증 스크립트

설치된 패키지와 의존성을 확인하고 문제를 진단합니다.
"""

import sys
import importlib
from pathlib import Path
from typing import List, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Python 버전 확인"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (3.11+ 필요)"


def check_package(package_name: str) -> Tuple[bool, str]:
    """패키지 import 가능 여부 확인"""
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, "__version__", "unknown")
        return True, f"✅ {package_name} ({version})"
    except ImportError:
        return False, f"❌ {package_name} (미설치)"
    except Exception as e:
        return False, f"❌ {package_name} (오류: {e})"


def check_files_exist() -> List[Tuple[bool, str]]:
    """필수 파일 존재 확인"""
    required_files = [
        ".env",
        "src/presentation/api/main.py",
        "examples/01_basic_usage.py",
    ]

    optional_files = [
        "data/samples/simple_temperature.csv",
        "data/samples/flow_simulation.csv",
        "data/samples/pressure_field.vtk",
    ]

    results = []

    # 필수 파일
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        results.append((exists, f"{status} {file_path} (필수)"))

    # 선택적 파일
    for file_path in optional_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "⚠️"
        results.append((exists, f"{status} {file_path} (선택)"))

    return results


def main():
    """메인 검증 함수"""
    print("=" * 70)
    print("KooAI 설치 검증")
    print("=" * 70)
    print()

    all_ok = True
    warnings = []

    # Python 버전
    print("📌 Python 버전 확인")
    success, msg = check_python_version()
    print(f"  {msg}")
    if not success:
        print("\n❌ 검증 실패: Python 3.11 이상이 필요합니다.")
        sys.exit(1)
    print()

    # 핵심 패키지
    print("📦 핵심 패키지 확인 (필수)")
    core_packages = [
        "numpy",
        "pandas",
        "scipy",
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "click",
        "rich",
    ]

    for pkg in core_packages:
        success, msg = check_package(pkg)
        print(f"  {msg}")
        if not success:
            all_ok = False
    print()

    # 선택적 패키지
    print("🔧 선택적 패키지 확인")
    optional_packages = [
        ("vtk", "3D 파일 지원 (VTK, VTU)"),
        ("pyvista", "3D 시각화"),
        ("trimesh", "3D 메시 처리"),
        ("torch", "AI/ML 기능 (PyTorch)"),
        ("transformers", "LLM 통합"),
        ("h5py", "HDF5 파서"),
        ("redis", "캐시 지원"),
        ("celery", "비동기 작업"),
    ]

    for pkg, desc in optional_packages:
        success, msg = check_package(pkg)
        print(f"  {msg} - {desc}")
        if not success:
            warnings.append(f"{pkg}: {desc}")
    print()

    # KooAI 모듈 확인
    print("🔍 KooAI 모듈 확인")
    kooai_modules = [
        "src.core.simulation.models",
        "src.application.batch.processor",
        "src.presentation.api.main",
    ]

    for module in kooai_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module} - {e}")
            all_ok = False
    print()

    # 파일 확인
    print("📄 필수 파일 및 샘플 데이터 확인")
    file_results = check_files_exist()
    for success, msg in file_results:
        print(f"  {msg}")
        if "(필수)" in msg and not success:
            all_ok = False
        elif "(선택)" in msg and not success:
            warnings.append(msg.split("(선택)")[0].strip())
    print()

    # 최종 결과
    print("=" * 70)
    if all_ok:
        print("✅ 모든 필수 검증을 통과했습니다!")
        print("=" * 70)

        if warnings:
            print()
            print("⚠️  다음 선택적 기능들이 사용 불가능합니다:")
            for warning in warnings[:5]:  # 최대 5개만 표시
                print(f"  - {warning}")
            if len(warnings) > 5:
                print(f"  ... 외 {len(warnings) - 5}개")
            print()
            print("전체 기능을 사용하려면 다음 명령어로 재설치하세요:")
            print("  ./setup.sh  # 프로파일 선택 시 'full' 선택")

        print()
        print("다음 명령어로 시작하세요:")
        print("  python examples/01_basic_usage.py")
        print()
        sys.exit(0)
    else:
        print("❌ 일부 필수 검증에 실패했습니다.")
        print("=" * 70)
        print()
        print("다음 명령어로 재설치하세요:")
        print("  ./setup.sh     # Linux/macOS")
        print("  setup.bat      # Windows")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
