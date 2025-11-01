# Ultimate Discord Intelligence Bot

[![CI Pipeline](https://github.com/your-org/ultimate-discord-intelligence-bot/workflows/CI%20Pipeline/badge.svg)](https://github.com/your-org/ultimate-discord-intelligence-bot/actions)
[![Test Coverage](https://codecov.io/gh/your-org/ultimate-discord-intelligence-bot/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/ultimate-discord-intelligence-bot)
[![MyPy](https://img.shields.io/badge/MyPy-58%20import%20stubs-yellow "Missing type stubs for optional dependencies (crewai, httpx, torch, scipy) - not code errors")](https://github.com/your-org/ultimate-discord-intelligence-bot)

A comprehensive, production-ready Discord bot system powered by CrewAI agents for autonomous content analysis, fact-checking, and intelligence gathering across multiple platforms.

## 🚀 Overview

The Ultimate Discord Intelligence Bot is a sophisticated multi-agent system that provides:

- **Autonomous Content Analysis**: AI-powered analysis of videos, articles, and social media content
- **Fact-Checking & Verification**: Advanced claim verification and truth assessment
- **Multi-Platform Intelligence**: Comprehensive monitoring across YouTube, TikTok, Twitter, Reddit, and more
- **Real-Time Processing**: Live stream analysis and real-time content monitoring
- **Advanced Memory Systems**: Vector storage, graph databases, and traditional storage integration
- **Quality Assurance**: Comprehensive content quality assessment and validation
- **Trajectory Evaluation & Feedback**: LangSmith-powered scoring with reinforcement learning feedback loops
- **Performance Optimization**: Intelligent caching, model routing, and system optimization
- **OpenAI Integration**: Advanced AI capabilities including structured outputs, function calling, streaming, voice, vision, and multimodal analysis

## 🏗️ Architecture

### Core Components

- **CrewAI Framework**: Orchestrates 20+ specialized agents
- **110+ Tools**: Comprehensive tool ecosystem for all operations
- **Multi-Tenant Support**: Complete tenant isolation and workspace management
- **Advanced Memory**: Vector stores, graph databases, and traditional storage
- **Performance Optimization**: Intelligent caching and model routing
- **Quality Assurance**: Comprehensive validation and consistency checking
- **Observability Pipeline**: Langfuse tracing, Prometheus metrics, and StepResult instrumentation

### Agent Specialists

1. **Mission Orchestrator**: End-to-end mission coordination
2. **Executive Supervisor**: Strategic oversight and quality control
3. **Acquisition Specialist**: Content acquisition and ingestion
4. **Analysis Specialist**: Content analysis and insights
5. **Verification Specialist**: Fact-checking and claim verification
6. **Quality Assurance Specialist**: Content quality and validation
7. **Performance Optimization Engineer**: System performance optimization
8. **Enhanced MCP Integration Specialist**: Advanced MCP client management
9. **Next-Gen Cache & Memory Architect**: Advanced memory systems
10. **Content Production Manager**: Smart content creation
11. **Enhanced Social Media Archivist**: Advanced social media management
12. **Advanced Verification Specialist**: Enhanced claim verification
13. **Reinforcement Learning Optimization Specialist**: RL-based optimization
14. **Compliance & Regulatory Officer**: Policy and regulatory compliance

## 🤖 OpenAI Integration

The bot includes comprehensive OpenAI integration with advanced AI capabilities:

### Core Features

- **Structured Outputs**: Generate validated, structured responses using JSON schemas
- **Function Calling**: Enable AI models to call custom functions during analysis
- **Streaming**: Real-time streaming of AI responses for better user experience
- **Voice Processing**: Convert between text and speech using OpenAI's voice models
- **Vision Analysis**: Analyze images and visual content with advanced vision models
- **Multimodal Analysis**: Process content across multiple modalities (text, images, audio)

### Services

- **OpenAIStructuredOutputsService**: Generate structured, validated responses
- **OpenAIFunctionCallingService**: Enable function calling capabilities
- **OpenAIStreamingService**: Stream responses in real-time
- **OpenAIVoiceService**: Text-to-speech and speech-to-text conversion
- **OpenAIVisionService**: Image analysis and visual content processing
- **MultimodalAnalysisService**: Cross-modal content analysis
- **OpenAIIntegrationService**: Main service combining all capabilities
- **OpenAICostMonitoringService**: Track API usage and costs

### Discord Commands

- `!openai-health` - Check OpenAI service health
- `!openai-analyze-structured <content>` - Perform structured analysis
- `!openai-analyze-multimodal <prompt>` - Analyze multimodal content
- `!openai-voice-command` - Process voice commands

### CrewAI Integration

The OpenAI capabilities are available as CrewAI tools:

- **OpenAIEnhancedAnalysisTool**: Enhanced analysis with OpenAI capabilities
- Integrated with analysis agents for advanced content processing
- Supports structured outputs, function calling, and multimodal analysis

For detailed documentation, see [OpenAI Integration Features](docs/openai_integration_features.md).

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Discord Bot Token
- OpenAI/OpenRouter API Key
- Qdrant Vector Database

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ultimate-discord-intelligence-bot
   ```

2. **Set up environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.lock
   ```

4. **Start services**

   ```bash
   docker-compose up -d
   ```

5. **Run the bot**

   ```bash
   python -m ultimate_discord_intelligence_bot.main
   ```

## ⚙️ Configuration

### Environment Variables

#### Core Services

```bash
# Discord Bot
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_PRIVATE_WEBHOOK=your_private_webhook_url

# LLM Services
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key
```

#### LLM Provider Routing (new)

Configure the provider-agnostic router that selects the best model per request.

```bash
# Comma-separated provider allowlist used to build routing candidates
# Examples: openai,anthropic,google,openrouter,groq,together,cohere,mistral,fireworks,perplexity,xai,deepseek,azure_openai,bedrock
LLM_PROVIDER_ALLOWLIST=openai,anthropic,google,openrouter

# Router policy: quality_first | cost | latency
ROUTER_POLICY=quality_first

# Comma-separated task names that should force quality-first routing
QUALITY_FIRST_TASKS=analysis,reasoning,coding
```

These values are also available at runtime via `core.secure_config.get_config()`
as `llm_provider_allowlist` (parsed list) and `router_policy`.

#### Feature Flags

```bash
# Core Features
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true
ENABLE_MULTI_PLATFORM_MONITORING=true

# Advanced Features
ENABLE_UNIFIED_KNOWLEDGE=true
ENABLE_UNIFIED_METRICS=true
ENABLE_UNIFIED_ORCHESTRATION=true
ENABLE_UNIFIED_ROUTER=true

# Performance Features
ENABLE_CACHE_OPTIMIZATION=true
ENABLE_MODEL_ROUTING=true
ENABLE_PERFORMANCE_OPTIMIZATION=true

# OpenAI Integration Features
ENABLE_OPENAI_STRUCTURED_OUTPUTS=true
ENABLE_OPENAI_STREAMING=true
ENABLE_OPENAI_VOICE=false
ENABLE_OPENAI_VISION=false
ENABLE_OPENAI_MULTIMODAL=false
ENABLE_OPENAI_FUNCTION_CALLING=true
ENABLE_OPENAI_FALLBACK=true

# Evaluation & Observability
ENABLE_TRAJECTORY_EVALUATION=1  # Set to 1 to enable runtime scoring
ENABLE_TRAJECTORY_FEEDBACK_LOOP=0  # Set to 1 to push scores into RL router
RL_FEEDBACK_BATCH_SIZE=25  # Optional: number of feedback items processed per tick
RL_FEEDBACK_LOOP_INTERVAL_SECONDS=15  # Optional: delay (seconds) between feedback loop runs
ENABLE_LANGSMITH_EVAL=false
ENABLE_LANGFUSE_EXPORT=false
```

#### Performance Settings

```bash
# CrewAI Configuration
CREW_MAX_RPM=10
CREW_EMBEDDER_PROVIDER=openai

# Cache Settings
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10
```

## 🎯 Usage

### Discord Commands

#### Basic Commands

- `!analyze <url>` - Analyze content from any supported platform
- `!factcheck <claim>` - Fact-check a specific claim
- `!monitor <creator>` - Start monitoring a creator
- `!status` - Get system status and metrics

#### Advanced Commands

- `!deep_analysis <url>` - Comprehensive content analysis
- `!verify_claims <url>` - Extract and verify all claims
- `!trend_analysis <topic>` - Analyze trends for a topic
- `!quality_assess <content>` - Assess content quality

### API Usage

#### Content Analysis

```python
from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

crew = UltimateDiscordIntelligenceBotCrew()
result = crew.crew().kickoff(inputs={"url": "https://youtube.com/watch?v=example"})
```

#### Fact-Checking

```python
result = crew.crew().kickoff(inputs={
    "claim": "The Earth is flat",
    "context": "Scientific discussion"
})
```

## 📊 Monitoring & Observability

### Langfuse Tracing

- Feature-gated exporter capturing traces and spans for every pipeline step via `LangfuseService`
- Configure with `ENABLE_LANGFUSE_EXPORT`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and optional `LANGFUSE_BASE_URL`
- StepResult-aware sanitization ensures payload safety and tenant metadata tagging
- Validate instrumentation with `python run_observability_tests.py` or enable live export in staging

### Metrics Dashboard

- Real-time performance metrics
- Agent execution statistics
- Tool usage analytics
- Error rates and success rates

### Logging

- Structured logging with tenant isolation
- Performance tracing
- Error tracking and alerting
- Audit trails for compliance

### Health Checks

- System health endpoints
- Service availability monitoring
- Resource usage tracking
- Automated alerting

## 🧪 Testing

### Run Tests

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/tools/          # Tool tests
pytest tests/agents/         # Agent tests
pytest tests/services/       # Service tests
pytest tests/integration/    # Integration tests
```

### Trajectory Evaluation Suite

- Validates LangSmith adapters and heuristic fallbacks.
- Execute `pytest tests_new/unit/eval/test_langsmith_adapter.py` for focused coverage.
- Enable `ENABLE_TRAJECTORY_EVALUATION=1` and `ENABLE_TRAJECTORY_FEEDBACK_LOOP=1` to exercise reinforcement feedback paths in integration environments.

### Quality Gates

```bash
make format     # Code formatting
make lint       # Linting
make type       # Type checking
make test       # Testing
make docs       # Documentation validation
```

For detailed quality gate requirements, see [docs/quality-gates.md](docs/quality-gates.md).

## 📚 Documentation

### Core Documentation

- [Architecture Overview](docs/architecture/system_overview.md)
- [Agent Reference](docs/agent_reference.md)
- [Tools Reference](docs/tools_reference.md)
- [Configuration Guide](docs/configuration.md)

### Specialized Guides

- [Quality Assurance Tools](docs/tools/quality_assurance.md)
- [Performance Optimization](docs/tools/performance_optimization.md)
- [Compliance Tools](docs/tools/compliance.md)
- [MCP Integration](docs/tools/mcp_enhanced.md)

### API Documentation

- [Tools API](docs/api/tools_api.md)
- [Agents API](docs/api/agents_api.md)
- [Services API](docs/api/services_api.md)

## 🚀 Deployment

### Docker Deployment

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale bot=3
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -l app=discord-intelligence-bot
```

### Environment-Specific Configs

- `docker-compose.yml` - Development
- `docker-compose.prod.yml` - Production
- `docker-compose.staging.yml` - Staging

## 🔧 Development

### Project Structure

```text
src/ultimate_discord_intelligence_bot/
├── main.py                 # Application entry point
├── crew.py                 # CrewAI crew definition
├── settings.py             # Global configuration
├── step_result.py          # Standard result format
├── tools/                  # CrewAI tools (123+ tools)
├── services/               # Core services
├── tenancy/                # Multi-tenancy support
└── config/                 # YAML configurations
```

### Adding New Tools

1. Create tool class inheriting from `BaseTool`
1. Implement `_run` method returning `StepResult`
1. Add to `tools/__init__.py` exports
1. Register in `crew.py` with appropriate agent
1. Add comprehensive tests

### Adding New Agents

1. Define agent in `crew.py` with `@agent` decorator
1. Specify role, goal, backstory, and tools
1. Add to crew construction in `crew()` method
1. Update agent documentation

## 🤝 Contributing

### Development Workflow

1. Fork the repository
1. Create feature branch
1. Implement changes with tests
1. Run quality gates
1. Submit pull request

### Code Standards

- Follow PEP 8 and project formatting rules
- Include comprehensive type hints
- Write tests for all new functionality
- Update documentation for new features
- Use `StepResult` for all tool returns

### Quality Requirements

- All quality gates must pass
- 100% test coverage for new code
- Documentation updates required
- No increase in MyPy error baseline

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- Check [documentation](docs/) for detailed guides
- Review [troubleshooting guide](docs/operations/troubleshooting.md)
- Open an issue for bugs or feature requests
- Join our Discord server for community support

### Reporting Issues

When reporting issues, please include:

- System information (OS, Python version)
- Error logs and stack traces
- Steps to reproduce
- Expected vs actual behavior

## 🗺️ Roadmap

### Phase 1: Core System ✅

- [x] Tool registration and organization
- [x] Agent architecture implementation
- [x] Basic functionality testing

### Phase 2: Advanced Features ✅

- [x] Quality assurance systems
- [x] Performance optimization
- [x] Enhanced MCP integration

### Phase 3: Production Readiness 🚧

- [ ] Complete system configuration
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Performance optimization

### Phase 4: Scale & Optimize 📋

- [ ] Advanced monitoring
- [ ] Auto-scaling capabilities
- [ ] Advanced analytics
- [ ] Machine learning optimization

## 🏆 Features

### ✅ Implemented

- 123+ specialized tools
- 20+ AI agents
- Multi-platform content ingestion
- Advanced fact-checking
- Vector memory systems
- Quality assurance
- Performance optimization
- Multi-tenancy support

### 🚧 In Development

- Advanced analytics dashboard
- Real-time collaboration features
- Enhanced security features
- Advanced workflow automation

### 📋 Planned

- Machine learning model training
- Advanced visualization tools
- Enterprise integrations
- Mobile applications

---

**Built with ❤️ using CrewAI, Discord.py, and modern Python technologies.**
