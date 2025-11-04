# Docker Setup for WSL2 Environment

## Overview

This project runs in WSL2 (Windows Subsystem for Linux) but Docker containers must be built and run on the **Windows host** using Docker Desktop. This document explains how to set up and use Docker with this configuration.

> **Note**: If you need to install Docker on a different drive (like F:) for more storage space, see [Docker F Drive Setup](./DOCKER_F_DRIVE_SETUP.md).

## Prerequisites

1. **Docker Desktop for Windows** installed on your Windows host
1. **WSL2 integration enabled** in Docker Desktop settings
1. Project files accessible from both WSL2 and Windows

## Setup Steps

### 1. Install Docker Desktop on Windows

Download and install from: <https://docs.docker.com/desktop/install/windows-install/>

### 2. Enable WSL2 Integration

1. Open Docker Desktop
1. Go to **Settings** → **Resources** → **WSL Integration**
1. Enable integration with your WSL2 distro (likely "Ubuntu" or your custom distro name)
1. Click **Apply & Restart**

### 3. Verify Docker Access from WSL2

Once integration is enabled, you should be able to run Docker commands from WSL2:

```bash
# Check Docker is accessible
docker --version
docker compose version

# Test with hello-world
docker run hello-world
```

If you see "The command 'docker' could not be found" error, the integration isn't enabled yet.

## Building and Running Containers

### Build All Services

```bash
cd /home/crew
docker compose -f config/docker/docker-compose.yml build
```

This builds:

- **ultimate-discord-intelligence-bot**: Main Discord bot (FastAPI + bot logic)
- **ultimate-discord-intelligence-arq-worker**: Background task worker
- Supporting infrastructure: Qdrant, Redis, PostgreSQL, Neo4j, Prometheus, Grafana, Jaeger, Nginx

### Start All Services

```bash
# Start in detached mode
docker compose -f config/docker/docker-compose.yml up -d

# View logs
docker compose -f config/docker/docker-compose.yml logs -f

# Check service health
curl http://localhost:8000/health
```

### Individual Service Management

```bash
# Start specific service
docker compose -f config/docker/docker-compose.yml up -d bot

# View logs for specific service
docker logs ultimate-discord-intelligence-bot
docker logs ultimate-discord-intelligence-arq-worker

# Restart service
docker compose -f config/docker/docker-compose.yml restart bot

# Stop all services
docker compose -f config/docker/docker-compose.yml down
```

## Environment Configuration

Before building, ensure your `.env` file is configured:

```bash
# Required for Docker deployment
cp env.example .env

# Edit .env and set:
# - DISCORD_BOT_TOKEN=your_token
# - OPENAI_API_KEY or OPENROUTER_API_KEY
# - NEO4J_PASSWORD=defaultpassword (or custom)
# - GRAFANA_PASSWORD=admin (or custom)
```

## Port Mappings

The stack exposes the following ports on your Windows host:

- **8000**: FastAPI server (health, metrics, API)
- **6333**: Qdrant vector database (HTTP)
- **6334**: Qdrant (gRPC)
- **6379**: Redis
- **5432**: PostgreSQL
- **7474**: Neo4j browser
- **7687**: Neo4j bolt
- **9090**: Prometheus
- **3000**: Grafana
- **16686**: Jaeger UI
- **80**: Nginx reverse proxy

Access from WSL2 or Windows browser: `http://localhost:<port>`

## Troubleshooting

### "docker: command not found" in WSL2

**Cause**: Docker Desktop WSL2 integration not enabled

**Solution**:

1. Open Docker Desktop on Windows
1. Settings → Resources → WSL Integration
1. Enable integration for your distro
1. Restart Docker Desktop

### Containers fail to start

**Check logs**:

```bash
docker compose -f config/docker/docker-compose.yml logs bot
docker compose -f config/docker/docker-compose.yml logs arq-worker
```

**Common issues**:

- Missing environment variables in `.env`
- Port conflicts (another service using 8000, 6379, etc.)
- Insufficient Docker resources (increase RAM/CPU in Docker Desktop settings)

### Health endpoint returns connection refused

**Verify container is running**:

```bash
docker ps | grep ultimate-discord-intelligence-bot
```

**Check container logs**:

```bash
docker logs ultimate-discord-intelligence-bot
```

**Restart service**:

```bash
docker compose -f config/docker/docker-compose.yml restart bot
```

## Development Workflow

### Typical Development Cycle

1. **Code changes in WSL2**: Edit files in `/home/crew/src/`
1. **Rebuild container**: `docker compose -f config/docker/docker-compose.yml build bot`
1. **Restart service**: `docker compose -f config/docker/docker-compose.yml up -d bot`
1. **Check logs**: `docker compose -f config/docker/docker-compose.yml logs -f bot`
1. **Test endpoint**: `curl http://localhost:8000/health`

### Hot Reload for Development

For faster iteration, you can mount source code as a volume:

```yaml
# Add to docker-compose.yml bot service:
volumes:
  - /home/crew/src:/app/src:ro
```

Then changes are reflected without rebuilding (restart required).

### Local vs Docker Testing

**Local (without Docker)**:

```bash
# Faster for quick iteration
source .venv/bin/activate  # Note: use .venv, not venv
python -m app.main run
```

**Docker (production-like)**:

```bash
# More accurate for deployment testing
docker compose -f config/docker/docker-compose.yml up bot
```

## Performance Considerations

- **WSL2 file access**: Docker Desktop accesses WSL2 filesystem, which can be slower than native Windows paths
- **Resource limits**: Configure Docker Desktop memory/CPU limits (Settings → Resources)
- **Build cache**: Docker caches layers; use `--no-cache` flag to force fresh build if needed

## Production Deployment

For production deployment outside WSL2:

1. **Build on target platform** (Linux server, cloud VM)
1. **Use production Dockerfile stage**:

   ```bash
   docker build -f config/docker/Dockerfile --target production -t bot:prod .
   ```

1. **Configure secrets** via environment variables or secrets manager
1. **Use orchestration** (Kubernetes, Docker Swarm, ECS) for resilience

## Related Documentation

- [Docker Desktop WSL2 Backend](https://docs.docker.com/desktop/wsl/)
- [Project README](../README.md)
- [Quick Start Guide](../QUICK_START_GUIDE.md)
- [Environment Setup](../env.example)

## Quick Reference

```bash
# Build
docker compose -f config/docker/docker-compose.yml build

# Start
docker compose -f config/docker/docker-compose.yml up -d

# Logs
docker compose -f config/docker/docker-compose.yml logs -f

# Stop
docker compose -f config/docker/docker-compose.yml down

# Clean rebuild
docker compose -f config/docker/docker-compose.yml down -v
docker compose -f config/docker/docker-compose.yml build --no-cache
docker compose -f config/docker/docker-compose.yml up -d
```
