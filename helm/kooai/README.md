# KooAI Helm Chart

This Helm chart deploys KooAI Simulation Post-Processing Platform on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- Ingress controller (e.g., nginx-ingress)
- cert-manager (optional, for TLS)

## Installing the Chart

### Quick Start

```bash
# Add helm repository (if published)
helm repo add kooai https://charts.kooai.example.com
helm repo update

# Install with default values
helm install kooai kooai/kooai --namespace kooai --create-namespace

# Or install from local directory
helm install kooai ./helm/kooai --namespace kooai --create-namespace
```

### With Custom Values

```bash
# Create custom values file
cat > my-values.yaml <<EOF
api:
  replicaCount: 5
  image:
    tag: "v1.0.0"

postgresql:
  auth:
    password: "my-strong-password"

redis:
  auth:
    password: "my-redis-password"

secrets:
  secretKey: "generated-secret-key"

ingress:
  hosts:
    - host: kooai.mydomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: kooai-tls
      hosts:
        - kooai.mydomain.com
EOF

# Install with custom values
helm install kooai ./helm/kooai \
  --namespace kooai \
  --create-namespace \
  --values my-values.yaml
```

### Using --set Flags

```bash
helm install kooai ./helm/kooai \
  --namespace kooai \
  --create-namespace \
  --set api.replicaCount=5 \
  --set postgresql.auth.password=strong-password \
  --set redis.auth.password=redis-password \
  --set secrets.secretKey=your-secret-key \
  --set ingress.hosts[0].host=kooai.mydomain.com
```

## Uninstalling the Chart

```bash
helm uninstall kooai --namespace kooai
```

This removes all the Kubernetes components associated with the chart and deletes the release.

**Note**: PersistentVolumeClaims are not deleted automatically. To delete them:

```bash
kubectl delete pvc --all -n kooai
```

## Configuration

The following table lists the configurable parameters of the KooAI chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.storageClass` | Global storage class | `standard` |
| `namespaceOverride` | Override namespace name | `""` |

### API Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.replicaCount` | Number of API replicas | `3` |
| `api.image.repository` | API image repository | `ghcr.io/yourusername/kooai` |
| `api.image.tag` | API image tag | `latest` |
| `api.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `api.resources.limits.cpu` | CPU limit | `1000m` |
| `api.resources.limits.memory` | Memory limit | `2Gi` |
| `api.autoscaling.enabled` | Enable HPA | `true` |
| `api.autoscaling.minReplicas` | Minimum replicas | `3` |
| `api.autoscaling.maxReplicas` | Maximum replicas | `10` |
| `api.persistence.data.enabled` | Enable data persistence | `true` |
| `api.persistence.data.size` | Data volume size | `20Gi` |

### PostgreSQL Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL | `true` |
| `postgresql.image.tag` | PostgreSQL image tag | `pg16` |
| `postgresql.auth.username` | PostgreSQL username | `kooai` |
| `postgresql.auth.password` | PostgreSQL password | `""` (required) |
| `postgresql.auth.database` | PostgreSQL database | `kooai` |
| `postgresql.persistence.size` | PostgreSQL volume size | `10Gi` |

### Redis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis | `true` |
| `redis.image.tag` | Redis image tag | `7-alpine` |
| `redis.auth.password` | Redis password | `""` (required) |
| `redis.persistence.size` | Redis volume size | `5Gi` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts` | Ingress hosts | `[{host: kooai.example.com, paths: [{path: /, pathType: Prefix}]}]` |
| `ingress.tls` | Ingress TLS configuration | `[{secretName: kooai-tls, hosts: [kooai.example.com]}]` |

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.kooaiEnv` | Application environment | `production` |
| `config.debug` | Enable debug mode | `false` |
| `config.logLevel` | Log level | `INFO` |
| `config.apiWorkers` | Number of API workers | `4` |
| `config.maxUploadSize` | Max upload size | `104857600` (100MB) |

### Secrets Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.secretKey` | Application secret key | `""` (required) |
| `secrets.openaiApiKey` | OpenAI API key (optional) | `""` |
| `secrets.anthropicApiKey` | Anthropic API key (optional) | `""` |

## Examples

### Production Deployment

```bash
helm install kooai ./helm/kooai \
  --namespace kooai-prod \
  --create-namespace \
  --set api.replicaCount=5 \
  --set api.image.tag=v1.0.0 \
  --set api.resources.requests.cpu=500m \
  --set api.resources.requests.memory=1Gi \
  --set postgresql.auth.password=$(openssl rand -base64 32) \
  --set redis.auth.password=$(openssl rand -base64 32) \
  --set secrets.secretKey=$(python -c "import secrets; print(secrets.token_urlsafe(64))") \
  --set ingress.hosts[0].host=kooai.company.com \
  --set ingress.tls[0].hosts[0]=kooai.company.com
```

### Development Deployment

```bash
helm install kooai-dev ./helm/kooai \
  --namespace kooai-dev \
  --create-namespace \
  --set api.replicaCount=1 \
  --set api.autoscaling.enabled=false \
  --set config.debug=true \
  --set config.logLevel=DEBUG \
  --set ingress.enabled=false
```

### Upgrade Deployment

```bash
# Upgrade to new version
helm upgrade kooai ./helm/kooai \
  --namespace kooai \
  --set api.image.tag=v1.1.0 \
  --reuse-values

# Rollback
helm rollback kooai 1 --namespace kooai
```

## Monitoring

### Prometheus

If Prometheus Operator is installed, enable ServiceMonitor:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
```

### Grafana Dashboards

Import the KooAI Grafana dashboard from `grafana/dashboard.json` (if available).

## Persistence

The chart mounts PersistentVolumeClaims for:

- PostgreSQL data (`/var/lib/postgresql/data`)
- Redis data (`/data`)
- API data (`/app/data`)
- API logs (`/app/logs`)

Ensure your cluster has a storage provisioner configured.

## Scaling

### Manual Scaling

```bash
kubectl scale deployment kooai-api --replicas=10 -n kooai
```

### Auto-scaling

Horizontal Pod Autoscaler is enabled by default:

```bash
# View HPA
kubectl get hpa -n kooai

# Describe HPA
kubectl describe hpa kooai-api -n kooai
```

## Troubleshooting

### Check Installation

```bash
# Helm status
helm status kooai -n kooai

# List releases
helm list -n kooai

# Get values
helm get values kooai -n kooai
```

### Check Pods

```bash
# Get pods
kubectl get pods -n kooai

# Describe pod
kubectl describe pod <pod-name> -n kooai

# Logs
kubectl logs -f <pod-name> -n kooai
```

### Validate Chart

```bash
# Dry-run
helm install kooai ./helm/kooai --namespace kooai --dry-run --debug

# Template
helm template kooai ./helm/kooai --namespace kooai
```

## License

MIT

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/kooai/issues
- Documentation: https://github.com/yourusername/kooai/blob/main/README.md
