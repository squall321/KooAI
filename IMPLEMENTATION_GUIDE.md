# KooAI 구현 가이드

이 문서는 프로젝트를 처음부터 구현할 때 따라야 할 단계별 가이드입니다.

## 시작하기

현재 프로젝트는 Phase 1의 초기 설정이 완료된 상태입니다. 다음 단계로 진행하세요.

## Phase 1 완료하기

### 1.1 필요한 디렉토리 생성

```bash
# 프로젝트 디렉토리 구조 생성
mkdir -p src/{core,application,infrastructure,presentation,plugins}
mkdir -p src/core/{domain,data_types,repositories,factories,ai_models,llm,pipeline,analysis,geometry,training,search,json_processing}
mkdir -p src/application/{use_cases,services}
mkdir -p src/infrastructure/{database,repositories,monitoring}
mkdir -p src/presentation/{api,cli}
mkdir -p src/presentation/api/{routes,schemas}
mkdir -p tests/{unit,integration,api}
mkdir -p docs/{architecture,guides,api,operations}

# __init__.py 파일 생성
find src -type d -exec touch {}/__init__.py \;
```

### 1.2 의존성 설치

```bash
# 가상 환경 생성
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -e ".[dev]"

# Pre-commit 설치
pre-commit install
```

### 1.3 Docker 환경 시작

```bash
# 서비스 시작
docker-compose up -d postgres redis

# 로그 확인
docker-compose logs -f

# 연결 테스트
docker-compose exec postgres psql -U kooai -d kooai -c "SELECT version();"
docker-compose exec redis redis-cli ping
```

### 1.4 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요한 값 수정 (에디터로 열기)
# - SECRET_KEY 변경 (랜덤 문자열 생성)
# - 필요한 API 키 추가 (OpenAI 등)
```

## Phase 2로 진행: 핵심 도메인 모델

### 2.1 도메인 엔티티 구현

`src/core/domain/entities.py` 파일을 생성하고 시작:

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

@dataclass
class SimulationResult:
    """시뮬레이션 결과 엔티티"""

    id: UUID = field(default_factory=uuid4)
    name: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_as_completed(self) -> None:
        """시뮬레이션을 완료로 표시"""
        self.status = "completed"
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """시뮬레이션을 실패로 표시"""
        self.status = "failed"
        self.metadata["error"] = error_message
        self.updated_at = datetime.utcnow()

# 다른 엔티티들도 유사하게 구현...
```

### 2.2 테스트 작성

`tests/unit/domain/test_entities.py`:

```python
import pytest
from datetime import datetime
from src.core.domain.entities import SimulationResult

def test_simulation_result_creation():
    """시뮬레이션 결과 생성 테스트"""
    sim = SimulationResult(
        name="Test Simulation",
        type="CFD",
        parameters={"mesh_size": 1000}
    )

    assert sim.name == "Test Simulation"
    assert sim.type == "CFD"
    assert sim.status == "pending"
    assert isinstance(sim.id, UUID)

def test_mark_as_completed():
    """완료 표시 테스트"""
    sim = SimulationResult(name="Test", type="CFD")
    sim.mark_as_completed()

    assert sim.status == "completed"
    assert sim.updated_at > sim.created_at

# 더 많은 테스트...
```

### 2.3 테스트 실행

```bash
pytest tests/unit/domain/test_entities.py -v
```

## Phase 3: 데이터 타입 추상화

### 3.1 기본 인터페이스 정의

`src/core/data_types/base.py`:

```python
from typing import Protocol, Self, Dict, Any
from abc import abstractmethod

class IDataType(Protocol):
    """모든 데이터 타입의 기본 인터페이스"""

    @abstractmethod
    def validate(self) -> bool:
        """데이터 유효성 검증"""
        ...

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """직렬화"""
        ...

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> Self:
        """역직렬화"""
        ...
```

자세한 구현은 [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md)의 2.1절을 참조하세요.

## Phase 4: Repository 패턴

### 4.1 데이터베이스 모델 생성

`src/infrastructure/database/models.py`:

```python
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class SimulationModel(Base):
    __tablename__ = "simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    parameters = Column(JSON)
    metadata = Column(JSON)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4.2 Alembic 설정

```bash
# Alembic 초기화
alembic init alembic

# alembic.ini 수정 (sqlalchemy.url)

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial schema"

# 마이그레이션 실행
alembic upgrade head
```

## Phase 5 이후

각 Phase별 상세 구현 내용은 다음 문서를 참조하세요:

- [PROJECT_PLAN.md](PROJECT_PLAN.md) - 전체 로드맵
- [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) - 기술 설계
- [PHASE_CHECKLISTS.md](PHASE_CHECKLISTS.md) - 체크리스트

## 개발 워크플로우

### 일반적인 개발 사이클

1. **기능 브랜치 생성**
```bash
git checkout -b feature/your-feature-name
```

2. **코드 작성**
   - 도메인 로직부터 시작
   - 테스트 작성 (TDD 권장)
   - 인프라 레이어 구현

3. **테스트 실행**
```bash
pytest
```

4. **코드 품질 체크**
```bash
black src tests
ruff check src tests --fix
mypy src
```

5. **커밋**
```bash
git add .
git commit -m "feat: add new feature"
```

6. **Push 및 PR**
```bash
git push origin feature/your-feature-name
# GitHub에서 PR 생성
```

## 유용한 명령어

### Docker 관련

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 서비스 재시작
docker-compose restart api

# 모든 서비스 중지
docker-compose down

# 볼륨까지 삭제
docker-compose down -v
```

### 데이터베이스 관련

```bash
# PostgreSQL 접속
docker-compose exec postgres psql -U kooai -d kooai

# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```

### 테스트 관련

```bash
# 전체 테스트
pytest

# 특정 파일
pytest tests/unit/domain/test_entities.py

# 커버리지 포함
pytest --cov=src --cov-report=html

# 마크된 테스트만
pytest -m "integration"

# 병렬 실행
pytest -n auto
```

## 문제 해결

### Docker 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker-compose logs

# 컨테이너 상태 확인
docker-compose ps

# 재시작
docker-compose restart
```

### 의존성 문제

```bash
# pip 캐시 삭제
pip cache purge

# 가상 환경 재생성
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 데이터베이스 연결 문제

```bash
# PostgreSQL 상태 확인
docker-compose exec postgres pg_isready -U kooai

# 연결 테스트
docker-compose exec postgres psql -U kooai -d kooai -c "SELECT 1;"
```

## 다음 단계

1. [PHASE_CHECKLISTS.md](PHASE_CHECKLISTS.md)에서 현재 Phase 확인
2. 체크리스트에 따라 작업 진행
3. 각 작업 완료 후 테스트 작성 및 실행
4. PR 생성 및 리뷰 요청

## 추가 리소스

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [PyTorch 문서](https://pytorch.org/docs/)
- [Pydantic 문서](https://docs.pydantic.dev/)

프로젝트에 대한 질문이 있으면 이슈를 생성하거나 팀에 문의하세요!
