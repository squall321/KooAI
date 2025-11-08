# Production Deployment Guide

Complete guide for deploying KooAI to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Redis Configuration](#redis-configuration)
5. [Application Deployment](#application-deployment)
6. [Logging Configuration](#logging-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Security Checklist](#security-checklist)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ or RHEL 8+)
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 100GB+ SSD recommended
- **Python**: 3.11+
- **PostgreSQL**: 13+ or MySQL 8+
- **Redis**: 6+ (optional but recommended)

### Network Requirements

- Outbound internet access for package installation
- Inbound access on configured port (default: 8000)
- Access to database server (default: 5432 for PostgreSQL)
- Access to Redis server (default: 6379)

---

## Environment Configuration

### 1. Create Environment File

Create `.env` file in the project root:

```bash
# Production environment file
cp .env.example .env
```

### 2. Required Environment Variables

```bash
# Environment
ENVIRONMENT=production
KOOAI_ENV=production

# Application
HOST=0.0.0.0
PORT=8000
WORKERS=4  # Number of Uvicorn workers (typically 2-4x CPU cores)

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/kooai_production
# Or individual variables:
DB_HOST=db-host.example.com
DB_PORT=5432
DB_NAME=kooai_production
DB_USER=kooai_user
DB_PASSWORD=***SECURE_PASSWORD***

# Redis Cache
REDIS_URL=redis://redis-host:6379/0
# Or individual variables:
REDIS_HOST=redis-host.example.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=***REDIS_PASSWORD***  # If Redis requires authentication

# Storage
STORAGE_BACKEND=local  # or s3
LOCAL_STORAGE_PATH=/data/kooai/storage
# For S3:
# S3_BUCKET=kooai-production
# S3_REGION=us-west-2
# S3_ACCESS_KEY=***AWS_ACCESS_KEY***
# S3_SECRET_KEY=***AWS_SECRET_KEY***

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # Use JSON format for production
LOG_FILE=/var/log/kooai/app.log

# Security
SECRET_KEY=***GENERATE_SECURE_KEY_HERE***  # Use: openssl rand -hex 32
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOW_CREDENTIALS=true

# API Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Task Queue
CELERY_BROKER_URL=redis://redis-host:6379/1
CELERY_RESULT_BACKEND=redis://redis-host:6379/2
TASK_WORKERS=4

# Feature Flags
ENABLE_CACHING=true
ENABLE_ASYNC_TASKS=true
ENABLE_COMPRESSION=true
```

### 3. Generate Secure Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate database password
openssl rand -base64 32
```

### 4. Validate Configuration

```bash
# Check environment variables
python scripts/validate_env.py

# Test database connection
python scripts/test_db_connection.py
```

---

## Database Setup

### 1. PostgreSQL Production Setup

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql-13 postgresql-client-13

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE kooai_production;
CREATE USER kooai_user WITH ENCRYPTED PASSWORD '***SECURE_PASSWORD***';
GRANT ALL PRIVILEGES ON DATABASE kooai_production TO kooai_user;
\q
EOF
```

### 2. Run Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run Alembic migrations
alembic upgrade head

# Verify migrations
alembic current
```

### 3. Database Backup Configuration

```bash
# Create backup script
cat > /usr/local/bin/kooai-db-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backup/kooai
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U kooai_user -h localhost kooai_production | gzip > $BACKUP_DIR/kooai_$TIMESTAMP.sql.gz
# Keep only last 7 days
find $BACKUP_DIR -name "kooai_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/kooai-db-backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/kooai-db-backup.sh" | crontab -
```

---

## Redis Configuration

### 1. Install Redis

```bash
sudo apt install redis-server

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. Configure Redis for Production

Edit `/etc/redis/redis.conf`:

```conf
# Bind to specific interface (not public)
bind 127.0.0.1 ::1

# Set password
requirepass ***REDIS_PASSWORD***

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

Restart Redis:

```bash
sudo systemctl restart redis-server
```

### 3. Test Redis Connection

```bash
redis-cli -h localhost -a ***REDIS_PASSWORD*** ping
# Should return: PONG
```

---

## Application Deployment

### 1. Install Application

```bash
# Clone repository
git clone https://github.com/your-org/KooAI.git /opt/kooai
cd /opt/kooai

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies (production profile)
pip install -e ".[standard]"
```

### 2. Create Systemd Service

Create `/etc/systemd/system/kooai.service`:

```ini
[Unit]
Description=KooAI Simulation Post-Processing API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=kooai
Group=kooai
WorkingDirectory=/opt/kooai
Environment="PATH=/opt/kooai/venv/bin"
EnvironmentFile=/opt/kooai/.env

# Main application
ExecStart=/opt/kooai/venv/bin/uvicorn src.presentation.api.main:app \
    --host ${HOST} \
    --port ${PORT} \
    --workers ${WORKERS} \
    --log-config /opt/kooai/logging.conf

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/kooai/data /var/log/kooai

# Resource limits
LimitNOFILE=65535
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### 3. Create Task Worker Service

Create `/etc/systemd/system/kooai-worker.service`:

```ini
[Unit]
Description=KooAI Task Worker
After=network.target redis.service

[Service]
Type=simple
User=kooai
Group=kooai
WorkingDirectory=/opt/kooai
Environment="PATH=/opt/kooai/venv/bin"
EnvironmentFile=/opt/kooai/.env

ExecStart=/opt/kooai/venv/bin/python -m src.infrastructure.tasks.worker

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable kooai
sudo systemctl enable kooai-worker

# Start services
sudo systemctl start kooai
sudo systemctl start kooai-worker

# Check status
sudo systemctl status kooai
sudo systemctl status kooai-worker
```

### 5. Setup Nginx Reverse Proxy

Install Nginx:

```bash
sudo apt install nginx
```

Create `/etc/nginx/sites-available/kooai`:

```nginx
upstream kooai_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/kooai_access.log;
    error_log /var/log/nginx/kooai_error.log;

    # Client upload size limit
    client_max_body_size 100M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://kooai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://kooai_backend/health;
        access_log off;
    }
}
```

Enable and start Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/kooai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

---

## Logging Configuration

### 1. Create Log Directory

```bash
sudo mkdir -p /var/log/kooai
sudo chown kooai:kooai /var/log/kooai
```

### 2. Configure Log Rotation

Create `/etc/logrotate.d/kooai`:

```
/var/log/kooai/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 kooai kooai
    sharedscripts
    postrotate
        systemctl reload kooai > /dev/null 2>&1 || true
    endscript
}
```

### 3. Verify Logging

```bash
# Check logs
sudo tail -f /var/log/kooai/app.log

# Check systemd logs
sudo journalctl -u kooai -f
```

---

## Monitoring Setup

### 1. Health Check Endpoints

KooAI provides multiple health check endpoints:

```bash
# Basic liveness check
curl http://localhost:8000/api/v1/health/live

# Detailed readiness check (includes dependencies)
curl http://localhost:8000/api/v1/health/ready

# Startup probe
curl http://localhost:8000/api/v1/health/startup

# Metrics endpoint
curl http://localhost:8000/api/v1/health/metrics
```

### 2. Prometheus Metrics (Future)

The `/api/v1/health/metrics` endpoint can be extended to export Prometheus metrics.

### 3. Monitoring Script

Create `/usr/local/bin/kooai-monitor.sh`:

```bash
#!/bin/bash
# Simple monitoring script

HEALTH_URL="http://localhost:8000/api/v1/health/ready"
ALERT_EMAIL="admin@example.com"

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE != "200" ]; then
    echo "KooAI health check failed with status $RESPONSE" | \
        mail -s "KooAI Alert: Service Unhealthy" $ALERT_EMAIL

    # Restart service
    systemctl restart kooai
fi
```

Add to crontab (check every 5 minutes):

```bash
*/5 * * * * /usr/local/bin/kooai-monitor.sh
```

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets stored in environment variables (not in code)
- [ ] DATABASE_URL contains strong password
- [ ] REDIS_PASSWORD set and strong
- [ ] SECRET_KEY generated using `openssl rand -hex 32`
- [ ] ALLOWED_ORIGINS configured for production domains only
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] HTTPS enabled for all production endpoints
- [ ] Firewall configured (only allow necessary ports)
- [ ] Database accessible only from application server
- [ ] Redis accessible only from application server

### Application Security

- [ ] Rate limiting enabled (`RATE_LIMIT_ENABLED=true`)
- [ ] CORS configured correctly
- [ ] Security headers middleware active
- [ ] File upload size limits set
- [ ] SQL injection protection (using ORM)
- [ ] XSS protection enabled
- [ ] CSRF tokens for state-changing operations

### Infrastructure Security

- [ ] OS security updates enabled
- [ ] SSH key-based authentication only
- [ ] Fail2ban or similar intrusion prevention
- [ ] Firewall rules (UFW/iptables) configured
- [ ] SSL certificates valid and auto-renewing
- [ ] Regular backup schedule configured
- [ ] Monitoring and alerting active

---

## Performance Tuning

### 1. Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_simulations_created_at ON simulations(created_at);
CREATE INDEX idx_simulations_status ON simulations(status);

-- Vacuum regularly
VACUUM ANALYZE;

-- Connection pooling (in DATABASE_URL)
postgresql://user:pass@host/db?pool_size=20&max_overflow=10
```

### 2. Redis Optimization

```conf
# Increase max clients
maxclients 10000

# Use appropriate eviction policy
maxmemory-policy allkeys-lru

# Disable persistence if pure cache
save ""
```

### 3. Application Tuning

```bash
# Increase worker count (2-4x CPU cores)
WORKERS=8

# Enable caching
ENABLE_CACHING=true

# Enable compression
ENABLE_COMPRESSION=true

# Tune task workers
TASK_WORKERS=4
```

### 4. Nginx Tuning

```nginx
# Worker processes
worker_processes auto;
worker_connections 4096;

# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=kooai_cache:10m max_size=1g inactive=60m;

# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
sudo journalctl -u kooai -n 100

# Check configuration
python -c "from src.presentation.api.main import app; print('✅ Config OK')"

# Check database connection
python scripts/test_db_connection.py
```

#### 2. High Memory Usage

```bash
# Check memory usage
ps aux | grep kooai | sort -k 4 -r

# Reduce workers
# Edit /etc/systemd/system/kooai.service
# Set WORKERS=2

# Restart
sudo systemctl restart kooai
```

#### 3. Slow Response Times

```bash
# Check database queries
# Enable slow query log in PostgreSQL
ALTER DATABASE kooai_production SET log_min_duration_statement = 1000;

# Check Redis latency
redis-cli --latency

# Check Nginx logs
sudo tail -f /var/log/nginx/kooai_access.log
```

#### 4. Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U kooai_user -d kooai_production

# Check connection limits
sudo -u postgres psql -c "SHOW max_connections;"
```

#### 5. Cache Issues

```bash
# Flush Redis cache
redis-cli -a ***PASSWORD*** FLUSHDB

# Check Redis memory
redis-cli -a ***PASSWORD*** INFO memory

# Restart Redis
sudo systemctl restart redis-server
```

### Performance Diagnostics

```bash
# CPU usage
top -u kooai

# Disk I/O
iotop -u kooai

# Network connections
netstat -anp | grep :8000

# Open files
lsof -u kooai

# Database connections
psql -U kooai_user -d kooai_production -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Maintenance Tasks

### Daily

- Monitor logs for errors
- Check health check endpoints
- Verify backups completed

### Weekly

- Review performance metrics
- Check disk space usage
- Update security patches

### Monthly

- Review and rotate logs
- Database maintenance (VACUUM, ANALYZE)
- SSL certificate renewal check
- Dependency updates
- Security audit

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop new version
sudo systemctl stop kooai

# 2. Restore previous version
cd /opt/kooai
git checkout <previous-tag>

# 3. Rollback database migrations (if needed)
alembic downgrade -1

# 4. Restart service
sudo systemctl start kooai

# 5. Verify
curl http://localhost:8000/health
```

---

## Support

### Logs Locations

- Application logs: `/var/log/kooai/app.log`
- Systemd logs: `journalctl -u kooai`
- Nginx logs: `/var/log/nginx/kooai_*.log`
- PostgreSQL logs: `/var/log/postgresql/`
- Redis logs: `/var/log/redis/`

### Useful Commands

```bash
# Service management
sudo systemctl {start|stop|restart|status} kooai
sudo systemctl {start|stop|restart|status} kooai-worker

# Logs
sudo journalctl -u kooai -f
sudo tail -f /var/log/kooai/app.log

# Database
psql -U kooai_user -d kooai_production
alembic current
alembic history

# Redis
redis-cli -a ***PASSWORD*** INFO
redis-cli -a ***PASSWORD*** MONITOR
```

---

## Additional Resources

- [Database Migration Guide](DATABASE_GUIDE.md)
- [API Documentation](https://api.example.com/docs)
- [Architecture Overview](ARCHITECTURE.md)
- [Security Best Practices](SECURITY.md)

---

**Last Updated**: 2025-11-07
**Version**: 1.0
