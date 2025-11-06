# Integration Tests

통합 테스트는 여러 컴포넌트가 함께 작동하는지 검증합니다.

## 테스트 구조

```
tests/integration/
├── conftest.py                     # 공통 fixtures 및 설정
├── test_api_integration.py         # API 엔드포인트 통합 테스트
├── test_database_integration.py    # 데이터베이스 통합 테스트
├── test_storage_integration.py     # 스토리지 통합 테스트
└── test_e2e_workflow.py           # End-to-End 워크플로우 테스트
```

## Fixtures

### 데이터베이스 Fixtures
- **`test_db_url`**: 테스트 데이터베이스 URL (기본: sqlite:///:memory:)
- **`db_engine`**: SQLAlchemy 엔진 (테스트 전후 자동 생성/삭제)
- **`db_session`**: 데이터베이스 세션 (트랜잭션 롤백 지원)
- **`simulation_repository`**: 시뮬레이션 리포지토리

### 스토리지 Fixtures
- **`temp_storage_dir`**: 임시 스토리지 디렉토리
- **`storage_backend`**: 로컬 스토리지 백엔드

### API Fixtures
- **`api_client`**: FastAPI TestClient (의존성 주입 오버라이드 포함)

### 테스트 데이터 Fixtures
- **`sample_csv_file`**: 샘플 CSV 시뮬레이션 파일
- **`sample_vtk_file`**: 샘플 VTK 시뮬레이션 파일
- **`simulation_factory`**: 시뮬레이션 생성 팩토리

## 실행 방법

### 전체 통합 테스트 실행
```bash
pytest tests/integration/ -v
```

### 특정 테스트 파일 실행
```bash
# API 통합 테스트
pytest tests/integration/test_api_integration.py -v

# 데이터베이스 통합 테스트
pytest tests/integration/test_database_integration.py -v

# 스토리지 통합 테스트
pytest tests/integration/test_storage_integration.py -v

# E2E 워크플로우 테스트
pytest tests/integration/test_e2e_workflow.py -v
```

### 특정 테스트 클래스/메서드 실행
```bash
# 특정 테스트 클래스
pytest tests/integration/test_api_integration.py::TestSimulationAPI -v

# 특정 테스트 메서드
pytest tests/integration/test_api_integration.py::TestSimulationAPI::test_upload_simulation_csv -v
```

### 커버리지와 함께 실행
```bash
pytest tests/integration/ --cov=src --cov-report=html
```

## 테스트 카테고리

### API 통합 테스트 (`test_api_integration.py`)
- **TestSimulationAPI**: 시뮬레이션 API 엔드포인트 테스트
  - 파일 업로드 (CSV, VTK)
  - 시뮬레이션 조회 (단일, 목록)
  - 필드 분석
  - 수렴성 분석
  - 공간 분석
  - 시뮬레이션 삭제
  - 에러 처리
  
- **TestHealthCheck**: 헬스 체크 엔드포인트
  - `/health`
  - `/ready`

- **TestAPIValidation**: 입력 검증 테스트
  - 필수 파라미터 누락
  - 잘못된 파라미터 형식

### 데이터베이스 통합 테스트 (`test_database_integration.py`)
- **TestSimulationRepository**: 리포지토리 CRUD 작업
  - 생성 및 조회
  - 목록 조회
  - 업데이트
  - 삭제
  - 대용량 데이터 처리
  - 트랜잭션 롤백
  
- **TestDatabaseConstraints**: 데이터베이스 제약 조건
  - Unique 제약
  - Foreign key 제약
  - Null 제약

- **TestDatabasePerformance**: 성능 테스트
  - 대량 삽입
  - 쿼리 성능

### 스토리지 통합 테스트 (`test_storage_integration.py`)
- **TestStorageBackend**: 스토리지 기본 작업
  - 업로드/다운로드
  - 파일 존재 확인
  - 파일 삭제
  - 파일 목록 조회
  - 메타데이터 관리
  - 파일 복사/이동
  - 대용량 파일 처리
  - 스트림 다운로드

- **TestStorageCleanup**: 정리 작업
  - 오래된 파일 정리
  - 대량 삭제

- **TestStorageEdgeCases**: 엣지 케이스
  - 빈 파일
  - 존재하지 않는 파일
  - 특수 문자

### E2E 워크플로우 테스트 (`test_e2e_workflow.py`)
- **TestSimulationWorkflow**: 완전한 시뮬레이션 처리 흐름
  - 업로드 → 분석 → 조회 → 삭제
  - 다중 필드 분석
  - 배치 업로드
  - 에러 복구

- **TestConcurrentWorkflows**: 동시 실행 테스트
  - 동시 업로드
  - 동시 분석

- **TestPerformanceWorkflow**: 성능 테스트
  - 업로드 성능
  - 분석 성능

- **TestDataIntegrity**: 데이터 무결성
  - 데이터 일관성
  - 필드 데이터 보존

## 환경 변수

테스트 실행 시 다음 환경 변수를 설정할 수 있습니다:

```bash
# 테스트 데이터베이스 URL
export TEST_DATABASE_URL="sqlite:///:memory:"

# PostgreSQL 사용 시
export TEST_DATABASE_URL="postgresql://user:pass@localhost/test_db"

# 테스트 스토리지 경로
export TEST_STORAGE_PATH="/tmp/test_storage"
```

## 테스트 데이터

통합 테스트는 fixtures를 통해 자동으로 테스트 데이터를 생성합니다:

### 샘플 CSV 파일
```csv
x,y,z,temperature,pressure
0.0,0.0,0.0,300.0,101325.0
1.0,0.0,0.0,350.0,101330.0
0.0,1.0,0.0,400.0,101340.0
1.0,1.0,0.0,450.0,101350.0
```

### 샘플 VTK 파일
```
# vtk DataFile Version 2.0
Test VTK file
ASCII
DATASET POLYDATA
POINTS 4 float
0.0 0.0 0.0
1.0 0.0 0.0
0.0 1.0 0.0
1.0 1.0 0.0
POINT_DATA 4
SCALARS temperature float 1
LOOKUP_TABLE default
300.0
350.0
400.0
450.0
```

### 시뮬레이션 팩토리
`simulation_factory` fixture를 사용하여 프로그래밍 방식으로 시뮬레이션을 생성할 수 있습니다:

```python
def test_example(simulation_factory):
    # 100개 포인트를 가진 시뮬레이션 생성
    simulation = simulation_factory("Test Simulation", num_points=100)
    assert simulation.simulation_id is not None
```

## CI/CD 통합

GitHub Actions에서 통합 테스트를 실행합니다:

```yaml
- name: Run integration tests
  run: pytest tests/integration/ -v --cov=src
  env:
    TEST_DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
```

## 주의사항

1. **격리**: 각 테스트는 독립적으로 실행되며 서로 영향을 주지 않습니다
2. **클린업**: 테스트 후 자동으로 데이터베이스와 파일이 정리됩니다
3. **성능**: 통합 테스트는 단위 테스트보다 느릴 수 있습니다
4. **의존성**: 일부 테스트는 외부 서비스(Redis, PostgreSQL)가 필요할 수 있습니다

## 트러블슈팅

### 데이터베이스 연결 실패
```
Solution: TEST_DATABASE_URL 환경 변수를 확인하거나 인메모리 SQLite를 사용하세요
```

### 파일 권한 오류
```
Solution: 테스트 실행 사용자가 임시 디렉토리에 쓰기 권한이 있는지 확인하세요
```

### 포트 충돌
```
Solution: 다른 프로세스가 테스트 포트를 사용하고 있지 않은지 확인하세요
```

## 기여 가이드

새로운 통합 테스트를 추가할 때:

1. 적절한 테스트 파일을 선택하거나 새로 생성
2. 필요한 fixtures를 `conftest.py`에 추가
3. 테스트 메서드에 설명적인 docstring 작성
4. 에러 케이스와 엣지 케이스 포함
5. 테스트 후 리소스 정리 확인

예시:
```python
def test_new_feature(api_client, simulation_factory):
    """Test new feature end-to-end"""
    # Arrange
    simulation = simulation_factory("Test")
    
    # Act
    response = api_client.post(f"/api/v1/simulations/{simulation.simulation_id}/new-feature")
    
    # Assert
    assert response.status_code == 200
    assert "expected_field" in response.json()
    
    # Cleanup (if needed)
    api_client.delete(f"/api/v1/simulations/{simulation.simulation_id}")
```
