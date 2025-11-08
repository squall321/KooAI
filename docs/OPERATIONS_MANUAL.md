# Operations Manual

Comprehensive operations guide for deploying, monitoring, and maintaining the KooAI platform.

## Table of Contents

- [Deployment Guide](#deployment-guide)
- [Configuration Management](#configuration-management)
- [Monitoring & Alerting](#monitoring--alerting)
- [Backup & Recovery](#backup--recovery)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Incident Response](#incident-response)
- [Maintenance Procedures](#maintenance-procedures)
- [Security Operations](#security-operations)
- [Disaster Recovery](#disaster-recovery)
- [Runbooks](#runbooks)

---

## Deployment Guide

### Prerequisites

**Infrastructure Requirements:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 100 GB SSD | 500+ GB NVMe SSD |
| Network | 100 Mbps | 1 Gbps |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

**Software Requirements:**

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker 20.10+ (optional)
- Kubernetes 1.25+ (optional)

### Production Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.9 python3.9-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    git

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

#### 2. Database Setup

```bash
# Create database user
sudo -u postgres psql
CREATE USER kooai WITH PASSWORD 'secure_password';
CREATE DATABASE kooai OWNER kooai;
GRANT ALL PRIVILEGES ON DATABASE kooai TO kooai;
\q

# Enable PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Configure PostgreSQL
sudo nano /etc/postgresql/13/main/postgresql.conf
```

**PostgreSQL Configuration:**
```conf
# Performance tuning
shared_buffers = 4GB              # 25% of RAM
effective_cache_size = 12GB       # 75% of RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1            # For SSD
effective_io_concurrency = 200    # For SSD

# Connection settings
max_connections = 100
```

#### 3. Application Deployment

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/kooai/kooai.git
cd kooai

# Create virtual environment
poetry install --only main

# Configure environment
sudo cp .env.example .env
sudo nano .env
```

**Production .env Configuration:**
```bash
# Application
APP_NAME=KooAI
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-super-secret-key-min-32-characters-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://kooai:secure_password@localhost:5432/kooai

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
OPENAI_API_KEY=sk-your-production-key
ANTHROPIC_API_KEY=sk-ant-your-production-key

# File Storage
UPLOAD_DIR=/var/kooai/uploads
MAX_UPLOAD_SIZE_MB=1000

# CORS
CORS_ORIGINS=["https://kooai.com", "https://app.kooai.com"]

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

#### 4. Run Database Migrations

```bash
poetry run alembic upgrade head
```

#### 5. Create Systemd Service

**Create `/etc/systemd/system/kooai.service`:**
```ini
[Unit]
Description=KooAI FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/kooai
Environment="PATH=/opt/kooai/.venv/bin"
ExecStart=/opt/kooai/.venv/bin/uvicorn src.presentation.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-config logging.conf

# Restart policy
Restart=always
RestartSec=10

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable kooai
sudo systemctl start kooai
sudo systemctl status kooai
```

#### 6. Configure Nginx Reverse Proxy

**Create `/etc/nginx/sites-available/kooai`:**
```nginx
upstream kooai_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name api.kooai.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.kooai.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.kooai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.kooai.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # File upload limit
    client_max_body_size 1G;

    # Timeouts
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;

    location / {
        proxy_pass http://kooai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /api/v1/ws {
        proxy_pass http://kooai_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (if any)
    location /static {
        alias /opt/kooai/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/kooai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. SSL Certificate Setup

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.kooai.com

# Auto-renewal (already configured by certbot)
sudo systemctl status certbot.timer
```

### Docker Deployment

#### Docker Compose Setup

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: kooai-web
    command: uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://kooai:password@db:5432/kooai
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
      - redis
    restart: unless-stopped

  worker:
    build: .
    container_name: kooai-worker
    command: celery -A src.infrastructure.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://kooai:password@db:5432/kooai
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    container_name: kooai-db
    environment:
      - POSTGRES_USER=kooai
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=kooai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    container_name: kooai-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: kooai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**Deploy:**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec web alembic upgrade head

# Stop
docker-compose down
```

### Kubernetes Deployment

**See separate Kubernetes deployment guide in `/docs/k8s/README.md`**

---

## Configuration Management

### Environment Variables

**Critical Settings:**

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | JWT signing | Min 32 characters |
| `DATABASE_URL` | Database connection | `postgresql://...` |
| `OPENAI_API_KEY` | LLM access | `sk-...` |
| `SENTRY_DSN` | Error tracking | `https://...` |
| `ENVIRONMENT` | Environment name | `production` |

### Configuration Files

**Location:** `/opt/kooai/.env`

**Backup:**
```bash
# Backup configuration (without secrets)
grep -v 'SECRET\|PASSWORD\|KEY' .env > .env.backup
```

**Secret Management:**

Use environment variables or secret management tools:

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id kooai/production

# HashiCorp Vault
vault kv get kooai/production

# Kubernetes Secrets
kubectl get secret kooai-secrets -o yaml
```

---

## Monitoring & Alerting

### Health Checks

**Endpoint:** `GET /api/v1/health`

```bash
# Manual check
curl https://api.kooai.com/api/v1/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-08T10:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "disk_space": "healthy"
  }
}
```

### Prometheus Metrics

**Exposed at:** `/metrics`

**Key Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request duration |
| `active_connections` | Gauge | Active WebSocket connections |
| `file_uploads_total` | Counter | Total file uploads |
| `llm_requests_total` | Counter | Total LLM requests |
| `llm_tokens_total` | Counter | Total tokens used |
| `database_connections` | Gauge | Active DB connections |

**Prometheus Configuration:**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kooai'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboards

**Import dashboards:**

1. FastAPI Dashboard: ID 14280
2. PostgreSQL Dashboard: ID 9628
3. Redis Dashboard: ID 11835

**Custom Panels:**

- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate
- LLM token usage
- File upload throughput
- WebSocket connections

### Log Aggregation

**Log Locations:**

```bash
# Application logs
/var/log/kooai/app.log

# Nginx access logs
/var/log/nginx/access.log

# Nginx error logs
/var/log/nginx/error.log

# System logs
journalctl -u kooai -f
```

**Log Rotation:**

```bash
# /etc/logrotate.d/kooai
/var/log/kooai/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload kooai
    endscript
}
```

**Centralized Logging (ELK Stack):**

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/kooai/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### Alerting Rules

**Prometheus Alerts:**

```yaml
# alerts.yml
groups:
  - name: kooai_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile response time > 2s"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"

      - alert: HighDiskUsage
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk usage > 90%"
```

---

## Backup & Recovery

### Database Backups

#### Automated Daily Backups

**Create backup script `/opt/kooai/scripts/backup_db.sh`:**

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/kooai"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kooai_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U kooai kooai | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "kooai_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE s3://kooai-backups/database/

echo "Backup completed: $BACKUP_FILE"
```

**Schedule with cron:**

```bash
# Add to crontab
sudo crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/kooai/scripts/backup_db.sh
```

#### Manual Backup

```bash
# Create backup
pg_dump -U kooai kooai > kooai_backup.sql

# Compressed backup
pg_dump -U kooai kooai | gzip > kooai_backup.sql.gz

# Backup specific tables
pg_dump -U kooai -t simulations -t analyses kooai > partial_backup.sql
```

#### Restore from Backup

```bash
# Restore from SQL file
psql -U kooai kooai < kooai_backup.sql

# Restore from compressed backup
gunzip -c kooai_backup.sql.gz | psql -U kooai kooai

# Drop and recreate database first (careful!)
sudo -u postgres psql
DROP DATABASE kooai;
CREATE DATABASE kooai OWNER kooai;
\q

# Then restore
psql -U kooai kooai < kooai_backup.sql
```

### File Storage Backups

```bash
# Backup uploaded files
rsync -av --progress /var/kooai/uploads/ /mnt/backup/uploads/

# Sync to S3
aws s3 sync /var/kooai/uploads/ s3://kooai-uploads/

# Incremental backup with rclone
rclone sync /var/kooai/uploads/ remote:kooai-uploads/
```

### Application Code Backup

```bash
# Git repository is source of truth
# Tag releases
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# Backup .env and configuration (encrypted)
tar czf config_backup.tar.gz .env logging.conf
gpg -c config_backup.tar.gz
```

### Recovery Testing

**Monthly recovery drill:**

```bash
# 1. Restore database to staging environment
# 2. Restore file uploads
# 3. Verify application functionality
# 4. Document any issues
# 5. Update recovery procedures
```

---

## Performance Tuning

### Application Performance

#### Uvicorn Workers

```bash
# Calculate optimal workers: (2 x CPU cores) + 1
# For 8 cores: 17 workers
uvicorn src.presentation.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 17 \
    --worker-class uvicorn.workers.UvicornWorker
```

#### Database Connection Pool

```python
# src/infrastructure/database/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Base connections
    max_overflow=10,        # Additional connections
    pool_pre_ping=True,     # Check connections before use
    pool_recycle=3600,      # Recycle connections every hour
)
```

### Database Performance

#### Indexing

```sql
-- Frequently queried columns
CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX idx_analyses_simulation_id ON analyses(simulation_id);

-- Composite indexes
CREATE INDEX idx_simulations_user_status
ON simulations(user_id, status);

-- Partial indexes
CREATE INDEX idx_active_simulations
ON simulations(status)
WHERE status IN ('uploaded', 'processing');
```

#### Query Optimization

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM simulations WHERE user_id = 'usr_123';
```

#### Vacuum and Analyze

```bash
# Manual vacuum
sudo -u postgres vacuumdb -z kooai

# Auto-vacuum (configured in postgresql.conf)
autovacuum = on
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
```

### Redis Performance

```bash
# Monitor Redis
redis-cli INFO stats

# Check slow queries
redis-cli SLOWLOG GET 10

# Memory usage
redis-cli INFO memory
```

### Nginx Performance

```nginx
# nginx.conf optimizations
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Compression
    gzip on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript;

    # Caching
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;

    # Buffers
    client_body_buffer_size 128k;
    client_max_body_size 1G;
}
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check service status
sudo systemctl status kooai

# View logs
sudo journalctl -u kooai -n 100 --no-pager

# Common causes:
# - Port already in use
# - Database connection failed
# - Missing environment variables
# - Permission issues

# Check port
sudo lsof -i :8000

# Check database connection
psql -U kooai -h localhost kooai -c "SELECT 1"

# Check environment
sudo -u www-data env | grep DATABASE_URL
```

#### 2. Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U kooai -h localhost kooai

# Check max connections
sudo -u postgres psql -c "SHOW max_connections;"

# View active connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < NOW() - INTERVAL '30 minutes';
"
```

#### 3. High Memory Usage

```bash
# Check memory usage
free -h
top -o %MEM

# Check application memory
ps aux | grep uvicorn

# Restart service if necessary
sudo systemctl restart kooai

# Reduce workers if needed
# Edit /etc/systemd/system/kooai.service
--workers 2  # Reduce from 4
```

#### 4. Slow API Responses

```bash
# Check application logs
tail -f /var/log/kooai/app.log

# Monitor database queries
sudo -u postgres psql kooai -c "
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
"

# Check Redis performance
redis-cli --latency

# Check system resources
vmstat 1
iostat -x 1
```

#### 5. File Upload Failures

```bash
# Check disk space
df -h

# Check upload directory permissions
ls -la /var/kooai/uploads/

# Check nginx configuration
sudo nginx -t

# Check client_max_body_size
grep client_max_body_size /etc/nginx/sites-available/kooai
```

### Debug Mode

**Enable debug logging:**

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Restart service
sudo systemctl restart kooai

# View debug logs
tail -f /var/log/kooai/app.log | grep DEBUG
```

---

## Incident Response

### Incident Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| **P0** | Complete outage | Immediate | API completely down |
| **P1** | Critical degradation | 15 minutes | Database unavailable |
| **P2** | Significant impact | 1 hour | Slow responses, errors |
| **P3** | Minor impact | 4 hours | Non-critical feature broken |
| **P4** | Cosmetic | Next business day | UI glitch |

### Incident Response Process

#### 1. Detection

- Monitoring alerts (Prometheus, Sentry)
- User reports
- Health check failures

#### 2. Triage

```bash
# Quick health check
curl https://api.kooai.com/api/v1/health

# Check service status
sudo systemctl status kooai
sudo systemctl status postgresql
sudo systemctl status redis

# Check logs for errors
sudo journalctl -u kooai -n 100 | grep ERROR

# Check resources
top
df -h
```

#### 3. Communication

- Post incident in #incidents Slack channel
- Update status page
- Notify affected customers (P0/P1)

#### 4. Mitigation

**Common mitigation steps:**

```bash
# Restart service
sudo systemctl restart kooai

# Clear Redis cache
redis-cli FLUSHALL

# Rollback deployment
git checkout v1.0.0-stable
sudo systemctl restart kooai

# Scale resources (if using Kubernetes)
kubectl scale deployment kooai --replicas=10
```

#### 5. Recovery

- Verify service is healthy
- Run smoke tests
- Monitor for recurrence

#### 6. Post-Mortem

- Document incident
- Identify root cause
- Create action items
- Update runbooks

---

## Maintenance Procedures

### Scheduled Maintenance

**Maintenance Windows:**
- Day: Sunday
- Time: 02:00-04:00 UTC
- Frequency: Monthly

**Pre-Maintenance Checklist:**

- [ ] Notify users 7 days in advance
- [ ] Create database backup
- [ ] Test changes in staging
- [ ] Prepare rollback plan
- [ ] Schedule team availability

### Rolling Updates (Zero-Downtime)

```bash
# With multiple workers

# 1. Deploy new code
git pull origin main

# 2. Reload workers one by one
# Worker 1
sudo systemctl reload kooai

# Wait 30 seconds, verify health

# Worker 2
sudo systemctl reload kooai

# Continue for all workers
```

### Database Migrations

```bash
# 1. Backup database
pg_dump -U kooai kooai > pre_migration_backup.sql

# 2. Run migration
poetry run alembic upgrade head

# 3. Verify migration
poetry run alembic current

# 4. If issues, rollback
poetry run alembic downgrade -1
```

### Security Updates

```bash
# System updates
sudo apt update
sudo apt upgrade -y

# Reboot if kernel updated
sudo reboot

# Python dependencies
poetry update

# Check for vulnerabilities
poetry run pip-audit
```

---

## Security Operations

### Security Monitoring

**Log suspicious activity:**

```bash
# Failed login attempts
grep "authentication failed" /var/log/kooai/app.log

# Rate limit violations
grep "rate limit exceeded" /var/log/kooai/app.log

# Unauthorized access attempts
grep "403\|401" /var/log/nginx/access.log
```

### SSL Certificate Management

```bash
# Check certificate expiration
echo | openssl s_client -servername api.kooai.com \
    -connect api.kooai.com:443 2>/dev/null | \
    openssl x509 -noout -dates

# Renew certificate (Let's Encrypt)
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run
```

### Secret Rotation

**Rotate JWT secret key:**

```bash
# 1. Generate new secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Update .env with new secret
# OLD_SECRET_KEY=old_value
# SECRET_KEY=new_value

# 3. Deploy with both keys (grace period)
# Allow both old and new tokens for 24 hours

# 4. Remove old secret after grace period
```

### Security Audits

**Monthly security checklist:**

- [ ] Review user access logs
- [ ] Check for outdated dependencies
- [ ] Verify firewall rules
- [ ] Review SSL configuration
- [ ] Check for exposed secrets in logs
- [ ] Verify backup encryption
- [ ] Test disaster recovery

---

## Disaster Recovery

### Recovery Point Objective (RPO)

- **Target**: 24 hours
- **Implementation**: Daily backups at 02:00 UTC

### Recovery Time Objective (RTO)

- **Target**: 4 hours
- **Components**:
  - Database restoration: 1 hour
  - Application deployment: 30 minutes
  - File restoration: 2 hours
  - Testing and verification: 30 minutes

### Disaster Recovery Plan

#### Scenario: Complete Server Failure

**Recovery Steps:**

```bash
# 1. Provision new server
# (Use infrastructure as code if available)

# 2. Install dependencies
sudo apt update && sudo apt install -y \
    python3.9 postgresql redis-server nginx

# 3. Restore database
# Get latest backup from S3
aws s3 cp s3://kooai-backups/database/latest.sql.gz .
gunzip latest.sql.gz

# Create database
sudo -u postgres createdb kooai

# Restore
psql -U postgres kooai < latest.sql

# 4. Deploy application
git clone https://github.com/kooai/kooai.git
cd kooai
git checkout production
poetry install
cp .env.backup .env

# 5. Restore file uploads
aws s3 sync s3://kooai-uploads/ /var/kooai/uploads/

# 6. Start services
sudo systemctl start kooai
sudo systemctl start nginx

# 7. Verify
curl http://localhost:8000/api/v1/health

# 8. Update DNS (if IP changed)
# Point api.kooai.com to new server IP
```

### Multi-Region Failover

**Active-Passive Configuration:**

```
Primary Region (us-east-1)
    ↓ Continuous Replication
Standby Region (us-west-2)
```

**Failover Process:**

1. Detect primary region failure
2. Promote standby database to primary
3. Update DNS to point to standby region
4. Verify application functionality
5. Investigate primary region issues

---

## Runbooks

### Runbook: High CPU Usage

**Symptoms:** CPU usage > 80% for > 5 minutes

**Investigation:**

```bash
# 1. Identify process
top -o %CPU

# 2. Check worker count
ps aux | grep uvicorn | wc -l

# 3. Check for runaway processes
ps aux | awk '$3 > 50'

# 4. Check database queries
sudo -u postgres psql kooai -c "
SELECT pid, query_start, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY query_start;
"
```

**Resolution:**

```bash
# Quick fix: Restart service
sudo systemctl restart kooai

# Long-term: Optimize code or scale resources
```

### Runbook: Database Connection Pool Exhausted

**Symptoms:** "connection pool exhausted" errors

**Investigation:**

```bash
# Check active connections
sudo -u postgres psql -c "
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;
"

# Check pool size in code
grep pool_size src/infrastructure/database/database.py
```

**Resolution:**

```bash
# 1. Kill idle connections
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < NOW() - INTERVAL '5 minutes';
"

# 2. Increase pool size (if needed)
# Edit database.py
pool_size=30  # Increase from 20

# 3. Restart application
sudo systemctl restart kooai
```

### Runbook: Disk Space Full

**Symptoms:** "No space left on device" errors

**Investigation:**

```bash
# Check disk usage
df -h

# Find large files
du -h /var/kooai | sort -rh | head -20

# Check log sizes
du -h /var/log
```

**Resolution:**

```bash
# 1. Clear old uploads (if configured)
find /var/kooai/uploads -mtime +90 -delete

# 2. Rotate logs
sudo logrotate -f /etc/logrotate.d/kooai

# 3. Clear old backups
find /var/backups/kooai -mtime +30 -delete

# 4. Clean Docker (if used)
docker system prune -a
```

---

## Monitoring Dashboard

### Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Uptime | 99.9% | < 99.5% |
| Response Time (p95) | < 500ms | > 2s |
| Error Rate | < 0.1% | > 1% |
| Database CPU | < 70% | > 85% |
| Disk Usage | < 80% | > 90% |
| Active Users | N/A | Track trend |

---

## Support Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| On-Call Engineer | oncall@kooai.com | 24/7 |
| DevOps Team | devops@kooai.com | Business hours |
| Security Team | security@kooai.com | 24/7 (emergencies) |
| Database Admin | dba@kooai.com | Business hours |

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
**Maintained By**: KooAI Operations Team
