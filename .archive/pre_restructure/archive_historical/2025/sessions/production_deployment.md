# Production Deployment Guide

## Ultimate Content Intelligence Ecosystem

This guide provides comprehensive instructions for deploying the Ultimate Content Intelligence Ecosystem to production.

## Prerequisites

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended
- **Storage**: 50GB+ available space
- **Network**: Stable internet connection for API calls

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ultimate-discord-intelligence-bot
```

### 2. Configure Environment

```bash
# Copy and edit environment template
cp .env.example .env.production
# Edit with your actual credentials
nano .env.production
```

### 3. Deploy

```bash
# Run the deployment script
./scripts/production_deployment.sh
```

## Configuration

### Environment Variables

#### Discord Bot Configuration

```bash
DISCORD_BOT_TOKEN=your_discord_bot_token_here
```

#### LLM Services

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

#### Platform OAuth Credentials

```bash
# YouTube
YOUTUBE_CLIENT_ID=your_youtube_client_id_here
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret_here

# Twitch
TWITCH_CLIENT_ID=your_twitch_client_id_here
TWITCH_CLIENT_SECRET=your_twitch_client_secret_here

# TikTok
TIKTOK_CLIENT_KEY=your_tiktok_client_key_here
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret_here

# Instagram
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here

# X (Twitter)
X_API_KEY=your_x_api_key_here
X_API_SECRET=your_x_api_secret_here
X_ACCESS_TOKEN=your_x_access_token_here
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here
```

#### Database Configuration

```bash
POSTGRES_DB=ultimate_discord_intelligence
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
```

#### Storage Configuration

```bash
# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_secure_minio_password_here

# Redis
REDIS_PASSWORD=your_secure_redis_password_here
```

#### Monitoring Configuration

```bash
ENABLE_PROMETHEUS_ENDPOINT=true
ENABLE_HTTP_METRICS=true
ENABLE_TRACING=true
```

## Service Architecture

### Core Services

- **PostgreSQL** (Port 5432): Primary database
- **Redis** (Port 6380): Cache and message queues
- **Qdrant** (Port 6333): Vector database for embeddings
- **MinIO** (Port 9000/9001): Object storage for media files

### Application Services

- **Creator Operations API** (Port 8001): REST API service
- **Creator Operations Worker**: Background processing
- **Discord Bot**: Discord integration service

### Monitoring Services

- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Loki**: Log aggregation

## Deployment Commands

### Full Deployment

```bash
./scripts/production_deployment.sh
```

### Individual Operations

```bash
# Check prerequisites only
./scripts/production_deployment.sh check

# Deploy services only
./scripts/production_deployment.sh deploy

# Run health checks only
./scripts/production_deployment.sh health

# Initialize monitoring only
./scripts/production_deployment.sh monitor

# Stop all services
./scripts/production_deployment.sh stop

# View logs
./scripts/production_deployment.sh logs
```

## Health Monitoring

### Health Check Endpoints

- **API Health**: `http://localhost:8001/health`
- **Metrics**: `http://localhost:8001/metrics`
- **Performance Dashboard**: `http://localhost:8001/dashboard`

### Service Health Checks

```bash
# Check all services
docker-compose -f docker-compose.creator-ops.yml ps

# Check specific service
docker-compose -f docker-compose.creator-ops.yml ps postgres

# View service logs
docker-compose -f docker-compose.creator-ops.yml logs creator-ops-api
```

### Monitoring Integration

```python
from ultimate_discord_intelligence_bot.monitoring import get_production_monitor

# Get monitor instance
monitor = get_production_monitor()

# Get comprehensive metrics
metrics = monitor.get_comprehensive_metrics()

# Run health checks
health = monitor.run_health_checks()

# Start continuous monitoring
monitor.start_monitoring(interval=30)
```

## Performance Optimization

### Resource Allocation

```yaml
# docker-compose.creator-ops.yml
services:
  creator-ops-worker:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Caching Configuration

```bash
# Redis cache settings
REDIS_CACHE_TTL=3600
REDIS_MAX_CONNECTIONS=100

# LLM cache settings
ENABLE_LLM_CACHE=true
LLM_CACHE_SIZE=1000
```

### Database Optimization

```bash
# PostgreSQL settings
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
POSTGRES_WORK_MEM=4MB
```

## Security Configuration

### Authentication

- OAuth 2.0 for platform integrations
- JWT tokens for API authentication
- Encrypted credential storage

### Network Security

- Internal Docker networks
- Firewall rules for external access
- HTTPS/TLS for external communications

### Data Protection

- Encrypted data at rest
- Secure credential management
- Privacy filtering for user content

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.creator-ops.yml logs service-name

# Check resource usage
docker stats

# Restart service
docker-compose -f docker-compose.creator-ops.yml restart service-name
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose -f docker-compose.creator-ops.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.creator-ops.yml logs postgres
```

#### Memory Issues

```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.creator-ops.yml
# Restart services
docker-compose -f docker-compose.creator-ops.yml restart
```

#### API Not Responding

```bash
# Check API health
curl http://localhost:8001/health

# Check API logs
docker-compose -f docker-compose.creator-ops.yml logs creator-ops-api

# Restart API service
docker-compose -f docker-compose.creator-ops.yml restart creator-ops-api
```

### Performance Issues

#### High CPU Usage

- Check agent execution patterns
- Optimize tool caching
- Reduce concurrent job limits

#### High Memory Usage

- Check vector database size
- Optimize embedding storage
- Increase Redis memory limits

#### Slow Response Times

- Check database query performance
- Optimize cache hit rates
- Review network latency

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.creator-ops.yml exec postgres pg_dump -U postgres ultimate_discord_intelligence > backup.sql

# Restore backup
docker-compose -f docker-compose.creator-ops.yml exec -T postgres psql -U postgres ultimate_discord_intelligence < backup.sql
```

### Vector Database Backup

```bash
# Backup Qdrant collections
curl -X POST "http://localhost:6333/collections/{collection_name}/snapshots"
```

### Configuration Backup

```bash
# Backup configuration files
tar -czf config-backup.tar.gz .env.production docker-compose.creator-ops.yml
```

## Scaling

### Horizontal Scaling

```yaml
# Scale worker services
docker-compose -f docker-compose.creator-ops.yml up -d --scale creator-ops-worker=3
```

### Vertical Scaling

- Increase CPU/memory limits in docker-compose.creator-ops.yml
- Restart services to apply changes

### Load Balancing

- Use nginx or similar for API load balancing
- Configure multiple worker instances

## Maintenance

### Regular Tasks

- Monitor disk space usage
- Review log files for errors
- Update Docker images regularly
- Backup databases weekly

### Updates

```bash
# Pull latest images
docker-compose -f docker-compose.creator-ops.yml pull

# Rebuild and restart
docker-compose -f docker-compose.creator-ops.yml up -d --build
```

## Support

### Logs and Diagnostics

```bash
# System logs
docker-compose -f docker-compose.creator-ops.yml logs

# Service-specific logs
docker-compose -f docker-compose.creator-ops.yml logs creator-ops-api

# Resource usage
docker stats
```

### Monitoring Dashboards

- Access Grafana at configured port
- View Prometheus metrics
- Monitor system health via API endpoints

For additional support, check the troubleshooting section or review the monitoring dashboards for system health indicators.
