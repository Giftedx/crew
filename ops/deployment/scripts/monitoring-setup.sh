#!/bin/bash

# Ultimate Discord Intelligence Bot - Production Monitoring Setup
# This script sets up comprehensive monitoring and observability

set -e  # Exit on any error

echo "📊 Production Monitoring Setup"
echo "=============================="

# Create config directories
echo "📁 Creating configuration directories..."
mkdir -p config/{grafana/{dashboards,datasources},prometheus,nginx}
mkdir -p logs data ssl

# Create Prometheus configuration
echo "⚙️ Creating Prometheus configuration..."
cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"

scrape_configs:
  - job_name: 'discord-bot'
    static_configs:
      - targets: ['discord-bot:8000']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - "alertmanager:9093"
EOF

# Create Grafana datasources
echo "📈 Creating Grafana datasources..."
cat > config/grafana/datasources/prometheus.yaml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    access: proxy

  - name: Loki
    type: loki
    url: http://loki:3100
    access: proxy
EOF

# Create Grafana dashboard
echo "📊 Creating Grafana dashboards..."
cat > config/grafana/dashboards/bot-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Ultimate Discord Intelligence Bot",
    "tags": ["discord", "bot", "monitoring"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Bot Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"discord-bot\"}",
            "legendFormat": "Bot Online"
          }
        ]
      },
      {
        "id": 2,
        "title": "Message Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(discord_messages_processed_total[5m])",
            "legendFormat": "Messages/sec"
          }
        ]
      },
      {
        "id": 3,
        "title": "API Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}
EOF

# Create Loki configuration
echo "📝 Creating Loki configuration..."
cat > config/loki.yml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /tmp/loki
  storage:
    filesystem:
      chunks_directory: /tmp/loki/chunks
      rules_directory: /tmp/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
EOF

# Create Redis configuration
echo "🔴 Creating Redis configuration..."
cat > config/redis.conf << 'EOF'
# Redis production configuration
bind 0.0.0.0
port 6379
tcp-backlog 511

timeout 0
tcp-keepalive 300

daemonize no
supervised no
pidfile /var/run/redis_6379.pid

loglevel notice
logfile ""

databases 16

save 900 1
save 300 10
save 60 10000

stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb

maxmemory 256mb
maxmemory-policy allkeys-lru

appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
EOF

# Create environment template for production
echo "🌐 Creating production environment template..."
cat > .env.production.template << 'EOF'
# Production Environment Configuration

# Required API Keys
DISCORD_BOT_TOKEN=your-production-bot-token
OPENAI_API_KEY=your-production-openai-key

# Discord Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook
DISCORD_PRIVATE_WEBHOOK_URL=https://discord.com/api/webhooks/your-private-webhook

# Database Configuration
QDRANT_URL=http://qdrant:6333
REDIS_URL=redis://redis:6379

# Production Features
ENVIRONMENT=production
ENABLE_TRACING=true
ENABLE_PROMETHEUS_ENDPOINT=true
ENABLE_HTTP_METRICS=true
ENABLE_API=true

# Security
ENABLE_PII_DETECTION=true
ENABLE_CONTENT_MODERATION=true
ENABLE_RATE_LIMITING=true

# Performance
MAX_WORKERS=8
VECTOR_BATCH_SIZE=256
RATE_LIMIT_RPS=50
RATE_LIMIT_BURST=100

# Monitoring
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true

# Grafana (Optional)
GRAFANA_PASSWORD=secure-password-here
EOF

echo ""
echo "✅ Production monitoring setup complete!"
echo "======================================="
echo ""
echo "📋 Next steps:"
echo "1. Copy .env.production.template to .env.production and configure"
echo "2. Start services: docker-compose -f ops/deployment/docker/production.yml up -d"
echo "3. Access dashboards:"
echo "   - Grafana: http://localhost:3000 (admin/changeme)"
echo "   - Prometheus: http://localhost:9090"
echo ""
echo "📊 Monitoring features:"
echo "- ✅ Prometheus metrics collection"
echo "- ✅ Grafana dashboards"
echo "- ✅ Loki log aggregation"
echo "- ✅ Health checks for all services"
echo "- ✅ Redis performance monitoring"
echo "- ✅ Qdrant vector database monitoring"
echo ""
echo "🔧 Management commands:"
echo "- View logs: docker-compose -f ops/deployment/docker/production.yml logs -f discord-bot"
echo "- Scale bot: docker-compose -f ops/deployment/docker/production.yml up -d --scale discord-bot=3"
echo "- Health check: docker-compose -f ops/deployment/docker/production.yml ps"
