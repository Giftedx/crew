# Getting Started Guide

This guide will help you get up and running with the Ultimate Discord Intelligence Bot system quickly and efficiently.

## Quick Start

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Git** for cloning the repository
- **Docker** (optional, for containerized deployment)
- **API Keys** for external services (OpenRouter, Serper, Anthropic)

### 1. Installation

#### Clone the Repository

```bash
git clone https://github.com/your-org/ultimate-discord-intelligence-bot.git
cd ultimate-discord-intelligence-bot
```

#### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.lock
```

### 2. Configuration

#### Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
SERPER_API_KEY=your_serper_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./ultimate_discord_intelligence_bot.db

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

#### API Key Setup

1. **OpenRouter API Key**
   - Visit [OpenRouter](https://openrouter.ai/)
   - Create an account and generate an API key
   - Add to your `.env` file

2. **Serper API Key**
   - Visit [Serper](https://serper.dev/)
   - Sign up and get your API key
   - Add to your `.env` file

3. **Anthropic API Key**
   - Visit [Anthropic](https://www.anthropic.com/)
   - Create an account and generate an API key
   - Add to your `.env` file

### 3. Database Setup

#### Initialize Database

```bash
python -m ultimate_discord_intelligence_bot.db.init
```

#### Run Migrations

```bash
python -m ultimate_discord_intelligence_bot.db.migrate
```

### 4. Start the System

#### Start Qdrant (Vector Database)

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or install locally
# Follow Qdrant installation guide
```

#### Start the Application

```bash
python -m ultimate_discord_intelligence_bot.main
```

The system should now be running at `http://localhost:8000`

### 5. Verify Installation

#### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "qdrant": "healthy",
    "external_apis": "healthy"
  }
}
```

#### Test Basic Functionality

```bash
# Test content analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test message for analysis",
    "tenant": "test_tenant",
    "workspace": "test_workspace"
  }'
```

## Docker Quick Start

### Using Docker Compose

1. **Clone and navigate to the repository**

   ```bash
   git clone https://github.com/your-org/ultimate-discord-intelligence-bot.git
   cd ultimate-discord-intelligence-bot
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start all services**

   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**

   ```bash
   curl http://localhost:8000/health
   ```

### Docker Compose Services

The Docker Compose setup includes:

- **app**: Main application
- **db**: PostgreSQL database
- **qdrant**: Vector database
- **redis**: Cache and message queue
- **nginx**: Reverse proxy (production)

## First Steps

### 1. Understanding the System

The Ultimate Discord Intelligence Bot is built around several key concepts:

#### Agents

- **Mission Orchestrator**: Coordinates overall operations
- **Acquisition Specialist**: Handles content acquisition
- **Quality Assurance Specialist**: Ensures content quality
- **Performance Optimization Engineer**: Optimizes system performance

#### Tools

- **Content Analysis Tools**: Analyze text for bias, fallacies, sentiment
- **Media Processing Tools**: Download and transcribe content
- **Search & Retrieval Tools**: Semantic search and fact-checking
- **Discord Integration Tools**: Post results to Discord

#### Services

- **Memory Service**: Persistent storage and retrieval
- **Prompt Engine**: Generate and optimize prompts
- **OpenRouter Service**: LLM integration

### 2. Basic Usage

#### Analyze Content

```python
from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

# Create crew instance
crew = UltimateDiscordIntelligenceBotCrew()

# Analyze content
inputs = {
    "url": "https://example.com/video",
    "tenant": "your_tenant",
    "workspace": "your_workspace"
}

result = crew.crew().kickoff(inputs=inputs)
print(result)
```

#### Use Individual Tools

```python
from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool

# Create tool instance
tool = LogicalFallacyTool()

# Analyze text for logical fallacies
result = tool._run("Everyone knows this is true, so you must agree.")
print(result.data)
```

### 3. Discord Integration

#### Setup Discord Bot

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token

2. **Configure Bot Token**

   ```bash
   # Add to .env file
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   ```

3. **Invite Bot to Server**
   - Go to "OAuth2" > "URL Generator"
   - Select "bot" scope
   - Select required permissions
   - Use generated URL to invite bot

#### Test Discord Commands

```bash
# In Discord, use the bot commands:
!analyze https://youtube.com/watch?v=example
!fact-check "The Earth is flat"
!sentiment "I love this new feature!"
```

## Configuration Guide

### Environment Variables

#### Core Configuration

```bash
# API Keys (Required)
OPENROUTER_API_KEY=your_key
SERPER_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Database
DATABASE_URL=sqlite:///./app.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Vector Database
QDRANT_URL=http://localhost:6333

# Discord Integration
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_WEBHOOK_URL=your_webhook_url
```

#### Feature Flags

```bash
# Enable/disable features
ENABLE_UNIFIED_KNOWLEDGE=true
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_BIAS_DETECTION=true

# Performance features
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=true
ENABLE_RETRY_LOGIC=true
```

#### System Configuration

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json, text

# Performance
CACHE_TTL_SECONDS=3600
MAX_RETRIES=5
RETRY_DELAY_SECONDS=2
REQUEST_TIMEOUT=30

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Configuration Files

#### Agent Configuration

Edit `src/ultimate_discord_intelligence_bot/config/agents.yaml`:

```yaml
mission_orchestrator:
  role: "Mission Orchestrator"
  goal: "Coordinate and oversee intelligence operations"
  backstory: "Experienced intelligence coordinator..."
  tools:
    - MissionOrchestratorTool
    - SystemStatusTool
    - TimelineTool
```

#### Task Configuration

Edit `src/ultimate_discord_intelligence_bot/config/tasks.yaml`:

```yaml
content_analysis_task:
  description: "Analyze content for bias, fallacies, and sentiment"
  expected_output: "Comprehensive analysis report"
  agent: "mission_orchestrator"
  tools:
    - LogicalFallacyTool
    - SentimentTool
    - BiasDetectionTool
```

## Development Setup

### Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with coverage
pytest --cov=ultimate_discord_intelligence_bot
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make type

# Run all quality gates
make quality
```

### Adding New Tools

1. **Create Tool File**

   ```bash
   touch src/ultimate_discord_intelligence_bot/tools/my_new_tool.py
   ```

2. **Implement Tool Class**

   ```python
   from ultimate_discord_intelligence_bot.tools._base import BaseTool
   from ultimate_discord_intelligence_bot.step_result import StepResult

   class MyNewTool(BaseTool):
       def _run(self, input_data: str) -> StepResult:
           try:
               # Tool logic here
               result = process_data(input_data)
               return StepResult.ok(data=result)
           except Exception as e:
               return StepResult.fail(str(e))
   ```

3. **Register Tool**

   ```python
   # Add to src/ultimate_discord_intelligence_bot/tools/__init__.py
   from .my_new_tool import MyNewTool

   __all__ = [
       # ... existing tools
       "MyNewTool",
   ]
   ```

4. **Add to Agent**

   ```python
   # Add to crew.py agent definition
   tools=[
       # ... existing tools
       wrap_tool_for_crewai(MyNewTool()),
   ]
   ```

5. **Write Tests**

   ```python
   # Create test file
   touch tests/tools/test_my_new_tool.py
   ```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError` when importing tools

**Solution**:

```bash
# Ensure you're in the correct directory
cd ultimate-discord-intelligence-bot

# Activate virtual environment
source venv/bin/activate

# Install in development mode
pip install -e .
```

#### 2. Database Connection Issues

**Problem**: Cannot connect to database

**Solution**:

```bash
# Check database URL
echo $DATABASE_URL

# Test connection
python -c "from ultimate_discord_intelligence_bot.db import get_engine; print(get_engine())"

# Initialize database
python -m ultimate_discord_intelligence_bot.db.init
```

#### 3. API Key Issues

**Problem**: API requests failing with authentication errors

**Solution**:

```bash
# Check environment variables
env | grep API_KEY

# Test API connectivity
python -c "from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService; print(OpenRouterService().get_available_models())"
```

#### 4. Qdrant Connection Issues

**Problem**: Cannot connect to Qdrant

**Solution**:

```bash
# Check Qdrant status
curl http://localhost:6333/health

# Start Qdrant if not running
docker run -p 6333:6333 qdrant/qdrant
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
python -m ultimate_discord_intelligence_bot.main
```

### Log Files

Check log files for detailed error information:

```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log

# Debug logs
tail -f logs/debug.log
```

## Next Steps

### 1. Explore the System

- **Read the documentation**: Check out the [Tools Reference](tools_reference.md) and [Agents Reference](agents_reference.md)
- **Try different tools**: Experiment with various analysis tools
- **Test Discord integration**: Set up and test Discord bot commands

### 2. Customize for Your Use Case

- **Configure agents**: Modify agent roles and goals in `config/agents.yaml`
- **Add custom tools**: Create tools specific to your needs
- **Adjust analysis parameters**: Tune analysis thresholds and parameters

### 3. Scale for Production

- **Set up monitoring**: Configure Prometheus and Grafana
- **Implement backup**: Set up database and data backups
- **Configure security**: Implement proper authentication and authorization
- **Optimize performance**: Tune system parameters for your workload

### 4. Contribute

- **Report issues**: Use GitHub issues to report bugs
- **Suggest features**: Propose new features and improvements
- **Submit pull requests**: Contribute code improvements
- **Improve documentation**: Help improve the documentation

## Support

### Getting Help

- **Documentation**: Check the comprehensive documentation in the `docs/` directory
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Join community discussions
- **Email**: Contact the development team

### Community

- **GitHub**: [Repository](https://github.com/your-org/ultimate-discord-intelligence-bot)
- **Discord**: Join our Discord server for community support
- **Documentation**: [Full Documentation](https://docs.your-domain.com)

### Professional Support

For enterprise support and custom development:

- **Email**: <enterprise@your-domain.com>
- **Website**: <https://your-domain.com/enterprise>
- **Consulting**: Custom implementation and training services
