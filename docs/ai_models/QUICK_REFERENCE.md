# AI Model Quick Reference - At-a-Glance Guide

**For Immediate Use in All AI Operations**

---

## Model Selection Flow Chart

```
Content Type?
├─ Text Only
│  ├─ Simple → Claude Haiku / GPT-3.5 / Gemini Flash
│  ├─ Standard → Claude Sonnet / GPT-4 / Gemini Pro
│  └─ Complex → Claude Opus / GPT-5 (high effort) / Gemini Pro
├─ Image Analysis
│  ├─ Basic → GPT-4 Vision / Claude 3 Sonnet
│  └─ Advanced → GPT-4 Vision / Claude 3 Opus / Gemini Pro Vision
├─ Video Analysis
│  └─ Frame Analysis → GPT-5 (high) / Claude Opus / Gemini Pro
└─ Multi-Modal
   └─ Cross-Media → GPT-5 (high) / Claude Opus / Gemini Pro
```

---

## Configuration Cheat Sheet

### Quick Config Templates

**Fast & Cheap (Budget):**

```python
{
    "model": "claude-3-haiku" | "gpt-3.5-turbo" | "gemini-flash",
    "temperature": 0.3,
    "max_tokens": 512
}
```

**Balanced (Production):**

```python
{
    "model": "claude-3-sonnet" | "gpt-4" | "gemini-pro",
    "temperature": 0.7,
    "max_tokens": 2048
}
```

**Advanced (Premium):**

```python
{
    "model": "claude-3-opus" | "gpt-5" | "gemini-pro",
    "temperature": 0.8,
    "max_tokens": 4096,
    "reasoning": {"effort": "high"}  # OpenAI only
}
```

---

## Prompt Templates

### Structured Analysis Template

```markdown
# Identity
You are an expert [domain] analyst with advanced [specific skills].

# Instructions
- [Primary instruction]
- [Secondary instruction]
- [Format requirement]
- Return results as structured JSON

# Context
[Relevant background information]

# Examples
<user_query>[Example input]</user_query>
<assistant_response>[Example output]</assistant_response>

# Task
[Actual task description]
```

### Multi-Modal Analysis Template

```markdown
# Multi-Modal Content Analysis

## Task
Analyze the provided content across all available modalities:
- Visual elements (if image/video)
- Audio elements (if video/audio)
- Textual elements (captions, transcripts)
- Metadata (timestamps, creators, context)

## Output Format
Return structured JSON with:
{
  "content_type": "string",
  "visual_analysis": {...},
  "audio_analysis": {...},
  "text_analysis": {...},
  "unified_sentiment": "string",
  "dominant_themes": ["array"],
  "confidence_scores": {...}
}

## Requirements
- Provide confidence scores for all assertions
- Include cross-modal correlations
- Cite specific evidence from content
```

---

## Tool Usage Best Practices

### Parallel Tool Calls

```xml
<use_parallel_tool_calls>
For maximum efficiency, whenever you perform multiple independent operations,
invoke all relevant tools simultaneously rather than sequentially.
Prioritize calling tools in parallel whenever possible.
</use_parallel_tool_calls>
```

### Tool Choice Strategy

```python
# Let model decide (default)
tool_choice = "auto"

# Require tool use (any tool)
tool_choice = "any"

# Force specific tool
tool_choice = {"type": "tool", "name": "analyze_content"}

# Disable tools
tool_choice = "none"
```

---

## Temperature Guidelines

| Temperature | Use Case | Example |
|-------------|----------|---------|
| 0.0 | Deterministic, factual | "List all Python built-in functions" |
| 0.2 | Code generation | "Write a function to parse JSON" |
| 0.4 | Analysis | "Analyze this dataset for trends" |
| 0.7 | General purpose | "Explain quantum computing" |
| 0.9 | Creative tasks | "Write a story about..." |
| 1.0 | Maximum creativity | "Brainstorm 50 startup ideas" |

---

## Token Optimization

### By Task Complexity

```python
TOKEN_ALLOCATION = {
    "quick_query": 512,           # Simple questions
    "standard_analysis": 1024,    # Normal analysis
    "detailed_report": 2048,      # Comprehensive output
    "extensive_document": 4096,   # Long-form content
    "maximum_output": 8192        # Edge cases only
}
```

### Caching Priority

**Always Cache:**

- System instructions
- Tool definitions
- Large reference documents
- Frequently used examples

**Selectively Cache:**

- User conversation history
- Temporary context
- Session-specific data

**Never Cache:**

- User-specific sensitive data
- Time-sensitive information
- One-time queries

---

## Error Handling

### Retry Strategy

```python
RETRY_CONFIG = {
    "rate_limit": {
        "max_retries": 3,
        "backoff_factor": 2,
        "max_backoff": 60
    },
    "network_error": {
        "max_retries": 2,
        "backoff_factor": 1.5
    },
    "api_error": {
        "max_retries": 1,
        "backoff_factor": 1
    }
}
```

### Fallback Strategy

```python
MODEL_FALLBACK_CHAIN = [
    "primary_model",      # Try first
    "backup_model",       # If primary fails
    "budget_model"        # Last resort
]
```

---

## Performance Benchmarks

### Expected Latencies

| Model | Simple Query | Analysis | Complex Task |
|-------|-------------|----------|--------------|
| GPT-5 (low) | 1-2s | 3-5s | 8-12s |
| GPT-5 (high) | 3-5s | 8-15s | 20-40s |
| Claude Haiku | 0.5-1s | 1-2s | 3-5s |
| Claude Sonnet | 1-2s | 3-5s | 8-12s |
| Claude Opus | 2-4s | 5-10s | 15-30s |
| Gemini Flash | 0.5-1s | 1-3s | 4-8s |
| Gemini Pro | 1-2s | 3-6s | 10-20s |

---

## Cost Estimates

### Approximate Pricing (per 1M tokens)

| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| GPT-5 | $$ | $$$$ | + reasoning tokens |
| GPT-4 Turbo | $$ | $$$ | Vision capable |
| Claude Opus | $$$ | $$$$ | Highest quality |
| Claude Sonnet | $ | $$ | Best value |
| Claude Haiku | $ | $ | Most economical |
| Gemini Pro | $$ | $$$ | Long context |
| Gemini Flash | $ | $ | Fastest/cheapest |

---

## Usage in Current System

### From Agent Code

```python
# Import official best practices
from docs.ai_models.official_prompt_engineering_guide import (
    get_prompt_template,
    get_model_config
)

# Create prompt following best practices
prompt = get_prompt_template(
    model_family="anthropic",
    task_type="multi_modal_analysis",
    complexity="comprehensive"
)

# Get optimized configuration
config = get_model_config(
    model="claude-3-opus",
    task_type="analysis"
)
```

### From MCP Tools

```python
# Use in MCP tool calls
result = await mcp.analyze_content_auto(
    content_url=url,
    config={
        "model_selection": "auto",  # Use router's best practices
        "complexity": "comprehensive",
        "optimize_for": "accuracy"  # or "speed", "cost"
    }
)
```

### From Discord Commands

```python
# Interactive selection follows best practices
depth_config = {
    "quick": ("haiku", "low", 0.3),
    "standard": ("sonnet", "medium", 0.7),
    "comprehensive": ("opus", "high", 0.8),
    "expert": ("opus", "high", 0.9)
}

model, effort, temp = depth_config[user_selection]
```

---

## Monitoring & Optimization

### Key Metrics to Track

```python
MONITOR_METRICS = {
    "quality_score": "Track output quality vs expectations",
    "latency": "Response time per model/task",
    "cost": "Token usage and API costs",
    "cache_hit_rate": "Semantic cache effectiveness",
    "tool_call_success": "Tool usage reliability"
}
```

### Optimization Triggers

```python
OPTIMIZE_WHEN = {
    "quality_drops": "quality_score < 0.8",
    "latency_high": "response_time > 10s",
    "cost_exceeds": "daily_cost > budget * 1.2",
    "cache_misses": "hit_rate < 0.5"
}
```

---

## Common Patterns

### For Content Analysis

```python
prompt = f"""
Analyze this {content_type} content:

Content: {content_url}

Provide:
1. Sentiment analysis (positive/neutral/negative)
2. Key themes (top 3)
3. Emotional tone
4. Factual accuracy assessment
5. Confidence scores

Return as JSON.
"""
```

### For Code Generation

```python
prompt = """
# Identity
You are an expert Python developer following PEP 8 standards.

# Instructions
- Write clean, documented code
- Include type hints
- Add error handling
- Return StepResult objects
- Follow tenant-aware patterns

# Task
{task_description}
"""
```

### For Multi-Step Planning

```python
prompt = """
Create a step-by-step plan for: {objective}

For each step provide:
1. Clear action description
2. Required tools/resources
3. Success criteria
4. Estimated time/cost

Think through the entire workflow before suggesting the first step.
"""
```

---

## Emergency Quick Reference

**Model Down? Use Fallback:**

```python
PRIMARY → BACKUP → BUDGET
GPT-5 → GPT-4 → GPT-3.5
Claude Opus → Sonnet → Haiku
Gemini Pro → Flash
```

**Rate Limited? Strategies:**

1. Switch to different provider
2. Reduce max_tokens
3. Increase delay between requests
4. Use cached responses

**Quality Issues? Adjustments:**

1. Increase temperature (0.7 → 0.8)
2. Raise reasoning effort (medium → high)
3. Add more examples to prompt
4. Switch to more capable model

**Cost Too High? Optimizations:**

1. Use prompt compression
2. Enable semantic caching
3. Switch to cheaper model tier
4. Reduce max_tokens allocation

---

**This guide is based on official documentation from OpenAI, Anthropic, and Google AI and is updated regularly to reflect latest best practices.**
