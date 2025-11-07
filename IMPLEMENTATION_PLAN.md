# KooAI 사용성 개선 구체적 실행 계획

**작성일**: 2025-11-07
**목표**: 테스트 통과 상태에서 실제 사용 가능한 상태로 전환
**예상 기간**: 2-3주 (20-25시간)
**환경**: Apptainer 기반, 가상환경 자동 설정

---

## 📋 목차

1. [현재 상태 분석](#현재-상태-분석)
2. [Phase 1: 즉시 사용 가능하게 (Week 1)](#phase-1-즉시-사용-가능하게-week-1)
3. [Phase 2: 프로덕션 준비 (Week 2)](#phase-2-프로덕션-준비-week-2)
4. [Phase 3: 품질 향상 (Week 3)](#phase-3-품질-향상-week-3)
5. [자동화 스크립트 상세 설계](#자동화-스크립트-상세-설계)
6. [Apptainer 구성 상세](#apptainer-구성-상세)
7. [검증 체크리스트](#검증-체크리스트)

---

## 🔍 현재 상태 분석

### 프로젝트 구조
```
KooAI/
├── src/                    # 소스 코드 (잘 구조화됨)
├── tests/                  # 테스트 (550개 통과)
├── examples/               # 예제 (실행 불가 ❌)
├── alembic/               # DB 마이그레이션 (설정됨)
├── pyproject.toml         # 의존성 정의 (재구성 필요)
├── docker-compose.yml     # Docker 설정 (Apptainer로 전환)
├── Dockerfile            # Docker 이미지 (Apptainer로 전환)
└── .env.example          # 환경 변수 예시 (수정 필요)
```

### 의존성 현황
```python
# 필수 의존성 (현재 모두 required)
- 경량: numpy, pandas, scipy, fastapi (< 500MB)
- 중량: vtk, pyvista, trimesh (~500MB)
- 초중량: torch, transformers (~2.5GB)

# 문제: 모두 필수로 설정됨
# 해결: optional-dependencies로 재구성 필요
```

### 주요 문제점 (우선순위별)

**🔴 Critical (사용 불가)**
1. 패키지 미설치로 import 실패
2. 샘플 데이터 부재
3. 환경 변수 불일치
4. 설치 가이드 부재

**🟠 High (프로덕션 불가)**
5. Dockerfile 의존성 불완전
6. Heavy 의존성 필수 설정
7. API 보안 취약
8. 예외 처리 부재

**🟡 Medium (개선 필요)**
9. DB 마이그레이션 가이드 없음
10. 통합 테스트 부재
11. 로깅 설정 미비
12. CLI 문서화 부족

---

## 🚀 Phase 1: 즉시 사용 가능하게 (Week 1)

**목표**: 사용자가 git clone 후 5분 안에 예제 실행 가능
**예상 시간**: 4.5시간
**완료 기준**: `python examples/01_basic_usage.py` 성공

### Task 1.1: 자동 셋업 스크립트 작성 (1시간)

#### 1.1.1 기본 셋업 스크립트 - `setup.sh`

**목적**: 가상환경 생성 + 패키지 설치 자동화

**구현 내용**:
```bash
#!/bin/bash
# setup.sh - KooAI 자동 설치 스크립트

set -e  # 에러 발생 시 중단

echo "🚀 KooAI 설치를 시작합니다..."

# 1. Python 버전 확인
echo "📌 Python 버전 확인 중..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.11 이상이 필요합니다. 현재: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION 확인 완료"

# 2. 가상환경 존재 확인 및 생성
if [ -d "venv" ]; then
    echo "⚠️  기존 가상환경(venv)이 발견되었습니다."
    read -p "삭제하고 새로 만드시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  기존 가상환경 삭제 중..."
        rm -rf venv
    else
        echo "기존 가상환경을 사용합니다."
    fi
fi

if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
fi

# 3. 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source venv/bin/activate

# 4. pip 업그레이드
echo "📦 pip 업그레이드 중..."
pip install --upgrade pip setuptools wheel

# 5. 설치 프로파일 선택
echo ""
echo "설치 프로파일을 선택하세요:"
echo "  1) minimal  - 기본 기능만 (CSV 파싱, 통계 분석) [~300MB, 5분]"
echo "  2) standard - 3D 파일 지원 추가 (VTK, VTU) [~800MB, 10분]"
echo "  3) full     - AI 기능 포함 전체 설치 [~3.5GB, 20분]"
echo "  4) dev      - 개발 환경 (테스트, 린터 포함) [~4GB, 25분]"
echo ""
read -p "선택 (1-4) [기본값: 2]: " PROFILE
PROFILE=${PROFILE:-2}

case $PROFILE in
    1)
        echo "📦 Minimal 프로파일 설치 중..."
        pip install -e ".[minimal]"
        ;;
    2)
        echo "📦 Standard 프로파일 설치 중..."
        pip install -e ".[standard]"
        ;;
    3)
        echo "📦 Full 프로파일 설치 중..."
        echo "⚠️  이 작업은 20분 정도 소요됩니다..."
        pip install -e ".[full]"
        ;;
    4)
        echo "📦 Development 프로파일 설치 중..."
        echo "⚠️  이 작업은 25분 정도 소요됩니다..."
        pip install -e ".[dev,full]"
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

# 6. 환경 설정 파일 생성
if [ ! -f ".env" ]; then
    echo "⚙️  .env 파일 생성 중..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다. 필요시 편집하세요."
fi

# 7. 샘플 데이터 생성
echo "📊 샘플 데이터 생성 중..."
python scripts/generate_sample_data.py

# 8. 설치 완료
echo ""
echo "✅ 설치가 완료되었습니다!"
echo ""
echo "다음 명령어로 시작하세요:"
echo "  source venv/bin/activate"
echo "  python examples/01_basic_usage.py"
echo ""
echo "API 서버 시작:"
echo "  uvicorn src.presentation.api.main:app --reload"
echo ""
```

**파일 위치**: `/KooAI/setup.sh`

#### 1.1.2 Windows 셋업 스크립트 - `setup.bat`

```batch
@echo off
REM setup.bat - KooAI Windows 자동 설치 스크립트

echo 🚀 KooAI 설치를 시작합니다...

REM Python 버전 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    exit /b 1
)

REM 가상환경 생성
if exist venv (
    echo ⚠️ 기존 가상환경이 발견되었습니다.
    set /p REPLY="삭제하고 새로 만드시겠습니까? (y/N): "
    if /i "%REPLY%"=="y" (
        echo 🗑️ 기존 가상환경 삭제 중...
        rmdir /s /q venv
    )
)

if not exist venv (
    echo 📦 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM pip 업그레이드
echo 📦 pip 업그레이드 중...
python -m pip install --upgrade pip setuptools wheel

REM 설치 프로파일 선택
echo.
echo 설치 프로파일을 선택하세요:
echo   1) minimal  - 기본 기능만
echo   2) standard - 3D 파일 지원 추가
echo   3) full     - AI 기능 포함 전체 설치
echo   4) dev      - 개발 환경
echo.
set /p PROFILE="선택 (1-4) [기본값: 2]: "
if "%PROFILE%"=="" set PROFILE=2

if "%PROFILE%"=="1" (
    pip install -e ".[minimal]"
) else if "%PROFILE%"=="2" (
    pip install -e ".[standard]"
) else if "%PROFILE%"=="3" (
    pip install -e ".[full]"
) else if "%PROFILE%"=="4" (
    pip install -e ".[dev,full]"
)

REM 환경 설정
if not exist .env (
    copy .env.example .env
)

REM 샘플 데이터 생성
python scripts\generate_sample_data.py

echo.
echo ✅ 설치가 완료되었습니다!
echo.
echo 다음 명령어로 시작하세요:
echo   venv\Scripts\activate
echo   python examples\01_basic_usage.py
```

**파일 위치**: `/KooAI/setup.bat`

#### 1.1.3 검증 스크립트 - `scripts/verify_installation.py`

```python
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
        return False, f"❌ Python {version.major}.{version.minor} (3.11+ 필요)"


def check_package(package_name: str) -> Tuple[bool, str]:
    """패키지 import 가능 여부 확인"""
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, "__version__", "unknown")
        return True, f"✅ {package_name} ({version})"
    except ImportError:
        return False, f"❌ {package_name} (미설치)"


def check_files_exist() -> List[Tuple[bool, str]]:
    """필수 파일 존재 확인"""
    required_files = [
        ".env",
        "data/samples/simple_temperature.csv",
        "src/presentation/api/main.py",
        "examples/01_basic_usage.py",
    ]

    results = []
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        results.append((exists, f"{status} {file_path}"))

    return results


def main():
    """메인 검증 함수"""
    print("=" * 60)
    print("KooAI 설치 검증")
    print("=" * 60)
    print()

    # Python 버전
    print("📌 Python 버전 확인")
    success, msg = check_python_version()
    print(f"  {msg}")
    if not success:
        print("\n❌ 검증 실패: Python 3.11 이상이 필요합니다.")
        sys.exit(1)
    print()

    # 핵심 패키지
    print("📦 핵심 패키지 확인")
    core_packages = [
        "numpy",
        "pandas",
        "scipy",
        "fastapi",
        "pydantic",
        "sqlalchemy",
    ]

    all_ok = True
    for pkg in core_packages:
        success, msg = check_package(pkg)
        print(f"  {msg}")
        if not success:
            all_ok = False
    print()

    # 선택적 패키지
    print("🔧 선택적 패키지 확인")
    optional_packages = [
        ("vtk", "3D 파일 지원"),
        ("pyvista", "3D 시각화"),
        ("torch", "AI/ML 기능"),
        ("transformers", "LLM 통합"),
    ]

    for pkg, desc in optional_packages:
        success, msg = check_package(pkg)
        print(f"  {msg} - {desc}")
    print()

    # 파일 확인
    print("📄 필수 파일 확인")
    file_results = check_files_exist()
    for success, msg in file_results:
        print(f"  {msg}")
        if not success:
            all_ok = False
    print()

    # 최종 결과
    print("=" * 60)
    if all_ok:
        print("✅ 모든 검증을 통과했습니다!")
        print()
        print("다음 명령어로 시작하세요:")
        print("  python examples/01_basic_usage.py")
        sys.exit(0)
    else:
        print("❌ 일부 검증에 실패했습니다.")
        print()
        print("다음 명령어로 재설치하세요:")
        print("  ./setup.sh")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**파일 위치**: `/KooAI/scripts/verify_installation.py`

---

### Task 1.2: pyproject.toml 재구성 (30분)

#### 1.2.1 의존성 프로파일 재구성

**현재 문제**:
- 모든 패키지가 필수 (torch 2GB 포함)
- 경량 사용 불가

**재구성 방안**:

```toml
[project]
name = "kooai"
version = "0.1.0"
description = "AI-powered simulation post-processing analysis platform"
requires-python = ">=3.11"

# 최소 필수 의존성만 포함 (경량)
dependencies = [
    # Core
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",

    # Web Framework
    "fastapi>=0.108.0",
    "uvicorn[standard]>=0.25.0",
    "python-multipart>=0.0.6",

    # Data Processing (경량)
    "numpy>=1.26.0",
    "pandas>=2.1.0",
    "scipy>=1.11.0",

    # Database (기본)
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.13.0",

    # Utilities
    "aiofiles>=23.2.0",
    "httpx>=0.25.0",
    "structlog>=23.2.0",
    "click>=8.1.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
# Minimal: 기본 설치 (위의 dependencies만 사용)
minimal = []

# Standard: 3D 파일 + 데이터베이스 완전 지원
standard = [
    "vtk>=9.3.0",
    "pyvista>=0.43.0",
    "trimesh>=4.0.0",
    "shapely>=2.0.0",
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.9",
    "redis[hiredis]>=5.0.1",
]

# AI/ML 기능
ai = [
    "torch>=2.1.0",
    "transformers>=4.36.0",
    "scikit-learn>=1.3.0",
    "optuna>=3.5.0",
]

# Database extras
database = [
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.9",
    "pgvector>=0.2.4",
]

# Cache
cache = [
    "redis[hiredis]>=5.0.1",
]

# Authentication
auth = [
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
]

# Task queue
tasks = [
    "celery[redis]>=5.3.0",
]

# HDF5 파서
parsers = [
    "h5py>=3.9.0",
]

# Storage (S3, MinIO)
storage = [
    "aioboto3>=12.0.0",
]

# Monitoring
monitoring = [
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.21.0",
    "opentelemetry-sdk>=1.21.0",
    "opentelemetry-instrumentation-fastapi>=0.42b0",
]

# Development
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "black>=23.12.0",
    "ruff>=0.1.9",
    "mypy>=1.7.0",
    "isort>=5.13.0",
]

# Full installation (standard + AI)
full = [
    "kooai[standard,ai,database,cache,auth,tasks,parsers,storage,monitoring]",
]

# All (including dev)
all = [
    "kooai[full,dev]",
]
```

**변경 사항**:
1. **dependencies**: 300MB 이하 경량 패키지만
2. **minimal**: 추가 설치 없음 (dependencies만)
3. **standard**: VTK + DB 완전 지원 (~800MB)
4. **full**: AI 포함 전체 (~3.5GB)
5. **dev**: 개발 도구 포함

**파일 위치**: `/KooAI/pyproject.toml` (수정)

---

### Task 1.3: 샘플 데이터 생성 스크립트 (30분)

#### 1.3.1 샘플 데이터 생성 - `scripts/generate_sample_data.py`

```python
#!/usr/bin/env python3
"""
샘플 시뮬레이션 데이터 생성 스크립트

예제 실행을 위한 다양한 형식의 샘플 데이터를 생성합니다.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_csv(output_path: Path):
    """
    CSV 형식 샘플 데이터 생성

    시뮬레이션: 2D 열전달 문제
    """
    logger.info(f"Creating CSV sample: {output_path}")

    # 10x10 그리드, 5 타임스텝
    n_points = 100
    n_timesteps = 5

    data = []
    for t in range(n_timesteps):
        for i in range(n_points):
            x = (i % 10) * 0.1
            y = (i // 10) * 0.1

            # 시간에 따라 변하는 온도 분포
            temperature = 300 + 50 * np.sin(np.pi * x) * np.sin(np.pi * y) * (1 + 0.1 * t)
            pressure = 101325 + 1000 * np.cos(np.pi * x) * np.cos(np.pi * y)
            velocity_x = 0.1 * np.sin(2 * np.pi * x)
            velocity_y = 0.1 * np.cos(2 * np.pi * y)

            data.append({
                'timestep': t,
                'point_id': i,
                'x': x,
                'y': y,
                'z': 0.0,
                'temperature': temperature,
                'pressure': pressure,
                'velocity_x': velocity_x,
                'velocity_y': velocity_y,
                'velocity_z': 0.0,
            })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"✅ Created: {output_path} ({len(df)} rows)")


def create_large_csv(output_path: Path):
    """대용량 CSV 샘플 (배치 처리 테스트용)"""
    logger.info(f"Creating large CSV sample: {output_path}")

    n_points = 10000
    n_timesteps = 10

    data = []
    for t in range(n_timesteps):
        for i in range(n_points):
            x = np.random.random()
            y = np.random.random()
            z = np.random.random()

            temperature = 300 + 50 * np.random.random()
            pressure = 101325 + 1000 * np.random.randn()

            data.append({
                'timestep': t,
                'point_id': i,
                'x': x,
                'y': y,
                'z': z,
                'temperature': temperature,
                'pressure': pressure,
            })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"✅ Created: {output_path} ({len(df)} rows, ~{output_path.stat().st_size / 1024 / 1024:.1f} MB)")


def create_vtk_ascii(output_path: Path):
    """
    VTK Legacy ASCII 형식 샘플 생성
    """
    logger.info(f"Creating VTK sample: {output_path}")

    # 5x5x5 structured grid
    nx, ny, nz = 5, 5, 5
    n_points = nx * ny * nz

    with open(output_path, 'w') as f:
        # Header
        f.write("# vtk DataFile Version 3.0\n")
        f.write("Sample 3D structured grid\n")
        f.write("ASCII\n")
        f.write("DATASET STRUCTURED_POINTS\n")
        f.write(f"DIMENSIONS {nx} {ny} {nz}\n")
        f.write("ORIGIN 0.0 0.0 0.0\n")
        f.write("SPACING 0.1 0.1 0.1\n")
        f.write(f"POINT_DATA {n_points}\n")

        # Temperature field (scalar)
        f.write("SCALARS temperature float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    x, y, z = i * 0.1, j * 0.1, k * 0.1
                    temp = 300 + 50 * np.sin(np.pi * x) * np.sin(np.pi * y) * np.sin(np.pi * z)
                    f.write(f"{temp:.6f}\n")

        # Velocity field (vector)
        f.write("VECTORS velocity float\n")
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    x, y, z = i * 0.1, j * 0.1, k * 0.1
                    vx = 0.1 * np.sin(2 * np.pi * x)
                    vy = 0.1 * np.cos(2 * np.pi * y)
                    vz = 0.05 * np.sin(np.pi * z)
                    f.write(f"{vx:.6f} {vy:.6f} {vz:.6f}\n")

    logger.info(f"✅ Created: {output_path}")


def create_readme(output_dir: Path):
    """샘플 데이터 설명 README"""
    readme_content = """# 샘플 시뮬레이션 데이터

이 디렉토리는 KooAI 예제 실행을 위한 샘플 데이터를 포함합니다.

## 파일 설명

### simple_temperature.csv
- **형식**: CSV
- **크기**: ~50KB
- **설명**: 2D 열전달 시뮬레이션 결과
- **타임스텝**: 5개
- **포인트 수**: 100개 (10x10 그리드)
- **필드**: temperature, pressure, velocity (x, y, z)
- **용도**: 기본 사용 예제 (`01_basic_usage.py`)

### flow_simulation.csv
- **형식**: CSV
- **크기**: ~15MB
- **설명**: 대용량 유동 시뮬레이션
- **타임스텝**: 10개
- **포인트 수**: 10,000개
- **필드**: temperature, pressure
- **용도**: 배치 처리 예제 (`02_batch_processing.py`)

### pressure_field.vtk
- **형식**: VTK Legacy ASCII
- **크기**: ~100KB
- **설명**: 3D 구조 격자 데이터
- **차원**: 5x5x5
- **필드**: temperature (scalar), velocity (vector)
- **용도**: VTK 파싱 테스트

## 재생성 방법

샘플 데이터를 다시 생성하려면:

```bash
python scripts/generate_sample_data.py
```

## 커스텀 데이터

자신의 시뮬레이션 데이터를 사용하려면:

1. CSV 형식의 경우:
   - `timestep`, `point_id`, `x`, `y`, `z` 컬럼 필수
   - 분석할 필드 컬럼 추가 (예: `temperature`, `pressure`)

2. VTK 형식의 경우:
   - VTK Legacy ASCII 또는 VTK XML (VTU) 지원
   - STRUCTURED_POINTS, POLYDATA, UNSTRUCTURED_GRID 지원

3. 예제 코드에서 파일 경로 수정:
   ```python
   simulation = parser.parse(Path("your_data.csv"))
   ```
"""

    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content)
    logger.info(f"✅ Created: {readme_path}")


def main():
    """메인 함수"""
    # 출력 디렉토리 생성
    data_dir = Path("data")
    samples_dir = data_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("샘플 데이터 생성 시작")
    logger.info("=" * 60)

    try:
        # CSV 샘플
        create_sample_csv(samples_dir / "simple_temperature.csv")
        create_large_csv(samples_dir / "flow_simulation.csv")

        # VTK 샘플
        create_vtk_ascii(samples_dir / "pressure_field.vtk")

        # README
        create_readme(samples_dir)

        logger.info("=" * 60)
        logger.info("✅ 모든 샘플 데이터 생성 완료!")
        logger.info("=" * 60)
        logger.info(f"위치: {samples_dir.absolute()}")

    except Exception as e:
        logger.error(f"❌ 샘플 데이터 생성 실패: {e}")
        raise


if __name__ == "__main__":
    main()
```

**파일 위치**: `/KooAI/scripts/generate_sample_data.py`

---

### Task 1.4: 환경 변수 통일 (2시간)

#### 1.4.1 DatabaseConfig 수정 - `src/infrastructure/database/config.py`

**변경 내용**: `DATABASE_URL` 환경 변수 우선 지원

```python
"""
데이터베이스 설정 관리
"""

import os
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache
from urllib.parse import urlparse


@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""

    host: str = "localhost"
    port: int = 5432
    database: str = "kooai"
    user: str = "kooai"
    password: str = "kooai"

    pool_size: int = 20
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_recycle: int = 3600

    echo: bool = False
    echo_pool: bool = False
    use_test_db: bool = False

    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL 생성"""
        if self.use_test_db:
            return "sqlite+aiosqlite:///:memory:"

        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def sync_database_url(self) -> str:
        """동기 데이터베이스 연결 URL (Alembic용)"""
        if self.use_test_db:
            return "sqlite:///:memory:"

        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        환경 변수로부터 설정 로드

        우선순위:
        1. DATABASE_URL (전체 URL)
        2. DB_HOST, DB_PORT 등 (개별 변수)
        """
        # 1. DATABASE_URL 우선 확인
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return cls._from_url(database_url)

        # 2. 개별 환경 변수 사용
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "kooai"),
            user=os.getenv("DB_USER", "kooai"),
            password=os.getenv("DB_PASSWORD", "kooai"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            echo_pool=os.getenv("DB_ECHO_POOL", "false").lower() == "true",
            use_test_db=os.getenv("USE_TEST_DB", "false").lower() == "true",
        )

    @classmethod
    def _from_url(cls, url: str) -> "DatabaseConfig":
        """DATABASE_URL 파싱"""
        parsed = urlparse(url)

        # PostgreSQL URL 파싱
        if parsed.scheme in ["postgresql", "postgres"]:
            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/"),
                user=parsed.username or "kooai",
                password=parsed.password or "kooai",
            )

        # SQLite
        elif parsed.scheme == "sqlite":
            return cls(use_test_db=True)

        else:
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")


@lru_cache()
def get_database_config() -> DatabaseConfig:
    """데이터베이스 설정 가져오기 (캐시됨)"""
    return DatabaseConfig.from_env()
```

**변경 사항**:
1. `DATABASE_URL` 환경 변수 우선 지원
2. URL 파싱 로직 추가 (`_from_url`)
3. 하위 호환성 유지 (개별 변수도 지원)

**파일 위치**: `/KooAI/src/infrastructure/database/config.py` (수정)

#### 1.4.2 CacheConfig 수정 - `src/infrastructure/cache/config.py`

**변경 내용**: `REDIS_URL` 환경 변수 지원

```python
"""
Cache configuration
"""

from typing import Optional
from pydantic import Field, ConfigDict, field_validator
from pydantic_settings import BaseSettings
import os


class CacheConfig(BaseSettings):
    """Cache 설정"""

    # Redis connection - REDIS_URL 또는 개별 변수 사용
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (우선순위 높음)",
    )
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=1, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis")

    # ... (나머지 설정 동일)

    @field_validator("redis_url", mode="before")
    @classmethod
    def check_redis_url(cls, v):
        """REDIS_URL 환경 변수 확인"""
        if v is None:
            # REDIS_URL 환경 변수 확인
            v = os.getenv("REDIS_URL")
        return v

    def get_redis_url(self) -> str:
        """실제 사용할 Redis URL 반환"""
        if self.redis_url:
            return self.redis_url

        # 개별 변수로 URL 구성
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = ConfigDict(
        env_prefix="",  # prefix 제거 (REDIS_URL, CACHE_REDIS_URL 모두 지원)
        case_sensitive=False,
    )
```

**파일 위치**: `/KooAI/src/infrastructure/cache/config.py` (수정)

#### 1.4.3 .env.example 업데이트

```bash
# KooAI 환경 설정

#############################################
# 데이터베이스 설정 (Database)
#############################################

# 방법 1: DATABASE_URL 사용 (권장 - Docker/Apptainer)
DATABASE_URL=postgresql://kooai:changeme_password@localhost:5432/kooai

# 방법 2: 개별 변수 사용 (로컬 개발)
# DATABASE_URL이 설정되면 아래 변수들은 무시됩니다
#DB_HOST=localhost
#DB_PORT=5432
#DB_NAME=kooai
#DB_USER=kooai
#DB_PASSWORD=changeme_password

# 연결 풀 설정
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600

# 디버깅
DB_ECHO=false
DB_ECHO_POOL=false

# 테스트 모드 (SQLite in-memory)
USE_TEST_DB=false

#############################################
# Redis/Cache 설정
#############################################

# 방법 1: REDIS_URL 사용 (권장)
REDIS_URL=redis://localhost:6379/1

# 방법 2: 개별 변수 사용
# REDIS_URL이 설정되면 아래 변수들은 무시됩니다
#REDIS_HOST=localhost
#REDIS_PORT=6379
#REDIS_DB=1
#REDIS_PASSWORD=

# Cache TTL 설정
CACHE_DEFAULT_TTL=3600
CACHE_ANALYSIS_TTL=86400

#############################################
# 애플리케이션 설정
#############################################

KOOAI_ENV=development
DEBUG=true
LOG_LEVEL=INFO
LOG_FILE=logs/kooai.log

#############################################
# API 설정
#############################################

API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS (프로덕션에서는 특정 도메인으로 제한)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

#############################################
# 보안 설정
#############################################

# SECRET_KEY 생성 방법:
#   python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=changeme_generate_secure_random_key_using_command_above

#############################################
# 파일 저장
#############################################

DATA_DIR=./data
UPLOAD_DIR=./data/uploads
MODEL_DIR=./models

#############################################
# AI/ML 설정 (선택사항)
#############################################

# OpenAI API
#OPENAI_API_KEY=sk-...

# Anthropic API
#ANTHROPIC_API_KEY=sk-ant-...

# Hugging Face
#HUGGINGFACE_TOKEN=hf_...
```

**파일 위치**: `/KooAI/.env.example` (수정)

---

### Task 1.5: README 퀵스타트 가이드 추가 (1시간)

README.md 파일 상단에 추가:

```markdown
## 🚀 빠른 시작 (Quick Start)

### 전제 조건
- Python 3.11 이상
- Git

### 자동 설치 (권장)

**Linux/macOS**:
```bash
git clone https://github.com/yourusername/kooai.git
cd kooai
./setup.sh
```

**Windows**:
```batch
git clone https://github.com/yourusername/kooai.git
cd kooai
setup.bat
```

설치 프로파일 선택:
- `1` - Minimal: 기본 기능만 (~300MB, 5분)
- `2` - Standard: 3D 파일 지원 (~800MB, 10분) **[권장]**
- `3` - Full: AI 기능 포함 (~3.5GB, 20분)
- `4` - Dev: 개발 환경 (~4GB, 25분)

### 수동 설치

```bash
# 1. 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install --upgrade pip
pip install -e ".[standard]"  # 또는 [minimal], [full]

# 3. 환경 설정
cp .env.example .env
# .env 파일 편집 (선택사항)

# 4. 샘플 데이터 생성
python scripts/generate_sample_data.py

# 5. 설치 검증
python scripts/verify_installation.py
```

### 첫 실행

```bash
# 가상환경 활성화 (필수)
source venv/bin/activate

# 예제 실행
python examples/01_basic_usage.py

# API 서버 시작
uvicorn src.presentation.api.main:app --reload

# 브라우저에서 API 문서 확인
# http://localhost:8000/docs
```

### 문제 해결

설치 문제가 발생하면:

```bash
# 설치 검증
python scripts/verify_installation.py

# 재설치
rm -rf venv
./setup.sh
```
```

**파일 위치**: `/KooAI/README.md` (상단에 추가)

---

## ✅ Phase 1 완료 기준

### 검증 항목
1. ✅ `./setup.sh` 실행 성공
2. ✅ `python scripts/verify_installation.py` 모든 검사 통과
3. ✅ `python examples/01_basic_usage.py` 실행 성공
4. ✅ 샘플 데이터 파일 3개 생성됨
5. ✅ README 가이드대로 5분 안에 실행 가능

### 결과물
- ✅ `setup.sh`, `setup.bat` (자동 설치 스크립트)
- ✅ `scripts/generate_sample_data.py` (샘플 데이터 생성)
- ✅ `scripts/verify_installation.py` (설치 검증)
- ✅ `pyproject.toml` (의존성 재구성)
- ✅ `src/infrastructure/database/config.py` (DATABASE_URL 지원)
- ✅ `src/infrastructure/cache/config.py` (REDIS_URL 지원)
- ✅ `.env.example` (통일된 환경 변수)
- ✅ `README.md` (퀵스타트 가이드)
- ✅ `data/samples/` (샘플 데이터 3개 + README)

### 예상 소요 시간: 4.5시간

---

## 🏗️ Phase 2: 프로덕션 준비 (Week 2)

**목표**: Apptainer 컨테이너 + 보안 강화
**예상 시간**: 6.5시간

계속 작성하시겠습니까?
# KooAI 구현 계획 - Phase 2 & 3

## 🏗️ Phase 2: 프로덕션 준비 (Week 2)

**목표**: Apptainer 컨테이너 + 보안 강화 + 프로덕션 배포 가능
**예상 시간**: 6.5시간
**완료 기준**: Apptainer 이미지로 API 서버 실행 성공

---

### Task 2.1: Apptainer Definition 파일 작성 (1시간)

#### 2.1.1 기본 Apptainer Definition - `kooai.def`

```def
Bootstrap: docker
From: python:3.11-slim

%labels
    Author KooAI Team
    Version 0.1.0
    Description AI-powered simulation post-processing platform

%help
    KooAI - Simulation Post-Processing Platform

    사용법:
        # API 서버 실행
        apptainer run kooai.sif

        # CLI 명령어
        apptainer exec kooai.sif kooai parse data/sample.csv

        # Shell 접근
        apptainer shell kooai.sif

    환경 변수:
        DATABASE_URL - 데이터베이스 연결 URL
        REDIS_URL - Redis 연결 URL
        LOG_LEVEL - 로그 레벨 (INFO, DEBUG, WARNING)

%environment
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export PATH="/opt/kooai/venv/bin:$PATH"
    export KOOAI_ENV=production

%files
    # 소스 코드 복사
    src /opt/kooai/src
    examples /opt/kooai/examples
    pyproject.toml /opt/kooai/
    README.md /opt/kooai/
    .env.example /opt/kooai/
    kooai_cli.py /opt/kooai/
    alembic /opt/kooai/alembic
    alembic.ini /opt/kooai/

%post
    # 시스템 패키지 업데이트
    apt-get update
    apt-get install -y \
        gcc \
        g++ \
        make \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        git \
        && rm -rf /var/lib/apt/lists/*

    # 작업 디렉토리
    cd /opt/kooai

    # Python 가상환경 생성
    python3 -m venv venv
    . venv/bin/activate

    # pip 업그레이드
    pip install --upgrade pip setuptools wheel

    # KooAI 설치 (standard 프로파일)
    pip install -e ".[standard]"

    # 로그 및 데이터 디렉토리 생성
    mkdir -p /opt/kooai/logs
    mkdir -p /opt/kooai/data
    mkdir -p /opt/kooai/data/uploads

    # 샘플 데이터 생성
    python scripts/generate_sample_data.py || true

    # 권한 설정
    chmod +x kooai_cli.py

%runscript
    # 기본 실행: API 서버 시작
    cd /opt/kooai
    . venv/bin/activate

    # 환경 변수 체크
    if [ -z "$DATABASE_URL" ]; then
        echo "Warning: DATABASE_URL not set, using SQLite"
        export USE_TEST_DB=true
    fi

    echo "Starting KooAI API Server..."
    exec uvicorn src.presentation.api.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level info

%startscript
    # 서비스 시작 (instance 모드)
    cd /opt/kooai
    . venv/bin/activate
    exec uvicorn src.presentation.api.main:app \
        --host 0.0.0.0 \
        --port 8000

%test
    # 빌드 후 테스트
    cd /opt/kooai
    . venv/bin/activate

    echo "Testing Python import..."
    python -c "import sys; print(f'Python {sys.version}')"

    echo "Testing package imports..."
    python -c "
import numpy as np
import pandas as pd
import fastapi
import pydantic
print('✅ All core packages imported successfully')
"

    echo "Testing KooAI modules..."
    python -c "
from src.core.simulation.models import SimulationResult
from src.application.batch.processor import BatchProcessor
print('✅ KooAI modules imported successfully')
"

    echo "Testing CLI..."
    python kooai_cli.py --help

    echo "✅ All tests passed!"
```

**파일 위치**: `/KooAI/kooai.def`

#### 2.1.2 AI 기능 포함 버전 - `kooai-full.def`

```def
Bootstrap: docker
From: python:3.11-slim

%labels
    Author KooAI Team
    Version 0.1.0-full
    Description KooAI with AI/ML capabilities (PyTorch, Transformers)

%help
    KooAI Full - with AI/ML support

    ⚠️  이 이미지는 ~4GB 크기입니다.

%environment
    export PYTHONUNBUFFERED=1
    export PATH="/opt/kooai/venv/bin:$PATH"
    export KOOAI_ENV=production

%files
    src /opt/kooai/src
    pyproject.toml /opt/kooai/
    README.md /opt/kooai/
    kooai_cli.py /opt/kooai/

%post
    apt-get update
    apt-get install -y \
        gcc g++ make git \
        libgl1-mesa-glx libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*

    cd /opt/kooai
    python3 -m venv venv
    . venv/bin/activate

    pip install --upgrade pip setuptools wheel

    # Full 프로파일 설치 (AI 포함)
    echo "Installing KooAI with AI support (this will take ~20 minutes)..."
    pip install -e ".[full]"

    mkdir -p /opt/kooai/logs /opt/kooai/data

%runscript
    cd /opt/kooai
    . venv/bin/activate
    exec uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000
```

**파일 위치**: `/KooAI/kooai-full.def`

#### 2.1.3 Apptainer 빌드 스크립트 - `scripts/build_apptainer.sh`

```bash
#!/bin/bash
# Apptainer 이미지 빌드 스크립트

set -e

echo "======================================"
echo "KooAI Apptainer Image Builder"
echo "======================================"
echo ""

# Apptainer 설치 확인
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  Ubuntu/Debian:"
    echo "    sudo apt-get install -y apptainer"
    echo ""
    echo "  CentOS/RHEL:"
    echo "    sudo yum install -y apptainer"
    echo ""
    echo "  또는 공식 문서 참조:"
    echo "    https://apptainer.org/docs/admin/main/installation.html"
    exit 1
fi

echo "✅ Apptainer $(apptainer --version) 확인 완료"
echo ""

# 빌드 프로파일 선택
echo "빌드할 이미지를 선택하세요:"
echo "  1) standard - 기본 기능 + 3D 지원 (~1.5GB)"
echo "  2) full     - AI/ML 포함 전체 (~4GB)"
echo ""
read -p "선택 (1-2) [기본값: 1]: " PROFILE
PROFILE=${PROFILE:-1}

case $PROFILE in
    1)
        DEF_FILE="kooai.def"
        OUTPUT_FILE="kooai.sif"
        echo "📦 Standard 이미지 빌드 시작..."
        ;;
    2)
        DEF_FILE="kooai-full.def"
        OUTPUT_FILE="kooai-full.sif"
        echo "📦 Full 이미지 빌드 시작 (20분 소요 예상)..."
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

# 기존 이미지 백업
if [ -f "$OUTPUT_FILE" ]; then
    echo "⚠️  기존 이미지 발견: $OUTPUT_FILE"
    BACKUP_FILE="${OUTPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    mv "$OUTPUT_FILE" "$BACKUP_FILE"
    echo "   백업 저장: $BACKUP_FILE"
fi

# Apptainer 빌드
echo ""
echo "🔨 Apptainer 이미지 빌드 중..."
echo "   Definition: $DEF_FILE"
echo "   Output: $OUTPUT_FILE"
echo ""

# 권한 확인
if [ "$EUID" -eq 0 ]; then
    # root로 실행 중
    apptainer build "$OUTPUT_FILE" "$DEF_FILE"
else
    # 일반 사용자 - fakeroot 또는 remote builder 사용
    echo "일반 사용자로 빌드 중... (fakeroot 사용)"
    apptainer build --fakeroot "$OUTPUT_FILE" "$DEF_FILE"
fi

# 빌드 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 빌드 성공!"
    echo "======================================"
    echo ""
    echo "생성된 이미지: $OUTPUT_FILE"
    ls -lh "$OUTPUT_FILE"
    echo ""
    echo "실행 방법:"
    echo "  # API 서버 실행"
    echo "  apptainer run $OUTPUT_FILE"
    echo ""
    echo "  # CLI 명령어"
    echo "  apptainer exec $OUTPUT_FILE python kooai_cli.py --help"
    echo ""
    echo "  # Shell 접근"
    echo "  apptainer shell $OUTPUT_FILE"
    echo ""
    echo "  # 환경 변수 전달"
    echo "  apptainer run --env DATABASE_URL=postgresql://... $OUTPUT_FILE"
    echo ""
else
    echo ""
    echo "❌ 빌드 실패!"
    exit 1
fi
```

**파일 위치**: `/KooAI/scripts/build_apptainer.sh`

#### 2.1.4 Apptainer 실행 가이드 - `docs/APPTAINER_GUIDE.md`

```markdown
# Apptainer 사용 가이드

KooAI를 Apptainer 컨테이너로 실행하는 방법을 설명합니다.

## Apptainer란?

- HPC(고성능 컴퓨팅) 환경에서 사용되는 컨테이너 기술
- Docker와 유사하지만 root 권한 없이 실행 가능
- 대학, 연구소, 슈퍼컴퓨터에서 많이 사용

## 이미지 빌드

### 자동 빌드 (권장)

\`\`\`bash
./scripts/build_apptainer.sh
\`\`\`

선택:
- `1` - Standard (기본 + 3D, ~1.5GB, 10분)
- `2` - Full (AI 포함, ~4GB, 20분)

### 수동 빌드

\`\`\`bash
# Standard 버전
apptainer build kooai.sif kooai.def

# Full 버전 (AI 포함)
apptainer build kooai-full.sif kooai-full.def
\`\`\`

## 실행 방법

### 1. API 서버 실행

\`\`\`bash
# 기본 실행
apptainer run kooai.sif

# 백그라운드 실행
apptainer instance start kooai.sif kooai-api

# 인스턴스 확인
apptainer instance list

# 인스턴스 중지
apptainer instance stop kooai-api
\`\`\`

### 2. 환경 변수 전달

\`\`\`bash
# 데이터베이스 연결
apptainer run \
    --env DATABASE_URL="postgresql://user:pass@host:5432/kooai" \
    --env REDIS_URL="redis://host:6379/1" \
    kooai.sif

# 또는 .env 파일 사용
apptainer run \
    --env-file .env \
    kooai.sif
\`\`\`

### 3. 볼륨 마운트

\`\`\`bash
# 데이터 디렉토리 마운트
apptainer run \
    --bind ./data:/opt/kooai/data \
    --bind ./logs:/opt/kooai/logs \
    kooai.sif

# 호스트의 PostgreSQL 소켓 마운트
apptainer run \
    --bind /var/run/postgresql:/var/run/postgresql \
    kooai.sif
\`\`\`

### 4. CLI 명령어 실행

\`\`\`bash
# 파일 파싱
apptainer exec kooai.sif \
    python kooai_cli.py parse data/sample.csv

# 배치 처리
apptainer exec kooai.sif \
    python kooai_cli.py batch data/ --pattern "*.csv"

# Shell 접근
apptainer shell kooai.sif
Apptainer> python examples/01_basic_usage.py
\`\`\`

## HPC 환경에서 사용

### SLURM 작업 스크립트 예시

\`\`\`bash
#!/bin/bash
#SBATCH --job-name=kooai-api
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --partition=compute

# Apptainer 이미지 경로
KOOAI_SIF=/path/to/kooai.sif

# 환경 변수
export DATABASE_URL="postgresql://user:pass@dbhost:5432/kooai"
export REDIS_URL="redis://cachehost:6379/1"

# API 서버 시작
apptainer instance start \
    --bind $SCRATCH/kooai-data:/opt/kooai/data \
    --env DATABASE_URL=$DATABASE_URL \
    --env REDIS_URL=$REDIS_URL \
    $KOOAI_SIF kooai-api

# 로그 확인
sleep 5
apptainer exec instance://kooai-api cat /opt/kooai/logs/api.log

# 작업 완료 후 정리
trap "apptainer instance stop kooai-api" EXIT

# 작업 대기
wait
\`\`\`

### 배치 분석 작업 예시

\`\`\`bash
#!/bin/bash
#SBATCH --job-name=kooai-batch
#SBATCH --array=1-100
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

KOOAI_SIF=/path/to/kooai.sif
INPUT_DIR=/data/simulations
FILE=$(ls $INPUT_DIR/*.csv | sed -n ${SLURM_ARRAY_TASK_ID}p)

apptainer exec $KOOAI_SIF \
    python kooai_cli.py analyze $FILE --output results/
\`\`\`

## 네트워킹

### 포트 바인딩

\`\`\`bash
# 호스트의 8000번 포트로 API 노출
apptainer run \
    --bind ./data:/opt/kooai/data \
    kooai.sif

# 브라우저에서 접근
curl http://localhost:8000/health
\`\`\`

### 여러 서비스 연결

\`\`\`bash
# PostgreSQL과 Redis가 호스트에서 실행 중인 경우
apptainer run \
    --env DATABASE_URL="postgresql://user:pass@localhost:5432/kooai" \
    --env REDIS_URL="redis://localhost:6379/1" \
    kooai.sif
\`\`\`

## 문제 해결

### 권한 문제

Apptainer는 기본적으로 사용자 권한으로 실행됩니다.

\`\`\`bash
# fakeroot 빌드 (root 권한 없이)
apptainer build --fakeroot kooai.sif kooai.def

# 파일 소유권 문제 해결
apptainer exec kooai.sif id  # 사용자 확인
\`\`\`

### 네트워크 문제

\`\`\`bash
# 호스트 네트워크 사용
apptainer run --network=host kooai.sif

# DNS 설정
apptainer run --dns 8.8.8.8 kooai.sif
\`\`\`

### 로그 확인

\`\`\`bash
# 컨테이너 내부 로그
apptainer exec kooai.sif cat /opt/kooai/logs/api.log

# 실시간 로그
apptainer exec kooai.sif tail -f /opt/kooai/logs/api.log
\`\`\`

## 성능 최적화

### CPU 제한

\`\`\`bash
# CPU 코어 수 제한
apptainer run \
    --cpus 4 \
    --env API_WORKERS=4 \
    kooai.sif
\`\`\`

### 메모리 제한

\`\`\`bash
# 메모리 제한 (cgroup 필요)
apptainer run \
    --memory 8G \
    kooai.sif
\`\`\`

## 보안

### Read-only 파일시스템

\`\`\`bash
# 컨테이너를 read-only로 실행
apptainer run \
    --bind ./data:/opt/kooai/data \
    --writable-tmpfs \
    kooai.sif
\`\`\`

### 격리된 환경

\`\`\`bash
# 호스트와 격리
apptainer run \
    --cleanenv \
    --contain \
    --home /tmp \
    kooai.sif
\`\`\`
\`\`\`

**파일 위치**: `/KooAI/docs/APPTAINER_GUIDE.md`

---

### Task 2.2: API 보안 강화 (3시간)

#### 2.2.1 CORS 설정 개선 - `src/presentation/api/main.py`

```python
"""
FastAPI 애플리케이션
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .exceptions import register_exception_handlers
from .routes import simulation_routes

# Rate limiter 초기화
limiter = Limiter(key_func=get_remote_address)

# FastAPI 앱 생성
app = FastAPI(
    title="Simulation Post-Processing API",
    description="AI-powered simulation result analysis and processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiter 등록
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정 (환경 변수 기반)
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# 프로덕션 환경 체크
is_production = os.getenv("KOOAI_ENV", "development") == "production"

if is_production and "*" in allowed_origins:
    raise ValueError(
        "CORS allow_origins=['*'] is not allowed in production. "
        "Set ALLOWED_ORIGINS environment variable to specific domains."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,  # Preflight cache 1시간
)

# Gzip 압축 (응답 > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 예외 핸들러 등록
register_exception_handlers(app)

# 라우터 등록
app.include_router(simulation_routes.router, prefix="/api/v1")


# 헬스 체크 엔드포인트
@app.get("/health", tags=["health"])
@limiter.limit("100/minute")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "version": "1.0.0"}


# 루트 엔드포인트
@app.get("/", tags=["root"])
async def root():
    """API 루트"""
    return {
        "message": "Simulation Post-Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
```

#### 2.2.2 Rate Limiting 추가

**pyproject.toml에 slowapi 추가**:

```toml
dependencies = [
    # ... 기존 의존성
    "slowapi>=0.1.9",  # Rate limiting
]
```

#### 2.2.3 보안 헤더 미들웨어 - `src/presentation/api/middleware/security.py`

```python
"""
보안 헤더 미들웨어
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Remove server header
        if "Server" in response.headers:
            del response.headers["Server"]

        return response
```

**main.py에 적용**:

```python
from .middleware.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

---

### Task 2.3: 커스텀 예외 시스템 (2시간)

#### 2.3.1 예외 클래스 정의 - `src/core/exceptions.py`

```python
"""
KooAI 커스텀 예외 클래스
"""

from typing import Optional, Dict, Any


class KooAIException(Exception):
    """Base exception for all KooAI errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ParsingError(KooAIException):
    """파일 파싱 오류"""
    pass


class UnsupportedFileFormatError(ParsingError):
    """지원하지 않는 파일 형식"""

    def __init__(self, file_format: str, supported_formats: list):
        self.file_format = file_format
        self.supported_formats = supported_formats
        super().__init__(
            message=f"File format '{file_format}' is not supported. "
            f"Supported formats: {', '.join(supported_formats)}",
            error_code="UNSUPPORTED_FILE_FORMAT",
            details={
                "format": file_format,
                "supported": supported_formats,
            },
        )


class FileNotFoundError(ParsingError):
    """파일을 찾을 수 없음"""

    def __init__(self, file_path: str):
        super().__init__(
            message=f"File not found: {file_path}",
            error_code="FILE_NOT_FOUND",
            details={"file_path": file_path},
        )


class CorruptedFileError(ParsingError):
    """손상된 파일"""

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            message=f"File is corrupted or invalid: {file_path}. Reason: {reason}",
            error_code="CORRUPTED_FILE",
            details={"file_path": file_path, "reason": reason},
        )


class DatabaseError(KooAIException):
    """데이터베이스 오류"""
    pass


class ConnectionError(DatabaseError):
    """데이터베이스 연결 오류"""

    def __init__(self, db_url: str, original_error: Exception):
        super().__init__(
            message=f"Failed to connect to database: {original_error}",
            error_code="DB_CONNECTION_ERROR",
            details={"db_url": db_url, "original_error": str(original_error)},
        )


class ValidationError(KooAIException):
    """데이터 검증 오류"""

    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"Validation failed for field '{field}': {reason}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": value, "reason": reason},
        )


class CacheError(KooAIException):
    """캐시 오류"""
    pass


class AnalysisError(KooAIException):
    """분석 오류"""
    pass


class InsufficientDataError(AnalysisError):
    """데이터 부족"""

    def __init__(self, required: int, actual: int):
        super().__init__(
            message=f"Insufficient data for analysis. Required: {required}, Actual: {actual}",
            error_code="INSUFFICIENT_DATA",
            details={"required": required, "actual": actual},
        )


class ConfigurationError(KooAIException):
    """설정 오류"""

    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Configuration error for '{config_key}': {reason}",
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, "reason": reason},
        )
```

**파일 위치**: `/KooAI/src/core/exceptions.py` (신규 생성)

#### 2.3.2 API 예외 핸들러 - `src/presentation/api/exceptions.py`

```python
"""
FastAPI 예외 핸들러
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.exceptions import KooAIException
import logging

logger = logging.getLogger(__name__)


async def kooai_exception_handler(request: Request, exc: KooAIException):
    """KooAI 커스텀 예외 핸들러"""
    logger.error(
        f"KooAI Exception: {exc.error_code} - {exc.message}",
        extra={"details": exc.details},
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.to_dict(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPI validation 예외 핸들러"""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
        },
    )


def register_exception_handlers(app):
    """예외 핸들러 등록"""
    app.add_exception_handler(KooAIException, kooai_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```

**파일 위치**: `/KooAI/src/presentation/api/exceptions.py` (수정)

---

### Task 2.4: 데이터베이스 마이그레이션 가이드 (30분)

#### 2.4.1 마이그레이션 가이드 - `docs/DATABASE_GUIDE.md`

```markdown
# 데이터베이스 설정 가이드

## PostgreSQL 설치

### Ubuntu/Debian

\`\`\`bash
# PostgreSQL 설치
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql
\`\`\`

### macOS

\`\`\`bash
# Homebrew로 설치
brew install postgresql

# 서비스 시작
brew services start postgresql
\`\`\`

### CentOS/RHEL

\`\`\`bash
# PostgreSQL 설치
sudo yum install -y postgresql-server postgresql-contrib

# 초기화
sudo postgresql-setup initdb

# 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql
\`\`\`

## 데이터베이스 생성

\`\`\`bash
# postgres 사용자로 전환
sudo -u postgres psql

# 데이터베이스 및 사용자 생성
CREATE DATABASE kooai;
CREATE USER kooai WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE kooai TO kooai;

# pgvector 확장 설치 (벡터 검색용)
\c kooai
CREATE EXTENSION IF NOT EXISTS vector;

# 종료
\q
\`\`\`

## Alembic 마이그레이션

### 초기 설정

\`\`\`bash
# .env 파일 설정
DATABASE_URL=postgresql://kooai:your_password@localhost:5432/kooai
\`\`\`

### 마이그레이션 명령어

\`\`\`bash
# 현재 버전 확인
alembic current

# 마이그레이션 히스토리
alembic history

# 최신 버전으로 업그레이드
alembic upgrade head

# 특정 버전으로 이동
alembic upgrade <revision_id>

# 한 단계 업그레이드
alembic upgrade +1

# 한 단계 다운그레이드
alembic downgrade -1

# 특정 버전으로 다운그레이드
alembic downgrade <revision_id>

# 모든 마이그레이션 취소
alembic downgrade base
\`\`\`

### 새 마이그레이션 생성

\`\`\`bash
# 자동 생성 (모델 변경 감지)
alembic revision --autogenerate -m "Add new field"

# 수동 생성
alembic revision -m "Custom migration"
\`\`\`

생성된 마이그레이션 파일(`alembic/versions/*.py`)을 수정하여 원하는 작업 정의

## Docker/Apptainer 환경

### Docker Compose

\`\`\`bash
# PostgreSQL 시작
docker-compose up -d postgres

# 마이그레이션 실행
docker-compose exec api alembic upgrade head
\`\`\`

### Apptainer

\`\`\`bash
# 호스트 PostgreSQL 사용
apptainer exec \
    --env DATABASE_URL="postgresql://kooai:pass@localhost:5432/kooai" \
    kooai.sif \
    alembic upgrade head
\`\`\`

## 백업 및 복원

### 백업

\`\`\`bash
# 전체 백업
pg_dump -U kooai kooai > backup.sql

# 스키마만
pg_dump -U kooai --schema-only kooai > schema.sql

# 데이터만
pg_dump -U kooai --data-only kooai > data.sql
\`\`\`

### 복원

\`\`\`bash
# 데이터베이스 복원
psql -U kooai kooai < backup.sql
\`\`\`

## 문제 해결

### 연결 실패

\`\`\`bash
# PostgreSQL 서비스 확인
sudo systemctl status postgresql

# 연결 테스트
psql -U kooai -h localhost -d kooai

# 로그 확인
sudo tail -f /var/log/postgresql/postgresql-*.log
\`\`\`

### 권한 문제

\`\`\`sql
-- 권한 확인
\du

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE kooai TO kooai;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kooai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kooai;
\`\`\`
\`\`\`

**파일 위치**: `/KooAI/docs/DATABASE_GUIDE.md`

---

## ✅ Phase 2 완료 기준

### 검증 항목
1. ✅ `apptainer build kooai.sif kooai.def` 성공
2. ✅ `apptainer run kooai.sif` API 서버 시작 성공
3. ✅ `curl http://localhost:8000/health` 응답 성공
4. ✅ CORS 설정이 환경 변수로 제어됨
5. ✅ Rate limiting 동작 확인
6. ✅ 커스텀 예외가 올바른 JSON 응답 반환
7. ✅ Alembic 마이그레이션 실행 성공

### 결과물
- ✅ `kooai.def` (Apptainer definition - standard)
- ✅ `kooai-full.def` (Apptainer definition - AI 포함)
- ✅ `scripts/build_apptainer.sh` (빌드 스크립트)
- ✅ `docs/APPTAINER_GUIDE.md` (Apptainer 가이드)
- ✅ `src/presentation/api/main.py` (보안 강화)
- ✅ `src/presentation/api/middleware/security.py` (보안 헤더)
- ✅ `src/core/exceptions.py` (커스텀 예외)
- ✅ `docs/DATABASE_GUIDE.md` (DB 가이드)

### 예상 소요 시간: 6.5시간

---

## 🎨 Phase 3: 품질 향상 (Week 3)

**목표**: 통합 테스트 + 문서화 완성
**예상 시간**: 8시간

### Task 3.1: 통합 테스트 추가 (4시간)

#### 3.1.1 API 시작 테스트 - `tests/integration/test_api_startup.py`

[이전 USAGE_GAPS.md에서 제안한 내용 구현]

#### 3.1.2 예제 스크립트 테스트 - `tests/integration/test_examples.py`

[이전 USAGE_GAPS.md에서 제안한 내용 구현]

#### 3.1.3 End-to-end 테스트 - `tests/integration/test_e2e.py`

실제 파일 업로드 → 파싱 → 분석 → 결과 조회 전체 플로우 테스트

### Task 3.2: 로깅 시스템 구성 (2시간)

[이전 USAGE_GAPS.md에서 제안한 로깅 설정 구현]

### Task 3.3: CLI 문서화 (1시간)

#### 3.3.1 CLI Help 개선 - `kooai_cli.py`

더 상세한 도움말 및 예시 추가

#### 3.3.2 CLI 가이드 - `docs/CLI_GUIDE.md`

모든 CLI 명령어 상세 설명

### Task 3.4: 프로덕션 체크리스트 (1시간)

[이전 USAGE_GAPS.md에서 제안한 체크리스트 문서화]

---

## ✅ Phase 3 완료 기준

### 검증 항목
1. ✅ 통합 테스트 전체 통과
2. ✅ 예제 스크립트 자동 테스트 통과
3. ✅ 로깅이 파일과 콘솔에 정상 출력
4. ✅ CLI 도움말이 명확하고 유용함
5. ✅ 프로덕션 체크리스트 작성 완료

### 결과물
- ✅ `tests/integration/` (통합 테스트 3개)
- ✅ `src/core/logging/` (로깅 설정)
- ✅ `docs/CLI_GUIDE.md` (CLI 가이드)
- ✅ `docs/PRODUCTION_CHECKLIST.md` (체크리스트)

### 예상 소요 시간: 8시간

---

## 📊 전체 진행 상황 추적

### Timeline

| Week | Phase | 작업 내용 | 시간 | 누적 |
|------|-------|----------|------|------|
| 1 | Phase 1 | 기본 사용 가능 | 4.5h | 4.5h |
| 2 | Phase 2 | 프로덕션 준비 | 6.5h | 11h |
| 3 | Phase 3 | 품질 향상 | 8h | 19h |

### 완료 기준별 체크리스트

#### Week 1 종료 시
- [ ] git clone 후 `./setup.sh` 실행으로 5분 안에 설치 완료
- [ ] `python examples/01_basic_usage.py` 실행 성공
- [ ] 샘플 데이터 3개 자동 생성됨
- [ ] README 퀵스타트 가이드 완성

#### Week 2 종료 시
- [ ] Apptainer 이미지 빌드 성공
- [ ] `apptainer run kooai.sif`로 API 서버 실행
- [ ] CORS, Rate Limiting 동작 확인
- [ ] 커스텀 예외 응답 확인
- [ ] 데이터베이스 마이그레이션 성공

#### Week 3 종료 시
- [ ] 통합 테스트 전체 통과
- [ ] 로깅 시스템 동작 확인
- [ ] CLI 문서 완성
- [ ] 프로덕션 체크리스트 완성

---

## 🎯 최종 목표

**Before** (현재):
```
❌ 테스트 550개 통과하지만 실제 사용 불가
❌ 예제 코드 실행 안됨
❌ Docker만 지원, Apptainer 없음
❌ 보안 취약
❌ 문서 불충분
```

**After** (3주 후):
```
✅ 테스트 550개 + 통합 테스트 통과
✅ 예제 즉시 실행 가능
✅ Apptainer 지원 (HPC 환경)
✅ 프로덕션 보안 기준 충족
✅ 완전한 문서화
✅ 신규 사용자 5분 안에 시작 가능
```

---

**문서 작성**: Claude Code
**기준일**: 2025-11-07
**다음 단계**: Phase 1 Task 1.1부터 순차 실행
