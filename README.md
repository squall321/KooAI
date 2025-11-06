# KooAI - AI-Powered Simulation Post-Processing Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![CI](https://github.com/yourusername/kooai/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/ci.yml)
[![Docker](https://github.com/yourusername/kooai/actions/workflows/docker.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/docker.yml)
[![Code Quality](https://github.com/yourusername/kooai/actions/workflows/code-quality.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/code-quality.yml)
[![Release](https://github.com/yourusername/kooai/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/kooai/actions/workflows/release.yml)

## 🎯 프로젝트 개요

KooAI는 시뮬레이션 후처리 분석을 위한 AI 기반 통합 솔루션 플랫폼입니다. Clean Architecture 원칙을 따르며 확장 가능하고 유지보수하기 쉬운 구조로 설계되었습니다.

### 핵심 기능

- **📊 다양한 시뮬레이션 형식 지원**: CSV, VTK Legacy ASCII, VTU (VTK XML), HDF5 등
- **🔬 고급 결과 분석**: 통계 분석, 극값 탐지, 이상치 감지, 수렴성 분석
- **📐 3D 기하학 처리**: 메시 분석, 변환, 스무딩, 서브디비전
- **🚀 REST API**: FastAPI 기반 RESTful API with 자동 문서화
- **💻 CLI 도구**: Click + Rich 기반 명령줄 인터페이스
- **🏗️ Clean Architecture**: 계층 분리, 의존성 역전, 테스트 가능한 설계

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

## 🐳 Docker 배포

### 로컬 개발 환경

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

**완료된 Phase: 16개**

- ✅ Phase 1-11: 프로젝트 기반 구조 (도메인 모델, 리포지토리, JSON 처리, AI 모델, LLM, 파이프라인, 플러그인, Transfer Learning)
- ✅ Phase 12: 3D 데이터 처리 시스템
- ✅ Phase 13: 시뮬레이션 결과 파싱 및 분석
- ✅ Phase 14: Application Use Cases 및 서비스 계층
- ✅ Phase 15: REST API (Presentation Layer)
- ✅ Phase 16: CLI 인터페이스

**구현 통계:**
- 총 코드: ~14,000+ lines
- 총 테스트: 55+ tests
- 테스트 통과율: 100%
- Average Coverage: 40-85%

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

**개발 상태**: ✅ 주요 기능 완료 (Phase 16/16)

자세한 개발 일지는 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)를 참조하세요.
