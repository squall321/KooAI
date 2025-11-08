# KooAI 운영 매뉴얼

## 📖 목차
- [일상 운영 작업](#일상-운영-작업)
- [모니터링](#모니터링)
- [트러블슈팅 가이드](#트러블슈팅-가이드)
- [스케일링 가이드](#스케일링-가이드)
- [백업 및 복구](#백업-및-복구)
- [보안 운영](#보안-운영)
- [성능 튜닝](#성능-튜닝)

---

## 🔄 일상 운영 작업

### 서비스 상태 확인

#### 헬스 체크
```bash
# API 서버 상태
curl http://localhost:8000/health

# 상세 상태 (DB, Redis, Storage)
curl http://localhost:8000/health/ready

# Prometheus metrics
curl http://localhost:8000/metrics
```

#### 로그 확인
```bash
# 애플리케이션 로그
tail -f logs/kooai.log

# Uvicorn 로그
journalctl -u kooai-api -f

# Celery worker 로그
journalctl -u kooai-worker -f
```

#### 프로세스 확인
```bash
# API 서버
systemctl status kooai-api

# Celery worker
systemctl status kooai-worker

# Celery beat (스케줄러)
systemctl status kooai-beat

# Redis
systemctl status redis

# PostgreSQL
systemctl status postgresql
```

---

### 정기 점검 (Daily)

#### 1. 시스템 리소스 확인
```bash
# CPU, 메모리, 디스크
htop
df -h
free -h

# 디스크 I/O
iostat -x 1
```

#### 2. 데이터베이스 상태
```bash
# PostgreSQL 연결 수
psql -U kooai_user -d kooai_db -c "
  SELECT count(*) as connections 
  FROM pg_stat_activity 
  WHERE datname='kooai_db';
"

# 테이블 크기
psql -U kooai_user -d kooai_db -c "
  SELECT 
    schemaname, 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
  LIMIT 10;
"

# 느린 쿼리 확인
psql -U kooai_user -d kooai_db -c "
  SELECT 
    query, 
    calls, 
    total_time, 
    mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
"
```

#### 3. Redis 상태
```bash
# Redis 메모리 사용량
redis-cli INFO memory

# Key 개수
redis-cli DBSIZE

# Hit rate
redis-cli INFO stats | grep keyspace
```

#### 4. 캐시 히트율 확인
```bash
# Prometheus query
curl -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=rate(kooai_cache_hits_total[5m]) / (rate(kooai_cache_hits_total[5m]) + rate(kooai_cache_misses_total[5m]))'
```

---

### 정기 점검 (Weekly)

#### 1. 로그 로테이션 확인
```bash
ls -lh /var/log/kooai/
logrotate -d /etc/logrotate.d/kooai
```

#### 2. 백업 검증
```bash
# 최근 백업 확인
ls -lht /backup/kooai/ | head -10

# 백업 무결성 테스트
pg_restore --list /backup/kooai/backup_20241107.dump | head
```

#### 3. 보안 업데이트
```bash
# 시스템 패키지 업데이트
apt update && apt list --upgradable

# Python 패키지 업데이트 확인
pip list --outdated

# 보안 취약점 스캔
safety check
bandit -r src/
```

#### 4. 디스크 정리
```bash
# 오래된 로그 파일 삭제 (30일 이상)
find /var/log/kooai/ -name "*.log.*" -mtime +30 -delete

# 임시 파일 정리
find /tmp -name "kooai_*" -mtime +7 -delete

# 오래된 업로드 파일 아카이빙
# (비즈니스 로직에 따라 조정)
```

---

## 📊 모니터링

### Grafana 대시보드

#### 주요 메트릭
1. **HTTP 요청률**
   - 메트릭: `rate(kooai_http_requests_total[5m])`
   - 임계값: > 1000 req/s (경고)

2. **응답 시간 (P95)**
   - 메트릭: `histogram_quantile(0.95, kooai_http_request_duration_seconds_bucket)`
   - 임계값: > 500ms (경고), > 1s (위험)

3. **에러율**
   - 메트릭: `rate(kooai_http_requests_total{status=~"5.."}[5m])`
   - 임계값: > 1% (경고), > 5% (위험)

4. **캐시 히트율**
   - 메트릭: `kooai_cache_hit_rate`
   - 임계값: < 80% (경고)

5. **큐 크기**
   - 메트릭: `kooai_task_queue_size`
   - 임계값: > 1000 (경고), > 5000 (위험)

### Alert Rules

#### Critical Alerts (즉시 대응)
- **ApplicationDown**: API 서버 다운
- **DatabaseDown**: 데이터베이스 연결 불가
- **HighErrorRate**: 에러율 > 5%
- **DiskSpaceCritical**: 디스크 사용률 > 90%

#### Warning Alerts (모니터링 필요)
- **HighLatency**: P95 응답 시간 > 500ms
- **HighMemoryUsage**: 메모리 사용률 > 80%
- **LowCacheHitRate**: 캐시 히트율 < 80%
- **QueueBacklog**: 큐 크기 > 1000

### 로그 분석

#### 에러 로그 모니터링
```bash
# 최근 1시간 에러 개수
grep -c "ERROR" logs/kooai.log

# 에러 패턴 분석
grep "ERROR" logs/kooai.log | awk '{print $5}' | sort | uniq -c | sort -rn

# 특정 에러 추적
grep "DatabaseError" logs/kooai.log | tail -20
```

---

## 🔧 트러블슈팅 가이드

### 문제: API 응답 느림

#### 1. 원인 파악
```bash
# CPU/메모리 확인
top

# 네트워크 확인
netstat -ant | grep :8000 | wc -l

# DB 쿼리 확인
psql -U kooai_user -d kooai_db -c "
  SELECT pid, now() - query_start as duration, query
  FROM pg_stat_activity
  WHERE state = 'active' AND now() - query_start > interval '1 second'
  ORDER BY duration DESC;
"
```

#### 2. 해결 방법
- **DB 느림**: 쿼리 최적화, 인덱스 추가
- **메모리 부족**: 워커 수 감소, 메모리 증설
- **네트워크 병목**: Nginx 설정 튜닝

---

### 문제: 데이터베이스 연결 실패

#### 1. 진단
```bash
# PostgreSQL 상태
systemctl status postgresql

# 연결 테스트
psql -U kooai_user -d kooai_db -c "SELECT 1;"

# 연결 수 확인
psql -U postgres -c "
  SELECT max_conn, used, res_for_super, max_conn-used-res_for_super AS res_for_normal
  FROM 
    (SELECT count(*) used FROM pg_stat_activity) t1,
    (SELECT setting::int res_for_super FROM pg_settings WHERE name='superuser_reserved_connections') t2,
    (SELECT setting::int max_conn FROM pg_settings WHERE name='max_connections') t3;
"
```

#### 2. 해결 방법
```bash
# 연결 수 증가
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections = 200;"
sudo systemctl restart postgresql

# 유휴 연결 정리
psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE datname = 'kooai_db'
    AND pid <> pg_backend_pid()
    AND state = 'idle'
    AND state_change < now() - interval '5 minutes';
"
```

---

### 문제: Redis 메모리 부족

#### 1. 진단
```bash
# 메모리 사용량
redis-cli INFO memory | grep used_memory_human

# 가장 큰 키 찾기
redis-cli --bigkeys

# Key 만료 확인
redis-cli INFO keyspace
```

#### 2. 해결 방법
```bash
# 만료된 키 제거
redis-cli --scan --pattern "cache:*" | xargs redis-cli del

# maxmemory 증가
redis-cli CONFIG SET maxmemory 4gb

# LRU 정책 설정
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

### 문제: 디스크 공간 부족

#### 1. 진단
```bash
# 디스크 사용량
df -h

# 큰 파일 찾기
du -h /var/lib/kooai | sort -rh | head -20

# inode 확인
df -i
```

#### 2. 해결 방법
```bash
# 로그 정리
journalctl --vacuum-time=7d

# 오래된 백업 삭제
find /backup/kooai -name "*.dump" -mtime +30 -delete

# 임시 파일 정리
find /tmp -type f -mtime +7 -delete

# Docker 정리 (사용 시)
docker system prune -a
```

---

## 📈 스케일링 가이드

### 수직 스케일링 (Scale Up)

#### 1. CPU/메모리 증설
```bash
# 현재 리소스 확인
nproc
free -h

# Uvicorn worker 수 조정
# /etc/systemd/system/kooai-api.service
[Service]
ExecStart=/opt/kooai/venv/bin/uvicorn \
  --workers 8 \
  --host 0.0.0.0 \
  --port 8000

sudo systemctl daemon-reload
sudo systemctl restart kooai-api
```

#### 2. 데이터베이스 튜닝
```bash
# PostgreSQL 설정
# /etc/postgresql/15/main/postgresql.conf

# 메모리 설정 (총 메모리의 25%)
shared_buffers = 4GB
effective_cache_size = 12GB

# 연결 설정
max_connections = 200
```

---

### 수평 스케일링 (Scale Out)

#### 1. 로드 밸런서 추가
```nginx
# /etc/nginx/conf.d/kooai.conf
upstream kooai_backend {
    least_conn;
    server 192.168.1.10:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 192.168.1.11:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 192.168.1.12:8000 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    location / {
        proxy_pass http://kooai_backend;
    }
}
```

#### 2. Celery Worker 증설
```bash
# 각 서버에서
celery -A src.infrastructure.tasks.celery_app worker \
  --concurrency=4 \
  --hostname=worker-%h \
  --loglevel=info
```

#### 3. Redis Cluster
```bash
# Redis Sentinel 설정
# /etc/redis/sentinel.conf
sentinel monitor kooai-master 192.168.1.20 6379 2
sentinel down-after-milliseconds kooai-master 5000
sentinel parallel-syncs kooai-master 1
sentinel failover-timeout kooai-master 10000
```

---

## 💾 백업 및 복구

### 자동 백업 설정

#### 1. 데이터베이스 백업
```bash
# /opt/kooai/scripts/backup.sh
#!/bin/bash
BACKUP_DIR="/backup/kooai"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL 백업
pg_dump -U kooai_user -d kooai_db -F c -f "$BACKUP_DIR/db_$DATE.dump"

# 압축
gzip "$BACKUP_DIR/db_$DATE.dump"

# S3 업로드 (선택)
aws s3 cp "$BACKUP_DIR/db_$DATE.dump.gz" s3://kooai-backups/

# 30일 이상 로컬 백업 삭제
find "$BACKUP_DIR" -name "db_*.dump.gz" -mtime +30 -delete
```

#### 2. Cron 설정
```bash
# crontab -e
0 2 * * * /opt/kooai/scripts/backup.sh >> /var/log/kooai/backup.log 2>&1
```

### 복구 절차

#### 1. 데이터베이스 복구
```bash
# 서비스 중지
sudo systemctl stop kooai-api kooai-worker

# DB 복구
pg_restore -U kooai_user -d kooai_db -c /backup/kooai/db_20241107.dump

# 마이그레이션 확인
cd /opt/kooai
source venv/bin/activate
alembic current

# 서비스 시작
sudo systemctl start kooai-api kooai-worker
```

#### 2. 파일 복구
```bash
# 업로드 파일 복구
tar -xzf /backup/kooai/files_20241107.tar.gz -C /var/lib/kooai/uploads/
```

---

## 🔒 보안 운영

### 정기 보안 점검

#### 1. 패키지 취약점 스캔
```bash
# Python 패키지
safety check --full-report

# 시스템 패키지
apt list --upgradable
```

#### 2. 로그 모니터링
```bash
# 실패한 로그인 시도
grep "authentication failed" logs/kooai.log

# 의심스러운 요청
grep "403\|401" logs/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn
```

#### 3. SSL/TLS 인증서
```bash
# 만료일 확인
echo | openssl s_client -connect kooai.example.com:443 2>/dev/null | openssl x509 -noout -dates

# 갱신 (Let's Encrypt)
certbot renew --dry-run
```

---

## ⚡ 성능 튜닝

### 1. 데이터베이스 최적화
```sql
-- 인덱스 추가
CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_files_simulation_id ON files(simulation_id);

-- Vacuum
VACUUM ANALYZE simulations;
```

### 2. 캐시 최적화
```python
# TTL 조정
CACHE_TTL = {
    "simulations_list": 300,  # 5분
    "simulation_detail": 600,  # 10분
    "file_metadata": 3600,     # 1시간
}
```

### 3. Nginx 튜닝
```nginx
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
}

http {
    # 연결 유지
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # 압축
    gzip on;
    gzip_types text/plain application/json;
    
    # 버퍼 크기
    client_body_buffer_size 128k;
    client_max_body_size 5G;
}
```

---

## 📞 비상 연락망

| 역할 | 담당자 | 연락처 | 대응 범위 |
|------|--------|--------|-----------|
| DevOps Lead | - | - | 인프라 전반 |
| Backend Lead | - | - | API 서버 |
| DBA | - | - | 데이터베이스 |
| Security | - | - | 보안 사고 |

---

## 📚 참고 문서

- [Production Guide](PRODUCTION_GUIDE.md)
- [Monitoring Guide](MONITORING_GUIDE.md)
- [CI/CD Guide](CI_CD_GUIDE.md)
- [API Guide](API_GUIDE.md)

---

**최종 업데이트:** 2024-11-07
