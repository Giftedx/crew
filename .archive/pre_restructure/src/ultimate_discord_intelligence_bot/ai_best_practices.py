"""AI Model Best Practices - Official Guidelines for Immediate Use.

This module provides programmatic access to official best practices from:
- OpenAI Platform Documentation
- Anthropic Claude Documentation
- Google Gemini API Documentation

All AI operations in the system should reference these guidelines for optimal performance.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelConfig:
    """Configuration for AI model based on official best practices."""

    model_id: str
    temperature: float
    max_tokens: int
    reasoning_effort: str | None = None  # For reasoning models
    top_p: float | None = None
    top_k: int | None = None
    tool_choice: str | dict[str, str] | None = None


# Official model configurations from provider documentation
OFFICIAL_MODEL_CONFIGS = {
    # OpenAI Models
    "gpt-5-quick": ModelConfig(model_id="gpt-5", temperature=0.3, max_tokens=512, reasoning_effort="low"),
    "gpt-5-standard": ModelConfig(model_id="gpt-5", temperature=0.7, max_tokens=2048, reasoning_effort="medium"),
    "gpt-5-expert": ModelConfig(model_id="gpt-5", temperature=0.8, max_tokens=4096, reasoning_effort="high"),
    "gpt-4-turbo": ModelConfig(model_id="gpt-4-turbo", temperature=0.7, max_tokens=4096, top_p=0.9),
    "gpt-4-vision": ModelConfig(model_id="gpt-4-vision-preview", temperature=0.7, max_tokens=4096, top_p=0.9),
    # Anthropic Models
    "claude-opus": ModelConfig(
        model_id="claude-3-opus-20240229",
        temperature=0.8,
        max_tokens=4096,
        top_p=0.9,
        top_k=40,
    ),
    "claude-sonnet": ModelConfig(
        model_id="claude-3-7-sonnet-20250219",
        temperature=0.7,
        max_tokens=2048,
        top_p=0.9,
        top_k=40,
    ),
    "claude-haiku": ModelConfig(
        model_id="claude-3-haiku-20240307",
        temperature=0.5,
        max_tokens=1024,
        top_p=0.8,
        top_k=30,
    ),
    # Google Gemini Models
    "gemini-pro": ModelConfig(model_id="gemini-2.5-pro", temperature=0.8, max_tokens=2048, top_p=0.8, top_k=10),
    "gemini-flash": ModelConfig(
        model_id="gemini-2.5-flash",
        temperature=0.7,
        max_tokens=1024,
        top_p=0.8,
        top_k=10,
    ),
    "gemini-pro-vision": ModelConfig(
        model_id="gemini-pro-vision",
        temperature=0.7,
        max_tokens=2048,
        top_p=0.8,
        top_k=10,
    ),
}


# Task-based temperature recommendations (official guidelines)
TEMPERATURE_BY_TASK = {
    "factual_retrieval": 0.0,  # Deterministic, factual (all providers)
    "code_generation": 0.2,  # Mostly deterministic (OpenAI, Anthropic)
    "data_analysis": 0.4,  # Low creativity, high accuracy
    "general_chat": 0.7,  # Default balanced (official default)
    "content_analysis": 0.7,  # Balanced understanding
    "creative_writing": 0.9,  # More creative (Anthropic, Google)
    "brainstorming": 1.0,  # Maximum creativity
}


# Reasoning effort mapping (cross-provider)
REASONING_EFFORT_MAP = {
    "quick": {
        "openai_effort": "low",
        "anthropic_model": "claude-3-haiku",
        "google_temperature": 0.5,
        "description": "Fast, economical responses",
    },
    "standard": {
        "openai_effort": "medium",
        "anthropic_model": "claude-3-sonnet",
        "google_temperature": 0.7,
        "description": "Balanced performance (default)",
    },
    "comprehensive": {
        "openai_effort": "high",
        "anthropic_model": "claude-3-opus",
        "google_temperature": 0.8,
        "description": "Deep analysis, high quality",
    },
    "expert": {
        "openai_effort": "high",
        "anthropic_model": "claude-3-opus",
        "google_temperature": 0.9,
        "description": "Maximum capability, extended thinking",
    },
}


# Official prompt templates from provider documentation
OFFICIAL_PROMPT_TEMPLATES = {
    "structured_analysis": """# Identity
You are an expert {domain} analyst with advanced {skills}.

# Instructions
{instructions}

# Context
{context}

# Examples
{examples}

# Task
{task}
""",
    "multi_modal_analysis": """# Multi-Modal Content Analysis

## Task
Analyze the provided content across all available modalities:
- Visual elements (if image/video)
- Audio elements (if video/audio)
- Textual elements (captions, transcripts)
- Metadata (timestamps, creators, context)

## Output Format
Return structured JSON with:
{{
  "content_type": "string",
  "visual_analysis": {{}},
  "audio_analysis": {{}},
  "text_analysis": {{}},
  "unified_sentiment": "string",
  "dominant_themes": ["array"],
  "confidence_scores": {{}}
}}

## Requirements
- Provide confidence scores for all assertions
- Include cross-modal correlations
- Cite specific evidence from content

Content: {content_url}
""",
    "code_analysis": """# Identity
You are an expert {language} developer following official style guidelines and best practices.

# Instructions
- Write clean, well-documented code
- Include comprehensive type hints
- Add proper error handling
- Follow language-specific conventions
- Include tests where appropriate

# Context
{context}

# Task
{task}
""",
    "investigation_first": """<investigate_before_answering>
Never speculate about code you haven't opened. If the user refers to a specific file,
you MUST read the file before responding. Ensure you investigate and read relevant files
BEFORE answering questions about the codebase.
</investigate_before_answering>

{task}
""",
}


# Best practice tags from official documentation
BEST_PRACTICE_TAGS = {
    "parallel_tools": """<use_parallel_tool_calls>
For maximum efficiency, whenever you perform multiple independent operations,
invoke all relevant tools simultaneously rather than sequentially.
Prioritize calling tools in parallel whenever possible.
</use_parallel_tool_calls>""",
    "general_solution": """<general_solution>
Please write a high-quality, general-purpose solution using the standard tools available.
Do not create helper scripts or workarounds. Implement a solution that works correctly
for all valid inputs, not just test cases. Focus on understanding the problem requirements
and implementing the correct algorithm.
</general_solution>""",
    "context_management": """<context_management>
Your context window will automatically compress when approaching its limit. Don't stop
tasks prematurely due to token budget concerns. If approaching your limit, save current
progress and state to memory before the context window refreshes. Complete tasks fully
even when approaching budget limits.
</context_management>""",
    "default_to_action": """<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent
is unclear, infer the most useful likely action and proceed, using tools to discover
any missing details instead of guessing.
</default_to_action>""",
}


def get_model_config(model_name: str, task_complexity: str = "standard", task_type: str | None = None) -> ModelConfig:
    """Get official model configuration based on provider best practices.

    Args:
        model_name: Friendly model name (gpt-5, claude-opus, gemini-pro, etc.)
        task_complexity: Complexity level (quick, standard, comprehensive, expert)
        task_type: Optional task type for temperature adjustment

    Returns:
        ModelConfig with official recommended settings
    """
    # Map complexity to config key
    config_key = f"{model_name}-{task_complexity}" if task_complexity != "standard" else model_name

    # Get base config
    if config_key in OFFICIAL_MODEL_CONFIGS:
        config = OFFICIAL_MODEL_CONFIGS[config_key]
    elif model_name in OFFICIAL_MODEL_CONFIGS:
        config = OFFICIAL_MODEL_CONFIGS[model_name]
    else:
        # Fallback to standard config
        config = OFFICIAL_MODEL_CONFIGS.get("claude-sonnet")

    # Adjust temperature based on task type if specified
    if task_type and task_type in TEMPERATURE_BY_TASK:
        config.temperature = TEMPERATURE_BY_TASK[task_type]

    return config


def get_prompt_template(template_name: str, variables: dict[str, Any] | None = None) -> str:
    """Get official prompt template with variable substitution.

    Args:
        template_name: Template identifier (structured_analysis, multi_modal_analysis, etc.)
        variables: Variables to substitute into template

    Returns:
        Formatted prompt following official best practices
    """
    if template_name not in OFFICIAL_PROMPT_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")

    template = OFFICIAL_PROMPT_TEMPLATES[template_name]

    if variables:
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}") from e

    return template


def get_best_practice_tag(tag_name: str) -> str:
    """Get official best practice tag for prompt enhancement.

    Args:
        tag_name: Tag identifier (parallel_tools, general_solution, etc.)

    Returns:
        Best practice prompt tag from official documentation
    """
    if tag_name not in BEST_PRACTICE_TAGS:
        raise ValueError(f"Unknown best practice tag: {tag_name}")

    return BEST_PRACTICE_TAGS[tag_name]


def get_reasoning_config(complexity: str, provider: str = "openai") -> dict[str, Any]:
    """Get reasoning configuration for specific complexity level.

    Args:
        complexity: Complexity level (quick, standard, comprehensive, expert)
        provider: AI provider (openai, anthropic, google)

    Returns:
        Provider-specific reasoning configuration
    """
    if complexity not in REASONING_EFFORT_MAP:
        complexity = "standard"

    effort_config = REASONING_EFFORT_MAP[complexity]

    if provider == "openai":
        return {"reasoning": {"effort": effort_config["openai_effort"]}}
    elif provider == "anthropic":
        return {"model": effort_config["anthropic_model"]}
    elif provider == "google":
        return {"temperature": effort_config["google_temperature"]}
    else:
        # Default to OpenAI format
        return {"reasoning": {"effort": effort_config["openai_effort"]}}


def create_optimized_prompt(
    task_description: str,
    content_type: str,
    complexity: str = "standard",
    include_best_practices: list[str] | None = None,
) -> str:
    """Create an optimized prompt following all official best practices.

    Args:
        task_description: Description of the task to perform
        content_type: Type of content (text, image, video, audio, multimodal)
        complexity: Task complexity level
        include_best_practices: List of best practice tags to include

    Returns:
        Optimized prompt with official best practices applied
    """
    # Select appropriate template
    if content_type in ["image", "video", "audio", "multimodal"]:
        template_name = "multi_modal_analysis"
    else:
        template_name = "structured_analysis"

    # Get base template
    prompt = OFFICIAL_PROMPT_TEMPLATES[template_name]

    # Add best practice tags
    if include_best_practices:
        tags = "\n\n".join(get_best_practice_tag(tag) for tag in include_best_practices)
        prompt = f"{tags}\n\n{prompt}"

    # Format with task description
    with contextlib.suppress(KeyError):
        prompt = prompt.format(
            task=task_description,
            content_url="[Content URL will be provided]",
            domain="content analysis",
            skills="multi-modal understanding and sentiment analysis",
            instructions="Analyze thoroughly and provide structured output",
            context=f"Content type: {content_type}, Complexity: {complexity}",
            examples="",
            language="Python",
        )

    return prompt


__all__ = [
    "BEST_PRACTICE_TAGS",
    "OFFICIAL_MODEL_CONFIGS",
    "OFFICIAL_PROMPT_TEMPLATES",
    "REASONING_EFFORT_MAP",
    "TEMPERATURE_BY_TASK",
    "ModelConfig",
    "create_optimized_prompt",
    "get_best_practice_tag",
    "get_model_config",
    "get_prompt_template",
    "get_reasoning_config",
]
