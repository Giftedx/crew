# AI Frameworks & Features Comprehensive Inventory

**Purpose**: Complete accounting of all AI/ML frameworks, integrations, and features for repository reorganization.

## Primary AI Orchestration Frameworks (4 Systems)

### 1. CrewAI (Primary)
**Location**: Multiple locations (consolidation needed)
- `src/ai/frameworks/crewai/adapter.py` - Framework adapter
- `src/crewai/` - Standalone package
- `src/ultimate_discord_intelligence_bot/crew_core/` - Core integration
- `src/ultimate_discord_intelligence_bot/agents/` - 20+ agent definitions
- `src/ultimate_discord_intelligence_bot/tasks/` - Task orchestration
- `src/ultimate_discord_intelligence_bot/crew.py` - Main crew setup

**Target**: `src/domains/orchestration/crewai/`

### 2. LangGraph
**Location**:
- `src/ai/frameworks/langgraph/adapter.py` - Adapter
- `src/graphs/langgraph_pilot.py` - Pilot implementation

**Target**: `src/domains/orchestration/langgraph/`

### 3. AutoGen (Microsoft)
**Location**:
- `src/ai/frameworks/autogen/adapter.py` - Adapter
- `src/ultimate_discord_intelligence_bot/services/autogen_service.py` - Service

**Target**: `src/domains/orchestration/autogen/`

### 4. LlamaIndex (RAG/Indexing)
**Location**:
- `src/ai/frameworks/llamaindex/adapter.py` - Adapter
- Integrated with vector storage

**Target**: `src/platform/rag/llamaindex/`

## LLM Service Integration (15+ Services)

### OpenAI Services (9 Services)
1. `services/openai_service.py` - Base integration
2. `services/openai_integration_service.py` - Comprehensive facade
3. `services/openai_streaming.py` - Streaming responses
4. `services/openai_structured_outputs.py` - Instructor-based structured outputs
5. `services/openai_function_calling.py` - Function calling
6. `services/openai_voice.py` - TTS/STT
7. `services/openai_vision.py` - Image analysis
8. `services/openai_multimodal.py` - Cross-modal
9. `services/openai_cost_monitoring.py` - Usage tracking

**Target**: `src/platform/llm/providers/openai/`

### OpenRouter (25+ Files)
**Main Directory**: `services/openrouter_service/`
- `service.py`, `refactored_service.py`, `facade.py` - Core services
- `adaptive_routing.py` - Adaptive routing logic
- `circuit_breaker.py` - Circuit breaker pattern
- `cache_layer.py`, `cache.py`, `cache_warmer.py`, `tenant_semantic_cache.py` - Caching
- `rate_limiter.py` - Rate limiting
- `retry_strategy.py` - Retry logic
- `monitoring.py`, `health.py` - Observability
- `budget.py`, `request_budget.py` - Cost management
- `batcher.py`, `async_execution.py`, `execution.py` - Execution engines
- `connection_pool.py`, `object_pool.py` - Resource pooling
- `workflow.py`, `context.py`, `state.py`, `quality.py` - Workflow management
- `plugins/` subdirectory (3 plugins)

**Plugins**:
- `plugins/enhanced_linucb_plugin.py` - LinUCB for routing
- `plugins/doubly_robust_plugin.py` - Doubly robust estimation
- `plugins/base_plugin.py` - Plugin architecture

**Duplicates**:
- `services/openrouter_service.py` - Standalone file
- `services/enhanced_openrouter_service.py` - Enhanced version

**Target**: `src/platform/llm/providers/openrouter/`

### LLM Routing (6 Services)
1. `services/litellm_router.py` - LiteLLM multi-provider
2. `services/model_router.py` - Custom routing
3. `services/routing_service.py` - Routing service
4. `services/rl_model_router.py` - RL-based routing
5. `services/llm_router_adapter.py` - Adapter pattern
6. `services/llm_provider_registry.py` - Provider registry

**Target**: `src/platform/llm/routing/`

### Anthropic (Claude)
- Core dependency in pyproject.toml
- Integrated throughout services

**Target**: Document in `src/platform/llm/providers/anthropic/`

## Reinforcement Learning System (40+ Files)

### Core RL Infrastructure (`src/core/rl/` - 15 files)

**Policies** (`policies/` - 5 files):
- `linucb.py` - LinUCB contextual bandit
- `vowpal_wabbit.py` - Vowpal Wabbit integration
- `thompson_sampling.py` - Thompson sampling
- `advanced_bandits.py` - Advanced algorithms
- `bandit_base.py` - Base bandit class

**Experiment Framework** (4 files):
- `experiment.py` - Base experimentation
- `advanced_experiments.py` - Advanced A/B testing
- `cost_quality_optimization.py` - Cost-quality tradeoffs
- `feature_store.py` - Feature engineering

**RL Infrastructure** (6 files):
- `reward_engine.py` - Reward signal processing
- `shadow_regret.py` - Shadow mode evaluation
- `shields.py` - Safety constraints
- `ucb_bandit.py` - UCB algorithms
- `registry.py` - RL component registry
- `provider_preference_learning.py` - Provider learning

**Target**: `src/platform/rl/core/`

### AI-Level RL (`src/ai/rl/` - 6 files)
- `agent_routing_bandit.py` - Agent selection
- `tool_routing_bandit.py` - Tool selection
- `threshold_tuning_bandit.py` - Threshold optimization
- `meta_learning_aggregator.py` - Meta-learning
- `langsmith_trajectory_evaluator.py` - LangSmith integration
- `unified_feedback_orchestrator.py.DEPRECATED` - Legacy

**Target**: `src/domains/intelligence/optimization/rl/`

### Routing RL (`src/ai/routing/` - 8 files)
- `bandit_router.py` - Base bandit router
- `linucb_router.py` - LinUCB router
- `thompson_sampling_router.py` - Thompson router
- `vw_bandit_router.py` - Vowpal Wabbit router
- `cold_start_priors.py` - Cold start handling
- `feature_engineering.py` - Feature extraction
- `router_registry.py` - Router registry
- `_metrics_types.py` - Metrics types

**Target**: `src/platform/llm/routing/bandits/`

### Service-Level RL (4 files)
- `services/bandit_policy.py` - Bandit policies
- `services/rl_cache_optimizer.py` - RL for caching
- `services/rl_model_router.py` - RL for model selection
- `services/performance_learning_engine.py` - Performance learning

**Target**: `src/platform/optimization/`

### Enhancements (1 file)
- `src/enhancements/neural_contextual_bandit.py` - Neural bandits

**Target**: `src/platform/rl/neural/`

## Memory Systems (6 Backends + Unified)

### 1. Qdrant Vector Store (Primary)
**Location** (`src/memory/` - 7 files):
- `qdrant_provider.py` - Qdrant client
- `vector_store.py` - Vector store interface
- `enhanced_vector_store.py` - Enhanced version
- `hybrid_retriever.py` - Hybrid search
- `embeddings.py` - Embedding generation
- `embedding_service.py` - Embedding service
- `store.py` - Store interface

**Target**: `src/domains/memory/backends/qdrant/`

### 2. Mem0 (Memory Framework)
**Location** (3 locations):
- `services/mem0_service.py` - Service integration
- `tools/memory/mem0_memory_tool.py` - CrewAI tool
- `memory/plugins/mem0_plugin.py` - Plugin

**Target**: `src/domains/memory/backends/mem0/`

### 3. HippoRAG (Continual Learning)
**Location** (3 locations):
- `tools/memory/hipporag_continual_memory_tool.py` - Tool
- `memory/plugins/hipporag_plugin.py` - Plugin
- `monitoring/hipporag_alerts.py` - Monitoring

**Target**: `src/domains/memory/backends/hipporag/`

### 4. Neo4j Graph Memory
**Location**:
- `tools/memory/graph_memory_tool.py` - Tool
- `src/kg/` - Knowledge graph package
- `memory/unified_graph_store.py` - Graph store

**Target**: `src/domains/memory/backends/neo4j/`

### 5. ChromaDB
**Location**:
- Optional dependency
- Integrated via tools

**Target**: `src/domains/memory/backends/chromadb/`

### 6. Unified Memory System
**Location** (`src/ultimate_discord_intelligence_bot/`):
- `knowledge/unified_memory.py` - Unified interface
- `knowledge/retrieval_engine.py` - Retrieval
- `tools/memory/unified_memory_tool.py` - Tool
- `features/memory_coordinator.py` - Coordinator

**Target**: `src/domains/memory/unified/`

### Memory Tools (15+ tools in `tools/memory/`)
- `rag_hybrid_tool.py`, `rag_query_vs_tool.py` - RAG querying
- `rag_ingest_tool.py`, `rag_ingest_url_tool.py` - RAG ingestion
- `offline_rag_tool.py` - Offline RAG
- `lc_summarize_tool.py` - LangChain summarization
- `vector_search_tool.py` - Vector search
- `research_and_brief_tool.py`, `research_and_brief_multi_tool.py` - Research
- `strategic_planning_tool.py` - Planning
- `knowledge_ops_tool.py` - Operations
- `memory_storage_tool.py` - Storage
- `memory_compaction_tool.py` - Compaction
- `prompt_compression_tool.py` - Compression
- `vowpal_wabbit_bandit_tool.py` - RL tool
- `mock_vector_tool.py` - Testing

**Target**: `src/domains/memory/tools/`

## DSPy (Prompt Optimization)

**Location** (4 locations):
- `src/ultimate_discord_intelligence_bot/dspy_components/` (2 files)
  - `optimized_analysis_tool.py` - Optimized tool
  - `__init__.py`
- `services/dspy_optimization_service.py` - Service
- `services/dspy_components/signature.py` - Signature definitions
- `src/enhancements/dspy_prompt_optimizer.py` - Optimizer

**Target**: `src/platform/prompts/dspy/`

## Prompt Engineering & Compression

### Prompt Engine
**Location** (3 locations):
- `services/prompt_engine.py` - Main engine
- `src/prompt_engine/` standalone package:
  - `guards.py` - Prompt guards
  - `llmlingua_adapter.py` - LLMLingua integration

**Target**: `src/platform/prompts/engine/`

### Compression
**Location** (3 locations):
- `services/prompt_compressor.py` - Compressor service
- `src/ai/compression/llmlingua_compressor.py` - LLMLingua compressor
- `tools/memory/prompt_compression_tool.py` - Tool

**Target**: `src/platform/prompts/compression/`

## Evaluation & Observability

### LangSmith Integration (3 locations)
- `services/langfuse_service.py` - Langfuse service (note naming)
- `src/ai/evaluation/langsmith_evaluator.py` - Evaluator
- `src/ai/rl/langsmith_trajectory_evaluator.py` - Trajectory eval
- `src/eval/langsmith_adapter.py` - Eval adapter

**Target**: `src/platform/observability/langsmith/`

### Logfire (Pydantic Observability)
**Location** (`src/obs/`):
- `logfire_config.py` - Configuration
- `logfire_spans.py` - Span tracking

**Target**: `src/platform/observability/logfire/`

### OpenTelemetry (Custom Implementation)
**Location**: `src/opentelemetry/` (complete OTEL stack):
- `_logs/` - Logging
- `exporter/` - Exporters
- `metrics/` - Metrics
- `propagators/` - Context propagation
- `sdk/` - SDK implementation
- `trace/` - Tracing
- `util/` - Utilities
- `attributes.py`, `context.py`, `environment_variables.py`, `propagate.py`, `trace.py`

**Target**: `src/platform/observability/opentelemetry/`

## RAG & Retrieval

### RAG Tools (5 tools)
- `tools/memory/rag_hybrid_tool.py` - Hybrid RAG
- `tools/memory/rag_query_vs_tool.py` - Query vector store
- `tools/memory/rag_ingest_tool.py` - Ingestion
- `tools/memory/rag_ingest_url_tool.py` - URL ingestion
- `tools/memory/offline_rag_tool.py` - Offline RAG

**RAG Enhancement**:
- `src/ai/rag/rag_quality_feedback.py` - Quality feedback

**Retrieval**:
- `knowledge/retrieval_engine.py` - Retrieval engine
- `memory/hybrid_retriever.py` - Hybrid retrieval

**GraphRAG**:
- `src/enhancements/graphrag_integration.py` - GraphRAG

**Target**: `src/domains/memory/rag/`

## Content Analysis AI Features

### Vision & Multimodal
**Location**:
- `analysis/vision/` - Computer vision pipelines
- `services/multimodal_understanding_service.py` - Multimodal service
- OpenAI vision/multimodal (see OpenAI section)

**Target**: `src/domains/intelligence/analysis/vision/`

### NLP Analysis
**Location**:
- `analysis/nlp/` - NLP pipelines
- `analysis/sentiment/` - Sentiment analysis
- `analysis/topic/` - Topic modeling

**Target**: `src/domains/intelligence/analysis/nlp/`

### Safety & Moderation
**Location**:
- `analysis/safety/` - Content safety
- `security/moderation.py` - Moderation
- `security/net_guard.py` - Network guard

**Target**: `src/platform/security/moderation/`

## A/B Testing & Experimentation

**Location** (3 files):
- `src/ai/ab_testing_framework.py` - A/B testing
- `src/core/rl/experiment.py` - Base experiments
- `src/core/rl/advanced_experiments.py` - Advanced experiments
- `services/evaluation_harness.py` - Evaluation harness

**Target**: `src/platform/experimentation/`

## Semantic Caching

**Location** (4 locations):
- `src/enhancements/semantic_cache_enhanced.py` - Enhanced cache
- `services/unified_cache_service.py` - Unified cache
- `services/semantic_router_service.py` - Semantic router
- `services/openrouter_service/tenant_semantic_cache.py` - Tenant cache

**Target**: `src/platform/cache/semantic/`

## Agent Communication

**Location**:
- `src/ai/agent_messaging/` - Inter-agent messaging

**Target**: `src/domains/orchestration/messaging/`

## Self-Improvement

**Location**:
- `src/ai/self_improvement/` - Autonomous improvement

**Target**: `src/domains/intelligence/self_improvement/`

## Additional AI Integrations

### Instructor (Structured Outputs)
- Core dependency for validated LLM outputs
- Integrated throughout OpenAI services

### Playwright (Browser Automation)
- `tools/web/playwright_automation_tool.py` - Browser automation
- Used for intelligent web scraping

**Target**: `src/platform/web/automation/`

### WebSockets & Real-time
- `services/websocket_service.py` - WebSocket service
- `services/websocket_integration.py` - Integration

**Target**: `src/platform/realtime/`

## Third-Party Dependencies Summary

From `pyproject.toml`:

### Core AI/ML
- `crewai>=0.80.0` - Primary orchestration
- `crewai-tools>=0.12.0` - Tool ecosystem

### LLM Services
- `openai>=1.0.0` - OpenAI API
- `anthropic>=0.69.0` - Claude API
- `instructor>=1.7.0` - Structured outputs
- `litellm>=1.51.0` - Multi-provider routing
- `logfire[fastapi,httpx]>=2.5.0` - Observability

### Vector & Memory
- `qdrant-client>=1.7.0` - Vector database
- `llama-index>=0.10.0` - RAG framework
- `chromadb>=0.4.0` - Vector DB (optional)
- `mem0ai>=0.1.0` - Memory framework (optional)
- `neo4j>=5.14.0` - Graph database

### ML/AI (Optional)
- `torch>=2.0.0` - PyTorch
- `transformers>=4.35.0` - Hugging Face
- `sentence-transformers>=2.2.0` - Embeddings
- `scikit-learn>=1.3.0` - ML utilities

### Vision (Optional)
- `opencv-python>=4.8.0` - Computer vision
- `pillow>=10.0.0` - Image processing

## Reorganization Actions Required

### Platform Layer
1. **LLM Platform** (`src/platform/llm/`):
   - `providers/` - openai, anthropic, openrouter
   - `routing/` - routing services, bandits
   - `structured/` - instructor integration

2. **RL Platform** (`src/platform/rl/`):
   - `core/` - policies, experiments, shields
   - `neural/` - neural bandits

3. **Prompts Platform** (`src/platform/prompts/`):
   - `engine/` - prompt engine
   - `compression/` - LLMLingua
   - `dspy/` - DSPy optimization

4. **Cache Platform** (`src/platform/cache/`):
   - `semantic/` - semantic caching
   - `backends/` - Redis, in-memory

5. **Observability Platform** (`src/platform/observability/`):
   - `langsmith/` - LangSmith integration
   - `logfire/` - Logfire
   - `opentelemetry/` - OTEL

### Domain Layer
1. **Intelligence Domain** (`src/domains/intelligence/`):
   - `analysis/` - NLP, vision, multimodal
   - `optimization/` - RL strategies
   - `self_improvement/` - Auto-improvement

2. **Memory Domain** (`src/domains/memory/`):
   - `backends/` - qdrant, mem0, hipporag, neo4j, chroma
   - `unified/` - unified memory interface
   - `rag/` - RAG pipelines
   - `tools/` - memory tools

3. **Orchestration Domain** (`src/domains/orchestration/`):
   - `crewai/` - CrewAI integration
   - `langgraph/` - LangGraph integration
   - `autogen/` - AutoGen integration
   - `messaging/` - Agent communication

### Keep Separate
1. **MCP Servers** - `src/mcp_server/` (12 servers)
2. **FastAPI Server** - `src/server/` (production API)
3. **Evaluation** - `src/eval/` (evaluation harness)

## Total Component Count

- **AI Frameworks**: 4 (CrewAI, LangGraph, AutoGen, LlamaIndex)
- **LLM Services**: 15+ (OpenAI 9, OpenRouter 25+ files, Routing 6)
- **RL Components**: 40+ files (Core 15, AI 6, Routing 8, Service 4, Enhancement 1, OpenRouter plugins 3)
- **Memory Backends**: 6 (Qdrant, Mem0, HippoRAG, Neo4j, ChromaDB, Unified) + 15+ tools
- **Prompt Engineering**: 7 files (Engine 3, Compression 3, DSPy 4)
- **Observability**: 3 systems (LangSmith 4, Logfire 2, OpenTelemetry 15+ files)
- **RAG & Retrieval**: 10+ files
- **Content Analysis**: Vision, NLP, Safety modules
- **A/B Testing**: 4 files
- **Semantic Caching**: 4 implementations
- **Additional**: Agent messaging, self-improvement, WebSockets, Playwright

**Total**: 150+ AI/ML related files to reorganize
