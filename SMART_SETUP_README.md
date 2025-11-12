# Smart Setup Script - Ultimate Discord Intelligence Bot

A comprehensive, intelligent setup and service management script that combines all available service options into a single, unified system with full automation, dependency checking, and monitoring capabilities.

## Overview

The `smart-setup.sh` script provides a complete solution for setting up and managing the Ultimate Discord Intelligence Bot system. It intelligently handles:

- **System Requirements Validation**: Checks for Python, Docker, Git, and Make
- **Virtual Environment Setup**: Creates and configures Python virtual environment with uv/pip fallback
- **Configuration Wizard**: Runs the setup wizard with smart defaults for non-interactive setup
- **Infrastructure Management**: Handles Docker services and dependencies
- **Service Orchestration**: Manages all services (Discord Bot, API Server, CrewAI, MCP Server) with background process handling
- **Health Monitoring**: Comprehensive health checks and status monitoring
- **Progress Tracking**: Real-time progress bars and completion indicators
- **Interactive Menu**: 16 different options for complete system control
- **Command-Line Interface**: Direct commands for automation and scripting

## Quick Start

### Interactive Setup

```bash
./smart-setup.sh
```

This launches the interactive menu with all available options.

### Command-Line Usage

```bash
# Full system setup and start
./smart-setup.sh --setup --start-all

# Quick setup (skip some checks)
./smart-setup.sh --quick

# Start specific service
./smart-setup.sh --start-discord

# Check system status
./smart-setup.sh --status

# View logs
./smart-setup.sh --logs

# Stop all services
./smart-setup.sh --stop-all
```

## Available Options

### Interactive Menu Options (16 total)

1. **Full System Setup & Start** - Complete setup from scratch and start all services
1. **Quick Setup & Start** - Fast setup with minimal checks, start all services
1. **Setup Only** - Run full setup without starting services
1. **Start All Services** - Start Discord Bot, API Server, CrewAI, and MCP Server
1. **Start Discord Bot** - Start the basic Discord bot
1. **Start Enhanced Discord Bot** - Start Discord bot with performance optimizations
1. **Start API Server** - Start the FastAPI server
1. **Start CrewAI** - Start the CrewAI autonomous intelligence system
1. **Start MCP Server** - Start the Model Context Protocol server
1. **Start Full Stack** - Start all services with infrastructure (Docker)
1. **Custom Service Selection** - Choose which services to start
1. **Check System Status** - Show status of all services and infrastructure
1. **View Service Logs** - Display logs from running services
1. **Run Health Checks** - Execute comprehensive health diagnostics
1. **Stop All Services** - Gracefully stop all running services
1. **Exit** - Exit the menu

### Command-Line Flags

- `--setup`: Run full system setup
- `--quick`: Run quick setup (skip some validations)
- `--start-all`: Start all services
- `--start-discord`: Start basic Discord bot
- `--start-discord-enhanced`: Start enhanced Discord bot
- `--start-api`: Start API server
- `--start-crew`: Start CrewAI
- `--start-mcp`: Start MCP server
- `--start-full`: Start full stack with infrastructure
- `--status`: Show system status
- `--logs`: Show service logs
- `--health`: Run health checks
- `--stop-all`: Stop all services
- `--help`: Show help information

## Features

### Intelligent System Validation

- **Python Version Check**: Ensures Python 3.11+ is available
- **Docker Availability**: Checks for Docker daemon and required images
- **Git Repository**: Validates Git installation and repository integrity
- **Make Tool**: Confirms Make is available for build processes
- **Dependency Resolution**: Automatically installs missing system dependencies

### Smart Virtual Environment Management

- **uv Priority**: Uses uv for fast Python package management when available
- **pip Fallback**: Falls back to pip if uv is not installed
- **Environment Activation**: Automatically activates the virtual environment
- **Dependency Installation**: Installs all required Python packages

### Configuration Wizard Integration

- **Non-Interactive Mode**: Runs setup wizard with smart defaults
- **Environment File Creation**: Generates `.env` from `env.example`
- **Feature Flag Configuration**: Sets up optimal feature flags for production
- **Tenant Setup**: Configures multi-tenant environment
- **Directory Structure**: Creates all required directories

### Infrastructure Management

- **Docker Service Control**: Manages Docker containers and networks
- **Health Checks**: Validates infrastructure components are running
- **Resource Monitoring**: Tracks system resources and service health
- **Automatic Recovery**: Attempts to restart failed infrastructure components

### Advanced Service Orchestration

- **Background Process Management**: Runs services in background with PID tracking
- **Process Monitoring**: Continuously monitors service health and restarts on failure
- **Log Aggregation**: Collects and displays logs from all services
- **Graceful Shutdown**: Properly stops all services and cleans up resources

### Comprehensive Monitoring

- **Real-Time Status**: Shows current state of all services and infrastructure
- **Health Diagnostics**: Runs doctor checks and validation tests
- **Performance Metrics**: Displays system performance and resource usage
- **Error Detection**: Identifies and reports service failures and issues

### Progress Tracking & User Experience

- **Progress Bars**: Visual progress indicators for long-running operations
- **Colored Output**: Color-coded messages for different types of information
- **Timestamped Logs**: All operations are logged with timestamps
- **Error Handling**: Comprehensive error handling with helpful error messages

## Prerequisites

### System Requirements

- **Python 3.11+**: Required for the application
- **Docker**: For infrastructure services (optional but recommended)
- **Git**: For version control operations
- **Make**: For build automation
- **curl**: For downloading dependencies
- **jq**: For JSON processing (optional)

### Environment Setup

- Copy `env.example` to `.env` and configure:

  ```bash
  cp env.example .env
  # Edit .env with your configuration
  ```

## Configuration

### Environment Variables

The script respects all environment variables from `.env`:

- `DISCORD_BOT_TOKEN`: Discord bot authentication token
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY`: AI service API key
- Various feature flags for enabling/disabling components

### Feature Flags

Common feature flags that affect service behavior:

- `ENABLE_CONTENT_ROUTING`: Content analysis routing
- `ENABLE_QUALITY_FILTERING`: Quality control filters
- `ENABLE_SEMANTIC_CACHE*`: Semantic caching features
- `ENABLE_PROMETHEUS_ENDPOINT`: Metrics endpoint

## Usage Examples

### First-Time Setup

```bash
# Interactive full setup
./smart-setup.sh

# Or command-line full setup
./smart-setup.sh --setup --start-all
```

### Development Workflow

```bash
# Quick restart after code changes
./smart-setup.sh --stop-all --start-all

# Check status and logs
./smart-setup.sh --status
./smart-setup.sh --logs
```

### Production Deployment

```bash
# Full production setup with all services
./smart-setup.sh --setup --start-full

# Monitor production system
./smart-setup.sh --health --status
```

### Troubleshooting

```bash
# Run health checks
./smart-setup.sh --health

# View detailed logs
./smart-setup.sh --logs

# Stop everything and restart
./smart-setup.sh --stop-all --start-all
```

## Service Details

### Discord Bot

- **Basic Mode**: Standard Discord bot functionality
- **Enhanced Mode**: Includes performance optimizations, semantic caching, and advanced features
- **Configuration**: Requires `DISCORD_BOT_TOKEN` in `.env`

### API Server (FastAPI)

- **Endpoints**: REST API for system interaction
- **Metrics**: Prometheus metrics at `/metrics` when enabled
- **Port**: Configurable via environment variables

### CrewAI Autonomous Intelligence

- **AI Processing**: Advanced AI-driven content analysis
- **Tool Integration**: Uses various AI tools and models
- **Background Processing**: Runs as background service

### MCP Server

- **Model Context Protocol**: Standardized AI model interface
- **Tool Serving**: Provides AI tools to connected clients
- **Extensibility**: Supports custom tool development

## Monitoring & Maintenance

### Health Checks

The script provides comprehensive health monitoring:

- **System Resources**: CPU, memory, disk usage
- **Service Status**: Individual service health checks
- **Infrastructure**: Docker container and network status
- **Dependencies**: Database connections, external services

### Log Management

- **Centralized Logging**: All services log to designated locations
- **Log Rotation**: Automatic log rotation and cleanup
- **Log Analysis**: Tools for analyzing service logs

### Performance Monitoring

- **Metrics Collection**: Real-time performance metrics
- **Resource Tracking**: System resource utilization
- **Service Metrics**: Individual service performance data

## Troubleshooting

### Common Issues

**Python Version Error**

```
Error: Python 3.11+ required, found 3.10
```

Solution: Install Python 3.11+ or use a version manager like pyenv.

**Docker Not Available**

```
Error: Docker daemon not running
```

Solution: Start Docker service or install Docker if missing.

**Virtual Environment Issues**

```
Error: Failed to create virtual environment
```

Solution: Check disk space and permissions, or manually create venv.

**Service Startup Failures**

```
Error: Service failed to start
```

Solution: Check logs with `--logs`, verify configuration in `.env`.

### Debug Mode

Enable debug logging by setting:

```bash
export DEBUG=1
./smart-setup.sh --status
```

### Manual Recovery

If the script fails, you can manually run components:

```bash
# Activate environment
source .venv/bin/activate

# Run individual services
make run-discord
make run-api
make run-crew
```

## Advanced Usage

### Custom Service Configuration

The script supports custom service configurations through environment variables and feature flags. See `env.example` for all available options.

### Integration with CI/CD

The script can be used in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Setup and Test
  run: |
    ./smart-setup.sh --setup --health
    ./smart-setup.sh --start-api
    # Run tests
    make test
```

### Automated Deployments

For automated deployments, use non-interactive mode:

```bash
# Production deployment
./smart-setup.sh --setup --start-full --no-interactive
```

## Contributing

When modifying the script:

1. Test all interactive menu options
2. Validate command-line flags
3. Ensure backward compatibility
4. Update this README for new features

## Support

For issues or questions:

1. Run `./smart-setup.sh --health` to diagnose problems
2. Check logs with `./smart-setup.sh --logs`
3. Review system status with `./smart-setup.sh --status`
4. Consult the main project documentation in `README.md`

---

**Note**: This script provides a unified interface to all system components. For detailed documentation on individual services, see the main `README.md` and service-specific documentation in the `docs/` directory.
