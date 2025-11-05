# Grafana Dashboard Deployment Guide

**Dashboard**: Tool Cache Performance  
**Location**: `dashboards/cache_performance.json`  
**Version**: 1.0  
**Last Updated**: November 5, 2025  

---

## Overview

This guide provides step-by-step instructions for deploying the Tool Cache Performance dashboard to Grafana. The dashboard visualizes cache hit rates, latency improvements, and per-namespace performance metrics for the semantic cache system.

**Prerequisites**:

- Grafana instance running (v9.0+)
- Prometheus datasource configured
- Metrics endpoint enabled (`ENABLE_PROMETHEUS_ENDPOINT=1`)
- Cache enhancement deployed (commits: c1f0e98, d838bb4, e02850e)

---

## Dashboard Panels

### Panel 1: Cache Hit Rate by Namespace (Gauge)

- **Metric**: `sum(rate(tool_cache_hits_total[5m])) / (sum(rate(tool_cache_hits_total[5m])) + sum(rate(tool_cache_misses_total[5m])))`
- **Threshold**: Red <40%, Yellow 40-60%, Green >60%
- **Position**: Top-left (12 cols wide, 8 rows high)

### Panel 2: Cache Hits vs Misses Over Time (Time Series)

- **Metrics**:
  - `sum(rate(tool_cache_hits_total[5m])) by (namespace)` (hits)
  - `sum(rate(tool_cache_misses_total[5m])) by (namespace)` (misses)
- **Position**: Top-right (12 cols wide, 8 rows high)

### Panel 3: Tool Latency: Cached vs Uncached (Time Series)

- **Metrics**:
  - P50: `histogram_quantile(0.50, sum(rate(tool_run_seconds_bucket[5m])) by (le, tool, cached))`
  - P95: `histogram_quantile(0.95, sum(rate(tool_run_seconds_bucket[5m])) by (le, tool, cached))`
- **Position**: Full width (24 cols, 8 rows)
- **Colors**: Green for cached, Red for uncached

### Panel 4: Total Cache Hits (Stat)

- **Metric**: `sum(tool_cache_hits_total)`
- **Position**: Bottom-left third

### Panel 5: Total Cache Misses (Stat)

- **Metric**: `sum(tool_cache_misses_total)`
- **Position**: Bottom-middle third

### Panel 6: Overall Cache Hit Rate (Stat)

- **Metric**: `sum(tool_cache_hits_total) / (sum(tool_cache_hits_total) + sum(tool_cache_misses_total))`
- **Threshold**: Red <50%, Yellow 50-70%, Green >70%
- **Position**: Bottom-right third

### Panel 7: Cache Performance by Namespace (Table)

- **Metrics**: Combines hits, misses, and hit rate per namespace
- **Columns**: Namespace, Hits, Misses, Hit Rate (color-coded)
- **Position**: Full width at bottom

---

## Deployment Methods

### Method 1: Grafana UI Import (Recommended for Initial Setup)

1. **Access Grafana**:

   ```bash
   # If running locally
   open http://localhost:3000
   
   # If running in container
   docker exec -it grafana-container-name /bin/sh
   ```

2. **Navigate to Import**:
   - Click **+** (Create) → **Import**
   - Or go to: `http://localhost:3000/dashboard/import`

3. **Import Dashboard JSON**:
   - Click **Upload JSON file**
   - Select `dashboards/cache_performance.json`
   - **OR** copy-paste JSON content into text area

4. **Configure Options**:
   - **Name**: Tool Cache Performance (default)
   - **Folder**: Select existing folder or create new one (e.g., "Caching")
   - **UID**: `tool-cache-performance` (default, must be unique)

5. **Select Datasource**:
   - **Prometheus**: Select your Prometheus datasource from dropdown
   - If no datasource exists, create one first (see Prometheus Setup below)

6. **Import**:
   - Click **Import** button
   - Dashboard should load immediately with panels

### Method 2: Grafana API Import (Recommended for Production/CI)

```bash
# Set variables
GRAFANA_URL="http://localhost:3000"
GRAFANA_API_KEY="your-api-key-here"  # Create in Grafana UI: Configuration → API Keys
DASHBOARD_FILE="dashboards/cache_performance.json"

# Import dashboard
curl -X POST \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @${DASHBOARD_FILE} \
  "${GRAFANA_URL}/api/dashboards/db"
```

**Response**:

```json
{
  "id": 1,
  "slug": "tool-cache-performance",
  "status": "success",
  "uid": "tool-cache-performance",
  "url": "/d/tool-cache-performance/tool-cache-performance",
  "version": 1
}
```

### Method 3: Provisioning (Recommended for Infrastructure-as-Code)

1. **Create Provisioning Directory**:

   ```bash
   mkdir -p /etc/grafana/provisioning/dashboards
   ```

2. **Create Dashboard Provider Config**:

   ```yaml
   # /etc/grafana/provisioning/dashboards/cache-dashboards.yaml
   apiVersion: 1

   providers:
     - name: 'Cache Performance'
       orgId: 1
       folder: 'Caching'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       allowUiUpdates: true
       options:
         path: /var/lib/grafana/dashboards/cache
   ```

3. **Copy Dashboard JSON**:

   ```bash
   mkdir -p /var/lib/grafana/dashboards/cache
   cp dashboards/cache_performance.json /var/lib/grafana/dashboards/cache/
   ```

4. **Restart Grafana**:

   ```bash
   # Docker
   docker restart grafana
   
   # SystemD
   sudo systemctl restart grafana-server
   ```

5. **Verify**:
   - Dashboard should auto-load at: `http://localhost:3000/d/tool-cache-performance`

---

## Prometheus Setup

### Step 1: Enable Metrics Endpoint

Ensure the application exposes Prometheus metrics:

```bash
# In .env or environment
export ENABLE_PROMETHEUS_ENDPOINT=1

# Verify metrics endpoint is accessible
curl http://localhost:8000/metrics | grep tool_cache
```

**Expected output**:

```
# HELP tool_cache_hits_total Total number of cache hits by namespace
# TYPE tool_cache_hits_total counter
tool_cache_hits_total{namespace="sentiment_analysis"} 150
tool_cache_hits_total{namespace="enhanced_analysis"} 89
tool_cache_misses_total{namespace="sentiment_analysis"} 30
tool_cache_misses_total{namespace="enhanced_analysis"} 18
```

### Step 2: Configure Prometheus Datasource in Grafana

**Via UI**:

1. Navigate to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Configure:
   - **Name**: Prometheus
   - **URL**: `http://localhost:9090` (or your Prometheus host)
   - **Access**: Server (default) or Browser
   - **Scrape interval**: 15s (default)
5. Click **Save & Test**
6. Verify: "Data source is working" message

**Via API**:

```bash
GRAFANA_URL="http://localhost:3000"
GRAFANA_API_KEY="your-api-key"

curl -X POST \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }' \
  "${GRAFANA_URL}/api/datasources"
```

### Step 3: Configure Prometheus Scrape Config

Add scrape target for your application:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'crew-cache-metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']  # Adjust to your app's host:port
    metrics_path: '/metrics'
```

**Reload Prometheus**:

```bash
# Send SIGHUP to reload config
kill -HUP $(pgrep prometheus)

# Or restart
docker restart prometheus
```

**Verify scrape**:

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="crew-cache-metrics")'
```

---

## Validation Checklist

After deployment, verify the dashboard is working correctly:

- [ ] **Dashboard loads**: Access `http://localhost:3000/d/tool-cache-performance`
- [ ] **Panels render**: All 7 panels display without "No data" errors
- [ ] **Metrics available**: Cache hit rate gauge shows percentage (not "NaN")
- [ ] **Time series populated**: Hits vs Misses chart shows data points
- [ ] **Latency data**: P50/P95 latency charts show cached vs uncached comparison
- [ ] **Stats accurate**: Total hits, misses, and overall hit rate display numbers
- [ ] **Table populated**: Namespace table shows at least one row
- [ ] **Thresholds work**: Gauges/stats change color based on thresholds
- [ ] **Refresh works**: Click refresh icon, data updates
- [ ] **Time range works**: Change time range (e.g., Last 6 hours), data adjusts

### Common Issues & Fixes

**Issue**: "No data" in all panels  
**Fix**:

1. Check metrics endpoint: `curl http://localhost:8000/metrics | grep tool_cache`
2. Verify Prometheus scraping: Check Prometheus UI → Status → Targets
3. Ensure cache is active: Run a cached tool and check metrics

**Issue**: Dashboard import fails with "UID already exists"  
**Fix**:

1. Either delete existing dashboard with same UID
2. Or change UID in JSON before import (search for `"uid": "tool-cache-performance"`)

**Issue**: Datasource not found  
**Fix**:

1. Edit dashboard JSON: Change `"datasource": "Prometheus"` to your datasource name
2. Or select datasource manually after import

**Issue**: Latency panel shows no data  
**Fix**:

1. Verify `tool_run_seconds_bucket` histogram is being emitted
2. Check if tools have `cached` label in metrics
3. Ensure histogram buckets are configured correctly

---

## Alert Configuration (Optional)

Add alerts to notify when cache performance degrades:

### Alert 1: Low Cache Hit Rate

```yaml
# In Grafana UI: Panel → Alert tab
name: Low Cache Hit Rate
conditions:
  - type: query
    query: C
    reducer: last
    evaluator:
      type: lt
      params: [0.6]  # Alert if hit rate < 60%
    
for: 5m
annotations:
  summary: Cache hit rate is below 60%
  description: "Namespace: {{ $labels.namespace }}, Hit Rate: {{ $value }}%"
```

### Alert 2: High Cache Miss Rate

```yaml
name: High Cache Miss Rate
conditions:
  - type: query
    query: sum(rate(tool_cache_misses_total[5m]))
    reducer: avg
    evaluator:
      type: gt
      params: [10]  # Alert if > 10 misses/sec
    
for: 5m
annotations:
  summary: Cache miss rate exceeds threshold
```

### Alert 3: Latency Increase Despite Cache

```yaml
name: Cached Tool Latency Increase
conditions:
  - type: query
    query: histogram_quantile(0.95, sum(rate(tool_run_seconds_bucket{cached="true"}[5m])) by (le, tool))
    reducer: avg
    evaluator:
      type: gt
      params: [0.5]  # Alert if P95 cached latency > 500ms
    
for: 10m
annotations:
  summary: Cached tool latency unexpectedly high
  description: "Tool: {{ $labels.tool }}, P95 Latency: {{ $value }}s"
```

**Configure Notification Channel**:

1. Grafana → Alerting → Notification channels
2. Add channel (Slack, Email, PagerDuty, etc.)
3. Test notification
4. Link alerts to notification channel

---

## Dashboard Maintenance

### Updating the Dashboard

**Via UI**:

1. Make changes in Grafana dashboard
2. Click **Save dashboard** (disk icon, top-right)
3. Export updated JSON: **Share** → **Export** → **Save to file**
4. Commit updated JSON to repo: `git add dashboards/cache_performance.json && git commit`

**Via API**:

```bash
# Export current dashboard
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "${GRAFANA_URL}/api/dashboards/uid/tool-cache-performance" \
  | jq '.dashboard' > dashboards/cache_performance.json

# Commit to git
git add dashboards/cache_performance.json
git commit -m "docs(dashboards): Update cache performance dashboard"
```

### Version Control

Dashboard JSON is version-controlled in git:

- **Location**: `dashboards/cache_performance.json`
- **Commits**: Track changes via git history
- **Rollback**: `git checkout <commit> -- dashboards/cache_performance.json`

### Backup

**Manual backup**:

```bash
# Export all dashboards
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "${GRAFANA_URL}/api/search?type=dash-db" \
  | jq -r '.[] | .uid' \
  | xargs -I {} curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
    "${GRAFANA_URL}/api/dashboards/uid/{}" \
    > "backup-dashboards-$(date +%Y%m%d).json"
```

**Automated backup** (cron):

```bash
# /etc/cron.daily/grafana-backup
#!/bin/bash
BACKUP_DIR="/var/backups/grafana/dashboards"
mkdir -p "$BACKUP_DIR"
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "${GRAFANA_URL}/api/search?type=dash-db" \
  | jq -r '.[] | .uid' \
  | xargs -I {} curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
    "${GRAFANA_URL}/api/dashboards/uid/{}" \
    > "$BACKUP_DIR/backup-$(date +%Y%m%d).json"
find "$BACKUP_DIR" -name "backup-*.json" -mtime +30 -delete
```

---

## Production Deployment Checklist

Complete before deploying to production:

### Pre-Deployment

- [ ] Metrics endpoint enabled (`ENABLE_PROMETHEUS_ENDPOINT=1` in production env)
- [ ] Prometheus scraping production application (verify `/metrics` accessible)
- [ ] Grafana datasource configured and tested
- [ ] Dashboard JSON validated (no syntax errors)
- [ ] Cache enhancement deployed (commits c1f0e98, d838bb4, e02850e)
- [ ] Baseline metrics captured (run cache benchmark, record initial hit rates)

### Deployment

- [ ] Import dashboard via preferred method (UI, API, or provisioning)
- [ ] Verify all panels load and display data
- [ ] Set up alerts (optional but recommended)
- [ ] Configure notification channels for alerts
- [ ] Test time range selectors (1h, 6h, 24h, 7d)
- [ ] Test refresh intervals (10s default, verify real-time updates)

### Post-Deployment

- [ ] Share dashboard URL with team
- [ ] Document access credentials (Grafana login)
- [ ] Schedule weekly review meetings to analyze cache performance
- [ ] Set up automated reports (Grafana → Sharing → Report)
- [ ] Monitor for 7 days, capture production baselines
- [ ] Update cache TTLs based on real traffic patterns (if needed)
- [ ] Create runbook for common cache issues

### Documentation

- [ ] Add dashboard link to team wiki/docs
- [ ] Document alert thresholds and escalation procedures
- [ ] Create troubleshooting guide for common cache issues
- [ ] Update ADR with cache performance findings

---

## Grafana Configuration Best Practices

### Resource Limits

```yaml
# grafana.ini or docker-compose
[server]
root_url = http://localhost:3000

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db

[analytics]
reporting_enabled = false  # Disable telemetry for privacy

[metrics]
enabled = true
interval_seconds = 10

[security]
admin_user = admin
admin_password = <strong-password>  # Change default!
secret_key = <random-secret>
```

### Performance Tuning

```ini
[dataproxy]
timeout = 30
keep_alive_seconds = 30
max_idle_connections_per_host = 100

[panels]
enable_alpha = false
disable_sanitize_html = false
```

### High Availability (Optional)

- Use external database (PostgreSQL/MySQL) instead of SQLite
- Enable session storage in Redis for multi-instance deployments
- Configure shared storage for provisioning and dashboards
- Set up Grafana behind load balancer for redundancy

---

## Troubleshooting

### Dashboard not loading

```bash
# Check Grafana logs
docker logs grafana-container-name --tail 100

# Check Grafana API health
curl http://localhost:3000/api/health

# Verify dashboard exists
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  http://localhost:3000/api/dashboards/uid/tool-cache-performance
```

### Metrics not appearing

```bash
# 1. Check metrics endpoint
curl http://localhost:8000/metrics | grep -E "tool_cache|tool_run_seconds"

# 2. Check Prometheus scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="crew-cache-metrics")'

# 3. Query Prometheus directly
curl 'http://localhost:9090/api/v1/query?query=tool_cache_hits_total'

# 4. Check Grafana datasource connection
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  http://localhost:3000/api/datasources/proxy/1/api/v1/label/__name__/values
```

### Panel "No data" errors

- **Check query syntax**: Click panel title → Edit → Query tab, verify PromQL
- **Check time range**: Ensure time range covers period with metrics
- **Check label selectors**: Verify namespace/tool labels match actual metrics
- **Check Prometheus data retention**: Ensure retention period covers dashboard time range

### High memory usage

- Reduce dashboard refresh interval (10s → 30s)
- Limit time range queries (avoid "Last 30 days" with 5s resolution)
- Optimize PromQL queries (use rate() instead of increase() where possible)
- Enable query caching in Grafana datasource settings

---

## Related Documentation

- **Cache Usage Guide**: `docs/cache_usage_guide.md`
- **Metrics API Fixes**: `METRICS_API_FIXES_COMPLETE.md`
- **Import Fixes**: `TEST_SUITE_IMPORT_FIXES_COMPLETE.md`
- **Cache Benchmarking**: `benchmarks/results/cache_performance_benchmark_*.json`
- **Prometheus Metrics**: `docs/observability.md`

---

## Support & Feedback

- **Issues**: Report dashboard bugs via GitHub Issues
- **Feature Requests**: Suggest new panels/metrics via team discussion
- **Updates**: Dashboard JSON is version-controlled, check git history for changes
- **Questions**: Contact SRE team or check team wiki

---

**Deployment Status**: Ready for production  
**Estimated Deployment Time**: 30 minutes (initial setup) + 10 minutes (validation)  
**Required Access**: Grafana admin, Prometheus configuration  
**Last Validated**: November 5, 2025
