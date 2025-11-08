# Database Migration Guide

실전 데이터베이스 마이그레이션 및 운영 가이드

이 문서는 KooAI 프로젝트의 데이터베이스 마이그레이션과 운영에 대한 실무 가이드입니다.
기본 설정은 [DATABASE.md](./DATABASE.md)를 참조하세요.

---

## 목차

1. [개발 환경 설정](#1-개발-환경-설정)
2. [마이그레이션 작업 흐름](#2-마이그레이션-작업-흐름)
3. [프로덕션 배포](#3-프로덕션-배포)
4. [데이터 백업 및 복구](#4-데이터-백업-및-복구)
5. [일반적인 시나리오](#5-일반적인-시나리오)
6. [트러블슈팅](#6-트러블슈팅)

---

## 1. 개발 환경 설정

### 1.1 첫 설정 (신규 개발자)

```bash
# 1. KooAI 저장소 클론
git clone https://github.com/your-org/KooAI.git
cd KooAI

# 2. 자동 설치 실행 (가상환경 + 패키지)
./setup.sh  # Linux/macOS
# 또는
setup.bat   # Windows

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 데이터베이스 설정

# 4. PostgreSQL 시작 (Docker 사용 시)
docker-compose up -d postgres

# 5. 데이터베이스 마이그레이션
alembic upgrade head

# 6. 설치 검증
python scripts/verify_installation.py
```

### 1.2 환경 변수 설정

#### Method 1: DATABASE_URL 사용 (권장)

```bash
# .env 파일
DATABASE_URL=postgresql://kooai:changeme@localhost:5432/kooai
```

#### Method 2: 개별 변수 사용

```bash
# .env 파일
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kooai
DB_USER=kooai
DB_PASSWORD=changeme
```

#### SQLite 사용 (빠른 테스트)

```bash
# .env 파일
USE_TEST_DB=true
```

SQLite는 마이그레이션이 불필요하며, 애플리케이션 시작 시 자동으로 테이블이 생성됩니다.

### 1.3 로컬 PostgreSQL 설정

#### Docker 사용 (권장)

```bash
# PostgreSQL 컨테이너 시작
docker run -d \
  --name kooai-postgres \
  -e POSTGRES_DB=kooai \
  -e POSTGRES_USER=kooai \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 \
  -v kooai-postgres-data:/var/lib/postgresql/data \
  postgres:15-alpine

# 연결 테스트
docker exec -it kooai-postgres psql -U kooai -d kooai
```

#### 네이티브 설치

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 및 사용자 생성
sudo -u postgres psql <<EOF
CREATE DATABASE kooai;
CREATE USER kooai WITH PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE kooai TO kooai;
\q
EOF
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15

# 데이터베이스 생성
createdb kooai
psql kooai
```

---

## 2. 마이그레이션 작업 흐름

### 2.1 새로운 마이그레이션 생성

#### 스키마 변경이 필요한 경우

1. **모델 수정**

   예: `src/infrastructure/database/models.py`에서 테이블 정의 수정

   ```python
   # 예: simulations 테이블에 컬럼 추가
   class Simulation(Base):
       __tablename__ = "simulations"

       id = Column(UUID, primary_key=True)
       name = Column(String(255), nullable=False)
       # 새 컬럼 추가
       priority = Column(Integer, default=0)  # 우선순위
   ```

2. **마이그레이션 자동 생성**

   ```bash
   # Alembic이 모델 변경을 감지하여 마이그레이션 생성
   alembic revision --autogenerate -m "Add priority column to simulations"
   ```

3. **생성된 마이그레이션 검토**

   ```bash
   # alembic/versions/ 디렉토리에 새 파일 생성됨
   # 예: alembic/versions/abc123_add_priority_column.py

   cat alembic/versions/abc123_add_priority_column.py
   ```

4. **마이그레이션 수정 (필요 시)**

   자동 생성된 마이그레이션을 열어서 검토하고 필요시 수정:

   ```python
   def upgrade():
       # 자동 생성된 코드 검토
       op.add_column('simulations',
                     sa.Column('priority', sa.Integer(), nullable=True))

       # 기존 데이터에 기본값 설정 (추가 작업)
       op.execute("UPDATE simulations SET priority = 0 WHERE priority IS NULL")

       # NOT NULL 제약 조건 추가
       op.alter_column('simulations', 'priority', nullable=False)

   def downgrade():
       op.drop_column('simulations', 'priority')
   ```

5. **마이그레이션 적용**

   ```bash
   alembic upgrade head
   ```

6. **검증**

   ```bash
   # 데이터베이스 스키마 확인
   psql -U kooai -d kooai -c "\d simulations"

   # 또는 Python으로
   python -c "
   from src.infrastructure.database.models import Simulation
   print(Simulation.__table__.columns)
   "
   ```

### 2.2 데이터 마이그레이션

스키마 변경 없이 데이터만 수정하는 경우:

```bash
# 빈 마이그레이션 생성
alembic revision -m "Update simulation priorities"
```

생성된 파일 편집:

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 데이터 업데이트 쿼리
    op.execute("""
        UPDATE simulations
        SET priority =
            CASE
                WHEN status = 'failed' THEN 0
                WHEN status = 'pending' THEN 1
                WHEN status = 'processing' THEN 2
                WHEN status = 'completed' THEN 3
                ELSE 0
            END
    """)

def downgrade():
    # 롤백 시 데이터 복원 (선택사항)
    op.execute("UPDATE simulations SET priority = 0")
```

### 2.3 마이그레이션 히스토리 관리

```bash
# 현재 데이터베이스 버전 확인
alembic current

# 모든 마이그레이션 히스토리 보기
alembic history --verbose

# 특정 범위의 히스토리
alembic history -r abc123:head

# 미적용 마이그레이션 확인
alembic heads
```

---

## 3. 프로덕션 배포

### 3.1 배포 전 체크리스트

- [ ] 로컬에서 마이그레이션 테스트 완료
- [ ] 프로덕션 데이터베이스 백업 완료
- [ ] 마이그레이션 롤백 계획 수립
- [ ] 다운타임 예상 시간 계산
- [ ] 팀원들에게 배포 일정 공지
- [ ] 마이그레이션 스크립트 리뷰 완료

### 3.2 안전한 배포 절차

#### Step 1: 백업

```bash
# 프로덕션 데이터베이스 백업
ssh production-server
cd /var/backups/kooai

# 백업 생성 (timestamp 포함)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U kooai kooai > kooai_backup_${TIMESTAMP}.sql

# 압축
gzip kooai_backup_${TIMESTAMP}.sql

# 백업 확인
ls -lh kooai_backup_${TIMESTAMP}.sql.gz
```

#### Step 2: 코드 배포

```bash
# Git pull
cd /opt/kooai
git fetch origin
git checkout main
git pull origin main

# 가상환경 활성화
source venv/bin/activate

# 의존성 업데이트 (필요시)
pip install -e ".[standard]" --upgrade
```

#### Step 3: 마이그레이션 적용

```bash
# 현재 버전 확인
alembic current

# 마이그레이션 미리보기 (dry-run, 실제로는 지원되지 않음)
# 대신 로컬에서 --sql 옵션으로 SQL 생성
alembic upgrade head --sql > migration_preview.sql
cat migration_preview.sql

# 실제 마이그레이션 적용
alembic upgrade head

# 결과 확인
alembic current
```

#### Step 4: 애플리케이션 재시작

```bash
# Systemd 사용 시
sudo systemctl restart kooai-api

# Docker 사용 시
docker-compose restart api

# 로그 확인
tail -f /var/log/kooai/api.log
```

#### Step 5: 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8000/health

# 데이터베이스 연결 테스트
curl http://localhost:8000/api/v1/simulations?limit=1
```

### 3.3 롤백 절차 (마이그레이션 실패 시)

```bash
# Step 1: 애플리케이션 중지
sudo systemctl stop kooai-api

# Step 2: 마이그레이션 롤백
alembic downgrade -1  # 한 단계 롤백
# 또는
alembic downgrade <previous_revision>  # 특정 버전으로 롤백

# Step 3: 코드 롤백
git checkout <previous_commit>

# Step 4: 애플리케이션 재시작
sudo systemctl start kooai-api

# Step 5: 헬스 체크
curl http://localhost:8000/health
```

### 3.4 Zero-Downtime 배포

데이터베이스 마이그레이션으로 인한 다운타임을 최소화:

**전략 1: Backward Compatible Migrations**

```python
# 나쁜 예: 즉시 컬럼 삭제 (다운타임 발생)
def upgrade():
    op.drop_column('simulations', 'old_field')

# 좋은 예: 2단계 배포
# Phase 1: 컬럼을 nullable로 변경 (기존 코드 호환)
def upgrade():
    op.alter_column('simulations', 'old_field', nullable=True)

# Phase 2: 코드 배포 후, 별도 마이그레이션으로 컬럼 삭제
def upgrade():
    op.drop_column('simulations', 'old_field')
```

**전략 2: Blue-Green Deployment**

1. Green 환경에 새 버전 배포
2. 마이그레이션 적용
3. 트래픽을 Green으로 전환
4. Blue 환경 제거

---

## 4. 데이터 백업 및 복구

### 4.1 자동 백업 설정

#### Cron Job 설정

```bash
# crontab 편집
crontab -e

# 매일 새벽 2시에 백업
0 2 * * * /opt/kooai/scripts/backup_database.sh
```

#### 백업 스크립트 (`scripts/backup_database.sh`)

```bash
#!/bin/bash
set -e

# 설정
BACKUP_DIR="/var/backups/kooai"
DB_NAME="kooai"
DB_USER="kooai"
RETENTION_DAYS=30

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# 백업 파일명
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kooai_backup_${TIMESTAMP}.sql.gz"

# 백업 실행
echo "Starting backup: $BACKUP_FILE"
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# 백업 크기 확인
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup completed: $SIZE"

# 오래된 백업 삭제 (30일 이상)
find "$BACKUP_DIR" -name "kooai_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup retention: keeping last $RETENTION_DAYS days"
```

### 4.2 복구 절차

#### 전체 복구

```bash
# Step 1: 애플리케이션 중지
sudo systemctl stop kooai-api

# Step 2: 기존 데이터베이스 삭제 (주의!)
sudo -u postgres psql <<EOF
DROP DATABASE kooai;
CREATE DATABASE kooai;
GRANT ALL PRIVILEGES ON DATABASE kooai TO kooai;
\q
EOF

# Step 3: 백업 복구
gunzip -c /var/backups/kooai/kooai_backup_20250101_020000.sql.gz | \
  psql -U kooai kooai

# Step 4: 마이그레이션 상태 확인 및 동기화
cd /opt/kooai
source venv/bin/activate
alembic current
alembic upgrade head  # 필요시

# Step 5: 애플리케이션 재시작
sudo systemctl start kooai-api
```

#### 특정 테이블만 복구

```bash
# 백업에서 특정 테이블만 추출
pg_restore -U kooai -d kooai -t simulations /var/backups/kooai/backup.sql
```

### 4.3 Point-in-Time Recovery (PITR)

프로덕션 환경에서 권장:

```bash
# PostgreSQL WAL 아카이빙 설정
# postgresql.conf 편집
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

# 기본 백업 생성
pg_basebackup -U kooai -D /var/backups/kooai/base -Fp -Xs -P

# 특정 시점으로 복구 (recovery.conf)
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2025-01-15 14:30:00'
```

---

## 5. 일반적인 시나리오

### 5.1 시나리오 1: 새 테이블 추가

**목표**: `reports` 테이블 추가

1. **모델 정의**

   ```python
   # src/infrastructure/database/models.py
   class Report(Base):
       __tablename__ = "reports"

       id = Column(UUID, primary_key=True, default=uuid4)
       simulation_id = Column(UUID, ForeignKey("simulations.id"), nullable=False)
       report_type = Column(String(100), nullable=False)
       content = Column(JSON, default={})
       created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
   ```

2. **마이그레이션 생성**

   ```bash
   alembic revision --autogenerate -m "Add reports table"
   ```

3. **마이그레이션 적용**

   ```bash
   alembic upgrade head
   ```

### 5.2 시나리오 2: 컬럼 타입 변경

**목표**: `simulations.status`를 VARCHAR에서 ENUM으로 변경

1. **ENUM 타입 생성 마이그레이션**

   ```python
   def upgrade():
       # ENUM 타입 생성
       status_enum = sa.Enum(
           'pending', 'processing', 'completed', 'failed', 'cancelled',
           name='simulation_status'
       )
       status_enum.create(op.get_bind())

       # 기존 컬럼을 임시로 변경
       op.alter_column('simulations', 'status',
                       new_column_name='status_old')

       # 새 컬럼 추가
       op.add_column('simulations',
                     sa.Column('status', status_enum, nullable=False))

       # 데이터 마이그레이션
       op.execute("""
           UPDATE simulations
           SET status = status_old::simulation_status
       """)

       # 기존 컬럼 삭제
       op.drop_column('simulations', 'status_old')

   def downgrade():
       # VARCHAR로 복원
       op.alter_column('simulations', 'status',
                       type_=sa.String(50))
       op.execute("DROP TYPE simulation_status")
   ```

### 5.3 시나리오 3: 외래 키 추가

**목표**: `datasets.created_by` 컬럼 추가 및 `users` 테이블 참조

1. **마이그레이션 생성**

   ```python
   def upgrade():
       # 컬럼 추가 (nullable)
       op.add_column('datasets',
                     sa.Column('created_by', sa.UUID(), nullable=True))

       # 외래 키 제약 조건 추가
       op.create_foreign_key(
           'fk_datasets_created_by',
           'datasets', 'users',
           ['created_by'], ['id']
       )

   def downgrade():
       op.drop_constraint('fk_datasets_created_by', 'datasets')
       op.drop_column('datasets', 'created_by')
   ```

### 5.4 시나리오 4: 인덱스 추가

**목표**: 자주 조회되는 컬럼에 인덱스 추가

```python
def upgrade():
    # 단일 컬럼 인덱스
    op.create_index('idx_simulations_status', 'simulations', ['status'])

    # 복합 인덱스
    op.create_index(
        'idx_simulations_status_created_at',
        'simulations',
        ['status', 'created_at']
    )

    # 부분 인덱스 (PostgreSQL)
    op.execute("""
        CREATE INDEX idx_simulations_active
        ON simulations(status)
        WHERE status IN ('pending', 'processing')
    """)

def downgrade():
    op.drop_index('idx_simulations_status')
    op.drop_index('idx_simulations_status_created_at')
    op.drop_index('idx_simulations_active')
```

### 5.5 시나리오 5: 대용량 데이터 마이그레이션

**목표**: 수백만 행의 데이터 변환

```python
def upgrade():
    # 배치 처리로 대용량 데이터 업데이트
    connection = op.get_bind()

    # 1. 임시 컬럼 추가
    op.add_column('simulations',
                  sa.Column('new_field', sa.String(255), nullable=True))

    # 2. 배치로 데이터 변환 (10000개씩)
    batch_size = 10000
    offset = 0

    while True:
        result = connection.execute(f"""
            UPDATE simulations
            SET new_field = transform_function(old_field)
            WHERE id IN (
                SELECT id FROM simulations
                WHERE new_field IS NULL
                LIMIT {batch_size}
            )
        """)

        if result.rowcount == 0:
            break

        offset += batch_size
        print(f"Processed {offset} rows...")

    # 3. NULL 체크 및 제약 조건 추가
    op.alter_column('simulations', 'new_field', nullable=False)

    # 4. 기존 컬럼 삭제
    op.drop_column('simulations', 'old_field')

def downgrade():
    # 롤백 로직...
    pass
```

---

## 6. 트러블슈팅

### 6.1 문제: 마이그레이션 충돌

**증상**: `alembic upgrade head` 실패

```
FAILED: Multiple head revisions are present
```

**해결**:

```bash
# 1. 현재 헤드 확인
alembic heads

# 2. 두 브랜치를 병합하는 마이그레이션 생성
alembic merge -m "Merge branches" <head1> <head2>

# 3. 병합 마이그레이션 적용
alembic upgrade head
```

### 6.2 문제: 마이그레이션 상태 불일치

**증상**: 데이터베이스 스키마와 Alembic 히스토리가 맞지 않음

**해결**:

```bash
# 1. 현재 데이터베이스 버전 확인
psql -U kooai -d kooai -c "\d alembic_version"

# 2. 실제 적용되어야 할 버전 확인
alembic current

# 3. 강제로 버전 동기화 (주의: 스키마가 실제로 일치하는 경우만)
alembic stamp head
```

### 6.3 문제: 마이그레이션 실패 후 복구

**증상**: 마이그레이션 중 오류 발생

```bash
# 1. 현재 상태 확인
alembic current
psql -U kooai -d kooai -c "SELECT * FROM alembic_version"

# 2. 실패한 마이그레이션 식별
alembic history

# 3. 트랜잭션이 열린 경우 롤백
psql -U kooai -d kooai -c "ROLLBACK"

# 4. 수동으로 스키마 정리 (필요시)
psql -U kooai -d kooai
-- 추가된 테이블/컬럼 제거

# 5. Alembic 버전 테이블 수정
UPDATE alembic_version SET version_num = '<previous_revision>';

# 6. 마이그레이션 스크립트 수정 후 재시도
alembic upgrade head
```

### 6.4 문제: 연결 풀 고갈

**증상**: `TimeoutError: QueuePool limit of size 10 overflow 5 reached`

**해결**:

```bash
# .env 파일 수정
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# 또는 코드에서
# src/infrastructure/database/connection.py
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**근본 원인 진단**:

```python
# 세션이 제대로 닫히는지 확인
async with get_db_session() as session:
    # 작업 수행
    pass  # 자동으로 세션 종료
```

### 6.5 문제: 느린 마이그레이션

**증상**: 마이그레이션이 몇 시간씩 걸림

**해결**:

1. **인덱스를 나중에 생성**

   ```python
   def upgrade():
       # 1. 컬럼 추가 (빠름)
       op.add_column('simulations', sa.Column('new_field', sa.String(255)))

       # 2. 데이터 변환
       op.execute("UPDATE simulations SET new_field = old_field")

       # 3. 인덱스는 CONCURRENTLY 생성 (PostgreSQL)
       op.execute("""
           CREATE INDEX CONCURRENTLY idx_simulations_new_field
           ON simulations(new_field)
       """)
   ```

2. **배치 처리 사용** (시나리오 5.5 참조)

3. **다운타임 수용**

   큰 테이블의 경우 마이그레이션 중 다운타임을 계획하는 것이 더 안전할 수 있습니다.

### 6.6 문제: 외래 키 제약 조건 위반

**증상**: `IntegrityError: foreign key constraint fails`

**해결**:

```bash
# 1. 고아 레코드 확인
psql -U kooai -d kooai <<EOF
SELECT d.id
FROM datasets d
LEFT JOIN simulations s ON d.simulation_id = s.id
WHERE s.id IS NULL;
EOF

# 2. 고아 레코드 처리
# Option A: 삭제
DELETE FROM datasets
WHERE simulation_id NOT IN (SELECT id FROM simulations);

# Option B: NULL로 설정 (외래 키가 nullable인 경우)
UPDATE datasets
SET simulation_id = NULL
WHERE simulation_id NOT IN (SELECT id FROM simulations);
```

---

## 부록: 유용한 명령어 모음

### Alembic 명령어

```bash
# 현재 버전 확인
alembic current

# 히스토리 확인
alembic history
alembic history --verbose

# 업그레이드
alembic upgrade head          # 최신 버전
alembic upgrade +1            # 한 단계
alembic upgrade <revision>    # 특정 버전

# 다운그레이드
alembic downgrade -1          # 한 단계 롤백
alembic downgrade <revision>  # 특정 버전
alembic downgrade base        # 모두 롤백

# 마이그레이션 생성
alembic revision --autogenerate -m "message"
alembic revision -m "message"  # 빈 마이그레이션

# SQL 생성 (적용하지 않음)
alembic upgrade head --sql

# 버전 동기화 (강제)
alembic stamp head
```

### PostgreSQL 명령어

```bash
# 접속
psql -U kooai -d kooai

# 테이블 목록
\dt

# 테이블 구조 확인
\d simulations

# 인덱스 목록
\di

# 외래 키 확인
\d+ simulations

# 데이터베이스 크기
\l+

# 테이블 크기
\dt+

# 현재 연결 확인
SELECT * FROM pg_stat_activity;

# 느린 쿼리 찾기
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds';
```

---

## 참고 자료

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Migrations Best Practices](https://docs.sqlalchemy.org/en/14/core/metadata.html)
- [Zero-Downtime Migrations](https://engineering.theblueground.com/blog/zero-downtime-migrations/)
- [KooAI DATABASE.md](./DATABASE.md) - 기본 설정 가이드
