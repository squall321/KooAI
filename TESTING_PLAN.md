# 🧪 KooAI 프로젝트 종합 테스트 계획

> **목적**: 실제 구현된 모든 기능이 제대로 동작하는지 체계적으로 검증
> **예상 소요 시간**: 2-3시간
> **난이도**: ⭐⭐⭐

---

## 📋 목차

1. [사전 준비](#1-사전-준비)
2. [Phase 1: 환경 설정 검증](#phase-1-환경-설정-검증)
3. [Phase 2: 백엔드 단독 테스트](#phase-2-백엔드-단독-테스트)
4. [Phase 3: 프론트엔드 단독 테스트](#phase-3-프론트엔드-단독-테스트)
5. [Phase 4: 통합 테스트](#phase-4-통합-테스트)
6. [Phase 5: 고급 기능 테스트](#phase-5-고급-기능-테스트)
7. [Phase 6: 성능 및 부하 테스트](#phase-6-성능-및-부하-테스트)
8. [문제 해결 가이드](#문제-해결-가이드)
9. [테스트 체크리스트](#테스트-체크리스트)

---

## 1. 사전 준비

### 1.1 필수 소프트웨어 확인

```bash
# Python 버전 확인 (3.11 이상 필요)
python --version
# 예상 출력: Python 3.11.x 또는 3.12.x

# Node.js 버전 확인 (18 이상 필요)
node --version
# 예상 출력: v18.x.x 또는 v20.x.x

# npm 버전 확인
npm --version
# 예상 출력: 9.x.x 또는 10.x.x

# Git 확인
git --version
# 예상 출력: git version 2.x.x
```

**✅ 체크포인트**: 모든 버전이 요구사항을 충족하는가?

### 1.2 프로젝트 구조 확인

```bash
# 프로젝트 루트 디렉토리에서
ls -la

# 예상 출력:
# - src/                (백엔드 소스)
# - frontend/           (프론트엔드)
# - tests/              (테스트)
# - pyproject.toml      (Python 설정)
# - README.md
# - TODO_NEXT_SESSION.md
```

**✅ 체크포인트**: 필수 디렉토리가 모두 존재하는가?

---

## Phase 1: 환경 설정 검증

### 1.1 Python 가상환경 생성 및 의존성 설치

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# pip 업그레이드
pip install --upgrade pip

# 기본 의존성 설치 (빠른 테스트용)
pip install -e ".[minimal]"

# 예상 소요 시간: 2-3분
# 예상 출력: Successfully installed ... (여러 패키지)
```

**⚠️ 주의사항**:
- `minimal` 프로파일은 AI/ML 제외
- 전체 테스트는 `pip install -e ".[full]"` 필요

**✅ 체크포인트**: 설치 중 에러 없이 완료되었는가?

### 1.2 의존성 충돌 확인

```bash
# 의존성 검증
pip check

# 예상 출력 (정상):
# No broken requirements found.

# 예상 출력 (문제 있음):
# package-name X.Y.Z has requirement other-package>=A.B.C, but you have other-package 1.2.3.
```

**✅ 체크포인트**: 의존성 충돌이 없는가?

**문제 발생 시**:
```bash
# 충돌하는 패키지 재설치
pip uninstall [package-name]
pip install [package-name]==X.Y.Z
```

### 1.3 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 vim, code 등
```

**최소 설정** (.env):
```env
# 데이터베이스 (SQLite - 테스트용)
DATABASE_URL=sqlite:///./kooai_test.db

# Redis (선택적 - 로컬 테스트 시)
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=false

# 로깅
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# API 설정
API_HOST=0.0.0.0
API_PORT=8000
```

**✅ 체크포인트**: .env 파일이 생성되고 기본 설정이 되어 있는가?

### 1.4 데이터베이스 초기화

```bash
# Alembic 마이그레이션 실행
alembic upgrade head

# 예상 출력:
# INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
# INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> 6ef43ae90e64, initial schema
```

**✅ 체크포인트**: 마이그레이션이 성공했는가?

**문제 발생 시**:
```bash
# 데이터베이스 초기화 (기존 DB 삭제)
rm kooai_test.db
alembic upgrade head
```

---

## Phase 2: 백엔드 단독 테스트

### 2.1 pytest 실행

```bash
# 전체 테스트 실행 (간단한 출력)
pytest tests/ -v

# 예상 출력:
# tests/unit/simulation/parsers/test_csv_parser.py::TestCSVParser::test_parse_simple_csv PASSED
# tests/unit/simulation/parsers/test_vtk_parser.py::TestVTKParser::test_parse_vtk PASSED
# ...
# ==================== X passed in Y.YYs ====================

# 커버리지 포함 실행
pytest tests/ --cov=src --cov-report=html

# 예상 출력:
# Coverage HTML written to dir htmlcov
```

**예상 결과**:
- **통과**: 450-510개 테스트
- **실패**: 0-15개 (optimization 모듈 제외)
- **커버리지**: 40-50%

**✅ 체크포인트**: 대부분의 테스트가 통과했는가? (90% 이상)

### 2.2 코드 품질 검사

```bash
# Ruff 린터
ruff check src/ tests/

# 예상 출력:
# All checks passed!
# 또는
# src/some_file.py:42:5: F401 'module' imported but unused

# Black 포맷 확인
black --check src/ tests/

# 예상 출력:
# All done! ✨ 🍰 ✨
# X files would be left unchanged.

# Mypy 타입 체크 (경고 많을 수 있음)
mypy src/ --ignore-missing-imports

# 예상 출력:
# Success: no issues found in X source files
# 또는
# Found X errors in Y files (checked Z source files)
```

**✅ 체크포인트**:
- Ruff: 에러 < 10개
- Black: 포맷 이슈 없음
- Mypy: 치명적 에러 없음

### 2.3 API 서버 시작

```bash
# API 서버 실행
uvicorn src.presentation.api.main:app --reload --log-level debug

# 예상 출력:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [12345] using StatReload
# INFO:     Started server process [12346]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**✅ 체크포인트**: 서버가 에러 없이 시작되었는가?

**문제 발생 시**:
- Import 에러: 가상환경 활성화 확인
- Port 충돌: `--port 8001` 사용
- DB 에러: Alembic 마이그레이션 재실행

### 2.4 API 엔드포인트 테스트

**새 터미널 열기** (서버는 계속 실행)

#### 2.4.1 Health Check

```bash
# 헬스 체크
curl http://localhost:8000/health

# 예상 출력:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "database": "connected",
#   "timestamp": "2025-11-17T..."
# }
```

**✅ 체크포인트**: status가 "healthy"인가?

#### 2.4.2 API 문서 접근

브라우저에서 다음 URL 접속:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**✅ 체크포인트**:
- 문서 페이지가 정상적으로 로드되는가?
- API 엔드포인트 목록이 보이는가?

#### 2.4.3 시뮬레이션 업로드 테스트

```bash
# 샘플 CSV 파일 생성
cat > /tmp/test_simulation.csv << 'EOF'
x,y,z,temperature,pressure
0.0,0.0,0.0,300.0,101325.0
1.0,0.0,0.0,350.0,101325.0
0.0,1.0,0.0,325.0,101325.0
1.0,1.0,0.0,375.0,101325.0
EOF

# 파일 업로드
curl -X POST http://localhost:8000/api/v1/simulations/upload \
  -F "file=@/tmp/test_simulation.csv" \
  -F "name=Test Simulation"

# 예상 출력 (JSON):
# {
#   "simulation_id": "abc123...",
#   "name": "Test Simulation",
#   "simulation_type": "CSV",
#   "num_vertices": 4,
#   "num_timesteps": 1,
#   "fields": ["temperature", "pressure"]
# }
```

**✅ 체크포인트**:
- 업로드 성공했는가?
- simulation_id가 반환되었는가?
- 필드가 정확히 파싱되었는가?

**simulation_id를 복사해두세요** (다음 테스트에 사용)

#### 2.4.4 시뮬레이션 조회

```bash
# simulation_id를 실제 값으로 교체
export SIM_ID="abc123..."

# 시뮬레이션 정보 조회
curl http://localhost:8000/api/v1/simulations/$SIM_ID

# 예상 출력:
# {
#   "simulation_id": "abc123...",
#   "name": "Test Simulation",
#   "num_vertices": 4,
#   "fields": ["temperature", "pressure"],
#   ...
# }
```

**✅ 체크포인트**: 업로드한 시뮬레이션 정보가 정확한가?

#### 2.4.5 필드 분석

```bash
# 온도 필드 분석
curl -X POST http://localhost:8000/api/v1/simulations/$SIM_ID/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "temperature",
    "timestep": 0,
    "compute_extremes": true,
    "compute_outliers": true
  }'

# 예상 출력:
# {
#   "field_name": "temperature",
#   "statistics": {
#     "min": 300.0,
#     "max": 375.0,
#     "mean": 337.5,
#     "std": ...,
#     "median": ...
#   },
#   "extremes": {
#     "max_values": [...],
#     "max_locations": [...],
#     ...
#   }
# }
```

**✅ 체크포인트**: 통계가 정확히 계산되었는가?

### 2.5 CLI 도구 테스트

```bash
# CLI 헬프
python kooai_cli.py --help

# 예상 출력:
# Usage: kooai_cli.py [OPTIONS] COMMAND [ARGS]...
# Commands:
#   upload      Upload simulation file
#   list        List all simulations
#   analyze     Analyze field
#   ...

# CLI로 업로드
python kooai_cli.py upload /tmp/test_simulation.csv --name "CLI Test"

# 예상 출력:
# ℹ Uploading /tmp/test_simulation.csv...
# ✓ Uploaded: xyz789...
# ℹ Name: CLI Test
# ℹ Type: CSV
# ℹ Vertices: 4
# ℹ Fields: temperature, pressure

# 시뮬레이션 목록
python kooai_cli.py list

# 예상 출력:
# ID                   Name              Type  Vertices  Timesteps
# abc123...            Test Simulation   CSV   4         1
# xyz789...            CLI Test          CSV   4         1
```

**✅ 체크포인트**: CLI가 정상 동작하는가?

---

## Phase 3: 프론트엔드 단독 테스트

### 3.1 의존성 설치

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 예상 소요 시간: 3-5분
# 예상 출력: added X packages in Ys
```

**✅ 체크포인트**: 설치 중 에러 없이 완료되었는가?

### 3.2 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**내용** (.env):
```env
VITE_API_BASE_URL=http://localhost:8000
```

**✅ 체크포인트**: API URL이 백엔드와 일치하는가?

### 3.3 TypeScript 타입 체크

```bash
# 타입 체크
npm run build

# 예상 출력:
# vite v7.1.7 building for production...
# ✓ X modules transformed.
# dist/index.html  Y.YY kB
# ...
# ✓ built in Z.ZZs
```

**✅ 체크포인트**: 빌드가 성공했는가?

### 3.4 개발 서버 시작

```bash
# 개발 서버 실행
npm run dev

# 예상 출력:
# VITE v7.1.7  ready in 500 ms
#
# ➜  Local:   http://localhost:5173/
# ➜  Network: use --host to expose
```

**✅ 체크포인트**: 서버가 시작되었는가?

### 3.5 브라우저 테스트

브라우저에서 http://localhost:5173 접속

**체크리스트**:
- [ ] 페이지가 로드되는가?
- [ ] 네비게이션 바가 보이는가? (Upload, Simulations)
- [ ] Material-UI 스타일이 적용되었는가?
- [ ] 콘솔 에러가 없는가? (F12 → Console 탭)

**✅ 체크포인트**: 프론트엔드가 정상 렌더링되는가?

---

## Phase 4: 통합 테스트

### 4.1 백엔드 + 프론트엔드 동시 실행

**상태 확인**:
- 터미널 1: 백엔드 API 서버 실행 중 (http://localhost:8000)
- 터미널 2: 프론트엔드 dev 서버 실행 중 (http://localhost:5173)

### 4.2 파일 업로드 테스트 (웹 UI)

1. **업로드 페이지 접속**
   - 브라우저: http://localhost:5173/upload

2. **파일 선택**
   - "Choose File" 버튼 클릭
   - `/tmp/test_simulation.csv` 선택
   - 이름 자동 채워짐 확인

3. **옵션 설정**
   - "Analyze on upload" 체크박스 확인

4. **업로드 실행**
   - "Upload" 버튼 클릭
   - 진행률 바 표시 확인
   - 성공 메시지 확인

5. **자동 이동**
   - 시뮬레이션 상세 페이지로 자동 이동
   - URL: `/simulations/[id]`

**✅ 체크포인트**: 파일 업로드 → 상세 페이지 이동이 성공했는가?

### 4.3 시뮬레이션 목록 테스트

1. **목록 페이지 접속**
   - 네비게이션: "Simulations" 클릭
   - 또는 직접: http://localhost:5173/simulations

2. **카드 표시 확인**
   - 업로드한 시뮬레이션이 카드로 표시되는가?
   - 이름, 타입, 타임스텝 수가 정확한가?
   - 생성 날짜가 표시되는가?

3. **반응형 확인**
   - 브라우저 창 크기 조절
   - 카드 레이아웃 변경 확인 (1열 → 2열 → 3열)

**✅ 체크포인트**: 목록이 정상 표시되는가?

### 4.4 시뮬레이션 상세 페이지 테스트

1. **카드 클릭**
   - 시뮬레이션 카드 클릭
   - 상세 페이지로 이동

2. **정보 섹션 확인**
   - Type (CSV)
   - Simulation ID
   - Number of Timesteps
   - Time Range
   - Fields 목록

3. **3D 뷰어 확인**
   - 3D Canvas 렌더링 확인
   - Placeholder 큐브 회전 확인
   - 마우스 드래그로 회전 테스트
   - 스크롤로 줌 테스트
   - "Reset View" 버튼 테스트

4. **탭 전환**
   - [Overview] [3D View] [Analysis] 탭 클릭
   - 각 탭 내용 확인

**✅ 체크포인트**: 상세 페이지가 정상 동작하는가?

### 4.5 필드 분석 테스트 (UI)

1. **Analysis 탭 클릭**

2. **필드 선택**
   - 드롭다운에서 "temperature" 선택
   - Timestep 0 확인

3. **분석 옵션**
   - "Compute outliers" 체크
   - Threshold: 3.0

4. **분석 실행**
   - "Analyze" 버튼 클릭
   - 로딩 스피너 확인
   - 결과 표시 확인

5. **통계 차트 확인**
   - Recharts 막대 그래프 표시
   - Min, Mean, Max 값 확인
   - Percentiles 표시 확인

**✅ 체크포인트**: 분석 기능이 정상 동작하는가?

### 4.6 삭제 기능 테스트

1. **목록 페이지로 이동**
   - http://localhost:5173/simulations

2. **삭제 버튼 클릭**
   - 카드 우측 상단 휴지통 아이콘 클릭
   - 확인 대화상자 표시 확인

3. **삭제 확인**
   - "OK" 클릭
   - 카드가 목록에서 사라지는가?

4. **백엔드 확인**
   ```bash
   # 시뮬레이션 목록 확인 (API)
   curl http://localhost:8000/api/v1/simulations

   # 삭제된 시뮬레이션이 없어야 함
   ```

**✅ 체크포인트**: 삭제가 정상 동작하는가?

### 4.7 네트워크 통신 확인

**브라우저 개발자 도구**:
1. F12 → Network 탭
2. 페이지 새로고침
3. API 요청 확인:
   - `GET /api/v1/simulations` → 200 OK
   - `POST /api/v1/simulations/upload` → 201 Created
   - `POST /api/v1/simulations/[id]/analyze` → 200 OK

**✅ 체크포인트**: 모든 API 호출이 성공하는가? (2xx 응답)

---

## Phase 5: 고급 기능 테스트

### 5.1 고급 분석 기능 (FFT, POD, DMD)

#### 5.1.1 예제 스크립트 실행

```bash
# 프로젝트 루트로 돌아가기
cd ..

# 기본 사용 예제
python examples/01_basic_usage.py

# 예상 출력:
# 📁 시뮬레이션 파일 로드 중...
# ✅ 로드 완료!
#    - 이름: sample_simulation
#    - 타임스텝: X개
#    - 필드: temperature, pressure, ...
#
# 📊 필드 분석 중...
# 🌡️ 온도 통계:
#    - 평균: XXX.XX
#    - 최소: XXX.XX
#    - 최대: XXX.XX
```

**✅ 체크포인트**: 예제가 에러 없이 실행되는가?

#### 5.1.2 배치 처리 테스트

```bash
# 배치 처리 예제
python examples/02_batch_processing.py

# 예상 출력:
# Processing 3 files...
# [1/3] file1.csv - ✓
# [2/3] file2.csv - ✓
# [3/3] file3.csv - ✓
```

**✅ 체크포인트**: 배치 처리가 정상 동작하는가?

#### 5.1.3 시뮬레이션 비교

```bash
# 비교 예제
python examples/03_simulation_comparison.py

# 예상 출력:
# Comparing simulations...
# RMSE: X.XXXX
# Correlation: 0.XXXX
# Difference classification: moderate
```

**✅ 체크포인트**: 비교 기능이 정상 동작하는가?

### 5.2 Redis 캐싱 테스트 (선택적)

**Redis 필요**: Docker로 실행 권장

```bash
# Redis 실행 (Docker)
docker run -d -p 6379:6379 --name kooai-redis redis:latest

# .env 파일 수정
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# API 서버 재시작
# Ctrl+C → uvicorn src.presentation.api.main:app --reload
```

**캐싱 테스트**:
```bash
# 첫 번째 분석 (캐시 미스)
time curl -X POST http://localhost:8000/api/v1/simulations/$SIM_ID/analyze \
  -H "Content-Type: application/json" \
  -d '{"field_name": "temperature", "timestep": 0}'

# 두 번째 분석 (캐시 히트 - 더 빠름)
time curl -X POST http://localhost:8000/api/v1/simulations/$SIM_ID/analyze \
  -H "Content-Type: application/json" \
  -d '{"field_name": "temperature", "timestep": 0}'

# 예상 결과:
# 첫 번째: 0.5s
# 두 번째: 0.05s (10배 빠름)
```

**✅ 체크포인트**: 캐싱으로 성능이 향상되는가?

### 5.3 Celery 백그라운드 작업 (선택적)

**Redis 필요** (위에서 실행)

```bash
# Celery worker 실행 (새 터미널)
celery -A celery_worker worker -Q simulation --loglevel=info

# 예상 출력:
# [tasks]
#   . src.infrastructure.tasks.simulation.parse_simulation_async
#   . src.infrastructure.tasks.analysis.analyze_field_async
#
# [2025-11-17 12:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
# [2025-11-17 12:00:00,001: INFO/MainProcess] mingle: searching for neighbors
# [2025-11-17 12:00:00,100: INFO/MainProcess] mingle: sync complete
# celery@hostname ready.
```

**비동기 작업 테스트**:
```bash
# 비동기 파싱 요청 (API)
curl -X POST http://localhost:8000/api/v1/tasks/parse \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/tmp/test_simulation.csv"}'

# 예상 출력:
# {
#   "task_id": "task-abc123...",
#   "status": "pending"
# }

# Worker 터미널에서 작업 실행 확인:
# [2025-11-17 12:00:01,000: INFO/MainProcess] Task parse_simulation_async[task-abc123...] received
# [2025-11-17 12:00:01,500: INFO/ForkPoolWorker-1] Task parse_simulation_async[task-abc123...] succeeded in 0.5s
```

**✅ 체크포인트**: Celery 작업이 정상 처리되는가?

### 5.4 Prometheus 메트릭 확인

```bash
# 메트릭 엔드포인트
curl http://localhost:8000/metrics

# 예상 출력 (Prometheus format):
# # HELP kooai_requests_total Total number of requests
# # TYPE kooai_requests_total counter
# kooai_requests_total{method="GET",endpoint="/health"} 10.0
# kooai_requests_total{method="POST",endpoint="/api/v1/simulations/upload"} 2.0
#
# # HELP kooai_request_duration_seconds Request duration
# # TYPE kooai_request_duration_seconds histogram
# kooai_request_duration_seconds_bucket{le="0.1"} 8.0
# kooai_request_duration_seconds_bucket{le="0.5"} 10.0
# ...
```

**✅ 체크포인트**: 메트릭이 수집되고 있는가?

---

## Phase 6: 성능 및 부하 테스트

### 6.1 단위 성능 테스트

```bash
# 파서 성능 벤치마크
python tests/load/benchmark.py

# 예상 출력:
# CSV Parser:
#   - Small file (1KB): 0.005s
#   - Medium file (1MB): 0.15s
#   - Large file (10MB): 1.5s
#
# VTK Parser:
#   - Small file: 0.008s
#   - Medium file: 0.20s
```

**✅ 체크포인트**: 성능이 허용 범위 내인가?

### 6.2 Locust 부하 테스트 (선택적)

```bash
# Locust 설치 (dev 프로파일에 포함)
pip install locust

# Locust 실행
locust -f locustfile.py --host=http://localhost:8000

# 브라우저에서 http://localhost:8089 접속
# - Number of users: 10
# - Spawn rate: 2
# - Start swarming
```

**테스트 시나리오**:
1. 시뮬레이션 목록 조회 (70%)
2. 시뮬레이션 업로드 (20%)
3. 필드 분석 (10%)

**목표 성능**:
- 평균 응답 시간: < 200ms
- P95 응답 시간: < 500ms
- 실패율: < 1%

**✅ 체크포인트**: 목표 성능을 달성하는가?

### 6.3 메모리 프로파일링 (선택적)

```bash
# memory_profiler 설치
pip install memory-profiler

# 프로파일링 실행
python -m memory_profiler examples/01_basic_usage.py

# 예상 출력:
# Line #    Mem usage    Increment  Occurrences   Line Contents
# ============================================================
#     10   45.1 MiB   45.1 MiB           1   def main():
#     11   45.2 MiB    0.1 MiB           1       parser = CSVParser()
#     12   47.5 MiB    2.3 MiB           1       simulation = parser.parse(...)
```

**✅ 체크포인트**: 메모리 사용량이 합리적인가? (< 500MB)

---

## 문제 해결 가이드

### 문제 1: Import 에러

**증상**:
```
ModuleNotFoundError: No module named 'src'
```

**해결**:
```bash
# 가상환경 확인
which python
# /path/to/KooAI/venv/bin/python 이어야 함

# 재설치
pip install -e .
```

### 문제 2: 데이터베이스 에러

**증상**:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: simulations
```

**해결**:
```bash
# 마이그레이션 재실행
alembic upgrade head

# 또는 초기화
rm kooai_test.db
alembic upgrade head
```

### 문제 3: Redis 연결 실패

**증상**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**해결**:
```bash
# Redis 실행 확인
docker ps | grep redis

# Redis 재시작
docker restart kooai-redis

# 또는 캐싱 비활성화
# .env 파일:
CACHE_ENABLED=false
```

### 문제 4: 프론트엔드 빌드 실패

**증상**:
```
Error: Cannot find module '@vitejs/plugin-react'
```

**해결**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 문제 5: CORS 에러

**증상** (브라우저 콘솔):
```
Access to XMLHttpRequest blocked by CORS policy
```

**해결**:
백엔드 `.env` 파일:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

API 서버 재시작 필요.

### 문제 6: 포트 충돌

**증상**:
```
OSError: [Errno 48] Address already in use
```

**해결**:
```bash
# 점유 프로세스 찾기
lsof -i :8000

# 프로세스 종료
kill -9 [PID]

# 또는 다른 포트 사용
uvicorn src.presentation.api.main:app --port 8001
```

---

## 테스트 체크리스트

### Phase 1: 환경 설정 ✅
- [ ] Python 3.11+ 설치 확인
- [ ] Node.js 18+ 설치 확인
- [ ] 가상환경 생성
- [ ] Python 의존성 설치 (`pip install -e .`)
- [ ] 의존성 충돌 없음 (`pip check`)
- [ ] .env 파일 생성 및 설정
- [ ] 데이터베이스 마이그레이션 (`alembic upgrade head`)

### Phase 2: 백엔드 ✅
- [ ] pytest 통과 (90% 이상)
- [ ] Ruff 린터 통과
- [ ] API 서버 시작 성공
- [ ] Health check 응답 정상
- [ ] API 문서 접근 가능
- [ ] 시뮬레이션 업로드 성공
- [ ] 시뮬레이션 조회 성공
- [ ] 필드 분석 성공
- [ ] CLI 도구 동작 확인

### Phase 3: 프론트엔드 ✅
- [ ] npm install 성공
- [ ] .env 파일 설정
- [ ] TypeScript 빌드 성공
- [ ] 개발 서버 시작 성공
- [ ] 브라우저 렌더링 정상
- [ ] 콘솔 에러 없음

### Phase 4: 통합 테스트 ✅
- [ ] 웹 UI 파일 업로드 성공
- [ ] 시뮬레이션 목록 표시
- [ ] 상세 페이지 표시
- [ ] 3D 뷰어 동작
- [ ] 필드 분석 (UI) 성공
- [ ] 통계 차트 표시
- [ ] 삭제 기능 동작
- [ ] 네트워크 통신 정상 (2xx 응답)

### Phase 5: 고급 기능 ✅
- [ ] 예제 스크립트 실행
- [ ] 배치 처리 동작
- [ ] 시뮬레이션 비교 동작
- [ ] Redis 캐싱 동작 (선택)
- [ ] Celery 작업 처리 (선택)
- [ ] Prometheus 메트릭 수집

### Phase 6: 성능 ✅
- [ ] 벤치마크 실행
- [ ] Locust 부하 테스트 (선택)
- [ ] 메모리 프로파일링 (선택)

---

## 테스트 결과 보고서 템플릿

```markdown
# KooAI 테스트 결과 보고서

**테스트 일시**: 2025-XX-XX
**테스트 환경**:
- OS:
- Python:
- Node.js:

## Phase 1: 환경 설정
- [ ] ✅ 모든 의존성 설치 완료
- [ ] ⚠️ [문제 설명]
- [ ] ❌ [실패 원인]

## Phase 2: 백엔드
- Pytest: X/Y passed (Z% 성공률)
- API 서버: ✅ 정상 동작
- 주요 기능: ✅ 모두 테스트 통과

## Phase 3: 프론트엔드
- 빌드: ✅ 성공
- 렌더링: ✅ 정상
- 콘솔 에러: 없음

## Phase 4: 통합 테스트
- 파일 업로드: ✅
- 데이터 조회: ✅
- 분석 기능: ✅
- 차트 표시: ✅

## Phase 5: 고급 기능
- 예제: X/Y 성공
- Redis: (테스트 안 함)
- Celery: (테스트 안 함)

## Phase 6: 성능
- 평균 응답 시간: XXXms
- 메모리 사용: XXX MB

## 종합 평가
- **전체 완성도**: XX%
- **프로덕션 준비도**: XX%
- **권장 사항**: [개선 필요 사항]
```

---

## 다음 단계

테스트를 모두 통과한 후:

1. **프로덕션 배포 준비**
   - [ ] Docker 이미지 빌드
   - [ ] 환경 변수 프로덕션 설정
   - [ ] PostgreSQL 설정
   - [ ] Redis 설정
   - [ ] 배포 문서: `docs/PRODUCTION_GUIDE.md`

2. **인증 시스템 구현** (필요 시)
   - [ ] JWT 토큰 발급
   - [ ] 사용자 관리
   - [ ] 권한 시스템

3. **모니터링 설정**
   - [ ] Prometheus + Grafana
   - [ ] 알람 규칙 설정
   - [ ] 문서: `docs/MONITORING_GUIDE.md`

---

**총 예상 시간**: 2-3시간
**난이도**: ⭐⭐⭐
**목표**: 모든 Phase에서 90% 이상 성공

**행운을 빕니다!** 🚀
