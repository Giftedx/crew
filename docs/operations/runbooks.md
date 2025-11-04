# Operational Runbooks

## Overview

This document provides comprehensive operational runbooks for managing the Ultimate Discord Intelligence Bot unified system in production environments.

## System Health Monitoring

### Health Check Endpoints

#### Basic Health Check

```bash
curl -X GET https://api.example.com/health
```

**Expected Response:**

```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "uptime": 86400
}
```

#### Detailed Health Check

```bash
curl -X GET https://api.example.com/health/detailed
```

**Expected Response:**

```json
{
    "status": "healthy",
    "components": {
        "database": "healthy",
        "cache": "healthy",
        "vector_store": "healthy",
        "external_apis": "healthy"
    },
    "metrics": {
        "response_time": 150,
        "memory_usage": 75.5,
        "cpu_usage": 45.2
    }
}
```

### Monitoring Dashboards

#### Grafana Dashboard Access

- **URL**: <https://grafana.example.com/dashboards/unified-system>
- **Credentials**: See secure credential store
- **Key Metrics**: Response time, error rate, throughput, resource usage

#### Prometheus Metrics

- **URL**: <https://prometheus.example.com/graph>
- **Key Queries**:
  - `rate(http_requests_total[5m])` - Request rate
  - `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` - 95th percentile latency

## Incident Response

### Severity Levels

#### P1 - Critical

- System completely down
- Data loss or corruption
- Security breach
- **Response Time**: 15 minutes
- **Escalation**: Immediate

#### P2 - High

- Significant performance degradation
- Partial service outage
- High error rates
- **Response Time**: 1 hour
- **Escalation**: 2 hours

#### P3 - Medium

- Minor performance issues
- Non-critical feature failures
- **Response Time**: 4 hours
- **Escalation**: 8 hours

#### P4 - Low

- Cosmetic issues
- Enhancement requests
- **Response Time**: 24 hours
- **Escalation**: 48 hours

### Incident Response Process

#### 1. Detection and Alerting

```bash
# Check system status
curl -X GET https://api.example.com/health

# Check logs
kubectl logs -f deployment/unified-system --tail=100

# Check metrics
curl -X GET https://prometheus.example.com/api/v1/query?query=up
```

#### 2. Initial Response

1. Acknowledge the incident
2. Assess severity level
3. Notify relevant team members
4. Create incident ticket
5. Begin investigation

#### 3. Investigation

```bash
# Check system resources
kubectl top pods
kubectl top nodes

# Check application logs
kubectl logs deployment/unified-system --since=1h

# Check database status
kubectl exec -it postgres-pod -- psql -c "SELECT * FROM pg_stat_activity;"

# Check cache status
kubectl exec -it redis-pod -- redis-cli info
```

#### 4. Resolution

1. Implement fix
2. Verify resolution
3. Monitor for recurrence
4. Update incident ticket
5. Conduct post-incident review

### Common Issues and Solutions

#### High Memory Usage

**Symptoms:**

- Memory usage > 90%
- Slow response times
- Out of memory errors

**Diagnosis:**

```bash
# Check memory usage
kubectl top pods
kubectl describe pod unified-system-pod

# Check memory leaks
kubectl logs deployment/unified-system | grep -i "memory\|leak"
```

**Solutions:**

1. Restart the affected pod
2. Increase memory limits
3. Investigate memory leaks
4. Optimize memory usage

```bash
# Restart pod
kubectl rollout restart deployment/unified-system

# Increase memory limits
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

#### Database Connection Issues

**Symptoms:**

- Database connection errors
- Slow queries
- Connection timeouts

**Diagnosis:**

```bash
# Check database status
kubectl exec -it postgres-pod -- psql -c "SELECT * FROM pg_stat_activity;"

# Check connection pool
kubectl logs deployment/unified-system | grep -i "connection\|pool"
```

**Solutions:**

1. Check database health
2. Increase connection pool size
3. Optimize queries
4. Restart database if necessary

```bash
# Check database health
kubectl exec -it postgres-pod -- pg_isready

# Increase connection pool
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"DB_POOL_SIZE","value":"20"}]}]}}}}'
```

#### Cache Performance Issues

**Symptoms:**

- High cache miss rates
- Slow cache operations
- Cache connection errors

**Diagnosis:**

```bash
# Check cache status
kubectl exec -it redis-pod -- redis-cli info

# Check cache metrics
curl -X GET https://prometheus.example.com/api/v1/query?query=redis_keyspace_hits
```

**Solutions:**

1. Check cache health
2. Optimize cache configuration
3. Increase cache memory
4. Restart cache if necessary

```bash
# Check cache health
kubectl exec -it redis-pod -- redis-cli ping

# Increase cache memory
kubectl patch deployment redis -p '{"spec":{"template":{"spec":{"containers":[{"name":"redis","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

## Deployment Procedures

### Rolling Deployment

#### Pre-deployment Checklist

- [ ] All tests passing
- [ ] Database migrations ready
- [ ] Configuration updated
- [ ] Monitoring configured
- [ ] Rollback plan prepared

#### Deployment Steps

```bash
# 1. Update configuration
kubectl apply -f config/unified-system-config.yaml

# 2. Deploy new version
kubectl set image deployment/unified-system unified-system=registry.example.com/unified-system:v1.1.0

# 3. Monitor deployment
kubectl rollout status deployment/unified-system

# 4. Verify deployment
curl -X GET https://api.example.com/health

# 5. Check metrics
curl -X GET https://prometheus.example.com/api/v1/query?query=up
```

#### Rollback Procedure

```bash
# Rollback to previous version
kubectl rollout undo deployment/unified-system

# Verify rollback
kubectl rollout status deployment/unified-system
curl -X GET https://api.example.com/health
```

### Blue-Green Deployment

#### Blue-Green Setup

```bash
# Deploy green environment
kubectl apply -f deployments/unified-system-green.yaml

# Wait for green to be ready
kubectl wait --for=condition=available deployment/unified-system-green

# Switch traffic to green
kubectl patch service unified-system -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor green environment
kubectl logs -f deployment/unified-system-green
```

#### Blue-Green Rollback

```bash
# Switch traffic back to blue
kubectl patch service unified-system -p '{"spec":{"selector":{"version":"blue"}}}'

# Clean up green environment
kubectl delete deployment unified-system-green
```

## Database Operations

### Backup Procedures

#### Automated Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
kubectl exec postgres-pod -- pg_dump -U postgres unified_system > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://backups/unified-system/
```

#### Manual Backup

```bash
# Create backup
kubectl exec postgres-pod -- pg_dump -U postgres unified_system > manual_backup.sql

# Verify backup
kubectl exec postgres-pod -- psql -U postgres -c "SELECT pg_database_size('unified_system');"
```

### Restore Procedures

#### Full Restore

```bash
# Stop application
kubectl scale deployment unified-system --replicas=0

# Restore database
kubectl exec -i postgres-pod -- psql -U postgres unified_system < backup_20240101_120000.sql

# Start application
kubectl scale deployment unified-system --replicas=3
```

#### Point-in-Time Recovery

```bash
# Stop application
kubectl scale deployment unified-system --replicas=0

# Restore to specific time
kubectl exec postgres-pod -- psql -U postgres -c "SELECT pg_start_backup('recovery');"
kubectl exec postgres-pod -- psql -U postgres -c "SELECT pg_stop_backup();"

# Start application
kubectl scale deployment unified-system --replicas=3
```

### Migration Procedures

#### Database Migration

```bash
# Run migrations
kubectl exec deployment/unified-system -- python manage.py migrate

# Verify migration
kubectl exec deployment/unified-system -- python manage.py showmigrations
```

#### Schema Changes

```bash
# Create migration
kubectl exec deployment/unified-system -- python manage.py makemigrations

# Apply migration
kubectl exec deployment/unified-system -- python manage.py migrate

# Verify schema
kubectl exec postgres-pod -- psql -U postgres -c "\d unified_system"
```

## Performance Tuning

### Application Performance

#### Memory Optimization

```bash
# Check memory usage
kubectl top pods
kubectl describe pod unified-system-pod

# Optimize memory settings
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"PYTHONOPTIMIZE","value":"1"}]}]}}}}'
```

#### CPU Optimization

```bash
# Check CPU usage
kubectl top pods
kubectl describe pod unified-system-pod

# Optimize CPU settings
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","resources":{"requests":{"cpu":"500m"},"limits":{"cpu":"1000m"}}}]}}}}'
```

### Database Performance

#### Query Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze table statistics
ANALYZE unified_system;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

#### Connection Pool Optimization

```bash
# Check connection pool status
kubectl exec postgres-pod -- psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Optimize connection pool
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"DB_POOL_SIZE","value":"20"},{"name":"DB_POOL_OVERFLOW","value":"30"}]}]}}}}'
```

### Cache Performance

#### Redis Optimization

```bash
# Check Redis performance
kubectl exec redis-pod -- redis-cli info stats

# Optimize Redis configuration
kubectl patch deployment redis -p '{"spec":{"template":{"spec":{"containers":[{"name":"redis","args":["redis-server","--maxmemory","1gb","--maxmemory-policy","allkeys-lru"]}]}}}}'
```

#### Cache Hit Rate Optimization

```bash
# Check cache hit rate
kubectl exec redis-pod -- redis-cli info stats | grep keyspace

# Optimize cache TTL
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"CACHE_TTL","value":"3600"}]}]}}}}'
```

## Security Operations

### Security Monitoring

#### Access Log Analysis

```bash
# Check access logs
kubectl logs deployment/unified-system | grep -i "unauthorized\|forbidden\|error"

# Monitor failed login attempts
kubectl logs deployment/unified-system | grep -i "failed.*login"
```

#### Security Scanning

```bash
# Run security scan
kubectl exec deployment/unified-system -- python -m safety check

# Check for vulnerabilities
kubectl exec deployment/unified-system -- python -m bandit -r .
```

### Certificate Management

#### Certificate Renewal

```bash
# Check certificate expiration
kubectl get secrets -o jsonpath='{.items[?(@.type=="kubernetes.io/tls")].metadata.name}' | xargs -I {} kubectl get secret {} -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates

# Renew certificate
kubectl apply -f certificates/unified-system-tls.yaml
```

#### SSL/TLS Configuration

```bash
# Check SSL configuration
kubectl get ingress unified-system -o yaml

# Update SSL configuration
kubectl patch ingress unified-system -p '{"spec":{"tls":[{"secretName":"unified-system-tls","hosts":["api.example.com"]}]}}'
```

## Monitoring and Alerting

### Alert Configuration

#### Critical Alerts

```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"

# High memory usage
- alert: HighMemoryUsage
  expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High memory usage detected"
```

#### Warning Alerts

```yaml
# High response time
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High response time detected"

# Low cache hit rate
- alert: LowCacheHitRate
  expr: rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) < 0.8
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Low cache hit rate detected"
```

### Log Management

#### Log Aggregation

```bash
# Check log aggregation
kubectl logs deployment/unified-system --tail=100 | grep -i "error\|warning"

# Configure log levels
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"LOG_LEVEL","value":"INFO"}]}]}}}}'
```

#### Log Retention

```bash
# Check log retention
kubectl exec deployment/unified-system -- du -sh /var/log/

# Configure log rotation
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"LOG_RETENTION_DAYS","value":"30"}]}]}}}}'
```

## Disaster Recovery

### Backup and Recovery

#### System Backup

```bash
# Create system backup
kubectl create configmap system-backup --from-file=backup.sh
kubectl apply -f backup-job.yaml
```

#### Disaster Recovery Plan

1. **Assessment**: Evaluate the scope of the disaster
2. **Communication**: Notify stakeholders
3. **Recovery**: Execute recovery procedures
4. **Validation**: Verify system functionality
5. **Documentation**: Document lessons learned

### Failover Procedures

#### Database Failover

```bash
# Check primary database
kubectl exec postgres-primary -- pg_isready

# Promote standby database
kubectl exec postgres-standby -- pg_ctl promote

# Update application configuration
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"DB_HOST","value":"postgres-standby"}]}]}}}}'
```

#### Application Failover

```bash
# Check application health
kubectl get pods -l app=unified-system

# Scale up standby region
kubectl scale deployment unified-system-standby --replicas=3

# Update load balancer
kubectl patch service unified-system -p '{"spec":{"selector":{"region":"standby"}}}'
```

## Troubleshooting Guide

### Common Issues

#### Application Won't Start

```bash
# Check pod status
kubectl get pods -l app=unified-system

# Check pod logs
kubectl logs deployment/unified-system

# Check pod description
kubectl describe pod unified-system-pod
```

#### Database Connection Issues

```bash
# Check database status
kubectl exec postgres-pod -- pg_isready

# Check connection pool
kubectl logs deployment/unified-system | grep -i "connection"

# Test database connection
kubectl exec deployment/unified-system -- python -c "import psycopg2; print('Connection test')"
```

#### Cache Issues

```bash
# Check cache status
kubectl exec redis-pod -- redis-cli ping

# Check cache logs
kubectl logs deployment/redis

# Test cache connection
kubectl exec deployment/unified-system -- python -c "import redis; print('Cache test')"
```

### Debug Commands

#### Application Debug

```bash
# Enable debug logging
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"DEBUG","value":"true"}]}]}}}}'

# Check debug logs
kubectl logs deployment/unified-system | grep -i "debug"
```

#### System Debug

```bash
# Check system resources
kubectl top pods
kubectl top nodes

# Check system events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check network connectivity
kubectl exec deployment/unified-system -- ping postgres-pod
```

## Maintenance Windows

### Scheduled Maintenance

#### Weekly Maintenance

- **Time**: Sunday 2:00 AM - 4:00 AM UTC
- **Tasks**:
  - System updates
  - Database maintenance
  - Log cleanup
  - Performance optimization

#### Monthly Maintenance

- **Time**: First Saturday 2:00 AM - 6:00 AM UTC
- **Tasks**:
  - Security patches
  - Database backups
  - Certificate renewal
  - Capacity planning

### Maintenance Procedures

#### Pre-Maintenance

```bash
# Notify users
kubectl create configmap maintenance-notice --from-literal=message="Scheduled maintenance in progress"

# Create maintenance mode
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"MAINTENANCE_MODE","value":"true"}]}]}}}}'
```

#### Post-Maintenance

```bash
# Remove maintenance mode
kubectl patch deployment unified-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"unified-system","env":[{"name":"MAINTENANCE_MODE","value":"false"}]}]}}}}'

# Verify system health
curl -X GET https://api.example.com/health

# Remove maintenance notice
kubectl delete configmap maintenance-notice
```
