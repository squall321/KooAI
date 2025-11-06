# 데이터베이스 설정 가이드 (Database Setup Guide)

KooAI는 PostgreSQL을 주 데이터베이스로 사용하며, Alembic을 통한 마이그레이션을 지원합니다.

## 빠른 시작 (Quick Start)

### 1. PostgreSQL 설치

#### Docker를 사용하는 경우 (권장)

```bash
# PostgreSQL + pgvector 실행
docker run -d \
  --name kooai-postgres \
  -e POSTGRES_DB=kooai \
  -e POSTGRES_USER=kooai \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  ankane/pgvector:latest

# 또는 docker-compose 사용
docker-compose up -d postgres
```

#### 로컬 설치

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

macOS:
```bash
brew install postgresql
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 편집:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kooai
DB_USER=kooai
DB_PASSWORD=your_secure_password
```

### 3. 데이터베이스 마이그레이션

```bash
# 최신 버전으로 마이그레이션
alembic upgrade head

# 현재 상태 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history
```

### 4. 확인

```bash
# Python으로 연결 테스트
python -c "
from src.infrastructure.database.config import get_database_url
from src.infrastructure.database.connection import DatabaseConnection
import asyncio

async def test():
    db = DatabaseConnection(get_database_url())
    print('✓ Database connection successful!')
    await db.close()

asyncio.run(test())
"
```

## 데이터베이스 스키마 (Database Schema)

### 주요 테이블

#### simulations
시뮬레이션 실행 정보를 저장합니다.

```sql
CREATE TABLE simulations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed, cancelled
    parameters JSON NOT NULL DEFAULT '{}',
    metadata JSON NOT NULL DEFAULT '{}',
    tags JSON NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by UUID
);
```

#### datasets
시뮬레이션 데이터셋 메타데이터를 저장합니다.

```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY,
    simulation_id UUID NOT NULL REFERENCES simulations(id),
    data_type VARCHAR(100) NOT NULL,  -- mesh, contour, curve, etc.
    data_format VARCHAR(50) NOT NULL,  -- json, vtk, csv, binary
    storage_path TEXT NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0,
    checksum VARCHAR(64),
    metadata JSON NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

#### analyses
분석 작업 정보를 저장합니다.

```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    simulation_id UUID NOT NULL REFERENCES simulations(id),
    model_id UUID REFERENCES ai_models(id),
    analysis_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    input_parameters JSON NOT NULL DEFAULT '{}',
    results JSON NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by UUID
);
```

#### ai_models
AI/ML 모델 메타데이터를 저장합니다.

```sql
CREATE TABLE ai_models (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL,  -- vae, transformer, cnn, etc.
    description TEXT,
    architecture JSON NOT NULL DEFAULT '{}',
    performance_metrics JSON NOT NULL DEFAULT '{}',
    training_config JSON NOT NULL DEFAULT '{}',
    storage_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    trained_by UUID
);
```

## 마이그레이션 (Migrations)

### 새 마이그레이션 생성

```bash
# 자동 생성 (권장)
alembic revision --autogenerate -m "Add new table"

# 수동 생성
alembic revision -m "Custom migration"
```

### 마이그레이션 적용

```bash
# 최신 버전으로 업그레이드
alembic upgrade head

# 특정 버전으로 업그레이드
alembic upgrade <revision>

# 한 단계 업그레이드
alembic upgrade +1
```

### 롤백

```bash
# 한 단계 다운그레이드
alembic downgrade -1

# 특정 버전으로 다운그레이드
alembic downgrade <revision>

# 모든 마이그레이션 취소
alembic downgrade base
```

## 개발 환경 설정

### SQLite 사용 (테스트용)

테스트나 빠른 개발을 위해 SQLite in-memory 데이터베이스를 사용할 수 있습니다:

```bash
# .env 파일에서
USE_TEST_DB=true
```

또는 코드에서:

```python
from src.infrastructure.database.connection import InMemoryDatabaseConnection

db = InMemoryDatabaseConnection()
await db.create_tables()
```

### 데이터베이스 리셋

```bash
# 모든 테이블 삭제 후 재생성 (주의: 데이터 손실!)
alembic downgrade base
alembic upgrade head
```

## 프로덕션 설정

### 연결 풀 튜닝

```env
# .env 파일
DB_POOL_SIZE=20          # 기본 연결 수
DB_MAX_OVERFLOW=10       # 추가 가능한 최대 연결 수
DB_POOL_PRE_PING=true    # 연결 유효성 사전 검사
DB_POOL_RECYCLE=3600     # 연결 재사용 시간 (초)
```

### 성능 최적화

1. **인덱스 추가**: 자주 조회하는 컬럼에 인덱스 생성
   ```sql
   CREATE INDEX idx_simulations_name ON simulations(name);
   CREATE INDEX idx_simulations_status ON simulations(status);
   CREATE INDEX idx_datasets_simulation_id ON datasets(simulation_id);
   ```

2. **연결 풀 모니터링**:
   ```bash
   # PostgreSQL 연결 확인
   psql -U kooai -d kooai -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **쿼리 최적화**:
   ```sql
   -- EXPLAIN으로 쿼리 성능 분석
   EXPLAIN ANALYZE SELECT * FROM simulations WHERE status = 'completed';
   ```

### 백업 및 복구

```bash
# 백업
pg_dump -U kooai kooai > backup_$(date +%Y%m%d).sql

# 압축 백업
pg_dump -U kooai kooai | gzip > backup_$(date +%Y%m%d).sql.gz

# 복구
psql -U kooai kooai < backup_20250101.sql
```

## 트러블슈팅

### 연결 오류

```bash
# PostgreSQL 실행 상태 확인
sudo systemctl status postgresql

# 포트 사용 확인
sudo lsof -i :5432

# 로그 확인
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 마이그레이션 충돌

```bash
# 현재 상태 확인
alembic current

# 충돌 해결 후 stamp
alembic stamp head
```

### 성능 문제

```sql
-- 느린 쿼리 찾기
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds';

-- 테이블 크기 확인
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## API에서 사용

FastAPI 라우트에서 데이터베이스를 사용하는 방법:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.dependencies import get_db_session
from src.infrastructure.repositories.sql_repository import SimulationRepository

router = APIRouter()

@router.get("/simulations/{id}")
async def get_simulation(
    id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """시뮬레이션 조회"""
    repo = SimulationRepository(session)
    simulation = await repo.find_by_id(id)
    
    if simulation is None:
        raise HTTPException(status_code=404, detail="Not found")
    
    return simulation
```

## 참고 자료

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
