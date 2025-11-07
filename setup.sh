#!/bin/bash
# setup.sh - KooAI 자동 설치 스크립트

set -e  # 에러 발생 시 중단

echo "======================================"
echo "🚀 KooAI 설치를 시작합니다..."
echo "======================================"
echo ""

# 1. Python 버전 확인
echo "📌 Python 버전 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되어 있지 않습니다."
    echo "Python 3.11 이상을 설치해주세요."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "   현재 Python 버전: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "❌ Python 3.11 이상이 필요합니다. 현재: $PYTHON_VERSION"
    echo ""
    echo "Python 3.11+ 설치 방법:"
    echo "  Ubuntu/Debian: sudo apt-get install python3.11"
    echo "  macOS: brew install python@3.11"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION 확인 완료"
echo ""

# 2. 가상환경 존재 확인 및 생성
if [ -d "venv" ]; then
    echo "⚠️  기존 가상환경(venv)이 발견되었습니다."
    read -p "삭제하고 새로 만드시겠습니까? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  기존 가상환경 삭제 중..."
        rm -rf venv
    else
        echo "✅ 기존 가상환경을 사용합니다."
    fi
fi

if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
fi

# 3. 가상환경 활성화
echo ""
echo "🔧 가상환경 활성화 중..."
source venv/bin/activate

# 4. pip 업그레이드
echo "📦 pip 업그레이드 중..."
pip install --upgrade pip setuptools wheel -q

# 5. 설치 프로파일 선택
echo ""
echo "======================================"
echo "설치 프로파일을 선택하세요:"
echo "======================================"
echo ""
echo "  1) minimal  - 기본 기능만 (CSV 파싱, 통계 분석)"
echo "                예상 크기: ~300MB, 소요 시간: ~5분"
echo ""
echo "  2) standard - 3D 파일 지원 추가 (VTK, VTU) [권장]"
echo "                예상 크기: ~800MB, 소요 시간: ~10분"
echo ""
echo "  3) full     - AI 기능 포함 전체 설치"
echo "                예상 크기: ~3.5GB, 소요 시간: ~20분"
echo ""
echo "  4) dev      - 개발 환경 (테스트, 린터 포함)"
echo "                예상 크기: ~4GB, 소요 시간: ~25분"
echo ""
read -p "선택 (1-4) [기본값: 2]: " PROFILE
PROFILE=${PROFILE:-2}

echo ""
echo "======================================"

case $PROFILE in
    1)
        echo "📦 Minimal 프로파일 설치 중..."
        INSTALL_TARGET=".[minimal]"
        ;;
    2)
        echo "📦 Standard 프로파일 설치 중... (권장)"
        INSTALL_TARGET=".[standard]"
        ;;
    3)
        echo "📦 Full 프로파일 설치 중..."
        echo "⚠️  이 작업은 20분 정도 소요됩니다..."
        INSTALL_TARGET=".[full]"
        ;;
    4)
        echo "📦 Development 프로파일 설치 중..."
        echo "⚠️  이 작업은 25분 정도 소요됩니다..."
        INSTALL_TARGET=".[dev,full]"
        ;;
    *)
        echo "❌ 잘못된 선택입니다. 기본값(standard)으로 설치합니다."
        INSTALL_TARGET=".[standard]"
        ;;
esac

echo "======================================"
echo ""

# 6. 패키지 설치
echo "📥 패키지 설치 중... (시간이 걸릴 수 있습니다)"
echo ""

# 설치 시작 시간 기록
START_TIME=$(date +%s)

# 설치 실행 (에러가 발생하면 대체 방법 시도)
if pip install -e "$INSTALL_TARGET"; then
    echo ""
    echo "✅ 패키지 설치 완료"
else
    echo ""
    echo "⚠️  선택한 프로파일 설치에 실패했습니다."
    echo "📦 기본 패키지로 대체 설치 중..."
    pip install -e .
fi

# 설치 소요 시간 계산
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo "   소요 시간: ${MINUTES}분 ${SECONDS}초"
echo ""

# 7. 환경 설정 파일 생성
if [ ! -f ".env" ]; then
    echo "⚙️  .env 파일 생성 중..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다."
    echo "   필요한 경우 .env 파일을 편집하세요."
else
    echo "ℹ️  .env 파일이 이미 존재합니다."
fi

echo ""

# 8. 샘플 데이터 생성
echo "📊 샘플 데이터 생성 중..."
if [ -f "scripts/generate_sample_data.py" ]; then
    python scripts/generate_sample_data.py
else
    echo "⚠️  샘플 데이터 생성 스크립트를 찾을 수 없습니다."
    echo "   나중에 수동으로 생성하세요: python scripts/generate_sample_data.py"
fi

echo ""

# 9. 설치 검증 (선택사항)
echo "======================================"
read -p "설치를 검증하시겠습니까? (Y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    if [ -f "scripts/verify_installation.py" ]; then
        python scripts/verify_installation.py
    else
        echo "⚠️  검증 스크립트를 찾을 수 없습니다."
        echo ""
        echo "수동 검증:"
        python -c "import numpy, pandas, fastapi; print('✅ 핵심 패키지 import 성공')"
    fi
fi

# 10. 설치 완료
echo ""
echo "======================================"
echo "✅ 설치가 완료되었습니다!"
echo "======================================"
echo ""
echo "다음 명령어로 시작하세요:"
echo ""
echo "  # 가상환경 활성화"
echo "  source venv/bin/activate"
echo ""
echo "  # 예제 실행"
echo "  python examples/01_basic_usage.py"
echo ""
echo "  # API 서버 시작"
echo "  uvicorn src.presentation.api.main:app --reload"
echo ""
echo "  # API 문서 확인"
echo "  # 브라우저에서 http://localhost:8000/docs 열기"
echo ""
echo "문제가 발생하면:"
echo "  python scripts/verify_installation.py"
echo ""
echo "======================================"
