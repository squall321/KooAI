@echo off
REM setup.bat - KooAI Windows 자동 설치 스크립트
setlocal enabledelayedexpansion

echo ======================================
echo 🚀 KooAI 설치를 시작합니다...
echo ======================================
echo.

REM 1. Python 버전 확인
echo 📌 Python 버전 확인 중...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python 3.11 이상을 설치해주세요.
    echo.
    echo 다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    현재 Python 버전: %PYTHON_VERSION%

REM Python 버전 체크 (간단 버전)
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.11 이상이 필요합니다.
    echo 현재 버전: %PYTHON_VERSION%
    pause
    exit /b 1
)

echo ✅ Python %PYTHON_VERSION% 확인 완료
echo.

REM 2. 가상환경 존재 확인
if exist venv (
    echo ⚠️ 기존 가상환경이 발견되었습니다.
    set /p REPLY="삭제하고 새로 만드시겠습니까? (y/N): "
    if /i "!REPLY!"=="y" (
        echo 🗑️ 기존 가상환경 삭제 중...
        rmdir /s /q venv
    ) else (
        echo ✅ 기존 가상환경을 사용합니다.
    )
)

if not exist venv (
    echo 📦 가상환경 생성 중...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo ✅ 가상환경 생성 완료
)

REM 3. 가상환경 활성화
echo.
echo 🔧 가상환경 활성화 중...
call venv\Scripts\activate.bat

REM 4. pip 업그레이드
echo 📦 pip 업그레이드 중...
python -m pip install --upgrade pip setuptools wheel -q

REM 5. 설치 프로파일 선택
echo.
echo ======================================
echo 설치 프로파일을 선택하세요:
echo ======================================
echo.
echo   1) minimal  - 기본 기능만 (CSV 파싱, 통계 분석)
echo                 예상 크기: ~300MB, 소요 시간: ~5분
echo.
echo   2) standard - 3D 파일 지원 추가 (VTK, VTU) [권장]
echo                 예상 크기: ~800MB, 소요 시간: ~10분
echo.
echo   3) full     - AI 기능 포함 전체 설치
echo                 예상 크기: ~3.5GB, 소요 시간: ~20분
echo.
echo   4) dev      - 개발 환경 (테스트, 린터 포함)
echo                 예상 크기: ~4GB, 소요 시간: ~25분
echo.
set /p PROFILE="선택 (1-4) [기본값: 2]: "
if "%PROFILE%"=="" set PROFILE=2

echo.
echo ======================================

if "%PROFILE%"=="1" (
    echo 📦 Minimal 프로파일 설치 중...
    set INSTALL_TARGET=.[minimal]
) else if "%PROFILE%"=="2" (
    echo 📦 Standard 프로파일 설치 중... (권장)
    set INSTALL_TARGET=.[standard]
) else if "%PROFILE%"=="3" (
    echo 📦 Full 프로파일 설치 중...
    echo ⚠️ 이 작업은 20분 정도 소요됩니다...
    set INSTALL_TARGET=.[full]
) else if "%PROFILE%"=="4" (
    echo 📦 Development 프로파일 설치 중...
    echo ⚠️ 이 작업은 25분 정도 소요됩니다...
    set INSTALL_TARGET=.[dev,full]
) else (
    echo ❌ 잘못된 선택입니다. 기본값(standard)으로 설치합니다.
    set INSTALL_TARGET=.[standard]
)

echo ======================================
echo.

REM 6. 패키지 설치
echo 📥 패키지 설치 중... (시간이 걸릴 수 있습니다)
echo.

pip install -e %INSTALL_TARGET%
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ 선택한 프로파일 설치에 실패했습니다.
    echo 📦 기본 패키지로 대체 설치 중...
    pip install -e .
)

echo.
echo ✅ 패키지 설치 완료
echo.

REM 7. 환경 설정
if not exist .env (
    echo ⚙️ .env 파일 생성 중...
    copy .env.example .env >nul
    echo ✅ .env 파일이 생성되었습니다.
    echo    필요한 경우 .env 파일을 편집하세요.
) else (
    echo ℹ️ .env 파일이 이미 존재합니다.
)

echo.

REM 8. 샘플 데이터 생성
echo 📊 샘플 데이터 생성 중...
if exist scripts\generate_sample_data.py (
    python scripts\generate_sample_data.py
) else (
    echo ⚠️ 샘플 데이터 생성 스크립트를 찾을 수 없습니다.
    echo    나중에 수동으로 생성하세요: python scripts\generate_sample_data.py
)

echo.

REM 9. 설치 검증
echo ======================================
set /p VERIFY="설치를 검증하시겠습니까? (Y/n): "
if /i not "!VERIFY!"=="n" (
    echo.
    if exist scripts\verify_installation.py (
        python scripts\verify_installation.py
    ) else (
        echo ⚠️ 검증 스크립트를 찾을 수 없습니다.
        echo.
        echo 수동 검증:
        python -c "import numpy, pandas, fastapi; print('✅ 핵심 패키지 import 성공')"
    )
)

REM 10. 설치 완료
echo.
echo ======================================
echo ✅ 설치가 완료되었습니다!
echo ======================================
echo.
echo 다음 명령어로 시작하세요:
echo.
echo   # 가상환경 활성화
echo   venv\Scripts\activate
echo.
echo   # 예제 실행
echo   python examples\01_basic_usage.py
echo.
echo   # API 서버 시작
echo   uvicorn src.presentation.api.main:app --reload
echo.
echo   # API 문서 확인
echo   # 브라우저에서 http://localhost:8000/docs 열기
echo.
echo 문제가 발생하면:
echo   python scripts\verify_installation.py
echo.
echo ======================================
pause
