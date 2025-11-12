# Full Auto Setup & Start Script

## Overview

The `full-auto-setup.sh` script is a **single-command solution** that automatically handles the complete setup and startup of the Ultimate Discord Intelligence Bot system. It requires **zero user interaction** - just run it and everything gets configured and started automatically.

## What It Does

This script performs a complete end-to-end setup and deployment:

### 1. System Validation

- ✅ Checks Python 3.11+ availability
- ✅ Validates Git and Make installation
- ✅ Verifies Docker availability (optional)
- ✅ Installs missing system dependencies automatically

### 2. Environment Setup

- ✅ Creates Python virtual environment (with uv preference)
- ✅ Installs all required Python packages
- ✅ Sets up proper PYTHONPATH configuration

### 3. Configuration

- ✅ Creates `.env` file from template (if missing)
- ✅ Runs configuration wizard with smart defaults
- ✅ Sets up all necessary directories and permissions

### 4. Infrastructure

- ✅ Starts Docker services (if available)
- ✅ Validates infrastructure health
- ✅ Sets up networking and dependencies

### 5. Service Deployment

- ✅ **Enhanced Discord Bot** with all performance optimizations
- ✅ **FastAPI Server** for REST API access
- ✅ **CrewAI** autonomous intelligence system
- ✅ **MCP Server** for model context protocol

### 6. Health Monitoring

- ✅ Validates all services are running
- ✅ Provides startup status and health checks
- ✅ Shows comprehensive deployment summary

## Usage

### Simple Execution

```bash
./full-auto-setup.sh
```

That's it! The script handles everything automatically with no prompts or user interaction required.

### What You'll See

```bash
🚀 Ultimate Discord Intelligence Bot - Full Auto Setup & Start
═══════════════════════════════════════════════════════════════
This script will automatically set up and run EVERYTHING
No user interaction required - just sit back and relax!

[Progress bars and status updates...]

╔═══════════════════════════════════════════════════════════╗
║ DEPLOYMENT COMPLETE                                     ║
╚═══════════════════════════════════════════════════════════╝

🚀 Ultimate Discord Intelligence Bot is now running!

Active Services:
  ✅ Discord Bot (Enhanced) - PID: 12345
  ✅ API Server - PID: 12346
  ✅ CrewAI - PID: 12347
  ✅ MCP Server - PID: 12348

Monitoring:
  📊 Status Check: ./smart-setup.sh status
  ⏱️ View Logs: ./smart-setup.sh logs
  🛡️ Health Check: ./smart-setup.sh health

Setup completed in 45 seconds
```

## Performance Optimizations Enabled

The script automatically enables all Phase 1-4 performance optimizations:

- **ENABLE_GPTCACHE**: ✅ Active
- **ENABLE_SEMANTIC_CACHE_SHADOW**: ✅ Active
- **ENABLE_GPTCACHE_ANALYSIS_SHADOW**: ✅ Active
- **ENABLE_PROMPT_COMPRESSION**: ✅ Active
- **ENABLE_GRAPH_MEMORY**: ✅ Active
- **ENABLE_HIPPORAG_MEMORY**: ✅ Active

**Expected Result**: 40-60% latency reduction through comprehensive caching, AI-driven optimization, and intelligent resource management.

## Post-Deployment

### Monitoring Your System

```bash
# Check service status
./smart-setup.sh status

# View service logs
./smart-setup.sh logs

# Run health diagnostics
./smart-setup.sh health
```

### Configuration Notes

- **Discord Token**: Configure `DISCORD_BOT_TOKEN` in `.env` for full Discord connectivity
- **API Access**: FastAPI server runs on `http://localhost:8000`
- **Metrics**: Prometheus metrics available at `/metrics` endpoint

### Log Files

- **Setup Log**: `full_auto_setup_$(date +%Y%m%d_%H%M%S).log`
- **Service Logs**: `logs/services/` directory
- **PID Files**: `logs/pids/` directory for process management

## Troubleshooting

### If Services Don't Start

1. Check the setup log for errors
2. Run `./smart-setup.sh health` for diagnostics
3. View individual service logs in `logs/services/`

### Common Issues

- **Python Version**: Ensure Python 3.11+ is available
- **Dependencies**: Check that all system requirements are met
- **Permissions**: Ensure proper file permissions for log directories

### Manual Recovery

If auto-setup fails, you can use the interactive setup:

```bash
./smart-setup.sh
```

## Architecture

The script follows this deployment sequence:

1. **Validation Phase**: System requirements and dependencies
2. **Setup Phase**: Virtual environment and package installation
3. **Configuration Phase**: Environment and wizard setup
4. **Infrastructure Phase**: Docker services and networking
5. **Deployment Phase**: Start all application services
6. **Validation Phase**: Health checks and status verification

## Security & Best Practices

- ✅ Uses virtual environments for isolation
- ✅ Sets proper PYTHONPATH for module resolution
- ✅ Creates dedicated log directories with appropriate permissions
- ✅ Validates all critical dependencies before proceeding
- ✅ Provides comprehensive error handling and recovery

## Performance Expectations

- **Setup Time**: 30-60 seconds (depending on system and network)
- **Memory Usage**: ~500MB-1GB for full system
- **CPU Usage**: Moderate during startup, optimized during operation
- **Latency Reduction**: 40-60% improvement through optimizations

---

**🎉 One Command. Everything Running. Zero Hassle.**

Just run `./full-auto-setup.sh` and enjoy your fully configured, high-performance Discord Intelligence Bot system!
