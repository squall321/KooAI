# KooAI - AI-Powered Simulation Post-Processing Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![CI](https://github.com/yourusername/kooai/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/ci.yml)
[![Docker](https://github.com/yourusername/kooai/actions/workflows/docker.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/docker.yml)
[![Code Quality](https://github.com/yourusername/kooai/actions/workflows/code-quality.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/code-quality.yml)
[![Release](https://github.com/yourusername/kooai/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/release.yml)

## 🎯 프로젝트 개요

KooAI는 시뮬레이션 후처리 분석을 위한 AI 기반 통합 솔루션 플랫폼입니다.

**핵심 가치**:
- 🏗️ **Clean Architecture**: 계층 분리, 의존성 역전, 테스트 가능한 설계
- 🚀 **프로덕션 준비**: 모니터링, 로깅, 헬스체크, CI/CD 자동화
- 🐳 **HPC 지원**: Apptainer 컨테이너로 슈퍼컴퓨터 환경 지원
- 📊 **엔터프라이즈급**: Redis 캐싱, Celery 태스크 큐, Prometheus 모니터링
- ✅ **높은 품질**: 510+ 테스트 통과 (97%), 44% 커버리지

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
- **1 - Minimal**: 기본 기능만 (~300MB, 5분)
- **2 - Standard**: 3D 파일 지원 (~800MB, 10분) **[권장]**
- **3 - Full**: AI 기능 포함 (~3.5GB, 20분)
- **4 - Dev**: 개발 환경 (~4GB, 25분)

### 수동 설치

```bash
# 1. 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install --upgrade pip
pip install -e ".[standard]"  # 또는 [minimal], [full], [dev]

# 3. 환경 설정
cp .env.example .env
# .env 파일 편집 (필요시)

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

---

### 핵심 기능

#### 시뮬레이션 처리
- **📊 다양한 형식 지원**: CSV, VTK Legacy ASCII, VTU (VTK XML), HDF5
- **🔬 고급 결과 분석**: 통계 분석, 극값 탐지, 이상치 감지, 수렴성 분석
- **🎯 최첨단 분석**: FFT, POD, DMD, 난류 통계, 시계열, 상관관계
- **📐 3D 기하학 처리**: 메시 분석, 변환, 스무딩, 서브디비전
- **⚡ 스트리밍 파서**: 대용량 파일을 메모리 효율적으로 처리

#### 인프라 & 운영 (Priority 1-4 완료 ✅)
- **📝 구조화된 로깅**: Structlog 기반, 민감 데이터 자동 필터링
- **💚 헬스 체크**: Kubernetes 호환 (liveness, readiness, startup)
- **📊 Prometheus 모니터링**: 50+ 메트릭, Grafana 대시보드, 20+ 알람
- **🤖 CI/CD 자동화**: GitHub Actions (테스트, 품질, 빌드, 릴리스)
- **🐳 Apptainer 지원**: HPC 환경용 컨테이너 (minimal, standard, full)
- **⚡ 멀티티어 캐싱**: Redis L1 + In-Memory L2, 데코레이터 지원
- **🔄 비동기 작업**: Celery 기반 백그라운드 태스크, 우선순위 큐
- **☁️ 파일 스토리지**: 로컬, S3, MinIO, presigned URL

#### API & 인터페이스
- **🚀 REST API**: FastAPI 기반, 자동 문서화, OpenAPI
- **💻 CLI 도구**: Click + Rich 기반, 색상 출력
- **🏗️ Clean Architecture**: 계층 분리, 의존성 역전, 테스트 가능

## ✨ 주요 특징

### 시뮬레이션 결과 파싱
- CSV 형식 (스칼라/벡터 필드 자동 인식)
- VTK Legacy ASCII (POLYDATA, UNSTRUCTURED_GRID)
- VTU (VTK XML Unstructured Grid)
- HDF5 (대용량 데이터 형식, 선택적 의존성)
- 확장 가능한 파서 시스템

### 데이터 분석
- **통계 분석**: min, max, mean, std, percentiles
- **극값 탐지**: 최댓값/최솟값 자동 추출
- **이상치 감지**: Z-score 기반 outlier detection
- **그래디언트 계산**: Finite difference 방법
- **타임스텝 비교**: RMS change, relative change
- **수렴성 분석**: 시간에 따른 변화율 추적
- **공간 영역 분석**: 값 범위 기반 영역 검색

### 3D 기하학 처리
- 메시 분석 (면적, 부피, 무게중심, 바운딩 박스)
- 메시 품질 평가
- 메시 변환 (이동, 회전, 스케일)
- Laplacian smoothing
- Loop subdivision
- 메시 단순화 (decimation)

### 파일 스토리지
- **로컬 파일 시스템**: 개발/테스트용 로컬 스토리지
- **AWS S3**: 프로덕션 클라우드 스토리지
- **MinIO**: S3 호환 자체 호스팅 스토리지
- **Presigned URL**: 안전한 임시 URL 생성
- **멀티파트 업로드**: 대용량 파일 최적화
- **메타데이터 관리**: 커스텀 파일 메타데이터
- **배치 작업**: 다중 파일 업로드/삭제
- **자동 정리**: 오래된 파일 자동 삭제

### 비동기 작업 처리 (Celery)
- **백그라운드 파싱**: 대용량 시뮬레이션 파일 비동기 파싱
- **복잡한 분석**: 수렴성 분석, 공간 분석 등 장시간 작업
- **우선순위 큐**: High/Default/Low 우선순위 지원
- **자동 재시도**: Exponential backoff를 통한 실패 처리
- **진행률 추적**: 실시간 작업 진행률 모니터링
- **스케줄링**: Celery Beat를 통한 주기적 작업
  - 오래된 파일 정리 (매일 2AM)
  - 만료된 결과 정리 (6시간마다)
  - 헬스 체크 (5분마다)
- **모니터링**: Flower 웹 UI로 실시간 모니터링

### 고급 분석 기법
- **FFT (Fast Fourier Transform)**
  - 주파수 도메인 분석
  - Power spectral density
  - Spectrogram (시간-주파수 분석)
  - Coherence 분석
- **POD (Proper Orthogonal Decomposition)**
  - 공간 모드 추출
  - 에너지 기반 모드 선택
  - SVD, correlation, snapshot 방법 지원
  - 필드 재구성
- **DMD (Dynamic Mode Decomposition)**
  - 시공간 coherent 구조 추출
  - 모드 주파수 및 성장률 분석
  - Exact/Standard DMD 알고리즘
  - 미래 상태 예측
- **시계열 분석**
  - 통계량 계산 (평균, 분산, 왜도, 첨도)
  - 자기상관함수
  - 주기성 탐지
  - 트렌드 분석 및 제거
  - 이동평균 및 exponential smoothing
  - 이상치 탐지 (Z-score, IQR, MAD)
- **상관관계 분석**
  - Cross-correlation
  - Pearson/Spearman 상관계수
  - Lagged correlation
  - Mutual information
  - Coherence spectrum
- **난류 통계**
  - Reynolds 응력 텐서
  - 난류 운동에너지 (TKE)
  - 난류 강도
  - 소산율 (Dissipation rate)
  - 비등방성 텐서
  - 난류 불변량

### 성능 최적화 & 캐싱 (Phase 30) ✅
- **Redis 캐싱**
  - 자동 직렬화/역직렬화 (JSON, Pickle)
  - 압축 지원 (zlib)
  - 배치 작업 (get_many, set_many)
  - TTL 관리 (분석, 쿼리, 세션별 TTL)
  - 캐시 무효화 및 접두사 기반 삭제
- **캐시 데코레이터**
  - `@cache_result()` - 함수 결과 캐싱
  - `@cache_analysis()` - 분석 결과 자동 캐싱
  - `@invalidate_cache()` - 캐시 무효화
  - `@cache_async_result()` - 비동기 함수 캐싱
- **쿼리 최적화**
  - 배치 쿼리 처리
  - 연결 풀 관리
  - 인덱스 제안 시스템
  - `@optimize_query()`, `@batch_query()` 데코레이터
- **성능 프로파일링**
  - 실행 시간 측정
  - 성능 통계 수집 (평균, 최소, 최대)
  - `@profile_function()` 데코레이터
  - PerformanceMonitor for metrics tracking
- **응답 압축**
  - Gzip/Zlib 압축
  - 자동 압축 판단 (크기 & content-type)
  - ASGI 미들웨어 지원
  - 압축률 로깅

### 실용 비즈니스 로직 (Phase 33) ✅
- **시뮬레이션 비교**
  - RMSE 계산
  - 상관계수 분석
  - 수렴성 분석
  - 차이 분류 (negligible, small, moderate, large, critical)
  - 공간 차이 맵 생성
- **배치 처리**
  - 병렬 파일 처리 (멀티스레딩)
  - 순차 처리
  - 에러 핸들링 (stop_on_error)
  - 진행률 추적
  - 재시도 기능
- **파이프라인 시스템**
  - 스테이지 기반 처리 (Parse → Analyze → Export)
  - 메서드 체이닝
  - 커스텀 스테이지 정의
  - 에러 전파
- **다중 형식 내보내기**
  - JSON (메타데이터 포함)
  - CSV (필드 플래팅)
  - NumPy (.npz)
  - Text (요약 리포트)
  - 분석 결과 JSON 직렬화
- **리포트 생성**
  - Markdown 리포트
  - HTML 리포트 (스타일링 포함)
  - Text 리포트
  - 통계 테이블
  - 비교 요약
  - 배치 결과 리포트
  - 커스텀 섹션 지원

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────┐
│   Presentation Layer                     │
│   - REST API (FastAPI)                  │
│   - CLI (Click + Rich)                  │
├─────────────────────────────────────────┤
│   Application Layer                      │
│   - Use Cases (비즈니스 로직)           │
│   - Application Services                 │
├─────────────────────────────────────────┤
│   Core Layer                             │
│   - Domain Models                        │
│   - Simulation Parsing & Analysis        │
│   - 3D Geometry Processing               │
├─────────────────────────────────────────┤
│   Infrastructure Layer                   │
│   - Repository Implementations           │
│   - External Services                    │
└─────────────────────────────────────────┘
```

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.11 이상
- pip

### 설치

1. **저장소 클론**
```bash
git clone https://github.com/yourusername/kooai.git
cd kooai
```

2. **기본 설치**
```bash
pip install -e .
```

3. **선택적 의존성 설치**

개발 도구 포함:
```bash
pip install -e ".[dev]"
```

HDF5 파서 지원:
```bash
pip install -e ".[parsers]"
```

S3/MinIO 스토리지 지원:
```bash
pip install -e ".[storage]"
```

Flower 모니터링 지원:
```bash
pip install -e ".[tasks]"
```

모든 의존성 포함:
```bash
pip install -e ".[all]"
```

### REST API 실행

```bash
uvicorn src.presentation.api.main:app --reload
```

API는 http://localhost:8000 에서 접근 가능합니다.
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### CLI 사용

```bash
# 헬프 확인
python kooai_cli.py --help

# 시뮬레이션 업로드
python kooai_cli.py upload simulation.csv --name "My Simulation"

# 시뮬레이션 목록
python kooai_cli.py list

# 필드 분석
python kooai_cli.py analyze {simulation_id} temperature --extremes --outliers

# 수렴성 분석
python kooai_cli.py convergence {simulation_id} temperature
```

### Celery 워커 실행

**Redis 시작** (필수):
```bash
# Docker로 Redis 시작
docker run -d -p 6379:6379 redis:latest
```

**워커 시작**:
```bash
# 모든 워커 시작
chmod +x scripts/start_workers.sh
./scripts/start_workers.sh

# 또는 개별 워커 시작
celery -A celery_worker worker -Q simulation --loglevel=info
```

**Beat 스케줄러 시작**:
```bash
chmod +x scripts/start_beat.sh
./scripts/start_beat.sh
```

**Flower 모니터링 시작**:
```bash
celery -A celery_worker flower --port=5555
# http://localhost:5555 에서 접근
```

**워커 중지**:
```bash
chmod +x scripts/stop_workers.sh
./scripts/stop_workers.sh
```

## 🐳 컨테이너 배포

### Apptainer (HPC 환경) 🚀

Apptainer는 슈퍼컴퓨터와 HPC 클러스터 환경을 위한 컨테이너 시스템입니다.

#### 빌드

```bash
# Standard 이미지 빌드 (권장)
sudo apptainer build kooai-standard.sif containers/kooai.def

# Minimal 이미지 (최소 의존성)
sudo apptainer build kooai-minimal.sif containers/kooai-minimal.def

# Full 이미지 (AI/ML 포함)
sudo apptainer build kooai-full.sif containers/kooai-full.def

# 또는 빌드 스크립트 사용
./scripts/build-apptainer.sh standard
```

#### 실행

```bash
# API 서버 실행
apptainer run kooai-standard.sif

# 또는 실행 스크립트 사용
./scripts/run-apptainer.sh kooai-standard.sif 8000 /path/to/data

# Shell 접근
apptainer shell kooai-standard.sif

# 특정 명령 실행
apptainer exec kooai-standard.sif python -c "import vtk; print(vtk.vtkVersion().GetVTKVersion())"
```

#### CI/CD

GitHub Actions에서 자동으로 빌드됩니다:
- **Trigger**: Git tag push (`v*`)
- **Artifacts**: kooai-minimal.sif, kooai-standard.sif, kooai-full.sif
- **Testing**: Import verification, API health check

```bash
# 릴리스 생성
git tag v1.0.0
git push origin v1.0.0
# → GitHub Actions가 자동으로 Apptainer 이미지 빌드 및 릴리스
```

---

### Docker 배포

#### 로컬 개발 환경

Docker Compose를 사용하여 전체 스택을 쉽게 실행할 수 있습니다:

```bash
# 서비스 시작 (PostgreSQL, Redis, API)
./deploy/start.sh

# 또는 docker-compose 직접 사용
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 서비스 중지
./deploy/stop.sh
```

### Docker 이미지 빌드

```bash
# 빌드 스크립트 사용
./deploy/docker-build.sh

# 또는 직접 빌드
docker build -t kooai:latest .

# 이미지 실행
docker run -p 8000:8000 kooai:latest
```

### 프로덕션 배포

프로덕션 환경을 위한 별도의 docker-compose 설정이 제공됩니다:

```bash
# 1. 프로덕션 환경 설정
cp .env.production.example .env.production
# .env.production 파일을 편집하여 비밀번호 등을 설정

# 2. 프로덕션 서비스 시작
docker-compose -f docker-compose.production.yml up -d

# 3. 서비스 상태 확인
docker-compose -f docker-compose.production.yml ps

# 4. 로그 모니터링
docker-compose -f docker-compose.production.yml logs -f
```

프로덕션 배포에는 다음이 포함됩니다:
- PostgreSQL (pgvector 지원)
- Redis (캐싱)
- KooAI API (멀티 워커)
- Nginx (리버스 프록시, 레이트 리미팅)

### 환경 변수 설정

중요한 환경 변수들:

```bash
# 보안 (필수!)
SECRET_KEY=your-secret-key-here
POSTGRES_PASSWORD=strong-password
REDIS_PASSWORD=redis-password

# 데이터베이스
DATABASE_URL=postgresql://kooai:password@postgres:5432/kooai

# API 설정
API_WORKERS=4
LOG_LEVEL=INFO

# CORS (프론트엔드 도메인)
CORS_ORIGINS=https://yourdomain.com
```

자세한 설정은 `.env.example` 및 `.env.production.example` 파일을 참조하세요.

## 📚 API 사용 예제

### 시뮬레이션 업로드

```bash
curl -X POST http://localhost:8000/api/v1/simulations/upload \
  -F "file=@simulation.csv" \
  -F "name=My Simulation"
```

### 필드 분석

```bash
curl -X POST http://localhost:8000/api/v1/simulations/{id}/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "timestep": 0,
    "field_name": "temperature",
    "compute_extremes": true,
    "detect_outliers": true,
    "compute_histogram": true
  }'
```

### Python 클라이언트 예제

```python
import requests

# 업로드
with open("simulation.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/simulations/upload",
        files={"file": f},
        data={"name": "My Simulation"},
    )

sim_id = response.json()["simulation_id"]

# 필드 분석
analysis = requests.post(
    f"http://localhost:8000/api/v1/simulations/{sim_id}/analyze",
    json={
        "timestep": 0,
        "field_name": "temperature",
        "compute_extremes": True,
        "n_extremes": 10,
    },
).json()

print(f"Temperature: {analysis['statistics']['min']:.2f} - {analysis['statistics']['max']:.2f}")
```

## 🧪 테스트

### 전체 테스트 실행

```bash
pytest
```

### 커버리지 포함 테스트

```bash
pytest --cov=src --cov-report=html
```

### 특정 모듈 테스트

```bash
# 시뮬레이션 테스트
pytest tests/unit/simulation/

# API 테스트
pytest tests/api/

# CLI 테스트
pytest tests/unit/cli/
```

## 🏛️ 프로젝트 구조

```
kooai/
├── src/
│   ├── core/                          # 핵심 비즈니스 로직
│   │   ├── domain/                    # 도메인 엔티티
│   │   ├── simulation/                # 시뮬레이션 파싱 & 분석
│   │   │   ├── models.py              # 도메인 모델
│   │   │   ├── parsers/               # CSV, VTK 파서
│   │   │   └── analysis.py            # 결과 분석
│   │   ├── geometry/                  # 3D 기하학
│   │   │   ├── analysis.py            # 메시 분석
│   │   │   └── operations.py          # 메시 조작
│   │   └── repositories/              # 리포지토리 인터페이스
│   ├── application/                   # 애플리케이션 계층
│   │   ├── use_cases/                 # Use Cases (7개)
│   │   └── services/                  # Application Services
│   ├── infrastructure/                # 인프라 계층
│   │   └── repositories/              # 리포지토리 구현
│   └── presentation/                  # 프레젠테이션 계층
│       ├── api/                       # REST API (FastAPI)
│       │   ├── routes/                # API 라우트
│       │   ├── schemas/               # Pydantic 스키마
│       │   └── main.py                # FastAPI 앱
│       └── cli/                       # CLI (Click)
│           ├── commands.py            # CLI 명령어
│           └── utils.py               # CLI 유틸리티
├── tests/                             # 테스트
│   ├── unit/                          # 단위 테스트
│   │   ├── simulation/                # 시뮬레이션 테스트
│   │   ├── geometry/                  # 기하학 테스트
│   │   ├── application/               # Use Cases 테스트
│   │   └── cli/                       # CLI 테스트
│   └── api/                           # API 통합 테스트
├── kooai_cli.py                       # CLI 엔트리포인트
├── DEVELOPMENT_LOG.md                 # 개발 일지
└── README.md                          # 프로젝트 문서
```

## 📊 개발 현황

**완료된 Phase: 28개**

### 기본 기능 (Phase 1-22)
- ✅ Phase 1-11: 프로젝트 기반 구조 (도메인 모델, 리포지토리, JSON 처리, AI 모델, LLM, 파이프라인, 플러그인, Transfer Learning)
- ✅ Phase 12: 3D 데이터 처리 시스템
- ✅ Phase 13: 시뮬레이션 결과 파싱 및 분석
- ✅ Phase 14: Application Use Cases 및 서비스 계층
- ✅ Phase 15: REST API (Presentation Layer)
- ✅ Phase 16: CLI 인터페이스
- ✅ Phase 19: CI/CD 파이프라인 (GitHub Actions)
- ✅ Phase 20: Kubernetes 배포 시스템 및 Helm Chart
- ✅ Phase 21: 데이터베이스 통합 (PostgreSQL, SQLAlchemy)
- ✅ Phase 22: 프론트엔드 웹 애플리케이션 (React)

### 인프라 & 최적화 (Phase 25-33)
- ✅ Phase 25: 파일 스토리지 통합 (Local, S3, MinIO)
- ✅ Phase 26: 백그라운드 작업 처리 (Celery, Redis, Flower)
- ✅ Phase 27: 고급 분석 기능 (FFT, POD, DMD, 난류 통계)
- ✅ Phase 30: 성능 최적화 및 캐싱 (Redis Cache, Query Optimizer, Profiling, Compression)
- ✅ Phase 31: 통합 테스트 (Integration & E2E Tests)
- ✅ Phase 32: 부하 테스트 및 성능 튜닝 (Locust, Benchmarks, DB Performance)
- ✅ Phase 33: 실용 비즈니스 로직 (비교, 배치, Export, 리포트)

**구현 통계:**
- 총 코드: ~24,000+ lines
- 총 테스트: 150+ tests
- 부하 테스트: Locust (3 user types)
- 비즈니스 로직: 시뮬레이션 비교, 배치 처리, Export/Import, 자동 리포트
- 테스트 커버리지: 평균 60-85%
- 지원 파일 형식: CSV, VTK, Ensight, OpenFOAM, Fluent, HDF5
- Export 형식: JSON, CSV, NumPy, Text, HTML, Markdown

## 🎨 사용 예제

### CLI 예제

```bash
# 시뮬레이션 업로드 및 자동 분석
python kooai_cli.py upload simulation.csv --name "CFD Test" --analyze

# 출력:
# ℹ Uploading simulation.csv...
# ✓ Uploaded: abc123...
# ℹ Name: CFD Test
# ℹ Type: CSV
# ℹ Vertices: 1,000
# ℹ Fields: temperature, pressure, velocity

# 필드 분석 (통계, 극값, 이상치)
python kooai_cli.py analyze abc123 temperature --extremes --outliers

# 수렴성 분석 (테이블 형식 출력)
python kooai_cli.py convergence abc123 temperature

# 공간 영역 분석
python kooai_cli.py spatial abc123 temperature --min 450.0
```

### 프로그래밍 API 예제

```python
from pathlib import Path
from src.application.services import SimulationService
from src.infrastructure.repositories.memory_simulation_repository import (
    InMemorySimulationResultRepository
)

# 서비스 초기화
repository = InMemorySimulationResultRepository()
service = SimulationService(repository)

# 시뮬레이션 업로드 및 자동 분석
result = service.upload_and_analyze(
    file_path=Path("simulation.csv"),
    name="My Simulation",
    analyze_all_fields=True
)

print(f"Simulation ID: {result.simulation_info.simulation_id}")
print(f"Fields: {result.simulation_info.fields}")

# 필드 분석 결과
for field_name, analysis in result.field_analyses.items():
    stats = analysis.statistics
    print(f"{field_name}: min={stats['min']:.2f}, max={stats['max']:.2f}")

# 수렴성 분석
convergence = service.analyze_convergence(
    simulation_id=result.simulation_info.simulation_id,
    field_names=["temperature", "pressure"]
)

# 임계 영역 찾기
high_temp, low_temp = service.find_critical_regions(
    simulation_id=result.simulation_info.simulation_id,
    timestep=0,
    field_name="temperature",
    percentile=95.0
)

print(f"High temperature region: {high_temp.region_size} points")
```

## 🔧 개발 가이드

### 코드 스타일

프로젝트는 다음 코딩 표준을 따릅니다:
- PEP 8 스타일 가이드
- Type hints 사용
- Docstring (Google style)

### 새로운 파서 추가

```python
from src.core.simulation.parsers.base import BaseParser
from src.core.simulation.models import SimulationResult

class MyCustomParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".custom"

    def parse(self, file_path: Path, **options) -> SimulationResult:
        # 파싱 로직 구현
        pass

    def get_supported_extensions(self) -> List[str]:
        return [".custom"]

# 파서 등록
registry = ParserRegistry()
registry.register(MyCustomParser())
```

### 새로운 Use Case 추가

```python
from src.application.use_cases.base import UseCase

@dataclass
class MyRequest:
    data: str

@dataclass
class MyResponse:
    result: str

class MyUseCase(UseCase[MyRequest, MyResponse]):
    def execute(self, request: MyRequest) -> MyResponse:
        # 비즈니스 로직 구현
        return MyResponse(result="processed")
```

## 📖 API 문서

전체 API 문서는 서버 실행 후 다음 URL에서 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/v1/simulations/upload` | 시뮬레이션 업로드 |
| GET | `/api/v1/simulations/{id}` | 시뮬레이션 조회 |
| GET | `/api/v1/simulations/` | 시뮬레이션 목록 |
| POST | `/api/v1/simulations/{id}/analyze` | 필드 분석 |
| POST | `/api/v1/simulations/{id}/compare` | 타임스텝 비교 |
| POST | `/api/v1/simulations/{id}/convergence` | 수렴성 분석 |
| POST | `/api/v1/simulations/{id}/spatial` | 공간 분석 |
| DELETE | `/api/v1/simulations/{id}` | 시뮬레이션 삭제 |

## 🤝 기여

기여는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 📧 연락처

문의사항이 있으시면 이슈를 생성해주세요.

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:
- [FastAPI](https://fastapi.tiangolo.com/) - 웹 프레임워크
- [Click](https://click.palletsprojects.com/) - CLI 프레임워크
- [Rich](https://rich.readthedocs.io/) - 터미널 출력
- [NumPy](https://numpy.org/) - 수치 계산
- [Pydantic](https://pydantic.dev/) - 데이터 검증

---

## 📈 개발 현황

### 완료된 작업 ✅

#### Phase 1-33 (핵심 기능)
- ✅ **Phase 1-3**: 기본 인프라 구축 (도메인, 리포지토리, AI 모델)
- ✅ **Phase 25-27**: 파일 스토리지, 비동기 작업, 고급 분석
- ✅ **Phase 30-33**: 최적화, 테스트, 비즈니스 로직

#### Priority 1-4 (안정성 & 자동화)
- ✅ **Priority 1**: Testing & Stability (테스트 스위트 510+ 테스트)
- ✅ **Priority 2**: Operational Convenience (로깅, 헬스체크)
- ✅ **Priority 3**: Monitoring (Prometheus, Grafana, Alerting)
- ✅ **Priority 4**: CI/CD Automation (GitHub Actions, Apptainer)

#### Priority A (Critical - 2025-11-08 완료)
- ✅ **A1**: 코드 품질 검증 (510/525 테스트 통과)
- ✅ **A2**: 환경 변수 검증 (중앙 설정 시스템)
- ✅ **A3**: 의존성 충돌 해결 (충돌 없음)
- ✅ **코드 품질**: Ruff 377개 이슈 수정, Black 135개 파일 포맷팅

### 테스트 통계

```
✅ 510 tests passed (97% 성공률)
❌ 15 tests failed (optimization 모듈만)
📊 Coverage: 44% (11,391 lines)
🎯 Target: 70% coverage
```

### 코드 품질

```
✅ Ruff: 2/400 errors (99.5% 개선)
✅ Black: 100% formatted
✅ Type hints: 179 mypy errors (개선 중)
```

### 문서

- [TODO_NEXT_SESSION.md](TODO_NEXT_SESSION.md) - 다음 작업 계획 (Priority B-G)
- [PRODUCTION_GUIDE.md](docs/PRODUCTION_GUIDE.md) - 프로덕션 배포 가이드
- [MONITORING_GUIDE.md](docs/MONITORING_GUIDE.md) - 모니터링 설정
- [CI_CD_GUIDE.md](docs/CI_CD_GUIDE.md) - CI/CD 파이프라인
