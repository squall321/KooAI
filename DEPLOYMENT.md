# KooAI Deployment Guide

This document provides comprehensive instructions for deploying KooAI in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ (included with Docker Desktop)
- **Python**: 3.11+ (for local development)
- **Git**: For version control

### Recommended Hardware

#### Development Environment
- CPU: 2+ cores
- RAM: 4GB minimum, 8GB recommended
- Storage: 10GB free space

#### Production Environment
- CPU: 4+ cores
- RAM: 8GB minimum, 16GB recommended
- Storage: 50GB+ SSD

---

## Local Development

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/kooai.git
cd kooai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run API server
uvicorn src.presentation.api.main:app --reload

# 4. Run tests
pytest
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

Services will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Docker Deployment

### Building the Image

#### Using the Build Script

```bash
./deploy/docker-build.sh [TAG] [PLATFORM]

# Examples:
./deploy/docker-build.sh v1.0.0
./deploy/docker-build.sh latest linux/amd64
```

#### Manual Build

```bash
docker build -t kooai:latest .
```

#### Multi-platform Build

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kooai:latest \
  --push \
  .
```

### Running the Container

#### Standalone Container

```bash
docker run -d \
  --name kooai-api \
  -p 8000:8000 \
  -e KOOAI_ENV=production \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  kooai:latest
```

#### With Environment File

```bash
docker run -d \
  --name kooai-api \
  -p 8000:8000 \
  --env-file .env.production \
  kooai:latest
```

---

## Production Deployment

### Configuration

#### 1. Create Production Environment File

```bash
cp .env.production.example .env.production
```

Edit `.env.production`:

```bash
# Critical: Change these!
SECRET_KEY=<generate-random-secret-key>
POSTGRES_PASSWORD=<strong-database-password>
REDIS_PASSWORD=<strong-redis-password>

# Application
KOOAI_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
POSTGRES_USER=kooai
POSTGRES_DB=kooai

# API
API_WORKERS=4
API_REPLICAS=2
```

**Security Note**: Never commit `.env.production` to version control!

#### 2. Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate passwords
openssl rand -base64 32
```

### Deploying with Docker Compose

#### Start Production Stack

```bash
docker-compose -f docker-compose.production.yml up -d
```

This will start:
- PostgreSQL with pgvector
- Redis with authentication
- KooAI API (multiple replicas)
- Nginx reverse proxy

#### Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f

# Test API
curl http://localhost/health
```

### SSL/TLS Configuration

#### 1. Obtain SSL Certificates

Using Let's Encrypt with Certbot:

```bash
sudo certbot certonly --standalone -d yourdomain.com
```

Or use your own certificates.

#### 2. Update Nginx Configuration

Edit `deploy/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of configuration
}
```

#### 3. Mount Certificates

Update `docker-compose.production.yml`:

```yaml
nginx:
  volumes:
    - ./deploy/ssl:/etc/nginx/ssl:ro
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm (optional, recommended)

### Deploy Using Kubectl

#### 1. Create Namespace

```bash
kubectl create namespace kooai
```

#### 2. Create Secrets

```bash
kubectl create secret generic kooai-secrets \
  --from-literal=secret-key=<your-secret-key> \
  --from-literal=postgres-password=<postgres-password> \
  --from-literal=redis-password=<redis-password> \
  -n kooai
```

#### 3. Apply Configurations

```bash
kubectl apply -f k8s/ -n kooai
```

#### 4. Check Status

```bash
kubectl get pods -n kooai
kubectl get services -n kooai
```

### Scaling

```bash
# Scale API replicas
kubectl scale deployment kooai-api --replicas=5 -n kooai

# Autoscaling
kubectl autoscale deployment kooai-api \
  --min=2 --max=10 \
  --cpu-percent=80 \
  -n kooai
```

---

## Monitoring and Logging

### Prometheus Monitoring

Enable monitoring in `docker-compose.yml`:

```bash
docker-compose --profile monitoring up -d
```

Access Prometheus: http://localhost:9090

### Grafana Dashboards

Access Grafana: http://localhost:3000
- Default login: admin/admin

Import KooAI dashboard from `config/grafana/dashboards/`.

### Log Aggregation

#### Viewing Logs

```bash
# Docker Compose
docker-compose logs -f api

# Kubernetes
kubectl logs -f deployment/kooai-api -n kooai

# Follow all containers
kubectl logs -f -l app=kooai -n kooai --all-containers
```

#### Log Rotation

Configure in `docker-compose.yml`:

```yaml
api:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

---

## Troubleshooting

### Common Issues

#### 1. API Not Starting

**Symptom**: Container exits immediately

**Solutions**:
```bash
# Check logs
docker-compose logs api

# Verify environment variables
docker-compose config

# Test database connection
docker-compose exec postgres psql -U kooai -c "SELECT 1"
```

#### 2. Database Connection Failed

**Symptom**: `Could not connect to database`

**Solutions**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Verify credentials
docker-compose exec postgres pg_isready -U kooai

# Check network connectivity
docker-compose exec api ping postgres
```

#### 3. Redis Connection Issues

**Symptom**: `Connection refused` to Redis

**Solutions**:
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Verify password
docker-compose exec redis redis-cli -a <password> ping
```

#### 4. High Memory Usage

**Solutions**:
```bash
# Check resource usage
docker stats

# Limit container memory
docker update --memory 2g kooai-api

# Or in docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### 5. Slow API Response

**Solutions**:
- Increase worker count: `API_WORKERS=8`
- Enable Redis caching
- Add database indexes
- Use connection pooling
- Monitor with Prometheus

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Backup and Restore

#### Backup Database

```bash
docker-compose exec postgres pg_dump \
  -U kooai kooai > backup_$(date +%Y%m%d).sql
```

#### Restore Database

```bash
cat backup_20250101.sql | \
  docker-compose exec -T postgres psql -U kooai kooai
```

#### Backup Data Volumes

```bash
docker run --rm \
  -v kooai_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data.tar.gz /data
```

---

## Performance Optimization

### Database Tuning

Edit PostgreSQL configuration:

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
work_mem = 16MB
```

### API Optimization

```bash
# Increase workers
API_WORKERS=8

# Enable caching
CACHE_TTL=3600

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

### Nginx Optimization

```nginx
worker_processes auto;
worker_connections 2048;
keepalive_timeout 65;
client_max_body_size 200M;
```

---

## Security Best Practices

1. **Never use default passwords** in production
2. **Always use HTTPS** in production
3. **Regularly update dependencies**
4. **Enable rate limiting** (configured in Nginx)
5. **Use secrets management** (Vault, AWS Secrets Manager)
6. **Enable network policies** in Kubernetes
7. **Regular security audits** and penetration testing
8. **Implement proper CORS** policies
9. **Use non-root containers** (already configured)
10. **Enable audit logging**

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/kooai/issues
- Documentation: See README.md
- Email: support@yourdomain.com

---

## License

MIT License - see LICENSE file for details
