# Deployment Guide

This directory contains comprehensive deployment documentation for the Ultimate Discord Intelligence Bot.

## Quick Start

### Prerequisites

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
```

## Deployment Options

### Option 1: Development Setup

- **Target**: Local development
- **Services**: Minimal (Discord Bot + Qdrant)
- **Configuration**: Development environment variables
- **Guide**: See [Development Setup](development-setup.md)

### Option 2: Staging Deployment

- **Target**: Testing and validation
- **Services**: Full stack with monitoring
- **Configuration**: Staging environment variables
- **Guide**: See [Staging Deployment](staging-deployment.md)

### Option 3: Production Deployment

- **Target**: Production environment
- **Services**: Full stack with high availability
- **Configuration**: Production environment variables
- **Guide**: See [Production Deployment](production-deployment.md)

### Option 4: Full Stack Deployment

- **Target**: Complete ecosystem
- **Services**: All services with monitoring and alerting
- **Configuration**: All features enabled
- **Guide**: See [Full Stack Deployment](full-stack-deployment.md)

## Infrastructure Services

### Core Services

- **PostgreSQL** (port 5432) - Relational database
- **Redis** (port 6379) - Cache and message broker
- **Qdrant** (ports 6333, 6334) - Vector database
- **MinIO** (ports 9000, 9001) - Object storage

### Monitoring Services

- **Prometheus** (port 9090) - Metrics collection
- **Grafana** (port 3000) - Visualization dashboards
- **Alertmanager** (port 9093) - Alert management

### Application Services

- **API Server** (port 8080) - FastAPI REST API
- **Discord Bot** - Multi-platform intelligence bot

## Configuration

### Environment Variables

See [Environment Configuration](../configuration.md) for complete list of environment variables.

### Feature Flags

See [Feature Flags](../feature_flags.md) for available feature toggles.

### Tenant Configuration

See [Tenancy Guide](../tenancy.md) for multi-tenant setup.

## Monitoring

### Health Checks

- **API Health**: `GET /health`
- **Discord Bot**: `!status` command
- **Services**: Docker health checks

### Metrics

- **Application Metrics**: Prometheus endpoints
- **System Metrics**: Grafana dashboards
- **Custom Metrics**: Application-specific metrics

### Alerting

- **Critical Alerts**: Discord notifications
- **Warning Alerts**: Email notifications
- **Info Alerts**: Log entries

## Troubleshooting

### Common Issues

1. **Service Startup Failures**: Check environment variables
2. **API Connection Issues**: Verify network connectivity
3. **Discord Bot Issues**: Check bot token and permissions
4. **Database Issues**: Verify connection strings

### Logs

- **Application Logs**: `logs/application.log`
- **Discord Bot Logs**: `logs/bot.log`
- **Service Logs**: Docker logs

### Support

- **Documentation**: This guide and linked resources
- **Issues**: GitHub issues for bug reports
- **Discussions**: GitHub discussions for questions

## Security

### Best Practices

- Use environment variables for secrets
- Enable HTTPS in production
- Regular security updates
- Monitor access logs

### Network Security

- Firewall configuration
- VPN access for sensitive environments
- API rate limiting
- Input validation

## Performance

### Optimization

- Resource allocation tuning
- Cache configuration
- Database optimization
- Network optimization

### Scaling

- Horizontal scaling strategies
- Load balancing
- Database sharding
- Service mesh

---

**Last Updated**: 2025-01-05
**Version**: 1.0
**Maintainer**: Ultimate Discord Intelligence Bot Team
