# Monitoring Guide

Complete guide for setting up monitoring and observability for KooAI.

## Table of Contents

1. [Overview](#overview)
2. [Metrics Overview](#metrics-overview)
3. [Prometheus Setup](#prometheus-setup)
4. [Grafana Setup](#grafana-setup)
5. [Alert Configuration](#alert-configuration)
6. [Querying Metrics](#querying-metrics)
7. [Dashboards](#dashboards)
8. [Troubleshooting](#troubleshooting)

---

## Overview

KooAI provides comprehensive monitoring through:

- **Prometheus Metrics**: Application and system metrics in Prometheus format
- **Grafana Dashboards**: Pre-built dashboards for visualization
- **Alerting**: Alert rules for proactive monitoring
- **Health Checks**: HTTP endpoints for liveness/readiness checks

### Architecture

```
┌─────────────┐
│   KooAI API │
│  :8000      │──┐
└─────────────┘  │
                 │ /api/v1/metrics
                 ▼
┌─────────────────────────────────────┐
│         Prometheus                   │
│         :9090                        │
│  - Scrapes metrics every 15s        │
│  - Evaluates alert rules            │
│  - Stores time-series data          │
└──────────┬──────────────────────────┘
           │
           ├──────▶ Grafana :3000 (Visualization)
           │
           └──────▶ Alertmanager :9093 (Alerts)
                      │
                      ├──▶ Email
                      ├──▶ Slack
                      └──▶ PagerDuty
```

---

## Metrics Overview

### Metric Categories

KooAI exposes 50+ metrics across 7 categories:

#### 1. HTTP Metrics
```
kooai_http_requests_total{method, endpoint, status}
kooai_http_request_duration_seconds{method, endpoint}
kooai_http_requests_in_progress{method, endpoint}
```

#### 2. Database Metrics
```
kooai_database_queries_total{operation}
kooai_database_query_duration_seconds{operation}
kooai_database_connections_active
kooai_database_connection_pool_size
kooai_database_errors_total{error_type}
```

#### 3. Cache Metrics
```
kooai_cache_hits_total{cache_tier}
kooai_cache_misses_total{cache_tier}
kooai_cache_evictions_total{cache_tier}
kooai_cache_memory_bytes{cache_tier}
kooai_cache_entries_total{cache_tier}
kooai_cache_operation_duration_seconds{operation, cache_tier}
```

#### 4. Task Queue Metrics
```
kooai_task_queue_size{status}
kooai_task_processing_duration_seconds{task_name, priority}
kooai_tasks_total{task_name, status}
kooai_task_retries_total{task_name}
kooai_active_workers
```

#### 5. Simulation Metrics
```
kooai_simulations_processed_total{file_format, status}
kooai_simulation_file_size_bytes{file_format}
kooai_simulation_processing_duration_seconds{file_format}
kooai_simulation_vertices_total
```

#### 6. System Metrics
```
kooai_system_cpu_usage_percent
kooai_system_memory_usage_bytes
kooai_system_memory_available_bytes
kooai_system_disk_usage_bytes{mountpoint}
kooai_system_disk_available_bytes{mountpoint}
kooai_system_network_sent_bytes_total
kooai_system_network_received_bytes_total
```

#### 7. Application Metrics
```
kooai_app_info{version, environment, python_version}
kooai_app_uptime_seconds
kooai_app_start_time_seconds
```

---

## Prometheus Setup

### 1. Install Prometheus

**Ubuntu/Debian:**
```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64

# Move binaries
sudo mv prometheus promtool /usr/local/bin/
sudo mkdir -p /etc/prometheus /var/lib/prometheus

# Move configuration files
sudo mv prometheus.yml /etc/prometheus/
sudo mv consoles console_libraries /etc/prometheus/
```

### 2. Configure Prometheus

Copy the provided configuration:

```bash
sudo cp monitoring/prometheus/prometheus.yml /etc/prometheus/
sudo cp -r monitoring/prometheus/alerts /etc/prometheus/
```

Edit `/etc/prometheus/prometheus.yml` and update the target:

```yaml
scrape_configs:
  - job_name: 'kooai'
    static_configs:
      - targets:
          - 'YOUR_KOOAI_HOST:8000'  # Update this
```

### 3. Create Systemd Service

Create `/etc/systemd/system/prometheus.service`:

```ini
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --storage.tsdb.retention.time=15d \
    --storage.tsdb.retention.size=50GB

Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Start Prometheus

```bash
# Create prometheus user
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus

# Check status
sudo systemctl status prometheus
```

### 5. Verify Installation

```bash
# Check Prometheus is running
curl http://localhost:9090/-/healthy

# Check targets
curl http://localhost:9090/api/v1/targets
```

Access Prometheus UI: `http://localhost:9090`

---

## Grafana Setup

### 1. Install Grafana

**Ubuntu/Debian:**
```bash
# Add Grafana repository
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Install
sudo apt-get update
sudo apt-get install grafana

# Enable and start
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### 2. Access Grafana

- URL: `http://localhost:3000`
- Default credentials: `admin` / `admin`
- Change password on first login

### 3. Add Prometheus Data Source

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Configure:
   - **Name**: Prometheus
   - **URL**: `http://localhost:9090`
   - **Access**: Server (default)
5. Click **Save & Test**

### 4. Import Dashboard

1. Go to **Dashboards** → **Import**
2. Upload `monitoring/grafana/kooai-dashboard.json`
3. Select **Prometheus** as data source
4. Click **Import**

### 5. Alternative: Import from File

```bash
# Copy dashboard to Grafana provisioning directory
sudo mkdir -p /etc/grafana/provisioning/dashboards
sudo cp monitoring/grafana/kooai-dashboard.json /etc/grafana/provisioning/dashboards/

# Create provisioning config
sudo cat > /etc/grafana/provisioning/dashboards/kooai.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'KooAI'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# Restart Grafana
sudo systemctl restart grafana-server
```

---

## Alert Configuration

### 1. Install Alertmanager

```bash
# Download
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvf alertmanager-0.26.0.linux-amd64.tar.gz
cd alertmanager-0.26.0.linux-amd64

# Move binary
sudo mv alertmanager amtool /usr/local/bin/
sudo mkdir -p /etc/alertmanager
```

### 2. Configure Alertmanager

```bash
# Copy configuration
sudo cp monitoring/prometheus/alertmanager.yml /etc/alertmanager/

# Update with your settings
sudo vi /etc/alertmanager/alertmanager.yml
```

Update these fields:
- SMTP settings for email
- PagerDuty service key
- Slack webhook URL

### 3. Create Systemd Service

Create `/etc/systemd/system/alertmanager.service`:

```ini
[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml \
    --storage.path=/var/lib/alertmanager/

Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Start Alertmanager

```bash
# Create user and directories
sudo useradd --no-create-home --shell /bin/false alertmanager
sudo mkdir -p /var/lib/alertmanager
sudo chown -R alertmanager:alertmanager /etc/alertmanager /var/lib/alertmanager

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable alertmanager
sudo systemctl start alertmanager

# Check status
sudo systemctl status alertmanager
```

Access Alertmanager UI: `http://localhost:9093`

### 5. Test Alerts

```bash
# Trigger a test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }]'
```

---

## Querying Metrics

### Prometheus Query Language (PromQL)

#### Basic Queries

**Current HTTP request rate:**
```promql
rate(kooai_http_requests_total[5m])
```

**P95 latency:**
```promql
histogram_quantile(0.95,
  sum(rate(kooai_http_request_duration_seconds_bucket[5m])) by (le)
)
```

**Cache hit rate:**
```promql
sum(rate(kooai_cache_hits_total[5m]))
/
(sum(rate(kooai_cache_hits_total[5m])) + sum(rate(kooai_cache_misses_total[5m])))
* 100
```

**Error rate:**
```promql
sum(rate(kooai_http_requests_total{status=~"5.."}[5m]))
/
sum(rate(kooai_http_requests_total[5m]))
* 100
```

#### Advanced Queries

**Request rate by endpoint:**
```promql
sum(rate(kooai_http_requests_total[5m])) by (endpoint)
```

**Top 5 slowest endpoints:**
```promql
topk(5,
  sum(rate(kooai_http_request_duration_seconds_sum[5m])) by (endpoint)
  /
  sum(rate(kooai_http_request_duration_seconds_count[5m])) by (endpoint)
)
```

**Database query breakdown:**
```promql
sum(rate(kooai_database_queries_total[5m])) by (operation)
```

**Memory usage percentage:**
```promql
(kooai_system_memory_usage_bytes / (kooai_system_memory_usage_bytes + kooai_system_memory_available_bytes)) * 100
```

### Using the Metrics Endpoint

**Curl:**
```bash
curl http://localhost:8000/api/v1/metrics
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/api/v1/metrics')
metrics = response.text
print(metrics)
```

---

## Dashboards

### Pre-built Dashboard Features

The provided Grafana dashboard includes:

1. **HTTP Metrics**
   - Request rate over time
   - P95 latency gauge
   - Status code breakdown

2. **Cache Performance**
   - Hit rate by tier (L1/L2)
   - Memory usage
   - Eviction rate

3. **Task Queue**
   - Queue size by status
   - Processing time histogram
   - Active workers

4. **System Resources**
   - CPU usage timeline
   - Memory usage (used/available)
   - Disk usage by mountpoint
   - Application uptime

5. **Database**
   - Query rate by operation
   - Connection pool usage
   - Error rate

6. **Simulations**
   - Processing rate by format
   - File size distribution
   - Vertices count histogram

### Creating Custom Dashboards

1. Go to **Dashboards** → **New Dashboard**
2. Click **Add a new panel**
3. Enter PromQL query
4. Configure visualization
5. Save dashboard

Example panel:

```json
{
  "targets": [
    {
      "expr": "rate(kooai_http_requests_total[5m])",
      "legendFormat": "{{method}} {{endpoint}}"
    }
  ],
  "title": "HTTP Request Rate",
  "type": "graph"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Metrics Endpoint Returns 500 Error

**Cause**: Error collecting metrics

**Solution**:
```bash
# Check application logs
sudo journalctl -u kooai -n 100

# Verify dependencies are running
curl http://localhost:8000/api/v1/health/ready
```

#### 2. Prometheus Can't Scrape Metrics

**Cause**: Network or authentication issue

**Solution**:
```bash
# Test metrics endpoint
curl http://YOUR_HOST:8000/api/v1/metrics

# Check Prometheus logs
sudo journalctl -u prometheus -n 100

# Verify scrape configuration
curl http://localhost:9090/api/v1/targets
```

#### 3. No Data in Grafana

**Cause**: Data source not configured or no data in Prometheus

**Solution**:
1. Test Prometheus data source in Grafana
2. Check Prometheus has data: `http://localhost:9090/graph`
3. Query metrics directly: `kooai_app_uptime_seconds`

#### 4. Alerts Not Firing

**Cause**: Alert rules not loaded or Alertmanager not configured

**Solution**:
```bash
# Check alert rules in Prometheus
curl http://localhost:9090/api/v1/rules

# Test Alertmanager
curl http://localhost:9093/api/v1/status

# Manually trigger alert (see Test Alerts section)
```

### Verification Checklist

- [ ] Metrics endpoint accessible: `curl http://localhost:8000/api/v1/metrics`
- [ ] Prometheus scraping successfully: Check `/targets` page
- [ ] Grafana can query Prometheus: Test data source
- [ ] Dashboard displays data: Check time range
- [ ] Alert rules loaded: Check `/rules` page
- [ ] Alertmanager receiving alerts: Check UI

---

## Best Practices

### 1. Metric Naming

- Use consistent naming: `kooai_<category>_<metric>_<unit>`
- Add labels for dimensions: `{method, endpoint, status}`
- Include units in name: `_seconds`, `_bytes`, `_total`

### 2. Query Optimization

- Use recording rules for expensive queries
- Limit cardinality (avoid high-cardinality labels)
- Use appropriate time ranges

### 3. Alert Design

- Set appropriate thresholds
- Use `for` clause to avoid flapping
- Include context in annotations
- Test alerts before deploying

### 4. Dashboard Design

- Group related metrics
- Use consistent time ranges
- Add descriptions to panels
- Include links to runbooks

### 5. Data Retention

- Configure retention based on disk space
- Use downsampling for long-term storage
- Archive important data externally

---

## Additional Resources

### Prometheus Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Best Practices](https://prometheus.io/docs/practices/naming/)

### Grafana Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [Template Variables](https://grafana.com/docs/grafana/latest/variables/)

### KooAI Resources

- [Production Deployment Guide](PRODUCTION_GUIDE.md)
- [Health Check Documentation](../src/presentation/api/routes/health_routes.py)
- [Metrics Implementation](../src/infrastructure/monitoring/prometheus_metrics.py)

---

## Support

### Useful Commands

**Prometheus:**
```bash
# Reload configuration
curl -X POST http://localhost:9090/-/reload

# Check configuration
promtool check config /etc/prometheus/prometheus.yml

# Check rules
promtool check rules /etc/prometheus/alerts/*.yml
```

**Grafana:**
```bash
# Restart Grafana
sudo systemctl restart grafana-server

# Check logs
sudo journalctl -u grafana-server -f
```

**Alertmanager:**
```bash
# Reload configuration
curl -X POST http://localhost:9093/-/reload

# Silence alert
amtool silence add alertname=TestAlert

# List active alerts
amtool alert query
```

---

**Last Updated**: 2025-11-07
**Version**: 1.0
