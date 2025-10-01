"""Declarative metric specifications for obs.metrics.

Each entry: (kind, name, help_text, labels)
 where kind is one of: 'counter' | 'histogram' | 'gauge'.

Keeping this list separate reduces churn in the core metrics module and keeps
the file sizes manageable while preserving the public API in obs.metrics.
"""

from __future__ import annotations

from typing import Literal

Kind = Literal["counter", "histogram", "gauge"]


METRIC_SPECS: list[tuple[Kind, str, str, list[str]]] = [
    ("counter", "router_decisions_total", "Number of routing decisions made", ["tenant", "workspace"]),
    ("histogram", "llm_latency_ms", "Latency of LLM calls in milliseconds", ["tenant", "workspace"]),
    (
        "counter",
        "llm_model_selected_total",
        "LLM model selections",
        ["tenant", "workspace", "task", "model", "provider"],
    ),
    (
        "counter",
        "llm_budget_rejections_total",
        "LLM calls rejected due to budget",
        ["tenant", "workspace", "task", "provider"],
    ),
    (
        "histogram",
        "llm_estimated_cost_usd",
        "Estimated cost (USD) of LLM calls",
        ["tenant", "workspace", "model", "provider"],
    ),
    ("counter", "llm_cache_hits_total", "Total LLM cache hits", ["tenant", "workspace", "model", "provider"]),
    ("counter", "llm_cache_misses_total", "Total LLM cache misses", ["tenant", "workspace", "model", "provider"]),
    # Structured LLM metrics
    (
        "counter",
        "structured_llm_requests_total",
        "Total structured LLM requests",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "counter",
        "structured_llm_success_total",
        "Total successful structured LLM responses",
        ["tenant", "workspace", "task", "method", "model"],
    ),
    (
        "counter",
        "structured_llm_errors_total",
        "Total structured LLM errors by type",
        ["tenant", "workspace", "task", "method", "error_type"],
    ),
    (
        "counter",
        "structured_llm_parsing_failures_total",
        "Total JSON parsing failures in structured responses",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "counter",
        "structured_llm_validation_failures_total",
        "Total Pydantic validation failures",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "counter",
        "structured_llm_instructor_usage_total",
        "Total usage of Instructor for structured outputs",
        ["tenant", "workspace", "task", "model"],
    ),
    (
        "counter",
        "structured_llm_fallback_usage_total",
        "Total fallback to manual parsing",
        ["tenant", "workspace", "task", "model"],
    ),
    (
        "histogram",
        "structured_llm_latency_ms",
        "Latency of structured LLM operations",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "histogram",
        "structured_llm_parsing_latency_ms",
        "Latency of JSON parsing operations",
        ["tenant", "workspace", "task"],
    ),
    # Streaming-specific metrics
    (
        "counter",
        "structured_llm_streaming_requests_total",
        "Total streaming structured LLM requests",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "counter",
        "structured_llm_streaming_chunks_total",
        "Total streaming chunks processed",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "histogram",
        "structured_llm_streaming_latency_ms",
        "Latency of streaming structured LLM operations",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "histogram",
        "structured_llm_streaming_progress_ratio",
        "Progress ratio for streaming operations (0.0-1.0)",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "counter",
        "structured_llm_streaming_errors_total",
        "Total streaming structured LLM errors",
        ["tenant", "workspace", "task", "method", "error_type"],
    ),
    # Cache-specific metrics for structured LLM
    (
        "counter",
        "structured_llm_cache_hits_total",
        "Total structured LLM cache hits",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        "counter",
        "structured_llm_cache_misses_total",
        "Total structured LLM cache misses",
        ["tenant", "workspace", "task", "method"],
    ),
    ("histogram", "http_request_latency_ms", "Latency of inbound HTTP requests (FastAPI)", ["route", "method"]),
    ("counter", "http_requests_total", "Total inbound HTTP requests", ["route", "method", "status"]),
    (
        "counter",
        "rate_limit_rejections_total",
        "Total HTTP requests rejected due to rate limiting (429)",
        ["route", "method"],
    ),
    (
        "counter",
        "http_retry_attempts_total",
        "Total HTTP retry attempts (excluding first attempt)",
        ["tenant", "workspace", "method", "host"],
    ),
    (
        "counter",
        "http_retry_giveups_total",
        "Total HTTP operations that exhausted retries",
        ["tenant", "workspace", "method", "host"],
    ),
    # Tenancy fallback visibility
    (
        "counter",
        "tenancy_fallback_total",
        "Count of events where no TenantContext was set and default was used",
        ["tenant", "workspace", "component"],
    ),
    # Pipeline-specific metrics
    ("counter", "pipeline_requests_total", "Total pipeline processing requests", ["tenant", "workspace"]),
    (
        "counter",
        "pipeline_steps_completed_total",
        "Total pipeline steps completed successfully",
        ["tenant", "workspace", "step"],
    ),
    ("counter", "pipeline_steps_failed_total", "Total pipeline steps that failed", ["tenant", "workspace", "step"]),
    ("counter", "pipeline_steps_skipped_total", "Total pipeline steps skipped", ["tenant", "workspace", "step"]),
    (
        "histogram",
        "pipeline_duration_seconds",
        "Duration of full pipeline processing",
        ["tenant", "workspace", "status"],
    ),
    (
        "histogram",
        "pipeline_step_duration_seconds",
        "Duration of individual pipeline steps",
        ["tenant", "workspace", "step", "orchestrator", "status"],
    ),
    (
        "histogram",
        "pipeline_total_duration_seconds",
        "Duration of full pipeline processing (orchestrator-specific)",
        ["tenant", "workspace", "orchestrator", "status"],
    ),
    ("gauge", "pipeline_inflight", "Current number of inflight pipeline runs", ["tenant", "workspace", "orchestrator"]),
    (
        "counter",
        "circuit_breaker_requests_total",
        "Circuit breaker outcomes",
        ["tenant", "workspace", "circuit", "result"],
    ),
    (
        "gauge",
        "circuit_breaker_state",
        "Circuit breaker state (0=closed,0.5=half-open,1=open)",
        ["tenant", "workspace", "circuit"],
    ),
    # Ingest fallbacks (observability for resilience decisions)
    (
        "counter",
        "ingest_transcript_fallbacks_total",
        "Count of transcript fallbacks to Whisper",
        ["tenant", "workspace", "source"],
    ),
    (
        "counter",
        "ingest_missing_id_fallbacks_total",
        "Count of ingest runs missing episode_id (used URL-hash fallback)",
        ["tenant", "workspace", "source"],
    ),
    # Scheduler metrics
    ("counter", "scheduler_enqueued_total", "Jobs enqueued by scheduler", ["tenant", "workspace", "source"]),
    (
        "counter",
        "scheduler_processed_total",
        "Jobs processed successfully by worker",
        ["tenant", "workspace", "source"],
    ),
    ("counter", "scheduler_errors_total", "Worker errors while processing jobs", ["tenant", "workspace", "source"]),
    ("gauge", "scheduler_queue_backlog", "Current number of pending jobs in queue", ["tenant", "workspace"]),
    ("gauge", "system_health_score", "Overall system health score (0-100)", ["tenant", "workspace"]),
    ("gauge", "cost_per_interaction", "Average cost per user interaction in USD", ["tenant", "workspace"]),
    # Cache performance metrics
    (
        "counter",
        "cache_hits_total",
        "Total cache hits by cache and level",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        "counter",
        "cache_misses_total",
        "Total cache misses by cache and level",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        "counter",
        "cache_promotions_total",
        "Total entries promoted to higher cache level",
        ["tenant", "workspace", "cache_name"],
    ),
    (
        "counter",
        "cache_demotions_total",
        "Total entries demoted to lower cache level",
        ["tenant", "workspace", "cache_name"],
    ),
    (
        "counter",
        "cache_evictions_total",
        "Total entries evicted due to capacity limits",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    ("counter", "cache_compressions_total", "Total entries compressed", ["tenant", "workspace", "cache_name"]),
    ("counter", "cache_decompressions_total", "Total entries decompressed", ["tenant", "workspace", "cache_name"]),
    (
        "counter",
        "cache_errors_total",
        "Total cache operation errors",
        ["tenant", "workspace", "cache_name", "operation", "error_type"],
    ),
    ("gauge", "cache_size_bytes", "Current cache size in bytes", ["tenant", "workspace", "cache_name", "cache_level"]),
    (
        "gauge",
        "cache_entries_count",
        "Current number of entries in cache",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        "gauge",
        "cache_hit_rate_ratio",
        "Current cache hit rate (0.0-1.0)",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        "gauge",
        "cache_memory_usage_ratio",
        "Cache memory usage ratio (0.0-1.0)",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        "histogram",
        "cache_operation_latency_ms",
        "Latency of cache operations in milliseconds",
        ["tenant", "workspace", "cache_name", "operation"],
    ),
    (
        "histogram",
        "cache_compression_ratio",
        "Compression effectiveness ratio (compressed/original)",
        ["tenant", "workspace", "cache_name"],
    ),
    # Segmenter & embedding instrumentation (low cardinality)
    (
        "histogram",
        "segment_chunk_size_chars",
        "Distribution of segment chunk sizes (characters)",
        ["tenant", "workspace"],
    ),
    (
        "histogram",
        "segment_chunk_size_tokens",
        "Approximate distribution of segment chunk sizes (tokens, heuristic)",
        ["tenant", "workspace"],
    ),
    (
        "counter",
        "segment_chunk_merges_total",
        "Number of chunk merges/flushes performed during segmentation",
        ["tenant", "workspace"],
    ),
    (
        "counter",
        "embed_deduplicates_skipped_total",
        "Number of duplicate text segments skipped before embedding",
        ["tenant", "workspace"],
    ),
    # Degradation / fallback reporting metrics (flag gated usage)
    (
        "counter",
        "degradation_events_total",
        "Count of recorded degradation events (fallbacks, timeouts, partial failures)",
        ["tenant", "workspace", "component", "event_type", "severity"],
    ),
    (
        "histogram",
        "degradation_impact_latency_ms",
        "Observed added latency (ms) attributed to degradation events when measurable",
        ["tenant", "workspace", "component", "event_type"],
    ),
    # New retrieval & RL / compression instrumentation
    (
        "histogram",
        "retrieval_selected_k",
        "Distribution of selected retrieval k values (post-adaptive heuristic)",
        ["tenant", "workspace", "strategy"],
    ),
    (
        "histogram",
        "retrieval_latency_ms",
        "Latency of retrieval phases (phase label: initial|post_rerank|prefetch)",
        ["tenant", "workspace", "phase"],
    ),
    (
        "histogram",
        "prompt_compression_ratio",
        "Prompt compression ratio (compressed/original tokens)",
        ["tenant", "workspace", "method"],
    ),
    (
        "histogram",
        "semantic_cache_similarity",
        "Similarity scores for semantic cache hits",
        ["tenant", "workspace", "bucket"],
    ),
    (
        "counter",
        "semantic_cache_prefetch_issued_total",
        "Number of semantic cache prefetch attempts issued",
        ["tenant", "workspace"],
    ),
    (
        "counter",
        "semantic_cache_prefetch_used_total",
        "Number of prefetched semantic cache entries actually used",
        ["tenant", "workspace"],
    ),
    (
        "counter",
        "semantic_cache_shadow_hits_total",
        "Number of semantic cache hits in shadow mode (would have been cache hits)",
        ["tenant", "workspace", "model"],
    ),
    (
        "counter",
        "semantic_cache_shadow_misses_total",
        "Number of semantic cache misses in shadow mode",
        ["tenant", "workspace", "model"],
    ),
    (
        "gauge",
        "semantic_cache_shadow_hit_ratio",
        "Current semantic cache hit ratio in shadow mode",
        ["tenant", "workspace"],
    ),
    (
        "histogram",
        "rl_reward_latency_gap_ms",
        "Latency between model response and reward recording",
        ["tenant", "workspace", "domain"],
    ),
    (
        "gauge",
        "active_bandit_policy",
        "Current active bandit policy per domain (1 if active)",
        ["tenant", "workspace", "domain", "policy"],
    ),
    # Experiment harness metrics for A/B testing
    (
        "counter",
        "experiment_variant_allocations_total",
        "Total variant allocations by experiment",
        ["tenant", "workspace", "experiment_id", "variant", "phase"],
    ),
    (
        "counter",
        "experiment_rewards_total",
        "Total rewards recorded by experiment variant",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    (
        "histogram",
        "experiment_reward_value",
        "Distribution of reward values by experiment variant",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    (
        "gauge",
        "experiment_regret_total",
        "Cumulative regret by experiment variant",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    (
        "gauge",
        "experiment_phase_status",
        "Experiment phase status (0=shadow, 1=active)",
        ["tenant", "workspace", "experiment_id"],
    ),
    # Trajectory evaluation metrics
    (
        "counter",
        "trajectory_evaluations_total",
        "Total trajectory evaluations performed",
        ["tenant", "workspace", "success"],
    ),
    # Advanced bandit metrics
    (
        "gauge",
        "advanced_bandit_reward_model_mse",
        "Mean squared error of DoublyRobust reward model",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    (
        "gauge",
        "advanced_bandit_tree_depth",
        "Average tree depth for OffsetTree bandit",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    (
        "gauge",
        "advanced_bandit_importance_weight",
        "Average importance weight for DoublyRobust bandit",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    (
        "gauge",
        "advanced_bandit_confidence_interval",
        "Average confidence interval width for advanced bandits",
        ["tenant", "workspace", "experiment_id", "variant"],
    ),
    # Prompt-specific counters
    (
        "counter",
        "prompt_compression_target_met_total",
        "Number of times prompt compression met the configured target",
        ["tenant", "workspace"],
    ),
    (
        "counter",
        "prompt_emergency_truncations_total",
        "Number of times emergency prompt truncation was applied",
        ["tenant", "workspace"],
    ),
]

__all__ = ["METRIC_SPECS", "Kind"]
