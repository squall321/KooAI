# KooAI Kubernetes Deployment

This directory contains Kubernetes manifests for deploying KooAI on a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured to access your cluster
- Ingress Controller (e.g., nginx-ingress)
- cert-manager (optional, for TLS)
- Storage provisioner (for PersistentVolumes)

## Quick Start

### 1. Create Secrets

Copy the secrets template and fill in your actual values:

```bash
cp secrets.yaml.template secrets.yaml

# Edit secrets.yaml and replace placeholder values
# Generate base64 encoded values:
echo -n "your-secret-value" | base64

# Or use the helper script:
./generate-secrets.sh  # If you have one
```

### 2. Update Configuration

Edit `configmap.yaml` and `ingress.yaml` with your specific values:

- **configmap.yaml**: Update database names, storage paths, etc.
- **ingress.yaml**: Update domain names (replace `kooai.example.com`)

### 3. Deploy

#### Option A: Using kubectl

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply secrets
kubectl apply -f secrets.yaml

# Apply all other manifests
kubectl apply -f configmap.yaml
kubectl apply -f persistent-volumes.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f ingress.yaml
```

#### Option B: Using Kustomize

```bash
# Deploy everything at once
kubectl apply -k .

# Or with kustomize binary
kustomize build . | kubectl apply -f -
```

### 4. Verify Deployment

```bash
# Check namespace
kubectl get ns kooai

# Check pods
kubectl get pods -n kooai

# Check services
kubectl get svc -n kooai

# Check ingress
kubectl get ing -n kooai

# Check logs
kubectl logs -f -l app.kubernetes.io/component=api -n kooai
```

### 5. Access the Application

```bash
# Port-forward for local testing
kubectl port-forward -n kooai svc/kooai-api 8000:8000

# Then access: http://localhost:8000/docs

# For production (after DNS setup):
# https://kooai.example.com/docs
```

## Architecture

```
┌─────────────────────────────────────────┐
│   Ingress (TLS Termination)            │
│   - nginx-ingress                       │
│   - cert-manager (Let's Encrypt)        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   KooAI API (Deployment)                │
│   - 3 replicas (auto-scaling 3-10)     │
│   - Rolling updates                     │
│   - Health checks                       │
└────┬────────────────────────┬───────────┘
     │                        │
     ▼                        ▼
┌─────────┐             ┌──────────┐
│PostgreSQL│            │  Redis   │
│(StatefulSet)          │(Deployment)
│- pgvector  │          │- Cache   │
│- PVC: 10Gi │          │- PVC: 5Gi│
└────────────┘          └──────────┘
```

## Components

### Deployments

1. **KooAI API** (`api-deployment.yaml`)
   - 3 replicas (default)
   - Auto-scaling (HPA): 3-10 pods
   - Resource limits: 2Gi RAM, 1 CPU per pod
   - Health checks: liveness, readiness, startup
   - Zero-downtime rolling updates

2. **PostgreSQL** (`postgres-deployment.yaml`)
   - Single replica (StatefulSet pattern)
   - pgvector extension
   - Initialization scripts
   - PVC: 10Gi

3. **Redis** (`redis-deployment.yaml`)
   - Single replica
   - Persistence enabled
   - PVC: 5Gi

### Services

- **kooai-api**: ClusterIP service for API (port 8000)
- **kooai-postgres**: ClusterIP service for PostgreSQL (port 5432)
- **kooai-redis**: ClusterIP service for Redis (port 6379)

### Ingress

- **kooai-ingress**: External access with TLS
- Rate limiting: 10 req/s per IP
- Body size limit: 100MB (for file uploads)
- CORS enabled
- SSL/TLS with cert-manager

### Storage

- **kooai-postgres-pvc**: 10Gi (ReadWriteOnce)
- **kooai-redis-pvc**: 5Gi (ReadWriteOnce)
- **kooai-api-data-pvc**: 20Gi (ReadWriteMany)
- **kooai-api-logs-pvc**: 5Gi (ReadWriteMany)

## Configuration

### ConfigMap

Edit `configmap.yaml` to configure:

- Application settings (DEBUG, LOG_LEVEL)
- Database connection (host, port, name)
- Redis connection
- Storage settings
- CORS origins

### Secrets

Create `secrets.yaml` from `secrets.yaml.template`:

```yaml
POSTGRES_USER: <base64-encoded>
POSTGRES_PASSWORD: <base64-encoded>
REDIS_PASSWORD: <base64-encoded>
SECRET_KEY: <base64-encoded>
```

Generate secrets:

```bash
# PostgreSQL password
echo -n "my-strong-postgres-password" | base64

# Redis password
echo -n "my-strong-redis-password" | base64

# Application secret key
python -c "import secrets; print(secrets.token_urlsafe(64))" | base64
```

## Scaling

### Manual Scaling

```bash
# Scale API deployment
kubectl scale deployment kooai-api --replicas=5 -n kooai

# Check HPA status
kubectl get hpa -n kooai
```

### Auto-scaling (HPA)

Horizontal Pod Autoscaler is configured in `api-deployment.yaml`:

- **Min replicas**: 3
- **Max replicas**: 10
- **CPU target**: 70%
- **Memory target**: 80%

```bash
# View HPA metrics
kubectl get hpa kooai-api-hpa -n kooai

# Describe HPA
kubectl describe hpa kooai-api-hpa -n kooai
```

## Monitoring

### Check Pod Status

```bash
# Get all pods
kubectl get pods -n kooai -o wide

# Watch pods
kubectl get pods -n kooai -w

# Describe pod
kubectl describe pod <pod-name> -n kooai
```

### Logs

```bash
# API logs
kubectl logs -f -l app.kubernetes.io/component=api -n kooai

# PostgreSQL logs
kubectl logs -f -l app.kubernetes.io/component=database -n kooai

# Redis logs
kubectl logs -f -l app.kubernetes.io/component=cache -n kooai

# Previous pod logs (if crashed)
kubectl logs --previous <pod-name> -n kooai
```

### Events

```bash
# Namespace events
kubectl get events -n kooai --sort-by='.lastTimestamp'

# Watch events
kubectl get events -n kooai -w
```

### Resource Usage

```bash
# Pod resource usage
kubectl top pods -n kooai

# Node resource usage
kubectl top nodes
```

## Updates and Rollouts

### Update API Image

```bash
# Update image tag
kubectl set image deployment/kooai-api api=ghcr.io/yourusername/kooai:v1.0.0 -n kooai

# Or edit deployment
kubectl edit deployment kooai-api -n kooai
```

### Rollout Status

```bash
# Check rollout status
kubectl rollout status deployment/kooai-api -n kooai

# View rollout history
kubectl rollout history deployment/kooai-api -n kooai

# Rollback to previous version
kubectl rollout undo deployment/kooai-api -n kooai

# Rollback to specific revision
kubectl rollout undo deployment/kooai-api --to-revision=2 -n kooai
```

## Maintenance

### Database Backup

```bash
# Create backup
kubectl exec -n kooai -it <postgres-pod> -- \
  pg_dump -U kooai kooai > backup_$(date +%Y%m%d).sql

# Restore from backup
cat backup_20250101.sql | \
  kubectl exec -n kooai -i <postgres-pod> -- \
  psql -U kooai kooai
```

### Database Migrations

```bash
# Run migrations (if using Alembic)
kubectl exec -n kooai -it <api-pod> -- \
  alembic upgrade head
```

### Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace kooai

# Or delete specific resources
kubectl delete -f api-deployment.yaml -n kooai
kubectl delete -f postgres-deployment.yaml -n kooai
kubectl delete -f redis-deployment.yaml -n kooai

# Delete PVCs (will delete data!)
kubectl delete pvc --all -n kooai
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n kooai

# Check logs
kubectl logs <pod-name> -n kooai

# Check previous logs if crashed
kubectl logs --previous <pod-name> -n kooai
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl exec -n kooai -it <api-pod> -- \
  nc -zv kooai-postgres 5432

# Check PostgreSQL logs
kubectl logs -n kooai <postgres-pod>

# Connect to PostgreSQL
kubectl exec -n kooai -it <postgres-pod> -- \
  psql -U kooai kooai
```

### Ingress Not Working

```bash
# Check ingress
kubectl get ing -n kooai
kubectl describe ing kooai-ingress -n kooai

# Check ingress controller logs
kubectl logs -f -n ingress-nginx <ingress-controller-pod>

# Test service directly
kubectl port-forward -n kooai svc/kooai-api 8000:8000
```

### Storage Issues

```bash
# Check PVCs
kubectl get pvc -n kooai

# Describe PVC
kubectl describe pvc <pvc-name> -n kooai

# Check PVs
kubectl get pv
```

## Security Best Practices

1. **Secrets Management**
   - Never commit `secrets.yaml` to version control
   - Use external secret management (Vault, AWS Secrets Manager)
   - Rotate secrets regularly

2. **Network Policies**
   - Implement NetworkPolicy for pod-to-pod communication
   - Restrict ingress/egress traffic

3. **RBAC**
   - Use ServiceAccounts with minimal permissions
   - Review and audit RBAC policies

4. **Pod Security**
   - Run containers as non-root user (already configured)
   - Use Pod Security Standards
   - Scan images for vulnerabilities

5. **TLS/SSL**
   - Always use HTTPS in production
   - Use cert-manager for automatic certificate management

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/kooai/issues
- Documentation: See main README.md and DEPLOYMENT.md
