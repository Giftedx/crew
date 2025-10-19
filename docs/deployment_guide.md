# Production Deployment Guide

This guide provides comprehensive instructions for deploying the Ultimate Discord Intelligence Bot to staging and production environments.

## Prerequisites

### System Requirements

- **Docker**: Version 20.10+ with Docker Compose
- **Memory**: Minimum 8GB RAM, Recommended 16GB+
- **Storage**: Minimum 100GB available disk space
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Network**: Stable internet connection for external API calls

### Required Environment Variables

#### Core Configuration

```bash
# Discord Bot
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id

# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key
QDRANT_API_KEY=your_qdrant_api_key

# OAuth Credentials
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
X_CLIENT_ID=your_x_client_id
X_CLIENT_SECRET=your_x_client_secret

# Monitoring
DISCORD_WEBHOOK_URL=your_discord_webhook_url
GRAFANA_PASSWORD=your_grafana_password
```

## Deployment Process

### 1. Staging Deployment

#### Step 1: Prepare Environment

```bash
# Clone repository
git clone <repository-url>
cd ultimate-discord-intelligence-bot

# Copy staging configuration
cp ops/deployment/staging/staging.env .env

# Set environment variables
export $(cat .env | xargs)
```

#### Step 2: Deploy to Staging

```bash
# Run deployment script
python3 scripts/deploy_production.py --environment staging

# Or deploy manually
docker-compose -f ops/deployment/docker/docker-compose.yml up -d
```

#### Step 3: Verify Deployment

```bash
# Check service status
docker-compose -f ops/deployment/docker/docker-compose.yml ps

# View logs
docker-compose -f ops/deployment/docker/docker-compose.yml logs -f

# Run health checks
curl http://localhost:8080/health
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

### 2. Production Deployment

#### Step 1: Prepare Production Environment

```bash
# Copy production configuration
cp ops/deployment/production/production.env .env

# Set secure environment variables
export $(cat .env | xargs)
```

#### Step 2: Deploy to Production

```bash
# Run deployment script
python3 scripts/deploy_production.py --environment production

# Or deploy manually with production settings
docker-compose -f ops/deployment/docker/docker-compose.yml --env-file .env up -d
```

#### Step 3: Post-Deployment Verification

```bash
# Run comprehensive tests
python3 scripts/test_service_integration.py
python3 scripts/test_end_to_end_workflow.py
python3 scripts/validate_mcp_tools.py

# Check monitoring dashboards
# Grafana: http://localhost:3000 (admin/staging_grafana_admin)
# Prometheus: http://localhost:9090
```

## Service Architecture

### Core Services

1. **Discord Bot** (`discord-bot`)
   - Handles Discord interactions
   - Processes user commands
   - Manages bot responses

2. **API Server** (`api-server`)
   - REST API endpoints
   - Health checks
   - Metrics exposure

3. **Worker Processes** (`worker-processes`)
   - Background task processing
   - Content analysis
   - Memory operations

### Infrastructure Services

1. **PostgreSQL** (`postgresql`)
   - Primary database
   - User data storage
   - Configuration management

2. **Redis** (`redis`)
   - Caching layer
   - Session storage
   - Queue management

3. **Qdrant** (`qdrant`)
   - Vector database
   - Embedding storage
   - Semantic search

4. **MinIO** (`minio`)
   - Object storage
   - File management
   - Backup storage

### Monitoring Services

1. **Prometheus** (`prometheus`)
   - Metrics collection
   - Alerting rules
   - Data retention

2. **Grafana** (`grafana`)
   - Dashboards
   - Visualization
   - Alert management

3. **Alertmanager** (`alertmanager`)
   - Alert routing
   - Notification management
   - Escalation policies

## Configuration Management

### Environment-Specific Settings

#### Staging

- **Log Level**: INFO
- **Debug Mode**: false
- **Resource Limits**: Lower
- **Retention**: 7 days
- **Rate Limits**: 100 req/min

#### Production

- **Log Level**: WARNING
- **Debug Mode**: false
- **Resource Limits**: Higher
- **Retention**: 30 days
- **Rate Limits**: 1000 req/min

### Feature Flags

```bash
# Enable/disable features
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_MEMORY_STORAGE=true
ENABLE_MCP_TOOLS=true
ENABLE_OAUTH_INTEGRATION=true
```

## Monitoring and Observability

### Key Metrics

1. **Application Metrics**
   - Request rate and latency
   - Error rates
   - Memory usage
   - CPU utilization

2. **Business Metrics**
   - Content processing rate
   - Analysis accuracy
   - User engagement
   - Cost per operation

3. **Infrastructure Metrics**
   - Database performance
   - Cache hit rates
   - Network latency
   - Storage usage

### Alerting Rules

1. **Critical Alerts**
   - Service down
   - High error rate (>5%)
   - Memory usage (>90%)
   - Disk space (<10%)

2. **Warning Alerts**
   - High latency (>2s)
   - Low cache hit rate (<60%)
   - Queue backlog (>100)
   - OAuth token expiration

### Dashboards

1. **System Overview**
   - Service health
   - Resource utilization
   - Error rates
   - Performance metrics

2. **Business Intelligence**
   - Content analysis trends
   - User activity patterns
   - Cost analysis
   - Quality metrics

## Security Considerations

### Network Security

- All services run in isolated Docker network
- No direct external access to internal services
- HTTPS/TLS for external communications
- Rate limiting and DDoS protection

### Data Security

- Encrypted data at rest
- Secure credential management
- PII redaction and privacy filters
- Audit logging for sensitive operations

### Access Control

- Role-based access control
- Multi-factor authentication
- API key rotation
- Principle of least privilege

## Backup and Recovery

### Data Backup

```bash
# Database backup
docker exec postgresql pg_dump -U discord_user discord_intelligence > backup.sql

# Vector database backup
docker exec qdrant tar -czf /backup/qdrant_backup.tar.gz /qdrant/storage

# Object storage backup
docker exec minio mc mirror /data s3://backup-bucket/
```

### Recovery Procedures

1. **Service Recovery**: Automatic restart policies
2. **Data Recovery**: Point-in-time recovery from backups
3. **Disaster Recovery**: Multi-region deployment strategy

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   - Check environment variables
   - Verify Docker daemon is running
   - Check port conflicts
   - Review container logs

2. **High Memory Usage**
   - Monitor memory leaks
   - Adjust container limits
   - Optimize application code
   - Scale horizontally

3. **Database Connection Issues**
   - Verify connection strings
   - Check network connectivity
   - Review authentication
   - Monitor connection pools

### Debug Commands

```bash
# View service logs
docker-compose logs -f [service-name]

# Check service status
docker-compose ps

# Access service shell
docker-compose exec [service-name] /bin/bash

# Monitor resource usage
docker stats

# Check network connectivity
docker-compose exec [service-name] ping [target-service]
```

## Performance Optimization

### Scaling Strategies

1. **Horizontal Scaling**
   - Multiple worker instances
   - Load balancing
   - Database read replicas
   - CDN for static content

2. **Vertical Scaling**
   - Increase container resources
   - Optimize database queries
   - Cache frequently accessed data
   - Use faster storage

### Performance Tuning

1. **Database Optimization**
   - Index optimization
   - Query optimization
   - Connection pooling
   - Read/write splitting

2. **Caching Strategy**
   - Redis for hot data
   - Application-level caching
   - CDN for static assets
   - Browser caching

## Maintenance

### Regular Tasks

1. **Daily**
   - Monitor system health
   - Check error logs
   - Verify backups
   - Review alerts

2. **Weekly**
   - Update dependencies
   - Review performance metrics
   - Clean up old data
   - Test disaster recovery

3. **Monthly**
   - Security updates
   - Capacity planning
   - Cost optimization
   - Documentation updates

### Update Procedures

1. **Application Updates**

   ```bash
   # Pull latest changes
   git pull origin main
   
   # Rebuild and restart services
   docker-compose build
   docker-compose up -d
   
   # Run health checks
   python3 scripts/deploy_production.py --environment production
   ```

2. **Infrastructure Updates**
   - Plan maintenance windows
   - Test in staging first
   - Coordinate with team
   - Monitor during updates

## Support and Documentation

### Resources

- **API Documentation**: `/docs/api/`
- **Architecture Guide**: `/docs/architecture/`
- **Configuration Reference**: `/docs/configuration.md`
- **Troubleshooting Guide**: `/docs/troubleshooting.md`

### Contact Information

- **Technical Support**: <support@discord-intelligence.com>
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Documentation**: <docs@discord-intelligence.com>

### Escalation Procedures

1. **Level 1**: Application logs and basic troubleshooting
2. **Level 2**: Infrastructure and system-level issues
3. **Level 3**: Critical system failures and data loss
4. **Level 4**: External vendor and third-party issues
