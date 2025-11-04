# Operational Guides

This document provides comprehensive operational guidance for deploying, monitoring, and maintaining the Ultimate Discord Intelligence Bot system.

## Deployment Guide

### Prerequisites

#### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.10 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 20GB free space
- **Network**: Stable internet connection for API access

#### Required Services

- **Database**: PostgreSQL 13+ or SQLite (for development)
- **Vector Database**: Qdrant (for semantic search)
- **Cache**: Redis (optional, for performance)
- **Message Queue**: RabbitMQ or Redis (for async processing)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/your-org/ultimate-discord-intelligence-bot.git
cd ultimate-discord-intelligence-bot
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.lock
```

#### 4. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:

```bash
# Core API Keys
OPENROUTER_API_KEY=your_openrouter_key
SERPER_API_KEY=your_serper_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/udi_db

# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# Feature Flags
ENABLE_UNIFIED_KNOWLEDGE=true
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true

# System Configuration
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=3600
MAX_RETRIES=5
RETRY_DELAY_SECONDS=2
```

#### 5. Database Setup

```bash
# Initialize database
python -m ultimate_discord_intelligence_bot.db.init

# Run migrations
python -m ultimate_discord_intelligence_bot.db.migrate
```

#### 6. Start Services

```bash
# Start Qdrant (if using local instance)
docker run -p 6333:6333 qdrant/qdrant

# Start the application
python -m ultimate_discord_intelligence_bot.main
```

### Docker Deployment

#### 1. Build Docker Image

```bash
docker build -t ultimate-discord-intelligence-bot .
```

#### 2. Run with Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Docker Compose Configuration

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/udi_db
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - db
      - qdrant
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: udi_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  qdrant_data:
```

### Production Deployment

#### 1. Infrastructure Setup

**Recommended Architecture:**

- **Load Balancer**: Nginx or HAProxy
- **Application Servers**: 2+ instances behind load balancer
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster
- **Vector Database**: Qdrant cluster
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or similar

#### 2. Security Configuration

```bash
# Firewall rules
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable

# SSL/TLS certificates
certbot --nginx -d your-domain.com
```

#### 3. Process Management

Using systemd:

```ini
[Unit]
Description=Ultimate Discord Intelligence Bot
After=network.target

[Service]
Type=simple
User=udi
WorkingDirectory=/opt/ultimate-discord-intelligence-bot
Environment=PATH=/opt/ultimate-discord-intelligence-bot/venv/bin
ExecStart=/opt/ultimate-discord-intelligence-bot/venv/bin/python -m ultimate_discord_intelligence_bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Monitoring Guide

### Health Checks

#### Application Health

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

#### Database Health

```bash
# Database connectivity
curl http://localhost:8000/health/db

# Database performance
curl http://localhost:8000/health/db/performance
```

#### External Services Health

```bash
# External API health
curl http://localhost:8000/health/external

# Qdrant health
curl http://localhost:8000/health/qdrant
```

### Metrics Collection

#### Prometheus Metrics

The system exposes metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:

- **Request counts**: `http_requests_total`
- **Response times**: `http_request_duration_seconds`
- **Error rates**: `http_requests_errors_total`
- **Memory usage**: `process_resident_memory_bytes`
- **CPU usage**: `process_cpu_seconds_total`

#### Custom Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
REQUEST_COUNT = Counter('udi_requests_total', 'Total requests', ['method', 'endpoint'])

# Response time histogram
REQUEST_DURATION = Histogram('udi_request_duration_seconds', 'Request duration')

# Active connections gauge
ACTIVE_CONNECTIONS = Gauge('udi_active_connections', 'Active connections')
```

### Logging Configuration

#### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about system operation
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause system failure

#### Log Format

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'tenant'):
            log_entry['tenant'] = record.tenant
        if hasattr(record, 'workspace'):
            log_entry['workspace'] = record.workspace

        return json.dumps(log_entry)
```

#### Log Rotation

```bash
# Logrotate configuration
/var/log/ultimate-discord-intelligence-bot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 udi udi
    postrotate
        systemctl reload ultimate-discord-intelligence-bot
    endscript
}
```

### Alerting

#### Alert Rules

```yaml
# Prometheus alert rules
groups:
- name: ultimate-discord-intelligence-bot
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"

  - alert: DatabaseConnectionFailure
    expr: up{job="postgresql"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection failed"
      description: "Cannot connect to PostgreSQL database"
```

#### Notification Channels

```yaml
# Alertmanager configuration
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://your-webhook-url'
    send_resolved: true

- name: 'email'
  email_configs:
  - to: 'admin@your-domain.com'
    from: 'alerts@your-domain.com'
    smarthost: 'smtp.your-domain.com:587'
    auth_username: 'alerts@your-domain.com'
    auth_password: 'your-password'
```

## Maintenance Guide

### Regular Maintenance Tasks

#### Daily Tasks

1. **Check system health**

   ```bash
   curl http://localhost:8000/health
   ```

2. **Review error logs**

   ```bash
   tail -f /var/log/ultimate-discord-intelligence-bot/error.log
   ```

3. **Monitor resource usage**

   ```bash
   htop
   df -h
   ```

#### Weekly Tasks

1. **Database maintenance**

   ```bash
   # Analyze tables
   psql -d udi_db -c "ANALYZE;"

   # Vacuum database
   psql -d udi_db -c "VACUUM;"
   ```

2. **Log rotation**

   ```bash
   # Check log rotation
   logrotate -d /etc/logrotate.d/ultimate-discord-intelligence-bot
   ```

3. **Security updates**

   ```bash
   apt update && apt upgrade
   ```

#### Monthly Tasks

1. **Performance analysis**

   ```bash
   # Generate performance report
   python -m ultimate_discord_intelligence_bot.scripts.performance_report
   ```

2. **Capacity planning**

   ```bash
   # Analyze growth trends
   python -m ultimate_discord_intelligence_bot.scripts.capacity_analysis
   ```

3. **Backup verification**

   ```bash
   # Test backup restoration
   python -m ultimate_discord_intelligence_bot.scripts.test_backup
   ```

### Backup and Recovery

#### Database Backup

```bash
# Full backup
pg_dump -h localhost -U postgres udi_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Incremental backup
pg_dump -h localhost -U postgres --schema-only udi_db > schema_backup.sql
```

#### Application Backup

```bash
# Backup application data
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    /opt/ultimate-discord-intelligence-bot/data \
    /opt/ultimate-discord-intelligence-bot/config
```

#### Qdrant Backup

```bash
# Backup Qdrant collections
curl -X POST "http://localhost:6333/collections/backup" \
     -H "Content-Type: application/json" \
     -d '{"collection_name": "your_collection", "backup_path": "/backup/path"}'
```

#### Recovery Procedures

1. **Database Recovery**

   ```bash
   # Restore from backup
   psql -h localhost -U postgres udi_db < backup_20240101_120000.sql
   ```

2. **Application Recovery**

   ```bash
   # Restore application data
   tar -xzf app_backup_20240101_120000.tar.gz -C /
   ```

3. **Qdrant Recovery**

   ```bash
   # Restore Qdrant collection
   curl -X POST "http://localhost:6333/collections/restore" \
        -H "Content-Type: application/json" \
        -d '{"collection_name": "your_collection", "backup_path": "/backup/path"}'
   ```

### Performance Tuning

#### Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_content_tenant_workspace ON content(tenant, workspace);
CREATE INDEX idx_content_created_at ON content(created_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM content WHERE tenant = 'tenant_123';
```

#### Application Optimization

```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Caching configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
}
```

#### System Optimization

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

### Troubleshooting

#### Common Issues

1. **High Memory Usage**

   ```bash
   # Check memory usage
   free -h
   ps aux --sort=-%mem | head

   # Check for memory leaks
   python -m ultimate_discord_intelligence_bot.scripts.memory_analysis
   ```

2. **Database Connection Issues**

   ```bash
   # Check database connectivity
   psql -h localhost -U postgres -c "SELECT 1;"

   # Check connection pool
   python -m ultimate_discord_intelligence-bot.scripts.db_health
   ```

3. **API Rate Limiting**

   ```bash
   # Check rate limit status
   curl http://localhost:8000/health/rate_limits

   # Adjust rate limiting
   export OPENROUTER_RATE_LIMIT=100
   ```

#### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Start with debug mode
python -m ultimate_discord_intelligence_bot.main --debug
```

#### Performance Profiling

```python
# Profile application performance
import cProfile
import pstats

def profile_function():
    # Your code here
    pass

cProfile.run('profile_function()', 'profile_output.prof')

# Analyze results
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative').print_stats(10)
```

### Security Maintenance

#### Regular Security Tasks

1. **Update dependencies**

   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

2. **Security scanning**

   ```bash
   # Scan for vulnerabilities
   safety check
   bandit -r src/
   ```

3. **Access review**

   ```bash
   # Review user access
   python -m ultimate_discord_intelligence_bot.scripts.access_review
   ```

#### Security Monitoring

```python
# Monitor for suspicious activity
import logging

security_logger = logging.getLogger('security')

def log_security_event(event_type, details):
    security_logger.warning(f"Security event: {event_type}", extra={
        'event_type': event_type,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    })
```

### Disaster Recovery

#### Recovery Time Objectives (RTO)

- **Critical systems**: 1 hour
- **Important systems**: 4 hours
- **Standard systems**: 24 hours

#### Recovery Point Objectives (RPO)

- **Critical data**: 15 minutes
- **Important data**: 1 hour
- **Standard data**: 24 hours

#### Recovery Procedures

1. **Assess damage**

   ```bash
   # Check system status
   systemctl status ultimate-discord-intelligence-bot

   # Check data integrity
   python -m ultimate_discord_intelligence_bot.scripts.integrity_check
   ```

2. **Restore services**

   ```bash
   # Restore from backup
   python -m ultimate_discord_intelligence_bot.scripts.disaster_recovery
   ```

3. **Validate recovery**

   ```bash
   # Run health checks
   curl http://localhost:8000/health

   # Run integration tests
   pytest tests/integration/
   ```

## Best Practices

### Operational Excellence

1. **Automate everything**: Use scripts and tools for repetitive tasks
2. **Monitor proactively**: Set up alerts before issues occur
3. **Document procedures**: Keep operational procedures up to date
4. **Test recovery**: Regularly test backup and recovery procedures
5. **Plan for scale**: Design systems to handle growth

### Security Best Practices

1. **Principle of least privilege**: Grant minimum necessary permissions
2. **Defense in depth**: Implement multiple security layers
3. **Regular updates**: Keep systems and dependencies updated
4. **Monitor access**: Track and audit all system access
5. **Incident response**: Have clear procedures for security incidents

### Performance Best Practices

1. **Measure first**: Profile before optimizing
2. **Cache appropriately**: Use caching for frequently accessed data
3. **Optimize queries**: Ensure database queries are efficient
4. **Monitor resources**: Track CPU, memory, and disk usage
5. **Plan capacity**: Monitor growth and plan for scaling
