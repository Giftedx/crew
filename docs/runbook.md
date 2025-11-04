# Ultimate Discord Intelligence Bot - Operations Runbook

## Overview

This runbook provides operational guidance for the Ultimate Discord Intelligence Bot, including deployment, monitoring, troubleshooting, and maintenance procedures.

## System Architecture

### Core Components

- **CrewAI Orchestrator**: Main agent coordination system
- **Content Pipeline**: Multi-platform content processing
- **Vector Memory**: Qdrant-based knowledge storage
- **Discord Integration**: Bot commands and webhook publishing
- **Observability**: Metrics, logging, and health monitoring

### Data Flow

```
Content Sources → Ingestion → Transcription → Analysis → Memory → Discord
```

## Deployment

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Environment variables configured
- Required API keys and tokens

### Environment Setup

1. **Copy environment template**:

   ```bash
   cp .env.example .env
   ```

2. **Configure required variables**:

   ```bash
   # Discord
   DISCORD_BOT_TOKEN=Bot your_token_here
   DISCORD_PRIVATE_WEBHOOK=https://discord.com/api/webhooks/...

   # LLM Services
   OPENAI_API_KEY=your_openai_key
   # OR
   OPENROUTER_API_KEY=your_openrouter_key

   # Vector Database
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=your_qdrant_key

   # Feature Flags
   ENABLE_DISCORD_PUBLISHING=true
   ENABLE_DEBATE_ANALYSIS=true
   ENABLE_FACT_CHECKING=true
   ```

3. **Install dependencies**:

   ```bash
   make install
   ```

### Docker Deployment

1. **Build and start services**:

   ```bash
   make docker-build
   make docker-up
   ```

2. **Verify deployment**:

   ```bash
   make health
   ```

### Kubernetes Deployment

1. **Apply configurations**:

   ```bash
   kubectl apply -f k8s/
   ```

2. **Check pod status**:

   ```bash
   kubectl get pods -l app=ultimate-discord-intelligence-bot
   ```

## Configuration Management

### Feature Flags

The system uses feature flags for gradual rollouts and A/B testing:

```bash
# Core Features
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true
ENABLE_SENTIMENT_ANALYSIS=true

# Performance Features
ENABLE_CACHING=true
ENABLE_OPTIMIZATION=true
ENABLE_LAZY_LOADING=false

# Integration Features
ENABLE_DISCORD_INTEGRATION=true
ENABLE_YOUTUBE_INTEGRATION=true
ENABLE_TIKTOK_INTEGRATION=true

# Crew Consolidation
ENABLE_LEGACY_CREW=false
ENABLE_CREW_MODULAR=false
ENABLE_CREW_REFACTORED=false
ENABLE_CREW_NEW=false
```

### Environment-Specific Configuration

- **Development**: Debug mode, verbose logging, test data
- **Staging**: Production-like with monitoring, limited external APIs
- **Production**: Full features, monitoring, alerting, security

## Monitoring and Observability

### Health Checks

1. **System health**:

   ```bash
   make health
   ```

2. **Metrics endpoint**:

   ```bash
   curl http://localhost:8080/metrics
   ```

3. **Discord bot status**:

   ```bash
   curl http://localhost:8080/health/discord
   ```

### Key Metrics

- **Tool Execution**: Success rate, duration, error rate
- **Memory Usage**: Vector storage, cache hit rate
- **Discord Integration**: Message processing, webhook delivery
- **Content Processing**: Pipeline throughput, quality scores

### Alerting

- **High Error Rate**: >5% tool execution failures
- **Memory Usage**: >80% vector storage capacity
- **Discord Failures**: Webhook delivery issues
- **Content Quality**: Low analysis confidence scores

## Troubleshooting

### Common Issues

#### 1. Tool Execution Failures

**Symptoms**: Tools returning StepResult.fail, high error rates

**Diagnosis**:

```bash
# Check tool compliance
python3 scripts/stepresult_compliance_check.py

# Check specific tool logs
grep "ERROR" logs/tools.log
```

**Resolution**:

- Fix StepResult compliance issues
- Check API keys and permissions
- Verify tool dependencies

#### 2. Memory Issues

**Symptoms**: High memory usage, slow vector searches

**Diagnosis**:

```bash
# Check memory usage
curl http://localhost:8080/metrics | grep memory

# Check Qdrant status
curl http://localhost:6333/collections
```

**Resolution**:

- Enable memory compaction
- Adjust cache settings
- Scale Qdrant resources

#### 3. Discord Integration Issues

**Symptoms**: Bot not responding, webhook failures

**Diagnosis**:

```bash
# Test Discord connection
python3 scripts/post_to_discord.py test

# Check bot permissions
curl http://localhost:8080/health/discord
```

**Resolution**:

- Verify bot token and permissions
- Check webhook URLs
- Review rate limiting settings

### Performance Issues

#### High Latency

1. **Check caching**:

   ```bash
   curl http://localhost:8080/metrics | grep cache
   ```

2. **Enable optimizations**:

   ```bash
   export ENABLE_CACHE_OPTIMIZATION=true
   export ENABLE_MEMORY_OPTIMIZATION=true
   ```

3. **Scale resources**:
   - Increase CPU/memory allocation
   - Enable parallel processing
   - Optimize database queries

#### Memory Leaks

1. **Monitor memory usage**:

   ```bash
   watch -n 5 'curl -s http://localhost:8080/metrics | grep memory'
   ```

2. **Enable memory management**:

   ```bash
   export ENABLE_MEMORY_COMPACTION=true
   export ENABLE_MEMORY_TTL=true
   ```

3. **Restart services**:

   ```bash
   make restart
   ```

## Maintenance

### Regular Tasks

#### Daily

- Monitor system health and metrics
- Check error rates and alerts
- Review Discord bot activity

#### Weekly

- Update dependencies
- Review performance metrics
- Clean up old data and logs

#### Monthly

- Security updates and patches
- Performance optimization review
- Capacity planning assessment

### Backup and Recovery

#### Data Backup

1. **Vector database backup**:

   ```bash
   # Qdrant snapshot
   curl -X POST http://localhost:6333/snapshots
   ```

2. **Configuration backup**:

   ```bash
   cp .env .env.backup
   cp -r config/ config.backup/
   ```

#### Recovery Procedures

1. **Restore from backup**:

   ```bash
   # Restore Qdrant
   curl -X POST http://localhost:6333/snapshots/restore

   # Restore configuration
   cp .env.backup .env
   ```

2. **Verify recovery**:

   ```bash
   make health
   make test
   ```

### Updates and Upgrades

#### Dependency Updates

1. **Check for updates**:

   ```bash
   pip list --outdated
   ```

2. **Update dependencies**:

   ```bash
   make update-deps
   ```

3. **Test after updates**:

   ```bash
   make test
   make health
   ```

#### Feature Rollouts

1. **Enable feature flags**:

   ```bash
   export ENABLE_NEW_FEATURE=true
   ```

2. **Monitor rollout**:

   ```bash
   # Check metrics
   curl http://localhost:8080/metrics | grep new_feature

   # Check logs
   tail -f logs/application.log | grep new_feature
   ```

3. **Rollback if needed**:

   ```bash
   export ENABLE_NEW_FEATURE=false
   make restart
   ```

## Security

### Access Control

- **API Keys**: Rotate regularly, use environment variables
- **Discord Tokens**: Secure storage, minimal permissions
- **Database Access**: Network isolation, authentication

### Data Protection

- **PII Filtering**: Automatic detection and filtering
- **Content Moderation**: Automated content analysis
- **Data Retention**: Configurable retention policies

### Monitoring

- **Security Alerts**: Failed authentication attempts
- **Data Leaks**: PII detection in logs
- **Access Patterns**: Unusual access patterns

## Performance Optimization

### Caching Strategy

1. **Enable caching**:

   ```bash
   export ENABLE_CACHING=true
   export ENABLE_SMART_CACHING=true
   ```

2. **Monitor cache performance**:

   ```bash
   curl http://localhost:8080/metrics | grep cache
   ```

### Memory Optimization

1. **Enable memory features**:

   ```bash
   export ENABLE_MEMORY_OPTIMIZATION=true
   export ENABLE_MEMORY_POOLING=true
   ```

2. **Monitor memory usage**:

   ```bash
   curl http://localhost:8080/metrics | grep memory
   ```

### Database Optimization

1. **Vector database tuning**:
   - Adjust collection parameters
   - Optimize index settings
   - Monitor query performance

2. **Cache optimization**:
   - Tune cache sizes
   - Adjust TTL settings
   - Monitor hit rates

## Troubleshooting

### Common Issues

#### 1. StepResult Compliance Issues

**Problem**: Tools not returning StepResult objects
**Symptoms**:

- Compliance checker shows low compliance rate
- Tools returning raw dictionaries instead of StepResult

**Solution**:

```python
# Before (incorrect)
def run(self, data: str) -> dict:
    return {"status": "success", "data": result}

# After (correct)
def run(self, data: str) -> StepResult:
    return StepResult.ok(data=result)
```

**Prevention**: Use the StepResult migration guide and compliance checker

#### 2. Crew Consolidation Issues

**Problem**: Wrong crew implementation being used
**Symptoms**:

- Unexpected behavior in crew execution
- Feature flags not working

**Solution**:

```bash
# Check current crew flags
env | grep ENABLE_CREW

# Reset to canonical crew
unset ENABLE_CREW_NEW
unset ENABLE_CREW_MODULAR
unset ENABLE_CREW_REFACTORED
unset ENABLE_LEGACY_CREW
```

**Prevention**: Use only one crew flag at a time

#### 3. Discord Publishing Issues

**Problem**: Messages not appearing in Discord
**Symptoms**:

- No error messages but no Discord posts
- Publishing disabled warnings

**Solution**:

```bash
# Check if publishing is enabled
echo $ENABLE_DISCORD_PUBLISHING

# Enable publishing
export ENABLE_DISCORD_PUBLISHING=true

# Check webhook URL
echo $DISCORD_WEBHOOK_URL
```

**Prevention**: Verify environment variables and webhook URLs

#### 4. Observability Issues

**Problem**: Metrics not being collected
**Symptoms**:

- Empty metrics dashboard
- Missing tool execution metrics

**Solution**:

```python
# Check metrics collection
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
metrics = get_metrics()

# Test counter
metrics.counter("test_total", labels={"test": "true"}).inc()
```

**Prevention**: Ensure metrics are properly initialized

#### 5. Memory/Vector Store Issues

**Problem**: Vector search not working
**Symptoms**:

- Empty search results
- Connection errors to Qdrant

**Solution**:

```bash
# Check Qdrant connection
curl http://localhost:6333/collections

# Restart Qdrant
docker-compose restart qdrant
```

**Prevention**: Monitor Qdrant health and connection

### Debug Procedures

#### 1. System Health Check

```bash
# Check all services
make health

# Check specific components
python3 scripts/test_observability.py
```

#### 2. Log Analysis

```bash
# Check application logs
docker-compose logs -f app

# Check specific service logs
docker-compose logs -f qdrant
docker-compose logs -f redis
```

#### 3. Performance Analysis

```bash
# Check system resources
docker stats

# Check application metrics
curl http://localhost:8000/metrics
```

### Error Recovery

#### 1. Service Restart

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart app
```

#### 2. Data Recovery

```bash
# Backup vector database
docker-compose exec qdrant qdrant-backup create /backup/backup.tar

# Restore from backup
docker-compose exec qdrant qdrant-backup restore /backup/backup.tar
```

#### 3. Configuration Reset

```bash
# Reset to default configuration
cp .env.example .env
docker-compose down
docker-compose up -d
```

## Emergency Procedures

### System Outage

1. **Immediate response**:
   - Check system status
   - Review recent changes
   - Notify stakeholders

2. **Recovery steps**:
   - Restart services
   - Restore from backup
   - Verify functionality

3. **Post-incident**:
   - Root cause analysis
   - Update procedures
   - Implement improvements

### Data Loss

1. **Assessment**:
   - Identify affected data
   - Check backup availability
   - Estimate recovery time

2. **Recovery**:
   - Restore from backup
   - Rebuild missing data
   - Verify data integrity

3. **Prevention**:
   - Improve backup procedures
   - Enhance monitoring
   - Update documentation

## Contact Information

### Support Channels

- **Technical Issues**: Create GitHub issue
- **Security Issues**: <security@company.com>
- **General Questions**: <support@company.com>

### Escalation Procedures

1. **Level 1**: Development team
2. **Level 2**: Senior engineers
3. **Level 3**: Architecture team
4. **Level 4**: Management

## Appendix

### Useful Commands

```bash
# System health
make health
make metrics
make logs

# Testing
make test
make test-integration
make test-e2e

# Deployment
make docker-build
make docker-up
make k8s-deploy

# Maintenance
make clean
make update-deps
make backup
```

### Configuration Files

- **Environment**: `.env`
- **Feature Flags**: `config/feature_flags.py`
- **Docker**: `docker-compose.yml`
- **Kubernetes**: `k8s/`
- **Monitoring**: `grafana/`, `prometheus/`

### Log Locations

- **Application**: `logs/application.log`
- **Tools**: `logs/tools.log`
- **Discord**: `logs/discord.log`
- **Metrics**: `logs/metrics.log`
