# KooAI 아키텍처 문서

**작성일**: 2025-11-06
**버전**: 1.0.0
**아키텍처 패턴**: Clean Architecture

---

## 📋 목차

1. [개요](#개요)
2. [아키텍처 원칙](#아키텍처-원칙)
3. [계층 구조](#계층-구조)
4. [프로젝트 구조](#프로젝트-구조)
5. [핵심 컴포넌트](#핵심-컴포넌트)
6. [데이터 흐름](#데이터-흐름)
7. [의존성 관리](#의존성-관리)
8. [확장성 및 플러그인](#확장성-및-플러그인)
9. [테스트 전략](#테스트-전략)
10. [성능 최적화](#성능-최적화)

---

## 개요

KooAI는 시뮬레이션 후처리 분석을 위한 AI 기반 플랫폼으로, **Clean Architecture** 원칙을 엄격히 따릅니다. 이를 통해 높은 유지보수성, 테스트 가능성, 확장성을 확보합니다.

### 핵심 설계 목표

- ✅ **관심사의 분리** (Separation of Concerns)
- ✅ **의존성 역전** (Dependency Inversion)
- ✅ **단일 책임 원칙** (Single Responsibility)
- ✅ **테스트 가능성** (Testability)
- ✅ **확장 가능성** (Extensibility)

---

## 아키텍처 원칙

### 1. 계층 분리 (Layered Architecture)

```
┌─────────────────────────────────────────────────┐
│           Presentation Layer                     │  ← 사용자 인터페이스
│   (API, CLI)                                    │
├─────────────────────────────────────────────────┤
│           Application Layer                      │  ← 비즈니스 유스케이스
│   (Use Cases, Services)                         │
├─────────────────────────────────────────────────┤
│           Core/Domain Layer                      │  ← 비즈니스 로직
│   (Entities, Domain Services, Interfaces)       │
├─────────────────────────────────────────────────┤
│           Infrastructure Layer                   │  ← 외부 시스템 통합
│   (Database, Storage, Cache, Tasks)             │
└─────────────────────────────────────────────────┘
```

### 2. 의존성 규칙 (Dependency Rule)

**중요**: 의존성은 항상 **안쪽으로만** 향합니다.

```
Infrastructure → Application → Core
              ↑              ↑
         (depends on)   (depends on)
```

- **Core Layer**: 외부 레이어에 대한 의존성 **없음**
- **Application Layer**: Core에만 의존
- **Infrastructure Layer**: Core와 Application에 의존
- **Presentation Layer**: Application과 Core에 의존

### 3. 인터페이스 분리 (Interface Segregation)

```python
# Core Layer에 인터페이스 정의
class SimulationRepository(ABC):
    @abstractmethod
    def save(self, simulation: SimulationResult) -> str:
        pass

# Infrastructure Layer에 구현
class SQLSimulationRepository(SimulationRepository):
    def save(self, simulation: SimulationResult) -> str:
        # 실제 구현
        pass
```

---

## 계층 구조

### 🎨 Presentation Layer

**책임**: 사용자 인터페이스 및 외부 통신

**구성 요소**:
- `src/presentation/api/` - REST API (FastAPI)
- `src/presentation/cli/` - CLI 인터페이스 (Click)

**특징**:
- HTTP 요청/응답 처리
- 데이터 검증 (Pydantic)
- 에러 핸들링 및 HTTP 상태 코드
- Swagger/ReDoc 자동 문서화

**예시**:
```python
@router.post("/simulations/upload")
async def upload_simulation(
    file: UploadFile,
    use_case: UploadSimulationUseCase = Depends()
):
    request = UploadSimulationRequest(file=file)
    response = use_case.execute(request)
    return response
```

---

### 🎯 Application Layer

**책임**: 비즈니스 유스케이스 조율

**구성 요소**:
- `src/application/use_cases/` - Use Case 구현
- `src/application/services/` - Application 서비스
- `src/application/batch/` - 배치 처리
- `src/application/comparison/` - 시뮬레이션 비교
- `src/application/export/` - 데이터 내보내기
- `src/application/reporting/` - 리포트 생성

**특징**:
- 도메인 로직 조율
- 트랜잭션 관리
- 비즈니스 규칙 적용
- Repository 패턴 사용

**예시**:
```python
class AnalyzeFieldUseCase(UseCase):
    def __init__(self, repository: SimulationRepository, analyzer: FieldAnalyzer):
        self.repository = repository
        self.analyzer = analyzer

    def execute(self, request: AnalyzeFieldRequest) -> AnalyzeFieldResponse:
        # 1. 시뮬레이션 조회
        simulation = self.repository.find_by_id(request.simulation_id)

        # 2. 분석 수행
        field = simulation.get_field(request.field_name)
        stats = self.analyzer.calculate_statistics(field)

        # 3. 결과 반환
        return AnalyzeFieldResponse(statistics=stats)
```

---

### 🧠 Core/Domain Layer

**책임**: 핵심 비즈니스 로직 및 도메인 모델

**구성 요소**:
- `src/core/domain/` - 엔티티 및 값 객체
- `src/core/simulation/` - 시뮬레이션 관련 로직
- `src/core/advanced_analysis/` - 고급 분석 (POD, DMD, FFT)
- `src/core/geometry/` - 3D 기하학 처리
- `src/core/ai_models/` - AI 모델 (VAE, LLM)
- `src/core/repositories/interfaces.py` - Repository 인터페이스

**특징**:
- 외부 의존성 없음 (순수 Python)
- 불변성 (Immutable data structures)
- 도메인 전문가 언어 사용
- 자체 검증 로직 포함

**엔티티 예시**:
```python
@dataclass(frozen=True)
class SimulationResult:
    """시뮬레이션 결과 엔티티"""
    id: Optional[str]
    name: str
    file_format: str
    timesteps: List[TimeStepData]
    metadata: SimulationMetadata

    def get_field(self, field_name: str, timestep: int = 0) -> FieldData:
        """특정 필드 데이터 조회"""
        return self.timesteps[timestep].get_field(field_name)
```

---

### 🔧 Infrastructure Layer

**책임**: 외부 시스템과의 통합 및 기술적 구현

**구성 요소**:
- `src/infrastructure/database/` - 데이터베이스 (SQLAlchemy)
- `src/infrastructure/repositories/` - Repository 구현
- `src/infrastructure/storage/` - 파일 스토리지 (S3, Local)
- `src/infrastructure/cache/` - Redis 캐싱
- `src/infrastructure/tasks/` - Celery 비동기 작업
- `src/infrastructure/optimization/` - 성능 최적화

**특징**:
- 외부 라이브러리 의존
- 구현 세부사항 캡슐화
- 인터페이스 구현
- 설정 관리

**Repository 구현 예시**:
```python
class SQLSimulationRepository(SimulationRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, simulation: SimulationResult) -> str:
        model = SimulationModel.from_entity(simulation)
        self.session.add(model)
        self.session.commit()
        return model.id

    def find_by_id(self, simulation_id: str) -> SimulationResult:
        model = self.session.query(SimulationModel).get(simulation_id)
        return model.to_entity()
```

---

## 프로젝트 구조

```
KooAI/
├── src/
│   ├── core/                          # 🧠 Core Layer
│   │   ├── domain/                    # 도메인 엔티티 및 값 객체
│   │   │   ├── entities.py            # SimulationResult, AnalysisStatus
│   │   │   └── value_objects.py       # Coordinate3D, Statistics
│   │   ├── simulation/                # 시뮬레이션 처리
│   │   │   ├── models.py              # TimeStepData, FieldData
│   │   │   ├── analysis.py            # FieldAnalyzer, SpatialAnalyzer
│   │   │   └── parsers/               # CSV, VTK, VTU, HDF5 파서
│   │   ├── advanced_analysis/         # 고급 분석
│   │   │   ├── fft.py                 # FFT 분석
│   │   │   ├── pod.py                 # POD 분석
│   │   │   ├── dmd.py                 # DMD 분석
│   │   │   ├── turbulence.py          # 난류 통계
│   │   │   ├── timeseries.py          # 시계열 분석
│   │   │   └── correlation.py         # 상관관계 분석
│   │   ├── geometry/                  # 기하학 처리
│   │   │   ├── analysis.py            # 메시 분석
│   │   │   └── operations.py          # 메시 변환
│   │   ├── ai_models/                 # AI 모델
│   │   │   ├── vae/                   # VAE 모델
│   │   │   ├── adapters/              # 모델 어댑터
│   │   │   └── registry.py            # 모델 레지스트리
│   │   ├── llm/                       # LLM 통합
│   │   │   ├── clients/               # Anthropic, OpenAI, Local
│   │   │   ├── chains.py              # LLM 체인
│   │   │   └── prompts/               # 프롬프트 템플릿
│   │   ├── pipeline/                  # 파이프라인 시스템
│   │   │   ├── base.py                # Pipeline 기본 클래스
│   │   │   ├── parallel.py            # 병렬 파이프라인
│   │   │   └── stages/                # 파이프라인 스테이지
│   │   ├── data_types/                # 데이터 타입
│   │   │   ├── mesh.py                # Mesh 데이터 타입
│   │   │   ├── curve.py               # Curve 데이터 타입
│   │   │   └── contour.py             # Contour 데이터 타입
│   │   └── repositories/              # Repository 인터페이스
│   │       └── interfaces.py          # 추상 인터페이스
│   │
│   ├── application/                   # 🎯 Application Layer
│   │   ├── use_cases/                 # Use Cases
│   │   │   ├── base.py                # UseCase 기본 클래스
│   │   │   └── simulation_use_cases.py
│   │   ├── services/                  # Application 서비스
│   │   │   └── simulation_service.py
│   │   ├── batch/                     # 배치 처리
│   │   │   ├── processor.py           # BatchProcessor
│   │   │   └── pipeline.py            # Pipeline
│   │   ├── comparison/                # 시뮬레이션 비교
│   │   │   ├── comparator.py          # SimulationComparator
│   │   │   └── diff_analyzer.py       # DifferenceAnalyzer
│   │   ├── export/                    # 데이터 내보내기
│   │   │   └── exporter.py            # MultiFormatExporter
│   │   └── reporting/                 # 리포트 생성
│   │       └── generator.py           # ReportGenerator
│   │
│   ├── infrastructure/                # 🔧 Infrastructure Layer
│   │   ├── database/                  # 데이터베이스
│   │   │   ├── connection.py          # DB 연결
│   │   │   ├── models.py              # SQLAlchemy 모델
│   │   │   └── config.py              # DB 설정
│   │   ├── repositories/              # Repository 구현
│   │   │   ├── sql_repository.py      # SQL 구현
│   │   │   └── memory_simulation_repository.py  # 메모리 구현
│   │   ├── storage/                   # 파일 스토리지
│   │   │   ├── local.py               # 로컬 스토리지
│   │   │   ├── s3.py                  # S3 스토리지
│   │   │   └── factory.py             # 스토리지 팩토리
│   │   ├── cache/                     # Redis 캐싱
│   │   │   ├── redis_cache.py         # RedisCache
│   │   │   ├── decorators.py          # 캐시 데코레이터
│   │   │   └── config.py              # 캐시 설정
│   │   ├── optimization/              # 성능 최적화
│   │   │   ├── query_optimizer.py     # 쿼리 최적화
│   │   │   ├── profiling.py           # 프로파일링
│   │   │   └── compression.py         # 응답 압축
│   │   ├── tasks/                     # Celery 작업
│   │   │   ├── celery_app.py          # Celery 설정
│   │   │   ├── simulation.py          # 시뮬레이션 작업
│   │   │   └── analysis.py            # 분석 작업
│   │   └── model_storage.py           # AI 모델 스토리지
│   │
│   └── presentation/                  # 🎨 Presentation Layer
│       ├── api/                       # REST API
│       │   ├── main.py                # FastAPI app
│       │   ├── routes/                # API 라우트
│       │   ├── schemas/               # Pydantic 스키마
│       │   ├── dependencies.py        # 의존성 주입
│       │   └── exceptions.py          # 예외 처리
│       └── cli/                       # CLI
│           ├── commands.py            # CLI 명령어
│           └── utils.py               # CLI 유틸리티
│
├── tests/                             # 테스트
│   ├── unit/                          # 단위 테스트
│   ├── integration/                   # 통합 테스트
│   └── load/                          # 부하 테스트
│
├── examples/                          # 사용 예제
├── docs/                              # 문서
└── pyproject.toml                     # 프로젝트 설정
```

---

## 핵심 컴포넌트

### 1. 도메인 모델 (Domain Models)

**SimulationResult** - 시뮬레이션 결과의 루트 엔티티
```python
@dataclass(frozen=True)
class SimulationResult:
    id: Optional[str]
    name: str
    file_format: str
    timesteps: List[TimeStepData]
    metadata: SimulationMetadata
```

**TimeStepData** - 시간 단계 데이터
```python
@dataclass(frozen=True)
class TimeStepData:
    time: float
    fields: Dict[str, FieldData]
    mesh: Optional[MeshData]
```

**FieldData** - 필드 데이터
```python
@dataclass(frozen=True)
class FieldData:
    name: str
    data: np.ndarray
    type: FieldType  # SCALAR, VECTOR
```

### 2. Repository 패턴

**인터페이스 정의** (Core Layer):
```python
class SimulationRepository(ABC):
    @abstractmethod
    def save(self, simulation: SimulationResult) -> str:
        pass

    @abstractmethod
    def find_by_id(self, simulation_id: str) -> Optional[SimulationResult]:
        pass

    @abstractmethod
    def find_all(self, skip: int = 0, limit: int = 100) -> List[SimulationResult]:
        pass

    @abstractmethod
    def delete(self, simulation_id: str) -> bool:
        pass
```

**구현** (Infrastructure Layer):
- `SQLSimulationRepository` - PostgreSQL/SQLite 구현
- `MemorySimulationRepository` - 인메모리 구현 (테스트용)

### 3. Use Case 패턴

**기본 구조**:
```python
@dataclass
class Request:
    # 요청 데이터

@dataclass
class Response:
    # 응답 데이터

class UseCase(Generic[Request, Response], ABC):
    @abstractmethod
    def execute(self, request: Request) -> Response:
        pass
```

**예시**:
```python
class UploadSimulationUseCase(UseCase):
    def __init__(
        self,
        repository: SimulationRepository,
        parser_registry: ParserRegistry,
        storage: FileStorage
    ):
        self.repository = repository
        self.parser_registry = parser_registry
        self.storage = storage

    def execute(self, request: UploadRequest) -> UploadResponse:
        # 1. 파일 저장
        file_path = self.storage.save(request.file)

        # 2. 파싱
        parser = self.parser_registry.get_parser(file_path)
        simulation = parser.parse(file_path)

        # 3. 저장
        simulation_id = self.repository.save(simulation)

        # 4. 응답
        return UploadResponse(simulation_id=simulation_id)
```

---

## 데이터 흐름

### 시뮬레이션 업로드 플로우

```
User Request (HTTP)
      ↓
[Presentation] API Endpoint
      ↓
[Application] UploadSimulationUseCase
      ↓
[Infrastructure] FileStorage.save()
      ↓
[Core] Parser.parse() → SimulationResult
      ↓
[Infrastructure] Repository.save()
      ↓
[Infrastructure] Database
```

### 분석 요청 플로우

```
User Request
      ↓
[Presentation] API Endpoint
      ↓
[Application] AnalyzeFieldUseCase
      ↓
[Infrastructure] Repository.find_by_id()
      ↓
[Core] FieldAnalyzer.calculate_statistics()
      ↓
[Application] Response 생성
      ↓
[Presentation] HTTP Response
```

---

## 의존성 관리

### 의존성 주입 (Dependency Injection)

**FastAPI Dependencies**:
```python
# dependencies.py
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_simulation_repository(
    db: Session = Depends(get_db_session)
) -> SimulationRepository:
    return SQLSimulationRepository(db)

def get_upload_use_case(
    repository: SimulationRepository = Depends(get_simulation_repository),
    storage: FileStorage = Depends(get_file_storage),
    parser_registry: ParserRegistry = Depends(get_parser_registry)
) -> UploadSimulationUseCase:
    return UploadSimulationUseCase(repository, parser_registry, storage)
```

**사용**:
```python
@router.post("/upload")
async def upload(
    file: UploadFile,
    use_case: UploadSimulationUseCase = Depends()
):
    return use_case.execute(UploadRequest(file=file))
```

---

## 확장성 및 플러그인

### 플러그인 시스템

**새로운 파서 추가**:
```python
class MyCustomParser(SimulationParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == ".custom"

    def parse(self, file_path: Path) -> SimulationResult:
        # 파싱 로직
        pass

# 등록
registry = ParserRegistry()
registry.register(MyCustomParser())
```

**새로운 스토리지 백엔드 추가**:
```python
class AzureBlobStorage(FileStorage):
    def save(self, file: BinaryIO, path: str) -> str:
        # Azure Blob Storage 구현
        pass

    def load(self, path: str) -> BinaryIO:
        # 로드 로직
        pass
```

---

## 테스트 전략

### 테스트 피라미드

```
        /\
       /  \      E2E Tests (통합 테스트)
      /    \     - API 엔드포인트
     /------\    - 전체 워크플로우
    /        \
   /  Unit    \  Unit Tests (단위 테스트)
  /   Tests    \ - 도메인 로직
 /              \- Use Cases
/________________\- Repository
```

### 테스트 구조

**단위 테스트**:
```python
def test_field_analyzer_calculate_statistics():
    analyzer = FieldAnalyzer()
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    stats = analyzer.calculate_statistics(data)

    assert stats.mean == 3.0
    assert stats.min == 1.0
    assert stats.max == 5.0
```

**통합 테스트**:
```python
def test_upload_simulation_end_to_end(client, temp_csv_file):
    with open(temp_csv_file, "rb") as f:
        response = client.post(
            "/api/v1/simulations/upload",
            files={"file": f}
        )

    assert response.status_code == 200
    assert "simulation_id" in response.json()
```

---

## 성능 최적화

### 1. 캐싱 전략

**Redis 캐싱**:
```python
@cache_result(ttl=3600, key_prefix="simulation")
def get_simulation(simulation_id: str) -> SimulationResult:
    return repository.find_by_id(simulation_id)

@cache_analysis(ttl=1800, key_prefix="analysis")
def analyze_field(simulation_id: str, field_name: str) -> Statistics:
    simulation = get_simulation(simulation_id)
    field = simulation.get_field(field_name)
    return analyzer.calculate_statistics(field)
```

### 2. 쿼리 최적화

**배치 쿼리**:
```python
@batch_query(batch_size=100)
def find_simulations_by_ids(simulation_ids: List[str]) -> List[SimulationResult]:
    return repository.find_by_ids(simulation_ids)
```

### 3. 비동기 처리

**Celery 작업**:
```python
@celery_app.task(bind=True, max_retries=3)
def parse_large_simulation(self, file_path: str):
    try:
        parser = get_parser(file_path)
        simulation = parser.parse(Path(file_path))
        repository.save(simulation)
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### 4. 응답 압축

**Gzip 미들웨어**:
```python
from src.infrastructure.optimization.compression import CompressionMiddleware

app.add_middleware(CompressionMiddleware, minimum_size=1000)
```

---

## 배포 아키텍처

```
                    ┌──────────────┐
                    │  Load        │
                    │  Balancer    │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
      ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
      │ FastAPI │    │ FastAPI │    │ FastAPI │
      │ Instance│    │ Instance│    │ Instance│
      └────┬────┘    └────┬────┘    └────┬────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
      ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
      │ Celery  │    │ Celery  │    │ Celery  │
      │ Worker  │    │ Worker  │    │ Worker  │
      └────┬────┘    └────┬────┘    └────┬────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
      ┌────▼─────┐                   ┌────▼────┐
      │PostgreSQL│                   │  Redis  │
      │(Primary) │                   │ (Cache) │
      └──────────┘                   └─────────┘
           │
      ┌────▼─────┐
      │PostgreSQL│
      │(Replica) │
      └──────────┘
```

---

## 보안 고려사항

### 1. 인증 & 인가
- JWT 토큰 기반 인증 (Phase 36, 스킵됨)
- Role-based Access Control (RBAC)

### 2. 입력 검증
- Pydantic 스키마 검증
- 파일 형식 검증
- 파일 크기 제한

### 3. 데이터 보호
- Database 암호화
- HTTPS 전송
- Secrets 관리 (환경 변수)

---

## 결론

KooAI의 Clean Architecture는 다음과 같은 장점을 제공합니다:

✅ **유지보수성**: 계층 분리로 코드 변경 영향 최소화
✅ **테스트 가능성**: 의존성 주입으로 쉬운 Mock
✅ **확장성**: 플러그인 시스템으로 기능 추가 용이
✅ **독립성**: 외부 프레임워크/라이브러리 교체 가능
✅ **명확성**: 계층별 책임 명확화

**참고 문서**:
- [README.md](README.md) - 프로젝트 개요
- [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) - 개발 현황
- [INCOMPLETE_PHASES.md](INCOMPLETE_PHASES.md) - 미완료 Phase

---

**작성자**: KooAI Development Team
**최종 업데이트**: 2025-11-06
