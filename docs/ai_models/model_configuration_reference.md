# Official Model Configuration Reference

**Official Sources:** OpenAI, Anthropic, Google AI
**Last Updated:** 2025-10-09

---

## Table of Contents

1. [Model Comparison Matrix](#model-comparison-matrix)
2. [OpenAI Models](#openai-models)
3. [Anthropic Claude Models](#anthropic-claude-models)
4. [Google Gemini Models](#google-gemini-models)
5. [Configuration Best Practices](#configuration-best-practices)
6. [Cost Optimization](#cost-optimization)

---

## Model Comparison Matrix

| Model | Provider | Context Window | Strengths | Best For | Relative Cost |
|-------|----------|----------------|-----------|----------|---------------|
| GPT-5 | OpenAI | 128k | Advanced reasoning, coding | Complex analysis, planning | $$$$$ |
| GPT-4 Turbo | OpenAI | 128k | Balanced performance | General purpose, multi-modal | $$$$ |
| GPT-4 Vision | OpenAI | 128k | Image understanding | Visual analysis | $$$$ |
| Claude 3 Opus | Anthropic | 200k | Nuanced understanding | Complex tasks, long context | $$$$$ |
| Claude 3 Sonnet | Anthropic | 200k | Balanced speed/intelligence | Production workflows | $$$ |
| Claude 3 Haiku | Anthropic | 200k | Fast, economical | Simple tasks, high volume | $ |
| Gemini Pro | Google | 1M+ | Long context, multi-modal | Comprehensive analysis | $$$ |
| Gemini Flash | Google | 1M+ | Fast, efficient | Real-time applications | $ |
| Gemini Pro Vision | Google | 1M+ | Advanced vision | Visual understanding | $$$$ |

---

## OpenAI Models

### GPT-5 (Reasoning Models)

**Model IDs:**

- `gpt-5` - Full reasoning capability
- `gpt-5-mini` - Faster, lighter reasoning
- `gpt-5-nano` - Most economical reasoning

**Configuration:**

```python
{
    "model": "gpt-5",
    "reasoning": {
        "effort": "high"  # low, medium, high
    },
    "max_output_tokens": 4096,
    "temperature": 0.7,
    "stream": False
}
```

**Reasoning Effort Guidance:**

- **Low:** Simple queries, quick responses (faster, cheaper)
- **Medium:** Balanced tasks, general problem-solving (default)
- **High:** Complex coding, multi-step planning, deep analysis (slower, more thorough)

**Token Usage:**

```python
{
    "usage": {
        "input_tokens": 75,
        "output_tokens": 1186,
        "output_tokens_details": {
            "reasoning_tokens": 1024  # Internal reasoning not shown in output
        },
        "total_tokens": 1261
    }
}
```

### GPT-4 Series

**Model IDs:**

- `gpt-4-turbo` - Latest GPT-4 with vision
- `gpt-4` - Original GPT-4
- `gpt-4-vision-preview` - Image understanding

**Configuration:**

```python
{
    "model": "gpt-4-turbo",
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}
```

**Vision-Specific:**

```python
{
    "model": "gpt-4-vision-preview",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "https://..."}}
            ]
        }
    ],
    "max_tokens": 300
}
```

---

## Anthropic Claude Models

### Claude 3 Series

**Model IDs:**

- `claude-3-7-sonnet-20250219` - Latest Claude 3 Sonnet
- `claude-3-opus-20240229` - Most capable Claude 3
- `claude-3-sonnet-20240229` - Balanced Claude 3
- `claude-3-haiku-20240307` - Fast, economical Claude 3

**Configuration:**

```python
{
    "model": "claude-3-7-sonnet-20250219",
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "stop_sequences": [],
    "stream": False
}
```

### Tool Use Configuration

**Tool Choice Options:**

```python
# Auto (default) - Claude decides
{
    "tool_choice": "auto"
}

# Any - Must use one tool
{
    "tool_choice": "any"
}

# Specific tool
{
    "tool_choice": {
        "type": "tool",
        "name": "get_weather"
    }
}

# No tools
{
    "tool_choice": "none"
}
```

### Prompt Caching (Cost Optimization)

```python
{
    "model": "claude-3-7-sonnet-20250219",
    "system": [
        {
            "type": "text",
            "text": "Long system prompt...",
            "cache_control": {"type": "ephemeral"}  # Cache this content
        }
    ],
    "messages": [...]
}
```

**Cache Best Practices:**

- Cache system instructions, background info, tool definitions
- Place cached content at prompt beginning
- Use cache breakpoints for different sections
- Monitor cache hit rates

---

## Google Gemini Models

### Gemini 2.5 Series

**Model IDs:**

- `gemini-2.5-pro` - Most capable
- `gemini-2.5-flash` - Fast, efficient

**Configuration:**

```python
{
    "model": "gemini-2.5-flash",
    "generationConfig": {
        "temperature": 1.0,
        "topP": 0.8,
        "topK": 10,
        "maxOutputTokens": 2048,
        "responseMimeType": "text/plain",  # or "application/json"
        "stopSequences": []
    },
    "safetySettings": [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
}
```

### Function Calling

**Tool Definition:**

```python
{
    "tools": [
        {
            "functionDeclarations": [
                {
                    "name": "function_name",
                    "description": "What the function does",
                    "parameters": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                }
            ]
        }
    ]
}
```

---

## Configuration Best Practices

### Temperature Selection

**By Task Type:**

```python
TEMPERATURE_GUIDELINES = {
    "factual_retrieval": 0.0,      # Deterministic, factual
    "code_generation": 0.2,         # Mostly deterministic
    "analysis": 0.4,                # Balanced
    "general_chat": 0.7,            # Default balanced
    "creative_writing": 0.9,        # More creative
    "brainstorming": 1.0            # Maximum creativity
}
```

### Token Management

**Optimization Strategy:**

```python
MAX_TOKENS_BY_TASK = {
    "quick_response": 512,
    "standard_response": 1024,
    "detailed_analysis": 2048,
    "comprehensive_report": 4096,
    "extensive_document": 8192
}
```

### Reasoning Effort Mapping

**Cross-Provider Mapping:**

```python
REASONING_EFFORT_MAP = {
    "quick": {
        "openai_effort": "low",
        "anthropic_model": "claude-3-haiku",
        "google_config": {"temperature": 0.5}
    },
    "standard": {
        "openai_effort": "medium",
        "anthropic_model": "claude-3-sonnet",
        "google_config": {"temperature": 0.7}
    },
    "comprehensive": {
        "openai_effort": "high",
        "anthropic_model": "claude-3-opus",
        "google_config": {"temperature": 0.8, "topK": 40}
    },
    "expert": {
        "openai_effort": "high",
        "anthropic_model": "claude-3-opus",
        "google_config": {"temperature": 0.9, "topP": 0.95}
    }
}
```

---

## Cost Optimization

### Token Efficiency

**Strategies:**

1. **Prompt Compression:** Remove redundant context
2. **Semantic Caching:** Cache similar query results
3. **Model Cascading:** Start with cheaper models, escalate if needed
4. **Batch Processing:** Combine multiple requests when possible

### Model Selection by Budget

**Cost-Aware Selection:**

```python
COST_TIERS = {
    "budget": ["claude-3-haiku", "gpt-3.5-turbo", "gemini-flash"],
    "balanced": ["claude-3-sonnet", "gpt-4", "gemini-pro"],
    "premium": ["claude-3-opus", "gpt-5", "gemini-pro-vision"]
}
```

### Caching Strategy

**High-Value Caching:**

```python
CACHE_PRIORITY = {
    "always_cache": [
        "system_instructions",
        "tool_definitions",
        "large_context_documents",
        "frequently_used_examples"
    ],
    "selective_cache": [
        "user_history",
        "temporary_context"
    ],
    "never_cache": [
        "user_specific_data",
        "time_sensitive_info"
    ]
}
```

---

## Integration with Current System

### Prompt Engine Configuration

**File:** `src/ultimate_discord_intelligence_bot/services/prompt_engine.py`

**Usage:**

```python
from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine

engine = PromptEngine()

# Create optimized prompt following official best practices
prompt = engine.create_prompt_with_best_practices(
    model_family="anthropic",  # openai, anthropic, google
    task_type="code_analysis",
    complexity="comprehensive",
    context={
        "content": file_content,
        "focus": "security_vulnerabilities"
    }
)
```

### Router Configuration

**File:** `src/core/llm_router.py`

**Usage:**

```python
from core.llm_router import LLMRouter

router = LLMRouter(clients)

# Auto-select model following best practices
model = router.select_model_for_content_type(
    content_type="multimodal",
    task_complexity="comprehensive",
    quality_requirement=0.9
)

# Will automatically:
# - Select appropriate reasoning effort
# - Configure temperature optimally
# - Set token limits appropriately
# - Enable caching where beneficial
```

---

## References

**Official Documentation:**

- OpenAI: <https://platform.openai.com/docs>
- Anthropic: <https://docs.anthropic.com>
- Google AI: <https://ai.google.dev/gemini-api/docs>

**Cookbooks & Examples:**

- OpenAI Cookbook: <https://github.com/openai/openai-cookbook>
- Anthropic Cookbook: <https://github.com/anthropics/anthropic-cookbook>
- Gemini Cookbook: <https://github.com/google-gemini/cookbook>

**Additional Resources:**

- Anthropic Courses: <https://github.com/anthropics/courses>
- OpenAI Best Practices: <https://platform.openai.com/docs/guides/prompt-engineering>
- Gemini Prompting Strategies: <https://ai.google.dev/gemini-api/docs/prompting-strategies>
