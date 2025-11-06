# KooAI 개발 현황 및 다음 세션 가이드

**최종 업데이트**: 2025-11-06
**현재 브랜치**: `claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq`
**Python 버전**: 3.13
**프로젝트**: 시뮬레이션 후처리 플랫폼 (Simulation Post-Processing Platform)

---

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [완료된 개발 Phase](#완료된-개발-phase)
3. [최근 세션에서 완료한 작업](#최근-세션에서-완료한-작업)
4. [검증 완료된 모듈](#검증-완료된-모듈)
5. [검증 필요 모듈](#검증-필요-모듈)
6. [다음 개발 Phase](#다음-개발-phase)
7. [기술 스택 및 아키텍처](#기술-스택-및-아키텍처)
8. [개발 시작 방법](#개발-시작-방법)
9. [주요 파일 위치](#주요-파일-위치)
10. [알려진 이슈](#알려진-이슈)

---

## 🎯 프로젝트 개요

**KooAI**는 다양한 형식의 시뮬레이션 결과를 업로드, 저장, 분석, 비교할 수 있는 종합 후처리 플랫폼입니다.

### 핵심 기능
- **다양한 파일 형식 지원**: CSV, VTK, VTU, HDF5
- **고급 분석**: 통계 분석, 수렴성 분석, 난류 분석, POD, DMD, FFT
- **AI 모델 통합**: VAE, LLM (Anthropic, OpenAI, Local)
- **비교 및 보고**: 시뮬레이션 간 비교, 자동 리포트 생성
- **배치 처리**: 병렬 파일 처리, 파이프라인 시스템
- **캐싱 및 최적화**: Redis 캐싱, 쿼리 최적화, 압축

---

## ✅ 완료된 개발 Phase

### Phase 1-20 (이전 세션에서 완료)
- ✅ 프로젝트 초기 설정 및 구조 정의
- ✅ 도메인 모델 및 엔티티 구현
- ✅ Repository 패턴 구현 (메모리, SQL)
- ✅ CSV/VTK/VTU/HDF5 파서 구현
- ✅ 기본 분석 기능 (통계, 공간 분석)
- ✅ REST API 엔드포인트 (FastAPI)
- ✅ CLI 인터페이스
- ✅ 고급 분석 기능 (POD, DMD, FFT, 난류 분석)
- ✅ AI 모델 통합 (VAE, LLM)
- ✅ 플러그인 시스템
- ✅ 데이터 타입 시스템 (Mesh, Curve, Contour)
- ✅ 파이프라인 시스템
- ✅ 비동기 작업 (Celery)
- ✅ 모델 훈련 인프라

### Phase 27: Documentation & Examples (스킵)
- Documentation 및 예제는 나중에 추가

### Phase 28-29: External Integration (스킵)
- 외부 통합은 나중에 추가

### Phase 30: Performance Optimization & Caching ✅
**완료 날짜**: 2025-11-06

#### 구현 내용
- **Redis 캐싱**
  - `src/infrastructure/cache/redis_cache.py`: Redis 클라이언트, 직렬화(JSON/Pickle), 압축(zlib)
  - `src/infrastructure/cache/decorators.py`: `@cache_result`, `@cache_analysis`, `@invalidate_cache`
  - `src/infrastructure/cache/config.py`: 캐시 설정 (TTL, prefix, 크기 제한)

- **쿼리 최적화**
  - `src/infrastructure/optimization/query_optimizer.py`: QueryOptimizer, ConnectionPoolManager, IndexManager

- **성능 프로파일링**
  - `src/infrastructure/optimization/profiling.py`: Profiler, PerformanceMonitor

- **응답 압축**
  - `src/infrastructure/optimization/compression.py`: gzip/zlib 압축 미들웨어

#### 의존성
```toml
[project.optional-dependencies]
cache = ["redis>=5.0.0"]
```

### Phase 31: Integration Testing Infrastructure ✅
**완료 날짜**: 2025-11-06

#### 구현 내용
- **통합 테스트 인프라**
  - `tests/integration/conftest.py`: 테스트 픽스처 (DB, 스토리지, API 클라이언트)
  - `tests/integration/test_api_integration.py`: API 통합 테스트 (17개)
  - `tests/integration/test_database_integration.py`: DB 통합 테스트 (12개)
  - `tests/integration/test_storage_integration.py`: 스토리지 통합 테스트 (11개)
  - `tests/integration/test_e2e_workflow.py`: E2E 워크플로우 테스트 (14개)

#### 테스트 통계
- 총 54개 통합 테스트
- CSV, VTK 파일 업로드/분석 워크플로우
- 데이터베이스 CRUD 작업
- 스토리지 백엔드 통합

### Phase 32: Load Testing & Benchmarking ✅
**완료 날짜**: 2025-11-06

#### 구현 내용
- **Locust 부하 테스트**
  - `tests/load/locustfile.py`: 3가지 사용자 타입 (SimulationAPIUser, ReadOnlyUser, WriteHeavyUser)

- **성능 벤치마크**
  - `tests/load/benchmark.py`: 엔드포인트별 벤치마크 (7개 테스트)
  - `tests/load/db_performance.py`: 데이터베이스 성능 테스트 (10개 테스트)

#### 의존성
```toml
[project.optional-dependencies]
load = ["locust>=2.15.0"]
```

### Phase 33: Practical Business Logic ✅
**완료 날짜**: 2025-11-06

#### 구현 내용
- **시뮬레이션 비교 모듈** (검증 완료 ✓)
  - `src/application/comparison/comparator.py`: SimulationComparator
  - `src/application/comparison/diff_analyzer.py`: DifferenceAnalyzer
  - 기능: RMSE, 상관계수, 수렴성 분석, 차이 분류

- **배치 처리 시스템** (검증 진행 중)
  - `src/application/batch/processor.py`: BatchProcessor (병렬 처리)
  - `src/application/batch/pipeline.py`: Pipeline (스테이지 체이닝)

- **내보내기/가져오기 시스템** (검증 필요)
  - `src/application/export/exporter.py`: JSON, CSV, NumPy, Text 형식

- **리포트 생성** (검증 필요)
  - `src/application/reporting/generator.py`: Markdown, HTML, Text 리포트

#### 특징
- 외부 의존성 없음 (표준 라이브러리만 사용)
- Python 3.13 호환

---

## 🔍 최근 세션에서 완료한 작업

### 1. Comparison 모듈 검증 및 수정 ✅
**파일**: `src/application/comparison/comparator.py`

#### 발견된 문제
- ❌ 잘못된 import 경로: `src.core.domain.simulation` → `src.core.simulation.models`
- ❌ 잘못된 데이터 구조 가정: `.data.fields` → `.timesteps[i].fields`
- ❌ 없는 속성 참조: `.simulation_id` → `.id` or `.name`

#### 적용된 수정
- ✅ 올바른 import 경로로 변경
- ✅ 모든 메서드에 `timestep` 파라미터 추가
- ✅ SimulationResult의 실제 구조에 맞게 수정:
  - `sim.timesteps[timestep].get_field(field_name)`
  - FieldData의 `.data` 속성 사용
  - `sim.id if sim.id else sim.name` 안전 처리

### 2. 종합 테스트 생성 ✅

#### SimulationComparator 테스트 (14개)
`tests/unit/application/comparison/test_comparator.py`
- ✅ 기본 필드 비교
- ✅ 동일 필드 비교
- ✅ 모든 필드 비교
- ✅ 다중 시뮬레이션 비교
- ✅ 수렴성 계산
- ✅ 차이 식별
- ✅ 에러 처리 (없는 필드, 타임스텝)

#### DifferenceAnalyzer 테스트 (25개)
`tests/unit/application/comparison/test_diff_analyzer.py`
- ✅ 모든 차이 타입 (negligible, small, moderate, large, critical)
- ✅ 필드 메트릭 계산
- ✅ 다중 필드 분석
- ✅ 요약 생성
- ✅ 아웃라이어 영역 식별
- ✅ 엣지 케이스 (0값, 음수, 동일 필드)

#### 테스트 결과
```
tests/unit/application/comparison/test_comparator.py: 14 passed
tests/unit/application/comparison/test_diff_analyzer.py: 25 passed
총 39 tests passed ✅

Coverage:
- diff_analyzer.py: 100%
- comparator.py: 88%
```

### 3. Exporter 구문 오류 수정 ✅
**파일**: `src/application/export/exporter.py`

#### 문제
```python
format: Export   # 줄바꿈 오류

Format = ExportFormat.JSON,
```

#### 수정
```python
format: ExportFormat = ExportFormat.JSON,
```

### 4. Git 커밋 및 푸시 ✅
```bash
Commit: ab7730a
Message: "fix: Verify and test comparison module implementation"
Branch: claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq
```

---

## ✅ 검증 완료된 모듈

### 1. SimulationComparator
**위치**: `src/application/comparison/comparator.py`

**주요 메서드**:
- `compare_fields(sim1, sim2, field_name, timestep=0)` - 필드 비교
- `compare_all_fields(sim1, sim2, timestep=0)` - 모든 필드 비교
- `compare_multiple(simulations, field_name, timestep=0)` - 다중 시뮬레이션 비교
- `calculate_convergence(simulations, field_name, timestep=0)` - 수렴성 분석
- `identify_differences(sim1, sim2, field_name, threshold=0.1, timestep=0)` - 유의미한 차이 식별

**반환값**:
- `ComparisonResult`: RMSE, 상관계수, 평균/최대/최소 차이, 히스토그램, 공간 차이 맵

**검증 상태**: ✅ 완료 (14 tests passed)

### 2. DifferenceAnalyzer
**위치**: `src/application/comparison/diff_analyzer.py`

**주요 메서드**:
- `analyze_field_difference(field1, field2, field_name)` - 필드 차이 분석
- `analyze_all_fields(fields1, fields2)` - 모든 필드 분석
- `generate_summary(differences)` - 요약 생성
- `identify_outlier_regions(field1, field2, threshold_std=3.0)` - 아웃라이어 영역 식별

**차이 분류**:
- NEGLIGIBLE: < 1%
- SMALL: 1-5%
- MODERATE: 5-20%
- LARGE: 20-50%
- CRITICAL: > 50%

**검증 상태**: ✅ 완료 (25 tests passed)

---

## 🔄 검증 필요 모듈

### 1. BatchProcessor (진행 중)
**위치**: `src/application/batch/processor.py`

**주요 클래스**:
- `BatchJob`: 개별 작업 관리
- `BatchResult`: 배치 처리 결과
- `BatchProcessor`: 병렬 파일 처리

**테스트 상태**:
- ⚠️ 테스트 생성됨 (`tests/unit/application/batch/test_processor.py`)
- ⚠️ 일부 테스트 실패 (메서드 인터페이스 불일치)
- 🔧 수정 필요: `_add_job`, `process`, `process_parallel` 메서드

### 2. Pipeline
**위치**: `src/application/batch/pipeline.py`

**주요 클래스**:
- `PipelineStage`: 파이프라인 스테이지 추상 클래스
- `Pipeline`: 스테이지 체이닝
- `ParseStage`, `AnalyzeStage`, `ExportStage`: 사전 정의 스테이지

**테스트 상태**:
- ⚠️ 테스트 생성됨 (`tests/unit/application/batch/test_pipeline.py`)
- 🔍 실행 필요

### 3. MultiFormatExporter
**위치**: `src/application/export/exporter.py`

**지원 형식**: JSON, CSV, NumPy, Text

**테스트 상태**:
- ❌ 테스트 미생성
- ✅ 구문 오류 수정 완료

### 4. ReportGenerator
**위치**: `src/application/reporting/generator.py`

**출력 형식**: Markdown, HTML, Text

**테스트 상태**:
- ❌ 테스트 미생성
- 🔍 구현 검증 필요

---

## 📝 다음 개발 Phase

### 즉시 진행 가능 (Phase 33 완료)
1. **배치 처리 테스트 수정 완료**
   - `test_processor.py` 실패 테스트 수정
   - `test_pipeline.py` 실행 및 검증

2. **Export 시스템 테스트 생성**
   - `test_exporter.py` 생성
   - JSON, CSV, NumPy, Text 형식 검증

3. **Report Generator 테스트 생성**
   - `test_generator.py` 생성
   - Markdown, HTML, Text 출력 검증

### Phase 34: 실시간 협업 (계획)
**예상 내용**:
- WebSocket 실시간 통신
- 다중 사용자 협업
- 실시간 알림

### Phase 35: 모니터링 및 로깅 (계획)
**예상 내용**:
- Prometheus/Grafana 통합
- 구조화된 로깅
- 경고 시스템

### Phase 36: 보안 강화 (계획)
**예상 내용**:
- 인증/인가 (JWT)
- Rate limiting
- 입력 검증 및 살균

### 스킵된 Phase 재검토
- **Phase 27**: Documentation (README, API 문서, 사용자 가이드)
- **Phase 28-29**: External Integration (Slack, Email, Cloud storage)

---

## 🏗️ 기술 스택 및 아키텍처

### 핵심 기술
- **언어**: Python 3.13
- **웹 프레임워크**: FastAPI
- **데이터베이스**: SQLAlchemy (PostgreSQL/SQLite)
- **캐싱**: Redis
- **작업 큐**: Celery
- **테스팅**: pytest, pytest-cov, pytest-asyncio
- **부하 테스트**: Locust

### 아키텍처 패턴
**Clean Architecture** - 계층 분리
```
┌─────────────────────────────────────┐
│   Presentation Layer                │
│   (API, CLI)                        │
├─────────────────────────────────────┤
│   Application Layer                 │
│   (Use Cases, Services)             │
├─────────────────────────────────────┤
│   Domain Layer                      │
│   (Entities, Value Objects)         │
├─────────────────────────────────────┤
│   Infrastructure Layer              │
│   (Database, Storage, Cache, Tasks) │
└─────────────────────────────────────┘
```

### 프로젝트 구조
```
KooAI/
├── src/
│   ├── core/                    # 도메인 및 비즈니스 로직
│   │   ├── domain/              # 엔티티, 값 객체
│   │   ├── simulation/          # 시뮬레이션 모델, 파서
│   │   ├── advanced_analysis/   # POD, DMD, FFT, 난류
│   │   ├── ai_models/           # VAE, LLM
│   │   ├── data_types/          # Mesh, Curve, Contour
│   │   ├── geometry/            # 기하학 분석
│   │   ├── json_processing/     # JSON 파싱
│   │   ├── llm/                 # LLM 클라이언트
│   │   ├── pipeline/            # 파이프라인 시스템
│   │   └── plugins/             # 플러그인 시스템
│   │
│   ├── application/             # 애플리케이션 로직
│   │   ├── batch/               # 배치 처리, 파이프라인
│   │   ├── comparison/          # 시뮬레이션 비교 ✅
│   │   ├── export/              # 내보내기 ⚠️
│   │   ├── reporting/           # 리포트 생성 ⚠️
│   │   ├── services/            # 서비스
│   │   └── use_cases/           # 유스케이스
│   │
│   ├── infrastructure/          # 인프라 구현
│   │   ├── cache/               # Redis 캐싱 ✅
│   │   ├── database/            # DB 연결, 모델
│   │   ├── optimization/        # 쿼리 최적화, 프로파일링 ✅
│   │   ├── repositories/        # Repository 구현
│   │   ├── storage/             # 파일 스토리지
│   │   └── tasks/               # Celery 작업
│   │
│   └── presentation/            # 표현 계층
│       ├── api/                 # FastAPI 라우트
│       └── cli/                 # CLI 명령어
│
├── tests/
│   ├── unit/                    # 단위 테스트
│   │   └── application/
│   │       ├── comparison/ ✅   # 39 tests passed
│   │       └── batch/ ⚠️        # 일부 실패
│   ├── integration/             # 통합 테스트 (54 tests)
│   └── load/                    # 부하 테스트
│
├── docs/                        # 문서 (TODO)
├── examples/                    # 예제 (TODO)
└── pyproject.toml               # 프로젝트 설정
```

---

## 🚀 개발 시작 방법

### 1. 환경 설정
```bash
# 리포지토리 클론 및 이동
cd /home/user/KooAI

# Python 가상환경 (이미 설정되어 있음)
# Python 3.13 사용

# 의존성 설치
pip install -e ".[dev,cache,load]"
```

### 2. 브랜치 확인
```bash
# 현재 개발 브랜치 확인
git status
# branch: claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq

# 최신 변경사항 가져오기
git fetch origin
git pull origin claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq
```

### 3. 테스트 실행
```bash
# Comparison 모듈 테스트 (검증 완료)
pytest tests/unit/application/comparison/ -v

# 배치 모듈 테스트 (수정 필요)
pytest tests/unit/application/batch/ -v

# 통합 테스트
pytest tests/integration/ -v

# 커버리지 포함
pytest --cov=src --cov-report=html
```

### 4. 개발 서버 실행
```bash
# FastAPI 서버
uvicorn src.presentation.api.main:app --reload --port 8000

# Celery worker (비동기 작업용)
celery -A src.infrastructure.tasks.celery_app worker --loglevel=info

# Redis (캐싱용)
redis-server
```

---

## 📂 주요 파일 위치

### 설정 파일
- `pyproject.toml` - 프로젝트 메타데이터, 의존성
- `pytest.ini` / `pyproject.toml [tool.pytest]` - pytest 설정
- `.gitignore` - Git 무시 파일

### 핵심 모듈

#### 도메인 모델
```
src/core/domain/
├── entities.py          # SimulationResult, AnalysisStatus
└── value_objects.py     # Coordinate3D, Vector3D, BoundingBox, Statistics
```

#### 시뮬레이션 처리
```
src/core/simulation/
├── models.py            # SimulationResult, TimeStepData, FieldData, MeshData
├── analysis.py          # FieldAnalyzer, SpatialAnalyzer
└── parsers/
    ├── csv_parser.py    # CSV 파서
    ├── vtk_parser.py    # VTK 파서
    ├── vtu_parser.py    # VTU 파서
    └── hdf5_parser.py   # HDF5 파서
```

#### 비교 및 분석 (검증 완료)
```
src/application/comparison/
├── comparator.py        # SimulationComparator ✅
└── diff_analyzer.py     # DifferenceAnalyzer ✅
```

#### 배치 처리 (검증 진행 중)
```
src/application/batch/
├── processor.py         # BatchProcessor ⚠️
└── pipeline.py          # Pipeline ⚠️
```

#### 캐싱 및 최적화
```
src/infrastructure/cache/
├── redis_cache.py       # RedisCache ✅
├── decorators.py        # @cache_result, @cache_analysis ✅
└── config.py            # CacheConfig ✅

src/infrastructure/optimization/
├── query_optimizer.py   # QueryOptimizer ✅
├── profiling.py         # Profiler, PerformanceMonitor ✅
└── compression.py       # Response compression ✅
```

#### API 엔드포인트
```
src/presentation/api/
├── main.py              # FastAPI app
└── routes/
    └── simulation_routes.py  # 시뮬레이션 API
```

---

## ⚠️ 알려진 이슈

### 1. BatchProcessor 테스트 실패
**파일**: `tests/unit/application/batch/test_processor.py`

**문제**:
- `_add_job` 메서드가 private이거나 구현과 테스트 간 인터페이스 불일치
- 병렬 처리 테스트에서 call count가 스레드 간 공유되지 않음

**해결 방법**:
```python
# 옵션 1: processor.py 읽고 실제 메서드 확인
# 옵션 2: 간단한 통합 테스트로 대체
```

### 2. Pipeline 테스트 미실행
**파일**: `tests/unit/application/batch/test_pipeline.py`

**상태**: 생성되었지만 실행 안 됨

**해결 방법**:
```bash
pytest tests/unit/application/batch/test_pipeline.py -v
```

### 3. Export 및 Report 모듈 미검증
**파일**:
- `src/application/export/exporter.py`
- `src/application/reporting/generator.py`

**상태**: 구문 오류는 수정했지만 기능 검증 안 됨

**해결 방법**: 단위 테스트 생성 필요

---

## 📊 개발 진행률

### Phase별 진행 상황
```
Phase 1-20:   ████████████████████ 100% ✅
Phase 27:     ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% (스킵)
Phase 28-29:  ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% (스킵)
Phase 30:     ████████████████████ 100% ✅ (캐싱, 최적화)
Phase 31:     ████████████████████ 100% ✅ (통합 테스트)
Phase 32:     ████████████████████ 100% ✅ (부하 테스트)
Phase 33:     ████████████████⬜⬜⬜  80% ⚠️ (비즈니스 로직)
  ├─ Comparison:  ████████████████████ 100% ✅
  ├─ Batch:       ████████████⬜⬜⬜⬜⬜⬜  60% ⚠️
  ├─ Export:      ████⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜  20% ⚠️
  └─ Reporting:   ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌
```

### 테스트 커버리지
```
전체 프로젝트: ~4%
src/application/comparison/: 88-100% ✅
src/application/batch/: 0% (테스트 실패)
src/infrastructure/cache/: 0% (통합 테스트만 있음)
src/infrastructure/optimization/: 0% (통합 테스트만 있음)
```

---

## 🎯 다음 세션 우선순위

### High Priority (즉시 진행)
1. ✅ **Comparison 모듈 완료 확인** - DONE
2. 🔧 **Batch 모듈 테스트 수정** - IN PROGRESS
3. 📝 **Export 모듈 테스트 생성**
4. 📝 **Report 모듈 테스트 생성**

### Medium Priority
5. 📚 **Documentation (Phase 27)** - README, API 문서
6. 🔌 **External Integration 검토 (Phase 28-29)**
7. 🚀 **Phase 34 계획** - 실시간 협업

### Low Priority
8. 🎨 **UI 프론트엔드** - 현재 없음, 필요시 추가
9. 🐳 **Docker 컨테이너화**
10. ☁️ **클라우드 배포** (AWS/GCP/Azure)

---

## 💡 개발 팁

### 테스트 작성 시
1. **Fixture 활용**: `conftest.py`에서 공통 픽스처 정의
2. **Parametrize**: `@pytest.mark.parametrize`로 여러 케이스 테스트
3. **Mock**: 외부 의존성은 mock 처리
4. **Coverage**: `--cov` 플래그로 커버리지 확인

### 코드 스타일
- **Black**: 코드 포맷팅
- **isort**: Import 정렬
- **mypy**: 타입 체크 (선택적)
- **flake8**: 린팅 (선택적)

### Git Workflow
```bash
# 개발 브랜치에서 작업
git checkout claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq

# 변경사항 커밋
git add .
git commit -m "feat: Add feature description"

# 푸시 (재시도 로직 포함)
git push -u origin claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq
```

### 유용한 명령어
```bash
# 전체 테스트 실행
pytest tests/ -v

# 특정 모듈만 테스트
pytest tests/unit/application/comparison/ -v

# 커버리지와 함께
pytest --cov=src --cov-report=html

# 실패한 테스트만 재실행
pytest --lf

# 특정 테스트만 실행
pytest tests/unit/application/comparison/test_comparator.py::test_compare_fields_basic -v

# 로그 출력 포함
pytest -v -s
```

---

## 📞 연락처 및 리소스

### 프로젝트 문서
- **ROADMAP.md**: 전체 개발 로드맵
- **PHASE_CHECKLISTS.md**: Phase별 체크리스트
- **DEVELOPMENT_STATUS.md**: 현재 문서

### Git 정보
- **Repository**: KooAI
- **Branch**: `claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq`
- **Latest Commit**: `ab7730a` - "fix: Verify and test comparison module implementation"

---

## 🔄 최근 커밋 히스토리

```
ab7730a (HEAD) fix: Verify and test comparison module implementation
141095b feat: 실용 비즈니스 로직 구현 및 Python 3.13 업데이트 (Phase 33 완료)
7210e3b feat: 부하 테스트 및 성능 벤치마크 구현 (Phase 32 완료)
cd3cd7e feat: 통합 테스트 인프라 구현 (Phase 31 완료)
fb2bf22 feat: 성능 최적화 및 캐싱 시스템 구현 (Phase 30 완료)
```

---

**마지막 업데이트**: 2025-11-06
**작성자**: Claude AI
**다음 세션 준비 완료**: ✅

---

## 🚦 Quick Start for Next Session

```bash
# 1. 현재 상태 확인
cd /home/user/KooAI
git status

# 2. 이전 테스트 결과 확인
pytest tests/unit/application/comparison/ -v  # ✅ 39 passed

# 3. 다음 작업 진행
pytest tests/unit/application/batch/ -v       # ⚠️ 수정 필요

# 4. 새로운 테스트 생성
# - tests/unit/application/export/test_exporter.py
# - tests/unit/application/reporting/test_generator.py

# 5. 모든 검증 완료 후 커밋
git add .
git commit -m "feat: Complete Phase 33 verification"
git push -u origin claude/simulation-postprocessing-backend-011CUqimy93ZYRqxAvM4GTEq
```

행운을 빕니다! 🚀
