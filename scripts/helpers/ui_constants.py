"""UI constants and configuration values for Discord bot interface.

This module centralizes magic numbers and constants used throughout the bot
to improve maintainability and make values easier to adjust.
"""

# Discord UI Constants
DISCORD_MAX_CONTENT_LENGTH = 1800
DISCORD_TRUNCATION_SUFFIX = "… (truncated)"

# Discord Button Styles (from discord.py)
BUTTON_STYLE_PRIMARY = 1
BUTTON_STYLE_SECONDARY = 2
BUTTON_STYLE_LINK = 5

# Response Quality Assessment Thresholds
QUALITY_OPTIMAL_LENGTH_MIN = 100
QUALITY_OPTIMAL_LENGTH_MAX = 2000
QUALITY_ACCEPTABLE_LENGTH_MIN = 50
QUALITY_ACCEPTABLE_LENGTH_MAX = 3000

# Response Quality Scoring Weights
QUALITY_WEIGHT_LENGTH = 0.20
QUALITY_WEIGHT_FACT_CHECKING = 0.30
QUALITY_WEIGHT_REASONING = 0.30
QUALITY_WEIGHT_BALANCE = 0.20

# Response Quality Partial Credit
QUALITY_PARTIAL_CREDIT = 0.10
QUALITY_FULL_CREDIT_THRESHOLD = 2
QUALITY_PARTIAL_CREDIT_THRESHOLD = 1

# Response Quality Indicator Keywords
FACT_CHECKING_INDICATORS = [
    "verified",
    "source",
    "fact-check",
    "according to",
    "evidence",
    "confirmed",
    "research shows",
]

REASONING_INDICATORS = [
    "because",
    "analysis",
    "therefore",
    "however",
    "indicates",
    "suggests",
    "demonstrates",
]

BALANCE_INDICATORS = [
    "on the other hand",
    "alternatively",
    "different perspective",
    "counterpoint",
    "various viewpoints",
    "both sides",
]

BIAS_INDICATORS = [
    "obviously",
    "clearly wrong",
    "everyone knows",
    "without question",
    "absolutely certain",
    "no doubt",
    "undeniable",
]

# Environment Variable Defaults
DEFAULT_FEATURE_FLAGS = {
    # Ingestion/performance
    "ENABLE_INGEST_CONCURRENT": "1",
    # Reliability/observability
    "ENABLE_HTTP_RETRY": "1",
    "ENABLE_HTTP_CACHE": "1",
    "ENABLE_METRICS": "1",
    "ENABLE_TRACING": "1",
    # Intelligence surfaces
    "ENABLE_VECTOR_SEARCH": "1",
    "ENABLE_SEMANTIC_CACHE": "1",
    "ENABLE_RAG_CONTEXT": "1",
    "ENABLE_RETRIEVAL_ADAPTIVE_K": "1",
    "ENABLE_RERANKER": "1",
    "ENABLE_PROMPT_COMPRESSION": "1",
    "ENABLE_PII_DETECTION": "1",
    # Routing + RL for adaptive model selection
    "ENABLE_RL_ROUTING": "1",
    "ENABLE_RL_GLOBAL": "1",
    "ENABLE_RL_CONTEXTUAL": "1",
    "ENABLE_RL_THOMPSON": "1",
    # Platforms
    "ENABLE_INGEST_YOUTUBE": "1",
    # Grounding/citations
    "ENABLE_GROUNDING": "1",
    # Backfill
    "ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST": "1",
    "ENABLE_UPLOADER_BACKFILL": "1",
    "ENABLE_AUTO_FOLLOW_UPLOADER": "1",
    # Background queue worker (fully automatic)
    "ENABLE_INGEST_WORKER": "1",
    "INGEST_WORKER_CONCURRENCY": "1",
    # Discord UX
    "DISCORD_CREATE_THREADS": "1",
}

# Python Environment Detection
PYTHON_VERSION = "3.12"
SITE_PACKAGES_PATH = f"lib/python{PYTHON_VERSION}/site-packages"

# Path Insertion Priorities
PATH_PRIORITY_SITE_PACKAGES = 0
PATH_PRIORITY_SRC = 0

# System Constants
LIGHTWEIGHT_IMPORT_FLAG = "1"
