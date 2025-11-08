#!/bin/bash
# Apptainer 이미지 빌드 스크립트

set -e  # 에러 발생 시 중단

echo "======================================"
echo "KooAI Apptainer Image Builder"
echo "======================================"
echo ""

# Apptainer 설치 확인
if ! command -v apptainer &> /dev/null; then
    echo "❌ Apptainer가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y software-properties-common"
    echo "  sudo add-apt-repository -y ppa:apptainer/ppa"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y apptainer"
    echo ""
    echo "CentOS/RHEL:"
    echo "  sudo yum install -y epel-release"
    echo "  sudo yum install -y apptainer"
    echo ""
    echo "공식 문서:"
    echo "  https://apptainer.org/docs/admin/main/installation.html"
    echo ""
    exit 1
fi

APPTAINER_VERSION=$(apptainer --version 2>&1)
echo "✅ Apptainer 확인: $APPTAINER_VERSION"
echo ""

# 빌드 프로파일 선택
echo "======================================"
echo "빌드할 이미지를 선택하세요:"
echo "======================================"
echo ""
echo "  1) standard - 기본 기능 + 3D 지원"
echo "                크기: ~1.5GB"
echo "                시간: ~10분"
echo "                권장: 대부분의 사용자"
echo ""
echo "  2) full     - AI/ML 포함 전체"
echo "                크기: ~4GB"
echo "                시간: ~20분"
echo "                권장: AI 기능 필요 시"
echo ""
read -p "선택 (1-2) [기본값: 1]: " PROFILE
PROFILE=${PROFILE:-1}

case $PROFILE in
    1)
        DEF_FILE="kooai.def"
        OUTPUT_FILE="kooai.sif"
        DESCRIPTION="Standard"
        echo ""
        echo "📦 Standard 이미지 빌드 시작..."
        ;;
    2)
        DEF_FILE="kooai-full.def"
        OUTPUT_FILE="kooai-full.sif"
        DESCRIPTION="Full (AI/ML)"
        echo ""
        echo "📦 Full 이미지 빌드 시작..."
        echo "⚠️  이 작업은 20분 이상 소요됩니다."
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

# Definition 파일 존재 확인
if [ ! -f "$DEF_FILE" ]; then
    echo "❌ Definition 파일을 찾을 수 없습니다: $DEF_FILE"
    exit 1
fi

echo "======================================"
echo "빌드 설정:"
echo "  Definition: $DEF_FILE"
echo "  Output: $OUTPUT_FILE"
echo "  Profile: $DESCRIPTION"
echo "======================================"
echo ""

# 기존 이미지 백업
if [ -f "$OUTPUT_FILE" ]; then
    echo "⚠️  기존 이미지 발견: $OUTPUT_FILE"
    BACKUP_FILE="${OUTPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "   백업 저장 중: $BACKUP_FILE"
    mv "$OUTPUT_FILE" "$BACKUP_FILE"
    echo "✅ 백업 완료"
    echo ""
fi

# Apptainer 빌드
echo "======================================"
echo "🔨 Apptainer 이미지 빌드 중..."
echo "======================================"
echo ""

# 빌드 시작 시간 기록
START_TIME=$(date +%s)

# 권한 확인 및 빌드
if [ "$EUID" -eq 0 ]; then
    # root로 실행 중
    echo "ℹ️  root 권한으로 빌드 중..."
    apptainer build "$OUTPUT_FILE" "$DEF_FILE"
else
    # 일반 사용자 - fakeroot 사용
    echo "ℹ️  일반 사용자 권한으로 빌드 중 (fakeroot 사용)..."

    # fakeroot 사용 가능 여부 확인
    if apptainer build --help 2>&1 | grep -q "\-\-fakeroot"; then
        apptainer build --fakeroot "$OUTPUT_FILE" "$DEF_FILE"
    else
        echo "⚠️  fakeroot를 사용할 수 없습니다."
        echo ""
        echo "다음 중 하나를 선택하세요:"
        echo "  1) sudo로 실행: sudo ./scripts/build_apptainer.sh"
        echo "  2) fakeroot 설정: https://apptainer.org/docs/user/main/fakeroot.html"
        echo ""
        exit 1
    fi
fi

# 빌드 결과 확인
BUILD_EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 빌드 성공!"
    echo "======================================"
    echo ""
    echo "생성된 이미지: $OUTPUT_FILE"
    echo "빌드 시간: ${MINUTES}분 ${SECONDS}초"
    echo ""

    # 이미지 정보 표시
    if [ -f "$OUTPUT_FILE" ]; then
        FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        echo "이미지 크기: $FILE_SIZE"
        echo ""
    fi

    echo "======================================"
    echo "사용 방법:"
    echo "======================================"
    echo ""
    echo "# API 서버 실행"
    echo "apptainer run $OUTPUT_FILE"
    echo ""
    echo "# 환경 변수 전달"
    echo "apptainer run \\"
    echo "    --env DATABASE_URL=\"postgresql://user:pass@host:5432/kooai\" \\"
    echo "    --env REDIS_URL=\"redis://host:6379/1\" \\"
    echo "    $OUTPUT_FILE"
    echo ""
    echo "# 데이터 디렉토리 바인딩"
    echo "apptainer run \\"
    echo "    --bind ./data:/opt/kooai/data \\"
    echo "    --bind ./logs:/opt/kooai/logs \\"
    echo "    $OUTPUT_FILE"
    echo ""
    echo "# CLI 명령어 실행"
    echo "apptainer exec $OUTPUT_FILE python kooai_cli.py --help"
    echo ""
    echo "# Shell 접근"
    echo "apptainer shell $OUTPUT_FILE"
    echo ""
    echo "# 도움말 보기"
    echo "apptainer run-help $OUTPUT_FILE"
    echo ""
    echo "======================================"
    echo ""
    echo "더 많은 정보:"
    echo "  docs/APPTAINER_GUIDE.md"
    echo ""

else
    echo ""
    echo "======================================"
    echo "❌ 빌드 실패!"
    echo "======================================"
    echo ""
    echo "빌드 시간: ${MINUTES}분 ${SECONDS}초"
    echo ""
    echo "문제 해결:"
    echo "  1. Definition 파일 확인: cat $DEF_FILE"
    echo "  2. 로그 확인 (위의 에러 메시지)"
    echo "  3. Apptainer 버전 확인: apptainer --version"
    echo "  4. 디스크 공간 확인: df -h"
    echo ""
    exit 1
fi
