# Official Prompt Engineering Best Practices

**Compiled from:** OpenAI Platform Documentation, Anthropic Claude Documentation, Google Gemini API Documentation

**Last Updated:** 2025-10-09

---

## Table of Contents

1. [OpenAI Best Practices](#openai-best-practices)
2. [Anthropic Claude Best Practices](#anthropic-claude-best-practices)
3. [Google Gemini Best Practices](#google-gemini-best-practices)
4. [Universal Best Practices](#universal-best-practices)
5. [Model-Specific Configuration](#model-specific-configuration)

---

## OpenAI Best Practices

### General Guidelines

**Key Principles:**

- Use clear, specific instructions for desired behavior
- Provide examples to guide model behavior (few-shot learning)
- Leverage structured prompts with sections (Identity, Instructions, Examples)
- Use reasoning models (GPT-5) for complex tasks requiring multi-step thinking

### Reasoning Models (GPT-5)

**Reasoning Effort Levels:**

```json
{
  "reasoning": {
    "effort": "low"     // Faster, more economical (simple tasks)
    "effort": "medium"  // Balanced (default, most use cases)
    "effort": "high"    // Most thorough (complex tasks like coding, planning)
  }
}
```

**Best For:**

- **High Effort:** Code generation, bug fixing, multi-step planning, complex analysis
- **Medium Effort:** General problem-solving, moderate complexity tasks
- **Low Effort:** Simple queries, quick responses, conversational interactions

### Structured Prompt Pattern

```markdown
# Identity
You are [role description with specific expertise and behavior guidelines]

# Instructions
* [Specific instruction 1]
* [Specific instruction 2]
* [Format requirements]

# Examples
<user_query>
[Example input]
</user_query>

<assistant_response>
[Example output]
</assistant_response>
```

### Developer vs User Messages

```python
# Developer messages define system rules (highest priority)
{
    "role": "developer",
    "content": "Talk like a pirate."
}

# User messages provide inputs
{
    "role": "user",
    "content": "Are semicolons optional in JavaScript?"
}
```

### Reusable Prompts

**Benefits:**

- Version control for prompts
- Variable substitution
- Centralized prompt management
- No hardcoding in application code

```python
response = client.responses.create(
    model="gpt-5",
    prompt={
        "id": "pmpt_abc123",
        "version": "2",
        "variables": {
            "customer_name": "Jane Doe",
            "product": "40oz juice box"
        }
    }
)
```

---

## Anthropic Claude Best Practices

### Core Principles

**Claude 4 Optimization Guidelines:**

1. **Prioritize General Solutions Over Hard-Coding**

   ```text
   <general_solution>
   Please write a high-quality, general-purpose solution using the standard tools available.
   Do not create helper scripts or workarounds to accomplish the task more efficiently.
   Implement a solution that works correctly for all valid inputs, not just test cases.
   Focus on understanding the problem requirements and implementing the correct algorithm.
   </general_solution>
   ```

2. **Default to Action (Proactive Mode)**

   ```text
   <default_to_action>
   By default, implement changes rather than only suggesting them. If the user's intent
   is unclear, infer the most useful likely action and proceed, using tools to discover
   any missing details instead of guessing.
   </default_to_action>
   ```

3. **Conservative Mode (When Appropriate)**

   ```text
   <do_not_act_before_instructions>
   Don't jump into implementation or file changes unless clearly instructed to make
   modifications. When the user's intent is ambiguous, default to providing information,
   conducting research, and offering recommendations rather than taking action.
   </do_not_act_before_instructions>
   ```

### Context Management

**Handling Context Limits:**

```text
<context_management>
Your context window will automatically compress when approaching its limit, allowing you
to continue indefinitely from where you left off. Therefore, don't stop tasks prematurely
due to token budget concerns. If approaching your token budget limit, save your current
progress and state to memory before the context window refreshes. Always be as persistent
and autonomous as possible, completing tasks fully even when the end of your budget approaches.
</context_management>
```

### Parallel Tool Calls

**Maximize Efficiency:**

```text
<use_parallel_tool_calls>
For maximum efficiency, whenever you perform multiple independent operations, invoke all
relevant tools simultaneously rather than sequentially. Prioritize calling tools in
parallel whenever possible.
</use_parallel_tool_calls>
```

### Minimize Hallucinations

**Investigation Policy:**

```text
<investigate_before_answering>
Never speculate about code you haven't opened. If the user refers to a specific file,
you MUST read the file before responding. Ensure you investigate and read relevant files
BEFORE answering questions about the codebase. Never make claims about code before
investigating, unless you are certain of the correct answer.
</investigate_before_answering>
```

### Tool Choice Configuration

```python
# Claude decides whether to use tools (default)
tool_choice = "auto"

# Claude must use one of the provided tools
tool_choice = "any"

# Force specific tool usage
tool_choice = {"type": "tool", "name": "your_tool_name"}

# Prevent tool usage
tool_choice = "none"
```

### Prompt Caching

**Best Practices:**

- Cache stable, reusable content (system instructions, background info, large contexts)
- Place cached content at the beginning of the prompt
- Use cache breakpoints strategically
- Analyze cache hit rates regularly

---

## Google Gemini Best Practices

### Prompting Strategies

**1. Few-Shot Learning**

Show the model examples of desired behavior:

```text
Below are some examples showing a question, explanation, and answer format:

Question: Why is the sky blue?
Explanation1: [Detailed explanation]
Explanation2: [Concise explanation]
Answer: Explanation2

Question: What is the cause of earthquakes?
Explanation1: [Concise explanation]
Explanation2: [Detailed explanation]
Answer: Explanation1

Now, Answer the following question:
Question: How is snow formed?
[Your question here]
```

**2. Format Guidance**

Guide output format by providing structure:

```text
Create an outline for an essay about hummingbirds.
I. Introduction
   *
```

**3. Contextualized Prompts**

Provide specific context for accurate responses:

```text
Answer the question using the text below. Respond with only the text provided.
Question: [Your question]

Text:
[Reference material]
```

### Function Calling

**Schema Definition:**

```json
{
  "functionDeclarations": [
    {
      "name": "schedule_meeting",
      "description": "Schedules a meeting with specified attendees",
      "parameters": {
        "type": "object",
        "properties": {
          "attendees": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of people attending"
          },
          "date": {
            "type": "string",
            "description": "Date of the meeting (e.g., '2024-07-29')"
          },
          "time": {
            "type": "string",
            "description": "Time of the meeting (e.g., '15:00')"
          }
        },
        "required": ["attendees", "date", "time"]
      }
    }
  ]
}
```

### Generation Configuration

```json
{
  "generationConfig": {
    "temperature": 1.0,      // Randomness (0.0 = deterministic, 1.0 = creative)
    "topP": 0.8,             // Nucleus sampling
    "topK": 10,              // Top-k sampling
    "maxOutputTokens": 2048, // Maximum tokens to generate
    "stopSequences": ["END"]  // Stop generation at these sequences
  }
}
```

---

## Universal Best Practices

### Prompt Structure

**1. Be Explicit and Specific**

```text
❌ Create an analytics dashboard
✅ Create an analytics dashboard. Include as many relevant features and interactions
   as possible. Go beyond the basics to create a fully-featured implementation with
   user authentication, real-time updates, customizable widgets, and export functionality.
```

**2. Provide Context and Motivation**

```text
❌ Don't use ellipses
✅ Your response will be read aloud by a text-to-speech engine, so never use ellipses
   as the text-to-speech engine doesn't know how to pronounce them.
```

**3. Use Examples Over Negations**

```text
❌ Don't end haikus with a question
✅ Always end haikus with an assertion:
   Haiku are fun
   A short and simple poem
   A joy to write
```

### Multi-Turn Conversations

**Structured Interaction:**

```json
{
  "messages": [
    {
      "role": "developer",  // or "system" for some models
      "content": "You are an expert code reviewer focused on security."
    },
    {
      "role": "user",
      "content": "Review this authentication function for vulnerabilities."
    },
    {
      "role": "assistant",
      "content": "I'll analyze the authentication function..."
    },
    {
      "role": "user",
      "content": "Now check for SQL injection risks."
    }
  ]
}
```

### Output Format Control

**1. Structured Data (JSON)**

```text
Extract the following attributes and return as JSON:
- ingredients (array of strings)
- cuisine_type (string)
- is_vegetarian (boolean)
- difficulty_level (string: easy|medium|hard)
```

**2. Markdown Tables**

```text
Parse the table in this image into markdown format
```

**3. Constrained Options**

```text
Multiple choice: Which option best describes the book The Odyssey?
Options:
- thriller
- sci-fi
- mythology
- biography

Answer with only the option name.
```

---

## Model-Specific Configuration

### OpenAI Models

**GPT-4/GPT-5 Configuration:**

```python
{
    "model": "gpt-5",
    "reasoning": {"effort": "medium"},  # For GPT-5 reasoning models
    "max_output_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9
}
```

### Anthropic Claude Models

**Claude 3/4 Configuration:**

```python
{
    "model": "claude-3-7-sonnet-20250219",  # or claude-3-opus, claude-3-haiku
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "tool_choice": "auto"  # or "any", {"type": "tool", "name": "tool_name"}, "none"
}
```

### Google Gemini Models

**Gemini Configuration:**

```python
{
    "model": "gemini-2.5-flash",  # or gemini-2.5-pro
    "generationConfig": {
        "temperature": 1.0,
        "topP": 0.8,
        "topK": 10,
        "maxOutputTokens": 2048,
        "stopSequences": []
    }
}
```

---

## Implementation Recommendations

### For This System

**1. Auto-Routing Integration:**

```python
# Use content-type aware routing with reasoning effort
router.select_model_for_content_type(
    content_type="multimodal",
    task_complexity="comprehensive",  # Maps to reasoning effort
    quality_requirement=0.9
)
```

**2. Prompt Template Management:**

```python
# Store prompts in version-controlled templates
prompt_engine.create_prompt(
    template_id="analysis_comprehensive",
    variables={
        "content_url": url,
        "depth": "comprehensive",
        "focus_areas": ["sentiment", "topics", "emotions"]
    }
)
```

**3. Parallel Tool Execution:**

```python
# Enable parallel tool calls for efficiency
<use_parallel_tool_calls>
Whenever you intend to call multiple tools and there are no dependencies between
the tool calls, make all of the independent tool calls in parallel.
</use_parallel_tool_calls>
```

**4. Cost Optimization:**

```python
# Use appropriate models for task complexity
- Quick analysis: Use fast, economical models (Haiku, GPT-3.5)
- Standard analysis: Use balanced models (Sonnet, GPT-4)
- Comprehensive analysis: Use advanced models (Opus, GPT-5 high reasoning)
- Expert analysis: Use maximum capability models with extended thinking
```

---

## Quick Reference

### Model Selection by Task Type

| Task Type | OpenAI | Anthropic | Google | Reasoning Effort |
|-----------|--------|-----------|--------|------------------|
| Simple Q&A | GPT-4 | Claude Haiku | Gemini Flash | Low |
| Code Review | GPT-4 | Claude Sonnet | Gemini Pro | Medium |
| Complex Planning | GPT-5 | Claude Opus | Gemini Pro | High |
| Multi-Modal | GPT-4 Vision | Claude 3 Opus | Gemini Pro Vision | Medium-High |
| Long Context | GPT-4 Turbo | Claude 3 Sonnet | Gemini Pro | Medium |

### Temperature Guidelines

| Temperature | Use Case |
|-------------|----------|
| 0.0 - 0.3 | Factual tasks, deterministic outputs, code generation |
| 0.4 - 0.7 | Balanced creativity and coherence (default) |
| 0.8 - 1.0 | Creative writing, brainstorming, diverse outputs |

### Token Optimization

**Best Practices:**

- Cache frequently used system prompts
- Use prompt compression for large contexts
- Leverage semantic caching for similar queries
- Monitor token usage and adjust max_tokens appropriately
- Use streaming for long-running tasks

---

## Integration with Current System

**Prompt Engine Integration:**

```python
from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine

engine = PromptEngine()

# Use official best practices
prompt = engine.create_prompt(
    template="structured_analysis",
    identity="Expert multi-modal content analyst",
    instructions=[
        "Analyze content across all modalities",
        "Provide structured JSON output",
        "Include confidence scores"
    ],
    examples=[...],
    context={"content_type": "image", "depth": "comprehensive"}
)
```

**Model Router Integration:**

```python
from core.llm_router import LLMRouter

router = LLMRouter(clients)

# Select model with reasoning effort
model = router.select_model_for_content_type(
    content_type="multimodal",
    task_complexity="expert",  # Maps to "high" reasoning effort
    quality_requirement=0.95
)
```

---

## References

- [OpenAI Platform Documentation](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Claude Documentation](https://docs.anthropic.com/docs/build-with-claude/prompt-engineering)
- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs/prompting-intro)
- [OpenAI Cookbook](https://github.com/openai/openai-cookbook)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)
- [Google Gemini Cookbook](https://github.com/google-gemini/cookbook)
