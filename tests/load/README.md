# Load Testing & Performance Benchmarks

부하 테스트 및 성능 벤치마크 도구 모음입니다.

## 도구

### 1. Locust (locustfile.py)
분산 부하 테스트 프레임워크

### 2. Benchmark (benchmark.py)
단일 엔드포인트 성능 벤치마크

### 3. Database Performance (db_performance.py)
데이터베이스 성능 테스트

## 설치

```bash
# Locust 설치
pip install locust

# 또는 프로젝트 전체 의존성 설치
pip install -e ".[load]"
```

## 사용법

### Locust 부하 테스트

#### 웹 UI로 실행
```bash
# API 서버가 localhost:8000에서 실행 중이어야 함
locust -f tests/load/locustfile.py --host=http://localhost:8000

# 브라우저에서 http://localhost:8089 접속
# 사용자 수와 증가율 설정 후 테스트 시작
```

#### Headless 모드 (CLI)
```bash
# 100명의 사용자, 초당 10명씩 증가, 60초 동안 실행
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s

# 결과를 CSV로 저장
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --csv=results/load_test
```

#### 분산 실행
```bash
# Master 노드
locust -f tests/load/locustfile.py --master --host=http://localhost:8000

# Worker 노드 (여러 개 실행 가능)
locust -f tests/load/locustfile.py --worker --master-host=<master-ip>
```

### 사용자 클래스

#### SimulationAPIUser (기본)
모든 API 작업을 시뮬레이션하는 일반 사용자
- 업로드, 조회, 분석, 삭제 등 모든 작업 수행
- 가중치: 조회(3) > 분석(2) > 업로드(1)

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 50 \
    --spawn-rate 5
```

#### ReadOnlyUser
읽기 전용 작업만 수행
- 조회 및 분석만 실행 (업로드 없음)
- 캐시 효과 테스트에 유용

```bash
locust -f tests/load/locustfile.py ReadOnlyUser \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10
```

#### WriteHeavyUser
쓰기 작업 중심 사용자
- 주로 업로드 작업 수행
- 데이터베이스 부하 테스트용

```bash
locust -f tests/load/locustfile.py WriteHeavyUser \
    --host=http://localhost:8000 \
    --users 20 \
    --spawn-rate 2
```

### Performance Benchmark

개별 엔드포인트 성능 측정:

```bash
# 기본 실행
python tests/load/benchmark.py

# 커스텀 호스트
python tests/load/benchmark.py --host=http://production-api:8000
```

벤치마크 항목:
- Health Check (100회)
- List Simulations (50회)
- Upload Small/Medium/Large Files (10회)
- Field Analysis (20회)
- Concurrent Requests (10 동시)

출력 예시:
```
Health Check:
------------------------------------------------------------
  Requests: 100
  Errors: 0 (0.0%)
  Min: 1.23ms
  Max: 5.67ms
  Mean: 2.45ms
  Median: 2.34ms
  StdDev: 0.78ms
  P95: 3.89ms
  P99: 4.56ms
```

### Database Performance Test

데이터베이스 성능 측정:

```bash
# SQLite (기본)
python tests/load/db_performance.py

# PostgreSQL
python tests/load/db_performance.py \
    --db-url="postgresql://user:pass@localhost/testdb"
```

테스트 항목:
- Single Insert (100회)
- Bulk Insert 100/1000 (5회)
- Simple/Complex Query (50-100회)
- Update/Delete Performance (50회)
- Connection Pool Test (20 concurrent)
- Transaction Rollback (50회)

## 테스트 시나리오

### 1. 기본 부하 테스트
```bash
# 50명의 사용자, 5분 동안
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 50 \
    --spawn-rate 5 \
    --run-time 5m \
    --csv=results/basic_load
```

### 2. Spike 테스트 (급격한 부하 증가)
```bash
# 1초에 50명씩 증가하여 500명까지
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 500 \
    --spawn-rate 50 \
    --run-time 2m
```

### 3. Stress 테스트 (시스템 한계 테스트)
```bash
# 1000명의 사용자로 시스템 한계 확인
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 1000 \
    --spawn-rate 20 \
    --run-time 10m
```

### 4. Soak 테스트 (장시간 안정성)
```bash
# 100명의 사용자로 1시간 동안
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 1h
```

### 5. 읽기 전용 부하 테스트
```bash
# 캐시 효과 확인
locust -f tests/load/locustfile.py ReadOnlyUser \
    --host=http://localhost:8000 \
    --headless \
    --users 200 \
    --spawn-rate 20 \
    --run-time 5m
```

## 메트릭 분석

### Locust 메트릭
- **RPS (Requests Per Second)**: 초당 요청 수
- **Response Time**: 응답 시간 (평균, P50, P95, P99)
- **Failure Rate**: 실패율 (%)
- **Concurrent Users**: 동시 사용자 수

### 목표 성능 지표

| 엔드포인트 | P95 Response Time | RPS | Error Rate |
|-----------|-------------------|-----|-----------|
| Health Check | < 50ms | > 500 | < 0.1% |
| List Simulations | < 200ms | > 100 | < 1% |
| Upload (Small) | < 500ms | > 50 | < 2% |
| Upload (Large) | < 2000ms | > 10 | < 5% |
| Field Analysis | < 1000ms | > 20 | < 3% |

## 결과 분석

### CSV 출력 파일
```bash
# 생성되는 파일들
results/load_test_stats.csv           # 요청별 통계
results/load_test_stats_history.csv   # 시간대별 통계
results/load_test_failures.csv        # 실패 로그
```

### 분석 스크립트
```python
import pandas as pd

# 통계 로드
stats = pd.read_csv('results/load_test_stats.csv')

# 평균 응답 시간
print(stats.groupby('Name')['Average Response Time'].mean())

# RPS
print(stats.groupby('Name')['Requests/s'].sum())

# 실패율
print(stats.groupby('Name')['Failure Count'].sum() / stats.groupby('Name')['Request Count'].sum())
```

## CI/CD 통합

### GitHub Actions 예시
```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Start API server
        run: |
          docker-compose up -d
          sleep 10
      
      - name: Install dependencies
        run: pip install locust
      
      - name: Run load test
        run: |
          locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --headless \
            --users 50 \
            --spawn-rate 5 \
            --run-time 3m \
            --csv=results/load_test
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: results/
      
      - name: Check thresholds
        run: python scripts/check_performance_thresholds.py results/load_test_stats.csv
```

## 모니터링

부하 테스트 중 모니터링해야 할 메트릭:

### 시스템 메트릭
- CPU 사용률
- 메모리 사용률
- 디스크 I/O
- 네트워크 대역폭

### 애플리케이션 메트릭
- API 응답 시간
- 에러율
- 스레드/코루틴 수
- 데이터베이스 연결 수

### 데이터베이스 메트릭
- 쿼리 실행 시간
- 연결 풀 사용률
- 트랜잭션/초
- 락 대기 시간

## 문제 해결

### 높은 응답 시간
1. 데이터베이스 쿼리 최적화 확인
2. 인덱스 추가
3. 캐시 활성화
4. 연결 풀 크기 조정

### 높은 에러율
1. 로그 확인
2. 타임아웃 설정 확인
3. 리소스 제한 확인
4. 동시성 제한 확인

### 낮은 처리량
1. Worker 수 증가
2. 비동기 처리 활용
3. 배치 처리 구현
4. 불필요한 연산 제거

## 베스트 프랙티스

1. **점진적 부하 증가**: 한 번에 너무 많은 사용자를 추가하지 말 것
2. **현실적인 시나리오**: 실제 사용 패턴을 반영할 것
3. **데이터 정리**: 각 테스트 후 데이터베이스 정리
4. **반복 실행**: 여러 번 실행하여 일관성 확인
5. **베이스라인 설정**: 초기 성능을 기록하고 변화 추적
6. **격리된 환경**: 프로덕션과 분리된 환경에서 실행
7. **리소스 모니터링**: 시스템 리소스를 함께 모니터링

## 참고자료

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)
- [API Load Testing Guide](https://k6.io/docs/testing-guides/api-load-testing/)
