# Optional Dependencies Guide

The Ultimate Discord Intelligence Bot has several optional dependency groups that extend its capabilities. These are not required for core functionality but enable specific advanced features.

## Installation

Install optional dependencies using the extras syntax:

```bash
# Single extra
pip install -e '.[extra_name]'

# Multiple extras
pip install -e '.[extra1,extra2,extra3]'

# All extras for development
pip install -e '.[dev,llm_opt,graph_memory,hipporag,enhanced_memory,dspy,semantic_router]'
```

**Important for zsh users:** Always quote the brackets to prevent glob expansion:

```bash
pip install -e '.[semantic_router]'  # ✅ Correct
pip install -e .[semantic_router]    # ❌ Will fail in zsh
```

## Available Optional Extras

### Development Tools (`dev`)

Essential development and testing utilities.

**Includes:**

- pytest, pytest-asyncio (testing)
- ruff, mypy (linting and type checking)
- pre-commit (git hooks)
- Type stubs for common libraries

**Install:**

```bash
pip install -e '.[dev]'
```

**Use when:** Setting up for development, running tests, or contributing code.

---

### LLM Optimization (`llm_opt`)

Advanced LLM caching and prompt compression.

**Includes:**

- gptcache (LLM response caching)
- llmlingua (prompt compression)

**Install:**

```bash
pip install -e '.[llm_opt]'
```

**Features enabled:**

- `ENABLE_GPTCACHE=true`
- `ENABLE_LLMLINGUA=true`
- `ENABLE_PROMPT_COMPRESSION=true`

**Use when:** Optimizing API costs and reducing token usage.

---

### Graph Memory (`graph_memory`)

Knowledge graph-based memory system.

**Includes:**

- graphrag (Microsoft GraphRAG)
- networkx (graph algorithms)

**Install:**

```bash
pip install -e '.[graph_memory]'
```

**Features enabled:**

- `ENABLE_GRAPH_MEMORY=true`
- `ENABLE_KNOWLEDGE_GRAPH=true`

**Use when:** Building cross-content knowledge relationships and entity tracking.

---

### HippoRAG Memory (`hipporag`)

Continual learning memory system based on hippocampus-inspired algorithms.

**Includes:**

- hipporag (continual memory)
- torch (PyTorch)
- transformers (Hugging Face)

**Install:**

```bash
pip install -e '.[hipporag]'
```

**Features enabled:**

- `ENABLE_HIPPORAG_MEMORY=true`
- `ENABLE_HIPPORAG_CONTINUAL_MEMORY=true`

**Use when:** Implementing long-term, evolving memory across sessions.

---

### Enhanced Memory (`enhanced_memory`)

Mem0 personal memory system.

**Includes:**

- mem0ai (personal memory)

**Install:**

```bash
pip install -e '.[enhanced_memory]'
```

**Features enabled:**

- `ENABLE_MEM0_MEMORY=true`

**Use when:** Tracking user-specific context and preferences.

---

### DSPy Optimization (`dspy`)

Prompt optimization and program synthesis.

**Includes:**

- dspy-ai (prompt optimization framework)

**Install:**

```bash
pip install -e '.[dspy]'
```

**Features enabled:**

- `ENABLE_DSPY_OPTIMIZATION=true`

**Use when:** Automatically optimizing prompts for better performance.

---

### Semantic Router (`semantic_router`)

Intelligent query routing based on semantic similarity.

**Includes:**

- semantic-router (semantic routing)

**Install:**

```bash
pip install -e '.[semantic_router]'
```

**Features enabled:**

- `ENABLE_SEMANTIC_ROUTER=true`

**Use when:** Dynamically routing queries to the best-suited tools/agents.

**Note:** The system gracefully handles the absence of this library. If not installed, semantic routing will be skipped with a warning.

---

### Contextual Bandits (`bandits`)

Vowpal Wabbit for reinforcement learning.

**Includes:**

- vowpalwabbit (contextual bandits)

**Install:**

```bash
pip install -e '.[bandits]'
```

**Features enabled:**

- `ENABLE_ADVANCED_BANDITS=true`

**Use when:** Implementing adaptive model/prompt selection based on feedback.

---

### LangGraph (`langgraph`)

Graph-based agent workflows.

**Includes:**

- langgraph (LangChain graphs)

**Install:**

```bash
pip install -e '.[langgraph]'
```

**Features enabled:**

- `ENABLE_LANGGRAPH_PILOT=true`
- `ENABLE_LANGGRAPH_PILOT_API=true`

**Use when:** Building complex multi-step agent workflows.

---

### AutoGen (`autogen`)

Microsoft AutoGen multi-agent framework.

**Includes:**

- pyautogen (multi-agent conversations)

**Install:**

```bash
pip install -e '.[autogen]'
```

**Use when:** Implementing collaborative multi-agent systems.

---

### MCP Tools (`mcp`)

Model Context Protocol server.

**Includes:**

- fastmcp (MCP server framework)

**Install:**

```bash
pip install -e '.[mcp]'
```

**Features enabled:**

- `ENABLE_MCP_TOOLS=true`

**Command:**

```bash
crew_mcp  # Starts MCP server
```

**Use when:** Exposing bot capabilities via Model Context Protocol.

---

### Metrics & Monitoring (`metrics`)

Prometheus metrics collection.

**Includes:**

- prometheus-client (metrics export)

**Install:**

```bash
pip install -e '.[metrics]'
```

**Features enabled:**

- `ENABLE_HTTP_METRICS=true`
- `ENABLE_PROMETHEUS_ENDPOINT=true`

**Use when:** Setting up production monitoring and observability.

---

### Whisper Transcription (`whisper`)

OpenAI Whisper for audio transcription.

**Includes:**

- openai-whisper (speech-to-text)

**Install:**

```bash
pip install -e '.[whisper]'
```

**Note:** The default installation uses `faster-whisper` which is faster and lighter. Only install this if you need the original OpenAI Whisper implementation.

---

### vLLM (`vllm`)

High-performance local LLM inference.

**Includes:**

- vllm (optimized LLM serving)
- torch (PyTorch)

**Install:**

```bash
pip install -e '.[vllm]'
```

**Use when:** Running local LLM inference with optimized throughput.

---

### Profiling Tools (`profiling`)

Performance analysis and debugging utilities.

**Includes:**

- line-profiler (line-by-line profiling)
- memory-profiler (memory usage)
- snakeviz (visualization)
- py-spy (sampling profiler)
- pympler (memory analysis)

**Install:**

```bash
pip install -e '.[profiling]'
```

**Use when:** Debugging performance issues or optimizing code.

---

### RL Adaptation (`rl_adapt`)

Advanced reinforcement learning for adaptive systems.

**Includes:**

- ax-platform (Bayesian optimization)
- botorch (Bayesian optimization)
- pyro-ppl (probabilistic programming)

**Install:**

```bash
pip install -e '.[rl_adapt]'
```

**Use when:** Implementing sophisticated adaptive routing and parameter tuning.

---

## Recommended Combinations

### Full Production Setup

```bash
pip install -e '.[metrics,llm_opt,graph_memory,hipporag,enhanced_memory,mcp]'
```

Includes: Monitoring, all memory systems, caching, and MCP server.

### Development Setup

```bash
pip install -e '.[dev,profiling]'
```

Includes: Testing, linting, type checking, and profiling tools.

### Maximum Capabilities

```bash
pip install -e '.[dev,metrics,llm_opt,graph_memory,hipporag,enhanced_memory,dspy,semantic_router,bandits,langgraph,mcp,profiling]'
```

All optional features enabled (requires significant disk space and memory).

### Minimal Production

```bash
pip install -e .
```

Core features only, no optional extras.

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError` for an optional dependency:

1. Check if the feature is enabled in `.env`
2. Install the corresponding extra: `pip install -e '.[extra_name]'`
3. Or disable the feature in `.env` to skip it

### Conflict Resolution

Some extras may have conflicting requirements. If installation fails:

1. Try installing extras one at a time
2. Check `pyproject.toml` for version constraints
3. Create a separate virtual environment for conflicting features

### Disk Space

Full installation with all extras requires ~5-10 GB:

- PyTorch (vllm, hipporag): ~2-3 GB
- Transformers models: ~2-5 GB
- Other dependencies: ~1-2 GB

---

## Feature Flag Reference

Map extras to their corresponding `.env` flags:

| Extra | Feature Flags |
|-------|--------------|
| `llm_opt` | `ENABLE_GPTCACHE`, `ENABLE_LLMLINGUA`, `ENABLE_PROMPT_COMPRESSION` |
| `graph_memory` | `ENABLE_GRAPH_MEMORY`, `ENABLE_KNOWLEDGE_GRAPH` |
| `hipporag` | `ENABLE_HIPPORAG_MEMORY`, `ENABLE_HIPPORAG_CONTINUAL_MEMORY` |
| `enhanced_memory` | `ENABLE_MEM0_MEMORY` |
| `dspy` | `ENABLE_DSPY_OPTIMIZATION` |
| `semantic_router` | `ENABLE_SEMANTIC_ROUTER` |
| `bandits` | `ENABLE_ADVANCED_BANDITS` |
| `langgraph` | `ENABLE_LANGGRAPH_PILOT`, `ENABLE_LANGGRAPH_PILOT_API` |
| `mcp` | `ENABLE_MCP_TOOLS` |
| `metrics` | `ENABLE_HTTP_METRICS`, `ENABLE_PROMETHEUS_ENDPOINT` |

---

## Checking Installed Extras

To see what's currently installed:

```bash
# Check specific package
pip show semantic-router

# List all installed packages
pip list | grep -E "(gptcache|hipporag|mem0ai|dspy|semantic-router)"

# Verify imports work
python -c "import semantic_router; print('✅ semantic-router installed')"
```

---

## Uninstalling Extras

To remove an optional dependency:

```bash
pip uninstall semantic-router  # Uninstall specific package
```

To reinstall without an extra:

```bash
pip install -e .  # Reinstall without any extras
```

---

## CI/CD Considerations

For automated deployments, install only needed extras:

```dockerfile
# Dockerfile example
RUN pip install -e '.[metrics,llm_opt,enhanced_memory]'
```

```yaml
# GitHub Actions example
- name: Install dependencies
  run: pip install -e '.[dev,metrics]'
```

---

## Support

If you encounter issues with optional dependencies:

1. Run `make doctor` to check system health
2. Check logs for specific error messages
3. Review this guide for installation instructions
4. See `pyproject.toml` for version constraints
5. File an issue with dependency name and error message
